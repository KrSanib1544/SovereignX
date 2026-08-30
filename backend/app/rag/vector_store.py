# backend/app/rag/vector_store.py
"""
Local Qdrant Vector Database Manager
Manages embedded file-backed Qdrant collections with strict pre-retrieval authorization filters.
"""

import uuid
import warnings
from typing import Any, Dict, List, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, MatchAny

from backend.app.config import settings
from backend.app.rag.provenance import ChunkProvenance


def deterministic_point_id(chunk_id: str) -> str:
    """Generate a deterministic UUID from chunk_id to ensure idempotent upserts."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))


class QdrantVectorStore:
    """
    Local-only Qdrant Vector Database Client.
    """

    COLLECTION_NAME: str = "sovereign_rag"

    def __init__(self, location: Optional[str] = None, path: Optional[str] = None):
        """
        Initialize Qdrant client. If location is ':memory:', uses in-memory mode for tests.
        Otherwise, uses local storage path configured in settings.
        """
        if location == ":memory:":
            self.client = QdrantClient(location=":memory:")
        else:
            storage_path = path or str(settings.QDRANT_STORAGE_DIR)
            settings.QDRANT_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
            self.client = QdrantClient(path=storage_path)

    def init_collection(self, dimension: int = 384, recreate: bool = False) -> None:
        """
        Create the sovereign_rag collection and payload indexes if not already present.
        """
        collections = self.client.get_collections().collections
        exists = any(c.name == self.COLLECTION_NAME for c in collections)

        if exists and recreate:
            self.client.delete_collection(self.COLLECTION_NAME)
            exists = False

        if not exists:
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
            )

            # Silently attempt payload indexing (informational on local SQLite/in-memory Qdrant)
            for field in ["workspace_id", "classification", "document_id"]:
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        self.client.create_payload_index(
                            collection_name=self.COLLECTION_NAME,
                            field_name=field,
                            field_schema=rest.PayloadSchemaType.KEYWORD
                        )
                except Exception:
                    pass

    def upsert_chunks(
        self,
        chunks: List[ChunkProvenance],
        vectors: List[List[float]]
    ) -> int:
        """
        Idempotently upsert chunk vectors and their rich provenance payload into Qdrant.
        """
        if not chunks or not vectors:
            return 0

        points = []
        for chunk, vector in zip(chunks, vectors):
            point_id = deterministic_point_id(chunk.chunk_id)
            payload = chunk.to_qdrant_payload()
            points.append(PointStruct(id=point_id, vector=vector, payload=payload))

        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=points,
            wait=True
        )
        return len(points)

    def delete_document_chunks(self, document_id: str) -> None:
        """Delete all vector points belonging to a specific document."""
        self.client.delete(
            collection_name=self.COLLECTION_NAME,
            points_selector=rest.FilterSelector(
                filter=Filter(
                    must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
                )
            )
        )

    def delete_workspace_chunks(self, workspace_id: str) -> None:
        """Wipe all vector points belonging to a deleted workspace."""
        self.client.delete(
            collection_name=self.COLLECTION_NAME,
            points_selector=rest.FilterSelector(
                filter=Filter(
                    must=[FieldCondition(key="workspace_id", match=MatchValue(value=workspace_id))]
                )
            )
        )

    def search(
        self,
        query_vector: List[float],
        workspace_id: str,
        allowed_classifications: List[str],
        top_k: int = 4,
        filter_document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute dense vector similarity search with strict pre-retrieval authorization filters.
        """
        must_conditions: List[rest.Condition] = [
            FieldCondition(key="workspace_id", match=MatchValue(value=workspace_id)),
            FieldCondition(key="classification", match=MatchAny(any=allowed_classifications)),
        ]

        if filter_document_id:
            must_conditions.append(
                FieldCondition(key="document_id", match=MatchValue(value=filter_document_id))
            )

        query_filter = Filter(must=must_conditions)

        # In qdrant-client >= 1.10.0, search method is query_points or search
        try:
            results = self.client.query_points(
                collection_name=self.COLLECTION_NAME,
                query=query_vector,
                query_filter=query_filter,
                limit=top_k,
                with_payload=True
            ).points
        except Exception:
            results = self.client.search(
                collection_name=self.COLLECTION_NAME,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=top_k,
                with_payload=True
            )

        formatted_results = []
        for scored_point in results:
            payload = scored_point.payload or {}
            formatted_results.append({
                "chunk_id": payload.get("chunk_id", str(scored_point.id)),
                "score": round(scored_point.score, 4),
                "content": payload.get("text", ""),
                "document_id": payload.get("document_id", ""),
                "filename": payload.get("filename", ""),
                "page_number": payload.get("page_number"),
                "section_title": payload.get("section_title"),
                "source_location": payload.get("source_location"),
                "bbox": payload.get("bbox"),
                "classification": payload.get("classification"),
                "is_table": payload.get("is_table", False),
                "token_count": payload.get("token_count", 0),
            })

        return formatted_results

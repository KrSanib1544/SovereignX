# backend/app/agent/tools/search_knowledge.py
"""
Search Knowledge Tool
Integrates directly with Phase 2B FastEmbed local embeddings and Qdrant vector retrieval.
Enforces strict workspace filtering and returns structured provenance citations.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

from backend.app.agent.tools.base import BaseTool, ToolDefinition, ToolRiskLevel
from backend.app.rag.embeddings import LocalEmbeddingEngine
from backend.app.rag.vector_store import QdrantVectorStore


class SearchCitation(BaseModel):
    citation_id: str
    document_id: str
    document_name: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    content: str
    score: float


class SearchKnowledgeInput(BaseModel):
    query: str = Field(..., description="Natural language search query")
    top_k: int = Field(4, ge=1, le=10, description="Maximum number of relevant chunks to retrieve")
    document_id: Optional[str] = Field(None, description="Optional document UUID filter")


class SearchKnowledgeOutput(BaseModel):
    query: str
    results: List[SearchCitation]
    total_found: int


class SearchKnowledgeTool(BaseTool):
    def __init__(
        self,
        embedding_engine: Optional[LocalEmbeddingEngine] = None,
        vector_store: Optional[QdrantVectorStore] = None
    ):
        self._embedding_engine = embedding_engine
        self._vector_store = vector_store

    @property
    def embedding_engine(self) -> LocalEmbeddingEngine:
        if self._embedding_engine is None:
            self._embedding_engine = LocalEmbeddingEngine.get_instance()
        return self._embedding_engine

    @property
    def vector_store(self) -> QdrantVectorStore:
        if self._vector_store is None:
            self._vector_store = QdrantVectorStore()
        return self._vector_store

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="search_knowledge",
            description="Perform semantic search over indexed engineering documents and manuals in the workspace.",
            input_schema=SearchKnowledgeInput,
            output_schema=SearchKnowledgeOutput,
            risk_level=ToolRiskLevel.LOW,
            required_permissions=["workspace:read", "rag:search"],
            requires_human_approval=False
        )

    async def execute(self, workspace_id: str, input_data: SearchKnowledgeInput) -> SearchKnowledgeOutput:
        # Generate dense embedding vector using local ONNX engine
        if hasattr(self.embedding_engine, "embed_query"):
            query_vector = self.embedding_engine.embed_query(input_data.query)
        else:
            query_vector = self.embedding_engine.embed_text(input_data.query)

        # Query vector store with mandatory workspace isolation filter
        raw_results = self.vector_store.search(
            query_vector=query_vector,
            workspace_id=workspace_id,
            top_k=input_data.top_k,
            filter_document_id=input_data.document_id
        )

        citations: List[SearchCitation] = []
        for i, hit in enumerate(raw_results, start=1):
            doc_name = hit.get("filename") or hit.get("document_name") or "Unknown Document"
            citations.append(SearchCitation(
                citation_id=f"CIT-{i:02d}",
                document_id=hit.get("document_id", ""),
                document_name=doc_name,
                page_number=hit.get("page_number"),
                section_title=hit.get("section_title"),
                content=hit.get("content", ""),
                score=round(hit.get("score", 0.0), 4)
            ))

        return SearchKnowledgeOutput(
            query=input_data.query,
            results=citations,
            total_found=len(citations)
        )

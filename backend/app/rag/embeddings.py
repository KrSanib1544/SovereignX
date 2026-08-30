# backend/app/rag/embeddings.py
"""
Local Dense Embeddings Engine
Uses FastEmbed with BAAI/bge-small-en-v1.5 running on ONNX / CPU.
Guarantees 100% offline execution and ZERO GPU VRAM consumption.
"""

from typing import List, Optional
import numpy as np
from fastembed import TextEmbedding


class LocalEmbeddingEngine:
    """
    Singleton wrapper for FastEmbed ONNX local CPU embeddings.
    """

    DEFAULT_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"
    _instance: Optional["LocalEmbeddingEngine"] = None

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME):
        self.model_name = model_name
        self._model = TextEmbedding(model_name=model_name)
        # Verify dynamic embedding dimension directly from model
        sample_vec = list(self._model.embed(["test"]))[0]
        self.dimension: int = len(sample_vec)

    @classmethod
    def get_instance(cls, model_name: str = DEFAULT_MODEL_NAME) -> "LocalEmbeddingEngine":
        """Get or initialize the shared CPU embedding engine instance."""
        if cls._instance is None or cls._instance.model_name != model_name:
            cls._instance = cls(model_name=model_name)
        return cls._instance

    def embed_query(self, query: str) -> List[float]:
        """
        Embed a single search query string into a dense unit vector.
        """
        if not query or not query.strip():
            return [0.0] * self.dimension
        embeddings = list(self._model.embed([query]))
        return [float(x) for x in embeddings[0]]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a batch of text passages into normalized dense vectors.
        """
        if not texts:
            return []
        
        # Replace empty strings with single space to avoid empty embedding issues
        safe_texts = [t if t.strip() else " " for t in texts]
        raw_embeddings = list(self._model.embed(safe_texts))
        return [[float(x) for x in vec] for vec in raw_embeddings]

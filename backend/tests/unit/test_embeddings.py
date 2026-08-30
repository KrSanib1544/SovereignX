# backend/tests/unit/test_embeddings.py
"""
Unit Tests for Local Dense Embeddings Engine (FastEmbed)
Validates model loading, vector dimensions (384-dim), determinism, and CPU execution.
"""

from backend.app.rag.embeddings import LocalEmbeddingEngine


def test_local_embedding_dimension_and_loading():
    """Test that FastEmbed loads BAAI/bge-small-en-v1.5 on CPU and returns 384-dimensional vectors."""
    engine = LocalEmbeddingEngine.get_instance()

    assert engine.dimension == 384
    assert engine.model_name == "BAAI/bge-small-en-v1.5"

    vec = engine.embed_query("Pump 3B casing ultrasonic thickness")
    assert len(vec) == 384
    assert all(isinstance(x, float) for x in vec)


def test_embedding_batch_and_determinism():
    """Test batch embedding and deterministic outputs for identical inputs."""
    engine = LocalEmbeddingEngine.get_instance()

    texts = [
        "First document paragraph regarding casing wear.",
        "Second document paragraph regarding OEM tolerances.",
        "First document paragraph regarding casing wear."
    ]

    vectors = engine.embed_documents(texts)
    assert len(vectors) == 3
    assert len(vectors[0]) == 384

    # Identical texts must produce identical embedding vectors
    for v1, v3 in zip(vectors[0], vectors[2]):
        assert abs(v1 - v3) < 1e-5

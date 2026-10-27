import pytest
from app.services.embeddings import (
    EMBEDDING_DIMENSION,
    embed_texts,
    embed_query,
    cosine_similarity,
)


def test_embed_query_returns_384_dimensions():
    vector = embed_query("How does semantic search work?")
    assert isinstance(vector, list)
    assert len(vector) == EMBEDDING_DIMENSION
    assert all(isinstance(x, float) for x in vector)


def test_embed_texts_batches_multiple_chunks():
    chunks = [
        "FastAPI is a modern web framework for building APIs with Python.",
        "SQLite is a C-language library that implements a small SQL database engine.",
    ]
    vectors = embed_texts(chunks)
    assert len(vectors) == 2
    assert len(vectors[0]) == EMBEDDING_DIMENSION
    assert len(vectors[1]) == EMBEDDING_DIMENSION


def test_semantic_similarity_ranks_meaning_over_exact_words():
    query_vec = embed_query("How can I get my money back for an order?")

    refund_chunk_vec = embed_query(
        "Customers may request a full refund within 30 days of purchase."
    )
    unrelated_chunk_vec = embed_query(
        "The database server uses Write-Ahead Logging for concurrency."
    )

    sim_relevant = cosine_similarity(query_vec, refund_chunk_vec)
    sim_unrelated = cosine_similarity(query_vec, unrelated_chunk_vec)

    print(f"\nRelevant similarity: {sim_relevant:.4f}")
    print(f"Unrelated similarity: {sim_unrelated:.4f}")

    # Even with zero overlapping keywords ("money back" vs "refund"),
    # the relevant sentence should score significantly higher!
    assert sim_relevant > sim_unrelated
    assert sim_relevant > 0.4


def test_embed_query_rejects_empty_string():
    with pytest.raises(ValueError):
        embed_query("   ")
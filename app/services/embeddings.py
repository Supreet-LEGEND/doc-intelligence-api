from functools import lru_cache
import math
from langchain_huggingface import HuggingFaceEmbeddings

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384


@lru_cache(maxsize=1)
def get_embedding_model() -> HuggingFaceEmbeddings:
    """
    Load and cache the Sentence Transformer model via LangChain.
    maxsize=1 ensures the ~80MB model is loaded into RAM only once.
    """
    return HuggingFaceEmbeddings(
        model_name=MODEL_NAME,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a batch of document chunks.
    Returns a list of 384-dimensional vectors.
    """
    if not texts:
        return []

    cleaned = [t.strip() for t in texts if t and t.strip()]
    if not cleaned:
        return []

    model = get_embedding_model()
    return model.embed_documents(cleaned)


def embed_query(query: str) -> list[float]:
    """
    Embed a single search query.
    Returns a single 384-dimensional vector.
    """
    if not query or not query.strip():
        raise ValueError("Query text cannot be empty.")

    model = get_embedding_model()
    return model.embed_query(query.strip())


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Custom implementation of cosine similarity between two vectors.
    Helps verify how vector search works underneath FAISS.
    """
    if len(vec_a) != len(vec_b):
        raise ValueError("Vectors must have the same dimension.")

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (norm_a * norm_b)
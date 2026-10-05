import numpy as np

from app.config import settings

_model = None


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(settings.embedding_model)
    return _model


def generate_embeddings(texts: list) -> np.ndarray:
    if not texts:
        return np.zeros((0, settings.embedding_dimension), dtype=np.float32)

    model = get_model()
    vectors = model.encode(
        texts,
        batch_size=32,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return np.asarray(vectors, dtype=np.float32)


def generate_query_embedding(query: str) -> np.ndarray:
    return generate_embeddings([query])[0]
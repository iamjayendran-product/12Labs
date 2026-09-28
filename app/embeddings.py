"""Local embedding model wrapper (no API key required)."""
from functools import lru_cache

from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_model()
    return model.encode(list(texts), convert_to_numpy=True).tolist()


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]

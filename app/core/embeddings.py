from sentence_transformers import SentenceTransformer
from functools import lru_cache
from app.config import settings

@lru_cache(maxsize=1)
def get_model():
    return SentenceTransformer(settings.embedding_model)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of strings, return a list of vectors.
    """
    #load the model once and reuse it by calling get_model() function
    model = get_model()
    vectors = model.encode(texts, normalize_embeddings=True)
    return vectors.tolist()

from sentence_transformers import SentenceTransformer
from functools import lru_cache


@lru_cache(maxsize=1)
def get_model():
    return SentenceTransformer('all-MiniLM-L6-v2')


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of strings, return a list of vectors.
    """
    #load the model once and reuse it by calling get_model() function
    model = get_model()
    vectors = model.encode(texts, normalize_embeddings=True)
    return vectors.tolist()

model1 = get_model()
model2 = get_model()
print(model1 is model2)   # should print True
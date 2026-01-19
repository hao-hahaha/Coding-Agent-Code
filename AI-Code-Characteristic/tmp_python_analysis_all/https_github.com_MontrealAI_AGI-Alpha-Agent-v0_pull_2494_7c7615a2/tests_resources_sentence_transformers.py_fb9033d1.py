class SentenceTransformer:
    def __init__(self, *a, **k):
        pass

    def encode(self, texts, normalize_embeddings=True):
        import numpy as np

        return np.zeros((len(texts), 384), dtype="float32")

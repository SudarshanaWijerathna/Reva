import numpy as np

def cosine_similarity(a, b):
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)

class SimilarityEngine:
    def __init__(self, vector_repo):
        self.vector_repo = vector_repo

    def compute_similarity(self, text_embedding):
        raw_embeddings = self.vector_repo.get_all_embeddings()
        if raw_embeddings is None:
            # No references yet, so we default to zero similarity.
            return 0.0, 0.0

        if len(raw_embeddings) == 0:
            return 0.0, 0.0

        all_embeddings = [np.array(e) for e in raw_embeddings]
        scores = [cosine_similarity(text_embedding, e) for e in all_embeddings]
        if not scores:
            return 0.0, 0.0

        return max(scores), float(np.mean(scores))

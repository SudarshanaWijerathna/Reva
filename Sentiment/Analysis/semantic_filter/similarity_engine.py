import numpy as np
from Analysis.storage.vector import VectorRepo

def cosine_similarity(a, b):
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)

class SimilarityEngine:
    def __init__(self):
        self.vector_repo = VectorRepo()

    def compute_similarity(self, text_embedding):
        raw_embeddings = self.vector_repo.get_all_embeddings()
        count = self.vector_repo.count()
        print(f"Retrieved {len(raw_embeddings)} reference embeddings for similarity computation.✅✅✅ AND THE CPUNT IS {count}")

        if raw_embeddings is None:
            # No references yet, so we default to zero similarity.
            print("No reference embeddings found. Returning zero similarity.✅✅✅")
            return 0.0, 0.0

        if len(raw_embeddings) == 0:
            print("Reference embeddings list is empty. Returning zero similarity.✅✅✅")
            return 0.0, 0.0

        all_embeddings = [np.array(e) for e in raw_embeddings]
        print(f"Converted reference embeddings to numpy arrays. Total: {len(all_embeddings)}✅✅✅")

        scores = [cosine_similarity(text_embedding, e) for e in all_embeddings]
        if not scores:
            print("No similarity scores computed. Returning zero similarity.✅✅✅")
            return 0.0, 0.0

        return max(scores), float(np.mean(scores))

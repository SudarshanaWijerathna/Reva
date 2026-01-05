import numpy as np
from Analysis.storage.vector import VectorRepo

def cosine_similarity(a, b):
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)

class SimilarityEngine:
    def __init__(self):
        self.vector_repo = VectorRepo("reference_vectors")
        self.short_repo = VectorRepo("short_term_vectors")
        self.medium_repo = VectorRepo("medium_term_vectors")
        self.long_repo = VectorRepo("long_term_vectors")
    

        
    def compute_similarity(self, text_embedding):
 
        results = {}

        # Map of collection names to VectorRepo objects
        collections = {
            "ref": self.vector_repo,
            "short": self.short_repo,
            "medium": self.medium_repo,
            "long": self.long_repo,
        }

        for name, repo in collections.items():
            raw_embeddings = repo.get_all_embeddings()

            # Safe checks: None or empty
            if raw_embeddings is None or len(raw_embeddings) == 0:  # covers None or empty list
                results[name] = 0.0
                continue

            # Convert to numpy arrays
            all_embeddings = [np.array(e) for e in raw_embeddings]

            # Compute cosine similarity safely
            scores = [cosine_similarity(text_embedding, e) for e in all_embeddings]

            if not scores:
                print(f"No similarity scores computed for {name}. Returning zero.✅✅✅")
                results[name] = 0.0
            else:
                results[name] = max(scores)

        return results


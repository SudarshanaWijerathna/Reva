from Analysis.semantic_filter.embedder import Embedder
from Analysis.semantic_filter.similarity_engine import SimilarityEngine
from Analysis.semantic_filter.threshold import NOISE_THRESHOLD, RELEVANT_THRESHOLD

class FilterService:
    def __init__(self, vector_repo):
        self.embedder = Embedder()
        self.sim_engine = SimilarityEngine(vector_repo)

    def evaluate_document(self, doc):
        emb = self.embedder.embed(doc["cleaned_text"])
        max_sim, mean_sim = self.sim_engine.compute_similarity(emb)
        doc["similarity"] = max_sim
        doc["relevance"] = "relevant" if max_sim >= RELEVANT_THRESHOLD else "noise" if max_sim <= NOISE_THRESHOLD else "maybe"
        return doc

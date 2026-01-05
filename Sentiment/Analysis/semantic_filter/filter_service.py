from Analysis.semantic_filter.embedder import Embedder
from Analysis.semantic_filter.similarity_engine import SimilarityEngine
from Analysis.semantic_filter.threshold import NOISE_THRESHOLD, RELEVANT_THRESHOLD

class FilterService:
    def __init__(self): #(self, vector_repo):
        self.embedder = Embedder()
        self.sim_engine = SimilarityEngine() #(vector_repo)

    def evaluate_document(self, doc):
        emb = self.embedder.embed(doc["cleaned_text"])
        sim_scores = self.sim_engine.compute_similarity(emb)

        # Noise / relevance logic based on reference repo
        ref_max = sim_scores["ref"]
        if ref_max < NOISE_THRESHOLD:
            relevance = "noise"
        elif ref_max >= RELEVANT_THRESHOLD:
            relevance = "relevant"
        else:
            relevance = "uncertain"

        return {
            "similarity_ref": sim_scores["ref"],
            "similarity_short": sim_scores["short"],
            "similarity_medium": sim_scores["medium"],
            "similarity_long": sim_scores["long"],
            "relevance": relevance
        }

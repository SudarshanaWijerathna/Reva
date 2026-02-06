from Sentiment.Analysis.storage.store import SentimentStorage
from Sentiment.Analysis.semantic_filter.filter_service import FilterService


class SemanticPipeline:
    def __init__(self, sentiment_repo: SentimentStorage | None = None, filter_service: FilterService | None = None) -> None:
        self.sentiment_repo = sentiment_repo or SentimentStorage()
        # vector_repo = VectorRepo() can be injected once needed by FilterService.
        self.filter_service = filter_service or FilterService()

    def run_semantic_pipeline(self) -> None:
        docs = self.sentiment_repo.fetch_all_docs()
        print(f"Fetched ✅✅✅{len(docs)} documents for evaluation.")
        for doc in docs:
            scores = self.filter_service.evaluate_document(doc)
            self.sentiment_repo.update_doc_similarity(doc["_id"], scores)



from Analysis.storage.store import SentimentStorage
from Analysis.storage.vector import VectorRepo
from Analysis.semantic_filter.filter_service import FilterService

def run_pipeline():
    # Initialize repos
    sentiment_repo = SentimentStorage()
    #vector_repo = VectorRepo()
    filter_service = FilterService() #-> (vector_repo)

    # Fetch documents
    docs = sentiment_repo.fetch_all_docs()
    print(f"Fetched ✅✅✅{len(docs)} documents for evaluation.")

    # Evaluate each document
    for doc in docs:
        scores = filter_service.evaluate_document(doc)
        sentiment_repo.update_doc_similarity(doc["_id"], scores)

run_pipeline()

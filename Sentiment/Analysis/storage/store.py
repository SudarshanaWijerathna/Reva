from Analysis.database import Sentiment_collection
from datetime import datetime

class SentimentStorage:
    def __init__(self):
        self.db_collection = Sentiment_collection

    def store_sentiment_results(self, results: list):
        """
        Store sentiment analysis results into the database.
        Each result in the list should be a dictionary containing:
        - raw_article
        - title
        - description
        - content
        - cleaned_text
        - predictions
        """
        docs = [res if isinstance(res, dict) else dict(res) for res in results]

        # Insert into MongoDB
        self.db_collection.insert_many(docs)
        print(f"{len(docs)} documents inserted into MongoDB.")
        
    
    def fetch_all_docs(self):
        return list(self.db_collection.find({}))
    
    def update_doc_similarity(self, doc_id,scores_dict):
        self.db_collection.update_one(
            {"_id": doc_id},
            {"$set": scores_dict},
        )
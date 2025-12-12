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
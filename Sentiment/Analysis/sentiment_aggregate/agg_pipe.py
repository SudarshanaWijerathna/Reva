from datetime import datetime, timedelta, timezone
from Sentiment.Analysis.sentiment_aggregate.aggregator import MarketSentimentAggregator
from Sentiment.Analysis.storage.store import SentimentStorage
from functools import lru_cache, cache

#Aggregator without Cache
repo = SentimentStorage()


def get_market_sentiment():

    five_years_ago = datetime.now(timezone.utc) - timedelta(days=2)

    docs = repo.fetch_relevant_docs(five_years_ago)
    aggregator = MarketSentimentAggregator(docs)
    market_sentiment = aggregator.aggregate()
    
    return market_sentiment


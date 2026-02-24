from Sentiment.Analysis.sentiment_aggregate.aggregator import MarketSentimentAggregator
from Sentiment.Analysis.storage.store import SentimentStorage
from functools import lru_cache, cache

#Aggregator without Cache
repo = SentimentStorage()

@cache
def get_market_sentiment():

    docs = repo.fetch_relevant_docs()
    aggregator = MarketSentimentAggregator(docs)
    market_sentiment = aggregator.aggregate()
    
    return market_sentiment
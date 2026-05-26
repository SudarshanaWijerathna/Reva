from Sentiment.Analysis.sentiment_aggregate.aggregator import MarketSentimentAggregator
from Sentiment.Analysis.storage.store import SentimentStorage

#Aggregator without Cache
repo = SentimentStorage()


def get_market_sentiment():
    docs = repo.fetch_relevant_docs()
    print(f"Fetched {len(docs)} noise documents for sentiment aggregation.")
    aggregator = MarketSentimentAggregator(docs)
    market_sentiment = aggregator.aggregate()
    
    return market_sentiment


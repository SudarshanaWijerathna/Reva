from Analysis.sentiment_aggregate.aggregator import MarketSentimentAggregator
from Analysis.storage.store import SentimentStorage

repo = SentimentStorage()
docs = repo.fetch_relevant_docs()
print(f"Fetched {len(docs)} relevant documents for aggregation.")

aggregator = MarketSentimentAggregator(docs)
market_sentiment = aggregator.aggregate()

print(market_sentiment)

from Analysis.sentiment_aggregate.aggregator import MarketSentimentAggregator
from Analysis.sentiment_aggregate.state_cache import AggregatorService
from Analysis.storage.store import SentimentStorage

#Aggregator without Cache
repo = SentimentStorage()
docs = repo.fetch_relevant_docs()
print(f"Fetched {len(docs)} relevant documents for aggregation.")

aggregator = MarketSentimentAggregator(docs)
market_sentiment = aggregator.aggregate()

print(market_sentiment)


# there is a prblame with a catche implementation in state_cache.py. Individually other 2 piplines works perfectly

#Aggregator with Cache
'''repo = SentimentStorage()
docs = repo.fetch_relevant_docs()
print(f"Fetched {len(docs)} relevant documents for aggregation.")

service = AggregatorService(ttl_seconds=300)
market_sentiment = service.get_market_state(docs)

print(market_sentiment)'''
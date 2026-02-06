import time
from typing import Optional
from Sentiment.Analysis.sentiment_aggregate.state_cache import MarketStateCache
from Sentiment.Analysis.sentiment_aggregate.aggregator import MarketSentimentAggregator

class MarketStateCache:
    def __init__(self, ttl_seconds: int = 300):
        """
        ttl_seconds:
        - Short-term systems: 300–900 seconds
        - Medium-term: hours
        - Long-term: days
        """
        self.ttl = ttl_seconds
        self._cached_value: Optional[dict] = None
        self._last_updated: float = 0.0

    def is_valid(self) -> bool:
        if self._cached_value is None:
            return False
        return (time.time() - self._last_updated) < self.ttl

    def get(self) -> Optional[dict]:
        if self.is_valid():
            return self._cached_value
        return None

    def set(self, value: dict):
        self._cached_value = value
        self._last_updated = time.time()

    def invalidate(self):
        self._cached_value = None
        self._last_updated = 0.0




class AggregatorService:
    def __init__(self, ttl_seconds: int = 300):
        self.cache = MarketStateCache(ttl_seconds)

    def get_market_state(self, documents: list[dict]) -> dict:
        cached = self.cache.get()
        if cached:
            return cached
        print("Cache miss or expired. Recomputing market state...")

        aggregator = MarketSentimentAggregator(documents)
        state = aggregator.aggregate()

        self.cache.set(state)
        return state


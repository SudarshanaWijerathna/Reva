from Analysis.sentiment_aggregate.sentiment_utils import SentimentUtils
from Analysis.sentiment_aggregate.thresholds import SentimentThresholds


class MarketSentimentAggregator:
    def __init__(self, documents: list[dict]):
        """
        documents: list of MongoDB documents
        (already filtered by relevance == 'relevant')
        """
        self.documents = documents

    def _compute_horizon_score(self, horizon_key: str) -> float:
        """
        horizon_key: similarity_short | similarity_medium | similarity_long
        """
        if not self.documents:
            return 0.0

        total = 0.0
        count = 0

        for doc in self.documents:
            predictions = doc.get("predictions", [])
            if not predictions:
                continue

            sentiment_label = predictions[0].get("label", "neutral")
            sentiment_score = predictions[0].get("score", 0.0)
            

            sign = SentimentUtils.label_to_sign(sentiment_label)
            similarity = doc.get(horizon_key, 0.0)

            impact = similarity * sentiment_score * sign * 10
            total += impact
            count += 1

        if count == 0:
            return 0.0

        return total / count

    def aggregate(self) -> dict:
        short_value = self._compute_horizon_score("similarity_short")
        medium_value = self._compute_horizon_score("similarity_medium")
        long_value = self._compute_horizon_score("similarity_long")

        return {
            "short_term": {
                "value": round(short_value, 4),
                "label": SentimentThresholds.classify(short_value),
            },
            "medium_term": {
                "value": round(medium_value, 4),
                "label": SentimentThresholds.classify(medium_value),
            },
            "long_term": {
                "value": round(long_value, 4),
                "label": SentimentThresholds.classify(long_value),
            },
        }

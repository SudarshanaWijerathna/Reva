from Sentiment.Analysis.sentiment_aggregate.sentiment_utils import SentimentUtils
from Sentiment.Analysis.sentiment_aggregate.thresholds import SentimentThresholds


class MarketSentimentAggregator:
    # Document type weights
    TYPE_WEIGHTS = {
        "news_scraper": 0.5,
        "web_scraper": 0.3,
        "api_article": 0.2,
    }

    def __init__(self, documents: list[dict]):
        """
        documents: list of MongoDB documents
        (already filtered by relevance == 'relevant')
        """
        self.documents = documents

    def _get_weight_for_type(self, doc_type: str) -> float:
        """Get weight based on document type"""
        return self.TYPE_WEIGHTS.get(doc_type, 0.0)

    def _compute_horizon_score(self) -> float:
        """
        Compute sentiment score based on document type weights
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
            doc_type = doc.get("type", "")
            weight = self._get_weight_for_type(doc_type)

            impact = weight * sentiment_score * sign * 10
            total += impact
            count += 1

        if count == 0:
            return 0.0

        return total / count

    def aggregate(self) -> dict:
        sentiment_value = self._compute_horizon_score()

        return {
            "short_term": {
                "value": round(sentiment_value, 4),
                "label": SentimentThresholds.classify(sentiment_value),
            },
            "medium_term": {
                "value": round(sentiment_value, 4),
                "label": SentimentThresholds.classify(sentiment_value),
            },
            "long_term": {
                "value": round(sentiment_value, 4),
                "label": SentimentThresholds.classify(sentiment_value),
            },
        }

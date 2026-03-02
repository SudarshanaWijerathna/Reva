from Sentiment.Analysis.sentiment_aggregate.sentiment_utils import SentimentUtils
from Sentiment.Analysis.sentiment_aggregate.thresholds import SentimentThresholds
from datetime import datetime
import math

class MarketSentimentAggregator:
    # Document type weights
    TYPE_WEIGHTS = {
        "news_scraper": 0.5,
        "web_scraper": 0.3,
        "api_article": 0.2,
    }

    # Decay rates per time horizon
    DECAY_RATES = {
        "short": 0.15,
        "medium": 0.03,
        "long": 0.005
    }

    # Hard window limits (days)
    WINDOW_LIMITS = {
        "short": 30,
        "medium": 365,
        "long": 365 * 5
    }

    def __init__(self, documents: list[dict]):
        """
        documents: list of MongoDB documents
        (already filtered by relevance == 'relevant')
        """
        self.documents = documents

    def _compute_time_decay(self, doc_timestamp, horizon: str) -> float:
        """
        Compute exponential decay weight based on document age.
        """
        if not doc_timestamp:
            return 0.0

        now = datetime.utcnow()
        age_days = (now - doc_timestamp).days

        # Hard window cutoff
        if age_days > self.WINDOW_LIMITS[horizon]:
            return 0.0

        lambda_value = self.DECAY_RATES[horizon]
        return math.exp(-lambda_value * age_days)
    

    def _get_weight_for_type(self, doc_type: str) -> float:
        """Get weight based on document type"""
        return self.TYPE_WEIGHTS.get(doc_type, 0.0)

    def _compute_sentiment_for_property_and_horizon(self, property_type: str, time_horizon: str) -> float:
        """
        Compute sentiment score for a specific property type and time horizon
        Only includes documents where the property type has the highest similarity score
        property_type: 'land', 'house', 'rental'
        time_horizon: 'short', 'medium', 'long'
        """
        time_similarity_key = f"similarity_{time_horizon}"
        
        if not self.documents:
            return 0.0

        total = 0.0
        count = 0

        for doc in self.documents:
            # Determine dominant property type based on highest similarity
            land_similarity = doc.get("similarity_land", 0.0)
            house_similarity = doc.get("similarity_house", 0.0)
            rental_similarity = doc.get("similarity_rental", 0.0)
            
            property_similarities = {
                "land": land_similarity,
                "house": house_similarity,
                "rental": rental_similarity
            }
            
            # Find the property type with highest similarity
            dominant_property = max(property_similarities, key=property_similarities.get)
            
            # Only process this document if it matches the target property type
            if dominant_property != property_type:
                continue
            
            predictions = doc.get("predictions", [])
            if not predictions:
                continue

            sentiment_label = predictions[0].get("label", "neutral")
            sentiment_score = predictions[0].get("score", 0.0)
            
            sign = SentimentUtils.label_to_sign(sentiment_label)
            doc_type = doc.get("type", "")
            weight = self._get_weight_for_type(doc_type)
            doc_timestamp = doc.get("timestamp")
            time_decay = self._compute_time_decay(doc_timestamp, time_horizon)
            
            # Get time horizon relevance score
            time_relevance = doc.get(time_similarity_key, 0.0)
            
            impact = weight * sentiment_score * sign * time_relevance * time_decay * 100
            total += impact
            count += 1

        if count == 0:
            return 0.0

        return total / count

    def aggregate(self) -> dict:
        property_types = {
            "land": "land",
            "house": "housing",
            "rental": "rental"
        }
        time_horizons = ["short", "medium", "long"]
        
        result = {}
        
        for similarity_key, output_key in property_types.items():
            result[output_key] = {}
            for horizon in time_horizons:
                sentiment_value = self._compute_sentiment_for_property_and_horizon(similarity_key, horizon)
                result[output_key][f"{horizon}_term"] = {
                    "value": round(sentiment_value, 4),
                    "label": SentimentThresholds.classify(sentiment_value),
                }
        
        return result

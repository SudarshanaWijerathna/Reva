class SentimentThresholds:
    BULLISH = 0.2
    BEARISH = -0.2

    @staticmethod
    def classify(value: float) -> str:
        if value >= SentimentThresholds.BULLISH:
            return "bullish"
        if value <= SentimentThresholds.BEARISH:
            return "bearish"
        return "neutral"

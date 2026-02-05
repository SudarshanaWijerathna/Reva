class SentimentUtils:
    @staticmethod
    def label_to_sign(label: str) -> int:
        label = label.lower()
        if label == "positive":
            return 1
        if label == "negative":
            return -1
        return 0  # neutral

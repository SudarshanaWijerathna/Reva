from functools import lru_cache, cache
from Sentiment.Analysis.sentiment_aggregate.agg_pipe import get_market_sentiment

def get_overall_sentiment(data: dict):
    properties = ["land", "housing", "rental"]
    result = 0
    for prop in properties:
        result += data[prop]["medium_term"]["value"]
    average_sentiment = result / (len(properties))
    if average_sentiment >= 0.5:
        average_sentiment_label = "positive"
    else:
        average_sentiment_label = "negative"
    return average_sentiment_label


def get_sentiment(data: dict, property_type: str, term: str):
    try:
        result = data[property_type][term]
        return {
            "value": result["value"],
            "label": result["label"]
        }
    except KeyError:
        return {"error": "Invalid property type or term"}
    





    


    
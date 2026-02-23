from Sentiment.Analysis.sentiment_aggregate.agg_pipe import get_market_sentiment

def get_overall_sentiment():
    data = get_market_sentiment()
    properties = ["land", "housing", "rental"]
    result = 0
    for prop in properties:
        result += data[prop]["medium_term"]["value"]
    average_sentiment = result / (len(properties))
    return average_sentiment


def get_sentiment(property_type: str, term: str):
    try:
        data = get_market_sentiment()
        result = data[property_type][term]
        return {
            "value": result["value"],
            "label": result["label"]
        }
    except KeyError:
        return {"error": "Invalid property type or term"}
    


    
from backend.core.cache_service import get_future_predictions, get_current_prices

def lstm_next_close(property_type):
    predictions = get_future_predictions()
    if not predictions:
        return {"error": "No predictions available"}
    if property_type == "land":
        return {"next_close": predictions["land"]["next_close"]}
    elif property_type == "housing":
        return {"next_close": predictions["housing"]["next_close"]}
    elif property_type == "rental":
        return {"next_close": predictions["rental"]["next_close"]}
    else:
        return {"error": "Invalid property type"}
def lstm_future_sequence(property_type, steps=None):
    predictions = get_future_predictions()
    if not predictions:
        return {"error": "No predictions available"}
    if property_type == "land":
        return {"sequence": predictions["land"]["next_5_close"][:steps]}
    elif property_type == "housing":
        return {"sequence": predictions["housing"]["next_5_close"][:steps]}
    elif property_type == "rental":
        return {"sequence": predictions["rental"]["next_5_close"][:steps]}
    else:
        return {"error": "Invalid property type"}

def current_price(property_type,city):
    prices = get_current_prices()
    city=city.lower()
    if not prices:
        return {"error": "No current prices available"}
    if property_type == "land":
        return {f"current_price for the {city}": prices["lands"].get(city, "City not found")}
    elif property_type == "housing":
        return {f"current_price for the {city}": prices["sales"].get(city, "City not found")}
    elif property_type == "rental":
        return {f"current_price for the {city}": prices["rentals"].get(city, "City not found")}




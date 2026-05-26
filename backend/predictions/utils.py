from backend.core.cache_service import get_current_prices
def get_current_market_price(property_type: str, location: str) -> float:

    current_prices = get_current_prices()
    #print(result_custom.get("sales", {}).get("kandy", "N/A"), "Kandy Sale Price")
    #print(result_custom.get("sales", {}).get("national average", "N/A"), "National Average Sale Price")
    #print(result_custom.get("rentals", {}).get("national average", "N/A"), "National Average Rental Price")
    #print(result_custom.get("lands", {}).get("national average", "N/A"), "National Average Land Price")
    # housing | rental | land
     
    if property_type == "housing":
        val = current_prices.get("sales", {}).get(location, 0.0)
        if val == 0.0:
            val = current_prices.get("sales", {}).get("national average", 0.0)
        return val

    elif property_type == "rental":
        val = current_prices.get("rentals", {}).get(location, 0.0)
        if val == 0.0:
            val = current_prices.get("rentals", {}).get("national average", 0.0)
        return val
    elif property_type == "land":
        val = current_prices.get("lands", {}).get(location, 0.0)
        if val == 0.0:
            val = current_prices.get("lands", {}).get("national average", 0.0)
        return val
    else:
        return current_prices.get("sales", {}).get("national average", "N/A") # Unknown property type,
    

def generate_insight(summary):
    growth = summary.get("growth_percentage", 0)
    sentiment = (summary.get("sentiment") or "unknown").lower()

    if growth > 10 and sentiment == "bullish":
        return "Your portfolio is growing strongly, and current market sentiment is bullish."
    if sentiment == "bearish":
        return "Market sentiment is bearish right now, so it may be a good time to review risk exposure across your properties."
    if sentiment == "neutral":
        return "Market sentiment is neutral at the moment, so portfolio performance will depend more on asset quality and location."
    if growth > 10:
        return "Your portfolio is growing strongly with positive market momentum."
    return "Your portfolio is stable but has room for growth."

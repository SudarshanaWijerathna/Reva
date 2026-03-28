def get_current_market_price(prop):
    # Placeholder for ML model
    #return property.purchase_price * 1.2
    return 100.0

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

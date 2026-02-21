def get_current_market_price(prop):
    # Placeholder for ML model
    #return property.purchase_price * 1.2
    return 100.0

def generate_insight(summary):
    if summary["growth_percentage"] > 10:
        return "Your portfolio is growing strongly with positive market momentum."
    return "Your portfolio is stable but has room for growth."
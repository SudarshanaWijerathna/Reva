# scrapers/trends_scraper.py

from pytrends.request import TrendReq
from datetime import datetime

def fetch_sri_lanka_trends(keywords=None):
    """
    Fetch Google Trends interest for keywords in Sri Lanka (last 1h or 1d).
    Returns simulated or real trend scores (0–100).
    """
    if keywords is None:
        keywords = ["Artificial Intelligeence"]
    
    try:
        # Connect to Google Trends
        pytrend = TrendReq()
        pytrend.build_payload(
            kw_list=keywords[:1],  # Google Trends allows 1 keyword per request for real-time
            geo='US',              # Sri Lanka
            timeframe='today 1-d'    # Last hour (real-time)
        )
        interest = pytrend.interest_over_time()
        if not interest.empty:
            score = int(interest[keywords[0]].iloc[-1])
            return {
                "title": f"Google Trends: '{keywords[0]}' interest = {score}/100 in Sri Lanka",
                "url": "https://trends.google.com",
                "timestamp": datetime.now().isoformat(),
                "source": "Google Trends"
            }
    except Exception as e:
        print(f"⚠️  Google Trends failed (using simulated): {e}")
        # Fallback to simulated realistic score
        from random import choice
        keyword = keywords[0]
        score = choice([10, 35, 75, 90])  # Simulate low to spiking
        return {
            "title": f"Google Trends (Simulated): '{keyword}' interest = {score}/100 in Sri Lanka",
            "url": "https://trends.google.com",
            "timestamp": datetime.now().isoformat(),
            "source": "Google Trends (Simulated)"
        }

print(fetch_sri_lanka_trends())
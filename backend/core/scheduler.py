from apscheduler.schedulers.background import BackgroundScheduler
from backend.core.cache_service import update_sentiment_cache


scheduler = BackgroundScheduler()

def start_scheduler():
    scheduler.add_job(update_sentiment_cache, "interval", minutes=5)
    scheduler.start()

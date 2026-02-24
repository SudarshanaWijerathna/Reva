from apscheduler.schedulers.background import BackgroundScheduler
from backend.core.cache_service import update_sentiment_cache
from Sentiment.Analysis.run_both import run_both_pipelines


scheduler = BackgroundScheduler()

def start_scheduler():
    scheduler.add_job(update_sentiment_cache, "interval", minutes=5)
    scheduler.add_job(run_both_pipelines, "interval", days=7)
    scheduler.start()

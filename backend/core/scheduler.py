from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from backend.core.cache_service import update_sentiment_cache
from Sentiment.Analysis.run_both import run_both_pipelines


scheduler = BackgroundScheduler()

def start_scheduler():
    scheduler.add_job(update_sentiment_cache, "interval", minutes=15, next_run_time=datetime.now(timezone.utc) + timedelta(minutes=15))  # Update cache every 5 minutes
    scheduler.add_job(run_both_pipelines, "interval", days=7, next_run_time=datetime.now(timezone.utc) + timedelta(days=7))
    scheduler.start()

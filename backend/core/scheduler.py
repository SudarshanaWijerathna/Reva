from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from backend.core.cache_service import update_sentiment_cache
from Sentiment.Analysis.run_both import run_both_pipelines


scheduler = BackgroundScheduler()


def snapshot_all_active_portfolios():
    from backend.database.database import SessionLocal
    from backend.database.schemas import Property
    from backend.portfolio.service import snapshot_portfolio
    from sqlalchemy import func, or_

    db = SessionLocal()
    try:
        user_ids = [row[0] for row in db.query(Property.user_id).filter(
            or_(Property.status.is_(None), func.lower(Property.status) != "sold")
        ).distinct().all()]
        for user_id in user_ids:
            snapshot_portfolio(db, user_id)
    finally:
        db.close()

def start_scheduler():
    scheduler.add_job(update_sentiment_cache, "interval", days=1, next_run_time=datetime.now(timezone.utc) + timedelta(minutes=15))  # Update cache every 5 minutes
    scheduler.add_job(run_both_pipelines, "interval", days=1, next_run_time=datetime.now(timezone.utc) + timedelta(days=7))
    scheduler.add_job(
        snapshot_all_active_portfolios,
        "cron",
        month="3,6,9,12",
        day="last",
        hour=23,
        minute=30,
        id="quarterly_portfolio_snapshots",
        replace_existing=True,
    )
    scheduler.start()

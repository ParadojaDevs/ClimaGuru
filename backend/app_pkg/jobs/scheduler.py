"""APScheduler-based background scheduler."""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.ingestion_service import WeatherIngestionService

logger = logging.getLogger(__name__)
svc = WeatherIngestionService()


def run_all_ingest():
    try:
        results = svc.ingest_all()
        logger.info(f"Scheduled ingest completed: {len(results)} sources")
    except Exception as e:
        logger.error(f"Scheduled ingest error: {e}")


class JobScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler(daemon=True)
        self._configured = False

    def start(self):
        if not self._configured:
            # Default: run every 6 hours
            self.scheduler.add_job(run_all_ingest, 'interval', hours=6, id='ingest_all')
            self._configured = True
        self.scheduler.start()
        logger.info("Background job scheduler started")

    def shutdown(self):
        self.scheduler.shutdown()

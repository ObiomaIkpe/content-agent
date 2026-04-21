import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from aggregator import collect_snapshot, save_snapshot, flush_retry_queue
from logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

scheduler = BlockingScheduler(timezone="Africa/Lagos")


@scheduler.scheduled_job("interval", hours=3, id="snapshot_job")
def run_snapshot():
    logger.info("Running 3-hour snapshot...")
    flush_retry_queue()
    snapshot = collect_snapshot(hours=3)
    save_snapshot(snapshot)
    logger.info("Snapshot complete.")


if __name__ == "__main__":
    logger.info("Scheduler started. Running every 3 hours.")
    logger.info("First snapshot will run at the next 3-hour mark.")
    scheduler.start()
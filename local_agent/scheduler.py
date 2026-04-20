import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
from aggregator import collect_snapshot, save_snapshot, flush_retry_queue

scheduler = BlockingScheduler(timezone="Africa/Lagos")


@scheduler.scheduled_job("interval", hours=3, id="snapshot_job")
def run_snapshot():
    print(f"[{datetime.now()}] Running 3-hour snapshot...")
    flush_retry_queue()
    snapshot = collect_snapshot(hours=3)
    save_snapshot(snapshot)
    print(f"[{datetime.now()}] Snapshot complete.")


if __name__ == "__main__":
    print("Scheduler started. Running every 3 hours.")
    print("First snapshot will run at the next 3-hour mark.")
    print("Press Ctrl+C to stop.")
    scheduler.start()
import os
import json
import logging
import httpx
from datetime import datetime, timezone
from dotenv import load_dotenv

from claude_logs import collect_claude_logs
from github_collector import collect_github
from activitywatch_collector import collect_activitywatch
from git_diff_collector import collect_git_diffs

load_dotenv()

logger = logging.getLogger(__name__)

SNAPSHOTS_DIR = os.path.join(os.path.dirname(__file__), "..", "snapshots")
RETRY_QUEUE_FILE = os.path.join(SNAPSHOTS_DIR, "retry_queue.json")
SNAPSHOT_RECEIVER_URL = os.getenv("SNAPSHOT_RECEIVER_URL", "")
SNAPSHOT_API_SECRET = os.getenv("SNAPSHOT_API_SECRET", "")


def collect_snapshot(hours: int = 3) -> dict:
    logger.info("Collecting Claude Code logs...")
    claude = collect_claude_logs(hours=hours)

    logger.info("Collecting GitHub activity...")
    github = collect_github(hours=hours)

    logger.info("Collecting ActivityWatch data...")
    aw = collect_activitywatch(hours=hours)

    logger.info("Collecting local git diffs...")
    git_diffs = collect_git_diffs(hours=hours, claude_sessions=claude, activitywatch=aw)

    snapshot = {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "window_hours": hours,
        "claude_sessions": claude,
        "github": github,
        "activitywatch": aw,
        "git_diffs": git_diffs,
    }

    return snapshot


def _push_snapshot(snapshot: dict) -> bool:
    """Try to POST a snapshot to Hetzner. Returns True on success."""
    try:
        headers = {"x-api-secret": SNAPSHOT_API_SECRET} if SNAPSHOT_API_SECRET else {}
        httpx.post(SNAPSHOT_RECEIVER_URL, json=snapshot, headers=headers, timeout=15)
        return True
    except Exception as e:
        logger.warning("Push failed: %s", e)
        return False


def _load_retry_queue() -> list[dict]:
    if not os.path.exists(RETRY_QUEUE_FILE):
        return []
    try:
        with open(RETRY_QUEUE_FILE) as f:
            return json.load(f)
    except Exception:
        return []


def _save_retry_queue(queue: list[dict]):
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
    with open(RETRY_QUEUE_FILE, "w") as f:
        json.dump(queue, f)


def flush_retry_queue():
    """Try to push any previously failed snapshots. Called before each collection."""
    if not SNAPSHOT_RECEIVER_URL:
        return
    queue = _load_retry_queue()
    if not queue:
        return

    logger.info("Retrying %d queued snapshot(s)...", len(queue))
    remaining = []
    for snapshot in queue:
        if _push_snapshot(snapshot):
            logger.info("Queued snapshot pushed: %s", snapshot.get("collected_at"))
        else:
            remaining.append(snapshot)

    _save_retry_queue(remaining)
    if remaining:
        logger.warning("%d snapshot(s) still pending after retry.", len(remaining))


def save_snapshot(snapshot: dict) -> str:
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
    filename = f"snapshot_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(SNAPSHOTS_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(snapshot, f, indent=2)
    logger.info("Snapshot saved: %s", filepath)

    if SNAPSHOT_RECEIVER_URL:
        if _push_snapshot(snapshot):
            logger.info("Snapshot pushed to %s", SNAPSHOT_RECEIVER_URL)
        else:
            queue = _load_retry_queue()
            queue.append(snapshot)
            _save_retry_queue(queue)
            logger.warning("Push failed — snapshot added to retry queue.")

    return filepath


if __name__ == "__main__":
    snapshot = collect_snapshot(hours=3)
    save_snapshot(snapshot)
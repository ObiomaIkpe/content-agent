import json
import os
from datetime import datetime, timedelta
from pathlib import Path

HISTORY_FILE = Path(__file__).parent / "snapshots" / "content_history.json"
KEEP_DAYS = 30


def load_history() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    try:
        entries = json.loads(HISTORY_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return []
    cutoff = (datetime.utcnow() - timedelta(days=KEEP_DAYS)).isoformat()
    return [e for e in entries if e.get("posted_at", "") >= cutoff]


def save_topic(topic: str, platforms: list[str]):
    entries = load_history()
    entries.append({
        "topic": topic,
        "platforms": platforms,
        "posted_at": datetime.utcnow().isoformat(),
    })
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(entries, indent=2))

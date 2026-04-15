import os
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

from claude_logs import collect_claude_logs
from github_collector import collect_github
from activitywatch_collector import collect_activitywatch
from git_diff_collector import collect_git_diffs

load_dotenv()

SNAPSHOTS_DIR = os.path.join(os.path.dirname(__file__), "..", "snapshots")


def collect_snapshot(hours: int = 3) -> dict:
    print("Collecting Claude Code logs...")
    claude = collect_claude_logs(hours=hours)

    print("Collecting GitHub activity...")
    github = collect_github(hours=hours)

    print("Collecting ActivityWatch data...")
    aw = collect_activitywatch(hours=hours)

    print("Collecting local git diffs...")
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


def save_snapshot(snapshot: dict) -> str:
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
    filename = f"snapshot_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(SNAPSHOTS_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(snapshot, f, indent=2)
    print(f"Snapshot saved: {filepath}")
    return filepath


if __name__ == "__main__":
    snapshot = collect_snapshot(hours=3)
    save_snapshot(snapshot)
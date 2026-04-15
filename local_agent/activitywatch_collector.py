import json
import requests
from datetime import datetime, timezone, timedelta


AW_BASE = "http://localhost:5600/api/0"


def get_buckets() -> list[str]:
    r = requests.get(f"{AW_BASE}/buckets")
    return list(r.json().keys())


def get_events(bucket_id: str, hours: int = 3) -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    r = requests.get(f"{AW_BASE}/buckets/{bucket_id}/events?start={since}&limit=100")
    if r.status_code != 200:
        return []
    return r.json()


def summarize_window_activity(events: list[dict]) -> list[dict]:
    summary = {}
    for e in events:
        app = e.get("data", {}).get("app", "unknown")
        duration = e.get("duration", 0)
        summary[app] = summary.get(app, 0) + duration
    return [{"app": k, "seconds": round(v)} for k, v in sorted(summary.items(), key=lambda x: -x[1])]


def summarize_vscode_activity(events: list[dict]) -> list[dict]:
    summary = {}
    for e in events:
        data = e.get("data", {})
        file = data.get("file", "unknown")
        lang = data.get("language", "unknown")
        duration = e.get("duration", 0)
        key = f"{file} ({lang})"
        summary[key] = summary.get(key, 0) + duration
    return [{"file": k, "seconds": round(v)} for k, v in sorted(summary.items(), key=lambda x: -x[1])[:20]]


def collect_activitywatch(hours: int = 3) -> dict:
    buckets = get_buckets()
    result = {}

    for bucket in buckets:
        events = get_events(bucket, hours)
        if not events:
            continue

        if "window" in bucket:
            result["window_activity"] = summarize_window_activity(events)
        elif "vscode" in bucket:
            result["vscode_activity"] = summarize_vscode_activity(events)
        elif "afk" in bucket:
            # just count active vs afk time
            active = sum(e["duration"] for e in events if e.get("data", {}).get("status") == "not-afk")
            result["active_seconds"] = round(active)
        elif "web" in bucket:
            result["browser_activity"] = [
                {"url": e.get("data", {}).get("url", ""), "title": e.get("data", {}).get("title", ""), "seconds": round(e.get("duration", 0))}
                for e in events[:20]
            ]

    return result


if __name__ == "__main__":
    data = collect_activitywatch(hours=3)
    print(json.dumps(data, indent=2))
import os
import json
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

CLAUDE_LOGS_DIR = os.getenv("CLAUDE_LOGS_DIR")
ANONYMIZED_PROJECTS = os.getenv("ANONYMIZED_PROJECTS", "").split(",")


def should_anonymize(project_name: str) -> bool:
    return any(anon in project_name for anon in ANONYMIZED_PROJECTS)


def anonymize_branch(branch: str) -> str:
    """Strip ticket numbers, keep human-readable description."""
    parts = branch.replace("-", " ").split()
    # Remove ticket-like parts (e.g. CCB-149, ABC-123)
    cleaned = [p for p in parts if not (p.isupper() or p.isdigit())]
    return " ".join(cleaned).strip()


def parse_session(filepath: str, project_name: str, since: datetime) -> dict | None:
    messages = []
    branch = None
    cwd = None
    timestamps = []

    with open(filepath, "r") as f:
        for line in f:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts = entry.get("timestamp")
            if not ts:
                continue

            entry_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if entry_time < since:
                continue

            timestamps.append(entry_time)

            if not branch and entry.get("gitBranch"):
                branch = entry["gitBranch"]
            if not cwd and entry.get("cwd"):
                cwd = entry["cwd"]

            # Extract meaningful user messages only
            # Extract meaningful user messages only
            if entry.get("type") == "user" and not entry.get("isMeta"):
                content = entry.get("message", {}).get("content", "")
                if not isinstance(content, str):
                    continue
                content = content.strip()
                # Skip noise
                if len(content) < 15:
                    continue
                if content.startswith("<command-name>"):
                    continue
                if content.startswith("<local-command-stdout>"):
                    continue
                if content.startswith("source "):
                    continue
                messages.append(content)

    if not timestamps:
        return None

    anonymize = should_anonymize(project_name)

    return {
        "project": "anonymized" if anonymize else project_name,
        "branch": anonymize_branch(branch) if (branch and anonymize) else branch,
        "cwd": None if anonymize else cwd,
        "messages": messages[:10],  # cap at 10 messages per session
        "start_time": min(timestamps).isoformat(),
        "end_time": max(timestamps).isoformat(),
        "anonymized": anonymize,
    }


def collect_claude_logs(hours: int = 3) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    results = []

    for project_dir in os.listdir(CLAUDE_LOGS_DIR):
        project_path = os.path.join(CLAUDE_LOGS_DIR, project_dir)
        if not os.path.isdir(project_path):
            continue

        # Normalize project name from directory name
        project_name = project_dir.lstrip("-").replace("-", "/", 2).replace("-", " ")

        for filename in os.listdir(project_path):
            if not filename.endswith(".jsonl"):
                continue
            filepath = os.path.join(project_path, filename)
            session = parse_session(filepath, project_dir, since)
            if session:
                results.append(session)

    return results


if __name__ == "__main__":
    logs = collect_claude_logs(hours=3)
    print(json.dumps(logs, indent=2))

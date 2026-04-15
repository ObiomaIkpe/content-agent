import os
import subprocess
import json
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

ANONYMIZED_PROJECTS = os.getenv("ANONYMIZED_PROJECTS", "").split(",")

MAX_COMMITS_PER_REPO = 10
SMALL_DIFF_LINE_THRESHOLD = 50  # include full diff only if total changed lines <= this


def should_anonymize(repo_path: str) -> bool:
    return any(anon and anon in repo_path for anon in ANONYMIZED_PROJECTS)


def run_git(args: list[str], cwd: str) -> str:
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=15,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def find_git_root(path: str) -> str | None:
    """Walk up from path until we find a .git directory."""
    path = os.path.abspath(path)
    if os.path.isfile(path):
        path = os.path.dirname(path)
    while path != os.path.dirname(path):
        if os.path.isdir(os.path.join(path, ".git")):
            return path
        path = os.path.dirname(path)
    return None


def discover_repos(claude_sessions: list[dict], activitywatch: dict) -> set[str]:
    """Auto-discover git repo roots from Claude session cwds and ActivityWatch VSCode file paths."""
    candidates = set()

    for session in claude_sessions:
        cwd = session.get("cwd")
        if cwd:
            candidates.add(cwd)

    for entry in activitywatch.get("vscode_activity", []):
        raw = entry.get("file", "")
        file_path = raw.split(" (")[0].strip()
        if file_path and file_path != "unknown":
            candidates.add(file_path)

    roots = set()
    for candidate in candidates:
        root = find_git_root(candidate)
        if root:
            roots.add(root)

    return roots


def count_diff_lines(patch: str) -> int:
    """Count added + removed lines in a patch."""
    return sum(1 for line in patch.splitlines() if line.startswith(("+", "-")) and not line.startswith(("+++", "---")))


def get_recent_commit_hashes(repo_path: str, hours: int) -> list[str]:
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S")
    out = run_git(
        ["log", f"--since={since}", "--format=%H", f"-{MAX_COMMITS_PER_REPO}"],
        repo_path,
    )
    return [h for h in out.splitlines() if h]


def get_commit_info(repo_path: str, commit_hash: str) -> dict:
    # Metadata
    meta = run_git(["show", "--format=%s|%an|%ai", "--no-patch", commit_hash], repo_path)
    parts = meta.split("|", 2)
    message = parts[0] if len(parts) > 0 else ""
    author = parts[1] if len(parts) > 1 else ""
    timestamp = parts[2] if len(parts) > 2 else ""

    # Stat summary (always included)
    stat = run_git(["show", "--stat", "--format=", commit_hash], repo_path)

    # Full diff only for small commits
    patch = run_git(["show", "--format=", "--no-color", commit_hash], repo_path)
    line_count = count_diff_lines(patch)
    diff = patch if line_count <= SMALL_DIFF_LINE_THRESHOLD else None

    return {
        "hash": commit_hash[:10],
        "message": message,
        "author": author,
        "timestamp": timestamp,
        "stat": stat,
        "diff": diff,
    }


def collect_git_diffs(
    hours: int = 3,
    claude_sessions: list[dict] = None,
    activitywatch: dict = None,
) -> list[dict]:
    repo_roots = discover_repos(claude_sessions or [], activitywatch or {})

    if not repo_roots:
        print("No git repos discovered from activity data.")
        return []

    results = []
    for repo_path in sorted(repo_roots):
        anonymize = should_anonymize(repo_path)
        repo_name = os.path.basename(repo_path) if not anonymize else "anonymized"

        hashes = get_recent_commit_hashes(repo_path, hours)
        if not hashes:
            continue

        commits = [get_commit_info(repo_path, h) for h in hashes]

        results.append({
            "repo": repo_name,
            "repo_path": None if anonymize else repo_path,
            "commit_count": len(commits),
            "commits": commits,
        })
        print(f"  {repo_name}: {len(commits)} commit(s)")

    return results


if __name__ == "__main__":
    test_sessions = [{"cwd": os.getcwd()}]
    data = collect_git_diffs(hours=3, claude_sessions=test_sessions)
    print(json.dumps(data, indent=2))

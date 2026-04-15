import os
import json
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}


def get_recent_commits(hours: int = 3) -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    results = []

    # Get all repos for the user
    repos_url = f"https://api.github.com/users/{GITHUB_USERNAME}/repos?per_page=100&sort=pushed"
    repos = requests.get(repos_url, headers=HEADERS).json()

    for repo in repos:
        repo_name = repo["name"]
        commits_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/commits?author={GITHUB_USERNAME}&since={since}&per_page=20"
        response = requests.get(commits_url, headers=HEADERS)

        if response.status_code != 200:
            continue

        commits = response.json()
        if not isinstance(commits, list) or not commits:
            continue

        for commit in commits:
            results.append({
                "repo": repo_name,
                "message": commit["commit"]["message"],
                "timestamp": commit["commit"]["author"]["date"],
                "url": commit["html_url"],
            })

    return results


def get_recent_prs(hours: int = 3) -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    results = []

    search_url = f"https://api.github.com/search/issues?q=author:{GITHUB_USERNAME}+type:pr+updated:>{since}&per_page=20"
    response = requests.get(search_url, headers=HEADERS).json()

    for item in response.get("items", []):
        results.append({
            "repo": item["repository_url"].split("/")[-1],
            "title": item["title"],
            "state": item["state"],
            "url": item["html_url"],
            "updated_at": item["updated_at"],
        })

    return results


def collect_github(hours: int = 3) -> dict:
    return {
        "commits": get_recent_commits(hours),
        "pull_requests": get_recent_prs(hours),
    }


if __name__ == "__main__":
    data = collect_github(hours=999)
    print(json.dumps(data, indent=2))
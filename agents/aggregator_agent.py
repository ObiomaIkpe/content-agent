import os
import json
from pathlib import Path
from dotenv import load_dotenv
from crewai import Agent, Task, Crew

load_dotenv()

SNAPSHOTS_DIR = Path(__file__).parent.parent / "snapshots"


def load_todays_snapshots() -> list[dict]:
    snapshots = []
    for f in sorted(SNAPSHOTS_DIR.glob("snapshot_*.json")):
        with open(f) as file:
            snapshots.append(json.load(file))
    return snapshots


def build_aggregator_agent(llm) -> Agent:
    return Agent(
        role="Work Analyst",
        llm=llm,
        goal="Merge all activity snapshots from the day into a single clear work report",
        backstory=(
            "You are an expert at reading raw developer activity data — git commits, "
            "Claude Code session logs, VSCode file activity, and browser research — "
            "and turning it into a coherent, accurate summary of what was built and solved."
        ),
        verbose=True,
    )


def build_aggregator_task(agent: Agent, snapshots: list[dict]) -> Task:
    return Task(
        description=f"""
You are given a list of activity snapshots collected throughout the day.
Each snapshot contains:
- claude_sessions: Claude Code session logs (what was built, problems solved)
- github: commits and PRs pushed
- activitywatch: VSCode files edited, apps used, browser activity

Your job is to merge all snapshots and produce a clean work report with:
1. A summary of what was worked on today (projects, features, bugs, research)
2. Technologies and tools used
3. Key problems solved
4. Estimated effort level (low / medium / high)

Here are today's snapshots:
{json.dumps(snapshots, indent=2)}

Return a structured JSON work report with these fields:
- summary: string (2-4 sentences)
- projects: list of project names worked on
- technologies: list of tech/tools used
- problems_solved: list of problems/features tackled
- effort_level: "low" | "medium" | "high"
- raw_highlights: list of notable specific things worth posting about
""",
        agent=agent,
        expected_output="A structured JSON work report",
    )


def run_aggregator() -> dict:
    snapshots = load_todays_snapshots()
    if not snapshots:
        return {}

    agent = build_aggregator_agent()
    task = build_aggregator_task(agent, snapshots)
    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    result = crew.kickoff()

    # Extract JSON from result
    raw = str(result)
    start = raw.find("{")
    end = raw.rfind("}") + 1
    return json.loads(raw[start:end])


if __name__ == "__main__":
    report = run_aggregator()
    print(json.dumps(report, indent=2))
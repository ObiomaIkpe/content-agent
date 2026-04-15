import json
from crewai import Agent, Task


def build_strategist_agent(llm) -> Agent:
    return Agent(
        role="Content Strategist",
        llm=llm,
        goal="Decide what angles to push for each audience based on the work report",
        backstory=(
            "You are a personal branding strategist for developers. "
            "You know exactly how to position technical work to appeal to "
            "hiring companies looking for skilled engineers, and to businesses "
            "looking for freelancers to build custom software for them. "
            "You avoid repetition and always find the most compelling angle."
        ),
        verbose=True,
    )


def build_strategist_task(agent: Agent, work_report: dict, content_history: list[dict]) -> Task:
    return Task(
        description=f"""
You are given a work report summarizing what a developer did today.
You are also given a content history of what has already been posted recently.

Work report:
{json.dumps(work_report, indent=2)}

Recent content history (avoid repeating these topics/angles):
{json.dumps(content_history, indent=2)}

Your job is to:
1. Pick 1-2 highlights from the work report worth posting about
2. For each highlight, generate two angles:
   - hiring_angle: positions the work to impress companies looking to hire
   - freelance_angle: positions the work to attract businesses needing custom software

Return a structured JSON with:
- highlights: list of objects, each with:
  - topic: string (what the highlight is about)
  - hiring_angle: string (1-2 sentences framing for hiring companies)
  - freelance_angle: string (1-2 sentences framing for freelance clients)
  - suggested_platforms: list of platforms best suited for this highlight
""",
        agent=agent,
        expected_output="A structured JSON with content angles",
    )
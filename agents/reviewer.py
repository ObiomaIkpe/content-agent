import json
from crewai import Agent, Task


def build_reviewer_agent(llm) -> Agent:
    return Agent(
        role="Content Quality Reviewer",
        llm=llm,
        goal="Review all drafted posts for quality, consistency, and brand voice alignment",
        backstory=(
            "You are a meticulous content editor who reviews social media posts "
            "for software developers. You check that each post matches the intended "
            "platform tone, aligns with the developer's brand voice, doesn't contain "
            "sensitive company information, and is ready to publish. "
            "You give clear, actionable feedback or approve posts as-is."
        ),
        verbose=True,
    )


def build_reviewer_task(agent: Agent, drafts: dict, brand_voice: dict) -> Task:
    return Task(
        description=f"""
Review the following social media post drafts for a software developer.

Drafts:
{json.dumps(drafts, indent=2)}

Brand voice configuration:
{json.dumps(brand_voice, indent=2)}

For each draft, check:
1. Does it match the platform's tone and format?
2. Does it align with the brand voice config?
3. Does it contain any sensitive company/client information that should be removed?
4. Is it ready to publish as-is?

Return a structured JSON with:
- reviews: dict with platform names as keys, each containing:
  - status: "approved" | "needs_revision"
  - feedback: string (what to fix, or "Looks good" if approved)
  - revised_post: string (the revised post if needs_revision, otherwise null)
""",
        agent=agent,
        expected_output="A structured JSON with reviews for each platform",
    )
import json
from crewai import Agent, Task


def build_linkedin_writer(llm) -> Agent:
    return Agent(
        role="LinkedIn Copywriter",
        llm=llm,
        goal="Write compelling LinkedIn posts that showcase developer work professionally",
        backstory=(
            "You are an expert LinkedIn ghostwriter for software developers. "
            "You write posts that are professional but human, achievement-focused, "
            "and structured to perform well on LinkedIn. You avoid buzzwords, "
            "corporate speak, and generic advice. You write in first person as the developer."
        ),
        verbose=True,
    )


def build_linkedin_task(agent: Agent, highlight: dict, brand_voice: dict) -> Task:
    return Task(
        description=f"""
Write a LinkedIn post for a software developer based on this highlight:
{json.dumps(highlight, indent=2)}

Brand voice configuration:
{json.dumps(brand_voice, indent=2)}

LinkedIn post guidelines:
- Start with a strong hook (first line must stop the scroll)
- 150-300 words
- Use short paragraphs (1-3 lines max)
- End with a question or call to action
- 3-5 relevant hashtags at the end
- Write in first person
- Do NOT use buzzwords like "excited to share", "humbled", "synergy"
- Tone should match the brand voice config

Return only the post text, nothing else.
""",
        agent=agent,
        expected_output="A LinkedIn post as plain text",
    )
import json
from crewai import Agent, Task


def build_facebook_writer(llm) -> Agent:
    return Agent(
        role="Facebook Copywriter",
        llm=llm,
        goal="Write casual, relatable Facebook posts that showcase developer work to a general audience",
        backstory=(
            "You are an expert at writing Facebook posts for developers. "
            "You know that Facebook audiences are more general and less technical "
            "than LinkedIn or Twitter. You write posts that are warm, relatable, "
            "and tell a human story behind the technical work. You make complex "
            "technical work understandable and interesting to non-developers."
        ),
        verbose=True,
    )


def build_facebook_task(agent: Agent, highlight: dict, brand_voice: dict) -> Task:
    return Task(
        description=f"""
Write a Facebook post for a software developer based on this highlight:
{json.dumps(highlight, indent=2)}

Brand voice configuration:
{json.dumps(brand_voice, indent=2)}

Facebook post guidelines:
- 100-200 words
- Casual, warm, and conversational tone
- Explain technical work in simple terms a non-developer can understand
- Tell the human story behind the work (the challenge, the breakthrough, the feeling)
- End with a relatable question or observation
- 2-3 relevant hashtags at the end
- Write in first person
- Tone should match the brand voice config

Return only the post text, nothing else.
""",
        agent=agent,
        expected_output="A Facebook post as plain text",
    )
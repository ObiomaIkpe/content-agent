import json
from crewai import Agent, Task


def build_twitter_writer(llm) -> Agent:
    return Agent(
        role="X (Twitter) Copywriter",
        llm=llm,
        goal="Write punchy, engaging X posts and threads for a developer audience",
        backstory=(
            "You are an expert at writing for X (Twitter). You know how to hook "
            "readers in the first line, keep things concise, and write threads "
            "that people actually read to the end. You write for developers and "
            "tech-savvy audiences. You are direct, confident, and avoid fluff."
        ),
        verbose=True,
    )


def build_twitter_task(agent: Agent, highlight: dict, brand_voice: dict) -> Task:
    return Task(
        description=f"""
Write an X (Twitter) post or short thread for a software developer based on this highlight:
{json.dumps(highlight, indent=2)}

Brand voice configuration:
{json.dumps(brand_voice, indent=2)}

X post guidelines:
- If a single tweet: max 280 characters
- If a thread: max 5 tweets, each under 280 characters, numbered (1/, 2/, etc.)
- First tweet must hook immediately — no slow buildup
- Be direct and confident
- No hashtags unless absolutely necessary (max 2)
- Write in first person
- Tone should match the brand voice config

Return only the post text, nothing else.
""",
        agent=agent,
        expected_output="An X post or thread as plain text",
    )
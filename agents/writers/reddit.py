import json
from crewai import Agent, Task


def build_reddit_writer(llm) -> Agent:
    return Agent(
        role="Reddit Copywriter",
        llm=llm,
        goal="Write authentic, story-driven Reddit posts that resonate with developer communities",
        backstory=(
            "You are an expert at writing for Reddit, specifically developer subreddits "
            "like r/programming, r/webdev, r/learnprogramming, and r/freelance. "
            "You know that Reddit users hate self-promotion and corporate tone. "
            "You write posts that feel genuine, tell a real story, provide value, "
            "and only subtly highlight the developer's skills and work."
        ),
        verbose=True,
    )


def build_reddit_task(agent: Agent, highlight: dict, brand_voice: dict) -> Task:
    return Task(
        description=f"""
Write a Reddit post for a software developer based on this highlight:
{json.dumps(highlight, indent=2)}

Brand voice configuration:
{json.dumps(brand_voice, indent=2)}

Reddit post guidelines:
- Format: Title + Body
- Title: curiosity-driven or value-driven, not clickbait
- Body: 150-400 words, conversational and story-driven
- Must provide genuine value or insight, not just self-promotion
- End with an open question to invite discussion
- Suggest the most relevant subreddit to post in
- Write in first person
- Tone should match the brand voice config

Return the post in this format:
SUBREDDIT: r/...
TITLE: ...
BODY:
...
""",
        agent=agent,
        expected_output="A Reddit post with subreddit, title, and body",
    )
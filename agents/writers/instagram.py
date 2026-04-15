import json
from crewai import Agent, Task


def build_instagram_writer(llm) -> Agent:
    return Agent(
        role="Instagram Copywriter",
        llm=llm,
        goal="Write engaging Instagram captions that showcase developer work visually and concisely",
        backstory=(
            "You are an expert at writing Instagram captions for developers. "
            "You know that Instagram is visual-first, so captions must complement "
            "a code screenshot or workspace photo. You write captions that are "
            "punchy, motivational, and authentic. You use line breaks strategically "
            "and know exactly which hashtags perform well in the dev community."
        ),
        verbose=True,
    )


def build_instagram_task(agent: Agent, highlight: dict, brand_voice: dict) -> Task:
    return Task(
        description=f"""
Write an Instagram caption for a software developer based on this highlight:
{json.dumps(highlight, indent=2)}

Brand voice configuration:
{json.dumps(brand_voice, indent=2)}

Instagram caption guidelines:
- 80-150 words
- First line must be a strong hook (this shows before "more" cutoff)
- Use line breaks between short paragraphs for readability
- Motivational or behind-the-scenes tone
- End with a call to action (save, comment, follow)
- 10-15 hashtags on a separate line at the end
- Mix popular and niche hashtags (e.g. #coding #python #buildinpublic #devlife)
- Write in first person
- Tone should match the brand voice config

Return only the caption text, nothing else.
""",
        agent=agent,
        expected_output="An Instagram caption as plain text",
    )
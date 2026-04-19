import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from crewai import Crew, Agent, Task, LLM

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.loader import load_brand_voice
from history import load_history, save_topic
from image_generator import generate_image

from aggregator_agent import build_aggregator_agent, build_aggregator_task, load_todays_snapshots
from strategist_agent import build_strategist_agent, build_strategist_task
from writers.linkedin import build_linkedin_writer, build_linkedin_task
from writers.twitter import build_twitter_writer, build_twitter_task
from writers.reddit import build_reddit_writer, build_reddit_task
from writers.facebook import build_facebook_writer, build_facebook_task
from writers.instagram import build_instagram_writer, build_instagram_task
from reviewer import build_reviewer_agent, build_reviewer_task

claude_llm = LLM(
    model="claude-sonnet-4-20250514",
    api_key=os.getenv("ANTHROPIC_API_KEY"),
)

DEFAULT_BRAND_VOICE = load_brand_voice()


def extract_json(text: str) -> dict:
    raw = str(text)
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start == -1 or end == 0:
        return {}
    try:
        return json.loads(raw[start:end])
    except json.JSONDecodeError:
        return {}


def run_pipeline(brand_voice: dict = None, content_history: list = None) -> dict:
    if brand_voice is None:
        brand_voice = DEFAULT_BRAND_VOICE
    if content_history is None:
        content_history = load_history()

    # Step 1 — Aggregate snapshots into work report
    print("\n=== STEP 1: Aggregating snapshots ===")
    snapshots = load_todays_snapshots()
    if not snapshots:
        print("No snapshots found. Run the local agent first.")
        return {}

    agg_agent = build_aggregator_agent(claude_llm)
    agg_task = build_aggregator_task(agg_agent, snapshots)
    agg_crew = Crew(agents=[agg_agent], tasks=[agg_task], verbose=True)
    work_report = extract_json(agg_crew.kickoff())
    print("\nWork report:", json.dumps(work_report, indent=2))

    # Step 2 — Strategist picks angles
    print("\n=== STEP 2: Generating content angles ===")
    strat_agent = build_strategist_agent(claude_llm)
    strat_task = build_strategist_task(strat_agent, work_report, content_history)
    strat_crew = Crew(agents=[strat_agent], tasks=[strat_task], verbose=True)
    strategy = extract_json(strat_crew.kickoff())
    print("\nStrategy:", json.dumps(strategy, indent=2))

    highlights = strategy.get("highlights", [])
    if not highlights:
        print("No highlights generated.")
        return {}

    highlight = highlights[0]
    save_topic(
        topic=highlight.get("topic", ""),
        platforms=highlight.get("suggested_platforms", []),
    )

    # Step 3 — Write platform drafts
    print("\n=== STEP 3: Writing platform drafts ===")
    writers = [
        ("linkedin", build_linkedin_writer(claude_llm), build_linkedin_task),
        ("twitter", build_twitter_writer(claude_llm), build_twitter_task),
        ("reddit", build_reddit_writer(claude_llm), build_reddit_task),
        ("facebook", build_facebook_writer(claude_llm), build_facebook_task),
        ("instagram", build_instagram_writer(claude_llm), build_instagram_task),
    ]

    drafts = {}
    images = {}
    topic = highlight.get("topic", "")
    summary = work_report.get("summary", "")

    for platform, writer, task_fn in writers:
        print(f"\nWriting {platform} post...")
        task = task_fn(writer, highlight, brand_voice)
        crew = Crew(agents=[writer], tasks=[task], verbose=False)
        drafts[platform] = str(crew.kickoff())

        print(f"Generating {platform} image...")
        try:
            images[platform] = generate_image(topic=topic, summary=summary, platform=platform, draft=drafts[platform])
            print(f"  Saved: {images[platform]}")
        except Exception as e:
            print(f"  Image generation failed for {platform}: {e}")
            images[platform] = None

    # Step 4 — Review drafts
    print("\n=== STEP 4: Reviewing drafts ===")
    reviewer = build_reviewer_agent(claude_llm)
    review_task = build_reviewer_task(reviewer, drafts, brand_voice)
    review_crew = Crew(agents=[reviewer], tasks=[review_task], verbose=True)
    reviews = extract_json(review_crew.kickoff())

    # Step 5 — Merge drafts with reviews
    final_posts = {}
    for platform, draft in drafts.items():
        review = reviews.get("reviews", {}).get(platform, {})
        final_posts[platform] = {
            "draft": draft,
            "status": review.get("status", "approved"),
            "feedback": review.get("feedback", ""),
            "final": review.get("revised_post") or draft,
            "image_path": images.get(platform),
        }

    return final_posts


if __name__ == "__main__":
    import asyncio
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from bot.telegram_bot import build_app, send_all_drafts

    results = run_pipeline()
    if results:
        print("\n=== Sending drafts to Telegram ===")
        app = build_app()
        async def send():
            async with app:
                await send_all_drafts(app, results)
        asyncio.run(send())
    else:
        print("No results to send.")
import os
import tweepy
from dotenv import load_dotenv

load_dotenv()


def publish(text: str) -> dict:
    client = tweepy.Client(
        consumer_key=os.getenv("TWITTER_CONSUMER_KEY"),
        consumer_secret=os.getenv("TWITTER_CONSUMER_SECRET"),
        access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    )

    # If text is a thread (contains numbered tweets separated by \n\n---\n\n), post each in reply
    parts = [p.strip() for p in text.split("\n\n---\n\n") if p.strip()]
    if len(parts) <= 1:
        parts = [text.strip()]

    last_id = None
    tweet_ids = []
    for part in parts:
        if len(part) > 280:
            part = part[:277] + "..."
        kwargs = {"text": part}
        if last_id:
            kwargs["in_reply_to_tweet_id"] = last_id
        response = client.create_tweet(**kwargs)
        last_id = response.data["id"]
        tweet_ids.append(last_id)

    return {"tweet_ids": tweet_ids, "url": f"https://twitter.com/i/web/status/{tweet_ids[0]}"}

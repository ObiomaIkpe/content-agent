import os
import tweepy
from dotenv import load_dotenv

load_dotenv()


def publish(text: str, image_path: str = None) -> dict:
    auth = tweepy.OAuth1UserHandler(
        os.getenv("TWITTER_CONSUMER_KEY"),
        os.getenv("TWITTER_CONSUMER_SECRET"),
        os.getenv("TWITTER_ACCESS_TOKEN"),
        os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    )
    api_v1 = tweepy.API(auth)
    client = tweepy.Client(
        consumer_key=os.getenv("TWITTER_CONSUMER_KEY"),
        consumer_secret=os.getenv("TWITTER_CONSUMER_SECRET"),
        access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    )

    media_ids = []
    if image_path:
        media = api_v1.media_upload(filename=image_path)
        media_ids.append(str(media.media_id))

    parts = [p.strip() for p in text.split("\n\n---\n\n") if p.strip()]
    if len(parts) <= 1:
        parts = [text.strip()]

    last_id = None
    tweet_ids = []
    for i, part in enumerate(parts):
        if len(part) > 280:
            part = part[:277] + "..."
        kwargs = {"text": part}
        if last_id:
            kwargs["in_reply_to_tweet_id"] = last_id
        # Attach image only to first tweet
        if i == 0 and media_ids:
            kwargs["media_ids"] = media_ids
        response = client.create_tweet(**kwargs)
        last_id = response.data["id"]
        tweet_ids.append(last_id)

    return {"tweet_ids": tweet_ids, "url": f"https://twitter.com/i/web/status/{tweet_ids[0]}"}

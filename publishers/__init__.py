from . import twitter, linkedin


def publish(platform: str, text: str, image_path: str = None) -> dict:
    publishers = {
        "twitter": twitter.publish,
        "linkedin": linkedin.publish,
    }
    fn = publishers.get(platform)
    if fn is None:
        return {"skipped": True, "reason": f"No publisher for {platform} yet"}
    return fn(text, image_path=image_path)

import os
import requests
from dotenv import load_dotenv

load_dotenv()

LINKEDIN_API = "https://api.linkedin.com/v2"


def publish(text: str) -> dict:
    token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    person_urn = os.getenv("LINKEDIN_PERSON_URN")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    response = requests.post(f"{LINKEDIN_API}/ugcPosts", headers=headers, json=payload)
    response.raise_for_status()
    post_id = response.headers.get("x-restli-id", "unknown")
    return {"post_id": post_id}

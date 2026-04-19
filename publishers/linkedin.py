import os
import requests
from dotenv import load_dotenv

load_dotenv()

LINKEDIN_API = "https://api.linkedin.com/v2"


def _upload_image(token: str, person_urn: str, image_path: str) -> str:
    """Upload image to LinkedIn and return the asset URN."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    # Step 1: Register upload
    register_payload = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": person_urn,
            "serviceRelationships": [
                {"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}
            ],
        }
    }
    r = requests.post(f"{LINKEDIN_API}/assets?action=registerUpload", headers=headers, json=register_payload)
    r.raise_for_status()
    data = r.json()
    upload_url = data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
    asset = data["value"]["asset"]

    # Step 2: Upload binary
    with open(image_path, "rb") as f:
        requests.put(upload_url, data=f, headers={"Authorization": f"Bearer {token}"})

    return asset


def publish(text: str, image_path: str = None) -> dict:
    token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    person_urn = os.getenv("LINKEDIN_PERSON_URN")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    share_content = {"shareCommentary": {"text": text}}

    if image_path:
        asset = _upload_image(token, person_urn, image_path)
        share_content["shareMediaCategory"] = "IMAGE"
        share_content["media"] = [{"status": "READY", "media": asset}]
    else:
        share_content["shareMediaCategory"] = "NONE"

    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {"com.linkedin.ugc.ShareContent": share_content},
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    response = requests.post(f"{LINKEDIN_API}/ugcPosts", headers=headers, json=payload)
    response.raise_for_status()
    post_id = response.headers.get("x-restli-id", "unknown")
    return {"post_id": post_id}

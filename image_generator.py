import uuid
import httpx
from pathlib import Path
from urllib.parse import quote

IMAGES_DIR = Path(__file__).parent / "snapshots" / "images"
POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}?width=1280&height=720&nologo=true"

PLATFORM_STYLES = {
    "linkedin": (
        "Professional and polished. Clean minimal layout, dark navy background, "
        "subtle blue accents. Corporate tech aesthetic. Inspires trust and credibility."
    ),
    "twitter": (
        "Bold, punchy, high contrast. Vibrant electric blue and cyan on near-black. "
        "Dynamic composition, eye-catching at small size. Stops a fast-scrolling feed."
    ),
    "reddit": (
        "Casual and community-feel. Flat illustration style, muted colors with one "
        "bold accent. Feels approachable, not corporate."
    ),
    "facebook": (
        "Warm and social. Bright, friendly colors, inviting composition. "
        "Feels like something a friend would share."
    ),
    "instagram": (
        "Highly aesthetic, visually stunning. Rich gradients, vivid colors, "
        "strong visual hierarchy. Premium feel, looks great on mobile."
    ),
}


def _build_image_prompt(topic: str, summary: str, platform: str, draft: str = "") -> str:
    style = PLATFORM_STYLES.get(platform, PLATFORM_STYLES["twitter"])
    draft_context = f"The post says: {draft[:300]}" if draft else f"Context: {summary}"
    return (
        f"A digital illustration for a {platform} post by a software developer. "
        f"Topic: {topic}. {draft_context}. "
        f"Style: {style} "
        f"No text, no letters, no words in the image."
    )


def generate_image(topic: str, summary: str = "", platform: str = "twitter", draft: str = "") -> str:
    """Generate a platform-specific image informed by the actual post content. Returns local file path."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    prompt = _build_image_prompt(topic, summary, platform, draft)
    url = POLLINATIONS_URL.format(prompt=quote(prompt))

    for attempt in range(3):
        try:
            response = httpx.get(url, timeout=90, follow_redirects=True)
            response.raise_for_status()
            break
        except (httpx.ReadTimeout, httpx.ConnectTimeout):
            if attempt == 2:
                raise
            continue

    filename = IMAGES_DIR / f"{platform}_{uuid.uuid4().hex[:8]}.png"
    filename.write_bytes(response.content)

    return str(filename)

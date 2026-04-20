import json
import os
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

SNAPSHOTS_DIR = Path(__file__).parent.parent / "snapshots"
API_SECRET = os.getenv("SNAPSHOT_API_SECRET", "")


@app.post("/snapshots")
async def receive_snapshot(
    payload: dict,
    x_api_secret: str = Header(default=""),
):
    if API_SECRET and x_api_secret != API_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = SNAPSHOTS_DIR / f"snapshot_{timestamp}.json"
    filename.write_text(json.dumps(payload, indent=2))

    return {"status": "ok", "saved": str(filename)}


@app.get("/health")
async def health():
    return {"status": "ok"}

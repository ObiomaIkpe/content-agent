import os
import json
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.loader import load_brand_voice

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# In-memory store for current drafts pending review
pending_posts = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Content Agent bot is running.\n\n"
        "Commands:\n"
        "/status - Check pipeline status\n"
        "/run - Trigger pipeline manually\n"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    snapshots_dir = os.path.join(os.path.dirname(__file__), "..", "snapshots")
    count = len(list(__import__("pathlib").Path(snapshots_dir).glob("snapshot_*.json")))
    await update.message.reply_text(f"Snapshots collected today: {count}")

async def set_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        current = load_brand_voice()
        await update.message.reply_text(
            f"Current brand voice:\n\n"
            f"Tone: {current.get('tone')}\n"
            f"Style: {current.get('style')}\n"
            f"Personality: {current.get('personality_notes')}\n\n"
            f"To update, use:\n"
            f"/setvoice tone casual but technical\n"
            f"/setvoice style storytelling\n"
            f"/setvoice personality Your notes here"
        )
        return

    field = context.args[0]
    value = " ".join(context.args[1:])

    field_map = {
        "tone": "tone",
        "style": "style",
        "personality": "personality_notes",
    }

    if field not in field_map:
        await update.message.reply_text(f"Unknown field: {field}. Use tone, style, or personality.")
        return

    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from config.loader import update_brand_voice
    update_brand_voice({field_map[field]: value})
    await update.message.reply_text(f"✅ Updated {field} to: {value}")



async def run_pipeline_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Running pipeline... this will take a few minutes.")
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from agents.crew import run_pipeline

    try:
        results = await asyncio.get_event_loop().run_in_executor(None, run_pipeline)
        if results:
            await send_all_drafts(context.application, results)
        else:
            await update.message.reply_text("⚠️ No content generated. Check your snapshots.")
    except Exception as e:
        await update.message.reply_text(f"❌ Pipeline failed: {str(e)}")


async def send_draft_for_review(app: Application, platform: str, post_data: dict):
    """Send a single platform draft with Approve/Reject buttons."""
    draft = post_data.get("final", post_data.get("draft", ""))
    status = post_data.get("status", "approved")
    feedback = post_data.get("feedback", "")

    text = (
        f"📝 *{platform.upper()} DRAFT*\n\n"
        f"{draft}\n\n"
        f"---\n"
        f"Reviewer: {feedback or 'Looks good'}"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve:{platform}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject:{platform}"),
        ]
    ])

    await app.bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=text,
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


async def send_all_drafts(app: Application, final_posts: dict):
    """Send all platform drafts for review."""
    global pending_posts
    pending_posts = final_posts

    await app.bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text="🚀 *Today's content drafts are ready for review!*\nReview each platform below:",
        parse_mode="Markdown",
    )

    for platform, post_data in final_posts.items():
        await send_draft_for_review(app, platform, post_data)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, platform = query.data.split(":")

    if action == "approve":
        pending_posts[platform]["approved"] = True
        await query.edit_message_reply_markup(
            InlineKeyboardMarkup([[
                InlineKeyboardButton(f"✅ {platform.upper()} Approved", callback_data="noop")
            ]])
        )
        await query.message.reply_text(f"✅ {platform.capitalize()} post approved.")

    elif action == "reject":
        pending_posts[platform]["approved"] = False
        await query.edit_message_reply_markup(
            InlineKeyboardMarkup([[
                InlineKeyboardButton(f"❌ {platform.upper()} Rejected", callback_data="noop")
            ]])
        )
        await query.message.reply_text(f"❌ {platform.capitalize()} post rejected.")

    # Check if all platforms have been reviewed
    reviewed = [p for p in pending_posts if "approved" in pending_posts[p]]
    if len(reviewed) == len(pending_posts):
        approved = [p for p in pending_posts if pending_posts[p].get("approved")]
        rejected = [p for p in pending_posts if not pending_posts[p].get("approved")]
        await query.message.reply_text(
            f"All posts reviewed!\n"
            f"✅ Approved: {', '.join(approved) or 'none'}\n"
            f"❌ Rejected: {', '.join(rejected) or 'none'}\n\n"
            f"Approved posts will be queued for posting."
        )


def build_app() -> Application:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("run", run_pipeline_command))
    app.add_handler(CommandHandler("setvoice", set_voice))
    app.add_handler(CallbackQueryHandler(handle_callback))
    return app


if __name__ == "__main__":
    print("Starting Telegram bot...")
    app = build_app()
    app.run_polling()
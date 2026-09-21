import os
import json
import time
import datetime
from dotenv import load_dotenv

load_dotenv()

from telethon import TelegramClient, events
from telethon.errors.rpcerrorlist import ChatForwardsRestrictedError
from classifier import classify_job, is_tech_related, MODEL
import db


API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]

with open("groups.json", "r", encoding="utf-8") as f:
    GROUPS = json.load(f)["groups"]

client = TelegramClient("job_bot_session", API_ID, API_HASH)


@client.on(events.NewMessage(chats=GROUPS))
async def handler(event):
    text = event.raw_text
    if not text:
        return

    try:
        classification = classify_job(text)
    except Exception as e:
        print(f"[classifier error] {e}")
        return

    if classification.get("is_tech"):
        try:
            await client.forward_messages("me", event.message)
        except ChatForwardsRestrictedError:
            await client.send_message("me", text)
        print(f"[forwarded] {text[:60]}...")

        try:
            chat = await event.get_chat()
            group_title = getattr(chat, "title", None) or getattr(chat, "username", None) or str(event.chat_id)
        except Exception:
            group_title = str(event.chat_id)

        msg_date = getattr(event.message, "date", None)
        timestamp_str = (
            msg_date.isoformat()
            if msg_date
            else datetime.datetime.now(datetime.timezone.utc).isoformat()
        )
        category = classification.get("category", "Other Tech")

        try:
            db.save_job(
                message_text=text,
                source_group=group_title,
                timestamp=timestamp_str,
                category=category,
            )
            print(f"[db saved] Category: {category} | Group: {group_title}")
        except Exception as e:
            print(f"[db error] {e}")


@client.on(events.NewMessage(chats="me", pattern=r"(?i)^/help(?:\s|$)", forwards=False))
async def help_handler(event):
    help_text = (
        "**🤖 Job Filter Bot**\n\n"
        "• **Status:** Active & listening\n"
        f"• **Monitored Groups:** {len(GROUPS)}\n"
        f"• **AI Model:** {MODEL}\n\n"
        "**What I do:**\n"
        "I monitor your configured Telegram channels and groups for tech/software job postings, "
        "filter them using Gemini AI, and forward matching opportunities to Saved Messages.\n\n"
        "**Commands:**\n"
        "• `/help` — Show this overview and bot status"
    )
    await event.respond(help_text)


def main():
    db.init_db()
    while True:
        try:
            with client:
                print("Bot is running. Listening to:", GROUPS)
                client.run_until_disconnected()
        except (ConnectionError, OSError) as e:
            print(f"[connection lost] {e}. Reconnecting in 5s...")
            time.sleep(5)
        except KeyboardInterrupt:
            print("Bot stopped by user.")
            break
        except Exception as e:
            print(f"[unexpected error] {e}. Reconnecting in 5s...")
            time.sleep(5)


if __name__ == "__main__":
    main()



import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import Chat, Channel

load_dotenv()

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]

client = TelegramClient("job_bot_session", API_ID, API_HASH)


async def main():
    async for dialog in client.iter_dialogs():
        if isinstance(dialog.entity, (Chat, Channel)):
            print(f"{dialog.id}\t{dialog.name}")


with client:
    client.loop.run_until_complete(main())

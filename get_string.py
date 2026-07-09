from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio
API_ID = 37079063
API_HASH = '3936d3b05c17ced6d29da7c814358426'
CHANNEL = '@SAMARTHZURALE_52'
client = TelegramClient('session', API_ID, API_HASH)  # 'session' = teri session.session file


async def main():
    await client.start()
    session_string = StringSession.save(client.session)  # ✅ ye sahi tarika hai
    print(f"COPY THIS: {session_string}")
    await client.disconnect()

asyncio.run(main())
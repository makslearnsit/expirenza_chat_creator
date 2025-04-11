# authenticate.py
import asyncio
from telethon import TelegramClient
from core.config import API_ID, API_HASH, SESSION_NAME # Імпортуємо з конфігу

async def run_auth():
    print("Starting Telethon authentication...")
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.start() # Це запустить інтерактивний вхід у консолі
    print(f"Authentication successful! Session file '{SESSION_NAME}.session' should be created/updated.")
    me = await client.get_me()
    print(f"Logged in as: {me.first_name} {me.last_name or ''} (@{me.username or ''})")
    await client.disconnect()
    print("Client disconnected.")

if __name__ == "__main__":
     asyncio.run(run_auth())
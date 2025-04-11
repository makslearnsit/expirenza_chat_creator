# authenticate.py
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path to resolve imports correctly
current_dir = Path(__file__).parent
# When running on Heroku or elsewhere, ensure imports work
if current_dir.name == 'telegram_group_creator':
    # Import from the local module
    from core.config import API_ID, API_HASH, SESSION_NAME
else:
    # Try to add the parent directory to the path
    parent_dir = current_dir.parent
    sys.path.append(str(parent_dir))
    from telegram_group_creator.core.config import API_ID, API_HASH, SESSION_NAME

from telethon import TelegramClient

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
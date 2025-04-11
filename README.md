# Telegram Group Creator Bot

A Telegram bot that automates group creation and management tasks using Telethon and python-telegram-bot.

## Features

- Automated group creation
- User management functionalities
- Conversation-based interaction flow

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/makslearnsit/expirenza_chat_creator.git
   cd expirenza_chat_creator
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r telegram_group_creator/requirements.txt
   ```

3. Create a `.env` file in the `telegram_group_creator` directory with your credentials:
   ```
   BOT_TOKEN=your_telegram_bot_token
   API_ID=your_telegram_api_id
   API_HASH=your_telegram_api_hash
   PHONE=your_phone_number  # With country code, e.g., +12345678901
   ```

## Usage

Run the bot:

```bash
python -m telegram_group_creator.main
```

Available commands:

- `/start` - Start the conversation
- `/cancel` - Cancel the current operation

## Project Structure

```
telegram_group_creator/
├── bot_logic/       # Bot command handlers and conversation logic
├── core/            # Core configuration and utilities
├── utils/           # Helper functions
├── main.py          # Entry point for the application
├── authenticate.py  # Authentication utilities
└── requirements.txt # Project dependencies
```

## License

MIT

## Contributing

Contributions, issues, and feature requests are welcome!

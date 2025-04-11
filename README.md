# Telegram Group Creator Bot

A Telegram bot for creating and managing group chats.

## Heroku Deployment

This project includes a custom Heroku setup that handles Telegram authentication before starting the main application.

### Deployment Steps

1. Create a Heroku account and install the Heroku CLI
2. Log in to Heroku:
   ```
   heroku login
   ```
3. Create a new Heroku app:
   ```
   heroku create your-app-name
   ```
4. Configure environment variables:
   ```
   heroku config:set API_ID=your_api_id
   heroku config:set API_HASH=your_api_hash
   heroku config:set BOT_TOKEN=your_bot_token
   heroku config:set SESSION_NAME=your_session_name
   ```
5. Deploy to Heroku:
   ```
   git push heroku main
   ```

### Authentication Process

When the app starts on Heroku:

1. The authentication script will run first
2. You will need to complete the authentication process through Heroku logs
3. After authentication is complete, the main bot will start automatically

To view logs and complete authentication:

```
heroku logs --tail
```

## Local Development

To run the application locally:

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Run the authentication script first:
   ```
   python -m telegram_group_creator.authenticate
   ```
3. Then run the main application:
   ```
   python -m telegram_group_creator.main
   ```

## Project Structure

- `telegram_group_creator/` - Main application directory
  - `authenticate.py` - Telegram authentication script
  - `main.py` - Main bot application
- `heroku_startup.py` - Heroku entry point that handles authentication
- `Procfile` - Heroku process definition file
- `requirements.txt` - Python dependencies
- `runtime.txt` - Python version specification for Heroku

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

## License

MIT

## Contributing

Contributions, issues, and feature requests are welcome!

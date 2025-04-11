#!/usr/bin/env python3
"""
Heroku startup script that handles the main application.
"""
import os
import sys
import logging
import subprocess
import threading
import time
import requests
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

# Setup basic logging with reduced verbosity
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('heroku_startup')

# Get the app URL from environment or default to localhost
APP_URL = os.environ.get('HEROKU_APP_URL', 'https://expirenza-telegram-bot-eu-2bc6b8b0d3f4.herokuapp.com')

# Reduce logging verbosity for requests library
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    """Simple HTTP request handler to keep Heroku happy"""
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        response = f'<html><body>Telegram bot is running! Uptime: {time.time() - startup_time:.2f} seconds</body></html>'
        self.wfile.write(response.encode())
    
    def log_message(self, format, *args):
        # Suppress the default logging to reduce noise
        return

def keep_alive():
    """Send periodic requests to the app to prevent it from sleeping, with optimized frequency"""
    ping_count = 0
    while True:
        try:
            # Only log every 5th ping to reduce log size
            verbose = (ping_count % 5 == 0)
            requests.get(APP_URL, timeout=5)
            if verbose:
                logger.info(f"Keep-alive ping sent to {APP_URL}")
            ping_count += 1
        except Exception as e:
            logger.error(f"Keep-alive request failed: {e}")
        
        # Sleep for 20 minutes - Heroku Basic dynos sleep after 30 min of inactivity
        # This is less frequent than before to reduce resource usage
        time.sleep(1200)

def start_web_server():
    """Start a simple web server to keep Heroku happy"""
    try:
        port = int(os.environ.get('PORT', 8080))
        logger.info(f"Starting web server on port {port}")
        server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
        server.serve_forever()
    except Exception as e:
        logger.error(f"Web server error: {e}")
        # Try to restart the web server if it fails
        time.sleep(5)
        start_web_server()

def check_session_file():
    """Check if the Telethon session file exists"""
    session_name = os.environ.get('TELETHON_SESSION_NAME', 'new_account_session')
    session_file = f"{session_name}.session"
    
    if os.path.exists(session_file):
        logger.info(f"Session file '{session_file}' found.")
        return True
    else:
        logger.error(f"Session file '{session_file}' not found!")
        return False

def start_main_application():
    """Start the main application"""
    logger.info("Starting main application...")
    try:
        # Get the path to main.py
        main_script_path = Path(__file__).parent / "telegram_group_creator" / "main.py"
        
        # Only log directory contents on first startup for debugging
        if os.environ.get('DEBUG_LOGGING', '0') == '1':
            logger.info(f"Working directory: {os.getcwd()}")
            logger.info(f"Files in current directory: {os.listdir()}")
            logger.info(f"Files in telegram_group_creator: {os.listdir('telegram_group_creator')}")
        
        # Add the project root to PYTHONPATH
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        # Use subprocess to run the main script in the same process
        subprocess.call([sys.executable, str(main_script_path)])
    except Exception as e:
        logger.error(f"Failed to start main application: {e}")
        sys.exit(1)

# Global startup time to track uptime
startup_time = time.time()

def main():
    """Main entry point for Heroku"""
    logger.info("Starting Heroku application...")
    
    # First check if the session file exists
    if check_session_file():
        # Start web server in a separate thread
        web_thread = threading.Thread(target=start_web_server, daemon=True)
        web_thread.start()
        logger.info("Web server thread started")
        
        # Start keep-alive thread to prevent the app from sleeping
        keepalive_thread = threading.Thread(target=keep_alive, daemon=True)
        keepalive_thread.start()
        logger.info("Keep-alive thread started")
        
        # Start the main application in the main thread
        start_main_application()
    else:
        logger.error("Session file check failed, cannot start application")
        sys.exit(1)

if __name__ == "__main__":
    main() 
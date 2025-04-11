#!/usr/bin/env python3
"""
Heroku startup script that handles the main application.
"""
import os
import sys
import logging
import subprocess
import threading
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('heroku_startup')

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    """Simple HTTP request handler to keep Heroku happy"""
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Telegram bot is running!')

def start_web_server():
    """Start a simple web server to keep Heroku happy"""
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting web server on port {port}")
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

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
        
        # Print out environment for debugging
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

def main():
    """Main entry point for Heroku"""
    logger.info("Starting Heroku application...")
    
    # First check if the session file exists
    if check_session_file():
        # Start web server in a separate thread
        web_thread = threading.Thread(target=start_web_server, daemon=True)
        web_thread.start()
        logger.info("Web server thread started")
        
        # Start the main application in the main thread
        start_main_application()
    else:
        logger.error("Session file check failed, cannot start application")
        sys.exit(1)

if __name__ == "__main__":
    main() 
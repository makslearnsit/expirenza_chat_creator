#!/usr/bin/env python3
"""
Heroku startup script that handles authentication before starting the main application.
This script will:
1. Run the authentication process
2. Wait for user to complete authentication
3. Start the main application
"""
import os
import sys
import asyncio
import logging
import subprocess
from pathlib import Path

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('heroku_startup')

async def run_authentication():
    """Run the Telegram authentication process"""
    logger.info("Starting authentication process...")
    try:
        # Import and run the authentication function
        # Ensure the telegram_group_creator directory is in the Python path
        project_root = Path(__file__).parent
        sys.path.append(str(project_root))
        
        # Import the authenticate module and run auth
        from telegram_group_creator.authenticate import run_auth
        await run_auth()
        return True
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        return False

def start_main_application():
    """Start the main application"""
    logger.info("Starting main application...")
    try:
        # Get the path to main.py
        main_script_path = Path(__file__).parent / "telegram_group_creator" / "main.py"
        
        # Use subprocess to run the main script in the same process
        subprocess.call([sys.executable, main_script_path])
    except Exception as e:
        logger.error(f"Failed to start main application: {e}")
        sys.exit(1)

async def main():
    """Main entry point for Heroku"""
    logger.info("Starting Heroku application...")
    
    # First run authentication
    auth_success = await run_authentication()
    
    if auth_success:
        logger.info("Authentication completed successfully")
        
        # Add a small delay to ensure authentication is complete
        await asyncio.sleep(2)
        
        # Start the main application
        start_main_application()
    else:
        logger.error("Authentication failed, cannot start application")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 
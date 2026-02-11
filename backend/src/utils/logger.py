"""Logging utilities."""
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        # Store logs in logs/ directory to avoid triggering file watchers
        logging.FileHandler(logs_dir / f'app_{datetime.now().strftime("%Y%m%d")}.log')
    ]
)


def get_logger(name: str):
    """Get logger instance."""
    return logging.getLogger(name)


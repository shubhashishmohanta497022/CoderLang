import logging
import sys
import os

# Define the log file path
LOG_FILE = os.path.join(os.path.dirname(__file__), 'logs', 'events.log')
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')

# Ensure the log directory exists
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Configure the root logger to output to both console and file
def setup_logging():
    """Configures the logging system for console and file output."""
    
    # 1. Basic configuration (overwrites previous config)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)-8s - %(name)-25s - %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            # Console Handler (Already configured in main.py, but safe to redefine)
            logging.StreamHandler(sys.stdout),
        ]
    )

    # 2. File Handler (Ensure logs/events.log is written to)
    file_handler = logging.FileHandler(LOG_FILE, mode='a')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)-8s - %(name)-25s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    
    # Get the root logger and add the file handler
    root_logger = logging.getLogger()
    if not any(isinstance(h, logging.FileHandler) for h in root_logger.handlers):
        root_logger.addHandler(file_handler)
    
    # Inform where logs are going
    root_logger.info(f"Logging configured. Console output enabled. File logging to {LOG_FILE}")
    
# Call setup immediately to ensure all subsequent imports and actions are logged
setup_logging()

# You can now import logging in any file and use: 
# log = logging.getLogger(__name__)
# log.info("...")

# Utility function for the main demo
def tail_logs(n_lines: int = 20) -> str:
    """Reads and returns the last N lines of the events log file."""
    try:
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()
        return "".join(lines[-n_lines:])
    except FileNotFoundError:
        return "Log file not found."
    except Exception as e:
        return f"Error reading log file: {e}"
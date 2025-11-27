# /////////////////////////////////////////////////////////////////////////////////////////////////////
# FileName   : modem_logger.py
# Owner      : Mohammad Mahdi Mohammadi (Mahdi.mohammadi@cortus.com)
# Date       : 12/11/2025
# Description: This Module is for generating a log for the modem commands and responses
# /////////////////////////////////////////////////////////////////////////////////////////////////////

import os
from datetime import datetime

# Define the default log file path (in the same folder as this file)
LOG_FILE = os.path.join(os.path.dirname(__file__), "modem_log.log")

def log_message(message, filename=LOG_FILE):
    """Write timestamped messages into a log file with milliseconds precision."""
    try:
        now = datetime.now()
        # Format timestamp with milliseconds only
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # remove last 3 digits
        with open(filename, "a") as f:
            f.write(f"{timestamp}: {message}\n")
        # print(f"{timestamp}: {message}")  # optional: also print to console
    except Exception as e:
        print(f"[LOG ERROR] Could not write to log file: {e}")

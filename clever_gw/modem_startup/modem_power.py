# /////////////////////////////////////////////////////////////////////////////////////////////////////
# FileName   : modem_power.py
# Owner      : Mohammad Mahdi Mohammadi (Mahdi.mohammadi@cortus.com)
# Date       : 12/11/2025
# Description: This Module is for performing power toggle on SIM7070G modem via GPIO4 (PWRKEY pin)
# /////////////////////////////////////////////////////////////////////////////////////////////////////
import RPi.GPIO as GPIO
import time
from modem_logger import log_message # To record modem commands and responses

# ANSI color codes
RESET = "\033[97m"
BOLD = "\033[1m"
WHITE = "\033[97m"
GREEN = "\033[32m"
YELLOW = "\033[93m"
RED = "\033[31m"
# ---------------------------
# Configuration
# ---------------------------
PWRKEY_PIN = 4          # GPIO4 (BCM numbering, physical pin 7)
HOLD_TIME = 2           # Time to hold HIGH to simulate button press (seconds)
POST_POWER_DELAY = 10.0 # Time to wait after releasing button for modem to power up

# ---------------------------
# Functions
# Power cycle the SIM7070G modem via GPIO4
# ---------------------------
def toggle_modem_power():

    try:
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PWRKEY_PIN, GPIO.OUT)

        # Ensure idle state (chip sees HIGH through transistor)
        GPIO.output(PWRKEY_PIN, GPIO.LOW)

        print(f"{RESET}Toggling modem power: driving {GREEN}GPIO{PWRKEY_PIN} HIGH{RESET} for {HOLD_TIME}s...")
        log_message("Power toggle start")

        # Pulse (chip sees LOW)
        GPIO.output(PWRKEY_PIN, GPIO.HIGH)
        time.sleep(HOLD_TIME)

        # Back to idle
        print(f"Releasing {GREEN}GPIO{PWRKEY_PIN} to LOW...{RESET}")
        log_message(f"GPIO{PWRKEY_PIN} set LOW (idle)")
        GPIO.output(PWRKEY_PIN, GPIO.LOW)

        print(f"Waiting {POST_POWER_DELAY}s for modem...")
        time.sleep(POST_POWER_DELAY)

        print("Modem power toggle done!")
        log_message("Modem power toggle done!")

    except Exception as e:
        print(f"{RED}Error while toggling modem power: {e}{RESET}")

    finally:
        GPIO.cleanup()

# ---------------------------
# Main Execution
# ---------------------------
if __name__ == "__main__":
    toggle_modem_power()

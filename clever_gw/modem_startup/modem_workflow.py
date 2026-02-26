# /////////////////////////////////////////////////////////////////////////////////////////////////////
# FileName   : modem_workflow.py
# Owner      : Mohammad Mahdi Mohammadi  (Mahdi.mohammadi@cortus.com)
# Date       : 12/11/2025
# Description: Top Module is for performing the full workflow
# (power up + initializing + tcp + http test) of the the modem (SIM7070G)
# /////////////////////////////////////////////////////////////////////////////////////////////////////
import sys
import time
import modem_power
import modem_initializer
import tcp_test
import modem_logger
import http_test
import ping_test

# ANSI color codes
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
RESET = "\033[97m"
CYAN = "\033[36m"

MAX_RETRIES = 3
modem_logger.log_message(f"\n>>>>>>>> TEST START POINT")
modem_power.toggle_modem_power()
for attempt in range(1, MAX_RETRIES + 1):
    if modem_initializer.modem_handshake():
        TCP_CONTEXT_ID = modem_initializer.initialize_modem()
        if TCP_CONTEXT_ID is None:
            print(f"{RED}PDP activation failed. Skipping the workflow.{RESET}")
            sys.exit(1)
        ping_test.main()
        tcp_test.main_workflow(TCP_CONTEXT_ID)
        http_test.main()
        break  # success, exit loop
    else:
        print(f"{YELLOW}Modem not responding. Power cycle attempt {attempt}...{RESET}")
        modem_logger.log_message(f"Modem not responding. Power cycle attempt {attempt}...")
        modem_power.toggle_modem_power()
        time.sleep(1)  # let modem boot
else:
    # If loop completes without break
    print(f"{RED}ERROR: Modem still not responding after power cycles.{RESET}")
    print(f"{YELLOW}Verify power, cabling, and reset sequence.{RESET}")
    print(f"{CYAN}-----------------------------------------------------------------{RESET}")
    modem_logger.log_message("ERROR: Modem still not responding after power cycles.")
modem_logger.log_message(f"\n>>>>>>>> TEST END POINT")
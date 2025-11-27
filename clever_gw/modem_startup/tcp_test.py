# /////////////////////////////////////////////////////////////////////////////////////////////////////
# FileName   : tcp_test.py
# Owner      : Mohammad Mahdi Mohammadi (Mahdi.mohammadi@cortus.com)
# Date       : 12/11/2025
# Description: This module includes commands for testing of establishing a TCP connection
# /////////////////////////////////////////////////////////////////////////////////////////////////////

# Import required modules
import serial                        # For serial communication with the modem
import time                          # To add delays between operations
from modem_logger import log_message # To record modem commands and responses
import ipaddress                     # To check if IP address is valid

# ---------------------------
# Configuration
# ---------------------------
AT_PORT = '/dev/ttyUSB5'      # Clean AT port
BAUDRATE = 115200             # Serial communication baud rate
SERIAL_TIMEOUT = 1            # seconds

# ---------------------------
# ANSI color codes
# ---------------------------
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
RESETW = "\033[97m"
RESETA = "\033[0m"
CYAN = "\033[36m"
BOLD = "\033[1m"

# ---------------------------
# Helper to send AT command and read full response
# ---------------------------
def send_and_wait(cmd, ser, timeout=5):
    ser.reset_input_buffer()
    ser.write(cmd.encode() + b'\r\n')
    log_message(f"{cmd}")
    # print(">>> ", cmd)
    ser.flush()
    end_time = time.time() + timeout
    lines = []
    while time.time() < end_time:
        line = ser.readline().decode(errors="ignore").strip()
        if line:
            lines.append(line)
            log_message(f"{line}")
            # print("<<< ",  line)
            if line == "OK" or line.startswith("ERROR") or line.startswith("+CME ERROR"):
                return lines
    print(f"{RED}Timeout waiting for response to: {cmd}{RESETW}")
    return lines

# -------------------------------
# TCP CLIENT SESSION
# ------------------------------
def tcp_client_session(TCP_CONTEXT_ID):

    # -------------------------------
    # Starting communication
    # -------------------------------
    with serial.Serial(AT_PORT, BAUDRATE, timeout=SERIAL_TIMEOUT) as ser:
        time.sleep(1)
        # -------------------------------
        # TCP TEST (using tcpbin.com or user data)
        # -------------------------------
        print(f"Starting TCP test session...")
        TCP_CONN_ID = 0  # First TCP connection
        # -------------------------------
        # Select server
        # -------------------------------
        while True:
            server_input = input(
                f"\nSelect TCP test server by entering the number:\n"
                " 1 - TCPBIN (public echo server)\n"
                " 2 - Enter a custom server\n"
                f"Your choice (1 or 2): "
            ).strip()
            if server_input in ["1", "2"]:
                break
            print(f"{RED}Invalid selection. Please enter 1 or 2.{RESETW}")
        if server_input == "1":
            SERVER_IP = "45.79.112.203"
            SERVER_PORT = 4242
        elif server_input == "2":
            # Keep asking until the user enters a valid IP
            while True:
                SERVER_IP = input(f"Enter TCP test server IP: ").strip()
                try:
                    ipaddress.ip_address(SERVER_IP)
                    break
                except ValueError:
                    print(f"{RED}Invalid IP address. Please enter a valid IPv4 or IPv6 address.{RESETW}")
            # Port check
            while True:
                try:
                    SERVER_PORT = int(input(f"Enter the TCP port number:"))
                    if 1 <= SERVER_PORT <= 65535:
                        break
                    else:
                        print(f"{RED}Port must be between 1 and 65535. Try again.{RESETW}")
                except ValueError:
                    print(f"{RED}Invalid input. Enter a numeric port.{RESETW}")
        print(f"TCP server set to {BOLD}{GREEN}{SERVER_IP}:{SERVER_PORT}{RESETA}{RESETW}")
        # -------------------------------
        # Open TCP connection with retries
        # -------------------------------
        MAX_TCP_RETRIES = 3
        TCP_RETRY_DELAY = 5
        print(f"\n===== OPEN TCP CONNECTION =====")
        print(f"TCP_CONTEXT_ID is {GREEN}{TCP_CONTEXT_ID}{RESETW}")
        print(f"Disabling SSL for TCP connection {GREEN}{TCP_CONN_ID}{RESETW}")
        resp = send_and_wait(f'AT+CASSLCFG={TCP_CONN_ID},"SSL",0', ser)
        connection_ok = False
        for attempt in range(1, MAX_TCP_RETRIES + 1):
            print(f"Attempt {GREEN}{attempt}{RESETW} to open TCP connection with PDP context: {GREEN}{TCP_CONTEXT_ID}{RESETW}...")
            resp = send_and_wait(f'AT+CAOPEN={TCP_CONN_ID},{TCP_CONTEXT_ID},"TCP","{SERVER_IP}",{SERVER_PORT}', ser)
            for line in resp:
                if line not in ("OK", ""):
                    if line.startswith(f"+CAOPEN: {TCP_CONN_ID},0"):
                        connection_ok = True
            if connection_ok:
                print(f"TCP connection {GREEN}{TCP_CONN_ID}{RESETW} established successfully!")
                break
            else:
                if attempt < MAX_TCP_RETRIES:
                    print(f"{YELLOW}TCP connection attempt {attempt} failed, trying to close the connection in {TCP_RETRY_DELAY}s...{RESETW}")
                    resp = send_and_wait(f'AT+CACLOSE={TCP_CONN_ID}', ser)
                    time.sleep(TCP_RETRY_DELAY)
                else:
                    print(f"{RED}Failed to open TCP connection {TCP_CONN_ID} after {MAX_TCP_RETRIES} attempts. Aborting test.{RESETW}")
                    return
        # -------------------------------
        # Send test data
        # -------------------------------
        resp = send_and_wait(f'AT+CASTATE?', ser)
        connection_active = any(line.startswith(f"+CASTATE: {TCP_CONN_ID},1") for line in resp)
        if connection_active:
            data_to_send = "Hello world!\n"
            print(f"\n===== SEND DATA =====")
            ser.reset_input_buffer()
            ser.write(f'AT+CASEND={TCP_CONN_ID},{len(data_to_send)}\r\n'.encode())
            start_time = time.time()
            while True:
                if time.time() - start_time > 5:
                    print(f"{RED}Timeout waiting for '>' prompt{RESETW}")
                    break
                line = ser.readline().decode(errors="ignore").strip()
                if line == ">":
                    ser.write(data_to_send.encode())
                    print(f"Data sent: {GREEN}{data_to_send.strip()}{RESETW}")
                    break
        else:
            print(f"{RED}TCP connection {TCP_CONN_ID} is not active. Cannot send data.{RESETW}")
            return
        # -------------------------------
        # Receive data
        # -------------------------------
        print(f"\n===== RECEIVE DATA =====")
        timeout = 10
        start_time = time.time()
        received = False
        while time.time() - start_time < timeout:
            resp = send_and_wait(f'AT+CARECV={TCP_CONN_ID},100', ser)
            for line in resp:
                line = line.strip()
                if line.startswith("+CARECV:"):
                    parts = line.split(",", 1)
                    if len(parts) == 2:
                        data = parts[1]
                        print(f"Received: {GREEN}{data.strip()}{RESETW}")
                        received = True
            if received:
                break
            time.sleep(1)
        if not received:
            print(f"{YELLOW}No echoed data received within timeout.{RESETW}")
        # -------------------------------
        # Close TCP connection
        # -------------------------------
        print(f"\n===== CLOSE TCP CONNECTION =====")
        resp = send_and_wait(f'AT+CACLOSE={TCP_CONN_ID}', ser)
        for line in resp:
            if line not in ("OK", ""):
                print(line)
        print(f"TCP connection closed!")

def main():
    print(f"{CYAN}\n--------------------------- TCP Test ----------------------------{RESETW}")
    while True:
        try:
            user_input = int(input(f"Enter TCP context ID (1–4): ").strip())
            if 1 <= user_input <= 4:
                TCP_CONTEXT_ID = user_input
                break
            else:
                print(f"{RED}Invalid range. Please enter a number between 1 and 4.{RESETW}")
        except ValueError:
            print(f"{RED}Invalid input. Please enter a number between 1 and 4.{RESETW}")
    tcp_client_session(TCP_CONTEXT_ID)
    print(f"{CYAN}------------------------- Test Finished -------------------------\n{RESETW}")

def main_workflow(TCP_CONTEXT_ID):
    print(f"{CYAN}\n--------------------------- TCP Test ----------------------------{RESETW}")
    while True:
        user_input = input(f"{RESETW}Do you want to perform a TCP client test? {GREEN}(yes/no){RESETW}: ")
        if user_input.lower() in ["yes", "y", "no", "n"]:
            if user_input.lower() in ["yes", "y"]:
                tcp_client_session(TCP_CONTEXT_ID)
                break
            else:
                print(f"{YELLOW}TCP test skipped.{RESETW}")
                break
        else:
            print(f"{RED}Invalid selection. Please enter [y] yes or [n] no.{RESETW}")
    print(f"{CYAN}------------------------- Test Finished -------------------------\n{RESETW}")


# ---------------------------
# Entry point
# ---------------------------
if __name__ == "__main__":
    main()

# /////////////////////////////////////////////////////////////////////////////////////////////////////
# FileName   : ping_test.py
# Owner      : Mohammad Mahdi Mohammadi (Mahdi.mohammadi@cortus.com)
# Date       : 23/02/2026
# Description: IPv4 ICMP Ping test for SIM7070G modem on Raspberry Pi
# Uses AT+CNACT, AT+SNPDPID, AT+SNPING4 to validate IP connectivity over NB-IoT
# /////////////////////////////////////////////////////////////////////////////////////////////////////

import requests
import serial
import time
from modem_logger import log_message

# ---------------------------
# Serial Port Configuration
# ---------------------------
AT_PORT = '/dev/ttyUSB5'   # USB port connected to SIM7070G
BAUDRATE = 115200          # Typical baud rate for SIM7070G
SERIAL_TIMEOUT = 1         # Serial read timeout (seconds)

# ---------------------------
# Default Ping Parameters
# ---------------------------
CLEVER_HOST = "4.175.145.21"
DEFAULT_HOST = "8.8.8.8"
DEFAULT_COUNT = 4
DEFAULT_TIMEOUT = 1000     # ms
DEFAULT_PACKET_SIZE = 32   # bytes

# ---------------------------
# ANSI Color Codes
# ---------------------------
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
RESETW = "\033[97m"
CYAN   = "\033[36m"
BLUE   = "\033[34m"

# ---------------------------
# Function: send_and_wait
# Sends an AT command and reads response lines.
# ---------------------------
def send_and_wait(cmd, ser, timeout=2):
    ser.reset_input_buffer()
    ser.write(cmd.encode() + b'\r\n')
    log_message(cmd)
    print(">>> ", cmd)
    ser.flush()

    end_time = time.time() + timeout
    lines = []

    while time.time() < end_time:
        line = ser.readline().decode(errors="ignore").strip()
        if line:
            lines.append(line)
            log_message(line)
            print("<<< ", line)
            # Stop reading if command completed successfully
            if line == "OK" or "ERROR" in line:
                break
    return lines

# ---------------------------
# Function: get_ip_location
# ---------------------------
def get_ip_location(ip):
    """Return city, region, country and ISP for a given IP"""
    try:
        resp = requests.get(f"http://ip-api.com/json/{ip}", timeout=5).json()
        if resp.get("status") == "success":
            country = resp.get("country", "Unknown")
            region = resp.get("regionName", "Unknown")
            city = resp.get("city", "Unknown")
            isp = resp.get("isp", "Unknown")
            return f"{city}, {region}, {country} (ISP: {isp})"
        else:
            return "Location not found"
    except Exception:
        return "Location not found"

# ---------------------------
# Function: perform_ipv4_ping
# Uses already activated PDP
# ---------------------------
def perform_ipv4_ping(ser, host, count=DEFAULT_COUNT, packet_size=DEFAULT_PACKET_SIZE, timeout_ms=DEFAULT_TIMEOUT):
    print(f"\n{CYAN}===== STARTING IPv4 PING TEST ====={RESETW}")
    print(f"{BLUE}Target:{RESETW} {host}")
    print(f"{BLUE}Count:{RESETW} {count}")
    print(f"{BLUE}Timeout:{RESETW} {timeout_ms} ms")
    print(f"{BLUE}Packet Size:{RESETW} {packet_size} bytes\n")
    # Send IPv4 ping directly
    cmd = f'AT+SNPING4="{host}",{count},{packet_size},{timeout_ms}'
    resp = send_and_wait(cmd, ser, timeout=20)
    # Parse results
    transmitted = received = 0
    print(f"\nPing Results:")
    for line in resp:
        if line.startswith("+SNPING4:"):
            parts = line.split(":")[1].strip().split(",")
            if len(parts) == 3:
                seq, ip, delay = parts
                print(f"{GREEN} Seq {seq} | IP: {ip} | Delay: {delay} ms{RESETW}")
                transmitted += 1
                if int(delay) >= 0:
                    received += 1
    lost = transmitted - received
    print(f"\nPing Statistics:")
    print(f"{GREEN} Transmitted: {transmitted}")
    print(f" Received   : {received}")
    print(f" Lost       : {lost}{RESETW}")
    if "OK" not in resp:
        print(f"{YELLOW}Ping may have some errors, check modem output.{RESETW}")

# ---------------------------
# Function: user_confirmation
# ---------------------------
def user_confirmation(prompt):
    while True:
        choice = input(prompt).lower()
        if choice in ["yes", "y", "no", "n"]:
            return choice in ["yes", "y"]
        print(f"{RED}Invalid input. Please enter yes/y or no/n.{RESETW}")

# ---------------------------
# Main routine
# ---------------------------
def main():
    print(f"{CYAN}\n------------------------ IPv4 ICMP Ping Test ------------------------{RESETW}")

    with serial.Serial(AT_PORT, BAUDRATE, timeout=SERIAL_TIMEOUT) as ser:
        time.sleep(1)

        if not user_confirmation("Perform IPv4 ICMP ping test? (yes/no): "):
            print(f"{YELLOW}Ping test skipped.{RESETW}")
            return

        host = input(f"Enter target host, Agricolus is {CLEVER_HOST}, Default is {DEFAULT_HOST} : ").strip()
        if not host:
            host = DEFAULT_HOST

        # Get and display physical location
        location = get_ip_location(host)
        print(f"\n{BLUE}Target Location:{RESETW} {GREEN}{location}{RESETW}")

        perform_ipv4_ping(ser, host)

    print(f"{CYAN}------------------------- Test Finished -------------------------\n{RESETW}")

# ---------------------------
# Entry point
# ---------------------------
if __name__ == "__main__":
    main()
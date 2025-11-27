# /////////////////////////////////////////////////////////////////////////////////////////////////////
# FileName   : http_test.py
# Owner      : Mohammad Mahdi Mohammadi (Mahdi.mohammadi@cortus.com)
# Date       : 12/11/2025
# Description: HTTP/HTTPS GET test for SIM7070G modem on Raspberry Pi
# Supports multiple HTTPS servers with user selection
# /////////////////////////////////////////////////////////////////////////////////////////////////////

import serial
import time
import os
import json
from datetime import datetime
from modem_logger import log_message
from upload_ssl import upload_ssl_certificate

# ---------------------------
# Serial Port Configuration
# ---------------------------
AT_PORT = '/dev/ttyUSB5'   # USB port connected to SIM7070G
BAUDRATE = 115200          # Typical baud rate for SIM7070G
SERIAL_TIMEOUT = 1         # Serial read timeout (seconds)

# ---------------------------
# HTTP/HTTPS Parameters
# ---------------------------
HTTP_BODYLEN = 1024        # Maximum HTTP response body length (in bytes)
HTTP_HEADERLEN = 350       # Maximum HTTP response header length (in bytes)

# URLs and paths
HTTPBIN_URL = "http://httpbin.org"
HTTPBIN_PATH = "/get?user=jack&password=123"
CLEVER_URL = "https://agricolus.staging.api.k.agricolus.com"
CLEVER_PATH = "/api/clever/modelresults"

# HTTP headers
COMMON_HEADERS = {
    "User-Agent": "CORTUS_SIM7070G",
    "Cache-control": "no-cache",
    "Connection": "keep-alive",
    "Accept": "*/*"
}

HTTPS_HEADERS = {
    **COMMON_HEADERS,
    "Accept": "application/json"
}

JSON_HEADERS = {
    "User-Agent": "CORTUS_SIM7070G",
    "Content-Type": "application/json",
    "Cache-control": "no-cache",
    "Connection": "keep-alive",
    "Accept": "*/*"
}

AGRICOLUS_HEADERS = {
    "User-Agent": "CORTUS_SIM7070G",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Cache-control": "no-cache",
    "Connection": "keep-alive"
}

POST_BODY = {
    "deviceId": "CORTUS_SIM7070G",
    "oranges": 10,
    "maturity": [70, 75, 80],
    "avgMaturity": 75,
    "dimensions": [4, 5, 6],
    "avgDimensions": 5,
    "weights": [100, 105, 110],
    "avgWeights": 105,
    "sourceImages": 12,
    "date": datetime.utcnow().isoformat() + "Z",  # ISO 8601 UTC
    "execTime": 120  # in seconds
}

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
            print("<<< ",  line)
            # Continue reading even after OK/ERROR
            if line in ("OK", "ERROR") or line.startswith(("+CME ERROR", "+CMS ERROR")):
                continue
    return lines

# ---------------------------
# Function: parse_shreq_response
# Extracts HTTP response code and data length from +SHREQ response
# ---------------------------
def parse_shreq_response(resp):
    http_code = None
    data_len = None
    for line in resp:
        if "+SHREQ:" in line:
            parts = line.split(",")
            if len(parts) >= 3:
                http_code = parts[1].strip()
                data_len = parts[2].strip()
    return http_code, data_len

# ---------------------------
# Function: configure_headers
# Clears previous headers and sets new headers
# ---------------------------
def configure_headers(ser, headers):
    send_and_wait("AT+SHCHEAD", ser)
    for key, value in headers.items():
        resp = send_and_wait(f'AT+SHAHEAD="{key}","{value}"', ser)
        if "OK" in resp:
            print(f"{key} header set to {GREEN}{value}{RESETW}")

# ---------------------------
# Function: open_connection
# Opens HTTP/HTTPS connection with retries
# ---------------------------
def open_connection(ser, url, max_retries=5, retry_delay=5):
    send_and_wait("AT+SHDISC", ser)  # Close existing session
    send_and_wait(f'AT+SHCONF="URL","{url}"', ser)
    send_and_wait(f'AT+SHCONF="BODYLEN",{HTTP_BODYLEN}', ser)
    send_and_wait(f'AT+SHCONF="HEADERLEN",{HTTP_HEADERLEN}', ser)
    for attempt in range(1, max_retries + 1):
        send_and_wait("AT+SHCONN", ser, timeout=10)
        state_resp = send_and_wait("AT+SHSTATE?", ser)
        if any("+SHSTATE: 1" in line for line in state_resp):
            print(f"{GREEN}Connection established successfully! (attempt {attempt}){RESETW}")
            return True
        else:
            print(f"{YELLOW}Failed to connect. Retrying in {retry_delay}s...{RESETW}")
            time.sleep(retry_delay)
    print(f"{RED}Unable to establish connection.{RESETW}")
    return False

# ---------------------------
# Function: read_response
# Reads and prints the HTTP(S) response body
# ---------------------------
def read_response(ser, data_len):
    if data_len and data_len.isdigit() and int(data_len) > 0:
        resp = send_and_wait(f'AT+SHREAD=0,{data_len}', ser, timeout=15)
        print("\nReceived data:")
        for line in resp:
            if not line.startswith(("+SHREAD", "OK")):
                print(f"{BLUE}{line}{RESETW}")
    else:
        print(f"{YELLOW}No data available to read.{RESETW}")

# ---------------------------
# Function: perform_get
# Performs GET request for HTTP or HTTPS
# ---------------------------
def perform_get(ser, url, path, headers, use_https=False, cert_file=None):
    if use_https and cert_file:
        upload_ssl_certificate(ser, cert_file)
        send_and_wait('AT+CSSLCFG="sslversion",1,3', ser)
        send_and_wait('AT+SHSSL=1,""', ser)
    if open_connection(ser, url):
        configure_headers(ser, headers)
        print(f"\n===== SEND GET REQUEST =====\n{GREEN}{path}{RESETW}")
        resp = send_and_wait(f'AT+SHREQ="{path}",1', ser, timeout=15)
        http_code, data_len = parse_shreq_response(resp)
        if http_code: print(f"Response Code: {GREEN}{http_code}{RESETW}")
        if data_len: print(f"Data Length: {GREEN}{data_len}{RESETW}")
        read_response(ser, data_len)
        send_and_wait("AT+SHDISC", ser)
        print(f"{CYAN}Connection closed.{RESETW}")

# ---------------------------
# Function: perform_post
# Performs POST request for HTTP or HTTPS using JSON body
# ---------------------------
def perform_post(ser, url, path, headers, body_params, cert_file=None, expect_echo=True):
    """
    ser         : serial object
    url         : server URL
    path        : request path
    headers     : dict with HTTP headers
    body_params : dict for JSON POST
    cert_file   : SSL certificate file path
    expect_echo : True if we want to read/print response
    """
    # SSL setup if HTTPS
    if cert_file and os.path.exists(cert_file):
        upload_ssl_certificate(ser, cert_file)
        send_and_wait('AT+CSSLCFG="sslversion",1,3', ser)
        send_and_wait('AT+SHSSL=1,""', ser)  # skip verification if empty
    # Open connection
    if not open_connection(ser, url):
        print(f"{RED}POST aborted due to connection failure.{RESETW}")
        return
    # Configure headers
    configure_headers(ser, headers)
    # Convert body dict to JSON string
    body_str = json.dumps(body_params)
    body_len = len(body_str)
    print(f"\n===== SEND POST REQUEST =====\n{GREEN}{path}{RESETW}")
    print(f"{CYAN}Body: {body_str}{RESETW}")
    # Set HTTP body
    resp = send_and_wait(f'AT+SHBOD={body_len},10000', ser)
    # Wait for prompt ">"
    time.sleep(0.5)
    ser.write(body_str.encode() + b'\r\n')
    log_message(body_str)
    print(f">>> {body_str}")
    # Send POST request
    resp = send_and_wait(f'AT+SHREQ="{path}",3', ser, timeout=15)
    http_code, data_len = parse_shreq_response(resp)
    if http_code:
        print(f"Response Code: {GREEN}{http_code}{RESETW}")
    if data_len:
        print(f"Data Length: {GREEN}{data_len}{RESETW}")
    # Read response if needed
    if expect_echo:
        read_response(ser, data_len)
    # Disconnect
    send_and_wait("AT+SHDISC", ser)
    print(f"{CYAN}Connection closed.{RESETW}")

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
    print(f"{CYAN}\n------------------------ HTTP/HTTPS Test ------------------------{RESETW}")
    with serial.Serial(AT_PORT, BAUDRATE, timeout=SERIAL_TIMEOUT) as ser:
        time.sleep(1)
        # HTTP GET test
        if user_confirmation("Perform HTTP GET test? (yes/no): "):
            perform_get(ser, HTTPBIN_URL, HTTPBIN_PATH, COMMON_HEADERS)
        else:
            print(f"{YELLOW}HTTP test skipped.{RESETW}")
        # HTTPS GET test with server choice
        if user_confirmation("Perform HTTPS GET test? (yes/no): "):
            HTTPS_SERVERS = {
                "1": {"name": "HTTPIN Echo Server", "url": HTTPBIN_URL, "path": HTTPBIN_PATH, "cert": "httpbin.cer"},
                "2": {"name": "Agricolus API", "url": CLEVER_URL, "path": CLEVER_PATH, "cert": "agricolus.cer"}
            }
            print("Choose HTTPS server to test:")
            for key, info in HTTPS_SERVERS.items():
                print(f" {key}) {info['name']}")
            while True:
                choice = input("Enter 1 or 2: ").strip()
                if choice in HTTPS_SERVERS:
                    server = HTTPS_SERVERS[choice]
                    cert_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), server["cert"])
                    perform_get(ser, server["url"], server["path"], HTTPS_HEADERS,
                                use_https=True, cert_file=cert_path)
                    break
                else:
                    print(f"{RED}Invalid selection. Please enter 1 or 2.{RESETW}")
        else:
            print(f"{YELLOW}HTTPS test skipped.{RESETW}")

        # HTTPS POST test with server choice
        if user_confirmation("Perform HTTPS POST test? (yes/no): "):
            HTTPS_SERVERS = {
                "1": {"name": "HTTPIN Echo Server", "url": HTTPBIN_URL, "path": "/post", "cert": "httpbin.cer", "echo":True},
                "2": {"name": "Agricolus API", "url": CLEVER_URL, "path": CLEVER_PATH, "cert": "agricolus.cer", "echo":False}
            }
            print("Choose HTTPS server to POST:")
            for key, info in HTTPS_SERVERS.items():
                print(f" {key}) {info['name']}")
            while True:
                choice = input("Enter 1 or 2: ").strip()
                if choice in HTTPS_SERVERS:
                    server = HTTPS_SERVERS[choice]
                    cert_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), server["cert"])
                    perform_post(
                        ser,
                        server["url"],
                        server["path"],
                        JSON_HEADERS,
                        POST_BODY,
                        cert_file=cert_path,
                        expect_echo=server["echo"]
                    )
                    break
                else:
                    print(f"{RED}Invalid selection. Please enter 1 or 2.{RESETW}")

    print(f"{CYAN}------------------------- Test Finished -------------------------\n{RESETW}")

# ---------------------------
# Entry point
# ---------------------------
if __name__ == "__main__":
    main()

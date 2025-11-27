# /////////////////////////////////////////////////////////////////////////////////////////////////////
# FileName   : upload_ssl.py
# Owner      : Mohammad Mahdi Mohammadi (Mahdi.mohammadi@cortus.com)
# Date       : 12/11/2025
# Description: SSL Certificate uploader for SIM7070G
# /////////////////////////////////////////////////////////////////////////////////////////////////////

import serial
import time
import os
from modem_logger import log_message  # import your logging module

# ----------------------------
# Configuration
# ----------------------------
AT_PORT = '/dev/ttyUSB5'      # Clean AT port
BAUDRATE = 115200             # Check SIM7070 default baudrate
SERIAL_TIMEOUT = 2            # seconds
actual_cert = "agricolus.cer" # Certificate file's name (for stand alone run only)

# ---------------------------
# ANSI color codes
# ---------------------------
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
RESETW = "\033[97m"
CYAN   = "\033[36m"

# ---------------------------
# General helper to send AT command and read response
# ---------------------------
def send_and_wait(cmd, ser, wait_for=None, timeout=5):
    try:
        ser.reset_input_buffer()
        ser.write((cmd + "\r\n").encode())
        ser.flush()
        log_message(cmd)
        end_time = time.time() + timeout
        lines = []
        while time.time() < end_time:
            if ser.in_waiting:
                line = ser.readline().decode(errors="ignore").strip()
                if line:
                    lines.append(line)
                    log_message(line)

                    if wait_for and wait_for in line:
                        break

                    if not wait_for and (line in ("OK", "ERROR") or line.startswith(("+CME ERROR", "+CMS ERROR"))):
                        break
            time.sleep(0.05)
        return lines
    except Exception as e:
        log_message(str(e))
        return [f"ERROR: {e}"]

# ----------------------------
# Upload SSL certificate
# Upload and convert a certificate on SIM7070 modem.
# Follows SIMCOM application note procedure.
# ----------------------------
def upload_ssl_certificate(ser, cert_filepath):
    if not os.path.exists(cert_filepath):
        print(f"{RED}ERROR! Certificate '{cert_filepath}' not found{RESETW}")
        return False
    file_size = os.path.getsize(cert_filepath)
    cert_name = os.path.basename(cert_filepath)
    print(f"{CYAN}-----------------------------------------------------------------{RESETW}")
    print(f"Uploading SSL certificate {GREEN}'{cert_name}' ({file_size} bytes){RESETW}")
    # 1. Initialize FS
    send_and_wait("AT+CFSINIT", ser)
    time.sleep(0.5)
    # 2. Reset FS (optional, ensures clean buffer)
    send_and_wait("AT+CFSTERM", ser)
    time.sleep(0.2)
    send_and_wait("AT+CFSINIT", ser)
    time.sleep(0.5)
    # 3. Prepare modem to accept file upload
    timeout_ms = max(5000, file_size)
    resp = send_and_wait(f'AT+CFSWFILE=3,"{cert_name}",0,{file_size},{timeout_ms}', ser, wait_for="DOWNLOAD")
    if not any("DOWNLOAD" in line for line in resp):
        print("{RED}ERROR! No DOWNLOAD prompt from modem. Aborting.")
        return False
    # 4. Send file as continuous stream
    with open(cert_filepath, "rb") as f:
        ser.write(f.read())
        ser.flush()
    print(f"Sent file '{cert_name}' ({file_size} bytes) to modem")
    # Wait for modem to process
    time.sleep(1.5)
    response = ser.read_all().decode(errors="ignore")
    if "OK" not in response:
        print(f"{RED}ERROR! Upload failed: modem did not confirm OK{RESETW}")
        send_and_wait("AT+CFSTERM", ser)
        return False
    print(f"Certificate '{cert_name}' uploaded {GREEN}successfully{RESETW}")
    # 5. Close FS
    send_and_wait("AT+CFSTERM", ser)
    # 6. Convert certificate
    resp = send_and_wait(f'AT+CSSLCFG="convert",2,"{cert_name}"', ser)
    if any("OK" in line for line in resp):
        print(f"Certificate '{cert_name}' converted and ready!")
        print(f"{CYAN}-----------------------------------------------------------------{RESETW}")
        return True
    else:
        # Meaningful warning message
        print(f"{YELLOW}WARNING! Certificate conversion failed for '{cert_name}'. "
              f"This usually means a certificate with the same name already exists in the modem storage. "
              f"Consider deleting the old certificate first using AT+CSSLCFG=\"del\",2,\"{cert_name}\"{RESETW}")
        return False

# ----------------------------
# Main test routine
# ----------------------------
def main():
    # Open serial port with RTS/CTS flow control
    with serial.Serial(AT_PORT, BAUDRATE, timeout=SERIAL_TIMEOUT, rtscts=True) as ser:
        time.sleep(1)  # allow modem to initialize
        # Attempt to upload actual certificate
        if os.path.exists(actual_cert):
            success = upload_ssl_certificate(ser, actual_cert)
            print(f"Actual upload result: {GREEN}{success}{RESETW}")
        else:
            print(f"{YELLOW}WARNING! Actual certificate '{actual_cert}' not found, skipping.{RESETW}")

if __name__ == "__main__":
    main()

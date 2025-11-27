# /////////////////////////////////////////////////////////////////////////////////////////////////////
# FileName   : modem_initializer.py
# Owner      : Mohammad Mahdi Mohammadi (mahdi.mohammadi@cortus.com)
# Date       : 12/11/2025
# Description: Modular initialization and check of SIM7070G modem
# /////////////////////////////////////////////////////////////////////////////////////////////////////

# Import required modules
import serial                        # For serial communication with the modem
import time                          # To add delays between operations
import ipaddress                     # To check if IP address is valid
import sys                           # To stop the script wherever it's needed
import re                            # To extract numbers from modem responses
import modem_logger                  # To record modem commands and responses

# ---------------------------
# Configuration
# ---------------------------
AT_PORT = '/dev/ttyUSB5'      # Clean AT port
# AT_PORT = '/dev/ttyS0'      # Clean AT port
BAUDRATE = 115200             # Serial communication baud rate
SERIAL_TIMEOUT = 1            # seconds
EXPECTED_APN = "iot.1nce.net" # Correct APN for 1NCE

# ANSI color codes
RESET = "\033[97m"
BOLD = "\033[1m"
WHITE = "\033[97m"
GREEN = "\033[32m"
YELLOW = "\033[93m"
RED = "\033[31m"
RESETA = "\033[0m"
CYAN   = "\033[36m"

# ---------------------------
# Helper functions
# Send AT command and wait for modem response, return list of response lines.
# ---------------------------
def send_and_wait(cmd, ser, timeout=5):
    ser.reset_input_buffer()
    ser.write(cmd.encode() + b'\r\n')
    modem_logger.log_message(f"{cmd}")
    ser.flush()
    end_time = time.time() + timeout
    lines = []
    while time.time() < end_time:
        line = ser.readline().decode(errors="ignore").strip()
        if line:
            lines.append(line)
            modem_logger.log_message(f"{line}")
            if line == "OK" or line.startswith("ERROR") or line.startswith("+CME ERROR"):
                return lines
    print(f"{YELLOW}Timeout waiting for response to: {cmd}{RESET}")
    return lines

# -------------------------------
# AT CHECK
# A quick check to see if the modem is connected and alive before sending more AT commands.
# -------------------------------
def modem_handshake():
    print(f"\n{CYAN}------------------- Modem Connectivity Check --------------------{RESET}")
    print(f"Starting Modem check and 1NCE SIM preparation procedure!")
    print("===== MODEM HANDSHAKE =====")
    try:
        # Create a serial connection
        ser = serial.Serial(AT_PORT, BAUDRATE, timeout=SERIAL_TIMEOUT)
        # Wait 1 second after opening the port to let modem get ready
        time.sleep(1)
        # Send basic AT command (modem handshake)
        ser.write(b'AT\r\n')
        modem_logger.log_message("AT")
        # Read up to 64 bytes from the modem's response
        # decode() converts bytes to string, ignore errors if any
        response = ser.read(64).decode(errors="ignore")
        # Check if the response contains "OK" expected reply for a valid AT command
        if "OK" in response:
            # If modem replied correctly, log success and print on terminal
            print(f"Modem responded: {GREEN}OK{RESET}")
            modem_logger.log_message("OK")
            return True
        else:
            # If modem responded with anything else it's an error!
            print(f"{RED}Modem not responding.{RESET}")
            modem_logger.log_message(f"Unexpected modem response.")
            return False
    # If any error happens log it
    except Exception as e:
        print(f"{RED}Error communicating with modem:{RESET} {YELLOW}{e}{RESET}")
        modem_logger.log_message(f"Error communicating with modem: {e}")
        return False

# -------------------------------
# Set modem to full functionality
# Hey modem, are you fully on, partially off, or in flight mode?
# -------------------------------
def check_functionality(ser):
    print("===== FUNCTIONALITY =====")
    resp = send_and_wait('AT+CFUN?', ser)
    mode = None
    for line in resp:
        if "+CFUN:" in line:
            mode = line.split(":")[1].strip()
            if mode == "1":
                print(f"Modem is in {GREEN}full{RESET} functionality!")
                return True
    # Not in full mode — try to set it
    print(f"{YELLOW}Modem is in mode {mode or '?'} (not fully operational). Setting to full functionality...{RESET}")
    send_and_wait('AT+CFUN=1', ser)
    time.sleep(3)
    # Check again after setting it
    resp = send_and_wait('AT+CFUN?', ser)
    for line in resp:
        if "+CFUN:" in line:
            mode = line.split(":")[1].strip()
            if mode == "1":
                print(f"Modem successfully set to {GREEN}full{RESET} functionality!")
                return True
    # Still not functional
    print(f"{RED}Failed to set modem to full functionality!{RESET}")
    return False

# -------------------------------
# Check and Wait for SIM ready
# Is the SIM usable right now?
# -------------------------------
def check_sim_status(ser):
    print("\n===== SIM STATUS =====")
    sim_ready = False
    for _ in range(10):  # wait up to 10 seconds
        resp = send_and_wait('AT+CPIN?', ser)
        if any("READY" in line for line in resp):
            sim_ready = True
            break
        time.sleep(1)
    if not sim_ready:
        print(f"{RED}SIM not ready, aborting modem preparation.{RESET}")
        return False
    else:
        print(f"SIM status: {GREEN}Ready{RESET}")
        return True

# -------------------------------
# Check signal strength
# How strong is my connection to the cellular network?
# -------------------------------
def check_signal(ser):
    print("\n===== SIGNAL STRENGTH =====")
    MAX_SIGNAL_RETRIES = 5
    SIGNAL_DELAY = 30
    for attempt in range(1, MAX_SIGNAL_RETRIES + 1):
        print(f"Attempt: {attempt}")
        resp = send_and_wait('AT+CSQ', ser)
        for line in resp:
            if "+CSQ:" in line:
                try:
                    rssi = int(line.split(":")[1].split(",")[0].strip())
                    if rssi == 99:
                        raise ValueError
                    dbm = -113 + (rssi * 2)
                    print(f"Signal strength: {GREEN}{rssi} ({dbm} dBm){RESET}")
                    return True
                except ValueError:
                    pass
        if (attempt!=5):
            print(f"{YELLOW}Signal unknown. Waiting {SIGNAL_DELAY}s to retry...{RESET}")
            time.sleep(SIGNAL_DELAY)
    print(f"{RED}No valid signal detected.{RESET}")
    print(f"{YELLOW}Check the antenna connection, reinsert the SIM, or move the modem to an open area.{RESET}")
    return False

# -------------------------------
# Check network attachment with retries
# Am I logged into the mobile network’s data side yet?
# -------------------------------
def check_network_attachment(ser):
    """Check network attachment status with retries."""
    print("\n===== NET ATTACHMENT =====")
    MAX_RETRIES = 5
    RETRY_DELAY = 20
    for attempt in range(1, MAX_RETRIES + 1):
        resp = send_and_wait('AT+CGATT?', ser)
        if any("+CGATT: 1" in line for line in resp):
            print(f"Packet network attached (attempt {attempt})")
            return True
        print(f"{YELLOW}Packet network not attached. Retrying in {RETRY_DELAY}s...{RESET}")
        time.sleep(RETRY_DELAY)
    print(f"{RED}Failed to attach to packet network.{RESET}")
    return False

# -------------------------------
# Check supported network modes
# Ask modem which network modes it can use
# -------------------------------
def print_supported_network_modes(ser):
    print("\n===== SUPPORTED NETWORK MODES =====")
    resp = send_and_wait('AT+CNMP=?', ser)
    # Mapping for human-readable mode names
    cnmp_human_map = {
        "2": "Automatic",
        "13": "GSM Only",
        "38": "LTE Only",
        "51": "GSM + LTE Only"}
    supported_modes = []
    for line in resp:
        if line.startswith("+CNMP:"):
            # Extract numbers from parentheses
            nums = re.findall(r'\d+', line)
            supported_modes.extend(nums)
    if supported_modes:
        print("Supported modes:")
        for m in sorted(set(supported_modes), key=int):
            mode_name = cnmp_human_map.get(m, f"Unknown ({m})")
            print(f"  - {mode_name}")
    else:
       print(f"{RED}No supported modes found.{RESET}")

# -------------------------------
# Check supported NB-IoT / Cat-M modes
# Ask modem which low-power wide-area network modes it can use
# -------------------------------
def print_supported_nb_iot_cat_m_modes(ser):
    print("\n===== SUPPORTED NB-IoT / CAT-M MODES =====")
    resp = send_and_wait('AT+CMNB=?', ser)
    # Mapping for human-readable NB-IoT / Cat-M modes
    cmnb_human_map = {
        "1": "Cat-M only",
        "2": "NB-IoT only",
        "3": "Cat-M + NB-IoT"}
    for line in resp:
        if line.startswith("+CMNB:"):
            # Extract numbers from the modem output
            matches = re.findall(r'\d+', line)
            print("Supported modes:")
            for m in matches:
                mode_name = cmnb_human_map.get(m, f"Unknown ({m})")
                print(f"  - {mode_name}")

# -------------------------------
# Configure network mode: LTE Only + Cat-M/NB-IoT
#Force LTE-only and enable Cat-M/NB-IoT modes.
# -------------------------------
def configure_network_modes(ser):
    print("\n===== NETWORK MODE CONFIGURATION =====")
    print("Setting LTE-only mode and enabling both Cat-M and NB-IoT...")
    access_tech_map = {
        "LTE NB-IOT": "Narrowband Internet of things (NB-IoT)",
        "LTE CAT-M": "LTE Cat M1 (eMTC)",
        "LTE": "LTE",
        "GSM": "GSM"}
    operator_map = {
        "22210": "Vodafone IT",
        "22201": "TIM IT",
        "22288": "WindTre IT",
        "22299": "Iliad IT",
        "26201": "Telekom DE",
        "26202": "Vodafone DE",
        "26203": "O2 DE",
        "00760": "Vodafone DE (1NCE roaming)",
        "0057003": "Vodafone DE (1NCE roaming)",
        "00760030003": "Vodafone DE (1NCE roaming)"}
    # 1. Disable radio temporarily
    send_and_wait("AT+CFUN=0", ser)
    time.sleep(3)
    # 2. Force LTE-only operation (no GSM)
    send_and_wait("AT+CNMP=38", ser)
    # 3. Enable both Cat-M and NB-IoT (auto-select)
    # print("Enabling both Cat-M and NB-IoT...")
    # send_and_wait("AT+CMNB=3", ser)
    # 3. Enable NB-IoT ONLY!
    print("Enabling NB-IoT...")
    send_and_wait("AT+CMNB=2", ser)
    # 4. Re-enable full radio functionality
    send_and_wait("AT+CFUN=1", ser)
    time.sleep(5)
    # 5. Poll network attachment until RAT is available or timeout
    MAX_WAIT = 30  # seconds
    interval = 10
    elapsed = 0
    attached = False
    while elapsed < MAX_WAIT:
        resp = send_and_wait("AT+CPSI?", ser)
        for line in resp:
            if line.startswith("+CPSI:") and "NO SERVICE" not in line:
                # Example: +CPSI: LTE NB-IOT,Online,222-10,0xB7F5,20087664,217,EUTRAN-BAND20,6353,0,0,-10,-79,-69,14
                attached = True
                try:
                    parts = line.split(":")[1].split(",")
                    rat = parts[0].strip()
                    state = parts[1].strip()
                    plmn = parts[2].strip()               # e.g. "222-10"
                    tac = parts[3].strip()                # e.g. 0xB7F5
                    cell_dec = parts[4].strip()           # e.g. 20087664
                    pci = parts[5].strip()
                    band = parts[6].strip()
                    earfcn = parts[7].strip()

                    # Defaults
                    rsrq = rssi = rsrp = sinr = "?"

                    if "NB-IOT" in rat or "CAT-M" in rat:
                        # Manual order for NB-IoT and Cat-M
                        rsrq = parts[10].strip()
                        rsrp = parts[11].strip()
                        rssi = parts[12].strip()
                        sinr = parts[13].strip() if len(parts) > 13 else "?"
                    elif "LTE" in rat:
                        # LTE sometimes uses the same order, keep it parallel
                        rsrq = parts[10].strip() if len(parts) > 10 else "?"
                        rsrp = parts[11].strip() if len(parts) > 11 else "?"
                        rssi = parts[12].strip() if len(parts) > 12 else "?"
                        sinr = parts[13].strip() if len(parts) > 13 else "?"
                    # Fix invalid RSRP value
                    if rsrp == "0":
                        rsrp = "N/A"

                    # Decode operator name
                    plmn_code = plmn.replace("-", "")
                    operator_name = operator_map.get(plmn_code, f"Unknown ({plmn})")
                    # Decode RAT name
                    access_tech_name = access_tech_map.get(rat, rat)
                    # Print clear, human-readable network info
                    print(f"\n===== NETWORK DETAILS ====={RESET}")
                    print(f"Connection type  : {GREEN}{access_tech_name}{RESET}")
                    print(f"Status           : {GREEN}{state}{RESET}")
                    print(f"Operator         : {GREEN}{operator_name}{RESET} (PLMN {plmn})")
                    print(f"Band / EARFCN    : {GREEN}{band} / {earfcn}{RESET}")
                    print(f"Cell ID          : {GREEN}{cell_dec}{RESET} (TAC {tac})")
                    print(f"Signal quality   : RSSI {GREEN}{rssi} dBm{RESET}, RSRQ {GREEN}{rsrq} dB{RESET}, RSRP {GREEN}{rsrp} dBm{RESET}, SINR {GREEN}{sinr} dB{RESET}")
                    if "NB-IOT" in rat:
                        print(f"Connected via    : {BOLD}{GREEN}Narrowband IoT (NB-IoT){RESETA}{RESET}")
                    elif "CAT-M" in rat:
                        print(f"Connected via    : {BOLD}{GREEN}LTE Cat-M1 (eMTC){RESETA}{RESET}")
                    elif "LTE" in rat:
                        print(f"Connected via    : {BOLD}{GREEN}LTE{RESETA}{RESET}")
                    elif "GSM" in rat:
                        print(f"Connected via    : {BOLD}{GREEN}GSM fallback{RESETA}{RESET}")
                    else:
                        print(f"{YELLOW}Unknown radio technology: {rat}{RESET}")
                except Exception as e:
                    print(f"{RED}Error parsing CPSI line: {line} ({e}){RESET}")
                    return False
        if attached:
            return True
        print(f"{YELLOW}Waiting for network registration...{RESET}")
        time.sleep(interval)
        elapsed += interval
    if not attached:
        print(f"{RED}Modem did not register on LTE-M / NB-IoT within timeout!{RESET}")
        return False

# -------------------------------
# Check current network/operator
# Hey modem, who am I talking to right now?
# -------------------------------
def check_operator(ser):
    # Mapping tables
    print("\n===== OPERATOR INFO =====")
    network_mode_map = {
        "0": "Automatic selection",
        "1": "Manual selection"}
    format_type_map = {
        "0": "Numeric",
        "1": "Long alphanumeric",
        "2": "Short alphanumeric"}
    # Access Technology codes for SIM7070G
    access_tech_map = {
        "0": "GSM",
        "2": "EDGE",
        "3": "UMTS",
        "4": "HSDPA",
        "5": "HSUPA",
        "6": "HSPA",
        "7": "LTE Cat M1 (eMTC)",
        "8": "LTE",
        "9": "Narrowband Internet of Things (NB-IoT)"}
    # Example mapping of numeric MCC+MNC codes to operator names
    operator_map = {
        "26201"  : "Telekom DE",
        "26202"  : "Vodafone DE",
        "26203"  : "O2 DE",
        "00760"  : "Vodafone DE (1NCE roaming)",
        "0057003": "Vodafone DE (1NCE roaming)",
        "00760030003": "Vodafone DE (1NCE roaming)"
        # add more as needed
        }
    resp = send_and_wait('AT+COPS?', ser)
    for line in resp:
        if line.startswith("+COPS:"):
            parts = line.split(":")[1].split(",")
            mode = parts[0].strip()
            format_type = parts[1].strip()
            operator_numeric = parts[2].strip().strip('"')
            access_tech = parts[3].strip() if len(parts) > 3 else "Unknown"
            # Human-readable names
            network_mode_name = network_mode_map.get(mode, f"Unknown ({mode})")
            format_type_name = format_type_map.get(format_type, f"Unknown ({format_type})")
            # mcc_mnc = operator_numeric[:5]  # first 5 digits usually
            operator_name = operator_map.get(operator_numeric, f"Unknown ({operator_numeric})")
            access_tech_name = access_tech_map.get(access_tech, f"Unknown ({access_tech})")
            print(f"Network mode     : {GREEN}{network_mode_name}{RESET}")
            print(f"Format type      : {GREEN}{format_type_name}{RESET}")
            print(f"Operator         : {GREEN}{operator_name}{RESET}")
            print(f"Access Technology: {GREEN}{access_tech_name}{RESET}")

# -------------------------------
# Check configured APN
# Which APN (Access Point Name) is configured for my data connection?
# -------------------------------
def check_apn(ser):
    print("\n===== APN CHECK =====")
    resp = send_and_wait('AT+CGNAPN', ser)
    apn_found = False
    context_id = None
    for line in resp:
        if line.startswith("+CGNAPN:"):
            parts = line.split(":")[1].split(",")
            context_id = parts[0].strip()
            apn = parts[1].strip().strip('"')
            print(f"{WHITE}Configured APN:{RESET} {GREEN}{apn}{RESET}")
            apn_found = True

    if not apn_found or apn != EXPECTED_APN:
        print(f"{YELLOW}APN is not correct, setting to {GREEN}{EXPECTED_APN}{RESET}...")
        send_and_wait(f'AT+CNCFG={context_id},1,"{EXPECTED_APN}"', ser)
    else:
        print("APN is correct, no changes needed.")
    return context_id

# -------------------------------
# PDP CONTEXT ACTIVATION ONLY (with retries)
# Do we have an activate PDP context, activate it if it's not
# -------------------------------
def activate_pdp_context(ser, context_id):
    print("\n===== PDP CONTEXT ACTIVATION =====")
    if context_id is None:
        print(f"{RED}No PDP context found! Cannot activate.{RESET}")
        return None  # Only return the IP
    # Check current PDP status
    resp = send_and_wait('AT+CNACT?', ser)
    for line in resp:
        if line.startswith("+CNACT:"):
            parts = line.split(":")[1].split(",")
            cid = parts[0].strip()
            state = parts[1].strip()
            ip = parts[2].strip().strip('"') if len(parts) > 2 else None
            if cid == context_id and state == "1" and ip != "0.0.0.0":
                print(f"PDP context {BOLD}{GREEN}{context_id}{RESETA}{RESET} already active with IP: {BOLD}{GREEN}{ip}{RESETA}{RESET}")
                return None
    # Not active → try activating
    print(f"{YELLOW}PDP context {context_id} inactive, activating...{RESET}")
    MAX_RETRIES = 3
    RETRY_DELAY = 20  # seconds
    for attempt in range(1, MAX_RETRIES + 1):
        print(f"Attempt {attempt} to activate PDP context {context_id}...")
        send_and_wait(f'AT+CNACT={context_id},1', ser)
        resp = send_and_wait('AT+CNACT?', ser)
        for line in resp:
            if line.startswith("+CNACT:"):
                parts = line.split(":")[1].split(",")
                cid = parts[0].strip()
                state = parts[1].strip()
                ip = parts[2].strip().strip('"') if len(parts) > 2 else None
                if cid == context_id and state == "1" and ip != "0.0.0.0":
                    print(f"PDP context {BOLD}{GREEN}{context_id}{RESETA}{RESET} activated successfully with IP: {BOLD}{GREEN}{ip}{RESETA}{RESET}")
                    return ip
        print(f"{YELLOW}Activation attempt {attempt} failed, retrying in {RETRY_DELAY}s...{RESET}")
        time.sleep(RETRY_DELAY)
    print(f"{RED}Failed to activate PDP context {context_id} after {MAX_RETRIES} attempts.{RESET}")
    return None

# ---------------------------
# Main initialization function
# Perform full modem initialization workflow.
# ---------------------------
def initialize_modem():
    print(f"\n{CYAN}--------------------- Modem Initialization ----------------------{RESET}")
    with serial.Serial(AT_PORT, BAUDRATE, timeout=SERIAL_TIMEOUT) as ser:
        if not check_functionality(ser):
            return None
        if not check_sim_status(ser):
            return None
        if not check_signal(ser):
            return None
        if not check_network_attachment(ser):
            return None
        # print_supported_network_modes(ser)
        # print_supported_nb_iot_cat_m_modes(ser)
        if not configure_network_modes(ser):
            return None
        check_operator(ser)
        context_id = check_apn(ser)
        activate_pdp_context(ser, context_id)
        print("\nModem check and 1NCE preparation completed!")
        print(f"{CYAN}-----------------------------------------------------------------{RESET}")
        return context_id

# ---------------------------
# Main execution
# ---------------------------
if __name__ == "__main__":
    if (modem_handshake()):
        initialize_modem()
    else:
        pass

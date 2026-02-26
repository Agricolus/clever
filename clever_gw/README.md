# Clever NB-IoT Gateway

This repository contains the full software and documentation required to operate and test the **SIM7070G NB-IoT modem** on a Raspberry Pi 4.

It includes:
- Python modules for powering, initializing, and testing the modem (PING + TCP + HTTP/HTTPS)
- SSL certificate uploader
- Logging utilities
- Complete documentation (.adoc + .pdf)
- A Makefile to simplify usage

## Repository Structure

- clever_gw/
  - doc/
    - clever_nbiot_gateway.adoc
    - clever_nbiot_gateway.pdf
    - images/
    - references/
  - Makefile
  - modem_startup/
    - agricolus.cer
    - httpbin.cer
    - http_test.py
    - modem_initializer.py
    - modem_logger.py
    - modem_power.py
    - modem_workflow.py
    - ping_test.py
    - tcp_test.py
    - upload_ssl.py



## Documentation

Full hardware + software documentation is provided in:


doc/clever_nbiot_gateway.pdf


To generate the PDF from the AsciiDoc source:

`make pdf`

This will create or update the PDF document.

> **Important:** If you are working with the hardware, you **must read this PDF**. It explains power sequencing, USB enumeration, GPIO behavior, and modem initialization flow.

The .adoc source is also included in the repository.

## Requirements

**For Documentation Generation:**


`sudo apt update`


`sudo apt install asciidoctor asciidoctor-pdf`

**For Running the Modem Code:**
- Raspberry Pi OS
- Python 3
- RPi.GPIO (usually preinstalled)

If needed:


`sudo apt install python3-rpi.gpio`

## Running the Software

All commands are executed from the root folder:


`cd clever_gw`

See all available Make targets:


`make help`

## Full Modem Workflow

The complete workflow (power toggle → initialization → TCP test → HTTP/HTTPS test) can be run with:


`make workflow`

## Individual Components

Run the following commands from the root folder:

    make power     # Toggle modem power via GPIO4 -> PWRKEY
    make init      # Perform handshake + initialization
    make ping      # PING test
    make tcp       # TCP connection test
    make http      # HTTP/HTTPS GET/POST tests

> You do **not** need to enter the `modem_startup/` directory manually.

## SSL Certificate Uploading

The script modem_startup/upload_ssl.py is **not meant to be run standalone**. It serves as a helper module and is used automatically by other scripts when necessary (e.g., during HTTPS tests).

## Important Notes

After each Raspberry Pi reboot, GPIO4 starts floating. This may randomly turn the modem on or off.

> **Note:** You only need to run the following command manually if you want to skip running the full workflow, which already handles power toggling automatically:


`make power`


## Logging


Log files are generated automatically via modem_logger.py.

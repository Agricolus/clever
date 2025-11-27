PYTHON = python3

MODEM_SCRIPTS_DIR = modem_startup

workflow:
	$(PYTHON) $(MODEM_SCRIPTS_DIR)/modem_workflow.py

power:
	$(PYTHON) $(MODEM_SCRIPTS_DIR)/modem_power.py

init:
	$(PYTHON) $(MODEM_SCRIPTS_DIR)/modem_initializer.py

http:
	$(PYTHON) $(MODEM_SCRIPTS_DIR)/http_test.py

tcp:
	$(PYTHON) $(MODEM_SCRIPTS_DIR)/tcp_test.py

pdf:
	asciidoctor-pdf doc/clever_nbiot_gateway.adoc -o doc/clever_nbiot_gateway.pdf

clear:
	rm $(MODEM_SCRIPTS_DIR)/modem_log.log \
		rm -rf $(MODEM_SCRIPTS_DIR)/__pycache__

# ===== Colors =====
CYAN := \033[1;36m
GREEN := \033[1;32m
YELLOW := \033[1;33m
RESET := \033[0m

help:
	@echo ""
	@echo "$(CYAN)Available targets:$(RESET)"
	@echo "  $(GREEN)make workflow$(RESET)       - Run full modem workflow"
	@echo "  $(GREEN)make power$(RESET)          - Toggle modem power"
	@echo "  $(GREEN)make init$(RESET)           - Initialize modem"
	@echo "  $(GREEN)make tcp$(RESET)            - Run TCP test"
	@echo "  $(GREEN)make http$(RESET)           - Run HTTP test"
	@echo "  $(GREEN)make pdf$(RESET)            - Generate PDF from AsciiDoc"
	@echo "  $(GREEN)make clear$(RESET)          - Clear the directory"
	@echo ""

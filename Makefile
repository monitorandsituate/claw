.PHONY: run telegram setup check doctor

run:
	bash scripts/run_assistant.sh

telegram:
	bash scripts/run_telegram.sh

setup:
	bash scripts/setup.sh

check:
	@if command -v python >/dev/null 2>&1; then \
		python -m compileall src; \
	else \
		python3 -m compileall src; \
	fi

doctor:
	bash scripts/doctor.sh

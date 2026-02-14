.PHONY: run check doctor

run:
	bash scripts/run_assistant.sh

check:
	@if command -v python >/dev/null 2>&1; then \
		python -m compileall src; \
	else \
		python3 -m compileall src; \
	fi

doctor:
	bash scripts/doctor.sh

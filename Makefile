.PHONY: run check

run:
	bash scripts/run_assistant.sh

check:
	python -m compileall src

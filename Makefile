.PHONY: run check doctor

run:
	bash scripts/run_assistant.sh

check:
	python -m compileall src

doctor:
	bash scripts/doctor.sh

.PHONY: setup lint validate opa-test roadmap
setup:
	python3 -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -r requirements.txt
lint:
	. .venv/bin/activate && yamllint configs
validate:
	. .venv/bin/activate && python scripts/validate_configs.py
opa-test:
	opa test platform/gatekeeper/policies -v
roadmap:
	. .venv/bin/activate && python scripts/render_roadmap.py

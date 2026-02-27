.PHONY: install lint test audit demo clean

install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

lint:
	pylint src/

test:
	python -m pytest tests/ -v

audit:
	pip-audit

demo:
	python main.py demo

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache

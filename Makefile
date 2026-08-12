.PHONY: install run debug lint clean lint-strict

install:
	pip install mypy flake8

run:
	python main.py

debug:
	python -m pdb main.py

lint:
	python -m flake8 .
	python -m mypy --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs .

clean:
	rm -rf models/__pycache__ models/.mypy_cache
	rm -rf parsing/__pycache__ parsing/.mypy_cache
	rm -rf ./__pycache__ ./.mypy_cache

lint-strict:
	python -m flake8 .
	python -m mypy --strict .

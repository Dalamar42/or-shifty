VERSION?=$$(git rev-parse --abbrev-ref HEAD)

.PHONY: help
help:           ## Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

.PHONY: freeze
freeze:         ## Freeze python requirements
	poetry update --lock

.PHONY: install
install:        ## Install python requirments
	poetry install

.PHONY: format
format:
	isort **/*.py
	black shifty
	black tests
	flake8 shifty
	flake8 tests

.PHONY: test
test:
	pytest -vv tests

.PHONY: build
build:
	poetry build
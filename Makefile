VERSION?=$$(git rev-parse --abbrev-ref HEAD)

.PHONY: help
help:           ## Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

.PHONY: freeze
freeze:         ## Freeze python requirements
	poetry update --lock

.PHONY: install
install:        ## Install python requirements
	poetry install

.PHONY: format
format:         ## Run linter and formatter
	isort **/*.py
	black shifty
	black tests
	flake8 shifty
	flake8 tests

.PHONY: test
test:           ## Run tests
	pytest -vv tests

.PHONY: build
build:          ## Build project
	poetry build
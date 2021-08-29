SHELL := /bin/bash
.POSIX:

help: ## Show this help
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

get-pip: ## Install pip in a Python environment with Python's 'ensurepip' module
	python -m ensurepip --upgrade
	python -m pip install --upgrade pip

get-pipenv: ## Pipenv is a dependency manager for Python projects
	pip install --user pipenv
	pip install --user --upgrade pipenv

install: get-pipenv ## Install or update dependencies
	pipenv install

pipshell: ## Enter the virtual environment
	pipenv shell

fetch: ## Fetch fresh data using your environment variables (set $REPO and $MONTHS, and $TOKEN for a private repo)
	@test -n "$(REPO)" || (echo "Repository name not set"; exit 1)
	@test -n "$(MONTHS)" || (echo "Number of months is not set"; exit 1)
	@pipenv run python fetch.py $(REPO) $(MONTHS) --token=$(TOKEN)

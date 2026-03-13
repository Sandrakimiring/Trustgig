.PHONY: clean data lint requirements sync_data_down sync_data_up

#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PROJECT_NAME = trustgig
PYTHON_INTERPRETER = python

#################################################################################
# COMMANDS                                                                      #
#################################################################################

## Install Python dependencies
requirements:
	$(PYTHON_INTERPRETER) -m pip install -U pip setuptools wheel
	$(PYTHON_INTERPRETER) -m pip install -r requirements.txt

## Make dataset
data: requirements
	$(PYTHON_INTERPRETER) -m trustgig.dataset

## Train model
train: data
	$(PYTHON_INTERPRETER) -m trustgig.modeling.train

## Predict with trained model
predict:
	$(PYTHON_INTERPRETER) -m trustgig.modeling.predict

## Delete all compiled Python files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

## Lint using flake8 and black (use `make lint` to check, `make format` to fix)
lint:
	flake8 trustgig
	black --check --config pyproject.toml trustgig

## Format source code with black
format:
	black --config pyproject.toml trustgig

## Set up Python interpreter environment
create_environment:
	$(PYTHON_INTERPRETER) -m venv .venv
	@echo ">>> New virtualenv created. Activate with: .venv\\Scripts\\activate (Windows)"

#################################################################################
# PROJECT RULES                                                                 #
#################################################################################


#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

# Inspired by <http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html>
# sed script explained:
# /^##/:
# 	* save line in hold space
# 	* move to next line
# 	* check if it's an assignment or rule
# 	* if so, append hold space (with ##) to line and print
help:
	@echo "$$(tput bold)Available rules:$$(tput sgr0)"
	@sed -n -e "/^## / { \
		h; \
		s/.*//; \
		:doc" \
		-e "H; \
		n; \
		s/^## //; \
		t doc" \
		-e "s/:.*//; \
		G; \
		s/\\n## /---/; \
		s/\\n/ /g; \
		p; \
	}" ${MAKEFILE_LIST} \
	| LC_ALL='C' sort --ignore-case \
	| awk -F '---' \
		-v ncol=$$(tput cols) \
		-v indent=19 \
		-v color=$$(tput setaf 6) \
		-v reset=$$(tput sgr0) \
	'{ \
		printf "%s%*s%s ", color, -indent, $$1, reset; \
		n = split($$2, words, " "); \
		line_length = ncol - indent; \
		for (i = 1; i <= n; i++) { \
			line_length -= length(words[i]) + 1; \
			if (line_length <= 0) { \
				line_length = ncol - indent - length(words[i]) - 1; \
				printf "\n%*s ", -indent, " "; \
			} \
			printf "%s ", words[i]; \
		} \
		printf "\n"; \
	}'

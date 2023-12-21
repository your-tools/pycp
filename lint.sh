#!/bin/bash
set -e
set -x
poetry run black --check .
poetry run isort --check .
poetry run flake8 .
poetry run mypy

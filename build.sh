#!/usr/bin/env bash
# exit on error
set -o errexit
poetry run pip install --upgrade pip
poetry install

python manage.py migrate

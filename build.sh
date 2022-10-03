#!/usr/bin/env bash
# exit on error
set -o errexit
poetry run pip install --upgrade pip
poetry run pip install --upgrade setuptools
poetry install

python manage.py collectstatic --no-input
python manage.py migrate

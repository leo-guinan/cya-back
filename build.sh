#!/usr/bin/env bash
# exit on error
set -o errexit

poetry run pip install --upgrade pip
poetry run pip install --force-reinstall -U setuptools
poetry add pysqlite3-binary
poetry install

poetry run pip install --upgrade pip
poetry run pip install --force-reinstall -U setuptools

python manage.py collectstatic --no-input
python manage.py migrate

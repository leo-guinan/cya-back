#!/usr/bin/env bash
# exit on error
set -o errexit
poetry run pip install --upgrade pip
poetry run pip install --force-reinstall -U setuptools
poetry install

poetry run pip install --upgrade pip
poetry run pip install --force-reinstall -U setuptools

python manage.py collectstatic --no-input
python manage.py migrate

python -m nltk.downloader -d /var/nltk all
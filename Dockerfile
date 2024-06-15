# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /usr/src/app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc python3-dev libsqlite3-mod-spatialite wkhtmltopdf \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade SQLite3 to the latest version
# Note: You may need to find the appropriate way to upgrade SQLite3 for your base image
RUN apt-get update \
    && apt-get install -y sqlite3 \
    && sqlite3 --version

# Install Poetry
RUN pip install poetry

# Copy the Poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Install project dependencies via Poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy the Django project files to the container
COPY . .

# The command to run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
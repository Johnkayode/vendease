#!/bin/bash
# Wait for Postgres to be ready
python manage.py migrate --no-input

gunicorn --workers=4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 api.asgi:application --log-level debug
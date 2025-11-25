#!/bin/bash

set -e
# для Docker

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Starting Gunicorn..."
exec "$@"
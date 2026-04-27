#!/bin/sh

uv run python manage.py collectstatic --noinput
uv run python manage.py migrate

exec "$@"
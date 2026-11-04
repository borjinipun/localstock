#!/bin/sh
set -e

case "$1" in
  api)
    python manage.py migrate --noinput
    if [ "$SEED_DEMO" = "1" ]; then
      python manage.py seed_demo || echo "seed_demo failed (non-fatal)"
    fi
    if [ "$DJANGO_SUPERUSER" = "1" ]; then
      DJANGO_SUPERUSER_PASSWORD=admin python manage.py createsuperuser --noinput \
        --username admin --email admin@localstock.test || true
    fi
    exec python manage.py runserver 0.0.0.0:8000
    ;;
  test)
    python -m pytest "$@"
    ;;
  shell)
    exec python manage.py shell
    ;;
  *)
    exec "$@"
    ;;
esac

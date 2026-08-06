#!/bin/sh
set -e

if [ -n "$POSTGRES_DB" ]; then
    python - <<'PY'
import os
import time

import psycopg

host = os.environ.get("POSTGRES_HOST", "db")
port = os.environ.get("POSTGRES_PORT", "5432")
dbname = os.environ["POSTGRES_DB"]
user = os.environ["POSTGRES_USER"]
password = os.environ["POSTGRES_PASSWORD"]

for attempt in range(60):
    try:
        with psycopg.connect(host=host, port=port, dbname=dbname, user=user, password=password):
            break
    except psycopg.OperationalError:
        if attempt == 59:
            raise
        time.sleep(1)
PY
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"

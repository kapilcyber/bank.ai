#!/bin/sh
set -e
# Ensure uploads volume is writable by appuser (when mounted over /app/uploads)
chown -R appuser:appuser /app/uploads 2>/dev/null || true
# If a command was passed (e.g. celery), run it as appuser; otherwise run gunicorn
if [ $# -gt 0 ]; then
  exec gosu appuser "$@"
else
  exec gosu appuser gunicorn src.main:app -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --timeout 120
fi

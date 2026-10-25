#!/bin/sh
set -e

PORT="${PORT:-10000}"
sed "s/__PORT__/${PORT}/g" /etc/nginx/nginx.public.conf.template > /etc/nginx/conf.d/default.conf

python -m uvicorn app.main:app --app-dir /app/backend --host 127.0.0.1 --port 8001 &
exec nginx -g 'daemon off;'

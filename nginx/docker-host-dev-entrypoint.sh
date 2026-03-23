#!/bin/sh
set -e
FRONTEND_UPSTREAM="${FRONTEND_UPSTREAM:-host.docker.internal:3005}"
BACKEND_UPSTREAM="${BACKEND_UPSTREAM:-host.docker.internal:8000}"

sed -e "s|__FRONTEND_UPSTREAM__|${FRONTEND_UPSTREAM}|g" \
    -e "s|__BACKEND_UPSTREAM__|${BACKEND_UPSTREAM}|g" \
    /templates/nginx.host-dev.template > /etc/nginx/nginx.conf

exec nginx -g 'daemon off;'

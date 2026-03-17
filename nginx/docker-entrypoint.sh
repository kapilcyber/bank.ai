#!/bin/sh
set -e
# Create self-signed cert for HTTPS if not present (dev). In production, mount real certs in /etc/nginx/ssl/.
if [ ! -f /etc/nginx/ssl/cert.pem ]; then
  mkdir -p /etc/nginx/ssl
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/key.pem -out /etc/nginx/ssl/cert.pem \
    -subj "/CN=localhost"
fi
exec nginx -g "daemon off;"

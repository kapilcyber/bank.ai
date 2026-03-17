# Extend nginx:alpine so the custom entrypoint can generate self-signed certs
FROM nginx:alpine
RUN apk add --no-cache openssl
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

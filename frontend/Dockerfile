# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source and set build-time API URL (same-origin when behind nginx)
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL

COPY . .

RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Main config: pid and temp paths under /tmp so non-root nginx can write
COPY nginx-main.conf /etc/nginx/nginx.conf
# Server block for SPA (try_files fallback)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Run as non-root (nginx:alpine creates nginx user)
USER nginx

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

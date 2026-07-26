# Stage 1: Build React App
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html

# Custom Nginx config to listen on port 5173 and proxy backend endpoints (with SSE support)
RUN echo 'server { \
    listen 5173; \
    client_max_body_size 100M; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
    location /api { \
        proxy_pass http://backend:8000; \
        proxy_http_version 1.1; \
        proxy_set_header Upgrade $http_upgrade; \
        proxy_set_header Connection "upgrade"; \
        proxy_set_header Host $host; \
        proxy_cache_bypass $http_upgrade; \
        proxy_buffering off; \
        proxy_read_timeout 24h; \
        chunked_transfer_encoding on; \
    } \
    location /token { \
        proxy_pass http://backend:8000; \
        proxy_http_version 1.1; \
        proxy_set_header Host $host; \
    } \
    location /health { \
        proxy_pass http://backend:8000; \
        proxy_http_version 1.1; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 5173
CMD ["nginx", "-g", "daemon off;"]

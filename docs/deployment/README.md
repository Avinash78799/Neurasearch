# Deployment Guide

NeuraSearch is packaged for deployment using Docker and Docker Compose.

---

## 1. Production Docker Compose

Run the entire platform in production mode:
```bash
docker-compose up -d --build
```
This builds:
- **`backend`**: FastAPI exposed on `http://localhost:8000`.
- **`frontend`**: Nginx web server exposed on `http://localhost:5173`.
- **`ollama`**: Embedded Ollama API exposed on `http://localhost:11434`.

---

## 2. Nginx Reverse Proxy Config

When deploying to a public server (VPS/Cloud VM), route incoming traffic (ports 80/443) using Nginx:

```nginx
server {
    listen 80;
    server_name neurasearch.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name neurasearch.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/neurasearch.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/neurasearch.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```
Ensure ports are opened and firewalls permit `80`, `443`, and `11434`.

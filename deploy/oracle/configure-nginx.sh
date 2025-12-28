#!/bin/bash
# Oracle Cloud Always Free - Nginx Configuration Script
# Run after deploy-app.sh
# Usage: bash configure-nginx.sh [domain]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

DOMAIN="${1:-_}"
APP_DIR="/opt/bridge-bidding-app"

log_info "Configuring Nginx for Bridge Bidding App"

# Remove default configs
sudo rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
sudo rm -f /etc/nginx/conf.d/default.conf 2>/dev/null || true

# Create Nginx configuration
log_info "Creating Nginx configuration..."
sudo tee /etc/nginx/conf.d/bridge-bidding.conf << EOF
# Bridge Bidding App - Nginx Configuration

# Upstream for backend
upstream bridge_backend {
    server 127.0.0.1:5001;
    keepalive 32;
}

server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript application/xml+rss application/atom+xml image/svg+xml;

    # Frontend (React static files)
    location / {
        root $APP_DIR/frontend/build;
        try_files \$uri \$uri/ /index.html;

        # Cache static assets aggressively
        location ~* \.(?:css|js|woff2?|ttf|eot|svg|png|jpg|jpeg|gif|ico|webp)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            access_log off;
        }

        # Don't cache HTML
        location ~* \.html$ {
            expires -1;
            add_header Cache-Control "no-store, no-cache, must-revalidate";
        }
    }

    # API proxy
    location /api/ {
        proxy_pass http://bridge_backend;
        proxy_http_version 1.1;

        # Headers
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # WebSocket support (if needed)
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts (for DDS solver)
        proxy_connect_timeout 60s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;

        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;

        # Keep-alive
        proxy_set_header Connection "";
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "OK";
        add_header Content-Type text/plain;
    }

    # Block common attack vectors
    location ~ /\. {
        deny all;
    }

    location ~ ^/(wp-admin|wp-login|xmlrpc|phpmyadmin) {
        deny all;
    }
}
EOF

# Test Nginx configuration
log_info "Testing Nginx configuration..."
sudo nginx -t

if [ $? -ne 0 ]; then
    log_error "Nginx configuration test failed"
    exit 1
fi

# Enable and restart Nginx
sudo systemctl enable nginx
sudo systemctl restart nginx

# Check status
if sudo systemctl is-active --quiet nginx; then
    log_info "Nginx started successfully"
else
    log_error "Nginx failed to start"
    sudo journalctl -u nginx --no-pager -n 20
    exit 1
fi

# Get public IP
PUBLIC_IP=$(curl -s http://169.254.169.254/opc/v1/instance/metadata/publicIp 2>/dev/null || curl -s ifconfig.me)

log_info "=============================================="
log_info "Nginx configuration complete!"
log_info ""
log_info "Your app is now available at:"
log_info "  http://$PUBLIC_IP"
if [ "$DOMAIN" != "_" ]; then
    log_info "  http://$DOMAIN"
fi
log_info ""
log_info "Test the API:"
log_info "  curl http://$PUBLIC_IP/api/scenarios"
log_info ""
log_info "For HTTPS, either:"
log_info "  1. Use Cloudflare (recommended, free SSL)"
log_info "  2. Run: bash setup-ssl.sh $DOMAIN"

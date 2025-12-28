#!/bin/bash
# Oracle Cloud Always Free - SSL Setup with Let's Encrypt
# Run after configure-nginx.sh
# Usage: bash setup-ssl.sh <domain> [email]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check arguments
if [ -z "$1" ]; then
    log_error "Usage: bash setup-ssl.sh <domain> [email]"
    log_error "Example: bash setup-ssl.sh bridge.example.com admin@example.com"
    exit 1
fi

DOMAIN="$1"
EMAIL="${2:-admin@$DOMAIN}"

log_info "Setting up SSL for $DOMAIN"

# Detect OS
if [ -f /etc/oracle-release ]; then
    OS="oracle"
else
    OS="ubuntu"
fi

# Install Certbot
log_info "Installing Certbot..."
if [ "$OS" == "oracle" ]; then
    sudo dnf install certbot python3-certbot-nginx -y
else
    sudo apt install certbot python3-certbot-nginx -y
fi

# Verify domain points to this server
log_info "Verifying DNS configuration..."
PUBLIC_IP=$(curl -s http://169.254.169.254/opc/v1/instance/metadata/publicIp 2>/dev/null || curl -s ifconfig.me)
DOMAIN_IP=$(dig +short "$DOMAIN" | head -n1)

if [ "$PUBLIC_IP" != "$DOMAIN_IP" ]; then
    log_warn "DNS mismatch detected!"
    log_warn "Server IP: $PUBLIC_IP"
    log_warn "Domain resolves to: $DOMAIN_IP"
    log_warn ""
    log_warn "Please ensure your domain DNS points to $PUBLIC_IP"
    log_warn "DNS changes can take up to 48 hours to propagate."
    log_warn ""
    read -p "Continue anyway? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        log_info "Aborting SSL setup"
        exit 0
    fi
fi

# Update Nginx config with domain
log_info "Updating Nginx configuration with domain..."
sudo sed -i "s/server_name .*;/server_name $DOMAIN;/" /etc/nginx/conf.d/bridge-bidding.conf
sudo nginx -t && sudo systemctl reload nginx

# Obtain certificate
log_info "Obtaining SSL certificate..."
sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "$EMAIL" --redirect

# Enable auto-renewal
log_info "Enabling automatic certificate renewal..."
sudo systemctl enable certbot-renew.timer 2>/dev/null || true
sudo systemctl start certbot-renew.timer 2>/dev/null || true

# Create renewal hook to reload nginx
sudo tee /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh << 'EOF'
#!/bin/bash
systemctl reload nginx
EOF
sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh

# Test renewal
log_info "Testing certificate renewal..."
sudo certbot renew --dry-run

log_info "=============================================="
log_info "SSL setup complete!"
log_info ""
log_info "Your app is now available at:"
log_info "  https://$DOMAIN"
log_info ""
log_info "Certificate will auto-renew before expiration."
log_info "Certificates are stored in: /etc/letsencrypt/live/$DOMAIN/"

#!/bin/bash
# Oracle Cloud AMD Micro Instance - Lightweight Deployment
# Optimized for 1GB RAM instances
# Usage: bash deploy-micro.sh <server_ip> <ssh_key_path>

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check arguments
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: bash deploy-micro.sh <server_ip> <ssh_key_path>"
    echo "Example: bash deploy-micro.sh 129.146.229.15 ~/.ssh/ssh-key-2025-12-28.key"
    exit 1
fi

SERVER_IP="$1"
SSH_KEY="$2"
SSH_CMD="ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=30"
SCP_CMD="scp -i $SSH_KEY -o StrictHostKeyChecking=no"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

log_info "╔════════════════════════════════════════════════════════╗"
log_info "║  Bridge Bidding App - AMD Micro Deployment             ║"
log_info "║  Optimized for 1GB RAM instances                       ║"
log_info "╚════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Build frontend locally
log_info "[1/6] Building frontend locally..."
cd "$PROJECT_DIR/frontend"

# Set API URL to server IP
echo "REACT_APP_API_URL=http://${SERVER_IP}" > .env.production

# Build
npm install --legacy-peer-deps 2>/dev/null || npm install
npm run build

log_info "Frontend built successfully"

# Step 2: Test SSH connection
log_info "[2/6] Testing SSH connection..."
$SSH_CMD opc@$SERVER_IP "echo 'SSH OK'" || {
    log_error "Cannot connect to server. Check IP and SSH key."
    exit 1
}

# Step 3: Install server dependencies
log_info "[3/6] Installing server dependencies (this takes a few minutes)..."
$SSH_CMD opc@$SERVER_IP "sudo bash -s" << 'REMOTE_SETUP'
set -e

# Detect OS
if [ -f /etc/oracle-release ]; then
    # Oracle Linux 9
    echo "Installing on Oracle Linux..."

    # Install Python 3.11
    sudo dnf install -y python3.11 python3.11-pip python3.11-devel 2>/dev/null || \
    sudo dnf install -y python3 python3-pip python3-devel

    # Install nginx and git
    sudo dnf install -y nginx git

    # Configure firewall
    sudo firewall-cmd --permanent --add-service=http 2>/dev/null || true
    sudo firewall-cmd --permanent --add-service=https 2>/dev/null || true
    sudo firewall-cmd --reload 2>/dev/null || true
else
    # Ubuntu
    echo "Installing on Ubuntu..."
    sudo apt update
    sudo apt install -y python3.11 python3.11-venv python3-pip nginx git
    sudo ufw allow 80/tcp 2>/dev/null || true
    sudo ufw allow 443/tcp 2>/dev/null || true
fi

# Create app directory
sudo mkdir -p /opt/bridge-bidding-app
sudo chown opc:opc /opt/bridge-bidding-app 2>/dev/null || sudo chown ubuntu:ubuntu /opt/bridge-bidding-app

echo "Server dependencies installed"
REMOTE_SETUP

# Step 4: Upload application
log_info "[4/6] Uploading application files..."

# Create tarball of backend
cd "$PROJECT_DIR"
tar -czf /tmp/backend.tar.gz backend/ --exclude='*.pyc' --exclude='__pycache__' --exclude='venv' --exclude='*.db' --exclude='*.json'

# Create tarball of frontend build
tar -czf /tmp/frontend-build.tar.gz -C frontend build/

# Upload
$SCP_CMD /tmp/backend.tar.gz opc@$SERVER_IP:/tmp/
$SCP_CMD /tmp/frontend-build.tar.gz opc@$SERVER_IP:/tmp/

# Extract on server
$SSH_CMD opc@$SERVER_IP << 'EXTRACT'
cd /opt/bridge-bidding-app
rm -rf backend frontend 2>/dev/null || true
tar -xzf /tmp/backend.tar.gz
mkdir -p frontend
tar -xzf /tmp/frontend-build.tar.gz -C frontend/
rm /tmp/backend.tar.gz /tmp/frontend-build.tar.gz
echo "Files extracted"
EXTRACT

log_info "Files uploaded"

# Step 5: Setup Python backend
log_info "[5/6] Setting up Python backend..."
$SSH_CMD opc@$SERVER_IP "bash -s" << 'PYTHON_SETUP'
set -e
cd /opt/bridge-bidding-app/backend

# Find Python
PYTHON=$(which python3.11 2>/dev/null || which python3)
echo "Using Python: $PYTHON"

# Create venv
$PYTHON -m venv venv
source venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install flask flask-cors gunicorn python-dotenv

# Create minimal environment file (SQLite mode)
cat > .env << EOF
FLASK_ENV=production
DEFAULT_AI_DIFFICULTY=advanced
EOF

# Initialize database
python3 -c "from db import init_database; init_database()" 2>/dev/null || echo "DB init skipped"

echo "Python setup complete"
PYTHON_SETUP

# Step 6: Configure and start services
log_info "[6/6] Configuring services..."
$SSH_CMD opc@$SERVER_IP "sudo bash -s" << 'SERVICES'
set -e

APP_DIR="/opt/bridge-bidding-app"
USER=$(ls -ld $APP_DIR | awk '{print $3}')

# Create systemd service for backend
cat > /etc/systemd/system/bridge-backend.service << EOF
[Unit]
Description=Bridge Bidding App Backend
After=network.target

[Service]
User=$USER
WorkingDirectory=$APP_DIR/backend
Environment="PATH=$APP_DIR/backend/venv/bin"
ExecStart=$APP_DIR/backend/venv/bin/gunicorn --bind 127.0.0.1:5001 --workers 1 --timeout 120 server:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Create nginx config
cat > /etc/nginx/conf.d/bridge-bidding.conf << 'NGINX'
server {
    listen 80;
    server_name _;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    location / {
        root /opt/bridge-bidding-app/frontend/build;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 120s;
    }
}
NGINX

# Remove default configs
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
rm -f /etc/nginx/conf.d/default.conf 2>/dev/null || true

# Start services
systemctl daemon-reload
systemctl enable bridge-backend nginx
systemctl restart bridge-backend
systemctl restart nginx

echo "Services configured and started"
SERVICES

# Cleanup local temp files
rm -f /tmp/backend.tar.gz /tmp/frontend-build.tar.gz

# Verify deployment
log_info "Verifying deployment..."
sleep 3

$SSH_CMD opc@$SERVER_IP "curl -s http://localhost/api/scenarios | head -c 100" && {
    echo ""
    echo ""
    log_info "════════════════════════════════════════"
    log_info "  DEPLOYMENT SUCCESSFUL!"
    log_info "════════════════════════════════════════"
    echo ""
    echo "  Your app is live at:"
    echo ""
    echo -e "  ${BLUE}http://${SERVER_IP}${NC}"
    echo ""
} || {
    log_warn "API not responding yet. Check with:"
    echo "  ssh -i $SSH_KEY opc@$SERVER_IP"
    echo "  sudo systemctl status bridge-backend"
    echo "  sudo journalctl -u bridge-backend -n 50"
}

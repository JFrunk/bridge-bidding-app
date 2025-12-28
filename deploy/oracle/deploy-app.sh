#!/bin/bash
# Oracle Cloud Always Free - Application Deployment Script
# Run after setup-database.sh
# Usage: bash deploy-app.sh <github_repo_url> [branch]

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
    log_error "Usage: bash deploy-app.sh <github_repo_url> [branch]"
    log_error "Example: bash deploy-app.sh https://github.com/user/bridge_bidding_app.git main"
    exit 1
fi

REPO_URL="$1"
BRANCH="${2:-main}"
APP_DIR="/opt/bridge-bidding-app"

log_info "Deploying Bridge Bidding App from $REPO_URL ($BRANCH branch)"

# Clone or update repository
cd "$APP_DIR"
if [ -d ".git" ]; then
    log_info "Repository exists, pulling latest changes..."
    git fetch origin
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
else
    log_info "Cloning repository..."
    git clone -b "$BRANCH" "$REPO_URL" .
fi

# Setup Python backend
log_info "Setting up Python backend..."
cd "$APP_DIR/backend"

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
log_info "Installing Python dependencies..."
pip install -r requirements.txt

# Copy environment file if exists at parent level
if [ -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env" "$APP_DIR/backend/.env"
fi

# Initialize database
log_info "Initializing database..."
python3 database/init_all_tables.py

# Test backend
log_info "Testing backend..."
python3 -c "from server import app; print('Backend OK')"

# Build frontend
log_info "Building frontend..."
cd "$APP_DIR/frontend"

# Create production environment file
PUBLIC_IP=$(curl -s http://169.254.169.254/opc/v1/instance/metadata/publicIp 2>/dev/null || echo "localhost")
cat > .env.production << EOF
REACT_APP_API_URL=http://${PUBLIC_IP}
EOF

log_info "Frontend will use API URL: http://${PUBLIC_IP}"

# Install Node dependencies
npm install

# Build for production
npm run build

log_info "Frontend built successfully"

# Create systemd service
log_info "Creating systemd service..."
sudo tee /etc/systemd/system/bridge-backend.service << EOF
[Unit]
Description=Bridge Bidding App Backend
After=network.target postgresql.service

[Service]
User=$USER
Group=$USER
WorkingDirectory=$APP_DIR/backend
Environment="PATH=$APP_DIR/backend/venv/bin"
EnvironmentFile=$APP_DIR/backend/.env
ExecStart=$APP_DIR/backend/venv/bin/gunicorn \
    --bind 127.0.0.1:5001 \
    --workers 2 \
    --timeout 120 \
    --access-logfile /var/log/bridge-backend/access.log \
    --error-logfile /var/log/bridge-backend/error.log \
    server:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Create log directory
sudo mkdir -p /var/log/bridge-backend
sudo chown $USER:$USER /var/log/bridge-backend

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable bridge-backend
sudo systemctl restart bridge-backend

# Wait for service to start
sleep 3

# Check service status
if sudo systemctl is-active --quiet bridge-backend; then
    log_info "Backend service started successfully"
else
    log_error "Backend service failed to start"
    sudo journalctl -u bridge-backend --no-pager -n 20
    exit 1
fi

# Test API
log_info "Testing API..."
curl -s http://127.0.0.1:5001/api/scenarios > /dev/null
if [ $? -eq 0 ]; then
    log_info "API responding correctly"
else
    log_warn "API test failed, but service is running"
fi

log_info "=============================================="
log_info "Application deployment complete!"
log_info ""
log_info "Backend: http://127.0.0.1:5001"
log_info "Frontend build: $APP_DIR/frontend/build"
log_info ""
log_info "Next step: bash configure-nginx.sh [domain]"

#!/bin/bash
# Oracle Cloud Always Free - Complete Deployment Script
# One-command deployment for Bridge Bidding App
#
# Usage: curl -sSL https://raw.githubusercontent.com/JFrunk/bridge-bidding-app/main/deploy/oracle/deploy-all.sh | bash -s <db_password>
# OR:    bash deploy-all.sh <db_password>

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
log_section() { echo -e "\n${BLUE}════════════════════════════════════════${NC}"; echo -e "${BLUE}  $1${NC}"; echo -e "${BLUE}════════════════════════════════════════${NC}\n"; }

# Configuration
REPO_URL="https://github.com/JFrunk/bridge-bidding-app.git"
BRANCH="main"
APP_DIR="/opt/bridge-bidding-app"
DB_USER="bridge_user"
DB_NAME="bridge_bidding"

# Check arguments
if [ -z "$1" ]; then
    log_error "Usage: bash deploy-all.sh <db_password>"
    log_error "Example: bash deploy-all.sh MySecurePass123!"
    exit 1
fi

DB_PASSWORD="$1"

# Detect OS
detect_os() {
    if [ -f /etc/oracle-release ]; then
        OS="oracle"
        PKG_MANAGER="dnf"
        PG_HBA="/var/lib/pgsql/data/pg_hba.conf"
    elif [ -f /etc/lsb-release ]; then
        OS="ubuntu"
        PKG_MANAGER="apt"
        PG_VERSION=$(ls /etc/postgresql/ 2>/dev/null | head -n1 || echo "14")
        PG_HBA="/etc/postgresql/$PG_VERSION/main/pg_hba.conf"
    else
        log_error "Unsupported operating system"
        exit 1
    fi
    log_info "Detected OS: $OS"
}

# ============================================
# PHASE 1: System Setup
# ============================================
setup_system() {
    log_section "Phase 1: System Setup"

    log_info "Updating system packages..."
    if [ "$OS" == "oracle" ]; then
        sudo dnf update -y
    else
        sudo apt update && sudo apt upgrade -y
    fi

    log_info "Installing Python 3.11..."
    if [ "$OS" == "oracle" ]; then
        sudo dnf install python3.11 python3.11-pip python3.11-devel -y
    else
        sudo apt install python3.11 python3.11-venv python3.11-dev -y
    fi

    log_info "Installing Node.js 20..."
    if [ "$OS" == "oracle" ]; then
        curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
        sudo dnf install nodejs -y
    else
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
        sudo apt install nodejs -y
    fi

    log_info "Installing Nginx..."
    if [ "$OS" == "oracle" ]; then
        sudo dnf install nginx -y
    else
        sudo apt install nginx -y
    fi

    log_info "Installing PostgreSQL..."
    if [ "$OS" == "oracle" ]; then
        sudo dnf install postgresql-server postgresql-contrib -y
        sudo postgresql-setup --initdb 2>/dev/null || true
    else
        sudo apt install postgresql postgresql-contrib -y
    fi

    log_info "Installing build tools..."
    if [ "$OS" == "oracle" ]; then
        sudo dnf groupinstall "Development Tools" -y
        sudo dnf install git -y
    else
        sudo apt install build-essential git -y
    fi

    # Start PostgreSQL
    sudo systemctl start postgresql
    sudo systemctl enable postgresql

    # Configure firewall
    log_info "Configuring firewall..."
    if [ "$OS" == "oracle" ]; then
        sudo firewall-cmd --permanent --add-service=http 2>/dev/null || true
        sudo firewall-cmd --permanent --add-service=https 2>/dev/null || true
        sudo firewall-cmd --permanent --add-port=22/tcp 2>/dev/null || true
        sudo firewall-cmd --reload 2>/dev/null || true
    else
        sudo ufw allow 22/tcp 2>/dev/null || true
        sudo ufw allow 80/tcp 2>/dev/null || true
        sudo ufw allow 443/tcp 2>/dev/null || true
        sudo ufw --force enable 2>/dev/null || true
    fi

    log_info "System setup complete!"
}

# ============================================
# PHASE 2: Database Setup
# ============================================
setup_database() {
    log_section "Phase 2: Database Setup"

    log_info "Creating database and user..."
    sudo -u postgres psql << EOF
-- Drop existing if any (clean install)
DROP DATABASE IF EXISTS $DB_NAME;
DROP USER IF EXISTS $DB_USER;

-- Create user and database
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
CREATE DATABASE $DB_NAME OWNER $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;

-- PostgreSQL 15+ schema permissions
\c $DB_NAME
GRANT ALL ON SCHEMA public TO $DB_USER;
EOF

    log_info "Configuring PostgreSQL authentication..."
    sudo cp "$PG_HBA" "$PG_HBA.backup"

    if [ "$OS" == "oracle" ]; then
        sudo sed -i 's/ident/md5/g' "$PG_HBA"
        sudo sed -i 's/peer/md5/g' "$PG_HBA"
    else
        sudo sed -i 's/peer/md5/g' "$PG_HBA"
        sudo sed -i 's/scram-sha-256/md5/g' "$PG_HBA"
    fi

    sudo systemctl restart postgresql

    # Test connection
    log_info "Testing database connection..."
    PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        log_info "Database connection successful!"
    else
        log_error "Database connection failed!"
        exit 1
    fi
}

# ============================================
# PHASE 3: Application Deployment
# ============================================
deploy_application() {
    log_section "Phase 3: Application Deployment"

    # Create app directory
    sudo mkdir -p "$APP_DIR"
    sudo chown $USER:$USER "$APP_DIR"

    # Clone repository
    log_info "Cloning repository..."
    cd "$APP_DIR"
    if [ -d ".git" ]; then
        git fetch origin
        git checkout "$BRANCH"
        git pull origin "$BRANCH"
    else
        git clone -b "$BRANCH" "$REPO_URL" .
    fi

    # Create environment file
    log_info "Creating environment configuration..."
    cat > "$APP_DIR/backend/.env" << EOF
FLASK_ENV=production
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}
DEFAULT_AI_DIFFICULTY=expert
EOF
    chmod 600 "$APP_DIR/backend/.env"

    # Setup Python backend
    log_info "Setting up Python backend..."
    cd "$APP_DIR/backend"
    python3.11 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt

    # Initialize database
    log_info "Initializing database schema..."
    python3 database/init_all_tables.py

    # Get public IP for frontend config
    PUBLIC_IP=$(curl -s http://169.254.169.254/opc/v1/instance/metadata/publicIp 2>/dev/null || curl -s ifconfig.me)

    # Build frontend
    log_info "Building frontend..."
    cd "$APP_DIR/frontend"

    # Create production environment
    cat > .env.production << EOF
REACT_APP_API_URL=http://${PUBLIC_IP}
EOF

    npm install
    npm run build

    log_info "Application deployment complete!"
}

# ============================================
# PHASE 4: Services Configuration
# ============================================
configure_services() {
    log_section "Phase 4: Services Configuration"

    # Create systemd service for backend
    log_info "Creating backend service..."
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

    # Create Nginx configuration
    log_info "Configuring Nginx..."
    sudo rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
    sudo rm -f /etc/nginx/conf.d/default.conf 2>/dev/null || true

    sudo tee /etc/nginx/conf.d/bridge-bidding.conf << EOF
upstream bridge_backend {
    server 127.0.0.1:5001;
    keepalive 32;
}

server {
    listen 80;
    listen [::]:80;
    server_name _;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Gzip
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    # Frontend
    location / {
        root $APP_DIR/frontend/build;
        try_files \$uri \$uri/ /index.html;

        location ~* \\.(?:css|js|woff2?|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # API proxy
    location /api/ {
        proxy_pass http://bridge_backend;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
    }

    # Health check
    location /health {
        return 200 "OK";
        add_header Content-Type text/plain;
    }
}
EOF

    # Test Nginx config
    sudo nginx -t

    # Enable and start services
    log_info "Starting services..."
    sudo systemctl daemon-reload
    sudo systemctl enable bridge-backend nginx
    sudo systemctl restart bridge-backend
    sudo systemctl restart nginx

    # Wait for services to start
    sleep 3
}

# ============================================
# PHASE 5: Post-Deployment Setup
# ============================================
post_deployment() {
    log_section "Phase 5: Post-Deployment Setup"

    # Setup anti-idle cron (prevents Oracle reclamation)
    log_info "Setting up anti-idle cron job..."
    (crontab -l 2>/dev/null | grep -v "api/scenarios"; echo "0 */6 * * * curl -s http://localhost/api/scenarios > /dev/null 2>&1") | crontab -

    # Setup log rotation
    log_info "Configuring log rotation..."
    sudo tee /etc/logrotate.d/bridge-backend << EOF
/var/log/bridge-backend/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 $USER $USER
}
EOF

    # Create backup directory
    mkdir -p "$APP_DIR/backups"

    # Create update script
    cat > "$APP_DIR/update.sh" << 'EOF'
#!/bin/bash
cd /opt/bridge-bidding-app
git pull origin main
cd backend && source venv/bin/activate && pip install -r requirements.txt && python3 database/init_all_tables.py
cd ../frontend && npm install && npm run build
sudo systemctl restart bridge-backend && sudo systemctl reload nginx
echo "Update complete!"
EOF
    chmod +x "$APP_DIR/update.sh"

    log_info "Post-deployment setup complete!"
}

# ============================================
# PHASE 6: Verification
# ============================================
verify_deployment() {
    log_section "Phase 6: Verification"

    PUBLIC_IP=$(curl -s http://169.254.169.254/opc/v1/instance/metadata/publicIp 2>/dev/null || curl -s ifconfig.me)

    echo ""
    log_info "Checking services..."

    # Check PostgreSQL
    if systemctl is-active --quiet postgresql; then
        echo "  ✓ PostgreSQL: Running"
    else
        echo "  ✗ PostgreSQL: Not running"
    fi

    # Check Backend
    if systemctl is-active --quiet bridge-backend; then
        echo "  ✓ Backend: Running"
    else
        echo "  ✗ Backend: Not running"
    fi

    # Check Nginx
    if systemctl is-active --quiet nginx; then
        echo "  ✓ Nginx: Running"
    else
        echo "  ✗ Nginx: Not running"
    fi

    # Check API
    if curl -s http://127.0.0.1:5001/api/scenarios > /dev/null 2>&1; then
        echo "  ✓ API: Responding"
    else
        echo "  ✗ API: Not responding"
    fi

    echo ""
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo -e "${GREEN}  DEPLOYMENT COMPLETE!${NC}"
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo ""
    echo "  Your Bridge Bidding App is now live at:"
    echo ""
    echo -e "  ${BLUE}http://${PUBLIC_IP}${NC}"
    echo ""
    echo "  Useful commands:"
    echo "    View logs:    sudo journalctl -u bridge-backend -f"
    echo "    Update app:   bash $APP_DIR/update.sh"
    echo "    Restart:      sudo systemctl restart bridge-backend"
    echo ""
    echo "  You can now decommission your Render deployment!"
    echo ""
}

# ============================================
# MAIN
# ============================================
main() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Bridge Bidding App - Oracle Cloud Deployment          ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""

    detect_os
    setup_system
    setup_database
    deploy_application
    configure_services
    post_deployment
    verify_deployment
}

main "$@"

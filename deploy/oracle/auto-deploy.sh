#!/bin/bash
# Oracle Cloud - Automated Deployment Webhook Handler
# Listens for GitHub webhooks and auto-deploys on push to main
#
# Setup:
#   1. Run: bash auto-deploy.sh install
#   2. Add webhook in GitHub repo settings:
#      - URL: http://<YOUR_SERVER_IP>:9000/webhook
#      - Content type: application/json
#      - Secret: (set WEBHOOK_SECRET env var)
#      - Events: Just the push event
#
# Usage:
#   bash auto-deploy.sh install    # Install webhook listener service
#   bash auto-deploy.sh uninstall  # Remove service
#   bash auto-deploy.sh status     # Check service status
#   bash auto-deploy.sh logs       # View deployment logs

set -e

APP_DIR="/opt/bridge-bidding-app"
WEBHOOK_PORT=9000
LOG_FILE="/var/log/bridge-autodeploy.log"
WEBHOOK_SECRET="${WEBHOOK_SECRET:-}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Deploy function - called when webhook received
do_deploy() {
    echo "$(date): Starting deployment..." >> "$LOG_FILE"

    cd "$APP_DIR"

    # Pull latest code
    git fetch origin main
    git reset --hard origin/main

    # Update backend
    cd backend
    source venv/bin/activate
    pip install -r requirements.txt -q

    # Rebuild frontend
    cd ../frontend
    npm install --legacy-peer-deps 2>/dev/null || npm install
    npm run build

    # Restart backend
    sudo systemctl restart bridge-backend

    echo "$(date): Deployment complete!" >> "$LOG_FILE"
}

# Simple webhook listener using Python
create_webhook_listener() {
    cat > "$APP_DIR/webhook_listener.py" << 'PYTHON'
#!/usr/bin/env python3
"""Simple GitHub webhook listener for auto-deployment"""
import os
import hmac
import hashlib
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', '').encode()
DEPLOY_SCRIPT = '/opt/bridge-bidding-app/deploy/oracle/auto-deploy.sh'
LOG_FILE = '/var/log/bridge-autodeploy.log'

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != '/webhook':
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get('Content-Length', 0))
        payload = self.rfile.read(content_length)

        # Verify signature if secret is set
        if WEBHOOK_SECRET:
            signature = self.headers.get('X-Hub-Signature-256', '')
            expected = 'sha256=' + hmac.new(WEBHOOK_SECRET, payload, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected):
                self.send_response(401)
                self.end_headers()
                self.wfile.write(b'Invalid signature')
                return

        # Parse payload
        try:
            data = json.loads(payload)
        except:
            self.send_response(400)
            self.end_headers()
            return

        # Check if push to main branch
        ref = data.get('ref', '')
        if ref == 'refs/heads/main':
            with open(LOG_FILE, 'a') as f:
                f.write(f"Webhook received: push to main\n")

            # Trigger deployment in background
            subprocess.Popen(['bash', DEPLOY_SCRIPT, 'deploy'])

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Deployment triggered')
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(f'Ignored: {ref}'.encode())

    def log_message(self, format, *args):
        with open(LOG_FILE, 'a') as f:
            f.write(f"{self.address_string()} - {format % args}\n")

if __name__ == '__main__':
    port = int(os.environ.get('WEBHOOK_PORT', 9000))
    server = HTTPServer(('0.0.0.0', port), WebhookHandler)
    print(f'Webhook listener started on port {port}')
    server.serve_forever()
PYTHON
    chmod +x "$APP_DIR/webhook_listener.py"
}

# Install systemd service
install_service() {
    log_info "Installing auto-deploy webhook service..."

    # Create webhook listener script
    create_webhook_listener

    # Create systemd service
    sudo tee /etc/systemd/system/bridge-autodeploy.service > /dev/null << EOF
[Unit]
Description=Bridge App Auto-Deploy Webhook Listener
After=network.target

[Service]
Type=simple
User=opc
Environment="WEBHOOK_SECRET=${WEBHOOK_SECRET}"
Environment="WEBHOOK_PORT=${WEBHOOK_PORT}"
ExecStart=/usr/bin/python3 ${APP_DIR}/webhook_listener.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    # Open firewall port
    sudo firewall-cmd --permanent --add-port=${WEBHOOK_PORT}/tcp 2>/dev/null || true
    sudo firewall-cmd --reload 2>/dev/null || true

    # Enable and start service
    sudo systemctl daemon-reload
    sudo systemctl enable bridge-autodeploy
    sudo systemctl start bridge-autodeploy

    log_info "Auto-deploy service installed!"
    echo ""
    echo "Next steps:"
    echo "1. Add webhook in GitHub repo settings:"
    echo "   - URL: http://<YOUR_SERVER_IP>:${WEBHOOK_PORT}/webhook"
    echo "   - Content type: application/json"
    echo "   - Secret: (optional, set WEBHOOK_SECRET env var)"
    echo "   - Events: Just the push event"
    echo ""
    echo "2. Push to main branch to trigger auto-deployment"
}

uninstall_service() {
    log_info "Removing auto-deploy service..."
    sudo systemctl stop bridge-autodeploy 2>/dev/null || true
    sudo systemctl disable bridge-autodeploy 2>/dev/null || true
    sudo rm -f /etc/systemd/system/bridge-autodeploy.service
    sudo systemctl daemon-reload
    log_info "Service removed"
}

show_status() {
    echo "Auto-Deploy Service Status:"
    sudo systemctl status bridge-autodeploy --no-pager || true
}

show_logs() {
    echo "Recent deployment logs:"
    tail -50 "$LOG_FILE" 2>/dev/null || echo "No logs yet"
}

# Main
case "${1:-}" in
    install)
        install_service
        ;;
    uninstall)
        uninstall_service
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    deploy)
        do_deploy
        ;;
    *)
        echo "Oracle Cloud Auto-Deploy for Bridge Bidding App"
        echo ""
        echo "Usage: bash auto-deploy.sh [command]"
        echo ""
        echo "Commands:"
        echo "  install    Install webhook listener service"
        echo "  uninstall  Remove service"
        echo "  status     Check service status"
        echo "  logs       View deployment logs"
        echo ""
        echo "Environment variables:"
        echo "  WEBHOOK_SECRET  GitHub webhook secret (optional)"
        echo "  WEBHOOK_PORT    Port to listen on (default: 9000)"
        ;;
esac

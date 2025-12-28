#!/bin/bash
# Oracle Cloud Always Free - Maintenance & Update Script
# Usage: bash maintenance.sh [update|backup|status|logs|restart]

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
log_section() { echo -e "\n${BLUE}=== $1 ===${NC}"; }

APP_DIR="/opt/bridge-bidding-app"
BACKUP_DIR="$APP_DIR/backups"

# Show status of all services
show_status() {
    log_section "Service Status"

    echo "PostgreSQL:"
    systemctl is-active postgresql && echo "  Status: Running" || echo "  Status: Stopped"

    echo ""
    echo "Backend (Gunicorn):"
    systemctl is-active bridge-backend && echo "  Status: Running" || echo "  Status: Stopped"

    echo ""
    echo "Nginx:"
    systemctl is-active nginx && echo "  Status: Running" || echo "  Status: Stopped"

    log_section "API Health"
    if curl -s http://127.0.0.1:5001/api/scenarios > /dev/null 2>&1; then
        echo "API: Healthy"
    else
        echo "API: Not responding"
    fi

    log_section "Disk Usage"
    df -h / | tail -1

    log_section "Memory Usage"
    free -h | head -2

    log_section "Recent Errors (last 10)"
    sudo journalctl -u bridge-backend --no-pager -p err -n 10 2>/dev/null || echo "No recent errors"
}

# View logs
show_logs() {
    log_section "Recent Backend Logs"
    sudo journalctl -u bridge-backend --no-pager -n 50
}

# Backup database
backup_database() {
    log_section "Creating Database Backup"
    mkdir -p "$BACKUP_DIR"

    DATE=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/db_backup_$DATE.sql"

    # Get database URL from env file
    source "$APP_DIR/backend/.env"

    # Parse DATABASE_URL
    DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
    DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')

    log_info "Backing up database to $BACKUP_FILE..."
    PGPASSWORD=$(echo $DATABASE_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p') \
        pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE"

    # Compress backup
    gzip "$BACKUP_FILE"
    log_info "Backup created: ${BACKUP_FILE}.gz"

    # Clean old backups (keep last 7 days)
    find "$BACKUP_DIR" -name "*.gz" -mtime +7 -delete
    log_info "Old backups cleaned"

    log_section "Available Backups"
    ls -lh "$BACKUP_DIR"/*.gz 2>/dev/null || echo "No backups found"
}

# Update application
update_app() {
    log_section "Updating Application"

    # Backup first
    backup_database

    cd "$APP_DIR"

    # Pull latest code
    log_info "Pulling latest code..."
    git fetch origin
    git pull origin main

    # Update backend
    log_info "Updating backend dependencies..."
    cd backend
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt

    # Run migrations
    log_info "Running database migrations..."
    python3 database/init_all_tables.py

    # Update frontend
    log_info "Rebuilding frontend..."
    cd ../frontend
    npm install
    npm run build

    # Restart services
    log_info "Restarting services..."
    sudo systemctl restart bridge-backend
    sudo systemctl reload nginx

    # Wait and verify
    sleep 3
    if curl -s http://127.0.0.1:5001/api/scenarios > /dev/null 2>&1; then
        log_info "Update complete! API is healthy."
    else
        log_error "API not responding after update!"
        log_info "Check logs: bash maintenance.sh logs"
    fi
}

# Restart services
restart_services() {
    log_section "Restarting Services"

    log_info "Restarting PostgreSQL..."
    sudo systemctl restart postgresql

    log_info "Restarting backend..."
    sudo systemctl restart bridge-backend

    log_info "Reloading Nginx..."
    sudo systemctl reload nginx

    sleep 2
    show_status
}

# Setup anti-idle cron (prevents Oracle reclamation)
setup_anti_idle() {
    log_section "Setting Up Anti-Idle Cron"

    # Check if already configured
    if crontab -l 2>/dev/null | grep -q "api/scenarios"; then
        log_info "Anti-idle cron already configured"
        crontab -l | grep "api/scenarios"
        return
    fi

    # Add cron job
    (crontab -l 2>/dev/null; echo "0 */6 * * * curl -s http://localhost/api/scenarios > /dev/null 2>&1") | crontab -

    log_info "Anti-idle cron job added (runs every 6 hours)"
    log_info "This prevents Oracle from reclaiming your instance as idle"
}

# Setup logrotate
setup_logrotate() {
    log_section "Setting Up Log Rotation"

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

    log_info "Log rotation configured (14 days retention)"
}

# Main menu
main() {
    case "${1:-status}" in
        update)
            update_app
            ;;
        backup)
            backup_database
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        restart)
            restart_services
            ;;
        setup-anti-idle)
            setup_anti_idle
            ;;
        setup-logrotate)
            setup_logrotate
            ;;
        full-setup)
            setup_anti_idle
            setup_logrotate
            ;;
        *)
            echo "Bridge Bidding App - Maintenance Script"
            echo ""
            echo "Usage: bash maintenance.sh [command]"
            echo ""
            echo "Commands:"
            echo "  status          Show status of all services (default)"
            echo "  logs            View recent backend logs"
            echo "  backup          Backup database"
            echo "  update          Pull latest code and redeploy"
            echo "  restart         Restart all services"
            echo "  setup-anti-idle Configure anti-idle cron job"
            echo "  setup-logrotate Configure log rotation"
            echo "  full-setup      Run all setup tasks"
            ;;
    esac
}

main "$@"

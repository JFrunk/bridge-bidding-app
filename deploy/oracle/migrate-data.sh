#!/bin/bash
# Oracle Cloud Always Free - Data Migration from Render
# Run this to migrate your existing data from Render PostgreSQL
# Usage: bash migrate-data.sh <render_database_url>

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
    log_error "Usage: bash migrate-data.sh <render_database_url>"
    log_error ""
    log_error "To get your Render database URL:"
    log_error "1. Go to Render Dashboard → Your PostgreSQL database"
    log_error "2. Click 'Connect' → 'External Connection'"
    log_error "3. Copy the 'External Database URL'"
    log_error ""
    log_error "Example:"
    log_error "  bash migrate-data.sh 'postgres://user:pass@host.render.com:5432/dbname'"
    exit 1
fi

RENDER_DB_URL="$1"
APP_DIR="/opt/bridge-bidding-app"
BACKUP_FILE="/tmp/render_backup_$(date +%Y%m%d_%H%M%S).sql"

log_info "Starting data migration from Render"
log_warn "This will REPLACE all data in the Oracle database!"
echo ""
read -p "Continue? (y/N): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    log_info "Migration cancelled"
    exit 0
fi

# Export from Render
log_info "Exporting data from Render PostgreSQL..."
pg_dump "$RENDER_DB_URL" > "$BACKUP_FILE"

if [ ! -s "$BACKUP_FILE" ]; then
    log_error "Export failed or database is empty"
    exit 1
fi

log_info "Export complete: $(wc -l < "$BACKUP_FILE") lines"

# Load local environment
source "$APP_DIR/backend/.env"

# Parse local DATABASE_URL
LOCAL_DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
LOCAL_DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
LOCAL_DB_PASS=$(echo $DATABASE_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')

# Backup current Oracle data
log_info "Backing up current Oracle database..."
mkdir -p "$APP_DIR/backups"
ORACLE_BACKUP="$APP_DIR/backups/pre_migration_$(date +%Y%m%d_%H%M%S).sql"
PGPASSWORD="$LOCAL_DB_PASS" pg_dump -U "$LOCAL_DB_USER" "$LOCAL_DB_NAME" > "$ORACLE_BACKUP"
log_info "Oracle backup saved: $ORACLE_BACKUP"

# Clear and import
log_info "Importing data to Oracle PostgreSQL..."

# Drop and recreate tables
PGPASSWORD="$LOCAL_DB_PASS" psql -U "$LOCAL_DB_USER" "$LOCAL_DB_NAME" << EOF
-- Drop all tables
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO $LOCAL_DB_USER;
GRANT ALL ON SCHEMA public TO public;
EOF

# Import data
PGPASSWORD="$LOCAL_DB_PASS" psql -U "$LOCAL_DB_USER" "$LOCAL_DB_NAME" < "$BACKUP_FILE"

# Verify import
log_info "Verifying migration..."
TABLES=$(PGPASSWORD="$LOCAL_DB_PASS" psql -U "$LOCAL_DB_USER" "$LOCAL_DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
USERS=$(PGPASSWORD="$LOCAL_DB_PASS" psql -U "$LOCAL_DB_USER" "$LOCAL_DB_NAME" -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "0")

log_info "Tables imported: $TABLES"
log_info "Users imported: $USERS"

# Restart backend
log_info "Restarting backend service..."
sudo systemctl restart bridge-backend

# Clean up
rm -f "$BACKUP_FILE"

log_info "=============================================="
log_info "Data migration complete!"
log_info ""
log_info "Pre-migration backup saved: $ORACLE_BACKUP"
log_info ""
log_info "Please verify your app is working correctly:"
log_info "  1. Test login with existing user"
log_info "  2. Check dashboard shows historical data"
log_info "  3. Verify gameplay works"
log_info ""
log_info "If issues occur, restore with:"
log_info "  PGPASSWORD='$LOCAL_DB_PASS' psql -U $LOCAL_DB_USER $LOCAL_DB_NAME < '$ORACLE_BACKUP'"

#!/bin/bash
# Oracle Cloud Always Free - Database Setup Script
# Run after setup-server.sh
# Usage: bash setup-database.sh <db_password>

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
    log_error "Usage: bash setup-database.sh <db_password>"
    log_error "Example: bash setup-database.sh MySecurePass123!"
    exit 1
fi

DB_PASSWORD="$1"
DB_USER="bridge_user"
DB_NAME="bridge_bidding"

# Detect OS
if [ -f /etc/oracle-release ]; then
    OS="oracle"
    PG_HBA="/var/lib/pgsql/data/pg_hba.conf"
else
    OS="ubuntu"
    # Find PostgreSQL version
    PG_VERSION=$(ls /etc/postgresql/ | head -n1)
    PG_HBA="/etc/postgresql/$PG_VERSION/main/pg_hba.conf"
fi

log_info "Setting up PostgreSQL database..."

# Create database and user
sudo -u postgres psql << EOF
-- Create user
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';

-- Create database
CREATE DATABASE $DB_NAME OWNER $DB_USER;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;

-- Grant schema privileges (PostgreSQL 15+)
\c $DB_NAME
GRANT ALL ON SCHEMA public TO $DB_USER;
EOF

log_info "Database and user created"

# Configure pg_hba.conf for password authentication
log_info "Configuring PostgreSQL authentication..."

# Backup original
sudo cp "$PG_HBA" "$PG_HBA.backup"

# Update authentication method
if [ "$OS" == "oracle" ]; then
    sudo sed -i 's/ident/md5/g' "$PG_HBA"
    sudo sed -i 's/peer/md5/g' "$PG_HBA"
else
    sudo sed -i 's/peer/md5/g' "$PG_HBA"
    sudo sed -i 's/scram-sha-256/md5/g' "$PG_HBA"
fi

# Restart PostgreSQL
sudo systemctl restart postgresql

log_info "PostgreSQL authentication configured"

# Test connection
log_info "Testing database connection..."
PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1 as test;" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    log_info "Database connection successful!"
else
    log_error "Database connection failed. Check password and pg_hba.conf"
    exit 1
fi

# Create environment file
log_info "Creating environment file..."
cat > /opt/bridge-bidding-app/.env << EOF
# Bridge Bidding App - Production Environment
FLASK_ENV=production
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}
DEFAULT_AI_DIFFICULTY=expert
EOF

chmod 600 /opt/bridge-bidding-app/.env
log_info "Environment file created at /opt/bridge-bidding-app/.env"

log_info "=============================================="
log_info "Database setup complete!"
log_info ""
log_info "Connection string:"
log_info "postgresql://${DB_USER}:****@localhost:5432/${DB_NAME}"
log_info ""
log_info "Next step: bash deploy-app.sh <github_repo_url>"

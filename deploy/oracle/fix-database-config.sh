#!/bin/bash
# fix-database-config.sh
# Diagnose and fix DATABASE_URL issues on Oracle production server
#
# Usage: bash fix-database-config.sh [diagnose|fix-sqlite|fix-postgres]
#
# Run this script ON the Oracle server after SSHing in:
#   ssh opc@<ORACLE_IP>
#   bash /opt/bridge-bidding-app/deploy/oracle/fix-database-config.sh diagnose

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

APP_DIR="/opt/bridge-bidding-app"
BACKEND_DIR="$APP_DIR/backend"
ENV_FILE="$BACKEND_DIR/.env"
SERVICE_FILE="/etc/systemd/system/bridge-backend.service"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Database Configuration Diagnostic Tool${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

diagnose() {
    echo -e "${YELLOW}=== STEP 1: Checking DATABASE_URL in .env file ===${NC}"
    if [ -f "$ENV_FILE" ]; then
        echo -e "File exists: ${GREEN}$ENV_FILE${NC}"
        if grep -q "DATABASE_URL" "$ENV_FILE"; then
            echo -e "${RED}Found DATABASE_URL:${NC}"
            grep "DATABASE_URL" "$ENV_FILE"

            if grep -q "dpg-" "$ENV_FILE"; then
                echo -e "${RED}⚠️  WARNING: This is a Render PostgreSQL URL!${NC}"
                echo -e "${RED}   This is causing the connection error.${NC}"
            elif grep -q "localhost" "$ENV_FILE"; then
                echo -e "${GREEN}✓ Points to localhost (local PostgreSQL)${NC}"
            fi
        else
            echo -e "${GREEN}✓ No DATABASE_URL set (will use SQLite)${NC}"
        fi
    else
        echo -e "${YELLOW}No .env file found (will use defaults)${NC}"
    fi
    echo ""

    echo -e "${YELLOW}=== STEP 2: Checking systemd service file ===${NC}"
    if [ -f "$SERVICE_FILE" ]; then
        echo -e "File exists: ${GREEN}$SERVICE_FILE${NC}"
        if grep -qi "DATABASE_URL" "$SERVICE_FILE"; then
            echo -e "${RED}Found DATABASE_URL in service file:${NC}"
            grep -i "DATABASE_URL" "$SERVICE_FILE"
        else
            echo -e "${GREEN}✓ No DATABASE_URL in service file${NC}"
        fi

        if grep -q "EnvironmentFile" "$SERVICE_FILE"; then
            echo -e "${BLUE}EnvironmentFile reference:${NC}"
            grep "EnvironmentFile" "$SERVICE_FILE"
        fi
    else
        echo -e "${YELLOW}No systemd service file found${NC}"
    fi
    echo ""

    echo -e "${YELLOW}=== STEP 3: Checking environment variables ===${NC}"
    if [ -n "$DATABASE_URL" ]; then
        echo -e "${RED}DATABASE_URL is set in environment:${NC}"
        echo "$DATABASE_URL"
        if echo "$DATABASE_URL" | grep -q "dpg-"; then
            echo -e "${RED}⚠️  WARNING: This is a Render PostgreSQL URL!${NC}"
        fi
    else
        echo -e "${GREEN}✓ DATABASE_URL not set in current environment${NC}"
    fi
    echo ""

    echo -e "${YELLOW}=== STEP 4: Checking local PostgreSQL ===${NC}"
    if command -v psql &> /dev/null; then
        echo -e "${GREEN}PostgreSQL client installed${NC}"
        if sudo systemctl is-active --quiet postgresql 2>/dev/null; then
            echo -e "${GREEN}✓ PostgreSQL service is running${NC}"

            # Check if bridge database exists
            if sudo -u postgres psql -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "bridge_bidding"; then
                echo -e "${GREEN}✓ bridge_bidding database exists${NC}"
            else
                echo -e "${YELLOW}bridge_bidding database not found${NC}"
            fi
        else
            echo -e "${YELLOW}PostgreSQL service is not running${NC}"
        fi
    else
        echo -e "${YELLOW}PostgreSQL not installed (SQLite will be used)${NC}"
    fi
    echo ""

    echo -e "${YELLOW}=== STEP 5: Checking SQLite database ===${NC}"
    if [ -f "$BACKEND_DIR/bridge.db" ]; then
        echo -e "${GREEN}✓ SQLite database exists: $BACKEND_DIR/bridge.db${NC}"
        ls -lh "$BACKEND_DIR/bridge.db"
    else
        echo -e "${YELLOW}No SQLite database found${NC}"
    fi
    echo ""

    echo -e "${YELLOW}=== STEP 6: Testing backend connection ===${NC}"
    if curl -s "http://localhost:5001/api/scenarios" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is responding${NC}"
    else
        echo -e "${RED}✗ Backend is not responding on port 5001${NC}"
    fi
    echo ""

    echo -e "${YELLOW}=== STEP 7: Recent backend logs ===${NC}"
    echo "Last 10 lines of backend logs:"
    sudo journalctl -u bridge-backend --no-pager -n 10 2>/dev/null || echo "Could not read logs"
    echo ""

    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}  DIAGNOSIS COMPLETE${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""
    echo "To fix the issue, run one of:"
    echo "  bash $0 fix-sqlite    # Use SQLite (simpler, no PostgreSQL needed)"
    echo "  bash $0 fix-postgres  # Use local PostgreSQL"
}

fix_sqlite() {
    echo -e "${YELLOW}=== Configuring backend to use SQLite ===${NC}"
    echo ""

    # Backup existing .env if it exists
    if [ -f "$ENV_FILE" ]; then
        cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
        echo -e "${GREEN}✓ Backed up existing .env file${NC}"
    fi

    # Create new .env without DATABASE_URL
    cat > "$ENV_FILE" << 'EOF'
# Backend Environment Configuration
# Production on Oracle Cloud

# AI Configuration
DEFAULT_AI_DIFFICULTY=expert

# Database: Using SQLite (bridge.db)
# To use PostgreSQL instead, uncomment and set:
# DATABASE_URL=postgresql://bridge_user:password@localhost:5432/bridge_bidding
EOF

    echo -e "${GREEN}✓ Created new .env file (SQLite mode)${NC}"

    # Initialize SQLite database if needed
    echo -e "${YELLOW}Initializing SQLite database...${NC}"
    cd "$BACKEND_DIR"
    source venv/bin/activate 2>/dev/null || true
    python3 database/init_all_tables.py 2>/dev/null || echo "Database init script not found or failed"

    # Restart backend
    echo -e "${YELLOW}Restarting backend service...${NC}"
    sudo systemctl restart bridge-backend
    sleep 3

    # Verify
    echo -e "${YELLOW}Verifying backend...${NC}"
    if curl -s "http://localhost:5001/api/scenarios" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is responding!${NC}"
        echo ""
        echo -e "${GREEN}=== FIX SUCCESSFUL ===${NC}"
        echo "The backend is now using SQLite."
        echo "Test the dashboard: curl 'http://localhost:5001/api/analytics/dashboard?user_id=1'"
    else
        echo -e "${RED}✗ Backend still not responding${NC}"
        echo "Check logs: sudo journalctl -u bridge-backend -f"
    fi
}

fix_postgres() {
    echo -e "${YELLOW}=== Configuring backend to use local PostgreSQL ===${NC}"
    echo ""

    # Check if PostgreSQL is running
    if ! sudo systemctl is-active --quiet postgresql 2>/dev/null; then
        echo -e "${RED}PostgreSQL is not running. Starting it...${NC}"
        sudo systemctl start postgresql
        sudo systemctl enable postgresql
    fi

    # Prompt for password
    echo -e "${YELLOW}Enter the PostgreSQL password for bridge_user:${NC}"
    read -s DB_PASSWORD
    echo ""

    # Backup existing .env if it exists
    if [ -f "$ENV_FILE" ]; then
        cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
        echo -e "${GREEN}✓ Backed up existing .env file${NC}"
    fi

    # Create new .env with local PostgreSQL
    cat > "$ENV_FILE" << EOF
# Backend Environment Configuration
# Production on Oracle Cloud

# AI Configuration
DEFAULT_AI_DIFFICULTY=expert

# Database: Local PostgreSQL
DATABASE_URL=postgresql://bridge_user:${DB_PASSWORD}@localhost:5432/bridge_bidding
EOF

    echo -e "${GREEN}✓ Created new .env file (PostgreSQL mode)${NC}"

    # Initialize database
    echo -e "${YELLOW}Initializing PostgreSQL database...${NC}"
    cd "$BACKEND_DIR"
    source venv/bin/activate 2>/dev/null || true
    python3 database/init_all_tables.py 2>/dev/null || echo "Database init script not found or failed"

    # Restart backend
    echo -e "${YELLOW}Restarting backend service...${NC}"
    sudo systemctl restart bridge-backend
    sleep 3

    # Verify
    echo -e "${YELLOW}Verifying backend...${NC}"
    if curl -s "http://localhost:5001/api/scenarios" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is responding!${NC}"
        echo ""
        echo -e "${GREEN}=== FIX SUCCESSFUL ===${NC}"
        echo "The backend is now using local PostgreSQL."
        echo "Test the dashboard: curl 'http://localhost:5001/api/analytics/dashboard?user_id=1'"
    else
        echo -e "${RED}✗ Backend still not responding${NC}"
        echo "Check logs: sudo journalctl -u bridge-backend -f"
    fi
}

# Main
case "${1:-diagnose}" in
    diagnose)
        diagnose
        ;;
    fix-sqlite)
        fix_sqlite
        ;;
    fix-postgres)
        fix_postgres
        ;;
    *)
        echo "Usage: $0 [diagnose|fix-sqlite|fix-postgres]"
        echo ""
        echo "  diagnose     - Show current database configuration (default)"
        echo "  fix-sqlite   - Configure backend to use SQLite"
        echo "  fix-postgres - Configure backend to use local PostgreSQL"
        exit 1
        ;;
esac

#!/bin/bash
# Oracle Cloud Always Free - Server Setup Script
# Run this script on your Oracle Cloud VM after SSH connection
# Usage: bash setup-server.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Detect OS
detect_os() {
    if [ -f /etc/oracle-release ]; then
        OS="oracle"
        PKG_MANAGER="dnf"
    elif [ -f /etc/lsb-release ]; then
        OS="ubuntu"
        PKG_MANAGER="apt"
    else
        log_error "Unsupported operating system"
        exit 1
    fi
    log_info "Detected OS: $OS"
}

# Update system
update_system() {
    log_info "Updating system packages..."
    if [ "$OS" == "oracle" ]; then
        sudo dnf update -y
    else
        sudo apt update && sudo apt upgrade -y
    fi
}

# Install Python 3.11
install_python() {
    log_info "Installing Python 3.11..."
    if [ "$OS" == "oracle" ]; then
        sudo dnf install python3.11 python3.11-pip python3.11-devel -y
    else
        sudo apt install python3.11 python3.11-venv python3.11-dev -y
    fi
    python3.11 --version
}

# Install Node.js 20 LTS
install_nodejs() {
    log_info "Installing Node.js 20 LTS..."
    if [ "$OS" == "oracle" ]; then
        curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
        sudo dnf install nodejs -y
    else
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
        sudo apt install nodejs -y
    fi
    node --version
    npm --version
}

# Install Nginx
install_nginx() {
    log_info "Installing Nginx..."
    if [ "$OS" == "oracle" ]; then
        sudo dnf install nginx -y
    else
        sudo apt install nginx -y
    fi
    nginx -v
}

# Install PostgreSQL
install_postgresql() {
    log_info "Installing PostgreSQL..."
    if [ "$OS" == "oracle" ]; then
        sudo dnf install postgresql-server postgresql-contrib -y
        # Initialize database
        sudo postgresql-setup --initdb
    else
        sudo apt install postgresql postgresql-contrib -y
    fi

    # Start PostgreSQL
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    log_info "PostgreSQL installed and started"
}

# Install build tools (for DDS)
install_build_tools() {
    log_info "Installing build tools for DDS..."
    if [ "$OS" == "oracle" ]; then
        sudo dnf groupinstall "Development Tools" -y
    else
        sudo apt install build-essential -y
    fi
}

# Install Git
install_git() {
    log_info "Installing Git..."
    if [ "$OS" == "oracle" ]; then
        sudo dnf install git -y
    else
        sudo apt install git -y
    fi
    git --version
}

# Configure firewall
configure_firewall() {
    log_info "Configuring firewall..."
    if [ "$OS" == "oracle" ]; then
        sudo firewall-cmd --permanent --add-service=http
        sudo firewall-cmd --permanent --add-service=https
        sudo firewall-cmd --permanent --add-port=22/tcp
        sudo firewall-cmd --reload
        log_info "Firewalld configured"
    else
        sudo ufw allow 22/tcp
        sudo ufw allow 80/tcp
        sudo ufw allow 443/tcp
        sudo ufw --force enable
        log_info "UFW configured"
    fi
}

# Create application directory
create_app_directory() {
    log_info "Creating application directory..."
    sudo mkdir -p /opt/bridge-bidding-app
    sudo chown $USER:$USER /opt/bridge-bidding-app
}

# Main
main() {
    log_info "Starting Oracle Cloud VM setup for Bridge Bidding App"
    log_info "=============================================="

    detect_os
    update_system
    install_python
    install_nodejs
    install_nginx
    install_postgresql
    install_build_tools
    install_git
    configure_firewall
    create_app_directory

    log_info "=============================================="
    log_info "Server setup complete!"
    log_info ""
    log_info "Next steps:"
    log_info "1. Run: bash setup-database.sh <password>"
    log_info "2. Run: bash deploy-app.sh <github_repo_url>"
    log_info "3. Run: bash configure-nginx.sh"
}

main "$@"

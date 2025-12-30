#!/bin/bash
# Oracle Cloud Free Tier - Keep-Alive Script
# Prevents instance reclamation by maintaining CPU usage above 20% threshold
#
# Oracle's reclamation criteria (7-day window, 95th percentile):
# - CPU Utilization: < 20%
# - Memory Utilization: < 20% (ARM/Ampere A1 shapes)
# - Network Utilization: < 20%
#
# This script runs CPU stress periodically to ensure usage stays above threshold.
# It's designed for the Always Free tier micro instances.
#
# Usage:
#   bash keep-alive.sh install    # Install and enable systemd service + timer
#   bash keep-alive.sh uninstall  # Remove systemd service + timer
#   bash keep-alive.sh status     # Check if keep-alive is active
#   bash keep-alive.sh run        # Run one stress cycle (called by timer)
#   bash keep-alive.sh test       # Test run with shorter duration

set -e

# Configuration
STRESS_DURATION="30m"       # Duration of each stress cycle (30 min every 4 hours = 12.5% of time)
STRESS_CPU_PERCENT=25       # Target CPU percentage
LOG_FILE="/var/log/oracle-keep-alive.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if stress-ng is installed
check_stress_ng() {
    if ! command -v stress-ng &> /dev/null; then
        log_warn "stress-ng not found. Installing..."
        if [ -f /etc/oracle-release ]; then
            sudo dnf install -y epel-release
            sudo dnf install -y stress-ng
        elif [ -f /etc/lsb-release ]; then
            sudo apt update
            sudo apt install -y stress-ng
        else
            log_error "Cannot install stress-ng: unsupported OS"
            exit 1
        fi
        log_info "stress-ng installed successfully"
    fi
}

# Run one stress cycle
run_stress() {
    local duration="${1:-$STRESS_DURATION}"
    local cpu_percent="${2:-$STRESS_CPU_PERCENT}"

    log_info "Starting CPU stress: ${cpu_percent}% for ${duration}"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting stress cycle: ${cpu_percent}% for ${duration}" >> "$LOG_FILE"

    # Run stress-ng with specified CPU load
    # --cpu 0 means use all available CPUs
    # --cpu-load sets the target CPU percentage
    stress-ng --cpu 0 --cpu-load "$cpu_percent" --timeout "$duration" --quiet

    echo "$(date '+%Y-%m-%d %H:%M:%S') - Stress cycle completed" >> "$LOG_FILE"
    log_info "Stress cycle completed"
}

# Create systemd service
create_service() {
    log_info "Creating systemd service..."

    sudo tee /etc/systemd/system/oracle-keep-alive.service > /dev/null << 'EOF'
[Unit]
Description=Oracle Cloud Keep-Alive CPU Stress
Documentation=https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
After=network.target

[Service]
Type=oneshot
ExecStart=/opt/bridge-bidding-app/deploy/oracle/keep-alive.sh run
StandardOutput=append:/var/log/oracle-keep-alive.log
StandardError=append:/var/log/oracle-keep-alive.log

[Install]
WantedBy=multi-user.target
EOF

    log_info "Service file created"
}

# Create systemd timer (runs every 4 hours)
create_timer() {
    log_info "Creating systemd timer..."

    # Timer runs every 4 hours with some randomization
    # 4-hour intervals + 10-minute stress = ~4% of time at high CPU
    # Combined with normal app usage, should keep 95th percentile above 20%
    sudo tee /etc/systemd/system/oracle-keep-alive.timer > /dev/null << 'EOF'
[Unit]
Description=Oracle Cloud Keep-Alive Timer
Documentation=https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm

[Timer]
# Run every 4 hours
OnCalendar=*-*-* 00,04,08,12,16,20:00:00
# Add randomization to avoid detection patterns
RandomizedDelaySec=1800
# Start immediately on boot
OnBootSec=5min
Persistent=true

[Install]
WantedBy=timers.target
EOF

    log_info "Timer file created"
}

# Install and enable the service
install_keepalive() {
    log_info "Installing Oracle Keep-Alive service..."

    # Check and install stress-ng
    check_stress_ng

    # Create log file
    sudo touch "$LOG_FILE"
    sudo chmod 644 "$LOG_FILE"

    # Copy script to app directory if not already there
    SCRIPT_DIR="/opt/bridge-bidding-app/deploy/oracle"
    if [ ! -d "$SCRIPT_DIR" ]; then
        sudo mkdir -p "$SCRIPT_DIR"
    fi

    # Make sure script is executable
    SCRIPT_PATH="$SCRIPT_DIR/keep-alive.sh"
    if [ -f "$SCRIPT_PATH" ]; then
        sudo chmod +x "$SCRIPT_PATH"
    else
        log_error "Script not found at $SCRIPT_PATH"
        log_info "Please copy keep-alive.sh to $SCRIPT_DIR first"
        exit 1
    fi

    # Create systemd files
    create_service
    create_timer

    # Reload systemd
    sudo systemctl daemon-reload

    # Enable and start timer
    sudo systemctl enable oracle-keep-alive.timer
    sudo systemctl start oracle-keep-alive.timer

    log_info "Installation complete!"
    log_info ""
    log_info "Schedule: Every 4 hours with 30-minute random delay"
    log_info "Duration: ${STRESS_DURATION} at ${STRESS_CPU_PERCENT}% CPU"
    log_info "Log file: ${LOG_FILE}"
    log_info ""
    log_info "Check status: bash keep-alive.sh status"
    log_info "View logs: tail -f ${LOG_FILE}"
}

# Uninstall the service
uninstall_keepalive() {
    log_info "Uninstalling Oracle Keep-Alive service..."

    # Stop and disable timer
    sudo systemctl stop oracle-keep-alive.timer 2>/dev/null || true
    sudo systemctl disable oracle-keep-alive.timer 2>/dev/null || true

    # Remove systemd files
    sudo rm -f /etc/systemd/system/oracle-keep-alive.service
    sudo rm -f /etc/systemd/system/oracle-keep-alive.timer

    # Reload systemd
    sudo systemctl daemon-reload

    log_info "Service uninstalled"
    log_info "Log file preserved at: ${LOG_FILE}"
}

# Show status
show_status() {
    echo "Oracle Keep-Alive Status"
    echo "========================"
    echo ""

    echo "Timer Status:"
    systemctl status oracle-keep-alive.timer --no-pager 2>/dev/null || echo "  Timer not installed"

    echo ""
    echo "Next scheduled run:"
    systemctl list-timers oracle-keep-alive.timer --no-pager 2>/dev/null || echo "  Timer not scheduled"

    echo ""
    echo "Recent log entries:"
    if [ -f "$LOG_FILE" ]; then
        tail -10 "$LOG_FILE"
    else
        echo "  No log file found"
    fi

    echo ""
    echo "Current CPU usage:"
    top -bn1 | head -5 | tail -3
}

# Test run (short duration)
test_run() {
    log_info "Running test stress (30 seconds at 30% CPU)..."
    check_stress_ng
    run_stress "30s" 30
    log_info "Test completed"
}

# Main
main() {
    case "${1:-help}" in
        install)
            install_keepalive
            ;;
        uninstall)
            uninstall_keepalive
            ;;
        status)
            show_status
            ;;
        run)
            run_stress
            ;;
        test)
            test_run
            ;;
        *)
            echo "Oracle Cloud Free Tier - Keep-Alive Script"
            echo ""
            echo "Prevents instance reclamation by maintaining CPU usage above 20%"
            echo ""
            echo "Usage: bash keep-alive.sh [command]"
            echo ""
            echo "Commands:"
            echo "  install     Install and enable systemd service + timer"
            echo "  uninstall   Remove systemd service + timer"
            echo "  status      Check if keep-alive is active"
            echo "  run         Run one stress cycle (used by timer)"
            echo "  test        Test run with 30-second duration"
            echo ""
            echo "Configuration:"
            echo "  Stress duration: ${STRESS_DURATION}"
            echo "  Target CPU:      ${STRESS_CPU_PERCENT}%"
            echo "  Frequency:       Every 4 hours"
            echo "  Coverage:        ~12.5% of time at elevated CPU"
            echo ""
            echo "How it works:"
            echo "  Oracle reclaims instances if 95th percentile CPU < 20% over 7 days."
            echo "  This script runs CPU stress every 4 hours for ${STRESS_DURATION},"
            echo "  ensuring the 95th percentile stays above the threshold even with"
            echo "  minimal application usage."
            ;;
    esac
}

main "$@"

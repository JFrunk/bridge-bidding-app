#!/bin/bash
# Parallel retry script - one process per AD, all running simultaneously
# When ANY AD succeeds, all others are killed and deployment begins

set -o pipefail

OCI="/Users/simonroy/bin/oci"
export SUPPRESS_LABEL_WARNING=True

COMPARTMENT="ocid1.tenancy.oc1..aaaaaaaaffwwphxn7pjs2zx6rh6ke37dyfq2jla4doetqvs44nt3jyvpzixq"
IMAGE="ocid1.image.oc1.phx.aaaaaaaahzur55ghl5ypjy27zsuh7adac4ppnofrp2d3wuxu7iam4ibgkaia"
SUBNET="ocid1.subnet.oc1.phx.aaaaaaaa3gdyn5jdexo6pscsp3hjesy3l3xbznqp7mzslgj7zoyx76gpvclq"
SSH_KEY_FILE="$HOME/.ssh/id_rsa.pub"
SSH_PRIVATE_KEY="$HOME/.ssh/id_rsa"
SHAPE="VM.Standard.A1.Flex"
OCPUS=2
MEMORY_GB=12
DISPLAY_NAME="bridge-app"
DB_PASSWORD="BridgeApp2026Secure!"

PROJECT_DIR="/Users/simonroy/Desktop/Bridge-Bidding-Program"
LOG_FILE="/tmp/oracle-instance-creation.log"
SUCCESS_FILE="/tmp/oracle-instance-success"
PID_FILE="/tmp/oracle-ad-pids"

ADS=("Gxwa:PHX-AD-1" "Gxwa:PHX-AD-2" "Gxwa:PHX-AD-3")
RETRY_INTERVAL=30

log() {
    echo "$(date '+%H:%M:%S'): $1" | tee -a "$LOG_FILE"
}

# Remove any stale success file
rm -f "$SUCCESS_FILE"
rm -f "$PID_FILE"

# ============================================
# Per-AD retry loop (runs as background process)
# ============================================
retry_ad() {
    local ad="$1"
    local ad_short="${ad##*-}"  # AD-1, AD-2, AD-3
    local attempt=0

    while [ ! -f "$SUCCESS_FILE" ]; do
        attempt=$((attempt + 1))
        log "[$ad_short] Attempt #$attempt"

        result=$($OCI compute instance launch \
            --compartment-id "$COMPARTMENT" \
            --availability-domain "$ad" \
            --shape "$SHAPE" \
            --shape-config "{\"ocpus\": $OCPUS, \"memoryInGBs\": $MEMORY_GB}" \
            --image-id "$IMAGE" \
            --subnet-id "$SUBNET" \
            --assign-public-ip true \
            --display-name "$DISPLAY_NAME" \
            --ssh-authorized-keys-file "$SSH_KEY_FILE" \
            2>&1)

        exit_code=$?

        # Check if another AD already succeeded
        if [ -f "$SUCCESS_FILE" ]; then
            log "[$ad_short] Another AD succeeded. Stopping."
            return 0
        fi

        if [ $exit_code -eq 0 ]; then
            instance_id=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null)

            if [ -n "$instance_id" ]; then
                # Signal success to other processes
                echo "$instance_id" > "$SUCCESS_FILE"
                log "[$ad_short] ========================================="
                log "[$ad_short]   INSTANCE LAUNCHED! ID: $instance_id"
                log "[$ad_short] ========================================="
                return 0
            fi
        fi

        if echo "$result" | grep -qi "out of capacity\|Out of host capacity"; then
            log "[$ad_short] Out of capacity"
        elif echo "$result" | grep -qi "TooManyRequests"; then
            log "[$ad_short] Rate limited - backing off 120s"
            sleep 120
        elif echo "$result" | grep -qi "timed out\|timeout"; then
            log "[$ad_short] API timeout"
        else
            log "[$ad_short] Error: $(echo "$result" | grep -i 'message' | head -1 | cut -c1-80)"
        fi

        # Stagger retries with jitter to avoid rate limiting
        local jitter=$((RANDOM % 15))
        sleep $((RETRY_INTERVAL + jitter))
    done
}

# ============================================
# Post-creation: deploy application
# ============================================
deploy_after_creation() {
    local instance_id="$1"

    log "Waiting for instance to reach RUNNING state..."
    $OCI compute instance get --instance-id "$instance_id" \
        --wait-for-state RUNNING \
        --wait-interval-seconds 10 \
        --max-wait-seconds 600 >> "$LOG_FILE" 2>&1

    sleep 10

    PUBLIC_IP=$($OCI compute instance list-vnics \
        --instance-id "$instance_id" \
        --query 'data[0]."public-ip"' \
        --raw-output 2>/dev/null)

    log "========================================="
    log "  PUBLIC IP: $PUBLIC_IP"
    log "========================================="

    # Update SSH config
    log "Updating SSH config..."
    SSH_CONFIG="$HOME/.ssh/config"
    if grep -q "oracle-bridge" "$SSH_CONFIG" 2>/dev/null; then
        sed -i.bak "/Host oracle-bridge/,/^Host /{s/HostName .*/HostName $PUBLIC_IP/}" "$SSH_CONFIG"
        sed -i.bak "/Host oracle-bridge/,/^Host /{s/User .*/User ubuntu/}" "$SSH_CONFIG"
    else
        cat >> "$SSH_CONFIG" << EOF

Host oracle-bridge
    HostName $PUBLIC_IP
    User ubuntu
    IdentityFile $SSH_PRIVATE_KEY
    StrictHostKeyChecking no
EOF
    fi

    # Wait for SSH
    log "Waiting for SSH (cloud-init takes 2-5 min)..."
    local elapsed=0
    while [ $elapsed -lt 300 ]; do
        if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -i "$SSH_PRIVATE_KEY" ubuntu@"$PUBLIC_IP" "echo SSH_OK" 2>/dev/null | grep -q "SSH_OK"; then
            log "SSH is ready!"
            break
        fi
        sleep 15
        elapsed=$((elapsed + 15))
        log "  Waiting... (${elapsed}s)"
    done

    # Wait for cloud-init
    log "Waiting for cloud-init..."
    ssh -o StrictHostKeyChecking=no -i "$SSH_PRIVATE_KEY" ubuntu@"$PUBLIC_IP" "cloud-init status --wait" >> "$LOG_FILE" 2>&1 || true
    sleep 5

    # Deploy
    log "Deploying application (10-15 min)..."
    scp -o StrictHostKeyChecking=no -i "$SSH_PRIVATE_KEY" \
        "$PROJECT_DIR/deploy/oracle/deploy-all.sh" \
        ubuntu@"$PUBLIC_IP":/tmp/deploy-all.sh

    ssh -o StrictHostKeyChecking=no -i "$SSH_PRIVATE_KEY" ubuntu@"$PUBLIC_IP" \
        "chmod +x /tmp/deploy-all.sh && sudo bash /tmp/deploy-all.sh '$DB_PASSWORD'" 2>&1 | tee -a "$LOG_FILE"

    # Keep-alive
    log "Setting up keep-alive..."
    ssh -o StrictHostKeyChecking=no -i "$SSH_PRIVATE_KEY" ubuntu@"$PUBLIC_IP" \
        "cd /opt/bridge-bidding-app && sudo bash deploy/oracle/maintenance.sh setup-anti-idle" 2>&1 | tee -a "$LOG_FILE" || true

    # Verify
    sleep 5
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "http://$PUBLIC_IP/health" 2>/dev/null)

    log "========================================="
    if [ "$HTTP_CODE" = "200" ]; then
        log "  DEPLOYMENT SUCCESSFUL!"
        log "  App live at: http://$PUBLIC_IP"
    else
        log "  HTTP returned $HTTP_CODE (may still be starting)"
    fi
    log "========================================="
    log ""
    log "REMAINING MANUAL STEPS:"
    log "1. Update DNS: app.mybridgebuddy.com -> $PUBLIC_IP"
    log "2. SSL: ssh oracle-bridge 'sudo bash /opt/bridge-bidding-app/deploy/oracle/setup-ssl.sh'"
    log "3. Revert landing page maintenance mode"
}

# ============================================
# MAIN
# ============================================
log "========================================="
log "PARALLEL Instance Creation (3 ADs simultaneously)"
log "========================================="

# Launch one process per AD
for ad in "${ADS[@]}"; do
    retry_ad "$ad" &
    echo $! >> "$PID_FILE"
    log "Launched worker for $ad (PID: $!)"
    sleep 2  # slight offset so logs don't collide
done

log "All 3 AD workers running. Waiting for success..."

# Wait for any worker to succeed
while [ ! -f "$SUCCESS_FILE" ]; do
    sleep 5
done

# Read result
INSTANCE_ID=$(cat "$SUCCESS_FILE")

# Kill remaining workers
if [ -f "$PID_FILE" ]; then
    while read pid; do
        kill "$pid" 2>/dev/null
    done < "$PID_FILE"
    rm -f "$PID_FILE"
fi

# Kill any lingering OCI CLI processes
pkill -f "oci compute instance launch" 2>/dev/null

if [ "$INSTANCE_ID" = "LIMIT_ERROR" ]; then
    log "FAILED: Resource limit reached. Cannot create instance."
    rm -f "$SUCCESS_FILE"
    exit 1
fi

log "Instance ID: $INSTANCE_ID"
deploy_after_creation "$INSTANCE_ID"

rm -f "$SUCCESS_FILE"
log "ALL DONE."

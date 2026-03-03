#!/bin/bash
# Auto-retry script for creating Oracle Cloud Always Free ARM instance
# After creation, automatically deploys the full application
#
# Log file: /tmp/oracle-instance-creation.log

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

ADS=("Gxwa:PHX-AD-1" "Gxwa:PHX-AD-2" "Gxwa:PHX-AD-3")

RETRY_INTERVAL=60

log() {
    echo "$(date): $1" | tee -a "$LOG_FILE"
}

# ============================================
# PHASE 1: Create Instance (retry loop)
# ============================================
create_instance() {
    local attempt=0
    while true; do
        attempt=$((attempt + 1))

        for ad in "${ADS[@]}"; do
            log "Attempt #$attempt - Trying $ad..."

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

            if [ $exit_code -eq 0 ]; then
                INSTANCE_ID=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null)
                log "========================================="
                log "  INSTANCE LAUNCHED! ID: $INSTANCE_ID"
                log "========================================="
                log "Waiting for RUNNING state..."

                $OCI compute instance get --instance-id "$INSTANCE_ID" \
                    --wait-for-state RUNNING \
                    --wait-interval-seconds 10 \
                    --max-wait-seconds 600 >> "$LOG_FILE" 2>&1

                sleep 10

                PUBLIC_IP=$($OCI compute instance list-vnics \
                    --instance-id "$INSTANCE_ID" \
                    --query 'data[0]."public-ip"' \
                    --raw-output 2>/dev/null)

                log "========================================="
                log "  PUBLIC IP: $PUBLIC_IP"
                log "========================================="
                return 0
            fi

            if echo "$result" | grep -qi "out of capacity\|Out of host capacity\|capacity"; then
                log "  -> Out of capacity in $ad"
            elif echo "$result" | grep -qi "limit\|quota\|exceeded\|LimitExceeded"; then
                log "ERROR: Resource limit reached. Cannot create instance."
                log "$result"
                exit 1
            else
                log "  -> Error: $(echo "$result" | grep -i 'message' | head -1)"
            fi
        done

        log "All ADs tried. Retrying in ${RETRY_INTERVAL}s..."
        sleep "$RETRY_INTERVAL"
    done
}

# ============================================
# PHASE 2: Update SSH config
# ============================================
update_ssh_config() {
    log "Updating SSH config with new IP: $PUBLIC_IP"

    SSH_CONFIG="$HOME/.ssh/config"
    if grep -q "oracle-bridge" "$SSH_CONFIG" 2>/dev/null; then
        # Update existing entry - replace the HostName line
        sed -i.bak "/Host oracle-bridge/,/^Host /{s/HostName .*/HostName $PUBLIC_IP/}" "$SSH_CONFIG"
        # Also update User to ubuntu (Ubuntu image)
        sed -i.bak "/Host oracle-bridge/,/^Host /{s/User .*/User ubuntu/}" "$SSH_CONFIG"
    else
        # Add new entry
        cat >> "$SSH_CONFIG" << EOF

Host oracle-bridge
    HostName $PUBLIC_IP
    User ubuntu
    IdentityFile $SSH_PRIVATE_KEY
    StrictHostKeyChecking no
EOF
    fi

    log "SSH config updated"
}

# ============================================
# PHASE 3: Wait for SSH access
# ============================================
wait_for_ssh() {
    log "Waiting for SSH to become available (cloud-init takes 2-5 min)..."
    local max_wait=300
    local elapsed=0

    while [ $elapsed -lt $max_wait ]; do
        if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -i "$SSH_PRIVATE_KEY" ubuntu@"$PUBLIC_IP" "echo SSH_OK" 2>/dev/null | grep -q "SSH_OK"; then
            log "SSH is ready!"
            return 0
        fi
        sleep 15
        elapsed=$((elapsed + 15))
        log "  Waiting for SSH... (${elapsed}s / ${max_wait}s)"
    done

    log "ERROR: SSH not available after ${max_wait}s"
    return 1
}

# ============================================
# PHASE 4: Deploy application
# ============================================
deploy_app() {
    log "Starting application deployment..."

    SSH_CMD="ssh -o StrictHostKeyChecking=no -i $SSH_PRIVATE_KEY ubuntu@$PUBLIC_IP"

    # Wait for cloud-init to finish
    log "Waiting for cloud-init to complete..."
    $SSH_CMD "cloud-init status --wait" >> "$LOG_FILE" 2>&1 || true
    sleep 5

    # Copy deploy script to server
    log "Copying deployment script..."
    scp -o StrictHostKeyChecking=no -i "$SSH_PRIVATE_KEY" \
        "$PROJECT_DIR/deploy/oracle/deploy-all.sh" \
        ubuntu@"$PUBLIC_IP":/tmp/deploy-all.sh

    # Run deployment
    log "Running deploy-all.sh (this takes 10-15 minutes)..."
    $SSH_CMD "chmod +x /tmp/deploy-all.sh && sudo bash /tmp/deploy-all.sh '$DB_PASSWORD'" 2>&1 | tee -a "$LOG_FILE"

    log "Deployment script completed"
}

# ============================================
# PHASE 5: Setup keep-alive
# ============================================
setup_keepalive() {
    log "Setting up keep-alive anti-idle protection..."

    SSH_CMD="ssh -o StrictHostKeyChecking=no -i $SSH_PRIVATE_KEY ubuntu@$PUBLIC_IP"

    # The keep-alive script should already be in the repo after deploy
    $SSH_CMD "cd /opt/bridge-bidding-app && sudo bash deploy/oracle/maintenance.sh setup-anti-idle" 2>&1 | tee -a "$LOG_FILE" || {
        log "Keep-alive setup via maintenance.sh failed, setting up basic cron..."
        $SSH_CMD "sudo crontab -l 2>/dev/null | grep -v stress; (sudo crontab -l 2>/dev/null; echo '*/30 * * * * stress-ng --cpu 1 --timeout 300 2>/dev/null || dd if=/dev/urandom bs=1M count=100 of=/dev/null 2>/dev/null') | sudo crontab -" 2>&1 | tee -a "$LOG_FILE"
    }

    log "Keep-alive configured"
}

# ============================================
# PHASE 6: Verify deployment
# ============================================
verify_deployment() {
    log "Verifying deployment..."

    SSH_CMD="ssh -o StrictHostKeyChecking=no -i $SSH_PRIVATE_KEY ubuntu@$PUBLIC_IP"

    # Check services
    $SSH_CMD "systemctl is-active bridge-backend nginx" 2>&1 | tee -a "$LOG_FILE"

    # Check HTTP
    sleep 5
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "http://$PUBLIC_IP/health" 2>/dev/null)

    if [ "$HTTP_CODE" = "200" ]; then
        log "========================================="
        log "  DEPLOYMENT SUCCESSFUL!"
        log "  App is live at: http://$PUBLIC_IP"
        log "========================================="
    else
        log "WARNING: HTTP check returned $HTTP_CODE"
        log "App may still be starting up. Check: ssh oracle-bridge 'bash /opt/bridge-bidding-app/deploy/oracle/maintenance.sh status'"
    fi

    log ""
    log "REMAINING MANUAL STEPS:"
    log "1. Update DNS: Point app.mybridgebuddy.com to $PUBLIC_IP"
    log "2. Setup SSL: ssh oracle-bridge 'sudo bash /opt/bridge-bidding-app/deploy/oracle/setup-ssl.sh'"
    log "3. Update frontend .env.production with https://app.mybridgebuddy.com"
    log "4. Rebuild frontend: ssh oracle-bridge 'cd /opt/bridge-bidding-app/frontend && sudo npm run build'"
    log ""
}

# ============================================
# MAIN
# ============================================
main() {
    log "========================================="
    log "Oracle Cloud Instance Creation + Deploy"
    log "========================================="
    log "Log file: $LOG_FILE"

    create_instance
    update_ssh_config
    wait_for_ssh
    deploy_app
    setup_keepalive
    verify_deployment

    log "ALL DONE. Check $LOG_FILE for full log."
}

main "$@"

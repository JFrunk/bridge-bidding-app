#!/bin/bash
# Parallel retry for Ashburn region (second account)

set -o pipefail

OCI="/Users/simonroy/bin/oci"
export SUPPRESS_LABEL_WARNING=True
PROFILE="ASHBURN"

COMPARTMENT="ocid1.tenancy.oc1..aaaaaaaaxj5gxyr6hnkidokdol5zafytu3mgipre6jduln4zx6b6oa2opxqa"
IMAGE="ocid1.image.oc1.iad.aaaaaaaa3axglz7hak6fmtcrpfckybc4j7zkausb4xpbqwbfypzfsto2pdmq"
SUBNET="ocid1.subnet.oc1.iad.aaaaaaaat4jppht7ac7ozafia3pzr65x4q46mdiadntesgjnl4ngogclb3eq"
SSH_KEY_FILE="$HOME/.ssh/id_rsa.pub"
SSH_PRIVATE_KEY="$HOME/.ssh/id_rsa"
SHAPE="VM.Standard.A1.Flex"
OCPUS=2
MEMORY_GB=12
DISPLAY_NAME="bridge-app"
DB_PASSWORD="BridgeApp2026Secure!"

PROJECT_DIR="/Users/simonroy/Desktop/Bridge-Bidding-Program"
LOG_FILE="/tmp/oracle-ashburn-creation.log"
SUCCESS_FILE="/tmp/oracle-ashburn-success"
PID_FILE="/tmp/oracle-ashburn-pids"

ADS=("SChD:US-ASHBURN-AD-1" "SChD:US-ASHBURN-AD-2" "SChD:US-ASHBURN-AD-3")
RETRY_INTERVAL=30

log() {
    echo "$(date '+%H:%M:%S'): $1" | tee -a "$LOG_FILE"
}

rm -f "$SUCCESS_FILE" "$PID_FILE"

retry_ad() {
    local ad="$1"
    local ad_short="${ad##*-}"
    local attempt=0

    while [ ! -f "$SUCCESS_FILE" ]; do
        attempt=$((attempt + 1))
        log "[ASH-$ad_short] Attempt #$attempt"

        result=$($OCI compute instance launch \
            --profile "$PROFILE" \
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

        if [ -f "$SUCCESS_FILE" ]; then
            log "[ASH-$ad_short] Another AD succeeded. Stopping."
            return 0
        fi

        if [ $exit_code -eq 0 ]; then
            instance_id=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null)
            if [ -n "$instance_id" ]; then
                echo "$instance_id" > "$SUCCESS_FILE"
                log "[ASH-$ad_short] ========================================="
                log "[ASH-$ad_short]   INSTANCE LAUNCHED! ID: $instance_id"
                log "[ASH-$ad_short] ========================================="
                return 0
            fi
        fi

        if echo "$result" | grep -qi "out of capacity\|Out of host capacity"; then
            log "[ASH-$ad_short] Out of capacity"
        elif echo "$result" | grep -qi "TooManyRequests"; then
            log "[ASH-$ad_short] Rate limited - backing off 120s"
            sleep 120
        elif echo "$result" | grep -qi "timed out\|timeout"; then
            log "[ASH-$ad_short] API timeout"
        else
            log "[ASH-$ad_short] Error: $(echo "$result" | grep -i 'message' | head -1 | cut -c1-80)"
        fi

        local jitter=$((RANDOM % 15))
        sleep $((RETRY_INTERVAL + jitter))
    done
}

deploy_after_creation() {
    local instance_id="$1"

    log "Waiting for instance RUNNING state..."
    $OCI compute instance get --profile "$PROFILE" --instance-id "$instance_id" \
        --wait-for-state RUNNING \
        --wait-interval-seconds 10 \
        --max-wait-seconds 600 >> "$LOG_FILE" 2>&1

    sleep 10

    PUBLIC_IP=$($OCI compute instance list-vnics --profile "$PROFILE" \
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
    log "Waiting for SSH..."
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
    log "Deploying application..."
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
        log "  ASHBURN DEPLOYMENT SUCCESSFUL!"
        log "  App live at: http://$PUBLIC_IP"
    else
        log "  HTTP returned $HTTP_CODE (may still be starting)"
    fi
    log "========================================="
    log "NEXT: Update DNS app.mybridgebuddy.com -> $PUBLIC_IP"
}

# MAIN
log "========================================="
log "ASHBURN Parallel Instance Creation"
log "========================================="

for ad in "${ADS[@]}"; do
    retry_ad "$ad" &
    echo $! >> "$PID_FILE"
    log "Launched worker for $ad (PID: $!)"
    sleep 2
done

log "All 3 Ashburn AD workers running..."

while [ ! -f "$SUCCESS_FILE" ]; do
    sleep 5
done

INSTANCE_ID=$(cat "$SUCCESS_FILE")

if [ -f "$PID_FILE" ]; then
    while read pid; do
        kill "$pid" 2>/dev/null
    done < "$PID_FILE"
    rm -f "$PID_FILE"
fi

pkill -f "oci compute instance launch.*ASHBURN" 2>/dev/null

log "Instance ID: $INSTANCE_ID"
deploy_after_creation "$INSTANCE_ID"

rm -f "$SUCCESS_FILE"
log "ALL DONE."

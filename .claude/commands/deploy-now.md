Quick deploy to Oracle Cloud production:

**Prerequisites verified:** SSH config exists at ~/.ssh/config with alias `oracle-bridge` → 161.153.7.196

**Execute deployment:**

```bash
# Pull latest from main and restart services
ssh oracle-bridge "cd /opt/bridge-bidding-app && git pull origin main && bash deploy/oracle/maintenance.sh restart"
```

**Verify deployment:**

```bash
curl -s https://app.mybridgebuddy.com/api/scenarios | head -c 100
```

This is a quick deployment command. For full safety checks, use `/deploy-production` instead.

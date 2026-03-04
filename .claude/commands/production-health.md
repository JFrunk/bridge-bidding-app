---
description: Check production server health and status
---

---
description: Check production server health and status
---

Check production server health and status.

⚠️ **Read-only — no modifications to production.**

---

## Checks to Run

Execute all checks via SSH to `hetzner-bridge` (178.156.132.108). Present results in a single summary.

### 1. Service Status

```bash
ssh hetzner-bridge "systemctl is-active gunicorn nginx && echo '---' && systemctl status gunicorn --no-pager -l | head -15"
```

### 2. Memory & Disk

```bash
ssh hetzner-bridge "free -h && echo '---' && df -h / && echo '---' && cat /proc/swaps"
```

### 3. API Health

```bash
curl -s --max-time 10 https://app.mybridgebuddy.com/api/ai/status | python3 -m json.tool
```

Response includes: `ai_type`, `dds_available`, `platform`, `python_version`.

### 4. Recent Errors

```bash
ssh hetzner-bridge "cd /opt/bridge-bidding-app/backend && python3 analyze_errors.py --recent 5 2>/dev/null || echo 'No error analyzer or no recent errors'"
```

### 5. SSL Certificate

```bash
echo | openssl s_client -servername app.mybridgebuddy.com -connect app.mybridgebuddy.com:443 2>/dev/null | openssl x509 -noout -dates 2>/dev/null
```

### 6. Application Logs (last 20 lines)

```bash
ssh hetzner-bridge "journalctl -u gunicorn --no-pager -n 20"
```

### 7. Recent User Feedback Count

```bash
ssh hetzner-bridge "echo 'Last 24h:' && find /opt/bridge-bidding-app/backend/user_feedback/ -mtime -1 -name '*.json' 2>/dev/null | wc -l && echo 'Last 7d:' && find /opt/bridge-bidding-app/backend/user_feedback/ -mtime -7 -name '*.json' 2>/dev/null | wc -l"
```

---

## Output Format

```
## Production Health Check — app.mybridgebuddy.com

| Check              | Status |
|--------------------|--------|
| Gunicorn           | active / inactive / error |
| Nginx              | active / inactive / error |
| API Response       | OK (Xms) / TIMEOUT / ERROR |
| DDS Available      | yes / no |
| Memory             | X/2048 MB used (X% free) |
| Swap               | X/1024 MB used |
| Disk               | X/40 GB used (X% free) |
| SSL Expiry         | YYYY-MM-DD (N days remaining) |
| Recent Errors (24h)| N errors |
| User Feedback (7d) | N items |

### Alerts
- [Any concerning findings: high memory, expiring SSL, error spikes, disk pressure]

### Recent Errors
- [Brief summary of last 5 errors if any]
```

---

## Success Criteria

- [ ] All 7 checks executed successfully
- [ ] No modifications made to production
- [ ] Alerts raised for concerning findings
- [ ] Summary presented in table format

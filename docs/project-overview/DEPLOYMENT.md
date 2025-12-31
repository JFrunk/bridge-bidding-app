# Deployment Guide - Bridge Bidding Training App

**Last Updated:** 2025-12-31

## Overview

The Bridge Bidding Training App is deployed on **Oracle Cloud Always Free** tier.

**Production URL:** https://app.mybridgebuddy.com

## Deployment Documentation

### Primary Documentation

For complete deployment instructions, see:

- **[Oracle Cloud Setup Guide](../../deploy/oracle/README.md)** - Full deployment instructions
- **[Oracle Cloud Migration Plan](../deployment/ORACLE_CLOUD_MIGRATION.md)** - Detailed migration documentation

### Quick Reference

#### Oracle Cloud Resources
- **Server:** ARM VM (2 OCPU, 12GB RAM, 100GB storage)
- **Database:** PostgreSQL on same VM
- **Proxy:** Nginx reverse proxy
- **Cost:** $0/month (Always Free tier)

#### Key Commands

```bash
# SSH to production server
ssh opc@<ORACLE_IP>

# Check service status
bash /opt/bridge-bidding-app/deploy/oracle/maintenance.sh status

# View logs
bash /opt/bridge-bidding-app/deploy/oracle/maintenance.sh logs

# Update to latest code (manual deploy)
bash /opt/bridge-bidding-app/deploy/oracle/maintenance.sh update

# Restart services
bash /opt/bridge-bidding-app/deploy/oracle/maintenance.sh restart

# Backup database
bash /opt/bridge-bidding-app/deploy/oracle/maintenance.sh backup
```

---

## Deployment Workflow

### Standard Workflow

```bash
# 1. Develop on development branch
git checkout development
# ... make changes, test locally ...
git add .
git commit -m "Descriptive commit message"
git push origin development

# 2. When ready for production, merge to main
git checkout main
git merge development
git push origin main

# 3. Deploy to Oracle (choose one method)

# Option A: Webhook auto-deploy (if configured)
# Push to main triggers automatic deployment

# Option B: Manual deploy via SSH
ssh opc@<ORACLE_IP> "bash /opt/bridge-bidding-app/deploy/oracle/maintenance.sh update"
```

### Verification

After deployment, verify:
- [ ] App loads at https://app.mybridgebuddy.com
- [ ] Bidding works (try a hand)
- [ ] Card play works
- [ ] Dashboard loads
- [ ] No console errors

---

## Rollback

### Method 1: Git Revert (Safest)
```bash
git checkout main
git revert HEAD
git push origin main
# Then deploy: maintenance.sh update
```

### Method 2: Deploy Previous Commit
```bash
ssh opc@<ORACLE_IP>
cd /opt/bridge-bidding-app
git log --oneline -5  # Find good commit
git checkout <commit-hash>
sudo systemctl restart bridge-backend
```

---

## Monitoring

### Service Status
```bash
# On production server
sudo systemctl status bridge-backend
sudo systemctl status nginx
sudo systemctl status postgresql
```

### Logs
```bash
# Backend logs
sudo journalctl -u bridge-backend -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Anti-Idle Protection

Oracle reclaims idle instances after 7 days. Protection is automatic:
```bash
# Check keep-alive status
bash /opt/bridge-bidding-app/deploy/oracle/keep-alive.sh status
```

---

## Troubleshooting

### App Not Loading
```bash
# Check if backend is running
sudo systemctl status bridge-backend

# Check if nginx is running
sudo systemctl status nginx

# Check backend logs for errors
sudo journalctl -u bridge-backend --no-pager -n 50
```

### Database Connection Errors
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test database connection
sudo -u postgres psql -c "SELECT 1;"
```

### 502 Bad Gateway
```bash
# Backend not running or crashed
sudo systemctl restart bridge-backend

# Check if port 5001 is listening
netstat -tlnp | grep 5001
```

---

## Support

- **Oracle Cloud Status:** https://status.oracle.com
- **Project Issues:** GitHub repository issues
- **Maintenance Docs:** [deploy/oracle/README.md](../../deploy/oracle/README.md)

---

## Deprecated

The previous Render deployment configuration has been archived to `deploy/archive/render.yaml.deprecated`.

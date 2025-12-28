# Oracle Cloud Always Free Deployment

This directory contains scripts to deploy the Bridge Bidding App to Oracle Cloud Always Free tier.

## Quick Start

### 1. Prerequisites (Your Computer)

Before connecting to Oracle Cloud, ensure you have:
- Oracle Cloud account created ([sign up here](https://www.oracle.com/cloud/free/))
- SSH key pair generated
- VM instance created in Oracle Cloud Console

### 2. Create VM Instance

In Oracle Cloud Console:

1. **Compute → Instances → Create Instance**
2. **Name:** `bridge-bidding-app`
3. **Image:** Oracle Linux 8 or Ubuntu 22.04
4. **Shape:** VM.Standard.A1.Flex (ARM)
   - OCPUs: 2
   - Memory: 12 GB
5. **Network:** Create or select VCN with public subnet
6. **SSH Key:** Paste your public key
7. **Boot Volume:** 100 GB

### 3. Configure Security List

Add ingress rules for ports:
- 22 (SSH)
- 80 (HTTP)
- 443 (HTTPS)

### 4. Deploy (Two Options)

#### Option A: Cloud-Init (Recommended - Fastest)

When creating your VM instance:
1. Expand "Advanced options" → "Management"
2. Paste the contents of `cloud-init.yaml` into "Cloud-init script"
3. Create the instance and wait for it to boot (~5 min)
4. SSH in and run the finalize script:

```bash
ssh -i ~/.ssh/your_key opc@<PUBLIC_IP>  # Oracle Linux
# OR
ssh -i ~/.ssh/your_key ubuntu@<PUBLIC_IP>  # Ubuntu

# Complete the setup
bash /opt/bridge-bidding-app/finalize-setup.sh "YourSecurePassword123!"
```

#### Option B: Manual Scripts

```bash
# Connect to VM
ssh -i ~/.ssh/your_key opc@<PUBLIC_IP>  # Oracle Linux
# OR
ssh -i ~/.ssh/your_key ubuntu@<PUBLIC_IP>  # Ubuntu

# Download and run all-in-one script
curl -sSL https://raw.githubusercontent.com/JFrunk/bridge-bidding-app/main/deploy/oracle/deploy-all.sh -o deploy-all.sh
bash deploy-all.sh "YourSecurePassword123!"
```

#### Option C: Step-by-Step Scripts

```bash
# Download scripts
git clone https://github.com/JFrunk/bridge-bidding-app.git /tmp/app
cp /tmp/app/deploy/oracle/*.sh ~/

# Run setup scripts in order
bash setup-server.sh
bash setup-database.sh "YourSecurePassword123!"
bash deploy-app.sh https://github.com/JFrunk/bridge-bidding-app.git main
bash configure-nginx.sh
bash maintenance.sh full-setup
```

### 5. Access Your App

- **HTTP:** `http://<PUBLIC_IP>`
- **HTTPS:** `https://yourdomain.com` (after SSL setup)

## Scripts Reference

| Script | Purpose | Usage |
|--------|---------|-------|
| `cloud-init.yaml` | Auto-setup during VM creation | Paste into Oracle Cloud Console |
| `deploy-all.sh` | One-command full deployment | `bash deploy-all.sh <password>` |
| `setup-server.sh` | Install system dependencies | `bash setup-server.sh` |
| `setup-database.sh` | Configure PostgreSQL | `bash setup-database.sh <password>` |
| `deploy-app.sh` | Clone and deploy application | `bash deploy-app.sh <repo_url> [branch]` |
| `configure-nginx.sh` | Setup Nginx reverse proxy | `bash configure-nginx.sh [domain]` |
| `setup-ssl.sh` | Install Let's Encrypt SSL | `bash setup-ssl.sh <domain> [email]` |
| `maintenance.sh` | Ongoing maintenance tasks | `bash maintenance.sh [command]` |
| `migrate-data.sh` | Migrate data from Render | `bash migrate-data.sh <render_db_url>` |

## Maintenance Commands

```bash
# Check status of all services
bash maintenance.sh status

# View recent logs
bash maintenance.sh logs

# Update to latest code
bash maintenance.sh update

# Backup database
bash maintenance.sh backup

# Restart all services
bash maintenance.sh restart
```

## Migrating from Render

To migrate existing data:

1. Get your Render database URL from Dashboard
2. Run: `bash migrate-data.sh '<render_database_url>'`
3. Verify app works with migrated data
4. Update DNS to point to Oracle Cloud
5. Decommission Render after confirming stability

## Oracle Always Free Limits

Your deployment uses these resources:

| Resource | Used | Available |
|----------|------|-----------|
| ARM OCPUs | 2 | 4 |
| Memory | 12 GB | 24 GB |
| Block Storage | 100 GB | 200 GB |
| Outbound Data | ~1-5 GB/mo | 10 TB/mo |

## Preventing Instance Reclamation

Oracle reclaims idle instances. The `maintenance.sh full-setup` command configures a cron job that keeps your instance active.

## Troubleshooting

### Cannot SSH to Instance
- Verify security list has port 22 open
- Check instance is running in Console
- Verify correct username (opc for Oracle Linux, ubuntu for Ubuntu)

### Backend Won't Start
```bash
sudo journalctl -u bridge-backend -f
```

### Nginx 502 Bad Gateway
```bash
# Check if backend is running
sudo systemctl status bridge-backend

# Check if port is listening
netstat -tlnp | grep 5001
```

### Database Connection Failed
```bash
# Test PostgreSQL
sudo -u postgres psql -c "SELECT 1;"

# Check pg_hba.conf authentication
sudo cat /var/lib/pgsql/data/pg_hba.conf | grep -v '^#' | grep -v '^$'
```

## Support

For issues, check:
1. Service logs: `bash maintenance.sh logs`
2. System resources: `bash maintenance.sh status`
3. Oracle Cloud status: [status.oracle.com](https://status.oracle.com)

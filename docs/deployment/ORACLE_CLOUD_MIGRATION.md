# Oracle Cloud Always Free Migration Plan

**Document Version:** 1.0
**Created:** 2025-12-27
**Status:** Planning Phase

---

## Executive Summary

This document outlines the complete migration plan from Render to Oracle Cloud Always Free tier. The migration maintains full functionality while eliminating hosting costs.

### Current vs Target Architecture

| Component | Current (Render) | Target (Oracle Always Free) |
|-----------|-----------------|----------------------------|
| **Backend** | Render Web Service | ARM VM (2 OCPU, 12GB RAM) |
| **Frontend** | Render Static Site | Same VM (Nginx) |
| **Database** | Render PostgreSQL | Oracle Autonomous DB or PostgreSQL on VM |
| **Cost** | ~$7-25/month | $0/month (Always Free) |
| **DDS Support** | ✅ Linux production | ✅ Linux ARM64 |

---

## Phase 1: User Prerequisites

### What You Need To Do

#### 1. Create Oracle Cloud Account (15 minutes)

1. Go to [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/)
2. Click **"Start for free"**
3. Provide:
   - Valid email address
   - Credit/debit card (for identity verification only - **you will NOT be charged**)
   - Phone number for verification

4. **CRITICAL: Choose Home Region Carefully**
   - Select a region close to your users
   - **Recommended regions** (good availability):
     - US East (Ashburn)
     - US West (Phoenix)
     - UK South (London)
     - Germany Central (Frankfurt)
   - Always Free resources can ONLY be created in your home region
   - This choice is **permanent** and cannot be changed

5. Complete email and phone verification
6. Wait for account provisioning (5-10 minutes)

#### 2. Generate API Keys (5 minutes)

After account creation:

1. Click your profile icon (top right) → **User Settings**
2. Under **Resources** → Click **API Keys**
3. Click **Add API Key** → **Generate API Key Pair**
4. Download the **private key** (save as `~/.oci/oci_api_key.pem`)
5. Copy the **Configuration File Preview** content
6. Create `~/.oci/config` with the copied content

Your `~/.oci/config` should look like:
```ini
[DEFAULT]
user=ocid1.user.oc1..aaaaaaaaxxxxxxxxx
fingerprint=xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx
tenancy=ocid1.tenancy.oc1..aaaaaaaaxxxxxxxxx
region=us-ashburn-1
key_file=~/.oci/oci_api_key.pem
```

#### 3. Collect Required OCIDs (5 minutes)

You'll need these identifiers. Find them in the Oracle Cloud Console:

| Value | Where to Find |
|-------|---------------|
| **Tenancy OCID** | Profile icon → Tenancy → Copy OCID |
| **User OCID** | Profile icon → User Settings → Copy OCID |
| **Compartment OCID** | Identity → Compartments → root compartment OCID |
| **Region** | Top bar shows current region (e.g., `us-ashburn-1`) |

#### 4. Install OCI CLI (Optional but Recommended)

```bash
# macOS/Linux
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"

# Verify installation
oci --version

# Test authentication
oci iam region list --output table
```

---

## Phase 2: Infrastructure Setup

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Oracle Cloud Always Free                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   Virtual Cloud Network                   │   │
│  │                    (10.0.0.0/16)                         │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │              Public Subnet (10.0.0.0/24)           │  │   │
│  │  │                                                    │  │   │
│  │  │  ┌─────────────────────────────────────────────┐  │  │   │
│  │  │  │     ARM VM (VM.Standard.A1.Flex)            │  │  │   │
│  │  │  │     2 OCPU, 12GB RAM, 100GB Storage         │  │  │   │
│  │  │  │                                             │  │  │   │
│  │  │  │  ┌─────────┐  ┌─────────┐  ┌────────────┐  │  │  │   │
│  │  │  │  │  Nginx  │  │  Flask  │  │ PostgreSQL │  │  │  │   │
│  │  │  │  │  :80    │  │  :5001  │  │   :5432    │  │  │  │   │
│  │  │  │  │  :443   │  │         │  │            │  │  │  │   │
│  │  │  │  └────┬────┘  └────┬────┘  └─────┬──────┘  │  │  │   │
│  │  │  │       │            │             │         │  │  │   │
│  │  │  │       └────────────┴─────────────┘         │  │  │   │
│  │  │  │              Gunicorn (systemd)            │  │  │   │
│  │  │  └─────────────────────────────────────────────┘  │  │   │
│  │  │                        │                          │  │   │
│  │  │                   Public IP                       │  │   │
│  │  └────────────────────────┼───────────────────────────┘  │   │
│  │                           │                              │   │
│  └───────────────────────────┼──────────────────────────────┘   │
│                              │                                   │
│                    ┌─────────┴─────────┐                        │
│                    │   Internet Gateway │                        │
│                    └───────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
                               │
                          HTTPS/443
                               │
                    ┌──────────┴──────────┐
                    │    Your Domain      │
                    │ (Optional: Cloudflare│
                    │    for SSL/CDN)     │
                    └─────────────────────┘
```

### Resource Allocation Strategy

**Option A: Single Powerful ARM VM (Recommended)**
- 2 OCPU, 12GB RAM, 100GB storage
- Runs: Nginx + Flask + PostgreSQL
- Leaves: 2 OCPU, 12GB RAM for future expansion or redundancy

**Option B: Separate VMs**
- VM1: 2 OCPU, 8GB RAM - Application (Nginx + Flask)
- VM2: 2 OCPU, 8GB RAM - Database (PostgreSQL)
- More complex but better isolation

**Why ARM?**
- 4x more resources than AMD micro instances
- ARM64 Linux fully supports DDS (Double Dummy Solver)
- Better performance per resource unit

---

## Phase 3: Manual Deployment Steps

### Step 1: Create Virtual Cloud Network (VCN)

1. Navigate to **Networking → Virtual Cloud Networks**
2. Click **Start VCN Wizard** → **Create VCN with Internet Connectivity**
3. Configure:
   - **Name:** `bridge-app-vcn`
   - **Compartment:** (your root compartment)
   - **VCN CIDR Block:** `10.0.0.0/16`
   - **Public Subnet CIDR:** `10.0.0.0/24`
   - **Private Subnet CIDR:** `10.0.1.0/24`
4. Click **Next** → **Create**

### Step 2: Configure Security List

1. Go to your VCN → **Security Lists** → **Default Security List**
2. Add **Ingress Rules**:

| Source CIDR | Protocol | Dest Port | Description |
|-------------|----------|-----------|-------------|
| 0.0.0.0/0 | TCP | 22 | SSH |
| 0.0.0.0/0 | TCP | 80 | HTTP |
| 0.0.0.0/0 | TCP | 443 | HTTPS |
| 0.0.0.0/0 | TCP | 5001 | Flask API (temporary) |

### Step 3: Create Compute Instance

1. Navigate to **Compute → Instances** → **Create Instance**
2. Configure:

**Basics:**
- **Name:** `bridge-bidding-app`
- **Compartment:** (your root compartment)
- **Availability Domain:** AD-1 (or any available)

**Image and Shape:**
- Click **Edit** in Image and shape section
- **Image:** Oracle Linux 8 (or Ubuntu 22.04)
- **Shape:** Click **Change Shape**
  - **Shape series:** Ampere (ARM)
  - **Shape name:** VM.Standard.A1.Flex
  - **OCPU count:** 2
  - **Memory (GB):** 12

**Networking:**
- **Virtual cloud network:** bridge-app-vcn
- **Subnet:** Public Subnet
- **Public IPv4 address:** Assign a public IPv4 address

**Add SSH Keys:**
- **SSH key:** Paste your public SSH key or generate new
- Save the private key securely!

**Boot Volume:**
- **Size:** 100 GB (within 200GB Always Free limit)
- **Encryption:** Oracle-managed key (free)

3. Click **Create**
4. Wait for instance to be **Running** (2-5 minutes)
5. Note the **Public IP Address**

### Step 4: Connect and Setup Server

```bash
# Connect to your instance
ssh -i /path/to/private_key opc@<PUBLIC_IP>

# For Ubuntu, use 'ubuntu' user instead of 'opc'
ssh -i /path/to/private_key ubuntu@<PUBLIC_IP>
```

### Step 5: Install System Dependencies

```bash
# Update system
sudo dnf update -y  # Oracle Linux
# OR
sudo apt update && sudo apt upgrade -y  # Ubuntu

# Install Python 3.11
sudo dnf install python3.11 python3.11-pip python3.11-devel -y  # Oracle Linux
# OR
sudo apt install python3.11 python3.11-venv python3.11-dev -y  # Ubuntu

# Install Node.js 20 LTS
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo dnf install nodejs -y  # Oracle Linux
# OR
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs -y  # Ubuntu

# Install Nginx
sudo dnf install nginx -y  # Oracle Linux
# OR
sudo apt install nginx -y  # Ubuntu

# Install PostgreSQL
sudo dnf install postgresql-server postgresql-contrib -y  # Oracle Linux
# OR
sudo apt install postgresql postgresql-contrib -y  # Ubuntu

# Install Git
sudo dnf install git -y  # Oracle Linux
# OR
sudo apt install git -y  # Ubuntu

# Install build tools (for DDS compilation)
sudo dnf groupinstall "Development Tools" -y  # Oracle Linux
# OR
sudo apt install build-essential -y  # Ubuntu
```

### Step 6: Setup PostgreSQL

```bash
# Initialize database (Oracle Linux only)
sudo postgresql-setup --initdb

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE USER bridge_user WITH PASSWORD 'your_secure_password_here';
CREATE DATABASE bridge_bidding OWNER bridge_user;
GRANT ALL PRIVILEGES ON DATABASE bridge_bidding TO bridge_user;
\q
EOF

# Configure PostgreSQL authentication
# Edit pg_hba.conf to allow password auth
sudo nano /var/lib/pgsql/data/pg_hba.conf  # Oracle Linux
# OR
sudo nano /etc/postgresql/14/main/pg_hba.conf  # Ubuntu

# Change 'ident' to 'md5' for local connections:
# local   all   all   md5
# host    all   all   127.0.0.1/32   md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Step 7: Deploy Application

```bash
# Create app directory
sudo mkdir -p /opt/bridge-bidding-app
sudo chown $USER:$USER /opt/bridge-bidding-app

# Clone repository
cd /opt/bridge-bidding-app
git clone https://github.com/YOUR_USERNAME/bridge_bidding_app.git .

# Setup Python virtual environment
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create environment file
cat > .env << EOF
FLASK_ENV=production
DATABASE_URL=postgresql://bridge_user:your_secure_password_here@localhost:5432/bridge_bidding
DEFAULT_AI_DIFFICULTY=expert
EOF

# Initialize database
python3 database/init_all_tables.py

# Build frontend
cd ../frontend
npm install
npm run build
```

### Step 8: Configure Gunicorn Service

```bash
# Create systemd service file
sudo tee /etc/systemd/system/bridge-backend.service << EOF
[Unit]
Description=Bridge Bidding App Backend
After=network.target postgresql.service

[Service]
User=$USER
Group=$USER
WorkingDirectory=/opt/bridge-bidding-app/backend
Environment="PATH=/opt/bridge-bidding-app/backend/venv/bin"
EnvironmentFile=/opt/bridge-bidding-app/backend/.env
ExecStart=/opt/bridge-bidding-app/backend/venv/bin/gunicorn \
    --bind 127.0.0.1:5001 \
    --workers 2 \
    --timeout 120 \
    --access-logfile /var/log/bridge-backend/access.log \
    --error-logfile /var/log/bridge-backend/error.log \
    server:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Create log directory
sudo mkdir -p /var/log/bridge-backend
sudo chown $USER:$USER /var/log/bridge-backend

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable bridge-backend
sudo systemctl start bridge-backend

# Check status
sudo systemctl status bridge-backend
```

### Step 9: Configure Nginx

```bash
# Create Nginx configuration
sudo tee /etc/nginx/conf.d/bridge-bidding.conf << 'EOF'
server {
    listen 80;
    server_name _;  # Replace with your domain if you have one

    # Frontend (React build)
    location / {
        root /opt/bridge-bidding-app/frontend/build;
        try_files $uri $uri/ /index.html;

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 120s;
    }
}
EOF

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default 2>/dev/null
sudo rm -f /etc/nginx/conf.d/default.conf 2>/dev/null

# Test and reload Nginx
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx
```

### Step 10: Configure Firewall (Oracle Linux)

```bash
# Oracle Linux uses firewalld
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-port=22/tcp
sudo firewall-cmd --reload

# Ubuntu uses iptables (already open via Security List)
# Just ensure UFW isn't blocking:
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### Step 11: Verify Deployment

```bash
# Check all services
sudo systemctl status postgresql
sudo systemctl status bridge-backend
sudo systemctl status nginx

# Test API locally
curl http://localhost:5001/api/scenarios

# Test via public IP
curl http://<PUBLIC_IP>/api/scenarios
```

Access your app at: `http://<PUBLIC_IP>`

---

## Phase 4: SSL/HTTPS Setup

### Option A: Using Cloudflare (Recommended - Free)

1. Add your domain to Cloudflare (free account)
2. Point your domain's DNS to the Oracle VM public IP
3. Enable **Flexible SSL** in Cloudflare (free)
4. Cloudflare handles HTTPS termination

**Advantages:**
- Free SSL certificate (auto-renewed)
- DDoS protection
- CDN caching
- No server configuration needed

### Option B: Let's Encrypt with Certbot

```bash
# Install Certbot
sudo dnf install certbot python3-certbot-nginx -y  # Oracle Linux
# OR
sudo apt install certbot python3-certbot-nginx -y  # Ubuntu

# Obtain certificate (replace YOUR_DOMAIN)
sudo certbot --nginx -d YOUR_DOMAIN.com -d www.YOUR_DOMAIN.com

# Auto-renewal is configured automatically
sudo systemctl enable certbot-renew.timer
```

---

## Phase 5: Interim Period Strategy

### Running Both Render and Oracle in Parallel

During migration, run both deployments simultaneously:

```
┌─────────────────────────────────────────────────────────────────┐
│                     INTERIM PERIOD                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────┐     ┌─────────────────────┐            │
│  │       RENDER        │     │   ORACLE CLOUD      │            │
│  │   (Current Prod)    │     │   (New Prod)        │            │
│  │                     │     │                     │            │
│  │  bridge-bidding-    │     │  <public-ip>        │            │
│  │  app.onrender.com   │     │  or your-domain.com │            │
│  │                     │     │                     │            │
│  │  ✅ Active users    │     │  ✅ Testing         │            │
│  │  ✅ Production DB   │     │  ✅ Parallel DB     │            │
│  └─────────────────────┘     └─────────────────────┘            │
│                                                                  │
│  Timeline:                                                       │
│  Week 1: Deploy Oracle, test functionality                      │
│  Week 2: User acceptance testing on Oracle                      │
│  Week 3: Migrate data, switch DNS                               │
│  Week 4: Monitor Oracle, keep Render as backup                  │
│  Week 5+: Decommission Render                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Migration Strategy

```bash
# Export from Render PostgreSQL
pg_dump $RENDER_DATABASE_URL > bridge_backup.sql

# Import to Oracle PostgreSQL
psql -U bridge_user -d bridge_bidding -f bridge_backup.sql
```

### DNS Cutover Strategy

1. **Reduce TTL** (1 week before): Set DNS TTL to 300 seconds
2. **Test thoroughly** on Oracle Cloud
3. **Update DNS** to point to Oracle Cloud IP
4. **Monitor** both deployments for 48 hours
5. **Decommission** Render after successful cutover

---

## Phase 6: Monitoring & Maintenance

### Prevent Idle Instance Reclamation

Oracle reclaims instances idle for 7+ days. Prevent this:

```bash
# Create a simple cron job to generate activity
crontab -e

# Add this line (runs health check every 6 hours)
0 */6 * * * curl -s http://localhost/api/scenarios > /dev/null 2>&1
```

### Log Rotation

```bash
# Create logrotate configuration
sudo tee /etc/logrotate.d/bridge-backend << EOF
/var/log/bridge-backend/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 $USER $USER
}
EOF
```

### Backup Strategy

```bash
# Create backup script
cat > /opt/bridge-bidding-app/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/bridge-bidding-app/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -U bridge_user bridge_bidding > "$BACKUP_DIR/db_$DATE.sql"

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
EOF

chmod +x /opt/bridge-bidding-app/backup.sh

# Add to crontab (daily at 3 AM)
echo "0 3 * * * /opt/bridge-bidding-app/backup.sh" | crontab -
```

### Deployment Updates

```bash
# Create update script
cat > /opt/bridge-bidding-app/deploy.sh << 'EOF'
#!/bin/bash
cd /opt/bridge-bidding-app

# Pull latest code
git pull origin main

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
python3 database/init_all_tables.py

# Update frontend
cd ../frontend
npm install
npm run build

# Restart services
sudo systemctl restart bridge-backend
sudo systemctl reload nginx

echo "Deployment complete!"
EOF

chmod +x /opt/bridge-bidding-app/deploy.sh
```

---

## Troubleshooting

### Common Issues

#### 1. Cannot SSH to Instance
```bash
# Check security list has port 22 open
# Check instance is running
# Verify correct private key and username (opc for Oracle Linux, ubuntu for Ubuntu)
```

#### 2. Backend Service Won't Start
```bash
# Check logs
sudo journalctl -u bridge-backend -f

# Common fixes:
# - Check DATABASE_URL is correct
# - Verify PostgreSQL is running
# - Check Python dependencies are installed
```

#### 3. Nginx 502 Bad Gateway
```bash
# Backend not running
sudo systemctl status bridge-backend

# Check backend is listening
netstat -tlnp | grep 5001
```

#### 4. DDS Not Working
```bash
# Install endplay dependencies
pip install endplay

# Test DDS
python3 -c "from endplay import dds; print('DDS OK')"
```

#### 5. Instance Reclaimed
```bash
# Create new instance following Phase 3
# Restore from backup
# Implement anti-idle cron job (Phase 6)
```

---

## Cost Comparison

| Item | Render | Oracle Always Free |
|------|--------|-------------------|
| Backend (Web Service) | ~$7/month | $0 |
| Frontend (Static) | Free | $0 |
| Database | ~$7/month (free tier expired) | $0 |
| Bandwidth (10TB) | Included | Included |
| SSL/HTTPS | Included | Free (Cloudflare or Let's Encrypt) |
| **Monthly Total** | **~$14-25/month** | **$0/month** |
| **Annual Savings** | - | **$168-300/year** |

---

## Checklist Summary

### User Action Items

- [ ] Create Oracle Cloud account
- [ ] Verify home region selection
- [ ] Generate API keys
- [ ] Collect OCIDs
- [ ] Provide domain name (optional, for SSL)
- [ ] Provide GitHub repository URL (if private, provide deploy key)

### Deployment Checklist

- [ ] VCN created with Internet Gateway
- [ ] Security list configured (22, 80, 443)
- [ ] ARM VM created (2 OCPU, 12GB RAM)
- [ ] System dependencies installed
- [ ] PostgreSQL configured
- [ ] Application deployed
- [ ] Gunicorn service running
- [ ] Nginx configured
- [ ] SSL/HTTPS enabled
- [ ] Anti-idle cron job configured
- [ ] Backups configured
- [ ] DNS cutover complete
- [ ] Render decommissioned

---

## Your Configuration

Based on your input:
- **Oracle Cloud Account:** ✅ Ready
- **GitHub Repository:** https://github.com/JFrunk/bridge-bidding-app.git (public)
- **Custom Domain:** None (will use IP address)
- **Data Migration:** Not needed (fresh install)

---

## Quick Deploy (One Command)

After creating your VM instance, SSH in and run:

```bash
# Download and run the all-in-one deployment script
curl -sSL https://raw.githubusercontent.com/JFrunk/bridge-bidding-app/main/deploy/oracle/deploy-all.sh -o deploy-all.sh
bash deploy-all.sh "YourSecurePassword123!"
```

This single command will:
1. Install all system dependencies
2. Configure PostgreSQL
3. Deploy the application
4. Configure Nginx
5. Set up maintenance tasks

Your app will be live at `http://<YOUR_VM_PUBLIC_IP>`

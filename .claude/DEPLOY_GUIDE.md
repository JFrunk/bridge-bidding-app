# Deploy, Git Workflow & Database Guide

**Referenced from:** `CLAUDE.md` — Git Workflow section

---

## Branch Strategy

This project uses a **two-branch workflow**:
- **`development`** — Active development branch (default for commits)
- **`main`** — Production branch (deploy via Hetzner Cloud)

---

## Standard Workflow (Development Branch)

```bash
# Ensure you're on development branch
git checkout development

# Make changes, test locally, then commit
git add .
git commit -m "Descriptive commit message"

# Push to GitHub
git push origin development
```

---

## Creating Pull Requests via GitHub API

**When gh CLI is not available, use the GitHub API directly with git credentials:**

**Step 1: Extract GitHub credentials from keychain**
```bash
echo "protocol=https
host=github.com" | git credential-osxkeychain get
```

**Step 2: Create PR using curl**
```bash
cat > /tmp/pr_data.json << 'EOF'
{
  "title": "Your PR title",
  "body": "Your PR description\n\nWith multiple lines...",
  "head": "your-feature-branch",
  "base": "development"
}
EOF

curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/JFrunk/bridge-bidding-app/pulls \
  -d @/tmp/pr_data.json
```

**Step 3: Merge PR using API**
```bash
curl -X PUT \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/JFrunk/bridge-bidding-app/pulls/{PR_NUMBER}/merge \
  -d '{"commit_title": "Your commit message", "merge_method": "squash"}'
```

**Note:** Replace `YOUR_GITHUB_TOKEN` with the token from Step 1 (starts with `ghp_`).

---

## Deploying to Production

**Production Infrastructure:**
| Component | Host | URL |
|-----------|------|-----|
| Landing page | GitHub Pages | https://mybridgebuddy.com |
| Bridge app | Hetzner Cloud (178.156.132.108) | https://app.mybridgebuddy.com |

**Hetzner Cloud Server:**
- **IP Address:** 178.156.132.108
- **SSH Host Alias:** hetzner-bridge (configured in ~/.ssh/config)

### Database Migrations

**CRITICAL: Schema changes must be applied to BOTH production AND local databases.**

Any schema change (new table, new column, new index) must be run on:
1. **Local PostgreSQL** (`bridge_app` database via Postgres.app) — for localhost testing
2. **Production PostgreSQL** (`bridge_bidding` database on Hetzner) — for deployed app

Forgetting either side causes runtime errors.

**Local Database:**
- **App:** Postgres.app (v18)
- **Database:** `bridge_app`
- **psql path:** `/Applications/Postgres.app/Contents/Versions/18/bin/psql`
- **Apply migrations:**
```bash
/Applications/Postgres.app/Contents/Versions/18/bin/psql -d bridge_app -f backend/migrations/<migration_file>.sql
```

**Production Database:**
```bash
ssh hetzner-bridge
cd /opt/bridge-bidding-app/backend
source venv/bin/activate
python3 database/init_all_tables.py

# Verify tables exist
sudo -u postgres psql -d bridge_bidding -c "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;"
```

**Expected tables:** users, user_gamification, bidding_decisions, hand_analyses, game_sessions, session_hands, conventions, error_categories

### Code Deployment

```bash
# Switch to main branch
git checkout main

# Merge development changes
git merge development

# Push to GitHub
git push origin main

# Deploy to production via SSH
ssh hetzner-bridge "bash /opt/bridge-bidding-app/update.sh"

# Switch back to development for continued work
git checkout development
```

**One-liner for quick deploy (after pushing to main):**
```bash
ssh hetzner-bridge "bash /opt/bridge-bidding-app/update.sh"
```

### Verification Checklist

- [ ] Dashboard loads without errors
- [ ] Database tables exist
- [ ] Users can login and play
- [ ] Bidding feedback works
- [ ] Dashboard shows statistics

---

## Rollback Procedure

If deployment fails:
```bash
# Revert main branch
git checkout main
git reset --hard HEAD~1
git push origin main --force

# Or restore from previous commit
git revert HEAD
git push origin main
```

---

## User Feedback (Production)

**Use `/fetch-feedback` to retrieve, categorize, and analyze user feedback from production.**

**IMPORTANT:** Feedback is on the PRODUCTION server, not local. Local `backend/user_feedback/` is dev-only.

**Production location:** `/opt/bridge-bidding-app/backend/user_feedback/` on `hetzner-bridge`

**Email Notifications:** See `backend/engine/notifications/email_service.py`

---

## Quick Reference

```bash
# Check branch
git branch

# Switch branches
git checkout development  # For dev work
git checkout main        # For deployment

# View recent commits
git log --oneline -5

# Deploy (after pushing to main)
ssh hetzner-bridge "bash /opt/bridge-bidding-app/update.sh"
```

### Key Rules

- **Always commit to `development`** unless deploying
- **Only push to `main`** when ready for production
- **Deploy app via SSH:** `ssh hetzner-bridge "bash /opt/bridge-bidding-app/update.sh"`
- Keep `development` as your default working branch

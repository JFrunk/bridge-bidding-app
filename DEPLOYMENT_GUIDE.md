# Deployment Guide

## Overview
This guide covers deploying the Bridge Bidding Application from the feature branch to production.

## Pre-Deployment Checklist

### 1. Code Quality
```bash
# Backend tests
cd backend
source venv/bin/activate
pytest tests/ -v

# Frontend build
cd ../frontend
npm run build

# Check for build errors
```

### 2. Branch Status
```bash
# Verify you're on the feature branch
git branch --show-current
# Should show: refactor/shadcn-tailwind-migration

# Check for uncommitted changes
git status

# View commit history
git log --oneline -10
```

### 3. Environment Variables

**Backend (.env):**
```bash
FLASK_ENV=production
FLASK_DEBUG=0
DATABASE_URL=your_production_db
ANTHROPIC_API_KEY=your_key
```

**Frontend (.env.production):**
```bash
REACT_APP_API_URL=https://your-backend-url.com
```

## Deployment Methods

### Method 1: Pull Request (Recommended for Team)

**Step 1: Push feature branch to remote**
```bash
git push origin refactor/shadcn-tailwind-migration
```

**Step 2: Create Pull Request**
```bash
# Using GitHub CLI
gh pr create \
  --base main \
  --head refactor/shadcn-tailwind-migration \
  --title "UI/UX Improvements: Shadcn Migration + Gameplay Enhancements" \
  --body-file .github/pr-template.md

# Or via GitHub web UI:
# https://github.com/YOUR_ORG/bridge_bidding_app/compare/main...refactor/shadcn-tailwind-migration
```

**Step 3: Review & Merge**
- Have team review the PR
- Run automated tests (if configured)
- Merge when approved

### Method 2: Direct Merge (Solo Developer)

```bash
# Ensure feature branch is clean
git status

# Switch to main
git checkout main

# Pull latest changes
git pull origin main

# Merge feature branch
git merge refactor/shadcn-tailwind-migration

# Resolve any conflicts
# Test thoroughly

# Push to production
git push origin main
```

### Method 3: Release Branch (Best Practice)

```bash
# Create release branch
git checkout -b release/v2.0.0 refactor/shadcn-tailwind-migration

# Final testing and fixes only
# Update version numbers

# Merge to main
git checkout main
git merge release/v2.0.0

# Tag the release
git tag -a v2.0.0 -m "Release v2.0: UI/UX Overhaul"
git push origin main --tags

# Also merge back to development
git checkout development
git merge release/v2.0.0
git push origin development
```

## Post-Deployment

### 1. Verify Deployment

**Frontend:**
```bash
# Check build deployed correctly
curl https://your-app.com

# Test in browser
# - Cards overlap correctly
# - Scoring displays
# - Learning Dashboard loads
# - No console errors
```

**Backend:**
```bash
# Check API health
curl https://your-api.com/health

# Test deal endpoint
curl https://your-api.com/api/deal-hands
```

### 2. Monitoring

**Watch for errors:**
```bash
# Backend logs
tail -f /var/log/bridge-app/error.log

# Frontend errors (use Sentry, LogRocket, etc.)
# Check browser console in production
```

### 3. Database Migrations

```bash
# If any schema changes were made
cd backend
source venv/bin/activate
flask db upgrade

# Backup before migration!
pg_dump bridge_db > backup_$(date +%Y%m%d).sql
```

## Rollback Plan

### If Something Goes Wrong

**Quick Rollback:**
```bash
# Revert to previous commit
git revert HEAD
git push origin main

# Or reset to previous tag
git checkout v1.9.0
git push origin main --force  # Use with caution!
```

**Frontend Only:**
```bash
# Deploy previous build
cd frontend/build-backup
# Upload to hosting service
```

**Backend Only:**
```bash
# Restore database
psql bridge_db < backup_20251013.sql

# Deploy previous version
git checkout main@{1}
# Redeploy
```

## Branch Management Strategy

### Recommended Workflow

```
main (production)
  ├── development (integration)
  │   ├── feature/feature-name
  │   ├── bugfix/bug-name
  │   └── refactor/refactor-name
  └── hotfix/critical-fix (emergency only)
```

### Branch Naming Convention

- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `refactor/*` - Code improvements
- `hotfix/*` - Production emergency fixes
- `release/*` - Release preparation

### Commit Message Convention

```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring
- `style`: Formatting changes
- `docs`: Documentation
- `test`: Adding tests
- `chore`: Maintenance

**Examples:**
```bash
feat(play): add card overlap for better UX

Implemented 35% visible overlap for cards in both bidding
and play phases. Responsive across all screen sizes.

Closes #123
```

## Continuous Integration (Future)

### Recommended Setup

**.github/workflows/ci.yml:**
```yaml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Backend Tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest tests/
      - name: Frontend Tests
        run: |
          cd frontend
          npm install
          npm test
          npm run build
```

## Security Checklist

- [ ] API keys not in code (use env variables)
- [ ] CORS configured correctly
- [ ] Rate limiting enabled
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] HTTPS enforced
- [ ] Database backups automated

## Performance Optimization

### Frontend
```bash
# Analyze bundle size
cd frontend
npm run build
npx source-map-explorer build/static/js/*.js

# Lighthouse audit
lighthouse https://your-app.com --view
```

### Backend
```bash
# Profile slow endpoints
python -m cProfile server.py

# Database query optimization
EXPLAIN ANALYZE SELECT ...
```

## Support

### If Deployment Fails

1. Check logs for errors
2. Verify environment variables
3. Test locally first
4. Roll back if necessary
5. Document the issue
6. Fix and redeploy

### Getting Help

- GitHub Issues: [Your repo]/issues
- Documentation: /docs
- Team Chat: Your Slack/Discord

## Success Criteria

Deployment is successful when:

✅ All automated tests pass
✅ Application loads without errors
✅ All new features work as expected
✅ No regression in existing features
✅ Performance metrics acceptable
✅ No console errors
✅ Mobile responsive
✅ Accessibility maintained
✅ Monitoring shows healthy metrics

---

**Last Updated:** 2025-10-13
**Version:** 2.0.0
**Author:** Development Team

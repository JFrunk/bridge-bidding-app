# Deployment Guide - Bridge Bidding Training App

## Table of Contents
1. [Render Deployment (Recommended)](#render-deployment)
2. [Update Workflow](#update-workflow)
3. [Rollback Strategy](#rollback-strategy)
4. [Password Protection](#password-protection)
5. [Monitoring & Troubleshooting](#monitoring--troubleshooting)

---

## Render Deployment

### Prerequisites
- GitHub account
- This code pushed to a GitHub repository
- Render account (free, no credit card required)

### One-Time Setup (15 minutes)

#### Step 1: Push to GitHub
```bash
# If not already done:
cd bridge_bidding_app
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/bridge-bidding-app.git
git push -u origin main
```

#### Step 2: Sign Up for Render
1. Go to https://render.com
2. Click "Get Started for Free"
3. Sign up with GitHub (easiest option)
4. Authorize Render to access your repositories

#### Step 3: Deploy Backend (Flask API)
1. **In Render Dashboard:**
   - Click "New +" → "Web Service"
   - Connect your `bridge-bidding-app` repository
   - Configure:
     - **Name:** `bridge-bidding-api`
     - **Region:** Choose closest to your users
     - **Branch:** `main`
     - **Root Directory:** `backend`
     - **Runtime:** Python 3
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `gunicorn --bind 0.0.0.0:$PORT server:app`
     - **Plan:** Free

2. **Environment Variables:**
   - Click "Environment" tab
   - Add: `FLASK_ENV=production`
   - Add: `PYTHON_VERSION=3.11`

3. **Click "Create Web Service"**
   - Wait 2-3 minutes for initial deploy
   - Note the URL: `https://bridge-bidding-api.onrender.com`

#### Step 4: Deploy Frontend (React)
1. **In Render Dashboard:**
   - Click "New +" → "Static Site"
   - Connect your `bridge-bidding-app` repository
   - Configure:
     - **Name:** `bridge-bidding-app`
     - **Branch:** `main`
     - **Root Directory:** `frontend`
     - **Build Command:** `npm install && npm run build`
     - **Publish Directory:** `build`

2. **Environment Variables:**
   - Click "Environment" tab
   - Add: `REACT_APP_API_URL=https://bridge-bidding-api.onrender.com`
   - (Replace with your actual backend URL from Step 3)

3. **Click "Create Static Site"**
   - Wait 2-3 minutes for build
   - Note the URL: `https://bridge-bidding-app.onrender.com`

#### Step 5: Update Frontend API URL
Since frontend needs to know backend URL:
1. **Option A: Environment Variable (already done in Step 4)**
2. **Option B: Update code directly (if env vars don't work)**

In `frontend/src/App.js`, change:
```javascript
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';
```

Then commit and push:
```bash
git add frontend/src/App.js
git commit -m "Configure production API URL"
git push origin main
```

#### Step 6: Test Your Deployment
1. Visit your frontend URL: `https://bridge-bidding-app.onrender.com`
2. Test a few features:
   - Load a hand
   - Make a bid
   - Check AI response
3. Open browser console (F12) to check for errors

---

## Update Workflow

### Development Branch Workflow (Recommended)

**To commit changes WITHOUT triggering Render deployment:**

Use the `development` branch for all development work. Only merge to `main` when ready to deploy.

```bash
# 1. Make changes locally
# ... edit files ...

# 2. Test locally
cd backend && python server.py  # Test backend
cd frontend && npm start         # Test frontend

# 3. Ensure you're on development branch
git checkout development

# 4. Commit changes
git add .
git commit -m "Descriptive commit message"

# 5. Push to GitHub (does NOT trigger Render deployment)
git push origin development

# 6. When ready to deploy to production
git checkout main
git merge development
git push origin main           # NOW Render deploys
```

**Benefits of this workflow:**
- Changes backed up to GitHub without deploying
- Can accumulate multiple commits before deploying
- Easy to test staging features
- Production (main) stays stable

### Direct to Main Workflow (Immediate Deployment)

**For immediate production deployment:**

```bash
# 1. Make changes locally
# ... edit files ...

# 2. Test locally
cd backend && python server.py  # Test backend
cd frontend && npm start         # Test frontend

# 3. Commit changes
git add .
git commit -m "Descriptive commit message"

# 4. Push to GitHub (triggers Render deployment)
git push origin main

# 5. Watch auto-deploy
# Go to Render dashboard to monitor build
# Backend: ~2 minutes
# Frontend: ~3 minutes
```

**That's it!** Render automatically:
- Detects your push to main
- Pulls latest code
- Runs tests (if configured)
- Builds new version
- Deploys with zero downtime

### Example: Adding a New Convention

```bash
# 1. Create new convention
cd backend/engine/ai/conventions
touch michaels_cuebid.py
# ... implement convention ...

# 2. Add tests
cd backend/tests
touch test_michaels_cuebid.py
# ... write tests ...

# 3. Test locally
pytest tests/test_michaels_cuebid.py
python server.py  # Manual testing

# 4. Commit and push
git add backend/engine/ai/conventions/michaels_cuebid.py
git add backend/tests/test_michaels_cuebid.py
git commit -m "Add Michaels Cuebid convention

- Implemented 2-level cuebid showing 5-5 in majors
- Added hand generator for scenarios
- All tests passing (5/5)
"
git push origin main

# 5. Monitor deployment
# Render dashboard shows:
# ✅ Build started
# ✅ Installing dependencies
# ✅ Running build command
# ✅ Deployment live

# 6. Verify live
# Visit https://bridge-bidding-app.onrender.com
# Test new convention
```

### Advanced: Preview Environments

Create a staging environment for testing before production:

```bash
# 1. Create staging branch
git checkout -b staging
git push origin staging

# 2. In Render, create new services:
# - New Web Service for backend (point to "staging" branch)
# - New Static Site for frontend (point to "staging" branch)
# URLs: https://bridge-bidding-api-staging.onrender.com
#       https://bridge-bidding-app-staging.onrender.com

# 3. Test on staging first
git checkout staging
# ... make changes ...
git push origin staging
# Test on staging URL

# 4. When ready, merge to main
git checkout main
git merge staging
git push origin main
# Deploys to production
```

---

## Rollback Strategy

### If you deploy a broken update:

#### Method 1: Render Dashboard (Fastest)
1. Go to Render dashboard
2. Click on your service (backend or frontend)
3. Click "Deploys" tab
4. Find the last working deploy (green checkmark)
5. Click "..." menu → "Redeploy"
6. Wait ~1 minute
7. ✅ Back to working version

#### Method 2: Git Revert
```bash
# Revert the bad commit
git revert HEAD
git push origin main

# Render auto-deploys the revert
# Wait 2-3 minutes
```

#### Method 3: Git Reset (if recent)
```bash
# Reset to previous commit
git reset --hard HEAD~1
git push origin main --force

# ⚠️ Use with caution - rewrites history
```

---

## Password Protection

### Option 1: Render HTTP Basic Auth (Easiest)
In Render dashboard:
1. Go to your frontend service
2. Click "Settings" tab
3. Scroll to "HTTP Basic Auth"
4. Enable and set username/password
5. Share credentials with your users

Users will see a browser login prompt before accessing the site.

### Option 2: Custom Login Page (More Flexible)
Implement login in your React app:

```javascript
// frontend/src/Login.js (create this)
import React, { useState } from 'react';

function Login({ onLogin }) {
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (password === 'YOUR_SECRET_PASSWORD') {
      onLogin();
      localStorage.setItem('bridgeAuth', 'true');
    } else {
      alert('Incorrect password');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Enter password"
      />
      <button type="submit">Login</button>
    </form>
  );
}
```

Then in `App.js`:
```javascript
const [isAuthenticated, setIsAuthenticated] = useState(
  localStorage.getItem('bridgeAuth') === 'true'
);

if (!isAuthenticated) {
  return <Login onLogin={() => setIsAuthenticated(true)} />;
}

// ... rest of your app
```

### Option 3: IP Whitelist (Most Secure)
In Render dashboard:
1. Upgrade to paid plan ($7/month)
2. Go to service settings
3. Add "IP Allow List"
4. Add your users' IP addresses

---

## Monitoring & Troubleshooting

### Check Deployment Status
**Render Dashboard:**
- Go to https://dashboard.render.com
- Click on your service
- View recent deploys (green = success, red = failure)
- Click on a deploy to see logs

### View Live Logs
```bash
# In Render dashboard:
# Click service → "Logs" tab
# See real-time logs from your Flask app

# Useful for debugging errors
```

### Common Issues

#### ❌ "Build Failed"
**Symptoms:** Red deploy status in Render
**Cause:** Usually missing dependencies or syntax errors
**Fix:**
1. Click failed deploy → view logs
2. Find error message
3. Fix locally and push again

```bash
# Example: Missing dependency
# Error in logs: "ModuleNotFoundError: No module named 'gunicorn'"
# Fix: Add to requirements.txt
echo "gunicorn>=21.2.0" >> backend/requirements.txt
git add backend/requirements.txt
git commit -m "Add missing gunicorn dependency"
git push origin main
```

#### ❌ Frontend can't reach backend
**Symptoms:** Browser console shows CORS errors or 404s
**Cause:** Wrong API URL in frontend
**Fix:**
1. Check `REACT_APP_API_URL` environment variable in Render
2. Make sure it matches your backend URL (including `https://`)
3. Redeploy frontend

#### ❌ "This site can't be reached"
**Symptoms:** Site loads then shows connection error
**Cause:** Free tier cold start (15 min timeout)
**Fix:**
- Wait 30 seconds for backend to wake up
- First request after inactivity is slow
- Consider upgrading to paid plan ($7/month) for always-on

#### ❌ Changes not showing up
**Symptoms:** Pushed changes but site looks the same
**Cause:** Browser cache or deploy not triggered
**Fix:**
1. Check Render dashboard - did deploy actually run?
2. Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
3. Try incognito window
4. Check "Deploys" tab for recent activity

### Performance Monitoring
- Free tier: Check "Metrics" tab in Render dashboard
- See request count, response times, memory usage
- Upgrade for more detailed analytics

---

## Cost Estimation

### Free Tier (Recommended for limited users)
- **Backend:** Free (750 hours/month, cold starts)
- **Frontend:** Free (100 GB bandwidth)
- **Total:** $0/month
- **Good for:** 10-20 users, occasional use

### Always-On Tier (No cold starts)
- **Backend:** $7/month (Starter plan)
- **Frontend:** Free
- **Total:** $7/month
- **Good for:** 20-100 users, frequent use

### Production Tier (Serious deployment)
- **Backend:** $25/month (Standard plan)
- **Frontend:** Free (or $19/month for custom domain)
- **Total:** $25-44/month
- **Good for:** 100+ users, professional use

---

## Next Steps After Deployment

1. ✅ **Test thoroughly** - Try all features on live site
2. ✅ **Add password protection** - Restrict access to invited users
3. ✅ **Share URL** - Send to your test users
4. ✅ **Monitor logs** - Check for errors in first week
5. ✅ **Gather feedback** - Ask users what works/doesn't work
6. ✅ **Iterate** - Make improvements based on feedback

---

## Support

- **Render Documentation:** https://render.com/docs
- **Render Community:** https://community.render.com
- **This Project:** File issues in your GitHub repo

---

## Quick Reference

### Important URLs
- **Render Dashboard:** https://dashboard.render.com
- **Your Backend:** https://bridge-bidding-api.onrender.com
- **Your Frontend:** https://bridge-bidding-app.onrender.com

### Quick Commands
```bash
# Commit to development (NO deployment)
git checkout development
git add . && git commit -m "Update" && git push origin development

# Deploy to production (triggers Render deployment)
git checkout main
git merge development
git push origin main

# Check current branch
git branch

# Check status
git log --oneline -5

# Revert last change
git revert HEAD && git push origin main

# View Render logs
# (Go to dashboard.render.com → service → Logs)
```

### Emergency Contacts
- Render Support: support@render.com (paid plans)
- Render Status: https://status.render.com

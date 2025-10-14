# Bridge Bidding App - Deployment Context

**Last Updated:** 2025-10-14
**Current Status:** Deployed on Render (Free Tier)

---

## Quick Overview

This is a Bridge bidding training application with:
- **Backend:** Flask (Python) API with AI bidding engine
- **Frontend:** React application
- **Hosting:** Render.com (free tier)
- **Repository:** https://github.com/JFrunk/bridge-bidding-app.git

---

## Current Deployment Configuration

### Platform: Render.com

**Deployment Method:** Git-based auto-deployment
- Push to `main` branch triggers automatic deployment
- Deployments typically complete in 2-5 minutes
- Free tier includes cold starts after 15 minutes of inactivity

### Backend Service

**Name:** `bridge-bidding-api`
**Type:** Web Service (Python)
**Expected URL:** `https://bridge-bidding-api.onrender.com`

**Configuration:**
```yaml
Runtime: Python 3.11
Root Directory: backend/
Build Command: pip install -r requirements.txt
Start Command: gunicorn --bind 0.0.0.0:$PORT server:app
Health Check: /api/scenarios
```

**Environment Variables:**
- `PYTHON_VERSION=3.11`
- `FLASK_ENV=production`
- `ANTHROPIC_API_KEY` (if using Claude AI for bidding)

**Dependencies** (from requirements.txt):
- Flask >= 3.0.0
- Flask-Cors >= 4.0.0
- gunicorn >= 21.2.0
- pytest >= 7.4.0
- endplay >= 0.5.0

### Frontend Service

**Name:** `bridge-bidding-frontend`
**Type:** Static Site
**Expected URL:** `https://bridge-bidding-app.onrender.com`

**Configuration:**
```yaml
Runtime: Node.js (static site)
Root Directory: frontend/
Build Command: npm install && npm run build
Publish Directory: build
```

**Environment Variables:**
- `REACT_APP_API_URL=https://bridge-bidding-api.onrender.com`

---

## Deployment Workflow

### Development to Production Pipeline

**Current Branch Strategy:**
- `main` - Production branch (triggers Render deployment)
- `development` - Development branch (recommended for changes)

**To Deploy Changes:**

```bash
# 1. Work on development branch (does NOT deploy)
git checkout development
# ... make changes ...
git add .
git commit -m "Description of changes"
git push origin development

# 2. When ready to deploy
git checkout main
git merge development
git push origin main   # Triggers automatic Render deployment
```

**Deployment Timeline:**
- Push detected: ~30 seconds
- Backend build: ~2 minutes
- Frontend build: ~2-3 minutes
- Total: ~5 minutes from push to live

---

## Database & Data Persistence

### Current Database: SQLite

**Location:** `backend/bridge.db`

**Important Notes:**
- SQLite file is stored locally on backend server
- **Free tier limitation:** Database resets on service restarts
- For production persistence, consider PostgreSQL upgrade

**Database Schema Includes:**
- 20 tables for user data, practice tracking, mistake analysis
- 8 error categories for bidding mistakes
- 9 celebration templates for gamification
- Analytical views for learning patterns

**Key Tables:**
- `users` - User accounts
- `practice_sessions` - Bidding practice history
- `mistake_patterns` - Common errors tracking
- `error_categories` - Mistake classification
- `celebration_templates` - Achievement messages

---

## API Endpoints

### Core Endpoints

**Game Play:**
- `POST /api/deal-hands` - Generate new bridge hand
- `POST /api/make-bid` - Submit bid and get AI response
- `GET /api/scenarios` - List available practice scenarios

**Learning & Analytics:**
- `POST /api/practice/record` - Record practice with error categorization
- `GET /api/analytics/dashboard` - Get dashboard data
- `GET /api/analytics/mistakes` - Get mistake patterns
- `GET /api/analytics/celebrations` - Get achievements
- `POST /api/analytics/acknowledge-celebration` - Acknowledge milestone

**User Management:**
- `POST /api/user/create` - Create new user
- `GET /api/user/info` - Get user profile and stats

---

## Architecture & Components

### Backend Components

**AI Bidding Engine:**
- Location: `backend/engine/ai/`
- Conventions: Standard American (SAYC)
- AI Strength: Expert level (9/10 rating)
- Double Dummy Solver integrated for optimal play

**Learning System:**
- `engine/learning/user_manager.py` - User accounts
- `engine/learning/error_categorizer.py` - Mistake detection
- `engine/learning/mistake_analyzer.py` - Pattern analysis
- `engine/learning/celebration_manager.py` - Gamification

**Key Features:**
- Real-time bid evaluation
- Error categorization (8 types)
- XP/leveling system
- Streak tracking
- Personalized recommendations

### Frontend Components

**Main Pages:**
- Home/Landing page
- Practice Mode - Interactive bidding
- Learning Dashboard - Analytics and progress
- Play Mode - Full hand play (declarer/defender)

**UI Framework:**
- React 18
- React Router for navigation
- Custom components for cards, bidding box, etc.

**Styling:**
- CSS-in-JS approach
- Mobile responsive
- Dark mode support planned

---

## Monitoring & Troubleshooting

### How to Check Status

**Render Dashboard:**
1. Go to https://dashboard.render.com
2. View recent deploys (green = success, red = fail)
3. Click "Logs" tab for real-time debugging

**Live Site Health:**
```bash
# Check backend is responding
curl https://bridge-bidding-api.onrender.com/api/scenarios

# Check frontend loads
curl https://bridge-bidding-app.onrender.com
```

### Common Issues

**Cold Starts (Free Tier):**
- Symptom: First request after 15+ min is slow (30+ seconds)
- Cause: Free tier spins down after inactivity
- Solution: Upgrade to $7/month Starter plan for always-on

**CORS Errors:**
- Symptom: Frontend can't reach backend
- Cause: Wrong `REACT_APP_API_URL` in frontend env
- Solution: Verify env var matches backend URL

**Database Loss:**
- Symptom: Users/data disappears
- Cause: Free tier restarts clear SQLite file
- Solution: Upgrade to PostgreSQL (Render managed database)

### Logs Access

**View Logs:**
- Render Dashboard → Select Service → Logs tab
- Shows real-time stdout/stderr from Flask app
- Useful for debugging 500 errors, missing dependencies, etc.

---

## Cost & Scaling

### Current Cost: $0/month (Free Tier)

**Free Tier Limitations:**
- Backend: 750 hours/month, cold starts after 15 min
- Frontend: 100 GB bandwidth/month
- Database: SQLite (ephemeral, resets on restart)
- Good for: 10-20 users, occasional use

### Upgrade Options

**Starter Tier - $7/month:**
- Always-on backend (no cold starts)
- Persistent storage
- Good for: 20-100 users

**Professional Tier - $25-44/month:**
- Backend: $25/month (Standard plan)
- PostgreSQL: $7/month (managed database)
- Custom domain: $12/month (optional)
- Good for: 100+ users, production use

---

## Security & Access Control

### Current Security

**Backend:**
- CORS configured for frontend domain
- No authentication currently (add as needed)
- API keys in environment variables (not in code)

**Frontend:**
- Served over HTTPS by Render
- No login system currently
- Public access (anyone with URL can use)

### Password Protection Options

**Option 1: Render HTTP Basic Auth (Simplest)**
- Enable in Render dashboard → Settings → HTTP Basic Auth
- Users see browser login prompt
- Good for: Quick restriction to known users

**Option 2: Custom Login (More Control)**
- Implement login page in React
- Store auth token in localStorage
- Validate on backend endpoints
- Good for: Multiple users, user accounts

**Option 3: IP Whitelist (Most Secure)**
- Requires paid plan
- Add allowed IP addresses in Render settings
- Good for: Corporate/private use

---

## Development Environment

### Local Development Setup

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py  # Runs on http://localhost:5001
```

**Frontend:**
```bash
cd frontend
npm install
npm start  # Runs on http://localhost:3000
```

**Testing:**
```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend build test
cd frontend
npm run build
```

---

## File Structure

```
bridge_bidding_app/
├── backend/
│   ├── server.py              # Flask app entry point
│   ├── bridge.db              # SQLite database
│   ├── requirements.txt       # Python dependencies
│   ├── engine/
│   │   ├── ai/               # Bidding AI
│   │   └── learning/         # Analytics system
│   └── tests/                # Backend tests
│
├── frontend/
│   ├── src/
│   │   ├── App.js            # React app entry
│   │   ├── components/       # React components
│   │   └── services/         # API clients
│   ├── build/                # Production build output
│   └── package.json          # Node dependencies
│
├── render.yaml               # Render deployment config
├── DEPLOYMENT_GUIDE.md       # Detailed deployment docs
└── docs/                     # Additional documentation
```

---

## Important Configuration Files

### render.yaml
Defines Render deployment configuration for both services. Used when deploying via Render Blueprint.

### backend/requirements.txt
Python dependencies. Must include `gunicorn` for production server.

### frontend/.env.example
Template for environment variables. Create `.env.production` with:
```
REACT_APP_API_URL=https://bridge-bidding-api.onrender.com
```

---

## Rollback Procedures

### Quick Rollback (Render Dashboard)
1. Go to Render dashboard
2. Select service (backend or frontend)
3. Click "Deploys" tab
4. Find last working deploy
5. Click "..." → "Redeploy"
6. Wait ~1-2 minutes

### Git-Based Rollback
```bash
# Revert last commit
git revert HEAD
git push origin main  # Triggers auto-redeploy

# OR reset to specific commit
git reset --hard <commit-hash>
git push origin main --force  # Use with caution
```

---

## Support & Documentation

### Key Documentation Files
1. **DEPLOYMENT_COMPLETE.md** - Backend deployment status
2. **DEPLOYMENT_GUIDE.md** - Step-by-step Render setup
3. **docs/project-overview/DEPLOYMENT.md** - General deployment info
4. **backend/MISTAKE_DETECTION_QUICKSTART.md** - Backend API guide
5. **frontend/FRONTEND_INTEGRATION_GUIDE.md** - Frontend integration

### External Resources
- Render Docs: https://render.com/docs
- Flask Docs: https://flask.palletsprojects.com/
- React Docs: https://react.dev/

### Repository
- GitHub: https://github.com/JFrunk/bridge-bidding-app
- Current branch: `main`
- Development branch: Use `development` for non-deployment changes

---

## Next Steps & Recommendations

### Immediate (Free Tier)
- ✅ Backend deployed and running
- ✅ Frontend deployed and accessible
- ⚠️ Consider adding authentication
- ⚠️ Test all features on live site

### Short Term (1-2 weeks)
- Consider upgrading to Starter tier ($7/month) for:
  - No cold starts
  - Better user experience
  - Persistent database
- Add user authentication if sharing with others
- Set up monitoring/alerting

### Long Term (Production Ready)
- Migrate to PostgreSQL for data persistence
- Implement proper user authentication
- Add error tracking (Sentry, LogRocket)
- Set up automated testing in CI/CD
- Consider custom domain

---

## Questions for Claude (Other Chat)

When discussing deployment, Claude should know:

1. **Where is it hosted?** Render.com (free tier)
2. **How to deploy updates?** Push to `main` branch → auto-deploys in ~5 minutes
3. **What's the URL?** Check Render dashboard for exact URLs
4. **Database?** SQLite (ephemeral on free tier, resets on restart)
5. **Cost?** $0 currently, $7/month recommended for always-on
6. **Branch strategy?** Use `development` for changes, merge to `main` to deploy
7. **Backend tech?** Flask + gunicorn, Python 3.11
8. **Frontend tech?** React, built to static files
9. **How to rollback?** Render dashboard → Deploys → Redeploy old version
10. **Monitoring?** Render dashboard → Logs tab

---

**This document provides complete context for deployment discussions.**
**Share this with AI assistants for accurate deployment guidance.**

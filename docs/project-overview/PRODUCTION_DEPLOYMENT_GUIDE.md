# Production Deployment Guide - Bridge AI with DDS

**Date:** October 14, 2025
**Status:** Ready for Deployment 🚀

---

## Prerequisites

✅ Code pushed to GitHub (main branch)
✅ Backend tested locally
✅ Frontend builds successfully
✅ DDS AI integrated and working
✅ Render configuration file (`render.yaml`) ready

---

## Deployment Steps

### Step 1: Create Render Account (5 minutes)

1. Go to https://render.com
2. Click "Get Started for Free"
3. Sign up with GitHub (easiest option)
4. Authorize Render to access your repositories
5. Select your `bridge-bidding-app` repository

### Step 2: Deploy Using Blueprint (10 minutes)

Render will automatically detect the `render.yaml` file and deploy both services.

1. **In Render Dashboard:**
   - Click "New +" → "Blueprint"
   - Select your `bridge-bidding-app` repository
   - Click "Apply Blueprint"

2. **Render will create TWO services:**
   - `bridge-bidding-api` (Backend Flask/Python)
   - `bridge-bidding-frontend` (Frontend React/Static)

3. **Wait for deployment (~3-5 minutes):**
   - Backend: Installing Python dependencies (including endplay for DDS)
   - Frontend: Building React production bundle
   - Both services will show "Live" when ready

4. **Note your URLs:**
   - Backend: `https://bridge-bidding-api.onrender.com`
   - Frontend: `https://bridge-bidding-frontend.onrender.com`

### Step 3: Verify Deployment (5 minutes)

1. **Test Backend API:**
   ```bash
   curl https://bridge-bidding-api.onrender.com/api/scenarios
   ```
   Should return JSON with scenarios.

2. **Test DDS AI is loaded:**
   - Check backend logs in Render dashboard
   - Should see: "✅ DDS AI loaded for expert difficulty (9/10 rating)"

3. **Test Frontend:**
   - Visit `https://bridge-bidding-frontend.onrender.com`
   - Start a new hand
   - Try bidding and playing
   - Test "Expert" difficulty to verify DDS AI

### Step 4: Configure Custom Domain (Optional)

If you want a custom domain like `bridge-trainer.com`:

1. **Purchase domain** (from Namecheap, Google Domains, etc.)
2. **In Render Dashboard:**
   - Go to frontend service
   - Click "Settings" → "Custom Domain"
   - Add your domain
   - Follow DNS instructions
3. **Update backend URL:**
   - Go to frontend service → "Environment"
   - Update `REACT_APP_API_URL` if needed

---

## What Gets Deployed

### Backend (Python/Flask)
- ✅ Flask API server
- ✅ All gameplay engines (bidding, playing)
- ✅ All 4 AI difficulty levels (beginner, intermediate, advanced, expert)
- ✅ **DDS AI for expert difficulty** (9/10 rating)
- ✅ endplay library with Double Dummy Solver
- ✅ SQLite database for users and sessions
- ✅ Learning analytics and mistake tracking
- ✅ Authentication system

### Frontend (React)
- ✅ Production-optimized React build
- ✅ All UI components
- ✅ Bidding interface
- ✅ Card playing interface
- ✅ Learning dashboard
- ✅ Session tracking
- ✅ Score panels

---

## Configuration Details

### Backend Configuration
From `render.yaml`:
```yaml
buildCommand: "pip install -r backend/requirements.txt"
startCommand: "gunicorn --bind 0.0.0.0:$PORT server:app --workers 2 --timeout 120"
```

**Important Settings:**
- `--workers 2`: Runs 2 worker processes for better performance
- `--timeout 120`: 2-minute timeout (DDS can take up to 200ms per solve)
- Includes `endplay>=0.5.0` for DDS functionality

### Frontend Configuration
From `render.yaml`:
```yaml
buildCommand: "npm install && npm run build"
envVars:
  - REACT_APP_API_URL: https://bridge-bidding-api.onrender.com
```

The frontend automatically connects to your backend API.

---

## Performance Expectations

### Free Tier (Render)
- **Cold Start:** First request after 15 minutes of inactivity takes ~30 seconds
- **Active Performance:** <1 second response time
- **DDS Expert AI:** 10-200ms per move
- **Concurrent Users:** Up to 10-20 users comfortably

### Paid Tier ($7/month - Recommended)
- **No Cold Starts:** Always running, instant response
- **Performance:** <500ms response time
- **DDS Expert AI:** 10-200ms per move (unchanged)
- **Concurrent Users:** Up to 100+ users

---

## Monitoring & Logs

### View Live Logs
1. Go to Render Dashboard
2. Click on `bridge-bidding-api` service
3. Click "Logs" tab
4. Watch for:
   - "✅ DDS AI loaded for expert difficulty" (DDS working)
   - API requests and responses
   - Any errors

### Check DDS Status
In the backend logs, you should see on startup:
```
✅ DDS AI loaded for expert difficulty (9/10 rating)
✓ Learning path API endpoints registered
✓ Analytics API endpoints registered
✓ Simple Auth API endpoints registered
 * Running on http://0.0.0.0:10000
```

If you see "⚠️ Using Minimax D4 for expert (DDS not available)", it means endplay failed to install.

---

## Troubleshooting

### Issue: "DDS not available" in logs
**Cause:** endplay installation failed
**Fix:**
1. Check backend build logs for errors
2. Ensure `endplay>=0.5.0` is in `requirements.txt`
3. Try redeploy from Render dashboard

### Issue: Frontend can't reach backend
**Cause:** CORS or wrong API URL
**Fix:**
1. Check `REACT_APP_API_URL` environment variable
2. Ensure it's `https://bridge-bidding-api.onrender.com` (with https)
3. Check Flask-Cors is enabled in `server.py`

### Issue: Cold starts are slow
**Cause:** Free tier sleeps after 15 min inactivity
**Fix:**
- Upgrade to $7/month paid tier for always-on service
- Or accept 30-second cold start delay

### Issue: Expert AI not working
**Cause:** DDS not loaded or errors in gameplay
**Fix:**
1. Check logs for "DDS AI loaded"
2. Test with intermediate/advanced first
3. Check browser console for errors

---

## Post-Deployment Checklist

After deployment completes:

- [ ] Backend is "Live" in Render dashboard
- [ ] Frontend is "Live" in Render dashboard
- [ ] Backend logs show "DDS AI loaded"
- [ ] Can load frontend URL in browser
- [ ] Can start a new hand
- [ ] Bidding works
- [ ] Card playing works
- [ ] Can switch to "Expert" difficulty
- [ ] Expert AI makes moves (within 200ms)
- [ ] No errors in browser console

---

## Updating the Deployment

### Automatic Updates
Render watches your GitHub `main` branch. Any push triggers auto-deployment.

```bash
# Make changes locally
# ... edit files ...

# Test locally
cd backend && python server.py
cd frontend && npm start

# Commit and push
git add .
git commit -m "Update feature X"
git push origin main

# Render automatically deploys (~3-5 minutes)
```

### Manual Redeploy
In Render Dashboard:
1. Click service name
2. Click "Manual Deploy" → "Deploy latest commit"

---

## Cost Summary

### Free Tier (Current)
- **Backend:** Free (with cold starts)
- **Frontend:** Free
- **Database:** Included (SQLite)
- **Bandwidth:** 100 GB/month free
- **Total:** $0/month

### Recommended Tier
- **Backend:** $7/month (no cold starts, always-on)
- **Frontend:** Free
- **Total:** $7/month

---

## Support & Documentation

- **Render Docs:** https://render.com/docs
- **This Project:**
  - DDS Integration: [`DDS_INTEGRATION_COMPLETE.md`](DDS_INTEGRATION_COMPLETE.md)
  - AI Summary: [`DDS_IMPLEMENTATION_SUMMARY.md`](DDS_IMPLEMENTATION_SUMMARY.md)
  - General Deployment: [`docs/project-overview/DEPLOYMENT.md`](docs/project-overview/DEPLOYMENT.md)

---

## Security Notes

### Database
- SQLite database is stored on Render's disk
- Free tier: Disk is NOT persistent (resets on redeploy)
- Paid tier: Persistent disk available ($0.25/GB/month)

**Recommendation:** Use persistent disk if you need user data preserved.

### Authentication
- Basic MVP authentication implemented
- Email/phone only (no passwords yet)
- Consider adding OAuth or password auth for production

### Environment Variables
- All sensitive config in Render environment variables
- Never commit secrets to GitHub
- Use Render's secret management

---

## Next Steps After Deployment

1. **Share URL** with test users
2. **Monitor logs** for first 24 hours
3. **Gather feedback** on expert AI performance
4. **Consider upgrade** to $7/month for better experience
5. **Add analytics** to track usage
6. **Implement backups** if using persistent data

---

## Emergency Rollback

If deployment breaks:

### Method 1: Render Dashboard
1. Go to service → "Deploys"
2. Find last working deploy
3. Click "..." → "Redeploy"

### Method 2: Git Revert
```bash
git revert HEAD
git push origin main
# Render auto-deploys the revert
```

---

## Success Criteria ✅

Deployment is successful when:

- ✅ Both services show "Live" in Render
- ✅ Backend logs show DDS AI loaded
- ✅ Frontend loads without errors
- ✅ Can play a full hand on expert difficulty
- ✅ Expert AI responds within 200ms
- ✅ No errors in browser console or backend logs

---

**Ready to deploy!** Follow Step 1 above to get started. 🚀

**Estimated Total Time:** 20-30 minutes for first deployment

Deploy current development branch to production (main):

⚠️  **CRITICAL: This deploys to live production on Oracle Cloud**

**SAFETY CHECKS FIRST:**

1. Verify you're on development branch: `git branch --show-current`
2. Check for uncommitted changes: `git status`
3. Review recent commits: `git log --oneline -10`
4. Run full test suite: `cd backend && ./test_full.sh`
5. Run bidding quality baseline (500 hands):
   - `python3 backend/test_bidding_quality_score.py --hands 500`
   - Must achieve: Legality 100%, Composite ≥ baseline
6. Run play quality baseline (500 hands):
   - `python3 backend/test_play_quality_integrated.py --hands 500 --level 8`
   - Must achieve: Legality 100%, Composite ≥ baseline
7. Verify no TODO/FIXME markers in changed files

**DEPLOYMENT SEQUENCE:**

8. Checkout main: `git checkout main`
9. Pull latest: `git pull origin main`
10. Merge development: `git merge development`
11. **Database Migration Check:**
    - If database schema changed, document migration steps
    - Remind user to run `python3 backend/database/init_all_tables.py` on production
12. Push to GitHub: `git push origin main`
13. Checkout development: `git checkout development`

**ORACLE CLOUD DEPLOYMENT:**

**Server Details:**
- **IP:** 129.146.229.15
- **SSH Alias:** oracle-bridge (configured in ~/.ssh/config)
- **Production URL:** https://app.mybridgebuddy.com

After pushing to main, deploy via SSH:
```bash
ssh oracle-bridge "bash /opt/bridge-bidding-app/deploy/oracle/maintenance.sh update"
```

Or one-liner pull + restart:
```bash
ssh oracle-bridge "cd /opt/bridge-bidding-app && git pull origin main && bash deploy/oracle/maintenance.sh restart"
```

**VERIFICATION:**

14. Wait 2-3 minutes for deployment to complete
15. Visit production URL and verify:
    - [ ] Dashboard loads without errors
    - [ ] Users can login
    - [ ] New deal works
    - [ ] Bidding feedback works
    - [ ] Dashboard shows statistics
    - [ ] DDS is active (check /api/dds-test endpoint)
16. Monitor logs: SSH to server, run `bash /opt/bridge-bidding-app/deploy/oracle/maintenance.sh logs`

**QUICK VERIFICATION COMMANDS:**
```bash
# Test API is responding
curl -s https://app.mybridgebuddy.com/api/scenarios | head -c 100

# Test DDS is working
curl -s https://app.mybridgebuddy.com/api/dds-test | python3 -m json.tool

# Check AI status
curl -s https://app.mybridgebuddy.com/api/ai/status | python3 -m json.tool
```

**ROLLBACK (if issues found):**
```bash
git checkout main
git revert HEAD
git push origin main
git checkout development
```

Then SSH to server and run:
```bash
ssh oracle-bridge "bash /opt/bridge-bidding-app/deploy/oracle/maintenance.sh update"
```

⛔ **Do NOT deploy if:**
- Any safety checks fail
- Tests are failing
- Quality scores show regression
- Uncommitted changes exist
- User hasn't confirmed deployment

Reference: CLAUDE.md Deploying to Production section, deploy/oracle/README.md

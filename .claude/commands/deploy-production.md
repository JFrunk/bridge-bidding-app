Deploy current development branch to production (main):

⚠️  **CRITICAL: This deploys to live production on Render**

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
12. Push to trigger Render deploy: `git push origin main`
13. Display Render deployment URL to monitor
14. Checkout development: `git checkout development`

**VERIFICATION:**

15. Wait for Render deployment to complete (check dashboard)
16. Visit production URL and verify:
    - [ ] Dashboard loads without errors
    - [ ] Users can login
    - [ ] New deal works
    - [ ] Bidding feedback works
    - [ ] Dashboard shows statistics
17. Monitor error logs for 5 minutes: `heroku logs --tail` or Render dashboard

**ROLLBACK (if issues found):**
```bash
git checkout main
git revert HEAD
git push origin main
git checkout development
```

⛔ **Do NOT deploy if:**
- Any safety checks fail
- Tests are failing
- Quality scores show regression
- Uncommitted changes exist
- User hasn't confirmed deployment

Reference: CLAUDE.md Deploying to Production section

---
description: Run end-to-end tests and full test suite
---

Run comprehensive tests including E2E: $ARGUMENTS

Optional arguments: e2e, all, quick, backend, frontend

---

## Quick Reference

```bash
# E2E tests only (headless)
npm run test:e2e --prefix frontend

# E2E tests (interactive UI - recommended for debugging)
npm run test:e2e:ui --prefix frontend

# ALL tests (backend + frontend + E2E) - 2-3 minutes
./test_all.sh

# Quick tests only - 30 seconds
./test_all.sh --quick

# Backend tests only
cd backend && ./test_full.sh
```

---

## Option 1: E2E Tests (Playwright)

**Headless (CI/CD style):**
```bash
cd frontend
npm run test:e2e
```

**Interactive UI (RECOMMENDED for development):**
```bash
cd frontend
npm run test:e2e:ui
```
- Visual test runner
- Step through tests
- See browser interactions
- Time travel debugging

**Headed (watch in browser):**
```bash
cd frontend
npm run test:e2e:headed
```

**View last test report:**
```bash
cd frontend
npm run test:e2e:report
```

---

## Option 2: Full Test Suite (All Tests)

**Comprehensive - Backend + Frontend + E2E (2-3 minutes):**
```bash
./test_all.sh
```

**Quick - Unit tests only (30 seconds):**
```bash
./test_all.sh --quick
```

**Skip E2E (1 minute):**
```bash
./test_all.sh --skip-e2e
```

---

## Option 3: Backend Tests Only

**Quick tests (30 seconds):**
```bash
cd backend
./test_quick.sh
```

**Medium tests (2 minutes):**
```bash
cd backend
./test_medium.sh
```

**Full backend suite (5+ minutes):**
```bash
cd backend
./test_full.sh
```

---

## Option 4: Frontend Tests Only

**Jest unit tests:**
```bash
cd frontend
npm test
```

**Jest with coverage:**
```bash
cd frontend
npm test -- --coverage
```

---

## Option 5: Quality Score Tests

**Bidding quality (5-15 minutes):**
```bash
# Quick check (100 hands, 5 minutes)
python3 backend/test_bidding_quality_score.py --hands 100

# Comprehensive (500 hands, 15 minutes)
python3 backend/test_bidding_quality_score.py --hands 500
```

**Play quality (10-30 minutes):**
```bash
# Quick check (100 hands, 10 minutes)
python3 backend/test_play_quality_integrated.py --hands 100 --level 8

# Comprehensive (500 hands, 30 minutes)
python3 backend/test_play_quality_integrated.py --hands 500 --level 8
```

---

## E2E Test Files

Located in `frontend/e2e/tests/`:
- `1-authentication.spec.js` - Login flow, guest mode
- `2-complete-game-flow.spec.js` - Full bidding and play
- `3-bidding-feedback.spec.js` - Bid evaluation system
- `4-dashboard-analytics.spec.js` - Dashboard and statistics
- `5-multi-user-isolation.spec.js` - User data separation
- `6-bid-display-timing.spec.js` - Bid rendering timing

---

## Debugging E2E Test Failures

**Step 1: Run interactively**
```bash
npm run test:e2e:ui --prefix frontend
```

**Step 2: Check for common issues**
- Server running? (`/restart`)
- Database clean?
- Ports 3000 and 5001 available?

**Step 3: View screenshots/videos**
```bash
open frontend/test-results/
```

**Step 4: Run single test**
```bash
npx playwright test 1-authentication --project=chromium --prefix frontend
```

---

## Before Committing

**REQUIRED checklist:**
- [ ] Run `./test_all.sh` (all tests pass)
- [ ] If bidding logic changed: Run bidding quality score (500 hands)
- [ ] If play logic changed: Run play quality score (500 hands, level 8)
- [ ] E2E tests pass (`npm run test:e2e --prefix frontend`)

---

## Success Criteria

✅ **Development:** Use `npm run test:e2e:ui` for debugging
✅ **CI/CD:** Use `npm run test:e2e` for automated testing
✅ **Before commit:** Run `./test_all.sh` for comprehensive validation
✅ **Quality changes:** Run baseline quality scores (500 hands)

Reference: CLAUDE.md Testing Strategy, E2E_TESTING_INTEGRATION_COMPLETE.md

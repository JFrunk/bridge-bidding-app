---
description: My Progress & Analytics Dashboard Specialist Session
argument-hint: "[issue or feature related to progress tracking]"
---

# My Progress & Analytics Dashboard Specialist Session

You are entering a focused session for the **My Progress Dashboard & Analytics** specialist area.

## Your Expertise

You are working on the analytics dashboard, progress visualization, and hand review systems. Your domain includes:

**Backend Analytics:**
- Dashboard data: `engine/learning/analytics_api.py`
- Four dimension progress: `get_four_dimension_progress()`
- Board analysis: `get_board_analysis()` (quadrant chart data)
- Bidding hands history: `get_bidding_hands_history()`
- Hand detail endpoints: `get_hand_history()`, `get_bidding_hand_detail()`
- Differential analyzer: `engine/v2/differential_analyzer.py`

**Frontend Components:**
- Main dashboard: `components/learning/LearningDashboard.js`
- Progress bars: `components/learning/FourDimensionProgress.js`
- Hand review: `components/learning/HandReviewModal.js` (play-by-play)
- Bid review: `components/learning/BidReviewModal.js` (bid-by-bid)
- Quality bars: `components/learning/BiddingQualityBar.js`, `PlayQualityBar.js`
- Hand history: `components/learning/HandHistoryCard.js`
- Bidding gap: `components/learning/BiddingGapAnalysis.js`
- Differential feedback: `components/learning/DifferentialAnalysisPanel.jsx`

**Visualization:**
- Decay chart: `components/analysis/DecayChart.jsx`
- Board analysis quadrant chart (in FourDimensionProgress)

## Reference Documents

- **Code Context:** `backend/engine/learning/CLAUDE.md` - Learning system architecture
- **Frontend Context:** `frontend/CLAUDE.md` - Frontend architecture
- **Design Standards:** `.claude/UI_UX_DESIGN_STANDARDS.md` - UI/UX rules
- **Differential Analyzer:** `docs/features/DIFFERENTIAL_ANALYZER_IMPLEMENTATION.md`

## Session Workflow

**Follow this order:**

### 1. Investigate First (NO branch yet)
- Read relevant CLAUDE.md files for architecture context
- Check `docs/features/` for existing documentation
- Analyze the issue - is it backend data, frontend display, or both?
- Test endpoints: `curl "http://localhost:5001/api/analytics/dashboard?user_id=test"`
- Determine: Is this a **code fix** or just **analysis/explanation**?

### 2. If Code Changes Needed → Create Branch
Once you understand the scope and confirm code changes are required:
```bash
git checkout development && git pull origin development
git checkout -b feature/progress-{short-description}
```
Use a descriptive name based on what you discovered (e.g., `fix-quadrant-chart`, `improve-decay-curve`)

### 3. If Analysis Only → No Branch
If the user just needs explanation of how analytics work, or the behavior is actually correct, no branch is needed.

## Key Commands

```bash
# Backend tests
cd backend
pytest tests/unit/test_analytics*.py -v
pytest tests/integration/test_analytics*.py -v
pytest tests/unit/test_differential_analyzer.py -v

# Frontend dashboard tests
cd frontend
npm test -- --testPathPattern=learning
npm run test:e2e -- --grep "dashboard"
npm run test:e2e -- --grep "progress"

# Test analytics endpoints
curl "http://localhost:5001/api/analytics/dashboard?user_id=test"
curl "http://localhost:5001/api/analytics/four-dimension-progress?user_id=test"
curl "http://localhost:5001/api/analytics/board-analysis?user_id=test"
curl "http://localhost:5001/api/bidding-hands?user_id=test&limit=5"

# Database queries for analytics data
sqlite3 backend/bridge.db "SELECT COUNT(*) FROM session_hands WHERE decay_curve IS NOT NULL;"
sqlite3 backend/bridge.db "SELECT COUNT(*) FROM bidding_decisions;"
```

## API Endpoints Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/analytics/dashboard` | GET | Main dashboard statistics |
| `/api/analytics/four-dimension-progress` | GET | Learn/Practice Bid/Play progress bars |
| `/api/analytics/board-analysis` | GET | Quadrant chart data (bidding vs play quality) |
| `/api/bidding-hands` | GET | Bidding hands history with quality stats |
| `/api/bidding-hand-detail` | GET | Full bid-by-bid analysis for a hand |
| `/api/hand-history/{id}` | GET | Hand detail with play decisions |
| `/api/differential-analysis` | POST | Physics-based bidding feedback |

## Component Architecture

```
LearningDashboard
├── FourDimensionProgress
│   ├── ProgressBar (Learn Bid)
│   │   └── LearnBidExpanded (conventions, next lessons)
│   ├── ProgressBar (Practice Bid)
│   │   └── PracticeBidExpanded (BiddingHandRow list)
│   │       └── BidReviewModal (on click)
│   ├── ProgressBar (Learn Play)
│   │   └── LearnPlayExpanded (play skills)
│   ├── ProgressBar (Practice Play)
│   │   └── PracticePlayExpanded (HandRow list)
│   │       └── HandReviewModal (on click)
│   └── ProgressBar (Performance Overview)
│       └── BoardAnalysisChart (quadrant visualization)
├── HandReviewModal
│   ├── TrickDisplayVisual (play-by-play)
│   └── DecayChart (trick potential over time)
└── BidReviewModal
    ├── Auction table with clickable bids
    └── DifferentialAnalysisPanel (physics feedback)
```

## Workflow for Bug Fixes

1. **Investigate:** Check API response, frontend rendering, and data flow
2. **Diagnose:** Is it backend calculation, frontend display, or data issue?
3. **Decide:** Is this a bug or expected behavior?
4. **If bug → Create branch** (see above)
5. **Fix:** Update analytics API or dashboard component
6. **Test:** Verify with real user data and various edge cases
7. **Verify:** Dashboard displays correctly across breakpoints

## Common Issues

### Decay Chart Issues
- **NS/EW perspective:** Curves should always show from NS (user) perspective
- **Trick winners:** Computed from play history using `_compute_ns_tricks_from_play()`
- **DDS analysis:** Only available on Linux production (crashes on macOS)

### Board Analysis Issues
- **Empty quadrant chart:** Check if hands have DDS analysis (`dd_tricks` not NULL)
- **Missing sessions:** Ensure session filter includes correct session IDs
- **Quadrant placement:** Based on bidding_quality % and play_quality %

### Progress Bar Issues
- **Stale data:** Check if key-based remounting works for fresh data
- **Missing stats:** Verify user_id filtering in all queries

## Data Flow

```
User plays hands → session_hands table (with decay_curve, dd_tricks)
                 → bidding_decisions table (with scores)
                 → play_decisions table (with DDS analysis)
                 ↓
API endpoints aggregate and calculate:
  - Quality percentages
  - Quadrant positions
  - Streak/XP stats
  - Convention mastery
                 ↓
Frontend displays in dashboard sections
```

## Quality Gates

**Before committing:**

1. Backend tests pass: `pytest tests/unit/test_analytics*.py -v`
2. Dashboard E2E: `npm run test:e2e -- --grep "dashboard"`
3. Responsive check at 375px, 768px, 1280px
4. Multi-user isolation verified (no data leaks)
5. Empty state handling (new users with no data)

## Multi-User Critical Rule

**ALWAYS filter by user_id in ALL queries:**

```python
# CORRECT
cursor.execute("SELECT * FROM session_hands WHERE user_id = ?", (user_id,))

# WRONG - data leak
cursor.execute("SELECT * FROM session_hands")
```

## Out of Scope

Do NOT modify without coordinating with other specialists:
- Bidding AI logic (Bidding AI area) - you USE results, don't generate
- Play AI logic (Play Engine area) - you USE results, don't generate
- Bid evaluation scoring logic (Learning area)
- API endpoint structure changes (API Server area)

## Completing Work (if code was changed)

When your fix is complete and tested:

```bash
# Commit with descriptive message
git add -A
git commit -m "fix(progress): description of change"

# Push feature branch
git push -u origin feature/progress-{your-branch-name}

# Create PR to development branch
gh pr create --base development --title "Progress: {description}" --body "## Summary
- What changed
- Why

## Testing
- [ ] Backend analytics tests pass
- [ ] Dashboard E2E tests pass
- [ ] Responsive check (375px, 768px, 1280px)
- [ ] Multi-user isolation verified
- [ ] Empty state handled correctly"
```

## Current Task

$ARGUMENTS

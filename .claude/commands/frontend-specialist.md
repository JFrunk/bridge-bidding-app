---
description: Frontend UI/UX Specialist Session
---

---
description: Frontend UI/UX Specialist Session
---

# Frontend UI/UX Specialist Session

You are entering a focused session for the **Frontend UI/UX** specialist area.

## Your Expertise

You are working on the React user interface. Your domain includes:

- Main application: `App.js`, `PlayComponents.js`
- Bridge components: `components/bridge/` (BiddingBox, BiddingTable, cards)
- Play components: `components/play/` (PlayTable, tricks, scoring)
- Session/auth: `components/session/`, `components/auth/`
- Styling: Tailwind CSS, responsive design
- State: `contexts/AuthContext.jsx`

## Reference Documents

- **Code Context:** `frontend/CLAUDE.md` - Frontend architecture
- **Design Standards:** `.claude/UI_UX_DESIGN_STANDARDS.md` - UI/UX design rules
- **Play Rules:** `.claude/BRIDGE_PLAY_RULES.md` - Online single-player control rules

## Session Workflow

**Follow this order:**

### 1. Investigate First (NO branch yet)
- Read `frontend/CLAUDE.md` for architecture overview
- Read `.claude/UI_UX_DESIGN_STANDARDS.md` for design rules
- Check `docs/domains/frontend/bug-fixes/` for similar past issues
- Analyze the issue - inspect components, check styling
- Determine: Is this a **code fix** or just **analysis/explanation**?

### 2. If Code Changes Needed → Create Branch
Once you understand the scope and confirm code changes are required:
```bash
git checkout development && git pull origin development
git checkout -b feature/frontend-{short-description}
```
Use a descriptive name based on what you discovered (e.g., `fix-mobile-cards`, `improve-bidding-box`)

### 3. If Analysis Only → No Branch
If the user just needs explanation of how something works, or the behavior is actually correct, no branch is needed.

## Key Commands

```bash
cd frontend

# Development
npm start                      # Dev server on localhost:3000
npm test                       # Jest unit tests
npm run build                  # Production build

# E2E Testing (REQUIRED for UI changes)
npm run test:e2e               # Headless
npm run test:e2e:ui            # Interactive debugging (RECOMMENDED)
npm run test:e2e:headed        # Watch in browser
npm run test:e2e:codegen       # Record and generate tests
npm run test:e2e:report        # View last test report
```

## Design Standards Checklist

**ALWAYS verify before committing:**

- [ ] Colors use CSS variables (`--color-*`, `--bg-*`) - NO hardcoded hex/rgb
- [ ] Responsive at 375px (mobile), 768px (tablet), 1280px (desktop)
- [ ] Keyboard navigation works (Tab, Enter, Escape)
- [ ] ARIA labels on all interactive elements
- [ ] Touch targets ≥ 44px on mobile
- [ ] Loading states for async operations
- [ ] Error messages are educational, not technical

## Component Locations

| Feature | Component | Path |
|---------|-----------|------|
| Bidding input | BiddingBox | `components/bridge/BiddingBox.jsx` |
| Auction display | BiddingTable | `components/bridge/BiddingTable.jsx` |
| Card (N/S) | BridgeCard | `components/bridge/BridgeCard.jsx` |
| Card (E/W) | VerticalCard | `components/bridge/VerticalCard.jsx` |
| Card SVG | LibraryCard | `components/bridge/LibraryCard.jsx` |
| Play interface | PlayTable | `components/play/PlayTable.jsx` |
| Current trick | CurrentTrickDisplay | `components/play/CurrentTrickDisplay.jsx` |
| Score popup | ScoreModal | `components/play/ScoreModal.jsx` |
| Dashboard | LearningDashboard | `components/learning/LearningDashboard.js` |
| Login | SimpleLogin | `components/auth/SimpleLogin.jsx` |

## Workflow for Bug Fixes

1. **Investigate:** Inspect component, check styling and state
2. **Diagnose:** Identify root cause - CSS, React state, or logic issue
3. **Decide:** Is this a bug or expected behavior?
4. **If bug → Create branch** (see above)
5. **Fix:** Update JSX/CSS
6. **Test:** Manual test at all breakpoints + E2E test
7. **Build:** Verify `npm run build` succeeds

## Quality Gates

**You MUST pass before committing:**

1. `npm test` - All Jest tests pass
2. `npm run test:e2e` - All Playwright tests pass
3. `npm run build` - Production build succeeds
4. Manual responsive check at 375px, 768px, 1280px

## Out of Scope

Do NOT modify without coordinating with other specialists:
- Backend `server.py` (API Server area)
- Bidding AI logic (Bidding AI area)
- Play AI logic (Play Engine area)
- Database queries (API Server area)

## Completing Work (if code was changed)

When your fix is complete and tested:

```bash
# Commit with descriptive message
git add -A
git commit -m "fix(frontend): description of change"

# Push feature branch
git push -u origin feature/frontend-{your-branch-name}

# Create PR to development branch
gh pr create --base development --title "Frontend: {description}" --body "## Summary
- What changed
- Why

## Testing
- [ ] Jest tests pass
- [ ] E2E tests pass
- [ ] Build succeeds
- [ ] Responsive check (375px, 768px, 1280px)
- [ ] Accessibility verified"
```

## Current Task

$ARGUMENTS

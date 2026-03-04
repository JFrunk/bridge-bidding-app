---
description: Recommend specialist command(s) based on current changes or task
---

---
description: Recommend specialist command(s) based on current changes or task
---

Recommend specialist command(s) for current work: $ARGUMENTS

Task description or context: $ARGUMENTS

---

## Step 1: Gather Context

Check both the current diff and any task description provided:

```bash
git diff --name-only HEAD
git diff --name-only --cached
git status --short
git log --oneline -5
```

If `$ARGUMENTS` describes a task (not empty), use that as the primary signal. Otherwise, infer from changed files.

---

## Step 2: Map to Specialist Domains

| File Patterns | Specialist | Command |
|---------------|-----------|---------|
| `engine/opening_bids.py`, `engine/responses.py`, `engine/rebids.py`, `engine/overcalls.py`, `engine/ai/conventions/`, `engine/ai/decision_engine.py`, `engine/ai/feature_extractor.py` | Bidding AI | `/bidding-specialist` |
| `engine/play_engine.py`, `engine/play/ai/`, `engine/play/` | Play Engine | `/play-specialist` |
| `frontend/src/components/`, `frontend/src/pages/`, CSS files | Frontend UI | `/frontend-specialist` |
| `server.py`, `backend/utils/`, database, sessions, API routes | Server/API | `/server-specialist` |
| `engine/feedback/`, skill trees, learning paths, hand generators | Learning | `/learning-specialist` |
| `frontend/src/components/progress/`, analytics API, dashboard | Progress | `/progress-specialist` |

**Cross-cutting triggers:**
- Changes spanning 2+ domains -> recommend multiple specialists
- New convention files -> `/bidding-specialist` + `/add-convention`
- Quality regressions -> `/compare-quality` before specialist
- Error log mentions -> `/analyze-errors` first

---

## Step 3: Present Recommendation

```
## Specialist Recommendation

**Based on:** [git diff / task description / both]

### Recommended
1. `/specialist-name` — [why: which files/patterns triggered this]

### Also Consider
- `/other-command` — [if relevant but not primary]

### Pre-requisites
- [Any commands to run first, e.g., /analyze-errors, /quality-baseline]
```

If no specialist is clearly needed (docs-only changes, config updates), say so:
> No specialist session needed. Changes are limited to [docs/config/etc].

---

## Success Criteria

- [ ] Current changes or task analyzed
- [ ] Correct specialist(s) identified with rationale
- [ ] Cross-cutting concerns flagged
- [ ] Pre-requisite commands noted if applicable

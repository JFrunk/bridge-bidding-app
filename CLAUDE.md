# CLAUDE.md

Bridge Bidding Training App - SAYC bidding system with AI opponents.

## Quick Start

```bash
# Backend (terminal 1)
cd backend && source venv/bin/activate && python server.py  # localhost:5001

# Frontend (terminal 2)
cd frontend && npm start  # localhost:3000
```

## Run Tests

```bash
# Quick (30s)
cd backend && ./test_quick.sh

# Full (2-3 min)
./test_all.sh

# E2E only
cd frontend && npm run test:e2e
```

## Quality Scores (before bidding/play changes)

```bash
# Bidding
cd backend && python3 test_bidding_quality_score.py --hands 100

# Play (use minimax on macOS - DDS crashes)
cd backend && python3 test_play_quality_integrated.py --hands 100 --ai minimax --depth 3
```

## Architecture

**Backend** (`backend/`): Flask server on port 5001
- `server.py` - REST API endpoints
- `engine/bidding_engine.py` - Orchestrates bidding AI
- `engine/play_engine.py` - Card play and tricks
- `engine/ai/conventions/` - SAYC conventions (Stayman, Jacoby, Blackwood, etc.)

**Frontend** (`frontend/src/`): React app on port 3000
- `App.js` - Main orchestrator
- `components/bridge/` - BiddingBox, BiddingTable, cards
- `components/play/` - PlayTable, trick display

**Database**: SQLite (`backend/bridge.db`)

## Key Flows

```
Bidding: Request → BiddingEngine → DecisionEngine → Convention/Module → Bid
Play:    Request → PlayEngine → AI (Simple/Minimax/DDS) → Card → Trick eval
```

## AI Difficulty

| Difficulty | AI | Notes |
|------------|-----|-------|
| beginner | SimplePlayAI | Fast, basic heuristics |
| intermediate | MinimaxPlayAI (depth 2) | Moderate lookahead |
| advanced | MinimaxPlayAI (depth 3) | Default on macOS |
| expert | DDSPlayAI | Linux only (perfect play) |

## Git Workflow

```bash
git checkout development     # All dev work here
git push origin development  # Does NOT deploy

# To deploy:
git checkout main && git merge development && git push origin main
```

## Reference Documents

- `.claude/SAYC_REFERENCE.md` - Official SAYC bidding rules
- `.claude/BRIDGE_PLAY_RULES.md` - Play rules (online vs offline)
- `backend/engine/CLAUDE.md` - Bidding engine details
- `backend/engine/play/CLAUDE.md` - Play engine details
- `frontend/CLAUDE.md` - Frontend architecture

## Specialist Agents

Use `/bidding-specialist`, `/play-specialist`, `/frontend-specialist`, `/server-specialist`, or `/learning-specialist` for domain-focused work.

## Critical Rules

1. **DDS crashes on macOS** - Use 'advanced' difficulty for local testing
2. **Run quality score** before modifying bidding or play logic
3. **User is always South** - AI controls N/E/W
4. **Dealer rotates** North → East → South → West (Chicago)
5. **All queries filter by user_id** - Multi-user isolation required

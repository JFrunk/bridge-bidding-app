# DDS Verification System

**Date:** 2025-11-25
**Status:** Active

## Overview

The DDS (Double Dummy Solver) verification system provides endpoints to confirm that DDS is operational in production. This is critical because DDS can be "loaded" but fail silently during actual solves.

## Problem Solved

Previously, `/api/ai/status` showed `dds_available: true` but there was no way to verify DDS was actually solving correctly. The `ai_play_log` table was also missing from PostgreSQL, causing `/api/dds-health` to fail.

## Endpoints

### `/api/dds-test` (GET)

**Definitive DDS verification** - Actually runs a DDS solve.

Creates a test position and verifies DDS returns the correct answer.

**Response (DDS working):**
```json
{
  "platform": "Linux",
  "platform_allows_dds": true,
  "dds_available": true,
  "expert_ai_type": "Double Dummy Solver AI",
  "test_performed": true,
  "test_passed": true,
  "solve_time_ms": 45.23,
  "expected_tricks": 13,
  "computed_tricks": 13,
  "message": "DDS working correctly! Solved in 45.2ms"
}
```

**Response (DDS not available - macOS):**
```json
{
  "platform": "Darwin",
  "platform_allows_dds": false,
  "dds_available": false,
  "expert_ai_type": "Minimax AI (depth 4)",
  "test_performed": false,
  "test_passed": false,
  "error": "DDS not available on this platform"
}
```

### `/api/dds-health` (GET)

**DDS health dashboard** - Shows play statistics and fallback rates.

Query parameters:
- `hours`: Number of hours to look back (default: 24)

**Response:**
```json
{
  "dds_available": true,
  "platform": "Linux",
  "hours_analyzed": 24,
  "overall": {
    "total_plays": 156,
    "avg_solve_time_ms": 42.5,
    "fallback_rate": 0.02,
    "fallback_count": 3
  },
  "by_level": {
    "expert": {"plays": 100, "avg_solve_time_ms": 45.2, "fallback_rate": 0.01}
  },
  "recent_plays": [...]
}
```

### `/api/ai/status` (GET)

**AI configuration status** - Shows which AI is active.

## Database Requirements

The `ai_play_log` table must exist in PostgreSQL for health monitoring:

```sql
CREATE TABLE IF NOT EXISTS ai_play_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    session_id TEXT,
    hand_number INTEGER,
    trick_number INTEGER,
    position TEXT NOT NULL,
    ai_level TEXT NOT NULL,
    card_played TEXT NOT NULL,
    solve_time_ms REAL,
    used_fallback BOOLEAN DEFAULT FALSE,
    contract TEXT,
    trump_suit TEXT
);
```

Migration: `backend/migrations/003_add_ai_play_logging_postgres.sql`

## Usage

### Verify DDS in Production

```bash
# Quick check - does DDS actually solve?
curl https://bridge-bidding-api.onrender.com/api/dds-test | python3 -m json.tool

# After playing some hands - check health stats
curl https://bridge-bidding-api.onrender.com/api/dds-health | python3 -m json.tool
```

### Interpreting Results

| Scenario | `test_passed` | `fallback_rate` | Meaning |
|----------|---------------|-----------------|---------|
| DDS working | `true` | < 5% | Normal operation |
| DDS available but failing | `false` | > 20% | DDS crashing, investigate |
| DDS not available | `false` | N/A | Expected on macOS |

## Platform Notes

- **Linux (production):** DDS fully functional
- **macOS:** DDS disabled (crashes on Apple Silicon)
- **Windows:** DDS may work but not tested

## Files

- `/api/dds-test`: `backend/server.py` (lines 2307-2378)
- `/api/dds-health`: `backend/server.py` (lines 2212-2304)
- Schema: `backend/database/schema_postgresql.sql` (lines 403-422)
- Migration: `backend/migrations/003_add_ai_play_logging_postgres.sql`

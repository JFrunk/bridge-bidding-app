# Signal Integrity Validation

**Created:** 2026-01-06
**Status:** Active

## Overview

The Signal Integrity Validation system ensures that the DDS (Double Dummy Solver) AI plays cards that are not only mathematically optimal but also **human-understandable** - following standard bridge signaling conventions.

## The Problem

DDS treats all cards in an "equivalence set" (cards with the same trick count) as identical. But humans use card choice to signal information to partner:

- Leading Q from QJT tells partner "I have J and T, I don't have K"
- Playing J from QJ when following signals "I have the Q"
- Playing low when partner wins preserves honors for later

Without the Tactical Overlay, DDS would make arbitrary choices that confuse human partners.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Layer 3: Human Validation (test_understandable_play.py) │
├─────────────────────────────────────────────────────────┤
│  Layer 2: Tactical Overlay (play_signal_overlay.py)      │
├─────────────────────────────────────────────────────────┤
│  Layer 1: Pure DDS Engine (dds_ai.py)                    │
└─────────────────────────────────────────────────────────┘
```

## Key Files

- `backend/engine/play/ai/play_signal_overlay.py` - TacticalPlayFilter implementation
- `backend/engine/play/ai/signal_integrity_report.py` - Metrics and reporting
- `backend/tests/play/test_understandable_play.py` - Validation test suite
- `backend/tests/play/test_tactical_signal_overlay.py` - Unit tests

## Heuristics Implemented

| Heuristic | Rule | Example |
|-----------|------|---------|
| Top of Sequence | Lead highest from touching honors | K from KQJ |
| Lowest of Equals | Follow with lowest from sequence | J from QJ |
| 2nd Hand Low | Play low in second position | 3 from K53 |
| 3rd Hand High | Play high to force declarer | K from K53 |
| Win Cheaply | Win with lowest winning card | Q to beat J |
| Declarer Conservation | Don't waste winners on same trick | Play low on dummy's K |
| Defensive Deference | Don't overtake partner's winner | Play 7 on partner's J |
| Unblocking | Play blocking cards early | Singleton A on partner's K |

## Signal Integrity Report

The `SignalIntegrityAuditor` class tracks:

- **Deduction Confidence** - % of plays enabling accurate partner inference
- **Signal Noise Rate** - % of "random" choices from equivalence sets
- **Heuristic Adherence** - Per-heuristic compliance rates
- **Falsification Events** - Detailed log of convention violations

### Rating Scale

| Score | Rating | Meaning |
|-------|--------|---------|
| ≥95% | Expert | Partner can trust every card played |
| 85-95% | Competent | Minor inconsistencies |
| 70-85% | Developing | Some random choices |
| <70% | Chaotic | Cannot reliably place honors |

## Usage

### Running Tests

```bash
cd backend
source venv/bin/activate
PYTHONPATH=. pytest tests/play/test_understandable_play.py -v
```

### Using Signal Integrity Report

```python
from engine.play.ai.signal_integrity_report import SignalIntegrityAuditor

auditor = SignalIntegrityAuditor()
auditor.log_decision(
    equivalence_set=[Card('K', '♠'), Card('Q', '♠')],
    selected_card=Card('K', '♠'),
    context="opening_lead",
    actual_heuristic="top_of_sequence",
    reason="Top of sequence lead"
)
report = auditor.generate_report()
print(f"Integrity Score: {report['integrity_score']}%")
```

## Test Categories

1. **Top of Sequence Leads** - Validates K from KQJ, Q from QJT, J from JT9
2. **Lowest of Equals Follow** - Validates J from QJ, Q from KQ, T from JT
3. **Information Integrity** - Validates signal deduction chains
4. **Declarer Unit Coordination** - Prevents Ace-on-King wastage
5. **Defensive Deference** - Prevents Q-on-J wastage
6. **Unblocking Exceptions** - Validates singleton/doubleton honor handling

## Related Documentation

- Play Engine Architecture: `backend/engine/play/CLAUDE.md`
- Bridge Play Rules: `.claude/BRIDGE_PLAY_RULES.md`

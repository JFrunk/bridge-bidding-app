# ADR: Server Modularization

**Date:** 2025-10-16
**Status:** Decided — Do Not Modularize (with conditions for revisiting)
**Consolidated from:** CASE_AGAINST_SERVER_MODULARIZATION.md, MODULARIZATION_DECISION_MATRIX.md, MODULARIZATION_ASSESSMENT_PRIORITIZED.md

---

## Context

server.py reached 1,705 lines with 31 endpoints across 10+ domains (session, bidding, play, scenarios, AI, reviews, auth, analytics, learning, feedback). Three independent analyses were conducted to evaluate whether to split it into Flask Blueprints.

## Decision

**Do not modularize server.py.** Use the existing `register_endpoints()` pattern for new API groups.

## Rationale

### Why Not

1. **No test safety net.** No comprehensive integration test suite exists. Refactoring 31 endpoints blind risks breaking production. Writing tests first adds 2+ weeks before modularization even starts.

2. **Solo developer reality.** 80% of modularization benefits (merge conflicts, onboarding, team collaboration) don't apply. The codebase has one developer.

3. **Opportunity cost.** 3-4 week estimate (likely 6-8 weeks in practice) = months of user-facing features not shipped. ROI is negative for a solo developer.

4. **Already partially modular.** Learning, analytics, and auth APIs already use `register_endpoints()` pattern successfully. This gives ~80% of the organizational benefit without the risk.

5. **Flask Blueprints complexity.** State management (`get_state()`) must work uniformly across modules. Global AI instances dict, circular import risks, and request context subtleties add real implementation risk.

### File-by-File Assessment

| File | Lines | Decision | Rationale |
|------|-------|----------|-----------|
| server.py | 1,705 | Don't split | Risk too high without tests, register_endpoints works |
| evaluation.py | 813 | Don't split | Only worth it if actively tuning AI weights |
| play_engine.py | 545 | Never split | Core game logic must stay cohesive |
| minimax_ai.py | 512 | Never split | Algorithm is a cohesive unit, splitting adds overhead |
| mistake_analyzer.py | 703 | Never split | Already well-organized with clear method separation |

### Metrics

- Average endpoint: 55 lines (normal, not bloated)
- Estimated modularization effort: 3-4 weeks (likely 6-8)
- ROI for solo developer: Negative

## Conditions for Revisiting

Modularize server.py IF ALL of these become true:
1. Comprehensive integration test suite covers all 31 endpoints
2. Team scaling is anticipated or merge conflicts are causing real pain
3. Can absorb 3-4 week cost without sacrificing user-facing features
4. Use phased approach: low-risk extractions first (scenario_api, ai_config_api), then medium (session_api), then high (bidding_api, play_api)

## Alternative Chosen

Continue using `register_endpoints()` pattern for new API groups. Add section comments/markers to server.py for navigation. Write integration tests incrementally.

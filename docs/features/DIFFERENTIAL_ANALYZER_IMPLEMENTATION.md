# Differential Analyzer Implementation Plan

**Last Updated:** 2026-01-05
**Status:** Phase 3 Complete - All Phases Implemented
**Purpose:** Transform the feedback system from binary "right/wrong" to a physics-based differential analyzer

---

## Implementation Status

### Phase 1: Backend & Frontend Core ✅ COMPLETE

| Component | Status | Location |
|-----------|--------|----------|
| DifferentialAnalyzer service | ✅ | `backend/engine/v2/differential_analyzer.py` |
| `/api/differential-analysis` endpoint | ✅ | `backend/engine/learning/analytics_api.py` |
| Enhanced `/api/evaluate-bid` | ✅ | `backend/server.py` (includes differential data) |
| Unit tests | ✅ | `backend/tests/unit/test_differential_analyzer.py` (17 tests) |
| DifferentialAnalysisPanel.jsx | ✅ | `frontend/src/components/learning/` |
| BidFeedbackPanel integration | ✅ | "Why?" button with expandable differential view |

### Phase 2: Chart Integration ✅ COMPLETE

| Component | Status | Notes |
|-----------|--------|-------|
| DecayChart bidding context markers | ✅ | LoTT ceiling line, overbid indicator, domain badge |
| Success Map domain coloring | ✅ | Domain-based colors, tooltip with domain info, domain legend |

### Phase 3: Polish & Testing ✅ COMPLETE

| Component | Status | Notes |
|-----------|--------|-------|
| E2E tests | ✅ | `8-differential-feedback.spec.js` (8 test cases) |
| Quality baseline | ✅ | 95.0% composite score (Grade A) |
| Data-testid attributes | ✅ | Added to BidFeedbackPanel and DifferentialAnalysisPanel |

---

## Executive Summary

This document outlines the implementation of a **Differential Analyzer** system that provides educational, first-principles feedback to bridge bidding learners. Instead of simply telling users they are "wrong," the system quantifies the **Mathematical Delta** between the user's bid and the optimal choice using the same Golden Master logic that powers the AI.

### Key Principle: Unified Truth

The feedback loop is powered by the same `enhanced_extractor.py` and JSON rules used for the AI. This ensures that the reasoning provided to the user is **identical to the engine's internal physics**.

---

## 1. Current Infrastructure (What Already Exists)

### 1.1 Feature Extraction (`enhanced_extractor.py`)

**Location:** `backend/engine/v2/features/enhanced_extractor.py` (1,900+ lines)

**Already Implemented Features:**

| Category | Features | Status |
|----------|----------|--------|
| **HCP & Points** | `hcp`, `dist_points`, `total_points`, `quick_tricks` | ✅ Complete |
| **Working HCP** | `working_hcp_ratio` (HCP in partner's suits) | ✅ Complete |
| **LoTT/Safety** | `lott_safe_level` calculations, `total_tricks_index` | ✅ Complete |
| **Support Points** | `support_points`, `dummy_points`, `control_multiplier` | ✅ Complete |
| **SSP (Short Suit)** | Shortness valuation with trump quality scaling | ✅ Complete |
| **Stoppers** | `{suit}_stopped`, `{suit}_stopper_quality` | ✅ Complete |
| **Defensive Value** | `is_defensive_powerhouse`, `offense_to_defense_ratio` | ✅ Complete |
| **Misfit Detection** | `is_misfit`, `is_misfit_heavy` | ✅ Complete |
| **Trump Quality** | `trump_suit_quality_score`, `is_fragile_ruff` | ✅ Complete |
| **Auction Context** | `opener_relationship`, forcing status, position flags | ✅ Complete |

### 1.2 Gap Analysis (`SchemaInterpreter`)

**Location:** `backend/engine/v2/interpreters/schema_interpreter.py` (lines 716-1053)

**Already Implemented Methods:**

```python
# Main entry point - analyzes ALL rules against features
get_rule_gap_analysis(features, target_bid=None, max_rules=10) -> List[Dict]

# Per-rule analysis with detailed condition breakdown
_analyze_rule_gaps(rule, features, category) -> Dict

# Recursive condition analyzer with gap calculations
_analyze_conditions(conditions, features, prefix='') -> List[Dict]
```

**Gap Analysis Output Structure:**
```python
{
    'rule_id': 'responder_game_raise',
    'bid': '4♠',
    'category': 'responses',
    'priority': 225,
    'description': 'Raise with 4+ support and game values',
    'matched': False,
    'gap_count': 1,
    'trigger': 'pattern:1♠-Pass',
    'trigger_matched': True,
    'trigger_gap': None,
    'conditions': [
        {
            'key': 'hcp',
            'type': 'comparison',
            'required': {'min': 12},
            'actual': 10,
            'passed': False,
            'gap': 'min 12 (have 10, need +2)',
            'min_shortfall': 2
        },
        {
            'key': 'support_for_partner',
            'type': 'comparison',
            'required': {'min': 4},
            'actual': 5,
            'passed': True,
            'gap': None
        }
    ]
}
```

### 1.3 Gap Analysis API Endpoint

**Location:** `backend/engine/learning/analytics_api.py` (line 3487)

**Endpoint:** `POST /api/bidding-gap-analysis`

**Status:** ✅ Fully Implemented and Registered

**Request:**
```json
{
    "hand_cards": [{"suit": "♠", "rank": "A"}, ...],
    "auction_history": ["Pass", "1NT", "Pass"],
    "position": "S",
    "vulnerability": "None",
    "dealer": "N",
    "target_bid": "2NT"  // Optional filter
}
```

**Response:**
```json
{
    "matched_rules": [...],
    "near_misses": [...],  // 1-3 gaps only, max 10
    "hand_features": {
        "hcp": 12,
        "shape": "5-3-3-2",
        "is_balanced": true,
        "longest_suit": "♠",
        "spades_stopped": true,
        ...
    },
    "total_rules_checked": 247
}
```

### 1.4 Frontend Gap Analysis Component

**Location:** `frontend/src/components/learning/BiddingGapAnalysis.js`

**Status:** ✅ Component Built, Ready for Data

**Features:**
- Fetches from `/api/bidding-gap-analysis`
- Displays matched rules with expandable details
- Shows near-misses with specific gap information
- Color-coded pass/fail conditions
- Hand features summary (HCP, shape, stoppers)
- Auto-expands first matched and first near-miss

---

## 2. What Needs to Be Built: Differential Analyzer

### 2.1 Core Concept: The Differential

The Differential Analyzer compares:
1. **User's Bid** → Which rules does it match?
2. **Optimal Bid** → Which rules does the optimal bid match?
3. **The Delta** → What specific constraints separate them?

### 2.2 New Service: `DifferentialAnalyzer`

**Location:** `backend/engine/v2/differential_analyzer.py` (NEW FILE)

```python
class DifferentialAnalyzer:
    """
    Compares user's bid against optimal bid using rule-based analysis.
    Provides educational feedback showing exactly why bids differ.
    """

    def analyze_bid_differential(
        self,
        user_bid: str,
        optimal_bid: str,
        hand: Hand,
        auction_history: List[str],
        position: str,
        vulnerability: str,
        dealer: str
    ) -> DifferentialResult:
        """
        Main entry point for differential analysis.

        Returns:
            DifferentialResult with:
            - user_bid_rules: Rules that match user's bid
            - optimal_bid_rules: Rules that match optimal bid
            - differential_factors: Specific constraints that differ
            - learning_point: Educational summary
        """
        pass

    def get_rule_comparison(
        self,
        user_bid: str,
        optimal_bid: str,
        all_rules: List[Dict]
    ) -> RuleComparison:
        """
        Compare which rules match user's bid vs optimal bid.
        """
        pass

    def calculate_feature_shortfalls(
        self,
        rule: Dict,
        features: Dict
    ) -> List[FeatureShortfall]:
        """
        For a near-miss rule, calculate exactly what would make it match.
        """
        pass

    def generate_learning_message(
        self,
        differential_factors: List[Dict],
        domain: str
    ) -> str:
        """
        Generate educational text based on the differential.
        Domain: 'lott' | 'positional' | 'control' | 'defensive'
        """
        pass
```

### 2.3 Differential Result Schema

```python
@dataclass
class DifferentialResult:
    user_bid: str
    optimal_bid: str
    rating: str  # "optimal", "acceptable", "suboptimal", "error"
    score: int   # 0-100

    # Rule matching analysis
    user_bid_rules: List[Dict]     # Rules that match user's bid
    optimal_bid_rules: List[Dict]  # Rules that match optimal bid

    # The differential
    differential_factors: List[DifferentialFactor]

    # Physics context
    physics_summary: PhysicsSummary

    # Educational output
    primary_reason: str            # One-sentence explanation
    learning_point: str            # What to learn
    diagnostic_domain: str         # "safety" | "value" | "control" | "tactical"

@dataclass
class DifferentialFactor:
    feature: str                   # e.g., "hcp", "lott_safe_level"
    user_value: Any                # What user had
    optimal_threshold: Any         # What optimal rule required
    gap: str                       # Human-readable gap
    impact: str                    # How this affected the bid

@dataclass
class PhysicsSummary:
    lott_safe_level: int
    working_hcp_ratio: float
    quick_tricks: float
    support_points: int
    control_multiplier: float
    is_fragile_ruff: bool
```

---

## 3. API Specification

### 3.1 Enhanced Evaluate-Bid Response

**Endpoint:** `POST /api/evaluate-bid` (existing, enhanced)

**Enhanced Response:**
```json
{
    "evaluation": {
        "rating": "suboptimal",
        "score": 65,
        "optimal_bid": "Pass",
        "user_bid": "3♠",
        "matched_rule": "competitive_raise_minimal",
        "commentary_html": "<strong>Analysis:</strong> Your 3♠ bid..."
    },

    "differential": {
        "user_bid_rules": [
            {
                "rule_id": "competitive_raise_minimal",
                "bid": "3♠",
                "conditions_met": 5,
                "conditions_total": 5
            }
        ],
        "optimal_bid_rules": [
            {
                "rule_id": "lott_safety_ceiling_pass",
                "bid": "Pass",
                "priority": 200,
                "why_it_wins": "Higher priority safety rule"
            }
        ],
        "factors": [
            {
                "feature": "lott_safe_level",
                "user_value": 2,
                "bid_level": 3,
                "gap": "Level 3 exceeds safe level 2",
                "impact": "Overbid by 1 level"
            }
        ]
    },

    "physics": {
        "lott_safe_level": 2,
        "working_hcp_ratio": 0.92,
        "quick_tricks": 1.5,
        "ssp_adjusted": 3,
        "control_multiplier": 1.0
    },

    "learning": {
        "domain": "safety",
        "primary_reason": "Your 8-card fit only supports bidding to level 2.",
        "hint": "The Law of Total Tricks limits safety based on combined fit length.",
        "tutorial_link": "/learn/lott"
    }
}
```

### 3.2 New Endpoint: Differential Analysis

**Endpoint:** `POST /api/differential-analysis` (NEW)

**Request:**
```json
{
    "user_bid": "3♠",
    "hand_cards": [...],
    "auction_history": ["1♠", "2♥", "Pass"],
    "position": "S",
    "vulnerability": "Both",
    "dealer": "N"
}
```

**Response:**
```json
{
    "optimal_bid": "Pass",
    "rating": "suboptimal",
    "score": 55,

    "differential": {
        "explanation": "Your bid matched a competitive raise rule, but a higher-priority safety rule recommends Pass.",
        "key_factor": "lott_safe_level",
        "user_bid_logic": "You saw 4-card support and bid competitively",
        "optimal_bid_logic": "With only 8-card combined fit, level 3 exceeds safety threshold"
    },

    "factors": [
        {
            "feature": "lott_safe_level",
            "label": "LoTT Safe Level",
            "actual": 2,
            "required_for_bid": 3,
            "status": "FAIL",
            "gap_description": "8-card fit = level 2 safety"
        },
        {
            "feature": "vulnerability",
            "label": "Vulnerability",
            "actual": "Both",
            "impact": "Increases penalty risk",
            "status": "WARNING"
        }
    ],

    "visual_data": {
        "success_map_coords": {"x": 65, "y": 45},
        "decay_markers": [
            {"trick": 8, "label": "LoTT ceiling exceeded", "potential_loss": 1}
        ]
    }
}
```

---

## 4. Frontend Integration

### 4.1 New Component: `DifferentialAnalysisPanel`

**Location:** `frontend/src/components/learning/DifferentialAnalysisPanel.jsx` (NEW)

**Purpose:** Visual comparison of user's bid vs optimal bid with rule matching

**Layout:**
```
┌─ Differential Analysis ─────────────────────────────────┐
│                                                          │
│  Your Bid: 3♠              Optimal: Pass                │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                          │
│  ┌─ Your Bid Matches ─────┐  ┌─ Optimal Bid Matches ──┐ │
│  │ ✓ competitive_raise    │  │ ✓ lott_safety_pass    │ │
│  │   Priority: 120        │  │   Priority: 200       │ │
│  │   5/5 conditions       │  │   3/3 conditions      │ │
│  └────────────────────────┘  └────────────────────────┘ │
│                                                          │
│  ┌─ Key Difference ─────────────────────────────────────┐│
│  │ LoTT Safe Level: 2     Your Bid Level: 3            ││
│  │ ████████░░░░░░░░       ████████████░░░░             ││
│  │ 8-card fit             9 tricks needed              ││
│  │                                                     ││
│  │ ⚠️ Overbid by 1 level                               ││
│  └─────────────────────────────────────────────────────┘│
│                                                          │
│  💡 With an 8-card fit, the Law of Total Tricks         │
│     recommends bidding only to level 2.                 │
└──────────────────────────────────────────────────────────┘
```

### 4.2 Enhanced BidFeedbackPanel Integration

**Modify:** `frontend/src/components/bridge/BidFeedbackPanel.jsx`

**Add:**
- "Why?" link that opens DifferentialAnalysisPanel
- Brief gap summary in the feedback text
- Color-coded feature delta indicators

### 4.3 DecayChart Integration

**Modify:** `frontend/src/components/analysis/DecayChart.jsx`

**Add:**
- Bidding context markers at trick positions
- "LoTT Ceiling Exceeded" labels on potential drops
- Link between bidding features and play failures

### 4.4 Success Map Enhancement

**Modify:** `frontend/src/components/learning/FourDimensionProgress.js`

**Add:**
- Diagnostic domain coloring (Safety=blue, Value=yellow, Control=orange)
- Hover tooltips showing the differential factor
- Clickable quadrant navigation to review

---

## 5. Diagnostic Domains

### 5.1 Domain Classification

| Domain | Feature Basis | Educational Focus |
|--------|---------------|-------------------|
| **Safety** | LoTT ceiling violations | Law of Total Tricks tutorial |
| **Value** | Positional/Working HCP | "Working Points" analyzer |
| **Control** | Ruffing/Trump quality | Trump control drill |
| **Tactical** | Preempt/Sacrifice | Tactical bidding guide |
| **Defensive** | Quick tricks, penalty | Defense tutorial |

### 5.2 Domain Detection Logic

```python
def classify_diagnostic_domain(differential_factors: List[Dict]) -> str:
    """Classify the primary learning domain for feedback."""

    for factor in differential_factors:
        feature = factor['feature']

        if feature in ['lott_safe_level', 'total_tricks_index', 'fit_length']:
            return 'safety'

        if feature in ['working_hcp_ratio', 'positional_waste', 'wasted_honors']:
            return 'value'

        if feature in ['control_multiplier', 'is_fragile_ruff', 'trump_quality']:
            return 'control'

        if feature in ['aggression_score', 'sacrifice_viable']:
            return 'tactical'

        if feature in ['quick_tricks', 'is_defensive_powerhouse']:
            return 'defensive'

    return 'general'
```

---

## 6. Implementation Roadmap

### Phase 1: Backend Differential Service (4-6 hours)

1. **Create `differential_analyzer.py`**
   - Implement `DifferentialAnalyzer` class
   - Rule comparison logic
   - Feature shortfall calculations
   - Learning message generation

2. **Create API endpoint**
   - `POST /api/differential-analysis`
   - Integrate with existing gap analysis
   - Return enhanced payload

3. **Enhance `/api/evaluate-bid`**
   - Add differential data to response
   - Add physics summary
   - Add learning domain classification

4. **Unit tests**
   - Test differential calculation
   - Test domain classification
   - Test message generation

### Phase 2: Frontend Components (4-6 hours)

1. **Create `DifferentialAnalysisPanel.jsx`**
   - Rule comparison view
   - Feature delta visualization
   - Learning point display

2. **Integrate with BidFeedbackPanel**
   - Add "Why?" expansion
   - Show brief differential summary

3. **Enhance BiddingGapAnalysis**
   - Highlight user's bid vs optimal
   - Color-code by domain

4. **CSS styling**
   - Match design standards
   - Responsive breakpoints
   - Accessibility

### Phase 3: Chart Integration (2-3 hours)

1. **DecayChart markers**
   - Add bidding context labels
   - Link potential drops to features

2. **Success Map enhancement**
   - Domain-based coloring
   - Hover tooltips

### Phase 4: Testing & Polish (2-3 hours)

1. **E2E tests**
   - Test feedback flow
   - Test modal interactions

2. **Quality baseline**
   - Verify no regression
   - Test edge cases

3. **Documentation**
   - Update CLAUDE.md
   - Add feature docs

---

## 7. Example Walkthrough

### Scenario

**Hand:** ♠AKQ32 ♥K87 ♦J9 ♣T65 (12 HCP)
**Auction:** Pass - 1♠ - 2♥ - ?
**User bids:** 3♠ (competitive raise)
**AI would bid:** Pass (LoTT safety)

### Differential Analysis

```json
{
    "user_bid": "3♠",
    "optimal_bid": "Pass",
    "rating": "suboptimal",
    "score": 55,

    "differential": {
        "explanation": "Your 3♠ bid matches a competitive raise pattern, but the LoTT safety ceiling recommends Pass.",
        "key_factor": "lott_safe_level"
    },

    "user_bid_rules": [
        {
            "rule_id": "competitive_raise_3_level",
            "bid": "3♠",
            "priority": 120,
            "conditions_met": 5,
            "conditions_total": 5,
            "status": "MATCHED"
        }
    ],

    "optimal_bid_rules": [
        {
            "rule_id": "lott_safety_ceiling_pass",
            "bid": "Pass",
            "priority": 200,
            "conditions_met": 3,
            "conditions_total": 3,
            "status": "MATCHED",
            "why_it_wins": "Higher priority (200 > 120)"
        }
    ],

    "factors": [
        {
            "feature": "lott_safe_level",
            "label": "Law of Total Tricks Safe Level",
            "actual": 2,
            "required_for_3_level": 3,
            "status": "FAIL",
            "gap": "8-card fit supports level 2, not level 3"
        },
        {
            "feature": "vulnerability",
            "label": "Vulnerability Status",
            "actual": "Both",
            "status": "WARNING",
            "impact": "Increases penalty risk"
        }
    ],

    "physics": {
        "combined_fit_length": 8,
        "lott_safe_level": 2,
        "working_hcp_ratio": 0.92,
        "quick_tricks": 1.5
    },

    "learning": {
        "domain": "safety",
        "primary_reason": "Your 8-card fit only supports bidding to level 2.",
        "hint": "Law of Total Tricks: Fit Length - 6 = Safe Level. With 8-card fit, that's level 2.",
        "tutorial_link": "/learn/lott"
    }
}
```

### Frontend Display

```
┌─ Bid Feedback ─────────────────────────────────────────┐
│                                                         │
│  Your Bid: 3♠  →  Suboptimal (Score: 55)               │
│  Optimal Bid: Pass                                      │
│                                                         │
│  ⚠️ LoTT Safety Violation                              │
│  Your 8-card fit supports level 2, but you bid level 3 │
│                                                         │
│  [Why?]  [Show Gap Analysis]                           │
│                                                         │
│  💡 Law of Total Tricks: Fit Length - 6 = Safe Level   │
└─────────────────────────────────────────────────────────┘
```

---

## 8. Files to Create/Modify

### New Files

| File | Purpose |
|------|---------|
| `backend/engine/v2/differential_analyzer.py` | Core differential service |
| `frontend/src/components/learning/DifferentialAnalysisPanel.jsx` | Visual differential display |
| `frontend/src/components/learning/DifferentialAnalysisPanel.css` | Styling |
| `frontend/src/hooks/useDifferentialAnalysis.js` | React hook for fetching/processing |
| `backend/tests/unit/test_differential_analyzer.py` | Unit tests |

### Modified Files

| File | Changes |
|------|---------|
| `backend/engine/learning/analytics_api.py` | Add `/api/differential-analysis` endpoint |
| `backend/server.py` | Register new endpoint |
| `frontend/src/components/bridge/BidFeedbackPanel.jsx` | Add differential integration |
| `frontend/src/components/learning/BiddingGapAnalysis.js` | Enhance with user/optimal comparison |
| `frontend/src/components/analysis/DecayChart.jsx` | Add bidding context markers |
| `frontend/src/components/learning/FourDimensionProgress.js` | Add domain coloring |

---

## 9. Success Criteria

### Functional

- [ ] Differential analysis correctly identifies rule matches for user bid
- [ ] Differential analysis correctly identifies rule matches for optimal bid
- [ ] Feature shortfalls are calculated accurately
- [ ] Diagnostic domain is classified correctly
- [ ] Learning messages are educational and actionable

### UI/UX

- [ ] DifferentialAnalysisPanel renders correctly at all breakpoints
- [ ] BidFeedbackPanel shows brief differential summary
- [ ] DecayChart shows bidding context markers
- [ ] Success Map uses domain-based coloring
- [ ] All components pass accessibility checks

### Performance

- [ ] API response time < 200ms for differential analysis
- [ ] No regression in bidding quality scores
- [ ] No new console errors or warnings

### Educational Value

- [ ] Users understand why their bid differs from optimal
- [ ] Learning points are connected to specific features
- [ ] Tutorial links are relevant to the domain

---

## 10. Dependencies

- Existing `enhanced_extractor.py` (no changes needed)
- Existing `SchemaInterpreter.get_rule_gap_analysis()` (no changes needed)
- Existing `/api/bidding-gap-analysis` endpoint (no changes needed)
- Existing `BiddingGapAnalysis.js` component (minor enhancements)

---

## Appendix A: Feature-to-Hint Mapping

```python
FEATURE_HINTS = {
    'lott_safe_level': {
        'domain': 'safety',
        'hint_template': "Law of Total Tricks: Your {fit_length}-card fit supports level {safe_level}.",
        'tutorial': '/learn/lott'
    },
    'working_hcp_ratio': {
        'domain': 'value',
        'hint_template': "Only {ratio}% of your HCP are 'working' in useful suits.",
        'tutorial': '/learn/working-points'
    },
    'quick_tricks': {
        'domain': 'defensive',
        'hint_template': "With {qt} Quick Tricks, you have strong defensive potential.",
        'tutorial': '/learn/quick-tricks'
    },
    'control_multiplier': {
        'domain': 'control',
        'hint_template': "Your trump {quality} affects the value of shortness.",
        'tutorial': '/learn/trump-control'
    },
    'is_fragile_ruff': {
        'domain': 'control',
        'hint_template': "Weak trumps make your shortness vulnerable to over-ruffs.",
        'tutorial': '/learn/ruffing-value'
    }
}
```

---

## Appendix B: Priority System Reference

| Priority Range | Category | Example Rules |
|----------------|----------|---------------|
| 200-250 | Hard Stops | `PENALTY_POWERHOUSE_DOUBLE`, `LOTT_SAFETY_CEILING_PASS` |
| 170-199 | Strategic Filters | `MISFIT_WASTED_VALUE_PASS`, `FRAGILE_TRUMP_CAUTION` |
| 140-169 | Standard Bids | Game raises, slam tries, competitive actions |
| 100-139 | Positional | Overcalls, balancing, interference |
| 50-99 | Tactical | Preempts, sacrifices, obstructive bids |
| 1-49 | Fallback | Default passes, forced bids |

---

**Document Status:** Ready for Implementation
**Next Step:** Create `differential_analyzer.py` service

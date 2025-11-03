# BRIDGE BIDDING ARCHITECTURE - EXECUTIVE SUMMARY

**Document Created:** 2025-10-29
**Detailed Map Location:** `/Users/simonroy/Desktop/bridge_bidding_app/BIDDING_ARCHITECTURE_MAP.md`
**Map Length:** 968 lines, comprehensive coverage
**Related ADR:** [ADR-0002: Bidding System Robustness Improvements](docs/architecture/decisions/ADR-0002-bidding-system-robustness-improvements.md)

> **Architecture Status:** Proposed improvements in ADR-0002 to address system errors, validation bypasses, and runaway auctions through 4-layer robustness enhancements.

---

## QUICK REFERENCE

### HTTP Request Flow
```
Frontend → /api/get-next-bid → server.py → BiddingEngine.get_next_bid() 
→ extract_features() + select_bidding_module() + specialist.evaluate() 
→ _is_bid_legal() → return (bid, explanation)
```

### 15 Total Modules (All Registered in BiddingEngine)

**6 Natural Specialists:**
1. OpeningBidsModule - opening_bids.py
2. ResponseModule - responses.py
3. RebidModule - rebids.py
4. ResponderRebidModule - responder_rebids.py
5. AdvancerBidsModule - advancer_bids.py
6. OvercallModule - overcalls.py

**9 Convention Specialists:**
7. PreemptConvention - conventions/preempts.py
8. StaymanConvention - conventions/stayman.py
9. JacobyConvention - conventions/jacoby_transfers.py
10. BlackwoodConvention - conventions/blackwood.py
11. SplinterBidsConvention - conventions/splinter_bids.py
12. FourthSuitForcingConvention - conventions/fourth_suit_forcing.py
13. TakeoutDoubleConvention - conventions/takeout_doubles.py
14. NegativeDoubleConvention - conventions/negative_doubles.py
15. MichaelsCuebidConvention - conventions/michaels_cuebid.py
16. Unusual2NTConvention - conventions/unusual_2nt.py

---

## CORE ARCHITECTURE

### 1. BiddingEngine (Master Orchestrator)
**File:** `backend/engine/bidding_engine.py`

```python
class BiddingEngine:
    def __init__(self):
        self.modules = {15 specialist modules registered as strings}
    
    def get_next_bid(hand, auction_history, my_position, vulnerability):
        1. extract_features() → contextual data
        2. select_bidding_module(features) → module name (string)
        3. specialist = self.modules[module_name]
        4. result = specialist.evaluate(hand, features)
        5. _is_bid_legal(result) → validation
        6. Return (bid, explanation) or Pass
```

### 2. Decision Engine (Module Selection)
**File:** `backend/engine/ai/decision_engine.py`

**State-based routing:**
- STATE 1: Opening (no one bid yet) → PreemptConvention or OpeningBidsModule
- STATE 2: Competitive (opponent opened) → AdvancerBidsModule, OvercallModule, or Doubles
- STATE 3: Partnership (partner opened) → ResponseModule, ResponderRebidModule, or Conventions
- STATE 4: I Opened (rebid) → RebidModule or Conventions
- STATE 5: Default → 'pass_by_default'

### 3. Feature Extraction
**File:** `backend/engine/ai/feature_extractor.py`

**extract_features() returns comprehensive dict:**
```python
{
    'hand_features': {hcp, dist_points, total_points, suit_lengths, is_balanced},
    'auction_features': {opening_bid, opener, opener_relationship, partner_bids, interference},
    'auction_history': list of bids,
    'hand': Hand object,
    'my_index': position (0-3),
    'positions': ['North', 'East', 'South', 'West']
}
```

**Opener Relationship Values:**
- 'Me' - I opened
- 'Partner' - Partner opened
- 'Opponent' - Opponent opened
- None - No one opened yet

### 4. Base Class (All Modules)
**File:** `backend/engine/ai/conventions/base_convention.py`

```python
class ConventionModule(ABC):
    @abstractmethod
    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Return (bid_string, explanation_string) or None"""
        pass
    
    def get_constraints(self) -> Dict:
        """Optional: for hand generation in scenarios"""
        return {}
```

### 5. Validation Layers

#### Level 1: Auction Rules (BidValidator)
**File:** `backend/engine/bidding_validation.py`

- Pass/X/XX always legal
- Suits: ♣(1) < ♦(2) < ♥(3) < ♠(4) < NT(5)
- Bid legal if: level higher OR (same level AND suit ranking higher)

#### Level 2: Module Internal Validation
- HCP ranges (e.g., overcalls 8-16 HCP)
- Suit requirements (e.g., 5+ for opening suits)
- Special checks (e.g., suit quality for preempts)

#### Level 3: Universal Legality Check (BiddingEngine._is_bid_legal)
- Final safety net after specialist returns bid
- Prevents modules from suggesting illegal bids

#### Level 4: Bid Appropriateness (BidSafety)
**File:** `backend/engine/bid_safety.py`

- Prevents semantic errors (7NT with 27 HCP)
- Checks slam point requirements
- Validates trumpet support

---

## KEY DECISION POINTS

### Advancer Detection (Decision Engine, Lines 32-39)
```python
if (partner_last_bid and partner_last_bid not in ['Pass', 'XX'] and 
    len(my_bids) == 0):
    return 'advancer_bids'
```
**Critical:** Partner must have bid, I must not have bid yet

### Preempt Priority (Decision Engine, Lines 24-28)
```python
if not opener:
    if PreemptConvention().evaluate(...):
        return 'preempts'
    return 'opening_bids'
```
**Critical:** Preempts checked BEFORE natural openings

### 1NT Convention Priority (Decision Engine, Lines 115-119)
```python
if opening_bid == '1NT':
    if jacoby.evaluate(...): return 'jacoby'
    if stayman.evaluate(...): return 'stayman'
```
**Critical:** Conventions checked before natural responses

### Balancing Seat (Decision Engine, Lines 58-68)
```python
if len(auction_history) >= 2 and auction_history[-1] == 'Pass' and auction_history[-2] == 'Pass':
    # Check overcalls/doubles in balancing seat
```
**Critical:** Different point requirements than direct seat

---

## POINT REQUIREMENTS QUICK REFERENCE

| Module | Minimum Points | Maximum Points | Notes |
|--------|---|---|---|
| **Opening Bid** | 13 total | ∞ | With distribution |
| **Response** | 6 total | ∞ | Minimum responding |
| **1NT Overcall (Direct)** | 15 HCP | 18 HCP | Stopper required |
| **1NT Overcall (Balancing)** | 12 HCP | 15 HCP | Lighter |
| **Suit Overcall (Direct, 1-level)** | 8 HCP | 16 HCP | Suit quality |
| **Suit Overcall (2-level)** | 11 HCP | 16 HCP | Stronger suit |
| **Takeout Double** | 12 HCP | ∞ | + distribution check |
| **Strong Takeout Double** | 19 HCP | ∞ | Balanced (plan 1NT rebid) |
| **Negative Double (1-2 level)** | 6 HCP | ∞ | Responding values |
| **Negative Double (3-level)** | 8 HCP | ∞ | Invitational values |
| **Negative Double (4+ level)** | 12 HCP | ∞ | Game-forcing values |
| **Preempt (Weak 2)** | 6 HCP | 10 HCP | + suit quality (2 of A/K/Q) |
| **Preempt (3-level)** | 6 HCP | 10 HCP | + 2+ honors |
| **Stayman** | 7 HCP | ∞ | Response to 1NT |
| **Jacoby** | Any | ∞ | 5+ major, response to 1NT |
| **Blackwood** | 15 HCP (typical) | ∞ | Slam interest |
| **Simple Raise** | 8 HCP | 10 HCP | 3+ card support |
| **Jump Raise** | 11 HCP | 12 HCP | Invitational |

---

## MODULE CHARACTERISTICS

### Natural Modules (No Conventional Structure)
- **Behavior:** Directly evaluate hand against bidding rules
- **Return:** (bid_string, explanation_string)
- **Validation:** Built-in legality checks + adjustment logic
- **Examples:** OpeningBidsModule, ResponseModule, RebidModule

### Convention Modules (Conditional Activation)
- **Behavior:** Check if convention applies, then bid
- **Return:** (bid_string, explanation_string) or None if not applicable
- **Validation:** Some include checks (preempt suit quality)
- **Applicability Check:** Look at auction features (opening_bid, interference, etc.)
- **Examples:** StaymanConvention (only if partner opened 1NT), PreemptConvention (only if opening)

---

## KNOWN ISSUES & FIXES

### ✅ Fixed Issues

1. **Advancer Registration** - AdvancerBidsModule properly registered and routed
2. **Bid Legality Adjustment** - 2-level max check prevents runaway escalation
3. **Negative Double HCP** - Level-dependent requirements implemented
4. **Takeout Double Range** - 12+ HCP minimum, 19+ balanced special case
5. **Preempt Suit Quality** - SAYC strict: 2 of top 3 honors for weak 2s
6. **Opening Balance vs 2♣** - Balanced hands checked before 2♣ strong opening
7. **Responder Rebid Safety** - Prevents under-bidded slams (< 18 HCP at 5-level)

### ⚠️ Partial Issues (Need Monitoring)

1. **Bid Adjustment Point Checks** - BidSafety exists but not always used after adjustment
2. **Trump Support Validation** - Suit contracts need sufficient trump, not always checked post-adjustment

---

## FILE LOCATIONS - COMPLETE MAP

### Core Engine
- `/backend/engine/bidding_engine.py` - Master orchestrator (15 modules)
- `/backend/engine/ai/decision_engine.py` - Module selection (state machine)
- `/backend/engine/ai/feature_extractor.py` - Feature extraction + interference detection
- `/backend/engine/ai/conventions/base_convention.py` - Base class (ABC)

### Bidding Validation
- `/backend/engine/bidding_validation.py` - BidValidator class (legality)
- `/backend/engine/bid_safety.py` - BidSafety class (appropriateness)

### Natural Specialists (6 modules)
- `/backend/engine/opening_bids.py` - OpeningBidsModule
- `/backend/engine/responses.py` - ResponseModule
- `/backend/engine/rebids.py` - RebidModule
- `/backend/engine/responder_rebids.py` - ResponderRebidModule
- `/backend/engine/advancer_bids.py` - AdvancerBidsModule
- `/backend/engine/overcalls.py` - OvercallModule

### Convention Specialists (9 modules)
- `/backend/engine/ai/conventions/preempts.py` - PreemptConvention
- `/backend/engine/ai/conventions/stayman.py` - StaymanConvention
- `/backend/engine/ai/conventions/jacoby_transfers.py` - JacobyConvention
- `/backend/engine/ai/conventions/blackwood.py` - BlackwoodConvention
- `/backend/engine/ai/conventions/splinter_bids.py` - SplinterBidsConvention
- `/backend/engine/ai/conventions/fourth_suit_forcing.py` - FourthSuitForcingConvention
- `/backend/engine/ai/conventions/takeout_doubles.py` - TakeoutDoubleConvention
- `/backend/engine/ai/conventions/negative_doubles.py` - NegativeDoubleConvention
- `/backend/engine/ai/conventions/michaels_cuebid.py` - MichaelsCuebidConvention
- `/backend/engine/ai/conventions/unusual_2nt.py` - Unusual2NTConvention

### Supporting Systems
- `/backend/engine/hand.py` - Hand class (13 cards, auto-calculate properties)
- `/backend/engine/ai/bid_explanation.py` - BidExplanation class (rich explanations)
- `/backend/server.py` - Flask endpoints (/api/get-next-bid, /api/evaluate-bid)

### Frontend
- `/frontend/src/services/api.js` - API client for bidding endpoints
- `/frontend/src/App.js` - Main React app using bidding engine

---

## TESTING & VALIDATION

### Quality Score Testing
```bash
# Before any bidding changes:
python3 backend/test_bidding_quality_score.py --hands 500 --output baseline_before.json
# [make changes]
python3 backend/test_bidding_quality_score.py --hands 500 --output baseline_after.json
python3 compare_scores.py baseline_before.json baseline_after.json
```

### Requirements
- ✅ Legality: 100% (no illegal bids)
- ✅ Appropriateness: ≥ baseline (no regression)
- ✅ Composite: ≥ baseline - 2% (small tolerance)

### Current Baseline (500 hands, 3,013 bids)
```
Legality:        100.0% ✅
Appropriateness:  78.7% (improvement area)
Conventions:      99.7% ✅
Reasonableness:   92.1% ✅
Composite:        89.7% (Grade C)
```

---

## HOW TO ADD A NEW CONVENTION

1. **Create file** in `/backend/engine/ai/conventions/CONVENTION_NAME.py`
2. **Extend ConventionModule:**
   ```python
   from engine.ai.conventions.base_convention import ConventionModule
   
   class NewConvention(ConventionModule):
       def evaluate(self, hand, features):
           if <condition_applies>:
               return (bid, explanation)
           return None
   ```
3. **Register in BiddingEngine.__init__():**
   ```python
   'convention_key': NewConvention(),
   ```
4. **Add decision logic in decision_engine.py:**
   ```python
   if <appropriate_state>:
       if new_convention.evaluate(...): 
           return 'convention_key'
   ```
5. **Run baseline quality score before commit**

---

## COMMON DEBUGGING SCENARIOS

### "AI Bid is Never Suggested"
1. Check if module is registered in BiddingEngine (line 27-44)
2. Check if decision engine routes to it (decision_engine.py)
3. Check internal conditions in module.evaluate()
4. Verify features dict has required fields (use extract_features debugging)

### "AI Suggests Illegal Bid"
1. Check module's internal validation (HCP/suit checks)
2. Check BidValidator.is_legal_bid() logic
3. Check BiddingEngine._is_bid_legal() enforcement
4. May need to adjust module's bid generation logic

### "Bid Gets Adjusted Incorrectly"
1. Check 2-level max escalation logic in module
2. Check get_next_legal_bid() function
3. May need BidSafety check after adjustment
4. Check module's sanity check (usually around line 40-55)

### "Wrong Module Selected"
1. Debug extract_features() to see auction_features
2. Check opener_relationship value
3. Trace decision_engine logic path
4. Add print statements to decision_engine.py

---

## QUICK DEBUGGING ADDITIONS

```python
# In server.py or module evaluate() method:

# Print feature extraction
print(f"Features: opener={features['auction_features']['opener']}, " +
      f"relationship={features['auction_features']['opener_relationship']}")

# Print module selection
print(f"Selected module: {module_name}")

# Print bid validation
print(f"Bid {bid} legal? {self._is_bid_legal(bid, auction_history)}")

# Print hand evaluation
print(f"Hand: {hand.hcp} HCP, {hand.suit_lengths}, balanced={hand.is_balanced}")
```

---

## REFERENCES

- **Full Architecture Map:** `/Users/simonroy/Desktop/bridge_bidding_app/BIDDING_ARCHITECTURE_MAP.md` (968 lines)
- **Project Instructions:** `/Users/simonroy/Desktop/bridge_bidding_app/CLAUDE.md`
- **Coding Guidelines:** `/Users/simonroy/Desktop/bridge_bidding_app/.claude/CODING_GUIDELINES.md`


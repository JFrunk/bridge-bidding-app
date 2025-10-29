# BRIDGE BIDDING ARCHITECTURE - COMPREHENSIVE MAP

**Document Version:** 1.0
**Last Updated:** 2025-10-29
**Codebase:** /Users/simonroy/Desktop/bridge_bidding_app

**Related ADR:** [ADR-0002: Bidding System Robustness Improvements](docs/architecture/decisions/ADR-0002-bidding-system-robustness-improvements.md)

> **Note:** This architecture is currently undergoing robustness improvements to address system errors and validation bypasses. See ADR-0002 for planned changes including module registry pattern, centralized validation pipeline, sanity checks, and improved error handling.

---

## TABLE OF CONTENTS

1. [High-Level Request Flow](#high-level-request-flow)
2. [API Entry Points](#api-entry-points)
3. [Core Bidding Engine](#core-bidding-engine)
4. [Module Hierarchy & Registration](#module-hierarchy--registration)
5. [Decision Engine (Module Selection)](#decision-engine-module-selection)
6. [Specialist Modules](#specialist-modules)
7. [Validation & Legality Checking](#validation--legality-checking)
8. [Feature Extraction System](#feature-extraction-system)
9. [Bid Explanation System](#bid-explanation-system)
10. [Known Issues & Error Patterns](#known-issues--error-patterns)
11. [Data Flow Diagrams](#data-flow-diagrams)

---

## HIGH-LEVEL REQUEST FLOW

```
FRONTEND (React)
    ↓
[HTTP POST to /api/get-next-bid or /api/evaluate-bid]
    ↓
SERVER.PY (Flask)
    ↓
BiddingEngine.get_next_bid() or get_next_bid_structured()
    ↓
1. extract_features() → features dict
2. select_bidding_module() → module name
3. Get specialist from modules dict
4. specialist.evaluate(hand, features) → (bid, explanation)
5. _is_bid_legal() → validation check
6. Return (bid, explanation) or Pass
    ↓
[HTTP Response with bid, explanation, rating]
    ↓
FRONTEND receives and updates UI
```

---

## API ENTRY POINTS

**File:** `/Users/simonroy/Desktop/bridge_bidding_app/backend/server.py`

### 1. `/api/get-next-bid` [POST]
- **Purpose:** Get AI's next bid (string explanation)
- **Input:** `{ hand_for_X: [...], auction_history: [...], current_player: str, vulnerability: str, explanation_level?: str }`
- **Output:** `{ bid: str, explanation: str }`
- **Process:**
  1. Calls `BiddingEngine.get_next_bid()`
  2. Returns formatted explanation string
  3. Formats to requested level: "simple", "detailed", "expert"

### 2. `/api/get-next-bid-structured` [POST]
- **Purpose:** Get AI's next bid (JSON explanation)
- **Input:** Same as above
- **Output:** `{ bid: str, explanation_dict: { bid, primary_reason, rules, alternatives, ... } }`
- **Process:**
  1. Calls `BiddingEngine.get_next_bid_structured()`
  2. Returns structured BidExplanation.to_dict()
  3. Better for analysis and UI rich explanations

### 3. `/api/evaluate-bid` [POST]
- **Purpose:** Evaluate user's bid against optimal bid
- **Input:** `{ user_bid: str, auction_before_bid: [...], hand_for_south: [...], current_player: str, vulnerability: str, ... }`
- **Output:** `{ optimal_bid: str, user_bid: str, score: 0-10, correctness: enum, feedback: str }`
- **Process:**
  1. Gets user's bid
  2. Gets optimal bid from engine
  3. Compares and calculates score
  4. Stores in bidding_decisions table
  5. Returns evaluation

---

## CORE BIDDING ENGINE

**File:** `/Users/simonroy/Desktop/bridge_bidding_app/backend/engine/bidding_engine.py`

### Class: `BiddingEngine`

```python
class BiddingEngine:
    def __init__(self):
        self.modules = {
            'opening_bids': OpeningBidsModule(),
            'responses': ResponseModule(),
            'openers_rebid': RebidModule(),
            'responder_rebid': ResponderRebidModule(),
            'advancer_bids': AdvancerBidsModule(),
            'overcalls': OvercallModule(),
            'stayman': StaymanConvention(),
            'jacoby': JacobyConvention(),
            'preempts': PreemptConvention(),
            'blackwood': BlackwoodConvention(),
            'takeout_doubles': TakeoutDoubleConvention(),
            'negative_doubles': NegativeDoubleConvention(),
            'michaels_cuebid': MichaelsCuebidConvention(),
            'unusual_2nt': Unusual2NTConvention(),
            'splinter_bids': SplinterBidsConvention(),
            'fourth_suit_forcing': FourthSuitForcingConvention(),
        }
```

### Key Methods:

#### `get_next_bid(hand, auction_history, my_position, vulnerability, explanation_level)`
1. Extracts features from hand and auction
2. Selects module via decision engine
3. Gets bid from specialist
4. Performs universal legality check
5. Returns (bid, explanation) - formatted as string

#### `get_next_bid_structured(hand, auction_history, my_position, vulnerability)`
- Same as above but returns explanation as dict/BidExplanation object

#### `_is_bid_legal(bid, auction_history)`
- **Universal legality enforcement**
- Checks: Pass/X/XX always legal
- Finds last non-Pass bid in auction
- Compares: bid level > last level OR (same level AND suit ranking > last suit)
- Suit ranking: ♣(1) < ♦(2) < ♥(3) < ♠(4) < NT(5)

---

## MODULE HIERARCHY & REGISTRATION

### Base Class: `ConventionModule` (ABC)

**File:** `/Users/simonroy/Desktop/bridge_bidding_app/backend/engine/ai/conventions/base_convention.py`

```python
class ConventionModule(ABC):
    @abstractmethod
    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Return (bid, explanation) or None"""
        pass
    
    def get_constraints(self) -> Dict:
        """Optional: Hand generation constraints for scenarios"""
        return {}
```

### Module Registration Flow

1. **Specialist created in BiddingEngine.__init__()**
2. **Stored in self.modules dict with string key**
3. **Decision engine returns string key (e.g., 'opening_bids')**
4. **BiddingEngine retrieves via: `self.modules.get(module_name)`**

### All Modules (15 total)

#### NATURAL BIDDING SPECIALISTS (non-convention)
| Module | File | Applies When |
|--------|------|--------------|
| **OpeningBidsModule** | opening_bids.py | Opponent hasn't bid yet |
| **ResponseModule** | responses.py | Partner opened, responding (1st bid) |
| **RebidModule** | rebids.py | I opened, responding to partner |
| **ResponderRebidModule** | responder_rebids.py | Partner opened, responding (2nd+ bid) |
| **AdvancerBidsModule** | advancer_bids.py | Partner overcalled, advancing |
| **OvercallModule** | overcalls.py | Opponent opened, overcalling |

#### CONVENTION SPECIALISTS
| Convention | File | Applies When |
|-----------|------|--------------|
| **PreemptConvention** | conventions/preempts.py | Opening weak 2s, 3s, 4s; preemptive responses |
| **StaymanConvention** | conventions/stayman.py | Responding to 1NT; asking for majors |
| **JacobyConvention** | conventions/jacoby_transfers.py | Responding to 1NT; major suit transfers |
| **BlackwoodConvention** | conventions/blackwood.py | Slam seeking; ace inquiry (4NT) |
| **SplinterBidsConvention** | conventions/splinter_bids.py | Jump showing short suit + fit + slam interest |
| **FourthSuitForcingConvention** | conventions/fourth_suit_forcing.py | Bidding unbid 4th suit to force |
| **TakeoutDoubleConvention** | conventions/takeout_doubles.py | Double of opponent's suit showing takeout |
| **NegativeDoubleConvention** | conventions/negative_doubles.py | Double after opponent's interference |
| **MichaelsCuebidConvention** | conventions/michaels_cuebid.py | Cuebid showing 5-5 two suits |
| **Unusual2NTConvention** | conventions/unusual_2nt.py | 2NT showing 5-5 minors |

---

## DECISION ENGINE (MODULE SELECTION)

**File:** `/Users/simonroy/Desktop/bridge_bidding_app/backend/engine/ai/decision_engine.py`

### Function: `select_bidding_module(features) → str`

**Core Logic:** State-based routing with priority order

### STATE 1: Opening Situation (No one has bid yet)
```python
if not auction['opener']:
    # Priority: Check preempts FIRST
    if PreemptConvention().evaluate(hand, features):
        return 'preempts'
    return 'opening_bids'
```

### STATE 2: Competitive Situation (Opponent opened)
```python
if auction['opener_relationship'] == 'Opponent':
    # Sub-case A: Partner made overcall/double → I'm advancer
    if (partner_last_bid and partner_last_bid not in ['Pass', 'XX'] and 
        len(my_bids) == 0):
        return 'advancer_bids'
    
    # Sub-case B: First bid after opponent opened
    if len(my_bids) == 0:
        # Check conventions in order
        if MichaelsCuebidConvention().evaluate(...): return 'michaels_cuebid'
        if Unusual2NTConvention().evaluate(...): return 'unusual_2nt'
        if OvercallModule().evaluate(...): return 'overcalls'
        if TakeoutDoubleConvention().evaluate(...): return 'takeout_doubles'
    
    # Sub-case C: Subsequent bids (balancing, competitive)
    # ... try same modules again
```

### STATE 3: Partnership Auction (Partner opened)
```python
if auction['opener_relationship'] == 'Partner':
    # Check if responder's 2nd+ bid
    my_bids_after_opening = [bid for i, bid in enumerate(auction_history)
                              if (i % 4) == my_index and i > opener_index]
    if len(my_bids_after_opening) >= 1:
        return 'responder_rebid'
    
    # Check slam conventions first
    if BlackwoodConvention().evaluate(...): return 'blackwood'
    if SplinterBidsConvention().evaluate(...): return 'splinter_bids'
    if FourthSuitForcingConvention().evaluate(...): return 'fourth_suit_forcing'
    if NegativeDoubleConvention().evaluate(...): return 'negative_doubles'
    
    # Check 1NT conventions
    if opening_bid == '1NT':
        if JacobyConvention().evaluate(...): return 'jacoby'
        if StaymanConvention().evaluate(...): return 'stayman'
    
    # Default to natural responses
    return 'responses'
```

### STATE 4: I Opened (rebid situation)
```python
if auction['opener_relationship'] == 'Me':
    # Check 1NT convention completions first
    if opening_bid == '1NT':
        if JacobyConvention().evaluate(...): return 'jacoby'
        if StaymanConvention().evaluate(...): return 'stayman'
    
    # Check slam conventions
    if BlackwoodConvention().evaluate(...): return 'blackwood'
    
    # Default to natural rebids
    return 'openers_rebid'
```

### STATE 5: Default (no module matched)
```python
return 'pass_by_default'
```

---

## SPECIALIST MODULES

### All Modules Implement Same Interface

```python
def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
    """
    Returns:
        (bid_string, explanation) - (str, str) or (str, BidExplanation)
        None - if module doesn't apply
    """
```

### Key Design Pattern: Internal vs External Methods

**External:** `evaluate(hand, features)` - called by decision engine
- Performs bid legality validation
- Tries to adjust illegal bids
- Implements sanity checks (2-level max adjustment)

**Internal:** `_evaluate_XXXXX(hand, features)` - raw bid logic
- Returns bid without validation
- Called by evaluate() before legality check

### Example: AdvancerBidsModule

**File:** `/Users/simonroy/Desktop/bridge_bidding_app/backend/engine/advancer_bids.py`

```python
def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
    # Get raw suggestion
    result = self._evaluate_advance(hand, features)
    if not result: return None
    
    bid, explanation = result
    
    # Validate legality
    if BidValidator.is_legal_bid(bid, features['auction_history']):
        return result
    
    # Try adjustment
    next_legal = get_next_legal_bid(bid, features['auction_history'])
    if next_legal:
        # SANITY CHECK: max 2-level adjustment
        if int(next_legal[0]) - int(bid[0]) > 2:
            return ("Pass", "Cannot make reasonable bid...")
        return (next_legal, f"{explanation} [Adjusted to {next_legal}]")
    
    return None
```

### Point Requirements by Module

#### Overcalls (OvercallModule)
- **Direct seat, 1-level:** 8-16 HCP
- **Direct seat, 2-level:** 11-16 HCP
- **Balancing seat:** 7-16 HCP (lighter)
- **1NT overcall (direct):** 15-18 HCP
- **1NT overcall (balancing):** 12-15 HCP

#### Takeout Doubles (TakeoutDoubleConvention)
- **Minimum:** 12+ HCP
- **Special:** 19+ HCP balanced (double then bid NT next)
- **Requirements:** 0-2 cards in opponent's suit, 3+ cards in each unbid suit

#### Negative Doubles (NegativeDoubleConvention)
- **Through 2-level overcall:** 6+ HCP
- **3-level overcall:** 8-10 HCP
- **4-level+ overcall:** 12+ HCP

#### Advancer Bids (AdvancerBidsModule)
- **Simple raise (3+ cards):** 8-10 HCP
- **Jump raise (3+ cards):** 11-12 HCP invitational
- **Cuebid (fit):** 12+ HCP game-forcing
- **New suit:** 8+ HCP with 5+ card suit

#### Preempts (PreemptConvention)
- **2-level (6 cards):** 6-10 HCP, 2 of top 3 honors (SAYC strict)
- **3-level (7 cards):** 6-10 HCP, 2+ honors
- **4-level (8 cards):** 6-10 HCP, 2+ honors

#### Responses (ResponseModule)
- **Minimum:** 6 total points
- **Support points with fit:** +1 per doubleton, +3 per void
- **Level-specific:**
  - 1-level response: 6+ points
  - 2-level response: 10+ points
  - Jump to game: 13+ points with fit

---

## VALIDATION & LEGALITY CHECKING

### 1. Bid Legality (Auction Rules)

**File:** `/Users/simonroy/Desktop/bridge_bidding_app/backend/engine/bidding_validation.py`

#### BidValidator Class

```python
class BidValidator:
    SUIT_RANK = {'♣': 1, '♦': 2, '♥': 3, '♠': 4, 'NT': 5}
    
    @staticmethod
    def is_legal_bid(bid: str, auction: List[str]) -> bool:
        # Pass, X, XX always legal
        if bid in ['Pass', 'X', 'XX']: return True
        
        # Get minimum legal bid from auction
        min_legal = get_minimum_legal_bid(auction)
        if not min_legal: return True  # Opening position
        
        min_level, min_strain = min_legal
        
        # Parse proposed bid
        bid_level, bid_strain = int(bid[0]), bid[1:]
        
        # Higher level always legal
        if bid_level > min_level: return True
        
        # Same level - check suit ranking
        if bid_level == min_level:
            return SUIT_RANK[bid_strain] >= SUIT_RANK[min_strain]
        
        return False
```

#### Functions:
- **`is_legal_bid(bid, auction)`** - Check if single bid is legal
- **`get_minimum_legal_bid(auction)`** - Get (level, strain) that must be beaten
- **`get_next_legal_bid(target, auction)`** - Find next legal bid of same strain
- **`filter_legal_bids(candidates, auction)`** - Filter list to legal ones
- **`compare_bids(bid1, bid2)`** - Compare bid precedence

### 2. Universal Legality Check (BiddingEngine)

**Location:** `BiddingEngine._is_bid_legal()`

```python
def _is_bid_legal(self, bid: str, auction_history: list) -> bool:
    if bid in ['Pass', 'X', 'XX']: return True
    
    last_real_bid = next((b for b in reversed(auction_history) 
                         if b not in ['Pass', 'X', 'XX']), None)
    if not last_real_bid: return True
    
    try:
        my_level, my_suit = int(bid[0]), bid[1:]
        last_level, last_suit = int(last_real_bid[0]), last_real_bid[1:]
        
        suit_rank = {'♣': 1, '♦': 2, '♥': 3, '♠': 4, 'NT': 5}
        
        if my_level > last_level: return True
        if my_level == last_level and suit_rank.get(my_suit) > suit_rank.get(last_suit): 
            return True
    except: return False
    
    return False
```

### 3. Bid Appropriateness (Semantic Validation)

**File:** `/Users/simonroy/Desktop/bridge_bidding_app/backend/engine/bid_safety.py`

#### BidSafety Class

Purpose: Prevent semantically wrong bids (e.g., bidding 7NT with 27 HCP)

```python
class BidSafety:
    SLAM_SMALL_MIN_HCP = 33  # 6-level minimum
    SLAM_GRAND_MIN_HCP = 37  # 7-level minimum
    GAME_3NT_MIN_HCP = 24
    
    @staticmethod
    def safe_adjust_bid(original, next_legal, auction, hand, explanation):
        # Check 1: Level escalation (max 2 levels)
        if exceeds_2_levels(original, next_legal):
            return ("Pass", "Cannot adjust more than 2 levels")
        
        # Check 2: Point requirements for adjusted level
        if insufficient_points_for_level(next_legal, hand, auction):
            return ("Pass", "Insufficient points for that level")
        
        # Check 3: Trump requirements
        if insufficient_trump_support(next_legal, hand):
            return ("Pass", "Insufficient trump support")
        
        return (next_legal, adjusted_explanation)
```

#### Adjustments Used In:
- ResponseModule.evaluate()
- RebidModule.evaluate()
- ResponderRebidModule.evaluate()
- AdvancerBidsModule.evaluate()
- OvercallModule.evaluate()

### 4. Hand-Level Validation (Within Modules)

Each module has internal validation:

#### Point Ranges
- Opening: 13+ total points (with distribution)
- Responses: 6+ points minimum
- Raises: Support points (HCP + long suit adjustment)
- Overcalls: 8-16 HCP (varies by position)

#### Suit Requirements
- Major suit: 4+ cards
- Minor suit: 5+ cards for opening
- Fit requirement: 3+ cards for raises (or 4+ in majors)

#### Special Checks
- Preempts: Suit quality (2 of top 3 honors for weak twos)
- Takeout Doubles: Shortness in doubled suit
- Negatives: Unbid majors present

---

## FEATURE EXTRACTION SYSTEM

**File:** `/Users/simonroy/Desktop/bridge_bidding_app/backend/engine/ai/feature_extractor.py`

### Function: `extract_features(hand, auction_history, my_position, vulnerability)`

Returns dict with all contextual data:

```python
{
    'hand_features': {
        'hcp': int,
        'dist_points': int,
        'total_points': int,
        'suit_lengths': {'♠': int, ...},
        'is_balanced': bool
    },
    'auction_features': {
        'num_bids': int,
        'opening_bid': str,          # e.g., '1♥'
        'opener': str,               # Position (North/East/South/West)
        'opener_relationship': str,  # 'Me', 'Partner', 'Opponent', None
        'partner_bids': list[str],
        'partner_last_bid': str,
        'opener_last_bid': str,
        'opener_index': int,         # Position in 4-player cycle
        'is_contested': bool,
        'vulnerability': str,
        'interference': {
            'present': bool,
            'bid': str,              # e.g., '2♦'
            'level': int,
            'type': str,             # 'double', 'suit_overcall', 'nt_overcall', 'none'
            'position': int          # Index in auction_history
        }
    },
    'auction_history': list[str],
    'hand': Hand object,
    'my_index': int,                 # 0-3 position in cycle
    'positions': list[str]           # ['North', 'East', 'South', 'West']
}
```

### Interference Detection

```python
def _detect_interference(auction_history, positions, my_index, 
                         opener_relationship, opener_index):
    """Detects opponent's bid between partner's opening and my response."""
    
    # Only if partner opened
    if opener_relationship != 'Partner': return no_interference
    
    # Check for opponent bids after opening
    partner_index = opener_index
    lho_index = (partner_index + 1) % 4
    rho_index = (partner_index + 3) % 4
    
    for auction_idx in range(opener_index + 1, len(auction_history)):
        bidder = auction_idx % 4
        bid = auction_history[auction_idx]
        
        if (bidder == lho_index or bidder == rho_index) and bid != 'Pass':
            # Found interference!
            return {
                'present': True,
                'bid': bid,
                'type': classify(bid),
                'level': extract_level(bid),
                'position': auction_idx
            }
    
    return no_interference
```

### Key Uses
- Decision engine: Determines situation (opening/competitive/partnership)
- Modules: Access hand, auction history, interference details
- Conventions: Check applicability conditions (e.g., "partner opened 1NT?")

---

## BID EXPLANATION SYSTEM

**File:** `/Users/simonroy/Desktop/bridge_bidding_app/backend/engine/ai/bid_explanation.py`

### Class: `BidExplanation`

```python
class BidExplanation:
    def __init__(self, bid: str):
        self.bid = bid
        self.primary_reason: str
        self.requirements: dict = {}      # e.g., {"HCP": "15-17"}
        self.actual_values: dict = {}      # e.g., {"HCP": "16"}
        self.rule_checks: list = []        # Conditions evaluated
        self.alternatives: list = []       # Other bids considered
        self.convention: str = ""          # e.g., "Stayman"
        self.sayc_rule: str = ""          # e.g., "1nt_opening"
        self.forcing_status: str = ""     # "Sign-off", "Forcing", "Invitational"
```

### Methods:
- **`set_primary_reason(text)`** - Main reason for bid
- **`add_requirement(name, value)`** - Condition needed (e.g., "HCP", "15-17")
- **`add_actual_value(name, value)`** - What we have (e.g., "HCP", "16")
- **`set_forcing_status(status)`** - Game forcing? Invitational?
- **`set_convention(name)`** - Which convention applies
- **`add_alternative(bid, reason)`** - Other bids considered
- **`format(level)`** - Format as string for UI
- **`to_dict()`** - Convert to JSON-serializable dict

### Explanation Levels:

| Level | Detail | Use Case |
|-------|--------|----------|
| **SIMPLE** | One sentence | Mobile UI, quick feedback |
| **DETAILED** | Hand values + alternatives | Main UI explanations |
| **EXPERT** | SAYC rules + all logic | Learning dashboard |
| **CONVENTION_ONLY** | Without revealing actual values | Partner/opponent bids |

---

## KNOWN ISSUES & ERROR PATTERNS

### Issue 1: Advancer Bids Registration & Routing

**Status:** ✅ FIXED (but should verify after changes)

**Location:** `decision_engine.py`, lines 32-39

**Problem:** AdvancerBidsModule is registered in BiddingEngine but decision engine must detect advancer situation correctly.

**Detection Logic:**
```python
if (partner_last_bid and partner_last_bid not in ['Pass', 'XX'] and 
    auction['opener_relationship'] != 'Partner' and
    len(my_bids) == 0):
    return 'advancer_bids'
```

**Critical Conditions:**
1. Partner must have made a non-Pass bid
2. Opener relationship must be 'Opponent' (not None, not 'Me')
3. This must be my FIRST bid

### Issue 2: Bid Legality Adjustment in Competitive Situations

**Status:** ⚠️ PARTIAL (2-level max check implemented)

**Locations:**
- `advancer_bids.py`, lines 39-55
- `responses.py`, lines 32-48
- `rebids.py`, lines 59-76
- `responder_rebids.py`, lines 52-69
- `overcalls.py` - incorporated in logic

**Problem:** When module suggests illegal bid, it's adjusted to next legal bid. But if adjustment escalates too many levels, we pass instead of making unreasonable bid.

**Protection:**
```python
try:
    original_level = int(bid[0])
    adjusted_level = int(next_legal[0])
    
    if adjusted_level - original_level > 2:
        return ("Pass", f"Cannot make reasonable bid...")
except: pass
```

**Known Gaps:**
- No check for minimum HCP at adjusted level
- No check for trump support at adjusted level
- These checks exist in BidSafety but not always used

### Issue 3: Negative Doubles HCP Requirements

**Status:** ✅ IMPLEMENTED

**Location:** `ai/conventions/negative_doubles.py`, lines 31-40

**Rules:**
- Through 2-level overcall: 6+ HCP
- 3-level overcall: 8-10 HCP
- 4-level+ overcall: 12+ HCP

**Logic:**
```python
if overcall_level <= 2:
    min_hcp = 6
elif overcall_level == 3:
    min_hcp = 8
else:
    min_hcp = 12

if hand.hcp < min_hcp: return None
```

### Issue 4: Takeout Double Point Range

**Status:** ✅ IMPLEMENTED (with exception for strong hands)

**Location:** `ai/conventions/takeout_doubles.py`, lines 66-103

**Rules:**
- Minimum: 12+ HCP
- Special: 19+ HCP balanced (double then bid NT to show 19-21)
- Requirements: 0-2 in opponent's suit, 3+ in each unbid suit

**Special Case:**
```python
# SPECIAL CASE: Very strong balanced hand (19+ HCP)
# These hands are too strong for 1NT overcall (15-18) but too balanced for suit overcall
# Solution: Double now, bid NT later to show 19-21 HCP
if hand.hcp >= 19 and hand.is_balanced:
    return True  # Will double and bid NT next round
```

### Issue 5: Preempt Suit Quality Validation

**Status:** ✅ IMPLEMENTED

**Location:** `ai/conventions/preempts.py`, lines 48-78

**Rules (SAYC):**
- **Weak Two (2-level, 6 cards):** 2 of top 3 honors (A/K/Q) - STRICT
- **3-level (7 cards):** 2+ honors including J/T
- **4-level (8 cards):** 2+ honors

**Logic:**
```python
if suit_length == 6:
    # SAYC: Weak Two requires 2 of top 3 honors
    top_three_honors = {'A', 'K', 'Q'}
    top_honor_count = sum(1 for rank in suit_cards if rank in top_three_honors)
    has_quality_suit = top_honor_count >= 2
else:
    # 7-8 card preempts: 2+ honors (can include J, T)
    honors = {'A', 'K', 'Q', 'J', 'T'}
    honor_count = sum(1 for rank in suit_cards if rank in honors)
    has_quality_suit = honor_count >= 2
```

### Issue 6: Opening Bids Balanced vs 2♣ Priority

**Status:** ✅ IMPLEMENTED

**Location:** `opening_bids.py`, lines 25-90

**Problem:** Must check balanced 1NT/2NT/3NT BEFORE 2♣ to avoid conflicts

**Logic:**
```python
# Check BALANCED hands FIRST
if hand.is_balanced and 25 <= hand.hcp <= 27: return "3NT"
if hand.is_balanced and 22 <= hand.hcp <= 24: return "2NT"
if 15 <= hand.hcp <= 17 and hand.is_balanced: return "1NT"

# THEN check 2♣ for non-balanced strong hands
if hand.total_points >= 22: return "2♣"
```

### Issue 7: Responder Rebid Slam Safety

**Status:** ✅ IMPLEMENTED

**Location:** `responder_rebids.py`, lines 79-92

**Problem:** Responder with 10-12 HCP shouldn't bid slam even if opponent bids aggressively

**Logic:**
```python
if max_level >= 5 and hand.hcp < 18:
    return ("Pass", f"Auction already at {max_level}-level, insufficient values for slam")
```

---

## DATA FLOW DIAGRAMS

### Flow 1: AI Makes Bid

```
GET-NEXT-BID Request
│
├─ Hand (13 cards)
├─ Auction history (list of bids)
├─ My position (North/East/South/West)
└─ Vulnerability (None/NS/EW/Both)
│
↓
BiddingEngine.get_next_bid()
│
├─ 1. extract_features()
│   ├─ Calculate hand properties (HCP, dist, balanced)
│   ├─ Analyze auction (opener, relationship, contested)
│   └─ Detect interference
│   
├─ 2. select_bidding_module(features)
│   ├─ State 1: Opening? → preempts → opening_bids
│   ├─ State 2: Opponent opened? → advancer/overcall/double
│   ├─ State 3: Partner opened? → responder/conventions
│   └─ State 4: I opened? → rebid/conventions
│
├─ 3. specialist.evaluate(hand, features)
│   ├─ Internal logic (e.g., _evaluate_response)
│   ├─ Bid generation
│   └─ Explanation creation
│
├─ 4. _is_bid_legal(bid, auction_history)
│   ├─ Check pass/double/redouble
│   └─ Verify level+suit ranking
│
└─ 5. Return (bid, explanation)
    ├─ If legal: return as is
    └─ If illegal: try adjustment or pass
    
Response
├─ bid: "2♣"
├─ explanation: "Stayman showing 8+ HCP and 4-card major..."
└─ status: "success"
```

### Flow 2: User Submits Bid (Evaluate)

```
EVALUATE-BID Request
│
├─ User's bid (e.g., "2♥")
├─ Hand dealt to South
├─ Auction history before user's bid
└─ Other parameters
│
↓
BiddingEngine.get_next_bid()  [to get optimal bid]
│
├─ Extract features
├─ Select module
├─ Get specialist evaluation
├─ Validate legality
└─ Return optimal bid
│
↓
Compare user_bid to optimal_bid
│
├─ If same: score 10, "Optimal"
├─ If acceptable alternative: score 7-9, "Acceptable"
├─ If suboptimal but legal: score 4-6, "Suboptimal"
└─ If illegal: score 0-3, "Error"
│
↓
Store in database
│
├─ bidding_decisions table
├─ user_id, user_bid, optimal_bid
├─ score, correctness, timestamp
└─ explanation
│
Response
├─ user_bid: "2♥"
├─ optimal_bid: "2♣"
├─ score: 7
├─ rating: "acceptable"
└─ feedback: "2♥ shows only 5 hearts; 2♣ Stayman asks for majors..."
```

### Flow 3: Module Selection Decision Tree

```
select_bidding_module(features)
│
├─ opener = features['auction_features']['opener']
│
├─ if NOT opener (opening situation)
│   ├─ Check PreemptConvention
│   └─ Return 'preempts' or 'opening_bids'
│
├─ if opener_relationship == 'Opponent' (competitive)
│   ├─ if partner_last_bid and len(my_bids) == 0
│   │  └─ Return 'advancer_bids'
│   │
│   ├─ if len(my_bids) == 0 (first bid)
│   │  ├─ Check MichaelsCuebidConvention
│   │  ├─ Check Unusual2NTConvention
│   │  ├─ Check OvercallModule
│   │  └─ Check TakeoutDoubleConvention
│   │
│   └─ if len(my_bids) > 0 (subsequent bid)
│      ├─ Check balancing seat (last 2 = Pass)
│      ├─ Check OvercallModule
│      └─ Check TakeoutDoubleConvention
│
├─ if opener_relationship == 'Partner' (partnership auction)
│   ├─ if responder's 2nd+ bid
│   │  └─ Return 'responder_rebid'
│   │
│   ├─ Check BlackwoodConvention
│   ├─ Check SplinterBidsConvention
│   ├─ Check FourthSuitForcingConvention
│   ├─ Check NegativeDoubleConvention
│   │
│   ├─ if opening_bid == '1NT'
│   │  ├─ Check JacobyConvention
│   │  └─ Check StaymanConvention
│   │
│   └─ Return 'responses'
│
├─ if opener_relationship == 'Me' (I opened)
│   ├─ if opening_bid == '1NT'
│   │  ├─ Check JacobyConvention
│   │  └─ Check StaymanConvention
│   │
│   ├─ Check BlackwoodConvention
│   └─ Return 'openers_rebid'
│
└─ Return 'pass_by_default'
```

---

## SUMMARY TABLE: All Modules & Their Entry Points

| Module | File | Entry Point | Decision Trigger | External Point Check |
|--------|------|------------|------------------|----------------------|
| **OpeningBidsModule** | opening_bids.py | State 1 | No opener | 13+ total points |
| **PreemptConvention** | conventions/preempts.py | State 1 (Priority) | No opener | 6-10 HCP, 6+ suit |
| **ResponseModule** | responses.py | State 3 | Partner opened, 1st response | 6+ points |
| **RebidModule** | rebids.py | State 4 | I opened, rebidding | Varies by situation |
| **ResponderRebidModule** | responder_rebids.py | State 3 | Partner opened, 2nd+ bid | Varies (6-18+ HCP) |
| **OvercallModule** | overcalls.py | State 2 | Opponent opened | 8-16 HCP (varies) |
| **AdvancerBidsModule** | advancer_bids.py | State 2 | Partner overcalled, 1st bid | 8+ points |
| **TakeoutDoubleConvention** | conventions/takeout_doubles.py | State 2 (Alternative) | Opponent opened suit | 12+ HCP |
| **NegativeDoubleConvention** | conventions/negative_doubles.py | State 3 | Opponent interfered over partner's opening | 6-12+ HCP (level-dependent) |
| **StaymanConvention** | conventions/stayman.py | State 3 & 4 | Partner opened 1NT | 7+ HCP with majors |
| **JacobyConvention** | conventions/jacoby_transfers.py | State 3 & 4 | Partner opened 1NT | 5+ major |
| **BlackwoodConvention** | conventions/blackwood.py | State 3 & 4 | Partnership auction, slam interest | 15+ HCP typically |
| **SplinterBidsConvention** | conventions/splinter_bids.py | State 3 | Partnership auction, fit + shortness | 13-18 HCP with support |
| **FourthSuitForcingConvention** | conventions/fourth_suit_forcing.py | State 3 | Bidding 4th suit after 3 suits bid | 12+ HCP |
| **MichaelsCuebidConvention** | conventions/michaels_cuebid.py | State 2 | Opponent opened, 5-5 two suits | 8-16 HCP |
| **Unusual2NTConvention** | conventions/unusual_2nt.py | State 2 | Opponent opened, 5-5 minors | 8-16 HCP |

---

## KEY ARCHITECTURAL INSIGHTS

### 1. Modular Design
- Each module handles ONE context (opening, response, overcall, etc.)
- All inherit from ConventionModule base class
- Decision engine routes to correct module based on auction state

### 2. Layered Validation
- **Level 1:** Legality check (auction rules) - ALL bids validated
- **Level 2:** Module-internal checks (HCP, suit requirements)
- **Level 3:** Appropriateness checks (BidSafety) - prevents semantic errors

### 3. Feature-Driven Decisions
- ALL decisions based on extracted features dict
- Features include: hand properties, auction history, interference, opener relationship
- Modules don't need to parse auction themselves - features do it

### 4. Explanation Generation
- BidExplanation class captures WHY bid was chosen
- Different detail levels for different UIs
- Traced back to specific code that generated bid

### 5. Error Prevention
- 2-level max adjustment on bid escalation
- Slam safety checks prevent under-bidded slams
- Suit quality validation prevents weak preempts

### 6. Extensibility
- Adding new convention: Extend ConventionModule, add to registry, add decision logic
- Adding new situation: Add new state to decision_engine
- All modules follow same interface

---

**End of Architecture Map**

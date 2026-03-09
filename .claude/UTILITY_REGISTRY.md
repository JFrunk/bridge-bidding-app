# Shared Utility Registry

**This file is the single source of truth for all shared utilities in the codebase.**

Before writing ANY new function, constant, or logic — check this registry. If a utility exists for your domain, import from it. If not, consider whether your code should become a new registered utility.

---

## How This Registry Works

Each utility entry has:
- **File path** and **import statement** — copy-paste ready
- **Exports** — what's available
- **Banned patterns** — inline code that MUST be replaced with the utility
- **Tech debt** — existing violations to migrate (do NOT add to these)

**When adding a new utility:**
1. Create the utility file in the appropriate `utils/` directory
2. Add comprehensive tests
3. Add an entry to this registry following the same format
4. Add a row to the quick reference table in `CLAUDE.md`

---

## 1. Seat Positions (Backend + Frontend)

**Domain:** Player positions, turn order, partnerships, relative positions

### Backend
**File:** `backend/utils/seats.py`
**Import:** `from utils.seats import partner, lho, rho, relative_position, display_name, bidder_role, active_seat_bidding, active_seat_play, seat_index, seat_from_index, normalize, partnership, partnership_str, same_side, is_partner, is_opponent, dummy, opening_leader, is_declaring_side, is_defending_side`
**Constants:** `NORTH, EAST, SOUTH, WEST, NS, EW, SEATS, SEAT_NAMES, RELATIVE_NAMES, NS_SIDE, EW_SIDE, PARTNERS, NEXT_PLAYER, PREV_PLAYER`
**Tests:** `backend/tests/unit/test_seats.py` (50 tests)

### Frontend
**File:** `frontend/src/utils/seats.js`
**Import:** `import { partner, lho, rho, relativePosition, displayName, bidderRole, nsSuccess, activeSeatBidding, activeSeatPlay, seatIndex, seatFromIndex, normalize, partnership, partnershipStr, sameSide, isPartner, isOpponent, dummy, openingLeader, isDeclaringSide, isDefendingSide, NORTH, EAST, SOUTH, WEST, NS, EW, SEATS, SEAT_NAMES, RELATIVE_NAMES, NS_SIDE, EW_SIDE, PARTNERS, NEXT_PLAYER, PREV_PLAYER } from '../utils/seats'`
**Tests:** `frontend/src/utils/seats.test.js` (54 tests)

### Banned Patterns
```python
# BANNED: Inline partner maps
{'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}           # Use partner(seat)
{'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}[x]         # Use partner(x)
opposite = {'North': 'South', 'South': 'North', ...}  # Use partner(normalize(seat))

# BANNED: Inline modulo seat arithmetic
(idx + 1) % 4                                          # Use lho() or seat_from_index()
(idx + 2) % 4                                          # Use partner() or seat_from_index()
(dealer_idx + bid_count) % 4                            # Use active_seat_bidding(dealer, bid_count)
(leader_idx + cards_played) % 4                         # Use active_seat_play(leader, cards_played)
positions[idx % 4]                                      # Use seat_from_index(idx)

# BANNED: Inline seat arrays for rotation/lookup
['N', 'E', 'S', 'W'][idx]                              # Use seat_from_index(idx)
players = ['North', 'East', 'South', 'West']           # Use SEATS or SEAT_NAMES

# BANNED: Inline partnership checks
seat in ('N', 'S')                                      # Use same_side(seat, 'N')
seat == 'N' or seat == 'S'                              # Use same_side(seat, 'N')
partnership_map = {0: 'NS', 1: 'EW'}                   # Use partnership_str(seat)
```

### Self-check
Search changed files for: `% 4`, `'N': 'S'`, `'S': 'N'`, inline `['N', 'E', 'S', 'W']`

### Tech Debt (do NOT add to)
- `backend/engine/play_engine.py` — 3 inline partner/lho patterns
- `backend/server.py:984` — inline partner_map
- `backend/routes/room_api.py:206` — inline partner lookup
- `backend/engine/play/ai/play_signal_overlay.py:1077` — inline opposite map
- `backend/engine/feedback/heuristic_backfill_adapter.py:571` — inline opposite map
- `backend/engine/learning/analytics_api.py:2654` — inline dummy_pos lookup
- `backend/engine/ai/conventions/negative_doubles.py:158` — inline partners map
- `backend/engine/ai/conventions/takeout_doubles.py:169` — inline partners map
- `frontend/src/App.js:228,2747` — inline modulo arithmetic
- Multiple analysis/audit scripts with inline `% 4`

---

## 2. Suit Symbols & Bid Formatting (Frontend)

**Domain:** Suit letter/symbol conversion, suit colors, bid string parsing and display

**File:** `frontend/src/utils/suitColors.js`
**Import:** `import { SUIT_MAP, SYMBOL_TO_LETTER, SUIT_LOOKUP, SUIT_NAMES, isRedSuit, getSuitColorClass, normalizeSuit, extractSuitFromBid, extractLevelFromBid, isSpecialBid, formatBidDisplay } from '../utils/suitColors'`
**Tests:** None yet (needs test file)

### Exports
| Export | Type | Purpose |
|--------|------|---------|
| `SUIT_MAP` | const | `{ 'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣' }` |
| `SYMBOL_TO_LETTER` | const | `{ '♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C' }` |
| `SUIT_LOOKUP` | const | Bidirectional — accepts both letter and symbol |
| `SUIT_NAMES` | const | `{ '♠': 'spades', ... }` — for accessibility/aria |
| `isRedSuit(suit)` | fn | Accepts letter, symbol, or full name |
| `getSuitColorClass(suit, onDark?)` | fn | Returns Tailwind class |
| `normalizeSuit(suit)` | fn | Any format → Unicode symbol |
| `extractSuitFromBid(bid)` | fn | `"2H"` → `"H"` |
| `extractLevelFromBid(bid)` | fn | `"2H"` → `2` |
| `isSpecialBid(bid)` | fn | Pass, X, XX, DBL, RDBL |
| `formatBidDisplay(bid)` | fn | `"1S"` → `"1♠"` |

### Banned Patterns
```javascript
// BANNED: Inline suit symbol maps
{ 'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣' }       // Use SUIT_MAP or SUIT_LOOKUP
{ '♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C' }       // Use SYMBOL_TO_LETTER
{ '♠': 'spades', '♥': 'hearts', ... }              // Use SUIT_NAMES

// BANNED: Inline red suit checks
suit === '♥' || suit === '♦'                          // Use isRedSuit(suit)
['H', 'D', '♥', '♦'].includes(suit)                  // Use isRedSuit(suit)
const isRed = ...                                     // Use isRedSuit(suit)

// BANNED: Inline suit color ternaries
isRed ? 'text-suit-red' : 'text-suit-black'           // Use getSuitColorClass(suit)
suit === '♥' || suit === '♦' ? '#d32f2f' : '#000'    // Use getSuitColorClass(suit)

// BANNED: Inline bid parsing
bid[0]                                                 // Use extractLevelFromBid(bid)
bid.slice(1) / bid.substring(1)                        // Use extractSuitFromBid(bid)
bid === 'Pass' || bid === 'X' || bid === 'XX'          // Use isSpecialBid(bid)
```

### Self-check
Search changed files for: `'S': '♠'`, `'♥': 'H'`, `=== '♥' ||`, `includes('♥')`, `bid[0]`, `bid.slice(1)`

### Tech Debt (do NOT add to)
- `shared/utils/cardUtils.js` — uses `SUIT_LOOKUP` import (resolved)
- `components/learning/types/flow-types.js:100-105` — inline SUIT_MAP
- `components/learning/HandReviewModal.js:43,64` — inline SUIT_MAP (2x)
- `components/learning/BidReviewModal.js:129` — inline SUIT_MAP
- `components/learning/hand-review/constants.js:90-96` — inline reverse map
- `shared/components/Card.js:12` — inline red suit check
- `shared/components/SuitRow.jsx:24` — inline red suit check
- `components/bridge/BridgeCard.jsx:24-25` — inline red suit check
- `components/bridge/VerticalCard.jsx:30` — inline suit color
- `components/shared/BidChip.jsx:20-23` — local getSuitColor reimplementation
- `components/learning/BiddingGapAnalysis.js:22-30` — local getSuitColor with hex
- `components/play/LastTrickOverlay.jsx:16-18` — inline getSuitStyle
- `components/learning/SkillPractice.js:856` — inline suit color in className
- `components/learning/LearningCard.jsx:17-18` — inline isRed check

---

## 3. Card Manipulation (Frontend)

**Domain:** Card sorting, suit grouping, rank display, suit ordering, contract parsing

**File:** `frontend/src/shared/utils/cardUtils.js`
**Import:** `import { SUIT_ORDER, RANK_ORDER, RANK_DISPLAY, getSuitOrder, sortCards, groupCardsBySuit, rankToDisplay, getSuitColor, parseContract, formatContract } from '../shared/utils/cardUtils'`
**Tests:** `frontend/src/shared/__tests__/cardUtils.test.js` (13 tests)

### Exports
| Export | Type | Purpose |
|--------|------|---------|
| `SUIT_ORDER` | const | `['♠', '♥', '♣', '♦']` — standard display order |
| `RANK_ORDER` | const | `{ 'A': 14, 'K': 13, ... '2': 2 }` |
| `RANK_DISPLAY` | const | `{ 'A': 'A', 'K': 'K', ..., 'T': '10' }` |
| `getSuitOrder(trump)` | fn | Trump-aware suit order |
| `sortCards(cards)` | fn | Sort by rank descending (handles `.rank` and `.r`) |
| `groupCardsBySuit(cards)` | fn | Group into `{ '♠': [], '♥': [], ... }` |
| `rankToDisplay(rank)` | fn | `'T'` → `'10'` |
| `getSuitColor(suit)` | fn | Returns `'suit-red'` or `'suit-black'` (CSS class) |
| `parseContract(str)` | fn | `"4♠X"` → `{ level: 4, strain: '♠', doubled: 1 }` |
| `formatContract(obj)` | fn | Reverse of parseContract |

### Banned Patterns
```javascript
// BANNED: Inline rank ordering
{ 'A': 14, 'K': 13, 'Q': 12, ... }                  // Use RANK_ORDER
['A', 'K', 'Q', 'J', 'T', '9', ...]                 // Use RANK_ORDER (use Object.keys)
const rankMap = { 'T': '10', ... }                    // Use RANK_DISPLAY or rankToDisplay()

// BANNED: Inline suit order arrays
['♠', '♥', '♦', '♣']                                 // Use SUIT_ORDER or getSuitOrder()
['S', 'H', 'D', 'C']                                 // Use SUIT_ORDER
const SUIT_ORDER = [...]                               // Import from cardUtils

// BANNED: Duplicate sort/group functions
function sortCards(cards) { ... }                      // Import from cardUtils
cards.sort((a, b) => rankOrder[b.rank] - ...)         // Use sortCards(cards)
const groups = { '♠': [], '♥': [], ... }              // Use groupCardsBySuit(cards)
```

### Self-check
Search changed files for: `'A': 14`, `rankOrder`, local `sortCards`, local `groupBy`, inline `['♠', '♥'`

### Tech Debt (do NOT add to)
- `components/learning/types/hand-types.js` — duplicate sortCards, SUIT_ORDER, groupBySuit, isRedSuit
- `components/learning/hand-review/constants.js` — duplicate sortCards, RANK_ORDER, RANK_DISPLAY, groupCardsBySuit, getSuitOrder, normalizeSuit, isRedSuit
- `components/learning/HandReviewModal.js:53-60` — local sortCards
- `components/learning/BidReviewModal.js:125,134-141` — local SUIT_ORDER + sortCards
- `components/bridge/BeliefPanel.jsx:33` — local SUIT_ORDER
- `components/learning/LearningCard.jsx:60` — local SUIT_ORDER

---

## 4. Error Logging (Backend)

**Domain:** Structured error capture, categorization, pattern detection

**File:** `backend/utils/error_logger.py`
**Import:** `from utils.error_logger import log_error, get_error_summary, get_recent_errors, detect_error_patterns`
**Tests:** None yet (needs test file)

### Banned Patterns
```python
# BANNED: Raw traceback printing (bypasses structured logging)
except Exception as e:
    traceback.print_exc()                 # Use log_error(e, context={...})

# BANNED: Shadowing log_error in except clause
except Exception as log_error:            # NEVER use 'log_error' as exception variable

# BANNED: Silent exception swallowing
except Exception:
    pass                                  # At minimum: log_error(e, context={...})
```

### Self-check
Search changed files for: `traceback.print_exc`, `except Exception as log_error`, bare `except Exception: pass`

### Tech Debt (do NOT add to)
- `server.py` — 36 `traceback.print_exc()` calls bypass error_logger (only 4 of 65 handlers use log_error)
- `server.py:3512` — `except Exception as log_error:` shadows the imported function

---

## 5. Session Management (Frontend)

**Domain:** Session ID generation/storage, API request headers, authenticated fetch

**File:** `frontend/src/utils/sessionHelper.js`
**Import:** `import { getSessionId, getSessionHeaders, clearSession, getSessionInfo, fetchWithSession } from '../utils/sessionHelper'`
**Tests:** None yet (needs test file)

### Banned Patterns
```javascript
// BANNED: Local getSessionId implementations
function getSessionId() { return localStorage.getItem('bridge_session_id'); }

// BANNED: Inline session header construction
headers: { 'X-Session-ID': sessionId }       // Use ...getSessionHeaders()

// BANNED: Inline fetch with session
fetch(url, { headers: { 'X-Session-ID': id } })   // Use fetchWithSession(url, options)
```

### Self-check
Search changed files for: `localStorage.getItem('bridge_session_id')`, inline `'X-Session-ID'`

### Tech Debt (do NOT add to)
- `services/api.js` — unused duplicate SessionManager; do not import from this file
- `shared/services/SessionService.js` — abandoned duplicate; do not import from this file
- `components/DDSStatusIndicator.jsx:7-9` — local getSessionId
- `components/AIDifficultySelector.jsx:7-9` — local getSessionId

---

## Adding a New Utility

When you identify a pattern duplicated across 3+ files:

1. **Create the utility** in the appropriate `utils/` directory
2. **Export all constants and functions** that callers need (don't hide useful things internally)
3. **Write tests** — every exported function needs test coverage
4. **Add a registry entry** to this file following the format above (file, import, exports table, banned patterns, self-check, tech debt)
5. **Add a row** to the quick reference table in `CLAUDE.md` under "Shared Utilities Registry"
6. **Migrate at least one caller** to prove the import path works
7. **List remaining callers** in the tech debt section

Do NOT create a utility for patterns that appear in only 1-2 files — inline code is fine for isolated cases.

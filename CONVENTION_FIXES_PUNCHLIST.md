# Convention Modules - Comprehensive Punch List

**Review Date:** 2025-10-10
**Purpose:** Identify incorrect logic, missing levels, and other issues in all convention modules

---

## 🔴 CRITICAL ISSUES (High Priority - Breaks Correct Bidding)

### 1. **Takeout Doubles: HCP Requirement Too High**
**File:** `engine/ai/conventions/takeout_doubles.py:44`
**Issue:** Requires 13+ HCP for takeout double (line 44: `if hand.hcp < 13`)
**SAYC Standard:** Should be 12+ HCP
**Impact:** Missing valid takeout doubles with 12 HCP
**Fix:** Change line 44 to `if hand.hcp < 12:`

---

### 2. **Takeout Doubles: Missing ConventionModule Interface**
**File:** `engine/ai/conventions/takeout_doubles.py:4`
**Issue:** Class doesn't extend `ConventionModule` base class
**Current:** `class TakeoutDoubleConvention:`
**Should be:** `class TakeoutDoubleConvention(ConventionModule):`
**Impact:** May not be properly registered in decision engine
**Fix:** Add inheritance and implement required methods

---

### 3. **Jacoby Transfers: Missing After Transfer Actions**
**File:** `engine/ai/conventions/jacoby_transfers.py:11-16`
**Issue:** No logic for responder's actions AFTER opener completes transfer
**Missing Scenarios:**
- Responder with weak hand (0-7 HCP) should Pass
- Responder with invitational hand (8-9 HCP) should invite (raise to 3-level or bid 2NT)
- Responder with game-forcing hand (10+ HCP) should bid game or explore slam
- Responder with 6+ card suit should consider different continuations

**Example Missing Auction:**
```
1NT - 2♦ (transfer to hearts)
2♥  - ? (Responder needs to describe strength now)
```

**Impact:** After completing transfer, responder always passes regardless of strength
**Fix:** Add `_get_responder_continuation` method to handle post-transfer bids

---

### 4. **Stayman: Missing Responder's Rebid After 2♦ Response**
**File:** `engine/ai/conventions/stayman.py:12-18`
**Issue:** No logic for responder's rebid after opener bids 2♦ (denying 4-card major)
**Missing Scenarios:**
- With 8-9 HCP: Bid 2NT (invitational)
- With 10+ HCP: Bid 3NT (game forcing)
- With 5-card major and weak hand: Bid 2♥/2♠ (to play)
- With unbalanced game-forcing hand: Bid 3-level suit

**Example Missing Auction:**
```
1NT - 2♣ (Stayman)
2♦  - ? (Responder needs to continue)
```

**Impact:** Auction dies after 2♦ response
**Fix:** Add responder rebid logic after Stayman response

---

### 5. **Stayman: Missing Responder's Rebid After Finding Fit**
**File:** `engine/ai/conventions/stayman.py:12-18`
**Issue:** No logic for responder's rebid after finding 4-4 major fit
**Missing Scenarios:**
- With 8-9 HCP: Raise to 3-level (invitational)
- With 10+ HCP: Raise to 4-level (game)
- With 5-3-3-2 and other major: May still bid 3NT

**Example Missing Auction:**
```
1NT - 2♣ (Stayman, 10 HCP, 4 hearts)
2♥  - 4♥ (This bid is missing!)
```

**Impact:** After finding fit, responder doesn't set level
**Fix:** Add responder rebid logic after fit found

---

### 6. **Jacoby Transfers: Incorrect Super-Accept Logic**
**File:** `engine/ai/conventions/jacoby_transfers.py:28-33`
**Issue:** Super-accept check on line 28 & 32 uses `hand.hcp >= 17 and hand.suit_lengths['♥'] == 2`
**Problems:**
- Should check for 4-card support (`>= 4`), not doubleton (`== 2`)
- Should check for maximum 1NT (17 HCP), condition is correct but logic inverted
- Currently jumping to 2NT with DOUBLETON (worst possible holding)

**Current (WRONG):**
```python
if hand.hcp >= 17 and hand.suit_lengths['♥'] == 2:  # Doubleton!
    return ("2NT", "Maximum 1NT opening (17-18 HCP) with no fit for Hearts.")
```

**Should be:**
```python
if hand.hcp == 17 and hand.suit_lengths['♥'] >= 4:  # 4-card support!
    return ("3♥", "Super-accept showing maximum with 4-card support.")
```

**Impact:** Super-accepts never happen, and wrong bids with doubleton
**Fix:** Change to check for 4-card support and bid 3-level, not 2NT

---

### 7. **Blackwood: Insufficient Trigger Logic**
**File:** `engine/ai/conventions/blackwood.py:22-34`
**Issue:** Blackwood trigger is too simplistic
**Problems:**
- Only checks if partner bid 3 or 4-level (line 28)
- Doesn't verify trump fit exists
- Doesn't check for slam interest indicators
- Could ask for aces without agreed suit
- Missing check for sufficient combined strength

**Current Logic:**
```python
is_strong_raise = len(partner_last_bid) == 2 and partner_last_bid[0] in ['3', '4']
if is_strong_raise and hand.total_points >= 18:
    return True
```

**Should Check:**
- Trump fit agreed (explicit or implicit)
- Combined partnership points ~33+ for small slam
- Not already in game/slam
- No void in trump suit (RKC would be better)

**Impact:** May ask for aces at wrong times, or never ask when appropriate
**Fix:** Add comprehensive slam interest detection

---

### 8. **Blackwood: Missing Signoff Logic After Ace Response**
**File:** `engine/ai/conventions/blackwood.py:13-20`
**Issue:** After getting ace response, no logic to:
- Sign off at 5-level if missing 2 aces
- Bid 6-level if missing 1 ace
- Ask for kings with 5NT if all aces present
- Bid 7-level if all aces+kings present

**Current:** After partner responds to 4NT, asker doesn't know what to do
**Impact:** Auction stalls after Blackwood response
**Fix:** Add bid selection logic after receiving ace count

---

### 9. **Blackwood: Missing King-Asking (5NT) Logic**
**File:** `engine/ai/conventions/blackwood.py:19`
**Issue:** Comment says "King-asking and slam bidding logic can be added here later"
**Impact:** Can't ask for kings, even when all aces are present
**Fix:** Implement 5NT king ask and responses (same step responses as aces)

---

### 10. **Negative Doubles: Incorrect Applicability Check**
**File:** `engine/ai/conventions/negative_doubles.py:34-43`
**Issue:** Requires exactly 2 non-pass bids (line 40-41)
**Problem:** This excludes valid negative double situations where RHO passes:
- `1♣ - 1♠ - X` ✅ (Works - 2 bids)
- `1♣ - 1♠ - Pass - X` ❌ (Fails - still only 2 non-pass bids, but 4 total bids)

**Current:**
```python
non_pass_bids = [b for b in features['auction_history'] if b != 'Pass']
return (len(non_pass_bids) == 2 and ...
```

**Should Check:** Total auction length and position, not just non-pass count
**Impact:** Missing negative doubles in valid situations
**Fix:** Change applicability logic to check position and interference properly

---

### 11. **Negative Doubles: Point Range Not Level-Adjusted**
**File:** `engine/ai/conventions/negative_doubles.py:17`
**Issue:** Always requires only 6+ HCP regardless of level
**SAYC Standard:**
- Through 2♠: 6+ HCP (responding hand)
- 3-level: 8-10+ HCP (invitational values)
- 4-level+: 12+ HCP (game-forcing values)

**Current:** `if hand.hcp >= 6:` (always 6+, regardless of level)
**Impact:** Doubling at too high levels with insufficient strength
**Fix:** Add level-adjusted HCP requirements

---

### 12. **Preempts: Missing Response Logic Completeness**
**File:** `engine/ai/conventions/preempts.py:43-50`
**Issue:** Response logic incomplete
**Missing Scenarios:**
- With 15+ HCP: Bids 2NT (Ogust) but no logic to handle Ogust responses
- With new suit: Should be forcing
- With very strong hand (18+): Should explore slam
- Defensive actions if preempt gets overcalled

**Impact:** Limited responses to partner's preempt
**Fix:** Add comprehensive response structure

---

### 13. **Preempts: No 3-Level or 4-Level Preempts**
**File:** `engine/ai/conventions/preempts.py:23-36`
**Issue:** Only generates 2-level preempts (line 35: `return (f"2{suit}", ...`)
**Missing:**
- 3-level preempts (7-card suit, 6-10 HCP)
- 4-level preempts (8-card suit, 6-10 HCP)
- Vulnerability considerations

**SAYC Standard:**
- 2-level: 6-card suit, 6-10 HCP
- 3-level: 7-card suit, 6-10 HCP
- 4-level: 8-card suit, 6-10 HCP (or 7-card with favorable vulnerability)

**Impact:** Can't make proper 3-level or 4-level preempts
**Fix:** Add 3-level and 4-level preempt logic with suit length checks

---

## 🟡 MODERATE ISSUES (Medium Priority - Suboptimal Bidding)

### 14. **Opening Bids: No Weak Two Preempts**
**File:** `engine/opening_bids.py:6-41`
**Issue:** No logic for weak two bids (2♦, 2♥, 2♠)
**Note:** This is handled by PreemptConvention module, but not integrated into opening_bids
**Impact:** Opening bids module incomplete, relies on preempt module being checked first
**Fix:** Either integrate preempt logic or document dependency clearly

---

### 15. **Opening Bids: No 3NT Gambling or 4-Level Openings**
**File:** `engine/opening_bids.py:11`
**Issue:** Line 11 has 3NT for 25-27 HCP balanced, but missing:
- 3NT Gambling (long solid minor, little outside)
- 4♥/4♠ preemptive openings (8-card suit)
- 4NT Blackwood opening (rare but exists)

**Impact:** Missing some rare but valid opening bids
**Fix:** Add gambling 3NT and 4-level preemptive openings (low priority)

---

### 16. **Responses: Missing Jump Shift Responses**
**File:** `engine/responses.py:113-149`
**Issue:** No logic for jump shift responses (e.g., 1♥ - 3♣)
**SAYC Standard:** Jump shift shows 17+ HCP, game-forcing, typically 5+ card suit
**Example:** 1♥ - 3♣ (not 2♣) shows very strong hand

**Impact:** Can't show strong hands with jump shifts
**Fix:** Add jump shift detection and logic (requires 17+ HCP, 5+ suit)

---

### 17. **Responses: Missing 2NT Response**
**File:** `engine/responses.py:113-149`
**Issue:** No logic for 2NT response to 1-level suit opening
**SAYC Standard:** 2NT response shows 11-12 HCP, balanced, no fit, forcing to game
**Example:** 1♠ - 2NT

**Impact:** With 11-12 HCP balanced, bids 1NT (showing only 6-9) or a suit
**Fix:** Add 2NT response logic before 1NT response check

---

### 18. **Responses: Missing Inverted Minors**
**File:** `engine/responses.py:91-128`
**Issue:** No support for inverted minor raises
**Inverted Minors:** 1♣ - 2♣ or 1♦ - 2♦ shows 10+ HCP, 5+ card fit, game-forcing (inverse of major raises)
**Note:** This is an optional convention in SAYC, but commonly played
**Impact:** Can't use inverted minor raises
**Fix:** Add inverted minor logic (optional, document if not implementing)

---

### 19. **Rebids: No Reverse Bid Logic**
**File:** `engine/rebids.py:32-97`
**Issue:** No specific handling of reverse bids
**Reverse Bid:** Opener bids higher-ranking suit at 2-level (e.g., 1♣ - 1♠ - 2♦)
**SAYC Standard:** Reverse shows 17+ HCP, forcing one round, shows 5-4 distribution minimum

**Current:** May bid reverses without checking if hand qualifies
**Impact:** May reverse with minimum hands or not reverse when appropriate
**Fix:** Add reverse detection and 17+ HCP requirement

---

### 20. **Rebids: Missing 2NT Rebid After 1-Level Response**
**File:** `engine/rebids.py:61-73`
**Issue:** After 1-level response (e.g., 1♣ - 1♥), no logic for opener to rebid 2NT
**SAYC Standard:** 2NT rebid shows 18-19 HCP, balanced
**Example:** 1♣ - 1♥ - 2NT (shows 18-19 HCP, balanced, too strong for 1NT opening)

**Current:** Line 73 bids 1NT with 12-14 HCP, but no 2NT with 18-19
**Impact:** Can't show 18-19 HCP balanced hands properly
**Fix:** Add 2NT rebid logic for 18-19 HCP before other rebids

---

### 21. **Rebids: Missing 3NT Rebid**
**File:** `engine/rebids.py:86-102`
**Issue:** With 19+ points, jumps to 3NT only as fallback (line 102)
**Problem:** Should check for balanced hand and appropriate range first
**SAYC Standard:** 3NT rebid shows 19-20 HCP, balanced

**Current:** Only bids 3NT as last resort without checking if hand is balanced
**Impact:** May bid 3NT with unbalanced hands
**Fix:** Check `hand.is_balanced` and HCP range before bidding 3NT

---

### 22. **Overcalls: Missing Jump Overcalls (Weak and Intermediate)**
**File:** `engine/overcalls.py:180-182`
**Issue:** Lines 180-182 explicitly skip 3-level overcalls
**Missing:**
- Weak jump overcall (e.g., 1♥ - 2♠): 6-10 HCP, 6-card suit, preemptive
- Intermediate jump overcall (e.g., 1♥ - 2♠): 11-14 HCP, 6-card suit (partnership dependent)

**SAYC Standard:** Weak jump overcalls are standard
**Impact:** Can't make weak jump overcalls
**Fix:** Add weak jump overcall logic (check for 6-card suit, 6-10 HCP)

---

### 23. **Overcalls: Missing Cuebid Overcall**
**File:** `engine/overcalls.py:59-77`
**Issue:** No logic for Michaels Cuebid (immediate cuebid of opponent's suit)
**Note:** This should be in michaels_cuebid.py, but that file is empty
**Example:** 1♥ - 2♥ (Michaels, showing spades + minor)

**Impact:** Can't show two-suited hands with cuebid
**Fix:** Implement michaels_cuebid.py module

---

### 24. **Advancer: Very Minimal Logic**
**File:** `engine/advancer_bids.py:7-37`
**Issue:** Only 2 actions: raise partner or cuebid
**Missing:**
- New suit bids (non-forcing)
- NT bids after partner's suit overcall
- Jump raises (preemptive vs invitational)
- Negative free bids
- Responsive doubles (after partner's takeout double)

**Impact:** Very limited advancer actions
**Fix:** Add comprehensive advancer bidding structure

---

### 25. **Advancer: Cuebid Always Game-Forcing**
**File:** `engine/advancer_bids.py:33-35`
**Issue:** Cuebid logic (lines 33-35) shows cuebid with 12+ HCP
**Problem:** This is correct, but no alternative for invitational hands (10-11 HCP)
**Missing:** With 10-11 HCP and fit, should make invitational raise, not cuebid

**Impact:** Over-aggressive cuebids
**Fix:** Add invitational raise option before cuebid

---

## 🟢 MINOR ISSUES (Low Priority - Edge Cases or Documentation)

### 26. **Opening Bids: Tie-Breaking for Equal Length Suits**
**File:** `engine/opening_bids.py:36-39`
**Issue:** Lines 36-39 open longer minor, but with equal minors always opens 1♣
**SAYC Guideline:** With 3-3 minors, open 1♣; with 4-4, depends on hand strength/shape
**Current:** Always opens 1♣ with equal minors (line 38-39)

**Impact:** Minor issue, current behavior is acceptable for 3-3
**Fix:** Add note about 4-4 minor considerations (optional)

---

### 27. **Overcalls: No Defense Against Preempts**
**File:** `engine/overcalls.py:28-47`
**Issue:** Overcall logic doesn't adjust for opponent's preempt
**Example:** After opponent opens 3♦, different requirements for 3♥ overcall
**Impact:** May overcall preempts with insufficient strength
**Fix:** Add preempt-specific overcall adjustments (low priority)

---

### 28. **Takeout Doubles: No Support Doubles**
**File:** `engine/ai/conventions/takeout_doubles.py`
**Issue:** No logic for support doubles (showing 3-card support after partner responds)
**Support Double:** Partner opens, we respond, RHO overcalls, opener doubles to show 3-card support
**Example:** 1♣ - (P) - 1♥ - (1♠) - X (shows 3-card heart support)

**Impact:** Can't show 3-card support with support double
**Fix:** Add support double logic (advanced convention, low priority)

---

### 29. **Negative Doubles: Missing Responsive Doubles**
**File:** `engine/ai/conventions/negative_doubles.py`
**Issue:** Negative doubles only handle immediate position, not responsive situations
**Responsive Double:** Partner makes takeout double, RHO raises, we double
**Example:** 1♥ - (X) - 2♥ - (X) = responsive double

**Impact:** Can't make responsive doubles
**Fix:** Add responsive double logic (low priority, advanced)

---

## 📝 PLACEHOLDER MODULES (Need Implementation)

### 30. **Michaels Cuebid - Empty File**
**File:** `engine/ai/conventions/michaels_cuebid.py`
**Status:** Placeholder only (1 line)
**Required Implementation:**
- After 1♣/1♦: 2♣/2♦ shows both majors (5-5+)
- After 1♥: 2♥ shows spades + minor (5-5+)
- After 1♠: 2♠ shows hearts + minor (5-5+)
- 8-16 HCP range
- Partner asks for minor with 2NT if needed

---

### 31. **Unusual 2NT - Empty File**
**File:** `engine/ai/conventions/unusual_2nt.py`
**Status:** Placeholder only (1 line)
**Required Implementation:**
- After major opening: 2NT shows both minors (5-5+)
- 8-16 HCP range
- Responder picks a minor (or bids game with strong hand)

---

### 32. **Splinter Bids - Empty File**
**File:** `engine/ai/conventions/splinter_bids.py`
**Status:** Placeholder only (1 line)
**Required Implementation:**
- Double jump in new suit shows:
  * 4+ card support for partner's suit
  * Game-forcing values (12-15+ HCP)
  * Singleton or void in bid suit
- Example: 1♠ - 4♣ (shows spade support, club singleton, game forcing)

---

### 33. **Fourth Suit Forcing - Empty File**
**File:** `engine/ai/conventions/fourth_suit_forcing.py`
**Status:** Placeholder only (1 line)
**Required Implementation:**
- After 3 suits bid, 4th suit is artificial game force
- Example: 1♦ - 1♥ - 1♠ - 2♣ (4th suit forcing)
- Asks opener to further describe hand
- Responder has 12+ HCP, no clear bid

---

## 📊 SUMMARY STATISTICS

**Total Issues Identified:** 33

**By Severity:**
- 🔴 Critical: 13 issues
- 🟡 Moderate: 12 issues
- 🟢 Minor: 4 issues
- 📝 Placeholders: 4 modules

**By Module:**
| Module | Critical | Moderate | Minor | Total |
|--------|----------|----------|-------|-------|
| Jacoby Transfers | 2 | 0 | 0 | 2 |
| Stayman | 2 | 0 | 0 | 2 |
| Blackwood | 4 | 0 | 0 | 4 |
| Takeout Doubles | 2 | 0 | 1 | 3 |
| Negative Doubles | 2 | 0 | 1 | 3 |
| Preempts | 2 | 0 | 0 | 2 |
| Responses | 0 | 3 | 0 | 3 |
| Rebids | 0 | 3 | 0 | 3 |
| Opening Bids | 0 | 1 | 1 | 2 |
| Overcalls | 0 | 2 | 1 | 3 |
| Advancer | 0 | 2 | 0 | 2 |
| Placeholders | 4 | 0 | 0 | 4 |

---

## 🎯 RECOMMENDED FIX ORDER

### Phase 1: Critical Fixes (Breaks correct bidding)
1. ✅ **Fix #1-2:** Takeout Doubles HCP and interface
2. ✅ **Fix #3:** Jacoby post-transfer continuations
3. ✅ **Fix #4-5:** Stayman responder rebids
4. ✅ **Fix #6:** Jacoby super-accept logic (currently backwards!)
5. ✅ **Fix #7-9:** Blackwood trigger and follow-up
6. ✅ **Fix #10-11:** Negative Doubles applicability and levels
7. ✅ **Fix #12-13:** Preempts responses and 3/4-level

### Phase 2: Moderate Fixes (Suboptimal but functional)
8. ✅ **Fix #16-17:** Add jump shifts and 2NT responses
9. ✅ **Fix #19-21:** Rebids: reverses, 2NT, 3NT improvements
10. ✅ **Fix #22:** Weak jump overcalls
11. ✅ **Fix #24-25:** Advancer bidding expansion

### Phase 3: Placeholder Implementations
12. ✅ **Fix #30:** Michaels Cuebid
13. ✅ **Fix #31:** Unusual 2NT
14. ✅ **Fix #32:** Splinter Bids
15. ✅ **Fix #33:** Fourth Suit Forcing

### Phase 4: Minor Fixes (Low priority)
16. ✅ **Fix #26-29:** Edge cases and advanced conventions

---

## ✅ TESTING REQUIREMENTS

Each fix should include:
1. **Unit test** demonstrating the issue
2. **Unit test** demonstrating the fix
3. **Integration test** with full auction
4. **Hand generation** test for relevant scenarios

**Suggested Test Coverage:**
- Minimum: Fix the issue shown in the test
- Standard: Cover main use cases for the convention
- Comprehensive: Cover edge cases and interactions

---

## 📚 REFERENCE MATERIALS

**SAYC Reference:**
- Official SAYC document: http://www.acbl.org/learn_page/how-to-play-bridge/
- SAYC booklet (2018 edition)

**Testing Against:**
- Bridge World Standard (BWS) as comparison
- Common bridge practice guides
- User-reported issues and review requests

---

**Document Version:** 1.0
**Last Updated:** 2025-10-10
**Reviewed By:** Claude Code Agent
**Next Review:** After Phase 1 completion

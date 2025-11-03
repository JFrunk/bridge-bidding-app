# Bridge Bidding System - Example Auctions

**System:** Standard American Yellow Card (SAYC)
**Format:** Practical bidding sequences with hand diagrams and AI reasoning

---

## SECTION 1: STANDARD OPENING BIDS

### Example 1.1: Balanced 1NT Opening

**Hand (South):**
```
♠ K Q 7
♥ A J 9
♦ K 10 8 4
♣ Q 6 3
```
**HCP:** 15 | **Shape:** 4-3-3-3 (balanced)

**Auction:**
| North | East | South | West |
|-------|------|-------|------|
| - | - | **1NT** | Pass |

**AI Reasoning:**
- 15 HCP (in 15-17 range for 1NT)
- Balanced distribution (4-3-3-3)
- No 5-card major (would bid 1♥/1♠ with 5)
- Opens 1NT to describe hand precisely

---

### Example 1.2: 5-Card Major Opening

**Hand (South):**
```
♠ A K 10 8 4
♥ Q 6
♦ K 9 7
♣ J 10 5
```
**HCP:** 13 | **Shape:** 5-3-3-2

**Auction:**
| North | East | South | West |
|-------|------|-------|------|
| - | - | **1♠** | Pass |

**AI Reasoning:**
- 13 HCP (opening values)
- 5-card spade suit (always open 5-card majors)
- Opens 1♠ (SAYC requires 5+ for major openings)

---

### Example 1.3: Better Minor Opening

**Hand (South):**
```
♠ K 10 7
♥ A Q 9
♦ K 8 4
♣ Q 10 6 3
```
**HCP:** 13 | **Shape:** 4-3-3-3

**Auction:**
| North | East | South | West |
|-------|------|-------|------|
| - | - | **1♣** | Pass |

**AI Reasoning:**
- 13 HCP (opening values)
- Balanced but not 1NT range (too weak)
- No 5-card major
- Opens better minor (1♣ with 4 clubs vs 3 diamonds)

---

### Example 1.4: Weak Two Preempt

**Hand (South):**
```
♠ K Q J 10 8 7
♥ 9 4
♦ 10 8 5
♣ 7 2
```
**HCP:** 8 | **Shape:** 6-2-3-2

**Auction:**
| North | East | South | West |
|-------|------|-------|------|
| - | - | **2♠** | Pass |

**AI Reasoning:**
- 8 HCP (in 6-10 range for weak two)
- Good 6-card spade suit (3 honors)
- Preempts to obstruct opponents and describe hand
- Not vulnerable (would be more conservative if vulnerable)

---

## SECTION 2: RESPONSES TO 1NT

### Example 2.1: Stayman with 4-Card Major

**Partner's Hand (North):**
```
♠ A 10 6
♥ K Q 8
♦ A J 9 4
♣ K 7 3
```
**HCP:** 16 (1NT opener)

**Your Hand (South):**
```
♠ K 9 7 4
♥ A 6 5
♦ 10 8 3
♣ Q 10 4
```
**HCP:** 10 | **Shape:** 4-3-3-3

**Auction:**
| North | East | South | West |
|-------|------|-------|------|
| 1NT | Pass | **2♣** | Pass |
| 2♠ | Pass | **3NT** | Pass |

**AI Reasoning:**
- South: 10 HCP (game values with 1NT)
- South: 4-card spade suit → use Stayman to find 4-4 fit
- North: 4 spades → bid 2♠
- South: Spade fit found, enough for game → bid 3NT (could also bid 4♠)

---

### Example 2.2: Jacoby Transfer with 5-Card Major

**Partner's Hand (North):**
```
♠ K J 9
♥ A Q 7
♦ K 10 8 4
♣ Q 6 3
```
**HCP:** 15 (1NT opener)

**Your Hand (South):**
```
♠ 6 4
♥ K 10 9 6 5
♦ A 7 3
♣ J 10 8
```
**HCP:** 9 | **Shape:** 2-5-3-3

**Auction:**
| North | East | South | West |
|-------|------|-------|------|
| 1NT | Pass | **2♦** | Pass |
| 2♥ | Pass | **3NT** | Pass |

**AI Reasoning:**
- South: 9 HCP, 5-card heart suit → use Jacoby Transfer (2♦ = hearts)
- North: Forced to accept transfer → bid 2♥
- South: Game values (9+15=24), but only 5-card suit → bid 3NT instead of 4♥
- **Note:** With 6+ hearts would bid 4♥

---

### Example 2.3: Jacoby Transfer Priority Over Stayman

**Partner's Hand (North):**
```
♠ A Q 8
♥ K 10 9
♦ A J 7 3
♣ K 8 4
```
**HCP:** 17 (1NT opener)

**Your Hand (South):**
```
♠ K J 10 9 7
♥ Q 8 6 4
♦ 6 5
♣ 10 3
```
**HCP:** 7 | **Shape:** 5-4-2-2

**Auction:**
| North | East | South | West |
|-------|------|-------|------|
| 1NT | Pass | **2♥** | Pass |
| 2♠ | Pass | **Pass** | - |

**AI Reasoning:**
- South: 5 spades, 4 hearts → Jacoby Transfer takes priority
- South: 7 HCP (invitational values) → transfer to spades with 2♥
- North: Accepts transfer → bid 2♠
- South: Weak hand, satisfied with 2♠ → Pass
- **Note:** With 5+ major, always transfer rather than Stayman

---

## SECTION 3: SUIT OPENING RESPONSES

### Example 3.1: Simple Raise with Support

**Partner's Hand (North):**
```
♠ K Q 10 8 4
♥ A 7
♦ K J 9
♣ Q 10 5
```
**HCP:** 14 (1♠ opener)

**Your Hand (South):**
```
♠ J 9 6
♥ K 10 8
♦ A 7 4 3
♣ 9 6 2
```
**HCP:** 8 | **Shape:** 3-3-4-3

**Auction:**
| North | East | South | West |
|-------|------|-------|------|
| 1♠ | Pass | **2♠** | Pass |
| Pass | - | - | - |

**AI Reasoning:**
- South: 8 HCP, 3-card spade support → simple raise to 2♠
- South: Not enough for limit raise (10-12 HCP)
- North: Minimum opening (14 HCP) → Pass
- **Note:** With 10-12 HCP, would bid 3♠ (limit raise)

---

### Example 3.2: Limit Raise (Invitational)

**Partner's Hand (North):**
```
♠ A K 10 8 4
♥ K Q 7
♦ 9 6
♣ A 10 8
```
**HCP:** 15 (1♠ opener)

**Your Hand (South):**
```
♠ Q 9 6
♥ A 10 8
♦ K J 7 4
♣ 9 6 2
```
**HCP:** 10 | **Shape:** 3-3-4-3

**Auction:**
| North | East | South | West |
|-------|------|-------|------|
| 1♠ | Pass | **3♠** | Pass |
| **4♠** | Pass | Pass | - |

**AI Reasoning:**
- South: 10 HCP, 3-card spade support → limit raise to 3♠ (10-12 HCP)
- North: 15 HCP + fit = enough for game → accept invitation, bid 4♠
- **Note:** With 13+ HCP, South would bid 4♠ directly

---

### Example 3.3: New Suit Response (Forcing 1 Round)

**Partner's Hand (North):**
```
♠ K 8
♥ A 10 7
♦ K Q 10 8 4
♣ Q 9 6
```
**HCP:** 13 (1♦ opener)

**Your Hand (South):**
```
♠ A J 10 9 7
♥ K 8 6
♦ 7 4
♣ K 10 3
```
**HCP:** 11 | **Shape:** 5-3-2-3

**Auction:**
| North | East | South | West |
|-------|------|-------|------|
| 1♦ | Pass | **1♠** | Pass |
| 1NT | Pass | **3NT** | Pass |

**AI Reasoning:**
- South: 11 HCP, 5-card spade suit → bid 1♠ (forcing 1 round)
- North: No spade fit, balanced → rebid 1NT (12-14 HCP)
- South: Game values (11+13=24), balanced → bid 3NT
- **Note:** Bidding new suit at 1-level is forcing for 1 round

---

### Example 3.4: Jump Shift (Strong, Game-Forcing)

**Partner's Hand (North):**
```
♠ K 10 8
♥ A Q J 9 7
♦ K 6
♣ Q 10 4
```
**HCP:** 14 (1♥ opener)

**Your Hand (South):**
```
♠ A Q J 9 7 4
♥ K 8
♦ A 10 5
♣ K 7
```
**HCP:** 17 | **Shape:** 6-2-3-2

**Auction:**
| North | East | South | West |
|-------|------|-------|------|
| 1♥ | Pass | **2♠** | Pass |
| 3♥ | Pass | **4♥** | Pass |

**AI Reasoning:**
- South: 17 HCP, 6-card spade suit → jump shift to 2♠ (game-forcing)
- North: Shows heart rebid (6+ hearts) → bid 3♥
- South: Heart fit found, game values → bid 4♥
- **Note:** Jump shift (1♥-2♠) shows 17+ HCP and is game-forcing

---

## SECTION 4: COMPETITIVE BIDDING

### Example 4.1: Simple 1-Level Overcall

**RHO's Hand (East):**
```
♠ A K 10 7
♥ K 9 7
♦ Q J 10 4
♣ 8 6
```
**HCP:** 13 (1♦ opener)

**Your Hand (South):**
```
♠ 8 4
♥ A Q J 10 8
♦ 9 6 3
♣ K 10 7
```
**HCP:** 11 | **Shape:** 2-5-3-3

**Auction:**
| North | East | South | West |
|-------|------|-------|------|
| Pass | 1♦ | **1♥** | Pass |

**AI Reasoning:**
- South: 11 HCP, good 5-card heart suit → overcall 1♥
- South: In range for 1-level overcall (8-16 HCP)
- South: Suit quality is good (3 honors)
- **Note:** Would not overcall with poor suit quality or <8 HCP

---

### Example 4.2: Takeout Double

**RHO's Hand (East):**
```
♠ A K J 10 7
♥ 9 6
♦ K Q 10
♣ Q 8 4
```
**HCP:** 14 (1♠ opener)

**Your Hand (South):**
```
♠ 6 4
♥ A Q 10 8
♦ A J 7 4
♣ K 9 6
```
**HCP:** 13 | **Shape:** 2-4-4-3

**Auction:**
| North | East | South | West |
|-------|------|-------|------|
| Pass | 1♠ | **Double** | Pass |
| 2♥ | Pass | **4♥** | Pass |

**AI Reasoning:**
- South: 13 HCP, support for unbid suits (4 hearts, 4 diamonds) → Takeout Double
- North: Forced to bid, chooses hearts → 2♥
- South: Excellent heart fit + opening values → jump to 4♥
- **Note:** Takeout double promises support for unbid suits (not a penalty double)

---

### Example 4.3: Negative Double (Shows Unbid Major)

**Partner's Hand (North):**
```
♠ K Q 8
♥ A 10 7
♦ K 10 9 8 4
♣ 9 6
```
**HCP:** 12 (1♦ opener)

**Your Hand (South):**
```
♠ A 10 9 7
♥ K 8 6 4
♦ 7 3
♣ Q 10 5
```
**HCP:** 9 | **Shape:** 4-4-2-3

**RHO Overcalls:** 1♥

**Auction:**
| North | East | South | West |
|-------|------|-------|------|
| 1♦ | 1♥ | **Double** | Pass |
| 2♠ | Pass | **4♠** | Pass |

**AI Reasoning:**
- South: 9 HCP, 4 spades (unbid major) → Negative Double
- South: Cannot bid 1♠ naturally (would show 6+ HCP and be non-forcing)
- North: 4 spades → bid 2♠
- South: Spade fit found, game values with fit → bid 4♠
- **Note:** Negative double after partner opens and RHO overcalls shows unbid major(s)

---

### Example 4.4: Michaels Cuebid (Both Majors)

**RHO's Hand (East):**
```
♠ K 10 7
♥ 9 6
♦ A K Q 10 8
♣ Q 9 6
```
**HCP:** 13 (1♦ opener)

**Your Hand (South):**
```
♠ A Q 10 8 4
♥ K J 9 7 3
♦ 6
♣ 10 8
```
**HCP:** 10 | **Shape:** 5-5-1-2

**Auction:**
| North | East | South | West |
|-------|------|-------|------|
| Pass | 1♦ | **2♦** | Pass |
| 2♠ | Pass | **4♠** | Pass |

**AI Reasoning:**
- South: 10 HCP, 5-5 in both majors → Michaels Cuebid (2♦)
- South: Cuebidding opponent's suit shows both majors
- North: Prefers spades → bid 2♠
- South: Game values with fit → bid 4♠
- **Note:** 2♦ over 1♦ is Michaels (artificial), showing both majors 5-5+

---

### Example 4.5: Unusual 2NT (Both Minors)

**RHO's Hand (East):**
```
♠ A K J 10 7
♥ K Q 9
♦ 10 8
♣ Q 9 4
```
**HCP:** 13 (1♠ opener)

**Your Hand (South):**
```
♠ 6 4
♥ 8
♦ A Q 10 9 7
♣ K J 10 8 4
```
**HCP:** 10 | **Shape:** 2-1-5-5

**Auction:**
| North | East | South | West |
|-------|------|-------|------|
| Pass | 1♠ | **2NT** | Pass |
| 3♦ | Pass | **5♦** | Pass |

**AI Reasoning:**
- South: 10 HCP, 5-5 in both minors → Unusual 2NT
- South: 2NT over major opening is artificial, showing both minors 5-5+
- North: Prefers diamonds → bid 3♦
- South: Good fit + distributional values → bid 5♦ (competitive)
- **Note:** 2NT after opponent opens major is Unusual 2NT (not natural)

---

## SECTION 5: SLAM BIDDING

### Example 5.1: Blackwood Ace-Asking

**Partner's Hand (North):**
```
♠ K Q 10 8 4
♥ A K 7
♦ K Q 9
♣ 10 6
```
**HCP:** 17 (1♠ opener)

**Your Hand (South):**
```
♠ A J 9 7 3
♥ Q 8 6
♦ A J 10
♣ K 7
```
**HCP:** 14 | **Shape:** 5-3-3-2

**Auction:**
| North | East | South | West |
|-------|------|-------|------|
| 1♠ | Pass | 3♠ | Pass |
| **4NT** | Pass | 5♥ | Pass |
| **6♠** | Pass | Pass | - |

**AI Reasoning:**
- South: 14 HCP, 5-card spade support → limit raise to 3♠
- North: 17 HCP + fit = slam interest → bid 4NT (Blackwood)
- South: 2 aces → respond 5♥
- North: 2 aces + 2 = 4 aces, 1 king missing → bid 6♠ (small slam)
- **Note:** 4NT after suit agreement is always Blackwood (ace-asking)

---

### Example 5.2: Splinter Bid (Showing Shortness)

**Partner's Hand (North):**
```
♠ A K J 10 7
♥ K Q 9
♦ A 10 8
♣ 9 6
```
**HCP:** 16 (1♠ opener)

**Your Hand (South):**
```
♠ Q 9 6 3
♥ A 10 8 7
♦ K Q J
♣ 7
```
**HCP:** 13 | **Shape:** 4-4-3-1

**Auction:**
| North | East | South | West |
|-------|------|-------|------|
| 1♠ | Pass | **4♣** | Pass |
| 4NT | Pass | 5♦ | Pass |
| **6♠** | Pass | Pass | - |

**AI Reasoning:**
- South: 13 HCP, 4-card spade support, singleton club → Splinter Bid (4♣)
- South: 4♣ is artificial, shows spade support + club shortness + slam interest
- North: Excellent fit, wasted values in clubs minimal → bid 4NT (Blackwood)
- South: 1 ace → respond 5♦
- North: Enough aces + good fit → bid 6♠
- **Note:** Double jump in new suit = Splinter (shows shortness, 4+ support, slam interest)

---

## SECTION 6: SPECIAL CONVENTIONS

### Example 6.1: Fourth Suit Forcing

**Partner's Hand (North):**
```
♠ K 8
♥ A Q 10 7
♦ K Q 10 8 4
♣ 9 6
```
**HCP:** 13 (1♦ opener)

**Your Hand (South):**
```
♠ A Q 10 9
♥ 9 6
♦ A J 7
♣ K 10 8 4
```
**HCP:** 13 | **Shape:** 4-2-3-4

**Auction:**
| North | East | South | West |
|-------|------|-------|------|
| 1♦ | Pass | 1♠ | Pass |
| 2♥ | Pass | **3♣** | Pass |
| 3NT | Pass | Pass | - |

**AI Reasoning:**
- South: 13 HCP, 4 spades → bid 1♠
- North: 13 HCP, 4 hearts → rebid 2♥ (reverse, 16+ would be forcing)
- South: No fit found, game interest → bid 3♣ (Fourth Suit Forcing, artificial)
- South: Asking partner to describe hand further
- North: Balanced, diamond stopper → bid 3NT
- **Note:** When 3 suits have been bid naturally, bidding the 4th suit is artificial (game-forcing)

---

## SECTION 7: OPENER'S REBIDS

### Example 7.1: Minimum Rebid (13-15 HCP)

**Your Hand (North):**
```
♠ K 10 7
♥ A Q 10 8 7 4
♦ K 9
♣ 9 6
```
**HCP:** 13 | **Shape:** 3-6-2-2

**Partner's Hand (South):**
```
♠ A 9 6
♥ K 6
♦ Q 10 8 4
♣ K 10 7 3
```
**HCP:** 11

**Auction:**
| North | East | South | West |
|-------|------|-------|------|
| **1♥** | Pass | 1NT | Pass |
| **2♥** | Pass | Pass | - |

**AI Reasoning:**
- North: 13 HCP, 6 hearts → open 1♥
- South: 11 HCP, no heart fit, balanced → respond 1NT
- North: Minimum hand (13), 6-card suit → rebid 2♥ (non-forcing)
- South: No fit, minimum → Pass
- **Note:** Simple rebid of same suit shows minimum hand with 6+ cards

---

### Example 7.2: Jump Rebid (Invitational, 16-18 HCP)

**Your Hand (North):**
```
♠ A K J 10 8 7
♥ K Q 9
♦ A 10
♣ 9 6
```
**HCP:** 16 | **Shape:** 6-3-2-2

**Partner's Hand (South):**
```
♠ 9 6
♥ A 10 8
♦ K Q 8 4
♣ K 10 7 3
```
**HCP:** 11

**Auction:**
| North | East | South | West |
|-------|------|-------|------|
| **1♠** | Pass | 1NT | Pass |
| **3♠** | Pass | 4♠ | Pass |

**AI Reasoning:**
- North: 16 HCP, 6 spades → open 1♠
- South: 11 HCP, no spade fit, balanced → respond 1NT
- North: Invitational hand (16), 6-card suit → jump rebid 3♠
- South: Maximum for 1NT response + 2-card support → accept invitation, bid 4♠
- **Note:** Jump rebid in same suit shows 16-18 HCP, invitational

---

### Example 7.3: Reverse (16+ HCP, Forcing)

**Your Hand (North):**
```
♠ A K 10 7
♥ 9 6
♦ A K Q 10 8
♣ Q 9
```
**HCP:** 17 | **Shape:** 4-2-5-2

**Partner's Hand (South):**
```
♠ 9 6 3
♥ A 10 8 4
♦ 9 7
♣ K 10 8 7
```
**HCP:** 8

**Auction:**
| North | East | South | West |
|-------|------|-------|------|
| **1♦** | Pass | 1♥ | Pass |
| **1♠** | Pass | 1NT | Pass |
| Pass | - | - | - |

**AI Reasoning:**
- North: 17 HCP, 5 diamonds → open 1♦
- South: 8 HCP, 4 hearts → respond 1♥
- North: 17 HCP, 4 spades → reverse to 1♠ (shows 16+ HCP)
- South: Minimum hand, no fit → bid 1NT (forced)
- North: No fit found, minimum → Pass
- **Note:** Reverse (bidding higher-ranking suit at 2-level) shows 16+ HCP, forcing 1 round

---

## SECTION 8: COMMON MISTAKES TO AVOID

### Example 8.1: CORRECT - Jacoby Transfer Priority

**Hand:**
```
♠ K Q 10 9 7
♥ A 8 6 4
♦ 7 3
♣ 10 8
```
**HCP:** 10 | **Partner Opened:** 1NT

**CORRECT Auction:**
```
1NT - 2♥ (Jacoby Transfer to spades)
```

**INCORRECT Auction:**
```
1NT - 2♣ (Stayman) ← WRONG
```

**Reason:** With 5+ card major, always use Jacoby Transfer instead of Stayman

---

### Example 8.2: CORRECT - Don't Preempt with Opening Values

**Hand:**
```
♠ K Q J 10 8 7
♥ A K 9
♦ 10 8
♣ 7 2
```
**HCP:** 12 | **Shape:** 6-3-2-2

**CORRECT Opening:**
```
1♠ ← Correct (12 HCP is too strong for preempt)
```

**INCORRECT Opening:**
```
2♠ ← WRONG (preempts are 6-10 HCP)
```

**Reason:** Preempts show weak hands (6-10 HCP). With 12+ HCP, open at 1-level.

---

### Example 8.3: CORRECT - Support Partner Before Bidding Own Suit

**Partner's Hand:** Opened 1♥

**Your Hand:**
```
♠ A Q 10 9 7
♥ K 8 6
♦ Q 10 4
♣ 9 7
```
**HCP:** 11 | **Shape:** 5-3-3-2

**CORRECT Response:**
```
1♥ - 3♥ ← Correct (show heart support, limit raise)
```

**INCORRECT Response:**
```
1♥ - 1♠ ← Suboptimal (denies 3-card heart support)
```

**Reason:** With 3+ card support and limit raise values, raise partner immediately rather than bidding own suit.

---

## SECTION 9: EDGE CASES AND SPECIAL SITUATIONS

### Example 9.1: Responding to Partner's Takeout Double with Weak Hand

**Partner's Hand (North):** Doubled opponent's 1♥

**Your Hand (South):**
```
♠ 10 8 6 4
♥ 9 7
♦ J 10 8 4
♣ 9 6 3
```
**HCP:** 2 | **Shape:** 4-2-4-3

**Auction:**
| North | East | South | West |
|-------|------|-------|------|
| Pass | 1♥ | Pass | Pass |
| **Double** | Pass | **1♠** | Pass |

**AI Reasoning:**
- North: Takeout double → asks partner to bid
- South: Forced to bid even with 2 HCP → bid longest suit (1♠)
- **Note:** After partner's takeout double, you MUST bid even with 0 HCP

---

### Example 9.2: Passing Partner's Penalty Double

**Partner's Hand (North):**
```
♠ A K Q 10
♥ K Q J 9
♦ A 10 8
♣ 9 6
```
**HCP:** 18

**Your Hand (South):**
```
♠ 9 6
♥ 10 8 7
♦ K Q 9 7
♣ K 10 8 4
```
**HCP:** 8

**Opponent Opens:** 1NT (15-17)

**Auction:**
| North | East | South | West |
|-------|------|-------|------|
| Pass | Pass | Pass | 1NT |
| **Double** | Pass | **Pass** | Pass |

**AI Reasoning:**
- West: Opens 1NT
- North: 18 HCP → penalty double (shows 15+ HCP)
- South: Pass for penalty (converting to penalty)
- **Note:** Double of 1NT is penalty, not takeout. Pass with any values.

---

## SECTION 10: REVIEW CHECKLIST

Use these auctions to verify:

**Opening Bids:**
- [ ] 1NT shows 15-17 balanced (Example 1.1)
- [ ] 5-card majors required for 1♥/1♠ (Example 1.2)
- [ ] Better minor with no 5-card major (Example 1.3)
- [ ] Weak twos show 6-10 HCP (Example 1.4)

**1NT Responses:**
- [ ] Stayman with 4-card major, 8+ HCP (Example 2.1)
- [ ] Jacoby Transfer with 5+ major (Example 2.2)
- [ ] Transfer priority over Stayman (Example 2.3)

**Competitive Bidding:**
- [ ] 1-level overcalls: 8-16 HCP (Example 4.1)
- [ ] Takeout doubles: 12+ HCP, unbid suit support (Example 4.2)
- [ ] Negative doubles: unbid majors after RHO overcall (Example 4.3)
- [ ] Michaels: 2♦ over 1♦ shows both majors (Example 4.4)
- [ ] Unusual 2NT: shows both minors (Example 4.5)

**Slam Bidding:**
- [ ] Blackwood: 4NT asks for aces (Example 5.1)
- [ ] Splinter: double jump shows shortness + support (Example 5.2)

**Special Conventions:**
- [ ] Fourth Suit Forcing: artificial, game-forcing (Example 6.1)

---

**END OF EXAMPLE AUCTIONS**

For comprehensive rules and tables, see:
- `BIDDING_SYSTEM_CONVENTION_CARD.md` (complete convention card)
- `BIDDING_SYSTEM_QUICK_REFERENCE.md` (lookup tables)

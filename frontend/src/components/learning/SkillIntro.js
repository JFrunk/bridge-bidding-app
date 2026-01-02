/**
 * Skill Introduction Component
 *
 * Shows educational content explaining a skill before the user starts practicing.
 * Helps beginners understand the concept they're about to learn.
 *
 * Features:
 * - Auto-highlights bridge terms with tooltips (TermHighlight)
 * - Quick access to glossary button
 */

import React, { useState, useEffect, useRef } from 'react';
import './SkillIntro.css';
import { GlossaryDrawer, TermHighlight } from '../glossary';

// Educational content for each skill
const SKILL_CONTENT = {
  // Level 0: Foundations
  hand_evaluation_basics: {
    title: 'Hand Evaluation Basics',
    subtitle: 'Learn to count points in your hand',
    sections: [
      {
        heading: 'Why Point Counting Matters',
        content: `In bridge, you and your partner need to figure out how high to bid based on your combined strength.
Point counting gives you a common language to evaluate hands.`
      },
      {
        heading: 'High Card Points (HCP)',
        content: `Count your honor cards:
• Ace = 4 points
• King = 3 points
• Queen = 2 points
• Jack = 1 point

A deck has 40 total HCP. An "average" hand has 10 HCP.`
      },
      {
        heading: 'Distribution Points',
        content: `Long and short suits add value:
• Void (0 cards) = 3 points
• Singleton (1 card) = 2 points
• Doubleton (2 cards) = 1 point

These matter more in suit contracts than notrump.`
      },
      {
        heading: 'Balanced vs Unbalanced',
        content: `A balanced hand has no voids, no singletons, and at most one doubleton.
Common balanced patterns: 4-3-3-3, 4-4-3-2, 5-3-3-2

Balanced hands are good for notrump; unbalanced hands prefer suit contracts.`
      }
    ],
    practice_tip: 'Count the HCP in each hand shown. Remember: A=4, K=3, Q=2, J=1.'
  },

  suit_quality: {
    title: 'Suit Quality',
    subtitle: 'Understanding suit length and ranking',
    sections: [
      {
        heading: 'Why Suit Length Matters',
        content: `Your longest suit is usually your best suit to play in (as trumps).
When you have more cards in a suit than opponents, you control that suit.`
      },
      {
        heading: 'Suit Ranking',
        content: `From lowest to highest:
♣ Clubs (lowest)
♦ Diamonds
♥ Hearts (major suit)
♠ Spades (major suit, highest)
NT Notrump (highest level)

Higher-ranking suits can be bid at the same level. Lower suits need a higher level.`
      },
      {
        heading: 'Major vs Minor Suits',
        content: `♥ Hearts and ♠ Spades are "majors" - they score more points for game.
♣ Clubs and ♦ Diamonds are "minors" - you need more tricks for game.

Major suit game: 4♥ or 4♠ (10 tricks)
Minor suit game: 5♣ or 5♦ (11 tricks)
Notrump game: 3NT (9 tricks)`
      },
      {
        heading: 'Biddable Suits',
        content: `In SAYC, suit length requirements are:
• Major suits (♥/♠): 5+ cards to open or bid a new suit
• Minor suits (♣/♦): 3+ cards to open, 4+ to bid a new suit

For responses, you generally need 4+ cards to bid a new suit at the 1-level.`
      }
    ],
    practice_tip: 'Identify the longest suit in each hand. If two suits tie, the higher-ranking suit is often preferred.'
  },

  bidding_language: {
    title: 'Language of Bidding',
    subtitle: 'Understanding game and slam requirements',
    sections: [
      {
        heading: 'What is a Bid?',
        content: `A bid is a contract to take a certain number of tricks with a specific trump suit (or notrump).
"2♥" means: "I think we can take 8 tricks with hearts as trump."
(6 + the number bid = tricks needed)`
      },
      {
        heading: 'Game Contracts by Type',
        content: `Different games require different tricks:

• 3NT = 9 tricks (notrump game) → ~25 points
• 4♥ or 4♠ = 10 tricks (major game) → ~25 points
• 5♣ or 5♦ = 11 tricks (minor game) → ~29 points

Majors and NT are easier to make game, which is why we prefer them!`
      },
      {
        heading: 'Why Point Thresholds Differ',
        content: `Minors need more tricks for game, so you need more points:

• Majors/NT: 25 points for 9-10 tricks
• Minors: 29 points for 11 tricks

This is why bridge players work hard to find major suit fits or play in NT.`
      },
      {
        heading: 'Slam Bonuses',
        content: `Even bigger bonuses for:
• Small slam (12 tricks): 6-level → ~33 points
• Grand slam (13 tricks): 7-level → ~37 points

These bonuses are substantial - worth trying for with the right points!`
      }
    ],
    practice_tip: 'Key numbers: NT/Majors need ~25, Minors need ~29, Small slam ~33, Grand slam ~37.'
  },

  // Level 1: Opening Bids
  when_to_open: {
    title: 'When to Open',
    subtitle: 'Deciding whether to make the first bid',
    sections: [
      {
        heading: 'The Rule of 20',
        content: `Add your HCP + length of your two longest suits.
If the total is 20 or more, you can open!

Example: 11 HCP with 5-4 shape = 11 + 5 + 4 = 20 ✓`
      },
      {
        heading: 'Standard Opening Requirements',
        content: `Most players open with:
• 12+ HCP with a good suit
• 13+ HCP with any shape
• 11 HCP if you have great shape (5-5 or 6-4)

With fewer than 11 HCP, usually pass.`
      },
      {
        heading: 'Why Open?',
        content: `Opening the bidding:
• Tells partner you have values
• Gets your side into the auction
• Makes it harder for opponents

If you pass, partner may not be able to bid your suit!`
      }
    ],
    practice_tip: 'Decide if each hand meets opening requirements. Consider both points and shape.'
  },

  opening_one_suit: {
    title: 'Opening One of a Suit',
    subtitle: 'Choosing your opening bid',
    sections: [
      {
        heading: 'Which Suit to Open?',
        content: `With one 5+ card suit: Bid that suit
With two 5-card suits: Bid the higher-ranking
With two 4-card suits: Usually bid the lower-ranking minor

1♣ often shows clubs OR just 12-21 HCP with no better bid.`
      },
      {
        heading: 'Major vs Minor Priority',
        content: `Finding a major suit fit (♥ or ♠) is a key goal.
But you don't need to have a major to open!

Open your longest suit first - partner will help find the fit.`
      }
    ],
    practice_tip: 'Choose the best opening bid based on your suit length and strength.'
  },

  opening_1nt: {
    title: 'Opening 1NT',
    subtitle: 'The balanced hand opening',
    sections: [
      {
        heading: '1NT Requirements',
        content: `Open 1NT with:
• 15-17 HCP (exact range may vary)
• Balanced shape (4-3-3-3, 4-4-3-2, or 5-3-3-2)
• Stoppers in most suits help

1NT is very descriptive - partner knows a lot immediately!`
      },
      {
        heading: 'Why 1NT is Powerful',
        content: `1NT tells partner exactly what you have:
• Point range (15-17)
• Shape (balanced)
• No long major suit

Partner can often place the final contract.`
      }
    ],
    practice_tip: 'Identify hands that qualify for a 1NT opening: balanced shape with 15-17 HCP.'
  },

  opening_2c_strong: {
    title: 'Opening 2♣ (Strong)',
    subtitle: 'The game-forcing opening',
    sections: [
      {
        heading: 'When to Open 2♣',
        content: `Open 2♣ with VERY strong hands:
• 22+ HCP balanced, OR
• 9+ playing tricks with a long suit

2♣ is artificial - it doesn't promise clubs!
It says: "Partner, we're going to game no matter what."`
      },
      {
        heading: 'Responding to 2♣',
        content: `Partner MUST respond (even with 0 points):
• 2♦ = "waiting" (shows nothing)
• 2♥/2♠/3♣/3♦ = good 5+ card suit with 2 of top 3 honors
• 2NT = 8+ HCP, balanced`
      }
    ],
    practice_tip: 'Recognize the rare 2♣ opening hands - they\'re very strong!'
  },

  opening_2nt: {
    title: 'Opening 2NT',
    subtitle: 'The strong balanced opening',
    sections: [
      {
        heading: '2NT Requirements',
        content: `Open 2NT with:
• 20-21 HCP
• Balanced shape
• Similar to 1NT but stronger

This hand is too strong for 1NT but not quite 2♣ territory.`
      },
      {
        heading: 'After 2NT',
        content: `Partner can use Stayman (3♣) or transfers, just like after 1NT.
With 4+ HCP, partner usually bids game.`
      }
    ],
    practice_tip: 'Identify balanced hands with 20-21 HCP for a 2NT opening.'
  },

  // Level 2: Responding to Partner
  responding_to_major: {
    title: 'Responding to Major Suit Openings',
    subtitle: 'How to respond when partner opens 1♥ or 1♠',
    sections: [
      {
        heading: 'The Priority System',
        content: `When partner opens 1♥ or 1♠, your response depends on:
1. Do you have support (3+ cards) for partner's major?
2. How many points do you have?
3. Do you have a suit of your own to show?

Supporting partner's major is usually the best action when you have fit!`
      },
      {
        heading: 'With Support (3+ Cards)',
        content: `With fit for partner's major, raise based on your points:
• 6-10 points: Raise to 2 (e.g., 1♥ → 2♥)
• 10-12 points: Raise to 3 (invitational)
• 13+ points: Bid game directly (1♥ → 4♥)
• 13+ with good shape: Use Jacoby 2NT (forcing)

An 8-card fit in a major is the holy grail of bidding!`
      },
      {
        heading: 'Without Support',
        content: `Without major support, show your own suit or notrump:
• 1NT: 6-10 points, no fit, no biddable 4-card suit at 1-level
• New suit at 1-level: 6+ points, 4+ cards (e.g., 1♥ → 1♠)
• New suit at 2-level: 10+ points, 4+ cards (forcing)
• 2NT: 13-15 points, balanced, no major fit
• 3NT: 16-17 points, balanced, no major fit`
      },
      {
        heading: 'Why Support Matters',
        content: `Major suit games (4♥/4♠) need only 10 tricks.
With an 8-card fit, you have trump control and can ruff losers.

Key insight: A 6-3 fit is usually better than playing in notrump!
When you find a fit, tell partner immediately.`
      }
    ],
    practice_tip: 'First check for support (3+ cards). With support, raise based on points. Without support, bid your own suit or notrump.'
  },

  responding_to_minor: {
    title: 'Responding to Minor Suit Openings',
    subtitle: 'How to respond when partner opens 1♣ or 1♦',
    sections: [
      {
        heading: 'Minor Opens are Different',
        content: `When partner opens 1♣ or 1♦, your priorities shift:
1. Look for a 4-card major to bid
2. Consider notrump with balanced hands
3. Support the minor only as last resort

Why? Minor games need 11 tricks - majors and NT are easier!`
      },
      {
        heading: 'Bidding a Major',
        content: `Always show a 4-card major if you can:
• 1♣ → 1♦: 4+ diamonds, 6+ points
• 1♣ → 1♥: 4+ hearts, 6+ points
• 1♣ → 1♠: 4+ spades, 6+ points
• 1♦ → 1♥: 4+ hearts, 6+ points
• 1♦ → 1♠: 4+ spades, 6+ points

Bid your 4-card majors "up the line" (lowest first).`
      },
      {
        heading: 'Notrump Responses',
        content: `With balanced hands and no 4-card major:
• 1NT: 6-10 points, balanced
• 2NT: 13-15 points, balanced (forcing to game)
• 3NT: 16-17 points, balanced

Partner will continue the auction or pass.`
      },
      {
        heading: 'Supporting the Minor',
        content: `Only raise partner's minor when you must:
• Single raise (1♣ → 2♣): 6-10 points, 4+ support
• Jump raise (1♣ → 3♣): 10-12 points, 5+ support
• 5 of minor: Rare - need 29 points combined!

Usually prefer finding a major fit or playing in NT.`
      }
    ],
    practice_tip: 'Prioritize showing a 4-card major. With no major, consider NT. Raise the minor only if nothing else fits.'
  },

  responding_to_1nt: {
    title: 'Responding to 1NT',
    subtitle: 'Using Stayman and Transfers',
    sections: [
      {
        heading: '1NT Tells You a Lot',
        content: `Partner's 1NT opening shows:
• 15-17 HCP (precise range)
• Balanced shape
• No 5-card major (usually)

You can often place the final contract immediately!`
      },
      {
        heading: 'Stayman (2♣)',
        content: `Bid 2♣ (Stayman) to ask about 4-card majors:
• Partner bids 2♦ = no 4-card major
• Partner bids 2♥ = 4+ hearts
• Partner bids 2♠ = 4+ spades

Use Stayman when YOU have a 4-card major and game interest (8+ points).`
      },
      {
        heading: 'Jacoby Transfers',
        content: `Transfers show a 5+ card major with ANY point count:
• 2♦ = "I have 5+ hearts" → partner bids 2♥
• 2♥ = "I have 5+ spades" → partner bids 2♠

NO MINIMUM POINTS REQUIRED! Unlike Stayman, you transfer even with 0 points.

After the transfer:
• Pass with weak hand (0-7 points) - plays in 2-major
• Bid 2NT/3NT with game values (8+ points)
• Raise to 3 of major = invitational (8-9 points)`
      },
      {
        heading: 'Direct Responses',
        content: `Without a major:
• Pass: 0-7 points, balanced
• 2NT: 8-9 points (invitational)
• 3NT: 10-15 points (game)
• 4NT: 16-17 points (slam invite)

With a major, use Stayman or transfers first!`
      }
    ],
    practice_tip: 'Key difference: Stayman needs 8+ points, but transfers work with ANY points (even 0!). With 5-card major, always transfer first.'
  },

  responding_to_2c: {
    title: 'Responding to a Strong 2♣ Opening',
    subtitle: 'Partner has a monster hand - here\'s how to respond',
    sections: [
      {
        heading: 'What Does 2♣ Mean?',
        content: `When partner opens 2♣, they have a VERY strong hand:
• 22+ HCP, OR
• 9+ tricks in their own hand

This is an ARTIFICIAL bid - it says nothing about clubs!
It's the strongest opening bid in bridge and is GAME FORCING.`
      },
      {
        heading: 'The Waiting Bid: 2♦',
        content: `With a weak hand (0-7 HCP), bid 2♦.

This is also artificial - it doesn't show diamonds!
It simply says "I heard you, partner. Tell me more."

2♦ keeps the bidding low so opener can describe their hand.`
      },
      {
        heading: 'Positive Responses',
        content: `With 8+ HCP OR a good 5+ card suit, make a positive response:

• 2♥ or 2♠: 5+ card suit with good values
• 2NT: 8+ HCP, balanced hand
• 3♣ or 3♦: 5+ card suit with 2 of top 3 honors (AK, AQ, or KQ)

A "good suit" has at least 2 of the top 3 honors (A, K, Q).`
      },
      {
        heading: 'Key Points',
        content: `• You CANNOT pass 2♣ - it's forcing to game
• 2♦ is the most common response (weak hand, waiting)
• With 8+ HCP balanced, bid 2NT directly
• With a good 5-card major, show it immediately
• The auction continues until game is reached`
      }
    ],
    practice_tip: 'With 0-7 HCP and no good suit, bid 2♦ (waiting). With 8+ HCP balanced, bid 2NT. With a good 5-card suit, bid it!'
  },

  responding_to_2nt: {
    title: 'Responding to 2NT Opening',
    subtitle: 'Partner has 20-21 HCP balanced',
    sections: [
      {
        heading: 'What Does 2NT Show?',
        content: `Partner's 2NT opening shows:
• 20-21 HCP (very precise range)
• Balanced hand shape
• Stoppers in most suits

This is NOT forcing - you can pass with nothing!`
      },
      {
        heading: 'Point Requirements',
        content: `Game needs 25+ combined points. Partner has 20-21.

• 0-4 HCP: Pass (unlikely to make game)
• 5+ HCP: Bid 3NT (game values)
• With a 5+ card major: Use transfers (3♦ → 3♥, 3♥ → 3♠)
• With a 4-card major: Use Stayman (3♣)`
      },
      {
        heading: 'Conventions Still Apply',
        content: `Same conventions as after 1NT, but one level higher:

• 3♣ = Stayman (asking for 4-card major)
• 3♦ = Transfer to hearts (shows 5+ hearts)
• 3♥ = Transfer to spades (shows 5+ spades)
• 3NT = To play (no 4+ card major, 5+ points)`
      },
      {
        heading: 'Simple Decisions',
        content: `Most responses are straightforward:

• No major, under 5 points → Pass
• No major, 5+ points → Bid 3NT
• 5+ card major → Transfer, then decide
• 4-card major, 5+ points → Stayman`
      }
    ],
    practice_tip: 'With 5+ points and no major suit interest, just bid 3NT. Use Stayman with a 4-card major, transfers with a 5-card major.'
  },

  simple_raises: {
    title: 'Simple Raises',
    subtitle: 'Supporting partner\'s suit',
    sections: [
      {
        heading: 'What is a Raise?',
        content: `A raise means bidding partner's suit at a higher level.
Example: Partner opens 1♥, you bid 2♥ (a single raise).

Raises promise:
• Support (usually 3+ cards, 4+ is better)
• A specific point range`
      },
      {
        heading: 'Single Raise (6-10 Points)',
        content: `1♥ → 2♥ or 1♠ → 2♠ shows:
• 3+ card support
• 6-10 total points

This is a "limit bid" - partner knows exactly what you have.
Partner can pass or bid game with extra values.`
      },
      {
        heading: 'Jump Raise (10-12 Points)',
        content: `1♥ → 3♥ or 1♠ → 3♠ shows:
• 4+ card support (good trump holding)
• 10-12 total points (invitational)

Partner bids game with 14+ points, passes with minimum.`
      },
      {
        heading: 'Game Raise (13+ Points)',
        content: `1♥ → 4♥ or 1♠ → 4♠ shows:
• 4+ card support
• 13+ total points

With good shape and slam interest, use Jacoby 2NT instead.`
      }
    ],
    practice_tip: 'With 3+ card support: 6-10 = raise to 2, 10-12 = raise to 3, 13+ = raise to game.'
  }
};

// ==========================================
// PLAY SKILL CONTENT
// ==========================================

const PLAY_SKILL_CONTENT = {
  // Level 0: Play Foundations
  counting_winners: {
    title: 'Counting Winners',
    subtitle: 'The key technique for notrump contracts',
    sections: [
      {
        heading: 'Why Count Winners in Notrump?',
        content: `In notrump, you have NO TRUMPS. This creates two dangers:
• No cross-ruff available - you can't ruff losers in either hand
• If you lose control, opponents can RUN A LONG SUIT against you

So you must count what you can WIN with high cards, then develop more winners BEFORE opponents establish their suit.`
      },
      {
        heading: 'Winners vs Losers',
        content: `Bridge uses two counting methods:
• NOTRUMP → Count WINNERS (you need high cards to win)
• SUIT CONTRACTS → Count LOSERS (you have trumps to eliminate them)

Different contracts, different thinking!`
      },
      {
        heading: 'What Are Winners?',
        content: `Winners (or "sure tricks") are cards that win without giving up the lead:
• Aces - always winners
• Kings with the Ace (in either hand)
• Queens with A-K (solid sequence)
• Long cards in established suits

Example: A-K-Q-J-x = 5 sure winners`
      },
      {
        heading: 'The Counting Method',
        content: `Go suit by suit, counting tricks you can take NOW:
♠: A-K = 2 winners
♥: A = 1 winner
♦: A-K-Q = 3 winners
♣: A = 1 winner
Total: 7 winners

In 3NT you need 9 tricks. With 7 winners, you need to develop 2 more.`
      }
    ],
    practice_tip: 'In notrump, always count winners first. Compare to tricks needed (3NT = 9 tricks) to know how many you must develop.'
  },

  counting_losers: {
    title: 'Counting Losers',
    subtitle: 'The key technique for suit contracts',
    sections: [
      {
        heading: 'Why Count Losers in Suit Contracts?',
        content: `In suit contracts, you have TRUMPS - a huge advantage! Trumps let you:
• RUFF losers in the short hand (usually dummy)
• CROSS-RUFF between hands
• CONTROL the hand - opponents can't run a long suit against you

So count your LOSERS, then plan how to eliminate them (ruff, discard, or finesse).`
      },
      {
        heading: 'Winners vs Losers',
        content: `Bridge uses two counting methods:
• NOTRUMP → Count WINNERS (no trumps to help, need high cards)
• SUIT CONTRACTS → Count LOSERS (trumps let you eliminate them)

Different contracts, different thinking!`
      },
      {
        heading: 'The First-Three Rule',
        content: `Only count the FIRST THREE cards of each suit.
Why? In suit contracts, you'll trump by the 4th round, so cards beyond the 3rd don't matter.

Maximum 3 losers per suit, regardless of length.`
      },
      {
        heading: 'What Counts as a Loser?',
        content: `Look at your top 3 cards in each suit:
• A = not a loser (it wins)
• K = not a loser (it wins or forces the Ace)
• Q = not a loser (covers the 3rd position)
• J and below = loser

Examples:
• A-K-x = 1 loser (only the x)
• K-x-x = 2 losers (the two x's)
• Q-J-x = 2 losers (J and x are losers)
• x-x-x = 3 losers`
      },
      {
        heading: 'Short Suits',
        content: `Short suits have fewer losers:
• Void = 0 losers (no cards to lose!)
• Singleton A = 0 losers
• Singleton K = 0-1 loser (risky)
• Doubleton x-x = 2 losers (max for 2 cards)

The 4th+ cards are ignored: A-K-x-x = 1 loser (count A-K-x only)`
      },
      {
        heading: 'Example Count',
        content: `♠ A-K-5-3: Count A-K-5 → 1 loser (the 5)
♥ Q-J-6: Count Q-J-6 → 2 losers (J and 6)
♦ 8-4: Only 2 cards → 2 losers
♣ A-7-2: Count A-7-2 → 2 losers (7 and 2)
Total: 7 losers`
      }
    ],
    practice_tip: 'Remember: only count the first 3 cards per suit. In 4♠, you can afford 3 losers (13 - 10 tricks needed).'
  },

  analyzing_the_lead: {
    title: 'Analyzing the Lead',
    subtitle: 'Learn from the opening lead',
    sections: [
      {
        heading: 'Standard Leads',
        content: `The opening lead reveals information:
• 4th best from longest suit (7-6-5-3 → lead 5)
• Top of sequence (K-Q-J → lead K)
• Top of nothing (8-6-3 → lead 8)
• MUD from 3 small (8-5-3 → lead 5, then 8)`
      },
      {
        heading: 'What the Lead Tells You',
        content: `A low card (2, 3, 4): Suggests 4+ cards, probably with an honor
A high card (Q, J, 10): Usually top of a sequence
A middle card (6, 7, 8): Might be top of nothing or MUD`
      },
      {
        heading: 'Using the Information',
        content: `If they lead the 4 (4th best):
They have 3 cards higher, so max 3 cards lower
Rule of Eleven: 11 - 4 = 7 cards higher than 4 in other hands`
      }
    ],
    practice_tip: 'Use the Rule of Eleven with 4th best leads: 11 minus the card led = cards higher held by others.'
  },

  // Level 2: Finessing
  simple_finesse: {
    title: 'Simple Finesse',
    subtitle: 'Leading toward honors',
    sections: [
      {
        heading: 'What is a Finesse?',
        content: `A finesse is an attempt to win a trick with a card that isn't the highest.
You "lead TOWARD" the card you want to finesse, hoping the higher card is in the wrong opponent's hand.`
      },
      {
        heading: 'The Basic Technique',
        content: `With A-Q in dummy facing x-x-x:
Lead LOW from hand TOWARD the A-Q
If LHO plays low, finesse the Queen
If Queen wins, LHO has the King!

If RHO has the King, finesse fails (50% chance)`
      },
      {
        heading: 'Key Principle',
        content: `Always lead TOWARD the card you want to finesse.
Never lead the honor itself!

Wrong: Leading Q from A-Q
Right: Lead toward A-Q from the opposite hand`
      }
    ],
    practice_tip: 'A finesse has about 50% chance of success. Lead toward the honor, never away from it!'
  },

  finesse_or_drop: {
    title: 'Finesse or Drop',
    subtitle: 'When to finesse vs play for the drop',
    sections: [
      {
        heading: 'The Decision',
        content: `With A-K-J-x-x opposite x-x-x, missing the Queen:
Should you finesse (play J hoping LHO has Q)?
Or play A-K hoping Q drops (RHO has singleton or doubleton Q)?`
      },
      {
        heading: 'The Math',
        content: `Missing 5 cards including the Queen:
• Finesse: ~50% (Q is with LHO)
• Drop: ~35% (Q is doubleton or singleton)

With more cards, drop becomes better!
Missing 4 cards: Drop is ~52%
Missing 3 cards: Drop is even better`
      },
      {
        heading: 'The Rule',
        content: `"Eight ever, nine never"
• 8 cards in suit: Finesse (always)
• 9 cards in suit: Play for drop (never finesse)

This is a guideline, not absolute - other clues matter!`
      }
    ],
    practice_tip: 'Eight ever, nine never! With 8 cards finesse for the Queen, with 9 cards play for the drop.'
  },

  // Level 3: Suit Establishment
  establishing_long_suits: {
    title: 'Establishing Long Suits',
    subtitle: 'Creating winners through length',
    sections: [
      {
        heading: 'The Concept',
        content: `A long suit can generate winners even with small cards.
If you have A-K-x-x-x, the last two cards become winners after clearing the suit.`
      },
      {
        heading: 'The Process',
        content: `With A-K-x-x-x opposite x-x:
1. Play A (both follow)
2. Play K (both follow)
3. Give up a trick (opponents win)
4. Now x-x are winners!

Lost 1 trick but created 2 winners.`
      },
      {
        heading: 'Counting',
        content: `Count how opponents' cards divide:
• 8 cards total = opponents have 5
• If 3-2 split (likely): 3 rounds clears suit
• If 4-1 split: Need 4 rounds

Always assume the likely split unless clues suggest otherwise.`
      }
    ],
    practice_tip: 'To establish a suit, count how many rounds needed to clear opponents\' cards.'
  },

  // Level 4: Trump Management
  drawing_trumps: {
    title: 'Drawing Trumps',
    subtitle: 'When and how to pull trumps',
    sections: [
      {
        heading: 'Why Draw Trumps?',
        content: `Drawing trumps prevents opponents from ruffing your winners.
Usually you want to draw trumps early in suit contracts.`
      },
      {
        heading: 'How Many Rounds?',
        content: `Count opponents' trumps (usually 5):
• If 3-2 split: Draw 3 rounds
• If 4-1 split: Draw 4 rounds
• Watch for the count!

Stop when opponents have no trumps left.`
      },
      {
        heading: 'Exceptions',
        content: `DON'T draw trumps immediately if:
• You need to ruff losers in dummy
• You need entries (dummy's trumps are entries)
• Cross-ruff is the plan

Plan the whole hand before touching trumps!`
      }
    ],
    practice_tip: 'Usually draw trumps first, but stop to think if you need dummy\'s trumps for ruffing or entries.'
  },

  ruffing_losers: {
    title: 'Ruffing Losers',
    subtitle: 'Using dummy\'s trumps to eliminate losers',
    sections: [
      {
        heading: 'The Basic Idea',
        content: `If you have a loser in hand, you can ruff it in dummy.
This eliminates a loser without drawing trumps first.`
      },
      {
        heading: 'Setting Up the Ruff',
        content: `To ruff a loser:
1. Create a void (or shortness) in dummy in the loser's suit
2. Lead the loser from hand
3. Ruff with a trump in dummy

Each ruff eliminates one loser!`
      },
      {
        heading: 'Important Notes',
        content: `• Ruff in the SHORT hand (usually dummy)
• Ruffing in the long trump hand doesn't gain
• Do this BEFORE drawing all the trumps
• Count how many ruffs you need`
      }
    ],
    practice_tip: 'Ruff losers in the SHORT trump hand (usually dummy) BEFORE drawing all the trumps.'
  },

  // Level 7: Timing & Planning
  hold_up_plays: {
    title: 'Hold-Up Plays',
    subtitle: 'Cutting defenders\' communications',
    sections: [
      {
        heading: 'What is a Hold-Up?',
        content: `A hold-up means NOT winning a trick when you could.
By ducking, you exhaust one defender's cards in that suit.`
      },
      {
        heading: 'Classic Example',
        content: `Contract: 3NT. They lead ♠5.
You have: ♠ A-x-x
Don't win the Ace immediately!

Duck twice, then win the third round.
Now one defender is out of spades and can't return the suit.`
      },
      {
        heading: 'When to Hold Up',
        content: `Hold up when:
• You have one stopper
• You need to establish a suit (giving up the lead)
• You want to cut communications

Don't hold up if:
• You have multiple stoppers
• They might shift to a worse suit`
      }
    ],
    practice_tip: 'Hold up to exhaust one defender\'s cards. "One in, one out" - duck until only one defender has the suit.'
  }
};

// Default content for skills without specific content
const DEFAULT_CONTENT = {
  title: 'Practice Time!',
  subtitle: 'Test your bridge knowledge',
  sections: [
    {
      heading: 'Getting Started',
      content: 'Answer the questions to test your understanding. Take your time and think through each hand.'
    }
  ],
  practice_tip: 'Read each hand carefully and apply what you\'ve learned.'
};

const SkillIntro = ({ skillId, skillName, onStart, onBack }) => {
  const [showGlossary, setShowGlossary] = useState(false);
  const [selectedTermId, setSelectedTermId] = useState(null);
  const containerRef = useRef(null);

  // Scroll to top when component mounts or skillId changes
  useEffect(() => {
    // Scroll the container to top
    if (containerRef.current) {
      containerRef.current.scrollTop = 0;
    }
    // Also scroll the window to top for good measure
    window.scrollTo(0, 0);
  }, [skillId]);

  // Check both bidding and play skill content
  const content = SKILL_CONTENT[skillId] || PLAY_SKILL_CONTENT[skillId] || {
    ...DEFAULT_CONTENT,
    title: skillName || DEFAULT_CONTENT.title
  };

  // Handle opening glossary to a specific term
  const handleOpenGlossary = (termId) => {
    setSelectedTermId(termId);
    setShowGlossary(true);
  };

  // Handle closing glossary (reset selected term)
  const handleCloseGlossary = () => {
    setShowGlossary(false);
    setSelectedTermId(null);
  };

  return (
    <div className="skill-intro" ref={containerRef}>
      <div className="intro-header">
        <button onClick={onBack} className="back-button">← Back</button>
        <h1 className="intro-title">{content.title}</h1>
        <p className="intro-subtitle">{content.subtitle}</p>
        <div className="header-actions">
          <button
            onClick={() => {
              setSelectedTermId(null);
              setShowGlossary(true);
            }}
            className="glossary-link-button"
            title="View bridge terminology"
          >
            📖 Glossary
          </button>
        </div>
      </div>

      <div className="intro-content">
        {content.sections.map((section, index) => (
          <div key={index} className="intro-section">
            <h3>{section.heading}</h3>
            <p className="section-content">
              <TermHighlight
                text={section.content}
                onOpenGlossary={handleOpenGlossary}
              />
            </p>
          </div>
        ))}
      </div>

      {content.practice_tip && (
        <div className="practice-tip">
          <span className="tip-icon">💡</span>
          <span className="tip-text">
            <TermHighlight
              text={content.practice_tip}
              onOpenGlossary={handleOpenGlossary}
            />
          </span>
        </div>
      )}

      <div className="intro-actions">
        <button onClick={onStart} className="start-practice-button">
          Start Practice →
        </button>
      </div>

      {/* Glossary Drawer */}
      <GlossaryDrawer
        isOpen={showGlossary}
        onClose={handleCloseGlossary}
        initialTermId={selectedTermId}
      />
    </div>
  );
};

export default SkillIntro;

"""
Post-Stayman Responder Rebids

Handles responder's continuation after Stayman convention:
- 1NT - 2♣ - 2♦/2♥/2♠ - ?  (standard Stayman)
- 2NT - 3♣ - 3♦/3♥/3♠ - ?  (2NT Stayman)

Extracted from responder_rebids.py for focused module management.
"""

from engine.hand import Hand
from typing import Optional, Tuple, Dict


def handle_post_stayman(hand: Hand, opener_rebid: str,
                        features: Dict) -> Optional[Tuple[str, str]]:
    """
    Handle responder's rebid after Stayman response.

    Sequences handled:
    - 1NT - 2♣ - 2♦ - ? (opener denied 4-card major)
    - 1NT - 2♣ - 2♥ - ? (opener showed 4+ hearts)
    - 1NT - 2♣ - 2♠ - ? (opener showed 4+ spades)

    SAYC Guidelines (partner opened 1NT = 15-17 HCP):
    - 8-9 HCP: Invitational (2NT or 3M if fit found)
    - 10-14 HCP: Game values (3NT, 4M if fit found)
    - 15+ HCP: Slam interest (explored via 4NT/quantitative)

    Returns:
        3-tuple (bid, explanation, metadata) with bypass_hcp=True
    """
    hcp = hand.hcp
    spade_length = hand.suit_lengths.get('♠', 0)
    heart_length = hand.suit_lengths.get('♥', 0)

    partner_min = 15
    combined_min = hcp + partner_min

    stayman_metadata = {'bypass_hcp': True, 'bypass_suit_length': True, 'convention': 'stayman_continuation'}

    # Case 1: Opener bid 2♦ (no 4-card major)
    if opener_rebid == '2♦':
        if spade_length >= 5:
            if 8 <= hcp <= 9:
                return ("2♠", f"Invitational with 5 spades after Stayman denial. Partner raises with 3+ spades or bids 2NT/3NT.", stayman_metadata)
            elif hcp >= 10:
                return ("3♠", f"Game-forcing with 5+ spades. Partner bids 4♠ with 3+ support or 3NT.", stayman_metadata)

        if heart_length >= 5:
            if 8 <= hcp <= 9:
                return ("2♥", f"Invitational with 5 hearts after Stayman denial. Partner raises or bids NT.", stayman_metadata)
            elif hcp >= 10:
                return ("3♥", f"Game-forcing with 5+ hearts. Partner bids 4♥ with 3+ support or 3NT.", stayman_metadata)

        if 8 <= hcp <= 9:
            return ("2NT", f"Invitational after Stayman ({hcp} HCP). Combined {combined_min}+ HCP.", stayman_metadata)
        elif 10 <= hcp <= 15:
            return ("3NT", f"Game after Stayman denial ({hcp} HCP). Combined {combined_min}+ HCP.", stayman_metadata)
        elif hcp >= 16:
            return ("4NT", f"Quantitative slam invite ({hcp} HCP). Partner bids 6NT with 17 HCP.", stayman_metadata)

    # Case 2: Opener bid 2♥ (has 4+ hearts)
    elif opener_rebid == '2♥':
        if heart_length >= 4:
            if 8 <= hcp <= 9:
                return ("3♥", f"Invitational with 4+ heart fit. Partner bids 4♥ with 16-17 HCP.", stayman_metadata)
            elif 10 <= hcp <= 14:
                return ("4♥", f"Game with 4+ heart fit ({hcp} HCP). Combined {combined_min}+ HCP.", stayman_metadata)
            elif hcp >= 15:
                return ("4NT", f"RKCB for hearts - slam interest with 4+ heart fit and {hcp} HCP.", stayman_metadata)
        else:
            if 8 <= hcp <= 9:
                return ("2NT", f"Invitational, no heart fit ({hcp} HCP). Have 4 spades but partner bid hearts.", stayman_metadata)
            elif hcp >= 16:
                if spade_length >= 4:
                    return ("3♠", f"Slam try, showing 4 spades ({hcp} HCP). Partner bids 4♠/4NT with fit.", stayman_metadata)
                return ("4NT", f"Quantitative slam invite, no heart fit ({hcp} HCP). Combined {combined_min}+ HCP.", stayman_metadata)
            elif hcp >= 10:
                if spade_length >= 4:
                    return ("3♠", f"Game-forcing, showing 4 spades. Partner bids 4♠ with 4 spades, else 3NT.", stayman_metadata)
                return ("3NT", f"Game, no heart fit ({hcp} HCP).", stayman_metadata)

    # Case 3: Opener bid 2♠ (has 4+ spades)
    elif opener_rebid == '2♠':
        if spade_length >= 4:
            if 8 <= hcp <= 9:
                return ("3♠", f"Invitational with 4+ spade fit. Partner bids 4♠ with 16-17 HCP.", stayman_metadata)
            elif 10 <= hcp <= 14:
                return ("4♠", f"Game with 4+ spade fit ({hcp} HCP). Combined {combined_min}+ HCP.", stayman_metadata)
            elif hcp >= 15:
                return ("4NT", f"RKCB for spades - slam interest with 4+ spade fit and {hcp} HCP.", stayman_metadata)
        else:
            if 8 <= hcp <= 9:
                return ("2NT", f"Invitational, no spade fit ({hcp} HCP). Have 4 hearts but partner denied.", stayman_metadata)
            elif hcp >= 16:
                return ("4NT", f"Quantitative slam invite, no spade fit ({hcp} HCP). Combined {combined_min}+ HCP.", stayman_metadata)
            elif hcp >= 10:
                return ("3NT", f"Game, no spade fit ({hcp} HCP). Combined {combined_min}+ HCP.", stayman_metadata)

    return None


def handle_post_stayman_2nt(hand: Hand, opener_rebid: str) -> Optional[Tuple[str, str]]:
    """Handle responder's rebid after Stayman over 2NT opening.

    Sequences: 2NT - 3♣ - 3♦/3♥/3♠ - ?
    Partner opened 2NT (20-21 HCP).
    """
    hcp = hand.hcp
    spade_length = hand.suit_lengths.get('♠', 0)
    heart_length = hand.suit_lengths.get('♥', 0)
    metadata = {'bypass_hcp': True, 'bypass_suit_length': True, 'convention': 'stayman_continuation'}

    fit_suit = None
    if opener_rebid in ('3♥',) and heart_length >= 4:
        fit_suit = '♥'
    elif opener_rebid in ('3♠',) and spade_length >= 4:
        fit_suit = '♠'

    if fit_suit:
        if hcp >= 13:
            return ("4NT", f"Blackwood with {fit_suit} fit ({hcp} HCP). Combined {hcp + 20}+ HCP.", metadata)
        elif hcp >= 5:
            return (f"4{fit_suit}", f"Game with {fit_suit} fit ({hcp} HCP). Combined {hcp + 20}+ HCP.", metadata)
        else:
            return (f"4{fit_suit}", f"Game with {fit_suit} fit ({hcp} HCP).", metadata)
    else:
        if hcp >= 13:
            return ("4NT", f"Quantitative slam invite ({hcp} HCP). Combined {hcp + 20}+ HCP.", metadata)
        elif hcp >= 5:
            return ("3NT", f"Game, no major fit ({hcp} HCP). Combined {hcp + 20}+ HCP.", metadata)
        else:
            return ("3NT", f"Game ({hcp} HCP).", metadata)

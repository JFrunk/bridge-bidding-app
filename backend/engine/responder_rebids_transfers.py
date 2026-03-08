"""
Post-Jacoby Transfer Responder Rebids

Handles responder's continuation after Jacoby Transfer completion:
- 1NT - 2♦ - 2♥ - ?  (heart transfer completed)
- 1NT - 2♥ - 2♠ - ?  (spade transfer completed)
- 1NT - 2♦ - 3♥ - ?  (heart super-accept)
- 1NT - 2♥ - 3♠ - ?  (spade super-accept)

Extracted from responder_rebids.py for focused module management.
"""

from engine.hand import Hand
from typing import Optional, Tuple


def handle_post_jacoby_transfer(hand: Hand, my_first_response: str,
                                opener_rebid: str) -> Optional[Tuple[str, str]]:
    """
    Handle responder's rebid after Jacoby Transfer completion or super-accept.

    SAYC Guidelines (partner opened 1NT = 15-17 HCP):
    - 0-7 HCP: Pass (combined 15-24, not enough for game)
    - 8-9 HCP: Invite (2NT or 3M) - combined 23-26, borderline
    - 10+ HCP: Game (4M or 3NT) - combined 25+, game values

    Super-accept (3M) shows 17 HCP + 4-card support:
    - Any hand: Accept game (4M)
    - 10+ HCP: Explore slam

    Returns:
        2-tuple or 3-tuple (bid, explanation[, metadata])
    """
    jacoby_metadata = {'bypass_hcp': True, 'bypass_suit_length': True, 'convention': 'jacoby_continuation'}

    # Super-accept: heart
    if my_first_response == '2♦' and opener_rebid == '3♥':
        if hand.hcp >= 10:
            return ("4NT", f"RKCB for hearts - slam interest after super-accept ({hand.hcp} HCP + partner's 17).", jacoby_metadata)
        else:
            return ("4♥", f"Accepting super-accept - partner showed max with 4+ hearts ({hand.hcp} HCP + partner's 17).", jacoby_metadata)

    # Super-accept: spade
    if my_first_response == '2♥' and opener_rebid == '3♠':
        if hand.hcp >= 10:
            return ("4NT", f"RKCB for spades - slam interest after super-accept ({hand.hcp} HCP + partner's 17).", jacoby_metadata)
        else:
            return ("4♠", f"Accepting super-accept - partner showed max with 4+ spades ({hand.hcp} HCP + partner's 17).", jacoby_metadata)

    # Standard transfer completion
    if my_first_response == '2♦' and opener_rebid == '2♥':
        major = '♥'
        major_name = 'hearts'
    elif my_first_response == '2♥' and opener_rebid == '2♠':
        major = '♠'
        major_name = 'spades'
    else:
        return None

    major_length = hand.suit_lengths.get(major, 0)
    hcp = hand.hcp
    partner_min = 15
    partner_max = 17
    combined_min = hcp + partner_min
    combined_max = hcp + partner_max

    # MINIMUM (0-7 HCP): Pass
    if hcp <= 7:
        return ("Pass", f"Minimum hand ({hcp} HCP), signing off in 2{major}. Combined {combined_min}-{combined_max} HCP.")

    # INVITATIONAL (8-9 HCP)
    if 8 <= hcp <= 9:
        if major_length >= 6:
            return (f"3{major}", f"Invitational with {hcp} HCP and 6+ {major_name}. Partner bids 4{major} with max.")
        else:
            return ("2NT", f"Invitational with {hcp} HCP and 5 {major_name}. Partner can pass, bid 3{major}, or 3NT.")

    # GAME VALUES (10+ HCP)
    if hcp >= 10:
        if major_length >= 6:
            return (f"4{major}", f"Game with {hcp} HCP and 6+ {major_name}. Combined {combined_min}+ HCP.", jacoby_metadata)
        else:
            if hand.is_balanced:
                return ("3NT", f"Game with {hcp} HCP and 5 {major_name}. Partner can pass or correct to 4{major}.", jacoby_metadata)
            else:
                return (f"4{major}", f"Game with {hcp} HCP, 5 {major_name}, unbalanced. Partner has 2+ {major_name}.", jacoby_metadata)

    return None

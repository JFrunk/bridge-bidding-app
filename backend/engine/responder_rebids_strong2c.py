"""
Post-2♣ Strong Opening Responder Rebids

Handles responder's continuation after a 2♣ strong opening:
- 2♣ - 2♦ - 2NT - ?  (22-24 balanced)
- 2♣ - 2♦ - 3NT - ?  (25-27 balanced)
- 2♣ - 2♦ - 2♥/2♠ - ?  (5+ in suit)
- 2♣ - 2♦ - 3♣/3♦ - ?  (5+ in minor)

2♣ is GAME FORCING in SAYC unless opener shows 22-24 balanced (2NT rebid).

Extracted from responder_rebids.py for focused module management.
"""

from engine.hand import Hand
from typing import Optional, Tuple, Dict


def handle_strong_2c_continuation(hand: Hand, opener_rebid: str,
                                  my_first_response: str,
                                  features: Dict) -> Optional[Tuple[str, str]]:
    """
    Handle responder's continuation after a 2♣ strong opening.

    Returns:
        3-tuple (bid, explanation, metadata) - ALWAYS returns something
    """
    hcp = hand.hcp
    strong_2c_metadata = {'bypass_hcp': True, 'forcing_sequence': '2c_game_forcing', 'convention': '2c_continuation'}

    # Case 1: Opener rebid 2NT (22-24 balanced)
    if opener_rebid == '2NT':
        if hcp <= 3:
            return ("3NT", f"Game in NT after partner's 2NT (22-24 HCP + my {hcp} = {22+hcp}+ combined).", strong_2c_metadata)
        elif 4 <= hcp <= 7:
            return ("3NT", f"Game in NT ({hcp} HCP + partner's 22-24 = {22+hcp}-{24+hcp} combined).", strong_2c_metadata)
        elif 8 <= hcp <= 9:
            return ("4NT", f"Quantitative slam invite ({hcp} HCP + partner's 22-24 = {22+hcp}-{24+hcp} combined). Partner bids 6NT with max.", strong_2c_metadata)
        else:
            return ("6NT", f"Small slam with {hcp} HCP + partner's 22-24 = {22+hcp}+ combined.", strong_2c_metadata)

    # Case 2: Opener rebid 3NT (25-27 balanced)
    if opener_rebid == '3NT':
        if hcp <= 5:
            return ("Pass", f"Accepting 3NT game. Partner has 25-27, combined {25+hcp}+ is enough for game.", strong_2c_metadata)
        elif 6 <= hcp <= 7:
            return ("4NT", f"Quantitative slam invite ({hcp} HCP + partner's 25-27 = {25+hcp}+ combined).", strong_2c_metadata)
        else:
            return ("6NT", f"Slam with {hcp} HCP + partner's 25-27 = {25+hcp}+ combined.", strong_2c_metadata)

    # Case 3: Opener rebid a major (2♥ or 2♠) - shows 5+ cards
    if opener_rebid in ['2♥', '2♠']:
        major = opener_rebid[1]
        major_name = 'hearts' if major == '♥' else 'spades'
        support = hand.suit_lengths.get(major, 0)

        if support >= 3:
            return (f"4{major}", f"Game with {support}-card {major_name} support after partner's strong 2♣ and rebid.", strong_2c_metadata)
        if support == 2:
            return (f"3{major}", f"Preference to {major_name} with doubleton (game forcing sequence).", strong_2c_metadata)

        for suit in ['♠', '♥', '♦', '♣']:
            if hand.suit_lengths.get(suit, 0) >= 5:
                level = '2' if suit in ['♠'] and major == '♥' else '3'
                return (f"{level}{suit}", f"Own 5+ card suit in game forcing sequence.", strong_2c_metadata)

        if opener_rebid == '2♥':
            return ("2NT", f"Waiting/negative, no heart support, no suit to show.", strong_2c_metadata)
        else:
            return ("3NT", f"No spade support, suggesting NT game.", strong_2c_metadata)

    # Case 4: Opener rebid 3♣ or 3♦ (strong minor)
    if opener_rebid in ['3♣', '3♦']:
        minor = opener_rebid[1]
        minor_name = 'clubs' if minor == '♣' else 'diamonds'
        support = hand.suit_lengths.get(minor, 0)

        if support >= 4:
            return (f"4{minor}", f"Supporting partner's {minor_name} (4+ cards). Partner chooses 5m or 3NT.", strong_2c_metadata)
        return ("3NT", f"Game in NT after partner's {opener_rebid}. No major fit.", strong_2c_metadata)

    # Case 5: Other rebids - ensure we reach game
    return ("3NT", f"Continuing to game after 2♣ opening.", strong_2c_metadata)

import random
from engine.hand import Hand, Card
from typing import List

# This file should NOT import from itself.

def generate_hand_with_constraints(constraints: dict, deck: List[Card]):
    """
    Generates a random hand from a PROVIDED deck that meets specific constraints.
    """
    hcp_range = constraints.get('hcp_range', (0, 40))
    is_balanced = constraints.get('is_balanced')
    suit_length_req = constraints.get('suit_length_req')
    
    max_attempts = 20000
    for _ in range(max_attempts):
        random.shuffle(deck)
        hand_cards = deck[:13]
        temp_hand = Hand(hand_cards)

        hcp_ok = hcp_range[0] <= temp_hand.hcp <= hcp_range[1]
        balance_ok = is_balanced is None or temp_hand.is_balanced == is_balanced
        suit_ok = True

        if suit_length_req:
            # suit_length_req format: (suits_list, min_length, mode)
            # mode can be 'any_of' (at least one suit meets req) or 'all_of' (all suits meet req)
            suits_list, min_length, mode = suit_length_req

            if mode == 'any_of':
                # At least ONE of the suits must have min_length or more
                suit_ok = any(temp_hand.suit_lengths[suit] >= min_length for suit in suits_list)
            elif mode == 'all_of':
                # ALL of the suits must have min_length or more
                suit_ok = all(temp_hand.suit_lengths[suit] >= min_length for suit in suits_list)
            else:
                suit_ok = True

        if hcp_ok and balance_ok and suit_ok:
            remaining_deck = deck[13:]
            return temp_hand, remaining_deck

    print(f"Warning: Could not generate a hand with constraints after {max_attempts} attempts.")
    return None, deck

def generate_hand_for_convention(convention_specialist, deck: List[Card]):
    """
    Generates a hand that meets convention constraints from a provided deck.
    """
    if not hasattr(convention_specialist, 'get_constraints'):
        return None, deck
    constraints = convention_specialist.get_constraints()
    return generate_hand_with_constraints(constraints, deck)
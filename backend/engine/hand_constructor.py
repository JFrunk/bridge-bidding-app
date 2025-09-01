import random
from engine.hand import Hand, Card

def generate_hand_with_constraints(constraints):
    hcp_range = constraints.get('hcp_range', (0, 40))
    is_balanced = constraints.get('is_balanced')
    suit_length_req = constraints.get('suit_length_req')

    ranks = '23456789TJQKA'
    suits = ['♠', '♥', '♦', '♣']
    deck = [Card(rank, suit) for rank in ranks for suit in suits]
    
    max_attempts = 20000
    for _ in range(max_attempts):
        random.shuffle(deck)
        hand_cards = deck[:13]
        temp_hand = Hand(hand_cards)

        hcp_ok = hcp_range[0] <= temp_hand.hcp <= hcp_range[1]
        balance_ok = is_balanced is None or temp_hand.is_balanced == is_balanced
        
        suit_ok = True
        if suit_length_req:
            if len(suit_length_req) == 2 and isinstance(suit_length_req[0], str):
                suit, min_length = suit_length_req
                suit_ok = temp_hand.suit_lengths.get(suit, 0) >= min_length
            elif len(suit_length_req) == 2 and isinstance(suit_length_req[0], list):
                required_suits, min_length = suit_length_req
                suit_ok = any(temp_hand.suit_lengths.get(s, 0) >= min_length for s in required_suits)
            elif len(suit_length_req) == 3:
                required_suits, min_length, mode = suit_length_req
                if mode == 'any_of':
                    suit_ok = any(temp_hand.suit_lengths.get(s, 0) >= min_length for s in required_suits)
        
        if hcp_ok and suit_ok and balance_ok:
            return temp_hand
            
    print(f"Warning: Could not generate a hand with constraints after {max_attempts} attempts.")
    return None

def generate_hand_for_convention(convention_specialist):
    if not hasattr(convention_specialist, 'get_constraints'):
        return None
    constraints = convention_specialist.get_constraints()
    return generate_hand_with_constraints(constraints)
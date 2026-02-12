import random
from engine.hand import Hand, Card
from typing import List, Dict, Optional, Tuple

# This file should NOT import from itself.

# Card HCP values for suit-first generation
CARD_HCP = {'A': 4, 'K': 3, 'Q': 2, 'J': 1}


def _get_card_hcp(card: Card) -> int:
    """Get HCP value of a single card."""
    return CARD_HCP.get(card.rank, 0)


def _group_deck_by_suit(deck: List[Card]) -> Dict[str, List[Card]]:
    """Group cards in deck by suit."""
    suits = {'♠': [], '♥': [], '♦': [], '♣': []}
    for card in deck:
        suits[card.suit].append(card)
    return suits


def _generate_suit_first(
    deck: List[Card],
    required_suits: List[str],
    min_length: int,
    hcp_range: Tuple[int, int],
    is_balanced: Optional[bool],
    mode: str = 'any_of'
) -> Tuple[Optional[Hand], List[Card]]:
    """
    Suit-First Generation algorithm for constrained hand generation.

    Instead of pure rejection sampling (shuffle and check), this algorithm:
    1. Groups available cards by suit
    2. Assigns required suit lengths FIRST
    3. Fills remaining slots from other suits
    4. Only then checks HCP constraint

    This reduces rejection rate by several orders of magnitude for
    tight constraints like "6+ card suit with 8-10 HCP".

    Args:
        deck: Available cards to draw from
        required_suits: Suits that must meet length requirement
        min_length: Minimum cards required in suit(s)
        hcp_range: (min_hcp, max_hcp) tuple
        is_balanced: If True, require balanced shape; if False, require unbalanced
        mode: 'any_of' (one suit meets req) or 'all_of' (all suits meet req)

    Returns:
        (Hand, remaining_deck) or (None, original_deck) on failure
    """
    max_attempts = 5000  # Lower than pure rejection since we're smarter

    for _ in range(max_attempts):
        # Group deck by suit
        suits_available = _group_deck_by_suit(deck)
        hand_cards = []
        used_indices = set()

        # Track which suits we've drawn from and how many
        suit_draws = {'♠': 0, '♥': 0, '♦': 0, '♣': 0}

        # Step 1: Assign required suit lengths first
        if mode == 'any_of':
            # Pick ONE random suit from required_suits to be our long suit
            random.shuffle(required_suits)
            target_suit = required_suits[0]

            if len(suits_available[target_suit]) < min_length:
                continue  # Not enough cards in suit, try again

            # Draw min_length cards from target suit
            random.shuffle(suits_available[target_suit])
            for i in range(min_length):
                card = suits_available[target_suit][i]
                hand_cards.append(card)
                used_indices.add(deck.index(card))
            suit_draws[target_suit] = min_length

        elif mode == 'all_of':
            # ALL required suits must have min_length
            valid = True
            for suit in required_suits:
                if len(suits_available[suit]) < min_length:
                    valid = False
                    break
                random.shuffle(suits_available[suit])
                for i in range(min_length):
                    card = suits_available[suit][i]
                    hand_cards.append(card)
                    used_indices.add(deck.index(card))
                suit_draws[suit] = min_length

            if not valid or len(hand_cards) > 13:
                continue  # Constraints impossible, try again

        # Step 2: Fill remaining slots (13 - already drawn)
        remaining_needed = 13 - len(hand_cards)

        if remaining_needed < 0:
            continue  # Over-constrained

        # Collect available cards not yet used
        fill_cards = [card for card in deck if deck.index(card) not in used_indices]

        if len(fill_cards) < remaining_needed:
            continue  # Not enough cards left

        # For balanced hands, we need to be smarter about distribution
        if is_balanced:
            # Balanced means no singleton, no void, at most one doubleton
            # Try to fill to achieve 4-3-3-3, 4-4-3-2, or 5-3-3-2
            fill_by_suit = _group_deck_by_suit(fill_cards)

            # Calculate how many more we need per suit for balance
            target_lengths = _calculate_balanced_targets(suit_draws, remaining_needed)
            if target_lengths is None:
                continue

            for suit, target in target_lengths.items():
                additional = target - suit_draws[suit]
                if additional > 0:
                    if len(fill_by_suit[suit]) < additional:
                        break  # Can't achieve balance
                    random.shuffle(fill_by_suit[suit])
                    for i in range(additional):
                        card = fill_by_suit[suit][i]
                        hand_cards.append(card)
                        used_indices.add(deck.index(card))
                        suit_draws[suit] += 1

            if len(hand_cards) != 13:
                continue  # Couldn't achieve balance
        else:
            # Not balanced or don't care - just fill randomly
            random.shuffle(fill_cards)
            for i in range(remaining_needed):
                card = fill_cards[i]
                hand_cards.append(card)
                used_indices.add(deck.index(card))

        # Step 3: NOW check HCP constraint (much faster than checking everything)
        temp_hand = Hand(hand_cards)

        if not (hcp_range[0] <= temp_hand.hcp <= hcp_range[1]):
            continue  # HCP doesn't match, but suit structure is good

        # Check balance requirement
        if is_balanced is not None and temp_hand.is_balanced != is_balanced:
            continue

        # Success! Return hand and remaining deck
        remaining_deck = [card for i, card in enumerate(deck) if i not in used_indices]
        return temp_hand, remaining_deck

    return None, deck


def _calculate_balanced_targets(
    current_draws: Dict[str, int],
    remaining: int
) -> Optional[Dict[str, int]]:
    """
    Calculate target suit lengths for a balanced hand.

    Balanced patterns: 4-3-3-3, 4-4-3-2, 5-3-3-2
    """
    total_so_far = sum(current_draws.values())
    target_total = total_so_far + remaining

    if target_total != 13:
        return None

    # Start with current draws
    targets = dict(current_draws)
    suits = ['♠', '♥', '♦', '♣']

    # Try to achieve a balanced distribution
    # First, ensure no suit has more than 5 or less than 2
    for suit in suits:
        if targets[suit] > 5:
            return None  # Can't be balanced with 6+ in a suit from requirements

    # Fill to get balanced - aim for 3-3-3-4 or similar
    remaining_to_fill = remaining

    # Sort suits by current length (fill shorter suits first)
    suits_by_length = sorted(suits, key=lambda s: targets[s])

    for suit in suits_by_length:
        if remaining_to_fill <= 0:
            break
        # Fill up to 3 first, then up to 4
        if targets[suit] < 2:
            add = min(2 - targets[suit], remaining_to_fill)
            targets[suit] += add
            remaining_to_fill -= add

    # Second pass - fill to 3
    for suit in suits_by_length:
        if remaining_to_fill <= 0:
            break
        if targets[suit] < 3:
            add = min(3 - targets[suit], remaining_to_fill)
            targets[suit] += add
            remaining_to_fill -= add

    # Third pass - fill to 4 (only one suit if needed)
    for suit in suits_by_length:
        if remaining_to_fill <= 0:
            break
        if targets[suit] < 4:
            add = min(4 - targets[suit], remaining_to_fill)
            targets[suit] += add
            remaining_to_fill -= add

    # Verify we used all cards and have balanced shape
    if sum(targets.values()) != 13:
        return None

    # Check balanced: no void, no singleton, at most one doubleton
    lengths = sorted(targets.values())
    if lengths[0] < 2:  # Void or singleton
        return None
    if lengths[0] == 2 and lengths[1] == 2:  # Two doubletons
        return None

    return targets


def generate_hand_with_constraints(constraints: dict, deck: List[Card]):
    """
    Generates a random hand from a PROVIDED deck that meets specific constraints.

    Uses Suit-First Generation algorithm when suit length constraints are present,
    falling back to traditional rejection sampling for simple constraints.

    This hybrid approach provides:
    - Fast generation for simple HCP-only constraints (pure rejection)
    - Efficient generation for tight suit+HCP constraints (suit-first)
    """
    hcp_range = constraints.get('hcp_range', (0, 40))
    is_balanced = constraints.get('is_balanced')
    suit_length_req = constraints.get('suit_length_req')

    # Use Suit-First Generation for suit length constraints
    if suit_length_req:
        suits_list, min_length, mode = suit_length_req
        result = _generate_suit_first(
            deck=deck,
            required_suits=list(suits_list),  # Make a copy
            min_length=min_length,
            hcp_range=hcp_range,
            is_balanced=is_balanced,
            mode=mode
        )
        if result[0] is not None:
            return result
        # Fall through to rejection sampling as backup

    # Traditional rejection sampling for simple constraints
    # (or as fallback if suit-first failed)
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

def generate_hand_for_convention(convention_specialist, deck: List[Card], timeout_ms: int = 500):
    """
    Generates a hand that meets convention constraints from a provided deck.

    If the convention has a validate_hand() method, it will be called for
    additional validation beyond basic constraints (e.g., Strong 2♣ checking
    for 22+ HCP OR 19-21 HCP with 9+ playing tricks).

    Args:
        convention_specialist: Convention module with get_constraints() method
        deck: Card deck to draw from
        timeout_ms: Maximum time in milliseconds before giving up (default 500ms)

    Returns:
        (Hand, remaining_deck) or (None, deck) on failure
    """
    import time

    if not hasattr(convention_specialist, 'get_constraints'):
        return None, deck

    constraints = convention_specialist.get_constraints()
    has_custom_validator = hasattr(convention_specialist, 'validate_hand')

    start_time = time.time()
    timeout_sec = timeout_ms / 1000.0

    # If no custom validator, use standard constraint-based generation
    if not has_custom_validator:
        return generate_hand_with_constraints(constraints, deck)

    # With custom validator, we need rejection sampling with validation
    hcp_range = constraints.get('hcp_range', (0, 40))
    is_balanced = constraints.get('is_balanced')
    suit_length_req = constraints.get('suit_length_req')
    min_longest_suit = constraints.get('min_longest_suit')

    max_attempts = 50000  # High limit since we have timeout

    for attempt in range(max_attempts):
        # Check timeout
        if time.time() - start_time > timeout_sec:
            print(f"⚠️ Convention hand generation timed out after {timeout_ms}ms ({attempt} attempts)")
            return None, deck

        random.shuffle(deck)
        hand_cards = deck[:13]
        temp_hand = Hand(hand_cards)

        # Check basic constraints first (fast rejection)
        if not (hcp_range[0] <= temp_hand.hcp <= hcp_range[1]):
            continue

        if is_balanced is not None and temp_hand.is_balanced != is_balanced:
            continue

        if suit_length_req:
            suits_list, min_length, mode = suit_length_req
            if mode == 'any_of':
                if not any(temp_hand.suit_lengths[suit] >= min_length for suit in suits_list):
                    continue
            elif mode == 'all_of':
                if not all(temp_hand.suit_lengths[suit] >= min_length for suit in suits_list):
                    continue

        if min_longest_suit:
            if max(temp_hand.suit_lengths.values()) < min_longest_suit:
                continue

        # Basic constraints pass - now check custom validator
        if convention_specialist.validate_hand(temp_hand):
            remaining_deck = deck[13:]
            return temp_hand, remaining_deck

    print(f"⚠️ Could not generate hand for convention after {max_attempts} attempts")
    return None, deck
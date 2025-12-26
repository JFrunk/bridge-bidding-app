"""
Hand Generators for Learning Mode Skills

Generates hands for practicing fundamental bidding skills (Levels 0-4, 6).
Each skill has specific hand constraints that create appropriate practice scenarios.

Usage:
    from engine.learning.skill_hand_generators import get_skill_hand_generator

    generator = get_skill_hand_generator('hand_evaluation_basics')
    hand, remaining_deck = generator.generate(deck)
"""

import random
from typing import Dict, List, Optional, Tuple
from abc import ABC, abstractmethod

from engine.hand import Hand, Card


def create_deck() -> List[Card]:
    """Create a standard 52-card deck."""
    suits = ['♠', '♥', '♦', '♣']
    ranks = '23456789TJQKA'
    return [Card(rank, suit) for suit in suits for rank in ranks]


class SkillHandGenerator(ABC):
    """Base class for skill-specific hand generators."""

    skill_id: str = ""
    skill_level: int = 0
    description: str = ""

    @abstractmethod
    def get_constraints(self) -> Dict:
        """Return constraints for hand generation."""
        pass

    def generate(self, deck: List[Card] = None) -> Tuple[Optional[Hand], List[Card]]:
        """Generate a hand meeting skill constraints."""
        if deck is None:
            deck = create_deck()

        constraints = self.get_constraints()
        return generate_hand_with_constraints(constraints, deck)

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        """
        Get the expected correct response for this skill.
        Override in subclasses for specific evaluation logic.

        Returns:
            Dict with 'bid', 'explanation', 'alternatives' (if any)
        """
        return {
            'bid': None,
            'explanation': 'Evaluation not implemented for this skill',
            'alternatives': []
        }


def generate_hand_with_constraints(constraints: dict, deck: List[Card]) -> Tuple[Optional[Hand], List[Card]]:
    """
    Generate a hand from deck meeting constraints.

    Constraints:
        - hcp_range: (min, max) HCP
        - is_balanced: True/False/None
        - suit_length_req: (suits_list, min_length, mode)
          mode: 'any_of' or 'all_of'
        - void_suit: suit that must have 0 cards
        - singleton_suit: suit that must have 1 card
        - doubleton_suit: suit that must have 2 cards
        - max_suit_length: maximum cards in any suit
    """
    hcp_range = constraints.get('hcp_range', (0, 40))
    is_balanced = constraints.get('is_balanced')
    suit_length_req = constraints.get('suit_length_req')
    void_suit = constraints.get('void_suit')
    singleton_suit = constraints.get('singleton_suit')
    doubleton_suit = constraints.get('doubleton_suit')
    max_suit_length = constraints.get('max_suit_length')
    min_longest_suit = constraints.get('min_longest_suit')

    max_attempts = 20000
    for _ in range(max_attempts):
        random.shuffle(deck)
        hand_cards = deck[:13]
        temp_hand = Hand(hand_cards)

        # Check HCP
        if not (hcp_range[0] <= temp_hand.hcp <= hcp_range[1]):
            continue

        # Check balanced
        if is_balanced is not None and temp_hand.is_balanced != is_balanced:
            continue

        # Check suit length requirements
        if suit_length_req:
            suits_list, min_length, mode = suit_length_req
            if mode == 'any_of':
                if not any(temp_hand.suit_lengths[suit] >= min_length for suit in suits_list):
                    continue
            elif mode == 'all_of':
                if not all(temp_hand.suit_lengths[suit] >= min_length for suit in suits_list):
                    continue

        # Check void
        if void_suit and temp_hand.suit_lengths[void_suit] != 0:
            continue

        # Check singleton
        if singleton_suit and temp_hand.suit_lengths[singleton_suit] != 1:
            continue

        # Check doubleton
        if doubleton_suit and temp_hand.suit_lengths[doubleton_suit] != 2:
            continue

        # Check max suit length
        if max_suit_length and max(temp_hand.suit_lengths.values()) > max_suit_length:
            continue

        # Check min longest suit
        if min_longest_suit and max(temp_hand.suit_lengths.values()) < min_longest_suit:
            continue

        # All checks passed
        return temp_hand, deck[13:]

    print(f"Warning: Could not generate hand with constraints after {max_attempts} attempts")
    return None, deck


# ============================================================================
# LEVEL 0: FOUNDATIONS
# ============================================================================

class HandEvaluationBasicsGenerator(SkillHandGenerator):
    """Generate hands for practicing HCP counting and distribution points."""

    skill_id = 'hand_evaluation_basics'
    skill_level = 0
    description = 'Practice counting HCP and distribution points'

    def __init__(self, variant: str = 'random'):
        """
        Variants:
            - 'random': Any hand
            - 'balanced': Balanced hand (4333, 4432, 5332)
            - 'unbalanced': Has void, singleton, or long suit
            - 'strong': 16+ HCP
            - 'weak': 0-7 HCP
            - 'medium': 8-15 HCP
        """
        self.variant = variant

    def get_constraints(self) -> Dict:
        if self.variant == 'balanced':
            return {'is_balanced': True, 'hcp_range': (8, 18)}
        elif self.variant == 'unbalanced':
            return {'is_balanced': False, 'min_longest_suit': 6}
        elif self.variant == 'strong':
            return {'hcp_range': (16, 22)}
        elif self.variant == 'weak':
            return {'hcp_range': (0, 7)}
        elif self.variant == 'medium':
            return {'hcp_range': (8, 15)}
        else:  # random
            return {'hcp_range': (5, 20)}

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        """For Level 0, user should identify HCP, distribution points, and total."""
        return {
            'hcp': hand.hcp,
            'distribution_points': hand.dist_points,
            'total_points': hand.total_points,
            'is_balanced': hand.is_balanced,
            'explanation': f'{hand.hcp} HCP + {hand.dist_points} distribution = {hand.total_points} total points'
        }


class SuitQualityGenerator(SkillHandGenerator):
    """Generate hands for learning suit ranking and biddable suits."""

    skill_id = 'suit_quality'
    skill_level = 0
    description = 'Practice identifying suit quality and ranking'

    def __init__(self, variant: str = 'long_suit'):
        """
        Variants:
            - 'long_suit': Has a 5+ card suit to identify
            - 'two_suits': Has two 4+ card suits
            - 'no_long': No suit longer than 4
        """
        self.variant = variant

    def get_constraints(self) -> Dict:
        if self.variant == 'long_suit':
            return {
                'suit_length_req': (['♠', '♥', '♦', '♣'], 5, 'any_of'),
                'hcp_range': (10, 18)
            }
        elif self.variant == 'two_suits':
            return {
                'is_balanced': False,
                'hcp_range': (10, 18)
            }
        else:  # no_long
            return {
                'max_suit_length': 4,
                'hcp_range': (12, 18)
            }

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        """Identify longest/strongest suit."""
        longest_suit = max(hand.suit_lengths.items(), key=lambda x: (x[1], -'♣♦♥♠'.index(x[0])))[0]
        return {
            'longest_suit': longest_suit,
            'length': hand.suit_lengths[longest_suit],
            'suit_ranking': ['♣', '♦', '♥', '♠', 'NT'],
            'explanation': f'Longest suit is {longest_suit} with {hand.suit_lengths[longest_suit]} cards'
        }


class BiddingLanguageGenerator(SkillHandGenerator):
    """Generate hands for understanding forcing vs non-forcing bids."""

    skill_id = 'bidding_language'
    skill_level = 0
    description = 'Practice understanding bidding concepts'

    def get_constraints(self) -> Dict:
        # Various hands for discussing forcing vs non-forcing
        return {'hcp_range': (10, 17)}

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        return {
            'game_points_needed': 25,
            'small_slam_points': 33,
            'grand_slam_points': 37,
            'explanation': 'Game requires ~25 points combined, slam ~33+'
        }


# ============================================================================
# LEVEL 1: OPENING BIDS
# ============================================================================

class WhenToOpenGenerator(SkillHandGenerator):
    """Generate hands for deciding whether to open."""

    skill_id = 'when_to_open'
    skill_level = 1
    description = 'Practice deciding when to open the bidding'

    def __init__(self, variant: str = 'borderline'):
        """
        Variants:
            - 'clear_open': 13+ HCP, clear opener
            - 'borderline': 11-12 HCP, Rule of 20 decision
            - 'pass': 0-10 HCP, should pass
        """
        self.variant = variant

    def get_constraints(self) -> Dict:
        if self.variant == 'clear_open':
            return {'hcp_range': (13, 19)}
        elif self.variant == 'borderline':
            return {'hcp_range': (11, 12), 'min_longest_suit': 5}
        else:  # pass
            return {'hcp_range': (6, 10)}

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        # Rule of 20: HCP + length of two longest suits >= 20
        suit_lengths = sorted(hand.suit_lengths.values(), reverse=True)
        rule_of_20 = hand.hcp + suit_lengths[0] + suit_lengths[1]
        should_open = hand.hcp >= 13 or (hand.hcp >= 11 and rule_of_20 >= 20)

        return {
            'should_open': should_open,
            'hcp': hand.hcp,
            'rule_of_20_total': rule_of_20,
            'explanation': f'HCP={hand.hcp}, Rule of 20={rule_of_20}. {"Open" if should_open else "Pass"}'
        }


class OpeningOneSuitGenerator(SkillHandGenerator):
    """Generate hands for 1-of-a-suit openings."""

    skill_id = 'opening_one_suit'
    skill_level = 1
    description = 'Practice choosing the right suit opening'

    def __init__(self, variant: str = 'major'):
        """
        Variants:
            - 'major': 5+ card major
            - 'minor': No 5-card major, minor opening
            - 'two_suits': Two 5+ card suits
        """
        self.variant = variant

    def get_constraints(self) -> Dict:
        if self.variant == 'major':
            return {
                'hcp_range': (12, 21),
                'suit_length_req': (['♠', '♥'], 5, 'any_of'),
                'is_balanced': False
            }
        elif self.variant == 'minor':
            return {
                'hcp_range': (12, 21),
                'max_suit_length': 4,  # No 5-card major
            }
        else:  # two_suits
            return {
                'hcp_range': (12, 21),
                'min_longest_suit': 5,
                'is_balanced': False
            }

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        # Determine correct opening bid
        spades = hand.suit_lengths['♠']
        hearts = hand.suit_lengths['♥']
        diamonds = hand.suit_lengths['♦']
        clubs = hand.suit_lengths['♣']

        if spades >= 5 and spades >= hearts:
            bid = '1♠'
            explanation = f'Open 1♠ with {spades}-card spade suit'
        elif hearts >= 5:
            bid = '1♥'
            explanation = f'Open 1♥ with {hearts}-card heart suit'
        elif diamonds >= 4:
            bid = '1♦'
            explanation = f'Open 1♦ with {diamonds} diamonds (no 5-card major)'
        else:
            bid = '1♣'
            explanation = f'Open 1♣ with {clubs} clubs (no 5-card major or 4+ diamonds)'

        return {
            'bid': bid,
            'explanation': explanation,
            'alternatives': []
        }


class Opening1NTGenerator(SkillHandGenerator):
    """Generate hands for 1NT opening decisions."""

    skill_id = 'opening_1nt'
    skill_level = 1
    description = 'Practice 1NT opening requirements'

    def __init__(self, variant: str = 'correct'):
        """
        Variants:
            - 'correct': 15-17 HCP, balanced
            - 'too_weak': 12-14 balanced
            - 'too_strong': 18-19 balanced
            - 'unbalanced': 15-17 but not balanced
        """
        self.variant = variant

    def get_constraints(self) -> Dict:
        if self.variant == 'correct':
            return {'hcp_range': (15, 17), 'is_balanced': True}
        elif self.variant == 'too_weak':
            return {'hcp_range': (12, 14), 'is_balanced': True}
        elif self.variant == 'too_strong':
            return {'hcp_range': (18, 19), 'is_balanced': True}
        else:  # unbalanced
            return {'hcp_range': (15, 17), 'is_balanced': False}

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        should_open_1nt = 15 <= hand.hcp <= 17 and hand.is_balanced

        if should_open_1nt:
            bid = '1NT'
            explanation = f'{hand.hcp} HCP, balanced - open 1NT'
        elif hand.hcp >= 15 and not hand.is_balanced:
            bid = '1♠' if hand.suit_lengths['♠'] >= 5 else '1♥' if hand.suit_lengths['♥'] >= 5 else '1♦' if hand.suit_lengths['♦'] >= 4 else '1♣'
            explanation = f'{hand.hcp} HCP but unbalanced - open a suit'
        elif hand.hcp < 15:
            bid = 'Pass' if hand.hcp < 12 else '1♦'
            explanation = f'{hand.hcp} HCP - too weak for 1NT'
        else:
            bid = '1♠'
            explanation = f'{hand.hcp} HCP - too strong for 1NT'

        return {
            'bid': bid,
            'is_1nt_correct': should_open_1nt,
            'explanation': explanation
        }


class Opening2CStrongGenerator(SkillHandGenerator):
    """Generate hands for strong 2C opening."""

    skill_id = 'opening_2c_strong'
    skill_level = 1
    description = 'Practice recognizing 2C opening hands'

    def __init__(self, variant: str = 'correct'):
        self.variant = variant

    def get_constraints(self) -> Dict:
        if self.variant == 'correct':
            return {'hcp_range': (22, 25)}
        else:  # almost
            return {'hcp_range': (19, 21)}

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        should_open_2c = hand.hcp >= 22
        return {
            'bid': '2♣' if should_open_2c else '1♠',
            'explanation': f'{hand.hcp} HCP - {"2♣ strong opening" if should_open_2c else "not strong enough for 2♣"}'
        }


class Opening2NTGenerator(SkillHandGenerator):
    """Generate hands for 2NT opening."""

    skill_id = 'opening_2nt'
    skill_level = 1
    description = 'Practice 2NT opening requirements'

    def __init__(self, variant: str = 'correct'):
        self.variant = variant

    def get_constraints(self) -> Dict:
        if self.variant == 'correct':
            return {'hcp_range': (20, 21), 'is_balanced': True}
        else:  # borderline
            return {'hcp_range': (19, 22), 'is_balanced': True}

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        should_open_2nt = 20 <= hand.hcp <= 21 and hand.is_balanced
        return {
            'bid': '2NT' if should_open_2nt else '1NT' if hand.hcp <= 17 else '2♣',
            'explanation': f'{hand.hcp} HCP, balanced - {"2NT" if should_open_2nt else "not 2NT range"}'
        }


# ============================================================================
# LEVEL 2: RESPONDING TO OPENINGS
# ============================================================================

class RespondingToMajorGenerator(SkillHandGenerator):
    """Generate hands for responding to 1M opening."""

    skill_id = 'responding_to_major'
    skill_level = 2
    description = 'Practice responding to partner\'s 1H/1S opening'

    def __init__(self, variant: str = 'support'):
        """
        Variants:
            - 'support': Has 3+ card support
            - 'no_support': No fit, new suit
            - 'strong': Game-forcing hand
        """
        self.variant = variant

    def get_constraints(self) -> Dict:
        if self.variant == 'support':
            return {
                'hcp_range': (6, 12),
                'suit_length_req': (['♥'], 3, 'any_of')  # Support for hearts
            }
        elif self.variant == 'no_support':
            return {'hcp_range': (6, 12), 'max_suit_length': 4}
        else:  # strong
            return {'hcp_range': (13, 17)}

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        # Assume partner opened 1H for simplicity
        hearts = hand.suit_lengths['♥']
        spades = hand.suit_lengths['♠']

        if hearts >= 3:
            if hand.hcp >= 6 and hand.hcp <= 9:
                bid = '2♥'
                explanation = f'Simple raise with {hearts} hearts and {hand.hcp} HCP'
            elif hand.hcp >= 10 and hand.hcp <= 12:
                bid = '3♥'
                explanation = f'Limit raise with {hearts} hearts and {hand.hcp} HCP'
            else:
                bid = '4♥'
                explanation = f'Game raise with {hearts} hearts and {hand.hcp} HCP'
        elif spades >= 4 and hand.hcp >= 6:
            bid = '1♠'
            explanation = f'Bid 1♠ with {spades} spades (new suit)'
        elif hand.hcp >= 6 and hand.hcp <= 9:
            bid = '1NT'
            explanation = f'{hand.hcp} HCP, no fit - respond 1NT'
        else:
            bid = 'Pass'
            explanation = 'Too weak to respond'

        return {'bid': bid, 'explanation': explanation}


class RespondingToMinorGenerator(SkillHandGenerator):
    """Generate hands for responding to 1m opening."""

    skill_id = 'responding_to_minor'
    skill_level = 2
    description = 'Practice responding to partner\'s 1C/1D opening'

    def __init__(self, variant: str = 'major'):
        self.variant = variant

    def get_constraints(self) -> Dict:
        if self.variant == 'major':
            return {
                'hcp_range': (6, 15),
                'suit_length_req': (['♠', '♥'], 4, 'any_of')
            }
        else:  # nt
            return {'hcp_range': (6, 10), 'is_balanced': True}

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        spades = hand.suit_lengths['♠']
        hearts = hand.suit_lengths['♥']

        if hearts >= 4:
            bid = '1♥'
            explanation = f'Bid 1♥ with {hearts} hearts (4-card major over minor)'
        elif spades >= 4:
            bid = '1♠'
            explanation = f'Bid 1♠ with {spades} spades'
        else:
            bid = '1NT'
            explanation = f'{hand.hcp} HCP, no 4-card major - respond 1NT'

        return {'bid': bid, 'explanation': explanation}


class RespondingTo1NTGenerator(SkillHandGenerator):
    """Generate hands for responding to 1NT opening."""

    skill_id = 'responding_to_1nt'
    skill_level = 2
    description = 'Practice responding to partner\'s 1NT opening'

    def __init__(self, variant: str = 'balanced'):
        self.variant = variant

    def get_constraints(self) -> Dict:
        if self.variant == 'balanced':
            return {'hcp_range': (0, 12), 'is_balanced': True}
        elif self.variant == 'stayman':
            return {
                'hcp_range': (8, 15),
                'suit_length_req': (['♠', '♥'], 4, 'any_of')
            }
        else:  # transfer
            return {
                'hcp_range': (0, 15),
                'suit_length_req': (['♠', '♥'], 5, 'any_of')
            }

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        if hand.hcp <= 7 and hand.is_balanced:
            bid = 'Pass'
            explanation = f'{hand.hcp} HCP balanced - pass (partner has 15-17)'
        elif 8 <= hand.hcp <= 9:
            bid = '2NT'
            explanation = f'{hand.hcp} HCP - invite to game with 2NT'
        elif hand.hcp >= 10:
            bid = '3NT'
            explanation = f'{hand.hcp} HCP - bid game'
        else:
            bid = 'Pass'
            explanation = 'Weak hand - pass'

        return {'bid': bid, 'explanation': explanation}


class RespondingTo2CGenerator(SkillHandGenerator):
    """Generate hands for responding to 2C opening."""

    skill_id = 'responding_to_2c'
    skill_level = 2
    description = 'Practice responding to partner\'s strong 2C'

    def get_constraints(self) -> Dict:
        return {'hcp_range': (0, 12)}

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        if hand.hcp >= 8:
            # Positive response
            if hand.suit_lengths['♠'] >= 5:
                bid = '2♠'
            elif hand.suit_lengths['♥'] >= 5:
                bid = '2♥'
            else:
                bid = '2NT'
            explanation = f'{hand.hcp} HCP - positive response'
        else:
            bid = '2♦'
            explanation = f'{hand.hcp} HCP - waiting bid (2♦)'

        return {'bid': bid, 'explanation': explanation}


class RespondingTo2NTGenerator(SkillHandGenerator):
    """Generate hands for responding to 2NT opening."""

    skill_id = 'responding_to_2nt'
    skill_level = 2
    description = 'Practice responding to partner\'s 2NT opening'

    def get_constraints(self) -> Dict:
        return {'hcp_range': (0, 12)}

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        # Partner has 20-21, game is 25+
        if hand.hcp <= 4:
            bid = 'Pass'
            explanation = f'{hand.hcp} HCP - game unlikely, pass'
        elif hand.hcp >= 5:
            bid = '3NT'
            explanation = f'{hand.hcp} HCP + partner\'s 20-21 = game'
        else:
            bid = 'Pass'
            explanation = 'Borderline'

        return {'bid': bid, 'explanation': explanation}


# ============================================================================
# LEVEL 3: OPENER'S REBIDS
# ============================================================================

class RebidAfter1LevelGenerator(SkillHandGenerator):
    """Generate hands for opener's rebid after 1-level response."""

    skill_id = 'rebid_after_1_level'
    skill_level = 3
    description = 'Practice opener\'s rebid after partner responds at 1-level'

    def __init__(self, variant: str = 'minimum'):
        self.variant = variant

    def get_constraints(self) -> Dict:
        if self.variant == 'minimum':
            return {'hcp_range': (12, 14)}
        elif self.variant == 'medium':
            return {'hcp_range': (15, 17)}
        else:  # maximum
            return {'hcp_range': (18, 21)}

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        # Simplified - would depend on actual auction
        return {
            'strength_category': 'minimum' if hand.hcp <= 14 else 'medium' if hand.hcp <= 17 else 'maximum',
            'explanation': f'{hand.hcp} HCP - {"minimum" if hand.hcp <= 14 else "medium" if hand.hcp <= 17 else "maximum"} opener'
        }


class RebidAfter2LevelGenerator(SkillHandGenerator):
    """Generate hands for opener's rebid after 2-level response."""

    skill_id = 'rebid_after_2_level'
    skill_level = 3
    description = 'Practice opener\'s rebid after partner responds at 2-level'

    def get_constraints(self) -> Dict:
        return {'hcp_range': (12, 18)}


class RebidAfterRaiseGenerator(SkillHandGenerator):
    """Generate hands for opener's rebid after partner raises."""

    skill_id = 'rebid_after_raise'
    skill_level = 3
    description = 'Practice opener\'s rebid after partner raises your suit'

    def get_constraints(self) -> Dict:
        return {'hcp_range': (12, 18), 'suit_length_req': (['♠', '♥'], 5, 'any_of')}


class RebidAfter1NTResponseGenerator(SkillHandGenerator):
    """Generate hands for opener's rebid after 1NT response."""

    skill_id = 'rebid_after_1nt_response'
    skill_level = 3
    description = 'Practice opener\'s rebid after partner responds 1NT'

    def get_constraints(self) -> Dict:
        return {'hcp_range': (12, 18)}


# ============================================================================
# LEVEL 4: RESPONDER'S REBIDS
# ============================================================================

class AfterOpenerRaisesGenerator(SkillHandGenerator):
    """Generate hands for responder when opener raises."""

    skill_id = 'after_opener_raises'
    skill_level = 4
    description = 'Practice responder\'s rebid when opener raises your suit'

    def get_constraints(self) -> Dict:
        return {'hcp_range': (6, 15), 'suit_length_req': (['♠', '♥'], 5, 'any_of')}


class AfterOpenerRebidsSuitGenerator(SkillHandGenerator):
    """Generate hands for responder when opener rebids their suit."""

    skill_id = 'after_opener_rebids_suit'
    skill_level = 4
    description = 'Practice responder\'s rebid when opener rebids their suit'

    def get_constraints(self) -> Dict:
        return {'hcp_range': (6, 15)}


class AfterOpenerNewSuitGenerator(SkillHandGenerator):
    """Generate hands for responder when opener bids new suit."""

    skill_id = 'after_opener_new_suit'
    skill_level = 4
    description = 'Practice responder\'s rebid when opener shows new suit'

    def get_constraints(self) -> Dict:
        return {'hcp_range': (6, 15)}


class AfterOpenerRebidsNTGenerator(SkillHandGenerator):
    """Generate hands for responder when opener rebids NT."""

    skill_id = 'after_opener_rebids_nt'
    skill_level = 4
    description = 'Practice responder\'s rebid when opener rebids notrump'

    def get_constraints(self) -> Dict:
        return {'hcp_range': (6, 15)}


class PreferenceBidsGenerator(SkillHandGenerator):
    """Generate hands for preference bids."""

    skill_id = 'preference_bids'
    skill_level = 4
    description = 'Practice giving preference to opener\'s first suit'

    def get_constraints(self) -> Dict:
        return {'hcp_range': (6, 10)}


# ============================================================================
# LEVEL 6: COMPETITIVE BIDDING
# ============================================================================

class OvercallsGenerator(SkillHandGenerator):
    """Generate hands for overcalls."""

    skill_id = 'overcalls'
    skill_level = 6
    description = 'Practice making overcalls'

    def __init__(self, variant: str = 'simple'):
        self.variant = variant

    def get_constraints(self) -> Dict:
        if self.variant == 'simple':
            return {
                'hcp_range': (8, 16),
                'suit_length_req': (['♠', '♥', '♦', '♣'], 5, 'any_of')
            }
        elif self.variant == 'jump':
            return {
                'hcp_range': (6, 10),
                'suit_length_req': (['♠', '♥', '♦', '♣'], 6, 'any_of')
            }
        else:  # 1nt
            return {'hcp_range': (15, 18), 'is_balanced': True}


class RespondingToOvercallsGenerator(SkillHandGenerator):
    """Generate hands for responding to partner's overcall."""

    skill_id = 'responding_to_overcalls'
    skill_level = 6
    description = 'Practice responding to partner\'s overcall'

    def get_constraints(self) -> Dict:
        return {'hcp_range': (6, 15)}


class NegativeDoublesGenerator(SkillHandGenerator):
    """Generate hands for negative doubles."""

    skill_id = 'negative_doubles'
    skill_level = 6
    description = 'Practice making negative doubles'

    def get_constraints(self) -> Dict:
        return {
            'hcp_range': (7, 12),
            'suit_length_req': (['♠', '♥'], 4, 'any_of')
        }


class OverOpponentDoubleGenerator(SkillHandGenerator):
    """Generate hands for bidding over opponent's takeout double."""

    skill_id = 'over_opponent_double'
    skill_level = 6
    description = 'Practice bidding when opponent doubles partner'

    def get_constraints(self) -> Dict:
        return {'hcp_range': (6, 15)}


class BalancingGenerator(SkillHandGenerator):
    """Generate hands for balancing."""

    skill_id = 'balancing'
    skill_level = 6
    description = 'Practice balancing when opponents stop low'

    def get_constraints(self) -> Dict:
        return {'hcp_range': (8, 14)}


# ============================================================================
# GENERATOR REGISTRY
# ============================================================================

SKILL_GENERATORS = {
    # Level 0
    'hand_evaluation_basics': HandEvaluationBasicsGenerator,
    'suit_quality': SuitQualityGenerator,
    'bidding_language': BiddingLanguageGenerator,

    # Level 1
    'when_to_open': WhenToOpenGenerator,
    'opening_one_suit': OpeningOneSuitGenerator,
    'opening_1nt': Opening1NTGenerator,
    'opening_2c_strong': Opening2CStrongGenerator,
    'opening_2nt': Opening2NTGenerator,

    # Level 2
    'responding_to_major': RespondingToMajorGenerator,
    'responding_to_minor': RespondingToMinorGenerator,
    'responding_to_1nt': RespondingTo1NTGenerator,
    'responding_to_2c': RespondingTo2CGenerator,
    'responding_to_2nt': RespondingTo2NTGenerator,

    # Level 3
    'rebid_after_1_level': RebidAfter1LevelGenerator,
    'rebid_after_2_level': RebidAfter2LevelGenerator,
    'rebid_after_raise': RebidAfterRaiseGenerator,
    'rebid_after_1nt_response': RebidAfter1NTResponseGenerator,

    # Level 4
    'after_opener_raises': AfterOpenerRaisesGenerator,
    'after_opener_rebids_suit': AfterOpenerRebidsSuitGenerator,
    'after_opener_new_suit': AfterOpenerNewSuitGenerator,
    'after_opener_rebids_nt': AfterOpenerRebidsNTGenerator,
    'preference_bids': PreferenceBidsGenerator,

    # Level 6
    'overcalls': OvercallsGenerator,
    'responding_to_overcalls': RespondingToOvercallsGenerator,
    'negative_doubles': NegativeDoublesGenerator,
    'over_opponent_double': OverOpponentDoubleGenerator,
    'balancing': BalancingGenerator,
}


def get_skill_hand_generator(skill_id: str, variant: str = None) -> Optional[SkillHandGenerator]:
    """
    Get a hand generator for a specific skill.

    Args:
        skill_id: The skill ID from skill_tree.py
        variant: Optional variant for different difficulty/focus

    Returns:
        SkillHandGenerator instance or None if skill not found
    """
    generator_class = SKILL_GENERATORS.get(skill_id)
    if not generator_class:
        return None

    if variant:
        try:
            return generator_class(variant=variant)
        except TypeError:
            return generator_class()

    return generator_class()


def get_available_skills() -> List[str]:
    """Get list of all skill IDs with hand generators."""
    return list(SKILL_GENERATORS.keys())

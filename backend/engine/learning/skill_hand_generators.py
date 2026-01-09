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
        - unique_longest_suit: True requires exactly one suit with max length (no ties)
    """
    hcp_range = constraints.get('hcp_range', (0, 40))
    is_balanced = constraints.get('is_balanced')
    suit_length_req = constraints.get('suit_length_req')
    void_suit = constraints.get('void_suit')
    singleton_suit = constraints.get('singleton_suit')
    doubleton_suit = constraints.get('doubleton_suit')
    max_suit_length = constraints.get('max_suit_length')
    min_longest_suit = constraints.get('min_longest_suit')
    unique_longest_suit = constraints.get('unique_longest_suit', False)

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

        # Check unique longest suit (no ties for longest)
        if unique_longest_suit:
            suit_lengths_list = list(temp_hand.suit_lengths.values())
            max_length = max(suit_lengths_list)
            if suit_lengths_list.count(max_length) > 1:
                continue  # Multiple suits tied for longest, reject

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
            - 'long_suit': Has a 5+ card suit to identify (unique longest - no ties)
            - 'two_suits': Has two 4+ card suits
            - 'no_long': No suit longer than 4
        """
        self.variant = variant

    def get_constraints(self) -> Dict:
        if self.variant == 'long_suit':
            return {
                'suit_length_req': (['♠', '♥', '♦', '♣'], 5, 'any_of'),
                'hcp_range': (10, 18),
                'unique_longest_suit': True  # Prevent ties for longest suit
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
    """Generate conceptual questions about bidding language - no hand needed."""

    skill_id = 'bidding_language'
    skill_level = 0
    description = 'Practice understanding bidding concepts'

    # Questions about game/slam points by contract type
    QUESTIONS = [
        {
            'question_type': 'game_points_contract',
            'contract': '3NT',
            'display_contract': '3NT (9 tricks)',
            'correct_answer': 25,
            'explanation': '3NT requires about 25 combined points (9 tricks in notrump).'
        },
        {
            'question_type': 'game_points_contract',
            'contract': '4♥',
            'display_contract': '4♥ (10 tricks)',
            'correct_answer': 25,
            'explanation': '4♥ requires about 25 combined points (10 tricks in a major).'
        },
        {
            'question_type': 'game_points_contract',
            'contract': '4♠',
            'display_contract': '4♠ (10 tricks)',
            'correct_answer': 25,
            'explanation': '4♠ requires about 25 combined points (10 tricks in a major).'
        },
        {
            'question_type': 'game_points_contract',
            'contract': '5♣',
            'display_contract': '5♣ (11 tricks)',
            'correct_answer': 29,
            'explanation': '5♣ requires about 29 combined points (11 tricks in a minor).'
        },
        {
            'question_type': 'game_points_contract',
            'contract': '5♦',
            'display_contract': '5♦ (11 tricks)',
            'correct_answer': 29,
            'explanation': '5♦ requires about 29 combined points (11 tricks in a minor).'
        },
        {
            'question_type': 'slam_points',
            'contract': 'small slam',
            'display_contract': 'Small Slam (12 tricks)',
            'correct_answer': 33,
            'explanation': 'Small slam requires about 33 combined points (12 tricks).'
        },
        {
            'question_type': 'slam_points',
            'contract': 'grand slam',
            'display_contract': 'Grand Slam (13 tricks)',
            'correct_answer': 37,
            'explanation': 'Grand slam requires about 37 combined points (all 13 tricks).'
        },
    ]

    # Class-level tracking of asked questions (reset when all asked)
    _asked_indices = []

    def __init__(self, variant: str = None):
        self.variant = variant
        self._current_question = None

    def get_constraints(self) -> Dict:
        # No hand constraints needed - this is a conceptual skill
        return {'no_hand': True}

    def generate(self, deck: List[Card] = None) -> Tuple[Optional[Hand], List[Card]]:
        """Override generate - we don't need a hand for this skill."""
        # Return None for hand - frontend will detect this
        return None, deck if deck else []

    def get_expected_response(self, hand: Hand = None, auction: List[str] = None) -> Dict:
        """Return a question about game/slam points, avoiding repeats until all shown."""
        import random

        # Get available question indices (not yet asked)
        all_indices = list(range(len(self.QUESTIONS)))
        available = [i for i in all_indices if i not in BiddingLanguageGenerator._asked_indices]

        # If all questions have been asked, reset and start over
        if not available:
            BiddingLanguageGenerator._asked_indices = []
            available = all_indices

        # Pick a random available question
        chosen_idx = random.choice(available)
        BiddingLanguageGenerator._asked_indices.append(chosen_idx)

        question = self.QUESTIONS[chosen_idx]
        self._current_question = question

        return {
            'question_type': question['question_type'],
            'contract': question['contract'],
            'display_contract': question['display_contract'],
            'correct_answer': question['correct_answer'],
            'explanation': question['explanation'],
            'no_hand_required': True
        }


# ============================================================================
# LEVEL 1: BASIC BIDDING ACTIONS (Foundational Conventions)
# These generators support the ConventionRegistry foundational modules
# ============================================================================

class WhenToPassGenerator(SkillHandGenerator):
    """Generate hands for learning when NOT to bid.

    This foundational skill teaches discipline - knowing when to pass
    is as important as knowing what to bid.
    """

    skill_id = 'when_to_pass'
    skill_level = 1
    description = 'Practice recognizing when to Pass'

    VARIANT_WEIGHTS = {
        'opener_pass': 0.40,      # Not enough to open (< 12 HCP)
        'responder_pass': 0.35,   # Not enough to respond (< 6 HCP)
        'borderline_pass': 0.25,  # Borderline hands that should pass
    }

    def __init__(self, variant: str = None):
        if variant is None:
            self.variant = self._select_variant()
        else:
            self.variant = variant

    def _select_variant(self) -> str:
        r = random.random()
        cumulative = 0
        for variant, weight in self.VARIANT_WEIGHTS.items():
            cumulative += weight
            if r < cumulative:
                return variant
        return 'opener_pass'

    def get_constraints(self) -> Dict:
        if self.variant == 'opener_pass':
            return {'hcp_range': (5, 11)}  # Below opening strength
        elif self.variant == 'responder_pass':
            return {'hcp_range': (0, 5)}   # Below responding strength
        else:  # borderline_pass
            return {'hcp_range': (10, 11), 'max_suit_length': 4}  # Fails Rule of 20

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        suit_lengths = sorted(hand.suit_lengths.values(), reverse=True)
        rule_of_20 = hand.hcp + suit_lengths[0] + suit_lengths[1]

        if self.variant == 'opener_pass':
            explanation = f'{hand.hcp} HCP is below opening strength (need 12+). Pass!'
        elif self.variant == 'responder_pass':
            explanation = f'{hand.hcp} HCP is too weak to respond (need 6+). Pass!'
        else:
            explanation = f'{hand.hcp} HCP, Rule of 20 = {rule_of_20} (need 20). Not worth opening. Pass!'

        return {
            'bid': 'Pass',
            'should_pass': True,
            'hcp': hand.hcp,
            'explanation': explanation
        }


class OpeningOneMajorGenerator(SkillHandGenerator):
    """Generate hands for 1♥ or 1♠ opening decisions.

    Teaches the 5-card major requirement and when to choose between majors.
    """

    skill_id = 'opening_one_major'
    skill_level = 1
    description = 'Practice opening 1♥ or 1♠ with 5+ card major'

    VARIANT_WEIGHTS = {
        'five_hearts': 0.35,
        'five_spades': 0.35,
        'both_majors': 0.20,
        'no_major': 0.10,  # Boundary: no 5-card major -> open minor
    }

    def __init__(self, variant: str = None):
        if variant is None:
            self.variant = self._select_variant()
        else:
            self.variant = variant

    def _select_variant(self) -> str:
        r = random.random()
        cumulative = 0
        for variant, weight in self.VARIANT_WEIGHTS.items():
            cumulative += weight
            if r < cumulative:
                return variant
        return 'five_hearts'

    def get_constraints(self) -> Dict:
        if self.variant == 'five_hearts':
            return {
                'hcp_range': (12, 21),
                'suit_length_req': (['♥'], 5, 'any_of'),
            }
        elif self.variant == 'five_spades':
            return {
                'hcp_range': (12, 21),
                'suit_length_req': (['♠'], 5, 'any_of'),
            }
        elif self.variant == 'both_majors':
            return {
                'hcp_range': (12, 21),
                'suit_length_req': (['♠', '♥'], 5, 'all_of'),
            }
        else:  # no_major - boundary case
            return {
                'hcp_range': (12, 21),
                'max_suit_length': 4,  # No 5-card suit
            }

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        spades = hand.suit_lengths['♠']
        hearts = hand.suit_lengths['♥']

        if spades >= 5 and spades >= hearts:
            bid = '1♠'
            explanation = f'Open 1♠ with {spades}-card spade suit ({hand.hcp} HCP). With equal length majors, bid the higher-ranking suit first.'
        elif hearts >= 5:
            bid = '1♥'
            explanation = f'Open 1♥ with {hearts}-card heart suit ({hand.hcp} HCP).'
        else:
            # No 5-card major - boundary case
            bid = '1♦' if hand.suit_lengths['♦'] >= 4 else '1♣'
            explanation = f'No 5-card major. Open {bid} and search for a major fit through the auction.'

        return {
            'bid': bid,
            'explanation': explanation
        }


class OpeningOneMinorGenerator(SkillHandGenerator):
    """Generate hands for 1♣ or 1♦ opening decisions.

    Teaches the "better minor" concept when no 5-card major exists.
    """

    skill_id = 'opening_one_minor'
    skill_level = 1
    description = 'Practice opening 1♣ or 1♦ with no 5-card major'

    VARIANT_WEIGHTS = {
        'longer_diamonds': 0.35,
        'longer_clubs': 0.35,
        'equal_minors': 0.30,
    }

    def __init__(self, variant: str = None):
        if variant is None:
            self.variant = self._select_variant()
        else:
            self.variant = variant

    def _select_variant(self) -> str:
        r = random.random()
        cumulative = 0
        for variant, weight in self.VARIANT_WEIGHTS.items():
            cumulative += weight
            if r < cumulative:
                return variant
        return 'longer_diamonds'

    def get_constraints(self) -> Dict:
        base = {'hcp_range': (12, 21), 'max_suit_length': 4}  # No 5-card major
        if self.variant == 'longer_diamonds':
            base['suit_length_req'] = (['♦'], 4, 'any_of')
        elif self.variant == 'longer_clubs':
            base['suit_length_req'] = (['♣'], 4, 'any_of')
        # equal_minors: no additional constraint
        return base

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        diamonds = hand.suit_lengths['♦']
        clubs = hand.suit_lengths['♣']

        if diamonds > clubs:
            bid = '1♦'
            explanation = f'Open 1♦ with {diamonds} diamonds (longer minor). No 5-card major.'
        elif clubs > diamonds:
            bid = '1♣'
            explanation = f'Open 1♣ with {clubs} clubs (longer minor). No 5-card major.'
        elif diamonds == 4 and clubs == 4:
            bid = '1♦'
            explanation = f'Open 1♦ with 4-4 in the minors (SAYC convention).'
        else:  # 3-3 minors
            bid = '1♣'
            explanation = f'Open 1♣ with 3-3 in the minors (SAYC convention).'

        return {
            'bid': bid,
            'explanation': explanation
        }


class SingleRaiseGenerator(SkillHandGenerator):
    """Generate hands for single raise of partner's major (1M-2M).

    Teaches the 6-10 point range with 3+ card support.
    """

    skill_id = 'single_raise'
    skill_level = 1
    description = 'Practice raising partner\'s major with minimum values'

    VARIANT_WEIGHTS = {
        'raise_hearts': 0.40,
        'raise_spades': 0.40,
        'no_support': 0.20,  # Boundary: no fit
    }

    def __init__(self, variant: str = None):
        if variant is None:
            self.variant = self._select_variant()
        else:
            self.variant = variant
        self.partner_opened = '1♥' if self.variant == 'raise_hearts' else '1♠'

    def _select_variant(self) -> str:
        r = random.random()
        cumulative = 0
        for variant, weight in self.VARIANT_WEIGHTS.items():
            cumulative += weight
            if r < cumulative:
                return variant
        return 'raise_hearts'

    def get_constraints(self) -> Dict:
        if self.variant == 'raise_hearts':
            return {
                'hcp_range': (6, 10),
                'suit_length_req': (['♥'], 3, 'any_of'),
            }
        elif self.variant == 'raise_spades':
            return {
                'hcp_range': (6, 10),
                'suit_length_req': (['♠'], 3, 'any_of'),
            }
        else:  # no_support
            return {
                'hcp_range': (6, 10),
                'max_suit_length': 2,  # No 3+ card support
            }

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        if self.variant == 'raise_hearts':
            support = hand.suit_lengths['♥']
            if support >= 3:
                bid = '2♥'
                explanation = f'Raise 1♥ to 2♥ with {support}-card support and {hand.hcp} HCP (6-10 points).'
            else:
                bid = '1NT'
                explanation = f'No heart support. Bid 1NT as a "dustbin" response.'
        elif self.variant == 'raise_spades':
            support = hand.suit_lengths['♠']
            if support >= 3:
                bid = '2♠'
                explanation = f'Raise 1♠ to 2♠ with {support}-card support and {hand.hcp} HCP (6-10 points).'
            else:
                bid = '1NT'
                explanation = f'No spade support. Bid 1NT as a "dustbin" response.'
        else:
            bid = '1NT'
            explanation = f'No 3-card support for partner\'s major. Bid 1NT.'

        return {
            'bid': bid,
            'explanation': explanation,
            'partner_opened': self.partner_opened
        }


class LimitRaiseGenerator(SkillHandGenerator):
    """Generate hands for limit raise (1M-3M).

    Teaches the invitational 10-12 point range with 4+ card support.
    """

    skill_id = 'limit_raise'
    skill_level = 1
    description = 'Practice the invitational limit raise'

    VARIANT_WEIGHTS = {
        'limit_hearts': 0.40,
        'limit_spades': 0.40,
        'too_weak': 0.20,  # Boundary: only single raise strength
    }

    def __init__(self, variant: str = None):
        if variant is None:
            self.variant = self._select_variant()
        else:
            self.variant = variant
        self.partner_opened = '1♥' if 'hearts' in self.variant or self.variant == 'too_weak' else '1♠'

    def _select_variant(self) -> str:
        r = random.random()
        cumulative = 0
        for variant, weight in self.VARIANT_WEIGHTS.items():
            cumulative += weight
            if r < cumulative:
                return variant
        return 'limit_hearts'

    def get_constraints(self) -> Dict:
        if self.variant == 'limit_hearts':
            return {
                'hcp_range': (10, 12),
                'suit_length_req': (['♥'], 4, 'any_of'),
            }
        elif self.variant == 'limit_spades':
            return {
                'hcp_range': (10, 12),
                'suit_length_req': (['♠'], 4, 'any_of'),
            }
        else:  # too_weak
            return {
                'hcp_range': (6, 9),
                'suit_length_req': (['♥'], 4, 'any_of'),
            }

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        if self.variant == 'limit_hearts':
            bid = '3♥'
            explanation = f'Limit raise to 3♥ with {hand.suit_lengths["♥"]}-card support and {hand.hcp} HCP (10-12). Invites game!'
        elif self.variant == 'limit_spades':
            bid = '3♠'
            explanation = f'Limit raise to 3♠ with {hand.suit_lengths["♠"]}-card support and {hand.hcp} HCP (10-12). Invites game!'
        else:  # too_weak
            bid = '2♥'
            explanation = f'Only {hand.hcp} HCP - not enough for limit raise (need 10-12). Simple raise to 2♥.'

        return {
            'bid': bid,
            'explanation': explanation,
            'partner_opened': self.partner_opened
        }


class NewSuitResponseGenerator(SkillHandGenerator):
    """Generate hands for new suit response at 1-level.

    Teaches the 6+ HCP requirement with 4+ cards in the suit.
    """

    skill_id = 'new_suit_response'
    skill_level = 1
    description = 'Practice bidding a new suit at the 1-level'

    VARIANT_WEIGHTS = {
        'one_heart_over_minor': 0.35,
        'one_spade_over_minor': 0.35,
        'one_spade_over_heart': 0.20,
        'too_weak': 0.10,  # Boundary
    }

    def __init__(self, variant: str = None):
        if variant is None:
            self.variant = self._select_variant()
        else:
            self.variant = variant

        if self.variant == 'one_spade_over_heart':
            self.partner_opened = '1♥'
        else:
            self.partner_opened = '1♦'

    def _select_variant(self) -> str:
        r = random.random()
        cumulative = 0
        for variant, weight in self.VARIANT_WEIGHTS.items():
            cumulative += weight
            if r < cumulative:
                return variant
        return 'one_heart_over_minor'

    def get_constraints(self) -> Dict:
        if self.variant == 'one_heart_over_minor':
            return {
                'hcp_range': (6, 15),
                'suit_length_req': (['♥'], 4, 'any_of'),
            }
        elif self.variant == 'one_spade_over_minor':
            return {
                'hcp_range': (6, 15),
                'suit_length_req': (['♠'], 4, 'any_of'),
            }
        elif self.variant == 'one_spade_over_heart':
            return {
                'hcp_range': (6, 15),
                'suit_length_req': (['♠'], 4, 'any_of'),
            }
        else:  # too_weak
            return {'hcp_range': (3, 5)}

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        if hand.hcp < 6:
            bid = 'Pass'
            explanation = f'{hand.hcp} HCP is too weak to respond (need 6+).'
        elif self.variant == 'one_heart_over_minor':
            bid = '1♥'
            explanation = f'Bid 1♥ with {hand.suit_lengths["♥"]} hearts and {hand.hcp} HCP. New suit at 1-level is forcing!'
        elif self.variant == 'one_spade_over_minor':
            bid = '1♠'
            explanation = f'Bid 1♠ with {hand.suit_lengths["♠"]} spades and {hand.hcp} HCP. New suit at 1-level is forcing!'
        elif self.variant == 'one_spade_over_heart':
            bid = '1♠'
            explanation = f'Bid 1♠ with {hand.suit_lengths["♠"]} spades over partner\'s 1♥. Looking for major fit!'
        else:
            bid = 'Pass'
            explanation = f'{hand.hcp} HCP - too weak to respond.'

        return {
            'bid': bid,
            'explanation': explanation,
            'partner_opened': self.partner_opened
        }


class DustbinNTResponseGenerator(SkillHandGenerator):
    """Generate hands for the "dustbin" 1NT response.

    The 1NT response catches hands that don't fit elsewhere:
    - 6-10 HCP
    - No support for partner's major
    - No suit to bid at the 1-level
    """

    skill_id = 'dustbin_1nt_response'
    skill_level = 1
    description = 'Practice the "dustbin" 1NT response'

    def __init__(self, variant: str = None):
        self.variant = variant or 'standard'
        self.partner_opened = '1♠'

    def get_constraints(self) -> Dict:
        return {
            'hcp_range': (6, 10),
            'is_balanced': True,
            'max_suit_length': 3,  # No 4+ card suit
        }

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        bid = '1NT'
        explanation = f'{hand.hcp} HCP with no fit for partner\'s spades and no suit to bid at 1-level. The "dustbin" 1NT catches these hands.'

        return {
            'bid': bid,
            'explanation': explanation,
            'partner_opened': self.partner_opened
        }


class GameRaiseGenerator(SkillHandGenerator):
    """Generate hands for direct game raise (1M-4M).

    Teaches the 13-16 point range with 5+ card support - sign-off.
    """

    skill_id = 'game_raise'
    skill_level = 1
    description = 'Practice the direct game raise'

    VARIANT_WEIGHTS = {
        'game_hearts': 0.40,
        'game_spades': 0.40,
        'too_strong': 0.20,  # Boundary: slam interest
    }

    def __init__(self, variant: str = None):
        if variant is None:
            self.variant = self._select_variant()
        else:
            self.variant = variant
        self.partner_opened = '1♥' if 'hearts' in self.variant else '1♠'

    def _select_variant(self) -> str:
        r = random.random()
        cumulative = 0
        for variant, weight in self.VARIANT_WEIGHTS.items():
            cumulative += weight
            if r < cumulative:
                return variant
        return 'game_hearts'

    def get_constraints(self) -> Dict:
        if self.variant == 'game_hearts':
            return {
                'hcp_range': (13, 16),
                'suit_length_req': (['♥'], 5, 'any_of'),
            }
        elif self.variant == 'game_spades':
            return {
                'hcp_range': (13, 16),
                'suit_length_req': (['♠'], 5, 'any_of'),
            }
        else:  # too_strong
            return {
                'hcp_range': (17, 19),
                'suit_length_req': (['♠'], 5, 'any_of'),
            }

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        if self.variant == 'game_hearts':
            bid = '4♥'
            explanation = f'Direct game raise to 4♥ with {hand.suit_lengths["♥"]}-card support and {hand.hcp} HCP. Sign-off - no slam interest.'
        elif self.variant == 'game_spades':
            bid = '4♠'
            explanation = f'Direct game raise to 4♠ with {hand.suit_lengths["♠"]}-card support and {hand.hcp} HCP. Sign-off - no slam interest.'
        else:  # too_strong
            bid = '2♣'  # or other forcing bid
            explanation = f'{hand.hcp} HCP with great support - too strong for 4♠ (denies slam interest). Start with forcing bid.'

        return {
            'bid': bid,
            'explanation': explanation,
            'partner_opened': self.partner_opened
        }


class TwoOverOneResponseGenerator(SkillHandGenerator):
    """Generate hands for 2-level new suit response.

    Teaches the 10+ HCP requirement with 5+ cards in the suit.
    """

    skill_id = 'two_over_one_response'
    skill_level = 1
    description = 'Practice 2-level new suit responses'

    VARIANT_WEIGHTS = {
        'two_clubs': 0.35,
        'two_diamonds': 0.35,
        'too_weak': 0.30,  # Boundary: should bid 1NT instead
    }

    def __init__(self, variant: str = None):
        if variant is None:
            self.variant = self._select_variant()
        else:
            self.variant = variant
        self.partner_opened = '1♠'

    def _select_variant(self) -> str:
        r = random.random()
        cumulative = 0
        for variant, weight in self.VARIANT_WEIGHTS.items():
            cumulative += weight
            if r < cumulative:
                return variant
        return 'two_clubs'

    def get_constraints(self) -> Dict:
        if self.variant == 'two_clubs':
            return {
                'hcp_range': (10, 15),
                'suit_length_req': (['♣'], 5, 'any_of'),
            }
        elif self.variant == 'two_diamonds':
            return {
                'hcp_range': (10, 15),
                'suit_length_req': (['♦'], 5, 'any_of'),
            }
        else:  # too_weak
            return {
                'hcp_range': (6, 9),
                'suit_length_req': (['♣'], 5, 'any_of'),
            }

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        if hand.hcp >= 10:
            if self.variant == 'two_clubs':
                bid = '2♣'
                explanation = f'Bid 2♣ with {hand.suit_lengths["♣"]} clubs and {hand.hcp} HCP. Two-over-one = 10+ HCP, game forcing!'
            else:
                bid = '2♦'
                explanation = f'Bid 2♦ with {hand.suit_lengths["♦"]} diamonds and {hand.hcp} HCP. Two-over-one = 10+ HCP, game forcing!'
        else:  # too_weak
            bid = '1NT'
            explanation = f'{hand.hcp} HCP is not enough for 2-level (need 10+). Bid 1NT instead.'

        return {
            'bid': bid,
            'explanation': explanation,
            'partner_opened': self.partner_opened
        }


# ============================================================================
# LEVEL 1 CONTINUED: OPENING BIDS (Original generators)
# ============================================================================

class WhenToOpenGenerator(SkillHandGenerator):
    """Generate hands for deciding whether to open.

    ~75% positive cases (should open), ~25% negative cases (should pass).
    Prerequisite knowledge: Level 0 (hand evaluation, suit quality, bidding language)
    """

    skill_id = 'when_to_open'
    skill_level = 1
    description = 'Practice deciding when to open the bidding'

    # Variant weights: 75% open, 25% pass
    VARIANT_WEIGHTS = {
        'clear_open': 0.50,      # 13-19 HCP, clear open
        'borderline_open': 0.25, # 11-12 HCP, meets Rule of 20
        'pass_weak': 0.15,       # 6-10 HCP, should pass
        'pass_borderline': 0.10, # 11-12 HCP, fails Rule of 20
    }

    def __init__(self, variant: str = None):
        """
        Variants:
            - 'clear_open': 13+ HCP, clear opener
            - 'borderline_open': 11-12 HCP, meets Rule of 20
            - 'pass_weak': 6-10 HCP, should pass
            - 'pass_borderline': 11-12 HCP, fails Rule of 20
        """
        if variant is None:
            # Random selection based on weights
            self.variant = self._select_variant()
        else:
            self.variant = variant

    def _select_variant(self) -> str:
        """Select variant based on weights."""
        r = random.random()
        cumulative = 0
        for variant, weight in self.VARIANT_WEIGHTS.items():
            cumulative += weight
            if r < cumulative:
                return variant
        return 'clear_open'

    def get_constraints(self) -> Dict:
        if self.variant == 'clear_open':
            return {'hcp_range': (13, 19)}
        elif self.variant == 'borderline_open':
            # 11-12 HCP with long suits (5-5 or better to meet Rule of 20)
            return {'hcp_range': (11, 12), 'min_longest_suit': 5}
        elif self.variant == 'pass_borderline':
            # 11-12 HCP with short suits (fails Rule of 20)
            return {'hcp_range': (11, 12), 'max_suit_length': 4}
        else:  # pass_weak
            return {'hcp_range': (6, 10)}

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        # Rule of 20: HCP + length of two longest suits >= 20
        suit_lengths = sorted(hand.suit_lengths.values(), reverse=True)
        rule_of_20 = hand.hcp + suit_lengths[0] + suit_lengths[1]
        should_open = hand.hcp >= 13 or (hand.hcp >= 11 and rule_of_20 >= 20)

        if should_open:
            explanation = f'{hand.hcp} HCP'
            if hand.hcp >= 13:
                explanation += ' - clear opening strength (13+).'
            else:
                explanation += f', Rule of 20 = {rule_of_20} (meets 20). Open!'
        else:
            explanation = f'{hand.hcp} HCP'
            if hand.hcp < 11:
                explanation += ' - too weak to open (need 12+ or Rule of 20).'
            else:
                explanation += f', Rule of 20 = {rule_of_20} (needs 20). Pass.'

        return {
            'should_open': should_open,
            'hcp': hand.hcp,
            'rule_of_20_total': rule_of_20,
            'explanation': explanation
        }


class OpeningOneSuitGenerator(SkillHandGenerator):
    """Generate hands for 1-of-a-suit openings.

    ~75% positive cases (open a suit), ~25% boundary cases.
    Prerequisite knowledge: when_to_open (can reference Pass)

    Boundary cases:
    - Too weak (should Pass) - references when_to_open
    - 1NT range balanced (should open 1NT, but learned AFTER this skill)
      -> For now, we only include Pass as boundary since 1NT comes later
    """

    skill_id = 'opening_one_suit'
    skill_level = 1
    description = 'Practice choosing the right suit opening'

    # Variant weights: 75% open suit, 25% boundary
    VARIANT_WEIGHTS = {
        'major': 0.30,        # 5+ card major
        'minor': 0.25,        # No 5-card major, minor opening
        'two_suits': 0.20,    # Two 5+ card suits (bid higher)
        'pass_weak': 0.25,    # Too weak to open (boundary case)
    }

    def __init__(self, variant: str = None):
        """
        Variants:
            - 'major': 5+ card major
            - 'minor': No 5-card major, minor opening
            - 'two_suits': Two 5+ card suits
            - 'pass_weak': Too weak to open (boundary case)
        """
        if variant is None:
            self.variant = self._select_variant()
        else:
            self.variant = variant

    def _select_variant(self) -> str:
        """Select variant based on weights."""
        r = random.random()
        cumulative = 0
        for variant, weight in self.VARIANT_WEIGHTS.items():
            cumulative += weight
            if r < cumulative:
                return variant
        return 'major'

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
        elif self.variant == 'two_suits':
            return {
                'hcp_range': (12, 21),
                'min_longest_suit': 5,
                'is_balanced': False
            }
        else:  # pass_weak - boundary case
            return {
                'hcp_range': (7, 11),  # Not enough to open
            }

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        # First check if hand is too weak to open
        suit_lengths = sorted(hand.suit_lengths.values(), reverse=True)
        rule_of_20 = hand.hcp + suit_lengths[0] + suit_lengths[1]
        should_open = hand.hcp >= 12 or (hand.hcp >= 11 and rule_of_20 >= 20)

        if not should_open:
            return {
                'bid': 'Pass',
                'explanation': f'{hand.hcp} HCP is too weak to open. Need 12+ HCP or meet Rule of 20.',
                'alternatives': []
            }

        # Determine correct opening bid
        spades = hand.suit_lengths['♠']
        hearts = hand.suit_lengths['♥']
        diamonds = hand.suit_lengths['♦']
        clubs = hand.suit_lengths['♣']

        if spades >= 5 and spades >= hearts:
            bid = '1♠'
            explanation = f'Open 1♠ with {spades}-card spade suit.'
        elif hearts >= 5:
            bid = '1♥'
            explanation = f'Open 1♥ with {hearts}-card heart suit.'
        elif diamonds >= 4:
            bid = '1♦'
            explanation = f'Open 1♦ with {diamonds} diamonds (no 5-card major).'
        else:
            bid = '1♣'
            explanation = f'Open 1♣ with {clubs} clubs (no 5-card major or 4+ diamonds).'

        return {
            'bid': bid,
            'explanation': explanation,
            'alternatives': []
        }


class Opening1NTGenerator(SkillHandGenerator):
    """Generate hands for 1NT opening decisions.

    ~75% positive cases (open 1NT), ~25% boundary cases (open suit instead).
    Prerequisite knowledge: when_to_open, opening_one_suit

    Boundary cases - all expect a SUIT opening (not 1NT):
    - Too weak (12-14 balanced): open longest suit
    - Too strong (18-19 balanced): open longest suit (plan to rebid 2NT)
    - Right points but unbalanced: open longest suit
    - 5-card major with 15-17: open the major (debatable, but common)
    """

    skill_id = 'opening_1nt'
    skill_level = 1
    description = 'Practice 1NT opening requirements'

    # Variant weights: 75% open 1NT, 25% boundary (open suit)
    VARIANT_WEIGHTS = {
        'correct': 0.75,           # 15-17 HCP, balanced, no 5-card major
        'too_weak': 0.08,          # 12-14 balanced -> open suit
        'too_strong': 0.07,        # 18-19 balanced -> open suit (plan 2NT rebid)
        'unbalanced': 0.10,        # 15-17 unbalanced -> open suit
    }

    def __init__(self, variant: str = None):
        """
        Variants:
            - 'correct': 15-17 HCP, balanced, no 5-card major
            - 'too_weak': 12-14 balanced -> open suit
            - 'too_strong': 18-19 balanced -> open suit
            - 'unbalanced': 15-17 but not balanced -> open suit
        """
        if variant is None:
            self.variant = self._select_variant()
        else:
            self.variant = variant

    def _select_variant(self) -> str:
        """Select variant based on weights."""
        r = random.random()
        cumulative = 0
        for variant, weight in self.VARIANT_WEIGHTS.items():
            cumulative += weight
            if r < cumulative:
                return variant
        return 'correct'

    def get_constraints(self) -> Dict:
        if self.variant == 'correct':
            return {'hcp_range': (15, 17), 'is_balanced': True, 'max_suit_length': 4}
        elif self.variant == 'too_weak':
            return {'hcp_range': (12, 14), 'is_balanced': True}
        elif self.variant == 'too_strong':
            return {'hcp_range': (18, 19), 'is_balanced': True}
        else:  # unbalanced
            return {'hcp_range': (15, 17), 'is_balanced': False, 'min_longest_suit': 5}

    def _get_longest_suit_bid(self, hand: Hand) -> str:
        """Determine the correct suit opening based on hand shape."""
        spades = hand.suit_lengths['♠']
        hearts = hand.suit_lengths['♥']
        diamonds = hand.suit_lengths['♦']
        clubs = hand.suit_lengths['♣']

        if spades >= 5 and spades >= hearts:
            return '1♠'
        elif hearts >= 5:
            return '1♥'
        elif diamonds >= 4:
            return '1♦'
        else:
            return '1♣'

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        should_open_1nt = 15 <= hand.hcp <= 17 and hand.is_balanced

        if should_open_1nt:
            bid = '1NT'
            explanation = f'{hand.hcp} HCP, balanced shape - perfect for 1NT (15-17).'
        elif hand.hcp < 15 and hand.is_balanced:
            # Too weak for 1NT
            bid = self._get_longest_suit_bid(hand)
            explanation = f'{hand.hcp} HCP is below 1NT range (15-17). Open {bid} instead.'
        elif hand.hcp > 17 and hand.is_balanced:
            # Too strong for 1NT (18-19)
            bid = self._get_longest_suit_bid(hand)
            explanation = f'{hand.hcp} HCP is above 1NT range (15-17). Open {bid}, plan to rebid 2NT.'
        else:
            # Unbalanced
            bid = self._get_longest_suit_bid(hand)
            explanation = f'{hand.hcp} HCP but unbalanced - 1NT requires balanced shape. Open {bid}.'

        return {
            'bid': bid,
            'is_1nt_correct': should_open_1nt,
            'explanation': explanation
        }


class Opening2CStrongGenerator(SkillHandGenerator):
    """Generate hands for strong 2♣ opening.

    ~75% positive cases (open 2♣), ~25% boundary cases (open 1-level).
    Prerequisite knowledge: when_to_open, opening_one_suit, opening_1nt

    Boundary cases:
    - 19-21 HCP balanced: too strong for 1NT but not 2♣ -> open suit
    - 19-21 HCP unbalanced: strong but not game-forcing -> open 1-level
    """

    skill_id = 'opening_2c_strong'
    skill_level = 1
    description = 'Practice recognizing 2♣ opening hands'

    # Variant weights: 75% open 2♣, 25% boundary
    VARIANT_WEIGHTS = {
        'correct_balanced': 0.35,    # 22+ balanced
        'correct_unbalanced': 0.40,  # 22+ with long suit
        'too_weak_balanced': 0.12,   # 19-21 balanced -> open suit
        'too_weak_unbalanced': 0.13, # 19-21 unbalanced -> open suit
    }

    def __init__(self, variant: str = None):
        if variant is None:
            self.variant = self._select_variant()
        else:
            self.variant = variant

    def _select_variant(self) -> str:
        """Select variant based on weights."""
        r = random.random()
        cumulative = 0
        for variant, weight in self.VARIANT_WEIGHTS.items():
            cumulative += weight
            if r < cumulative:
                return variant
        return 'correct_balanced'

    def get_constraints(self) -> Dict:
        if self.variant == 'correct_balanced':
            return {'hcp_range': (22, 25), 'is_balanced': True}
        elif self.variant == 'correct_unbalanced':
            return {'hcp_range': (22, 25), 'is_balanced': False, 'min_longest_suit': 6}
        elif self.variant == 'too_weak_balanced':
            return {'hcp_range': (19, 21), 'is_balanced': True}
        else:  # too_weak_unbalanced
            return {'hcp_range': (19, 21), 'is_balanced': False, 'min_longest_suit': 5}

    def _get_longest_suit_bid(self, hand: Hand) -> str:
        """Determine the correct suit opening based on hand shape."""
        spades = hand.suit_lengths['♠']
        hearts = hand.suit_lengths['♥']
        diamonds = hand.suit_lengths['♦']
        clubs = hand.suit_lengths['♣']

        if spades >= 5 and spades >= hearts:
            return '1♠'
        elif hearts >= 5:
            return '1♥'
        elif diamonds >= 4:
            return '1♦'
        else:
            return '1♣'

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        should_open_2c = hand.hcp >= 22

        if should_open_2c:
            bid = '2♣'
            explanation = f'{hand.hcp} HCP - strong enough for 2♣ (22+). Game-forcing opening!'
        else:
            # 19-21 HCP - not strong enough for 2♣
            bid = self._get_longest_suit_bid(hand)
            if hand.is_balanced:
                explanation = f'{hand.hcp} HCP balanced - not quite 2♣ strength (need 22+). Open {bid}, plan to jump rebid.'
            else:
                explanation = f'{hand.hcp} HCP - strong but not game-forcing (need 22+). Open {bid}.'

        return {
            'bid': bid,
            'explanation': explanation
        }


class Opening2NTGenerator(SkillHandGenerator):
    """Generate hands for 2NT opening.

    ~75% positive cases (open 2NT), ~25% boundary cases.
    Prerequisite knowledge: when_to_open, opening_one_suit, opening_1nt, opening_2c_strong

    Boundary cases:
    - 18-19 HCP balanced: too weak for 2NT -> open 1 of suit (rebid 2NT)
    - 22+ HCP balanced: too strong for 2NT -> open 2♣
    - 20-21 HCP unbalanced: right points but wrong shape -> open suit
    """

    skill_id = 'opening_2nt'
    skill_level = 1
    description = 'Practice 2NT opening requirements'

    # Variant weights: 75% open 2NT, 25% boundary
    VARIANT_WEIGHTS = {
        'correct': 0.75,           # 20-21 HCP, balanced
        'too_weak': 0.08,          # 18-19 balanced -> open suit
        'too_strong': 0.07,        # 22+ balanced -> open 2♣
        'unbalanced': 0.10,        # 20-21 unbalanced -> open suit
    }

    def __init__(self, variant: str = None):
        if variant is None:
            self.variant = self._select_variant()
        else:
            self.variant = variant

    def _select_variant(self) -> str:
        """Select variant based on weights."""
        r = random.random()
        cumulative = 0
        for variant, weight in self.VARIANT_WEIGHTS.items():
            cumulative += weight
            if r < cumulative:
                return variant
        return 'correct'

    def get_constraints(self) -> Dict:
        if self.variant == 'correct':
            return {'hcp_range': (20, 21), 'is_balanced': True}
        elif self.variant == 'too_weak':
            return {'hcp_range': (18, 19), 'is_balanced': True}
        elif self.variant == 'too_strong':
            return {'hcp_range': (22, 24), 'is_balanced': True}
        else:  # unbalanced
            return {'hcp_range': (20, 21), 'is_balanced': False, 'min_longest_suit': 5}

    def _get_longest_suit_bid(self, hand: Hand) -> str:
        """Determine the correct suit opening based on hand shape."""
        spades = hand.suit_lengths['♠']
        hearts = hand.suit_lengths['♥']
        diamonds = hand.suit_lengths['♦']
        clubs = hand.suit_lengths['♣']

        if spades >= 5 and spades >= hearts:
            return '1♠'
        elif hearts >= 5:
            return '1♥'
        elif diamonds >= 4:
            return '1♦'
        else:
            return '1♣'

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        should_open_2nt = 20 <= hand.hcp <= 21 and hand.is_balanced

        if should_open_2nt:
            bid = '2NT'
            explanation = f'{hand.hcp} HCP, balanced - perfect for 2NT (20-21).'
        elif hand.hcp >= 22 and hand.is_balanced:
            # Too strong for 2NT
            bid = '2♣'
            explanation = f'{hand.hcp} HCP is too strong for 2NT (max 21). Open 2♣.'
        elif hand.hcp < 20 and hand.is_balanced:
            # Too weak for 2NT (18-19)
            bid = self._get_longest_suit_bid(hand)
            explanation = f'{hand.hcp} HCP is below 2NT range (20-21). Open {bid}, plan to jump rebid 2NT.'
        else:
            # Unbalanced
            bid = self._get_longest_suit_bid(hand)
            explanation = f'{hand.hcp} HCP but unbalanced - 2NT requires balanced shape. Open {bid}.'

        return {
            'bid': bid,
            'explanation': explanation
        }


# ============================================================================
# LEVEL 2: RESPONDING TO OPENINGS
# ============================================================================

class RespondingToMajorGenerator(SkillHandGenerator):
    """Generate hands for responding to 1M opening."""

    skill_id = 'responding_to_major'
    skill_level = 2
    description = 'Practice responding to partner\'s 1H/1S opening'

    def __init__(self, variant: str = None):
        """
        Variants:
            - 'support_hearts': Has 3+ card heart support (partner opened 1♥)
            - 'support_spades': Has 3+ card spade support (partner opened 1♠)
            - 'no_support': No fit, new suit
            - 'weak': Too weak to respond
        """
        if variant is None:
            # Randomly select variant
            variants = ['support_hearts', 'support_spades', 'no_support', 'weak']
            weights = [0.35, 0.35, 0.20, 0.10]
            r = random.random()
            cumulative = 0
            for v, w in zip(variants, weights):
                cumulative += w
                if r < cumulative:
                    self.variant = v
                    break
            else:
                self.variant = 'support_hearts'
        else:
            self.variant = variant

        # Determine opening bid based on variant
        if self.variant == 'support_spades':
            self.opening_bid = '1♠'
        else:
            self.opening_bid = '1♥'

    def get_constraints(self) -> Dict:
        if self.variant == 'support_hearts':
            return {
                'hcp_range': (6, 15),
                'suit_length_req': (['♥'], 3, 'any_of')  # Support for hearts
            }
        elif self.variant == 'support_spades':
            return {
                'hcp_range': (6, 15),
                'suit_length_req': (['♠'], 3, 'any_of')  # Support for spades
            }
        elif self.variant == 'no_support':
            return {'hcp_range': (6, 12), 'max_suit_length': 2}  # Max 2 in partner's major
        else:  # weak
            return {'hcp_range': (0, 5)}

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        # Determine which major partner opened
        if self.opening_bid == '1♠':
            support_suit = '♠'
            support_length = hand.suit_lengths['♠']
        else:
            support_suit = '♥'
            support_length = hand.suit_lengths['♥']

        spades = hand.suit_lengths['♠']
        hearts = hand.suit_lengths['♥']

        # Too weak to respond?
        if hand.hcp < 6:
            bid = 'Pass'
            explanation = f'{hand.hcp} HCP is too weak to respond (need 6+).'
        # Has support for partner's major?
        elif support_length >= 3:
            if hand.hcp >= 6 and hand.hcp <= 9:
                bid = f'2{support_suit}'
                explanation = f'Simple raise with {support_length} {support_suit} and {hand.hcp} HCP.'
            elif hand.hcp >= 10 and hand.hcp <= 12:
                bid = f'3{support_suit}'
                explanation = f'Limit raise with {support_length} {support_suit} and {hand.hcp} HCP (invitational).'
            else:
                bid = f'4{support_suit}'
                explanation = f'Game raise with {support_length} {support_suit} and {hand.hcp} HCP.'
        # Can bid spades over 1♥?
        elif self.opening_bid == '1♥' and spades >= 4 and hand.hcp >= 6:
            bid = '1♠'
            explanation = f'Bid 1♠ with {spades} spades (new suit at 1-level).'
        # NT response
        elif hand.hcp >= 6 and hand.hcp <= 10:
            bid = '1NT'
            explanation = f'{hand.hcp} HCP, no major fit - respond 1NT.'
        elif hand.hcp >= 11 and hand.hcp <= 12:
            bid = '2NT'
            explanation = f'{hand.hcp} HCP, no major fit - 2NT is invitational.'
        else:
            bid = '3NT'
            explanation = f'{hand.hcp} HCP, no major fit - 3NT to play.'

        return {
            'bid': bid,
            'explanation': explanation,
            'opening_bid': self.opening_bid,
            'partner_opened': self.opening_bid
        }


class RespondingToMinorGenerator(SkillHandGenerator):
    """Generate hands for responding to 1m opening."""

    skill_id = 'responding_to_minor'
    skill_level = 2
    description = 'Practice responding to partner\'s 1C/1D opening'

    def __init__(self, variant: str = None):
        """
        Variants:
            - 'clubs_major': Partner opened 1♣, responder has 4+ card major
            - 'diamonds_major': Partner opened 1♦, responder has 4+ card major
            - 'no_major': No 4-card major, respond NT or raise minor
            - 'weak': Too weak to respond
        """
        if variant is None:
            # Randomly select variant
            variants = ['clubs_major', 'diamonds_major', 'no_major', 'weak']
            weights = [0.30, 0.30, 0.25, 0.15]
            r = random.random()
            cumulative = 0
            for v, w in zip(variants, weights):
                cumulative += w
                if r < cumulative:
                    self.variant = v
                    break
            else:
                self.variant = 'clubs_major'
        else:
            self.variant = variant

        # Determine opening bid based on variant
        if self.variant == 'diamonds_major' or self.variant == 'diamonds_nt':
            self.opening_bid = '1♦'
        else:
            self.opening_bid = '1♣'

    def get_constraints(self) -> Dict:
        if self.variant in ['clubs_major', 'diamonds_major']:
            return {
                'hcp_range': (6, 15),
                'suit_length_req': (['♠', '♥'], 4, 'any_of')
            }
        elif self.variant == 'no_major':
            return {'hcp_range': (6, 10), 'is_balanced': True, 'max_suit_length': 3}  # No 4-card major
        else:  # weak
            return {'hcp_range': (0, 5)}

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        spades = hand.suit_lengths['♠']
        hearts = hand.suit_lengths['♥']

        # Too weak to respond?
        if hand.hcp < 6:
            bid = 'Pass'
            explanation = f'{hand.hcp} HCP is too weak to respond (need 6+).'
        # Has 4-card major? Bid up-the-line (hearts before spades)
        elif hearts >= 4:
            bid = '1♥'
            explanation = f'Bid 1♥ with {hearts} hearts. Always show a 4-card major over a minor.'
        elif spades >= 4:
            bid = '1♠'
            explanation = f'Bid 1♠ with {spades} spades. Show your 4-card major.'
        # NT response
        elif hand.hcp >= 6 and hand.hcp <= 10:
            bid = '1NT'
            explanation = f'{hand.hcp} HCP, no 4-card major - respond 1NT.'
        elif hand.hcp >= 11 and hand.hcp <= 12:
            bid = '2NT'
            explanation = f'{hand.hcp} HCP, no 4-card major - 2NT is invitational.'
        else:
            bid = '3NT'
            explanation = f'{hand.hcp} HCP, no 4-card major - 3NT to play.'

        return {
            'bid': bid,
            'explanation': explanation,
            'opening_bid': self.opening_bid,
            'partner_opened': self.opening_bid
        }


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
        spades = hand.suit_lengths.get('♠', 0)
        hearts = hand.suit_lengths.get('♥', 0)

        # Check for 5+ card major -> Jacoby Transfer (ANY point count!)
        if hearts >= 5:
            bid = '2♦'
            explanation = f'Transfer to hearts (2♦→2♥). Shows 5+ hearts. No minimum points needed!'
        elif spades >= 5:
            bid = '2♥'
            explanation = f'Transfer to spades (2♥→2♠). Shows 5+ spades. No minimum points needed!'
        # Check for 4-card major with 8+ points -> Stayman
        elif (spades == 4 or hearts == 4) and hand.hcp >= 8:
            major = 'spades' if spades == 4 else 'hearts'
            bid = '2♣'
            explanation = f'Stayman (2♣) with 4 {major} and {hand.hcp} HCP. Asks partner for a 4-card major.'
        # Has 4-card major but too weak for Stayman
        elif (spades == 4 or hearts == 4) and hand.hcp <= 7:
            bid = 'Pass'
            major = 'spades' if spades == 4 else 'hearts'
            explanation = f'{hand.hcp} HCP with 4 {major} - pass. Too weak for Stayman (needs 8+ HCP to invite game).'
        # Balanced responses without major suit interest
        elif hand.hcp <= 7 and hand.is_balanced:
            bid = 'Pass'
            explanation = f'{hand.hcp} HCP balanced, no 4+ major - pass. Too weak for Stayman (needs 8+) and no 5-card major to transfer.'
        elif 8 <= hand.hcp <= 9:
            bid = '2NT'
            explanation = f'{hand.hcp} HCP - invite to game with 2NT (partner bids 3NT with max 17)'
        elif hand.hcp >= 10:
            bid = '3NT'
            explanation = f'{hand.hcp} HCP - bid 3NT (combined 25+, game values!)'
        else:
            bid = 'Pass'
            explanation = 'Weak hand - pass'

        return {'bid': bid, 'explanation': explanation, 'partner_opened': '1NT'}


class RespondingTo2CGenerator(SkillHandGenerator):
    """Generate hands for responding to 2C opening."""

    skill_id = 'responding_to_2c'
    skill_level = 2
    description = 'Practice responding to partner\'s strong 2C'

    def get_constraints(self) -> Dict:
        return {'hcp_range': (0, 12)}

    def _has_good_suit(self, hand: Hand, suit: str) -> bool:
        """
        Check if suit has two of the top three honors (A, K, Q).
        A 'good suit' qualifies for a positive response regardless of HCP.
        """
        if hand.suit_lengths.get(suit, 0) < 5:
            return False

        # Count top honors in this suit
        top_honors = 0
        for card in hand.cards:
            if card.suit == suit and card.rank in ['A', 'K', 'Q']:
                top_honors += 1

        return top_honors >= 2

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        # Check for positive response conditions:
        # 1. 8+ HCP with any 5+ card suit, OR
        # 2. Good 5+ card suit (two of top three honors: AK, AQ, or KQ)

        # First check for good suits (qualifies for positive regardless of HCP)
        for suit in ['♠', '♥', '♦', '♣']:
            if hand.suit_lengths.get(suit, 0) >= 5 and self._has_good_suit(hand, suit):
                bid = f'2{suit}' if suit in ['♠', '♥'] else f'3{suit}'
                explanation = f'Positive response showing good {suit} suit (two of top three honors).'
                return {'bid': bid, 'explanation': explanation, 'partner_opened': '2♣'}

        # Then check for 8+ HCP positive responses
        if hand.hcp >= 8:
            # Positive response based on HCP
            if hand.suit_lengths['♠'] >= 5:
                bid = '2♠'
                explanation = f'{hand.hcp} HCP with 5+ spades - positive response.'
            elif hand.suit_lengths['♥'] >= 5:
                bid = '2♥'
                explanation = f'{hand.hcp} HCP with 5+ hearts - positive response.'
            else:
                bid = '2NT'
                explanation = f'{hand.hcp} HCP balanced - positive response (2NT).'
            return {'bid': bid, 'explanation': explanation, 'partner_opened': '2♣'}

        # Default: waiting response
        bid = '2♦'
        explanation = f'{hand.hcp} HCP, no good suit - waiting bid (2♦).'

        return {'bid': bid, 'explanation': explanation, 'partner_opened': '2♣'}


class RespondingTo2NTGenerator(SkillHandGenerator):
    """Generate hands for responding to 2NT opening."""

    skill_id = 'responding_to_2nt'
    skill_level = 2
    description = 'Practice responding to partner\'s 2NT opening'

    def get_constraints(self) -> Dict:
        return {'hcp_range': (0, 12)}

    def get_expected_response(self, hand: Hand, auction: List[str] = None) -> Dict:
        # Partner has 20-21 HCP
        # After 2NT, transfers are at the 3-level: 3♦ = hearts, 3♥ = spades
        # Stayman is 3♣

        spades = hand.suit_lengths.get('♠', 0)
        hearts = hand.suit_lengths.get('♥', 0)

        # Check for 5+ card major -> Transfer (any point count!)
        # With a long major, playing in the major suit is usually better than 2NT
        if hearts >= 5:
            bid = '3♦'
            explanation = f'Transfer to hearts (3♦→3♥). With {hearts} hearts, a suit contract plays better than NT.'
        elif spades >= 5:
            bid = '3♥'
            explanation = f'Transfer to spades (3♥→3♠). With {spades} spades, a suit contract plays better than NT.'
        # Check for 4-card major with game values -> Stayman
        elif (spades == 4 or hearts == 4) and hand.hcp >= 4:
            major = 'spades' if spades == 4 else 'hearts'
            bid = '3♣'
            explanation = f'Stayman (3♣) with 4 {major}. Looking for a 4-4 major fit.'
        # No major suit interest - decide based on points
        # Partner has 20-21, game (25) needs 4-5 pts
        elif hand.hcp <= 3:
            bid = 'Pass'
            explanation = f'{hand.hcp} HCP - game unlikely (need ~4+ to reach 25 combined), pass.'
        elif hand.hcp >= 4:
            bid = '3NT'
            explanation = f'{hand.hcp} HCP + partner\'s 20-21 = {hand.hcp + 20}-{hand.hcp + 21} combined. Bid game!'
        else:
            bid = 'Pass'
            explanation = 'Weak hand - pass'

        return {'bid': bid, 'explanation': explanation, 'partner_opened': '2NT'}


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
    # Level 0: Foundations
    'hand_evaluation_basics': HandEvaluationBasicsGenerator,
    'suit_quality': SuitQualityGenerator,
    'bidding_language': BiddingLanguageGenerator,

    # Level 1: Basic Bidding Actions (Foundational Conventions)
    'when_to_pass': WhenToPassGenerator,
    'opening_one_major': OpeningOneMajorGenerator,
    'opening_one_minor': OpeningOneMinorGenerator,
    'single_raise': SingleRaiseGenerator,
    'limit_raise': LimitRaiseGenerator,
    'new_suit_response': NewSuitResponseGenerator,
    'dustbin_1nt_response': DustbinNTResponseGenerator,
    'game_raise': GameRaiseGenerator,
    'two_over_one_response': TwoOverOneResponseGenerator,

    # Level 2: Rebids (Foundational - V3 Logic Stack)
    # These map foundational convention IDs to existing generators
    'opener_rebid': RebidAfter1LevelGenerator,  # Primary opener rebid generator
    'responder_rebid': AfterOpenerRaisesGenerator,  # Primary responder rebid generator

    # Level 2: Opening Bids (Advanced)
    'when_to_open': WhenToOpenGenerator,
    'opening_one_suit': OpeningOneSuitGenerator,
    'opening_1nt': Opening1NTGenerator,
    'opening_2c_strong': Opening2CStrongGenerator,
    'opening_2nt': Opening2NTGenerator,

    # Level 3: Responding to Openings
    'responding_to_major': RespondingToMajorGenerator,
    'responding_to_minor': RespondingToMinorGenerator,
    'responding_to_1nt': RespondingTo1NTGenerator,
    'responding_to_2c': RespondingTo2CGenerator,
    'responding_to_2nt': RespondingTo2NTGenerator,

    # Level 4: Opener's Rebids (Detailed)
    'rebid_after_1_level': RebidAfter1LevelGenerator,
    'rebid_after_2_level': RebidAfter2LevelGenerator,
    'rebid_after_raise': RebidAfterRaiseGenerator,
    'rebid_after_1nt_response': RebidAfter1NTResponseGenerator,

    # Level 5: Responder's Rebids (Detailed)
    'after_opener_raises': AfterOpenerRaisesGenerator,
    'after_opener_rebids_suit': AfterOpenerRebidsSuitGenerator,
    'after_opener_new_suit': AfterOpenerNewSuitGenerator,
    'after_opener_rebids_nt': AfterOpenerRebidsNTGenerator,
    'preference_bids': PreferenceBidsGenerator,

    # Level 7: Competitive Bidding
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

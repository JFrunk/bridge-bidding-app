"""
Hand Generators for Play Learning Mode Skills

Generates hands for practicing declarer play skills (Levels 0-8).
Each skill generates specific play situations for practice.

Play skills differ from bidding skills:
- Need all 4 hands visible (or dummy at minimum)
- Practice formats: single_decision, mini_hand, full_hand
- Some situations accept multiple valid plays

Usage:
    from engine.learning.play_skill_hand_generators import get_play_skill_hand_generator

    generator = get_play_skill_hand_generator('counting_winners')
    deal, situation = generator.generate()
"""

import random
from typing import Dict, List, Optional, Tuple, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass

from engine.hand import Hand, Card


def create_deck() -> List[Card]:
    """Create a standard 52-card deck."""
    suits = ['♠', '♥', '♦', '♣']
    ranks = '23456789TJQKA'
    return [Card(rank, suit) for suit in suits for rank in ranks]


def shuffle_deck() -> List[Card]:
    """Create and shuffle a deck."""
    deck = create_deck()
    random.shuffle(deck)
    return deck


@dataclass
class PlayDeal:
    """Complete deal for play practice."""
    declarer_hand: Hand
    dummy_hand: Hand
    lho_hand: Hand  # Left-hand opponent (plays after declarer)
    rho_hand: Hand  # Right-hand opponent (plays before declarer)
    contract: str  # e.g., "3NT", "4♠"
    declarer_position: str  # "South" typically
    lead: Optional[Card] = None  # Opening lead if specified

    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dictionary."""
        return {
            'declarer_hand': {
                'cards': [{'rank': c.rank, 'suit': c.suit} for c in self.declarer_hand.cards],
                'display': str(self.declarer_hand),
                'hcp': self.declarer_hand.hcp
            },
            'dummy_hand': {
                'cards': [{'rank': c.rank, 'suit': c.suit} for c in self.dummy_hand.cards],
                'display': str(self.dummy_hand),
                'hcp': self.dummy_hand.hcp
            },
            'contract': self.contract,
            'declarer_position': self.declarer_position,
            'lead': {'rank': self.lead.rank, 'suit': self.lead.suit} if self.lead else None,
            'combined_hcp': self.declarer_hand.hcp + self.dummy_hand.hcp
        }


class PlaySkillHandGenerator(ABC):
    """Base class for play skill hand generators."""

    skill_id: str = ""
    skill_level: int = 0
    description: str = ""
    practice_format: str = "single_decision"  # single_decision, mini_hand, full_hand

    @abstractmethod
    def generate(self) -> Tuple[PlayDeal, Dict]:
        """
        Generate a deal and situation for this skill.

        Returns:
            Tuple of (PlayDeal, situation_dict)
            situation_dict contains:
                - question: What the player is asked
                - expected_response: Correct answer(s)
                - explanation: Why the answer is correct
                - accepts_multiple: Whether multiple answers are acceptable
        """
        pass

    def get_expected_response(self, deal: PlayDeal, situation: Dict) -> Dict:
        """Get the expected response for evaluation."""
        return situation.get('expected_response', {})


def has_stopper_in_all_suits(declarer: Hand, dummy: Hand) -> bool:
    """
    Check if declarer/dummy have at least one stopper in every suit.

    A stopper is defined as:
    - Ace (always a stopper)
    - King with 2+ cards in the suit (protected king)
    - Queen with 3+ cards in the suit (protected queen)

    This ensures the hand is suitable for teaching "counting winners"
    without the complexity of danger suits.
    """
    suits = ['♠', '♥', '♦', '♣']

    for suit in suits:
        declarer_suit = [c for c in declarer.cards if c.suit == suit]
        dummy_suit = [c for c in dummy.cards if c.suit == suit]
        all_cards = declarer_suit + dummy_suit

        if not all_cards:
            # Void in both hands - no stopper
            return False

        ranks = [c.rank for c in all_cards]
        length = len(all_cards)

        # Check for stoppers
        has_ace = 'A' in ranks
        has_king = 'K' in ranks
        has_queen = 'Q' in ranks

        # Ace is always a stopper
        if has_ace:
            continue

        # King with 2+ cards is a stopper
        if has_king and length >= 2:
            continue

        # Queen with 3+ cards is a stopper
        if has_queen and length >= 3:
            continue

        # No stopper in this suit
        return False

    return True


def generate_nt_deal_with_winners(target_winners: int,
                                   min_hcp: int = 20,
                                   max_hcp: int = 28,
                                   require_all_stoppers: bool = False) -> Optional[PlayDeal]:
    """
    Generate a NT deal where declarer has approximately target_winners sure tricks.

    Args:
        target_winners: Desired number of sure tricks
        min_hcp: Minimum combined HCP
        max_hcp: Maximum combined HCP
        require_all_stoppers: If True, ensure declarer has a stopper in every suit
                              (useful for beginner exercises to avoid danger suit complexity)

    Returns:
        PlayDeal or None if can't generate
    """
    max_attempts = 500
    for _ in range(max_attempts):
        deck = shuffle_deck()

        # Deal 4 hands
        declarer_cards = deck[0:13]
        dummy_cards = deck[13:26]
        lho_cards = deck[26:39]
        rho_cards = deck[39:52]

        declarer = Hand(declarer_cards)
        dummy = Hand(dummy_cards)
        lho = Hand(lho_cards)
        rho = Hand(rho_cards)

        combined_hcp = declarer.hcp + dummy.hcp
        if not (min_hcp <= combined_hcp <= max_hcp):
            continue

        # Check for stoppers in all suits if required
        if require_all_stoppers and not has_stopper_in_all_suits(declarer, dummy):
            continue

        # Count sure winners (aces and kings with support)
        winners = count_sure_winners(declarer, dummy)

        # Allow some variance
        if abs(winners - target_winners) <= 1:
            return PlayDeal(
                declarer_hand=declarer,
                dummy_hand=dummy,
                lho_hand=lho,
                rho_hand=rho,
                contract='3NT',
                declarer_position='South'
            )

    return None


def count_sure_winners(declarer: Hand, dummy: Hand) -> int:
    """
    Count sure tricks in a NT contract.

    Counts:
    - Top sequential honors (A, A-K, A-K-Q, etc.)
    - Long cards that become winners after opponents exhaust their cards

    IMPORTANT: Each trick requires playing one card from EACH hand.
    So with 7 cards in dummy and 3 in declarer (10 total), you can only
    play 3 rounds before declarer is exhausted. The remaining 4 cards
    in dummy can still win if opponents are also exhausted.

    Example: Dummy has AK10987 (7 cards), Declarer has Q54 (3 cards)
    - Round 1: A from dummy, 5 from declarer (opponents play 2 cards)
    - Round 2: K from dummy, 4 from declarer (opponents play 2 cards)
    - Round 3: Q wins from declarer (or 10 from dummy), other hand plays
    - After 3 rounds: opponents played 3 cards each = 6 total, but they only had 3
    - So after ~2 rounds opponents are out, remaining cards in longer hand win

    Formula: winners = max(declarer_length, dummy_length) when we control the suit
    (because the longer hand's cards become winners after shorter hand exhausts)
    """
    winners = 0
    suits = ['♠', '♥', '♦', '♣']

    for suit in suits:
        # Get cards in this suit from each hand separately
        declarer_suit = [c for c in declarer.cards if c.suit == suit]
        dummy_suit = [c for c in dummy.cards if c.suit == suit]

        declarer_length = len(declarer_suit)
        dummy_length = len(dummy_suit)
        combined_length = declarer_length + dummy_length

        if combined_length == 0:
            continue

        # The longer hand determines max tricks we can take in this suit
        longer_hand_length = max(declarer_length, dummy_length)

        # Combine ranks to check for top honors
        ranks_in_suit = [c.rank for c in declarer_suit + dummy_suit]

        # Count top sequential honors (must start from Ace)
        has_ace = 'A' in ranks_in_suit
        has_king = 'K' in ranks_in_suit
        has_queen = 'Q' in ranks_in_suit
        has_jack = 'J' in ranks_in_suit
        has_ten = 'T' in ranks_in_suit

        top_honors = 0
        if has_ace:
            top_honors = 1
            if has_king:
                top_honors = 2
                if has_queen:
                    top_honors = 3
                    if has_jack:
                        top_honors = 4
                        if has_ten:
                            top_honors = 5

        # Opponents have (13 - combined_length) cards in this suit
        opponents_length = 13 - combined_length

        # Calculate sure winners in this suit
        if top_honors >= opponents_length and top_honors > 0:
            # We have enough top honors to exhaust opponents
            # Winners = length of longer hand (we can run the whole suit)
            winners += longer_hand_length
        else:
            # We can only count top sequential honors as sure winners
            # (opponents will still have cards after we play our top honors)
            winners += top_honors

    # Cap at 13 (maximum tricks in a hand)
    return min(winners, 13)


def count_losers_in_suit(hand: Hand, suit: str) -> int:
    """
    Count losers in a suit for trump contracts.
    Only looks at first 3 cards (loser count method).
    """
    suit_cards = [c for c in hand.cards if c.suit == suit]
    if len(suit_cards) == 0:
        return 0  # Void = no losers

    ranks = [c.rank for c in suit_cards]
    losers = 0

    # Look at up to 3 cards
    for i, rank in enumerate(sorted(ranks, key=lambda r: 'AKQJT98765432'.index(r))[:3]):
        if rank not in ['A', 'K', 'Q']:
            losers += 1
        elif rank == 'K' and len(suit_cards) == 1:
            losers += 0.5  # Singleton K is risky
        elif rank == 'Q' and len(suit_cards) <= 2:
            losers += 0.5  # Doubleton Q is risky

    return int(losers)


# ============================================================================
# LEVEL 0: PLAY FOUNDATIONS
# ============================================================================

class CountingWinnersGenerator(PlaySkillHandGenerator):
    """Generate hands for practicing counting winners in NT.

    For this foundational skill, hands are generated with stoppers in all suits
    to avoid the complexity of "danger suits" - that concept is taught later
    in the learning path.
    """

    skill_id = 'counting_winners'
    skill_level = 0
    description = 'Practice counting sure tricks in NT'
    practice_format = 'single_decision'

    def generate(self) -> Tuple[PlayDeal, Dict]:
        # Generate deals with varying winner counts (5-9 winners)
        # require_all_stoppers=True ensures no "danger suits" for this beginner exercise
        target_winners = random.choice([5, 6, 7, 8, 9])
        deal = generate_nt_deal_with_winners(
            target_winners,
            min_hcp=20,
            max_hcp=30,
            require_all_stoppers=True  # Avoid danger suit complexity for beginners
        )

        if deal is None:
            # Fallback: try again without stopper requirement (rare)
            deal = generate_nt_deal_with_winners(target_winners, min_hcp=20, max_hcp=30)

        if deal is None:
            # Last resort fallback: generate random deal
            deck = shuffle_deck()
            deal = PlayDeal(
                declarer_hand=Hand(deck[0:13]),
                dummy_hand=Hand(deck[13:26]),
                lho_hand=Hand(deck[26:39]),
                rho_hand=Hand(deck[39:52]),
                contract='3NT',
                declarer_position='South'
            )

        actual_winners = count_sure_winners(deal.declarer_hand, deal.dummy_hand)

        situation = {
            'question': 'How many sure tricks do you have in this NT contract?',
            'question_type': 'count_winners',
            'expected_response': {
                'winners': actual_winners,
                'explanation': f'Count your sure winners: Aces, Kings (if you have the Ace), etc.',
                'acceptable_range': (max(0, actual_winners - 1), actual_winners + 1)
            },
            'accepts_multiple': False
        }

        return deal, situation


class CountingLosersGenerator(PlaySkillHandGenerator):
    """Generate hands for practicing counting losers in suit contracts."""

    skill_id = 'counting_losers'
    skill_level = 0
    description = 'Practice counting losers in suit contracts'
    practice_format = 'single_decision'

    def generate(self) -> Tuple[PlayDeal, Dict]:
        # Generate a deal for a suit contract
        max_attempts = 500
        for _ in range(max_attempts):
            deck = shuffle_deck()
            declarer = Hand(deck[0:13])
            dummy = Hand(deck[13:26])

            # Need a trump suit with 8+ cards combined
            for trump_suit in ['♠', '♥']:
                combined_trumps = (declarer.suit_lengths[trump_suit] +
                                  dummy.suit_lengths[trump_suit])
                if combined_trumps >= 8:
                    # Good trump fit found
                    deal = PlayDeal(
                        declarer_hand=declarer,
                        dummy_hand=dummy,
                        lho_hand=Hand(deck[26:39]),
                        rho_hand=Hand(deck[39:52]),
                        contract=f'4{trump_suit}',
                        declarer_position='South'
                    )

                    # Count losers in declarer's hand
                    total_losers = 0
                    loser_breakdown = {}
                    for suit in ['♠', '♥', '♦', '♣']:
                        losers = count_losers_in_suit(declarer, suit)
                        total_losers += losers
                        loser_breakdown[suit] = losers

                    situation = {
                        'question': f'In a {deal.contract} contract, how many losers do you have in the South hand?',
                        'question_type': 'count_losers',
                        'expected_response': {
                            'losers': int(total_losers),
                            'breakdown': loser_breakdown,
                            'explanation': 'Count losers in each suit (first 3 cards). Void=0, Ace=0, Kx=1 loser, etc.',
                            'acceptable_range': (max(0, int(total_losers) - 1), int(total_losers) + 1)
                        },
                        'accepts_multiple': False,
                        'trump_suit': trump_suit
                    }

                    return deal, situation

        # Fallback
        deck = shuffle_deck()
        deal = PlayDeal(
            declarer_hand=Hand(deck[0:13]),
            dummy_hand=Hand(deck[13:26]),
            lho_hand=Hand(deck[26:39]),
            rho_hand=Hand(deck[39:52]),
            contract='4♠',
            declarer_position='South'
        )
        return deal, {'question': 'Count your losers', 'expected_response': {'losers': 4}}


class AnalyzingTheLeadGenerator(PlaySkillHandGenerator):
    """Generate hands for understanding opening leads."""

    skill_id = 'analyzing_the_lead'
    skill_level = 0
    description = 'Practice reading the opening lead'
    practice_format = 'single_decision'

    # Lead types and their meanings
    LEAD_TYPES = [
        ('fourth_best', 'Fourth best from a long suit (shows length and honors)'),
        ('top_sequence', 'Top of a sequence (KQJ, QJT, etc.)'),
        ('top_nothing', 'Top of nothing (small doubleton or worthless suit)'),
        ('ace_from_ak', 'Ace from A-K (looking for partner\'s signal)'),
    ]

    def generate(self) -> Tuple[PlayDeal, Dict]:
        lead_type, description = random.choice(self.LEAD_TYPES)

        # Generate appropriate hands based on lead type
        deck = shuffle_deck()

        # Place specific cards in LHO's hand based on lead type
        lho_cards = []
        lead_card = None

        if lead_type == 'fourth_best':
            # LHO has something like K-J-8-5-2 and leads the 5
            target_suit = random.choice(['♠', '♥', '♦', '♣'])
            suit_cards = [c for c in deck if c.suit == target_suit]
            # Pick 5 cards from suit including K, J, and small ones
            available_ranks = [c.rank for c in suit_cards]
            if 'K' in available_ranks and '5' in available_ranks:
                holding = ['K', 'J', '8', '5', '2']
                lho_suit_cards = [c for c in suit_cards if c.rank in holding[:5]]
                lead_card = next((c for c in lho_suit_cards if c.rank == '5'), None)

        elif lead_type == 'top_sequence':
            target_suit = random.choice(['♠', '♥', '♦', '♣'])
            suit_cards = [c for c in deck if c.suit == target_suit]
            # Try to get K-Q-J
            if any(c.rank == 'K' for c in suit_cards):
                lead_card = next((c for c in suit_cards if c.rank == 'K'), None)

        # Build remaining deal
        remaining = [c for c in deck if c != lead_card]
        random.shuffle(remaining)

        deal = PlayDeal(
            declarer_hand=Hand(remaining[0:13]),
            dummy_hand=Hand(remaining[13:26]),
            lho_hand=Hand(remaining[26:39]),
            rho_hand=Hand(remaining[39:52]),
            contract='3NT',
            declarer_position='South',
            lead=lead_card
        )

        situation = {
            'question': f'LHO leads the {lead_card.rank if lead_card else "?"}{lead_card.suit if lead_card else "?"}. What does this lead likely show?',
            'question_type': 'analyze_lead',
            'expected_response': {
                'lead_type': lead_type,
                'meaning': description,
                'explanation': description
            },
            'accepts_multiple': False,
            'options': [lt[0] for lt in self.LEAD_TYPES]
        }

        return deal, situation


# ============================================================================
# LEVEL 2: FINESSING
# ============================================================================

class SimpleFinessGenerator(PlaySkillHandGenerator):
    """Generate hands for practicing simple finesses."""

    skill_id = 'simple_finesse'
    skill_level = 2
    description = 'Practice simple finesses (AQ vs K)'
    practice_format = 'single_decision'

    # Finesse holdings and their correct plays
    FINESSE_HOLDINGS = [
        # (declarer_holding, dummy_holding, correct_play, explanation)
        ('AQ3', 'xxx', 'Lead low toward AQ, play Q', 'Lead toward the AQ. If LHO plays low, finesse the Queen.'),
        ('AQJ', 'xxx', 'Lead low toward AQJ, play J', 'Lead toward AQJ. Finesse the Jack first (might pin the 10).'),
        ('KJT', 'xxx', 'Lead low toward KJT, play T or J', 'Lead toward the King-Jack. Finesse against the Queen.'),
        ('AJT', 'Kxx', 'Cash K, lead toward AJT, finesse J', 'With K opposite AJT, cash King then finesse the Jack.'),
    ]

    def generate(self) -> Tuple[PlayDeal, Dict]:
        # Pick a finesse situation
        holding = random.choice(self.FINESSE_HOLDINGS)
        declarer_str, dummy_str, correct_play, explanation = holding

        # Generate a deal with this holding
        target_suit = random.choice(['♠', '♥'])  # Majors for clarity
        deck = create_deck()

        # Build the specific holding
        declarer_suit_cards = []
        dummy_suit_cards = []

        # Parse holding strings and create cards
        for rank in declarer_str.replace('x', ''):
            card = next((c for c in deck if c.suit == target_suit and c.rank == rank), None)
            if card:
                declarer_suit_cards.append(card)
                deck.remove(card)

        # Fill with small cards for 'x'
        x_count = declarer_str.count('x')
        small_cards = [c for c in deck if c.suit == target_suit and c.rank in '23456']
        for i in range(x_count):
            if small_cards:
                card = small_cards.pop()
                declarer_suit_cards.append(card)
                deck.remove(card)

        for rank in dummy_str.replace('x', ''):
            card = next((c for c in deck if c.suit == target_suit and c.rank == rank), None)
            if card:
                dummy_suit_cards.append(card)
                deck.remove(card)

        x_count = dummy_str.count('x')
        small_cards = [c for c in deck if c.suit == target_suit and c.rank in '789']
        for i in range(x_count):
            if small_cards:
                card = small_cards.pop()
                dummy_suit_cards.append(card)
                deck.remove(card)

        # Complete hands with remaining cards
        random.shuffle(deck)

        # Ensure 13 cards each
        declarer_other = deck[:13 - len(declarer_suit_cards)]
        deck = deck[13 - len(declarer_suit_cards):]
        dummy_other = deck[:13 - len(dummy_suit_cards)]
        deck = deck[13 - len(dummy_suit_cards):]

        declarer = Hand(declarer_suit_cards + declarer_other)
        dummy = Hand(dummy_suit_cards + dummy_other)
        lho = Hand(deck[:13])
        rho = Hand(deck[13:26])

        deal = PlayDeal(
            declarer_hand=declarer,
            dummy_hand=dummy,
            lho_hand=lho,
            rho_hand=rho,
            contract='3NT',
            declarer_position='South'
        )

        situation = {
            'question': f'You hold {declarer_str} in your hand and {dummy_str} in dummy ({target_suit} suit). How do you play this suit for maximum tricks?',
            'question_type': 'finesse_play',
            'expected_response': {
                'correct_play': correct_play,
                'explanation': explanation,
                'suit': target_suit
            },
            'accepts_multiple': False
        }

        return deal, situation


class FinesseOrDropGenerator(PlaySkillHandGenerator):
    """Generate hands for finesse vs. drop decisions."""

    skill_id = 'finesse_or_drop'
    skill_level = 2
    description = 'Practice choosing between finesse and drop'
    practice_format = 'single_decision'

    def generate(self) -> Tuple[PlayDeal, Dict]:
        # Create holdings where decision matters
        # With 9+ cards missing Q: play for drop (52%)
        # With 8 cards missing Q: finesse slightly better (52% vs 48%)

        target_suit = random.choice(['♠', '♥'])
        combined_length = random.choice([8, 9, 10])  # Cards in suit combined

        deck = create_deck()
        suit_cards = [c for c in deck if c.suit == target_suit]

        # Give declarer A-K-x-x-x
        # Give dummy matching length
        high_cards = [c for c in suit_cards if c.rank in ['A', 'K']]
        remaining_suit = [c for c in suit_cards if c.rank not in ['A', 'K', 'Q']]
        random.shuffle(remaining_suit)

        declarer_suit = high_cards + remaining_suit[:3]  # 5 cards: A K x x x
        dummy_length = combined_length - 5
        dummy_suit = remaining_suit[3:3 + dummy_length]

        # Build hands
        for c in declarer_suit + dummy_suit:
            deck.remove(c)

        random.shuffle(deck)

        declarer_other = deck[:13 - len(declarer_suit)]
        deck = deck[13 - len(declarer_suit):]
        dummy_other = deck[:13 - len(dummy_suit)]
        deck = deck[13 - len(dummy_suit):]

        deal = PlayDeal(
            declarer_hand=Hand(declarer_suit + declarer_other),
            dummy_hand=Hand(dummy_suit + dummy_other),
            lho_hand=Hand(deck[:13]),
            rho_hand=Hand(deck[13:26]),
            contract='3NT',
            declarer_position='South'
        )

        # Correct answer depends on combined length
        if combined_length >= 9:
            correct = 'drop'
            explanation = f'With {combined_length} cards missing the Queen, play for the drop. The Q is more likely to fall.'
        else:
            correct = 'finesse'
            explanation = f'With {combined_length} cards missing the Queen, the finesse is slightly better (52% vs 48%).'

        situation = {
            'question': f'You have A-K and {combined_length - 2} small cards in {target_suit}. Missing the Queen. Do you finesse or play for the drop?',
            'question_type': 'finesse_or_drop',
            'expected_response': {
                'correct_play': correct,
                'explanation': explanation,
                'combined_cards': combined_length
            },
            'accepts_multiple': False,
            'options': ['finesse', 'drop']
        }

        return deal, situation


# ============================================================================
# LEVEL 3: SUIT ESTABLISHMENT
# ============================================================================

class EstablishingLongSuitsGenerator(PlaySkillHandGenerator):
    """Generate hands for practicing suit establishment."""

    skill_id = 'establishing_long_suits'
    skill_level = 3
    description = 'Practice establishing long suits'
    practice_format = 'mini_hand'

    def generate(self) -> Tuple[PlayDeal, Dict]:
        # Create a hand where declarer needs to establish a long suit
        target_suit = random.choice(['♦', '♣'])  # Minor suit typically

        deck = create_deck()
        suit_cards = [c for c in deck if c.suit == target_suit]

        # Give declarer/dummy A-x-x-x-x opposite K-x (7 cards)
        # Need to lose 2 tricks to establish 2 winners
        ace = next(c for c in suit_cards if c.rank == 'A')
        king = next(c for c in suit_cards if c.rank == 'K')
        small_cards = [c for c in suit_cards if c.rank not in ['A', 'K', 'Q', 'J']]
        random.shuffle(small_cards)

        declarer_suit = [ace] + small_cards[:4]  # A-x-x-x-x
        dummy_suit = [king] + small_cards[4:5]   # K-x

        for c in declarer_suit + dummy_suit:
            deck.remove(c)

        random.shuffle(deck)

        declarer_other = deck[:13 - len(declarer_suit)]
        deck = deck[8:]
        dummy_other = deck[:13 - len(dummy_suit)]
        deck = deck[11:]

        deal = PlayDeal(
            declarer_hand=Hand(declarer_suit + declarer_other),
            dummy_hand=Hand(dummy_suit + dummy_other),
            lho_hand=Hand(deck[:13]),
            rho_hand=Hand(deck[13:26]),
            contract='3NT',
            declarer_position='South'
        )

        situation = {
            'question': f'You have A-x-x-x-x in {target_suit} opposite K-x. How many tricks can you establish and how many times must you lose the lead?',
            'question_type': 'establish_suit',
            'expected_response': {
                'tricks_available': 5,
                'tricks_to_lose': 2,
                'explanation': 'With 7 cards, opponents have 6. After cashing A-K, lose 2 tricks to clear the suit. The remaining 3 small cards become winners.'
            },
            'accepts_multiple': False
        }

        return deal, situation


class HoldUpPlaysGenerator(PlaySkillHandGenerator):
    """Generate hands for practicing hold-up plays."""

    skill_id = 'hold_up_plays'
    skill_level = 3
    description = 'Practice hold-up plays in NT'
    practice_format = 'mini_hand'

    def generate(self) -> Tuple[PlayDeal, Dict]:
        # Classic NT hold-up: declarer has A-x-x in enemy's suit
        # Should duck twice to break communications

        deck = create_deck()
        lead_suit = random.choice(['♠', '♥'])  # Major suit lead

        # Give declarer A-x-x in lead suit
        suit_cards = [c for c in deck if c.suit == lead_suit]
        ace = next(c for c in suit_cards if c.rank == 'A')
        small = [c for c in suit_cards if c.rank in ['3', '4', '5']][:2]

        declarer_suit = [ace] + small

        for c in declarer_suit:
            deck.remove(c)

        # Give LHO a 5-card suit headed by K-Q
        remaining_suit = [c for c in deck if c.suit == lead_suit]
        king = next((c for c in remaining_suit if c.rank == 'K'), None)
        queen = next((c for c in remaining_suit if c.rank == 'Q'), None)

        random.shuffle(deck)

        deal = PlayDeal(
            declarer_hand=Hand(declarer_suit + deck[:10]),
            dummy_hand=Hand(deck[10:23]),
            lho_hand=Hand(deck[23:36]),
            rho_hand=Hand(deck[36:49]),
            contract='3NT',
            declarer_position='South',
            lead=king
        )

        situation = {
            'question': f'LHO leads the K{lead_suit}. You have A-x-x in that suit. What is the correct play at trick 1?',
            'question_type': 'hold_up',
            'expected_response': {
                'correct_play': 'duck',
                'explanation': 'Hold up the Ace! Duck this trick and the next. Win the third round. This exhausts RHO of the suit, so if RHO gets in later, they cannot return the suit to LHO.'
            },
            'accepts_multiple': False,
            'options': ['win_ace', 'duck']
        }

        return deal, situation


# ============================================================================
# LEVEL 4: TRUMP MANAGEMENT
# ============================================================================

class DrawingTrumpsGenerator(PlaySkillHandGenerator):
    """Generate hands for trump drawing decisions."""

    skill_id = 'drawing_trumps'
    skill_level = 4
    description = 'Practice when to draw trumps'
    practice_format = 'single_decision'

    def generate(self) -> Tuple[PlayDeal, Dict]:
        trump_suit = random.choice(['♠', '♥'])
        scenario = random.choice(['draw_immediately', 'delay_for_ruff'])

        deck = create_deck()

        if scenario == 'draw_immediately':
            # No need to ruff, draw trumps to prevent overruff
            # Combined 9 trumps, no side suit voids
            trump_cards = [c for c in deck if c.suit == trump_suit]
            declarer_trumps = trump_cards[:5]
            dummy_trumps = trump_cards[5:9]

            for c in declarer_trumps + dummy_trumps:
                deck.remove(c)

            random.shuffle(deck)

            deal = PlayDeal(
                declarer_hand=Hand(declarer_trumps + deck[:8]),
                dummy_hand=Hand(dummy_trumps + deck[8:17]),
                lho_hand=Hand(deck[17:30]),
                rho_hand=Hand(deck[30:43]),
                contract=f'4{trump_suit}',
                declarer_position='South'
            )

            explanation = 'With 9 trumps and no ruffs needed, draw trumps immediately. This prevents opponents from ruffing your winners.'
            correct = 'draw_trumps'

        else:  # delay_for_ruff
            # Need to ruff losers in dummy before drawing trumps
            trump_cards = [c for c in deck if c.suit == trump_suit]
            declarer_trumps = trump_cards[:5]
            dummy_trumps = trump_cards[5:8]  # Only 3 in dummy

            for c in declarer_trumps + dummy_trumps:
                deck.remove(c)

            # Give dummy a void/doubleton to ruff
            random.shuffle(deck)

            deal = PlayDeal(
                declarer_hand=Hand(declarer_trumps + deck[:8]),
                dummy_hand=Hand(dummy_trumps + deck[8:18]),
                lho_hand=Hand(deck[18:31]),
                rho_hand=Hand(deck[31:44]),
                contract=f'4{trump_suit}',
                declarer_position='South'
            )

            explanation = 'Delay drawing trumps! Use dummy\'s trumps to ruff your losers first. Drawing trumps would waste dummy\'s trump tricks.'
            correct = 'delay'

        situation = {
            'question': f'You\'re in 4{trump_suit}. Should you draw trumps immediately or delay?',
            'question_type': 'draw_trumps_decision',
            'expected_response': {
                'correct_play': correct,
                'explanation': explanation,
                'scenario': scenario
            },
            'accepts_multiple': False,
            'options': ['draw_trumps', 'delay']
        }

        return deal, situation


class RuffingLosersGenerator(PlaySkillHandGenerator):
    """Generate hands for ruffing loser decisions."""

    skill_id = 'ruffing_losers'
    skill_level = 4
    description = 'Practice ruffing losers in the short hand'
    practice_format = 'mini_hand'

    def generate(self) -> Tuple[PlayDeal, Dict]:
        trump_suit = random.choice(['♠', '♥'])
        side_suit = '♦' if trump_suit == '♠' else '♣'

        deck = create_deck()

        # Declarer has 5 trumps, dummy has 3
        # Declarer has losers in side suit, dummy is short
        trump_cards = [c for c in deck if c.suit == trump_suit]
        declarer_trumps = trump_cards[:5]
        dummy_trumps = trump_cards[5:8]

        for c in declarer_trumps + dummy_trumps:
            deck.remove(c)

        # Give dummy a doubleton in side suit
        side_cards = [c for c in deck if c.suit == side_suit]
        dummy_side = side_cards[:2]
        declarer_side = side_cards[2:6]  # 4 cards = 2 losers to ruff

        for c in dummy_side + declarer_side:
            deck.remove(c)

        random.shuffle(deck)

        deal = PlayDeal(
            declarer_hand=Hand(declarer_trumps + declarer_side + deck[:4]),
            dummy_hand=Hand(dummy_trumps + dummy_side + deck[4:12]),
            lho_hand=Hand(deck[12:25]),
            rho_hand=Hand(deck[25:38]),
            contract=f'4{trump_suit}',
            declarer_position='South'
        )

        situation = {
            'question': f'You have 4 {side_suit} cards in hand and only 2 in dummy. How do you use dummy\'s trumps?',
            'question_type': 'ruffing_losers',
            'expected_response': {
                'correct_play': 'ruff_in_dummy',
                'ruffs_available': 2,
                'explanation': 'Cash the 2 side suit winners, then ruff your 2 losers with dummy\'s trumps. Always ruff in the SHORT hand (dummy) to create extra tricks.'
            },
            'accepts_multiple': False
        }

        return deal, situation


# ============================================================================
# GENERATOR REGISTRY
# ============================================================================

PLAY_SKILL_GENERATORS = {
    # Level 0: Foundations
    'counting_winners': CountingWinnersGenerator,
    'counting_losers': CountingLosersGenerator,
    'analyzing_the_lead': AnalyzingTheLeadGenerator,

    # Level 2: Finessing
    'simple_finesse': SimpleFinessGenerator,
    'finesse_or_drop': FinesseOrDropGenerator,

    # Level 3: Suit Establishment
    'establishing_long_suits': EstablishingLongSuitsGenerator,
    'hold_up_plays': HoldUpPlaysGenerator,

    # Level 4: Trump Management
    'drawing_trumps': DrawingTrumpsGenerator,
    'ruffing_losers': RuffingLosersGenerator,
}


def get_play_skill_hand_generator(skill_id: str) -> Optional[PlaySkillHandGenerator]:
    """
    Get a hand generator for a specific play skill.

    Args:
        skill_id: The skill ID from play_skill_tree.py

    Returns:
        PlaySkillHandGenerator instance or None if skill not found
    """
    generator_class = PLAY_SKILL_GENERATORS.get(skill_id)
    if not generator_class:
        return None
    return generator_class()


def get_available_play_skills() -> List[str]:
    """Get list of all play skill IDs with hand generators."""
    return list(PLAY_SKILL_GENERATORS.keys())

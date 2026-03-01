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


def holding_to_cards(holding_str: str, suit: str, deck: List[Card]) -> Tuple[List[Card], List[Card]]:
    """
    Convert a holding string (like 'KQJ', 'xxx', or 'QJ10') to actual cards.
    'x' represents any small card (2-9).
    '10' is handled as a single rank 'T'.

    Returns: (cards_for_holding, remaining_deck)
    """
    cards = []
    small_cards = [c for c in deck if c.suit == suit and c.rank in '23456789']

    # Replace '10' with 'T' for easier parsing
    holding_str = holding_str.replace('10', 'T')

    for char in holding_str:
        if char == 'x':
            # Use a small card from the deck
            if small_cards:
                card = small_cards.pop(0)
                cards.append(card)
                deck = [c for c in deck if c != card]
        else:
            # Specific rank
            card = Card(char, suit)
            if card in deck:
                cards.append(card)
                deck = [c for c in deck if c != card]

    return cards, deck


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
        lho_suit_cards = []
        lead_card = None

        if lead_type == 'fourth_best':
            # LHO has something like K-J-8-5-2 and leads the 5
            target_suit = random.choice(['♠', '♥', '♦', '♣'])
            lho_suit_cards, deck = holding_to_cards('KJ852', target_suit, deck)
            lead_card = next((c for c in lho_suit_cards if c.rank == '5'), lho_suit_cards[3])

        elif lead_type == 'top_sequence':
            target_suit = random.choice(['♠', '♥', '♦', '♣'])
            lho_suit_cards, deck = holding_to_cards('KQJx', target_suit, deck)
            lead_card = lho_suit_cards[0]  # King (top of sequence)

        elif lead_type == 'top_nothing':
            target_suit = random.choice(['♠', '♥', '♦', '♣'])
            lho_suit_cards, deck = holding_to_cards('xx', target_suit, deck)
            lead_card = lho_suit_cards[0]  # Top of doubleton

        elif lead_type == 'ace_from_ak':
            target_suit = random.choice(['♠', '♥', '♦', '♣'])
            lho_suit_cards, deck = holding_to_cards('AKx', target_suit, deck)
            lead_card = lho_suit_cards[0]  # Ace

        # Build LHO hand with the specific suit holding
        lho_other_cards = deck[:13 - len(lho_suit_cards)]
        deck = deck[13 - len(lho_suit_cards):]
        lho_all_cards = lho_suit_cards + lho_other_cards

        # Deal remaining hands
        deal = PlayDeal(
            declarer_hand=Hand(deck[0:13]),
            dummy_hand=Hand(deck[13:26]),
            lho_hand=Hand(lho_all_cards),
            rho_hand=Hand(deck[26:39]),
            contract='3NT',
            declarer_position='South',
            lead=lead_card
        )

        situation = {
            'question': f'LHO leads the {lead_card.rank}{lead_card.suit}. What does this lead likely show?',
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
# LEVEL 1: BASIC TECHNIQUES
# ============================================================================

class ThirdHandHighGenerator(PlaySkillHandGenerator):
    """Generate hands for practicing third hand play."""

    skill_id = 'third_hand_high'
    skill_level = 1
    description = 'Practice playing high in third seat'
    practice_format = 'single_decision'

    # Third hand situations
    SITUATIONS = [
        # (your_holding, dummy_plays, correct_card, explanation)
        ('KQJ', '3', 'J', 'Play the Jack - lowest card from your sequence that wins the trick.'),
        ('KQ2', '3', 'Q', 'Play the Queen - second-highest from touching honors when dummy plays low.'),
        ('AQJ', '3', 'J', 'Play the Jack - finesse position, lowest card that might win.'),
        ('AQ5', '3', 'Q', 'Play the Queen - try to win or force a higher card.'),
        ('A95', 'K', 'A', 'Play the Ace - must beat dummy\'s King to win the trick.'),
        ('K84', 'A', '4', 'Play low - dummy\'s Ace wins, save your King for later.'),
        ('J94', 'Q', '4', 'Play low - dummy\'s Queen wins, save your Jack.'),
        ('543', '2', '5', 'Play high from nothing - the 5 is your best card.'),
        ('QJ3', '2', 'J', 'Play the Jack - bottom of touching honors.'),
        ('K53', 'Q', 'K', 'Play the King - try to force out the Ace or win if partner has it.'),
    ]

    def generate(self) -> Tuple[PlayDeal, Dict]:
        # Pick a situation
        your_holding_str, dummy_card, correct_card, explanation = random.choice(self.SITUATIONS)

        # Determine suit (use a simple suit for teaching)
        suit = random.choice(['♦', '♣'])  # Use minors to avoid confusion with trump

        # Build your hand with this holding in the practice suit
        # Convert holding string to cards
        your_cards_in_suit = [Card(rank, suit) for rank in your_holding_str]

        # Create a simple deck and build hands
        deck = shuffle_deck()

        # Remove the cards we're using for this suit
        for card in your_cards_in_suit:
            deck = [c for c in deck if not (c.rank == card.rank and c.suit == card.suit)]

        # Add one more card to dummy in this suit (the one that will be played)
        dummy_card_in_suit = Card(dummy_card, suit)
        if dummy_card_in_suit in deck:
            deck.remove(dummy_card_in_suit)

        # Build minimal hands for the situation
        # Your hand: holding in suit + random cards
        your_hand_cards = your_cards_in_suit + deck[:10]
        your_hand = Hand(your_hand_cards[:13])

        # Dummy: card in suit + random cards
        deck = deck[10:]
        dummy_cards = [dummy_card_in_suit] + deck[:12]
        dummy_hand = Hand(dummy_cards[:13])

        # Complete the deal (opponent hands don't matter for this exercise)
        deck = deck[12:]
        lho_hand = Hand(deck[:13])
        rho_hand = Hand(deck[13:26])

        # Contract doesn't matter much - use NT
        deal = PlayDeal(
            declarer_hand=your_hand,
            dummy_hand=dummy_hand,
            lho_hand=lho_hand,
            rho_hand=rho_hand,
            contract='3NT',
            declarer_position='South',
            lead=None  # Partner's lead not shown explicitly
        )

        # Determine suit name for question
        suit_names = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}
        suit_name = suit_names[suit]

        situation = {
            'question': f'Partner leads a low {suit_name}, dummy plays the {dummy_card}. Which card do you play from your hand?',
            'question_type': 'third_hand_play',
            'expected_response': {
                'card': correct_card,
                'suit': suit,
                'full_card': f'{correct_card}{suit}'
            },
            'explanation': explanation,
            'accepts_multiple': False,
            'context': {
                'suit': suit,
                'dummy_played': dummy_card,
                'your_holding': your_holding_str
            }
        }

        return deal, situation


class LeadingToTricksGenerator(PlaySkillHandGenerator):
    """Generate hands for practicing leading decisions."""

    skill_id = 'leading_to_tricks'
    skill_level = 1
    description = 'Practice which card to lead from various holdings'
    practice_format = 'single_decision'

    # Leading situations
    SITUATIONS = [
        # (your_holding, dummy_holding, correct_lead, explanation)
        ('KQJ', 'xxx', 'K', 'Lead top of sequence (KQJ) - the King. This drives out the Ace.'),
        ('QJ3', 'xxx', 'Q', 'Lead top of sequence (QJ) - the Queen. This forces the King.'),
        ('J109', 'xxx', 'J', 'Lead top of sequence (J10) - the Jack. Interior sequences start at the top.'),
        ('432', 'AK5', '3', 'Lead low toward honors in dummy. The 3 leads to dummy\'s AK.'),
        ('K52', 'AQ4', '2', 'Lead low toward honors. Never lead away from a King without the Queen.'),
        ('Q63', 'AJ5', '3', 'Lead low toward dummy\'s AJ. Leading the Queen would waste it.'),
        ('AK3', 'xxx', 'A', 'Lead top of touching honors (AK). Cash your winners.'),
        ('A52', 'K43', '2', 'Lead low toward the King. Don\'t waste your Ace.'),
        ('KJ4', 'xxx', '4', 'Lead low from this broken holding. Save honors for later.'),
        ('543', 'xxx', '5', 'From three small, lead the top (5). This shows no honors.'),
    ]

    def generate(self) -> Tuple[PlayDeal, Dict]:
        # Pick a situation
        your_holding_str, dummy_holding_str, correct_lead, explanation = random.choice(self.SITUATIONS)

        # Determine suit
        suit = random.choice(['♦', '♣'])

        # Convert holdings to cards (handling 'x' for small cards)
        deck = shuffle_deck()
        your_cards_in_suit, deck = holding_to_cards(your_holding_str, suit, deck)
        dummy_cards_in_suit, deck = holding_to_cards(dummy_holding_str, suit, deck)

        # Build hands (each must have exactly 13 cards)
        your_hand_cards = your_cards_in_suit + deck[:13-len(your_cards_in_suit)]
        your_hand = Hand(your_hand_cards)

        deck = deck[13-len(your_cards_in_suit):]
        dummy_hand_cards = dummy_cards_in_suit + deck[:13-len(dummy_cards_in_suit)]
        dummy_hand = Hand(dummy_hand_cards)

        deck = deck[13-len(dummy_cards_in_suit):]
        lho_hand = Hand(deck[:13])
        rho_hand = Hand(deck[13:26])

        deal = PlayDeal(
            declarer_hand=your_hand,
            dummy_hand=dummy_hand,
            lho_hand=lho_hand,
            rho_hand=rho_hand,
            contract='3NT',
            declarer_position='South',
            lead=None
        )

        suit_names = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}
        suit_name = suit_names[suit]

        situation = {
            'question': f'You are on lead. You have {your_holding_str} in {suit_name}, dummy has {dummy_holding_str}. Which card do you lead?',
            'question_type': 'leading_to_tricks',
            'expected_response': {
                'card': correct_lead,
                'suit': suit,
                'full_card': f'{correct_lead}{suit}'
            },
            'explanation': explanation,
            'accepts_multiple': False,
            'context': {
                'suit': suit,
                'your_holding': your_holding_str,
                'dummy_holding': dummy_holding_str
            }
        }

        return deal, situation


class SecondHandLowGenerator(PlaySkillHandGenerator):
    """Generate hands for practicing second hand play."""

    skill_id = 'second_hand_low'
    skill_level = 1
    description = 'Practice playing low in second seat'
    practice_format = 'single_decision'

    # Second hand situations
    SITUATIONS = [
        # (your_holding, opponent_leads, correct_card, explanation)
        ('K84', '3', '4', 'Play low (second hand low). Save your King to capture an honor later.'),
        ('Q52', '3', '2', 'Play low. Your Queen may capture their King or Jack later.'),
        ('A63', 'J', 'A', 'Cover an honor with an honor. Take the Jack with your Ace.'),
        ('K74', 'Q', 'K', 'Cover an honor with an honor. Force out a higher card.'),
        ('Q85', 'J', 'Q', 'Cover the Jack with your Queen. Try to promote lower honors.'),
        ('953', '2', '3', 'Play low from nothing. You have no honors to preserve.'),
        ('AJ4', '3', '4', 'Play low. Save your Ace-Jack for better opportunities.'),
        ('K95', 'Q', 'K', 'Cover the Queen with your King. Don\'t let it win cheaply.'),
        ('J62', '3', '2', 'Play low. Save your Jack - might win later.'),
        ('KQ3', '2', '3', 'Play low. Save your touching honors (KQ) to capture the Ace.'),
    ]

    def generate(self) -> Tuple[PlayDeal, Dict]:
        # Pick a situation
        your_holding_str, opponent_lead, correct_card, explanation = random.choice(self.SITUATIONS)

        suit = random.choice(['♦', '♣'])

        # Convert holdings to cards (handling 'x' and '10')
        deck = shuffle_deck()
        your_cards_in_suit, deck = holding_to_cards(your_holding_str, suit, deck)

        # Note: lead_card stays in the deck - it's in opponent's hand

        # Build hands (each must have exactly 13 cards)
        # Your hand: your_cards_in_suit + filler
        your_hand_cards = your_cards_in_suit + deck[:13-len(your_cards_in_suit)]
        your_hand = Hand(your_hand_cards)
        deck = deck[13-len(your_cards_in_suit):]

        # Dummy hand: 13 cards
        dummy_hand = Hand(deck[:13])
        deck = deck[13:]

        # LHO hand: 13 cards
        lho_hand = Hand(deck[:13])
        deck = deck[13:]

        # RHO hand: 13 cards
        rho_hand = Hand(deck[:13])

        deal = PlayDeal(
            declarer_hand=your_hand,
            dummy_hand=dummy_hand,
            lho_hand=lho_hand,
            rho_hand=rho_hand,
            contract='3NT',
            declarer_position='South',
            lead=None
        )

        suit_names = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}
        suit_name = suit_names[suit]

        situation = {
            'question': f'Opponent leads the {opponent_lead} of {suit_name}. You have {your_holding_str}. Which card do you play?',
            'question_type': 'second_hand_play',
            'expected_response': {
                'card': correct_card,
                'suit': suit,
                'full_card': f'{correct_card}{suit}'
            },
            'explanation': explanation,
            'accepts_multiple': False,
            'context': {
                'suit': suit,
                'opponent_lead': opponent_lead,
                'your_holding': your_holding_str
            }
        }

        return deal, situation


class WinningCheaplyGenerator(PlaySkillHandGenerator):
    """Generate hands for practicing winning tricks economically."""

    skill_id = 'winning_cheaply'
    skill_level = 1
    description = 'Practice winning with the cheapest card'
    practice_format = 'single_decision'

    # Winning cheaply situations
    SITUATIONS = [
        # (your_holding, dummy_plays, correct_card, explanation)
        ('AK3', 'Q', 'K', 'Win with the King, not the Ace. Save your Ace for later.'),
        ('KQJ', '2', 'J', 'Win with the Jack - cheapest card from your sequence.'),
        ('AQ5', 'J', 'Q', 'Win with the Queen. Save your Ace - it\'s more valuable.'),
        ('KJ4', 'Q', 'K', 'Must use the King to beat the Queen. No cheaper option.'),
        ('A94', 'K', 'A', 'Must use the Ace to beat the King.'),
        ('QJ10', '3', '10', 'Win with the 10 - cheapest card that wins from QJ10.'),
        ('AK2', 'J', 'K', 'Win with the King. Keep your Ace as a sure winner.'),
        ('KQ3', '4', 'Q', 'Win with the Queen (cheaper than King).'),
        ('A85', 'K', 'A', 'Must play Ace - only card that beats the King.'),
        ('J109', '2', '9', 'Win with the 9 - cheapest from equals (J109).'),
    ]

    def generate(self) -> Tuple[PlayDeal, Dict]:
        # Pick a situation
        your_holding_str, dummy_card, correct_card, explanation = random.choice(self.SITUATIONS)

        suit = random.choice(['♦', '♣'])

        # Convert holdings (handling 'x' and '10')
        deck = shuffle_deck()
        your_cards_in_suit, deck = holding_to_cards(your_holding_str, suit, deck)

        # Add dummy card
        dummy_card_obj = Card(dummy_card, suit)
        if dummy_card_obj in deck:
            deck = [c for c in deck if c != dummy_card_obj]

        # Build hands (each must have exactly 13 cards)
        your_hand_cards = your_cards_in_suit + deck[:13-len(your_cards_in_suit)]
        your_hand = Hand(your_hand_cards)

        deck = deck[13-len(your_cards_in_suit):]
        dummy_hand_cards = [dummy_card_obj] + deck[:12]
        dummy_hand = Hand(dummy_hand_cards)

        deck = deck[12:]
        lho_hand = Hand(deck[:13])
        rho_hand = Hand(deck[13:26])

        deal = PlayDeal(
            declarer_hand=your_hand,
            dummy_hand=dummy_hand,
            lho_hand=lho_hand,
            rho_hand=rho_hand,
            contract='3NT',
            declarer_position='South',
            lead=None
        )

        suit_names = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}
        suit_name = suit_names[suit]

        situation = {
            'question': f'Dummy plays the {dummy_card} of {suit_name}. You have {your_holding_str}. Which card do you play to win the trick economically?',
            'question_type': 'winning_cheaply',
            'expected_response': {
                'card': correct_card,
                'suit': suit,
                'full_card': f'{correct_card}{suit}'
            },
            'explanation': explanation,
            'accepts_multiple': False,
            'context': {
                'suit': suit,
                'dummy_played': dummy_card,
                'your_holding': your_holding_str
            }
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


class DoubleFinesseGenerator(PlaySkillHandGenerator):
    """Generate hands for practicing double finesses."""

    skill_id = 'double_finesse'
    skill_level = 2
    description = 'Practice double finesses (missing two honors)'
    practice_format = 'single_decision'

    # Double finesse situations
    SITUATIONS = [
        # (your_holding, dummy_holding, correct_answer, explanation)
        ('AQJ', 'xxx', '2', 'With AQJ opposite small, finesse twice. You can take 2 tricks if both K and 10 are onside.'),
        ('AJ10', 'xxx', '2', 'With AJ10, finesse the 10 first, then the J. Two finesses needed.'),
        ('KJ9', 'xxx', '2', 'With KJ9, finesse twice against AQ. Can take 2 tricks if both onside.'),
        ('AQ10', 'xxx', '2', 'With AQ10, finesse the 10 first, then Q. You can establish 3 tricks.'),
        ('KQ10', 'Axx', '2', 'With Axx opposite KQ10, cash A then finesse twice. Two finesse positions.'),
    ]

    def generate(self) -> Tuple[PlayDeal, Dict]:
        # Pick a situation
        your_holding_str, dummy_holding_str, correct_answer, explanation = random.choice(self.SITUATIONS)

        suit = random.choice(['♦', '♣'])

        # Convert holdings to cards
        deck = shuffle_deck()
        your_cards_in_suit, deck = holding_to_cards(your_holding_str, suit, deck)
        dummy_cards_in_suit, deck = holding_to_cards(dummy_holding_str, suit, deck)

        # Build hands
        your_hand_cards = your_cards_in_suit + deck[:13-len(your_cards_in_suit)]
        your_hand = Hand(your_hand_cards)

        deck = deck[13-len(your_cards_in_suit):]
        dummy_hand_cards = dummy_cards_in_suit + deck[:13-len(dummy_cards_in_suit)]
        dummy_hand = Hand(dummy_hand_cards)

        deck = deck[13-len(dummy_cards_in_suit):]
        lho_hand = Hand(deck[:13])
        rho_hand = Hand(deck[13:26])

        deal = PlayDeal(
            declarer_hand=your_hand,
            dummy_hand=dummy_hand,
            lho_hand=lho_hand,
            rho_hand=rho_hand,
            contract='3NT',
            declarer_position='South',
            lead=None
        )

        suit_names = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}
        suit_name = suit_names[suit]

        situation = {
            'question': f'You have {your_holding_str} in {suit_name}, dummy has {dummy_holding_str}. How many tricks can you win with two successful finesses?',
            'question_type': 'count_tricks',
            'expected_response': {
                'tricks': int(correct_answer),
                'correct_answer': int(correct_answer)
            },
            'explanation': explanation,
            'accepts_multiple': False
        }

        return deal, situation


class TwoWayFinesseGenerator(PlaySkillHandGenerator):
    """Generate hands for two-way finesse decisions."""

    skill_id = 'two_way_finesse'
    skill_level = 2
    description = 'Practice two-way finesses (can finesse either way)'
    practice_format = 'single_decision'

    # Two-way finesse situations
    SITUATIONS = [
        # (your_holding, dummy_holding, question, answers, explanation)
        ('AJx', 'Kxx', ['finesse_left', 'finesse_right'], 'Either direction works. With AJx opposite Kxx, you can finesse for the Queen in either direction.'),
        ('KJ9', 'A10x', ['finesse_left', 'finesse_right'], 'You can finesse for the Queen either way. Lead toward AJx or toward K109.'),
        ('AJ10', 'Kxx', ['finesse_left', 'finesse_right'], 'Two-way finesse for the Queen. Can go either direction.'),
        ('Q10x', 'AJx', ['finesse_left', 'finesse_right'], 'Can finesse for the King either way with this holding.'),
    ]

    def generate(self) -> Tuple[PlayDeal, Dict]:
        # Pick a situation
        your_holding_str, dummy_holding_str, valid_answers, explanation = random.choice(self.SITUATIONS)

        suit = random.choice(['♦', '♣'])

        # Convert holdings to cards
        deck = shuffle_deck()
        your_cards_in_suit, deck = holding_to_cards(your_holding_str, suit, deck)
        dummy_cards_in_suit, deck = holding_to_cards(dummy_holding_str, suit, deck)

        # Build hands
        your_hand_cards = your_cards_in_suit + deck[:13-len(your_cards_in_suit)]
        your_hand = Hand(your_hand_cards)

        deck = deck[13-len(your_cards_in_suit):]
        dummy_hand_cards = dummy_cards_in_suit + deck[:13-len(dummy_cards_in_suit)]
        dummy_hand = Hand(dummy_hand_cards)

        deck = deck[13-len(dummy_cards_in_suit):]
        lho_hand = Hand(deck[:13])
        rho_hand = Hand(deck[13:26])

        deal = PlayDeal(
            declarer_hand=your_hand,
            dummy_hand=dummy_hand,
            lho_hand=lho_hand,
            rho_hand=rho_hand,
            contract='3NT',
            declarer_position='South',
            lead=None
        )

        suit_names = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}
        suit_name = suit_names[suit]

        situation = {
            'question': f'You have {your_holding_str} in {suit_name}, dummy has {dummy_holding_str}. Which direction should you finesse?',
            'question_type': 'finesse_direction',
            'expected_response': {
                'direction': valid_answers[0],  # Accept any answer
                'valid_answers': valid_answers,
                'correct_answer': valid_answers[0]
            },
            'explanation': explanation,
            'accepts_multiple': True  # Both directions are valid
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


class DuckingPlaysGenerator(PlaySkillHandGenerator):
    """Generate hands for practicing ducking plays."""

    skill_id = 'ducking_plays'
    skill_level = 3
    description = 'Practice ducking to preserve entries'
    practice_format = 'single_decision'

    SITUATIONS = [
        # (correct_answer, explanation)
        ('1', 'Duck once. With Axx opposite 5+ cards, duck once to keep entry control.'),
        ('2', 'Duck twice. With Axx opposite 6+ cards, duck twice to preserve the Ace as entry.'),
        ('1', 'Duck once to establish the suit while keeping communication.'),
        ('0', 'Don\'t duck - cash the Ace immediately. Entry timing matters.'),
    ]

    def generate(self) -> Tuple[PlayDeal, Dict]:
        correct_answer, explanation = random.choice(self.SITUATIONS)

        suit = random.choice(['♦', '♣'])

        # Create a ducking scenario: Axx in hand, long suit in dummy
        your_holding = 'A32'
        dummy_holding = '98765'

        deck = shuffle_deck()
        your_cards_in_suit, deck = holding_to_cards(your_holding, suit, deck)
        dummy_cards_in_suit, deck = holding_to_cards(dummy_holding, suit, deck)

        your_hand_cards = your_cards_in_suit + deck[:13-len(your_cards_in_suit)]
        your_hand = Hand(your_hand_cards)

        deck = deck[13-len(your_cards_in_suit):]
        dummy_hand_cards = dummy_cards_in_suit + deck[:13-len(dummy_cards_in_suit)]
        dummy_hand = Hand(dummy_hand_cards)

        deck = deck[13-len(dummy_cards_in_suit):]
        lho_hand = Hand(deck[:13])
        rho_hand = Hand(deck[13:26])

        deal = PlayDeal(
            declarer_hand=your_hand,
            dummy_hand=dummy_hand,
            lho_hand=lho_hand,
            rho_hand=rho_hand,
            contract='3NT',
            declarer_position='South',
            lead=None
        )

        suit_names = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}
        suit_name = suit_names[suit]

        situation = {
            'question': f'Dummy has {dummy_holding} of {suit_name}, you have {your_holding}. How many times should you duck to establish the suit?',
            'question_type': 'duck_count',
            'expected_response': {
                'ducks': int(correct_answer),
                'correct_answer': int(correct_answer)
            },
            'explanation': explanation,
            'accepts_multiple': False
        }

        return deal, situation


class WhichSuitToEstablishGenerator(PlaySkillHandGenerator):
    """Generate hands for choosing which suit to establish."""

    skill_id = 'which_suit_to_establish'
    skill_level = 3
    description = 'Practice choosing the best suit to establish'
    practice_format = 'single_decision'

    def generate(self) -> Tuple[PlayDeal, Dict]:
        # Generate a hand with two potential suits to establish
        suit_a = '♦'
        suit_b = '♣'

        # One suit is better (longer, better entries, etc.)
        better_suit = random.choice([suit_a, suit_b])

        deck = shuffle_deck()

        # Build specific holdings
        if better_suit == suit_a:
            holding_a = 'KQJ98'  # 5-card suit, good honors
            holding_b = 'Q1065'   # 4-card suit, weaker
            explanation = f'Establish diamonds - longer suit (5 cards vs 4) with better honors.'
        else:
            holding_a = 'Q1065'
            holding_b = 'KQJ98'
            explanation = f'Establish clubs - longer suit (5 cards vs 4) with better honors.'

        cards_a, deck = holding_to_cards(holding_a, suit_a, deck)
        cards_b, deck = holding_to_cards(holding_b, suit_b, deck)

        your_hand_cards = cards_a + cards_b + deck[:13-len(cards_a)-len(cards_b)]
        your_hand = Hand(your_hand_cards[:13])

        deck = deck[13-len(cards_a)-len(cards_b):]
        dummy_hand = Hand(deck[:13])
        deck = deck[13:]
        lho_hand = Hand(deck[:13])
        rho_hand = Hand(deck[13:26])

        deal = PlayDeal(
            declarer_hand=your_hand,
            dummy_hand=dummy_hand,
            lho_hand=lho_hand,
            rho_hand=rho_hand,
            contract='3NT',
            declarer_position='South',
            lead=None
        )

        suit_names = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}

        situation = {
            'question': f'Which suit should you establish: diamonds or clubs?',
            'question_type': 'suit_choice',
            'expected_response': {
                'suit': better_suit,
                'suit_name': suit_names[better_suit],
                'correct_answer': suit_names[better_suit]
            },
            'explanation': explanation,
            'accepts_multiple': False
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


class TrumpControlGenerator(PlaySkillHandGenerator):
    """Generate hands for trump control decisions."""

    skill_id = 'trump_control'
    skill_level = 4
    description = 'Practice maintaining trump control'
    practice_format = 'single_decision'

    SITUATIONS = [
        ('2', 'Draw all enemy trumps (2 rounds). You have trump control - use it.'),
        ('1', 'Draw one round only. Preserve trumps for ruffing losers.'),
        ('3', 'Draw all three rounds. With 8+ combined trumps, draw them all.'),
        ('0', 'Don\'t draw trumps yet. Ruff losers first, then draw trumps.'),
    ]

    def generate(self) -> Tuple[PlayDeal, Dict]:
        correct_answer, explanation = random.choice(self.SITUATIONS)

        trump_suit = random.choice(['♠', '♥'])

        # Create trump holdings
        your_trump = 'AKQ'
        dummy_trump = '876'

        deck = shuffle_deck()
        your_trumps, deck = holding_to_cards(your_trump, trump_suit, deck)
        dummy_trumps, deck = holding_to_cards(dummy_trump, trump_suit, deck)

        your_hand_cards = your_trumps + deck[:13-len(your_trumps)]
        your_hand = Hand(your_hand_cards)

        deck = deck[13-len(your_trumps):]
        dummy_hand_cards = dummy_trumps + deck[:13-len(dummy_trumps)]
        dummy_hand = Hand(dummy_hand_cards)

        deck = deck[13-len(dummy_trumps):]
        lho_hand = Hand(deck[:13])
        rho_hand = Hand(deck[13:26])

        deal = PlayDeal(
            declarer_hand=your_hand,
            dummy_hand=dummy_hand,
            lho_hand=lho_hand,
            rho_hand=rho_hand,
            contract=f'4{trump_suit}',
            declarer_position='South',
            lead=None
        )

        suit_names = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}
        trump_name = suit_names[trump_suit]

        situation = {
            'question': f'Playing 4{trump_suit}, how many rounds of trumps should you draw immediately?',
            'question_type': 'trump_rounds',
            'expected_response': {
                'rounds': int(correct_answer),
                'correct_answer': int(correct_answer)
            },
            'explanation': explanation,
            'accepts_multiple': False
        }

        return deal, situation


class CrossruffGenerator(PlaySkillHandGenerator):
    """Generate hands for crossruff play."""

    skill_id = 'crossruff'
    skill_level = 4
    description = 'Practice crossruff technique'
    practice_format = 'single_decision'

    def generate(self) -> Tuple[PlayDeal, Dict]:
        trump_suit = random.choice(['♠', '♥'])
        side_suit_a = '♦' if trump_suit == '♠' else '♣'
        side_suit_b = '♣' if side_suit_a == '♦' else '♦'

        # Crossruff scenario: short in both hands in different suits
        your_trump = 'AK98'
        dummy_trump = 'QJ76'

        deck = shuffle_deck()
        your_trumps, deck = holding_to_cards(your_trump, trump_suit, deck)
        dummy_trumps, deck = holding_to_cards(dummy_trump, trump_suit, deck)

        # Short suits for crossruff
        your_short_in_a, deck = holding_to_cards('32', side_suit_a, deck)
        dummy_short_in_b, deck = holding_to_cards('43', side_suit_b, deck)

        your_hand_cards = your_trumps + your_short_in_a + deck[:13-len(your_trumps)-len(your_short_in_a)]
        your_hand = Hand(your_hand_cards[:13])

        deck = deck[13-len(your_trumps)-len(your_short_in_a):]
        dummy_hand_cards = dummy_trumps + dummy_short_in_b + deck[:13-len(dummy_trumps)-len(dummy_short_in_b)]
        dummy_hand = Hand(dummy_hand_cards[:13])

        deck = deck[13-len(dummy_trumps)-len(dummy_short_in_b):]
        lho_hand = Hand(deck[:13])
        rho_hand = Hand(deck[13:26])

        deal = PlayDeal(
            declarer_hand=your_hand,
            dummy_hand=dummy_hand,
            lho_hand=lho_hand,
            rho_hand=rho_hand,
            contract=f'4{trump_suit}',
            declarer_position='South',
            lead=None
        )

        situation = {
            'question': f'You have shortness in different suits. How many trump tricks can you make by crossruffing?',
            'question_type': 'crossruff_tricks',
            'expected_response': {
                'tricks': 8,  # 4 rounds of crossruffing
                'correct_answer': 8
            },
            'explanation': 'With 4 trumps in each hand and shortness in different suits, you can make 8 trump tricks by crossruffing - ruffing back and forth.',
            'accepts_multiple': False
        }

        return deal, situation


# ============================================================================
# LEVEL 5: ENTRY MANAGEMENT
# ============================================================================

class PreservingEntriesGenerator(PlaySkillHandGenerator):
    """Generate hands for preserving entry practice."""

    skill_id = 'preserving_entries'
    skill_level = 5
    description = 'Practice preserving entries to dummy'
    practice_format = 'single_decision'

    SITUATIONS = [
        ('A', 'Win with the Ace now to preserve the King as an entry for later.'),
        ('K', 'Win with the King first. Save the Ace as a sure entry.'),
        ('Q', 'Win with the Queen. Preserve higher cards as entries.'),
    ]

    def generate(self) -> Tuple[PlayDeal, Dict]:
        correct_card, explanation = random.choice(self.SITUATIONS)

        suit = random.choice(['♦', '♣'])
        your_holding = 'AKQ'
        dummy_holding = 'xxx'

        deck = shuffle_deck()
        your_cards, deck = holding_to_cards(your_holding, suit, deck)
        dummy_cards, deck = holding_to_cards(dummy_holding, suit, deck)

        your_hand = Hand(your_cards + deck[:13-len(your_cards)])
        deck = deck[13-len(your_cards):]
        dummy_hand = Hand(dummy_cards + deck[:13-len(dummy_cards)])
        deck = deck[13-len(dummy_cards):]
        lho_hand = Hand(deck[:13])
        rho_hand = Hand(deck[13:26])

        deal = PlayDeal(your_hand, dummy_hand, lho_hand, rho_hand, '3NT', 'South')

        situation = {
            'question': f'Dummy has a long suit but only {your_holding} as entries. Which card do you use first?',
            'question_type': 'entry_card',
            'expected_response': {'card': correct_card},
            'explanation': explanation,
            'accepts_multiple': False
        }
        return deal, situation


class UnblockingGenerator(PlaySkillHandGenerator):
    """Generate hands for unblocking practice."""

    skill_id = 'unblocking'
    skill_level = 5
    description = 'Practice unblocking to maintain communication'
    practice_format = 'single_decision'

    def generate(self) -> Tuple[PlayDeal, Dict]:
        suit = random.choice(['♦', '♣'])

        # Classic unblocking scenario: Qx opposite AKJxx
        your_holding = 'Q3'
        dummy_holding = 'AKJ98'

        deck = shuffle_deck()
        your_cards, deck = holding_to_cards(your_holding, suit, deck)
        dummy_cards, deck = holding_to_cards(dummy_holding, suit, deck)

        your_hand = Hand(your_cards + deck[:13-len(your_cards)])
        deck = deck[13-len(your_cards):]
        dummy_hand = Hand(dummy_cards + deck[:13-len(dummy_cards)])
        deck = deck[13-len(dummy_cards):]
        lho_hand = Hand(deck[:13])
        rho_hand = Hand(deck[13:26])

        deal = PlayDeal(your_hand, dummy_hand, lho_hand, rho_hand, '3NT', 'South')

        suit_names = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}

        situation = {
            'question': f'Dummy has AKJ98 of {suit_names[suit]}, you have Q3. Which card do you play under dummy\'s Ace?',
            'question_type': 'unblock_card',
            'expected_response': {'card': 'Q'},
            'explanation': 'Unblock the Queen! This lets you run dummy\'s long suit without blocking it.',
            'accepts_multiple': False
        }
        return deal, situation


class CreatingEntriesGenerator(PlaySkillHandGenerator):
    """Generate hands for creating entries practice."""

    skill_id = 'creating_entries'
    skill_level = 5
    description = 'Practice creating entries'
    practice_format = 'single_decision'

    def generate(self) -> Tuple[PlayDeal, Dict]:
        suit = random.choice(['♦', '♣'])

        # Create entry by ducking or finessing
        your_holding = 'AQ5'
        dummy_holding = '432'

        deck = shuffle_deck()
        your_cards, deck = holding_to_cards(your_holding, suit, deck)
        dummy_cards, deck = holding_to_cards(dummy_holding, suit, deck)

        your_hand = Hand(your_cards + deck[:13-len(your_cards)])
        deck = deck[13-len(your_cards):]
        dummy_hand = Hand(dummy_cards + deck[:13-len(dummy_cards)])
        deck = deck[13-len(dummy_cards):]
        lho_hand = Hand(deck[:13])
        rho_hand = Hand(deck[13:26])

        deal = PlayDeal(your_hand, dummy_hand, lho_hand, rho_hand, '3NT', 'South')

        situation = {
            'question': 'How many entries can you create to dummy by ducking or finessing?',
            'question_type': 'count_entries',
            'expected_response': {'correct_answer': 1},
            'explanation': 'Duck once to create an entry. The small cards become an entry after opponents take their honors.',
            'accepts_multiple': False
        }
        return deal, situation


class EntryKillingPlaysGenerator(PlaySkillHandGenerator):
    """Generate hands for entry-killing defense."""

    skill_id = 'entry_killing_plays'
    skill_level = 5
    description = 'Practice removing opponent entries (defense)'
    practice_format = 'single_decision'

    def generate(self) -> Tuple[PlayDeal, Dict]:
        suit = random.choice(['♦', '♣'])

        # Defensive: kill dummy's entry
        your_holding = 'AK3'
        dummy_holding = 'Q42'

        deck = shuffle_deck()
        your_cards, deck = holding_to_cards(your_holding, suit, deck)
        dummy_cards, deck = holding_to_cards(dummy_holding, suit, deck)

        your_hand = Hand(your_cards + deck[:13-len(your_cards)])
        deck = deck[13-len(your_cards):]
        dummy_hand = Hand(dummy_cards + deck[:13-len(dummy_cards)])
        deck = deck[13-len(dummy_cards):]
        lho_hand = Hand(deck[:13])
        rho_hand = Hand(deck[13:26])

        deal = PlayDeal(your_hand, dummy_hand, lho_hand, rho_hand, '3NT', 'South')

        situation = {
            'question': 'Dummy has a long suit with only the Q as entry. Should you hold up your A or cash it?',
            'question_type': 'entry_defense',
            'expected_response': {'correct_answer': 'cash'},
            'explanation': 'Cash your Ace to kill dummy\'s Queen entry. This strands dummy\'s long suit.',
            'accepts_multiple': False
        }
        return deal, situation


# ============================================================================
# LEVEL 6: CARD COMBINATIONS
# ============================================================================

class AQCombinationsGenerator(PlaySkillHandGenerator):
    """Generate hands for AQ combination practice."""

    skill_id = 'aq_combinations'
    skill_level = 6
    description = 'Practice playing AQ combinations'
    practice_format = 'single_decision'

    SITUATIONS = [
        ('AQ5', 'xxx', '2', 'With AQ opposite small, finesse twice. Take 2 tricks if King onside.'),
        ('AQJ', 'xxx', '3', 'With AQJ, you can take 3 tricks if K onside. Finesse the J first.'),
        ('A32', 'Qxx', '2', 'With A opposite Q, take 2 tricks. Cash A then lead to Q.'),
    ]

    def generate(self) -> Tuple[PlayDeal, Dict]:
        your_holding, dummy_holding, tricks, explanation = random.choice(self.SITUATIONS)

        suit = random.choice(['♦', '♣'])
        deck = shuffle_deck()
        your_cards, deck = holding_to_cards(your_holding, suit, deck)
        dummy_cards, deck = holding_to_cards(dummy_holding, suit, deck)

        your_hand = Hand(your_cards + deck[:13-len(your_cards)])
        deck = deck[13-len(your_cards):]
        dummy_hand = Hand(dummy_cards + deck[:13-len(dummy_cards)])
        deck = deck[13-len(dummy_cards):]
        lho_hand = Hand(deck[:13])
        rho_hand = Hand(deck[13:26])

        deal = PlayDeal(your_hand, dummy_hand, lho_hand, rho_hand, '3NT', 'South')

        situation = {
            'question': f'You have {your_holding}, dummy has {dummy_holding}. How many tricks can you make if the King is favorably placed?',
            'question_type': 'combination_tricks',
            'expected_response': {'correct_answer': int(tricks)},
            'explanation': explanation,
            'accepts_multiple': False
        }
        return deal, situation


class KJCombinationsGenerator(PlaySkillHandGenerator):
    """Generate hands for KJ combination practice."""

    skill_id = 'kj_combinations'
    skill_level = 6
    description = 'Practice playing KJ combinations'
    practice_format = 'single_decision'

    SITUATIONS = [
        ('KJ5', 'xxx', '2', 'With KJ opposite small, finesse for the Queen. Take 2 tricks if Q onside.'),
        ('KJ10', 'xxx', '3', 'With KJ10, finesse twice. Can take 3 tricks if both A and Q are onside.'),
        ('Kxx', 'J32', '1', 'With K opposite J, lead toward the King. Take 1 trick, maybe 2.'),
    ]

    def generate(self) -> Tuple[PlayDeal, Dict]:
        your_holding, dummy_holding, tricks, explanation = random.choice(self.SITUATIONS)

        suit = random.choice(['♦', '♣'])
        deck = shuffle_deck()
        your_cards, deck = holding_to_cards(your_holding, suit, deck)
        dummy_cards, deck = holding_to_cards(dummy_holding, suit, deck)

        your_hand = Hand(your_cards + deck[:13-len(your_cards)])
        deck = deck[13-len(your_cards):]
        dummy_hand = Hand(dummy_cards + deck[:13-len(dummy_cards)])
        deck = deck[13-len(dummy_cards):]
        lho_hand = Hand(deck[:13])
        rho_hand = Hand(deck[13:26])

        deal = PlayDeal(your_hand, dummy_hand, lho_hand, rho_hand, '3NT', 'South')

        situation = {
            'question': f'You have {your_holding}, dummy has {dummy_holding}. How many tricks can you make with best play?',
            'question_type': 'combination_tricks',
            'expected_response': {'correct_answer': int(tricks)},
            'explanation': explanation,
            'accepts_multiple': False
        }
        return deal, situation


class SafetyPlaysGenerator(PlaySkillHandGenerator):
    """Generate hands for safety play practice."""

    skill_id = 'safety_plays'
    skill_level = 6
    description = 'Practice safety plays'
    practice_format = 'single_decision'

    def generate(self) -> Tuple[PlayDeal, Dict]:
        suit = random.choice(['♦', '♣'])

        # Classic safety play: AKxxx opposite xxx
        your_holding = 'AKxxx'
        dummy_holding = 'xxx'

        deck = shuffle_deck()
        your_cards, deck = holding_to_cards(your_holding, suit, deck)
        dummy_cards, deck = holding_to_cards(dummy_holding, suit, deck)

        your_hand = Hand(your_cards + deck[:13-len(your_cards)])
        deck = deck[13-len(your_cards):]
        dummy_hand = Hand(dummy_cards + deck[:13-len(dummy_cards)])
        deck = deck[13-len(dummy_cards):]
        lho_hand = Hand(deck[:13])
        rho_hand = Hand(deck[13:26])

        deal = PlayDeal(your_hand, dummy_hand, lho_hand, rho_hand, '3NT', 'South')

        situation = {
            'question': 'You need 4 tricks from this suit. Cash A first or lead low to the A?',
            'question_type': 'safety_choice',
            'expected_response': {'correct_answer': 'low'},
            'explanation': 'Safety play: lead low to the A first. This guards against Qxxx in one hand.',
            'accepts_multiple': False
        }
        return deal, situation


class PercentagePlaysGenerator(PlaySkillHandGenerator):
    """Generate hands for percentage play practice."""

    skill_id = 'percentage_plays'
    skill_level = 6
    description = 'Practice choosing best percentage plays'
    practice_format = 'single_decision'

    SITUATIONS = [
        ('finesse', 'With 9 cards missing the Queen, finesse (52%) is slightly better than drop (48%).'),
        ('drop', 'With 9+ cards, play for the drop. More cards = higher chance of drop.'),
        ('finesse', 'With 8 cards or fewer, finesse is usually better percentage.'),
    ]

    def generate(self) -> Tuple[PlayDeal, Dict]:
        correct_play, explanation = random.choice(self.SITUATIONS)

        suit = random.choice(['♦', '♣'])
        your_holding = 'AKJ98'
        dummy_holding = '7653'

        deck = shuffle_deck()
        your_cards, deck = holding_to_cards(your_holding, suit, deck)
        dummy_cards, deck = holding_to_cards(dummy_holding, suit, deck)

        your_hand = Hand(your_cards + deck[:13-len(your_cards)])
        deck = deck[13-len(your_cards):]
        dummy_hand = Hand(dummy_cards + deck[:13-len(dummy_cards)])
        deck = deck[13-len(dummy_cards):]
        lho_hand = Hand(deck[:13])
        rho_hand = Hand(deck[13:26])

        deal = PlayDeal(your_hand, dummy_hand, lho_hand, rho_hand, '3NT', 'South')

        situation = {
            'question': 'You have 9 cards missing the Queen. Finesse or play for the drop?',
            'question_type': 'percentage_choice',
            'expected_response': {'correct_answer': correct_play},
            'explanation': explanation,
            'accepts_multiple': False
        }
        return deal, situation


# ============================================================================
# LEVEL 7: TIMING & PLANNING
# ============================================================================

class PlanningNTContractsGenerator(PlaySkillHandGenerator):
    """Generate hands for NT planning practice."""

    skill_id = 'planning_nt_contracts'
    skill_level = 7
    description = 'Practice planning NT contracts'
    practice_format = 'single_decision'

    def generate(self) -> Tuple[PlayDeal, Dict]:
        deck = shuffle_deck()

        # Random NT hand with clear plan
        your_hand = Hand(deck[:13])
        dummy_hand = Hand(deck[13:26])
        lho_hand = Hand(deck[26:39])
        rho_hand = Hand(deck[39:52])

        deal = PlayDeal(your_hand, dummy_hand, lho_hand, rho_hand, '3NT', 'South')

        # Count approximate winners
        combined_hcp = your_hand.hcp + dummy_hand.hcp
        estimated_winners = min(9, combined_hcp // 4)  # Rough estimate

        situation = {
            'question': f'In 3NT, you need 9 tricks. With {combined_hcp} combined HCP, roughly how many sure tricks do you have?',
            'question_type': 'count_winners',
            'expected_response': {'correct_answer': estimated_winners, 'acceptable_range': [max(0, estimated_winners-2), min(13, estimated_winners+2)]},
            'explanation': f'Count your sure winners first, then plan which suit to establish for additional tricks.',
            'accepts_multiple': False
        }
        return deal, situation


class PlanningSuitContractsGenerator(PlaySkillHandGenerator):
    """Generate hands for suit contract planning."""

    skill_id = 'planning_suit_contracts'
    skill_level = 7
    description = 'Practice planning suit contracts'
    practice_format = 'single_decision'

    def generate(self) -> Tuple[PlayDeal, Dict]:
        trump_suit = random.choice(['♠', '♥'])
        deck = shuffle_deck()

        your_hand = Hand(deck[:13])
        dummy_hand = Hand(deck[13:26])
        lho_hand = Hand(deck[26:39])
        rho_hand = Hand(deck[39:52])

        deal = PlayDeal(your_hand, dummy_hand, lho_hand, rho_hand, f'4{trump_suit}', 'South')

        situation = {
            'question': f'In 4{trump_suit}, what should you plan first: count winners, count losers, or count trumps?',
            'question_type': 'planning_choice',
            'expected_response': {'correct_answer': 'losers'},
            'explanation': 'In suit contracts, count LOSERS first. Then plan how to eliminate them (ruff, discard, or avoid).',
            'accepts_multiple': False
        }
        return deal, situation


class TimingDecisionsGenerator(PlaySkillHandGenerator):
    """Generate hands for timing decision practice."""

    skill_id = 'timing_decisions'
    skill_level = 7
    description = 'Practice timing decisions'
    practice_format = 'single_decision'

    SITUATIONS = [
        ('draw_trumps', 'Draw trumps first. You have plenty - use them.'),
        ('establish_suit', 'Establish your long suit before drawing trumps.'),
        ('ruff_losers', 'Ruff losers in dummy first, then draw trumps.'),
    ]

    def generate(self) -> Tuple[PlayDeal, Dict]:
        correct_play, explanation = random.choice(self.SITUATIONS)

        trump_suit = random.choice(['♠', '♥'])
        deck = shuffle_deck()

        your_hand = Hand(deck[:13])
        dummy_hand = Hand(deck[13:26])
        lho_hand = Hand(deck[26:39])
        rho_hand = Hand(deck[39:52])

        deal = PlayDeal(your_hand, dummy_hand, lho_hand, rho_hand, f'4{trump_suit}', 'South')

        situation = {
            'question': 'What is your first priority: draw trumps, establish a suit, or ruff losers?',
            'question_type': 'timing_choice',
            'expected_response': {'correct_answer': correct_play},
            'explanation': explanation,
            'accepts_multiple': False
        }
        return deal, situation


class DangerHandGenerator(PlaySkillHandGenerator):
    """Generate hands for danger hand recognition."""

    skill_id = 'danger_hand'
    skill_level = 7
    description = 'Practice identifying the danger hand'
    practice_format = 'single_decision'

    def generate(self) -> Tuple[PlayDeal, Dict]:
        deck = shuffle_deck()

        your_hand = Hand(deck[:13])
        dummy_hand = Hand(deck[13:26])
        lho_hand = Hand(deck[26:39])
        rho_hand = Hand(deck[39:52])

        deal = PlayDeal(your_hand, dummy_hand, lho_hand, rho_hand, '3NT', 'South')

        # Randomly designate one opponent as dangerous
        danger_opp = random.choice(['LHO', 'RHO'])

        situation = {
            'question': f'{danger_opp} has a long suit. Which opponent must you keep off lead?',
            'question_type': 'danger_choice',
            'expected_response': {'correct_answer': danger_opp},
            'explanation': f'The {danger_opp} is the danger hand. Avoid finesses that lose to {danger_opp}.',
            'accepts_multiple': False
        }
        return deal, situation


# ============================================================================
# LEVEL 8: ADVANCED TECHNIQUES
# ============================================================================

class EliminationPlayGenerator(PlaySkillHandGenerator):
    """Generate hands for elimination play practice."""

    skill_id = 'elimination_play'
    skill_level = 8
    description = 'Practice elimination plays'
    practice_format = 'single_decision'

    def generate(self) -> Tuple[PlayDeal, Dict]:
        trump_suit = random.choice(['♠', '♥'])
        deck = shuffle_deck()

        your_hand = Hand(deck[:13])
        dummy_hand = Hand(deck[13:26])
        lho_hand = Hand(deck[26:39])
        rho_hand = Hand(deck[39:52])

        deal = PlayDeal(your_hand, dummy_hand, lho_hand, rho_hand, f'4{trump_suit}', 'South')

        situation = {
            'question': 'For an elimination play, how many side suits should you eliminate before exiting?',
            'question_type': 'elimination_count',
            'expected_response': {'correct_answer': 2},
            'explanation': 'Eliminate 2+ side suits, then exit. Force opponents to lead into your tenace or give you a ruff-sluff.',
            'accepts_multiple': False
        }
        return deal, situation


class EndplaysGenerator(PlaySkillHandGenerator):
    """Generate hands for endplay practice."""

    skill_id = 'endplays'
    skill_level = 8
    description = 'Practice endplays and throw-ins'
    practice_format = 'single_decision'

    def generate(self) -> Tuple[PlayDeal, Dict]:
        trump_suit = random.choice(['♠', '♥'])
        deck = shuffle_deck()

        your_hand = Hand(deck[:13])
        dummy_hand = Hand(deck[13:26])
        lho_hand = Hand(deck[26:39])
        rho_hand = Hand(deck[39:52])

        deal = PlayDeal(your_hand, dummy_hand, lho_hand, rho_hand, f'4{trump_suit}', 'South')

        situation = {
            'question': 'To execute an endplay, should you exit early or late in the hand?',
            'question_type': 'endplay_choice',
            'expected_response': {'correct_answer': 'late'},
            'explanation': 'Exit LATE (near the end) after eliminating side suits. This forces opponent into a losing position.',
            'accepts_multiple': False
        }
        return deal, situation


class SimpleSqueezeGenerator(PlaySkillHandGenerator):
    """Generate hands for simple squeeze practice."""

    skill_id = 'simple_squeeze'
    skill_level = 8
    description = 'Practice simple squeeze technique'
    practice_format = 'single_decision'

    def generate(self) -> Tuple[PlayDeal, Dict]:
        deck = shuffle_deck()

        your_hand = Hand(deck[:13])
        dummy_hand = Hand(deck[13:26])
        lho_hand = Hand(deck[26:39])
        rho_hand = Hand(deck[39:52])

        deal = PlayDeal(your_hand, dummy_hand, lho_hand, rho_hand, '3NT', 'South')

        situation = {
            'question': 'For a simple squeeze, how many winners should you run before the squeeze card?',
            'question_type': 'squeeze_count',
            'expected_response': {'correct_answer': 'all'},
            'explanation': 'Run ALL your winners first (rectify the count). The last winner squeezes opponent.',
            'accepts_multiple': False
        }
        return deal, situation


class AvoidancePlaysGenerator(PlaySkillHandGenerator):
    """Generate hands for avoidance play practice."""

    skill_id = 'avoidance_plays'
    skill_level = 8
    description = 'Practice avoidance plays'
    practice_format = 'single_decision'

    def generate(self) -> Tuple[PlayDeal, Dict]:
        deck = shuffle_deck()

        your_hand = Hand(deck[:13])
        dummy_hand = Hand(deck[13:26])
        lho_hand = Hand(deck[26:39])
        rho_hand = Hand(deck[39:52])

        deal = PlayDeal(your_hand, dummy_hand, lho_hand, rho_hand, '3NT', 'South')

        # Random danger opponent
        danger = random.choice(['LHO', 'RHO'])
        safe = 'RHO' if danger == 'LHO' else 'LHO'

        situation = {
            'question': f'{danger} has a long suit ready to run. Which opponent can you safely lose to?',
            'question_type': 'avoidance_choice',
            'expected_response': {'correct_answer': safe},
            'explanation': f'Lose to {safe} if needed, but keep {danger} (danger hand) off lead at all costs.',
            'accepts_multiple': False
        }
        return deal, situation


class DeceptivePlaysGenerator(PlaySkillHandGenerator):
    """Generate hands for deceptive play practice."""

    skill_id = 'deceptive_plays'
    skill_level = 8
    description = 'Practice deceptive plays'
    practice_format = 'single_decision'

    SITUATIONS = [
        ('high', 'Play a high card to pretend you don\'t have the lower card.'),
        ('low', 'Play low smoothly to conceal your honor.'),
        ('false_card', 'False card to mislead opponents about holdings.'),
    ]

    def generate(self) -> Tuple[PlayDeal, Dict]:
        correct_play, explanation = random.choice(self.SITUATIONS)

        deck = shuffle_deck()

        your_hand = Hand(deck[:13])
        dummy_hand = Hand(deck[13:26])
        lho_hand = Hand(deck[26:39])
        rho_hand = Hand(deck[39:52])

        deal = PlayDeal(your_hand, dummy_hand, lho_hand, rho_hand, '3NT', 'South')

        situation = {
            'question': 'To deceive opponents, should you play high, low, or false card?',
            'question_type': 'deception_choice',
            'expected_response': {'correct_answer': correct_play},
            'explanation': explanation,
            'accepts_multiple': True  # Multiple deceptive plays can work
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

    # Level 1: Basic Techniques
    'leading_to_tricks': LeadingToTricksGenerator,
    'second_hand_low': SecondHandLowGenerator,
    'third_hand_high': ThirdHandHighGenerator,
    'winning_cheaply': WinningCheaplyGenerator,

    # Level 2: Finessing
    'simple_finesse': SimpleFinessGenerator,
    'double_finesse': DoubleFinesseGenerator,
    'two_way_finesse': TwoWayFinesseGenerator,
    'finesse_or_drop': FinesseOrDropGenerator,

    # Level 3: Suit Establishment
    'establishing_long_suits': EstablishingLongSuitsGenerator,
    'ducking_plays': DuckingPlaysGenerator,
    'hold_up_plays': HoldUpPlaysGenerator,
    'which_suit_to_establish': WhichSuitToEstablishGenerator,

    # Level 4: Trump Management
    'drawing_trumps': DrawingTrumpsGenerator,
    'ruffing_losers': RuffingLosersGenerator,
    'trump_control': TrumpControlGenerator,
    'crossruff': CrossruffGenerator,

    # Level 5: Entry Management
    'preserving_entries': PreservingEntriesGenerator,
    'unblocking': UnblockingGenerator,
    'creating_entries': CreatingEntriesGenerator,
    'entry_killing_plays': EntryKillingPlaysGenerator,

    # Level 6: Card Combinations
    'aq_combinations': AQCombinationsGenerator,
    'kj_combinations': KJCombinationsGenerator,
    'safety_plays': SafetyPlaysGenerator,
    'percentage_plays': PercentagePlaysGenerator,

    # Level 7: Timing & Planning
    'planning_nt_contracts': PlanningNTContractsGenerator,
    'planning_suit_contracts': PlanningSuitContractsGenerator,
    'timing_decisions': TimingDecisionsGenerator,
    'danger_hand': DangerHandGenerator,

    # Level 8: Advanced Techniques
    'elimination_play': EliminationPlayGenerator,
    'endplays': EndplaysGenerator,
    'simple_squeeze': SimpleSqueezeGenerator,
    'avoidance_plays': AvoidancePlaysGenerator,
    'deceptive_plays': DeceptivePlaysGenerator,
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

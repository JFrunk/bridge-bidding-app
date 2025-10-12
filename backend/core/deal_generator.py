"""
DealGenerator - Unified hand generation for bidding and play scenarios.

Provides consistent hand generation across all modules, reusing existing
hand_constructor logic while adding support for play-specific scenarios.
"""

from engine.hand_constructor import generate_hand_with_constraints, generate_hand_for_convention
from engine.hand import Hand, Card
from typing import Dict, List, Optional, Tuple
import random


class DealGenerator:
    """
    Generate deals for bidding or play scenarios.

    Features:
    - Random deal generation
    - Constrained deal generation (HCP, shape, suits)
    - Contract-based generation for play scenarios
    - Convention-based generation for bidding scenarios

    Usage:
        generator = DealGenerator()
        hands = generator.generate_random_deal()
        hands = generator.generate_constrained_deal({...})
    """

    @staticmethod
    def generate_random_deal() -> Dict[str, Hand]:
        """
        Generate completely random 4 hands.

        Returns:
            Dict mapping position ('N', 'E', 'S', 'W') to Hand

        Usage:
            hands = generator.generate_random_deal()
            south_hand = hands['S']
        """
        deck = list(Card('A', '♠') for suit in ['♠', '♥', '♦', '♣']
                   for rank in ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2'])

        # Create full deck
        deck = []
        for suit in ['♠', '♥', '♦', '♣']:
            for rank in ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']:
                deck.append(Card(rank, suit))

        random.shuffle(deck)

        return {
            'N': Hand(deck[0:13]),
            'E': Hand(deck[13:26]),
            'S': Hand(deck[26:39]),
            'W': Hand(deck[39:52])
        }

    @staticmethod
    def generate_constrained_deal(constraints: Dict[str, Dict]) -> Dict[str, Hand]:
        """
        Generate deal with specific constraints on each hand.

        Args:
            constraints: Dict mapping position to constraint dict
                Example: {
                    'S': {'hcp_range': (12, 14), 'is_balanced': True},
                    'N': {'hcp_range': (15, 17), 'is_balanced': True},
                    'E': None,  # random
                    'W': None   # random
                }

        Returns:
            Dict mapping position to Hand

        Constraint format:
            {
                'hcp_range': (min, max),  # HCP range
                'is_balanced': True/False/None,  # Hand shape
                'suit_length_req': (suits, min_length, mode)  # Suit requirements
            }
        """
        # Retry with progressively relaxed constraints if initial attempt fails
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                deck = []
                for suit in ['♠', '♥', '♦', '♣']:
                    for rank in ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']:
                        deck.append(Card(rank, suit))

                hands = {}

                # Generate constrained hands first to maximize success
                constrained_positions = [pos for pos in ['N', 'E', 'S', 'W'] if constraints.get(pos)]
                unconstrained_positions = [pos for pos in ['N', 'E', 'S', 'W'] if not constraints.get(pos)]

                for position in constrained_positions:
                    # Widen HCP ranges on retries to increase success probability
                    adjusted_constraints = constraints[position].copy()
                    if 'hcp_range' in adjusted_constraints and attempt > 0:
                        min_hcp, max_hcp = adjusted_constraints['hcp_range']
                        adjusted_constraints['hcp_range'] = (
                            max(0, min_hcp - attempt * 2),
                            min(37, max_hcp + attempt * 2)
                        )

                    # Generate constrained hand
                    hand, deck = generate_hand_with_constraints(
                        adjusted_constraints, deck
                    )
                    if hand is None:
                        raise ValueError(f"Could not generate hand for {position}")
                    hands[position] = hand

                # Fill in unconstrained positions with random hands
                for position in unconstrained_positions:
                    random.shuffle(deck)
                    hands[position] = Hand(deck[:13])
                    deck = deck[13:]

                return hands

            except ValueError:
                if attempt == max_attempts - 1:
                    raise ValueError(f"Could not generate deal after {max_attempts} attempts with constraints {constraints}")
                continue

    @staticmethod
    def generate_for_convention(
        convention_specialist,
        position: str = 'S'
    ) -> Dict[str, Hand]:
        """
        Generate hands suitable for practicing a specific convention.

        Args:
            convention_specialist: Convention module with get_constraints()
            position: Which position gets the convention hand (default South)

        Returns:
            Dict mapping position to Hand

        Usage:
            from engine.ai.conventions.stayman import StaymanConvention
            stayman = StaymanConvention()
            hands = generator.generate_for_convention(stayman, 'S')
        """
        deck = []
        for suit in ['♠', '♥', '♦', '♣']:
            for rank in ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']:
                deck.append(Card(rank, suit))

        # Generate hand for convention
        convention_hand, deck = generate_hand_for_convention(
            convention_specialist, deck
        )

        if convention_hand is None:
            raise ValueError(f"Could not generate hand for convention {convention_specialist.__class__.__name__}")

        # Generate random hands for other positions
        random.shuffle(deck)
        hands = {}
        positions = ['N', 'E', 'S', 'W']

        for i, pos in enumerate(positions):
            if pos == position:
                hands[pos] = convention_hand
            else:
                start = i * 13 if i < positions.index(position) else (i-1) * 13
                hands[pos] = Hand(deck[start:start+13])

        return hands

    @staticmethod
    def generate_for_contract(
        contract_str: str,
        declarer: str
    ) -> Dict[str, Hand]:
        """
        Generate plausible hands for a specific contract.

        Args:
            contract_str: Contract string (e.g., "3NT", "4♥", "6♠")
            declarer: Declarer position ('N', 'E', 'S', 'W')

        Returns:
            Dict mapping position to Hand

        Logic:
            - Calculates total HCP needed for contract
            - Distributes HCP between declarer and dummy
            - Generates plausible shapes for strain
            - Fills remaining positions with random hands

        Usage:
            hands = generator.generate_for_contract("3NT", "S")
            hands = generator.generate_for_contract("4♥", "S")
        """
        # Parse contract
        level = int(contract_str[0])
        strain = contract_str[1:]

        # Determine dummy position
        dummy_pos = {'N': 'S', 'E': 'W', 'S': 'N', 'W': 'E'}[declarer]

        # Build constraints with wider, more achievable ranges
        constraints = {}

        if strain == 'NT':
            # NT contracts: Both hands balanced, combined ~25-27 HCP for game
            if level >= 6:  # Slam
                constraints[declarer] = {'hcp_range': (15, 20), 'is_balanced': True}
                constraints[dummy_pos] = {'hcp_range': (15, 20), 'is_balanced': True}
            elif level >= 3:  # Game
                constraints[declarer] = {'hcp_range': (12, 17), 'is_balanced': True}
                constraints[dummy_pos] = {'hcp_range': (12, 17), 'is_balanced': True}
            else:  # Partscore
                constraints[declarer] = {'hcp_range': (10, 15), 'is_balanced': True}
                constraints[dummy_pos] = {'hcp_range': (8, 13), 'is_balanced': True}
        else:
            # Suit contract: At least 8-card fit
            if level >= 6:  # Slam
                constraints[declarer] = {
                    'hcp_range': (13, 20),
                    'suit_length_req': ([strain], 5, 'any_of')  # 5+ cards
                }
                constraints[dummy_pos] = {
                    'hcp_range': (10, 18),
                    'suit_length_req': ([strain], 3, 'any_of')  # 3+ for support
                }
            elif level >= 4:  # Game
                constraints[declarer] = {
                    'hcp_range': (11, 18),
                    'suit_length_req': ([strain], 5, 'any_of')  # 5+ cards
                }
                constraints[dummy_pos] = {
                    'hcp_range': (8, 15),
                    'suit_length_req': ([strain], 3, 'any_of')  # 3+ for support
                }
            else:  # Partscore
                constraints[declarer] = {
                    'hcp_range': (8, 15),
                    'suit_length_req': ([strain], 4, 'any_of')  # 4+ cards
                }
                constraints[dummy_pos] = {
                    'hcp_range': (6, 12),
                    'suit_length_req': ([strain], 3, 'any_of')  # 3+ for support
                }

        # Other positions get random hands
        for pos in ['N', 'E', 'S', 'W']:
            if pos not in constraints:
                constraints[pos] = None

        return DealGenerator.generate_constrained_deal(constraints)

    @staticmethod
    def generate_balanced_hand(hcp_range: Tuple[int, int]) -> Hand:
        """
        Generate a single balanced hand with HCP in range.

        Args:
            hcp_range: (min_hcp, max_hcp)

        Returns:
            Hand object

        Usage:
            hand = generator.generate_balanced_hand((15, 17))  # 1NT opening
        """
        deck = []
        for suit in ['♠', '♥', '♦', '♣']:
            for rank in ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']:
                deck.append(Card(rank, suit))

        constraints = {
            'hcp_range': hcp_range,
            'is_balanced': True
        }

        hand, _ = generate_hand_with_constraints(constraints, deck)
        if hand is None:
            raise ValueError(f"Could not generate balanced hand with {hcp_range} HCP")

        return hand

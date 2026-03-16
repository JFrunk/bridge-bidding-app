"""
PBN Test Set Generator

Generates PBN files with hands designed to trigger specific bidding scenarios.
Used to create targeted test suites for the QA harness, organized by the
priority matrix:

    High:   Balanced 12-14 HCP (1NT, Stayman, Transfers)
    Medium: Competitive auctions (Overcalls, Takeout Doubles)
    Low:    Slams/Interference (Blackwood, Gerber, 4th Suit Forcing)

Usage:
    from qa.pbn_generator import PBNTestGenerator

    gen = PBNTestGenerator(seed=42)
    gen.generate_balanced_suite(100, 'test_balanced.pbn')
    gen.generate_competitive_suite(100, 'test_competitive.pbn')
    gen.generate_mixed_suite(100, 'test_mixed.pbn')
"""

import random
from typing import Dict, List, Optional, Tuple

from engine.hand import Hand, Card, PBN_SUITS
from utils.seats import SEAT_NAMES

ALL_RANKS = list('AKQJT98765432')
ALL_SUITS = ['♠', '♥', '♦', '♣']
HCP_VALUES = {'A': 4, 'K': 3, 'Q': 2, 'J': 1}


def _make_deck() -> List[Card]:
    """Create a standard 52-card deck."""
    return [Card(rank, suit) for suit in ALL_SUITS for rank in ALL_RANKS]


def _calculate_hcp(cards: List[Card]) -> int:
    return sum(HCP_VALUES.get(c.rank, 0) for c in cards)


def _is_balanced(cards: List[Card]) -> bool:
    lengths = {}
    for c in cards:
        lengths[c.suit] = lengths.get(c.suit, 0) + 1
    counts = list(lengths.values())
    # Pad missing suits
    while len(counts) < 4:
        counts.append(0)
    return 0 not in counts and 1 not in counts and counts.count(2) <= 1


def _suit_lengths(cards: List[Card]) -> Dict[str, int]:
    lengths = {s: 0 for s in ALL_SUITS}
    for c in cards:
        lengths[c.suit] += 1
    return lengths


class PBNTestGenerator:
    """Generates PBN files with constrained hand distributions."""

    def __init__(self, seed: int = None):
        if seed is not None:
            self.rng = random.Random(seed)
        else:
            self.rng = random.Random()

    def _deal_random(self) -> Dict[str, List[Card]]:
        """Deal 4 random hands of 13 cards each."""
        deck = _make_deck()
        self.rng.shuffle(deck)
        return {
            'North': deck[0:13],
            'East': deck[13:26],
            'South': deck[26:39],
            'West': deck[39:52],
        }

    def _deal_constrained(
        self,
        south_hcp_range: Tuple[int, int] = (0, 40),
        south_balanced: Optional[bool] = None,
        south_min_suit: Optional[Tuple[str, int]] = None,
        north_hcp_range: Tuple[int, int] = (0, 40),
        max_attempts: int = 1000,
    ) -> Optional[Dict[str, List[Card]]]:
        """
        Deal hands with constraints on South (and optionally North).

        Args:
            south_hcp_range: (min, max) HCP for South
            south_balanced: If True, South must be balanced; if False, unbalanced
            south_min_suit: (suit_symbol, min_length) for South
            north_hcp_range: (min, max) HCP for North
            max_attempts: Maximum random deals to try
        """
        for _ in range(max_attempts):
            deal = self._deal_random()
            south = deal['South']
            north = deal['North']

            south_hcp = _calculate_hcp(south)
            if not (south_hcp_range[0] <= south_hcp <= south_hcp_range[1]):
                continue

            north_hcp = _calculate_hcp(north)
            if not (north_hcp_range[0] <= north_hcp <= north_hcp_range[1]):
                continue

            if south_balanced is True and not _is_balanced(south):
                continue
            if south_balanced is False and _is_balanced(south):
                continue

            if south_min_suit:
                suit, min_len = south_min_suit
                lengths = _suit_lengths(south)
                if lengths.get(suit, 0) < min_len:
                    continue

            return deal
        return None

    def _hands_to_pbn_deal(self, deal: Dict[str, List[Card]]) -> str:
        """Convert a deal to PBN [Deal] tag value."""
        parts = []
        for direction in SEAT_NAMES.values():
            hand = Hand(deal[direction])
            parts.append(hand.to_pbn())
        return f"N:{' '.join(parts)}"

    def _vulnerability_for_board(self, board: int) -> str:
        """Standard vulnerability rotation."""
        cycle = board % 16
        vul_map = {
            1: 'None', 2: 'NS', 3: 'EW', 4: 'Both',
            5: 'NS', 6: 'EW', 7: 'Both', 8: 'None',
            9: 'EW', 10: 'Both', 11: 'None', 12: 'NS',
            13: 'Both', 14: 'None', 15: 'NS', 16: 'EW',
            0: 'EW',
        }
        return vul_map.get(cycle, 'None')

    def _dealer_for_board(self, board: int) -> str:
        """Standard dealer rotation."""
        seat_names = list(SEAT_NAMES.values())
        return seat_names[(board - 1) % 4]

    def _write_pbn(self, boards: List[Dict], filepath: str, event: str = 'QA Test'):
        """Write boards to a PBN file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            for board in boards:
                f.write(f'[Event "{event}"]\n')
                f.write(f'[Board "{board["number"]}"]\n')
                f.write(f'[Dealer "{board["dealer"][0]}"]\n')
                f.write(f'[Vulnerable "{board["vulnerability"]}"]\n')
                f.write(f'[Deal "{board["deal"]}"]\n')
                f.write('\n')

    # =========================================================================
    # HIGH PRIORITY: Balanced 12-14 / 15-17 HCP (1NT, Stayman, Transfers)
    # =========================================================================

    def generate_balanced_suite(self, count: int, filepath: str):
        """
        Generate hands focused on 1NT opening and responses.

        Mix:
        - 40% South opens 1NT (15-17 balanced)
        - 30% South responds to partner's 1NT
        - 30% Balanced hands outside 1NT range (12-14, 18-19)
        """
        boards = []
        board_num = 1

        # 1NT openers (South has 15-17 balanced)
        for _ in range(int(count * 0.4)):
            deal = self._deal_constrained(
                south_hcp_range=(15, 17),
                south_balanced=True,
            )
            if deal:
                boards.append(self._make_board(deal, board_num))
                board_num += 1

        # 1NT responders (North has 15-17 balanced, South has response hand)
        for _ in range(int(count * 0.3)):
            deal = self._deal_constrained(
                south_hcp_range=(6, 17),
                north_hcp_range=(15, 17),
            )
            if deal:
                boards.append(self._make_board(deal, board_num))
                board_num += 1

        # Other balanced ranges
        for _ in range(int(count * 0.3)):
            deal = self._deal_constrained(
                south_hcp_range=(12, 14),
                south_balanced=True,
            )
            if not deal:
                deal = self._deal_constrained(
                    south_hcp_range=(18, 19),
                    south_balanced=True,
                )
            if deal:
                boards.append(self._make_board(deal, board_num))
                board_num += 1

        self._write_pbn(boards, filepath, event='QA Balanced Suite')
        return len(boards)

    # =========================================================================
    # MEDIUM PRIORITY: Competitive Auctions (Overcalls, Takeout Doubles)
    # =========================================================================

    def generate_competitive_suite(self, count: int, filepath: str):
        """
        Generate hands focused on competitive bidding.

        Mix:
        - 35% Overcall scenarios (12-17 HCP, 5+ card suit)
        - 35% Takeout double scenarios (12+ HCP, short in opponent's suit)
        - 30% General competitive (mixed HCP, unbalanced)
        """
        boards = []
        board_num = 1

        # Overcall hands (good 5+ card suit)
        for suit in ALL_SUITS:
            for _ in range(int(count * 0.35 / 4)):
                deal = self._deal_constrained(
                    south_hcp_range=(10, 17),
                    south_min_suit=(suit, 5),
                    south_balanced=False,
                )
                if deal:
                    boards.append(self._make_board(deal, board_num))
                    board_num += 1

        # Takeout double hands (support for unbid suits)
        for _ in range(int(count * 0.35)):
            deal = self._deal_constrained(
                south_hcp_range=(12, 20),
                south_balanced=False,
            )
            if deal:
                boards.append(self._make_board(deal, board_num))
                board_num += 1

        # General competitive
        for _ in range(int(count * 0.30)):
            deal = self._deal_constrained(
                south_hcp_range=(8, 20),
            )
            if deal:
                boards.append(self._make_board(deal, board_num))
                board_num += 1

        self._write_pbn(boards, filepath, event='QA Competitive Suite')
        return len(boards)

    # =========================================================================
    # LOW PRIORITY: Slams & Interference
    # =========================================================================

    def generate_slam_suite(self, count: int, filepath: str):
        """
        Generate hands focused on slam bidding.

        Mix:
        - 40% Partnership combined 30+ HCP
        - 30% Strong distributional hands (20+ total points)
        - 30% Slam-try hands (invitational range, 28-31 combined)
        """
        boards = []
        board_num = 1

        # Strong combined hands
        for _ in range(int(count * 0.4)):
            deal = self._deal_constrained(
                south_hcp_range=(15, 22),
                north_hcp_range=(15, 22),
            )
            if deal:
                boards.append(self._make_board(deal, board_num))
                board_num += 1

        # Distributional slam hands
        for _ in range(int(count * 0.3)):
            for suit in ALL_SUITS:
                deal = self._deal_constrained(
                    south_hcp_range=(12, 20),
                    south_min_suit=(suit, 6),
                    north_hcp_range=(10, 18),
                )
                if deal:
                    boards.append(self._make_board(deal, board_num))
                    board_num += 1
                    break

        # Slam-try (invitational)
        for _ in range(int(count * 0.3)):
            deal = self._deal_constrained(
                south_hcp_range=(13, 17),
                north_hcp_range=(13, 17),
            )
            if deal:
                boards.append(self._make_board(deal, board_num))
                board_num += 1

        self._write_pbn(boards, filepath, event='QA Slam Suite')
        return len(boards)

    # =========================================================================
    # MIXED: Full coverage
    # =========================================================================

    def generate_mixed_suite(self, count: int, filepath: str):
        """
        Generate a balanced mix covering all priority levels.

        Distribution: 40% balanced, 35% competitive, 25% slam
        """
        boards = []
        board_num = 1

        # Balanced scenarios
        for _ in range(int(count * 0.4)):
            deal = self._deal_constrained(
                south_hcp_range=(12, 20),
                south_balanced=True,
            )
            if not deal:
                deal = self._deal_random()
            boards.append(self._make_board(deal, board_num))
            board_num += 1

        # Competitive scenarios
        for _ in range(int(count * 0.35)):
            deal = self._deal_constrained(
                south_hcp_range=(8, 20),
                south_balanced=False,
            )
            if not deal:
                deal = self._deal_random()
            boards.append(self._make_board(deal, board_num))
            board_num += 1

        # Slam scenarios
        for _ in range(int(count * 0.25)):
            deal = self._deal_constrained(
                south_hcp_range=(15, 22),
                north_hcp_range=(12, 20),
            )
            if not deal:
                deal = self._deal_random()
            boards.append(self._make_board(deal, board_num))
            board_num += 1

        self._write_pbn(boards, filepath, event='QA Mixed Suite')
        return len(boards)

    def _make_board(self, deal: Dict[str, List[Card]], board_num: int) -> Dict:
        """Create a board dict for PBN output."""
        return {
            'number': board_num,
            'dealer': self._dealer_for_board(board_num),
            'vulnerability': self._vulnerability_for_board(board_num),
            'deal': self._hands_to_pbn_deal(deal),
        }

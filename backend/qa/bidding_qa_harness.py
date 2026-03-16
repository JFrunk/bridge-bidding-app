"""
Bidding QA Harness — Differential Testing Engine

Compares MyBridgeBuddy (MBB) bidding outputs against an external oracle
(WBridge5, BBA, or pre-computed reference auctions) to identify logic
deviations by falsification.

Usage:
    from qa.bidding_qa_harness import BiddingQAHarness
    from qa.oracle_wrapper import CSVOracle

    harness = BiddingQAHarness()
    results = harness.run_pbn_file('test_hands.pbn')
    harness.print_summary(results)
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple

from engine.hand import Hand
from engine.v2.bidding_engine_v2_schema import BiddingEngineV2Schema
from utils.seats import SEAT_NAMES, seat_index, seat_from_index
from qa.pbn_mapper import (
    PBNRecord,
    parse_pbn_file,
    pbn_record_to_engine_inputs,
    calculate_feature_vector,
    DIRECTION_FULL,
    SUIT_ASCII_TO_UNICODE,
)
from qa.oracle_wrapper import OracleBase

logger = logging.getLogger(__name__)

# Directions in auction order from a given dealer
SEAT_ORDER = list(SEAT_NAMES.values())


@dataclass
class BidComparison:
    """Result of comparing a single bid between MBB and oracle/reference."""
    board: int
    seat: str
    bid_index: int  # Position in auction (0-based)
    auction_so_far: List[str]
    mbb_bid: str
    reference_bid: str
    match: bool
    mbb_explanation: str = ''
    feature_vector: Optional[Dict] = None
    hand_pbn: str = ''

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class BoardResult:
    """Result of testing a complete board."""
    board: int
    dealer: str
    vulnerability: str
    total_bids_compared: int = 0
    matches: int = 0
    discrepancies: List[BidComparison] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def accuracy(self) -> float:
        if self.total_bids_compared == 0:
            return 0.0
        return self.matches / self.total_bids_compared

    def to_dict(self) -> Dict:
        return {
            'board': self.board,
            'dealer': self.dealer,
            'vulnerability': self.vulnerability,
            'total_bids_compared': self.total_bids_compared,
            'matches': self.matches,
            'accuracy': round(self.accuracy, 4),
            'discrepancies': [d.to_dict() for d in self.discrepancies],
            'error': self.error,
        }


@dataclass
class HarnessResult:
    """Aggregate result of a QA run."""
    total_boards: int = 0
    boards_with_hands: int = 0
    boards_with_auctions: int = 0
    total_bids_compared: int = 0
    total_matches: int = 0
    board_results: List[BoardResult] = field(default_factory=list)
    duration_seconds: float = 0.0

    @property
    def overall_accuracy(self) -> float:
        if self.total_bids_compared == 0:
            return 0.0
        return self.total_matches / self.total_bids_compared

    @property
    def discrepancy_count(self) -> int:
        return self.total_bids_compared - self.total_matches

    def to_dict(self) -> Dict:
        return {
            'summary': {
                'total_boards': self.total_boards,
                'boards_with_hands': self.boards_with_hands,
                'boards_with_auctions': self.boards_with_auctions,
                'total_bids_compared': self.total_bids_compared,
                'total_matches': self.total_matches,
                'overall_accuracy': round(self.overall_accuracy, 4),
                'discrepancy_count': self.discrepancy_count,
                'duration_seconds': round(self.duration_seconds, 2),
            },
            'boards': [b.to_dict() for b in self.board_results],
        }

    def save(self, filepath: str):
        """Save results to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)


class BiddingQAHarness:
    """
    Core differential testing engine.

    Modes:
    1. Reference auction mode: Compare MBB bids against the auction
       recorded in PBN files (from vugraph/tournament data).
    2. Oracle mode: Feed identical hands to both MBB and an external
       oracle, compare bid-by-bid.
    """

    def __init__(self, oracle: OracleBase = None):
        """
        Args:
            oracle: External oracle for live comparison. If None,
                    uses reference auctions from PBN files.
        """
        self.engine = BiddingEngineV2Schema()
        self.oracle = oracle

    def run_pbn_file(
        self,
        pbn_path: str,
        seats: List[str] = None,
        max_boards: int = None,
        include_features: bool = False,
    ) -> HarnessResult:
        """
        Run differential testing on a PBN file.

        Args:
            pbn_path: Path to PBN file with deals and auctions.
            seats: Which seats to test (default: all four).
                   Use ['South'] to test only user-facing bids.
            max_boards: Limit number of boards to process.
            include_features: Include feature vectors in discrepancy logs
                            (useful for debugging, increases output size).

        Returns:
            HarnessResult with summary and per-board details.
        """
        start_time = time.time()
        records = parse_pbn_file(pbn_path)
        result = HarnessResult(total_boards=len(records))

        if seats is None:
            seats = list(SEAT_ORDER)

        for i, record in enumerate(records):
            if max_boards and i >= max_boards:
                break

            if not record.hands:
                continue
            result.boards_with_hands += 1

            if not record.auction:
                continue
            result.boards_with_auctions += 1

            board_result = self._test_board(record, seats, include_features)
            result.total_bids_compared += board_result.total_bids_compared
            result.total_matches += board_result.matches
            result.board_results.append(board_result)

        result.duration_seconds = time.time() - start_time
        return result

    def _test_board(
        self,
        record: PBNRecord,
        seats: List[str],
        include_features: bool,
    ) -> BoardResult:
        """Test all bid positions in a single board."""
        board_result = BoardResult(
            board=record.board,
            dealer=record.dealer,
            vulnerability=record.vulnerability,
        )

        # Reset engine state for new deal
        self.engine.new_deal()

        # Build seat rotation from dealer
        dealer_idx = seat_index(record.dealer)
        rotation = [SEAT_NAMES[seat_from_index(dealer_idx + i)] for i in range(4)]

        # Walk through the auction, testing each position
        for bid_idx, reference_bid in enumerate(record.auction):
            current_seat = rotation[bid_idx % 4]

            if current_seat not in seats:
                continue

            if current_seat not in record.hands:
                continue

            hand = record.hands[current_seat]
            auction_so_far = record.auction[:bid_idx]

            try:
                mbb_bid, explanation = self.engine.get_next_bid(
                    hand=hand,
                    auction_history=auction_so_far,
                    my_position=current_seat,
                    vulnerability=record.vulnerability,
                    dealer=record.dealer,
                )
            except Exception as e:
                board_result.error = f"Engine error at bid {bid_idx}: {e}"
                logger.error(f"Board {record.board}, bid {bid_idx}: {e}")
                break

            is_match = self._bids_equivalent(mbb_bid, reference_bid)
            board_result.total_bids_compared += 1

            if is_match:
                board_result.matches += 1
            else:
                comparison = BidComparison(
                    board=record.board,
                    seat=current_seat,
                    bid_index=bid_idx,
                    auction_so_far=list(auction_so_far),
                    mbb_bid=mbb_bid,
                    reference_bid=reference_bid,
                    match=False,
                    mbb_explanation=explanation,
                    hand_pbn=hand.to_pbn(),
                )
                if include_features:
                    comparison.feature_vector = calculate_feature_vector(hand)
                board_result.discrepancies.append(comparison)

        return board_result

    def run_with_oracle(
        self,
        pbn_path: str,
        seats: List[str] = None,
        max_boards: int = None,
        include_features: bool = False,
    ) -> HarnessResult:
        """
        Run differential testing comparing MBB against a live oracle.

        Unlike run_pbn_file() which compares against recorded auctions,
        this feeds the same hand to both MBB and the oracle at each step.
        """
        if self.oracle is None:
            raise ValueError("No oracle configured. Pass oracle to constructor.")

        start_time = time.time()
        records = parse_pbn_file(pbn_path)
        result = HarnessResult(total_boards=len(records))

        if seats is None:
            seats = list(SEAT_ORDER)

        for i, record in enumerate(records):
            if max_boards and i >= max_boards:
                break

            if not record.hands:
                continue
            result.boards_with_hands += 1

            board_result = self._test_board_with_oracle(
                record, seats, include_features
            )
            result.total_bids_compared += board_result.total_bids_compared
            result.total_matches += board_result.matches
            result.board_results.append(board_result)

        result.duration_seconds = time.time() - start_time
        return result

    def _test_board_with_oracle(
        self,
        record: PBNRecord,
        seats: List[str],
        include_features: bool,
    ) -> BoardResult:
        """Test a board by comparing MBB and oracle bids in lockstep."""
        board_result = BoardResult(
            board=record.board,
            dealer=record.dealer,
            vulnerability=record.vulnerability,
        )

        self.engine.new_deal()

        dealer_idx = seat_index(record.dealer)
        rotation = [SEAT_NAMES[seat_from_index(dealer_idx + i)] for i in range(4)]
        auction_so_far = []
        consecutive_passes = 0

        for round_num in range(30):  # Safety limit: 30 bidding rounds
            for slot in range(4):
                current_seat = rotation[slot]
                if current_seat not in record.hands:
                    break

                hand = record.hands[current_seat]
                bid_idx = round_num * 4 + slot

                # Get MBB bid
                try:
                    mbb_bid, explanation = self.engine.get_next_bid(
                        hand=hand,
                        auction_history=list(auction_so_far),
                        my_position=current_seat,
                        vulnerability=record.vulnerability,
                        dealer=record.dealer,
                    )
                except Exception as e:
                    board_result.error = f"MBB error: {e}"
                    return board_result

                # Get oracle bid
                oracle_bid = self.oracle.get_bid(
                    hand=hand,
                    auction_history=list(auction_so_far),
                    position=current_seat,
                    vulnerability=record.vulnerability,
                    dealer=record.dealer,
                )

                if oracle_bid and current_seat in seats:
                    is_match = self._bids_equivalent(mbb_bid, oracle_bid)
                    board_result.total_bids_compared += 1

                    if is_match:
                        board_result.matches += 1
                    else:
                        comparison = BidComparison(
                            board=record.board,
                            seat=current_seat,
                            bid_index=bid_idx,
                            auction_so_far=list(auction_so_far),
                            mbb_bid=mbb_bid,
                            reference_bid=oracle_bid,
                            match=False,
                            mbb_explanation=explanation,
                            hand_pbn=hand.to_pbn(),
                        )
                        if include_features:
                            comparison.feature_vector = calculate_feature_vector(hand)
                        board_result.discrepancies.append(comparison)

                # Use MBB's bid to advance the auction (MBB is the "system under test")
                auction_so_far.append(mbb_bid)

                if mbb_bid == 'Pass':
                    consecutive_passes += 1
                else:
                    consecutive_passes = 0

                # Auction ends after 3 consecutive passes (after at least one bid)
                if consecutive_passes >= 3 and len(auction_so_far) >= 4:
                    return board_result

            # Check for all-pass auction
            if len(auction_so_far) == 4 and all(b == 'Pass' for b in auction_so_far):
                return board_result

        return board_result

    @staticmethod
    def _bids_equivalent(bid1: str, bid2: str) -> bool:
        """
        Check if two bids are equivalent, handling notation differences.

        Normalizes: "1S" == "1♠", "P" == "Pass", "D" == "X", etc.
        """
        def normalize(bid: str) -> str:
            bid = bid.strip()
            # Normalize special bids
            if bid in ('P', 'Pass', 'PASS'):
                return 'Pass'
            if bid in ('D', 'X', 'Dbl', 'DBL'):
                return 'X'
            if bid in ('R', 'XX', 'Rdbl', 'RDBL'):
                return 'XX'
            # Normalize suit bids
            for letter, sym in SUIT_ASCII_TO_UNICODE.items():
                bid = bid.replace(letter, sym)
            return bid

        return normalize(bid1) == normalize(bid2)

    def print_summary(self, result: HarnessResult):
        """Print a human-readable summary of QA results."""
        s = result.to_dict()['summary']
        print(f"\n{'='*60}")
        print(f"  Bidding QA Differential Testing Results")
        print(f"{'='*60}")
        print(f"  Boards processed:    {s['boards_with_auctions']}/{s['total_boards']}")
        print(f"  Bids compared:       {s['total_bids_compared']}")
        print(f"  Matches:             {s['total_matches']}")
        print(f"  Discrepancies:       {s['discrepancy_count']}")
        print(f"  Accuracy:            {s['overall_accuracy']*100:.1f}%")
        print(f"  Duration:            {s['duration_seconds']:.1f}s")
        print(f"{'='*60}")

        # Show top discrepancies grouped by type
        if result.discrepancy_count > 0:
            print(f"\n  Top Discrepancies:")
            print(f"  {'-'*56}")
            shown = 0
            for board in result.board_results:
                for d in board.discrepancies:
                    if shown >= 20:
                        remaining = result.discrepancy_count - shown
                        if remaining > 0:
                            print(f"  ... and {remaining} more")
                        return
                    auction_str = ' '.join(d.auction_so_far) if d.auction_so_far else '(opening)'
                    print(
                        f"  Board {d.board:>3} | {d.seat:>5} | "
                        f"MBB: {d.mbb_bid:<6} vs Ref: {d.reference_bid:<6} | "
                        f"After: {auction_str}"
                    )
                    shown += 1

    def analyze_discrepancies(self, result: HarnessResult) -> Dict:
        """
        Categorize discrepancies by type for targeted debugging.

        Returns dict with counts for each category.
        """
        categories = {
            'opening_disagreements': [],
            'response_disagreements': [],
            'competitive_disagreements': [],
            'level_only': [],
            'suit_only': [],
            'pass_vs_bid': [],
            'other': [],
        }

        for board in result.board_results:
            for d in board.discrepancies:
                mbb = d.mbb_bid
                ref = d.reference_bid

                if (mbb == 'Pass') != (ref == 'Pass'):
                    categories['pass_vs_bid'].append(d)
                elif d.bid_index < 4 and not d.auction_so_far:
                    categories['opening_disagreements'].append(d)
                elif (len(mbb) >= 2 and len(ref) >= 2 and
                      mbb[1:] == ref[1:] and mbb[0] != ref[0]):
                    categories['level_only'].append(d)
                elif (len(mbb) >= 2 and len(ref) >= 2 and
                      mbb[0] == ref[0] and mbb[1:] != ref[1:]):
                    categories['suit_only'].append(d)
                else:
                    categories['other'].append(d)

        return {k: len(v) for k, v in categories.items()}

    def analyze_by_phase(self, result: HarnessResult) -> Dict:
        """
        Categorize discrepancies by bidding phase to prioritize logic fixes.

        Phases:
        - opening: First non-pass bid by any player
        - response: Partner's first bid after opener
        - opener_rebid: Opener's second bid
        - responder_rebid: Responder's second bid
        - competition: Bids after opponent interference
        - slam_investigation: Bids at 4+ level in uncontested auctions

        Returns dict with phase → list of BidComparison objects.
        """
        phases = {
            'opening': [],
            'response': [],
            'opener_rebid': [],
            'responder_rebid': [],
            'competition': [],
            'slam_investigation': [],
        }

        for board in result.board_results:
            dealer_idx = seat_index(board.dealer)
            rotation = [SEAT_NAMES[seat_from_index(dealer_idx + i)] for i in range(4)]

            for d in board.discrepancies:
                phase = self._classify_phase(d, rotation)
                phases[phase].append(d)

        return phases

    @staticmethod
    def _classify_phase(d: BidComparison, rotation: List[str]) -> str:
        """Classify a single discrepancy into a bidding phase."""
        auction = d.auction_so_far
        seat = d.seat

        # Find who opened (first non-pass)
        opener_seat = None
        opener_idx = -1
        for i, bid in enumerate(auction):
            if bid not in ('Pass', 'X', 'XX'):
                opener_seat = rotation[i % 4]
                opener_idx = i
                break

        # No opener yet → this is an opening bid
        if opener_seat is None:
            return 'opening'

        # Determine partnership roles
        partner_of_opener = rotation[(rotation.index(opener_seat) + 2) % 4]

        # Check for opponent interference (competition)
        has_interference = False
        for i, bid in enumerate(auction):
            bidder = rotation[i % 4]
            if bid not in ('Pass', 'X', 'XX') and bidder not in (opener_seat, partner_of_opener):
                has_interference = True
                break

        # Slam investigation: bid level 4+ in uncontested auction
        mbb_level = int(d.mbb_bid[0]) if d.mbb_bid[0].isdigit() else 0
        ref_level = int(d.reference_bid[0]) if d.reference_bid[0].isdigit() else 0
        if max(mbb_level, ref_level) >= 4 and not has_interference:
            return 'slam_investigation'

        if has_interference:
            return 'competition'

        # Count bids by this seat before this point
        my_prior_bids = sum(
            1 for i, bid in enumerate(auction)
            if rotation[i % 4] == seat and bid not in ('Pass', 'X', 'XX')
        )

        if seat == opener_seat:
            return 'opener_rebid' if my_prior_bids >= 1 else 'opening'
        elif seat == partner_of_opener:
            return 'responder_rebid' if my_prior_bids >= 1 else 'response'

        # Opponent of opener making a bid
        return 'competition'

    def print_phase_analysis(self, result: HarnessResult):
        """Print discrepancies grouped by bidding phase."""
        phases = self.analyze_by_phase(result)
        total = sum(len(v) for v in phases.values())

        if total == 0:
            print("\n  No discrepancies to analyze by phase.")
            return

        print(f"\n  Discrepancies by Bidding Phase ({total} total):")
        print(f"  {'-'*56}")
        for phase, items in sorted(phases.items(), key=lambda x: -len(x[1])):
            if not items:
                continue
            pct = len(items) / total * 100
            print(f"  {phase:<22} {len(items):>4} ({pct:>5.1f}%)")

            # Show top 3 examples per phase
            for d in items[:3]:
                auction_str = ' '.join(d.auction_so_far[-4:]) if d.auction_so_far else '(none)'
                print(
                    f"    Board {d.board:>3} {d.seat:>5}: "
                    f"MBB={d.mbb_bid:<6} Ref={d.reference_bid:<6} "
                    f"after [{auction_str}]"
                )
            if len(items) > 3:
                print(f"    ... +{len(items)-3} more")

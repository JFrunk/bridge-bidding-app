"""
Centralized Bid Validation Utilities

This module provides helper functions to validate bid legality and filter candidate bids.
All bidding modules should use these utilities to ensure they only suggest legal bids.
"""

from typing import List, Optional, Tuple


class BidValidator:
    """Utilities for validating bid legality in bridge auctions."""

    # Suit ranking for bid comparison
    SUIT_RANK = {'♣': 1, '♦': 2, '♥': 3, '♠': 4, 'NT': 5}

    @staticmethod
    def get_minimum_legal_bid(auction: List[str]) -> Optional[Tuple[int, str]]:
        """
        Calculate the minimum legal bid based on auction history.

        Args:
            auction: List of bids in the auction (e.g., ['1♣', 'Pass', '1♥', '2♦'])

        Returns:
            Tuple of (min_level, min_strain) or None if any bid is legal (opening)
            Examples:
                - After ['1♣', '2♥'], returns (2, '♠') - must bid 2♠ or higher
                - After ['1♣', 'Pass', 'Pass'], returns (1, '♦') - must bid 1♦ or higher
                - After ['Pass', 'Pass', 'Pass'], returns None - any opening legal
        """
        if not auction:
            return None  # Opening position - any bid legal

        # Find last non-Pass/Double/Redouble bid
        last_real_bid = None
        for bid in reversed(auction):
            if bid not in ['Pass', 'X', 'XX', 'Double', 'Redouble']:
                last_real_bid = bid
                break

        if not last_real_bid:
            return None  # All passed - any opening bid legal

        # Parse the last real bid
        try:
            last_level = int(last_real_bid[0])
            last_strain = last_real_bid[1:]

            # Next bid must be at same level with higher strain, or higher level
            # Return the same level and next higher strain
            current_rank = BidValidator.SUIT_RANK.get(last_strain, 0)

            # If last bid was NT (rank 5), must go to next level
            if current_rank >= 5:
                return (last_level + 1, '♣')
            else:
                # Find next higher strain
                for strain, rank in BidValidator.SUIT_RANK.items():
                    if rank > current_rank:
                        return (last_level, strain)

            # Shouldn't reach here, but fallback
            return (last_level + 1, '♣')

        except (ValueError, IndexError):
            # Malformed bid - be conservative
            return None

    @staticmethod
    def is_legal_bid(bid: str, auction: List[str]) -> bool:
        """
        Check if a bid is legal given the current auction.

        Args:
            bid: The bid to check (e.g., '2♥', '1NT', 'Pass', 'X')
            auction: List of bids in the auction

        Returns:
            bool: True if bid is legal, False otherwise

        Examples:
            >>> BidValidator.is_legal_bid('Pass', ['1♣', '1♥'])
            True
            >>> BidValidator.is_legal_bid('2♣', ['1♣', '2♥'])
            False  # 2♣ is lower than 2♥
            >>> BidValidator.is_legal_bid('2♠', ['1♣', '2♥'])
            True  # 2♠ is higher than 2♥
        """
        # Pass, Double, and Redouble are always legal (with some exceptions we'll ignore)
        if bid in ['Pass', 'X', 'XX', 'Double', 'Redouble']:
            return True

        # Get minimum legal bid
        min_legal = BidValidator.get_minimum_legal_bid(auction)
        if min_legal is None:
            # Opening position - any bid is legal
            return True

        min_level, min_strain = min_legal

        # Parse the proposed bid
        try:
            bid_level = int(bid[0])
            bid_strain = bid[1:]

            # Check if bid is at a higher level
            if bid_level > min_level:
                return True

            # Same level - check strain ranking
            if bid_level == min_level:
                bid_rank = BidValidator.SUIT_RANK.get(bid_strain, 0)
                min_rank = BidValidator.SUIT_RANK.get(min_strain, 0)
                return bid_rank >= min_rank

            # Lower level - illegal
            return False

        except (ValueError, IndexError, KeyError):
            # Malformed bid
            return False

    @staticmethod
    def filter_legal_bids(candidate_bids: List[str], auction: List[str]) -> List[str]:
        """
        Filter a list of candidate bids to only include legal ones.

        Args:
            candidate_bids: List of potential bids to filter
            auction: Current auction history

        Returns:
            List of legal bids from the candidates

        Example:
            >>> candidates = ['1NT', '2♣', '2♥', '2♠', '3NT']
            >>> auction = ['1♣', '2♥']
            >>> BidValidator.filter_legal_bids(candidates, auction)
            ['2♠', '3NT']  # Only bids higher than 2♥
        """
        return [bid for bid in candidate_bids if BidValidator.is_legal_bid(bid, auction)]

    @staticmethod
    def compare_bids(bid1: str, bid2: str) -> int:
        """
        Compare two bids to determine which is higher.

        Args:
            bid1: First bid
            bid2: Second bid

        Returns:
            -1 if bid1 < bid2
             0 if bid1 == bid2
             1 if bid1 > bid2

        Example:
            >>> BidValidator.compare_bids('2♥', '2♠')
            -1  # 2♥ is lower than 2♠
            >>> BidValidator.compare_bids('3♣', '2NT')
            1   # 3♣ is higher than 2NT
        """
        try:
            level1 = int(bid1[0])
            level2 = int(bid2[0])
            strain1 = bid1[1:]
            strain2 = bid2[1:]

            if level1 != level2:
                return -1 if level1 < level2 else 1

            rank1 = BidValidator.SUIT_RANK.get(strain1, 0)
            rank2 = BidValidator.SUIT_RANK.get(strain2, 0)

            if rank1 == rank2:
                return 0
            return -1 if rank1 < rank2 else 1

        except (ValueError, IndexError, KeyError):
            return 0  # Treat as equal if can't parse

    @staticmethod
    def get_next_legal_bid(target_bid: str, auction: List[str], max_level_jump: int = None) -> Optional[str]:
        """
        Given a desired bid that might be illegal, find the next legal bid of same strain.

        Args:
            target_bid: The desired bid (may be illegal)
            auction: Current auction history
            max_level_jump: If set, cap search to target_level + max_level_jump.
                           None = search up to 7 (legacy behavior).

        Returns:
            Next legal bid of same strain, or None if no legal bid exists within range

        Example:
            >>> BidValidator.get_next_legal_bid('2NT', ['1♣', '3♥'])
            '3NT'  # 2NT is illegal, but 3NT is legal
            >>> BidValidator.get_next_legal_bid('1♠', ['1♣', '2♥'])
            '2♠'  # 1♠ is illegal, but 2♠ is legal
        """
        if BidValidator.is_legal_bid(target_bid, auction):
            return target_bid  # Already legal

        try:
            target_level = int(target_bid[0])
            target_strain = target_bid[1:]

            # Cap search range if max_level_jump is set
            max_search = min(target_level + max_level_jump, 7) if max_level_jump is not None else 7
            for level in range(target_level + 1, max_search + 1):
                candidate = f"{level}{target_strain}"
                if BidValidator.is_legal_bid(candidate, auction):
                    return candidate

            return None  # No legal bid found

        except (ValueError, IndexError):
            return None

    @staticmethod
    def find_best_legal_bid(candidate_bids: List[Tuple[str, float]], auction: List[str]) -> Optional[Tuple[str, float]]:
        """
        Given a list of candidate bids with scores, find the best legal one.

        Args:
            candidate_bids: List of (bid, score) tuples, sorted by preference
            auction: Current auction history

        Returns:
            Tuple of (bid, score) for best legal bid, or None if no legal bids

        Example:
            >>> candidates = [('2NT', 10.0), ('2♠', 8.0), ('3♣', 6.0)]
            >>> auction = ['1♣', '3♥']
            >>> BidValidator.find_best_legal_bid(candidates, auction)
            ('3♣', 6.0)  # 2NT and 2♠ are illegal, 3♣ is legal
        """
        for bid, score in candidate_bids:
            if BidValidator.is_legal_bid(bid, auction):
                return (bid, score)
        return None


# Convenience functions for direct use
def is_legal_bid(bid: str, auction: List[str]) -> bool:
    """Convenience wrapper for BidValidator.is_legal_bid"""
    return BidValidator.is_legal_bid(bid, auction)


def filter_legal_bids(candidate_bids: List[str], auction: List[str]) -> List[str]:
    """Convenience wrapper for BidValidator.filter_legal_bids"""
    return BidValidator.filter_legal_bids(candidate_bids, auction)


def get_minimum_legal_bid(auction: List[str]) -> Optional[Tuple[int, str]]:
    """Convenience wrapper for BidValidator.get_minimum_legal_bid"""
    return BidValidator.get_minimum_legal_bid(auction)


def get_next_legal_bid(target_bid: str, auction: List[str], max_level_jump: int = None) -> Optional[str]:
    """Convenience wrapper for BidValidator.get_next_legal_bid"""
    return BidValidator.get_next_legal_bid(target_bid, auction, max_level_jump)

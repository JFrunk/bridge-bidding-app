"""
Simple Rule-Based AI for Card Play

This is Phase 1 AI - good enough for learning, easy to understand.
Can be replaced with better AI later without changing PlayEngine.

Strategy:
- Opening leads: 4th highest from longest, top of sequence
- Following suit: Third hand high, second hand low
- Discarding: Lowest from longest weak suit
- Trumping: Trump when profitable
"""

from engine.hand import Hand, Card
from engine.play_engine import PlayState, Contract
from typing import List, Tuple, Optional
import random


class SimplePlayAI:
    """Rule-based AI for card play - Phase 1 MVP"""

    # Rank values for comparison
    RANK_VALUES = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
        'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
    }

    def choose_card(self, state: PlayState, position: str) -> Card:
        """
        Main entry point - choose a card to play

        This is where Phase 2/3 can plug in better AI
        """
        hand = state.hands[position]
        current_trick = state.current_trick
        contract = state.contract

        legal_cards = self._get_legal_cards(hand, current_trick, contract.trump_suit)

        if not current_trick:
            # Leading
            return self._choose_lead(legal_cards, hand, contract, state)

        # Following to a trick
        led_suit = current_trick[0][0].suit
        cards_in_suit = [c for c in legal_cards if c.suit == led_suit]

        if cards_in_suit:
            # Following suit
            return self._follow_suit(cards_in_suit, current_trick, contract, position, state)
        else:
            # Void in led suit - can trump or discard
            return self._discard_or_trump(legal_cards, current_trick, contract, position, state)

    def _get_legal_cards(self, hand: Hand, current_trick: List[Tuple[Card, str]],
                        trump_suit: Optional[str]) -> List[Card]:
        """Get all legal cards from hand"""
        if not current_trick:
            return list(hand.cards)

        led_suit = current_trick[0][0].suit
        cards_in_suit = [c for c in hand.cards if c.suit == led_suit]

        if cards_in_suit:
            return cards_in_suit

        # Void - any card is legal
        return list(hand.cards)

    def _choose_lead(self, legal_cards: List[Card], hand: Hand,
                    contract: Contract, state: PlayState) -> Card:
        """
        Opening lead strategy

        Rules:
        1. Lead 4th highest from longest suit
        2. Lead top of sequence (QJ10, KQ, etc.)
        3. Prefer partner's suit if they bid
        4. Avoid leading trump unless no choice
        """
        # Group cards by suit
        by_suit = {}
        for card in legal_cards:
            if card.suit not in by_suit:
                by_suit[card.suit] = []
            by_suit[card.suit].append(card)

        # Sort each suit by rank
        for suit in by_suit:
            by_suit[suit].sort(key=lambda c: self.RANK_VALUES[c.rank], reverse=True)

        # Don't lead trump if we have other options
        trump_suit = contract.trump_suit
        if trump_suit and len(by_suit) > 1:
            non_trump_suits = {s: cards for s, cards in by_suit.items() if s != trump_suit}
            if non_trump_suits:
                by_suit = non_trump_suits

        # Find longest suit
        longest_suit = max(by_suit.keys(), key=lambda s: len(by_suit[s]))
        suit_cards = by_suit[longest_suit]

        # Check for sequence (QJ, KQ, QJT, etc.)
        if self._has_sequence(suit_cards):
            return suit_cards[0]  # Top of sequence

        # Lead 4th highest from 4+ card suit
        if len(suit_cards) >= 4:
            return suit_cards[3]

        # Lead low from 3-card suit
        if len(suit_cards) >= 2:
            return suit_cards[-1]

        # Single card - lead it
        return suit_cards[0]

    def _has_sequence(self, cards: List[Card]) -> bool:
        """Check if top 2-3 cards form a sequence"""
        if len(cards) < 2:
            return False

        values = [self.RANK_VALUES[c.rank] for c in cards[:3]]

        # Check for touching honors
        if values[0] - values[1] == 1:
            return True

        return False

    def _follow_suit(self, cards_in_suit: List[Card], current_trick: List[Tuple[Card, str]],
                    contract: Contract, position: str, state: PlayState) -> Card:
        """
        Strategy for following suit

        Rules:
        - Second hand low (if partner hasn't played)
        - Third hand high (if partner hasn't played)
        - Fourth hand: win cheaply or dump low
        """
        # Sort cards by rank
        sorted_cards = sorted(cards_in_suit, key=lambda c: self.RANK_VALUES[c.rank])

        trick_position = len(current_trick)  # 0, 1, 2, or 3 (before playing)

        # Find current winning card
        highest_so_far = max(current_trick, key=lambda x: self.RANK_VALUES[x[0].rank])

        # Check if partner is currently winning
        partner_winning = self._is_partner_winning(highest_so_far[1], position, contract)

        if partner_winning:
            # Partner winning - play low
            return sorted_cards[0]

        if trick_position == 1:
            # Second hand - play low
            return sorted_cards[0]

        if trick_position == 2:
            # Third hand - play high to win
            # Find cheapest card that wins
            for card in reversed(sorted_cards):
                if self.RANK_VALUES[card.rank] > self.RANK_VALUES[highest_so_far[0].rank]:
                    return card
            # Can't win - play low
            return sorted_cards[0]

        if trick_position == 3:
            # Fourth hand - win cheaply or dump
            for card in sorted_cards:
                if self.RANK_VALUES[card.rank] > self.RANK_VALUES[highest_so_far[0].rank]:
                    return card
            # Can't win - play low
            return sorted_cards[0]

        # Default: play middle card
        return sorted_cards[len(sorted_cards) // 2]

    def _discard_or_trump(self, legal_cards: List[Card], current_trick: List[Tuple[Card, str]],
                         contract: Contract, position: str, state: PlayState) -> Card:
        """
        Strategy when void in led suit

        Rules:
        - Trump if opponents are winning
        - Discard from longest weak suit
        - Keep potential winners
        """
        trump_suit = contract.trump_suit

        # Check if partner is winning
        highest_so_far = max(current_trick, key=lambda x: self.RANK_VALUES[x[0].rank])
        partner_winning = self._is_partner_winning(highest_so_far[1], position, contract)

        # Get trump cards
        trump_cards = [c for c in legal_cards if trump_suit and c.suit == trump_suit]

        if not partner_winning and trump_cards:
            # Trump to win the trick
            # Find lowest trump that wins
            sorted_trumps = sorted(trump_cards, key=lambda c: self.RANK_VALUES[c.rank])
            return sorted_trumps[0]

        # Discard - get rid of low cards from long suits
        non_trump_cards = [c for c in legal_cards if not trump_suit or c.suit != trump_suit]

        if not non_trump_cards:
            non_trump_cards = legal_cards

        # Group by suit
        by_suit = {}
        for card in non_trump_cards:
            if card.suit not in by_suit:
                by_suit[card.suit] = []
            by_suit[card.suit].append(card)

        # Find longest suit with low cards
        longest_suit = max(by_suit.keys(), key=lambda s: len(by_suit[s]))
        suit_cards = sorted(by_suit[longest_suit], key=lambda c: self.RANK_VALUES[c.rank])

        # Discard lowest
        return suit_cards[0]

    def _is_partner_winning(self, winner_position: str, my_position: str,
                           contract: Contract) -> bool:
        """Check if partner is currently winning the trick"""
        # Determine partnerships
        if my_position in ['N', 'S']:
            my_partnership = ['N', 'S']
        else:
            my_partnership = ['E', 'W']

        return winner_position in my_partnership and winner_position != my_position

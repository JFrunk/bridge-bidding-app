"""
Position Evaluation for Bridge Card Play

This module evaluates how good a bridge card play position is from
a given player's perspective. Used by Minimax AI to score positions.

The evaluation function is the "brain" of the AI - it determines which
positions are favorable and guides the search toward good outcomes.
"""

from engine.play_engine import PlayState, PlayEngine
from typing import Dict, List


class PositionEvaluator:
    """
    Evaluates bridge card play positions

    Analyzes a position and returns a score indicating how favorable
    it is for a given player. Higher scores = better for that player.

    Score range: Approximately -13.0 to +13.0 (max tricks difference)
    """

    # Rank values for card evaluation
    RANK_VALUES = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
        'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
    }

    def __init__(self):
        """Initialize evaluator with default weights"""
        # Component weights (tuned for optimal balance)
        # Higher = more influence on position evaluation
        self.weights = {
            'tricks_won': 1.0,      # Definitive (already decided)
            'sure_winners': 0.5,    # High cards that must win (reduced to avoid overvaluing)
            'trump_control': 0.35,  # Trump length and strength (slightly reduced)
            'communication': 0.25,  # Entries between hands (reduced - was too influential)
            'finesse': 0.3,         # Finessing opportunities (increased - valuable)
            'long_suits': 0.15,     # Long suit potential (reduced - too speculative)
            'defensive': 0.0        # Disabled for now (future)
        }

    def evaluate(self, state: PlayState, perspective: str) -> float:
        """
        Evaluate position from given player's perspective

        Args:
            state: Current play state to evaluate
            perspective: Player to evaluate for ('N', 'E', 'S', 'W')

        Returns:
            Score (higher = better for this player)
            Typically in range [-13, +13] representing tricks advantage

        Example:
            >>> evaluator = PositionEvaluator()
            >>> score = evaluator.evaluate(play_state, 'S')
            >>> print(f"Position worth {score:.2f} tricks for South")
        """
        if state.is_complete:
            # Game over - return definitive result
            return self._evaluate_terminal(state, perspective)

        score = 0.0

        # Component 1: Tricks already won (definitive)
        score += self.weights['tricks_won'] * self._tricks_won_component(state, perspective)

        # Component 2: Sure winners (high cards that must win)
        score += self.weights['sure_winners'] * self._sure_winners_component(state, perspective)

        # Component 3: Trump control
        if self.weights['trump_control'] > 0:
            score += self.weights['trump_control'] * self._trump_control_component(state, perspective)

        # Component 4: Communication/entries
        if self.weights['communication'] > 0:
            score += self.weights['communication'] * self._communication_component(state, perspective)

        # Component 5: Finesse opportunities
        if self.weights.get('finesse', 0) > 0:
            score += self.weights['finesse'] * self._finesse_component(state, perspective)

        # Component 6: Long suit establishment
        if self.weights.get('long_suits', 0) > 0:
            score += self.weights['long_suits'] * self._long_suit_component(state, perspective)

        # Component 7: Defensive potential (disabled for now)
        if self.weights.get('defensive', 0) > 0:
            score += self.weights['defensive'] * self._defensive_component(state, perspective)

        return score

    def _evaluate_terminal(self, state: PlayState, perspective: str) -> float:
        """
        Evaluate completed game

        Just count tricks - game is over so this is definitive.
        """
        if perspective in ['N', 'S']:
            my_tricks = state.tricks_taken_ns
            opp_tricks = state.tricks_taken_ew
        else:
            my_tricks = state.tricks_taken_ew
            opp_tricks = state.tricks_taken_ns

        return float(my_tricks - opp_tricks)

    def _tricks_won_component(self, state: PlayState, perspective: str) -> float:
        """
        Count tricks already won

        This is definitive - these tricks are in the bag.
        Weight: 1.0 (full value)
        """
        if perspective in ['N', 'S']:
            my_tricks = state.tricks_taken_ns
            opp_tricks = state.tricks_taken_ew
        else:
            my_tricks = state.tricks_taken_ew
            opp_tricks = state.tricks_taken_ns

        return float(my_tricks - opp_tricks)

    def _sure_winners_component(self, state: PlayState, perspective: str) -> float:
        """
        Count high cards that are guaranteed winners

        This uses a simple heuristic: count top sequential cards in each suit.

        Example: If you hold AK and opponents hold QJ, both A and K are
        sure winners (worth ~2.0 points total across both hands in partnership)

        Weight: 0.6 (somewhat reliable but not definitive)
        """
        # Get both hands in partnership
        if perspective in ['N', 'S']:
            positions = ['N', 'S']
        else:
            positions = ['E', 'W']

        total_sure_winners = 0.0

        # Evaluate each suit
        for suit in ['♠', '♥', '♦', '♣']:
            # Collect all cards in this suit from both hands
            partnership_cards = []
            for pos in positions:
                hand = state.hands[pos]
                partnership_cards.extend([c for c in hand.cards if c.suit == suit])

            if not partnership_cards:
                continue

            # Sort by rank (highest first)
            sorted_cards = sorted(
                partnership_cards,
                key=lambda c: self.RANK_VALUES[c.rank],
                reverse=True
            )

            # Count top sequential cards as sure winners
            # This is conservative - only counts obvious winners
            top = 14  # Ace
            for card in sorted_cards:
                card_value = self.RANK_VALUES[card.rank]
                if card_value == top:
                    # This card is a sure winner
                    total_sure_winners += 0.5  # Conservative estimate
                    top -= 1
                else:
                    # Gap in sequence - stop counting
                    break

        return total_sure_winners

    def _trump_control_component(self, state: PlayState, perspective: str) -> float:
        """
        Evaluate trump suit control

        Considers:
        - Trump length in partnership hands
        - High trump honors (A, K, Q)
        - Outstanding trumps in opponents' hands
        - Ability to draw trumps

        Returns score representing trump advantage (typically 0-3)
        """
        trump_suit = state.contract.trump_suit

        # No trump contract - return 0
        if not trump_suit:
            return 0.0

        # Get partnership and opponent positions
        if perspective in ['N', 'S']:
            our_positions = ['N', 'S']
            opp_positions = ['E', 'W']
        else:
            our_positions = ['E', 'W']
            opp_positions = ['N', 'S']

        # Count our trumps
        our_trump_count = 0
        our_high_trumps = 0  # Count A, K, Q of trumps
        our_trump_cards = []

        for pos in our_positions:
            hand = state.hands[pos]
            for card in hand.cards:
                if card.suit == trump_suit:
                    our_trump_count += 1
                    our_trump_cards.append(card)
                    if card.rank in ['A', 'K', 'Q']:
                        our_high_trumps += 1

        # Count opponent trumps
        opp_trump_count = 0
        opp_high_trumps = 0

        for pos in opp_positions:
            hand = state.hands[pos]
            for card in hand.cards:
                if card.suit == trump_suit:
                    opp_trump_count += 1
                    if card.rank in ['A', 'K', 'Q']:
                        opp_high_trumps += 1

        score = 0.0

        # Component 1: Trump length advantage (0-2 points)
        # Having more trumps is good
        trump_length_advantage = our_trump_count - opp_trump_count
        score += trump_length_advantage * 0.15

        # Component 2: High trump honors (0-1.5 points)
        # A, K, Q of trumps are valuable
        trump_honor_advantage = our_high_trumps - opp_high_trumps
        score += trump_honor_advantage * 0.5

        # Component 3: Trump control bonus
        # Bonus if we have enough trumps to control the suit
        if our_trump_count >= 8:
            score += 0.3  # Good trump fit

        if our_trump_count >= opp_trump_count + 3:
            score += 0.4  # Significant trump advantage

        # Component 4: Master trumps
        # Check if we have the top trumps
        if our_trump_cards:
            our_highest = max(our_trump_cards, key=lambda c: self.RANK_VALUES[c.rank])
            if our_highest.rank == 'A':
                score += 0.3  # Trump ace is powerful

        return score

    def _communication_component(self, state: PlayState, perspective: str) -> float:
        """
        Evaluate entries between declarer and dummy

        Considers:
        - High cards (A, K) that can be used as entries
        - Distribution of entries between hands
        - Whether key hand has entries to winners

        This is crucial for:
        - Getting to dummy to cash winners
        - Finessing toward the right hand
        - Setting up long suits

        Returns score representing communication quality (typically 0-2)
        """
        # Get partnership positions
        if perspective in ['N', 'S']:
            positions = ['N', 'S']
        else:
            positions = ['E', 'W']

        # For declarer play, consider which hand is dummy
        # For this evaluation, we count entries in both hands
        trump_suit = state.contract.trump_suit

        total_entries = 0.0
        entries_by_position = {}

        for pos in positions:
            hand = state.hands[pos]
            position_entries = 0

            # Group cards by suit
            by_suit = {}
            for card in hand.cards:
                if card.suit not in by_suit:
                    by_suit[card.suit] = []
                by_suit[card.suit].append(card)

            # Count entries (A or K) in each suit
            for suit, cards in by_suit.items():
                sorted_cards = sorted(cards, key=lambda c: self.RANK_VALUES[c.rank], reverse=True)

                if sorted_cards:
                    highest = sorted_cards[0]
                    # Ace is a definite entry
                    if highest.rank == 'A':
                        position_entries += 1.0
                    # King is likely an entry if we have length
                    elif highest.rank == 'K':
                        position_entries += 0.6
                    # Queen might be an entry with length
                    elif highest.rank == 'Q' and len(sorted_cards) >= 3:
                        position_entries += 0.3

            entries_by_position[pos] = position_entries
            total_entries += position_entries

        # Score based on total entries
        score = 0.0

        # Having entries is good
        score += min(total_entries * 0.3, 2.0)

        # Bonus if entries are well-distributed (both hands have access)
        if len(positions) == 2:
            pos1, pos2 = positions
            if entries_by_position.get(pos1, 0) > 0 and entries_by_position.get(pos2, 0) > 0:
                score += 0.5  # Both hands have entries - good for flexibility

        # Penalty if one hand is completely blocked (no entries)
        if any(entries_by_position.get(pos, 0) == 0 for pos in positions):
            score -= 0.3

        return score

    def _finesse_component(self, state: PlayState, perspective: str) -> float:
        """
        Evaluate finessing opportunities

        Detects positions where finessing can gain tricks:
        - AQ combination (finesse for K)
        - KJ combination (finesse for Q)
        - AJ combination (finesse for K or Q)
        - Two-way finesses

        Returns score representing finesse potential (typically 0-2)
        """
        # Get partnership positions
        if perspective in ['N', 'S']:
            positions = ['N', 'S']
        else:
            positions = ['E', 'W']

        finesse_value = 0.0

        # Analyze each suit for finesse opportunities
        for suit in ['♠', '♥', '♦', '♣']:
            # Get all cards in this suit from partnership
            our_cards = []
            for pos in positions:
                hand = state.hands[pos]
                our_cards.extend([c for c in hand.cards if c.suit == suit])

            if len(our_cards) < 2:
                continue  # Need at least 2 cards to finesse

            # Get ranks we hold
            our_ranks = set(card.rank for card in our_cards)
            our_rank_values = set(self.RANK_VALUES[rank] for rank in our_ranks)

            # Check for specific finesse combinations

            # AQ combination (missing K)
            if 'A' in our_ranks and 'Q' in our_ranks and 'K' not in our_ranks:
                finesse_value += 0.5  # 50% to win an extra trick

            # KJ combination (missing Q)
            if 'K' in our_ranks and 'J' in our_ranks and 'Q' not in our_ranks:
                finesse_value += 0.4  # Good finesse opportunity

            # AJ combination (missing K and Q)
            if 'A' in our_ranks and 'J' in our_ranks and 'K' not in our_ranks and 'Q' not in our_ranks:
                finesse_value += 0.4  # Can finesse twice

            # KT combination (missing Q and J)
            if 'K' in our_ranks and 'T' in our_ranks and 'Q' not in our_ranks and 'J' not in our_ranks:
                finesse_value += 0.3

            # QT combination (missing K and J)
            if 'Q' in our_ranks and 'T' in our_ranks and 'K' not in our_ranks and 'J' not in our_ranks:
                finesse_value += 0.25

            # Two-way finesse detection (e.g., AQJ missing K)
            if 'A' in our_ranks and 'Q' in our_ranks and 'J' in our_ranks and 'K' not in our_ranks:
                finesse_value += 0.4  # Flexibility bonus

        return finesse_value

    def _long_suit_component(self, state: PlayState, perspective: str) -> float:
        """
        Evaluate long suit establishment potential

        Considers:
        - Suits with 5+ cards that can be set up
        - High cards in long suits
        - Whether suit is likely to run

        Returns score representing long suit potential (typically 0-2)
        """
        # Get partnership positions
        if perspective in ['N', 'S']:
            positions = ['N', 'S']
        else:
            positions = ['E', 'W']

        trump_suit = state.contract.trump_suit
        long_suit_value = 0.0

        # Analyze each non-trump suit
        for suit in ['♠', '♥', '♦', '♣']:
            if suit == trump_suit:
                continue  # Don't count trump as long suit

            # Count combined length in partnership
            total_length = 0
            high_cards = 0
            all_cards = []

            for pos in positions:
                hand = state.hands[pos]
                suit_cards = [c for c in hand.cards if c.suit == suit]
                total_length += len(suit_cards)
                all_cards.extend(suit_cards)

                # Count high cards (A, K, Q)
                for card in suit_cards:
                    if card.rank in ['A', 'K', 'Q']:
                        high_cards += 1

            # Long suits (5+) have potential
            if total_length >= 5:
                # Base value for having a long suit
                long_suit_value += 0.3

                # Bonus for extra length
                if total_length >= 6:
                    long_suit_value += 0.2
                if total_length >= 7:
                    long_suit_value += 0.2

                # Bonus for high cards in long suit
                long_suit_value += high_cards * 0.15

                # Check if suit is likely to run (have top cards)
                if all_cards:
                    sorted_cards = sorted(all_cards, key=lambda c: self.RANK_VALUES[c.rank], reverse=True)
                    top_card = sorted_cards[0]

                    # If we have A or K in long suit, it's more likely to run
                    if top_card.rank == 'A':
                        long_suit_value += 0.3
                    elif top_card.rank == 'K':
                        long_suit_value += 0.2

        return long_suit_value

    def _defensive_component(self, state: PlayState, perspective: str) -> float:
        """
        Evaluate defensive potential

        Not implemented yet - always returns 0.
        Future: Consider setting up defensive tricks, promoting honors.
        """
        return 0.0

    def get_component_scores(self, state: PlayState, perspective: str) -> Dict[str, float]:
        """
        Get individual component scores for debugging/analysis

        Returns:
            Dictionary mapping component name to its score

        Example:
            >>> scores = evaluator.get_component_scores(state, 'S')
            >>> print(f"Tricks won: {scores['tricks_won']}")
            >>> print(f"Sure winners: {scores['sure_winners']}")
        """
        return {
            'tricks_won': self._tricks_won_component(state, perspective),
            'sure_winners': self._sure_winners_component(state, perspective),
            'trump_control': self._trump_control_component(state, perspective),
            'communication': self._communication_component(state, perspective),
            'finesse': self._finesse_component(state, perspective),
            'long_suits': self._long_suit_component(state, perspective),
            'defensive': self._defensive_component(state, perspective),
        }

    def explain_evaluation(self, state: PlayState, perspective: str) -> str:
        """
        Get human-readable explanation of evaluation

        Returns detailed breakdown of why position received its score.

        Returns:
            Multi-line explanation string

        Example:
            >>> explanation = evaluator.explain_evaluation(state, 'S')
            >>> print(explanation)
            Position evaluation for S: +2.5
            ├─ Tricks won: +2.0 (2 more tricks than opponents)
            ├─ Sure winners: +0.5 (1 high card will win)
            └─ Total: +2.5
        """
        components = self.get_component_scores(state, perspective)
        total = self.evaluate(state, perspective)

        lines = [f"Position evaluation for {perspective}: {total:+.1f}"]

        for name, value in components.items():
            if abs(value) > 0.01:  # Only show non-zero components
                weight = self.weights[name]
                weighted = weight * value
                lines.append(f"├─ {name.replace('_', ' ').title()}: "
                           f"{weighted:+.1f} (raw: {value:.1f}, weight: {weight:.1f})")

        lines.append(f"└─ Total: {total:+.1f}")

        return '\n'.join(lines)


if __name__ == '__main__':
    # Self-test
    from tests.play_test_helpers import create_test_deal, create_play_scenario

    print("Testing Position Evaluator...")

    # Create a test position
    deal = create_test_deal(
        north="♠AKQ ♥432 ♦AKQ2 ♣432",    # 3+3+4+3 = 13
        east="♠432 ♥765 ♦765 ♣7654",     # 3+3+3+4 = 13
        south="♠765 ♥AKQ ♦432 ♣AKQ8",   # 3+3+3+4 = 13
        west="♠JT98 ♥JT98 ♦JT9 ♣J9"     # 4+4+3+2 = 13
    )

    play_state = create_play_scenario("3NT by S", deal, "None")

    evaluator = PositionEvaluator()

    # Evaluate from South's perspective
    score = evaluator.evaluate(play_state, 'S')
    print(f"\nEvaluation for South: {score:+.2f}")

    # Get detailed explanation
    print("\nDetailed breakdown:")
    print(evaluator.explain_evaluation(play_state, 'S'))

    # Evaluate from West's perspective (should be negative)
    score_west = evaluator.evaluate(play_state, 'W')
    print(f"\nEvaluation for West: {score_west:+.2f}")
    print("(Should be roughly negative of South's score)")

    print("\n✓ Position Evaluator self-test complete")

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
        # Component weights (can be tuned)
        self.weights = {
            'tricks_won': 1.0,      # Definitive (already decided)
            'sure_winners': 0.6,    # High cards that must win
            'trump_control': 0.0,   # Disabled for now
            'communication': 0.0,   # Disabled for now
            'defensive': 0.0        # Disabled for now
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

        # Component 3: Trump control (disabled for MVP)
        if self.weights['trump_control'] > 0:
            score += self.weights['trump_control'] * self._trump_control_component(state, perspective)

        # Component 4: Communication (disabled for MVP)
        if self.weights['communication'] > 0:
            score += self.weights['communication'] * self._communication_component(state, perspective)

        # Component 5: Defensive potential (disabled for MVP)
        if self.weights['defensive'] > 0:
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

        Not implemented in MVP - always returns 0.
        Future: Consider trump length, high trumps, ability to draw trumps.
        """
        return 0.0

    def _communication_component(self, state: PlayState, perspective: str) -> float:
        """
        Evaluate entries between declarer and dummy

        Not implemented in MVP - always returns 0.
        Future: Count high cards that can be used as entries.
        """
        return 0.0

    def _defensive_component(self, state: PlayState, perspective: str) -> float:
        """
        Evaluate defensive potential

        Not implemented in MVP - always returns 0.
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

"""
Minimax AI with Alpha-Beta Pruning for Bridge Card Play

This is Phase 2 AI - looks ahead several tricks to find the best line of play.
Significantly stronger than the rule-based SimplePlayAI.

Algorithm:
- Minimax search with alpha-beta pruning
- Position evaluation at leaf nodes
- Depth-limited search (configurable)
- Assumes perfect information (all cards visible)

Performance:
- Depth 2: ~16-64 positions, < 1 second
- Depth 3: ~64-256 positions, 1-3 seconds
- Depth 4: ~256-1024 positions, 3-10 seconds
"""

from engine.hand import Hand, Card
from engine.play_engine import PlayEngine, PlayState, Contract
from engine.play.ai.base_ai import BasePlayAI
from engine.play.ai.evaluation import PositionEvaluator
from typing import List, Tuple, Optional
import copy
import time


class MinimaxPlayAI(BasePlayAI):
    """
    Minimax AI with alpha-beta pruning for Bridge card play

    This AI performs look-ahead search to find the best card to play.
    It evaluates positions several tricks in advance and chooses the
    move that leads to the best outcome.

    Example:
        >>> ai = MinimaxPlayAI(max_depth=3)
        >>> card = ai.choose_card(play_state, 'S')
        >>> stats = ai.get_statistics()
        >>> print(f"Searched {stats['nodes']} nodes in {stats['time']:.2f}s")
    """

    def __init__(self, max_depth: int = 3, evaluator: Optional[PositionEvaluator] = None):
        """
        Initialize Minimax AI

        Args:
            max_depth: How many tricks to look ahead (2-4 recommended)
                - 2 = fast (~100-500ms), intermediate strength
                - 3 = balanced (~1-3s), advanced strength
                - 4 = slow (~3-10s), expert strength
            evaluator: Position evaluation function (uses default if None)

        Example:
            >>> # Fast AI for real-time play
            >>> ai_fast = MinimaxPlayAI(max_depth=2)

            >>> # Strong AI for analysis
            >>> ai_strong = MinimaxPlayAI(max_depth=4)
        """
        self.max_depth = max_depth
        self.evaluator = evaluator or PositionEvaluator()

        # Statistics (reset each move)
        self.nodes_searched = 0
        self.leaf_nodes = 0
        self.pruned_branches = 0
        self.search_time = 0.0
        self.best_score = 0.0

    def get_name(self) -> str:
        """Return AI name with depth"""
        return f"Minimax AI (depth {self.max_depth})"

    def get_difficulty(self) -> str:
        """Return difficulty level based on depth"""
        if self.max_depth <= 2:
            return "intermediate"
        elif self.max_depth <= 3:
            return "advanced"
        else:
            return "expert"

    def choose_card(self, state: PlayState, position: str) -> Card:
        """
        Choose best card using minimax search

        This is the main entry point. It searches all legal cards,
        evaluates resulting positions, and returns the best move.

        Args:
            state: Current play state
            position: Position making the play

        Returns:
            Best card to play according to minimax search

        Example:
            >>> ai = MinimaxPlayAI(max_depth=3)
            >>> card = ai.choose_card(play_state, 'S')
            >>> print(f"AI chose {card.rank}{card.suit}")
        """
        # Reset statistics
        self.reset_statistics()
        start_time = time.time()

        # Get legal moves
        legal_cards = self._get_legal_cards(state, position)

        if len(legal_cards) == 1:
            # Only one legal card, no need to search
            self.search_time = time.time() - start_time
            return legal_cards[0]

        # Determine if we're maximizing or minimizing
        # Declarer's side maximizes, defender's side minimizes
        is_declarer_side = self._is_declarer_side(position, state.contract.declarer)

        # Run minimax search for each legal card
        best_card = None
        best_score = float('-inf') if is_declarer_side else float('inf')

        for card in legal_cards:
            # Simulate playing this card
            test_state = self._simulate_play(state, card, position)

            # Evaluate resulting position
            score = self._minimax(
                test_state,
                depth=self.max_depth - 1,
                alpha=float('-inf'),
                beta=float('inf'),
                maximizing=is_declarer_side,
                perspective=position
            )

            # Update best move
            if is_declarer_side:
                if score > best_score:
                    best_score = score
                    best_card = card
            else:
                if score < best_score:
                    best_score = score
                    best_card = card

        self.search_time = time.time() - start_time
        self.best_score = best_score

        # Fallback (should never happen)
        return best_card or legal_cards[0]

    def _minimax(self, state: PlayState, depth: int, alpha: float,
                 beta: float, maximizing: bool, perspective: str) -> float:
        """
        Minimax search with alpha-beta pruning

        This is the recursive heart of the algorithm. It searches the
        game tree, pruning branches that can't affect the final result.

        Args:
            state: Current position to evaluate
            depth: Remaining search depth (stops at 0)
            alpha: Best value maximizer can guarantee
            beta: Best value minimizer can guarantee
            maximizing: True if maximizing player's turn
            perspective: Original player's position (for evaluation)

        Returns:
            Best evaluation score from this position

        Algorithm:
            1. If depth 0 or game over: evaluate position
            2. If maximizing: find maximum of child positions
            3. If minimizing: find minimum of child positions
            4. Prune when alpha >= beta (impossible to reach)
        """
        self.nodes_searched += 1

        # Terminal conditions
        if depth == 0 or state.is_complete:
            self.leaf_nodes += 1
            return self.evaluator.evaluate(state, perspective)

        # Get current player and legal moves
        current_player = state.next_to_play
        legal_cards = self._get_legal_cards(state, current_player)

        if maximizing:
            max_eval = float('-inf')
            for card in legal_cards:
                test_state = self._simulate_play(state, card, current_player)
                eval_score = self._minimax(
                    test_state, depth - 1, alpha, beta, False, perspective
                )
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)

                # Beta cutoff (pruning)
                if beta <= alpha:
                    self.pruned_branches += 1
                    break

            return max_eval
        else:
            min_eval = float('inf')
            for card in legal_cards:
                test_state = self._simulate_play(state, card, current_player)
                eval_score = self._minimax(
                    test_state, depth - 1, alpha, beta, True, perspective
                )
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)

                # Alpha cutoff (pruning)
                if beta <= alpha:
                    self.pruned_branches += 1
                    break

            return min_eval

    def _simulate_play(self, state: PlayState, card: Card,
                       position: str) -> PlayState:
        """
        Simulate playing a card and return resulting state

        Creates a deep copy of the state to avoid modifying the original.
        Handles trick completion and next player determination.

        Args:
            state: Current state to simulate from
            card: Card to play
            position: Position playing the card

        Returns:
            New state after playing the card

        Note:
            This is expensive (deep copy), but necessary for minimax search.
        """
        # Deep copy the state (expensive but necessary)
        new_state = copy.deepcopy(state)

        # Play the card
        new_state.current_trick.append((card, position))
        new_state.hands[position].cards.remove(card)

        # Check if trick is complete
        if len(new_state.current_trick) == 4:
            # Determine winner
            winner = PlayEngine.determine_trick_winner(
                new_state.current_trick,
                new_state.contract.trump_suit
            )

            # Update tricks won
            new_state.tricks_won[winner] += 1

            # Save to history
            from engine.play_engine import Trick
            new_state.trick_history.append(
                Trick(
                    cards=list(new_state.current_trick),
                    leader=new_state.next_to_play,
                    winner=winner
                )
            )

            # Clear trick and set next player
            new_state.current_trick = []
            new_state.next_to_play = winner
        else:
            # Next player clockwise
            new_state.next_to_play = PlayEngine.next_player(position)

        return new_state

    def _get_legal_cards(self, state: PlayState, position: str) -> List[Card]:
        """
        Get all legal cards for current position

        Bridge rules:
        - Must follow suit if able
        - If void in led suit, any card is legal

        Args:
            state: Current play state
            position: Position to get legal cards for

        Returns:
            List of legal cards
        """
        hand = state.hands[position]

        if not state.current_trick:
            # Leading - any card is legal
            return list(hand.cards)

        # Following - must follow suit if able
        led_suit = state.current_trick[0][0].suit
        cards_in_suit = [c for c in hand.cards if c.suit == led_suit]

        if cards_in_suit:
            return cards_in_suit
        else:
            # Void - any card is legal
            return list(hand.cards)

    def _is_declarer_side(self, position: str, declarer: str) -> bool:
        """
        Check if position is on declarer's side

        Args:
            position: Position to check
            declarer: Declarer position

        Returns:
            True if position is declarer or dummy
        """
        if declarer in ['N', 'S']:
            return position in ['N', 'S']
        else:
            return position in ['E', 'W']

    def get_statistics(self) -> dict:
        """
        Get search statistics

        Returns:
            Dictionary with:
            - nodes: Total nodes searched
            - leaf_nodes: Positions evaluated
            - pruned: Branches pruned by alpha-beta
            - time: Search time in seconds
            - nps: Nodes per second
            - score: Best score found

        Example:
            >>> card = ai.choose_card(state, 'S')
            >>> stats = ai.get_statistics()
            >>> print(f"Searched {stats['nodes']} nodes in {stats['time']:.2f}s")
            >>> print(f"Pruned {stats['pruned']} branches")
        """
        nps = self.nodes_searched / self.search_time if self.search_time > 0 else 0

        return {
            'nodes': self.nodes_searched,
            'leaf_nodes': self.leaf_nodes,
            'pruned': self.pruned_branches,
            'time': self.search_time,
            'nps': nps,
            'score': self.best_score,
            'depth': self.max_depth
        }

    def reset_statistics(self):
        """Reset search statistics (called before each move)"""
        self.nodes_searched = 0
        self.leaf_nodes = 0
        self.pruned_branches = 0
        self.search_time = 0.0
        self.best_score = 0.0

    def get_explanation(self, card: Card, state: PlayState, position: str) -> str:
        """
        Provide explanation for card choice

        Args:
            card: Card that was played
            state: State when card was chosen
            position: Position that played

        Returns:
            Human-readable explanation with search statistics
        """
        stats = self.get_statistics()

        explanation = f"Played {card.rank}{card.suit} "
        explanation += f"(searched {stats['nodes']} positions in {stats['time']:.2f}s, "
        explanation += f"evaluation: {stats['score']:+.1f})"

        return explanation


if __name__ == '__main__':
    # Self-test
    from tests.play_test_helpers import create_test_deal, create_play_scenario

    print("Testing Minimax AI...")

    # Create a test position
    deal = create_test_deal(
        north="♠AKQ ♥432 ♦AKQ2 ♣432",
        east="♠432 ♥765 ♦765 ♣7654",
        south="♠765 ♥AKQ ♦432 ♣AKQ8",
        west="♠JT98 ♥JT98 ♦JT9 ♣J9"
    )

    play_state = create_play_scenario("3NT by S", deal, "None")

    # Test with depth 2 (fast)
    print("\n=== Testing Minimax AI (depth 2) ===")
    ai_fast = MinimaxPlayAI(max_depth=2)
    card = ai_fast.choose_card(play_state, 'W')  # Opening leader

    print(f"AI chose: {card.rank}{card.suit}")

    stats = ai_fast.get_statistics()
    print(f"Nodes searched: {stats['nodes']}")
    print(f"Leaf nodes: {stats['leaf_nodes']}")
    print(f"Branches pruned: {stats['pruned']}")
    print(f"Search time: {stats['time']:.3f}s")
    print(f"Nodes/sec: {stats['nps']:.0f}")
    print(f"Best score: {stats['score']:+.2f}")

    # Test with depth 3 (stronger)
    print("\n=== Testing Minimax AI (depth 3) ===")
    ai_strong = MinimaxPlayAI(max_depth=3)
    card = ai_strong.choose_card(play_state, 'W')

    print(f"AI chose: {card.rank}{card.suit}")

    stats = ai_strong.get_statistics()
    print(f"Nodes searched: {stats['nodes']}")
    print(f"Leaf nodes: {stats['leaf_nodes']}")
    print(f"Branches pruned: {stats['pruned']}")
    print(f"Search time: {stats['time']:.3f}s")
    print(f"Nodes/sec: {stats['nps']:.0f}")
    print(f"Best score: {stats['score']:+.2f}")

    print("\n✓ Minimax AI self-test complete")
    print(f"\nAI Info:")
    print(f"  Name: {ai_strong.get_name()}")
    print(f"  Difficulty: {ai_strong.get_difficulty()}")

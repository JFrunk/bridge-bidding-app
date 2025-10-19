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

        # Determine if this position is making a declarer-side or defender-side move
        # (used for move ordering heuristics)
        is_declarer_side = self._is_declarer_side(position, state.contract.declarer)

        # CRITICAL: Detect if this is a discard situation
        is_discarding = False
        if state.current_trick:
            led_suit = state.current_trick[0][0].suit
            # If all our cards are different suit than led, we're discarding
            if all(card.suit != led_suit for card in legal_cards):
                is_discarding = True

        # Order moves for better alpha-beta pruning
        ordered_cards = self._order_moves(legal_cards, state, position, is_declarer_side)

        # Run minimax search for each legal card
        best_card = None
        best_score = float('-inf')  # ALWAYS maximize from perspective player's viewpoint

        # Track all cards with best score for tiebreaking
        best_cards = []

        for card in ordered_cards:
            # Simulate playing this card
            test_state = self._simulate_play(state, card, position)

            # Evaluate resulting position
            # CRITICAL FIX: Root player ALWAYS maximizes (evaluation is perspective-aware)
            # Next player will minimize from root's perspective (i.e., maximize from their own)
            score = self._minimax(
                test_state,
                depth=self.max_depth - 1,
                alpha=float('-inf'),
                beta=float('inf'),
                maximizing=False,  # Next player minimizes root's score
                perspective=position  # But evaluation stays from root's perspective
            )

            # DISCARD PENALTY: If discarding an honor card, apply strong penalty
            # This prevents AI from discarding Kings when low cards are available
            if is_discarding:
                discard_penalty = self._calculate_discard_penalty(card)
                score += discard_penalty  # Penalty is negative, so this reduces score

            # Update best move - ALWAYS maximize from root player's perspective
            if score > best_score:
                best_score = score
                best_card = card
                best_cards = [card]
            elif score == best_score:
                best_cards.append(card)

        # CRITICAL TIEBREAKER: If discarding, ALWAYS choose the LOWEST rank card
        # This prevents wasting high cards when positions are evaluated similarly
        if is_discarding:
            RANK_VALUES = {
                '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
                'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
            }

            # If we have multiple best cards, pick lowest
            if len(best_cards) > 1:
                best_card = min(best_cards, key=lambda c: RANK_VALUES[c.rank])

            # ADDITIONAL: Even if only one "best" card, check if any LOW card
            # has a similar score (within 0.3 tricks). If so, prefer the low card.
            # This prevents the AI from discarding K when 2 is nearly as good.
            elif best_card:
                tolerance = 0.3  # Allow 0.3 trick difference
                similar_cards = []

                for c in legal_cards:
                    # Simulate this card
                    test_state = self._simulate_play(state, c, position)
                    c_score = self._minimax(
                        test_state,
                        depth=0,  # Just evaluate, don't search deep again
                        alpha=float('-inf'),
                        beta=float('inf'),
                        maximizing=True,  # FIXED: Consistent with main logic (root maximizes)
                        perspective=position
                    )

                    # Check if score is similar to best (unified logic - no declarer check needed)
                    if abs(c_score - best_score) <= tolerance:
                        similar_cards.append(c)

                # If we found cards with similar scores, pick the lowest rank
                if len(similar_cards) > 1:
                    best_card = min(similar_cards, key=lambda c: RANK_VALUES[c.rank])

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

        # Order moves for better pruning
        is_decl = self._is_declarer_side(current_player, state.contract.declarer)
        ordered_cards = self._order_moves(legal_cards, state, current_player, is_decl)

        if maximizing:
            max_eval = float('-inf')
            for card in ordered_cards:
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
            for card in ordered_cards:
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
            # FIXED: Leader is the FIRST player in the trick, not next_to_play
            trick_leader = new_state.current_trick[0][1]  # (card, player) tuple
            new_state.trick_history.append(
                Trick(
                    cards=list(new_state.current_trick),
                    leader=trick_leader,  # Correct: first player in trick
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

    def _order_moves(self, cards: List[Card], state: PlayState,
                     position: str, is_declarer_side: bool) -> List[Card]:
        """
        Order moves to improve alpha-beta pruning efficiency

        Better move ordering = more cutoffs = faster search

        Heuristics:
        1. DISCARD SITUATION: Prioritize LOW cards (don't waste high cards)
        2. FOLLOWING SUIT: Prioritize cards that can win the trick
        3. High cards (A, K) when trying to win
        4. Trump cards (in trump contracts)
        5. Other cards by rank

        Args:
            cards: Legal cards to order
            state: Current state
            position: Position playing
            is_declarer_side: True if declarer/dummy

        Returns:
            Ordered list of cards (best first for pruning efficiency)
        """
        if len(cards) <= 1:
            return cards

        # Rank values for sorting
        RANK_VALUES = {
            '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
            'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
        }

        # CRITICAL: Detect if this is a discard situation
        is_discarding = False
        if state.current_trick:
            led_suit = state.current_trick[0][0].suit
            # If all our cards are different suit than led, we're discarding
            if all(card.suit != led_suit for card in cards):
                is_discarding = True

        def card_priority(card: Card) -> tuple:
            """Calculate priority score for card (higher = better for search)"""
            priority_score = 0

            # CRITICAL FIX: If discarding, REVERSE priority (examine low cards first)
            if is_discarding:
                # When discarding, LOW cards are best (don't waste high cards)
                # Examine low cards first in search
                priority_score -= RANK_VALUES[card.rank] * 10  # Reverse: lower rank = higher priority

                # Strong penalty for discarding honors when discarding
                if card.rank == 'A':
                    priority_score -= 200  # Examine last
                elif card.rank == 'K':
                    priority_score -= 150  # Examine last
                elif card.rank == 'Q':
                    priority_score -= 100  # Examine last
                elif card.rank == 'J':
                    priority_score -= 50

                # Return early for discard situation
                return (-priority_score, card.rank, card.suit)

            # NOT DISCARDING: Normal priority for winning/following suit

            # Priority 1: High cards (A, K) are usually good when following suit
            if card.rank == 'A':
                priority_score += 100
            elif card.rank == 'K':
                priority_score += 80
            elif card.rank == 'Q':
                priority_score += 60

            # Priority 2: Trump cards (if ruffing)
            if state.contract.trump_suit and card.suit == state.contract.trump_suit:
                if not state.current_trick or state.current_trick[0][0].suit != state.contract.trump_suit:
                    priority_score += 50  # Ruffing

            # Priority 3: Winning current trick
            if state.current_trick:
                led_suit = state.current_trick[0][0].suit
                if card.suit == led_suit:
                    # Following suit - check if this wins
                    current_highest = max(
                        (c for c, p in state.current_trick if c.suit == led_suit),
                        key=lambda c: RANK_VALUES[c.rank],
                        default=None
                    )
                    if current_highest and RANK_VALUES[card.rank] > RANK_VALUES[current_highest.rank]:
                        priority_score += 70  # Wins the trick

            # Priority 4: Base rank value
            priority_score += RANK_VALUES[card.rank]

            # Return as tuple for sorting (higher first)
            return (-priority_score, card.rank, card.suit)  # Negative for descending sort

        # Sort cards by priority
        return sorted(cards, key=card_priority)

    def _calculate_discard_penalty(self, card: Card) -> float:
        """
        Calculate penalty for discarding a specific card

        When void in the led suit, we're discarding. High cards (honors)
        should receive strong penalties to discourage wasting them.

        Args:
            card: Card being considered for discard

        Returns:
            Penalty value (negative float, larger magnitude = worse discard)

        Penalty values:
            - Ace: -2.0 (devastating to discard)
            - King: -1.5 (very bad to discard)
            - Queen: -1.0 (bad to discard)
            - Jack: -0.5 (poor to discard)
            - 10: -0.2 (slightly bad)
            - 2-9: 0.0 (no penalty, fine to discard)

        Example:
            >>> penalty = ai._calculate_discard_penalty(Card('K', '♣'))
            >>> # Returns -1.5 (strong penalty for discarding King)
        """
        if card.rank == 'A':
            return -2.0  # Devastating to discard an Ace
        elif card.rank == 'K':
            return -1.5  # Very bad to discard a King
        elif card.rank == 'Q':
            return -1.0  # Bad to discard a Queen
        elif card.rank == 'J':
            return -0.5  # Poor to discard a Jack
        elif card.rank == 'T':
            return -0.2  # Slightly bad to discard a Ten
        else:
            return 0.0  # Low cards (2-9) have no penalty - fine to discard

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

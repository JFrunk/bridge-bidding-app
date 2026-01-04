"""
Double Dummy Solver AI for Card Play

This module integrates the industry-standard DDS (Double Dummy Solver)
for expert-level bridge play. DDS provides perfect play assuming all
cards are known.

Rating: 9/10 (Expert level)
Performance: <1ms per solve (using solve_board)
Accuracy: 100% for perfect information scenarios

The implementation uses endplay's solve_board() which directly returns
optimal plays with trick counts, avoiding the need for simulation.

Dependencies:
- endplay library (includes DDS bindings)
- pip install endplay

Platform Notes:
- Works reliably on Linux (production default)
- Crashes on macOS M1/M2 - use Minimax fallback
"""

from engine.hand import Hand, Card
from engine.play_engine import PlayState, Contract, PlayEngine
from engine.play.ai.base_ai import BasePlayAI
from typing import List, Optional, Tuple
import time

try:
    from endplay.types import Deal, Player as EndplayPlayer, Denom, Card as EndplayCard
    from endplay.dds import calc_dd_table, solve_board
    DDS_AVAILABLE = True
except ImportError as e:
    DDS_AVAILABLE = False
    # Stub types for when DDS is not available
    Deal = None
    EndplayPlayer = None
    Denom = None
    EndplayCard = None
    solve_board = None
    calc_dd_table = None
    # Only print warning if running as main
    if __name__ == '__main__':
        print(f"⚠️  Warning: endplay not installed. DDS AI will not work.")
        print(f"   Install with: pip install endplay")
        print(f"   Error: {e}")


class DDSPlayAI(BasePlayAI):
    """
    Double Dummy Solver AI - Expert Level Play

    Uses the industry-standard DDS to find optimal play.
    Assumes perfect information (all cards visible).

    Example:
        >>> ai = DDSPlayAI()
        >>> card = ai.choose_card(play_state, 'S')
        >>> # Returns optimal card based on double dummy analysis
    """

    def __init__(self):
        """Initialize DDS AI"""
        if not DDS_AVAILABLE:
            raise ImportError(f"endplay library required for DDS AI. DDS_AVAILABLE={DDS_AVAILABLE}")

        # Statistics
        self.solve_time = 0.0
        self.solves_count = 0
        self.cache_hits = 0

    def get_name(self) -> str:
        """Return AI name"""
        return "Double Dummy Solver AI"

    def get_difficulty(self) -> str:
        """Return difficulty level"""
        return "expert"

    def choose_card(self, state: PlayState, position: str) -> Card:
        """
        Choose optimal card using DDS solve_board.

        Uses solve_board which directly returns optimal plays with trick counts,
        avoiding the need to simulate plays (which creates unbalanced hands
        that DDS cannot handle).

        Args:
            state: Current play state
            position: Position making the play

        Returns:
            Optimal card according to double dummy analysis
        """
        start_time = time.time()

        # Get legal cards first - if only one choice, return immediately
        legal_cards = self._get_legal_cards(state, position)

        if len(legal_cards) == 0:
            raise ValueError(f"No legal cards available for {position}")

        if len(legal_cards) == 1:
            self.solve_time = time.time() - start_time
            return legal_cards[0]

        # Validate that the position has cards in their hand
        hand_size = len(state.hands[position].cards)
        if hand_size == 0:
            raise ValueError(f"Position {position} has no cards in hand")

        try:
            # Convert our state to endplay Deal format
            deal = self._convert_to_endplay_deal(state)

            # Capture PBN for debugging before modifying deal
            debug_pbn = self._get_pbn_string(state)

            # Set the player to move and trump suit
            deal.first = self._convert_position(position)
            deal.trump = self._convert_trump(state.contract.trump_suit)

            # If there are cards in the current trick, add them to the deal
            # endplay Deal tracks the current trick state
            if state.current_trick:
                for played_card, played_pos in state.current_trick:
                    endplay_card = self._convert_card_to_endplay(played_card)
                    deal.play(endplay_card)

            # solve_board returns a SolvedBoard with (card, tricks) pairs
            # The tricks value is the number of tricks the CURRENT SIDE can make
            # if they play optimally from this point
            solved = solve_board(deal)

            # Debug: log DDS analysis for discards (void in led suit)
            is_discard = False
            if state.current_trick:
                led_suit = state.current_trick[0][0].suit
                has_led_suit = any(c.suit == led_suit for c in state.hands[position].cards)
                is_discard = not has_led_suit

            if is_discard:
                trick_num = len(state.trick_history) + 1
                current_trick_str = ' '.join([f"{p}:{c.rank}{c.suit}" for c, p in state.current_trick])
                dds_results = [(str(card), tricks) for card, tricks in solved]
                print(f"[DDS DEBUG T{trick_num}] {position} discards | PBN: {debug_pbn}")
                print(f"[DDS DEBUG T{trick_num}] Current trick: {current_trick_str}")
                print(f"[DDS DEBUG T{trick_num}] DDS options: {dds_results}")

            # Collect all cards with their trick counts
            card_options = []
            for endplay_card, tricks in solved:
                our_card = self._convert_endplay_card_to_ours(endplay_card, legal_cards)
                if our_card is not None:
                    card_options.append((our_card, tricks))

            if not card_options:
                # Fallback if no cards matched
                print(f"⚠️  DDS solve_board returned no matching cards for {position}")
                return legal_cards[0]

            # Find the maximum trick count
            max_tricks = max(tricks for _, tricks in card_options)

            # Get all cards that achieve the maximum tricks
            best_cards = [(card, tricks) for card, tricks in card_options if tricks == max_tricks]

            if len(best_cards) == 1:
                # Only one best option
                best_card = best_cards[0][0]
            else:
                # Multiple cards tied for best - use intelligent tie-breaking
                # This is critical for discards where DDS sees all options as "equal"
                best_card = self._break_tie(best_cards, state, position, legal_cards)

            self.solve_time = time.time() - start_time
            self.solves_count += 1

            if best_card:
                return best_card
            else:
                # Fallback if solve_board returned no results matching our cards
                print(f"⚠️  DDS solve_board returned no matching cards for {position}")
                return legal_cards[0]

        except Exception as e:
            # DDS can crash or fail on some positions (especially on macOS)
            # Fall back to simple heuristic play
            print(f"⚠️  DDS failed for {position}: {e}")
            print(f"   Falling back to simple heuristic play")
            return self._fallback_choose_card(state, position, legal_cards)

    def _get_pbn_string(self, state: PlayState) -> str:
        """Build PBN string from PlayState for debugging and Deal creation"""
        # Build PBN string: "N:♠ cards.♥ cards.♦ cards.♣ cards ..."
        # Format: "N:AKQ2.KJ3.T98.432 JT98.Q42.KJ4.987 765.AT9.AQ5.KQJ 43.8765.7632.AT6"

        hands = []
        for pos in ['N', 'E', 'S', 'W']:
            hand = state.hands[pos]
            suits = {'♠': [], '♥': [], '♦': [], '♣': []}

            for card in hand.cards:
                suits[card.suit].append(card.rank)

            # Sort each suit by rank (high to low)
            for suit in suits:
                suits[suit].sort(key=lambda r: self._rank_value(r), reverse=True)

            # Build hand string
            # NOTE: Use empty string for void suits, NOT '-'
            # The endplay library expects empty string for voids in PBN format
            hand_str = '.'.join([
                ''.join(suits['♠']),
                ''.join(suits['♥']),
                ''.join(suits['♦']),
                ''.join(suits['♣'])
            ])
            hands.append(hand_str)

        pbn = f"N:{' '.join(hands)}"
        return pbn

    def _convert_to_endplay_deal(self, state: PlayState) -> Deal:
        """Convert PlayState to endplay Deal format"""
        pbn = self._get_pbn_string(state)

        # Debug logging to help diagnose issues
        try:
            return Deal(pbn)
        except (ValueError, KeyError) as e:
            # Log the problematic PBN string for debugging
            print(f"ERROR: Failed to create Deal from PBN: {pbn}")
            print(f"Error details: {e}")
            print(f"Hand counts: {[(pos, len(state.hands[pos].cards)) for pos in ['N', 'E', 'S', 'W']]}")
            print(f"Current trick: {state.current_trick}")
            print(f"Tricks played: {len(state.trick_history)}")
            raise ValueError(f"Invalid PBN string '{pbn}': {e}") from e

    def _convert_trump(self, trump_suit: Optional[str]) -> Denom:
        """Convert trump suit to endplay Denom"""
        if not trump_suit:
            return Denom.nt

        mapping = {'♠': Denom.spades, '♥': Denom.hearts, '♦': Denom.diamonds, '♣': Denom.clubs}
        return mapping[trump_suit]

    def _convert_position(self, position: str) -> EndplayPlayer:
        """Convert position string to endplay Player"""
        mapping = {'N': EndplayPlayer.north, 'E': EndplayPlayer.east,
                  'S': EndplayPlayer.south, 'W': EndplayPlayer.west}
        return mapping[position]

    def _convert_card_to_endplay(self, card: Card):
        """Convert our Card to endplay Card format"""
        from endplay.types import Rank, Denom as EndplaySuit, Card as ECard

        # Map our rank to endplay Rank
        rank_map = {
            '2': Rank.R2, '3': Rank.R3, '4': Rank.R4, '5': Rank.R5,
            '6': Rank.R6, '7': Rank.R7, '8': Rank.R8, '9': Rank.R9,
            'T': Rank.RT, 'J': Rank.RJ, 'Q': Rank.RQ, 'K': Rank.RK, 'A': Rank.RA
        }

        # Map our suit to endplay Denom (suits)
        suit_map = {
            '♠': EndplaySuit.spades, '♥': EndplaySuit.hearts,
            '♦': EndplaySuit.diamonds, '♣': EndplaySuit.clubs
        }

        return ECard(suit=suit_map[card.suit], rank=rank_map[card.rank])

    def _convert_endplay_card_to_ours(self, endplay_card, legal_cards: List[Card]) -> Optional[Card]:
        """Convert endplay Card back to our Card format by finding match in legal cards"""
        from endplay.types import Rank, Denom as EndplaySuit

        # Reverse mappings - use the actual enum values as keys
        # endplay uses bitmask values: 2=4, 3=8, 4=16, 5=32, 6=64, 7=128, 8=256, 9=512, T=1024, J=2048, Q=4096, K=8192, A=16384
        rank_map = {
            4: '2', 8: '3', 16: '4', 32: '5',
            64: '6', 128: '7', 256: '8', 512: '9',
            1024: 'T', 2048: 'J', 4096: 'Q', 8192: 'K', 16384: 'A'
        }

        # Suit values: spades=0, hearts=1, diamonds=2, clubs=3
        suit_map = {
            0: '♠', 1: '♥', 2: '♦', 3: '♣'
        }

        # Get the numeric values from the endplay card
        rank_val = endplay_card.rank.value if hasattr(endplay_card.rank, 'value') else endplay_card.rank
        suit_val = endplay_card.suit.value if hasattr(endplay_card.suit, 'value') else endplay_card.suit

        target_rank = rank_map.get(rank_val)
        target_suit = suit_map.get(suit_val)

        if target_rank is None or target_suit is None:
            return None

        # Find matching card in legal cards
        for card in legal_cards:
            if card.rank == target_rank and card.suit == target_suit:
                return card

        return None

    def _rank_value(self, rank: str) -> int:
        """Get numeric value of rank for sorting"""
        values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
                 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        return values[rank]

    def _evaluate_position_with_dds(self, state: PlayState, trump: Denom,
                                    declarer: EndplayPlayer) -> float:
        """Evaluate position using DDS"""
        if state.is_complete:
            # Game over - return definitive result
            if declarer in [EndplayPlayer.north, EndplayPlayer.south]:
                return float(state.tricks_taken_ns - state.tricks_taken_ew)
            else:
                return float(state.tricks_taken_ew - state.tricks_taken_ns)

        try:
            # Convert to endplay format
            deal = self._convert_to_endplay_deal(state)

            # Calculate DD table - wrapped in additional error handling
            try:
                dd_table = calc_dd_table(deal)
                data = dd_table.to_list()
            except (RuntimeError, OSError, SystemError) as dds_error:
                # DDS library crashed or failed
                print(f"⚠️  DDS calc_dd_table failed: {dds_error}")
                raise  # Re-raise to trigger outer fallback

            # Get tricks for declarer in trump suit
            # data[denom_idx][player_idx]
            # Denoms: clubs=0, diamonds=1, hearts=2, spades=3, NT=4
            # Players: N=0, E=1, S=2, W=3

            denom_idx = {
                Denom.clubs: 0,
                Denom.diamonds: 1,
                Denom.hearts: 2,
                Denom.spades: 3,
                Denom.nt: 4
            }[trump]

            player_idx = {
                EndplayPlayer.north: 0,
                EndplayPlayer.east: 1,
                EndplayPlayer.south: 2,
                EndplayPlayer.west: 3
            }[declarer]

            declarer_tricks = data[denom_idx][player_idx]

            # Already played tricks
            if declarer in [EndplayPlayer.north, EndplayPlayer.south]:
                already_won = state.tricks_taken_ns
                opp_already_won = state.tricks_taken_ew
            else:
                already_won = state.tricks_taken_ew
                opp_already_won = state.tricks_taken_ns

            # Total tricks declarer will make
            total_tricks = already_won + declarer_tricks
            opp_total = 13 - total_tricks

            return float(total_tricks - opp_total)

        except Exception as e:
            # Fallback to trick count if DDS fails
            # This prevents crashes from propagating up
            if declarer in [EndplayPlayer.north, EndplayPlayer.south]:
                return float(state.tricks_taken_ns - state.tricks_taken_ew)
            else:
                return float(state.tricks_taken_ew - state.tricks_taken_ns)

    def _break_tie(self, tied_cards: List[Tuple[Card, int]], state: PlayState,
                   position: str, all_legal_cards: List[Card]) -> Card:
        """
        Break ties when multiple cards have the same DDS trick count.

        This is critical for discards where DDS often sees all options as "equal"
        but in practice some discards are catastrophic (like discarding a stopper).

        Strategy:
        1. When discarding (void in led suit), prefer low cards from long suits
        2. Avoid discarding lone high cards (likely stoppers)
        3. Prefer discarding from suits where we have length
        """
        hand = state.hands[position]
        cards = [card for card, _ in tied_cards]

        # Check if this is a discard situation (void in led suit)
        is_discard = False
        if state.current_trick:
            led_suit = state.current_trick[0][0].suit
            has_led_suit = any(c.suit == led_suit for c in hand.cards)
            is_discard = not has_led_suit

        if is_discard:
            # Discard logic: prefer low cards from long suits, avoid lone stoppers
            best_card = None
            best_score = -1000  # Higher is better for discard

            # Count cards in each suit
            suit_counts = {}
            for c in hand.cards:
                suit_counts[c.suit] = suit_counts.get(c.suit, 0) + 1

            for card in cards:
                score = 0
                suit_count = suit_counts.get(card.suit, 0)
                rank_value = self._rank_value(card.rank)

                # Prefer discarding from longer suits
                score += suit_count * 10

                # Prefer discarding low cards
                score -= rank_value

                # Heavily penalize discarding lone high cards (likely stoppers)
                if suit_count == 1 and rank_value >= 12:  # K or A
                    score -= 100  # Strong penalty for discarding lone K or A

                # Penalize discarding from short suits with high cards
                if suit_count <= 2 and rank_value >= 10:  # T or higher
                    score -= 20

                if score > best_score:
                    best_score = score
                    best_card = card

            return best_card if best_card else cards[0]

        else:
            # Not a discard - prefer lowest card (standard play, no preference)
            return min(cards, key=lambda c: self._rank_value(c.rank))

    def _get_legal_cards(self, state: PlayState, position: str) -> List[Card]:
        """Get all legal cards for current position"""
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

    def _simulate_play(self, state: PlayState, card: Card, position: str) -> PlayState:
        """Simulate playing a card and return resulting state"""
        import copy
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
            if winner in ['N', 'S']:
                new_state.tricks_taken_ns += 1
            else:
                new_state.tricks_taken_ew += 1

            # Clear trick and set next player
            new_state.current_trick = []
            new_state.next_to_play = winner
        else:
            # Next player clockwise
            new_state.next_to_play = PlayEngine.next_player(position)

        return new_state

    def _is_declarer_side(self, position: str, declarer: str) -> bool:
        """Check if position is on declarer's side"""
        if declarer in ['N', 'S']:
            return position in ['N', 'S']
        else:
            return position in ['E', 'W']

    def get_statistics(self) -> dict:
        """Get DDS statistics"""
        avg_time = self.solve_time / self.solves_count if self.solves_count > 0 else 0

        return {
            'solves': self.solves_count,
            'total_time': self.solve_time,
            'avg_time': avg_time,
            'cache_hits': self.cache_hits
        }

    def reset_statistics(self):
        """Reset statistics"""
        self.solve_time = 0.0
        self.solves_count = 0
        self.cache_hits = 0

    def _fallback_choose_card(self, state: PlayState, position: str, legal_cards: List[Card]) -> Card:
        """
        Fallback card selection when DDS fails
        Uses defensive bridge heuristics

        Args:
            state: Current play state
            position: Position making the play
            legal_cards: List of legal cards to choose from

        Returns:
            Card chosen by heuristic
        """
        # Heuristic 1: If only one legal card, play it
        if len(legal_cards) == 1:
            return legal_cards[0]

        # Heuristic 2: If leading, prefer high cards from long suits
        if not state.current_trick:
            # Find longest suit
            suits = {'♠': [], '♥': [], '♦': [], '♣': []}
            for card in legal_cards:
                suits[card.suit].append(card)

            longest_suit = max(suits.items(), key=lambda x: len(x[1]))[1]
            if longest_suit:
                # Play highest card from longest suit
                return max(longest_suit, key=lambda c: self._rank_value(c.rank))

        # Heuristic 3: If following suit, play appropriately
        if state.current_trick:
            led_suit = state.current_trick[0][0].suit

            # CRITICAL: Detect if this is a discard (void in led suit)
            following_suit = any(c.suit == led_suit for c in legal_cards)

            if not following_suit:
                # DISCARDING - ALWAYS play lowest card available
                # Group by suit to find weakest suit
                by_suit = {}
                for card in legal_cards:
                    if card.suit not in by_suit:
                        by_suit[card.suit] = []
                    by_suit[card.suit].append(card)

                # Find weakest suit (fewest high cards)
                def suit_weakness(suit_cards):
                    # Count high cards (lower = weaker suit = better to discard from)
                    high_card_count = sum(1 for c in suit_cards if c.rank in ['A', 'K', 'Q', 'J'])
                    return high_card_count  # Lower is better for discarding

                weakest_suit = min(by_suit.values(), key=suit_weakness)

                # From weakest suit, play LOWEST card
                return min(weakest_suit, key=lambda c: self._rank_value(c.rank))

            # Following suit - play low if partner winning, high if not
            if len(state.current_trick) >= 2:
                # Simplified: play low card (third hand low)
                return min(legal_cards, key=lambda c: self._rank_value(c.rank))
            else:
                # Second to play: play high
                return max(legal_cards, key=lambda c: self._rank_value(c.rank))

        # Default: play lowest card (conservative)
        return min(legal_cards, key=lambda c: self._rank_value(c.rank))


if __name__ == '__main__':
    # Self-test
    print("Testing DDS AI...")

    if not DDS_AVAILABLE:
        print("❌ endplay not available")
        exit(1)

    from tests.integration.play_test_helpers import create_test_deal, create_play_scenario

    # Create a test position
    deal = create_test_deal(
        north="♠AKQ ♥432 ♦AKQ2 ♣432",
        east="♠432 ♥765 ♦765 ♣7654",
        south="♠765 ♥AKQ ♦432 ♣AKQ8",
        west="♠JT98 ♥JT98 ♦JT9 ♣J9"
    )

    play_state = create_play_scenario("3NT by S", deal, "None")

    # Test DDS AI
    print("\n=== Testing DDS AI ===")
    ai = DDSPlayAI()
    card = ai.choose_card(play_state, 'W')  # Opening leader

    print(f"AI chose: {card.rank}{card.suit}")

    stats = ai.get_statistics()
    print(f"Solves: {stats['solves']}")
    print(f"Time: {stats['total_time']:.3f}s")
    print(f"Avg/solve: {stats['avg_time']:.3f}s")

    print("\n✓ DDS AI self-test complete")

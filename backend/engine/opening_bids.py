from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from engine.ai.bid_explanation import BidExplanation
from typing import Optional, Tuple, Dict, Union

class OpeningBidsModule(ConventionModule):
    """
    Opening bids module for natural 1-level and NT openings.

    NOTE: Preemptive openings (2♦, 2♥, 2♠, 3-level, 4-level) are handled by
    the PreemptConvention module (engine/ai/conventions/preempts.py).
    The PreemptConvention module is checked BEFORE this module in the decision
    engine, so preemptive hands are intercepted before reaching here.

    This module handles:
    - 1NT openings (15-17 HCP, balanced)
    - 2NT openings (20-21 HCP, balanced) - SAYC standard
    - 3NT openings (25-27 HCP, balanced)
    - 2♣ strong artificial openings (22+ total points, or 22-24 balanced which rebids 2NT)
    - 1-level suit openings (13-21 points, 5+ card suit or longer minor)
    """
    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, Union[str, BidExplanation]]]:
        # This module does not need features, but conforms to the interface

        # IMPORTANT: Check GAMBLING 3NT first (solid minor, 10-16 HCP)
        # Check before balanced 3NT to avoid conflicts
        gambling_result = self._check_gambling_3nt(hand)
        if gambling_result:
            return gambling_result

        # IMPORTANT: Check balanced NT openings FIRST before 2♣
        # This ensures proper priority: specific balanced ranges take precedence over general strength

        # Rule for very strong balanced hands (25-27 HCP)
        if hand.is_balanced and 25 <= hand.hcp <= 27:
            explanation = BidExplanation("3NT")
            explanation.set_primary_reason("Very strong balanced hand opens 3NT")
            explanation.add_requirement("HCP", "25-27")
            explanation.add_requirement("Shape", "Balanced")
            explanation.add_actual_value("HCP", str(hand.hcp))
            explanation.add_actual_value("Shape", "Balanced")
            explanation.add_actual_value("Distribution", f"{hand.suit_lengths['♠']}-{hand.suit_lengths['♥']}-{hand.suit_lengths['♦']}-{hand.suit_lengths['♣']}")
            explanation.set_forcing_status("Sign-off")
            explanation.add_alternative("2NT", f"Too strong (have {hand.hcp} HCP, 2NT shows 20-21)")
            explanation.add_alternative("2♣", f"Balanced hands 25-27 HCP use 3NT opening")
            return ("3NT", explanation)

        # Rule for strong balanced hands (20-21 HCP) - Opens 2NT per SAYC
        # Note: 22-24 HCP balanced hands open 2♣ and rebid 2NT
        if hand.is_balanced and 20 <= hand.hcp <= 21:
            explanation = BidExplanation("2NT")
            explanation.set_primary_reason("Strong balanced hand opens 2NT (SAYC: 20-21 HCP)")
            explanation.add_requirement("HCP", "20-21")
            explanation.add_requirement("Shape", "Balanced")
            explanation.add_actual_value("HCP", str(hand.hcp))
            explanation.add_actual_value("Shape", "Balanced")
            explanation.add_actual_value("Distribution", f"{hand.suit_lengths['♠']}-{hand.suit_lengths['♥']}-{hand.suit_lengths['♦']}-{hand.suit_lengths['♣']}")
            explanation.set_forcing_status("Forcing to game")
            explanation.add_alternative("1NT", f"Too strong (have {hand.hcp} HCP, 1NT shows 15-17)")
            explanation.add_alternative("2♣", f"With 22-24 HCP balanced, open 2♣ then rebid 2NT")
            return ("2NT", explanation)

        # Rule for standard balanced 1NT opening (15-17 HCP)
        if 15 <= hand.hcp <= 17 and hand.is_balanced:
            explanation = BidExplanation("1NT")
            explanation.set_primary_reason("Balanced hand with 15-17 HCP opens 1NT")
            explanation.add_requirement("HCP", "15-17")
            explanation.add_requirement("Shape", "Balanced (no singleton/void, at most 1 doubleton)")
            explanation.add_actual_value("HCP", str(hand.hcp))
            explanation.add_actual_value("Distribution", f"{hand.suit_lengths['♠']}-{hand.suit_lengths['♥']}-{hand.suit_lengths['♦']}-{hand.suit_lengths['♣']}")
            explanation.set_forcing_status("Sign-off (partner may pass)")
            explanation.set_sayc_rule("1nt_opening")
            explanation.add_alternative("1-level suit", f"Hand is balanced, 1NT more descriptive")
            return ("1NT", explanation)

        # Rule for very strong hands (22+ total points) - Only for non-balanced or extreme hands
        # Note: Balanced hands are handled above with specific NT bids
        if hand.total_points >= 22:
            explanation = BidExplanation("2♣")
            explanation.set_primary_reason("Very strong hand opens 2♣ (artificial, game-forcing)")
            explanation.add_requirement("Total Points", "22+")
            explanation.add_actual_value("Total Points", str(hand.total_points))
            explanation.add_actual_value("HCP", str(hand.hcp))
            explanation.add_actual_value("Distribution Points", str(hand.dist_points))
            explanation.set_forcing_status("Game-forcing")
            explanation.set_convention("Strong 2♣ - SAYC")

            # Show longest suit as context
            longest_suit = max(hand.suit_lengths, key=hand.suit_lengths.get)
            explanation.add_actual_value("Longest suit", f"{longest_suit} ({hand.suit_lengths[longest_suit]} cards)")
            return ("2♣", explanation)

        # Rule for standard 1-level openings (13-21 points)
        if hand.total_points >= 13:
            if max(hand.suit_lengths.values()) >= 5: # Has a 5+ card suit
                # Prioritize majors
                if hand.suit_lengths['♥'] >= 5 and hand.suit_lengths['♥'] >= hand.suit_lengths['♠']:
                    explanation = BidExplanation("1♥")
                    explanation.set_primary_reason("Open longest suit - hearts (5+ cards)")
                    explanation.add_requirement("Opening Points", "13+")
                    explanation.add_requirement("Heart Length", "5+")
                    explanation.add_actual_value("Total Points", str(hand.total_points))
                    explanation.add_actual_value("Hearts", f"{hand.suit_lengths['♥']} cards, {hand.suit_hcp['♥']} HCP")
                    if hand.suit_lengths['♠'] >= 5:
                        explanation.add_alternative("1♠", f"Hearts are longer or equal ({hand.suit_lengths['♥']} vs {hand.suit_lengths['♠']})")
                    explanation.set_forcing_status("Forcing for 1 round")
                    return ("1♥", explanation)

                if hand.suit_lengths['♠'] >= 5:
                    explanation = BidExplanation("1♠")
                    explanation.set_primary_reason("Open longest suit - spades (5+ cards)")
                    explanation.add_requirement("Opening Points", "13+")
                    explanation.add_requirement("Spade Length", "5+")
                    explanation.add_actual_value("Total Points", str(hand.total_points))
                    explanation.add_actual_value("Spades", f"{hand.suit_lengths['♠']} cards, {hand.suit_hcp['♠']} HCP")
                    explanation.set_forcing_status("Forcing for 1 round")
                    return ("1♠", explanation)

                # Then minors
                if hand.suit_lengths['♦'] >= 5 and hand.suit_lengths['♦'] >= hand.suit_lengths['♣']:
                    explanation = BidExplanation("1♦")
                    explanation.set_primary_reason("Open longest minor - diamonds (5+ cards)")
                    explanation.add_requirement("Opening Points", "13+")
                    explanation.add_requirement("Diamond Length", "5+")
                    explanation.add_actual_value("Total Points", str(hand.total_points))
                    explanation.add_actual_value("Diamonds", f"{hand.suit_lengths['♦']} cards, {hand.suit_hcp['♦']} HCP")
                    if hand.suit_lengths['♣'] >= 5:
                        explanation.add_alternative("1♣", f"Diamonds are longer or equal ({hand.suit_lengths['♦']} vs {hand.suit_lengths['♣']})")
                    explanation.set_forcing_status("Forcing for 1 round")
                    return ("1♦", explanation)

                if hand.suit_lengths['♣'] >= 5:
                    explanation = BidExplanation("1♣")
                    explanation.set_primary_reason("Open longest minor - clubs (5+ cards)")
                    explanation.add_requirement("Opening Points", "13+")
                    explanation.add_requirement("Club Length", "5+")
                    explanation.add_actual_value("Total Points", str(hand.total_points))
                    explanation.add_actual_value("Clubs", f"{hand.suit_lengths['♣']} cards, {hand.suit_hcp['♣']} HCP")
                    explanation.set_forcing_status("Forcing for 1 round")
                    return ("1♣", explanation)

            # No 5-card suit, open longer minor
            if hand.suit_lengths['♦'] > hand.suit_lengths['♣']:
                explanation = BidExplanation("1♦")
                explanation.set_primary_reason("No 5-card suit - open longer minor (diamonds)")
                explanation.add_requirement("Opening Points", "13+")
                explanation.add_actual_value("Total Points", str(hand.total_points))
                explanation.add_actual_value("Diamonds", f"{hand.suit_lengths['♦']} cards")
                explanation.add_actual_value("Clubs", f"{hand.suit_lengths['♣']} cards")
                explanation.add_actual_value("Distribution", f"{hand.suit_lengths['♠']}-{hand.suit_lengths['♥']}-{hand.suit_lengths['♦']}-{hand.suit_lengths['♣']}")
                explanation.add_alternative("1♣", f"Diamonds longer ({hand.suit_lengths['♦']} vs {hand.suit_lengths['♣']})")
                explanation.set_forcing_status("Forcing for 1 round")
                return ("1♦", explanation)
            else:
                # Equal length minors - use better tie-breaking logic
                club_len = hand.suit_lengths['♣']
                diamond_len = hand.suit_lengths['♦']

                if club_len == diamond_len and club_len == 4:
                    # 4-4 minors: Consider strength and quality
                    # SAYC guideline: With 4-4 minors, prefer 1♦ with:
                    # - Stronger diamonds (better honors)
                    # - Weak clubs (poor quality)
                    # - 4-4-3-2 shape (rebid issues with 1♣)

                    club_hcp = hand.suit_hcp['♣']
                    diamond_hcp = hand.suit_hcp['♦']

                    # If diamonds significantly stronger (2+ HCP difference), open 1♦
                    if diamond_hcp >= club_hcp + 2:
                        explanation = BidExplanation("1♦")
                        explanation.set_primary_reason("4-4 minors - open stronger minor (diamonds)")
                        explanation.add_requirement("Opening Points", "13+")
                        explanation.add_actual_value("Total Points", str(hand.total_points))
                        explanation.add_actual_value("Diamonds", f"4 cards, {diamond_hcp} HCP")
                        explanation.add_actual_value("Clubs", f"4 cards, {club_hcp} HCP")
                        explanation.add_actual_value("Distribution", f"{hand.suit_lengths['♠']}-{hand.suit_lengths['♥']}-{hand.suit_lengths['♦']}-{hand.suit_lengths['♣']}")
                        explanation.add_alternative("1♣", f"Diamonds stronger ({diamond_hcp} vs {club_hcp} HCP)")
                        explanation.set_forcing_status("Forcing for 1 round")
                        return ("1♦", explanation)

                # Default: open 1♣ with equal or clubs longer
                explanation = BidExplanation("1♣")
                explanation.set_primary_reason("No 5-card suit - open longer or equal minor (clubs)")
                explanation.add_requirement("Opening Points", "13+")
                explanation.add_actual_value("Total Points", str(hand.total_points))
                explanation.add_actual_value("Clubs", f"{hand.suit_lengths['♣']} cards")
                explanation.add_actual_value("Diamonds", f"{hand.suit_lengths['♦']} cards")
                explanation.add_actual_value("Distribution", f"{hand.suit_lengths['♠']}-{hand.suit_lengths['♥']}-{hand.suit_lengths['♦']}-{hand.suit_lengths['♣']}")
                if hand.suit_lengths['♦'] == hand.suit_lengths['♣']:
                    explanation.add_alternative("1♦", f"Equal length ({hand.suit_lengths['♣']} each) - default to clubs")
                explanation.set_forcing_status("Forcing for 1 round")
                return ("1♣", explanation)

        # Not enough to open
        explanation = BidExplanation("Pass")
        explanation.set_primary_reason("Not enough strength to open")
        explanation.add_requirement("Opening Points", "13+")
        explanation.add_actual_value("Total Points", str(hand.total_points))
        explanation.add_actual_value("HCP", str(hand.hcp))
        return ("Pass", explanation)

    def _check_gambling_3nt(self, hand: Hand) -> Optional[Tuple[str, BidExplanation]]:
        """
        Check for Gambling 3NT opening.

        Requirements (ACBL/SAYC):
        - Solid 7-8 card minor suit (must run without losing a trick)
        - Typically AKQxxxx or better in the minor
        - 10-16 HCP (if stronger, open 2♣ or 3NT balanced)
        - Little outside strength (asking partner to declare 3NT)
        - No void, no singleton Ace/King (too distributional)

        Asks partner to bid 3NT (gambling that their high cards fill the gaps).
        """
        # Must have 7-8 card minor
        club_len = hand.suit_lengths.get('♣', 0)
        diamond_len = hand.suit_lengths.get('♦', 0)

        long_minor = None
        minor_length = 0

        if club_len >= 7:
            long_minor = '♣'
            minor_length = club_len
        elif diamond_len >= 7:
            long_minor = '♦'
            minor_length = diamond_len
        else:
            return None  # Need 7+ card minor

        # Check HCP range (10-16)
        if not (10 <= hand.hcp <= 16):
            return None

        # Check for solid suit (must have AKQ at minimum)
        # Solid = running tricks without losing
        minor_hcp = hand.suit_hcp.get(long_minor, 0)

        # With 7 cards, need at least AKQ (9 HCP) to be solid
        # With 8 cards, AKQ still required
        if minor_hcp < 9:  # Less than AKQ
            return None

        # Count top honors in the minor (A=4, K=3, Q=2)
        # Need to verify we have at least AKQ
        # Simplified: if we have 9+ HCP in a 7+ card suit, likely solid
        # More precise: need top 3 honors

        # Check for problematic distribution
        # No voids (too distributional)
        if 0 in hand.suit_lengths.values():
            return None

        # No singleton Ace or King in side suits (too much side strength)
        for suit in ['♠', '♥', '♦', '♣']:
            if suit != long_minor:
                if hand.suit_lengths[suit] == 1 and hand.suit_hcp[suit] >= 3:
                    return None  # Singleton Ace/King is too much

        # Gambling 3NT should have weak sides (not too many HCP outside minor)
        outside_hcp = hand.hcp - minor_hcp
        if outside_hcp > 4:  # More than a Queen outside
            return None

        # All checks passed - bid Gambling 3NT!
        explanation = BidExplanation("3NT")
        explanation.set_primary_reason(f"Gambling 3NT with solid {minor_length}-card {long_minor} suit")
        explanation.add_requirement("Minor Length", "7-8 cards")
        explanation.add_requirement("Minor Quality", "Solid (AKQ+)")
        explanation.add_requirement("HCP", "10-16")
        explanation.add_requirement("Outside Strength", "Minimal (≤ Queen)")
        explanation.add_actual_value("HCP", str(hand.hcp))
        explanation.add_actual_value(f"{long_minor} Length", f"{minor_length} cards")
        explanation.add_actual_value(f"{long_minor} HCP", str(minor_hcp))
        explanation.add_actual_value("Outside HCP", str(outside_hcp))
        explanation.add_actual_value("Distribution", f"{hand.suit_lengths['♠']}-{hand.suit_lengths['♥']}-{hand.suit_lengths['♦']}-{hand.suit_lengths['♣']}")
        explanation.set_convention("Gambling 3NT")
        explanation.set_forcing_status("Partner expected to pass or correct")
        explanation.add_alternative("3♣/3♦", "Gambling 3NT is more descriptive with solid suit")
        explanation.add_alternative("1♣/1♦", "Hand qualifies for special Gambling 3NT treatment")

        return ("3NT", explanation)

# ADR-0002 Phase 1: Auto-register this module on import
from engine.ai.module_registry import ModuleRegistry
ModuleRegistry.register("opening_bids", OpeningBidsModule())


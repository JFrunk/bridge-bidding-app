"""
Signal Integrity Report (SIR) - Measuring AI "Partner Trust"

This module provides the ultimate diagnostic for DDS play quality, measuring
"Information Leakage" and "Deductive Consistency" rather than just tricks won.

Architecture:
- Operates on the principle of Inference Mapping
- If AI plays J from QJ, partner infers Q is held (lowest of equals)
- Validates that the AI's card choices allow accurate partner deduction

Key Metrics:
1. Deduction Confidence - Can partner place the honors from AI plays?
2. Signal Noise Rate - How often does AI play "random" cards from equiv sets?
3. Heuristic Adherence - Per-heuristic compliance rate
4. Positional Transparency - Accuracy of honor placement after N tricks

Usage:
    from engine.play.ai.signal_integrity_report import SignalIntegrityAuditor

    auditor = SignalIntegrityAuditor()

    # Log each DDS play decision
    auditor.log_decision(
        equivalence_set=[Card('Q', '♠'), Card('J', '♠')],
        selected_card=Card('J', '♠'),
        context=PlayContext.THIRD_HAND_FOLLOW,
        heuristic_expected='lowest_of_equals',
        actual_heuristic='bottom_of_sequence'
    )

    # Generate report
    report = auditor.generate_report()
    print(f"Deduction Confidence: {report['integrity_score']:.1f}%")
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import json
import time

# Import Card type
from engine.hand import Card


class SignalContext(Enum):
    """Context for signal integrity analysis"""
    OPENING_LEAD = "opening_lead"
    MIDHAND_LEAD = "midhand_lead"
    SECOND_HAND_FOLLOW = "second_hand_follow"
    THIRD_HAND_FOLLOW = "third_hand_follow"
    FOURTH_HAND_FOLLOW = "fourth_hand_follow"
    DISCARD_FIRST = "discard_first"
    DISCARD_SUBSEQUENT = "discard_subsequent"


class HeuristicType(Enum):
    """Standard bridge heuristics"""
    TOP_OF_SEQUENCE = "top_of_sequence"
    LOWEST_OF_EQUALS = "lowest_of_equals"
    SECOND_HAND_LOW = "second_hand_low"
    THIRD_HAND_HIGH = "third_hand_high"
    WIN_CHEAPLY = "win_cheaply"
    ATTITUDE_SIGNAL = "attitude_signal"
    COUNT_SIGNAL = "count_signal"
    CONSERVATION = "conservation"
    UNBLOCKING = "unblocking"


@dataclass
class SignalDecision:
    """Record of a single signal-relevant decision"""
    hand_id: str
    trick_number: int
    equivalence_set: List[Card]
    selected_card: Card
    context: str
    expected_heuristic: str
    actual_heuristic: str
    is_compliant: bool
    reason: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class FalsificationEvent:
    """Record of a heuristic violation"""
    hand_id: str
    trick_number: int
    error_type: str  # MISLEADING_SIGNAL, BROKEN_SEQUENCE, RANDOM_CHOICE, etc.
    detail: str
    equivalence_set: List[str]
    selected: str
    expected: str


class SignalIntegrityAuditor:
    """
    Audits AI play decisions for signal integrity.

    Tracks every decision where the DDS equivalence set size > 1,
    validates against standard heuristics, and produces integrity metrics.
    """

    # Heuristic rules by context
    HEURISTIC_RULES = {
        SignalContext.OPENING_LEAD.value: HeuristicType.TOP_OF_SEQUENCE,
        SignalContext.MIDHAND_LEAD.value: HeuristicType.TOP_OF_SEQUENCE,
        SignalContext.SECOND_HAND_FOLLOW.value: HeuristicType.SECOND_HAND_LOW,
        SignalContext.THIRD_HAND_FOLLOW.value: HeuristicType.THIRD_HAND_HIGH,
        SignalContext.FOURTH_HAND_FOLLOW.value: HeuristicType.WIN_CHEAPLY,
        SignalContext.DISCARD_FIRST.value: HeuristicType.ATTITUDE_SIGNAL,
        SignalContext.DISCARD_SUBSEQUENT.value: HeuristicType.COUNT_SIGNAL,
    }

    # Rank values for comparison
    RANK_VALUES = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
        'T': 10, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
    }

    def __init__(self):
        """Initialize the auditor"""
        self.decisions: List[SignalDecision] = []
        self.falsifications: List[FalsificationEvent] = []
        self.heuristic_stats: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"total": 0, "compliant": 0}
        )
        self.current_hand_id: str = "unknown"
        self.current_trick: int = 0

    def set_context(self, hand_id: str, trick_number: int):
        """Set current hand and trick for logging"""
        self.current_hand_id = hand_id
        self.current_trick = trick_number

    def log_decision(
        self,
        equivalence_set: List[Card],
        selected_card: Card,
        context: str,
        actual_heuristic: str,
        reason: str = "",
        hand_id: Optional[str] = None,
        trick_number: Optional[int] = None
    ):
        """
        Log a signal-relevant decision for audit.

        Args:
            equivalence_set: Cards DDS considered equivalent
            selected_card: Card actually played
            context: Play context (opening_lead, third_hand_follow, etc.)
            actual_heuristic: Heuristic used by TacticalPlayFilter
            reason: Explanation provided by filter
            hand_id: Optional hand identifier
            trick_number: Optional trick number
        """
        if len(equivalence_set) <= 1:
            return  # No signal decision when only one card

        hid = hand_id or self.current_hand_id
        trick = trick_number if trick_number is not None else self.current_trick

        # Determine expected heuristic
        expected = self._get_expected_heuristic(context, equivalence_set)

        # Check compliance
        is_compliant = self._check_compliance(
            equivalence_set, selected_card, context, expected
        )

        decision = SignalDecision(
            hand_id=hid,
            trick_number=trick,
            equivalence_set=equivalence_set,
            selected_card=selected_card,
            context=context,
            expected_heuristic=expected,
            actual_heuristic=actual_heuristic,
            is_compliant=is_compliant,
            reason=reason
        )

        self.decisions.append(decision)

        # Update heuristic stats
        self.heuristic_stats[expected]["total"] += 1
        if is_compliant:
            self.heuristic_stats[expected]["compliant"] += 1
        else:
            # Log falsification event
            self._log_falsification(decision, expected)

    def _get_expected_heuristic(
        self,
        context: str,
        equivalence_set: List[Card]
    ) -> str:
        """Determine the expected heuristic for a context"""
        # Check if it's a sequence situation
        if self._is_honor_sequence(equivalence_set):
            if context in [SignalContext.OPENING_LEAD.value, SignalContext.MIDHAND_LEAD.value]:
                return HeuristicType.TOP_OF_SEQUENCE.value
            else:
                return HeuristicType.LOWEST_OF_EQUALS.value

        # Default rules
        rule = self.HEURISTIC_RULES.get(context)
        if rule:
            return rule.value

        return HeuristicType.LOWEST_OF_EQUALS.value

    def _check_compliance(
        self,
        equivalence_set: List[Card],
        selected_card: Card,
        context: str,
        expected_heuristic: str
    ) -> bool:
        """Check if the selected card complies with the expected heuristic"""
        if not equivalence_set:
            return True

        # Get rank values
        ranks = [self._rank_value(c.rank) for c in equivalence_set]
        selected_rank = self._rank_value(selected_card.rank)

        min_rank = min(ranks)
        max_rank = max(ranks)

        # Check based on heuristic
        if expected_heuristic == HeuristicType.TOP_OF_SEQUENCE.value:
            # Should play highest
            return selected_rank == max_rank

        elif expected_heuristic == HeuristicType.LOWEST_OF_EQUALS.value:
            # Should play lowest
            return selected_rank == min_rank

        elif expected_heuristic == HeuristicType.SECOND_HAND_LOW.value:
            # Should play lowest
            return selected_rank == min_rank

        elif expected_heuristic == HeuristicType.THIRD_HAND_HIGH.value:
            # Usually highest, but lowest if sequence
            if self._is_honor_sequence(equivalence_set):
                return selected_rank == min_rank
            return selected_rank == max_rank

        elif expected_heuristic == HeuristicType.WIN_CHEAPLY.value:
            # Should play lowest winner (which would be lowest in equiv set)
            return selected_rank == min_rank

        elif expected_heuristic in [HeuristicType.ATTITUDE_SIGNAL.value,
                                    HeuristicType.COUNT_SIGNAL.value]:
            # Signals are context-dependent, any card from equiv set is valid
            return True

        elif expected_heuristic == HeuristicType.CONSERVATION.value:
            # Should play lowest
            return selected_rank == min_rank

        elif expected_heuristic == HeuristicType.UNBLOCKING.value:
            # Should play highest (the blocking card)
            return selected_rank == max_rank

        return True  # Default to compliant

    def _log_falsification(self, decision: SignalDecision, expected: str):
        """Log a falsification event"""
        equiv_strs = [f"{c.rank}{c.suit}" for c in decision.equivalence_set]
        selected_str = f"{decision.selected_card.rank}{decision.selected_card.suit}"

        # Determine expected card
        ranks = [(self._rank_value(c.rank), c) for c in decision.equivalence_set]
        if expected in [HeuristicType.TOP_OF_SEQUENCE.value]:
            expected_card = max(ranks, key=lambda x: x[0])[1]
        else:
            expected_card = min(ranks, key=lambda x: x[0])[1]

        expected_str = f"{expected_card.rank}{expected_card.suit}"

        error_type = "MISLEADING_SIGNAL"
        if expected == HeuristicType.TOP_OF_SEQUENCE.value:
            error_type = "BROKEN_SEQUENCE"
        elif expected == HeuristicType.SECOND_HAND_LOW.value:
            error_type = "PREMATURE_COMMIT"

        event = FalsificationEvent(
            hand_id=decision.hand_id,
            trick_number=decision.trick_number,
            error_type=error_type,
            detail=f"AI played {selected_str} from {equiv_strs}; expected {expected_str} ({expected}).",
            equivalence_set=equiv_strs,
            selected=selected_str,
            expected=expected_str
        )

        self.falsifications.append(event)

    def _rank_value(self, rank: str) -> int:
        """Get numeric value of rank"""
        return self.RANK_VALUES.get(rank, 0)

    def _is_honor_sequence(self, cards: List[Card]) -> bool:
        """Check if cards form a touching honor sequence"""
        if len(cards) < 2:
            return False

        # All same suit
        suits = set(c.suit for c in cards)
        if len(suits) > 1:
            return False

        ranks = sorted([self._rank_value(c.rank) for c in cards], reverse=True)

        # Check consecutive
        for i in range(len(ranks) - 1):
            if ranks[i] - ranks[i + 1] != 1:
                return False

        # Must include honors (J or higher)
        return any(r >= 11 for r in ranks)

    def generate_report(self) -> Dict[str, Any]:
        """
        Generate the Signal Integrity Report.

        Returns:
            Dict with integrity metrics and falsification events
        """
        total_decisions = len(self.decisions)
        compliant_decisions = sum(1 for d in self.decisions if d.is_compliant)

        # Calculate integrity score
        integrity_score = (
            (compliant_decisions / total_decisions * 100)
            if total_decisions > 0 else 100.0
        )

        # Calculate noise rate
        noise_rate = (
            (len(self.falsifications) / total_decisions * 100)
            if total_decisions > 0 else 0.0
        )

        # Per-heuristic adherence
        heuristic_adherence = {}
        for heuristic, stats in self.heuristic_stats.items():
            if stats["total"] > 0:
                heuristic_adherence[heuristic] = round(
                    stats["compliant"] / stats["total"], 2
                )

        # Format falsification events
        falsification_events = [
            {
                "hand_id": f.hand_id,
                "trick": f.trick_number,
                "error": f.error_type,
                "detail": f.detail
            }
            for f in self.falsifications[:20]  # Limit to first 20
        ]

        return {
            "integrity_score": round(integrity_score, 2),
            "metrics": {
                "deduction_confidence": round(integrity_score / 100, 2),
                "signal_noise_rate": round(noise_rate / 100, 2),
                "total_signaling_opportunities": total_decisions,
                "compliant_signals": compliant_decisions,
                "heuristic_adherence": heuristic_adherence
            },
            "rating": self._get_rating(integrity_score),
            "falsification_events": falsification_events,
            "summary": self._generate_summary(integrity_score, heuristic_adherence)
        }

    def _get_rating(self, score: float) -> str:
        """Get human-readable rating"""
        if score >= 95:
            return "Expert"
        elif score >= 85:
            return "Competent"
        elif score >= 70:
            return "Developing"
        else:
            return "Chaotic"

    def _generate_summary(
        self,
        score: float,
        adherence: Dict[str, float]
    ) -> str:
        """Generate human-readable summary"""
        rating = self._get_rating(score)

        if rating == "Expert":
            return (
                f"Signal Integrity: {score:.1f}% ({rating}). "
                "Partner can trust every card played. Honor deduction is reliable."
            )
        elif rating == "Competent":
            # Find weakest heuristic
            weakest = min(adherence.items(), key=lambda x: x[1]) if adherence else None
            weak_str = f"Weakest: {weakest[0]} ({weakest[1]*100:.0f}%)" if weakest else ""
            return (
                f"Signal Integrity: {score:.1f}% ({rating}). "
                f"Follows basic conventions with minor inconsistencies. {weak_str}"
            )
        else:
            return (
                f"Signal Integrity: {score:.1f}% ({rating}). "
                "Signal choices appear random. Partner cannot reliably place honors."
            )

    def reset(self):
        """Reset all statistics"""
        self.decisions.clear()
        self.falsifications.clear()
        self.heuristic_stats.clear()
        self.current_hand_id = "unknown"
        self.current_trick = 0

    def to_json(self) -> str:
        """Export report as JSON"""
        return json.dumps(self.generate_report(), indent=2)


class SignalIntegrityFilter:
    """
    Wraps TacticalPlayFilter with integrity auditing.

    Use this as a drop-in replacement for TacticalPlayFilter when you want
    to collect signal integrity metrics during play.
    """

    def __init__(self, tactical_filter=None):
        """
        Initialize with optional TacticalPlayFilter.

        Args:
            tactical_filter: Existing TacticalPlayFilter instance, or None to create new
        """
        from engine.play.ai.play_signal_overlay import TacticalPlayFilter
        self.filter = tactical_filter or TacticalPlayFilter()
        self.auditor = SignalIntegrityAuditor()

    def select_tactical_card(
        self,
        equivalence_set: List[Card],
        game_state: Any,
        position: str,
        hand: Any,
        trump_suit: Optional[str] = None,
        hand_id: Optional[str] = None,
        trick_number: Optional[int] = None,
        **kwargs
    ):
        """
        Select card and log for integrity audit.

        This wraps TacticalPlayFilter.select_tactical_card() and logs
        the decision for signal integrity analysis.
        """
        result = self.filter.select_tactical_card(
            equivalence_set, game_state, position, hand, trump_suit, **kwargs
        )

        # Log for audit
        self.auditor.log_decision(
            equivalence_set=equivalence_set,
            selected_card=result.card,
            context=result.context.value,
            actual_heuristic=result.heuristic.value,
            reason=result.reason,
            hand_id=hand_id,
            trick_number=trick_number
        )

        return result

    def get_report(self) -> Dict[str, Any]:
        """Get signal integrity report"""
        return self.auditor.generate_report()

    def reset_audit(self):
        """Reset audit statistics"""
        self.auditor.reset()


# Self-test
if __name__ == '__main__':
    print("Signal Integrity Report - Self Test")
    print("=" * 50)

    auditor = SignalIntegrityAuditor()

    # Simulate some decisions

    # Good: Top of sequence lead
    auditor.log_decision(
        equivalence_set=[Card('K', '♠'), Card('Q', '♠'), Card('J', '♠')],
        selected_card=Card('K', '♠'),
        context="opening_lead",
        actual_heuristic="top_of_sequence",
        reason="Top of sequence lead",
        hand_id="test1",
        trick_number=1
    )

    # Good: Lowest of equals follow
    auditor.log_decision(
        equivalence_set=[Card('Q', '♥'), Card('J', '♥')],
        selected_card=Card('J', '♥'),
        context="third_hand_follow",
        actual_heuristic="bottom_of_sequence",
        reason="Bottom of sequence",
        hand_id="test1",
        trick_number=2
    )

    # Bad: Should have led top of sequence
    auditor.log_decision(
        equivalence_set=[Card('Q', '♦'), Card('J', '♦'), Card('T', '♦')],
        selected_card=Card('J', '♦'),  # Wrong - should be Q
        context="opening_lead",
        actual_heuristic="random",
        reason="Random choice",
        hand_id="test2",
        trick_number=1
    )

    # Good: Second hand low
    auditor.log_decision(
        equivalence_set=[Card('K', '♣'), Card('5', '♣'), Card('3', '♣')],
        selected_card=Card('3', '♣'),
        context="second_hand_follow",
        actual_heuristic="min_of_equals",
        reason="2nd hand low",
        hand_id="test2",
        trick_number=2
    )

    # Generate report
    report = auditor.generate_report()

    print(f"\nIntegrity Score: {report['integrity_score']}%")
    print(f"Rating: {report['rating']}")
    print(f"\nMetrics:")
    print(f"  Deduction Confidence: {report['metrics']['deduction_confidence']}")
    print(f"  Signal Noise Rate: {report['metrics']['signal_noise_rate']}")
    print(f"\nHeuristic Adherence:")
    for h, rate in report['metrics']['heuristic_adherence'].items():
        print(f"  {h}: {rate*100:.0f}%")

    print(f"\nFalsification Events: {len(report['falsification_events'])}")
    for event in report['falsification_events']:
        print(f"  [{event['hand_id']}] T{event['trick']}: {event['error']}")
        print(f"    {event['detail']}")

    print(f"\nSummary: {report['summary']}")

    print("\n✓ Signal Integrity Report self-test complete")

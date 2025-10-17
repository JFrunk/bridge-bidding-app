"""
Structured explanation system for bridge bidding decisions.

This module provides a rich explanation framework that captures the actual
decision-making logic used by the AI, making explanations directly traceable
to the code that generated them.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ExplanationLevel(Enum):
    """Different levels of explanation detail."""
    SIMPLE = "simple"              # Minimal, one-line explanation
    CONVENTION_ONLY = "convention_only"  # Convention parameters only, no actual hand values (for partner/opponent bids)
    DETAILED = "detailed"          # Rich explanation with hand values and alternatives
    EXPERT = "expert"              # Includes SAYC rules, detailed reasoning, all checks


@dataclass
class RuleCheck:
    """Represents a single rule evaluation in the decision process."""
    condition: str  # Human-readable condition (e.g., "Hand is balanced")
    result: bool    # Whether condition was met
    value: str = "" # Actual value if applicable (e.g., "HCP: 16")


@dataclass
class AlternativeBid:
    """Represents a bid that was considered but not chosen."""
    bid: str
    reason_rejected: str


class BidExplanation:
    """
    Rich explanation object that captures the complete reasoning behind a bid.

    This class stores structured data about WHY a bid was chosen, including:
    - The specific hand characteristics that triggered the bid
    - Rules that were evaluated (both passed and failed)
    - Alternative bids that were considered and rejected
    - References to SAYC rules or conventions used
    """

    def __init__(self, bid: str):
        self.bid = bid
        self.primary_reason: str = ""
        self.hand_requirements: Dict[str, str] = {}
        self.actual_hand_values: Dict[str, str] = {}
        self.rule_checks: List[RuleCheck] = []
        self.alternatives_considered: List[AlternativeBid] = []
        self.convention_reference: Optional[str] = None
        self.forcing_status: Optional[str] = None  # "Forcing", "Invitational", "Sign-off", etc.
        self.sayc_rule_id: Optional[str] = None  # Reference to SAYC rule

    def add_requirement(self, key: str, value: str) -> 'BidExplanation':
        """Add a requirement that this bid needs (e.g., 'HCP': '15-17')."""
        self.hand_requirements[key] = value
        return self

    def add_actual_value(self, key: str, value: str) -> 'BidExplanation':
        """Add actual hand value (e.g., 'HCP': '16')."""
        self.actual_hand_values[key] = value
        return self

    def add_check(self, condition: str, result: bool, value: str = "") -> 'BidExplanation':
        """Add a rule check to the reasoning chain."""
        self.rule_checks.append(RuleCheck(condition, result, value))
        return self

    def add_alternative(self, bid: str, reason_rejected: str) -> 'BidExplanation':
        """Add an alternative bid that was considered but rejected."""
        self.alternatives_considered.append(AlternativeBid(bid, reason_rejected))
        return self

    def set_primary_reason(self, reason: str) -> 'BidExplanation':
        """Set the main explanation text."""
        self.primary_reason = reason
        return self

    def set_forcing_status(self, status: str) -> 'BidExplanation':
        """Set whether bid is forcing, invitational, etc."""
        self.forcing_status = status
        return self

    def set_convention(self, convention: str) -> 'BidExplanation':
        """Set the convention or rule system used."""
        self.convention_reference = convention
        return self

    def set_sayc_rule(self, rule_id: str) -> 'BidExplanation':
        """Set the SAYC rule reference for this bid."""
        self.sayc_rule_id = rule_id
        return self

    def to_simple_string(self) -> str:
        """
        Generate a simple, concise explanation (backward compatible).
        This is similar to the old string explanations.
        """
        parts = [self.primary_reason]

        if self.forcing_status:
            parts.append(f"({self.forcing_status})")

        return " ".join(parts)

    def to_convention_only_string(self) -> str:
        """
        Generate explanation showing only convention parameters/requirements,
        without revealing actual hand values. Used for partner/opponent bids
        to avoid giving unfair information advantage.
        """
        lines = []

        # Primary reason
        lines.append(f"📋 {self.primary_reason}")

        # Show hand requirements (convention parameters) only
        if self.hand_requirements:
            lines.append("\n📐 Requirements for this bid:")
            for key, value in self.hand_requirements.items():
                lines.append(f"  • {key}: {value}")

        # Forcing status
        if self.forcing_status:
            lines.append(f"\n⚡ Status: {self.forcing_status}")

        # Convention reference
        if self.convention_reference:
            lines.append(f"\n📖 Convention: {self.convention_reference}")

        return "\n".join(lines)

    def to_detailed_string(self) -> str:
        """
        Generate a detailed, educational explanation showing the reasoning.
        """
        lines = []

        # Primary reason
        lines.append(f"📋 {self.primary_reason}")

        # Hand values that matter
        if self.actual_hand_values:
            lines.append("\n🃏 Your hand:")
            for key, value in self.actual_hand_values.items():
                requirement = self.hand_requirements.get(key, "")
                if requirement:
                    lines.append(f"  • {key}: {value} (requires {requirement})")
                else:
                    lines.append(f"  • {key}: {value}")

        # Alternative bids considered
        if self.alternatives_considered:
            lines.append("\n🤔 Other bids considered:")
            for alt in self.alternatives_considered:
                lines.append(f"  • {alt.bid}: {alt.reason_rejected}")

        # Forcing status
        if self.forcing_status:
            lines.append(f"\n⚡ Status: {self.forcing_status}")

        # Convention reference
        if self.convention_reference:
            lines.append(f"\n📖 Convention: {self.convention_reference}")

        return "\n".join(lines)

    def to_expert_string(self) -> str:
        """
        Generate expert-level explanation with SAYC rules and complete reasoning.
        """
        from engine.ai.sayc_rules import get_rule, format_rule_reference

        lines = []

        # Primary reason
        lines.append(f"📋 {self.primary_reason}")

        # SAYC Rule Reference
        if self.sayc_rule_id:
            rule = get_rule(self.sayc_rule_id)
            if rule:
                lines.append(f"\n📖 SAYC Rule: {rule.name}")
                lines.append(f"   {rule.description}")
                if rule.url:
                    lines.append(f"   📚 Reference: {rule.url}")

        # Hand requirements vs actuals
        if self.hand_requirements or self.actual_hand_values:
            lines.append("\n🃏 Hand Analysis:")
            all_keys = set(self.hand_requirements.keys()) | set(self.actual_hand_values.keys())
            for key in sorted(all_keys):
                requirement = self.hand_requirements.get(key, "")
                actual = self.actual_hand_values.get(key, "")
                if requirement and actual:
                    lines.append(f"  ✓ {key}: {actual} (requires {requirement})")
                elif actual:
                    lines.append(f"  • {key}: {actual}")
                elif requirement:
                    lines.append(f"  ✗ {key}: (requires {requirement})")

        # Decision trace - all rule checks
        if self.rule_checks:
            lines.append("\n🔍 Decision Trace:")
            for check in self.rule_checks:
                status = "✓" if check.result else "✗"
                if check.value:
                    lines.append(f"  {status} {check.condition}: {check.value}")
                else:
                    lines.append(f"  {status} {check.condition}")

        # Alternative bids considered
        if self.alternatives_considered:
            lines.append("\n🤔 Alternatives Rejected:")
            for alt in self.alternatives_considered:
                lines.append(f"  ✗ {alt.bid}: {alt.reason_rejected}")

        # Forcing status and convention
        metadata = []
        if self.forcing_status:
            metadata.append(f"Status: {self.forcing_status}")
        if self.convention_reference:
            metadata.append(f"Convention: {self.convention_reference}")

        if metadata:
            lines.append("\n⚡ " + " | ".join(metadata))

        return "\n".join(lines)

    def format(self, level: ExplanationLevel = ExplanationLevel.DETAILED) -> str:
        """
        Format explanation at specified level.

        Args:
            level: ExplanationLevel (SIMPLE, CONVENTION_ONLY, DETAILED, or EXPERT)

        Returns:
            Formatted explanation string
        """
        if level == ExplanationLevel.SIMPLE:
            return self.to_simple_string()
        elif level == ExplanationLevel.CONVENTION_ONLY:
            return self.to_convention_only_string()
        elif level == ExplanationLevel.EXPERT:
            return self.to_expert_string()
        else:  # DETAILED
            return self.to_detailed_string()

    def to_dict(self) -> Dict:
        """
        Convert to dictionary for JSON serialization.
        Useful for sending to frontend.
        """
        from engine.ai.sayc_rules import get_rule

        result = {
            "bid": self.bid,
            "primary_reason": self.primary_reason,
            "hand_requirements": self.hand_requirements,
            "actual_hand_values": self.actual_hand_values,
            "rule_checks": [
                {"condition": rc.condition, "result": rc.result, "value": rc.value}
                for rc in self.rule_checks
            ],
            "alternatives_considered": [
                {"bid": alt.bid, "reason": alt.reason_rejected}
                for alt in self.alternatives_considered
            ],
            "convention_reference": self.convention_reference,
            "forcing_status": self.forcing_status,
            "sayc_rule_id": self.sayc_rule_id
        }

        # Include SAYC rule details if present
        if self.sayc_rule_id:
            rule = get_rule(self.sayc_rule_id)
            if rule:
                result["sayc_rule"] = {
                    "id": rule.id,
                    "name": rule.name,
                    "description": rule.description,
                    "url": rule.url,
                    "category": rule.category
                }

        return result

    def __str__(self) -> str:
        """Default string representation uses simple format."""
        return self.to_simple_string()


def compare_bids(user_bid: str, optimal_bid: str,
                 optimal_explanation: BidExplanation,
                 hand_summary: Dict[str, any]) -> str:
    """
    Generate a detailed comparison explaining why optimal_bid is better than user_bid.

    Args:
        user_bid: The bid the user made
        optimal_bid: The recommended bid
        optimal_explanation: The explanation for the optimal bid
        hand_summary: Dictionary with hand info (hcp, suit_lengths, etc.)

    Returns:
        Formatted string explaining the comparison
    """
    lines = []

    lines.append(f"⚠️ Your bid: {user_bid}")
    lines.append(f"Recommended: {optimal_bid}")
    lines.append("")
    lines.append(f"Why {optimal_bid}?")
    lines.append(f"{optimal_explanation.primary_reason}")

    # Show hand context
    if optimal_explanation.actual_hand_values:
        lines.append("\nYour hand characteristics:")
        for key, value in optimal_explanation.actual_hand_values.items():
            lines.append(f"  • {key}: {value}")

    # Show what was required
    if optimal_explanation.hand_requirements:
        lines.append("\nRequirements for this bid:")
        for key, value in optimal_explanation.hand_requirements.items():
            lines.append(f"  • {key}: {value}")

    return "\n".join(lines)

"""
SAYC (Standard American Yellow Card) Rule References

This module provides links and references to official SAYC documentation
for each bidding rule. These can be embedded in explanations to help users
learn the official system.
"""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class SAYCRule:
    """Represents a reference to a SAYC rule or convention."""
    id: str
    name: str
    description: str
    url: Optional[str] = None
    category: str = ""


# SAYC Rule Database
# Official SAYC card: https://web2.acbl.org/documentlibrary/play/sayc.pdf
# WBF System Card: http://www.worldbridge.org/
SAYC_RULES = {
    # OPENING BIDS
    "1nt_opening": SAYCRule(
        id="1nt_opening",
        name="1NT Opening",
        description="15-17 HCP, balanced distribution (no singleton/void, at most one doubleton)",
        url="https://web2.acbl.org/documentlibrary/play/sayc.pdf",
        category="Opening Bids"
    ),
    "2nt_opening": SAYCRule(
        id="2nt_opening",
        name="2NT Opening",
        description="20-21 HCP, balanced distribution (forcing to game)",
        url="https://web2.acbl.org/documentlibrary/play/sayc.pdf",
        category="Opening Bids"
    ),
    "3nt_opening": SAYCRule(
        id="3nt_opening",
        name="3NT Opening",
        description="25-27 HCP, balanced distribution (to play)",
        url="https://web2.acbl.org/documentlibrary/play/sayc.pdf",
        category="Opening Bids"
    ),
    "2c_opening": SAYCRule(
        id="2c_opening",
        name="Strong 2♣ Opening",
        description="22+ points or game-forcing hand (artificial and forcing)",
        url="https://web2.acbl.org/documentlibrary/play/sayc.pdf",
        category="Opening Bids"
    ),
    "one_level_major": SAYCRule(
        id="one_level_major",
        name="1-Level Major Opening",
        description="13+ points with 5+ card major suit",
        url="https://web2.acbl.org/documentlibrary/play/sayc.pdf",
        category="Opening Bids"
    ),
    "one_level_minor": SAYCRule(
        id="one_level_minor",
        name="1-Level Minor Opening",
        description="13+ points, may be 3-card club suit (better minor principle)",
        url="https://web2.acbl.org/documentlibrary/play/sayc.pdf",
        category="Opening Bids"
    ),

    # RESPONSES
    "simple_raise": SAYCRule(
        id="simple_raise",
        name="Simple Raise",
        description="Raise partner's suit one level with 6-9 support points and 3+ card support",
        url="https://web2.acbl.org/documentlibrary/play/sayc.pdf",
        category="Responses"
    ),
    "invitational_raise": SAYCRule(
        id="invitational_raise",
        name="Invitational Raise",
        description="Jump raise partner's suit with 10-12 support points and 3+ card support",
        url="https://web2.acbl.org/documentlibrary/play/sayc.pdf",
        category="Responses"
    ),
    "game_forcing_raise": SAYCRule(
        id="game_forcing_raise",
        name="Game-Forcing Raise",
        description="Jump to game in partner's suit with 13+ support points and 3+ card support",
        url="https://web2.acbl.org/documentlibrary/play/sayc.pdf",
        category="Responses"
    ),
    "jump_shift": SAYCRule(
        id="jump_shift",
        name="Jump Shift Response",
        description="Jump in new suit shows 17+ HCP and good suit (game-forcing)",
        url="https://web2.acbl.org/documentlibrary/play/sayc.pdf",
        category="Responses"
    ),
    "new_suit_forcing": SAYCRule(
        id="new_suit_forcing",
        name="New Suit Forcing",
        description="New suit by responder is forcing (1-level: 6+ HCP, 2-level: 10+ HCP)",
        url="https://web2.acbl.org/documentlibrary/play/sayc.pdf",
        category="Responses"
    ),
    "1nt_response": SAYCRule(
        id="1nt_response",
        name="1NT Response",
        description="6-10 HCP, balanced, no 4-card major to bid at 1-level, denies support",
        url="https://web2.acbl.org/documentlibrary/play/sayc.pdf",
        category="Responses"
    ),
    "2nt_response": SAYCRule(
        id="2nt_response",
        name="2NT Response",
        description="11-12 HCP, balanced, invitational to 3NT, denies support",
        url="https://web2.acbl.org/documentlibrary/play/sayc.pdf",
        category="Responses"
    ),

    # CONVENTIONS
    "stayman": SAYCRule(
        id="stayman",
        name="Stayman Convention",
        description="2♣ response to 1NT asks for 4-card major",
        url="https://en.wikipedia.org/wiki/Stayman_convention",
        category="Conventions"
    ),
    "jacoby_transfer": SAYCRule(
        id="jacoby_transfer",
        name="Jacoby Transfers",
        description="2♦ shows 5+ hearts, 2♥ shows 5+ spades after 1NT opening",
        url="https://en.wikipedia.org/wiki/Jacoby_transfer",
        category="Conventions"
    ),
    "blackwood": SAYCRule(
        id="blackwood",
        name="Blackwood Convention",
        description="4NT asks for aces (5♣=0/4, 5♦=1, 5♥=2, 5♠=3)",
        url="https://en.wikipedia.org/wiki/Blackwood_convention",
        category="Conventions"
    ),
    "takeout_double": SAYCRule(
        id="takeout_double",
        name="Takeout Double",
        description="Double of opening bid shows opening values with support for unbid suits",
        url="https://en.wikipedia.org/wiki/Takeout_double",
        category="Competitive Bidding"
    ),
    "negative_double": SAYCRule(
        id="negative_double",
        name="Negative Double",
        description="Double after partner opens and opponent overcalls, shows unbid major(s)",
        url="https://en.wikipedia.org/wiki/Negative_double",
        category="Competitive Bidding"
    ),
    "weak_two": SAYCRule(
        id="weak_two",
        name="Weak Two Bids",
        description="2♦/2♥/2♠ shows 6-card suit with 5-10 HCP (preemptive)",
        url="https://web2.acbl.org/documentlibrary/play/sayc.pdf",
        category="Opening Bids"
    ),

    # COMPETITIVE BIDDING
    "overcall": SAYCRule(
        id="overcall",
        name="Simple Overcall",
        description="1-level: 8+ HCP with 5+ card suit; 2-level: 10+ HCP with good 5+ card suit",
        url="https://web2.acbl.org/documentlibrary/play/sayc.pdf",
        category="Competitive Bidding"
    ),

    # SCORING CONCEPTS
    "support_points": SAYCRule(
        id="support_points",
        name="Support Points",
        description="HCP + shortness when raising: void=3, singleton=2, doubleton=1",
        url="https://web2.acbl.org/documentlibrary/play/sayc.pdf",
        category="Hand Evaluation"
    ),
    "distribution_points": SAYCRule(
        id="distribution_points",
        name="Distribution Points",
        description="Long suit points: 5th card=1pt, 6th card=2pts, etc.",
        url="https://web2.acbl.org/documentlibrary/play/sayc.pdf",
        category="Hand Evaluation"
    ),
}


def get_rule(rule_id: str) -> Optional[SAYCRule]:
    """Get a SAYC rule by ID."""
    return SAYC_RULES.get(rule_id)


def get_rules_by_category(category: str) -> Dict[str, SAYCRule]:
    """Get all rules in a category."""
    return {
        rule_id: rule
        for rule_id, rule in SAYC_RULES.items()
        if rule.category == category
    }


def format_rule_reference(rule_id: str, include_url: bool = True) -> str:
    """Format a rule reference for display in explanations."""
    rule = get_rule(rule_id)
    if not rule:
        return ""

    parts = [f"📖 SAYC: {rule.name}"]

    if include_url and rule.url:
        parts.append(f"   Learn more: {rule.url}")

    return "\n".join(parts)


def get_all_categories() -> list:
    """Get list of all rule categories."""
    return sorted(set(rule.category for rule in SAYC_RULES.values()))

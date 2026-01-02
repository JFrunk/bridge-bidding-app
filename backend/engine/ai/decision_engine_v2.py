"""
Priority-Based Decision Engine (V2)

This is an alternative to the imperative decision_engine.py that uses
priority-based module selection instead of hard-coded if/else chains.

Key differences from V1:
1. No manual routing logic - modules declare when they apply
2. Explicit priorities - conflicts are resolved by priority, not code order
3. Conflict detection - logs when multiple modules match (helps debugging)
4. Extensible - adding a new convention only requires registering it with priority

Part of ADR-0003: Priority-Based Bidding Architecture

Usage:
    from engine.ai.decision_engine_v2 import select_bidding_module_v2

    # Instead of:
    #   module_name = select_bidding_module(features)
    # Use:
    #   module_name, conflicts = select_bidding_module_v2(hand, features)
"""

import logging
from typing import Dict, Tuple, List, Optional

from engine.ai.module_registry import ModuleRegistry, get_module_priority
from engine.ai.conventions.base_convention import BiddingContext

logger = logging.getLogger(__name__)


def select_bidding_module_v2(hand, features: Dict) -> Tuple[str, List[str]]:
    """
    Select bidding module using priority-based approach.

    This replaces the imperative select_bidding_module() function with
    a declarative approach where:
    1. All registered modules are checked
    2. Each module declares if it applies via applies() method
    3. Highest priority module wins
    4. Conflicts are logged for debugging

    Args:
        hand: The player's hand
        features: Extracted features including auction context

    Returns:
        Tuple of (module_name, list_of_conflicts)
        - module_name: Selected module name, or 'pass_by_default'
        - conflicts: List of other modules that also matched (for debugging)

    Example:
        module_name, conflicts = select_bidding_module_v2(hand, features)
        if conflicts:
            print(f"Also considered: {conflicts}")
    """
    ctx = BiddingContext(features)

    # Log auction state for debugging
    logger.debug(
        f"\n🎯 DECISION ENGINE V2:\n"
        f"   Opening: {ctx.opening_bid}\n"
        f"   Opener relationship: {features.get('auction_features', {}).get('opener_relationship')}\n"
        f"   Partner last bid: {ctx.partner_last_bid}\n"
        f"   Auction: {features.get('auction_history', [])}"
    )

    # Use registry's priority-based selection
    selected, all_applicable = ModuleRegistry.select_module_by_priority(hand, features)

    if selected is None:
        logger.debug("   → No module applied, defaulting to pass_by_default")
        return 'pass_by_default', []

    # Calculate conflicts (modules that matched but weren't selected)
    conflicts = [name for name in all_applicable if name != selected]

    if conflicts:
        logger.info(
            f"   → Selected: {selected} (priority {get_module_priority(selected)})\n"
            f"   → Also matched: {[(n, get_module_priority(n)) for n in conflicts]}"
        )
    else:
        logger.debug(f"   → Selected: {selected} (only match)")

    return selected, conflicts


def get_applicable_modules_debug(hand, features: Dict) -> List[Dict]:
    """
    Get detailed information about all applicable modules.

    This is useful for debugging and understanding why a particular
    module was selected.

    Args:
        hand: The player's hand
        features: Extracted features including auction context

    Returns:
        List of dicts with module information:
        - name: Module name
        - priority: Module priority
        - selected: True if this was the selected module
        - bid: The bid this module would suggest (if any)
        - explanation: The explanation (if any)
    """
    applicable = ModuleRegistry.find_applicable_modules(hand, features)

    result = []
    for i, (priority, name, module) in enumerate(applicable):
        info = {
            'name': name,
            'priority': priority,
            'selected': (i == 0),  # First is highest priority
            'bid': None,
            'explanation': None,
        }

        # Try to get the bid suggestion
        try:
            eval_result = module.evaluate(hand, features)
            if eval_result:
                info['bid'] = eval_result[0]
                if len(eval_result) > 1:
                    # Handle both string and BidExplanation
                    exp = eval_result[1]
                    if hasattr(exp, 'format'):
                        info['explanation'] = exp.format()
                    else:
                        info['explanation'] = str(exp)
        except Exception as e:
            info['error'] = str(e)

        result.append(info)

    return result


def explain_routing_decision(hand, features: Dict) -> str:
    """
    Generate a human-readable explanation of the routing decision.

    This is useful for debugging and for showing users why a particular
    bid was chosen.

    Args:
        hand: The player's hand
        features: Extracted features including auction context

    Returns:
        Multi-line string explaining the decision
    """
    ctx = BiddingContext(features)
    modules_info = get_applicable_modules_debug(hand, features)

    lines = [
        "=== Routing Decision Analysis ===",
        f"Auction state: {features.get('auction_history', [])}",
        f"Opening bid: {ctx.opening_bid}",
        f"Opener relationship: {features.get('auction_features', {}).get('opener_relationship')}",
        "",
        "Applicable modules (by priority):",
    ]

    if not modules_info:
        lines.append("  (none - will pass by default)")
    else:
        for info in modules_info:
            marker = "→ " if info['selected'] else "  "
            bid_info = f" → {info['bid']}" if info['bid'] else ""
            lines.append(
                f"{marker}{info['name']} (priority {info['priority']}){bid_info}"
            )

    lines.append("")
    if modules_info:
        selected = modules_info[0]
        lines.append(f"Selected: {selected['name']}")
        if selected['bid']:
            lines.append(f"Bid: {selected['bid']}")
        if selected['explanation']:
            lines.append(f"Reason: {selected['explanation'][:100]}...")

    return "\n".join(lines)


# =============================================================================
# HYBRID MODE: Use V2 with V1 fallback
# =============================================================================

def select_bidding_module_hybrid(hand, features: Dict) -> str:
    """
    Hybrid selection that uses V2 with V1 as fallback.

    This allows gradual migration from the imperative to declarative approach.
    If V2 returns pass_by_default but V1 finds a module, log a warning
    (indicates a module missing applies() implementation).

    Args:
        hand: The player's hand
        features: Extracted features

    Returns:
        Module name string (compatible with existing BiddingEngine)
    """
    # Try V2 first
    v2_result, conflicts = select_bidding_module_v2(hand, features)

    if v2_result != 'pass_by_default':
        return v2_result

    # V2 didn't find anything, try V1 as fallback
    from engine.ai.decision_engine import select_bidding_module as v1_select
    v1_result = v1_select(features)

    if v1_result != 'pass_by_default':
        logger.warning(
            f"V2 returned pass_by_default but V1 found '{v1_result}'. "
            f"This module may need an applies() implementation."
        )
        return v1_result

    return 'pass_by_default'

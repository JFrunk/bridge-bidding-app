#!/usr/bin/env python3
"""
Migration Script: Add sets_forcing_level Tags to Schema Files

This script analyzes existing schema rules and automatically injects
the appropriate forcing level tags based on SAYC conventions.

Forcing Level Logic:
- GAME_FORCE: 2/1 responses (12+ HCP at 2-level), jump shifts, 4th suit forcing
- FORCING_1_ROUND: New suit responses, reverses, new suit by opener
- NON_FORCING: Raises, NT bids, Pass, rebids of own suit

Usage:
    python3 migrate_forcing_levels.py           # Preview changes
    python3 migrate_forcing_levels.py --apply   # Apply changes
"""

import json
import os
import sys
from pathlib import Path


SCHEMA_DIR = Path(__file__).parent.parent / 'schemas'


def determine_forcing_level(rule: dict) -> str:
    """
    Determine the appropriate forcing level for a rule based on SAYC conventions.

    Args:
        rule: The rule dictionary from the schema

    Returns:
        One of: "GAME_FORCE", "FORCING_1_ROUND", "NON_FORCING"
    """
    bid = rule.get('bid', '')
    rule_id = rule.get('id', '')
    conditions = rule.get('conditions', {})
    forcing = rule.get('forcing', 'none')

    # Already has forcing set in the rule
    if forcing == 'game':
        return "GAME_FORCE"

    # Extract HCP constraints
    hcp_constraint = conditions.get('hcp', {})
    hcp_min = hcp_constraint.get('min', 0) if isinstance(hcp_constraint, dict) else 0

    # === GAME FORCING BIDS ===

    # 2♣ opening is always game forcing
    if bid == '2♣' and conditions.get('is_opening'):
        return "GAME_FORCE"

    # 2/1 responses (2-level new suit with 10+ HCP responding to 1-level major)
    if bid.startswith('2') and hcp_min >= 10:
        if 'is_response' in conditions and conditions.get('is_response'):
            # Check if responding to 1-level major
            partner_bid = conditions.get('partner_last_bid', {})
            opening_bid = conditions.get('opening_bid', {})
            if isinstance(partner_bid, dict) and 'in' in partner_bid:
                if any(b in ['1♥', '1♠'] for b in partner_bid.get('in', [])):
                    return "GAME_FORCE"
            if isinstance(opening_bid, dict) and 'in' in opening_bid:
                if any(b in ['1♥', '1♠'] for b in opening_bid.get('in', [])):
                    return "GAME_FORCE"

    # Fourth suit forcing
    if 'fourth_suit' in rule_id.lower():
        return "GAME_FORCE"

    # Jump shift responses (skipping a level in a new suit)
    if 'jump_shift' in rule_id.lower():
        return "GAME_FORCE"

    # Strong 2NT response (Jacoby 2NT, etc.)
    if bid == '2NT' and hcp_min >= 13:
        return "GAME_FORCE"

    # === FORCING ONE ROUND ===

    # New suit response at 1-level
    if bid.startswith('1') and 'is_response' in conditions:
        if conditions.get('is_response') and '♠' in bid or '♥' in bid or '♦' in bid or '♣' in bid:
            if 'NT' not in bid:
                return "FORCING_1_ROUND"

    # Stayman is forcing one round
    if 'stayman' in rule_id.lower():
        return "FORCING_1_ROUND"

    # Jacoby transfers are forcing one round
    if 'jacoby' in rule_id.lower() or 'transfer' in rule_id.lower():
        return "FORCING_1_ROUND"

    # Takeout double
    if bid == 'X' and ('takeout' in rule_id.lower() or 'double' in rule_id.lower()):
        return "FORCING_1_ROUND"

    # Negative double
    if 'negative_double' in rule_id.lower():
        return "FORCING_1_ROUND"

    # Reverses by opener
    if 'reverse' in rule_id.lower():
        return "FORCING_1_ROUND"

    # New suit by opener (rebid)
    if 'new_suit' in rule_id.lower() and 'opener' in rule_id.lower():
        return "FORCING_1_ROUND"

    # Cuebids
    if 'cuebid' in rule_id.lower() or 'michaels' in rule_id.lower():
        return "FORCING_1_ROUND"

    # Unusual 2NT
    if 'unusual' in rule_id.lower():
        return "FORCING_1_ROUND"

    # === NON-FORCING ===
    # Default for raises, NT bids, rebids, passes
    return "NON_FORCING"


def migrate_schema(filepath: Path, apply: bool = False) -> dict:
    """
    Migrate a single schema file to add forcing level tags.

    Args:
        filepath: Path to the schema JSON file
        apply: If True, write changes. If False, just preview.

    Returns:
        Dict with migration stats
    """
    with open(filepath, 'r') as f:
        schema = json.load(f)

    stats = {
        'total_rules': 0,
        'game_force': 0,
        'forcing_1_round': 0,
        'non_forcing': 0,
        'already_tagged': 0,
        'changes': []
    }

    for rule in schema.get('rules', []):
        stats['total_rules'] += 1

        # Skip if already has forcing level tag
        if 'sets_forcing_level' in rule:
            stats['already_tagged'] += 1
            continue

        # Determine forcing level
        forcing_level = determine_forcing_level(rule)
        rule['sets_forcing_level'] = forcing_level

        # Track stats
        if forcing_level == "GAME_FORCE":
            stats['game_force'] += 1
        elif forcing_level == "FORCING_1_ROUND":
            stats['forcing_1_round'] += 1
        else:
            stats['non_forcing'] += 1

        stats['changes'].append({
            'rule_id': rule.get('id'),
            'bid': rule.get('bid'),
            'forcing_level': forcing_level
        })

    if apply and stats['changes']:
        with open(filepath, 'w') as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)

    return stats


def main():
    apply = '--apply' in sys.argv

    print("=" * 70)
    print("FORCING LEVEL MIGRATION SCRIPT")
    print("=" * 70)

    if not apply:
        print("Preview mode. Use --apply to write changes.\n")
    else:
        print("Applying changes to schema files.\n")

    total_stats = {
        'files': 0,
        'total_rules': 0,
        'game_force': 0,
        'forcing_1_round': 0,
        'non_forcing': 0
    }

    for schema_file in sorted(SCHEMA_DIR.glob('*.json')):
        print(f"\n{schema_file.name}")
        print("-" * 50)

        stats = migrate_schema(schema_file, apply=apply)

        print(f"  Total rules: {stats['total_rules']}")
        print(f"  Already tagged: {stats['already_tagged']}")
        print(f"  New tags added:")
        print(f"    GAME_FORCE: {stats['game_force']}")
        print(f"    FORCING_1_ROUND: {stats['forcing_1_round']}")
        print(f"    NON_FORCING: {stats['non_forcing']}")

        if stats['changes']:
            print(f"\n  Changes:")
            for change in stats['changes'][:10]:  # Show first 10
                print(f"    {change['rule_id']}: {change['bid']} -> {change['forcing_level']}")
            if len(stats['changes']) > 10:
                print(f"    ... and {len(stats['changes']) - 10} more")

        total_stats['files'] += 1
        total_stats['total_rules'] += stats['total_rules']
        total_stats['game_force'] += stats['game_force']
        total_stats['forcing_1_round'] += stats['forcing_1_round']
        total_stats['non_forcing'] += stats['non_forcing']

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Files processed: {total_stats['files']}")
    print(f"Total rules: {total_stats['total_rules']}")
    print(f"GAME_FORCE added: {total_stats['game_force']}")
    print(f"FORCING_1_ROUND added: {total_stats['forcing_1_round']}")
    print(f"NON_FORCING added: {total_stats['non_forcing']}")

    if not apply:
        print("\nTo apply these changes, run:")
        print("  python3 migrate_forcing_levels.py --apply")


if __name__ == '__main__':
    main()

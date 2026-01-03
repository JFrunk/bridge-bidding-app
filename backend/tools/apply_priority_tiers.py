#!/usr/bin/env python3
"""
Priority Tier Normalizer for V2 Schema Engine

This script applies a consistent priority hierarchy based on bidding "physics":
- Higher tiers ALWAYS override lower tiers
- Within tiers, original relative ordering is preserved

The 4-Tier Model:
  TIER I (800-999):   Artificial & Systemic - "Code Words"
  TIER II (500-799):  Constructive & Forcing - "Dialogue"
  TIER III (200-499): Invitational & Limit - "Proposals"
  TIER IV (0-199):    Terminal & Competitive - "Sign-offs"

Usage:
    python3 tools/apply_priority_tiers.py [--dry-run]
"""

import json
import glob
import os
import sys
import argparse
from pathlib import Path

# The "Physics" of Priority - Keyword to Base Priority mapping
# Order matters! More specific keywords should come first in matching
TIER_KEYWORDS = [
    # TIER I: Artificial & Systemic (800-999)
    # These are "code words" that change auction meaning
    ("rkcb", 950),
    ("blackwood", 950),
    ("queen_ask", 940),
    ("king_ask", 930),
    ("jacoby_rebid_void", 920),      # Jacoby rebid showing void (highest)
    ("jacoby_rebid_singleton", 910), # Jacoby rebid showing singleton
    ("jacoby_rebid_strong", 885),    # Jacoby rebid 18+ HCP
    ("jacoby_rebid_extra", 880),     # Jacoby rebid 15-17 HCP
    ("splinter", 860),
    ("jacoby_2nt", 850),
    ("jacoby_rebid_minimum", 840),   # Fast arrival (lowest Jacoby rebid)
    ("texas", 830),
    ("jacoby_transfer", 820),
    ("stayman", 810),
    ("smolen", 805),
    ("fourth_suit", 800),
    ("negative_double", 795),
    ("redouble", 790),

    # TIER II: Constructive & Forcing (500-799)
    # Natural bids that force the auction to continue
    ("reverse", 750),
    ("strong_jump", 720),
    ("jump_shift", 700),
    ("game_force", 650),
    ("new_suit_2_level", 600),     # 2-over-1
    ("cuebid", 580),
    ("limit_raise", 550),
    ("competitive_limit", 540),
    ("free_bid", 520),

    # TIER III: Invitational & Limit (200-499)
    # Bids that define hand limit and invite conclusion
    ("invitational", 450),
    ("quantitative", 400),
    ("limit", 380),
    ("raise_1nt_to_3nt", 350),
    ("raise_1nt_invitational", 340),
    ("game_raise", 320),
    ("simple_raise", 300),
    ("single_raise", 280),
    ("respond_1nt", 260),
    ("opener_rebid", 250),
    ("responder_rebid", 240),
    ("support_double", 230),
    ("jump_raise", 220),
    ("free_raise", 210),

    # TIER IV: Terminal & Competitive (0-199)
    # Sign-offs and competitive bids
    ("fast_arrival", 180),
    ("minimum", 170),
    ("sign_off", 160),
    ("simple_overcall", 140),
    ("direct_nt_overcall", 130),
    ("overcall", 120),
    ("takeout_double", 110),
    ("balancing", 100),
    ("advancer", 90),
    ("preempt", 80),
    ("weak", 70),
    ("pass", 20),
]


def get_tier_priority(rule_id: str, description: str, explanation: str) -> tuple:
    """
    Determine the base priority tier for a rule based on keywords.

    Returns (priority, matched_keyword) or (-1, None) if no match.
    Keywords are checked in order, so more specific patterns match first.
    """
    # Combine all text for keyword matching
    text = f"{rule_id} {description} {explanation}".lower()

    # Check keywords in order (more specific first)
    for keyword, base_priority in TIER_KEYWORDS:
        if keyword in text:
            return base_priority, keyword

    return -1, None


def calculate_new_priority(rule: dict, schema_category: str) -> tuple:
    """
    Calculate the new tiered priority for a rule.

    Returns (new_priority, matched_keyword, was_changed)
    """
    rule_id = rule.get('id', '')
    description = rule.get('description', '')
    explanation = rule.get('explanation', '')
    old_priority = rule.get('priority', 0)

    tier_priority, matched_keyword = get_tier_priority(rule_id, description, explanation)

    if tier_priority > 0:
        # Apply tier base + small offset to maintain relative ordering
        # The offset (0-9) preserves original sub-ordering within a tier
        offset = old_priority % 10
        new_priority = tier_priority + offset
        return new_priority, matched_keyword, (new_priority != old_priority)

    return old_priority, None, False


def process_schema_file(file_path: str, dry_run: bool = False) -> dict:
    """
    Process a single schema file and apply priority tiers.

    Returns statistics about changes made.
    """
    with open(file_path, 'r') as f:
        data = json.load(f)

    stats = {
        'file': os.path.basename(file_path),
        'total_rules': 0,
        'updated_rules': 0,
        'changes': []
    }

    rules = data.get('rules', [])
    stats['total_rules'] = len(rules)

    for rule in rules:
        old_priority = rule.get('priority', 0)
        new_priority, keyword, changed = calculate_new_priority(rule, data.get('category', ''))

        if changed:
            stats['updated_rules'] += 1
            stats['changes'].append({
                'rule_id': rule['id'],
                'old': old_priority,
                'new': new_priority,
                'keyword': keyword
            })

            if not dry_run:
                rule['priority'] = new_priority

    if not dry_run and stats['updated_rules'] > 0:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    return stats


def main():
    parser = argparse.ArgumentParser(description='Apply priority tiers to V2 schema files')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would change without modifying files')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed changes for each rule')
    args = parser.parse_args()

    # Find schema directory
    script_dir = Path(__file__).parent
    schema_dir = script_dir.parent / 'engine' / 'v2' / 'schemas'

    if not schema_dir.exists():
        print(f"Error: Schema directory not found: {schema_dir}")
        sys.exit(1)

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Processing schemas in: {schema_dir}")
    print("=" * 60)

    # Process all JSON files
    files = sorted(glob.glob(str(schema_dir / '*.json')))
    total_updated = 0

    for file_path in files:
        stats = process_schema_file(file_path, args.dry_run)

        if stats['updated_rules'] > 0:
            status = "would update" if args.dry_run else "updated"
            print(f"\n{stats['file']}: {status} {stats['updated_rules']}/{stats['total_rules']} rules")

            if args.verbose:
                for change in stats['changes']:
                    print(f"  - {change['rule_id']}: {change['old']} → {change['new']} (matched: {change['keyword']})")

            total_updated += stats['updated_rules']
        else:
            print(f"{stats['file']}: no changes needed ({stats['total_rules']} rules)")

    print("=" * 60)
    action = "Would update" if args.dry_run else "Updated"
    print(f"{action} {total_updated} rules across {len(files)} files")

    if args.dry_run:
        print("\nRun without --dry-run to apply changes.")


if __name__ == "__main__":
    main()

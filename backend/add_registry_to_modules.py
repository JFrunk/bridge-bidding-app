#!/usr/bin/env python3
"""
Script to add auto-registration to all bidding modules.
Part of ADR-0002 Phase 1 implementation.
"""

# Module files and their registration names
MODULES = [
    ('engine/responses.py', 'responses', 'ResponseModule'),
    ('engine/rebids.py', 'openers_rebid', 'RebidModule'),
    ('engine/responder_rebids.py', 'responder_rebid', 'ResponderRebidModule'),
    ('engine/advancer_bids.py', 'advancer_bids', 'AdvancerBidsModule'),
    ('engine/overcalls.py', 'overcalls', 'OvercallModule'),
    ('engine/ai/conventions/stayman.py', 'stayman', 'StaymanConvention'),
    ('engine/ai/conventions/jacoby_transfers.py', 'jacoby', 'JacobyConvention'),
    ('engine/ai/conventions/preempts.py', 'preempts', 'PreemptConvention'),
    ('engine/ai/conventions/blackwood.py', 'blackwood', 'BlackwoodConvention'),
    ('engine/ai/conventions/takeout_doubles.py', 'takeout_doubles', 'TakeoutDoubleConvention'),
    ('engine/ai/conventions/negative_doubles.py', 'negative_doubles', 'NegativeDoubleConvention'),
    ('engine/ai/conventions/michaels_cuebid.py', 'michaels_cuebid', 'MichaelsCuebidConvention'),
    ('engine/ai/conventions/unusual_2nt.py', 'unusual_2nt', 'Unusual2NTConvention'),
    ('engine/ai/conventions/splinter_bids.py', 'splinter_bids', 'SplinterBidsConvention'),
    ('engine/ai/conventions/fourth_suit_forcing.py', 'fourth_suit_forcing', 'FourthSuitForcingConvention'),
]

REGISTRATION_TEMPLATE = '''
# ADR-0002 Phase 1: Auto-register this module on import
from engine.ai.module_registry import ModuleRegistry
ModuleRegistry.register("{module_name}", {class_name}())
'''

def add_registration(file_path, module_name, class_name):
    """Add registration code to a module file if not already present."""
    with open(file_path, 'r') as f:
        content = f.read()

    # Check if already registered
    if 'ModuleRegistry.register' in content:
        print(f"✓ {file_path} already has registration")
        return False

    # Add registration at end of file
    registration = REGISTRATION_TEMPLATE.format(
        module_name=module_name,
        class_name=class_name
    )

    with open(file_path, 'a') as f:
        f.write(registration)

    print(f"✓ Added registration to {file_path}")
    return True

def main():
    print("Adding auto-registration to all bidding modules...")
    print()

    updated = 0
    for file_path, module_name, class_name in MODULES:
        if add_registration(file_path, module_name, class_name):
            updated += 1

    print()
    print(f"✅ Updated {updated} modules")
    print(f"✅ Skipped {len(MODULES) - updated} modules (already registered)")

if __name__ == '__main__':
    main()

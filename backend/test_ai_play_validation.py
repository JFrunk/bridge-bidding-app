"""
Test AI play validation to ensure AI doesn't play for human player
"""

import sys
sys.path.insert(0, '.')

# Test the validation logic
print("=" * 80)
print("AI Play Validation Logic Test")
print("=" * 80)
print()

def should_user_control(position, declarer, dummy, user_position='S'):
    """
    Test the logic for determining if user should control a position
    """
    user_is_declarer = (declarer == user_position)
    user_is_dummy = (dummy == user_position)

    user_should_control = False

    if user_is_declarer:
        # User is declarer - controls both declarer and dummy
        if position == user_position or position == dummy:
            user_should_control = True
    elif not user_is_dummy:
        # User is a defender (not declarer, not dummy) - controls only their position
        if position == user_position:
            user_should_control = True
    # If user is dummy, user_should_control stays False (declarer controls dummy)

    return user_should_control, user_is_declarer, user_is_dummy


# Test scenarios
scenarios = [
    # (position, declarer, dummy, expected_user_control, description)
    ('S', 'S', 'N', True, "User is declarer, playing from their hand"),
    ('N', 'S', 'N', True, "User is declarer, playing from dummy"),
    ('E', 'S', 'N', False, "User is declarer, defender East plays"),
    ('W', 'S', 'N', False, "User is declarer, defender West plays"),

    ('S', 'N', 'S', False, "User is dummy, declarer North controls dummy"),
    ('N', 'N', 'S', False, "User is dummy, declarer North plays"),
    ('E', 'N', 'S', False, "User is dummy, defender East plays"),
    ('W', 'N', 'S', False, "User is dummy, defender West plays"),

    ('S', 'N', 'W', True, "User is defender, playing their hand"),
    ('N', 'N', 'W', False, "User is defender, declarer North plays"),
    ('E', 'N', 'W', False, "User is defender, partner East plays"),
    ('W', 'N', 'W', False, "User is defender, dummy West is controlled by declarer"),

    ('S', 'E', 'W', True, "User is defender, playing their hand"),
    ('N', 'E', 'W', False, "User is defender, partner North plays"),
    ('E', 'E', 'W', False, "User is defender, declarer East plays"),
    ('W', 'E', 'W', False, "User is defender, dummy West is controlled by declarer"),
]

print("Testing all scenarios:\n")
all_passed = True

for position, declarer, dummy, expected, description in scenarios:
    user_control, is_declarer, is_dummy = should_user_control(position, declarer, dummy)

    status = "✅ PASS" if user_control == expected else "❌ FAIL"
    if user_control != expected:
        all_passed = False

    print(f"{status} | {description}")
    print(f"      Position: {position}, Declarer: {declarer}, Dummy: {dummy}")
    print(f"      User control: {user_control} (expected: {expected})")
    print(f"      User is declarer: {is_declarer}, User is dummy: {is_dummy}")
    print()

print("=" * 80)
if all_passed:
    print("✅ ALL TESTS PASSED")
    print()
    print("The validation logic correctly prevents AI from playing for:")
    print("  - User when user is declarer (for both declarer and dummy positions)")
    print("  - User when user is a defender (for user's position only)")
    print()
    print("The validation logic correctly allows AI to play for:")
    print("  - Defenders when user is declarer")
    print("  - Declarer and dummy when user is dummy")
    print("  - All positions when user is a defender (except user's own)")
else:
    print("❌ SOME TESTS FAILED - Please review the logic")

print("=" * 80)

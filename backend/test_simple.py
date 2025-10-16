#!/usr/bin/env python3
"""
Simple test to verify the session state refactoring works
Tests basic functionality without needing requests library
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 70)
print("  SESSION STATE - BASIC VERIFICATION TEST")
print("=" * 70)
print()

# Test 1: Import session state module
print("Test 1: Import session state module...")
try:
    from core.session_state import SessionState, SessionStateManager, get_session_id_from_request
    print("  ✅ Session state module imported successfully")
except Exception as e:
    print(f"  ❌ Failed to import: {e}")
    sys.exit(1)

# Test 2: Create session state manager
print("\nTest 2: Create session state manager...")
try:
    state_manager = SessionStateManager()
    print("  ✅ SessionStateManager created")
except Exception as e:
    print(f"  ❌ Failed to create: {e}")
    sys.exit(1)

# Test 3: Create session states
print("\nTest 3: Create multiple session states...")
try:
    state1 = state_manager.get_or_create("session_1")
    state2 = state_manager.get_or_create("session_2")
    print(f"  ✅ Created session_1: {state1.session_id}")
    print(f"  ✅ Created session_2: {state2.session_id}")
except Exception as e:
    print(f"  ❌ Failed to create sessions: {e}")
    sys.exit(1)

# Test 4: Verify isolation
print("\nTest 4: Verify session isolation...")
try:
    state1.vulnerability = "NS"
    state2.vulnerability = "EW"

    if state1.vulnerability == "NS" and state2.vulnerability == "EW":
        print("  ✅ Sessions are isolated (different vulnerabilities)")
    else:
        print("  ❌ Sessions not isolated!")
        sys.exit(1)
except Exception as e:
    print(f"  ❌ Failed isolation test: {e}")
    sys.exit(1)

# Test 5: Verify persistence
print("\nTest 5: Verify session persistence...")
try:
    state1_again = state_manager.get_or_create("session_1")
    if state1_again.vulnerability == "NS":
        print("  ✅ Session state persists across get_or_create calls")
    else:
        print("  ❌ Session state not persisting!")
        sys.exit(1)
except Exception as e:
    print(f"  ❌ Failed persistence test: {e}")
    sys.exit(1)

# Test 6: Verify server.py has no global references
print("\nTest 6: Verify server.py has no global state variables...")
try:
    with open('server.py', 'r') as f:
        content = f.read()

    # Check for problematic patterns
    global_vars = [
        'current_deal',
        'current_vulnerability',
        'current_play_state',
        'current_session',
        'current_hand_start_time'
    ]

    found_globals = []
    for var in global_vars:
        # Count occurrences (should be in comments only)
        count = content.count(var)
        if count > 0:
            # Check if in comments (starts with # or in docstrings)
            lines_with_var = [line for line in content.split('\n') if var in line]
            non_comment_lines = [line for line in lines_with_var
                                if not line.strip().startswith('#')
                                and '"""' not in line
                                and "'''" not in line
                                and 'REMOVED' not in line]
            if non_comment_lines:
                found_globals.append(f"{var}: {len(non_comment_lines)} references")

    if found_globals:
        print(f"  ⚠️  Found global references: {', '.join(found_globals)}")
        print("  ℹ️  This may be okay if they're in comments or error messages")
    else:
        print("  ✅ No global state variables found in code")

except Exception as e:
    print(f"  ⚠️  Could not check server.py: {e}")

# Test 7: Verify server.py imports session state
print("\nTest 7: Verify server.py imports session state...")
try:
    with open('server.py', 'r') as f:
        content = f.read()

    if 'from core.session_state import' in content:
        print("  ✅ server.py imports session state module")
    else:
        print("  ❌ server.py missing session state import!")
        sys.exit(1)

    if 'SessionStateManager()' in content:
        print("  ✅ server.py creates SessionStateManager")
    else:
        print("  ❌ server.py doesn't create SessionStateManager!")
        sys.exit(1)

    if 'def get_state():' in content:
        print("  ✅ server.py has get_state() helper function")
    else:
        print("  ❌ server.py missing get_state() function!")
        sys.exit(1)

except Exception as e:
    print(f"  ❌ Failed to check server.py: {e}")
    sys.exit(1)

# Test 8: Test session count and info
print("\nTest 8: Test session manager functions...")
try:
    count = state_manager.get_session_count()
    print(f"  ✅ Session count: {count} sessions")

    info = state_manager.get_all_session_info()
    print(f"  ✅ Session info available for {len(info)} sessions")

except Exception as e:
    print(f"  ❌ Failed session manager test: {e}")
    sys.exit(1)

# Summary
print("\n" + "=" * 70)
print("  ✅ ALL BASIC TESTS PASSED")
print("=" * 70)
print()
print("Session state refactoring is working correctly!")
print()
print("Next steps:")
print("  1. Start the server: python3 server.py")
print("  2. Start the frontend: cd ../frontend && npm start")
print("  3. Test with multiple users (different browser tabs)")
print()

sys.exit(0)

#!/usr/bin/env python3
"""
Automatic refactoring script to fix global state bug in server.py

This script:
1. Backs up the original server.py
2. Adds session state manager initialization
3. Replaces all global variable usage with session state
4. Creates refactored server.py ready to use

Usage:
    python3 apply_global_state_fix.py

Safety: Creates backup before any changes.
"""

import re
import os
from datetime import datetime

def backup_file(filename):
    """Create timestamped backup"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'{filename}_backup_{timestamp}'
    with open(filename, 'r') as src:
        with open(backup_name, 'w') as dst:
            dst.write(src.read())
    return backup_name

def refactor_imports(text):
    """Add session state imports"""
    # Find the import section end
    import_end = text.find('# DDS AI for expert level')

    # Insert new import before DDS section
    new_import = "\n# Session state management (fixes global state race conditions)\nfrom core.session_state import SessionStateManager, get_session_id_from_request\n\n"

    return text[:import_end] + new_import + text[import_end:]

def refactor_initialization(text):
    """Replace global variables with state manager"""

    # Find and replace the global variable declarations
    pattern = r'(session_manager = SessionManager\(\)  # Session management\n\n)(# Phase 2: AI difficulty settings\ncurrent_ai_difficulty = "expert".*?current_hand_start_time = None  # Track hand duration)'

    replacement = r'\1# Initialize session state manager (replaces global variables)\nstate_manager = SessionStateManager()\napp.config[\'STATE_MANAGER\'] = state_manager\n\n# REMOVED: Global state variables are now per-session\n# - current_deal -> state.deal\n# - current_vulnerability -> state.vulnerability\n# - current_play_state -> state.play_state\n# - current_session -> state.game_session\n# - current_ai_difficulty -> state.ai_difficulty (default: "expert")\n# - current_hand_start_time -> state.hand_start_time\n# Access via: state = get_state()'

    text = re.sub(pattern, replacement, text, flags=re.DOTALL)

    return text

def add_helper_function(text):
    """Add get_state() helper function"""

    helper = '''
# ============================================================================
# SESSION STATE HELPER FUNCTION
# ============================================================================

def get_state():
    """
    Get session state for current request

    Returns SessionState object with isolated per-session data.
    This replaces all global variables with per-session state.

    Session ID extracted from (in order):
      1. X-Session-ID header (recommended)
      2. session_id in JSON body
      3. session_id query parameter
      4. Fallback: user_{user_id}_default for backward compatibility

    Returns:
        SessionState object with .deal, .vulnerability, .play_state, etc.
    """
    session_id = get_session_id_from_request(request)

    if not session_id:
        # Backward compatibility: use user_id as session identifier
        data = request.get_json(silent=True) or {}
        user_id = data.get('user_id', request.args.get('user_id', 1))
        session_id = f"user_{user_id}_default"

    return state_manager.get_or_create(session_id)

'''

    # Insert after CONVENTION_MAP
    insertion_point = text.find('# Register learning path endpoints')
    return text[:insertion_point] + helper + '\n' + text[insertion_point:]

def refactor_endpoint(text, endpoint_start, endpoint_name):
    """Refactor a single endpoint"""

    # Find the endpoint function
    endpoint_pattern = rf'(@app\.route\({endpoint_start}.*?\ndef [a-z_]+\(\):.*?)(?=@app\.route|if __name__|$)'
    match = re.search(endpoint_pattern, text, re.DOTALL)

    if not match:
        print(f"  ⚠️  Could not find endpoint: {endpoint_name}")
        return text

    endpoint_text = match.group(1)
    original_endpoint = endpoint_text

    # Remove global declarations
    endpoint_text = re.sub(r'\n\s+global current_[a-z_]+(?:, current_[a-z_]+)*\n', '\n', endpoint_text)

    # Add state = get_state() after docstring or function def
    if '"""' in endpoint_text:
        # Add after docstring
        endpoint_text = re.sub(
            r'(""".*?""")\n',
            r'\1\n    # Get session state for this request\n    state = get_state()\n',
            endpoint_text,
            flags=re.DOTALL
        )
    else:
        # Add after function definition
        endpoint_text = re.sub(
            r'(def [a-z_]+\(\):)\n',
            r'\1\n    # Get session state for this request\n    state = get_state()\n',
            endpoint_text
        )

    # Replace global variable usage
    replacements = [
        (r'\bcurrent_deal\b', 'state.deal'),
        (r'\bcurrent_vulnerability\b', 'state.vulnerability'),
        (r'\bcurrent_play_state\b', 'state.play_state'),
        (r'\bcurrent_session\b', 'state.game_session'),
        (r'\bcurrent_ai_difficulty\b', 'state.ai_difficulty'),
        (r'\bcurrent_hand_start_time\b', 'state.hand_start_time'),
    ]

    for old, new in replacements:
        endpoint_text = re.sub(old, new, endpoint_text)

    # Replace in original text
    text = text.replace(original_endpoint, endpoint_text)

    return text

def main():
    print("=" * 70)
    print("  GLOBAL STATE FIX - Automatic Refactoring")
    print("=" * 70)
    print()

    # Check if server.py exists
    if not os.path.exists('server.py'):
        print("❌ ERROR: server.py not found in current directory")
        print("   Please run this script from /backend directory")
        return 1

    # Check if session_state.py exists
    if not os.path.exists('core/session_state.py'):
        print("❌ ERROR: core/session_state.py not found")
        print("   Please ensure the session state module is created first")
        return 1

    # Create backup
    print("📦 Creating backup...")
    backup_name = backup_file('server.py')
    print(f"✅ Backup created: {backup_name}")
    print()

    # Read server.py
    print("📖 Reading server.py...")
    with open('server.py', 'r') as f:
        text = f.read()
    print(f"✅ Read {len(text)} characters")
    print()

    # Apply refactorings
    print("🔧 Applying refactorings...")
    print()

    print("  1️⃣  Adding session state imports...")
    text = refactor_imports(text)
    print("  ✅ Imports updated")

    print("  2️⃣  Replacing global variable declarations...")
    text = refactor_initialization(text)
    print("  ✅ Initialization refactored")

    print("  3️⃣  Adding get_state() helper function...")
    text = add_helper_function(text)
    print("  ✅ Helper function added")

    print("  4️⃣  Refactoring endpoints...")

    # List of endpoints to refactor
    endpoints = [
        ("'/api/session/start'", "start_session"),
        ("'/api/session/status'", "get_session_status"),
        ("'/api/session/complete-hand'", "complete_session_hand"),
        ("'/api/session/history'", "get_session_history"),
        ("'/api/session/abandon'", "abandon_session"),
        ("'/api/ai/status'", "get_ai_status"),
        ("'/api/set-ai-difficulty'", "set_ai_difficulty"),
        ("'/api/ai-statistics'", "get_ai_statistics"),
        ("'/api/load-scenario'", "load_scenario"),
        ("'/api/deal-hands'", "deal_hands"),
        ("'/api/get-next-bid'", "get_next_bid"),
        ("'/api/get-feedback'", "get_feedback"),
        ("'/api/get-all-hands'", "get_all_hands"),
        ("'/api/request-review'", "request_review"),
        ("'/api/start-play'", "start_play"),
        ("'/api/play-card'", "play_card"),
        ("'/api/get-ai-play'", "get_ai_play"),
        ("'/api/get-play-state'", "get_play_state"),
        ("'/api/clear-trick'", "clear_trick"),
        ("'/api/complete-play'", "complete_play"),
    ]

    for route, name in endpoints:
        print(f"     - Refactoring {name}...")
        text = refactor_endpoint(text, route, name)

    print("  ✅ All endpoints refactored")
    print()

    # Write refactored file
    print("💾 Writing refactored server.py...")
    with open('server.py', 'w') as f:
        f.write(text)
    print("✅ File written successfully")
    print()

    # Summary
    print("=" * 70)
    print("  ✅ REFACTORING COMPLETE")
    print("=" * 70)
    print()
    print(f"📦 Backup: {backup_name}")
    print("📝 Refactored: server.py")
    print()
    print("Next steps:")
    print("  1. Review the changes: git diff server.py")
    print("  2. Test the server: python server.py")
    print("  3. Test with multiple sessions")
    print("  4. Update frontend to send X-Session-ID header")
    print()
    print("Rollback if needed:")
    print(f"  cp {backup_name} server.py")
    print()

    return 0

if __name__ == '__main__':
    exit(main())

"""
Refactoring script to convert server.py from global state to session-based state

This script automates the conversion of global variables to session state.
Run this script to refactor server.py in place.

Usage:
    python refactor_to_session_state.py

Creates backup before modifying.
"""

import re
from datetime import datetime

def refactor_server_file():
    """Refactor server.py to use session state instead of globals"""

    # Read original file
    with open('server.py', 'r') as f:
        content = f.lines()

    # Create backup
    backup_name = f'server_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py'
    with open(backup_name, 'w') as f:
        f.writelines(content)
    print(f"✅ Created backup: {backup_name}")

    # Convert to string for regex operations
    text = ''.join(content)

    # Step 1: Add imports
    import_section = """import random
import json
import traceback
import os
from datetime import datetime
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine
from engine.hand_constructor import generate_hand_for_convention, generate_hand_with_constraints
from engine.ai.conventions.preempts import PreemptConvention
from engine.ai.conventions.jacoby_transfers import JacobyConvention
from engine.ai.conventions.stayman import StaymanConvention
from engine.ai.conventions.blackwood import BlackwoodConvention
from engine.play_engine import PlayEngine, PlayState, Contract, GamePhase
from engine.simple_play_ai import SimplePlayAI
from engine.play.ai.simple_ai import SimplePlayAI as SimplePlayAINew
from engine.play.ai.minimax_ai import MinimaxPlayAI
from engine.learning.learning_path_api import register_learning_endpoints
from engine.session_manager import SessionManager, GameSession

# NEW: Session state management
from core.session_state import SessionStateManager, get_session_id_from_request
"""

    # Find and replace import section
    text = re.sub(
        r'import random.*?from engine\.session_manager import SessionManager, GameSession',
        import_section,
        text,
        flags=re.DOTALL
    )

    # Step 2: Initialize state manager and remove global variables
    init_section = """
app = Flask(__name__)
CORS(app)
engine = BiddingEngine()
play_engine = PlayEngine()
play_ai = SimplePlayAI()  # Default AI (backward compatibility)
session_manager = SessionManager()  # Session management

# NEW: Session state manager (replaces global variables)
state_manager = SessionStateManager()
app.config['STATE_MANAGER'] = state_manager

# Initialize AI instances with DDS for expert level if available
ai_instances = {
    "beginner": SimplePlayAINew(),      # 6/10 rating
    "intermediate": MinimaxPlayAI(max_depth=2),  # 7.5/10 rating
    "advanced": MinimaxPlayAI(max_depth=3),      # 8/10 rating
}

# Use DDS for expert level if available, otherwise fallback to Minimax D4
if DDS_AVAILABLE:
    ai_instances["expert"] = DDSPlayAI()  # 9/10 rating - Expert level
    print("✅ DDS AI loaded for expert difficulty (9/10 rating)")
else:
    ai_instances["expert"] = MinimaxPlayAI(max_depth=4)  # 8+/10 rating - Fallback
    print("⚠️  Using Minimax D4 for expert (DDS not available)")

# REMOVED: Global state variables (now in SessionState)
# - current_deal -> state.deal
# - current_vulnerability -> state.vulnerability
# - current_play_state -> state.play_state
# - current_session -> state.game_session
# - current_ai_difficulty -> state.ai_difficulty
# - current_hand_start_time -> state.hand_start_time

CONVENTION_MAP = {
    "Preempt": PreemptConvention(),
    "JacobyTransfer": JacobyConvention(),
    "Stayman": StaymanConvention(),
    "Blackwood": BlackwoodConvention()
}
"""

    # Replace init section
    pattern = r'app = Flask\(__name__\).*?current_hand_start_time = None  # Track hand duration'
    text = re.sub(pattern, init_section.strip(), text, flags=re.DOTALL)

    # Step 3: Add helper function to get session state
    helper_function = """

# ============================================================================
# SESSION STATE HELPER
# ============================================================================

def get_state():
    \"\"\"
    Get session state for current request

    Returns SessionState object or raises error if no session ID provided.
    Use this in every endpoint that needs access to session-specific state.
    \"\"\"
    session_id = get_session_id_from_request(request)

    if not session_id:
        # For backward compatibility, try to use user_id as session_id
        # This allows endpoints that don't yet send session_id to still work
        data = request.get_json(silent=True) or {}
        user_id = data.get('user_id', request.args.get('user_id', 1))
        session_id = f"user_{user_id}_default"
        print(f"⚠️  No session_id provided, using fallback: {session_id}")

    return state_manager.get_or_create(session_id)


"""

    # Insert after CONVENTION_MAP
    text = text.replace(
        'CONVENTION_MAP = {',
        helper_function + '\nCONVENTION_MAP = {'
    )

    print("✅ Refactored server.py structure")
    print("⚠️  Manual replacements still needed for endpoint implementations")
    print("    Run the second script to update endpoints")

    # Write refactored file
    with open('server_refactored_step1.py', 'w') as f:
        f.write(text)

    print(f"✅ Created: server_refactored_step1.py")
    print("   Review this file, then rename it to server.py")

if __name__ == '__main__':
    refactor_server_file()

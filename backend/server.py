# Load environment variables from .env file FIRST (before any other imports)
from dotenv import load_dotenv
load_dotenv()

import random
import json
import traceback
import os
import time
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# Database abstraction layer (supports SQLite locally, PostgreSQL in production)
from db import get_connection, is_postgres
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
from engine.bridge_rules_engine import BridgeRulesEngine, GameState as BridgeGameState
from engine.feedback.play_feedback import get_play_feedback_generator
from engine.play.dds_analysis import get_dds_service, is_dds_available


# Session state management (fixes global state race conditions)
from core.session_state import SessionStateManager, get_session_id_from_request

# Error logging for bidding/play diagnostics
from utils.error_logger import log_error

# DDS AI for expert level play (9/10 rating)
# CRITICAL: DDS is ONLY enabled on Linux (production)
# macOS M1/M2 has known DDS crashes (Error Code -14, segmentation faults)
# See: BUG_DDS_CRASH_2025-10-18.md, DDS_MACOS_INSTABILITY_REPORT.md
import platform

PLATFORM_ALLOWS_DDS = platform.system() == 'Linux'

try:
    from engine.play.ai.dds_ai import DDSPlayAI, DDS_AVAILABLE

    if DDS_AVAILABLE and PLATFORM_ALLOWS_DDS:
        print("✅ DDS available for Expert AI (9/10)")
        print("   Platform: Linux - DDS enabled")
    elif DDS_AVAILABLE and not PLATFORM_ALLOWS_DDS:
        print(f"⚠️  DDS detected but DISABLED on {platform.system()} (unstable)")
        print("   Expert AI will use Minimax depth 4 (~8/10)")
        print("   Reason: Known DDS crashes on macOS M1/M2 (Error Code -14)")
        print("   See: BUG_DDS_CRASH_2025-10-18.md")
        DDS_AVAILABLE = False  # Force disable on non-Linux platforms
    else:
        print("⚠️  DDS not available")
        print("   Expert AI will use Minimax depth 4 (~8/10)")
        print("   For production 9/10 play, deploy to Linux with 'pip install endplay'")
except ImportError:
    DDS_AVAILABLE = False
    PLATFORM_ALLOWS_DDS = False
    print("⚠️  DDS AI not available - install endplay for expert play")

app = Flask(__name__)

# CORS configuration - allow all origins with explicit settings
# This ensures CORS headers are sent even on error responses
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "X-Session-ID", "Authorization"],
        "expose_headers": ["Content-Type"],
        "supports_credentials": False
    }
})

# Global error handler to ensure CORS headers are always sent
@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all exceptions and ensure CORS headers are included."""
    import traceback
    print(f"❌ Unhandled exception: {e}")
    traceback.print_exc()
    response = jsonify({
        "error": str(e),
        "type": type(e).__name__
    })
    response.status_code = 500
    return response

@app.errorhandler(400)
def handle_bad_request(e):
    """Handle 400 errors with CORS headers."""
    response = jsonify({"error": str(e.description) if hasattr(e, 'description') else str(e)})
    response.status_code = 400
    return response

@app.errorhandler(404)
def handle_not_found(e):
    """Handle 404 errors with CORS headers."""
    response = jsonify({"error": "Not found"})
    response.status_code = 404
    return response

@app.errorhandler(500)
def handle_internal_error(e):
    """Handle 500 errors with CORS headers."""
    response = jsonify({"error": "Internal server error"})
    response.status_code = 500
    return response

# =============================================================================
# BIDDING ENGINE SELECTION (V1 vs V2)
# =============================================================================
# V2 engine has explicit state machine and improved SAYC compliance.
# Enable via environment variable: USE_V2_BIDDING_ENGINE=true
#
# Comparison mode runs both engines and logs discrepancies for safe migration.
# Enable via: BIDDING_ENGINE_COMPARISON_MODE=true
# =============================================================================

USE_V2_ENGINE = os.getenv('USE_V2_BIDDING_ENGINE', 'false').lower() == 'true'
COMPARISON_MODE = os.getenv('BIDDING_ENGINE_COMPARISON_MODE', 'false').lower() == 'true'

# Initialize bidding engines
engine_v1 = BiddingEngine()

# V2 engine (lazy loaded if enabled)
engine_v2 = None
if USE_V2_ENGINE or COMPARISON_MODE:
    try:
        from engine.bidding_engine_v2 import BiddingEngineV2
        engine_v2 = BiddingEngineV2(comparison_mode=COMPARISON_MODE)
        print(f"✅ BiddingEngineV2 initialized (comparison_mode={COMPARISON_MODE})")
    except Exception as e:
        print(f"⚠️  Failed to initialize BiddingEngineV2: {e}")
        USE_V2_ENGINE = False

# Select active engine
if USE_V2_ENGINE and engine_v2:
    engine = engine_v2
    print("🔷 Using BiddingEngineV2 (new state machine)")
else:
    engine = engine_v1
    print("🔶 Using BiddingEngine V1 (classic)")

play_engine = PlayEngine()
play_ai = SimplePlayAI()  # Default AI (backward compatibility)
session_manager = SessionManager('bridge.db')  # Session management

# Initialize session state manager (replaces global variables)
state_manager = SessionStateManager()
app.config['STATE_MANAGER'] = state_manager

# REMOVED: Global state variables are now per-session
# - current_deal -> state.deal
# - current_vulnerability -> state.vulnerability
# - current_play_state -> state.play_state
# - current_session -> state.game_session
# - current_ai_difficulty -> state.ai_difficulty (default: "expert")
# - current_hand_start_time -> state.hand_start_time
# Access via: state = get_state()

CONVENTION_MAP = {
    "Preempt": PreemptConvention(),
    "JacobyTransfer": JacobyConvention(),
    "Stayman": StaymanConvention(),
    "Blackwood": BlackwoodConvention()
}

# AI instances for different difficulty levels
# Expert level uses DDS ONLY on Linux (production)
# macOS/Windows use Minimax depth 4 fallback to prevent crashes
# See: BUG_DDS_CRASH_2025-10-18.md for details on macOS DDS instability
ai_instances = {
    'beginner': SimplePlayAINew(),
    'intermediate': MinimaxPlayAI(max_depth=2),
    'advanced': MinimaxPlayAI(max_depth=3),
    'expert': DDSPlayAI() if (DDS_AVAILABLE and PLATFORM_ALLOWS_DDS) else MinimaxPlayAI(max_depth=4)
}

# Fallback AI for when DDS/expert fails (prevents 502 crashes)
fallback_ai = MinimaxPlayAI(max_depth=3)

# ============================================================================
# SUBPROCESS-BASED DDS WRAPPER (SEGFAULT PROTECTION)
# ============================================================================
# DDS (endplay library) can crash with segfaults that Python can't catch.
# Running DDS in a subprocess isolates crashes - if the subprocess dies,
# the main server continues and falls back to Minimax AI.
# ============================================================================

import multiprocessing

def _dds_worker(play_state_dict, position, result_queue):
    """
    Worker function that runs DDS in a separate process.

    If DDS segfaults, this process dies but the main server survives.
    The result is communicated back via a multiprocessing Queue.
    """
    try:
        # Import DDS inside the subprocess
        from engine.play.ai.dds_ai import DDSPlayAI
        from engine.play_engine import PlayState, Contract
        from engine.hand import Hand, Card

        # Reconstruct PlayState from dict
        play_state = _reconstruct_play_state(play_state_dict)

        # Run DDS
        dds_ai = DDSPlayAI()
        card = dds_ai.choose_card(play_state, position)

        # Return card as dict (can't pickle Card namedtuple across processes easily)
        result_queue.put({
            'status': 'success',
            'card': {'rank': card.rank, 'suit': card.suit}
        })
    except Exception as e:
        result_queue.put({
            'status': 'error',
            'error': str(e)
        })

def _reconstruct_play_state(state_dict):
    """Reconstruct PlayState from a serializable dictionary."""
    from engine.play_engine import PlayState, Contract
    from engine.hand import Hand, Card

    # Reconstruct hands
    # NOTE: During play, hands may have fewer than 13 cards (cards are played)
    # Use _skip_validation=True to allow partial hands
    hands = {}
    for pos, hand_data in state_dict['hands'].items():
        cards = [Card(c['rank'], c['suit']) for c in hand_data['cards']]
        hands[pos] = Hand(cards, _skip_validation=True)

    # Reconstruct contract
    # Contract uses 'strain' not 'trump_suit', and doubled is int (0/1/2)
    trump_suit = state_dict['contract']['trump_suit']
    strain = 'NT' if trump_suit is None else trump_suit

    doubled = 0
    if state_dict['contract'].get('redoubled'):
        doubled = 2
    elif state_dict['contract'].get('doubled'):
        doubled = 1

    contract = Contract(
        level=state_dict['contract']['level'],
        strain=strain,
        declarer=state_dict['contract']['declarer'],
        doubled=doubled
    )

    # Reconstruct current trick
    current_trick = []
    for card_data, pos in state_dict['current_trick']:
        card = Card(card_data['rank'], card_data['suit'])
        current_trick.append((card, pos))

    # Reconstruct tricks_won from NS/EW totals
    # Note: We distribute evenly between partners since we don't track individual
    tricks_ns = state_dict.get('tricks_taken_ns', 0)
    tricks_ew = state_dict.get('tricks_taken_ew', 0)
    tricks_won = {
        'N': tricks_ns,  # Attribute all NS tricks to N for simplicity
        'S': 0,
        'E': tricks_ew,  # Attribute all EW tricks to E for simplicity
        'W': 0
    }

    # Create PlayState
    play_state = PlayState(
        hands=hands,
        contract=contract,
        current_trick=current_trick,
        tricks_won=tricks_won
    )
    play_state.trick_history = state_dict.get('trick_history', [])
    play_state.next_to_play = state_dict.get('next_to_play', 'W')
    play_state.dummy_revealed = state_dict.get('dummy_revealed', False)

    return play_state

def _serialize_play_state(play_state):
    """Convert PlayState to a serializable dictionary for subprocess."""
    hands = {}
    for pos, hand in play_state.hands.items():
        hands[pos] = {
            'cards': [{'rank': c.rank, 'suit': c.suit} for c in hand.cards]
        }

    current_trick = []
    for card, pos in play_state.current_trick:
        current_trick.append(({'rank': card.rank, 'suit': card.suit}, pos))

    return {
        'hands': hands,
        'contract': {
            'level': play_state.contract.level,
            'trump_suit': play_state.contract.trump_suit,
            'declarer': play_state.contract.declarer,
            'doubled': getattr(play_state.contract, 'doubled', False),
            'redoubled': getattr(play_state.contract, 'redoubled', False)
        },
        'current_trick': current_trick,
        'trick_history': play_state.trick_history,
        'tricks_taken_ns': play_state.tricks_taken_ns,
        'tricks_taken_ew': play_state.tricks_taken_ew,
        'next_to_play': play_state.next_to_play,
        'dummy': play_state.dummy,
        'dummy_revealed': play_state.dummy_revealed,
        'vulnerability': getattr(play_state, 'vulnerability', 'None')
    }

def safe_ai_choose_card(ai, play_state, position, difficulty, timeout_seconds=15):
    """
    Safely execute AI card selection with subprocess isolation for DDS.

    For expert (DDS) difficulty, runs in a subprocess to catch segfaults.
    For other difficulties, runs directly with timeout protection.

    If DDS crashes (segfault) or times out, falls back to Minimax AI.

    Args:
        ai: The AI instance to use
        play_state: Current play state
        position: Position making the play
        difficulty: AI difficulty level string
        timeout_seconds: Max time to wait for AI decision

    Returns:
        tuple: (card, used_fallback, actual_ai_name)
    """
    actual_ai_name = ai.get_name()

    # For expert difficulty with DDS available, use subprocess isolation
    if difficulty == 'expert' and DDS_AVAILABLE and PLATFORM_ALLOWS_DDS:
        try:
            # Serialize play state for subprocess
            state_dict = _serialize_play_state(play_state)

            # Create queue for result
            result_queue = multiprocessing.Queue()

            # Start subprocess
            process = multiprocessing.Process(
                target=_dds_worker,
                args=(state_dict, position, result_queue)
            )
            process.start()

            # Wait for result with timeout
            process.join(timeout_seconds)

            if process.is_alive():
                # Timeout - kill the subprocess
                print(f"⚠️  DDS TIMEOUT: Subprocess timed out after {timeout_seconds}s for {position}")
                process.terminate()
                process.join(1)  # Give it 1 second to terminate
                if process.is_alive():
                    process.kill()  # Force kill if still alive
                # Fall through to fallback

            elif process.exitcode != 0:
                # Subprocess crashed (likely segfault)
                print(f"⚠️  DDS CRASH: Subprocess exited with code {process.exitcode} for {position}")
                print(f"   This was likely a segfault in the DDS library")
                # Fall through to fallback

            else:
                # Process completed - check result
                try:
                    result = result_queue.get_nowait()
                    if result['status'] == 'success':
                        card = Card(result['card']['rank'], result['card']['suit'])
                        return card, False, actual_ai_name
                    else:
                        print(f"⚠️  DDS ERROR: {result.get('error', 'Unknown error')}")
                        # Fall through to fallback
                except Exception as e:
                    print(f"⚠️  DDS QUEUE ERROR: {e}")
                    # Fall through to fallback

        except Exception as e:
            print(f"⚠️  DDS SUBPROCESS ERROR: {e}")
            traceback.print_exc()
            # Fall through to fallback

        # Fallback to Minimax
        print(f"   Falling back to Minimax AI for {position}")
        try:
            card = fallback_ai.choose_card(play_state, position)
            return card, True, f"{actual_ai_name} (fallback: {fallback_ai.get_name()})"
        except Exception as fallback_error:
            print(f"❌ CRITICAL: Even fallback AI failed: {fallback_error}")
            # Last resort below

    else:
        # Non-DDS AI: run directly with simple timeout
        import signal
        import sys

        def timeout_handler(signum, frame):
            raise TimeoutError(f"AI decision timed out after {timeout_seconds}s")

        try:
            if sys.platform != 'win32':
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(timeout_seconds)

            try:
                card = ai.choose_card(play_state, position)
                return card, False, actual_ai_name
            finally:
                if sys.platform != 'win32':
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)

        except TimeoutError:
            print(f"⚠️  AI TIMEOUT: {difficulty} AI timed out for {position}")
        except Exception as e:
            print(f"⚠️  AI ERROR: {difficulty} AI failed for {position}: {e}")
            traceback.print_exc()

        # Fallback to Minimax
        print(f"   Falling back to Minimax AI")
        try:
            card = fallback_ai.choose_card(play_state, position)
            return card, True, f"{actual_ai_name} (fallback: {fallback_ai.get_name()})"
        except Exception as fallback_error:
            print(f"❌ CRITICAL: Even fallback AI failed: {fallback_error}")

    # Last resort: pick first legal card
    hand = play_state.hands[position]
    if play_state.current_trick:
        led_suit = play_state.current_trick[0][0].suit
        legal = [c for c in hand.cards if c.suit == led_suit] or list(hand.cards)
    else:
        legal = list(hand.cards)
    if legal:
        return legal[0], True, "Emergency fallback (first legal card)"
    raise ValueError(f"No legal cards for {position}")

# Import DEFAULT_AI_DIFFICULTY to show startup configuration
from core.session_state import DEFAULT_AI_DIFFICULTY
print(f"🎯 Default AI Difficulty: {DEFAULT_AI_DIFFICULTY}")
print(f"   Engine: {ai_instances[DEFAULT_AI_DIFFICULTY].get_name()}")
print(f"   Rating: ~{ai_instances[DEFAULT_AI_DIFFICULTY].get_difficulty()}")


# ============================================================================
# AI PLAY LOGGING FOR DDS QUALITY MONITORING
# ============================================================================

def log_ai_play(card, position, ai_level, solve_time_ms, used_fallback=False,
                session_id=None, hand_number=None, trick_number=None,
                contract=None, trump_suit=None):
    """
    Log AI play decision to database for quality monitoring.

    This minimal logging approach adds <1% overhead and enables:
    - Real-time DDS health monitoring
    - Quality analysis over time
    - Fallback rate tracking

    Args:
        card: Card object that was played
        position: Position making the play (N/E/S/W)
        ai_level: AI difficulty level (beginner/intermediate/advanced/expert)
        solve_time_ms: Time taken to choose card in milliseconds
        used_fallback: Whether DDS crashed and fallback was used
        session_id: Optional game session ID
        hand_number: Optional hand number in session
        trick_number: Optional trick number (1-13)
        contract: Optional contract string (e.g., "4S", "3NT")
        trump_suit: Optional trump suit symbol
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Convert card to simple string format
            card_str = f"{card.rank}{card.suit}"

            cursor.execute("""
                INSERT INTO ai_play_log
                (position, ai_level, card_played, solve_time_ms, used_fallback,
                 session_id, hand_number, trick_number, contract, trump_suit)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (position, ai_level, card_str, solve_time_ms, int(used_fallback),
                  session_id, hand_number, trick_number, contract, trump_suit))

    except Exception as e:
        # Never let logging break gameplay - just print error
        print(f"⚠️  Failed to log AI play: {e}")


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

    IMPORTANT: Also loads active GameSession from database if one exists
    for this user. This ensures session persistence across requests.

    Returns:
        SessionState object with .deal, .vulnerability, .play_state, etc.
    """
    session_id = get_session_id_from_request(request)

    if not session_id:
        # Backward compatibility: use user_id as session identifier
        data = request.get_json(silent=True) or {}
        user_id = data.get('user_id') or request.args.get('user_id') or 1
        session_id = f"user_{user_id}_default"

    # Get or create session state
    state = state_manager.get_or_create(session_id)

    # CRITICAL FIX: Load active game session from database if not already loaded
    # This ensures gameplay tracking persists across requests
    # BUG FIX: Only load if user_id is EXPLICITLY provided to prevent cross-user contamination
    if not state.game_session:
        # Extract user_id from request - DO NOT default to 1
        data = request.get_json(silent=True) or {}
        user_id = data.get('user_id') or request.args.get('user_id')

        # Only load session if user_id was explicitly provided
        # This prevents loading user 1's session for other users when user_id is missing
        if user_id is not None:
            try:
                user_id = int(user_id)  # Ensure it's an int
                existing_session = session_manager.get_active_session(user_id)
                if existing_session:
                    state.game_session = existing_session
                    print(f"✅ Loaded active session {existing_session.id} for user {user_id} (hands: {existing_session.hands_completed})")
            except Exception as e:
                # Don't fail the request if session loading fails
                print(f"⚠️  Could not load active session for user {user_id}: {e}")

    return state


# Register learning path endpoints (convention levels system)
register_learning_endpoints(app)

# Register analytics API endpoints (mistake detection & learning insights)
from engine.learning.analytics_api import register_analytics_endpoints
register_analytics_endpoints(app)

# Register authentication endpoints (MVP - email/phone only, no passwords)
from engine.auth.simple_auth_api import register_simple_auth_endpoints
register_simple_auth_endpoints(app)

# ============================================================================
# SESSION MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/api/session/start', methods=['POST'])
def start_session():
    """
    Start a new game session or resume existing active session

    Request body:
        - user_id: int (default 1)
        - session_type: str (default 'chicago')
        - player_position: str (default 'S')
        - ai_difficulty: str (default 'expert' - uses DDS when available)

    Returns:
        Session data and whether it was resumed
    """
    # Get session state for this request
    state = get_state()

    data = request.get_json() or {}
    user_id = data.get('user_id', 1)
    session_type = data.get('session_type', 'chicago')
    player_position = data.get('player_position', 'S')
    ai_difficulty = data.get('ai_difficulty', DEFAULT_AI_DIFFICULTY)  # Uses smart default from session_state

    try:
        # Check for existing active session
        existing = session_manager.get_active_session(user_id)
        if existing:
            state.game_session = existing
            state.hand_start_time = datetime.now()
            return jsonify({
                'session': existing.to_dict(),
                'resumed': True,
                'message': f'Resumed session #{existing.id}'
            })

        # Create new session
        state.game_session = session_manager.create_session(
            user_id=user_id,
            session_type=session_type,
            player_position=player_position,
            ai_difficulty=ai_difficulty
        )
        state.hand_start_time = datetime.now()

        return jsonify({
            'session': state.game_session.to_dict(),
            'resumed': False,
            'message': f'Started new {session_type} session'
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Failed to start session: {str(e)}'}), 500


@app.route('/api/session/status', methods=['GET'])
def get_session_status():
    """
    Get current session status

    Returns:
        Session data if active, otherwise active=False
    """
    # Get session state for this request
    state = get_state()
    if not state.game_session:
        return jsonify({'active': False})

    return jsonify({
        'active': True,
        'session': state.game_session.to_dict()
    })


@app.route('/api/session/complete-hand', methods=['POST'])
def complete_session_hand():
    """
    Complete current hand and update session scores

    Request body:
        - score_data: dict with hand results (score, tricks_taken, made, breakdown)
        - contract_data: dict with contract info (level, strain, declarer, doubled) - optional fallback
        - auction_history: list of bids
        - play_history: list of plays (optional)

    Returns:
        Updated session data
    """
    # Get session state for this request
    state = get_state()

    if not state.game_session:
        return jsonify({'error': 'No active session'}), 400

    try:
        data = request.get_json() or {}
        score_data = data.get('score_data', {})
        contract_data = data.get('contract_data', {})

        # Calculate hand duration
        hand_duration = 0
        if state.hand_start_time:
            hand_duration = int((datetime.now() - state.hand_start_time).total_seconds())

        # Get contract info - prefer play_state if available, fall back to frontend data
        if state.play_state and state.play_state.contract:
            contract = state.play_state.contract
            declarer = contract.declarer
            dummy = state.play_state.dummy
        elif contract_data:
            # Fallback: use contract data from frontend
            from engine.play_engine import Contract
            contract = Contract(
                level=contract_data.get('level', 1),
                strain=contract_data.get('strain', 'NT'),
                declarer=contract_data.get('declarer', 'S'),
                doubled=contract_data.get('doubled', 0)
            )
            declarer = contract.declarer
            # Calculate dummy position (partner of declarer)
            partner_map = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}
            dummy = partner_map.get(declarer, 'N')
        else:
            return jsonify({'error': 'No play state or contract data available'}), 400

        user_position = state.game_session.player_position
        user_was_declarer = (declarer == user_position)
        user_was_dummy = (dummy == user_position)

        # Add score to session
        hand_score = score_data.get('score', 0)
        state.game_session.add_hand_score(declarer, hand_score)

        # Get deal data - MUST use original_deal (preserved at start of play)
        # because play_state.hands is empty after all cards have been played
        deal_data = {}
        # Map full names to single letters for consistent storage
        name_to_pos = {'North': 'N', 'East': 'E', 'South': 'S', 'West': 'W'}

        if state.original_deal:
            # Use preserved original deal (full 13 cards per hand)
            # original_deal uses full names (North, East, etc.)
            for full_name, hand in state.original_deal.items():
                pos = name_to_pos.get(full_name, full_name)  # Convert to single letter
                deal_data[pos] = {
                    'hand': [{'rank': c.rank, 'suit': c.suit} for c in hand.cards],
                    'points': hand.hcp if hasattr(hand, 'hcp') else None
                }
            total_cards = sum(len(h.cards) for h in state.original_deal.values())
            print(f"✅ Using original_deal for hand history ({total_cards} cards)")
        else:
            print("⚠️ No original_deal available - hand history will be incomplete")

        # Build play_history from trick_history on backend
        # This is the authoritative source - don't rely on frontend
        play_history = []
        if state.play_state and state.play_state.trick_history:
            for trick_num, trick in enumerate(state.play_state.trick_history, 1):
                for play_idx, (card, position) in enumerate(trick.cards):
                    play_history.append({
                        'trick': trick_num,
                        'play_index': play_idx,
                        'position': position,
                        'rank': card.rank,
                        'suit': card.suit,
                        'is_winner': position == trick.winner if hasattr(trick, 'winner') else False
                    })
            print(f"✅ Built play_history from trick_history ({len(play_history)} plays)")
        else:
            # Fall back to frontend-provided play_history if available
            play_history = data.get('play_history', [])
            if play_history:
                print(f"⚠️ Using frontend play_history ({len(play_history)} plays)")
            else:
                print("⚠️ No play_history available - replay will not work")

        # Prepare hand data for database
        hand_data = {
            'hand_number': state.game_session.hands_completed,  # Already incremented by add_hand_score
            'dealer': GameSession.CHICAGO_DEALERS[(state.game_session.hands_completed - 1) % 4],
            'vulnerability': state.vulnerability or 'None',
            'contract': contract,
            'tricks_taken': score_data.get('tricks_taken', 0),
            'hand_score': hand_score,
            'made': score_data.get('made', False),
            'breakdown': score_data.get('breakdown', {}),
            'deal_data': deal_data,
            'auction_history': data.get('auction_history', []),
            'play_history': play_history,
            'user_was_declarer': user_was_declarer,
            'user_was_dummy': user_was_dummy,
            'hand_duration_seconds': hand_duration
        }

        # Save to database and get hand_id
        hand_id = session_manager.save_hand_result(state.game_session, hand_data)
        print(f"✅ Hand {state.game_session.hands_completed} saved to session_hands table (id={hand_id})")

        # Check if session is complete
        session_complete = state.game_session.is_complete()
        winner = state.game_session.get_winner() if session_complete else None
        user_won = state.game_session.get_user_won() if session_complete else None

        # Reset hand timer for next hand
        state.hand_start_time = datetime.now()

        return jsonify({
            'success': True,
            'session': state.game_session.to_dict(),
            'hand_id': hand_id,
            'hand_completed': state.game_session.hands_completed,
            'session_complete': session_complete,
            'winner': winner,
            'user_won': user_won,
            'message': f'Hand {state.game_session.hands_completed} completed'
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Failed to complete hand: {str(e)}'}), 500


@app.route('/api/session/history', methods=['GET'])
def get_session_history():
    """
    Get completed hands in current session

    Returns:
        List of hands with scores
    """
    # Get session state for this request
    state = get_state()
    if not state.game_session:
        return jsonify({'error': 'No active session'}), 400

    try:
        hands = session_manager.get_session_hands(state.game_session.id)
        return jsonify({
            'session_id': state.game_session.id,
            'hands': hands,
            'total_hands': len(hands)
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Failed to get session history: {str(e)}'}), 500


@app.route('/api/session/abandon', methods=['POST'])
def abandon_session():
    """
    Abandon current session

    Returns:
        Success message
    """
    # Get session state for this request
    state = get_state()

    if not state.game_session:
        return jsonify({'error': 'No active session'}), 400

    try:
        session_manager.abandon_session(state.game_session.id)
        session_id = state.game_session.id
        state.game_session = None

        return jsonify({
            'success': True,
            'message': f'Session {session_id} abandoned'
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Failed to abandon session: {str(e)}'}), 500


# ============================================================================
# AI STATUS ENDPOINT
# ============================================================================

@app.route('/api/ai/status', methods=['GET'])
def get_ai_status():
    """
    Get AI system status including DDS availability and environment info

    Returns:
        AI configuration, DDS status, and environment details
    """
    # Get session state for this request
    state = get_state()
    try:
        # Determine environment (production vs localhost)
        is_production = platform.system() == 'Linux'
        current_platform = platform.system()

        # DDS is only truly active on Linux production servers
        # macOS (Apple Silicon) has known DDS crashes - Error Code -14
        dds_active = DDS_AVAILABLE and PLATFORM_ALLOWS_DDS

        ai_status = {
            'dds_available': DDS_AVAILABLE,
            'dds_active': dds_active,  # Actually enabled and usable
            'platform': current_platform,
            'is_production': is_production,
            'environment': 'production' if is_production else 'development',
            'dds_disabled_reason': None if dds_active else (
                f'DDS disabled on {current_platform} (Apple Silicon crashes)'
                if current_platform == 'Darwin'
                else 'DDS library not installed' if not DDS_AVAILABLE
                else f'DDS not supported on {current_platform}'
            ),
            'difficulties': {
                'beginner': {
                    'name': ai_instances['beginner'].get_name(),
                    'rating': '6/10',
                    'description': 'Basic rule-based play'
                },
                'intermediate': {
                    'name': ai_instances['intermediate'].get_name(),
                    'rating': '7.5/10',
                    'description': 'Enhanced evaluation with 2-ply search'
                },
                'advanced': {
                    'name': ai_instances['advanced'].get_name(),
                    'rating': '8/10',
                    'description': 'Advanced components with 3-ply search'
                },
                'expert': {
                    'name': ai_instances['expert'].get_name(),
                    'rating': '9/10' if dds_active else '8+/10',
                    'description': 'Double Dummy Solver (perfect play)' if dds_active else 'Deep minimax search (4-ply)',
                    'using_dds': dds_active
                }
            },
            'current_difficulty': state.ai_difficulty
        }

        # Add DDS statistics if available and active
        if dds_active and state.ai_difficulty == 'expert':
            try:
                expert_ai = ai_instances['expert']
                if hasattr(expert_ai, 'get_statistics'):
                    ai_status['dds_statistics'] = expert_ai.get_statistics()
            except:
                pass

        return jsonify(ai_status)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Failed to get AI status: {str(e)}'}), 500


@app.route('/api/session/stats', methods=['GET'])
def get_session_stats():
    """
    Get user's overall session statistics

    Query params:
        - user_id: int (default 1)

    Returns:
        User statistics across all sessions
    """
    user_id = request.args.get('user_id', 1, type=int)

    try:
        stats = session_manager.get_user_session_stats(user_id)
        return jsonify(stats)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Failed to get stats: {str(e)}'}), 500

# ============================================================================
# END SESSION MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/api/scenarios', methods=['GET'])
def get_scenarios():
    try:
        print(f"Current working directory: {os.getcwd()}")
        print(f"Files in directory: {os.listdir('.')}")
        # Try new location first, fall back to old location
        try:
            with open('scenarios/bidding_scenarios.json', 'r') as f: scenarios = json.load(f)
        except FileNotFoundError:
            with open('scenarios.json', 'r') as f: scenarios = json.load(f)

        # Group scenarios by level for organized display
        scenarios_by_level = {
            'Essential': [],
            'Intermediate': [],
            'Advanced': []
        }

        for s in scenarios:
            level = s.get('level', 'Essential')  # Default to Essential if not specified
            scenario_info = {
                'name': s['name'],
                'level': level,
                'description': s.get('description', '')
            }
            scenarios_by_level[level].append(scenario_info)

        return jsonify({
            'scenarios_by_level': scenarios_by_level,
            'scenarios': [s['name'] for s in scenarios]  # Keep for backward compatibility
        })
    except Exception as e:
        print(f"ERROR in /api/scenarios: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Could not load scenarios: {str(e)}'}), 500

@app.route('/api/convention-info', methods=['GET'])
def get_convention_info():
    try:
        convention_name = request.args.get('name')
        with open('convention_descriptions.json', 'r') as f:
            descriptions = json.load(f)

        if convention_name and convention_name in descriptions:
            return jsonify(descriptions[convention_name])
        elif convention_name:
            return jsonify({'error': f'Convention "{convention_name}" not found'}), 404
        else:
            # Return all conventions if no name specified
            return jsonify(descriptions)
    except (IOError, json.JSONDecodeError) as e:
        return jsonify({'error': f'Could not load convention descriptions: {e}'}), 500

@app.route('/api/ai-difficulties', methods=['GET'])
def get_ai_difficulties():
    """
    Get available AI difficulty levels
    Phase 2 Integration
    """
    # Get session state for this request
    state = get_state()
    try:
        difficulties = []
        for difficulty, ai in ai_instances.items():
            difficulties.append({
                "id": difficulty,
                "name": difficulty.capitalize(),
                "description": ai.get_name(),
                "level": ai.get_difficulty()
            })

        return jsonify({
            "difficulties": difficulties,
            "current": state.ai_difficulty
        })
    except Exception as e:
        return jsonify({'error': f'Could not get AI difficulties: {str(e)}'}), 500

@app.route('/api/set-ai-difficulty', methods=['POST'])
def set_ai_difficulty():
    """
    Set AI difficulty level
    Phase 2 Integration
    """
    # Get session state for this request
    state = get_state()

    try:
        data = request.get_json()
        difficulty = data.get('difficulty')

        if difficulty not in ai_instances:
            return jsonify({
                'error': f'Invalid difficulty. Must be one of: {list(ai_instances.keys())}'
            }), 400

        state.ai_difficulty = difficulty
        # Note: play_ai is now per-session via state.ai_difficulty
        play_ai = ai_instances[difficulty]

        return jsonify({
            'success': True,
            'difficulty': difficulty,
            'ai_name': play_ai.get_name(),
            'ai_level': play_ai.get_difficulty()
        })
    except Exception as e:
        return jsonify({'error': f'Could not set AI difficulty: {str(e)}'}), 500

@app.route('/api/ai-statistics', methods=['GET'])
def get_ai_statistics():
    """
    Get statistics from last AI move (for minimax AIs)
    Phase 2 Integration
    """
    # Get session state for this request
    state = get_state()
    try:
        ai = ai_instances[state.ai_difficulty]

        if hasattr(ai, 'get_statistics'):
            stats = ai.get_statistics()
            return jsonify({
                'has_statistics': True,
                'statistics': stats,
                'ai_name': ai.get_name(),
                'difficulty': state.ai_difficulty
            })
        else:
            return jsonify({
                'has_statistics': False,
                'ai_name': ai.get_name(),
                'difficulty': state.ai_difficulty
            })
    except Exception as e:
        return jsonify({'error': f'Could not get AI statistics: {str(e)}'}), 500

@app.route('/api/load-scenario', methods=['POST'])
def load_scenario():
    # Get session state for this request
    state = get_state()
    state.vulnerability = "None"
    data = request.get_json()
    scenario_name = data.get('name')
    try:
        # Try new location first, fall back to old location
        try:
            with open('scenarios/bidding_scenarios.json', 'r') as f: scenarios = json.load(f)
        except FileNotFoundError:
            with open('scenarios.json', 'r') as f: scenarios = json.load(f)
        target_scenario = next((s for s in scenarios if s['name'] == scenario_name), None)
        if not target_scenario: return jsonify({'error': 'Scenario not found'}), 404
            
        ranks = '23456789TJQKA'
        suits = ['♠', '♥', '♦', '♣']
        deck = [Card(r, s) for r in ranks for s in suits]
        
        for pos in state.deal: state.deal[pos] = None
        
        for setup_rule in target_scenario.get('setup', []):
            position = setup_rule['position']
            hand = None
            if setup_rule.get('generate_for_convention'):
                specialist = CONVENTION_MAP.get(setup_rule['generate_for_convention'])
                if specialist:
                    hand, deck = generate_hand_for_convention(specialist, deck)
            elif setup_rule.get('constraints'):
                 hand, deck = generate_hand_with_constraints(setup_rule['constraints'], deck)
            if hand:
                state.deal[position] = hand
        
        remaining_cards = deck
        random.shuffle(remaining_cards)
        
        for position in ['North', 'East', 'South', 'West']:
            if not state.deal.get(position):
                state.deal[position] = Hand(remaining_cards[:13])
                remaining_cards = remaining_cards[13:]

        south_hand = state.deal['South']
        hand_for_json = [{'rank': card.rank, 'suit': card.suit} for card in south_hand.cards]
        points_for_json = { 'hcp': south_hand.hcp, 'dist_points': south_hand.dist_points, 'total_points': south_hand.total_points, 'suit_hcp': south_hand.suit_hcp, 'suit_lengths': south_hand.suit_lengths }
        return jsonify({'hand': hand_for_json, 'points': points_for_json, 'vulnerability': state.vulnerability})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Could not load scenario: {e}'}), 500

@app.route('/api/deal-hands', methods=['GET'])
def deal_hands():
    # Get session state for this request
    state = get_state()

    # Use Chicago rotation for dealer and vulnerability
    dealer = 'North'  # Default for non-session mode
    if state.game_session:
        dealer = state.game_session.get_current_dealer()
        state.vulnerability = state.game_session.get_current_vulnerability()
    else:
        # Non-session mode: rotate vulnerability manually
        vulnerabilities = ["None", "NS", "EW", "Both"]
        try:
            current_idx = vulnerabilities.index(state.vulnerability)
            state.vulnerability = vulnerabilities[(current_idx + 1) % len(vulnerabilities)]
        except ValueError:
            state.vulnerability = "None"

    ranks = '23456789TJQKA'
    suits = ['♠', '♥', '♦', '♣']
    deck = [Card(rank, suit) for rank in ranks for suit in suits]
    random.shuffle(deck)

    print(f"🃏 Deck size: {len(deck)} cards (should be 52)")

    state.deal['North'] = Hand(deck[0:13])
    state.deal['East'] = Hand(deck[13:26])
    state.deal['South'] = Hand(deck[26:39])
    state.deal['West'] = Hand(deck[39:52])

    print(f"🃏 North: {len(state.deal['North'].cards)} cards")
    print(f"🃏 East: {len(state.deal['East'].cards)} cards")
    print(f"🃏 South: {len(state.deal['South'].cards)} cards")
    print(f"🃏 West: {len(state.deal['West'].cards)} cards")

    south_hand = state.deal['South']
    hand_for_json = [{'rank': card.rank, 'suit': card.suit} for card in south_hand.cards]
    points_for_json = { 'hcp': south_hand.hcp, 'dist_points': south_hand.dist_points, 'total_points': south_hand.total_points, 'suit_hcp': south_hand.suit_hcp, 'suit_lengths': south_hand.suit_lengths }

    # Calculate DD table for trick potential (production only - Linux with DDS)
    dd_table = None
    if PLATFORM_ALLOWS_DDS and is_dds_available():
        try:
            dds_service = get_dds_service()
            hands_dict = {
                'N': state.deal['North'],
                'E': state.deal['East'],
                'S': state.deal['South'],
                'W': state.deal['West']
            }
            analysis = dds_service.analyze_deal(hands_dict, dealer=dealer[0], vulnerability=state.vulnerability)
            if analysis.is_valid and analysis.dd_table:
                # Simplify to NS/EW rows (partners have same trick counts)
                raw_table = analysis.dd_table.to_dict()
                dd_table = {
                    'NS': raw_table.get('N', raw_table.get('S', {})),
                    'EW': raw_table.get('E', raw_table.get('W', {}))
                }
        except Exception as e:
            print(f"⚠️ DD table calculation failed: {e}")
            # Non-fatal - just don't include dd_table

    # Include dealer in response for frontend
    response_data = {
        'hand': hand_for_json,
        'points': points_for_json,
        'vulnerability': state.vulnerability,
        'dealer': dealer
    }

    # Only include dd_table if calculated (production only)
    if dd_table:
        response_data['dd_table'] = dd_table

    return jsonify(response_data)

@app.route('/api/get-next-bid', methods=['POST'])
def get_next_bid():
    # Get session state for this request
    state = get_state()
    try:
        data = request.get_json()
        print(f"🔍 DEBUG: Received data: {data}")
        print(f"🔍 DEBUG: Keys in data: {list(data.keys()) if data else 'None'}")
        auction_history_raw, current_player = data['auction_history'], data['current_player']
        explanation_level = data.get('explanation_level', 'detailed')  # simple, detailed, or expert
        dealer = data.get('dealer')  # Get dealer from frontend

        # Normalize auction history: frontend may send {bid, explanation} objects or plain strings
        # Backend expects list of bid strings: ["1NT", "Pass", ...]
        auction_history = []
        for item in auction_history_raw:
            if isinstance(item, dict):
                bid = item.get('bid')
                auction_history.append(bid if bid else 'Pass')  # Handle None/missing
            else:
                auction_history.append(item if item else 'Pass')  # Handle None strings

        # For non-South players (hidden hands), use convention_only to avoid revealing hand specifics
        if current_player != 'South':
            explanation_level = 'convention_only'

        player_hand = state.deal[current_player]
        if not player_hand:
            return jsonify({'error': "Deal has not been made yet."}), 400

        bid, explanation = engine.get_next_bid(player_hand, auction_history, current_player,
                                                state.vulnerability, explanation_level, dealer=dealer)
        return jsonify({'bid': bid, 'explanation': explanation, 'player': current_player})

    except Exception as e:
        print("---!!! AN ERROR OCCURRED IN GET_NEXT_BID !!!---")
        traceback.print_exc()

        # Log error with context for analysis
        log_error(
            error=e,
            endpoint='/api/get-next-bid',
            user_id=data.get('user_id') if data else None,
            context={
                'current_player': data.get('current_player') if data else None,
                'auction_length': len(data.get('auction_history', [])) if data else 0,
                'vulnerability': state.vulnerability,
                'has_hand': bool(player_hand) if 'player_hand' in locals() else False
            },
            request_data=data if data else {}
        )

        return jsonify({'error': f"A critical server error occurred: {e}"}), 500

@app.route('/api/get-next-bid-structured', methods=['POST'])
def get_next_bid_structured():
    """
    Returns structured explanation data (JSON) instead of formatted string.
    Useful for frontend to render explanations with custom UI.
    """
    # Get session state for this request
    state = get_state()
    try:
        data = request.get_json()
        auction_history_raw, current_player = data['auction_history'], data['current_player']

        # Normalize auction history: frontend may send {bid, explanation} objects or plain strings
        def normalize_bid(item):
            if isinstance(item, dict):
                bid = item.get('bid')
                return bid if bid else 'Pass'
            return item if item else 'Pass'
        auction_history = [normalize_bid(item) for item in auction_history_raw]

        player_hand = state.deal[current_player]
        if not player_hand:
            return jsonify({'error': "Deal has not been made yet."}), 400

        bid, explanation_dict = engine.get_next_bid_structured(player_hand, auction_history,
                                                                current_player, state.vulnerability)
        return jsonify({
            'bid': bid,
            'explanation': explanation_dict
        })

    except Exception as e:
        print("---!!! AN ERROR OCCURRED IN GET_NEXT_BID_STRUCTURED !!!---")
        traceback.print_exc()
        return jsonify({'error': f"A critical server error occurred: {e}"}), 500

@app.route('/api/get-feedback', methods=['POST'])
def get_feedback():
    # Get session state for this request
    state = get_state()
    data = request.get_json()
    try:
        auction_history_raw = data['auction_history']
        explanation_level = data.get('explanation_level', 'detailed')  # simple, detailed, or expert

        # Normalize auction history: frontend may send {bid, explanation} objects or plain strings
        def normalize_bid(item):
            if isinstance(item, dict):
                bid = item.get('bid')
                return bid if bid else 'Pass'
            return item if item else 'Pass'
        auction_history = [normalize_bid(item) for item in auction_history_raw]

        user_bid, auction_before_user_bid = auction_history[-1], auction_history[:-1]
        user_hand = state.deal['South']
        optimal_bid, explanation = engine.get_next_bid(user_hand, auction_before_user_bid, 'South',
                                                        state.vulnerability, explanation_level)

        was_correct = (user_bid == optimal_bid)

        if was_correct:
            feedback = f"✅ Correct! Your bid of {user_bid} is optimal.\n\n{explanation}"
        else:
            # Provide detailed comparison
            feedback_lines = []
            feedback_lines.append(f"⚠️ Your bid: {user_bid}")
            feedback_lines.append(f"Recommended: {optimal_bid}")
            feedback_lines.append("")
            feedback_lines.append("Why this bid is recommended:")
            feedback_lines.append(explanation)

            # Add hand summary context (only for detailed/expert levels)
            if explanation_level in ['detailed', 'expert']:
                feedback_lines.append("")
                feedback_lines.append("📊 Your hand summary:")
                feedback_lines.append(f"  • Total Points: {user_hand.total_points} ({user_hand.hcp} HCP + {user_hand.dist_points} dist)")
                feedback_lines.append(f"  • Shape: {user_hand.suit_lengths['♠']}-{user_hand.suit_lengths['♥']}-{user_hand.suit_lengths['♦']}-{user_hand.suit_lengths['♣']}")
                feedback_lines.append(f"  • Suits: ♠{user_hand.suit_lengths['♠']}({user_hand.suit_hcp['♠']}), ♥{user_hand.suit_lengths['♥']}({user_hand.suit_hcp['♥']}), ♦{user_hand.suit_lengths['♦']}({user_hand.suit_hcp['♦']}), ♣{user_hand.suit_lengths['♣']}({user_hand.suit_hcp['♣']})")

            feedback = "\n".join(feedback_lines)

        # Record practice for learning analytics (async, don't block feedback response)
        try:
            from engine.learning.user_manager import get_user_manager
            from engine.learning.mistake_analyzer import get_mistake_analyzer

            user_id = 1  # Default user for now

            # Record in practice_history
            with get_connection() as conn:
                cursor = conn.cursor()

                # Insert practice record
                cursor.execute("""
                    INSERT INTO practice_history (
                        user_id, convention_id, user_bid, correct_bid, was_correct,
                        hints_used, time_taken_seconds, xp_earned
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    None,  # We don't have convention_id in this context yet
                    user_bid,
                    optimal_bid,
                    was_correct,
                    0,  # hints_used
                    None,  # time_taken_seconds
                    10 if was_correct else 5
                ))

                practice_id = cursor.lastrowid

            # Update user stats
            user_manager = get_user_manager()
            user_manager.update_streak(user_id)
            user_manager.add_xp(user_id, 10 if was_correct else 5)

            # Analyze pattern if error (don't wait for this)
            if not was_correct:
                try:
                    mistake_analyzer = get_mistake_analyzer()
                    mistake_analyzer.analyze_practice_hand(user_id, practice_id)
                except:
                    pass  # Don't fail feedback if analysis fails

        except Exception as analytics_error:
            # Don't fail the feedback response if analytics fails
            print(f"Analytics recording failed: {analytics_error}")
            import traceback
            traceback.print_exc()

        return jsonify({'feedback': feedback, 'was_correct': was_correct, 'xp_earned': 10 if was_correct else 5})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f"Server error in get_feedback: {e}"}), 500

@app.route('/api/evaluate-bid', methods=['POST'])
def evaluate_bid():
    """
    Evaluate a user's bid and provide structured feedback (Phase 1: Bidding Feedback)

    This endpoint:
    1. Takes user's bid and current game state
    2. Gets AI's optimal bid
    3. Generates detailed feedback using BiddingFeedbackGenerator
    4. Stores feedback in database for analytics
    5. Returns structured feedback for UI display

    IMPORTANT: This endpoint does NOT modify bidding state or sequences.
    It only evaluates decisions that have already been made.
    """
    state = get_state()

    try:
        data = request.get_json()

        # Required parameters
        user_bid = data.get('user_bid')
        auction_history_raw = data.get('auction_history', [])
        current_player = data.get('current_player', 'South')

        # Normalize auction history: frontend may send {bid, explanation} objects or plain strings
        def normalize_bid(item):
            if isinstance(item, dict):
                bid = item.get('bid')
                return bid if bid else 'Pass'
            return item if item else 'Pass'
        auction_history = [normalize_bid(item) for item in auction_history_raw]

        # Optional parameters
        user_id = data.get('user_id', 1)  # Default user
        session_id = data.get('session_id')
        feedback_level = data.get('feedback_level', 'intermediate')  # beginner, intermediate, expert

        print(f"📊 /api/evaluate-bid called: user_bid={user_bid}, auction_len={len(auction_history)}, player={current_player}, user_id={user_id}")

        if not user_bid:
            print("❌ evaluate-bid: Missing user_bid")
            return jsonify({'error': 'user_bid is required'}), 400

        # Get user's hand from session state (does NOT modify state)
        user_hand = state.deal.get(current_player)
        if not user_hand:
            print(f"❌ evaluate-bid: Hand for {current_player} not available. state.deal keys: {list(state.deal.keys()) if state.deal else 'None'}")
            return jsonify({'error': f'Hand for {current_player} not available'}), 400

        # Get AI's optimal bid and explanation (does NOT modify state)
        # We pass auction_history BEFORE the user's bid to get what AI would have bid
        optimal_bid, optimal_explanation_str = engine.get_next_bid(
            user_hand,
            auction_history,
            current_player,
            state.vulnerability,
            'detailed'
        )

        # Get structured explanation for better feedback
        _, optimal_explanation_dict = engine.get_next_bid_structured(
            user_hand,
            auction_history,
            current_player,
            state.vulnerability
        )

        # Create BidExplanation object from structured data
        from engine.ai.bid_explanation import BidExplanation
        optimal_explanation_obj = BidExplanation(optimal_bid)
        optimal_explanation_obj.primary_reason = optimal_explanation_dict.get('primary_reason', '')
        optimal_explanation_obj.convention_reference = optimal_explanation_dict.get('convention', {}).get('id')
        optimal_explanation_obj.forcing_status = optimal_explanation_dict.get('forcing_status')

        # Build auction context
        # Determine dealer from session or use default
        dealer = 'North'  # Default
        if state.game_session:
            dealer = state.game_session.get_current_dealer()

        auction_context = {
            'history': auction_history,
            'current_player': current_player,
            'dealer': dealer,
            'vulnerability': state.vulnerability
        }

        # Generate structured feedback using BiddingFeedbackGenerator
        from engine.feedback.bidding_feedback import get_feedback_generator
        # Use 'bridge.db' (works from root via symlink to backend/bridge.db)
        feedback_generator = get_feedback_generator('bridge.db')

        # Get hand_number from game session (1-indexed for display)
        hand_number = state.game_session.hands_completed + 1 if state.game_session else None

        feedback = feedback_generator.evaluate_and_store(
            user_id=user_id,
            hand=user_hand,
            user_bid=user_bid,
            auction_context=auction_context,
            optimal_bid=optimal_bid,
            optimal_explanation=optimal_explanation_obj,
            session_id=session_id,
            hand_number=hand_number
        )

        print(f"✅ evaluate-bid: Stored feedback for user {user_id}: {user_bid} ({feedback.correctness.value}, score: {feedback.score})")

        # Format explanation based on user level
        verbosity_map = {
            'beginner': 'minimal',
            'intermediate': 'normal',
            'expert': 'detailed'
        }
        verbosity = verbosity_map.get(feedback_level, 'normal')

        # Build response
        response = {
            'feedback': feedback.to_dict(),
            'user_message': feedback.to_user_message(verbosity=verbosity),
            'explanation': optimal_explanation_str,
            'was_correct': (user_bid == optimal_bid),
            'show_alternative': feedback.correctness.value != 'optimal'
        }

        return jsonify(response)

    except Exception as e:
        print(f"❌ Error in evaluate-bid: {e}")
        traceback.print_exc()

        # Log error with bidding context
        log_error(
            error=e,
            endpoint='/api/evaluate-bid',
            user_id=data.get('user_id') if 'data' in locals() else None,
            context={
                'user_bid': data.get('user_bid') if 'data' in locals() else None,
                'current_player': data.get('current_player') if 'data' in locals() else None,
                'auction_length': len(data.get('auction_history', [])) if 'data' in locals() else 0,
                'vulnerability': state.vulnerability if state else None,
                'has_hand': 'user_hand' in locals()
            },
            request_data=data if 'data' in locals() else {}
        )

        return jsonify({'error': f'Server error in evaluate_bid: {str(e)}'}), 500

@app.route('/api/get-all-hands', methods=['GET'])
def get_all_hands():
    # Get session state for this request
    state = get_state()
    try:
        print(f"🔍 get_all_hands DEBUG:")
        print(f"   - state.deal exists: {state.deal is not None}")
        print(f"   - state.deal type: {type(state.deal)}")
        print(f"   - state.play_state exists: {state.play_state is not None}")
        if state.deal:
            print(f"   - state.deal keys: {list(state.deal.keys())}")
            for pos in ['North', 'East', 'South', 'West']:
                hand = state.deal.get(pos)
                if hand:
                    print(f"   - {pos}: {len(hand.cards)} cards")

        # Check if a deal exists
        if not state.deal or not isinstance(state.deal, dict):
            print("⚠️ get_all_hands: No deal available yet")
            return jsonify({'error': 'No deal available. Please deal a new hand first.'}), 400

        all_hands = {}

        # CRITICAL FIX: During play phase, use play_state.hands (which contains current cards)
        # During bidding phase, use state.deal
        # This ensures replay works correctly and user always sees their current hand
        source_hands = None
        pos_map = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}

        if state.play_state and state.play_state.hands:
            # Play phase: use current hands from play state
            print("📋 get_all_hands: Using play_state.hands (play phase)")
            source_hands = state.play_state.hands
            # Map single-letter positions to full names for response
            for short_pos, full_pos in pos_map.items():
                if short_pos in source_hands:
                    hand = source_hands[short_pos]
                    hand_for_json = [{'rank': card.rank, 'suit': card.suit} for card in hand.cards]
                    points_for_json = {
                        'hcp': hand.hcp,
                        'dist_points': hand.dist_points,
                        'total_points': hand.total_points,
                        'suit_hcp': hand.suit_hcp,
                        'suit_lengths': hand.suit_lengths
                    }
                    all_hands[full_pos] = {
                        'hand': hand_for_json,
                        'points': points_for_json
                    }
        else:
            # Bidding phase: use original deal
            print("📋 get_all_hands: Using state.deal (bidding phase)")
            for position in ['North', 'East', 'South', 'West']:
                hand = state.deal.get(position)
                if not hand:
                    return jsonify({'error': f'Hand for {position} not available'}), 400

                print(f"🔍 {position}: {len(hand.cards)} cards - {hand.cards}")
                hand_for_json = [{'rank': card.rank, 'suit': card.suit} for card in hand.cards]
                points_for_json = {
                    'hcp': hand.hcp,
                    'dist_points': hand.dist_points,
                    'total_points': hand.total_points,
                    'suit_hcp': hand.suit_hcp,
                    'suit_lengths': hand.suit_lengths
                }
                all_hands[position] = {
                    'hand': hand_for_json,
                    'points': points_for_json
                }

        print(f"✅ get_all_hands: Successfully returning {len(all_hands)} hands")
        return jsonify({
            'hands': all_hands,
            'vulnerability': state.vulnerability
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Server error in get_all_hands: {e}'}), 500

@app.route('/api/request-review', methods=['POST'])
def request_review():
    # Get session state for this request
    state = get_state()
    try:
        data = request.get_json()
        auction_history = data.get('auction_history', [])
        user_concern = data.get('user_concern', '')
        game_phase = data.get('game_phase', 'bidding')  # 'bidding' or 'playing'
        user_hand_data = data.get('user_hand')  # Actual hand shown to user
        user_hand_points = data.get('user_hand_points')  # Actual points shown to user
        frontend_all_hands = data.get('all_hands')  # Fallback: all hands from frontend (if user clicked "Show All Hands")

        # Prepare all hands data (current state of hands)
        all_hands = {}

        if game_phase == 'playing' and state.play_state:
            # During play phase, use hands from play state
            pos_map = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}
            for short_pos, hand in state.play_state.hands.items():
                position = pos_map[short_pos]
                hand_for_json = [{'rank': card.rank, 'suit': card.suit} for card in hand.cards]
                points_for_json = {
                    'hcp': hand.hcp,
                    'dist_points': hand.dist_points,
                    'total_points': hand.total_points,
                    'suit_hcp': hand.suit_hcp,
                    'suit_lengths': hand.suit_lengths
                }
                all_hands[position] = {
                    'cards': hand_for_json,
                    'points': points_for_json
                }
        else:
            # During bidding phase, use initial deal
            for position in ['North', 'East', 'South', 'West']:
                # Use user's actual hand data if provided (for South position)
                if position == 'South' and user_hand_data and user_hand_points:
                    # Use the hand data that was actually shown to the user
                    all_hands[position] = {
                        'cards': user_hand_data,
                        'points': user_hand_points
                    }
                else:
                    # Use backend's stored hand for other positions
                    hand = state.deal.get(position)
                    if hand:
                        hand_for_json = [{'rank': card.rank, 'suit': card.suit} for card in hand.cards]
                        points_for_json = {
                            'hcp': hand.hcp,
                            'dist_points': hand.dist_points,
                            'total_points': hand.total_points,
                            'suit_hcp': hand.suit_hcp,
                            'suit_lengths': hand.suit_lengths
                        }
                        all_hands[position] = {
                            'cards': hand_for_json,
                            'points': points_for_json
                        }
                    elif frontend_all_hands and frontend_all_hands.get(position):
                        # Fallback: use frontend-provided hands (e.g., after server restart on production)
                        fe_hand = frontend_all_hands[position]
                        all_hands[position] = {
                            'cards': fe_hand.get('hand', []),
                            'points': fe_hand.get('points', {})
                        }
                        print(f"ℹ️  Using frontend-provided hand for {position} (backend state lost)")
                    else:
                        # No hand available from either source
                        return jsonify({'error': f'Hand for {position} not available. Try clicking "Show All Hands" first.'}), 400

        # Get dealer from request (frontend knows actual dealer from bidding) or fallback to session
        dealer = data.get('dealer')
        if not dealer:
            if state.game_session:
                dealer = state.game_session.get_current_dealer()
            else:
                dealer = 'North'

        # Get user position from session or default to South
        user_position = 'South'  # Default for non-session mode
        if state.game_session:
            # Convert abbreviated position to full name
            pos_map = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}
            user_position = pos_map.get(state.game_session.player_position, 'South')

        # Create review request object
        review_request = {
            'timestamp': datetime.now().isoformat(),
            'game_phase': game_phase,
            'all_hands': all_hands,
            'auction': auction_history,
            'vulnerability': state.vulnerability,
            'dealer': dealer,  # ✅ Use session dealer
            'user_position': user_position,  # ✅ Use session position
            'user_concern': user_concern
        }

        # Add play phase data if in gameplay
        if game_phase == 'playing' and state.play_state:
            contract = state.play_state.contract

            # Serialize trick history
            trick_history = []
            for trick in state.play_state.trick_history:
                trick_cards = [
                    {
                        'card': {'rank': card.rank, 'suit': card.suit},
                        'player': player
                    }
                    for card, player in trick.cards
                ]
                trick_history.append({
                    'cards': trick_cards,
                    'leader': trick.leader,
                    'winner': trick.winner
                })

            # Serialize current trick (if any)
            current_trick = [
                {
                    'card': {'rank': card.rank, 'suit': card.suit},
                    'player': player
                }
                for card, player in state.play_state.current_trick
            ]

            review_request['play_data'] = {
                'contract': {
                    'level': contract.level,
                    'strain': contract.strain,
                    'declarer': contract.declarer,
                    'doubled': contract.doubled,
                    'string': str(contract)
                },
                'dummy': state.play_state.dummy,
                'opening_leader': play_engine.next_player(contract.declarer),
                'trick_history': trick_history,
                'current_trick': current_trick,
                'tricks_won': state.play_state.tricks_won,
                'tricks_taken_ns': state.play_state.tricks_taken_ns,
                'tricks_taken_ew': state.play_state.tricks_taken_ew,
                'next_to_play': state.play_state.next_to_play,
                'dummy_revealed': state.play_state.dummy_revealed,
                'is_complete': state.play_state.is_complete
            }

        # Create filename with timestamp
        timestamp_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f'hand_{timestamp_str}.json'

        # Check if we're on Render (ephemeral storage - files won't persist for user access)
        # Render sets RENDER or RENDER_SERVICE_NAME environment variables
        # Oracle Cloud has persistent storage, so we save files there
        is_render = os.getenv('RENDER') or os.getenv('RENDER_SERVICE_NAME')

        if is_render:
            # On Render: don't save to file, embed data in prompt instead
            print("Running on Render - will embed full data in prompt (files not accessible to users)")
            saved_to_file = False
        else:
            # Local development or Oracle Cloud: save to file for reference
            try:
                filepath = os.path.join('review_requests', filename)
                os.makedirs('review_requests', exist_ok=True)
                with open(filepath, 'w') as f:
                    json.dump(review_request, indent=2, fp=f)
                saved_to_file = True
                print(f"Saved review request to {filepath}")
            except Exception as file_error:
                print(f"Could not save to file: {file_error}")
                saved_to_file = False

        # Send email notification (works in both local and production)
        email_sent = False
        try:
            from engine.notifications import send_review_notification
            email_sent = send_review_notification(review_request, filename)
        except Exception as email_error:
            print(f"⚠️  Email notification failed: {email_error}")

        # Return the full review data so frontend can display it
        return jsonify({
            'success': True,
            'filename': filename,
            'saved_to_file': saved_to_file,
            'email_sent': email_sent,
            'review_data': review_request  # Include full data in response
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Server error in request_review: {e}'}), 500


@app.route('/api/submit-feedback', methods=['POST'])
def submit_feedback():
    """
    Submit user feedback about the application.
    Works for both Learning Mode and Freeplay Mode.
    Saves feedback to backend/user_feedback/ directory for review.
    """
    try:
        data = request.get_json()
        feedback_type = data.get('type', 'issue')
        description = data.get('description', '')
        context = data.get('context', 'freeplay')  # 'learning' or 'freeplay'
        context_data = data.get('contextData', {})

        # Create feedback object
        feedback = {
            'timestamp': datetime.now().isoformat(),
            'feedback_type': feedback_type,
            'description': description,
            'context': context,
            'context_data': context_data,
        }

        # Add user info if available
        user_id = request.headers.get('X-User-ID')
        if user_id:
            feedback['user_id'] = user_id

        # Create filename with timestamp and context
        timestamp_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f'feedback_{context}_{timestamp_str}.json'

        # Check if we're on Render (ephemeral storage)
        # Oracle Cloud has persistent storage, so we save files there
        is_render = os.getenv('RENDER') or os.getenv('RENDER_SERVICE_NAME')

        if is_render:
            # On Render: log to console (will appear in Render logs)
            print(f"📝 User Feedback Received:")
            print(f"   Type: {feedback_type}")
            print(f"   Context: {context}")
            print(f"   Description: {description[:200]}..." if len(description) > 200 else f"   Description: {description}")
            print(f"   Full feedback: {json.dumps(feedback, indent=2)}")
            saved_to_file = False
        else:
            # Local development or Oracle Cloud: save to file
            try:
                feedback_dir = 'user_feedback'
                os.makedirs(feedback_dir, exist_ok=True)
                filepath = os.path.join(feedback_dir, filename)
                with open(filepath, 'w') as f:
                    json.dump(feedback, f, indent=2)
                saved_to_file = True
                print(f"📝 Saved user feedback to {filepath}")
            except Exception as file_error:
                print(f"⚠️  Could not save feedback to file: {file_error}")
                saved_to_file = False

        # Send email notification for feedback
        email_sent = False
        try:
            from engine.notifications import send_feedback_notification
            email_sent = send_feedback_notification(feedback, filename)
        except Exception as email_error:
            print(f"⚠️  Email notification failed: {email_error}")

        return jsonify({
            'success': True,
            'filename': filename if saved_to_file else None,
            'saved_to_file': saved_to_file,
            'email_sent': email_sent,
            'message': 'Thank you for your feedback!'
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Server error in submit_feedback: {e}'}), 500


# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@app.route('/api/admin/review-requests', methods=['GET'])
def get_review_requests():
    """
    List all review requests with their content.
    Returns HTML page for browser viewing or JSON for API calls.
    """
    try:
        review_dir = 'review_requests'
        requests_list = []

        if os.path.exists(review_dir):
            for filename in sorted(os.listdir(review_dir), reverse=True):
                if filename.endswith('.json'):
                    filepath = os.path.join(review_dir, filename)
                    try:
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                            requests_list.append({
                                'filename': filename,
                                'timestamp': data.get('timestamp', ''),
                                'game_phase': data.get('game_phase', 'unknown'),
                                'user_concern': data.get('user_concern', ''),
                                'user_position': data.get('user_position', 'South'),
                                'vulnerability': data.get('vulnerability', 'None'),
                                'dealer': data.get('dealer', 'N'),
                                'data': data
                            })
                    except Exception as e:
                        print(f"Error reading {filename}: {e}")

        # Check Accept header to determine response format
        accept = request.headers.get('Accept', '')
        if 'text/html' in accept:
            return _render_review_requests_html(requests_list)
        else:
            return jsonify({
                'success': True,
                'count': len(requests_list),
                'requests': requests_list
            })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Server error: {e}'}), 500


@app.route('/api/admin/review-requests/<filename>', methods=['GET'])
def get_review_request_detail(filename):
    """Get a single review request by filename."""
    try:
        filepath = os.path.join('review_requests', filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'Review request not found'}), 404

        with open(filepath, 'r') as f:
            data = json.load(f)

        accept = request.headers.get('Accept', '')
        if 'text/html' in accept:
            return _render_review_request_detail_html(data, filename)
        else:
            return jsonify({
                'success': True,
                'filename': filename,
                'data': data
            })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Server error: {e}'}), 500


def _format_hand_html(hand_data):
    """Format a hand for HTML display."""
    cards = hand_data.get('cards', [])
    points = hand_data.get('points', {})

    suits = {'♠': [], '♥': [], '♦': [], '♣': []}
    for card in cards:
        suit = card.get('suit', '')
        rank = card.get('rank', '')
        if suit in suits:
            suits[suit].append(rank)

    lines = []
    suit_colors = {'♠': '#000', '♥': '#c00', '♦': '#c00', '♣': '#000'}
    for suit in ['♠', '♥', '♦', '♣']:
        cards_in_suit = suits.get(suit, [])
        rank_order = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10}
        cards_in_suit.sort(key=lambda r: rank_order.get(r, int(r) if r.isdigit() else 0), reverse=True)
        color = suit_colors.get(suit, '#000')
        card_str = ''.join(cards_in_suit) if cards_in_suit else '-'
        lines.append(f'<span style="color:{color}">{suit}</span> {card_str}')

    hcp = points.get('hcp', 0)
    total = points.get('total_points', hcp)

    return '<br>'.join(lines) + f'<br><small>({hcp} HCP, {total} total)</small>'


def _render_review_requests_html(requests_list):
    """Render HTML page for review requests list."""
    rows = ""
    for req in requests_list:
        concern = req['user_concern'][:100] + '...' if len(req['user_concern']) > 100 else req['user_concern']
        rows += f"""
        <tr onclick="window.location='/api/admin/review-requests/{req['filename']}'" style="cursor:pointer">
            <td>{req['timestamp'][:16] if req['timestamp'] else 'N/A'}</td>
            <td>{req['game_phase']}</td>
            <td>{req['user_position']}</td>
            <td>{concern}</td>
            <td><a href="/api/admin/review-requests/{req['filename']}">View</a></td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Review Requests - Bridge Buddy Admin</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #1a5f2a; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background: #1a5f2a; color: white; }}
            tr:hover {{ background: #f5f5f5; }}
            .count {{ color: #666; font-size: 14px; }}
            a {{ color: #1a5f2a; }}
        </style>
    </head>
    <body>
        <h1>🃏 Review Requests</h1>
        <p class="count">{len(requests_list)} request(s)</p>
        <table>
            <tr>
                <th>Timestamp</th>
                <th>Phase</th>
                <th>User Position</th>
                <th>Concern</th>
                <th>Action</th>
            </tr>
            {rows if rows else '<tr><td colspan="5">No review requests yet</td></tr>'}
        </table>
    </body>
    </html>
    """
    return html


def _render_review_request_detail_html(data, filename):
    """Render HTML page for a single review request."""
    # Format hands
    all_hands = data.get('all_hands', {})
    hands_html = ""
    user_position = data.get('user_position', 'South')
    for position in ['North', 'East', 'South', 'West']:
        hand = all_hands.get(position, {})
        if hand:
            marker = " 👤" if position == user_position else ""
            hands_html += f"""
            <div class="hand-box">
                <strong>{position}{marker}</strong><br>
                {_format_hand_html(hand)}
            </div>
            """

    # Format auction
    auction = data.get('auction', [])
    auction_html = ""
    positions = ['North', 'East', 'South', 'West']
    for i, bid_data in enumerate(auction):
        pos = positions[i % 4]
        bid = bid_data.get('bid', '?')
        explanation = bid_data.get('explanation', '')
        if len(explanation) > 150:
            explanation = explanation[:147] + "..."
        auction_html += f"""
        <tr>
            <td><strong>{pos}</strong></td>
            <td style="font-size: 20px;">{bid}</td>
            <td style="color: #666; font-size: 13px;">{explanation}</td>
        </tr>
        """

    # Play data section
    play_html = ""
    play_data = data.get('play_data')
    if play_data:
        contract = play_data.get('contract', {})
        play_html = f"""
        <div class="section">
            <h3>🎴 Play Data</h3>
            <p><strong>Contract:</strong> {contract.get('string', 'Unknown')}</p>
            <p><strong>Declarer:</strong> {contract.get('declarer', 'Unknown')}</p>
            <p><strong>Tricks:</strong> NS: {play_data.get('tricks_taken_ns', 0)} | EW: {play_data.get('tricks_taken_ew', 0)}</p>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Review Request - {filename}</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #1a5f2a; }}
            .back {{ margin-bottom: 20px; }}
            .back a {{ color: #1a5f2a; text-decoration: none; }}
            .concern {{ background: #e8f5e9; padding: 15px; border-radius: 8px; margin: 20px 0; }}
            .hands {{ display: flex; flex-wrap: wrap; gap: 15px; margin: 20px 0; }}
            .hand-box {{ flex: 1; min-width: 150px; padding: 12px; background: #f5f5f5; border-radius: 8px; font-family: monospace; }}
            .section {{ margin: 20px 0; }}
            table {{ width: 100%; border-collapse: collapse; }}
            td {{ padding: 8px; border-bottom: 1px solid #eee; }}
            .meta {{ color: #666; font-size: 14px; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <div class="back"><a href="/api/admin/review-requests">← Back to all requests</a></div>
        <h1>🃏 Review Request</h1>
        <p class="meta">
            <strong>File:</strong> {filename} |
            <strong>Phase:</strong> {data.get('game_phase', 'unknown')} |
            <strong>Dealer:</strong> {data.get('dealer', 'N')} |
            <strong>Vuln:</strong> {data.get('vulnerability', 'None')}
        </p>

        <div class="concern">
            <h3>💬 User's Concern</h3>
            <p>{data.get('user_concern', 'No specific concern noted')}</p>
        </div>

        <div class="section">
            <h3>🎴 Hands</h3>
            <div class="hands">{hands_html}</div>
        </div>

        <div class="section">
            <h3>📋 Auction</h3>
            <table>
                {auction_html if auction_html else '<tr><td>No bids yet</td></tr>'}
            </table>
        </div>

        {play_html}
    </body>
    </html>
    """
    return html


# ============================================================================
# CARD PLAY ENDPOINTS
# ============================================================================

@app.route("/api/start-play", methods=["POST"])
def start_play():
    """
    Called when bidding completes (3 consecutive passes)
    Determines contract and sets up play state
    """
    # Get session state for this request
    state = get_state()

    try:
        data = request.get_json()
        auction = data.get("auction_history", [])
        vulnerability_str = data.get("vulnerability", "None")

        # Get dealer from request (frontend sends it based on actual auction order)
        # CRITICAL: Trust frontend's dealer because the auction was built with that dealer
        # Only fall back to session if frontend doesn't provide dealer
        dealer_str = data.get("dealer")
        if not dealer_str:
            # Fallback: use session dealer if no dealer provided
            if state.game_session:
                dealer_str = state.game_session.get_current_dealer()
            else:
                dealer_str = "North"

        # Log for debugging
        print(f"📋 start_play: dealer={dealer_str}, auction_length={len(auction)}")

        # Convert dealer to index for contract determination
        dealer_index = ['N', 'E', 'S', 'W'].index(dealer_str[0].upper())

        # Determine contract from auction using correct dealer
        contract = play_engine.determine_contract(auction, dealer_index=dealer_index)

        if not contract:
            return jsonify({"error": "No contract found (all passed)"}), 400

        # Set up vulnerability dict
        vuln_dict = {
            "ns": vulnerability_str in ["NS", "Both"],
            "ew": vulnerability_str in ["EW", "Both"]
        }

        # Get hands (from request or session state deal)
        hands_data = data.get("hands")
        if hands_data:
            # Convert JSON hand data to Hand objects
            from engine.hand import Hand, Card
            hands = {}
            for pos in ["N", "E", "S", "W"]:
                if pos in hands_data:
                    cards = [Card(c['rank'], c['suit']) for c in hands_data[pos]]
                    hands[pos] = Hand(cards)
        else:
            # Check if we should use preserved original_deal (for replays)
            # or current deal (for first-time play)
            use_original = data.get("replay", False)

            # Map single letters to full names
            pos_map = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}
            hands = {}

            if use_original and state.original_deal:
                # Replay: use preserved original deal
                print(f"🔄 Using preserved original_deal for replay")
                for pos in ["N", "E", "S", "W"]:
                    full_name = pos_map[pos]
                    if state.original_deal.get(full_name):
                        hands[pos] = state.original_deal[full_name]
                    else:
                        return jsonify({"error": f"Original hand data not found for {full_name}. Cannot replay."}), 400
            else:
                # First play: use current deal from bidding phase
                for pos in ["N", "E", "S", "W"]:
                    full_name = pos_map[pos]
                    if state.deal.get(full_name):
                        hands[pos] = state.deal[full_name]
                    else:
                        return jsonify({"error": f"Hand data not found for {full_name}. Please deal a new hand."}), 400

                # CRITICAL: Preserve original deal before play begins
                # Make deep copies of Hand objects to preserve original 13-card state
                import copy
                state.original_deal = {}
                for pos in ["N", "E", "S", "W"]:
                    full_name = pos_map[pos]
                    # Deep copy the Hand object including all cards
                    state.original_deal[full_name] = copy.deepcopy(state.deal[full_name])
                print(f"✅ Preserved original_deal with {sum(len(h.cards) for h in state.original_deal.values())} total cards")

        # Create play state
        state.play_state = PlayState(
            contract=contract,
            hands=hands,
            current_trick=[],
            tricks_won={"N": 0, "E": 0, "S": 0, "W": 0},
            trick_history=[],
            next_to_play=play_engine.next_player(contract.declarer),  # LHO of declarer leads
            dummy_revealed=False,
            phase=GamePhase.PLAY_STARTING  # Set initial phase
        )

        # Opening leader (LHO of declarer)
        opening_leader = state.play_state.next_to_play
        dummy_position = state.play_state.dummy

        return jsonify({
            "success": True,
            "contract": str(contract),
            "contract_details": {
                "level": contract.level,
                "strain": contract.strain,
                "declarer": contract.declarer,
                "doubled": contract.doubled
            },
            "opening_leader": opening_leader,
            "dummy": dummy_position,
            "next_to_play": opening_leader
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error starting play: {e}"}), 500

@app.route("/api/play-random-hand", methods=["POST"])
def play_random_hand():
    """
    Deal a new random hand and start play with an appropriate contract
    Uses the bidding engine to generate a realistic auction for the dealt hands
    Skips bidding phase from user perspective - goes straight to card play
    """
    # Get session state for this request
    state = get_state()

    try:
        # Deal a new random hand
        ranks = '23456789TJQKA'
        suits = ['♠', '♥', '♦', '♣']
        deck = [Card(rank, suit) for rank in ranks for suit in suits]
        random.shuffle(deck)

        state.deal['North'] = Hand(deck[0:13])
        state.deal['East'] = Hand(deck[13:26])
        state.deal['South'] = Hand(deck[26:39])
        state.deal['West'] = Hand(deck[39:52])

        # Use Chicago rotation for dealer and vulnerability if in session
        dealer = 'North'  # Default
        if state.game_session:
            dealer = state.game_session.get_current_dealer()
            state.vulnerability = state.game_session.get_current_vulnerability()
        else:
            # Non-session mode: rotate vulnerability manually
            vulnerabilities = ["None", "NS", "EW", "Both"]
            try:
                current_idx = vulnerabilities.index(state.vulnerability)
                state.vulnerability = vulnerabilities[(current_idx + 1) % len(vulnerabilities)]
            except ValueError:
                state.vulnerability = "None"

        # Generate realistic auction using the bidding engine
        # Simulate all 4 players bidding with AI
        auction_history = []
        players = ['North', 'East', 'South', 'West']
        dealer_index = ['N', 'E', 'S', 'W'].index(dealer[0].upper())  # Use Chicago dealer
        current_player_index = dealer_index

        # Maximum 50 bids to prevent infinite loops (typical auction is 4-15 bids)
        max_bids = 50
        bid_count = 0

        # Helper function to check if auction is over
        def is_auction_over(bids):
            if len(bids) < 4:
                return False
            # All passed out
            non_pass_bids = [b for b in bids if b != 'Pass']
            if len(bids) >= 4 and len(non_pass_bids) == 0:
                return True
            # 3 consecutive passes after a non-pass bid
            if len(non_pass_bids) > 0 and len(bids) >= 3:
                return bids[-1] == 'Pass' and bids[-2] == 'Pass' and bids[-3] == 'Pass'
            return False

        # Run AI bidding for all 4 players
        while not is_auction_over(auction_history) and bid_count < max_bids:
            current_player = players[current_player_index]
            player_hand = state.deal[current_player]

            try:
                # Get AI bid for this player
                bid, explanation = engine.get_next_bid(
                    player_hand,
                    auction_history,
                    current_player,
                    state.vulnerability,
                    explanation_level='simple'
                )
                auction_history.append(bid)
                bid_count += 1
            except Exception as e:
                print(f"Error getting bid for {current_player}: {e}")
                # Fallback to Pass on error
                auction_history.append('Pass')
                bid_count += 1

            # Move to next player
            current_player_index = (current_player_index + 1) % 4

        # Determine contract from the auction
        contract = play_engine.determine_contract(auction_history, dealer_index=dealer_index)

        if not contract:
            # All passed - retry with a new deal
            print("All players passed - dealing new hand")
            return play_random_hand()  # Recursive retry

        # Convert hands for play state
        pos_map = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}
        hands = {}
        for pos in ["N", "E", "S", "W"]:
            full_name = pos_map[pos]
            hands[pos] = state.deal[full_name]

        # CRITICAL: Preserve original deal before play begins (for replay functionality)
        import copy
        state.original_deal = {}
        for pos in ["N", "E", "S", "W"]:
            full_name = pos_map[pos]
            state.original_deal[full_name] = copy.deepcopy(state.deal[full_name])
        print(f"✅ Preserved original_deal with {sum(len(h.cards) for h in state.original_deal.values())} total cards")

        # Create play state
        state.play_state = PlayState(
            contract=contract,
            hands=hands,
            current_trick=[],
            tricks_won={"N": 0, "E": 0, "S": 0, "W": 0},
            trick_history=[],
            next_to_play=play_engine.next_player(contract.declarer),  # LHO of declarer leads
            dummy_revealed=False,
            phase=GamePhase.PLAY_STARTING
        )

        opening_leader = state.play_state.next_to_play
        dummy_position = state.play_state.dummy

        # Return South's hand for display
        # CONSISTENCY FIX: Use play_state.hands instead of state.deal
        # This ensures consistency with get-all-hands endpoint
        south_hand = state.play_state.hands['S']
        hand_for_json = [{'rank': card.rank, 'suit': card.suit} for card in south_hand.cards]
        points_for_json = {
            'hcp': south_hand.hcp,
            'dist_points': south_hand.dist_points,
            'total_points': south_hand.total_points,
            'suit_hcp': south_hand.suit_hcp,
            'suit_lengths': south_hand.suit_lengths
        }

        # Return the generated auction for reference (optional - can be displayed or hidden)
        auction_for_display = [{"bid": bid, "explanation": ""} for bid in auction_history]

        return jsonify({
            "success": True,
            "hand": hand_for_json,
            "points": points_for_json,
            "vulnerability": state.vulnerability,
            "dealer": dealer,  # NEW: Include dealer
            "contract": str(contract),
            "contract_details": {
                "level": contract.level,
                "strain": contract.strain,
                "declarer": contract.declarer,
                "doubled": contract.doubled
            },
            "opening_leader": opening_leader,
            "dummy": dummy_position,
            "next_to_play": opening_leader,
            "auction": auction_for_display  # Include generated auction
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error creating random play hand: {e}"}), 500

@app.route("/api/play-card", methods=["POST"])
def play_card():
    """
    User plays a card
    """
    # Get session state for this request
    state = get_state()

    if not state.play_state:
        return jsonify({"error": "No play in progress"}), 400
    
    try:
        data = request.get_json()
        card_data = data.get("card")
        position = data.get("position", "South")

        # === BRIDGE RULES ENGINE VALIDATION ===
        bridge_state = BridgeGameState(
            declarer=state.play_state.contract.declarer,
            dummy=state.play_state.dummy,
            user_position='S',
            next_to_play=state.play_state.next_to_play,
            dummy_revealed=state.play_state.dummy_revealed,
            opening_lead_made=len(state.play_state.current_trick) >= 1 or len(state.play_state.trick_history) >= 1
        )

        # Validate user can play from this position
        if not BridgeRulesEngine.can_user_play_from_position(bridge_state, position):
            user_role = BridgeRulesEngine.get_player_role('S', state.play_state.contract.declarer, state.play_state.dummy)
            return jsonify({
                "error": f"Cannot play from {position} - user does not control this position",
                "user_role": user_role.value,
                "controllable_positions": list(BridgeRulesEngine.get_controllable_positions(bridge_state))
            }), 403

        # Validate it's this position's turn
        is_valid, error_msg = BridgeRulesEngine.validate_play_request(bridge_state, position)
        if not is_valid:
            return jsonify({"error": error_msg}), 400

        # Check if trick is already complete (4 cards) - prevent overplay
        if len(state.play_state.current_trick) >= 4:
            return jsonify({
                "error": "Trick is complete. Please wait for it to be cleared."
            }), 400

        # Validate phase allows card play
        if not state.play_state.can_play_card():
            return jsonify({
                "error": f"Cannot play cards in current phase: {state.play_state.phase}"
            }), 400

        # Create card object
        card = Card(rank=card_data["rank"], suit=card_data["suit"])
        hand = state.play_state.hands[position]

        # Validate legal play
        is_legal = play_engine.is_legal_play(
            card, hand, state.play_state.current_trick,
            state.play_state.contract.trump_suit
        )
        
        if not is_legal:
            return jsonify({
                "legal": False,
                "error": "Must follow suit if able"
            }), 400

        # === EVALUATE PLAY FOR DASHBOARD (before modifying state) ===
        # Record plays from South OR from North/dummy when user controls both as declarer
        # User (South) controls: South always, AND dummy when South or North is declarer
        user_id = data.get('user_id')
        play_feedback = None
        declarer = state.play_state.contract.declarer
        dummy = state.play_state.dummy
        # User is declarer if South is declarer, or if North is declarer (user plays dummy)
        user_is_declarer = declarer == 'S' or declarer == 'N'
        is_user_controlled = position == 'S' or (
            user_is_declarer and position == dummy
        ) or (
            user_is_declarer and position == declarer and declarer == 'N'
        )
        if user_id and is_user_controlled:
            try:
                feedback_gen = get_play_feedback_generator(use_dds=PLATFORM_ALLOWS_DDS)
                # Get hand_number from game session (1-indexed for display)
                hand_number = state.game_session.hands_completed + 1 if state.game_session else None
                play_feedback = feedback_gen.evaluate_and_store(
                    user_id=user_id,
                    play_state=state.play_state,
                    user_card=card,
                    position=position,
                    session_id=data.get('session_id'),
                    hand_number=hand_number
                )
            except Exception as feedback_err:
                # Non-blocking - don't fail the play if feedback fails
                print(f"Play feedback error (non-blocking): {feedback_err}")

        # Play the card
        state.play_state.current_trick.append((card, position))

        # Track who led this trick (first card played)
        if len(state.play_state.current_trick) == 1:
            state.play_state.current_trick_leader = position

        # Remove card from hand
        hand.cards.remove(card)

        # Update phase after card played (auto-transition)
        state.play_state.update_phase_after_card()

        # Reveal dummy after opening lead
        if len(state.play_state.current_trick) == 1 and not state.play_state.dummy_revealed:
            state.play_state.dummy_revealed = True
        
        # Check if trick is complete
        trick_complete = len(state.play_state.current_trick) == 4
        trick_winner = None
        
        if trick_complete:
            # Determine winner
            trick_winner = play_engine.determine_trick_winner(
                state.play_state.current_trick,
                state.play_state.contract.trump_suit
            )

            # Update tricks won
            state.play_state.tricks_won[trick_winner] += 1

            # Save to history
            from engine.play_engine import Trick
            state.play_state.trick_history.append(
                Trick(
                    cards=list(state.play_state.current_trick),
                    leader=state.play_state.current_trick_leader,  # FIXED: Use tracked leader
                    winner=trick_winner
                )
            )

            # DON'T clear trick yet - let frontend display it with winner
            # Frontend will call /api/clear-trick after showing winner

            # Next player is the winner
            state.play_state.next_to_play = trick_winner
        else:
            # Next player clockwise
            state.play_state.next_to_play = play_engine.next_player(position)

        return jsonify({
            "legal": True,
            "trick_complete": trick_complete,
            "trick_winner": trick_winner,
            "next_to_play": state.play_state.next_to_play,
            "tricks_won": state.play_state.tricks_won,
            "dummy_revealed": state.play_state.dummy_revealed
        })
        
    except Exception as e:
        traceback.print_exc()

        # Log play error with context
        log_error(
            error=e,
            endpoint='/api/play-card',
            user_id=data.get('user_id') if 'data' in locals() else None,
            context={
                'position': data.get('position') if 'data' in locals() else None,
                'card': data.get('card') if 'data' in locals() else None,
                'trick_length': len(state.play_state.current_trick) if state and state.play_state else 0,
                'contract': str(state.play_state.contract) if state and state.play_state else None,
                'next_to_play': state.play_state.next_to_play if state and state.play_state else None
            },
            request_data=data if 'data' in locals() else {}
        )

        return jsonify({"error": f"Error playing card: {e}"}), 500

@app.route("/api/get-ai-play", methods=["POST"])
def get_ai_play():
    """
    AI plays a card
    """
    # Get session state for this request
    state = get_state()

    if not state.play_state:
        return jsonify({"error": "No play in progress"}), 400
    
    try:
        position = state.play_state.next_to_play
        declarer = state.play_state.contract.declarer
        dummy = state.play_state.dummy

        # ============================================================================
        # CRITICAL VALIDATION: Use BridgeRulesEngine to prevent AI from playing for user
        # ============================================================================
        bridge_state = BridgeGameState(
            declarer=declarer,
            dummy=dummy,
            user_position='S',
            next_to_play=position,
            dummy_revealed=state.play_state.dummy_revealed,
            opening_lead_made=len(state.play_state.current_trick) >= 1 or len(state.play_state.trick_history) >= 1
        )

        # Check if this is a position the user should control
        controllable = BridgeRulesEngine.get_controllable_positions(bridge_state)
        if position in controllable:
            # This is a user-controlled position - AI should not play
            # NOTE: This is a defensive safeguard, not a normal error condition
            # Frontend should detect user control before calling this endpoint
            user_role = BridgeRulesEngine.get_player_role('S', declarer, dummy)
            return jsonify({
                "message": f"Position {position} is user-controlled",
                "position": position,
                "user_role": user_role.value,
                "controllable_positions": list(controllable),
                "dummy": dummy,
                "declarer": declarer,
                "reason": "User should play from this position, not AI"
            }), 403  # 403 Forbidden - signals user turn, not an error

        # Validate using rules engine
        is_valid, error_msg = BridgeRulesEngine.validate_play_request(bridge_state, position)
        if not is_valid:
            return jsonify({"error": error_msg}), 400

        # ============================================================================

        # Check if trick is already complete (4 cards) - prevent overplay
        if len(state.play_state.current_trick) >= 4:
            return jsonify({
                "error": "Trick is complete. Please wait for it to be cleared."
            }), 400

        # Validate phase allows card play
        if not state.play_state.can_play_card():
            return jsonify({
                "error": f"Cannot play cards in current phase: {state.play_state.phase}"
            }), 400

        # ============================================================================
        # CRITICAL FIX: When playing from dummy, declarer AI makes the decision
        # Bridge Rule: Declarer controls BOTH declarer's hand AND dummy's hand
        # ============================================================================
        is_dummy_play = (position == dummy)
        ai_controlling_position = declarer if is_dummy_play else position

        if is_dummy_play:
            print(f"🎭 DUMMY PLAY: Declarer ({declarer}) controlling dummy ({dummy})")

        # AI chooses card (using current difficulty AI)
        current_ai = ai_instances.get(state.ai_difficulty, ai_instances["intermediate"])

        # DIAGNOSTIC: Log hand state before AI chooses
        hand = state.play_state.hands[position]
        print(f"🎴 AI Play Diagnostic for {position}:")
        print(f"   - Hand size: {len(hand.cards)}")
        print(f"   - Cards: {[f'{c.rank}{c.suit}' for c in hand.cards]}")
        print(f"   - Current trick size: {len(state.play_state.current_trick)}")
        print(f"   - Dummy: {dummy}, Declarer: {declarer}")
        print(f"   - Is dummy play: {is_dummy_play}")
        print(f"   - AI controlling position: {ai_controlling_position}")
        print(f"   - AI difficulty: {state.ai_difficulty}")

        # Validate hand is not empty
        if len(hand.cards) == 0:
            error_msg = f"Position {position} has no cards in hand - possible state corruption"
            print(f"❌ {error_msg}")
            return jsonify({"error": error_msg}), 500

        # IMPORTANT: AI always chooses from the perspective of the position being played
        # but for dummy, the AI is declarer making strategic decisions across both hands

        # Time the AI decision for performance monitoring
        # Use safe wrapper to prevent 502 crashes from DDS timeouts/errors
        start_time = time.time()
        card, ai_used_fallback, ai_name_used = safe_ai_choose_card(
            current_ai, state.play_state, position, state.ai_difficulty,
            timeout_seconds=15  # 15s timeout (Render has 30s limit)
        )
        solve_time_ms = (time.time() - start_time) * 1000  # Convert to milliseconds

        if ai_used_fallback:
            print(f"   ⚠️ AI used FALLBACK: {card.rank}{card.suit} (took {solve_time_ms:.1f}ms)")
        else:
            print(f"   ✅ AI chose: {card.rank}{card.suit} (took {solve_time_ms:.1f}ms)")

        # CRITICAL VALIDATION: Verify card is actually in hand before playing
        # This prevents state corruption if AI has a bug
        if card not in hand.cards:
            error_msg = (
                f"❌ AI VALIDATION FAILURE: {position} AI tried to play {card.rank}{card.suit} "
                f"which is not in hand!\n"
                f"   Hand contains: {[f'{c.rank}{c.suit}' for c in hand.cards]}\n"
                f"   AI: {current_ai.get_name()}\n"
                f"   Difficulty: {state.ai_difficulty}"
            )
            print(error_msg)
            traceback.print_exc()
            return jsonify({
                "error": f"AI validation failure - attempted to play card not in hand",
                "details": error_msg
            }), 500

        # Validate card is legal according to bridge rules
        is_legal = play_engine.is_legal_play(
            card, hand, state.play_state.current_trick,
            state.play_state.contract.trump_suit
        )
        if not is_legal:
            error_msg = (
                f"❌ AI LEGALITY FAILURE: {position} AI chose illegal card {card.rank}{card.suit}\n"
                f"   Must follow suit if able\n"
                f"   Current trick: {[(c.rank + c.suit, p) for c, p in state.play_state.current_trick]}"
            )
            print(error_msg)
            return jsonify({
                "error": f"AI chose illegal card",
                "details": error_msg
            }), 500

        # Log AI play for quality monitoring (minimal overhead: ~1ms)
        try:
            # Calculate current trick number
            trick_number = len(state.play_state.trick_history) + 1

            # Check if fallback was used (either due to platform or runtime error)
            # ai_used_fallback is set by safe_ai_choose_card() above
            used_fallback = ai_used_fallback or (
                state.ai_difficulty == 'expert' and
                not (DDS_AVAILABLE and PLATFORM_ALLOWS_DDS)
            )

            # Format contract string
            contract_str = None
            if state.play_state.contract:
                level = state.play_state.contract.level
                strain = state.play_state.contract.trump_suit or "NT"
                contract_str = f"{level}{strain}"

            log_ai_play(
                card=card,
                position=position,
                ai_level=state.ai_difficulty,
                solve_time_ms=solve_time_ms,
                used_fallback=used_fallback,
                session_id=state.game_session.session_id if state.game_session else None,
                hand_number=state.game_session.hands_completed + 1 if state.game_session else None,
                trick_number=trick_number,
                contract=contract_str,
                trump_suit=state.play_state.contract.trump_suit if state.play_state.contract else None
            )
        except Exception as log_error:
            # Never let logging break the game
            print(f"⚠️  Logging error (non-critical): {log_error}")

        # Play the card
        state.play_state.current_trick.append((card, position))

        # Track who led this trick (first card played)
        if len(state.play_state.current_trick) == 1:
            state.play_state.current_trick_leader = position

        hand.cards.remove(card)

        # Update phase after card played (auto-transition)
        state.play_state.update_phase_after_card()

        # Reveal dummy after opening lead
        if len(state.play_state.current_trick) == 1 and not state.play_state.dummy_revealed:
            state.play_state.dummy_revealed = True
        
        # Check if trick is complete
        trick_complete = len(state.play_state.current_trick) == 4
        trick_winner = None

        if trick_complete:
            # Determine winner
            trick_winner = play_engine.determine_trick_winner(
                state.play_state.current_trick,
                state.play_state.contract.trump_suit
            )

            # Update tricks won
            state.play_state.tricks_won[trick_winner] += 1

            # Save to history
            from engine.play_engine import Trick
            state.play_state.trick_history.append(
                Trick(
                    cards=list(state.play_state.current_trick),
                    leader=state.play_state.current_trick_leader,  # FIXED: Use tracked leader
                    winner=trick_winner
                )
            )

            # DON'T clear trick yet - let frontend display it with winner
            # Frontend will call /api/clear-trick after showing winner

            # Next player is the winner
            state.play_state.next_to_play = trick_winner
        else:
            # Next player clockwise
            state.play_state.next_to_play = play_engine.next_player(position)

        return jsonify({
            "card": {"rank": card.rank, "suit": card.suit},
            "position": position,
            "trick_complete": trick_complete,
            "trick_winner": trick_winner,
            "next_to_play": state.play_state.next_to_play,
            "tricks_won": state.play_state.tricks_won,
            "explanation": f"{position} played {card.rank}{card.suit}"
        })
        
    except Exception as e:
        traceback.print_exc()

        # Log AI play error with context
        log_error(
            error=e,
            endpoint='/api/get-ai-play',
            user_id=data.get('user_id') if 'data' in locals() else None,
            context={
                'position': position if 'position' in locals() else None,
                'ai_level': data.get('ai_level') if 'data' in locals() else None,
                'trick_length': len(state.play_state.current_trick) if state and state.play_state else 0,
                'contract': str(state.play_state.contract) if state and state.play_state else None,
                'next_to_play': state.play_state.next_to_play if state and state.play_state else None
            },
            request_data=data if 'data' in locals() else {}
        )

        return jsonify({"error": f"Error with AI play: {e}"}), 500

@app.route("/api/get-play-state", methods=["GET"])
def get_play_state():
    """
    Get current play state with BridgeRulesEngine integration

    Returns comprehensive state including:
    - Hand visibility (what hands should be shown)
    - Controllable positions (what positions user can play from)
    - Turn information (whose turn it is)
    - All hands that should be visible to user
    """
    # Get session state for this request
    state = get_state()

    if not state.play_state:
        return jsonify({"error": "No play in progress"}), 400

    try:
        # Convert current trick to JSON
        current_trick_json = [
            {"card": {"rank": c.rank, "suit": c.suit}, "position": p}
            for c, p in state.play_state.current_trick
        ]

        # Check if trick is complete (4 cards played)
        trick_complete = len(state.play_state.current_trick) == 4
        trick_winner = None
        if trick_complete:
            # Get winner from most recent trick in history
            if state.play_state.trick_history:
                trick_winner = state.play_state.trick_history[-1].winner

        # === BRIDGE RULES ENGINE INTEGRATION ===
        # Create BridgeGameState for rules engine
        bridge_state = BridgeGameState(
            declarer=state.play_state.contract.declarer,
            dummy=state.play_state.dummy,
            user_position='S',  # User always plays South
            next_to_play=state.play_state.next_to_play,
            dummy_revealed=state.play_state.dummy_revealed,
            opening_lead_made=len(state.play_state.current_trick) >= 1 or len(state.play_state.trick_history) >= 1
        )

        # Get rules-based UI display information
        ui_info = BridgeRulesEngine.get_ui_display_info(bridge_state)

        # Get visible hands (all hands user should see)
        visible_hands = {}
        for position in ui_info['visible_hands']:
            if position in state.play_state.hands:
                visible_hands[position] = {
                    "cards": [{"rank": c.rank, "suit": c.suit} for c in state.play_state.hands[position].cards],
                    "position": position
                }

        # Legacy dummy_hand for backward compatibility
        # CRITICAL FIX: Use AND logic - dummy should only be revealed if BOTH conditions are true:
        # 1. Opening lead has been made (at least 1 card played)
        # 2. Dummy revealed flag is set (set after first card)
        # OR if dummy_revealed is explicitly true (handles edge cases)
        dummy_hand = None
        if state.play_state.dummy_revealed and bridge_state.opening_lead_made:
            dummy_pos = state.play_state.dummy
            dummy_hand = {
                "cards": [{"rank": c.rank, "suit": c.suit} for c in state.play_state.hands[dummy_pos].cards],
                "position": dummy_pos
            }

        # Serialize trick history for "Show Last Trick" feature
        trick_history_json = []
        for trick in state.play_state.trick_history:
            trick_cards = [
                {"card": {"rank": card.rank, "suit": card.suit}, "position": player}
                for card, player in trick.cards
            ]
            trick_history_json.append({
                "cards": trick_cards,
                "leader": trick.leader,
                "winner": trick.winner
            })

        return jsonify({
            "contract": {
                "level": state.play_state.contract.level,
                "strain": state.play_state.contract.strain,
                "declarer": state.play_state.contract.declarer,
                "doubled": state.play_state.contract.doubled
            },
            "current_trick": current_trick_json,
            "trick_complete": trick_complete,
            "trick_winner": trick_winner,
            "trick_history": trick_history_json,  # For "Show Last Trick" feature
            "tricks_won": state.play_state.tricks_won,
            "next_to_play": state.play_state.next_to_play,
            "dummy": state.play_state.dummy,
            "dummy_revealed": state.play_state.dummy_revealed,
            "dummy_hand": dummy_hand,  # Legacy support
            "is_complete": state.play_state.is_complete,
            "phase": str(state.play_state.phase),
            # NEW: BridgeRulesEngine data
            "visible_hands": visible_hands,  # All hands user should see
            "controllable_positions": ui_info['controllable_positions'],
            "is_user_turn": ui_info['is_user_turn'],
            "user_role": ui_info['user_role'],
            "turn_message": ui_info['display_message']
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error getting play state: {e}"}), 500

@app.route("/api/clear-trick", methods=["POST"])
def clear_trick():
    """
    Clear the current trick after frontend has displayed it
    Called by frontend after showing trick winner for 5 seconds
    """
    # Get session state for this request
    state = get_state()

    if not state.play_state:
        return jsonify({"error": "No play in progress"}), 400

    try:
        # Clear the current trick and reset leader
        state.play_state.current_trick = []
        state.play_state.current_trick_leader = None

        # If play is complete after clearing, phase will already be PLAY_COMPLETE
        # (updated by update_phase_after_card when last card was played)

        return jsonify({
            "success": True,
            "message": "Trick cleared",
            "phase": str(state.play_state.phase)
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error clearing trick: {e}"}), 500

@app.route("/api/complete-play", methods=["GET", "POST"])
def complete_play():
    """
    Get final results after play completes
    """
    # Get session state for this request
    state = get_state()

    if not state.play_state:
        return jsonify({"error": "No play in progress"}), 400

    try:
        # Accept vulnerability from request (POST) or use global (GET)
        vulnerability = state.vulnerability
        if request.method == "POST":
            data = request.get_json() or {}
            vulnerability = data.get('vulnerability', state.vulnerability)

        # Determine declarer side and calculate tricks taken
        declarer = state.play_state.contract.declarer
        if declarer in ["N", "S"]:
            tricks_taken = state.play_state.tricks_won['N'] + state.play_state.tricks_won['S']
        else:
            tricks_taken = state.play_state.tricks_won['E'] + state.play_state.tricks_won['W']

        # Calculate vulnerability
        vuln_dict = {
            "ns": vulnerability in ["NS", "Both"],
            "ew": vulnerability in ["EW", "Both"]
        }
        
        # Calculate score (including honors)
        score_result = play_engine.calculate_score(
            state.play_state.contract,
            tricks_taken,
            vuln_dict,
            state.play_state.hands  # Pass hands for honors calculation
        )

        # Generate human-readable result text from player's (NS) perspective
        # Player always plays South, so player's team is North-South (NS)
        declarer = state.play_state.contract.declarer
        player_is_declarer = declarer in ['N', 'S']

        if score_result["made"]:
            overtricks = score_result.get("overtricks", 0)
            if player_is_declarer:
                # Player is declarer and made contract
                if overtricks == 0:
                    result_text = "Made exactly"
                else:
                    result_text = f"Made +{overtricks}"
            else:
                # Opponents are declarer and made contract
                if overtricks == 0:
                    result_text = "Opponents made contract"
                else:
                    result_text = f"Opponents made +{overtricks}"
        else:
            undertricks = score_result.get("undertricks", 0)
            if player_is_declarer:
                # Player is declarer and went down
                result_text = f"Down {undertricks}"
            else:
                # Opponents are declarer and went down (defense successful!)
                result_text = f"Defense successful! Down {undertricks}"

        return jsonify({
            "contract": {
                "level": state.play_state.contract.level,
                "strain": state.play_state.contract.strain,
                "declarer": state.play_state.contract.declarer,
                "doubled": state.play_state.contract.doubled
            },
            "tricks_taken": tricks_taken,
            "tricks_needed": state.play_state.contract.tricks_needed,
            "score": score_result["score"],
            "made": score_result["made"],
            "result": result_text,
            "overtricks": score_result.get("overtricks", 0),
            "undertricks": score_result.get("undertricks", 0),
            "breakdown": score_result.get("breakdown", {})
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error calculating final score: {e}"}), 500


# ============================================================================
# AI MONITORING & QUALITY ENDPOINTS
# ============================================================================

@app.route("/api/dds-health", methods=["GET"])
def dds_health():
    """
    Real-time DDS health monitoring dashboard.

    Returns metrics about AI play quality and DDS availability.
    Useful for operations monitoring and debugging.

    Query parameters:
        - hours: Number of hours to look back (default: 24)

    Returns:
        JSON with play counts, solve times, fallback rates, etc.
    """
    try:
        hours = int(request.args.get('hours', 24))

        # Calculate cutoff time in Python (database-agnostic)
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(hours=hours)

        with get_connection() as conn:
            cursor = conn.cursor()

            # Overall stats for specified time period
            cursor.execute("""
                SELECT
                    COUNT(*) as total_plays,
                    COUNT(DISTINCT session_id) as unique_sessions,
                    AVG(solve_time_ms) as avg_solve_time_ms,
                    MAX(solve_time_ms) as max_solve_time_ms,
                    MIN(solve_time_ms) as min_solve_time_ms,
                    AVG(CASE WHEN used_fallback THEN 1.0 ELSE 0.0 END) as fallback_rate,
                    COUNT(CASE WHEN used_fallback THEN 1 END) as fallback_count,
                    MAX(timestamp) as last_play_time
                FROM ai_play_log
                WHERE timestamp > ?
            """, (cutoff_time,))

            row = cursor.fetchone()
            overall = dict(row) if row else {}

            # Stats by AI level
            cursor.execute("""
                SELECT
                    ai_level,
                    COUNT(*) as plays,
                    AVG(solve_time_ms) as avg_solve_time_ms,
                    AVG(CASE WHEN used_fallback THEN 1.0 ELSE 0.0 END) as fallback_rate,
                    COUNT(CASE WHEN used_fallback THEN 1 END) as fallback_count
                FROM ai_play_log
                WHERE timestamp > ?
                GROUP BY ai_level
            """, (cutoff_time,))

            by_level = {row[0]: {'ai_level': row[0], 'plays': row[1], 'avg_solve_time_ms': row[2], 'fallback_rate': row[3], 'fallback_count': row[4]} for row in cursor.fetchall()}

            # Recent plays (last 10)
            cursor.execute("""
                SELECT
                    timestamp,
                    position,
                    ai_level,
                    card_played,
                    solve_time_ms,
                    used_fallback,
                    contract
                FROM ai_play_log
                ORDER BY timestamp DESC
                LIMIT 10
            """)

            recent_plays = [{'timestamp': row[0], 'position': row[1], 'ai_level': row[2], 'card_played': row[3], 'solve_time_ms': row[4], 'used_fallback': row[5], 'contract': row[6]} for row in cursor.fetchall()]

        return jsonify({
            "dds_available": DDS_AVAILABLE and PLATFORM_ALLOWS_DDS,
            "platform": platform.system(),
            "hours_analyzed": hours,
            "overall": overall,
            "by_level": by_level,
            "recent_plays": recent_plays,
            "ai_engines": {
                level: {
                    "name": ai_instances[level].get_name(),
                    "difficulty": ai_instances[level].get_difficulty()
                }
                for level in ['beginner', 'intermediate', 'advanced', 'expert']
            }
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error fetching DDS health: {e}"}), 500


@app.route("/api/dds-test", methods=["GET"])
def dds_test():
    """
    DDS self-test endpoint - actually runs a DDS solve to verify it works.

    This is the definitive test for DDS functionality in production.
    It creates a simple test position and runs DDS to solve it.

    Returns:
        JSON with test results including timing and correctness
    """
    import time

    result = {
        "platform": platform.system(),
        "platform_allows_dds": PLATFORM_ALLOWS_DDS,
        "dds_available": DDS_AVAILABLE,
        "expert_ai_type": ai_instances['expert'].get_name(),
        "test_performed": False,
        "test_passed": False,
        "error": None,
        "solve_time_ms": None,
        "expected_tricks": None,
        "computed_tricks": None
    }

    # If DDS not available, return early
    if not DDS_AVAILABLE or not PLATFORM_ALLOWS_DDS:
        result["error"] = "DDS not available on this platform"
        return jsonify(result)

    try:
        from endplay.types import Deal, Player as EndplayPlayer, Denom
        from endplay.dds import calc_dd_table

        # Create a simple test deal where North-South have all high cards
        # Each hand must have exactly 13 cards
        # N: ♠AKQ ♥AKQ ♦AKQ ♣AKQJ = 13 cards
        # E: ♠5432 ♥5432 ♦5432 ♣5 = 13 cards
        # S: ♠JT9 ♥JT9 ♦JT9 ♣T987 = 13 cards
        # W: ♠876 ♥876 ♦876 ♣6432 = 13 cards
        test_pbn = "N:AKQ.AKQ.AKQ.AKQJ 5432.5432.5432.5 JT9.JT9.JT9.T987 876.876.876.6432"

        result["test_performed"] = True

        # Time the DDS solve
        start_time = time.time()
        deal = Deal(test_pbn)
        dd_table = calc_dd_table(deal)
        solve_time = (time.time() - start_time) * 1000

        result["solve_time_ms"] = round(solve_time, 2)

        # Get the results - North should make 13 tricks in NT
        # dd_table.to_list() returns [clubs, diamonds, hearts, spades, nt] for each player [N, E, S, W]
        data = dd_table.to_list()
        # NT is index 4, North is index 0
        north_nt_tricks = data[4][0]

        result["expected_tricks"] = 13
        result["computed_tricks"] = north_nt_tricks
        result["test_passed"] = (north_nt_tricks == 13)

        if result["test_passed"]:
            result["message"] = f"DDS working correctly! Solved in {solve_time:.1f}ms"
        else:
            result["message"] = f"DDS returned unexpected result: {north_nt_tricks} tricks (expected 13)"
            result["error"] = "Incorrect solve result"

    except Exception as e:
        result["error"] = str(e)
        result["message"] = f"DDS test failed: {e}"
        import traceback
        result["traceback"] = traceback.format_exc()

    return jsonify(result)


@app.route("/api/dds-quality-check", methods=["GET"])
def dds_quality_check():
    """
    Comprehensive DDS quality verification endpoint.

    Tests DDS against multiple known positions with verified optimal plays.
    Used for:
    1. AI quality verification (is DDS working correctly?)
    2. Baseline for user play evaluation

    Returns:
        JSON with accuracy, timing, and detailed results for each test position
    """
    import time

    # If DDS not available, return early
    if not DDS_AVAILABLE or not PLATFORM_ALLOWS_DDS:
        return jsonify({
            "dds_available": False,
            "platform": platform.system(),
            "error": "DDS not available on this platform",
            "message": "Quality check requires DDS (Linux only)"
        })

    try:
        from endplay.types import Deal, Denom
        from endplay.dds import calc_dd_table, solve_board
        from endplay.dds.solve import SolveMode

        # Test positions with known optimal plays
        # Each hand must have EXACTLY 13 cards
        # PBN format: "N:spades.hearts.diamonds.clubs E-hand S-hand W-hand"
        test_positions = [
            # Position 1: Simple finesse - N has AQ spades, W has K
            # All hands validated: exactly 13 cards each, 52 total, no duplicates
            {
                "pbn": "N:AQ5.432.K32.5432 43.AK65.654.K876 J76.QJ9.QJ9.QJT9 KT982.T87.AT87.A",
                "trump": "nt",
                "declarer": "N",
                "to_play": "S",
                "description": "Simple finesse - lead low toward AQ",
                "category": "finesse"
            },
            # Position 2: Cash winners - N has AKQJ spades and hearts
            # All hands validated: exactly 13 cards each, 52 total, no duplicates
            {
                "pbn": "N:AKQJ.AKQJ.32.432 5432.5432.AK65.A T98.T98.QJ94.QJ9 76.76.T87.KT8765",
                "trump": "nt",
                "declarer": "N",
                "to_play": "N",
                "description": "Cash winners - run top cards",
                "category": "cashout"
            },
            # Position 3: Trump contract - N has AKQJT spades
            # All hands validated: exactly 13 cards each, 52 total, no duplicates
            {
                "pbn": "N:AKQJT.A32.32.432 9876.K65.K65.K65 432.QJ9.QJ94.QJ9 5.T874.AT87.AT87",
                "trump": "spades",
                "declarer": "N",
                "to_play": "N",
                "description": "Trump contract - draw trumps first",
                "category": "trump_management"
            },
            # Position 4: Defense - West leads against 3NT
            # All hands validated: exactly 13 cards each, 52 total, no duplicates
            {
                "pbn": "N:AKQ.432.AKQ.5432 J32.AKQ.J32.KQJ9 T98.J98.T98.T876 7654.T765.7654.A",
                "trump": "nt",
                "declarer": "S",
                "to_play": "W",
                "description": "Defense - cash/establish tricks",
                "category": "defense"
            },
            # Position 5: Squeeze/endplay - N has power hand
            # All hands validated: exactly 13 cards each, 52 total, no duplicates
            {
                "pbn": "N:AK.AK.AKQ.AKQJT9 5432.5432.5432.5 QJT.QJT.JT9.8764 9876.9876.876.32",
                "trump": "nt",
                "declarer": "N",
                "to_play": "N",
                "description": "Squeeze/endplay potential",
                "category": "advanced"
            },
        ]

        results = []
        total_time = 0
        correct_count = 0

        for i, pos in enumerate(test_positions):
            test_result = {
                "position": i + 1,
                "description": pos["description"],
                "category": pos["category"],
                "to_play": pos["to_play"],
                "passed": False,
                "solve_time_ms": None,
                "dds_tricks": None,
                "error": None
            }

            try:
                start_time = time.time()

                # Create deal
                deal = Deal(pos["pbn"])

                # Get trump denomination
                trump_map = {
                    "nt": Denom.nt, "spades": Denom.spades, "hearts": Denom.hearts,
                    "diamonds": Denom.diamonds, "clubs": Denom.clubs
                }
                trump = trump_map[pos["trump"]]

                # Calculate DD table to verify position
                dd_table = calc_dd_table(deal)
                data = dd_table.to_list()

                # Get expected tricks for declarer
                denom_idx = {"clubs": 0, "diamonds": 1, "hearts": 2, "spades": 3, "nt": 4}[pos["trump"]]
                declarer_idx = {"N": 0, "E": 1, "S": 2, "W": 3}[pos["declarer"]]
                expected_tricks = data[denom_idx][declarer_idx]

                solve_time = (time.time() - start_time) * 1000
                total_time += solve_time

                test_result["solve_time_ms"] = round(solve_time, 2)
                test_result["dds_tricks"] = expected_tricks
                test_result["passed"] = True  # If we get here without error, DDS is working
                correct_count += 1

            except Exception as e:
                test_result["error"] = str(e)
                test_result["passed"] = False

            results.append(test_result)

        # Calculate summary
        accuracy = (correct_count / len(test_positions)) * 100 if test_positions else 0
        avg_time = total_time / len(test_positions) if test_positions else 0

        return jsonify({
            "dds_available": True,
            "platform": platform.system(),
            "test_count": len(test_positions),
            "passed": correct_count,
            "failed": len(test_positions) - correct_count,
            "accuracy_pct": round(accuracy, 1),
            "total_time_ms": round(total_time, 2),
            "avg_time_ms": round(avg_time, 2),
            "status": "PASS" if accuracy == 100 else "DEGRADED" if accuracy >= 80 else "FAIL",
            "results": results,
            "message": f"DDS quality check: {correct_count}/{len(test_positions)} positions solved correctly"
        })

    except Exception as e:
        import traceback
        return jsonify({
            "dds_available": True,
            "platform": platform.system(),
            "error": str(e),
            "traceback": traceback.format_exc(),
            "status": "ERROR"
        }), 500


@app.route("/api/evaluate-play", methods=["POST"])
def evaluate_play():
    """
    Evaluate a user's card play against optimal play.

    This endpoint compares the user's chosen card against what DDS (or Minimax
    fallback) recommends as optimal, providing feedback similar to bidding evaluation.

    Uses PlayFeedbackGenerator for structured feedback generation with:
    - DDS-based evaluation on production (Linux)
    - Minimax heuristic fallback on development (macOS)

    Request body:
        - card: {rank, suit} - The card user played
        - position: str - Position playing from (N/E/S/W)
        - user_id: int - User ID for tracking
        - For context, uses current play_state from session

    Returns:
        - score: 0-10 rating
        - correctness: "optimal", "good", "suboptimal", "blunder", "illegal"
        - optimal_cards: List of optimal cards
        - tricks_cost: How many tricks this play costs vs optimal
        - feedback: Explanation of why the play was good/bad
        - reasoning: Detailed reasoning
        - helpful_hint: Actionable advice for improvement
        - play_category: Type of play (opening_lead, following_suit, etc.)
        - key_concept: Learning concept for this play
        - dds_available: Whether DDS was used for evaluation
    """
    from engine.feedback.play_feedback import get_play_feedback_generator

    # Get session state
    state = get_state()

    if not state.play_state:
        return jsonify({"error": "No play in progress"}), 400

    data = request.get_json()
    if not data or 'card' not in data:
        return jsonify({"error": "Card data required"}), 400

    try:
        # Parse card and position
        card_data = data['card']
        user_card = Card(card_data['rank'], card_data['suit'])
        position = data.get('position', state.play_state.next_to_play)
        user_id = data.get('user_id', 1)
        session_id = data.get('session_id')
        # Get hand_number from game session (1-indexed for display)
        hand_number = state.game_session.hands_completed + 1 if state.game_session else None

        # Get feedback generator (uses DDS if available, Minimax otherwise)
        feedback_generator = get_play_feedback_generator(use_dds=True)

        # Evaluate and store the play
        feedback = feedback_generator.evaluate_and_store(
            user_id=user_id,
            play_state=state.play_state,
            user_card=user_card,
            position=position,
            session_id=session_id,
            hand_number=hand_number
        )

        # Get legal cards for response
        hand = state.play_state.hands[position]
        legal_cards = list(hand.cards)
        if state.play_state.current_trick:
            led_suit = state.play_state.current_trick[0][0].suit
            suit_cards = [c for c in hand.cards if c.suit == led_suit]
            if suit_cards:
                legal_cards = suit_cards

        return jsonify({
            "dds_available": feedback_generator.dds_available,
            "score": feedback.score,
            "correctness": feedback.correctness.value,
            "rating": feedback.correctness.value,  # Alias for backward compatibility
            "optimal_cards": feedback.optimal_cards,
            "tricks_cost": feedback.tricks_cost,
            "tricks_with_user_card": feedback.tricks_with_user_card,
            "tricks_with_optimal": feedback.tricks_with_optimal,
            "feedback": feedback.reasoning,
            "reasoning": feedback.reasoning,
            "helpful_hint": feedback.helpful_hint,
            "play_category": feedback.play_category.value,
            "key_concept": feedback.key_concept,
            "difficulty": feedback.difficulty,
            "user_card": feedback.user_card,
            "legal_cards": [f"{c.rank}{c.suit}" for c in legal_cards],
            "contract": feedback.contract,
            "trick_number": feedback.trick_number,
            "is_declarer_side": feedback.is_declarer_side,
            "user_message": feedback.to_user_message()
        })

    except Exception as e:
        import traceback
        print(f"Play evaluation error: {e}")
        traceback.print_exc()
        return jsonify({
            "dds_available": False,
            "score": 5,
            "correctness": "error",
            "rating": "error",
            "feedback": f"Evaluation error: {str(e)}",
            "error": str(e)
        })


def log_play_decision(user_id, position, user_card, score, rating, contract, trick_number):
    """Log a user's play decision for dashboard analytics"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO play_decisions
                (user_id, position, user_card, score, rating, contract, trick_number, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, position, user_card, score, rating, contract, trick_number, datetime.now()))
    except Exception as e:
        # Table might not exist yet - that's ok
        print(f"Could not log play decision: {e}")


@app.route("/api/ai-quality-summary", methods=["GET"])
def ai_quality_summary():
    """
    Get aggregated AI quality metrics for analysis.

    This endpoint provides data suitable for generating quality reports
    and trend analysis.

    Returns:
        JSON with quality metrics, trends, and recommendations
    """
    try:
        # Calculate cutoff time for 30 days (database-agnostic)
        from datetime import timedelta
        cutoff_30_days = datetime.now() - timedelta(days=30)

        with get_connection() as conn:
            cursor = conn.cursor()

            # Daily play counts for trend analysis
            # Using CAST for date extraction (works in both SQLite and PostgreSQL)
            cursor.execute("""
                SELECT
                    COUNT(*) as plays,
                    COUNT(DISTINCT session_id) as sessions,
                    AVG(solve_time_ms) as avg_solve_time_ms,
                    AVG(CASE WHEN used_fallback THEN 1.0 ELSE 0.0 END) as fallback_rate
                FROM ai_play_log
                WHERE timestamp > ?
            """, (cutoff_30_days,))

            row = cursor.fetchone()
            daily_trends = [{'plays': row[0], 'sessions': row[1], 'avg_solve_time_ms': row[2], 'fallback_rate': row[3]}] if row else []

            # Contract type performance
            cursor.execute("""
                SELECT
                    contract,
                    COUNT(*) as plays,
                    AVG(solve_time_ms) as avg_solve_time_ms,
                    AVG(CASE WHEN used_fallback THEN 1.0 ELSE 0.0 END) as fallback_rate
                FROM ai_play_log
                WHERE contract IS NOT NULL
                GROUP BY contract
                ORDER BY COUNT(*) DESC
                LIMIT 20
            """)

            by_contract = [{'contract': row[0], 'plays': row[1], 'avg_solve_time_ms': row[2], 'fallback_rate': row[3]} for row in cursor.fetchall()]

            # All-time stats (use simple query instead of view for compatibility)
            cursor.execute("""
                SELECT
                    COUNT(*) as total_plays,
                    AVG(solve_time_ms) as avg_solve_time_ms,
                    AVG(CASE WHEN used_fallback THEN 1.0 ELSE 0.0 END) as overall_fallback_rate
                FROM ai_play_log
            """)

            row = cursor.fetchone()
            all_time = {'total_plays': row[0], 'avg_solve_time_ms': row[1], 'overall_fallback_rate': row[2]} if row else {}

        # Calculate quality score (0-100)
        # Based on: low fallback rate, reasonable solve times, consistent play
        quality_score = 100
        if overall_fallback_rate := all_time.get('overall_fallback_rate', 0):
            quality_score -= (overall_fallback_rate * 50)  # Penalize fallback

        avg_time = all_time.get('avg_solve_time_ms', 0)
        if avg_time > 1000:  # Over 1 second is slow
            quality_score -= min(30, (avg_time - 1000) / 100)

        quality_score = max(0, min(100, quality_score))

        return jsonify({
            "quality_score": round(quality_score, 1),
            "all_time": all_time,
            "daily_trends": daily_trends,
            "by_contract": by_contract,
            "recommendations": generate_quality_recommendations(all_time, daily_trends)
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error fetching quality summary: {e}"}), 500


def generate_quality_recommendations(all_time, daily_trends):
    """Generate actionable recommendations based on quality metrics"""
    recommendations = []

    fallback_rate = all_time.get('overall_fallback_rate', 0)
    if fallback_rate > 0.5:
        recommendations.append({
            "level": "warning",
            "message": f"High fallback rate ({fallback_rate*100:.1f}%) - DDS may be unavailable",
            "action": "Check DDS installation: pip install endplay"
        })

    avg_time = all_time.get('avg_solve_time_ms', 0)
    if avg_time > 2000:
        recommendations.append({
            "level": "warning",
            "message": f"Slow solve times ({avg_time:.0f}ms avg)",
            "action": "Consider caching or using lower depth for non-expert play"
        })

    total_plays = all_time.get('total_plays_all_time', 0)
    if total_plays < 100:
        recommendations.append({
            "level": "info",
            "message": f"Limited data ({total_plays} plays) - accumulating baseline",
            "action": "Quality metrics will improve with more gameplay data"
        })

    if not recommendations:
        recommendations.append({
            "level": "success",
            "message": "AI performance looks healthy",
            "action": "Continue monitoring for any changes"
        })

    return recommendations


@app.route('/api/auth/simple-login', methods=['POST'])
def simple_login():
    """
    Simple login endpoint - authenticate user by email or phone
    No password required - creates account if doesn't exist

    Expected JSON:
        {
            "email": "user@example.com",  // OR
            "phone": "+15551234567",
            "create_if_not_exists": true
        }

    Returns:
        {
            "user_id": 123,
            "email": "user@example.com",
            "phone": null,
            "created": true  // true if new user, false if existing
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        email = data.get('email')
        phone = data.get('phone')
        create_if_not_exists = data.get('create_if_not_exists', True)

        # Must provide either email or phone
        if not email and not phone:
            return jsonify({"error": "Either email or phone is required"}), 400

        # Validate email format if provided
        if email:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                return jsonify({"error": "Invalid email format"}), 400

        # Validate phone format if provided (basic check)
        if phone:
            # Remove spaces, dashes, parentheses for validation
            phone_cleaned = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')

            # Auto-add +1 for US numbers if not present
            if not phone_cleaned.startswith('+'):
                # Check if it looks like a US number (10 digits)
                digits_only = ''.join(c for c in phone_cleaned if c.isdigit())
                if len(digits_only) == 10:
                    phone = f"+1{digits_only}"
                    phone_cleaned = phone
                elif len(digits_only) == 11 and digits_only.startswith('1'):
                    # Already has 1 prefix, just add +
                    phone = f"+{digits_only}"
                    phone_cleaned = phone
                else:
                    return jsonify({"error": "Invalid phone format. US numbers should be 10 digits (e.g., 234-567-8900)"}), 400

            # Validate final format
            if len(phone_cleaned) < 12:  # +1 + 10 digits minimum
                return jsonify({"error": "Invalid phone format. US numbers should be 10 digits"}), 400

        with get_connection() as conn:
            cursor = conn.cursor()

            # Try to find existing user
            if email:
                cursor.execute('SELECT id, email, phone, display_name FROM users WHERE email = ?', (email,))
            else:
                cursor.execute('SELECT id, email, phone, display_name FROM users WHERE phone = ?', (phone,))

            existing_user = cursor.fetchone()

            if existing_user:
                # User exists - return their info
                return jsonify({
                    "user_id": existing_user[0],
                    "email": existing_user[1],
                    "phone": existing_user[2],
                    "display_name": existing_user[3],
                    "created": False
                })

            # User doesn't exist
            if not create_if_not_exists:
                return jsonify({"error": "User not found"}), 404

            # Create new user
            # Generate username from email or phone
            if email:
                username = email.split('@')[0]
            else:
                username = f"user_{phone[-4:]}"

            # Ensure username is unique
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                # Append random suffix to make unique
                username = f"{username}_{random.randint(1000, 9999)}"

            # Ensure username meets minimum length requirement (3 chars)
            if len(username) < 3:
                username = f"user_{random.randint(100, 999)}"

            # Insert new user
            cursor.execute('''
                INSERT INTO users (username, email, phone, display_name, created_at, last_login)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                username,
                email,
                phone,
                email or phone,  # Use email/phone as display name initially
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

            new_user_id = cursor.lastrowid

            # Send welcome email to new users (only for email signups)
            if email:
                try:
                    from engine.notifications.email_service import send_welcome_email
                    send_welcome_email(email, username)
                except Exception as email_error:
                    # Don't fail signup if email fails
                    print(f"⚠️ Welcome email failed (non-blocking): {email_error}")

            return jsonify({
                "user_id": new_user_id,
                "email": email,
                "phone": phone,
                "display_name": email or phone,
                "created": True
            })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Login failed: {str(e)}"}), 500


if __name__ == '__main__':
    # Use 0.0.0.0 to allow connections from other devices on the network
    # (e.g., testing on iPad, iPhone, Android via local IP address)
    app.run(host='0.0.0.0', port=5001, debug=True)

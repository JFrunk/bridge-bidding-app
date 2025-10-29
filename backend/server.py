import random
import json
import traceback
import os
import sqlite3
import time
from datetime import datetime
from flask import Flask, request, jsonify
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
from engine.bridge_rules_engine import BridgeRulesEngine, GameState as BridgeGameState


# Session state management (fixes global state race conditions)
from core.session_state import SessionStateManager, get_session_id_from_request

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
CORS(app)
engine = BiddingEngine()
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
        conn = sqlite3.connect('bridge.db')
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

        conn.commit()
        conn.close()

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
        user_id = data.get('user_id', request.args.get('user_id', 1))
        session_id = f"user_{user_id}_default"

    # Get or create session state
    state = state_manager.get_or_create(session_id)

    # CRITICAL FIX: Load active game session from database if not already loaded
    # This ensures gameplay tracking persists across requests
    if not state.game_session:
        # Extract user_id from request
        data = request.get_json(silent=True) or {}
        user_id = data.get('user_id', request.args.get('user_id', 1))

        # Check for active session in database
        try:
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
        - ai_difficulty: str (default 'intermediate')

    Returns:
        Session data and whether it was resumed
    """
    # Get session state for this request
    state = get_state()

    data = request.get_json() or {}
    user_id = data.get('user_id', 1)
    session_type = data.get('session_type', 'chicago')
    player_position = data.get('player_position', 'S')
    ai_difficulty = data.get('ai_difficulty', 'intermediate')

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
        - score_data: dict with hand results

    Returns:
        Updated session data
    """
    # Get session state for this request
    state = get_state()

    if not state.game_session:
        return jsonify({'error': 'No active session'}), 400

    if not state.play_state:
        return jsonify({'error': 'No play state available'}), 400

    try:
        data = request.get_json() or {}
        score_data = data.get('score_data', {})

        # Calculate hand duration
        hand_duration = 0
        if state.hand_start_time:
            hand_duration = int((datetime.now() - state.hand_start_time).total_seconds())

        # Determine if user was declarer or dummy
        declarer = state.play_state.contract.declarer
        dummy = state.play_state.dummy
        user_position = state.game_session.player_position

        user_was_declarer = (declarer == user_position)
        user_was_dummy = (dummy == user_position)

        # Add score to session
        hand_score = score_data['score']
        state.game_session.add_hand_score(declarer, hand_score)

        # Prepare hand data for database
        hand_data = {
            'hand_number': state.game_session.hands_completed,  # Already incremented by add_hand_score
            'dealer': session_manager.CHICAGO_DEALERS[(state.game_session.hands_completed - 1) % 4],
            'vulnerability': state.vulnerability,
            'contract': state.play_state.contract,
            'tricks_taken': score_data['tricks_taken'],
            'hand_score': hand_score,
            'made': score_data['made'],
            'breakdown': score_data['breakdown'],
            'deal_data': {
                pos: {
                    'hand': [{'rank': c.rank, 'suit': c.suit} for c in hand.cards],
                    'points': None  # Could add point count here
                }
                for pos, hand in state.play_state.hands.items()
            },
            'auction_history': data.get('auction_history', []),
            'play_history': data.get('play_history', []),
            'user_was_declarer': user_was_declarer,
            'user_was_dummy': user_was_dummy,
            'hand_duration_seconds': hand_duration
        }

        # Save to database
        session_manager.save_hand_result(state.game_session, hand_data)

        # Check if session is complete
        session_complete = state.game_session.is_complete()
        winner = state.game_session.get_winner() if session_complete else None
        user_won = state.game_session.get_user_won() if session_complete else None

        # Reset hand timer for next hand
        state.hand_start_time = datetime.now()

        return jsonify({
            'success': True,
            'session': state.game_session.to_dict(),
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
    Get AI system status including DDS availability

    Returns:
        AI configuration and DDS status
    """
    # Get session state for this request
    state = get_state()
    try:
        ai_status = {
            'dds_available': DDS_AVAILABLE,
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
                    'rating': '9/10' if DDS_AVAILABLE else '8+/10',
                    'description': 'Double Dummy Solver (perfect play)' if DDS_AVAILABLE else 'Deep minimax search (4-ply)',
                    'using_dds': DDS_AVAILABLE
                }
            },
            'current_difficulty': state.ai_difficulty
        }

        # Add DDS statistics if available
        if DDS_AVAILABLE and state.ai_difficulty == 'expert':
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

    # Include dealer in response for frontend
    return jsonify({
        'hand': hand_for_json,
        'points': points_for_json,
        'vulnerability': state.vulnerability,
        'dealer': dealer  # NEW: Send dealer to frontend
    })

@app.route('/api/get-next-bid', methods=['POST'])
def get_next_bid():
    # Get session state for this request
    state = get_state()
    try:
        data = request.get_json()
        print(f"🔍 DEBUG: Received data: {data}")
        print(f"🔍 DEBUG: Keys in data: {list(data.keys()) if data else 'None'}")
        auction_history, current_player = data['auction_history'], data['current_player']
        explanation_level = data.get('explanation_level', 'detailed')  # simple, detailed, or expert

        # For non-South players (hidden hands), use convention_only to avoid revealing hand specifics
        if current_player != 'South':
            explanation_level = 'convention_only'

        player_hand = state.deal[current_player]
        if not player_hand:
            return jsonify({'error': "Deal has not been made yet."}), 400

        bid, explanation = engine.get_next_bid(player_hand, auction_history, current_player,
                                                state.vulnerability, explanation_level)
        return jsonify({'bid': bid, 'explanation': explanation, 'player': current_player})

    except Exception as e:
        print("---!!! AN ERROR OCCURRED IN GET_NEXT_BID !!!---")
        traceback.print_exc()
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
        auction_history, current_player = data['auction_history'], data['current_player']

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
        auction_history = data['auction_history']
        explanation_level = data.get('explanation_level', 'detailed')  # simple, detailed, or expert
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
            import sqlite3

            user_id = 1  # Default user for now

            # Record in practice_history
            conn = sqlite3.connect('bridge.db')
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
            conn.commit()
            conn.close()

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
        auction_history = data.get('auction_history', [])
        current_player = data.get('current_player', 'South')

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

        feedback = feedback_generator.evaluate_and_store(
            user_id=user_id,
            hand=user_hand,
            user_bid=user_bid,
            auction_context=auction_context,
            optimal_bid=optimal_bid,
            optimal_explanation=optimal_explanation_obj,
            session_id=session_id
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
        return jsonify({'error': f'Server error in evaluate_bid: {str(e)}'}), 500

@app.route('/api/get-all-hands', methods=['GET'])
def get_all_hands():
    # Get session state for this request
    state = get_state()
    try:
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
                    if not hand:
                        return jsonify({'error': f'Hand for {position} not available'}), 400

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

        # Get dealer from session (Chicago rotation) or default to North
        dealer = 'North'  # Default for non-session mode
        if state.game_session:
            dealer = state.game_session.get_current_dealer()

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
        is_render = os.getenv('RENDER') or os.getenv('RENDER_SERVICE_NAME') or os.getenv('FLASK_ENV') == 'production'

        if is_render:
            # On Render: don't save to file, embed data in prompt instead
            print("Running on Render - will embed full data in prompt (files not accessible to users)")
            saved_to_file = False
        else:
            # Local development: save to file for reference
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

        # Return the full review data so frontend can display it
        return jsonify({
            'success': True,
            'filename': filename,
            'saved_to_file': saved_to_file,
            'review_data': review_request  # Include full data in response
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Server error in request_review: {e}'}), 500
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

        # Get dealer from request (frontend now sends it) or from session
        dealer_str = data.get("dealer", "North")
        if state.game_session:
            dealer_str = state.game_session.get_current_dealer()

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
            user_role = BridgeRulesEngine.get_player_role('S', declarer, dummy)
            return jsonify({
                "error": f"AI cannot play for position {position} - user controls this position",
                "position": position,
                "user_role": user_role.value,
                "controllable_positions": list(controllable),
                "dummy": dummy,
                "declarer": declarer
            }), 403  # 403 Forbidden

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
        start_time = time.time()
        card = current_ai.choose_card(state.play_state, position)
        solve_time_ms = (time.time() - start_time) * 1000  # Convert to milliseconds

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

            # Check if DDS was available and might have been used
            # If expert level and not on supported platform, fallback was definitely used
            used_fallback = (
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
        dummy_hand = None
        if state.play_state.dummy_revealed or bridge_state.opening_lead_made:
            dummy_pos = state.play_state.dummy
            dummy_hand = {
                "cards": [{"rank": c.rank, "suit": c.suit} for c in state.play_state.hands[dummy_pos].cards],
                "position": dummy_pos
            }

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

        # Generate human-readable result text
        if score_result["made"]:
            overtricks = score_result.get("overtricks", 0)
            if overtricks == 0:
                result_text = "Made exactly"
            else:
                result_text = f"Made +{overtricks}"
        else:
            undertricks = score_result.get("undertricks", 0)
            result_text = f"Down {undertricks}"

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

        conn = sqlite3.connect('bridge.db')
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        cursor = conn.cursor()

        # Overall stats for specified time period
        cursor.execute("""
            SELECT
                COUNT(*) as total_plays,
                COUNT(DISTINCT session_id) as unique_sessions,
                COUNT(DISTINCT DATE(timestamp)) as days_with_data,
                AVG(solve_time_ms) as avg_solve_time_ms,
                MAX(solve_time_ms) as max_solve_time_ms,
                MIN(solve_time_ms) as min_solve_time_ms,
                AVG(CASE WHEN used_fallback THEN 1.0 ELSE 0.0 END) as fallback_rate,
                COUNT(CASE WHEN used_fallback THEN 1 END) as fallback_count,
                MAX(timestamp) as last_play_time
            FROM ai_play_log
            WHERE timestamp > datetime('now', '-' || ? || ' hours')
        """, (hours,))

        overall = dict(cursor.fetchone())

        # Stats by AI level
        cursor.execute("""
            SELECT
                ai_level,
                COUNT(*) as plays,
                AVG(solve_time_ms) as avg_solve_time_ms,
                AVG(CASE WHEN used_fallback THEN 1.0 ELSE 0.0 END) as fallback_rate,
                COUNT(CASE WHEN used_fallback THEN 1 END) as fallback_count
            FROM ai_play_log
            WHERE timestamp > datetime('now', '-' || ? || ' hours')
            GROUP BY ai_level
        """, (hours,))

        by_level = {row['ai_level']: dict(row) for row in cursor.fetchall()}

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

        recent_plays = [dict(row) for row in cursor.fetchall()]

        conn.close()

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
        conn = sqlite3.connect('bridge.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Daily play counts for trend analysis
        cursor.execute("""
            SELECT
                DATE(timestamp) as date,
                COUNT(*) as plays,
                COUNT(DISTINCT session_id) as sessions,
                AVG(solve_time_ms) as avg_solve_time_ms,
                AVG(CASE WHEN used_fallback THEN 1.0 ELSE 0.0 END) as fallback_rate
            FROM ai_play_log
            WHERE timestamp > datetime('now', '-30 days')
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        """)

        daily_trends = [dict(row) for row in cursor.fetchall()]

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
            ORDER BY plays DESC
            LIMIT 20
        """)

        by_contract = [dict(row) for row in cursor.fetchall()]

        # All-time stats
        cursor.execute("""
            SELECT * FROM v_dds_health_summary
        """)

        all_time = dict(cursor.fetchone()) if cursor.fetchone() else {}

        conn.close()

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
            # Remove spaces and check for international format
            phone_cleaned = phone.replace(' ', '').replace('-', '')
            if not phone_cleaned.startswith('+') or len(phone_cleaned) < 10:
                return jsonify({"error": "Invalid phone format (use international format: +1234567890)"}), 400

        conn = sqlite3.connect('bridge.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Try to find existing user
        if email:
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        else:
            cursor.execute('SELECT * FROM users WHERE phone = ?', (phone,))

        existing_user = cursor.fetchone()

        if existing_user:
            # User exists - return their info
            user_dict = dict(existing_user)
            conn.close()

            return jsonify({
                "user_id": user_dict['id'],
                "email": user_dict.get('email'),
                "phone": user_dict.get('phone'),
                "display_name": user_dict.get('display_name'),
                "created": False
            })

        # User doesn't exist
        if not create_if_not_exists:
            conn.close()
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
            import random
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

        conn.commit()
        new_user_id = cursor.lastrowid
        conn.close()

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
    app.run(host='127.0.0.1', port=5001, debug=True)

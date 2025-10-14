import random
import json
import traceback
import os
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

# DDS AI for expert level play (9/10 rating)
try:
    from engine.play.ai.dds_ai import DDSPlayAI, DDS_AVAILABLE
except ImportError:
    DDS_AVAILABLE = False
    print("⚠️  DDS AI not available - install endplay for expert play")

app = Flask(__name__)
CORS(app)
engine = BiddingEngine()
play_engine = PlayEngine()
play_ai = SimplePlayAI()  # Default AI (backward compatibility)
session_manager = SessionManager()  # Session management

# Phase 2: AI difficulty settings
current_ai_difficulty = "beginner"  # Options: beginner, intermediate, advanced, expert

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

current_deal = { 'North': None, 'East': None, 'South': None, 'West': None }
current_vulnerability = "None"
current_play_state = None  # Will hold PlayState during card play
current_session = None  # Active game session
current_hand_start_time = None  # Track hand duration

CONVENTION_MAP = {
    "Preempt": PreemptConvention(),
    "JacobyTransfer": JacobyConvention(),
    "Stayman": StaymanConvention(),
    "Blackwood": BlackwoodConvention()
}

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
    global current_session, current_hand_start_time

    data = request.get_json() or {}
    user_id = data.get('user_id', 1)
    session_type = data.get('session_type', 'chicago')
    player_position = data.get('player_position', 'S')
    ai_difficulty = data.get('ai_difficulty', 'intermediate')

    try:
        # Check for existing active session
        existing = session_manager.get_active_session(user_id)
        if existing:
            current_session = existing
            current_hand_start_time = datetime.now()
            return jsonify({
                'session': existing.to_dict(),
                'resumed': True,
                'message': f'Resumed session #{existing.id}'
            })

        # Create new session
        current_session = session_manager.create_session(
            user_id=user_id,
            session_type=session_type,
            player_position=player_position,
            ai_difficulty=ai_difficulty
        )
        current_hand_start_time = datetime.now()

        return jsonify({
            'session': current_session.to_dict(),
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
    if not current_session:
        return jsonify({'active': False})

    return jsonify({
        'active': True,
        'session': current_session.to_dict()
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
    global current_session, current_play_state, current_hand_start_time

    if not current_session:
        return jsonify({'error': 'No active session'}), 400

    if not current_play_state:
        return jsonify({'error': 'No play state available'}), 400

    try:
        data = request.get_json() or {}
        score_data = data.get('score_data', {})

        # Calculate hand duration
        hand_duration = 0
        if current_hand_start_time:
            hand_duration = int((datetime.now() - current_hand_start_time).total_seconds())

        # Determine if user was declarer or dummy
        declarer = current_play_state.contract.declarer
        dummy = current_play_state.dummy
        user_position = current_session.player_position

        user_was_declarer = (declarer == user_position)
        user_was_dummy = (dummy == user_position)

        # Add score to session
        hand_score = score_data['score']
        current_session.add_hand_score(declarer, hand_score)

        # Prepare hand data for database
        hand_data = {
            'hand_number': current_session.hands_completed,  # Already incremented by add_hand_score
            'dealer': session_manager.CHICAGO_DEALERS[(current_session.hands_completed - 1) % 4],
            'vulnerability': current_vulnerability,
            'contract': current_play_state.contract,
            'tricks_taken': score_data['tricks_taken'],
            'hand_score': hand_score,
            'made': score_data['made'],
            'breakdown': score_data['breakdown'],
            'deal_data': {
                pos: {
                    'hand': [{'rank': c.rank, 'suit': c.suit} for c in hand.cards],
                    'points': None  # Could add point count here
                }
                for pos, hand in current_play_state.hands.items()
            },
            'auction_history': data.get('auction_history', []),
            'play_history': data.get('play_history', []),
            'user_was_declarer': user_was_declarer,
            'user_was_dummy': user_was_dummy,
            'hand_duration_seconds': hand_duration
        }

        # Save to database
        session_manager.save_hand_result(current_session, hand_data)

        # Check if session is complete
        session_complete = current_session.is_complete()
        winner = current_session.get_winner() if session_complete else None
        user_won = current_session.get_user_won() if session_complete else None

        # Reset hand timer for next hand
        current_hand_start_time = datetime.now()

        return jsonify({
            'success': True,
            'session': current_session.to_dict(),
            'hand_completed': current_session.hands_completed,
            'session_complete': session_complete,
            'winner': winner,
            'user_won': user_won,
            'message': f'Hand {current_session.hands_completed} completed'
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
    if not current_session:
        return jsonify({'error': 'No active session'}), 400

    try:
        hands = session_manager.get_session_hands(current_session.id)
        return jsonify({
            'session_id': current_session.id,
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
    global current_session

    if not current_session:
        return jsonify({'error': 'No active session'}), 400

    try:
        session_manager.abandon_session(current_session.id)
        session_id = current_session.id
        current_session = None

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
            'current_difficulty': current_ai_difficulty
        }

        # Add DDS statistics if available
        if DDS_AVAILABLE and current_ai_difficulty == 'expert':
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
        scenario_names = [s['name'] for s in scenarios]
        return jsonify({'scenarios': scenario_names})
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
            "current": current_ai_difficulty
        })
    except Exception as e:
        return jsonify({'error': f'Could not get AI difficulties: {str(e)}'}), 500

@app.route('/api/set-ai-difficulty', methods=['POST'])
def set_ai_difficulty():
    """
    Set AI difficulty level
    Phase 2 Integration
    """
    global current_ai_difficulty, play_ai

    try:
        data = request.get_json()
        difficulty = data.get('difficulty')

        if difficulty not in ai_instances:
            return jsonify({
                'error': f'Invalid difficulty. Must be one of: {list(ai_instances.keys())}'
            }), 400

        current_ai_difficulty = difficulty
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
    try:
        ai = ai_instances[current_ai_difficulty]

        if hasattr(ai, 'get_statistics'):
            stats = ai.get_statistics()
            return jsonify({
                'has_statistics': True,
                'statistics': stats,
                'ai_name': ai.get_name(),
                'difficulty': current_ai_difficulty
            })
        else:
            return jsonify({
                'has_statistics': False,
                'ai_name': ai.get_name(),
                'difficulty': current_ai_difficulty
            })
    except Exception as e:
        return jsonify({'error': f'Could not get AI statistics: {str(e)}'}), 500

@app.route('/api/load-scenario', methods=['POST'])
def load_scenario():
    global current_vulnerability
    current_vulnerability = "None"
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
        
        for pos in current_deal: current_deal[pos] = None
        
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
                current_deal[position] = hand
        
        remaining_cards = deck
        random.shuffle(remaining_cards)
        
        for position in ['North', 'East', 'South', 'West']:
            if not current_deal.get(position):
                current_deal[position] = Hand(remaining_cards[:13])
                remaining_cards = remaining_cards[13:]

        south_hand = current_deal['South']
        hand_for_json = [{'rank': card.rank, 'suit': card.suit} for card in south_hand.cards]
        points_for_json = { 'hcp': south_hand.hcp, 'dist_points': south_hand.dist_points, 'total_points': south_hand.total_points, 'suit_hcp': south_hand.suit_hcp, 'suit_lengths': south_hand.suit_lengths }
        return jsonify({'hand': hand_for_json, 'points': points_for_json, 'vulnerability': current_vulnerability})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Could not load scenario: {e}'}), 500

@app.route('/api/deal-hands', methods=['GET'])
def deal_hands():
    global current_vulnerability
    vulnerabilities = ["None", "NS", "EW", "Both"]
    try:
        current_idx = vulnerabilities.index(current_vulnerability)
        current_vulnerability = vulnerabilities[(current_idx + 1) % len(vulnerabilities)]
    except ValueError:
        current_vulnerability = "None"

    ranks = '23456789TJQKA'
    suits = ['♠', '♥', '♦', '♣']
    deck = [Card(rank, suit) for rank in ranks for suit in suits]
    random.shuffle(deck)
    
    current_deal['North'] = Hand(deck[0:13])
    current_deal['East'] = Hand(deck[13:26])
    current_deal['South'] = Hand(deck[26:39])
    current_deal['West'] = Hand(deck[39:52])
    
    south_hand = current_deal['South']
    hand_for_json = [{'rank': card.rank, 'suit': card.suit} for card in south_hand.cards]
    points_for_json = { 'hcp': south_hand.hcp, 'dist_points': south_hand.dist_points, 'total_points': south_hand.total_points, 'suit_hcp': south_hand.suit_hcp, 'suit_lengths': south_hand.suit_lengths }
    return jsonify({'hand': hand_for_json, 'points': points_for_json, 'vulnerability': current_vulnerability})

@app.route('/api/get-next-bid', methods=['POST'])
def get_next_bid():
    try:
        data = request.get_json()
        auction_history, current_player = data['auction_history'], data['current_player']
        explanation_level = data.get('explanation_level', 'detailed')  # simple, detailed, or expert

        player_hand = current_deal[current_player]
        if not player_hand:
            return jsonify({'error': "Deal has not been made yet."}), 400

        bid, explanation = engine.get_next_bid(player_hand, auction_history, current_player,
                                                current_vulnerability, explanation_level)
        return jsonify({'bid': bid, 'explanation': explanation})

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
    try:
        data = request.get_json()
        auction_history, current_player = data['auction_history'], data['current_player']

        player_hand = current_deal[current_player]
        if not player_hand:
            return jsonify({'error': "Deal has not been made yet."}), 400

        bid, explanation_dict = engine.get_next_bid_structured(player_hand, auction_history,
                                                                current_player, current_vulnerability)
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
    data = request.get_json()
    try:
        auction_history = data['auction_history']
        explanation_level = data.get('explanation_level', 'detailed')  # simple, detailed, or expert
        user_bid, auction_before_user_bid = auction_history[-1], auction_history[:-1]
        user_hand = current_deal['South']
        optimal_bid, explanation = engine.get_next_bid(user_hand, auction_before_user_bid, 'South',
                                                        current_vulnerability, explanation_level)

        was_correct = (user_bid == optimal_bid)

        if was_correct:
            feedback = f"✅ Correct! Your bid of {user_bid} is optimal.\n\n{explanation}"
        else:
            # Provide detailed comparison
            feedback_lines = []
            feedback_lines.append(f"⚠️ Your bid: {user_bid}")
            feedback_lines.append(f"✅ Recommended: {optimal_bid}")
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

@app.route('/api/get-all-hands', methods=['GET'])
def get_all_hands():
    try:
        all_hands = {}
        for position in ['North', 'East', 'South', 'West']:
            hand = current_deal.get(position)
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
                'hand': hand_for_json,
                'points': points_for_json
            }

        return jsonify({
            'hands': all_hands,
            'vulnerability': current_vulnerability
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Server error in get_all_hands: {e}'}), 500

@app.route('/api/request-review', methods=['POST'])
def request_review():
    try:
        data = request.get_json()
        auction_history = data.get('auction_history', [])
        user_concern = data.get('user_concern', '')
        game_phase = data.get('game_phase', 'bidding')  # 'bidding' or 'playing'
        user_hand_data = data.get('user_hand')  # Actual hand shown to user
        user_hand_points = data.get('user_hand_points')  # Actual points shown to user

        # Prepare all hands data (current state of hands)
        all_hands = {}

        if game_phase == 'playing' and current_play_state:
            # During play phase, use hands from play state
            pos_map = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}
            for short_pos, hand in current_play_state.hands.items():
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
                    hand = current_deal.get(position)
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

        # Create review request object
        review_request = {
            'timestamp': datetime.now().isoformat(),
            'game_phase': game_phase,
            'all_hands': all_hands,
            'auction': auction_history,
            'vulnerability': current_vulnerability,
            'dealer': 'North',
            'user_position': 'South',
            'user_concern': user_concern
        }

        # Add play phase data if in gameplay
        if game_phase == 'playing' and current_play_state:
            contract = current_play_state.contract

            # Serialize trick history
            trick_history = []
            for trick in current_play_state.trick_history:
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
                for card, player in current_play_state.current_trick
            ]

            review_request['play_data'] = {
                'contract': {
                    'level': contract.level,
                    'strain': contract.strain,
                    'declarer': contract.declarer,
                    'doubled': contract.doubled,
                    'string': str(contract)
                },
                'dummy': current_play_state.dummy,
                'opening_leader': play_engine.next_player(contract.declarer),
                'trick_history': trick_history,
                'current_trick': current_trick,
                'tricks_won': current_play_state.tricks_won,
                'tricks_taken_ns': current_play_state.tricks_taken_ns,
                'tricks_taken_ew': current_play_state.tricks_taken_ew,
                'next_to_play': current_play_state.next_to_play,
                'dummy_revealed': current_play_state.dummy_revealed,
                'is_complete': current_play_state.is_complete
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
    global current_play_state
    
    try:
        data = request.get_json()
        auction = data.get("auction_history", [])
        vulnerability_str = data.get("vulnerability", "None")
        
        # Determine contract from auction
        contract = play_engine.determine_contract(auction, dealer_index=0)
        
        if not contract:
            return jsonify({"error": "No contract found (all passed)"}), 400
        
        # Set up vulnerability dict
        vuln_dict = {
            "ns": vulnerability_str in ["NS", "Both"],
            "ew": vulnerability_str in ["EW", "Both"]
        }

        # Get hands (from request or global current_deal)
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
            # Use current deal from bidding phase
            # Map single letters to full names
            pos_map = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}
            hands = {}
            for pos in ["N", "E", "S", "W"]:
                full_name = pos_map[pos]
                if current_deal.get(full_name):
                    hands[pos] = current_deal[full_name]
                else:
                    return jsonify({"error": f"Hand data not found for {full_name}. Please deal a new hand."}), 400
        
        # Create play state
        current_play_state = PlayState(
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
        opening_leader = current_play_state.next_to_play
        dummy_position = current_play_state.dummy
        
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

@app.route("/api/play-card", methods=["POST"])
def play_card():
    """
    User plays a card
    """
    global current_play_state
    
    if not current_play_state:
        return jsonify({"error": "No play in progress"}), 400
    
    try:
        data = request.get_json()
        card_data = data.get("card")
        position = data.get("position", "South")

        # Check if trick is already complete (4 cards) - prevent overplay
        if len(current_play_state.current_trick) >= 4:
            return jsonify({
                "error": "Trick is complete. Please wait for it to be cleared."
            }), 400

        # Validate phase allows card play
        if not current_play_state.can_play_card():
            return jsonify({
                "error": f"Cannot play cards in current phase: {current_play_state.phase}"
            }), 400

        # Create card object
        card = Card(rank=card_data["rank"], suit=card_data["suit"])
        hand = current_play_state.hands[position]

        # Validate legal play
        is_legal = play_engine.is_legal_play(
            card, hand, current_play_state.current_trick,
            current_play_state.contract.trump_suit
        )
        
        if not is_legal:
            return jsonify({
                "legal": False,
                "error": "Must follow suit if able"
            }), 400
        
        # Play the card
        current_play_state.current_trick.append((card, position))

        # Track who led this trick (first card played)
        if len(current_play_state.current_trick) == 1:
            current_play_state.current_trick_leader = position

        # Remove card from hand
        hand.cards.remove(card)

        # Update phase after card played (auto-transition)
        current_play_state.update_phase_after_card()

        # Reveal dummy after opening lead
        if len(current_play_state.current_trick) == 1 and not current_play_state.dummy_revealed:
            current_play_state.dummy_revealed = True
        
        # Check if trick is complete
        trick_complete = len(current_play_state.current_trick) == 4
        trick_winner = None
        
        if trick_complete:
            # Determine winner
            trick_winner = play_engine.determine_trick_winner(
                current_play_state.current_trick,
                current_play_state.contract.trump_suit
            )

            # Update tricks won
            current_play_state.tricks_won[trick_winner] += 1

            # Save to history
            from engine.play_engine import Trick
            current_play_state.trick_history.append(
                Trick(
                    cards=list(current_play_state.current_trick),
                    leader=current_play_state.current_trick_leader,  # FIXED: Use tracked leader
                    winner=trick_winner
                )
            )

            # DON'T clear trick yet - let frontend display it with winner
            # Frontend will call /api/clear-trick after showing winner

            # Next player is the winner
            current_play_state.next_to_play = trick_winner
        else:
            # Next player clockwise
            current_play_state.next_to_play = play_engine.next_player(position)

        return jsonify({
            "legal": True,
            "trick_complete": trick_complete,
            "trick_winner": trick_winner,
            "next_to_play": current_play_state.next_to_play,
            "tricks_won": current_play_state.tricks_won,
            "dummy_revealed": current_play_state.dummy_revealed
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error playing card: {e}"}), 500

@app.route("/api/get-ai-play", methods=["POST"])
def get_ai_play():
    """
    AI plays a card
    """
    global current_play_state
    
    if not current_play_state:
        return jsonify({"error": "No play in progress"}), 400
    
    try:
        position = current_play_state.next_to_play

        # Check if trick is already complete (4 cards) - prevent overplay
        if len(current_play_state.current_trick) >= 4:
            return jsonify({
                "error": "Trick is complete. Please wait for it to be cleared."
            }), 400

        # Validate phase allows card play
        if not current_play_state.can_play_card():
            return jsonify({
                "error": f"Cannot play cards in current phase: {current_play_state.phase}"
            }), 400

        # AI chooses card
        card = play_ai.choose_card(current_play_state, position)
        hand = current_play_state.hands[position]

        # Play the card
        current_play_state.current_trick.append((card, position))

        # Track who led this trick (first card played)
        if len(current_play_state.current_trick) == 1:
            current_play_state.current_trick_leader = position

        hand.cards.remove(card)

        # Update phase after card played (auto-transition)
        current_play_state.update_phase_after_card()

        # Reveal dummy after opening lead
        if len(current_play_state.current_trick) == 1 and not current_play_state.dummy_revealed:
            current_play_state.dummy_revealed = True
        
        # Check if trick is complete
        trick_complete = len(current_play_state.current_trick) == 4
        trick_winner = None

        if trick_complete:
            # Determine winner
            trick_winner = play_engine.determine_trick_winner(
                current_play_state.current_trick,
                current_play_state.contract.trump_suit
            )

            # Update tricks won
            current_play_state.tricks_won[trick_winner] += 1

            # Save to history
            from engine.play_engine import Trick
            current_play_state.trick_history.append(
                Trick(
                    cards=list(current_play_state.current_trick),
                    leader=current_play_state.current_trick_leader,  # FIXED: Use tracked leader
                    winner=trick_winner
                )
            )

            # DON'T clear trick yet - let frontend display it with winner
            # Frontend will call /api/clear-trick after showing winner

            # Next player is the winner
            current_play_state.next_to_play = trick_winner
        else:
            # Next player clockwise
            current_play_state.next_to_play = play_engine.next_player(position)

        return jsonify({
            "card": {"rank": card.rank, "suit": card.suit},
            "position": position,
            "trick_complete": trick_complete,
            "trick_winner": trick_winner,
            "next_to_play": current_play_state.next_to_play,
            "tricks_won": current_play_state.tricks_won,
            "explanation": f"{position} played {card.rank}{card.suit}"
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error with AI play: {e}"}), 500

@app.route("/api/get-play-state", methods=["GET"])
def get_play_state():
    """
    Get current play state
    """
    if not current_play_state:
        return jsonify({"error": "No play in progress"}), 400

    try:
        # Convert current trick to JSON
        current_trick_json = [
            {"card": {"rank": c.rank, "suit": c.suit}, "position": p}
            for c, p in current_play_state.current_trick
        ]

        # Check if trick is complete (4 cards played)
        trick_complete = len(current_play_state.current_trick) == 4
        trick_winner = None
        if trick_complete:
            # Get winner from most recent trick in history
            if current_play_state.trick_history:
                trick_winner = current_play_state.trick_history[-1].winner

        # Get dummy hand if revealed
        dummy_hand = None
        if current_play_state.dummy_revealed:
            dummy_pos = current_play_state.dummy
            dummy_hand = {
                "cards": [{"rank": c.rank, "suit": c.suit} for c in current_play_state.hands[dummy_pos].cards],
                "position": dummy_pos
            }

        return jsonify({
            "contract": {
                "level": current_play_state.contract.level,
                "strain": current_play_state.contract.strain,
                "declarer": current_play_state.contract.declarer,
                "doubled": current_play_state.contract.doubled
            },
            "current_trick": current_trick_json,
            "trick_complete": trick_complete,
            "trick_winner": trick_winner,
            "tricks_won": current_play_state.tricks_won,
            "next_to_play": current_play_state.next_to_play,
            "dummy": current_play_state.dummy,
            "dummy_revealed": current_play_state.dummy_revealed,
            "dummy_hand": dummy_hand,
            "is_complete": current_play_state.is_complete,
            "phase": str(current_play_state.phase)  # Include current phase
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
    global current_play_state

    if not current_play_state:
        return jsonify({"error": "No play in progress"}), 400

    try:
        # Clear the current trick and reset leader
        current_play_state.current_trick = []
        current_play_state.current_trick_leader = None

        # If play is complete after clearing, phase will already be PLAY_COMPLETE
        # (updated by update_phase_after_card when last card was played)

        return jsonify({
            "success": True,
            "message": "Trick cleared",
            "phase": str(current_play_state.phase)
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error clearing trick: {e}"}), 500

@app.route("/api/complete-play", methods=["GET", "POST"])
def complete_play():
    """
    Get final results after play completes
    """
    if not current_play_state:
        return jsonify({"error": "No play in progress"}), 400

    try:
        # Accept vulnerability from request (POST) or use global (GET)
        vulnerability = current_vulnerability
        if request.method == "POST":
            data = request.get_json() or {}
            vulnerability = data.get('vulnerability', current_vulnerability)

        # Determine declarer side and calculate tricks taken
        declarer = current_play_state.contract.declarer
        if declarer in ["N", "S"]:
            tricks_taken = current_play_state.tricks_won['N'] + current_play_state.tricks_won['S']
        else:
            tricks_taken = current_play_state.tricks_won['E'] + current_play_state.tricks_won['W']

        # Calculate vulnerability
        vuln_dict = {
            "ns": vulnerability in ["NS", "Both"],
            "ew": vulnerability in ["EW", "Both"]
        }
        
        # Calculate score (including honors)
        score_result = play_engine.calculate_score(
            current_play_state.contract,
            tricks_taken,
            vuln_dict,
            current_play_state.hands  # Pass hands for honors calculation
        )
        
        return jsonify({
            "contract": str(current_play_state.contract),
            "tricks_taken": tricks_taken,
            "tricks_needed": current_play_state.contract.tricks_needed,
            "score": score_result["score"],
            "made": score_result["made"],
            "overtricks": score_result.get("overtricks", 0),
            "undertricks": score_result.get("undertricks", 0),
            "breakdown": score_result.get("breakdown", {})
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error calculating final score: {e}"}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)

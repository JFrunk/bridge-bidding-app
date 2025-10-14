"""
Analytics API - Endpoints for mistake analysis and learning insights

Provides:
- Practice recording with error categorization
- Mistake analysis and insights
- Dashboard summary data
- Celebration management
- Practice recommendations

To add to server.py:
    from engine.learning.analytics_api import register_analytics_endpoints
    register_analytics_endpoints(app)
"""

from flask import request, jsonify
from typing import Dict, List, Optional
import json

from engine.learning.user_manager import get_user_manager
from engine.learning.error_categorizer import get_error_categorizer
from engine.learning.mistake_analyzer import get_mistake_analyzer
from engine.learning.celebration_manager import get_celebration_manager
from engine.hand import Hand


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def parse_hand_from_request(hand_data: Dict) -> Optional[Hand]:
    """Parse hand data from request JSON"""
    try:
        # Assuming hand_data contains card information
        # This will depend on your Hand class implementation
        # For now, return None and handle in practice recording
        return None
    except Exception as e:
        print(f"Error parsing hand: {e}")
        return None


# ============================================================================
# PRACTICE RECORDING
# ============================================================================

def record_practice():
    """
    POST /api/practice/record
    Record a practice hand with error categorization

    Body:
        {
            "user_id": 1,
            "convention_id": "stayman",
            "hand": {...},
            "user_bid": "2♣",
            "correct_bid": "2♦",
            "was_correct": false,
            "auction_context": {...},
            "hints_used": 0,
            "time_taken_seconds": 45
        }
    """
    data = request.get_json()

    # Required fields
    user_id = data.get('user_id')
    user_bid = data.get('user_bid')
    correct_bid = data.get('correct_bid')
    was_correct = data.get('was_correct')

    if not all([user_id, user_bid is not None, correct_bid is not None, was_correct is not None]):
        return jsonify({'error': 'Missing required fields'}), 400

    # Optional fields
    convention_id = data.get('convention_id')
    hand_data = data.get('hand')
    auction_context = data.get('auction_context', {})
    hints_used = data.get('hints_used', 0)
    time_taken = data.get('time_taken_seconds')
    session_id = data.get('session_id')

    try:
        # Get managers
        user_manager = get_user_manager()
        error_categorizer = get_error_categorizer()
        mistake_analyzer = get_mistake_analyzer()

        # Categorize error (if incorrect)
        categorized_error = None
        if not was_correct and hand_data:
            # Parse hand (simplified - you may need to adjust based on your Hand class)
            hand = parse_hand_from_request(hand_data)

            if hand:
                categorized_error = error_categorizer.categorize(
                    hand=hand,
                    user_bid=user_bid,
                    correct_bid=correct_bid,
                    convention_id=convention_id,
                    auction_context=auction_context
                )

        # Record in practice_history
        import sqlite3
        conn = sqlite3.connect('bridge.db')
        cursor = conn.cursor()

        try:
            # Insert practice record
            cursor.execute("""
                INSERT INTO practice_history (
                    user_id, session_id, convention_id,
                    user_bid, correct_bid, was_correct,
                    error_category, error_subcategory,
                    hand_characteristics, hints_used,
                    time_taken_seconds, xp_earned, feedback_shown
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                session_id,
                convention_id,
                user_bid,
                correct_bid,
                was_correct,
                categorized_error.category if categorized_error else None,
                categorized_error.subcategory if categorized_error else None,
                json.dumps(categorized_error.hand_characteristics) if categorized_error else None,
                hints_used,
                time_taken,
                10 if was_correct else 5,  # XP: 10 for correct, 5 for attempt
                categorized_error.hint if categorized_error else None
            ))

            practice_id = cursor.lastrowid

            # Update streak and XP
            user_manager.update_streak(user_id)
            xp_earned = 10 if was_correct else 5
            user_manager.add_xp(user_id, xp_earned)

            # Update user gamification stats
            cursor.execute("""
                UPDATE user_gamification
                SET total_hands_practiced = total_hands_practiced + 1,
                    overall_accuracy = (
                        SELECT AVG(CASE WHEN was_correct THEN 1.0 ELSE 0.0 END)
                        FROM practice_history
                        WHERE user_id = ?
                    ),
                    recent_accuracy = (
                        SELECT AVG(CASE WHEN was_correct THEN 1.0 ELSE 0.0 END)
                        FROM (
                            SELECT was_correct
                            FROM practice_history
                            WHERE user_id = ?
                            ORDER BY timestamp DESC
                            LIMIT 20
                        )
                    )
                WHERE user_id = ?
            """, (user_id, user_id, user_id))

            conn.commit()

            # Analyze pattern if error
            if not was_correct:
                mistake_analyzer.analyze_practice_hand(user_id, practice_id)

            # Get updated stats
            user_stats = user_manager.get_user_stats(user_id)

            response = {
                'success': True,
                'practice_id': practice_id,
                'xp_earned': xp_earned,
                'user_stats': {
                    'total_xp': user_stats.total_xp,
                    'current_level': user_stats.current_level,
                    'current_streak': user_stats.current_streak_days,
                    'total_hands': user_stats.total_hands_practiced,
                    'overall_accuracy': user_stats.overall_accuracy
                } if user_stats else None
            }

            if categorized_error:
                response['feedback'] = {
                    'category': categorized_error.category,
                    'subcategory': categorized_error.subcategory,
                    'hint': categorized_error.hint
                }

            return jsonify(response)

        except Exception as e:
            conn.rollback()
            return jsonify({'error': f'Database error: {str(e)}'}), 500
        finally:
            conn.close()

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ANALYTICS & INSIGHTS
# ============================================================================

def get_mistakes():
    """
    GET /api/analytics/mistakes?user_id=<id>&status=<status>
    Get mistake patterns for user

    Query params:
        user_id: User ID (required)
        status: Optional status filter ('active', 'improving', 'resolved', 'needs_attention')
    """
    user_id = request.args.get('user_id', type=int)
    status_filter = request.args.get('status')

    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    try:
        analyzer = get_mistake_analyzer()
        patterns = analyzer.get_user_patterns(user_id, status_filter)

        return jsonify({
            'user_id': user_id,
            'status_filter': status_filter,
            'patterns': [
                {
                    'id': p.id,
                    'convention_id': p.convention_id,
                    'error_category': p.error_category,
                    'error_subcategory': p.error_subcategory,
                    'total_occurrences': p.total_occurrences,
                    'recent_occurrences': p.recent_occurrences,
                    'current_accuracy': p.current_accuracy,
                    'improvement_rate': p.improvement_rate,
                    'trend': p.trend,
                    'status': p.status,
                    'recommended_practice_hands': p.recommended_practice_hands,
                    'practice_hands_completed': p.practice_hands_completed
                }
                for p in patterns
            ],
            'count': len(patterns)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_dashboard():
    """
    GET /api/analytics/dashboard?user_id=<id>
    Get comprehensive dashboard summary

    Returns:
        - Insight summary (patterns, trends, growth areas)
        - Recent wins
        - Pending celebrations
        - User stats
        - Practice recommendations
    """
    user_id = request.args.get('user_id', type=int)

    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    try:
        user_manager = get_user_manager()
        analyzer = get_mistake_analyzer()
        celebration_manager = get_celebration_manager()

        # Get user stats
        user_stats = user_manager.get_user_stats(user_id)

        # Get insight summary
        insights = analyzer.get_insight_summary(user_id)

        # Get pending celebrations
        pending_celebrations = celebration_manager.get_pending_celebrations(user_id)

        # Get practice recommendations
        recommendations = analyzer.get_practice_recommendations(user_id, max_recommendations=3)

        return jsonify({
            'user_id': user_id,
            'user_stats': {
                'total_xp': user_stats.total_xp,
                'current_level': user_stats.current_level,
                'xp_to_next_level': user_stats.xp_to_next_level,
                'current_streak': user_stats.current_streak_days,
                'longest_streak': user_stats.longest_streak_days,
                'total_hands': user_stats.total_hands_practiced,
                'overall_accuracy': user_stats.overall_accuracy,
                'recent_accuracy': user_stats.recent_accuracy
            } if user_stats else None,
            'insights': {
                'total_patterns': insights.total_patterns,
                'active_patterns': insights.active_patterns,
                'improving_patterns': insights.improving_patterns,
                'resolved_patterns': insights.resolved_patterns,
                'needs_attention_patterns': insights.needs_attention_patterns,
                'overall_trend': insights.overall_trend,
                'top_growth_areas': insights.top_growth_areas,
                'recent_wins': insights.recent_wins,
                'recommended_focus': insights.recommended_focus
            },
            'pending_celebrations': [
                {
                    'id': c.id,
                    'milestone_type': c.milestone_type,
                    'title': c.title,
                    'message': c.message,
                    'emoji': c.celebration_emoji,
                    'xp_reward': c.xp_reward,
                    'achieved_at': c.achieved_at.isoformat()
                }
                for c in pending_celebrations
            ],
            'practice_recommendations': recommendations
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_celebrations():
    """
    GET /api/analytics/celebrations?user_id=<id>&pending_only=<bool>
    Get celebrations for user

    Query params:
        user_id: User ID (required)
        pending_only: If true, only return unshown celebrations (default: true)
    """
    user_id = request.args.get('user_id', type=int)
    pending_only = request.args.get('pending_only', 'true').lower() == 'true'

    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    try:
        celebration_manager = get_celebration_manager()

        if pending_only:
            celebrations = celebration_manager.get_pending_celebrations(user_id)
        else:
            celebrations = celebration_manager.get_recent_celebrations(user_id, limit=20)

        return jsonify({
            'user_id': user_id,
            'pending_only': pending_only,
            'celebrations': [
                {
                    'id': c.id,
                    'milestone_type': c.milestone_type,
                    'milestone_subtype': c.milestone_subtype,
                    'title': c.title,
                    'message': c.message,
                    'emoji': c.celebration_emoji,
                    'xp_reward': c.xp_reward,
                    'achieved_at': c.achieved_at.isoformat(),
                    'shown_to_user': c.shown_to_user,
                    'acknowledged_at': c.acknowledged_at.isoformat() if c.acknowledged_at else None
                }
                for c in celebrations
            ],
            'count': len(celebrations)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def acknowledge_celebration():
    """
    POST /api/analytics/acknowledge-celebration
    Mark a celebration as acknowledged

    Body:
        {
            "milestone_id": 123
        }
    """
    data = request.get_json()
    milestone_id = data.get('milestone_id')

    if not milestone_id:
        return jsonify({'error': 'milestone_id required'}), 400

    try:
        celebration_manager = get_celebration_manager()
        success = celebration_manager.acknowledge_celebration(milestone_id)

        if success:
            return jsonify({
                'success': True,
                'milestone_id': milestone_id
            })
        else:
            return jsonify({'error': 'Celebration not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_practice_recommended():
    """
    GET /api/practice/recommended?user_id=<id>&max=<count>
    Get recommended practice hands based on mistake patterns

    Query params:
        user_id: User ID (required)
        max: Maximum recommendations (default: 5)
    """
    user_id = request.args.get('user_id', type=int)
    max_recommendations = request.args.get('max', default=5, type=int)

    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    try:
        analyzer = get_mistake_analyzer()
        recommendations = analyzer.get_practice_recommendations(user_id, max_recommendations)

        return jsonify({
            'user_id': user_id,
            'recommendations': recommendations,
            'count': len(recommendations)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def run_analysis():
    """
    POST /api/analytics/run-analysis
    Run complete analysis for user (updates all pattern statuses)

    Body:
        {
            "user_id": 1
        }
    """
    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    try:
        analyzer = get_mistake_analyzer()
        results = analyzer.run_full_analysis(user_id)

        return jsonify({
            'success': True,
            'results': results
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# USER MANAGEMENT
# ============================================================================

def create_user():
    """
    POST /api/user/create
    Create a new user

    Body:
        {
            "username": "player1",
            "email": "player1@example.com",
            "display_name": "Player One"
        }
    """
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    display_name = data.get('display_name')

    if not username:
        return jsonify({'error': 'username required'}), 400

    try:
        user_manager = get_user_manager()
        user_id = user_manager.create_user(username, email, display_name)

        if user_id:
            user = user_manager.get_user(user_id)
            return jsonify({
                'success': True,
                'user_id': user_id,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'display_name': user.display_name
                } if user else None
            })
        else:
            return jsonify({'error': 'Failed to create user'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_user_info():
    """
    GET /api/user/info?user_id=<id>
    Get user information and stats
    """
    user_id = request.args.get('user_id', type=int)

    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    try:
        user_manager = get_user_manager()
        user = user_manager.get_user(user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        user_stats = user_manager.get_user_stats(user_id)
        user_settings = user_manager.get_user_settings(user_id)

        return jsonify({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'display_name': user.display_name,
                'created_at': user.created_at.isoformat() if user.created_at else None
            },
            'stats': {
                'total_xp': user_stats.total_xp,
                'current_level': user_stats.current_level,
                'xp_to_next_level': user_stats.xp_to_next_level,
                'current_streak': user_stats.current_streak_days,
                'longest_streak': user_stats.longest_streak_days,
                'total_hands': user_stats.total_hands_practiced,
                'overall_accuracy': user_stats.overall_accuracy,
                'recent_accuracy': user_stats.recent_accuracy
            } if user_stats else None,
            'settings': user_settings
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# REGISTER ENDPOINTS
# ============================================================================

def register_analytics_endpoints(app):
    """
    Register all analytics endpoints with Flask app.

    Usage in server.py:
        from engine.learning.analytics_api import register_analytics_endpoints
        register_analytics_endpoints(app)
    """

    # Practice recording
    app.route('/api/practice/record', methods=['POST'])(record_practice)
    app.route('/api/practice/recommended', methods=['GET'])(get_practice_recommended)

    # Analytics & insights
    app.route('/api/analytics/mistakes', methods=['GET'])(get_mistakes)
    app.route('/api/analytics/dashboard', methods=['GET'])(get_dashboard)
    app.route('/api/analytics/celebrations', methods=['GET'])(get_celebrations)
    app.route('/api/analytics/acknowledge-celebration', methods=['POST'])(acknowledge_celebration)
    app.route('/api/analytics/run-analysis', methods=['POST'])(run_analysis)

    # User management
    app.route('/api/user/create', methods=['POST'])(create_user)
    app.route('/api/user/info', methods=['GET'])(get_user_info)

    print("✓ Analytics API endpoints registered")

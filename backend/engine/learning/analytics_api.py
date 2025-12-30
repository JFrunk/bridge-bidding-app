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
import os
import sys
from pathlib import Path

from engine.learning.user_manager import get_user_manager
from engine.learning.error_categorizer import get_error_categorizer
from engine.learning.mistake_analyzer import get_mistake_analyzer
from engine.learning.celebration_manager import get_celebration_manager
from engine.hand import Hand

# Database abstraction layer for SQLite/PostgreSQL compatibility
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from db import get_connection, date_subtract, date_between

# Legacy DB_PATH kept for reference but not used
DB_PATH = 'bridge.db'


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
        conn = get_connection()
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


def get_bidding_feedback_stats_for_user(user_id: int) -> Dict:
    """
    Calculate bidding feedback statistics from bidding_decisions table (Phase 1)

    Returns:
        - avg_score: Average quality score (0-10)
        - total_decisions: Total bidding decisions recorded
        - optimal_rate: Percentage of optimal bids
        - error_rate: Percentage of error bids
        - critical_errors: Count of critical errors
        - recent_trend: 'improving', 'stable', or 'declining'
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Overall stats (last 30 days)
        cursor.execute(f"""
            SELECT
                COUNT(*) as total_decisions,
                AVG(score) as avg_score,
                SUM(CASE WHEN correctness = 'optimal' THEN 1 ELSE 0 END) as optimal_count,
                SUM(CASE WHEN correctness = 'acceptable' THEN 1 ELSE 0 END) as acceptable_count,
                SUM(CASE WHEN correctness = 'suboptimal' THEN 1 ELSE 0 END) as suboptimal_count,
                SUM(CASE WHEN correctness = 'error' THEN 1 ELSE 0 END) as error_count,
                SUM(CASE WHEN impact = 'critical' THEN 1 ELSE 0 END) as critical_errors
            FROM bidding_decisions
            WHERE user_id = ?
              AND timestamp >= {date_subtract(30)}
        """, (user_id,))

        overall_row = cursor.fetchone()

        if not overall_row or overall_row['total_decisions'] == 0:
            return {
                'avg_score': 0,
                'total_decisions': 0,
                'optimal_rate': 0,
                'acceptable_rate': 0,
                'error_rate': 0,
                'critical_errors': 0,
                'recent_trend': 'stable'
            }

        total = overall_row['total_decisions']
        avg_score = overall_row['avg_score'] or 0
        optimal_count = overall_row['optimal_count'] or 0
        acceptable_count = overall_row['acceptable_count'] or 0
        error_count = overall_row['error_count'] or 0
        critical_errors = overall_row['critical_errors'] or 0

        # Calculate trend (compare last 7 days vs previous 7 days)
        cursor.execute(f"""
            SELECT AVG(score) as avg_score
            FROM bidding_decisions
            WHERE user_id = ?
              AND timestamp >= {date_subtract(7)}
        """, (user_id,))
        recent_row = cursor.fetchone()
        recent_avg = recent_row['avg_score'] or 0

        prev_start, prev_end = date_between(14, 7)
        cursor.execute(f"""
            SELECT AVG(score) as avg_score
            FROM bidding_decisions
            WHERE user_id = ?
              AND timestamp >= {prev_start}
              AND timestamp < {prev_end}
        """, (user_id,))
        previous_row = cursor.fetchone()
        previous_avg = previous_row['avg_score'] or 0

        # Determine trend
        if previous_avg == 0:
            trend = 'stable'
        elif recent_avg > previous_avg + 0.3:
            trend = 'improving'
        elif recent_avg < previous_avg - 0.3:
            trend = 'declining'
        else:
            trend = 'stable'

        return {
            'avg_score': round(avg_score, 1),
            'total_decisions': total,
            'optimal_rate': round(optimal_count / total, 3) if total > 0 else 0,
            'acceptable_rate': round(acceptable_count / total, 3) if total > 0 else 0,
            'error_rate': round(error_count / total, 3) if total > 0 else 0,
            'critical_errors': critical_errors,
            'recent_trend': trend
        }

    finally:
        conn.close()


def get_recent_bidding_decisions_for_user(user_id: int, limit: int = 10) -> List[Dict]:
    """
    Get recent bidding decisions for dashboard display (Phase 1)

    Returns list of recent decisions with display-friendly format
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                id,
                bid_number,
                position,
                user_bid,
                optimal_bid,
                correctness,
                score,
                impact,
                key_concept,
                error_category,
                helpful_hint,
                timestamp
            FROM bidding_decisions
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user_id, limit))

        decisions = []
        for row in cursor.fetchall():
            decisions.append({
                'id': row['id'],
                'bid_number': row['bid_number'],
                'position': row['position'],
                'user_bid': row['user_bid'],
                'optimal_bid': row['optimal_bid'],
                'correctness': row['correctness'],
                'score': row['score'],
                'impact': row['impact'],
                'key_concept': row['key_concept'],
                'error_category': row['error_category'],
                'helpful_hint': row['helpful_hint'],
                'timestamp': row['timestamp']
            })

        return decisions

    finally:
        conn.close()


def get_play_feedback_stats_for_user(user_id: int) -> Dict:
    """
    Calculate play feedback statistics from play_decisions table.
    Mirrors bidding_feedback_stats structure for dashboard consistency.

    Returns:
        - avg_score: Average quality score (0-10)
        - total_decisions: Total play decisions recorded
        - optimal_rate: Percentage of optimal plays
        - good_rate: Percentage of good plays
        - blunder_rate: Percentage of blunders
        - recent_trend: 'improving', 'stable', or 'declining'
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Overall stats (last 30 days)
        cursor.execute(f"""
            SELECT
                COUNT(*) as total_decisions,
                AVG(score) as avg_score,
                SUM(CASE WHEN rating = 'optimal' THEN 1 ELSE 0 END) as optimal_count,
                SUM(CASE WHEN rating = 'good' THEN 1 ELSE 0 END) as good_count,
                SUM(CASE WHEN rating = 'suboptimal' THEN 1 ELSE 0 END) as suboptimal_count,
                SUM(CASE WHEN rating = 'blunder' THEN 1 ELSE 0 END) as blunder_count
            FROM play_decisions
            WHERE user_id = ?
              AND timestamp >= {date_subtract(30)}
        """, (user_id,))

        overall_row = cursor.fetchone()

        if not overall_row or overall_row['total_decisions'] == 0:
            return {
                'avg_score': 0,
                'total_decisions': 0,
                'optimal_rate': 0,
                'good_rate': 0,
                'blunder_rate': 0,
                'recent_trend': 'stable'
            }

        total = overall_row['total_decisions']
        avg_score = overall_row['avg_score'] or 0
        optimal_count = overall_row['optimal_count'] or 0
        good_count = overall_row['good_count'] or 0
        blunder_count = overall_row['blunder_count'] or 0

        # Calculate trend (compare last 7 days vs previous 7 days)
        cursor.execute(f"""
            SELECT AVG(score) as avg_score
            FROM play_decisions
            WHERE user_id = ?
              AND timestamp >= {date_subtract(7)}
        """, (user_id,))
        recent_row = cursor.fetchone()
        recent_avg = recent_row['avg_score'] or 0

        play_prev_start, play_prev_end = date_between(14, 7)
        cursor.execute(f"""
            SELECT AVG(score) as avg_score
            FROM play_decisions
            WHERE user_id = ?
              AND timestamp >= {play_prev_start}
              AND timestamp < {play_prev_end}
        """, (user_id,))
        previous_row = cursor.fetchone()
        previous_avg = previous_row['avg_score'] or 0

        # Determine trend
        if previous_avg == 0:
            trend = 'stable'
        elif recent_avg > previous_avg + 0.3:
            trend = 'improving'
        elif recent_avg < previous_avg - 0.3:
            trend = 'declining'
        else:
            trend = 'stable'

        return {
            'avg_score': round(avg_score, 1),
            'total_decisions': total,
            'optimal_rate': round(optimal_count / total, 3) if total > 0 else 0,
            'good_rate': round(good_count / total, 3) if total > 0 else 0,
            'blunder_rate': round(blunder_count / total, 3) if total > 0 else 0,
            'recent_trend': trend
        }

    except Exception as e:
        # Table might not exist yet
        print(f"Could not get play feedback stats: {e}")
        return {
            'avg_score': 0,
            'total_decisions': 0,
            'optimal_rate': 0,
            'good_rate': 0,
            'blunder_rate': 0,
            'recent_trend': 'stable'
        }

    finally:
        conn.close()


def get_recent_play_decisions_for_user(user_id: int, limit: int = 10) -> List[Dict]:
    """
    Get recent play decisions for dashboard display.
    Mirrors get_recent_bidding_decisions_for_user structure.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                id,
                position,
                trick_number,
                user_card,
                optimal_card,
                score,
                rating,
                tricks_cost,
                contract,
                feedback,
                timestamp
            FROM play_decisions
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user_id, limit))

        decisions = []
        for row in cursor.fetchall():
            decisions.append({
                'id': row['id'],
                'position': row['position'],
                'trick_number': row['trick_number'],
                'user_card': row['user_card'],
                'optimal_card': row['optimal_card'],
                'score': row['score'],
                'rating': row['rating'],
                'tricks_cost': row['tricks_cost'],
                'contract': row['contract'],
                'feedback': row['feedback'],
                'timestamp': row['timestamp']
            })

        return decisions

    except Exception as e:
        # Table might not exist yet
        print(f"Could not get recent play decisions: {e}")
        return []

    finally:
        conn.close()


def get_dashboard():
    """
    GET /api/analytics/dashboard?user_id=<id>
    Get comprehensive dashboard summary

    Returns:
        - Insight summary (patterns, trends, growth areas)
        - Recent wins
        - Pending celebrations
        - User stats (both bidding and gameplay)
        - Bidding feedback stats (Phase 1)
        - Recent bidding decisions (Phase 1)
        - Practice recommendations
    """
    user_id = request.args.get('user_id', type=int)

    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    try:
        user_manager = get_user_manager()
        analyzer = get_mistake_analyzer()
        celebration_manager = get_celebration_manager()

        # Get user stats (bidding)
        user_stats = user_manager.get_user_stats(user_id)

        # Get gameplay stats
        gameplay_stats = get_gameplay_stats_for_user(user_id)

        # Get bidding feedback stats (Phase 1)
        bidding_feedback_stats = get_bidding_feedback_stats_for_user(user_id)

        # Get recent bidding decisions (Phase 1)
        recent_decisions = get_recent_bidding_decisions_for_user(user_id, limit=10)

        # Get play feedback stats (DDS-based evaluation)
        play_feedback_stats = get_play_feedback_stats_for_user(user_id)

        # Get recent play decisions
        recent_play_decisions = get_recent_play_decisions_for_user(user_id, limit=10)

        # Get insight summary (bidding)
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
            'gameplay_stats': gameplay_stats,
            'bidding_feedback_stats': bidding_feedback_stats,  # Phase 1: NEW
            'recent_decisions': recent_decisions,  # Phase 1: NEW
            'play_feedback_stats': play_feedback_stats,  # DDS-based play evaluation
            'recent_play_decisions': recent_play_decisions,  # Recent play decisions
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


def get_gameplay_stats_for_user(user_id: int) -> Dict:
    """
    Calculate gameplay statistics from session_hands table

    Returns:
        - total_hands_played: Total hands as declarer or defender
        - hands_as_declarer: Count of hands where user was declarer
        - hands_as_defender: Count of hands where user was defender
        - contracts_made: Count of contracts made (as declarer)
        - contracts_failed: Count of contracts failed (as declarer)
        - declarer_success_rate: Percentage of contracts made
        - avg_tricks_as_declarer: Average tricks taken when declaring
        - recent_declarer_success_rate: Success rate in last 20 hands
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Get declarer statistics
        cursor.execute("""
            SELECT
                COUNT(*) as total_declarer_hands,
                SUM(CASE WHEN made = TRUE THEN 1 ELSE 0 END) as contracts_made,
                SUM(CASE WHEN made = FALSE THEN 1 ELSE 0 END) as contracts_failed,
                AVG(tricks_taken) as avg_tricks,
                AVG(CASE WHEN made = TRUE THEN 1.0 ELSE 0.0 END) as success_rate
            FROM session_hands sh
            JOIN game_sessions gs ON sh.session_id = gs.id
            WHERE gs.user_id = ?
              AND sh.user_was_declarer = TRUE
              AND sh.contract_level IS NOT NULL
        """, (user_id,))

        declarer_row = cursor.fetchone()

        # Get recent declarer performance (last 20 hands)
        cursor.execute("""
            SELECT AVG(CASE WHEN made = TRUE THEN 1.0 ELSE 0.0 END) as recent_success_rate
            FROM (
                SELECT made
                FROM session_hands sh
                JOIN game_sessions gs ON sh.session_id = gs.id
                WHERE gs.user_id = ?
                  AND sh.user_was_declarer = TRUE
                  AND sh.contract_level IS NOT NULL
                ORDER BY sh.played_at DESC
                LIMIT 20
            ) subq
        """, (user_id,))

        recent_row = cursor.fetchone()

        # Get defender statistics (user played but wasn't declarer or dummy)
        cursor.execute("""
            SELECT COUNT(*) as defender_hands
            FROM session_hands sh
            JOIN game_sessions gs ON sh.session_id = gs.id
            WHERE gs.user_id = ?
              AND sh.user_was_declarer = FALSE
              AND sh.user_was_dummy = FALSE
              AND sh.contract_level IS NOT NULL
        """, (user_id,))

        defender_row = cursor.fetchone()

        # Build stats object
        total_declarer = declarer_row['total_declarer_hands'] or 0
        contracts_made = declarer_row['contracts_made'] or 0
        contracts_failed = declarer_row['contracts_failed'] or 0
        avg_tricks = declarer_row['avg_tricks'] or 0.0
        success_rate = declarer_row['success_rate'] or 0.0
        recent_success = recent_row['recent_success_rate'] or 0.0
        defender_hands = defender_row['defender_hands'] or 0

        total_hands = total_declarer + defender_hands

        return {
            'total_hands_played': total_hands,
            'hands_as_declarer': total_declarer,
            'hands_as_defender': defender_hands,
            'contracts_made': contracts_made,
            'contracts_failed': contracts_failed,
            'declarer_success_rate': success_rate,
            'avg_tricks_as_declarer': round(avg_tricks, 1),
            'recent_declarer_success_rate': recent_success
        }

    finally:
        conn.close()


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

# ============================================================================
# FOUR-DIMENSION PROGRESS ENDPOINT
# ============================================================================

def get_four_dimension_progress():
    """
    GET /api/analytics/four-dimension-progress?user_id=<id>

    Get comprehensive four-dimension learning progress:
    1. Bid Learning Journey (structured curriculum progress)
    2. Bid Practice Quality (freeplay + conventions)
    3. Play Learning Journey (card play curriculum)
    4. Play Practice Quality (gameplay performance)

    Returns data optimized for dashboard visualization.
    """
    from engine.learning.skill_tree import get_skill_tree_manager
    from engine.learning.play_skill_tree import get_play_skill_tree_manager
    from engine.learning.learning_path_api import (
        get_user_completed_skills,
        get_user_mastered_conventions,
        get_user_completed_play_skills
    )
    from engine.ai.conventions.convention_registry import get_convention_registry

    user_id = request.args.get('user_id', type=int)

    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # =====================================================================
        # 1. BID LEARNING JOURNEY
        # =====================================================================
        bid_tree_manager = get_skill_tree_manager()
        completed_skills = get_user_completed_skills(user_id)
        mastered_conventions = get_user_mastered_conventions(user_id)

        user_progress = {
            'completed_skills': completed_skills,
            'mastered_conventions': mastered_conventions
        }

        bid_level_progress = bid_tree_manager.get_user_skill_tree_progress(user_progress)

        # Find current level and calculate totals
        bid_current_level = None
        bid_current_level_name = None
        bid_skills_in_level = 0
        bid_skills_completed_in_level = 0
        bid_total_levels = 9  # Levels 0-8
        bid_levels_completed = 0
        bid_total_skills = 0
        bid_total_skills_mastered = len(completed_skills) + len(mastered_conventions)

        for level_id, progress in bid_level_progress.items():
            bid_total_skills += progress['total']
            if progress['completed'] == progress['total']:
                bid_levels_completed += 1
            elif progress['unlocked'] and bid_current_level is None:
                bid_current_level = progress['level_number']
                bid_current_level_name = progress['name']
                bid_skills_in_level = progress['total']
                bid_skills_completed_in_level = progress['completed']

        # Get next skill to practice
        bid_next_skill = None
        if bid_current_level is not None:
            level_id = bid_tree_manager.get_level_id_by_number(bid_current_level)
            level_data = bid_tree_manager.get_level(level_id)
            if level_data:
                if 'skills' in level_data:
                    for skill in level_data['skills']:
                        if skill.id not in completed_skills:
                            bid_next_skill = {'id': skill.id, 'name': skill.name}
                            break
                elif 'conventions' in level_data:
                    for conv_id in level_data['conventions']:
                        if conv_id not in mastered_conventions:
                            registry = get_convention_registry()
                            conv = registry.get_convention(conv_id)
                            if conv:
                                bid_next_skill = {'id': conv_id, 'name': conv.name}
                            break

        bid_learning_journey = {
            'current_level': bid_current_level if bid_current_level is not None else 0,
            'current_level_name': bid_current_level_name or 'Level 0: Foundations',
            'skills_in_level': bid_skills_in_level,
            'skills_completed_in_level': bid_skills_completed_in_level,
            'total_levels': bid_total_levels,
            'levels_completed': bid_levels_completed,
            'total_skills_mastered': bid_total_skills_mastered,
            'next_skill': bid_next_skill,
            'progress_percentage': round(bid_total_skills_mastered / bid_total_skills * 100, 1) if bid_total_skills > 0 else 0,
            'level_progress': {
                level_id: {
                    'level': p['level_number'],
                    'name': p['name'],
                    'completed': p['completed'],
                    'total': p['total'],
                    'unlocked': p['unlocked'],
                    'is_convention_group': p['is_convention_group']
                }
                for level_id, p in bid_level_progress.items()
            }
        }

        # =====================================================================
        # 2. BID PRACTICE QUALITY (Including Conventions)
        # =====================================================================
        bidding_feedback_stats = get_bidding_feedback_stats_for_user(user_id)

        # Get convention mastery details
        registry = get_convention_registry()
        convention_mastery = []

        # Get all convention progress
        try:
            cursor.execute("""
                SELECT convention_id, status, accuracy, attempts, last_practiced
                FROM user_convention_progress
                WHERE user_id = ?
                ORDER BY last_practiced DESC
            """, (user_id,))

            for row in cursor.fetchall():
                conv = registry.get_convention(row['convention_id'])
                if conv:
                    convention_mastery.append({
                        'id': row['convention_id'],
                        'name': conv.name,
                        'level': conv.level,
                        'accuracy': round(row['accuracy'] * 100, 1) if row['accuracy'] else 0,
                        'attempts': row['attempts'] or 0,
                        'status': row['status'],
                        'last_practiced': row['last_practiced']
                    })
        except Exception:
            pass  # Table might not exist

        # Get error category breakdown
        error_heatmap = {}
        try:
            cursor.execute(f"""
                SELECT error_category, COUNT(*) as count
                FROM bidding_decisions
                WHERE user_id = ?
                  AND error_category IS NOT NULL
                  AND timestamp >= {date_subtract(30)}
                GROUP BY error_category
                ORDER BY count DESC
            """, (user_id,))

            total_errors = 0
            for row in cursor.fetchall():
                error_heatmap[row['error_category']] = row['count']
                total_errors += row['count']

            # Convert to rates
            if total_errors > 0:
                for cat in error_heatmap:
                    error_heatmap[cat] = round(error_heatmap[cat] / total_errors, 3)
        except Exception:
            pass

        # Find weakest convention (lowest accuracy with attempts)
        weakest_convention = None
        if convention_mastery:
            practiced_convs = [c for c in convention_mastery if c['attempts'] >= 3]
            if practiced_convs:
                weakest_convention = min(practiced_convs, key=lambda x: x['accuracy'])

        bid_practice_quality = {
            'overall_accuracy': round(bidding_feedback_stats.get('avg_score', 0) / 10 * 100, 1),
            'avg_score': bidding_feedback_stats.get('avg_score', 0),
            'total_decisions': bidding_feedback_stats.get('total_decisions', 0),
            'optimal_rate': round(bidding_feedback_stats.get('optimal_rate', 0) * 100, 1),
            'error_rate': round(bidding_feedback_stats.get('error_rate', 0) * 100, 1),
            'recent_trend': bidding_feedback_stats.get('recent_trend', 'stable'),
            'convention_mastery': convention_mastery,
            'conventions_mastered': len([c for c in convention_mastery if c['status'] == 'mastered']),
            'conventions_in_progress': len([c for c in convention_mastery if c['status'] == 'in_progress']),
            'error_heatmap': error_heatmap,
            'weakest_convention': weakest_convention
        }

        # =====================================================================
        # 3. PLAY LEARNING JOURNEY
        # =====================================================================
        play_tree_manager = get_play_skill_tree_manager()
        completed_play_skills = get_user_completed_play_skills(user_id)

        play_user_progress = {'completed_play_skills': completed_play_skills}
        play_level_progress = play_tree_manager.get_user_skill_tree_progress(play_user_progress)

        # Find current play level and calculate totals
        play_current_level = None
        play_current_level_name = None
        play_skills_in_level = 0
        play_skills_completed_in_level = 0
        play_total_levels = 9  # Levels 0-8
        play_levels_completed = 0
        play_total_skills = 0
        play_total_skills_mastered = len(completed_play_skills)

        for level_id, progress in play_level_progress.items():
            play_total_skills += progress['total']
            if progress['completed'] == progress['total']:
                play_levels_completed += 1
            elif progress['unlocked'] and play_current_level is None:
                play_current_level = progress['level_number']
                play_current_level_name = progress['name']
                play_skills_in_level = progress['total']
                play_skills_completed_in_level = progress['completed']

        # Get next play skill to practice
        play_next_skill = None
        if play_current_level is not None:
            level_id = play_tree_manager.get_level_id_by_number(play_current_level)
            level_data = play_tree_manager.get_level(level_id)
            if level_data and 'skills' in level_data:
                for skill in level_data['skills']:
                    if skill.id not in completed_play_skills:
                        play_next_skill = {'id': skill.id, 'name': skill.name}
                        break

        play_learning_journey = {
            'current_level': play_current_level if play_current_level is not None else 0,
            'current_level_name': play_current_level_name or 'Level 0: Play Foundations',
            'skills_in_level': play_skills_in_level,
            'skills_completed_in_level': play_skills_completed_in_level,
            'total_levels': play_total_levels,
            'levels_completed': play_levels_completed,
            'total_skills_mastered': play_total_skills_mastered,
            'next_skill': play_next_skill,
            'progress_percentage': round(play_total_skills_mastered / play_total_skills * 100, 1) if play_total_skills > 0 else 0,
            'level_progress': {
                level_id: {
                    'level': p['level_number'],
                    'name': p['name'],
                    'completed': p['completed'],
                    'total': p['total'],
                    'unlocked': p['unlocked']
                }
                for level_id, p in play_level_progress.items()
            }
        }

        # =====================================================================
        # 4. PLAY PRACTICE QUALITY (Gameplay Performance)
        # =====================================================================
        gameplay_stats = get_gameplay_stats_for_user(user_id)
        play_feedback_stats = get_play_feedback_stats_for_user(user_id)

        # Get contract type breakdown
        contracts_by_type = {
            'nt_partscore': {'count': 0, 'made': 0},
            'nt_game': {'count': 0, 'made': 0},
            'suit_partscore': {'count': 0, 'made': 0},
            'suit_game': {'count': 0, 'made': 0},
            'slam': {'count': 0, 'made': 0}
        }

        try:
            cursor.execute("""
                SELECT
                    contract_level,
                    contract_suit,
                    made,
                    COUNT(*) as count
                FROM session_hands sh
                JOIN game_sessions gs ON sh.session_id = gs.id
                WHERE gs.user_id = ?
                  AND sh.user_was_declarer = TRUE
                  AND sh.contract_level IS NOT NULL
                GROUP BY contract_level, contract_suit, made
            """, (user_id,))

            for row in cursor.fetchall():
                level = row['contract_level'] or 0
                suit = row['contract_suit'] or 'NT'
                made = row['made']
                count = row['count']

                # Categorize
                if level >= 6:
                    key = 'slam'
                elif suit == 'NT':
                    key = 'nt_game' if level >= 3 else 'nt_partscore'
                else:
                    key = 'suit_game' if level >= 4 else 'suit_partscore'

                contracts_by_type[key]['count'] += count
                if made:
                    contracts_by_type[key]['made'] += count
        except Exception:
            pass

        # Calculate success rates per type
        for key in contracts_by_type:
            ct = contracts_by_type[key]
            ct['success_rate'] = round(ct['made'] / ct['count'] * 100, 1) if ct['count'] > 0 else 0

        play_practice_quality = {
            'declarer_success_rate': round(gameplay_stats.get('declarer_success_rate', 0) * 100, 1),
            'recent_success_rate': round(gameplay_stats.get('recent_declarer_success_rate', 0) * 100, 1),
            'total_hands_played': gameplay_stats.get('total_hands_played', 0),
            'hands_as_declarer': gameplay_stats.get('hands_as_declarer', 0),
            'contracts_made': gameplay_stats.get('contracts_made', 0),
            'contracts_failed': gameplay_stats.get('contracts_failed', 0),
            'avg_tricks': gameplay_stats.get('avg_tricks_as_declarer', 0),
            'contracts_by_type': contracts_by_type,
            'play_decision_stats': {
                'avg_score': play_feedback_stats.get('avg_score', 0),
                'optimal_rate': round(play_feedback_stats.get('optimal_rate', 0) * 100, 1),
                'blunder_rate': round(play_feedback_stats.get('blunder_rate', 0) * 100, 1),
                'recent_trend': play_feedback_stats.get('recent_trend', 'stable')
            },
            'recent_trend': 'improving' if gameplay_stats.get('recent_declarer_success_rate', 0) > gameplay_stats.get('declarer_success_rate', 0) + 0.05 else (
                'declining' if gameplay_stats.get('recent_declarer_success_rate', 0) < gameplay_stats.get('declarer_success_rate', 0) - 0.05 else 'stable'
            )
        }

        conn.close()

        return jsonify({
            'user_id': user_id,
            'bid_learning_journey': bid_learning_journey,
            'bid_practice_quality': bid_practice_quality,
            'play_learning_journey': play_learning_journey,
            'play_practice_quality': play_practice_quality
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


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
    app.route('/api/analytics/four-dimension-progress', methods=['GET'])(get_four_dimension_progress)

    # User management
    app.route('/api/user/create', methods=['POST'])(create_user)
    app.route('/api/user/info', methods=['GET'])(get_user_info)

    print("✓ Analytics API endpoints registered")
    print("✓ Four-dimension progress endpoint registered")

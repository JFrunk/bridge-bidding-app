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
                'good_rate': 0,
                'suboptimal_rate': 0,
                'error_rate': 0,
                'critical_errors': 0,
                'recent_trend': 'stable'
            }

        total = overall_row['total_decisions']
        avg_score = overall_row['avg_score'] or 0
        optimal_count = overall_row['optimal_count'] or 0
        acceptable_count = overall_row['acceptable_count'] or 0
        suboptimal_count = overall_row['suboptimal_count'] or 0
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

        # Calculate rates
        optimal_rate = optimal_count / total if total > 0 else 0
        acceptable_rate = acceptable_count / total if total > 0 else 0
        suboptimal_rate = suboptimal_count / total if total > 0 else 0
        error_rate = error_count / total if total > 0 else 0
        good_rate = optimal_rate + acceptable_rate  # Combined for 3-tier display

        return {
            'avg_score': round(avg_score, 1),
            'total_decisions': total,
            'optimal_rate': round(optimal_rate, 3),
            'acceptable_rate': round(acceptable_rate, 3),
            'good_rate': round(good_rate, 3),  # Combined: optimal + acceptable
            'suboptimal_rate': round(suboptimal_rate, 3),  # "Needs Work"
            'error_rate': round(error_rate, 3),
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


def get_play_category_stats_for_user(user_id: int) -> Dict:
    """
    Calculate play statistics broken down by play category.

    Returns breakdown of accuracy by category:
    - opening_lead, following_suit, discarding, trumping, etc.
    - Each category includes: attempts, optimal_rate, avg_tricks_cost
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Get stats by play category (last 30 days)
        cursor.execute(f"""
            SELECT
                play_category,
                COUNT(*) as attempts,
                AVG(score) as avg_score,
                SUM(CASE WHEN rating = 'optimal' THEN 1 ELSE 0 END) as optimal_count,
                SUM(CASE WHEN rating = 'good' THEN 1 ELSE 0 END) as good_count,
                SUM(CASE WHEN rating = 'blunder' THEN 1 ELSE 0 END) as blunder_count,
                AVG(tricks_cost) as avg_tricks_cost,
                SUM(tricks_cost) as total_tricks_cost
            FROM play_decisions
            WHERE user_id = ?
              AND timestamp >= {date_subtract(30)}
              AND play_category IS NOT NULL
            GROUP BY play_category
            ORDER BY attempts DESC
        """, (user_id,))

        categories = {}
        total_tricks_lost = 0

        for row in cursor.fetchall():
            cat = row['play_category']
            attempts = row['attempts'] or 0
            optimal = row['optimal_count'] or 0
            good = row['good_count'] or 0
            blunders = row['blunder_count'] or 0
            avg_score = row['avg_score'] or 0
            avg_cost = row['avg_tricks_cost'] or 0
            total_cost = row['total_tricks_cost'] or 0

            total_tricks_lost += total_cost

            # Determine skill level based on accuracy
            accuracy = ((optimal + good) / attempts * 100) if attempts > 0 else 0
            if accuracy >= 85:
                skill_level = 'strong'
            elif accuracy >= 70:
                skill_level = 'good'
            elif accuracy >= 55:
                skill_level = 'developing'
            else:
                skill_level = 'focus_area'

            categories[cat] = {
                'attempts': attempts,
                'avg_score': round(avg_score, 1),
                'optimal_rate': round(optimal / attempts * 100, 1) if attempts > 0 else 0,
                'good_rate': round(good / attempts * 100, 1) if attempts > 0 else 0,
                'blunder_rate': round(blunders / attempts * 100, 1) if attempts > 0 else 0,
                'accuracy': round(accuracy, 1),
                'avg_tricks_cost': round(avg_cost, 2),
                'total_tricks_cost': total_cost,
                'skill_level': skill_level
            }

        # Category display names
        category_names = {
            'opening_lead': 'Opening Leads',
            'following_suit': 'Following Suit',
            'discarding': 'Discarding',
            'trumping': 'Trumping',
            'overruffing': 'Overruffing',
            'sluffing': 'Sluff vs Ruff',
            'finessing': 'Finessing',
            'cashing': 'Cashing Winners',
            'hold_up': 'Hold-up Plays',
            'ducking': 'Ducking'
        }

        # Add display names
        for cat in categories:
            categories[cat]['display_name'] = category_names.get(cat, cat.replace('_', ' ').title())

        return {
            'categories': categories,
            'total_tricks_lost': total_tricks_lost,
            'category_count': len(categories)
        }

    except Exception as e:
        print(f"Could not get play category stats: {e}")
        return {
            'categories': {},
            'total_tricks_lost': 0,
            'category_count': 0
        }

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
        - category_breakdown: Stats by play category
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
                'combined_good_rate': 0,
                'suboptimal_rate': 0,
                'blunder_rate': 0,
                'recent_trend': 'stable'
            }

        total = overall_row['total_decisions']
        avg_score = overall_row['avg_score'] or 0
        optimal_count = overall_row['optimal_count'] or 0
        good_count = overall_row['good_count'] or 0
        suboptimal_count = overall_row['suboptimal_count'] or 0
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

        # Get category breakdown
        category_stats = get_play_category_stats_for_user(user_id)

        # Calculate rates
        optimal_rate = optimal_count / total if total > 0 else 0
        good_rate_raw = good_count / total if total > 0 else 0
        suboptimal_rate = suboptimal_count / total if total > 0 else 0
        blunder_rate = blunder_count / total if total > 0 else 0

        # Combined good rate (optimal + good) for 3-tier display
        combined_good_rate = optimal_rate + good_rate_raw

        return {
            'avg_score': round(avg_score, 1),
            'total_decisions': total,
            'optimal_rate': round(optimal_rate, 3),
            'good_rate': round(good_rate_raw, 3),  # Just "good" rating
            'combined_good_rate': round(combined_good_rate, 3),  # optimal + good
            'suboptimal_rate': round(suboptimal_rate, 3),  # "Needs Work"
            'blunder_rate': round(blunder_rate, 3),  # Errors
            'recent_trend': trend,
            'category_breakdown': category_stats['categories'],
            'total_tricks_lost': category_stats['total_tricks_lost']
        }

    except Exception as e:
        # Table might not exist yet
        print(f"Could not get play feedback stats: {e}")
        return {
            'avg_score': 0,
            'total_decisions': 0,
            'optimal_rate': 0,
            'good_rate': 0,
            'combined_good_rate': 0,
            'suboptimal_rate': 0,
            'blunder_rate': 0,
            'recent_trend': 'stable',
            'category_breakdown': {},
            'total_tricks_lost': 0
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

        # Get in-progress skills (started but not yet mastered) - key for showing immediate progress
        in_progress_skills = []
        current_skill_progress = None
        try:
            cursor.execute("""
                SELECT skill_id, attempts, correct, accuracy, status, last_practiced
                FROM user_skill_progress
                WHERE user_id = ? AND status = 'in_progress'
                ORDER BY last_practiced DESC
            """, (user_id,))
            for row in cursor.fetchall():
                skill_data = {
                    'skill_id': row['skill_id'],
                    'attempts': row['attempts'],
                    'correct': row['correct'],
                    'accuracy': round(row['accuracy'] * 100, 1) if row['accuracy'] else 0,
                    'status': row['status']
                }
                in_progress_skills.append(skill_data)
                # Most recent in-progress skill is the current one
                if current_skill_progress is None:
                    current_skill_progress = skill_data
        except Exception:
            pass  # Table might not exist

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

        # Get next skill to practice (considering in-progress skills)
        bid_next_skill = None
        if bid_current_level is not None:
            level_id = bid_tree_manager.get_level_id_by_number(bid_current_level)
            level_data = bid_tree_manager.get_level(level_id)
            if level_data:
                if 'skills' in level_data:
                    for skill in level_data['skills']:
                        if skill.id not in completed_skills:
                            # Check if this skill is in-progress
                            in_progress_info = next(
                                (s for s in in_progress_skills if s['skill_id'] == skill.id),
                                None
                            )
                            bid_next_skill = {
                                'id': skill.id,
                                'name': skill.name,
                                'in_progress': in_progress_info is not None,
                                'attempts': in_progress_info['attempts'] if in_progress_info else 0,
                                'accuracy': in_progress_info['accuracy'] if in_progress_info else 0
                            }
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
            'skills_in_progress': len(in_progress_skills),
            'current_skill_progress': current_skill_progress,
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

        # Calculate combined rates for simpler 3-tier display
        optimal_rate = bidding_feedback_stats.get('optimal_rate', 0)
        acceptable_rate = bidding_feedback_stats.get('acceptable_rate', 0)
        error_rate = bidding_feedback_stats.get('error_rate', 0)
        # Suboptimal is whatever remains (scores 4-6)
        suboptimal_rate = max(0, 1.0 - optimal_rate - acceptable_rate - error_rate)
        # Good = optimal + acceptable (scores 7-10)
        good_rate = optimal_rate + acceptable_rate

        bid_practice_quality = {
            'overall_accuracy': round(bidding_feedback_stats.get('avg_score', 0) / 10 * 100, 1),
            'avg_score': bidding_feedback_stats.get('avg_score', 0),
            'total_decisions': bidding_feedback_stats.get('total_decisions', 0),
            'optimal_rate': round(optimal_rate * 100, 1),
            'acceptable_rate': round(acceptable_rate * 100, 1),
            'good_rate': round(good_rate * 100, 1),  # Combined: optimal + acceptable
            'suboptimal_rate': round(suboptimal_rate * 100, 1),  # Scores 4-6
            'error_rate': round(error_rate * 100, 1),
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

        # Get in-progress play skills (started but not yet mastered)
        play_in_progress_skills = []
        play_current_skill_progress = None
        try:
            cursor.execute("""
                SELECT skill_id, attempts, correct, accuracy, status, last_practiced
                FROM user_play_progress
                WHERE user_id = ? AND status = 'in_progress'
                ORDER BY last_practiced DESC
            """, (user_id,))
            for row in cursor.fetchall():
                skill_data = {
                    'skill_id': row['skill_id'],
                    'attempts': row['attempts'],
                    'correct': row['correct'],
                    'accuracy': round(row['accuracy'] * 100, 1) if row['accuracy'] else 0,
                    'status': row['status']
                }
                play_in_progress_skills.append(skill_data)
                if play_current_skill_progress is None:
                    play_current_skill_progress = skill_data
        except Exception:
            pass  # Table might not exist

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

        # Get next play skill to practice (considering in-progress skills)
        play_next_skill = None
        if play_current_level is not None:
            level_id = play_tree_manager.get_level_id_by_number(play_current_level)
            level_data = play_tree_manager.get_level(level_id)
            if level_data and 'skills' in level_data:
                for skill in level_data['skills']:
                    if skill.id not in completed_play_skills:
                        # Check if this skill is in-progress
                        in_progress_info = next(
                            (s for s in play_in_progress_skills if s['skill_id'] == skill.id),
                            None
                        )
                        play_next_skill = {
                            'id': skill.id,
                            'name': skill.name,
                            'in_progress': in_progress_info is not None,
                            'attempts': in_progress_info['attempts'] if in_progress_info else 0,
                            'accuracy': in_progress_info['accuracy'] if in_progress_info else 0
                        }
                        break

        play_learning_journey = {
            'current_level': play_current_level if play_current_level is not None else 0,
            'current_level_name': play_current_level_name or 'Level 0: Play Foundations',
            'skills_in_level': play_skills_in_level,
            'skills_completed_in_level': play_skills_completed_in_level,
            'total_levels': play_total_levels,
            'levels_completed': play_levels_completed,
            'total_skills_mastered': play_total_skills_mastered,
            'skills_in_progress': len(play_in_progress_skills),
            'current_skill_progress': play_current_skill_progress,
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
                'good_rate': round(play_feedback_stats.get('combined_good_rate', 0) * 100, 1),  # Combined: optimal + good
                'suboptimal_rate': round(play_feedback_stats.get('suboptimal_rate', 0) * 100, 1),  # Needs Work
                'blunder_rate': round(play_feedback_stats.get('blunder_rate', 0) * 100, 1),  # Errors
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


# ============================================================================
# HAND HISTORY & DDS ANALYSIS
# ============================================================================

def get_hand_play_quality_summary(session_id: int, hand_number: int, user_id: int) -> Dict:
    """
    Get a summary of play quality for a specific hand.

    Returns:
        - total_plays: Number of plays by the user in this hand
        - optimal_count, good_count, suboptimal_count, blunder_count
        - avg_score: Average play score (0-10)
        - total_tricks_lost: Sum of tricks lost from suboptimal plays
        - notable_mistakes: List of the worst plays (blunders/suboptimal with details)
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Get all play decisions for this user in this specific hand
        # Note: play_decisions uses session_id as text, not integer
        # Filter by hand_number to get plays for only this hand (not entire session)
        cursor.execute("""
            SELECT
                id,
                trick_number,
                position,
                user_card,
                optimal_card,
                score,
                rating,
                tricks_cost,
                contract,
                feedback
            FROM play_decisions
            WHERE user_id = ?
              AND session_id = ?
              AND (hand_number = ? OR hand_number IS NULL)
            ORDER BY trick_number, id
        """, (user_id, str(session_id), hand_number))

        decisions = []
        for row in cursor.fetchall():
            decisions.append({
                'id': row['id'],
                'trick_number': row['trick_number'],
                'position': row['position'],
                'user_card': row['user_card'],
                'optimal_card': row['optimal_card'],
                'score': row['score'],
                'rating': row['rating'],
                'tricks_cost': row['tricks_cost'],
                'contract': row['contract'],
                'feedback': row['feedback']
            })

        if not decisions:
            return {
                'has_data': False,
                'total_plays': 0,
                'message': 'No play analysis recorded for this hand'
            }

        # Calculate summary stats
        total = len(decisions)
        optimal = sum(1 for d in decisions if d['rating'] == 'optimal')
        good = sum(1 for d in decisions if d['rating'] == 'good')
        suboptimal = sum(1 for d in decisions if d['rating'] == 'suboptimal')
        blunders = sum(1 for d in decisions if d['rating'] == 'blunder')
        # Sum of individual tricks_cost values - note this can exceed 13 because
        # each play's cost is calculated independently (potential tricks lost from that position)
        raw_tricks_lost = sum(d['tricks_cost'] or 0 for d in decisions)
        # Cap at 13 for display since a hand only has 13 tricks
        # This is more meaningful as "tricks below double-dummy par"
        total_tricks_lost = min(raw_tricks_lost, 13)
        avg_score = sum(d['score'] for d in decisions) / total if total > 0 else 0
        # Count of plays that cost tricks (more meaningful than raw sum)
        mistakes_count = sum(1 for d in decisions if (d['tricks_cost'] or 0) > 0)

        # Get notable mistakes (blunders and suboptimal plays with tricks_cost > 0)
        notable_mistakes = [
            d for d in decisions
            if d['rating'] in ('blunder', 'suboptimal') and (d['tricks_cost'] or 0) > 0
        ]
        # Sort by tricks cost (worst first)
        notable_mistakes.sort(key=lambda x: -(x['tricks_cost'] or 0))
        notable_mistakes = notable_mistakes[:5]  # Limit to top 5

        return {
            'has_data': True,
            'total_plays': total,
            'optimal_count': optimal,
            'good_count': good,
            'suboptimal_count': suboptimal,
            'blunder_count': blunders,
            'avg_score': round(avg_score, 1),
            'total_tricks_lost': total_tricks_lost,
            'mistakes_count': mistakes_count,
            'optimal_rate': round(optimal / total * 100, 1) if total > 0 else 0,
            'accuracy_rate': round((optimal + good) / total * 100, 1) if total > 0 else 0,
            'notable_mistakes': notable_mistakes,
            'all_decisions': decisions
        }

    except Exception as e:
        print(f"Error getting play quality summary: {e}")
        return {
            'has_data': False,
            'total_plays': 0,
            'message': f'Error loading play analysis: {str(e)}'
        }

    finally:
        conn.close()


def get_hand_bidding_quality_summary(session_id: int, hand_number: int, user_id: int) -> Dict:
    """
    Get a summary of bidding quality for a specific hand.

    Returns:
        - total_bids: Number of bids by the user in this hand
        - optimal_count, acceptable_count, suboptimal_count, error_count
        - accuracy_rate: Percentage of optimal+acceptable bids
        - avg_score: Average bidding score (0-10)
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Get all bidding decisions for this user in this specific hand
        cursor.execute("""
            SELECT
                id,
                bid_number,
                position,
                user_bid,
                optimal_bid,
                score,
                correctness,
                impact,
                helpful_hint
            FROM bidding_decisions
            WHERE user_id = ?
              AND session_id = ?
              AND (hand_number = ? OR hand_number IS NULL)
            ORDER BY bid_number
        """, (user_id, str(session_id), hand_number))

        decisions = []
        for row in cursor.fetchall():
            decisions.append({
                'id': row['id'],
                'bid_number': row['bid_number'],
                'position': row['position'],
                'user_bid': row['user_bid'],
                'optimal_bid': row['optimal_bid'],
                'score': row['score'],
                'correctness': row['correctness'],
                'impact': row['impact'],
                'helpful_hint': row['helpful_hint']
            })

        if not decisions:
            return {
                'has_data': False,
                'total_bids': 0,
                'message': 'No bidding decisions recorded for this hand'
            }

        # Calculate aggregate stats
        total = len(decisions)
        optimal = sum(1 for d in decisions if d['correctness'] == 'optimal')
        acceptable = sum(1 for d in decisions if d['correctness'] == 'acceptable')
        suboptimal = sum(1 for d in decisions if d['correctness'] == 'suboptimal')
        errors = sum(1 for d in decisions if d['correctness'] == 'error')

        avg_score = sum(d['score'] for d in decisions) / total if total > 0 else 0

        return {
            'has_data': True,
            'total_bids': total,
            'optimal_count': optimal,
            'acceptable_count': acceptable,
            'suboptimal_count': suboptimal,
            'error_count': errors,
            'avg_score': round(avg_score, 1),
            'optimal_rate': round(optimal / total * 100, 1) if total > 0 else 0,
            'accuracy_rate': round((optimal + acceptable) / total * 100, 1) if total > 0 else 0,
            'all_decisions': decisions
        }

    except Exception as e:
        print(f"Error getting bidding quality summary: {e}")
        return {
            'has_data': False,
            'total_bids': 0,
            'message': f'Error loading bidding analysis: {str(e)}'
        }

    finally:
        conn.close()


def get_hand_history():
    """
    GET /api/hand-history?user_id=<id>&limit=<n>
    Get recent hands with replay data for the user.

    Query params:
        user_id: User ID (required)
        limit: Max hands to return (default 15, max 50)

    Returns list of hands with contract, result, and available replay data.
    """
    user_id = request.args.get('user_id', type=int)
    limit = request.args.get('limit', default=15, type=int)
    limit = min(limit, 50)  # Cap at 50

    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                sh.id,
                sh.session_id,
                sh.hand_number,
                sh.dealer,
                sh.vulnerability,
                sh.contract_level,
                sh.contract_strain,
                sh.contract_declarer,
                sh.contract_doubled,
                sh.tricks_taken,
                sh.tricks_needed,
                sh.made,
                sh.hand_score,
                sh.user_was_declarer,
                sh.user_was_dummy,
                sh.played_at,
                sh.deal_data IS NOT NULL as has_deal_data,
                sh.play_history IS NOT NULL as has_play_history
            FROM session_hands sh
            JOIN game_sessions gs ON sh.session_id = gs.id
            WHERE gs.user_id = ?
              AND sh.contract_level IS NOT NULL
            ORDER BY sh.played_at DESC
            LIMIT ?
        """, (user_id, limit))

        hands = []
        for row in cursor.fetchall():
            # Format contract display
            contract_display = None
            if row['contract_level']:
                contract_display = f"{row['contract_level']}{row['contract_strain']}"
                if row['contract_doubled'] == 1:
                    contract_display += "X"
                elif row['contract_doubled'] == 2:
                    contract_display += "XX"
                contract_display += f" by {row['contract_declarer']}"

            # Calculate result string
            result_str = None
            if row['tricks_taken'] is not None and row['tricks_needed'] is not None:
                diff = row['tricks_taken'] - row['tricks_needed']
                if diff == 0:
                    result_str = "="
                elif diff > 0:
                    result_str = f"+{diff}"
                else:
                    result_str = str(diff)

            hands.append({
                'id': row['id'],
                'session_id': row['session_id'],
                'hand_number': row['hand_number'],
                'dealer': row['dealer'],
                'vulnerability': row['vulnerability'],
                'contract': contract_display,
                'contract_level': row['contract_level'],
                'contract_strain': row['contract_strain'],
                'contract_declarer': row['contract_declarer'],
                'tricks_taken': row['tricks_taken'],
                'tricks_needed': row['tricks_needed'],
                'result': result_str,
                'made': row['made'],
                'score': row['hand_score'],
                'user_was_declarer': row['user_was_declarer'],
                'user_was_dummy': row['user_was_dummy'],
                'played_at': row['played_at'],
                'can_replay': bool(row['has_deal_data'] and row['has_play_history'])
            })

        conn.close()

        return jsonify({
            'user_id': user_id,
            'hands': hands,
            'count': len(hands)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


def generate_hand_strategy_summary(
    declarer_hand: Hand,
    dummy_hand: Hand,
    contract_level: int,
    contract_strain: str,
    is_nt: bool
) -> Dict:
    """
    Generate strategic guidance for the hand.

    For NT contracts:
    - Count sure tricks and identify how many more needed
    - Identify suits with establishment potential

    For Suit contracts:
    - Count losers in declarer's hand
    - Identify ruffing opportunities in dummy

    Returns:
        Dict with strategy summary including natural language guidance
    """
    from engine.learning.play_skill_hand_generators import count_sure_winners, count_losers_in_suit

    tricks_needed = 6 + contract_level  # e.g., 3NT needs 9 tricks
    result = {
        'contract': f"{contract_level}{contract_strain}",
        'tricks_needed': tricks_needed,
        'is_nt': is_nt
    }

    if is_nt:
        # NT Contract Analysis - Count sure tricks
        sure_tricks = count_sure_winners(declarer_hand, dummy_hand)
        tricks_to_develop = max(0, tricks_needed - sure_tricks)

        result['sure_tricks'] = sure_tricks
        result['tricks_to_develop'] = tricks_to_develop

        # Identify suits with establishment potential
        establishment_candidates = []
        suits = ['♠', '♥', '♦', '♣']

        for suit in suits:
            decl_suit = [c for c in declarer_hand.cards if c.suit == suit]
            dummy_suit = [c for c in dummy_hand.cards if c.suit == suit]
            combined_length = len(decl_suit) + len(dummy_suit)

            if combined_length == 0:
                continue

            # Get combined ranks
            combined_ranks = [c.rank for c in decl_suit + dummy_suit]
            has_ace = 'A' in combined_ranks
            has_king = 'K' in combined_ranks
            has_queen = 'Q' in combined_ranks

            # Calculate potential extra tricks from this suit
            longer_hand_length = max(len(decl_suit), len(dummy_suit))

            # Count top honors
            top_honors = 0
            if has_ace:
                top_honors = 1
                if has_king:
                    top_honors = 2
                    if has_queen:
                        top_honors = 3

            # Potential = length in longer hand minus guaranteed tricks
            potential_extra = longer_hand_length - top_honors

            # Suits with 5+ cards and some high cards are establishment candidates
            if combined_length >= 5 and potential_extra >= 2 and (has_ace or has_king):
                establishment_candidates.append({
                    'suit': suit,
                    'length': combined_length,
                    'potential_tricks': longer_hand_length,
                    'high_cards': top_honors
                })

        result['establishment_candidates'] = establishment_candidates

        # Generate natural language summary
        if sure_tricks >= tricks_needed:
            result['summary'] = f"You have {sure_tricks} sure tricks - enough to make {contract_level}NT. Cash your winners carefully."
        else:
            if establishment_candidates:
                suit_list = ', '.join([c['suit'] for c in establishment_candidates[:2]])
                result['summary'] = f"You have {sure_tricks} sure tricks and need {tricks_needed}. Develop {tricks_to_develop} more from {suit_list}."
            else:
                result['summary'] = f"You have {sure_tricks} sure tricks and need {tricks_needed}. Look for finesse opportunities."

    else:
        # Suit Contract Analysis - Count losers
        trump_suit = contract_strain
        total_losers = 0
        loser_breakdown = {}

        for suit in ['♠', '♥', '♦', '♣']:
            losers = count_losers_in_suit(declarer_hand, suit)
            total_losers += losers
            loser_breakdown[suit] = losers

        result['total_losers'] = int(total_losers)
        result['loser_breakdown'] = loser_breakdown

        # Losers we can afford = 13 - tricks_needed
        losers_allowed = 13 - tricks_needed
        losers_to_eliminate = int(max(0, total_losers - losers_allowed))

        result['losers_allowed'] = losers_allowed
        result['losers_to_eliminate'] = losers_to_eliminate

        # Check dummy for ruffing opportunities
        ruffing_opportunities = []
        dummy_trumps = len([c for c in dummy_hand.cards if c.suit == trump_suit])

        if dummy_trumps > 0:
            for suit in ['♠', '♥', '♦', '♣']:
                if suit == trump_suit:
                    continue
                dummy_length = len([c for c in dummy_hand.cards if c.suit == suit])
                decl_length = len([c for c in declarer_hand.cards if c.suit == suit])

                # Short in dummy, long in declarer = ruffing opportunity
                if dummy_length <= 2 and decl_length >= 4:
                    ruffs_available = min(dummy_trumps, decl_length - dummy_length)
                    if ruffs_available > 0:
                        ruffing_opportunities.append({
                            'suit': suit,
                            'dummy_length': dummy_length,
                            'ruffs_possible': ruffs_available
                        })

        result['ruffing_opportunities'] = ruffing_opportunities

        # Generate natural language summary
        if losers_to_eliminate == 0:
            result['summary'] = f"You have {int(total_losers)} losers and can afford {losers_allowed}. Make your contract with careful play."
        else:
            methods = []
            if ruffing_opportunities:
                suits = ', '.join([r['suit'] for r in ruffing_opportunities[:2]])
                methods.append(f"ruff {suits} in dummy")
            if losers_to_eliminate > len(ruffing_opportunities):
                methods.append("finesse or discard losers")

            method_str = ' or '.join(methods) if methods else "find discards"
            result['summary'] = f"You have {int(total_losers)} losers but can only afford {losers_allowed}. Eliminate {losers_to_eliminate} by: {method_str}."

    return result


def get_hand_detail():
    """
    GET /api/hand-history/<hand_id>
    Get full detail for a specific hand including all cards and plays.

    Returns:
        - Full deal (all 4 hands)
        - Auction history
        - Play history (all 52 cards played in order)
        - Contract and result details
    """
    hand_id = request.args.get('hand_id', type=int)

    if not hand_id:
        return jsonify({'error': 'hand_id required'}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                sh.*,
                gs.user_id,
                gs.player_position
            FROM session_hands sh
            JOIN game_sessions gs ON sh.session_id = gs.id
            WHERE sh.id = ?
        """, (hand_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({'error': 'Hand not found'}), 404

        # Parse JSON fields
        deal_data = json.loads(row['deal_data']) if row['deal_data'] else None
        auction_history = json.loads(row['auction_history']) if row['auction_history'] else []
        play_history = json.loads(row['play_history']) if row['play_history'] else []
        score_breakdown = json.loads(row['score_breakdown']) if row['score_breakdown'] else {}

        # Format contract display
        contract_display = None
        if row['contract_level']:
            contract_display = f"{row['contract_level']}{row['contract_strain']}"
            if row['contract_doubled'] == 1:
                contract_display += "X"
            elif row['contract_doubled'] == 2:
                contract_display += "XX"
            contract_display += f" by {row['contract_declarer']}"

        # Get play quality summary for this hand
        play_quality_summary = get_hand_play_quality_summary(
            row['session_id'],
            row['hand_number'],
            row['user_id']
        )

        # Get bidding quality summary for this hand
        bidding_quality_summary = get_hand_bidding_quality_summary(
            row['session_id'],
            row['hand_number'],
            row['user_id']
        )

        # Get DD table and par analysis if DDS is available
        dd_analysis = None
        par_comparison = None
        try:
            from engine.play.dds_analysis import is_dds_available, get_dds_service
            from engine.hand import Hand, Card as BridgeCard

            if is_dds_available() and deal_data:
                dds_service = get_dds_service()

                # Convert deal_data to Hand objects
                hands = {}
                for pos in ['N', 'E', 'S', 'W']:
                    if pos in deal_data and 'hand' in deal_data[pos]:
                        cards = []
                        for card in deal_data[pos]['hand']:
                            rank = card.get('rank') or card.get('r')
                            suit = card.get('suit') or card.get('s')
                            # Normalize suit to Unicode symbols (Hand class expects ♠♥♦♣)
                            # Handle both DDS format (S,H,D,C) and Unicode format (♠,♥,♦,♣)
                            suit_to_unicode = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}
                            suit = suit_to_unicode.get(suit, suit)  # Convert if DDS format, keep if already Unicode
                            cards.append(BridgeCard(rank=rank, suit=suit))
                        hands[pos] = Hand(cards=cards)

                if len(hands) == 4:
                    # Get full DD analysis
                    analysis = dds_service.analyze_deal(
                        hands,
                        dealer=row['dealer'] or 'N',
                        vulnerability=row['vulnerability'] or 'None'
                    )

                    if analysis.is_valid:
                        dd_analysis = analysis.to_dict()

                        # Compare with par if we have contract info
                        if row['contract_level'] and row['contract_strain'] and row['tricks_taken'] is not None:
                            par_comparison = dds_service.compare_with_par(
                                hands,
                                contract_level=row['contract_level'],
                                contract_strain=row['contract_strain'],
                                declarer=row['contract_declarer'] or 'S',
                                tricks_made=row['tricks_taken'],
                                vulnerability=row['vulnerability'] or 'None'
                            )

                            # Calculate actual score vs par score impact
                            if par_comparison.get('available') and analysis.par_result:
                                actual_score = row['hand_score'] or 0
                                par_score = analysis.par_result.score

                                # Determine if user was on declaring side
                                declarer_side = 'NS' if row['contract_declarer'] in ['N', 'S'] else 'EW'
                                user_side = 'NS' if row['player_position'] in ['N', 'S'] else 'EW'

                                # Adjust par score direction based on user's side
                                # Par score is always from NS perspective
                                if user_side == 'EW':
                                    par_score = -par_score
                                    actual_score = -actual_score

                                par_comparison['actual_score'] = row['hand_score'] or 0
                                par_comparison['par_score_for_user'] = par_score
                                par_comparison['score_difference'] = actual_score - par_score
                                par_comparison['user_side'] = user_side

        except Exception as dds_error:
            # DDS not available or failed - continue without it
            import traceback
            traceback.print_exc()
            dd_analysis = {'error': str(dds_error), 'available': False}

        # Generate strategy summary for the hand
        strategy_summary = None
        try:
            if deal_data and row['contract_level'] and row['contract_strain']:
                from engine.hand import Hand, Card as BridgeCard

                # Determine declarer and dummy positions
                declarer_pos = row['contract_declarer'] or 'S'
                dummy_pos = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}.get(declarer_pos, 'N')

                # Convert deal_data to Hand objects for declarer and dummy
                declarer_hand = None
                dummy_hand = None

                for pos in [declarer_pos, dummy_pos]:
                    if pos in deal_data and 'hand' in deal_data[pos]:
                        cards = []
                        for card in deal_data[pos]['hand']:
                            rank = card.get('rank') or card.get('r')
                            suit = card.get('suit') or card.get('s')
                            # Normalize suit to Unicode symbols (Hand class expects ♠♥♦♣)
                            suit_to_unicode = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}
                            suit = suit_to_unicode.get(suit, suit)
                            cards.append(BridgeCard(rank=rank, suit=suit))
                        if pos == declarer_pos:
                            declarer_hand = Hand(cards=cards)
                        else:
                            dummy_hand = Hand(cards=cards)

                if declarer_hand and dummy_hand:
                    is_nt = row['contract_strain'] in ['NT', 'N']
                    strategy_summary = generate_hand_strategy_summary(
                        declarer_hand=declarer_hand,
                        dummy_hand=dummy_hand,
                        contract_level=row['contract_level'],
                        contract_strain=row['contract_strain'],
                        is_nt=is_nt
                    )
        except Exception as strategy_error:
            import traceback
            traceback.print_exc()
            strategy_summary = {'error': str(strategy_error)}

        # Calculate which positions the user controlled during play
        # User controls their position, plus dummy when on declaring side
        user_position = row['player_position'] or 'S'
        declarer = row['contract_declarer']

        # Check if user was on the declaring side
        user_side = 'NS' if user_position in ['N', 'S'] else 'EW'
        declarer_side = 'NS' if declarer in ['N', 'S'] else 'EW'

        if user_side == declarer_side:
            # User was on declaring side - they controlled both declarer and dummy
            if declarer_side == 'NS':
                user_controlled_positions = ['N', 'S']
            else:
                user_controlled_positions = ['E', 'W']
        else:
            # User was on defending side - they only controlled their position
            user_controlled_positions = [user_position]

        return jsonify({
            'hand_id': hand_id,
            'session_id': row['session_id'],
            'hand_number': row['hand_number'],
            'dealer': row['dealer'],
            'vulnerability': row['vulnerability'],
            'contract': contract_display,
            'contract_level': row['contract_level'],
            'contract_strain': row['contract_strain'],
            'contract_declarer': row['contract_declarer'],
            'contract_doubled': row['contract_doubled'],
            'tricks_taken': row['tricks_taken'],
            'tricks_needed': row['tricks_needed'],
            'made': row['made'],
            'score': row['hand_score'],
            'score_breakdown': score_breakdown,
            'user_was_declarer': row['user_was_declarer'],
            'user_was_dummy': row['user_was_dummy'],
            'user_position': row['player_position'],
            'user_controlled_positions': user_controlled_positions,
            'played_at': row['played_at'],
            'deal': deal_data,
            'auction': auction_history,
            'play_history': play_history,
            'play_quality_summary': play_quality_summary,
            'bidding_quality_summary': bidding_quality_summary,
            'dd_analysis': dd_analysis,
            'par_comparison': par_comparison,
            'strategy_summary': strategy_summary
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


def analyze_play():
    """
    POST /api/analyze-play
    Analyze a specific play from a hand using DDS.

    Body:
        {
            "hand_id": 123,
            "trick_number": 1,  # 1-13
            "play_index": 0     # 0-3 for which card in the trick
        }

    Or for opening lead analysis:
        {
            "hand_id": 123,
            "opening_lead": true
        }

    Returns DDS analysis of the play including:
        - Optimal play
        - Tricks lost/gained
        - All alternative plays ranked
    """
    data = request.get_json()
    hand_id = data.get('hand_id')
    opening_lead = data.get('opening_lead', False)
    trick_number = data.get('trick_number', 1 if opening_lead else None)
    play_index = data.get('play_index', 0 if opening_lead else None)

    if not hand_id:
        return jsonify({'error': 'hand_id required'}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Get hand details
        cursor.execute("""
            SELECT
                sh.deal_data,
                sh.play_history,
                sh.contract_level,
                sh.contract_strain,
                sh.contract_declarer,
                gs.player_position
            FROM session_hands sh
            JOIN game_sessions gs ON sh.session_id = gs.id
            WHERE sh.id = ?
        """, (hand_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({'error': 'Hand not found'}), 404

        deal_data = json.loads(row['deal_data']) if row['deal_data'] else None
        play_history = json.loads(row['play_history']) if row['play_history'] else []

        if not deal_data or not play_history:
            return jsonify({'error': 'Hand does not have replay data'}), 400

        # Find the specific play to analyze
        if opening_lead:
            trick_number = 1
            play_index = 0

        if trick_number is None or play_index is None:
            return jsonify({'error': 'trick_number and play_index required'}), 400

        # Calculate which play in the sequence this is
        # Each trick has 4 plays, so play N is at index (trick-1)*4 + play_index
        total_play_index = (trick_number - 1) * 4 + play_index

        if total_play_index >= len(play_history):
            return jsonify({'error': 'Play not found in hand'}), 404

        # Get the actual play made
        actual_play = play_history[total_play_index]

        # Build hand state at the time of this play
        # This requires reconstructing what cards were still in each hand

        # Try to import DDS for analysis
        try:
            from engine.play.dds_analysis import is_dds_available, get_dds_service
            dds_available = is_dds_available()
        except ImportError:
            dds_available = False

        if not dds_available:
            # Return basic analysis without DDS
            return jsonify({
                'hand_id': hand_id,
                'trick_number': trick_number,
                'play_index': play_index,
                'actual_play': actual_play,
                'dds_available': False,
                'message': 'DDS analysis not available on this server (endplay library not installed)'
            })

        # Reconstruct the hand state before this play
        # Start with original deal and remove played cards
        remaining_hands = {}
        for pos, pos_data in deal_data.items():
            remaining_hands[pos] = []
            for card in pos_data.get('hand', []):
                remaining_hands[pos].append((card['rank'], card['suit']))

        # Remove cards played before this point
        for i in range(total_play_index):
            played = play_history[i]
            player = played.get('player', played.get('position'))
            card = (played.get('rank'), played.get('suit'))
            if player in remaining_hands and card in remaining_hands[player]:
                remaining_hands[player].remove(card)

        # Get the player for this play
        player = actual_play.get('player', actual_play.get('position'))

        # Get current trick cards (cards played in this trick before this play)
        current_trick = []
        trick_start = (trick_number - 1) * 4
        for i in range(trick_start, total_play_index):
            current_trick.append(play_history[i])

        # Determine who led this trick
        if play_index == 0:
            # This is the lead - determine from previous trick winner or declarer's LHO
            if trick_number == 1:
                # Opening lead - leader is declarer's LHO
                declarer = row['contract_declarer']
                position_order = ['N', 'E', 'S', 'W']
                declarer_idx = position_order.index(declarer)
                leader = position_order[(declarer_idx + 1) % 4]
            else:
                # Need to find previous trick winner - this is complex
                # For now, we'll skip this analysis for non-opening leads
                leader = player
        else:
            leader = current_trick[0].get('player', current_trick[0].get('position'))

        # On-demand DDS analysis for specific plays
        # This provides detailed analysis of what the optimal play would have been
        # Note: Real-time DDS analysis during gameplay is recorded in play_decisions table
        # This endpoint provides retroactive analysis of any play position

        try:
            # Get DDS service
            dds_service = get_dds_service()

            # Build Hand objects from remaining cards
            from engine.hand import Hand, Card as BridgeCard
            suit_to_unicode = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}
            hand_objects = {}
            for pos, cards in remaining_hands.items():
                # Convert (rank, suit) tuples to Card objects
                # Normalize suit to Unicode symbols (Hand class expects ♠♥♦♣)
                card_objs = [BridgeCard(rank=r, suit=suit_to_unicode.get(s, s)) for r, s in cards]
                hand_objects[pos] = Hand(cards=card_objs)

            # Get the contract strain for DD analysis
            contract_strain = row['contract_strain']

            # Use DDS to analyze this position
            analysis = dds_service.analyze_deal(hand_objects)

            if not analysis.is_valid:
                return jsonify({
                    'hand_id': hand_id,
                    'trick_number': trick_number,
                    'play_index': play_index,
                    'actual_play': actual_play,
                    'dds_available': False,
                    'error': analysis.error or 'DDS analysis failed',
                    'message': 'Position analysis not available'
                })

            # Get DD results for this position/strain
            strain_key = {'♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C', 'NT': 'NT',
                         'S': 'S', 'H': 'H', 'D': 'D', 'C': 'C'}.get(contract_strain, 'NT')
            dd_tricks = analysis.dd_table.get_tricks(player, strain_key)

            # Return analysis with DD table info
            return jsonify({
                'hand_id': hand_id,
                'trick_number': trick_number,
                'play_index': play_index,
                'is_opening_lead': opening_lead or (trick_number == 1 and play_index == 0),
                'player': player,
                'actual_play': actual_play,
                'dds_available': True,
                'dd_tricks_from_position': dd_tricks,
                'message': 'DD analysis shows optimal play from this position',
                'note': 'Detailed play-by-play analysis available in the Play Quality Summary above'
            })

        except Exception as dds_error:
            # DDS analysis failed, return informative message
            return jsonify({
                'hand_id': hand_id,
                'trick_number': trick_number,
                'play_index': play_index,
                'actual_play': actual_play,
                'dds_available': False,
                'error': f'DDS analysis error: {str(dds_error)}',
                'message': 'View Play Quality Summary above for recorded analysis'
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

    # Hand history & DDS analysis
    app.route('/api/hand-history', methods=['GET'])(get_hand_history)
    app.route('/api/hand-detail', methods=['GET'])(get_hand_detail)
    app.route('/api/analyze-play', methods=['POST'])(analyze_play)

    print("✓ Analytics API endpoints registered")
    print("✓ Four-dimension progress endpoint registered")
    print("✓ Hand history & DDS analysis endpoints registered")

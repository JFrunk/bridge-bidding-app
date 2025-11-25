"""
Learning Path API - Endpoints for structured learning and convention progression

Integrates:
- ConventionRegistry (metadata)
- SkillTree (progression)
- User progress tracking

To add to server.py:
    from engine.learning.learning_path_api import register_learning_endpoints
    register_learning_endpoints(app)
"""

from flask import request, jsonify
from typing import Dict, List
import sys
from pathlib import Path

# Database abstraction layer for SQLite/PostgreSQL compatibility
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from db import get_connection

from engine.ai.conventions.convention_registry import get_convention_registry
from engine.learning.skill_tree import get_skill_tree_manager


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_db_connection(db_path='bridge.db'):
    """Get database connection using abstraction layer"""
    return get_connection()


def get_user_completed_skills(user_id: int) -> List[str]:
    """Get list of skills user has completed"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT skill_id
        FROM user_progress
        WHERE user_id = ? AND mastered = 1
    """, (user_id,))

    skills = [row['skill_id'] for row in cursor.fetchall()]
    conn.close()

    return skills


def get_user_mastered_conventions(user_id: int) -> List[str]:
    """Get list of conventions user has mastered"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT convention_id
        FROM user_convention_progress
        WHERE user_id = ? AND status = 'mastered'
    """, (user_id,))

    conventions = [row['convention_id'] for row in cursor.fetchall()]
    conn.close()

    return conventions


def get_user_convention_status(user_id: int, convention_id: str) -> Dict:
    """Get detailed status for a specific convention"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM user_convention_progress
        WHERE user_id = ? AND convention_id = ?
    """, (user_id, convention_id))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return dict(row)


# ============================================================================
# API ENDPOINT FUNCTIONS
# ============================================================================

def conventions_by_level():
    """
    GET /api/conventions/by-level
    Get all conventions grouped by level (essential, intermediate, advanced)
    """
    registry = get_convention_registry()

    return jsonify({
        'essential': [c.to_dict() for c in registry.get_essential_conventions()],
        'intermediate': [c.to_dict() for c in registry.get_intermediate_conventions()],
        'advanced': [c.to_dict() for c in registry.get_advanced_conventions()]
    })


def convention_detail(convention_id: str):
    """
    GET /api/conventions/<convention_id>
    Get detailed information about a specific convention
    """
    registry = get_convention_registry()
    convention = registry.get_convention(convention_id)

    if not convention:
        return jsonify({'error': f'Convention {convention_id} not found'}), 404

    return jsonify(convention.to_dict())


def user_convention_progress():
    """
    GET /api/user/convention-progress?user_id=<id>
    Get user's progress across all convention levels
    """
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    registry = get_convention_registry()
    mastered = get_user_mastered_conventions(user_id)

    # Get progress summary
    progress_summary = registry.get_progress_summary(mastered)

    # Get detailed status for each convention
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT convention_id, status, accuracy, attempts, last_practiced
        FROM user_convention_progress
        WHERE user_id = ?
    """, (user_id,))

    convention_statuses = {}
    for row in cursor.fetchall():
        convention_statuses[row['convention_id']] = {
            'status': row['status'],
            'accuracy': row['accuracy'],
            'attempts': row['attempts'],
            'last_practiced': row['last_practiced']
        }

    conn.close()

    return jsonify({
        'user_id': user_id,
        'summary': progress_summary,
        'conventions': convention_statuses
    })


def unlocked_conventions():
    """
    GET /api/conventions/unlocked?user_id=<id>
    Get conventions that are unlocked and available for the user
    """
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    registry = get_convention_registry()
    completed_skills = get_user_completed_skills(user_id)
    mastered_conventions = get_user_mastered_conventions(user_id)

    unlocked = registry.get_unlocked_conventions(completed_skills, mastered_conventions)

    return jsonify({
        'user_id': user_id,
        'unlocked': [c.to_dict() for c in unlocked],
        'count': len(unlocked)
    })


def next_recommended_convention():
    """
    GET /api/conventions/next-recommended?user_id=<id>
    Get the next convention user should learn
    """
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    registry = get_convention_registry()
    completed_skills = get_user_completed_skills(user_id)
    mastered_conventions = get_user_mastered_conventions(user_id)

    next_conv = registry.get_next_recommended_convention(completed_skills, mastered_conventions)

    if not next_conv:
        return jsonify({'recommended': None, 'message': 'All conventions mastered!'})

    return jsonify({
        'recommended': next_conv.to_dict(),
        'message': f'We recommend learning {next_conv.name} next'
    })


def skill_tree_full():
    """
    GET /api/skill-tree
    Get the complete skill tree structure
    """
    tree_manager = get_skill_tree_manager()
    return jsonify(tree_manager.get_all_levels())


def skill_tree_progress():
    """
    GET /api/skill-tree/progress?user_id=<id>
    Get user's progress through the skill tree
    """
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    completed_skills = get_user_completed_skills(user_id)
    mastered_conventions = get_user_mastered_conventions(user_id)

    user_progress = {
        'completed_skills': completed_skills,
        'mastered_conventions': mastered_conventions
    }

    tree_manager = get_skill_tree_manager()
    progress = tree_manager.get_user_skill_tree_progress(user_progress)
    next_level = tree_manager.get_next_recommended_level(user_progress)

    return jsonify({
        'user_id': user_id,
        'levels': progress,
        'next_recommended_level': next_level
    })


def record_convention_practice():
    """
    POST /api/conventions/record-practice
    Record a practice attempt for a convention

    DEPRECATED: This endpoint is maintained for backward compatibility.
    New code should use /api/practice/record from analytics_api.py which includes
    error categorization and mistake pattern analysis.

    Body:
        {
            "user_id": 1,
            "convention_id": "stayman",
            "was_correct": true,
            "hints_used": 0,
            "time_taken_seconds": 45
        }
    """
    data = request.get_json()
    user_id = data.get('user_id')
    convention_id = data.get('convention_id')
    was_correct = data.get('was_correct')
    hints_used = data.get('hints_used', 0)
    time_taken = data.get('time_taken_seconds')

    if not all([user_id, convention_id, was_correct is not None]):
        return jsonify({'error': 'Missing required fields'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Record practice history (old table for backward compatibility)
        cursor.execute("""
            INSERT INTO convention_practice_history (
                user_id, convention_id, was_correct, hints_used, time_taken_seconds
            ) VALUES (?, ?, ?, ?, ?)
        """, (user_id, convention_id, was_correct, hints_used, time_taken))

        # Update progress
        cursor.execute("""
            SELECT attempts, correct, status
            FROM user_convention_progress
            WHERE user_id = ? AND convention_id = ?
        """, (user_id, convention_id))

        row = cursor.fetchone()

        if row:
            attempts = row['attempts'] + 1
            correct = row['correct'] + (1 if was_correct else 0)
            accuracy = correct / attempts
            current_status = row['status']

            # Determine new status
            if current_status == 'locked':
                new_status = 'in_progress'
            elif current_status in ['unlocked', 'in_progress']:
                # Check if mastered
                registry = get_convention_registry()
                convention = registry.get_convention(convention_id)
                if convention and accuracy >= convention.passing_accuracy and attempts >= convention.practice_hands_required:
                    new_status = 'mastered'
                else:
                    new_status = 'in_progress'
            else:
                new_status = current_status

            # Update
            cursor.execute("""
                UPDATE user_convention_progress
                SET attempts = ?,
                    correct = ?,
                    accuracy = ?,
                    status = ?,
                    last_practiced = CURRENT_TIMESTAMP,
                    mastered_at = CASE WHEN ? = 'mastered' AND status != 'mastered' THEN CURRENT_TIMESTAMP ELSE mastered_at END
                WHERE user_id = ? AND convention_id = ?
            """, (attempts, correct, accuracy, new_status, new_status, user_id, convention_id))

        else:
            # Create initial record
            accuracy = 1.0 if was_correct else 0.0
            cursor.execute("""
                INSERT INTO user_convention_progress (
                    user_id, convention_id, status, attempts, correct, accuracy,
                    started_at, last_practiced
                ) VALUES (?, ?, 'in_progress', 1, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (user_id, convention_id, 1 if was_correct else 0, accuracy))

        conn.commit()

        # Get updated progress
        cursor.execute("""
            SELECT *
            FROM user_convention_progress
            WHERE user_id = ? AND convention_id = ?
        """, (user_id, convention_id))

        updated = dict(cursor.fetchone())

        return jsonify({
            'success': True,
            'progress': updated
        })

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        conn.close()


def unlock_convention():
    """
    POST /api/conventions/unlock
    Manually unlock a convention for a user (used when prerequisites met)

    Body:
        {
            "user_id": 1,
            "convention_id": "stayman"
        }
    """
    data = request.get_json()
    user_id = data.get('user_id')
    convention_id = data.get('convention_id')

    if not all([user_id, convention_id]):
        return jsonify({'error': 'Missing required fields'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if record exists
        cursor.execute("""
            SELECT status
            FROM user_convention_progress
            WHERE user_id = ? AND convention_id = ?
        """, (user_id, convention_id))

        row = cursor.fetchone()

        if row:
            # Update status
            cursor.execute("""
                UPDATE user_convention_progress
                SET status = 'unlocked'
                WHERE user_id = ? AND convention_id = ? AND status = 'locked'
            """, (user_id, convention_id))
        else:
            # Create record
            cursor.execute("""
                INSERT INTO user_convention_progress (
                    user_id, convention_id, status
                ) VALUES (?, ?, 'unlocked')
            """, (user_id, convention_id))

        conn.commit()

        return jsonify({
            'success': True,
            'message': f'Convention {convention_id} unlocked for user {user_id}'
        })

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        conn.close()


# ============================================================================
# REGISTER ENDPOINTS
# ============================================================================

def register_learning_endpoints(app):
    """
    Register all learning path endpoints with Flask app.

    Usage in server.py:
        from engine.learning.learning_path_api import register_learning_endpoints
        register_learning_endpoints(app)
    """

    # Convention endpoints
    app.route('/api/conventions/by-level', methods=['GET'])(conventions_by_level)
    app.route('/api/conventions/<convention_id>', methods=['GET'])(convention_detail)
    app.route('/api/conventions/unlocked', methods=['GET'])(unlocked_conventions)
    app.route('/api/conventions/next-recommended', methods=['GET'])(next_recommended_convention)
    app.route('/api/conventions/record-practice', methods=['POST'])(record_convention_practice)
    app.route('/api/conventions/unlock', methods=['POST'])(unlock_convention)

    # User progress endpoints
    app.route('/api/user/convention-progress', methods=['GET'])(user_convention_progress)

    # Skill tree endpoints
    app.route('/api/skill-tree', methods=['GET'])(skill_tree_full)
    app.route('/api/skill-tree/progress', methods=['GET'])(skill_tree_progress)

    print("✓ Learning path API endpoints registered")

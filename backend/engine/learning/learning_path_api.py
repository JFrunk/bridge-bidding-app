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
    """Get list of skills user has completed (mastered status)."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT skill_id
            FROM user_skill_progress
            WHERE user_id = ? AND status = 'mastered'
        """, (user_id,))
        skills = [row['skill_id'] for row in cursor.fetchall()]
    except Exception:
        # Table doesn't exist yet - return empty list
        skills = []
    finally:
        conn.close()

    return skills


def get_user_skill_status(user_id: int, skill_id: str) -> Dict:
    """Get detailed status for a specific skill"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT *
            FROM user_skill_progress
            WHERE user_id = ? AND skill_id = ?
        """, (user_id, skill_id))

        row = cursor.fetchone()
        if row:
            return dict(row)
    except Exception:
        pass
    finally:
        conn.close()

    return None


def record_skill_practice(user_id: int, skill_id: str, skill_level: int,
                          was_correct: bool, hand_id: str = None,
                          user_bid: str = None, correct_bid: str = None) -> Dict:
    """Record a skill practice attempt and update progress."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Record the practice attempt
        cursor.execute("""
            INSERT INTO skill_practice_history
            (user_id, skill_id, skill_level, hand_id, user_bid, correct_bid, was_correct)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, skill_id, skill_level, hand_id, user_bid, correct_bid, was_correct))

        # Check if user has progress record for this skill
        cursor.execute("""
            SELECT * FROM user_skill_progress
            WHERE user_id = ? AND skill_id = ?
        """, (user_id, skill_id))
        existing = cursor.fetchone()

        if existing:
            # Update existing progress
            new_attempts = existing['attempts'] + 1
            new_correct = existing['correct'] + (1 if was_correct else 0)
            new_accuracy = new_correct / new_attempts if new_attempts > 0 else 0

            # Check if mastered (80% accuracy with minimum attempts)
            from engine.learning.skill_tree import get_skill_tree_manager
            manager = get_skill_tree_manager()
            skill_node = None
            for level_id, level_data in manager.tree.items():
                if 'skills' in level_data:
                    for skill in level_data['skills']:
                        if skill.id == skill_id:
                            skill_node = skill
                            break

            required_hands = skill_node.practice_hands_required if skill_node else 5
            required_accuracy = skill_node.passing_accuracy if skill_node else 0.80

            new_status = existing['status']
            mastered_at = existing['mastered_at']

            if (new_attempts >= required_hands and
                new_accuracy >= required_accuracy and
                new_status != 'mastered'):
                new_status = 'mastered'
                mastered_at = 'CURRENT_TIMESTAMP'

            cursor.execute("""
                UPDATE user_skill_progress
                SET attempts = ?, correct = ?, accuracy = ?,
                    status = ?, last_practiced = CURRENT_TIMESTAMP
                WHERE user_id = ? AND skill_id = ?
            """, (new_attempts, new_correct, new_accuracy, new_status,
                  user_id, skill_id))

            status = new_status
            attempts = new_attempts
            correct = new_correct
            accuracy = new_accuracy
        else:
            # Create new progress record
            accuracy = 1.0 if was_correct else 0.0
            cursor.execute("""
                INSERT INTO user_skill_progress
                (user_id, skill_id, skill_level, status, attempts, correct, accuracy, started_at, last_practiced)
                VALUES (?, ?, ?, 'in_progress', 1, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (user_id, skill_id, skill_level, 1 if was_correct else 0, accuracy))

            status = 'in_progress'
            attempts = 1
            correct = 1 if was_correct else 0

        conn.commit()

        return {
            'success': True,
            'skill_id': skill_id,
            'status': status,
            'attempts': attempts,
            'correct': correct,
            'accuracy': accuracy
        }

    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()


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
# SKILL PRACTICE ENDPOINT
# ============================================================================

def record_skill_practice_endpoint():
    """
    POST /api/skills/record-practice
    Record a practice attempt for a skill (non-convention)

    Body:
        {
            "user_id": 1,
            "skill_id": "hand_evaluation_basics",
            "skill_level": 0,
            "was_correct": true,
            "hand_id": "abc123",      (optional)
            "user_bid": "1H",         (optional)
            "correct_bid": "1S"       (optional)
        }
    """
    data = request.get_json()
    user_id = data.get('user_id')
    skill_id = data.get('skill_id')
    skill_level = data.get('skill_level', 0)
    was_correct = data.get('was_correct')

    if not all([user_id, skill_id, was_correct is not None]):
        return jsonify({'error': 'Missing required fields (user_id, skill_id, was_correct)'}), 400

    result = record_skill_practice(
        user_id=user_id,
        skill_id=skill_id,
        skill_level=skill_level,
        was_correct=was_correct,
        hand_id=data.get('hand_id'),
        user_bid=data.get('user_bid'),
        correct_bid=data.get('correct_bid')
    )

    if result.get('success'):
        return jsonify(result)
    else:
        return jsonify(result), 500


def user_skill_progress_endpoint():
    """
    GET /api/user/skill-progress?user_id=1
    Get user's progress on all skills
    """
    user_id = request.args.get('user_id', type=int)

    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT skill_id, skill_level, status, attempts, correct, accuracy,
                   started_at, mastered_at, last_practiced
            FROM user_skill_progress
            WHERE user_id = ?
            ORDER BY skill_level, skill_id
        """, (user_id,))

        skills = [dict(row) for row in cursor.fetchall()]
        return jsonify({
            'user_id': user_id,
            'skills': skills,
            'total_skills': len(skills),
            'mastered_count': sum(1 for s in skills if s['status'] == 'mastered')
        })

    except Exception as e:
        return jsonify({'error': str(e), 'skills': []})
    finally:
        conn.close()


def curriculum_summary():
    """
    GET /api/curriculum/summary
    Get summary of entire curriculum
    """
    manager = get_skill_tree_manager()
    return jsonify(manager.get_curriculum_summary())


def generate_skill_practice_hand():
    """
    GET /api/skills/practice-hand?skill_id=hand_evaluation_basics&variant=balanced

    Generate a practice hand for a specific skill.

    Query params:
        skill_id: The skill ID from skill_tree.py
        variant: Optional variant for different difficulty/focus

    Returns:
        {
            "skill_id": "hand_evaluation_basics",
            "skill_level": 0,
            "hand": {
                "cards": [...],
                "display": "♠ A K 5 3\n♥ Q J 2\n...",
                "hcp": 15,
                "distribution_points": 1,
                "total_points": 16,
                "is_balanced": true,
                "suit_lengths": {"♠": 4, "♥": 3, ...}
            },
            "expected_response": {...},
            "hand_id": "abc123"
        }
    """
    from engine.learning.skill_hand_generators import get_skill_hand_generator, create_deck
    import uuid

    skill_id = request.args.get('skill_id')
    variant = request.args.get('variant')

    if not skill_id:
        return jsonify({'error': 'skill_id required'}), 400

    generator = get_skill_hand_generator(skill_id, variant)
    if not generator:
        return jsonify({'error': f'No generator found for skill: {skill_id}'}), 404

    deck = create_deck()
    hand, remaining = generator.generate(deck)

    if not hand:
        return jsonify({'error': 'Failed to generate hand with constraints'}), 500

    hand_id = str(uuid.uuid4())[:8]

    # Format cards for JSON
    cards = [{'rank': c.rank, 'suit': c.suit} for c in hand.cards]

    response_data = {
        'skill_id': skill_id,
        'skill_level': generator.skill_level,
        'hand': {
            'cards': cards,
            'display': str(hand),
            'hcp': hand.hcp,
            'distribution_points': hand.dist_points,
            'total_points': hand.total_points,
            'is_balanced': hand.is_balanced,
            'suit_lengths': hand.suit_lengths
        },
        'expected_response': generator.get_expected_response(hand),
        'hand_id': hand_id
    }

    return jsonify(response_data)


def get_available_skill_generators():
    """
    GET /api/skills/available

    Get list of all skills that have hand generators.
    """
    from engine.learning.skill_hand_generators import get_available_skills, SKILL_GENERATORS

    skills = []
    for skill_id in get_available_skills():
        gen_class = SKILL_GENERATORS[skill_id]
        skills.append({
            'skill_id': skill_id,
            'level': gen_class.skill_level,
            'description': gen_class.description
        })

    return jsonify({
        'skills': skills,
        'total': len(skills)
    })


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
    app.route('/api/user/skill-progress', methods=['GET'])(user_skill_progress_endpoint)

    # Skill tree endpoints
    app.route('/api/skill-tree', methods=['GET'])(skill_tree_full)
    app.route('/api/skill-tree/progress', methods=['GET'])(skill_tree_progress)

    # Skill practice endpoints
    app.route('/api/skills/record-practice', methods=['POST'])(record_skill_practice_endpoint)
    app.route('/api/skills/practice-hand', methods=['GET'])(generate_skill_practice_hand)
    app.route('/api/skills/available', methods=['GET'])(get_available_skill_generators)

    # Curriculum endpoints
    app.route('/api/curriculum/summary', methods=['GET'])(curriculum_summary)

    print("✓ Learning path API endpoints registered")

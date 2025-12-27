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
# LEARNING MODE SESSION MANAGEMENT
# ============================================================================

import random
import uuid


def normalize_bid(bid: str) -> str:
    """Normalize bid string for comparison.

    Handles both ASCII (1H) and Unicode (1♥) formats.
    """
    if not bid:
        return ''
    bid = str(bid).upper().strip()
    # Map ASCII suit letters to Unicode
    bid = bid.replace('S', '♠').replace('H', '♥').replace('D', '♦').replace('C', '♣')
    return bid


def _get_opening_education(correct_bid: str) -> str:
    """
    Get educational context about opening bids based on conventions.

    Provides rule reminders for opening bid decisions.
    """
    normalized_bid = normalize_bid(correct_bid)

    # Opening bid conventions
    if normalized_bid == '1NT':
        return ' Convention: 1NT (15-17 HCP, balanced). Precise and descriptive - partner knows your range immediately!'
    elif normalized_bid == '2NT':
        return ' Convention: 2NT (20-21 HCP, balanced). Too strong for 1NT, not forcing like 2♣.'
    elif normalized_bid == '2♣':
        return ' Convention: 2♣ (22+ HCP or 9+ tricks). Artificial, game-forcing. Partner must respond!'
    elif normalized_bid == '1♠':
        return ' Convention: Open 1♠ with 5+ spades. With two 5-card suits, bid the higher-ranking first.'
    elif normalized_bid == '1♥':
        return ' Convention: Open 1♥ with 5+ hearts (or 4 hearts with no 5-card suit).'
    elif normalized_bid == '1♦':
        return ' Convention: Open 1♦ with 4+ diamonds (no 5-card major). "Better minor" principle.'
    elif normalized_bid == '1♣':
        return ' Convention: Open 1♣ with 3+ clubs (no 5-card major, <4 diamonds). Default opening.'
    elif normalized_bid.upper() == 'PASS':
        return ' Convention: Pass with <12 HCP unless Rule of 20 applies (HCP + two longest suits ≥ 20).'

    return ''


def _get_responding_education(partner_opening: str, correct_bid: str) -> str:
    """
    Get educational context about responding bids based on conventions.

    Provides rule reminders to help users learn the bidding logic.
    """
    normalized_bid = normalize_bid(correct_bid)
    normalized_opening = normalize_bid(partner_opening)

    education = ''

    # Major suit responses (1♥ or 1♠)
    if normalized_opening in ['1♥', '1♠']:
        suit = '♥' if normalized_opening == '1♥' else '♠'
        if normalized_bid.startswith('2') and suit in normalized_bid:
            education = f' Convention: Single raise (6-10 pts, 3+ {suit}) shows support but limited strength.'
        elif normalized_bid.startswith('3') and suit in normalized_bid:
            education = f' Convention: Jump raise (10-12 pts, 4+ {suit}) is invitational - partner bids game with extras.'
        elif normalized_bid.startswith('4') and suit in normalized_bid:
            education = f' Convention: Game raise (13+ pts, 4+ {suit}) - you have enough for game!'
        elif normalized_bid == '1♠' and normalized_opening == '1♥':
            education = ' Convention: New suit at 1-level (6+ pts, 4+ cards) - show your spades before supporting hearts.'
        elif normalized_bid == '1NT':
            education = ' Convention: 1NT response (6-10 pts) denies 4 spades and major support. Balanced, no better bid.'
        elif normalized_bid == '2NT':
            education = ' Convention: 2NT (11-12 pts) is invitational. Balanced, no major fit.'
        elif normalized_bid == '3NT':
            education = ' Convention: 3NT (13-15 pts) shows game values. Balanced, no major fit.'
        elif normalized_bid.upper() == 'PASS':
            education = ' Convention: Pass with fewer than 6 points - not enough to respond.'

    # Minor suit responses (1♣ or 1♦)
    elif normalized_opening in ['1♣', '1♦']:
        if normalized_bid == '1♦':
            education = ' Convention: Bid 1♦ with 4+ diamonds (6+ pts). Show suits "up the line."'
        elif normalized_bid == '1♥':
            education = ' Convention: Bid 1♥ with 4+ hearts (6+ pts). Always show a 4-card major over a minor!'
        elif normalized_bid == '1♠':
            education = ' Convention: Bid 1♠ with 4+ spades (6+ pts). Show your major suit.'
        elif normalized_bid == '1NT':
            education = ' Convention: 1NT response (6-10 pts) - no 4-card major to show.'
        elif normalized_bid == '2NT':
            education = ' Convention: 2NT (13-15 pts) is game-forcing. Balanced, no major.'
        elif normalized_bid == '3NT':
            education = ' Convention: 3NT (16-17 pts) - bid game directly with strong balanced hand.'
        elif normalized_bid.upper() == 'PASS':
            education = ' Convention: Pass with fewer than 6 points - not enough to respond.'

    # 1NT responses
    elif normalized_opening == '1NT':
        if normalized_bid == '2♣':
            education = ' Convention: Stayman (2♣) asks for 4-card majors. Use with 4-card major and 8+ pts.'
        elif normalized_bid == '2♦':
            education = ' Convention: Transfer to hearts (2♦→2♥). Shows 5+ hearts.'
        elif normalized_bid == '2♥':
            education = ' Convention: Transfer to spades (2♥→2♠). Shows 5+ spades.'
        elif normalized_bid == '2NT':
            education = ' Convention: 2NT (8-9 pts) invites game. Partner passes with minimum 15, bids 3NT with maximum.'
        elif normalized_bid == '3NT':
            education = ' Convention: 3NT (10-15 pts) - partner has 15-17, combined 25+ for game!'
        elif normalized_bid.upper() == 'PASS':
            education = ' Convention: Pass with 0-7 pts balanced - game is unlikely (need 25+ combined).'

    return education


def start_learning_session():
    """
    POST /api/learning/start-session

    Start a new learning session for a skill or convention.

    Body:
        {
            "user_id": 1,
            "topic_id": "hand_evaluation_basics",  // skill_id or convention_id
            "topic_type": "skill"  // "skill" or "convention"
        }

    Returns first hand and session info.
    """
    from engine.learning.skill_hand_generators import get_skill_hand_generator, create_deck

    data = request.get_json()
    user_id = data.get('user_id')
    topic_id = data.get('topic_id')
    topic_type = data.get('topic_type', 'skill')

    if not all([user_id, topic_id]):
        return jsonify({'error': 'user_id and topic_id required'}), 400

    session_id = str(uuid.uuid4())[:12]

    # Get progress
    if topic_type == 'convention':
        progress = get_user_convention_status(user_id, topic_id)
        # Get convention hand (existing infrastructure)
        # For now, return placeholder - convention generators already exist
        hand_data = {'message': 'Use existing convention practice'}
        hands_required = 10
        expected = None
    else:
        progress = get_user_skill_status(user_id, topic_id)
        generator = get_skill_hand_generator(topic_id)

        if not generator:
            return jsonify({'error': f'No generator for skill: {topic_id}'}), 404

        deck = create_deck()
        hand, _ = generator.generate(deck)

        # Get expected response first (some skills don't need hands)
        expected = generator.get_expected_response(hand)

        # Check if this is a no-hand skill (like bidding_language)
        if expected.get('no_hand_required'):
            hand_data = None
        elif not hand:
            return jsonify({'error': 'Failed to generate hand'}), 500
        else:
            hand_data = {
                'cards': [{'rank': c.rank, 'suit': c.suit} for c in hand.cards],
                'display': str(hand),
                'hcp': hand.hcp,
                'distribution_points': hand.dist_points,
                'total_points': hand.total_points,
                'is_balanced': hand.is_balanced,
                'suit_lengths': hand.suit_lengths
            }

        hands_required = generator.skill_level * 2 + 5  # Simple formula

    return jsonify({
        'session_id': session_id,
        'topic_id': topic_id,
        'topic_type': topic_type,
        'hand': hand_data,
        'expected_response': expected if topic_type == 'skill' else None,
        'progress': {
            'attempts': progress.get('attempts', 0) if progress else 0,
            'correct': progress.get('correct', 0) if progress else 0,
            'accuracy': progress.get('accuracy', 0) if progress else 0,
            'status': progress.get('status', 'not_started') if progress else 'not_started'
        },
        'hands_required': hands_required,
        'hand_id': str(uuid.uuid4())[:8]
    })


def submit_learning_answer():
    """
    POST /api/learning/submit-answer

    Submit answer for current hand, get feedback and optionally next hand.

    Body:
        {
            "user_id": 1,
            "topic_id": "hand_evaluation_basics",
            "topic_type": "skill",
            "answer": "15",  // or bid like "1NT"
            "hand_id": "abc123",
            "expected_response": {...}  // from previous hand
        }
    """
    from engine.learning.skill_hand_generators import get_skill_hand_generator, create_deck
    from engine.learning.skill_tree import get_skill_tree_manager

    data = request.get_json()
    user_id = data.get('user_id')
    topic_id = data.get('topic_id')
    topic_type = data.get('topic_type', 'skill')
    answer = data.get('answer')
    hand_id = data.get('hand_id')
    expected = data.get('expected_response', {})

    if not all([user_id, topic_id, answer is not None]):
        return jsonify({'error': 'user_id, topic_id, and answer required'}), 400

    # Evaluate answer
    is_correct = False
    feedback = ''

    if topic_type == 'skill':
        # Skill-specific evaluation with educational feedback
        if 'hcp' in expected:
            # HCP counting question
            try:
                user_hcp = int(answer)
                is_correct = user_hcp == expected['hcp']
                if is_correct:
                    feedback = f'Correct! {expected["hcp"]} HCP. '
                    feedback += 'Remember: A=4, K=3, Q=2, J=1.'
                else:
                    feedback = f'The hand has {expected["hcp"]} HCP, not {user_hcp}. '
                    feedback += 'Count: Ace=4, King=3, Queen=2, Jack=1 points.'
            except ValueError:
                feedback = 'Please enter a number for HCP'
        elif 'should_open' in expected:
            # Should open question
            user_answer = str(answer).lower() in ['yes', 'true', 'open', '1']
            is_correct = user_answer == expected['should_open']
            explanation = expected.get('explanation', '')
            if is_correct:
                feedback = f'Correct! {explanation}'
            else:
                feedback = f'Not quite. {explanation}'
            # Add educational rule reminder
            feedback += ' Rule: Open with 12+ HCP, or 11+ HCP if Rule of 20 applies (HCP + two longest suits ≥ 20).'
        elif 'bid' in expected:
            # Bidding question - normalize both for comparison
            is_correct = normalize_bid(answer) == normalize_bid(expected['bid'])
            explanation = expected.get('explanation', '')

            # Build educational feedback based on the skill type
            if is_correct:
                feedback = f'Correct! {expected["bid"]}. {explanation}'
            else:
                feedback = f'The correct bid is {expected["bid"]}. {explanation}'

            # Add convention-specific educational context
            partner_opened = expected.get('partner_opened', '')
            if partner_opened:
                # This is a responding situation
                feedback += _get_responding_education(partner_opened, expected['bid'])
            else:
                # This is an opening bid situation
                feedback += _get_opening_education(expected['bid'])
        elif 'longest_suit' in expected:
            # Longest suit question (suit quality)
            # Normalize both to handle different suit representations
            user_suit = str(answer).strip()
            expected_suit = expected['longest_suit']
            # Handle both Unicode symbols and letter representations
            suit_map = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣',
                       'SPADES': '♠', 'HEARTS': '♥', 'DIAMONDS': '♦', 'CLUBS': '♣',
                       '♠': '♠', '♥': '♥', '♦': '♦', '♣': '♣'}
            normalized_user = suit_map.get(user_suit.upper(), user_suit)
            normalized_expected = suit_map.get(expected_suit.upper(), expected_suit)
            is_correct = normalized_user == normalized_expected
            length = expected.get('length', '')
            if is_correct:
                feedback = f'Correct! {expected_suit} is the longest suit with {length} cards.'
            else:
                feedback = f'The longest suit is {expected_suit} with {length} cards, not {user_suit}.'
        elif 'correct_answer' in expected and expected.get('no_hand_required'):
            # Contract-specific game/slam points question (bidding language)
            try:
                user_points = int(answer)
                expected_points = expected['correct_answer']
                contract = expected.get('display_contract', expected.get('contract', 'game'))
                is_correct = user_points == expected_points
                if is_correct:
                    feedback = f'Correct! {contract} requires about {expected_points} combined points.'
                else:
                    feedback = f'{contract} requires about {expected_points} combined points, not {user_points}. {expected.get("explanation", "")}'
            except ValueError:
                feedback = 'Please enter a number.'
        elif 'game_points_needed' in expected:
            # Legacy game points question (bidding language)
            try:
                user_points = int(answer)
                expected_points = expected['game_points_needed']
                is_correct = user_points == expected_points
                if is_correct:
                    feedback = f'Correct! You need about {expected_points} combined points to bid game.'
                else:
                    feedback = f'You need about {expected_points} combined points for game, not {user_points}. {expected.get("explanation", "")}'
            except ValueError:
                feedback = 'Please enter a number.'
        else:
            # Generic comparison
            is_correct = str(answer) == str(expected.get('answer', ''))
            feedback = expected.get('explanation', '')

        # Record practice
        manager = get_skill_tree_manager()
        skill_level = 0
        for level_id, level_data in manager.tree.items():
            if 'skills' in level_data:
                for skill in level_data['skills']:
                    if skill.id == topic_id:
                        skill_level = skill.level
                        break

        result = record_skill_practice(
            user_id=user_id,
            skill_id=topic_id,
            skill_level=skill_level,
            was_correct=is_correct,
            hand_id=hand_id
        )
    else:
        # Convention - use existing infrastructure
        result = {'success': True, 'status': 'in_progress', 'accuracy': 0}
        feedback = 'Convention evaluation uses existing system'

    # Check if topic is mastered
    progress = get_user_skill_status(user_id, topic_id) if topic_type == 'skill' else get_user_convention_status(user_id, topic_id)
    is_mastered = progress and progress.get('status') == 'mastered'

    # Generate next hand/question if not mastered
    next_hand = None
    next_expected = None
    next_hand_id = None

    if not is_mastered and topic_type == 'skill':
        generator = get_skill_hand_generator(topic_id)
        if generator:
            deck = create_deck()
            hand, _ = generator.generate(deck)

            # Get expected response (works for both hand and no-hand skills)
            next_expected = generator.get_expected_response(hand)

            # Check if this is a no-hand skill
            if next_expected.get('no_hand_required'):
                next_hand = None  # No hand needed
                next_hand_id = str(uuid.uuid4())[:8]  # Still need ID for tracking
            elif hand:
                next_hand = {
                    'cards': [{'rank': c.rank, 'suit': c.suit} for c in hand.cards],
                    'display': str(hand),
                    'hcp': hand.hcp,
                    'distribution_points': hand.dist_points,
                    'total_points': hand.total_points,
                    'is_balanced': hand.is_balanced,
                    'suit_lengths': hand.suit_lengths
                }
                next_hand_id = str(uuid.uuid4())[:8]

    return jsonify({
        'is_correct': is_correct,
        'feedback': feedback,
        'expected': expected,
        'progress': {
            'attempts': progress.get('attempts', 0) if progress else 0,
            'correct': progress.get('correct', 0) if progress else 0,
            'accuracy': round(progress.get('accuracy', 0) * 100, 1) if progress else 0,
            'status': progress.get('status', 'in_progress') if progress else 'in_progress'
        },
        'is_mastered': is_mastered,
        'next_hand': next_hand,
        'next_expected': next_expected,
        'next_hand_id': next_hand_id
    })


def get_interleaved_review():
    """
    GET /api/learning/review?user_id=X&level=Y

    Get mixed review hands from completed topics in a level.
    For interleaved practice after blocked learning.
    """
    from engine.learning.skill_hand_generators import get_skill_hand_generator, create_deck
    from engine.learning.skill_tree import get_skill_tree_manager

    user_id = request.args.get('user_id', type=int)
    level = request.args.get('level', type=int)
    count = request.args.get('count', default=10, type=int)

    if not user_id or level is None:
        return jsonify({'error': 'user_id and level required'}), 400

    manager = get_skill_tree_manager()
    level_id = manager.get_level_id_by_number(level)

    if not level_id:
        return jsonify({'error': f'Invalid level: {level}'}), 404

    level_data = manager.get_level(level_id)

    # Get skills or conventions for this level
    if 'skills' in level_data:
        topic_ids = [s.id for s in level_data['skills']]
        topic_type = 'skill'
    elif 'conventions' in level_data:
        topic_ids = level_data['conventions']
        topic_type = 'convention'
    else:
        return jsonify({'error': 'No topics in level'}), 400

    # Get completed topics
    completed = []
    for topic_id in topic_ids:
        if topic_type == 'skill':
            status = get_user_skill_status(user_id, topic_id)
        else:
            status = get_user_convention_status(user_id, topic_id)

        if status and status.get('status') in ['mastered', 'in_progress']:
            completed.append(topic_id)

    if len(completed) < 2:
        return jsonify({
            'ready': False,
            'message': 'Need at least 2 practiced topics for review',
            'practiced': len(completed),
            'required': 2
        })

    # Generate mixed hands
    hands = []
    for _ in range(count):
        topic_id = random.choice(completed)

        if topic_type == 'skill':
            generator = get_skill_hand_generator(topic_id)
            if generator:
                deck = create_deck()
                hand, _ = generator.generate(deck)
                if hand:
                    hands.append({
                        'topic_id': topic_id,
                        'hand': {
                            'cards': [{'rank': c.rank, 'suit': c.suit} for c in hand.cards],
                            'display': str(hand),
                            'hcp': hand.hcp,
                            'distribution_points': hand.dist_points,
                            'total_points': hand.total_points,
                            'is_balanced': hand.is_balanced,
                            'suit_lengths': hand.suit_lengths
                        },
                        'expected_response': generator.get_expected_response(hand),
                        'hand_id': str(uuid.uuid4())[:8]
                    })

    random.shuffle(hands)

    return jsonify({
        'ready': True,
        'review_session': True,
        'level': level,
        'topics_included': completed,
        'hands': hands,
        'total_hands': len(hands)
    })


def get_level_assessment():
    """
    GET /api/learning/level-assessment?user_id=X&level=Y

    Get assessment test for level completion.
    All topics must be individually completed first.
    """
    from engine.learning.skill_hand_generators import get_skill_hand_generator, create_deck
    from engine.learning.skill_tree import get_skill_tree_manager

    user_id = request.args.get('user_id', type=int)
    level = request.args.get('level', type=int)

    if not user_id or level is None:
        return jsonify({'error': 'user_id and level required'}), 400

    manager = get_skill_tree_manager()
    level_id = manager.get_level_id_by_number(level)

    if not level_id:
        return jsonify({'error': f'Invalid level: {level}'}), 404

    level_data = manager.get_level(level_id)

    # Get all topics for level
    if 'skills' in level_data:
        all_topics = [s.id for s in level_data['skills']]
        topic_type = 'skill'
    elif 'conventions' in level_data:
        all_topics = level_data['conventions']
        topic_type = 'convention'
    else:
        return jsonify({'error': 'No topics in level'}), 400

    # Check which are mastered
    mastered = []
    not_mastered = []

    for topic_id in all_topics:
        if topic_type == 'skill':
            status = get_user_skill_status(user_id, topic_id)
        else:
            status = get_user_convention_status(user_id, topic_id)

        if status and status.get('status') == 'mastered':
            mastered.append(topic_id)
        else:
            not_mastered.append(topic_id)

    if not_mastered:
        return jsonify({
            'ready': False,
            'message': 'Complete all topics before level assessment',
            'mastered': len(mastered),
            'total': len(all_topics),
            'remaining': not_mastered
        })

    # Generate assessment hands (20 mixed)
    hands = []
    hands_per_topic = max(1, 20 // len(all_topics))

    for topic_id in all_topics:
        if topic_type == 'skill':
            generator = get_skill_hand_generator(topic_id)
            if generator:
                for _ in range(hands_per_topic):
                    deck = create_deck()
                    hand, _ = generator.generate(deck)
                    if hand:
                        hands.append({
                            'topic_id': topic_id,
                            'hand': {
                                'cards': [{'rank': c.rank, 'suit': c.suit} for c in hand.cards],
                                'display': str(hand),
                                'hcp': hand.hcp,
                                'distribution_points': hand.dist_points,
                                'total_points': hand.total_points,
                                'is_balanced': hand.is_balanced,
                                'suit_lengths': hand.suit_lengths
                            },
                            'expected_response': generator.get_expected_response(hand),
                            'hand_id': str(uuid.uuid4())[:8]
                        })

    random.shuffle(hands)

    passing_accuracy = 0.85 if level == 8 else 0.80

    return jsonify({
        'ready': True,
        'assessment': True,
        'level': level,
        'level_name': level_data['name'],
        'topics': all_topics,
        'hands': hands,
        'total_hands': len(hands),
        'passing_accuracy': passing_accuracy
    })


def get_user_learning_status():
    """
    GET /api/learning/status?user_id=X

    Get comprehensive learning status for a user.
    """
    from engine.learning.skill_tree import get_skill_tree_manager

    user_id = request.args.get('user_id', type=int)

    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    manager = get_skill_tree_manager()

    # Get completed skills
    completed_skills = get_user_completed_skills(user_id)
    mastered_conventions = get_user_mastered_conventions(user_id)

    user_progress = {
        'completed_skills': completed_skills,
        'mastered_conventions': mastered_conventions
    }

    # Get level progress
    level_progress = manager.get_user_skill_tree_progress(user_progress)

    # Find current level (first incomplete)
    current_level = None
    for level_id, progress in level_progress.items():
        if progress['unlocked'] and progress['completed'] < progress['total']:
            current_level = level_id
            break

    # Calculate overall progress
    total_skills = sum(p['total'] for p in level_progress.values())
    completed_count = sum(p['completed'] for p in level_progress.values())

    return jsonify({
        'user_id': user_id,
        'current_level': current_level,
        'overall_progress': {
            'completed': completed_count,
            'total': total_skills,
            'percentage': round(completed_count / total_skills * 100, 1) if total_skills > 0 else 0
        },
        'levels': level_progress,
        'next_recommended': manager.get_next_recommended_level(user_progress)
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

    # Learning Mode session endpoints
    app.route('/api/learning/start-session', methods=['POST'])(start_learning_session)
    app.route('/api/learning/submit-answer', methods=['POST'])(submit_learning_answer)
    app.route('/api/learning/review', methods=['GET'])(get_interleaved_review)
    app.route('/api/learning/level-assessment', methods=['GET'])(get_level_assessment)
    app.route('/api/learning/status', methods=['GET'])(get_user_learning_status)

    print("✓ Learning path API endpoints registered")

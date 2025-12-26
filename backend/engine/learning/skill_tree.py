"""
Skill Tree for Structured Bridge Learning

Defines the complete learning path from beginner to expert (Levels 0-8):
- Level 0: Foundations (hand evaluation, suit quality, bidding language)
- Level 1: Opening Bids
- Level 2: Responding to Openings
- Level 3: Opener's Rebids
- Level 4: Responder's Rebids
- Level 5: Essential Conventions (Stayman, Jacoby, Weak Two, Takeout Double)
- Level 6: Competitive Bidding
- Level 7: Intermediate Conventions (Blackwood, Michaels, Unusual 2NT, etc.)
- Level 8: Advanced Conventions (Fourth Suit Forcing, Splinters, etc.)

Works with ConventionRegistry for convention metadata.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class SkillType(Enum):
    """Type of skill node in the tree"""
    BASIC_SKILL = "basic_skill"           # Fundamental bidding skill
    CONVENTION = "convention"              # Single convention
    CONVENTION_GROUP = "convention_group"  # Group of related conventions
    TOPIC = "topic"                        # Learning topic (subtopic within a level)


@dataclass
class SkillNode:
    """A node in the skill tree"""
    id: str
    name: str
    skill_type: SkillType
    level: int
    description: str
    prerequisites: List[str]  # List of skill/convention IDs
    passing_accuracy: float
    practice_hands_required: int
    unlock_message: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'skill_type': self.skill_type.value,
            'level': self.level,
            'description': self.description,
            'prerequisites': self.prerequisites,
            'passing_accuracy': self.passing_accuracy,
            'practice_hands_required': self.practice_hands_required,
            'unlock_message': self.unlock_message
        }


# ============================================================================
# SKILL TREE DEFINITION - Complete SAYC Curriculum (Levels 0-8)
# ============================================================================

SKILL_TREE = {
    # ========================================================================
    # LEVEL 0: FOUNDATIONS
    # "You cannot bid until you can evaluate your hand"
    # ========================================================================
    'level_0_foundations': {
        'name': 'Level 0: Foundations',
        'description': 'Essential hand evaluation skills before bidding',
        'level': 0,
        'unlock_requirement': 'Available from start',
        'completion_requirement': 'Complete all topics with 80%+ accuracy',
        'skills': [
            SkillNode(
                id='hand_evaluation_basics',
                name='Hand Evaluation Basics',
                skill_type=SkillType.TOPIC,
                level=0,
                description='Count high card points (A=4, K=3, Q=2, J=1), '
                           'distribution points (void=3, singleton=2, doubleton=1), '
                           'and recognize balanced vs unbalanced hands.',
                prerequisites=[],
                passing_accuracy=0.80,
                practice_hands_required=5
            ),
            SkillNode(
                id='suit_quality',
                name='Suit Quality',
                skill_type=SkillType.TOPIC,
                level=0,
                description='Identify biddable suits and understand suit ranking '
                           '(Clubs < Diamonds < Hearts < Spades < NT).',
                prerequisites=['hand_evaluation_basics'],
                passing_accuracy=0.80,
                practice_hands_required=5
            ),
            SkillNode(
                id='bidding_language',
                name='Language of Bidding',
                skill_type=SkillType.TOPIC,
                level=0,
                description='Understand forcing vs non-forcing bids, game bonuses, '
                           'slam bonuses, and basic bidding concepts.',
                prerequisites=['suit_quality'],
                passing_accuracy=0.80,
                practice_hands_required=5
            ),
        ],
        'unlock_message': 'Welcome to bridge bidding! Let\'s start with hand evaluation.'
    },

    # ========================================================================
    # LEVEL 1: OPENING BIDS
    # "Should I open? What should I open?"
    # ========================================================================
    'level_1_opening_bids': {
        'name': 'Level 1: Opening Bids',
        'description': 'Learn when and what to open',
        'level': 1,
        'unlock_requirement': 'Complete Level 0 Foundations',
        'completion_requirement': 'Complete all topics with 80%+ accuracy',
        'skills': [
            SkillNode(
                id='when_to_open',
                name='When to Open',
                skill_type=SkillType.BASIC_SKILL,
                level=1,
                description='Rule of 20, minimum 12-13 HCP requirement for opening.',
                prerequisites=['hand_evaluation_basics'],
                passing_accuracy=0.80,
                practice_hands_required=5
            ),
            SkillNode(
                id='opening_one_suit',
                name='Opening 1 of a Suit',
                skill_type=SkillType.BASIC_SKILL,
                level=1,
                description='5-card major requirement, minor suit openings '
                           '(1D with 4+, 1C with 3+), choosing between suits.',
                prerequisites=['when_to_open'],
                passing_accuracy=0.80,
                practice_hands_required=8
            ),
            SkillNode(
                id='opening_1nt',
                name='Opening 1NT',
                skill_type=SkillType.BASIC_SKILL,
                level=1,
                description='15-17 HCP balanced hand requirement.',
                prerequisites=['when_to_open'],
                passing_accuracy=0.80,
                practice_hands_required=5
            ),
            SkillNode(
                id='opening_2c_strong',
                name='Opening 2C (Strong)',
                skill_type=SkillType.BASIC_SKILL,
                level=1,
                description='22+ HCP or game-forcing hand.',
                prerequisites=['when_to_open'],
                passing_accuracy=0.80,
                practice_hands_required=4
            ),
            SkillNode(
                id='opening_2nt',
                name='Opening 2NT',
                skill_type=SkillType.BASIC_SKILL,
                level=1,
                description='20-21 HCP balanced hand.',
                prerequisites=['opening_1nt'],
                passing_accuracy=0.80,
                practice_hands_required=3
            ),
        ],
        'unlock_message': 'Level 1 Unlocked! Now learn when and how to open the bidding.'
    },

    # ========================================================================
    # LEVEL 2: RESPONDING TO OPENING BIDS
    # "Partner opened - what do I say?"
    # ========================================================================
    'level_2_responding': {
        'name': 'Level 2: Responding to Openings',
        'description': 'Learn how to respond to partner\'s opening bid',
        'level': 2,
        'unlock_requirement': 'Complete Level 1 Opening Bids',
        'completion_requirement': 'Complete all topics with 80%+ accuracy',
        'skills': [
            SkillNode(
                id='responding_to_major',
                name='Responding to 1 of a Major',
                skill_type=SkillType.BASIC_SKILL,
                level=2,
                description='Single raises, limit raises, game raises, new suit responses, '
                           'NT responses.',
                prerequisites=['opening_one_suit'],
                passing_accuracy=0.80,
                practice_hands_required=8
            ),
            SkillNode(
                id='responding_to_minor',
                name='Responding to 1 of a Minor',
                skill_type=SkillType.BASIC_SKILL,
                level=2,
                description='Priority: bid 4-card major first. Raising minors, NT bids.',
                prerequisites=['opening_one_suit'],
                passing_accuracy=0.80,
                practice_hands_required=6
            ),
            SkillNode(
                id='responding_to_1nt',
                name='Responding to 1NT',
                skill_type=SkillType.BASIC_SKILL,
                level=2,
                description='Pass, raises to 2NT/3NT, when conventions apply (learned later).',
                prerequisites=['opening_1nt'],
                passing_accuracy=0.80,
                practice_hands_required=6
            ),
            SkillNode(
                id='responding_to_2c',
                name='Responding to 2C',
                skill_type=SkillType.BASIC_SKILL,
                level=2,
                description='2D waiting response, positive responses with 8+ HCP.',
                prerequisites=['opening_2c_strong'],
                passing_accuracy=0.80,
                practice_hands_required=5
            ),
            SkillNode(
                id='responding_to_2nt',
                name='Responding to 2NT',
                skill_type=SkillType.BASIC_SKILL,
                level=2,
                description='Similar to 1NT responses but adjusted for 20-21 HCP range.',
                prerequisites=['opening_2nt'],
                passing_accuracy=0.80,
                practice_hands_required=5
            ),
        ],
        'unlock_message': 'Level 2 Unlocked! Learn how to respond when partner opens.'
    },

    # ========================================================================
    # LEVEL 3: OPENER'S REBIDS
    # "Partner responded - how do I describe my hand further?"
    # ========================================================================
    'level_3_openers_rebids': {
        'name': 'Level 3: Opener\'s Rebids',
        'description': 'Learn opener\'s second bid to further describe hand',
        'level': 3,
        'unlock_requirement': 'Complete Level 2 Responding',
        'completion_requirement': 'Complete all topics with 80%+ accuracy',
        'skills': [
            SkillNode(
                id='rebid_after_1_level',
                name='Rebids After 1-Level Response',
                skill_type=SkillType.BASIC_SKILL,
                level=3,
                description='Supporting partner, rebidding your suit, new suit, '
                           'reverse, jump shift, NT rebids.',
                prerequisites=['responding_to_major', 'responding_to_minor'],
                passing_accuracy=0.80,
                practice_hands_required=8
            ),
            SkillNode(
                id='rebid_after_2_level',
                name='Rebids After 2-Level Response',
                skill_type=SkillType.BASIC_SKILL,
                level=3,
                description='Game is likely, show extra strength appropriately.',
                prerequisites=['rebid_after_1_level'],
                passing_accuracy=0.80,
                practice_hands_required=6
            ),
            SkillNode(
                id='rebid_after_raise',
                name='Rebids After a Raise',
                skill_type=SkillType.BASIC_SKILL,
                level=3,
                description='Accepting invites, passing minimum, exploring slam.',
                prerequisites=['rebid_after_1_level'],
                passing_accuracy=0.80,
                practice_hands_required=6
            ),
            SkillNode(
                id='rebid_after_1nt_response',
                name='Rebids After 1NT Response',
                skill_type=SkillType.BASIC_SKILL,
                level=3,
                description='Pass with minimum, rebid suit, show new suit, raise to 2NT.',
                prerequisites=['responding_to_major'],
                passing_accuracy=0.80,
                practice_hands_required=5
            ),
        ],
        'unlock_message': 'Level 3 Unlocked! Master opener\'s rebidding strategy.'
    },

    # ========================================================================
    # LEVEL 4: RESPONDER'S REBIDS
    # "Opener rebid - where do we land?"
    # ========================================================================
    'level_4_responders_rebids': {
        'name': 'Level 4: Responder\'s Rebids',
        'description': 'Learn responder\'s second bid to find the best contract',
        'level': 4,
        'unlock_requirement': 'Complete Level 3 Opener\'s Rebids',
        'completion_requirement': 'Complete all topics with 80%+ accuracy',
        'skills': [
            SkillNode(
                id='after_opener_raises',
                name='After Opener Raises Your Suit',
                skill_type=SkillType.BASIC_SKILL,
                level=4,
                description='Sign off, invite game, bid game with fit confirmed.',
                prerequisites=['rebid_after_raise'],
                passing_accuracy=0.80,
                practice_hands_required=5
            ),
            SkillNode(
                id='after_opener_rebids_suit',
                name='After Opener Rebids Their Suit',
                skill_type=SkillType.BASIC_SKILL,
                level=4,
                description='Finding a fit or choosing alternative contract.',
                prerequisites=['rebid_after_1_level'],
                passing_accuracy=0.80,
                practice_hands_required=5
            ),
            SkillNode(
                id='after_opener_new_suit',
                name='After Opener Bids New Suit',
                skill_type=SkillType.BASIC_SKILL,
                level=4,
                description='Preference, support new suit, rebid your suit.',
                prerequisites=['rebid_after_1_level'],
                passing_accuracy=0.80,
                practice_hands_required=5
            ),
            SkillNode(
                id='after_opener_rebids_nt',
                name='After Opener Rebids NT',
                skill_type=SkillType.BASIC_SKILL,
                level=4,
                description='Calculate combined points, bid game or invite.',
                prerequisites=['rebid_after_1_level'],
                passing_accuracy=0.80,
                practice_hands_required=3
            ),
            SkillNode(
                id='preference_bids',
                name='Preference Bids',
                skill_type=SkillType.BASIC_SKILL,
                level=4,
                description='Return to opener\'s first suit when second doesn\'t fit.',
                prerequisites=['after_opener_new_suit'],
                passing_accuracy=0.80,
                practice_hands_required=2
            ),
        ],
        'unlock_message': 'Level 4 Unlocked! Complete the bidding conversation as responder.'
    },

    # ========================================================================
    # LEVEL 5: ESSENTIAL CONVENTIONS
    # "Special agreements that improve accuracy"
    # ========================================================================
    'level_5_essential_conventions': {
        'name': 'Level 5: Essential Conventions',
        'description': 'Must-learn conventions for every bridge player',
        'level': 5,
        'type': SkillType.CONVENTION_GROUP,
        'unlock_requirement': 'Complete Level 4 Responder\'s Rebids',
        'completion_requirement': 'Master all 4 conventions with 80%+ accuracy',
        'conventions': [
            'stayman',            # References ConventionRegistry
            'jacoby_transfers',
            'weak_two',
            'takeout_double'
        ],
        'unlock_message': 'Level 5 Unlocked! Learn the essential conventions every player uses.'
    },

    # ========================================================================
    # LEVEL 6: COMPETITIVE BIDDING
    # "What changes when opponents bid?"
    # ========================================================================
    'level_6_competitive_bidding': {
        'name': 'Level 6: Competitive Bidding',
        'description': 'Bidding when opponents interfere',
        'level': 6,
        'unlock_requirement': 'Complete Level 5 Essential Conventions',
        'completion_requirement': 'Complete all topics with 80%+ accuracy',
        'skills': [
            SkillNode(
                id='overcalls',
                name='Overcalls',
                skill_type=SkillType.BASIC_SKILL,
                level=6,
                description='Simple overcalls, jump overcalls (weak), 1NT overcall.',
                prerequisites=['takeout_double'],
                passing_accuracy=0.80,
                practice_hands_required=8
            ),
            SkillNode(
                id='responding_to_overcalls',
                name='Responding to Overcalls',
                skill_type=SkillType.BASIC_SKILL,
                level=6,
                description='Raising partner\'s overcall, new suit, cue-bid, NT.',
                prerequisites=['overcalls'],
                passing_accuracy=0.80,
                practice_hands_required=7
            ),
            SkillNode(
                id='negative_doubles',
                name='Negative Doubles',
                skill_type=SkillType.BASIC_SKILL,
                level=6,
                description='When partner opens and RHO overcalls, double for takeout.',
                prerequisites=['takeout_double'],
                passing_accuracy=0.80,
                practice_hands_required=8
            ),
            SkillNode(
                id='over_opponent_double',
                name='Over Opponent\'s Takeout Double',
                skill_type=SkillType.BASIC_SKILL,
                level=6,
                description='Redouble with 10+, raises, Jordan 2NT.',
                prerequisites=['takeout_double'],
                passing_accuracy=0.80,
                practice_hands_required=7
            ),
            SkillNode(
                id='balancing',
                name='Balancing',
                skill_type=SkillType.BASIC_SKILL,
                level=6,
                description='Reopening light when opponents stop low.',
                prerequisites=['overcalls'],
                passing_accuracy=0.80,
                practice_hands_required=5
            ),
        ],
        'unlock_message': 'Level 6 Unlocked! Master competitive bidding situations.'
    },

    # ========================================================================
    # LEVEL 7: INTERMEDIATE CONVENTIONS
    # "More tools for specific situations"
    # ========================================================================
    'level_7_intermediate_conventions': {
        'name': 'Level 7: Intermediate Conventions',
        'description': 'Important conventions for competitive and slam bidding',
        'level': 7,
        'type': SkillType.CONVENTION_GROUP,
        'unlock_requirement': 'Complete Level 6 Competitive Bidding',
        'completion_requirement': 'Master all 5 conventions with 80%+ accuracy',
        'conventions': [
            'blackwood',
            'michaels_cuebid',
            'unusual_2nt',
            'preempts',          # 3-level and 4-level openings
            'strong_2c'          # Strong 2C sequences
        ],
        'unlock_message': 'Level 7 Unlocked! Add powerful intermediate conventions to your toolkit.'
    },

    # ========================================================================
    # LEVEL 8: ADVANCED CONVENTIONS
    # "Expert tools for nuanced situations"
    # ========================================================================
    'level_8_advanced_conventions': {
        'name': 'Level 8: Advanced Conventions',
        'description': 'Expert-level conventions for sophisticated bidding',
        'level': 8,
        'type': SkillType.CONVENTION_GROUP,
        'unlock_requirement': 'Complete Level 7 Intermediate Conventions',
        'completion_requirement': 'Master all 7 conventions with 85%+ accuracy',
        'conventions': [
            'fourth_suit_forcing',
            'splinter_bids',
            'new_minor_forcing',
            'responsive_double',
            'lebensohl',
            'gerber',
            'control_cuebidding'  # Slam exploration
        ],
        'unlock_message': 'Level 8 Unlocked! Master advanced conventions to complete your SAYC education.'
    },
}


# ============================================================================
# SKILL TREE MANAGER
# ============================================================================

class SkillTreeManager:
    """
    Manages the skill tree and user progression through it.
    Works in conjunction with ConventionRegistry.
    """

    def __init__(self):
        self.tree = SKILL_TREE

    def get_level(self, level_id: str) -> Optional[Dict]:
        """Get a specific level from the skill tree"""
        return self.tree.get(level_id)

    def get_all_levels(self) -> Dict:
        """Get the complete skill tree as JSON-serializable dict"""
        result = {}
        for level_id, level_data in self.tree.items():
            level_dict = {
                'name': level_data['name'],
                'description': level_data['description'],
                'level': level_data['level'],
                'unlock_requirement': level_data.get('unlock_requirement', ''),
                'completion_requirement': level_data.get('completion_requirement', ''),
            }

            # Handle convention groups
            if 'conventions' in level_data:
                level_dict['type'] = 'convention_group'
                level_dict['conventions'] = level_data['conventions']
                level_dict['unlock_message'] = level_data.get('unlock_message', '')

            # Handle skill groups - convert SkillNode objects to dicts
            if 'skills' in level_data:
                level_dict['type'] = 'skill_group'
                level_dict['skills'] = [
                    skill.to_dict() if hasattr(skill, 'to_dict') else skill
                    for skill in level_data['skills']
                ]
                level_dict['unlock_message'] = level_data.get('unlock_message', '')

            result[level_id] = level_dict

        return result

    def get_level_by_number(self, level_num: int) -> Optional[Dict]:
        """Get level by number (0-8)"""
        for level_id, level_data in self.tree.items():
            if level_data['level'] == level_num:
                return level_data
        return None

    def get_level_id_by_number(self, level_num: int) -> Optional[str]:
        """Get level ID by number (0-8)"""
        for level_id, level_data in self.tree.items():
            if level_data['level'] == level_num:
                return level_id
        return None

    def get_skills_for_level(self, level_id: str) -> List[SkillNode]:
        """Get all skill nodes for a level"""
        level = self.get_level(level_id)
        if not level:
            return []
        return level.get('skills', [])

    def get_conventions_for_level(self, level_id: str) -> List[str]:
        """Get convention IDs for a convention group level"""
        level = self.get_level(level_id)
        if not level:
            return []
        return level.get('conventions', [])

    def check_level_unlocked(self, level_id: str, user_progress: Dict) -> bool:
        """
        Check if a level is unlocked for the user.

        Args:
            level_id: Level to check
            user_progress: Dictionary with user's completed skills and conventions

        Returns:
            True if level is unlocked
        """
        level = self.get_level(level_id)
        if not level:
            return False

        # Level 0 always unlocked
        if level['level'] == 0:
            return True

        # Find previous level
        prev_level_num = level['level'] - 1
        prev_level_id = self.get_level_id_by_number(prev_level_num)
        prev_level = self.get_level(prev_level_id)

        if not prev_level:
            return False

        # Check if previous level is completed
        if 'conventions' in prev_level:
            # Convention group - check all conventions mastered
            conventions = prev_level.get('conventions', [])
            mastered = user_progress.get('mastered_conventions', [])
            return all(conv_id in mastered for conv_id in conventions)
        else:
            # Skill group - check all skills completed
            skills = prev_level.get('skills', [])
            completed = user_progress.get('completed_skills', [])
            return all(skill.id in completed for skill in skills)

    def get_user_skill_tree_progress(self, user_progress: Dict) -> Dict:
        """
        Get detailed progress for all levels.

        Args:
            user_progress: Dict with 'completed_skills' and 'mastered_conventions'

        Returns:
            Progress summary for each level
        """
        progress = {}

        for level_id, level_data in self.tree.items():
            level_num = level_data['level']

            # Check if unlocked
            unlocked = self.check_level_unlocked(level_id, user_progress)

            # Calculate completion
            if 'conventions' in level_data:
                # Convention group
                conventions = level_data.get('conventions', [])
                mastered = user_progress.get('mastered_conventions', [])
                total = len(conventions)
                completed = sum(1 for c in conventions if c in mastered)
                is_convention_group = True
            else:
                # Skill group
                skills = level_data.get('skills', [])
                completed_skills = user_progress.get('completed_skills', [])
                total = len(skills)
                completed = sum(1 for s in skills if s.id in completed_skills)
                is_convention_group = False

            progress[level_id] = {
                'level_number': level_num,
                'name': level_data['name'],
                'unlocked': unlocked,
                'total': total,
                'completed': completed,
                'percentage': round((completed / total * 100) if total > 0 else 0, 1),
                'is_convention_group': is_convention_group
            }

        return progress

    def get_next_recommended_level(self, user_progress: Dict) -> Optional[str]:
        """
        Get the next level user should work on.

        Args:
            user_progress: User's progress data

        Returns:
            Level ID or None if all complete
        """
        # Check levels in order (0-8)
        for level_num in range(9):
            level_id = self.get_level_id_by_number(level_num)
            if not level_id:
                continue

            level_progress = self.get_user_skill_tree_progress(user_progress).get(level_id)

            if not level_progress:
                continue

            # If unlocked but not completed, recommend it
            if level_progress['unlocked'] and level_progress['completed'] < level_progress['total']:
                return level_id

        return None

    def get_total_hands_for_level(self, level_id: str) -> int:
        """Get total practice hands required for a level"""
        level = self.get_level(level_id)
        if not level:
            return 0

        if 'skills' in level:
            return sum(skill.practice_hands_required for skill in level['skills'])
        elif 'conventions' in level:
            # Convention levels have 10 hands per convention
            return len(level['conventions']) * 10

        return 0

    def get_curriculum_summary(self) -> Dict:
        """Get summary of entire curriculum"""
        summary = {
            'total_levels': len(self.tree),
            'levels': [],
            'total_hands': 0
        }

        for level_id, level_data in self.tree.items():
            hands = self.get_total_hands_for_level(level_id)
            summary['total_hands'] += hands

            level_info = {
                'id': level_id,
                'number': level_data['level'],
                'name': level_data['name'],
                'hands_required': hands,
                'is_convention_group': 'conventions' in level_data
            }

            if 'skills' in level_data:
                level_info['topics'] = len(level_data['skills'])
            elif 'conventions' in level_data:
                level_info['conventions'] = len(level_data['conventions'])

            summary['levels'].append(level_info)

        return summary


def get_skill_tree_manager() -> SkillTreeManager:
    """Get singleton instance of SkillTreeManager"""
    return SkillTreeManager()

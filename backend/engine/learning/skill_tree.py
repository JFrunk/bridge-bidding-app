"""
Skill Tree for Structured Bridge Learning

Defines the complete learning path from beginner to expert, integrating:
- Basic skills (opening bids, responses, rebids, etc.)
- Convention groups (essential, intermediate, advanced)
- Prerequisites and unlock requirements

Works with ConventionRegistry for hybrid metadata approach.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class SkillType(Enum):
    """Type of skill node in the tree"""
    BASIC_SKILL = "basic_skill"      # Fundamental bidding skill
    CONVENTION = "convention"         # Single convention
    CONVENTION_GROUP = "convention_group"  # Group of related conventions
    PRACTICE_MODE = "practice_mode"   # Special practice modes


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


# ============================================================================
# SKILL TREE DEFINITION
# ============================================================================

SKILL_TREE = {
    # ========================================================================
    # LEVEL 1: FOUNDATIONS
    # ========================================================================
    'level_1_foundations': {
        'name': 'Level 1: Foundations',
        'description': 'Essential building blocks of bridge bidding',
        'level': 1,
        'unlock_requirement': 'Available from start',
        'completion_requirement': 'Complete all skills with 80%+ accuracy',
        'skills': [
            SkillNode(
                id='opening_bids_basic',
                name='Basic Opening Bids',
                skill_type=SkillType.BASIC_SKILL,
                level=1,
                description='Learn to open the bidding with 1-level suit bids. '
                           'Understand 13+ HCP requirement, 5-card major system, and suit quality.',
                prerequisites=[],
                passing_accuracy=0.80,
                practice_hands_required=10
            ),
            SkillNode(
                id='basic_responses',
                name='Basic Responses (6-9 HCP)',
                skill_type=SkillType.BASIC_SKILL,
                level=1,
                description='Respond to partner\'s opening with minimum hands. '
                           'Simple raises, new suit bids, and 1NT response.',
                prerequisites=['opening_bids_basic'],
                passing_accuracy=0.80,
                practice_hands_required=10
            ),
            SkillNode(
                id='1nt_opening',
                name='1NT Opening (15-17 HCP)',
                skill_type=SkillType.BASIC_SKILL,
                level=1,
                description='Open 1NT with balanced hands and 15-17 HCP. '
                           'Understand balanced distribution requirements.',
                prerequisites=['opening_bids_basic'],
                passing_accuracy=0.80,
                practice_hands_required=8
            ),
            SkillNode(
                id='simple_rebids',
                name='Simple Rebids',
                skill_type=SkillType.BASIC_SKILL,
                level=1,
                description='Opener\'s second bid showing minimum vs. extra strength. '
                           'Rebidding your suit, showing second suit, or raising partner.',
                prerequisites=['opening_bids_basic', 'basic_responses'],
                passing_accuracy=0.80,
                practice_hands_required=12
            ),
            SkillNode(
                id='overcalls',
                name='Simple Overcalls',
                skill_type=SkillType.BASIC_SKILL,
                level=1,
                description='Bid over opponent\'s opening with 8-16 HCP and good 5-card suit. '
                           'Understand suit quality and vulnerability considerations.',
                prerequisites=['opening_bids_basic'],
                passing_accuracy=0.80,
                practice_hands_required=10
            ),
        ]
    },

    # ========================================================================
    # LEVEL 2: ESSENTIAL CONVENTIONS
    # ========================================================================
    'level_2_essential_conventions': {
        'name': 'Level 2: Essential Conventions',
        'description': 'Must-learn conventions for every bridge player',
        'level': 2,
        'type': SkillType.CONVENTION_GROUP,
        'unlock_requirement': 'Complete Level 1 Foundations',
        'completion_requirement': 'Master all 4 conventions with 80%+ accuracy',
        'conventions': [
            'stayman',            # References ConventionRegistry
            'jacoby_transfers',
            'weak_two',
            'takeout_double'
        ],
        'unlock_message': '🎉 Level 2 Unlocked! You\'ve mastered the foundations. '
                         'Time to learn essential conventions that every bridge player uses.'
    },

    # ========================================================================
    # LEVEL 3: INTERMEDIATE BIDDING
    # ========================================================================
    'level_3_intermediate_bidding': {
        'name': 'Level 3: Intermediate Bidding',
        'description': 'Advanced bidding skills and game forcing sequences',
        'level': 3,
        'unlock_requirement': 'Complete Level 2 Essential Conventions',
        'completion_requirement': 'Complete all skills with 80%+ accuracy',
        'skills': [
            SkillNode(
                id='game_bidding',
                name='Game Bidding',
                skill_type=SkillType.BASIC_SKILL,
                level=3,
                description='Recognize when to bid games (3NT, 4♥, 4♠, 5♣, 5♦). '
                           'Understand combined points needed for game contracts.',
                prerequisites=['simple_rebids', 'basic_responses'],
                passing_accuracy=0.80,
                practice_hands_required=15
            ),
            SkillNode(
                id='invitational_bidding',
                name='Invitational Bidding (10-12 HCP)',
                skill_type=SkillType.BASIC_SKILL,
                level=3,
                description='Make invitational bids showing 10-12 HCP. '
                           'Jump raises, 2NT responses, and invitational rebids.',
                prerequisites=['game_bidding'],
                passing_accuracy=0.80,
                practice_hands_required=12
            ),
            SkillNode(
                id='rebids',
                name='Intermediate Rebids',
                skill_type=SkillType.BASIC_SKILL,
                level=3,
                description='Advanced rebidding including jump rebids, reverse bids, '
                           'and fourth suit forcing situations.',
                prerequisites=['simple_rebids', 'game_bidding'],
                passing_accuracy=0.80,
                practice_hands_required=15
            ),
        ]
    },

    # ========================================================================
    # LEVEL 4: INTERMEDIATE CONVENTIONS
    # ========================================================================
    'level_4_intermediate_conventions': {
        'name': 'Level 4: Intermediate Conventions',
        'description': 'Important conventions for competitive and slam bidding',
        'level': 4,
        'type': SkillType.CONVENTION_GROUP,
        'unlock_requirement': 'Master all Essential Conventions (Level 2)',
        'completion_requirement': 'Master all 5 conventions with 80%+ accuracy',
        'conventions': [
            'blackwood',
            'negative_double',
            'michaels_cuebid',
            'unusual_2nt',
            'strong_2c'
        ],
        'unlock_message': '🎯 Level 4 Unlocked! You\'ve mastered essential conventions. '
                         'Now learn powerful intermediate tools for competitive play.'
    },

    # ========================================================================
    # LEVEL 5: ADVANCED BIDDING
    # ========================================================================
    'level_5_advanced_bidding': {
        'name': 'Level 5: Advanced Bidding',
        'description': 'Sophisticated bidding sequences and slam exploration',
        'level': 5,
        'unlock_requirement': 'Complete Level 4 Intermediate Conventions',
        'completion_requirement': 'Complete all skills with 85%+ accuracy',
        'skills': [
            SkillNode(
                id='slam_bidding',
                name='Slam Bidding',
                skill_type=SkillType.BASIC_SKILL,
                level=5,
                description='Recognize slam-going hands (33+ combined points). '
                           'Use control-showing bids and Blackwood effectively.',
                prerequisites=['blackwood', 'game_bidding'],
                passing_accuracy=0.85,
                practice_hands_required=15
            ),
            SkillNode(
                id='competitive_bidding_advanced',
                name='Advanced Competitive Bidding',
                skill_type=SkillType.BASIC_SKILL,
                level=5,
                description='Sophisticated competitive decisions including sacrifice bidding, '
                           'penalty doubles, and law of total tricks.',
                prerequisites=['negative_double', 'takeout_double', 'overcalls'],
                passing_accuracy=0.85,
                practice_hands_required=18
            ),
            SkillNode(
                id='control_bidding',
                name='Control Bidding (Cuebids)',
                skill_type=SkillType.BASIC_SKILL,
                level=5,
                description='Show controls (aces and kings) in slam auctions. '
                           'Understand when and how to cuebid.',
                prerequisites=['slam_bidding', 'blackwood'],
                passing_accuracy=0.85,
                practice_hands_required=15
            ),
        ]
    },

    # ========================================================================
    # LEVEL 6: ADVANCED CONVENTIONS
    # ========================================================================
    'level_6_advanced_conventions': {
        'name': 'Level 6: Advanced Conventions',
        'description': 'Expert-level conventions for sophisticated bidding',
        'level': 6,
        'type': SkillType.CONVENTION_GROUP,
        'unlock_requirement': 'Master all Intermediate Conventions (Level 4)',
        'completion_requirement': 'Master all 6 conventions with 85%+ accuracy',
        'conventions': [
            'fourth_suit_forcing',
            'splinter_bids',
            'new_minor_forcing',
            'responsive_double',
            'lebensohl',
            'gerber'
        ],
        'unlock_message': '👑 Level 6 Unlocked! You\'ve reached expert territory. '
                         'Master these advanced conventions to complete your education.'
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
        """Get the complete skill tree"""
        return self.tree

    def get_level_by_number(self, level_num: int) -> Optional[Dict]:
        """Get level by number (1-6)"""
        level_id = f'level_{level_num}_{list(self.tree.keys())[level_num-1].split("_", 2)[2]}'
        return self.tree.get(level_id)

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

        # Level 1 always unlocked
        if level['level'] == 1:
            return True

        # Check previous level completion
        prev_level_num = level['level'] - 1
        prev_level_id = list(self.tree.keys())[prev_level_num - 1]
        prev_level = self.get_level(prev_level_id)

        if not prev_level:
            return False

        # Check if previous level is completed
        if prev_level.get('type') == SkillType.CONVENTION_GROUP:
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
            if level_data.get('type') == SkillType.CONVENTION_GROUP:
                # Convention group
                conventions = level_data.get('conventions', [])
                mastered = user_progress.get('mastered_conventions', [])
                total = len(conventions)
                completed = sum(1 for c in conventions if c in mastered)
            else:
                # Skill group
                skills = level_data.get('skills', [])
                completed_skills = user_progress.get('completed_skills', [])
                total = len(skills)
                completed = sum(1 for s in skills if s.id in completed_skills)

            progress[level_id] = {
                'level_number': level_num,
                'name': level_data['name'],
                'unlocked': unlocked,
                'total': total,
                'completed': completed,
                'percentage': round((completed / total * 100) if total > 0 else 0, 1),
                'is_convention_group': level_data.get('type') == SkillType.CONVENTION_GROUP
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
        for level_id, level_data in self.tree.items():
            level_progress = self.get_user_skill_tree_progress(user_progress).get(level_id)

            if not level_progress:
                continue

            # If unlocked but not completed, recommend it
            if level_progress['unlocked'] and level_progress['completed'] < level_progress['total']:
                return level_id

        return None


def get_skill_tree_manager() -> SkillTreeManager:
    """Get singleton instance of SkillTreeManager"""
    return SkillTreeManager()

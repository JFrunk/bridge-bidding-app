"""
Play Skill Tree for Structured Bridge Card Play Learning

Defines the complete declarer play learning path from beginner to expert (Levels 0-8):
- Level 0: Play Foundations (counting winners/losers, hand analysis)
- Level 1: Basic Techniques (leading, following suit, trumping)
- Level 2: Finessing (basic finesses, two-way finesses)
- Level 3: Suit Establishment (setting up long suits, ducking)
- Level 4: Trump Management (drawing trumps, ruffing losers)
- Level 5: Entry Management (transportation, preserving entries)
- Level 6: Card Combinations (common card combinations, percentages)
- Level 7: Timing & Planning (planning the play, timing decisions)
- Level 8: Advanced Techniques (endplays, squeezes, avoidance)

Note: Defense will be added as a separate track in a future phase.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class PlaySkillType(Enum):
    """Type of play skill node in the tree"""
    FOUNDATION = "foundation"           # Basic concepts before play
    TECHNIQUE = "technique"             # Core play technique
    ADVANCED = "advanced"               # Advanced play concepts
    TOPIC = "topic"                     # Learning topic within a level


@dataclass
class PlaySkillNode:
    """A node in the play skill tree"""
    id: str
    name: str
    skill_type: PlaySkillType
    level: int
    description: str
    prerequisites: List[str]  # List of skill IDs
    passing_accuracy: float
    practice_hands_required: int
    unlock_message: Optional[str] = None

    # Play-specific fields
    practice_format: str = "single_decision"  # single_decision, mini_hand, full_hand
    accepts_multiple_answers: bool = False    # Some plays are equally good

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
            'unlock_message': self.unlock_message,
            'practice_format': self.practice_format,
            'accepts_multiple_answers': self.accepts_multiple_answers,
            'track': 'play'  # Distinguish from bidding skills
        }


# ============================================================================
# PLAY SKILL TREE DEFINITION - Complete Declarer Play Curriculum (Levels 0-8)
# ============================================================================

PLAY_SKILL_TREE = {
    # ========================================================================
    # LEVEL 0: PLAY FOUNDATIONS
    # "Before you play, understand what you're working with"
    # ========================================================================
    'play_level_0_foundations': {
        'name': 'Level 0: Play Foundations',
        'description': 'Essential concepts before playing a hand',
        'level': 0,
        'track': 'play',
        'unlock_requirement': 'Available from start',
        'completion_requirement': 'Complete all topics with 80%+ accuracy',
        'skills': [
            PlaySkillNode(
                id='counting_winners',
                name='Counting Winners',
                skill_type=PlaySkillType.FOUNDATION,
                level=0,
                description='Count sure tricks in NT contracts. '
                           'Aces, Kings with support, and established cards are winners.',
                prerequisites=[],
                passing_accuracy=0.80,
                practice_hands_required=5,
                practice_format='single_decision'
            ),
            PlaySkillNode(
                id='counting_losers',
                name='Counting Losers',
                skill_type=PlaySkillType.FOUNDATION,
                level=0,
                description='Count losers in suit contracts. '
                           'Focus on the first 3 cards of each suit in declarer hand.',
                prerequisites=['counting_winners'],
                passing_accuracy=0.80,
                practice_hands_required=5,
                practice_format='single_decision'
            ),
            PlaySkillNode(
                id='analyzing_the_lead',
                name='Analyzing the Lead',
                skill_type=PlaySkillType.FOUNDATION,
                level=0,
                description='Understand what the opening lead tells you. '
                           'Standard leads: 4th best, top of sequence, top of nothing.',
                prerequisites=['counting_winners'],
                passing_accuracy=0.80,
                practice_hands_required=5,
                practice_format='single_decision'
            ),
        ],
        'unlock_message': 'Welcome to card play! Let\'s start by learning to analyze your hand.'
    },

    # ========================================================================
    # LEVEL 1: BASIC TECHNIQUES
    # "The fundamental mechanics of play"
    # ========================================================================
    'play_level_1_basic_techniques': {
        'name': 'Level 1: Basic Techniques',
        'description': 'Fundamental card play mechanics',
        'level': 1,
        'track': 'play',
        'unlock_requirement': 'Complete Level 0 Play Foundations',
        'completion_requirement': 'Complete all topics with 80%+ accuracy',
        'skills': [
            PlaySkillNode(
                id='leading_to_tricks',
                name='Leading to Tricks',
                skill_type=PlaySkillType.TECHNIQUE,
                level=1,
                description='Which card to lead from various holdings. '
                           'Lead toward high cards, not away from them.',
                prerequisites=['counting_winners'],
                passing_accuracy=0.80,
                practice_hands_required=6,
                practice_format='single_decision'
            ),
            PlaySkillNode(
                id='second_hand_low',
                name='Second Hand Low',
                skill_type=PlaySkillType.TECHNIQUE,
                level=1,
                description='Usually play low in second seat. '
                           'Save high cards to capture opponent\'s honors.',
                prerequisites=['leading_to_tricks'],
                passing_accuracy=0.80,
                practice_hands_required=5,
                practice_format='single_decision',
                accepts_multiple_answers=True
            ),
            PlaySkillNode(
                id='third_hand_high',
                name='Third Hand High',
                skill_type=PlaySkillType.TECHNIQUE,
                level=1,
                description='Play high in third seat to win or force a higher card. '
                           'But only as high as necessary.',
                prerequisites=['leading_to_tricks'],
                passing_accuracy=0.80,
                practice_hands_required=5,
                practice_format='single_decision'
            ),
            PlaySkillNode(
                id='winning_cheaply',
                name='Winning Cheaply',
                skill_type=PlaySkillType.TECHNIQUE,
                level=1,
                description='Win tricks with the cheapest card possible. '
                           'Preserve high cards for later.',
                prerequisites=['third_hand_high'],
                passing_accuracy=0.80,
                practice_hands_required=5,
                practice_format='single_decision'
            ),
        ],
        'unlock_message': 'Level 1 Unlocked! Learn the basic mechanics of playing cards.'
    },

    # ========================================================================
    # LEVEL 2: FINESSING
    # "The most common technique to create extra tricks"
    # ========================================================================
    'play_level_2_finessing': {
        'name': 'Level 2: Finessing',
        'description': 'Master the finesse - the most common play technique',
        'level': 2,
        'track': 'play',
        'unlock_requirement': 'Complete Level 1 Basic Techniques',
        'completion_requirement': 'Complete all topics with 80%+ accuracy',
        'skills': [
            PlaySkillNode(
                id='simple_finesse',
                name='Simple Finesse',
                skill_type=PlaySkillType.TECHNIQUE,
                level=2,
                description='Lead toward a high card hoping the higher honor is on your left. '
                           'AQ opposite xx: lead low to the Q.',
                prerequisites=['leading_to_tricks'],
                passing_accuracy=0.80,
                practice_hands_required=6,
                practice_format='single_decision'
            ),
            PlaySkillNode(
                id='double_finesse',
                name='Double Finesse',
                skill_type=PlaySkillType.TECHNIQUE,
                level=2,
                description='Finesse twice when missing two honors. '
                           'AQJ opposite xxx: finesse twice for two tricks.',
                prerequisites=['simple_finesse'],
                passing_accuracy=0.80,
                practice_hands_required=5,
                practice_format='single_decision'
            ),
            PlaySkillNode(
                id='two_way_finesse',
                name='Two-Way Finesse',
                skill_type=PlaySkillType.TECHNIQUE,
                level=2,
                description='AJx opposite Kxx - finesse either way. '
                           'Look for clues from bidding or play.',
                prerequisites=['simple_finesse'],
                passing_accuracy=0.75,
                practice_hands_required=5,
                practice_format='single_decision',
                accepts_multiple_answers=True
            ),
            PlaySkillNode(
                id='finesse_or_drop',
                name='Finesse or Drop?',
                skill_type=PlaySkillType.TECHNIQUE,
                level=2,
                description='When to finesse vs. play for the drop. '
                           'With 9+ cards, play for the drop.',
                prerequisites=['simple_finesse'],
                passing_accuracy=0.75,
                practice_hands_required=5,
                practice_format='single_decision'
            ),
        ],
        'unlock_message': 'Level 2 Unlocked! Master the finesse to win extra tricks.'
    },

    # ========================================================================
    # LEVEL 3: SUIT ESTABLISHMENT
    # "Turning small cards into winners"
    # ========================================================================
    'play_level_3_suit_establishment': {
        'name': 'Level 3: Suit Establishment',
        'description': 'Set up long suits to create extra winners',
        'level': 3,
        'track': 'play',
        'unlock_requirement': 'Complete Level 2 Finessing',
        'completion_requirement': 'Complete all topics with 80%+ accuracy',
        'skills': [
            PlaySkillNode(
                id='establishing_long_suits',
                name='Establishing Long Suits',
                skill_type=PlaySkillType.TECHNIQUE,
                level=3,
                description='Drive out enemy high cards to establish small cards as winners. '
                           'Count how many times you need to lose the lead.',
                prerequisites=['counting_winners'],
                passing_accuracy=0.80,
                practice_hands_required=6,
                practice_format='mini_hand'
            ),
            PlaySkillNode(
                id='ducking_plays',
                name='Ducking Plays',
                skill_type=PlaySkillType.TECHNIQUE,
                level=3,
                description='Lose early to preserve entries. '
                           'Axxxx opposite xx: duck twice, win third round.',
                prerequisites=['establishing_long_suits'],
                passing_accuracy=0.80,
                practice_hands_required=5,
                practice_format='mini_hand'
            ),
            PlaySkillNode(
                id='hold_up_plays',
                name='Hold-Up Plays',
                skill_type=PlaySkillType.TECHNIQUE,
                level=3,
                description='Don\'t win the first trick to break enemy communications. '
                           'Classic NT play against a long suit lead.',
                prerequisites=['analyzing_the_lead'],
                passing_accuracy=0.80,
                practice_hands_required=5,
                practice_format='mini_hand'
            ),
            PlaySkillNode(
                id='which_suit_to_establish',
                name='Which Suit to Establish',
                skill_type=PlaySkillType.TECHNIQUE,
                level=3,
                description='Choose the best suit to develop based on length, '
                           'number of losers, and entry considerations.',
                prerequisites=['establishing_long_suits', 'ducking_plays'],
                passing_accuracy=0.75,
                practice_hands_required=5,
                practice_format='single_decision'
            ),
        ],
        'unlock_message': 'Level 3 Unlocked! Learn to establish long suits for extra winners.'
    },

    # ========================================================================
    # LEVEL 4: TRUMP MANAGEMENT
    # "Using trumps effectively"
    # ========================================================================
    'play_level_4_trump_management': {
        'name': 'Level 4: Trump Management',
        'description': 'Master trump play in suit contracts',
        'level': 4,
        'track': 'play',
        'unlock_requirement': 'Complete Level 3 Suit Establishment',
        'completion_requirement': 'Complete all topics with 80%+ accuracy',
        'skills': [
            PlaySkillNode(
                id='drawing_trumps',
                name='Drawing Trumps',
                skill_type=PlaySkillType.TECHNIQUE,
                level=4,
                description='When to draw trumps immediately vs. delay. '
                           'Count opponent\'s trumps, draw when safe.',
                prerequisites=['counting_losers'],
                passing_accuracy=0.80,
                practice_hands_required=6,
                practice_format='single_decision'
            ),
            PlaySkillNode(
                id='ruffing_losers',
                name='Ruffing Losers',
                skill_type=PlaySkillType.TECHNIQUE,
                level=4,
                description='Use dummy\'s trumps to ruff your losers. '
                           'Ruff in the short hand, not the long hand.',
                prerequisites=['drawing_trumps'],
                passing_accuracy=0.80,
                practice_hands_required=6,
                practice_format='mini_hand'
            ),
            PlaySkillNode(
                id='trump_control',
                name='Trump Control',
                skill_type=PlaySkillType.TECHNIQUE,
                level=4,
                description='Maintain control when opponents force you to ruff. '
                           'Sometimes refuse to ruff.',
                prerequisites=['drawing_trumps'],
                passing_accuracy=0.75,
                practice_hands_required=5,
                practice_format='mini_hand'
            ),
            PlaySkillNode(
                id='crossruff',
                name='The Crossruff',
                skill_type=PlaySkillType.TECHNIQUE,
                level=4,
                description='Ruff back and forth between hands. '
                           'Cash side suit winners first!',
                prerequisites=['ruffing_losers'],
                passing_accuracy=0.80,
                practice_hands_required=5,
                practice_format='mini_hand'
            ),
        ],
        'unlock_message': 'Level 4 Unlocked! Master trump management in suit contracts.'
    },

    # ========================================================================
    # LEVEL 5: ENTRY MANAGEMENT
    # "Getting to where you need to be"
    # ========================================================================
    'play_level_5_entry_management': {
        'name': 'Level 5: Entry Management',
        'description': 'Master transportation between hands',
        'level': 5,
        'track': 'play',
        'unlock_requirement': 'Complete Level 4 Trump Management',
        'completion_requirement': 'Complete all topics with 80%+ accuracy',
        'skills': [
            PlaySkillNode(
                id='preserving_entries',
                name='Preserving Entries',
                skill_type=PlaySkillType.TECHNIQUE,
                level=5,
                description='Keep entries to the hand where you need them. '
                           'Don\'t waste high cards unnecessarily.',
                prerequisites=['establishing_long_suits'],
                passing_accuracy=0.80,
                practice_hands_required=6,
                practice_format='mini_hand'
            ),
            PlaySkillNode(
                id='unblocking',
                name='Unblocking',
                skill_type=PlaySkillType.TECHNIQUE,
                level=5,
                description='Play high cards from short hand first. '
                           'KQ opposite Axxxx: play KQ first.',
                prerequisites=['preserving_entries'],
                passing_accuracy=0.80,
                practice_hands_required=5,
                practice_format='single_decision'
            ),
            PlaySkillNode(
                id='creating_entries',
                name='Creating Entries',
                skill_type=PlaySkillType.TECHNIQUE,
                level=5,
                description='Use finesses and ruffs to create entries. '
                           'The entry you need may not be obvious.',
                prerequisites=['preserving_entries', 'simple_finesse'],
                passing_accuracy=0.75,
                practice_hands_required=5,
                practice_format='mini_hand'
            ),
            PlaySkillNode(
                id='entry_killing_plays',
                name='Blocking Enemy Entries',
                skill_type=PlaySkillType.TECHNIQUE,
                level=5,
                description='Remove or block entries to opponents\' long suits. '
                           'The hold-up extends to entry management.',
                prerequisites=['hold_up_plays', 'preserving_entries'],
                passing_accuracy=0.75,
                practice_hands_required=4,
                practice_format='mini_hand'
            ),
        ],
        'unlock_message': 'Level 5 Unlocked! Master entry management for smooth play.'
    },

    # ========================================================================
    # LEVEL 6: CARD COMBINATIONS
    # "Know your odds"
    # ========================================================================
    'play_level_6_card_combinations': {
        'name': 'Level 6: Card Combinations',
        'description': 'Learn optimal play for common card combinations',
        'level': 6,
        'track': 'play',
        'unlock_requirement': 'Complete Level 5 Entry Management',
        'completion_requirement': 'Complete all topics with 80%+ accuracy',
        'skills': [
            PlaySkillNode(
                id='aq_combinations',
                name='AQ Combinations',
                skill_type=PlaySkillType.TECHNIQUE,
                level=6,
                description='Handling AQ, AQJ, AQ10 and similar holdings. '
                           'Lead toward the honors, finesse position matters.',
                prerequisites=['simple_finesse'],
                passing_accuracy=0.80,
                practice_hands_required=6,
                practice_format='single_decision'
            ),
            PlaySkillNode(
                id='kj_combinations',
                name='KJ Combinations',
                skill_type=PlaySkillType.TECHNIQUE,
                level=6,
                description='Handling KJ, KJ10 and similar holdings. '
                           'Lead toward the King first.',
                prerequisites=['simple_finesse'],
                passing_accuracy=0.80,
                practice_hands_required=5,
                practice_format='single_decision'
            ),
            PlaySkillNode(
                id='safety_plays',
                name='Safety Plays',
                skill_type=PlaySkillType.TECHNIQUE,
                level=6,
                description='Give up maximum tricks for guaranteed contract. '
                           'AKJ10x opposite xxxx: cash A first.',
                prerequisites=['finesse_or_drop'],
                passing_accuracy=0.75,
                practice_hands_required=5,
                practice_format='single_decision',
                accepts_multiple_answers=True
            ),
            PlaySkillNode(
                id='percentage_plays',
                name='Percentage Plays',
                skill_type=PlaySkillType.TECHNIQUE,
                level=6,
                description='Know the odds for common combinations. '
                           'Missing Q with 8 cards: finesse (52%) vs drop (48%).',
                prerequisites=['finesse_or_drop'],
                passing_accuracy=0.75,
                practice_hands_required=5,
                practice_format='single_decision'
            ),
        ],
        'unlock_message': 'Level 6 Unlocked! Learn optimal play for card combinations.'
    },

    # ========================================================================
    # LEVEL 7: TIMING & PLANNING
    # "Think before you play"
    # ========================================================================
    'play_level_7_timing_planning': {
        'name': 'Level 7: Timing & Planning',
        'description': 'Plan the entire hand before playing',
        'level': 7,
        'track': 'play',
        'unlock_requirement': 'Complete Level 6 Card Combinations',
        'completion_requirement': 'Complete all topics with 80%+ accuracy',
        'skills': [
            PlaySkillNode(
                id='planning_nt_contracts',
                name='Planning NT Contracts',
                skill_type=PlaySkillType.TECHNIQUE,
                level=7,
                description='Count winners, identify source of extra tricks, '
                           'plan order of play before touching a card.',
                prerequisites=['counting_winners', 'which_suit_to_establish'],
                passing_accuracy=0.80,
                practice_hands_required=6,
                practice_format='full_hand'
            ),
            PlaySkillNode(
                id='planning_suit_contracts',
                name='Planning Suit Contracts',
                skill_type=PlaySkillType.TECHNIQUE,
                level=7,
                description='Count losers, plan how to eliminate them. '
                           'Ruff, finesse, discard, or establish?',
                prerequisites=['counting_losers', 'ruffing_losers'],
                passing_accuracy=0.80,
                practice_hands_required=6,
                practice_format='full_hand'
            ),
            PlaySkillNode(
                id='timing_decisions',
                name='Timing Decisions',
                skill_type=PlaySkillType.ADVANCED,
                level=7,
                description='When to take finesses, when to draw trumps, '
                           'when to establish suits. Order matters!',
                prerequisites=['planning_nt_contracts', 'planning_suit_contracts'],
                passing_accuracy=0.75,
                practice_hands_required=5,
                practice_format='mini_hand'
            ),
            PlaySkillNode(
                id='danger_hand',
                name='The Danger Hand',
                skill_type=PlaySkillType.ADVANCED,
                level=7,
                description='Identify which opponent is dangerous and keep them off lead. '
                           'Take finesses into the safe hand.',
                prerequisites=['planning_nt_contracts'],
                passing_accuracy=0.75,
                practice_hands_required=5,
                practice_format='mini_hand'
            ),
        ],
        'unlock_message': 'Level 7 Unlocked! Learn to plan the entire hand before playing.'
    },

    # ========================================================================
    # LEVEL 8: ADVANCED TECHNIQUES
    # "Expert plays for difficult hands"
    # ========================================================================
    'play_level_8_advanced_techniques': {
        'name': 'Level 8: Advanced Techniques',
        'description': 'Master expert-level declarer play techniques',
        'level': 8,
        'track': 'play',
        'unlock_requirement': 'Complete Level 7 Timing & Planning',
        'completion_requirement': 'Complete all topics with 85%+ accuracy',
        'skills': [
            PlaySkillNode(
                id='elimination_play',
                name='Elimination Play',
                skill_type=PlaySkillType.ADVANCED,
                level=8,
                description='Strip side suits, then throw an opponent in. '
                           'They must help you or give a ruff-sluff.',
                prerequisites=['danger_hand'],
                passing_accuracy=0.80,
                practice_hands_required=5,
                practice_format='full_hand'
            ),
            PlaySkillNode(
                id='endplays',
                name='Endplays',
                skill_type=PlaySkillType.ADVANCED,
                level=8,
                description='Force opponent to lead to your advantage. '
                           'Exit cards, throw-in plays.',
                prerequisites=['elimination_play'],
                passing_accuracy=0.80,
                practice_hands_required=5,
                practice_format='full_hand'
            ),
            PlaySkillNode(
                id='simple_squeeze',
                name='Simple Squeeze',
                skill_type=PlaySkillType.ADVANCED,
                level=8,
                description='Force opponent to discard a winner. '
                           'Need: menace cards, entry, timing.',
                prerequisites=['endplays'],
                passing_accuracy=0.75,
                practice_hands_required=5,
                practice_format='full_hand'
            ),
            PlaySkillNode(
                id='avoidance_plays',
                name='Avoidance Plays',
                skill_type=PlaySkillType.ADVANCED,
                level=8,
                description='Techniques to keep dangerous opponent off lead. '
                           'Duck to safe hand, backward finesses.',
                prerequisites=['danger_hand'],
                passing_accuracy=0.80,
                practice_hands_required=5,
                practice_format='mini_hand'
            ),
            PlaySkillNode(
                id='deceptive_plays',
                name='Deceptive Plays',
                skill_type=PlaySkillType.ADVANCED,
                level=8,
                description='False cards and deceptive plays to confuse defenders. '
                           'Playing the card you\'re known to hold.',
                prerequisites=['timing_decisions'],
                passing_accuracy=0.75,
                practice_hands_required=4,
                practice_format='single_decision',
                accepts_multiple_answers=True
            ),
        ],
        'unlock_message': 'Level 8 Unlocked! Master advanced techniques for expert play.'
    },
}


# ============================================================================
# PLAY SKILL TREE MANAGER
# ============================================================================

class PlaySkillTreeManager:
    """
    Manages the play skill tree and user progression through it.
    Parallel structure to SkillTreeManager for bidding.
    """

    def __init__(self):
        self.tree = PLAY_SKILL_TREE

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
                'track': level_data.get('track', 'play'),
                'unlock_requirement': level_data.get('unlock_requirement', ''),
                'completion_requirement': level_data.get('completion_requirement', ''),
            }

            # Handle skill groups - convert PlaySkillNode objects to dicts
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

    def get_skills_for_level(self, level_id: str) -> List[PlaySkillNode]:
        """Get all skill nodes for a level"""
        level = self.get_level(level_id)
        if not level:
            return []
        return level.get('skills', [])

    def get_skill_by_id(self, skill_id: str) -> Optional[PlaySkillNode]:
        """Find a skill by its ID across all levels"""
        for level_id, level_data in self.tree.items():
            skills = level_data.get('skills', [])
            for skill in skills:
                if skill.id == skill_id:
                    return skill
        return None

    def check_level_unlocked(self, level_id: str, user_progress: Dict) -> bool:
        """
        Check if a level is unlocked for the user.

        Args:
            level_id: Level to check
            user_progress: Dictionary with user's completed play skills

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
        skills = prev_level.get('skills', [])
        completed = user_progress.get('completed_play_skills', [])
        return all(skill.id in completed for skill in skills)

    def get_user_skill_tree_progress(self, user_progress: Dict) -> Dict:
        """
        Get detailed progress for all levels.

        Args:
            user_progress: Dict with 'completed_play_skills'

        Returns:
            Progress summary for each level
        """
        progress = {}

        for level_id, level_data in self.tree.items():
            level_num = level_data['level']

            # Check if unlocked
            unlocked = self.check_level_unlocked(level_id, user_progress)

            # Calculate completion
            skills = level_data.get('skills', [])
            completed_skills = user_progress.get('completed_play_skills', [])
            total = len(skills)
            completed = sum(1 for s in skills if s.id in completed_skills)

            progress[level_id] = {
                'level_number': level_num,
                'name': level_data['name'],
                'track': 'play',
                'unlocked': unlocked,
                'total': total,
                'completed': completed,
                'percentage': round((completed / total * 100) if total > 0 else 0, 1)
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

        return 0

    def get_curriculum_summary(self) -> Dict:
        """Get summary of entire curriculum"""
        summary = {
            'track': 'play',
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
                'skills_count': len(level_data.get('skills', []))
            }

            summary['levels'].append(level_info)

        return summary


def get_play_skill_tree_manager() -> PlaySkillTreeManager:
    """Get singleton instance of PlaySkillTreeManager"""
    return PlaySkillTreeManager()

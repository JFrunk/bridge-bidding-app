"""
Convention Registry - Metadata and management for all bridge conventions.

This module provides a centralized registry for convention metadata including:
- Convention levels (Essential, Intermediate, Advanced)
- Prerequisites and dependencies
- Learning characteristics (frequency, complexity)
- Practice requirements

Part of the structured learning platform.
"""

from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass


class ConventionLevel(Enum):
    """Convention difficulty levels for structured learning"""
    ESSENTIAL = 1      # Must learn - fundamental conventions
    INTERMEDIATE = 2   # Should learn - important competitive tools
    ADVANCED = 3       # Expert tools - sophisticated techniques


class ConventionCategory(Enum):
    """Convention categories for organization"""
    NT_SYSTEM = "1NT System"
    COMPETITIVE = "Competitive Bidding"
    SLAM = "Slam Bidding"
    PREEMPTIVE = "Preemptive"
    FORCING = "Forcing Bids"
    STRONG_HANDS = "Strong Hands"


@dataclass
class ConventionMetadata:
    """Metadata for a single convention"""
    id: str
    name: str
    level: ConventionLevel
    category: ConventionCategory
    frequency: str  # "Very High", "High", "Medium", "Low"
    complexity: str  # "Low", "Medium", "High", "Very High"
    prerequisites: List[str]  # List of skill/convention IDs
    practice_hands_required: int
    passing_accuracy: float
    description: str
    short_description: str
    learning_time_minutes: int

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'level': self.level.name.lower(),
            'category': self.category.value,
            'frequency': self.frequency,
            'complexity': self.complexity,
            'prerequisites': self.prerequisites,
            'practice_hands_required': self.practice_hands_required,
            'passing_accuracy': self.passing_accuracy,
            'description': self.description,
            'short_description': self.short_description,
            'learning_time_minutes': self.learning_time_minutes
        }


# ============================================================================
# CONVENTION REGISTRY - All conventions with metadata
# ============================================================================

CONVENTION_REGISTRY = {
    # ========================================================================
    # LEVEL 1: ESSENTIAL CONVENTIONS (Must Learn)
    # ========================================================================

    'stayman': ConventionMetadata(
        id='stayman',
        name='Stayman',
        level=ConventionLevel.ESSENTIAL,
        category=ConventionCategory.NT_SYSTEM,
        frequency='Very High',
        complexity='Low',
        prerequisites=['1nt_opening'],
        practice_hands_required=10,
        passing_accuracy=0.80,
        description='2♣ bid after partner opens 1NT to ask for 4-card majors. '
                   'Opener responds 2♥ (4+ hearts), 2♠ (4+ spades), or 2♦ (no 4-card major). '
                   'Essential for finding 4-4 major suit fits.',
        short_description='2♣ asks for majors after 1NT',
        learning_time_minutes=15
    ),

    'jacoby_transfers': ConventionMetadata(
        id='jacoby_transfers',
        name='Jacoby Transfers',
        level=ConventionLevel.ESSENTIAL,
        category=ConventionCategory.NT_SYSTEM,
        frequency='Very High',
        complexity='Low',
        prerequisites=['1nt_opening'],
        practice_hands_required=10,
        passing_accuracy=0.80,
        description='2♦ transfers to hearts, 2♥ transfers to spades after 1NT opening. '
                   'Used with 5+ card major to make opener declarer. '
                   'Opener must accept the transfer except with super-maximum hands.',
        short_description='2♦→♥, 2♥→♠ after 1NT',
        learning_time_minutes=15
    ),

    'weak_two': ConventionMetadata(
        id='weak_two',
        name='Weak Two Bids',
        level=ConventionLevel.ESSENTIAL,
        category=ConventionCategory.PREEMPTIVE,
        frequency='High',
        complexity='Low',
        prerequisites=['opening_bids_basic'],
        practice_hands_required=8,
        passing_accuracy=0.80,
        description='Preemptive 2♥ or 2♠ opening showing 6-card suit with 5-10 HCP. '
                   'Good suit quality required (2 of top 3 honors). '
                   'Primarily obstructive, making it difficult for opponents to bid.',
        short_description='2♥/2♠ = weak 6-card suit',
        learning_time_minutes=12
    ),

    'takeout_double': ConventionMetadata(
        id='takeout_double',
        name='Takeout Doubles',
        level=ConventionLevel.ESSENTIAL,
        category=ConventionCategory.COMPETITIVE,
        frequency='High',
        complexity='Medium',
        prerequisites=['overcalls', 'opening_bids_basic'],
        practice_hands_required=12,
        passing_accuracy=0.80,
        description='Double of opponent\'s opening bid for takeout (not penalty). '
                   'Shows opening strength (13+ HCP) with support for unbid suits. '
                   'Typically shortness in opponent\'s suit. Partner must bid.',
        short_description='X for takeout, shows support for unbid suits',
        learning_time_minutes=20
    ),

    # ========================================================================
    # LEVEL 2: INTERMEDIATE CONVENTIONS (Should Learn)
    # ========================================================================

    'blackwood': ConventionMetadata(
        id='blackwood',
        name='Blackwood (4NT)',
        level=ConventionLevel.INTERMEDIATE,
        category=ConventionCategory.SLAM,
        frequency='Medium',
        complexity='Medium',
        prerequisites=['stayman', 'jacoby_transfers', 'game_bidding'],
        practice_hands_required=12,
        passing_accuracy=0.80,
        description='4NT asks for aces: 5♣=0/4, 5♦=1, 5♥=2, 5♠=3 aces. '
                   'After ace response, 5NT asks for kings (same pattern). '
                   'Use when considering slam and holding good trump suit.',
        short_description='4NT ace-ask for slam',
        learning_time_minutes=18
    ),

    'negative_double': ConventionMetadata(
        id='negative_double',
        name='Negative Doubles',
        level=ConventionLevel.INTERMEDIATE,
        category=ConventionCategory.COMPETITIVE,
        frequency='Medium',
        complexity='High',
        prerequisites=['takeout_double', 'overcalls'],
        practice_hands_required=15,
        passing_accuracy=0.80,
        description='Double after partner opens and opponent overcalls. '
                   'Shows 6+ HCP and typically 4 cards in unbid major(s). '
                   'Forcing for one round. Requires good judgment.',
        short_description='X after partner opens (shows unbid major)',
        learning_time_minutes=25
    ),

    'michaels_cuebid': ConventionMetadata(
        id='michaels_cuebid',
        name='Michaels Cuebid',
        level=ConventionLevel.INTERMEDIATE,
        category=ConventionCategory.COMPETITIVE,
        frequency='Medium',
        complexity='Medium',
        prerequisites=['overcalls', 'takeout_double'],
        practice_hands_required=12,
        passing_accuracy=0.80,
        description='Cuebid of opponent\'s suit shows 5-5 in two other suits. '
                   '2♣/2♦ over minor = both majors. '
                   '2♥/2♠ over major = other major + minor (ask with 2NT).',
        short_description='Cuebid = 5-5 two suits',
        learning_time_minutes=20
    ),

    'unusual_2nt': ConventionMetadata(
        id='unusual_2nt',
        name='Unusual 2NT',
        level=ConventionLevel.INTERMEDIATE,
        category=ConventionCategory.COMPETITIVE,
        frequency='Medium',
        complexity='Medium',
        prerequisites=['overcalls', 'michaels_cuebid'],
        practice_hands_required=12,
        passing_accuracy=0.80,
        description='Jump to 2NT over opponent\'s opening shows 5-5 in minors. '
                   'Typically 6-11 HCP (weak) or 17+ HCP (strong). '
                   'Partner picks better minor or may bid 3NT with stoppers.',
        short_description='2NT = both minors (5-5+)',
        learning_time_minutes=18
    ),

    'strong_2c': ConventionMetadata(
        id='strong_2c',
        name='Strong 2♣',
        level=ConventionLevel.INTERMEDIATE,
        category=ConventionCategory.STRONG_HANDS,
        frequency='Low',
        complexity='Medium',
        prerequisites=['opening_bids_basic', 'game_bidding'],
        practice_hands_required=10,
        passing_accuracy=0.80,
        description='2♣ opening shows 22+ HCP or game-forcing hand. '
                   'Responder bids 2♦ (waiting) or shows positive with 8+ HCP. '
                   'Only forcing opening in SAYC.',
        short_description='2♣ = 22+ HCP, game forcing',
        learning_time_minutes=15
    ),

    # ========================================================================
    # LEVEL 3: ADVANCED CONVENTIONS (Expert Tools)
    # ========================================================================

    'fourth_suit_forcing': ConventionMetadata(
        id='fourth_suit_forcing',
        name='Fourth Suit Forcing',
        level=ConventionLevel.ADVANCED,
        category=ConventionCategory.FORCING,
        frequency='Medium',
        complexity='High',
        prerequisites=['rebids', 'game_bidding', 'blackwood'],
        practice_hands_required=15,
        passing_accuracy=0.85,
        description='When three suits have been bid naturally, bidding the fourth suit '
                   'is artificial and forcing to game (or 3NT). '
                   'Shows game interest without clear direction. Asks opener to clarify hand.',
        short_description='4th suit = artificial, forcing to game',
        learning_time_minutes=30
    ),

    'splinter_bids': ConventionMetadata(
        id='splinter_bids',
        name='Splinter Bids',
        level=ConventionLevel.ADVANCED,
        category=ConventionCategory.SLAM,
        frequency='Low',
        complexity='High',
        prerequisites=['blackwood', 'slam_bidding', 'game_bidding'],
        practice_hands_required=15,
        passing_accuracy=0.85,
        description='Unusual jump in new suit shows singleton/void and 4+ card support. '
                   'Game-forcing and slam interest. '
                   'Example: 1♥-4♣ = club shortness, heart support, slam interest.',
        short_description='Unusual jump = shortness + support',
        learning_time_minutes=25
    ),

    'new_minor_forcing': ConventionMetadata(
        id='new_minor_forcing',
        name='New Minor Forcing',
        level=ConventionLevel.ADVANCED,
        category=ConventionCategory.FORCING,
        frequency='Medium',
        complexity='High',
        prerequisites=['rebids', 'stayman', 'fourth_suit_forcing'],
        practice_hands_required=18,
        passing_accuracy=0.85,
        description='After 1m-1M-1NT sequence, responder\'s 2♣ (or other minor) is forcing. '
                   'Shows 11+ HCP or 5+ card major seeking game. '
                   'Asks opener to show 3-card major support or clarify hand.',
        short_description='New minor after 1NT rebid = forcing',
        learning_time_minutes=30
    ),

    'responsive_double': ConventionMetadata(
        id='responsive_double',
        name='Responsive Doubles',
        level=ConventionLevel.ADVANCED,
        category=ConventionCategory.COMPETITIVE,
        frequency='Low',
        complexity='High',
        prerequisites=['negative_double', 'takeout_double'],
        practice_hands_required=15,
        passing_accuracy=0.85,
        description='Double after partner makes takeout double and RHO bids. '
                   'Shows values but no clear bid. '
                   'Asks partner to pick a suit. Typically 2-suited flexibility.',
        short_description='X after partner doubles (shows cards)',
        learning_time_minutes=28
    ),

    'lebensohl': ConventionMetadata(
        id='lebensohl',
        name='Lebensohl',
        level=ConventionLevel.ADVANCED,
        category=ConventionCategory.NT_SYSTEM,
        frequency='Low',
        complexity='Very High',
        prerequisites=['stayman', 'jacoby_transfers', 'negative_double'],
        practice_hands_required=20,
        passing_accuracy=0.85,
        description='Complex relay system after interference over 1NT opening. '
                   '2NT forces 3♣ relay, then: '
                   '- Direct 3-level = 8+ HCP with stopper. '
                   '- Via relay = 8+ HCP without stopper or weak signoff.',
        short_description='2NT relay after interference over 1NT',
        learning_time_minutes=35
    ),

    'gerber': ConventionMetadata(
        id='gerber',
        name='Gerber (4♣)',
        level=ConventionLevel.ADVANCED,
        category=ConventionCategory.SLAM,
        frequency='Low',
        complexity='Medium',
        prerequisites=['blackwood', 'slam_bidding'],
        practice_hands_required=12,
        passing_accuracy=0.85,
        description='4♣ asks for aces after notrump bids (similar to Blackwood). '
                   'Responses: 4♦=0/4, 4♥=1, 4♠=2, 4NT=3 aces. '
                   '5♣ then asks for kings. Use instead of 4NT when clubs is trump.',
        short_description='4♣ ace-ask after NT bids',
        learning_time_minutes=15
    ),
}


# ============================================================================
# CONVENTION REGISTRY MANAGER
# ============================================================================

class ConventionRegistry:
    """
    Manages convention metadata and learning progression.

    Provides methods to:
    - Query conventions by level, category, etc.
    - Check prerequisites and unlocking
    - Recommend next convention to learn
    - Track user progress
    """

    def __init__(self):
        self.conventions = CONVENTION_REGISTRY

    def get_convention(self, convention_id: str) -> Optional[ConventionMetadata]:
        """Get metadata for a specific convention"""
        return self.conventions.get(convention_id)

    def get_all_conventions(self) -> List[ConventionMetadata]:
        """Get all conventions"""
        return list(self.conventions.values())

    def get_by_level(self, level: ConventionLevel) -> List[ConventionMetadata]:
        """Get all conventions at a specific level"""
        return [c for c in self.conventions.values() if c.level == level]

    def get_essential_conventions(self) -> List[ConventionMetadata]:
        """Get all essential (must-learn) conventions"""
        return self.get_by_level(ConventionLevel.ESSENTIAL)

    def get_intermediate_conventions(self) -> List[ConventionMetadata]:
        """Get all intermediate conventions"""
        return self.get_by_level(ConventionLevel.INTERMEDIATE)

    def get_advanced_conventions(self) -> List[ConventionMetadata]:
        """Get all advanced conventions"""
        return self.get_by_level(ConventionLevel.ADVANCED)

    def get_by_category(self, category: ConventionCategory) -> List[ConventionMetadata]:
        """Get all conventions in a category"""
        return [c for c in self.conventions.values() if c.category == category]

    def check_prerequisites_met(self, convention_id: str,
                               completed_skills: List[str],
                               mastered_conventions: List[str]) -> bool:
        """
        Check if user has completed prerequisites for a convention.

        Args:
            convention_id: Convention to check
            completed_skills: List of skill IDs user has completed
            mastered_conventions: List of convention IDs user has mastered

        Returns:
            True if all prerequisites are met
        """
        convention = self.get_convention(convention_id)
        if not convention:
            return False

        # Check each prerequisite
        for prereq in convention.prerequisites:
            # Check if it's a skill or convention
            if prereq in completed_skills or prereq in mastered_conventions:
                continue
            else:
                return False

        return True

    def get_unlocked_conventions(self, completed_skills: List[str],
                                 mastered_conventions: List[str]) -> List[ConventionMetadata]:
        """
        Get conventions that are unlocked for the user.

        A convention is unlocked if:
        1. All its skill/convention prerequisites are met
        2. Level prerequisites are met:
           - Essential: Always available (if prereqs met)
           - Intermediate: All Essential conventions mastered
           - Advanced: All Intermediate conventions mastered

        Args:
            completed_skills: Skills user has completed
            mastered_conventions: Conventions user has mastered

        Returns:
            List of unlocked conventions
        """
        unlocked = []

        # Get IDs of essential and intermediate conventions
        essential_ids = [c.id for c in self.get_essential_conventions()]
        intermediate_ids = [c.id for c in self.get_intermediate_conventions()]

        for convention in self.conventions.values():
            # Skip if already mastered
            if convention.id in mastered_conventions:
                continue

            # Check skill/convention prerequisites
            if not self.check_prerequisites_met(convention.id, completed_skills,
                                               mastered_conventions):
                continue

            # Check level prerequisites
            if convention.level == ConventionLevel.INTERMEDIATE:
                # Must master all essential conventions first
                if not all(eid in mastered_conventions for eid in essential_ids):
                    continue

            elif convention.level == ConventionLevel.ADVANCED:
                # Must master all intermediate conventions first
                if not all(iid in mastered_conventions for iid in intermediate_ids):
                    continue

            unlocked.append(convention)

        return unlocked

    def get_next_recommended_convention(self, completed_skills: List[str],
                                       mastered_conventions: List[str]) -> Optional[ConventionMetadata]:
        """
        Get the next convention the user should learn.

        Prioritizes by:
        1. Level (Essential > Intermediate > Advanced)
        2. Frequency (Very High > High > Medium > Low)

        Args:
            completed_skills: Skills user has completed
            mastered_conventions: Conventions user has mastered

        Returns:
            Next recommended convention or None if all mastered
        """
        unlocked = self.get_unlocked_conventions(completed_skills, mastered_conventions)

        if not unlocked:
            return None

        # Priority mappings
        level_priority = {
            ConventionLevel.ESSENTIAL: 1,
            ConventionLevel.INTERMEDIATE: 2,
            ConventionLevel.ADVANCED: 3
        }

        frequency_priority = {
            'Very High': 1,
            'High': 2,
            'Medium': 3,
            'Low': 4
        }

        # Sort by level first, then frequency
        sorted_conventions = sorted(
            unlocked,
            key=lambda c: (level_priority[c.level], frequency_priority[c.frequency])
        )

        return sorted_conventions[0] if sorted_conventions else None

    def get_progress_summary(self, mastered_conventions: List[str]) -> Dict:
        """
        Get overall progress summary across all levels.

        Args:
            mastered_conventions: Conventions user has mastered

        Returns:
            Dictionary with progress for each level
        """
        essential = self.get_essential_conventions()
        intermediate = self.get_intermediate_conventions()
        advanced = self.get_advanced_conventions()

        return {
            'essential': {
                'total': len(essential),
                'mastered': sum(1 for c in essential if c.id in mastered_conventions),
                'ids': [c.id for c in essential]
            },
            'intermediate': {
                'total': len(intermediate),
                'mastered': sum(1 for c in intermediate if c.id in mastered_conventions),
                'ids': [c.id for c in intermediate]
            },
            'advanced': {
                'total': len(advanced),
                'mastered': sum(1 for c in advanced if c.id in mastered_conventions),
                'ids': [c.id for c in advanced]
            },
            'overall': {
                'total': len(self.conventions),
                'mastered': len(mastered_conventions),
                'percentage': round(len(mastered_conventions) / len(self.conventions) * 100, 1)
            }
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_convention_registry() -> ConventionRegistry:
    """Get singleton instance of ConventionRegistry"""
    return ConventionRegistry()


def get_convention_by_id(convention_id: str) -> Optional[ConventionMetadata]:
    """Convenience function to get convention metadata"""
    registry = get_convention_registry()
    return registry.get_convention(convention_id)

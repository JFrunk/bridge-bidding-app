# Convention Levels Implementation Plan

## Executive Summary

This document outlines a comprehensive plan to implement a **3-tier convention difficulty system** that integrates with the structured learning platform. Conventions will be categorized as **Essential**, **Intermediate**, and **Advanced**, guiding users through a progressive learning path.

---

## Table of Contents

1. [Convention Categorization](#convention-categorization)
2. [Implementation Options](#implementation-options)
3. [Database Schema](#database-schema)
4. [Integration with Learning Platform](#integration-with-learning-platform)
5. [Recommended Approach](#recommended-approach)
6. [Implementation Steps](#implementation-steps)
7. [UI/UX Design](#uiux-design)

---

## Convention Categorization

### Level 1: Essential Conventions (MUST LEARN)
**For:** Beginners who need core bidding tools
**Prerequisites:** Basic opening bids and responses
**Unlock:** Available from start or after completing "Basic Bidding" skill

```
Essential Conventions (4 conventions)
├── 1. Stayman
│   ├── Frequency: Very High (used ~30% of hands after 1NT)
│   ├── Complexity: Low (simple ask-and-answer)
│   ├── Value: Critical for finding 4-4 major fits
│   └── Prerequisites: Understanding 1NT openings
│
├── 2. Jacoby Transfers
│   ├── Frequency: Very High (used ~40% of hands after 1NT)
│   ├── Complexity: Low-Medium (transfer concept)
│   ├── Value: Essential for 5-card major play
│   └── Prerequisites: Understanding 1NT openings
│
├── 3. Weak Two Bids
│   ├── Frequency: High (preemptive situations)
│   ├── Complexity: Low (6-card suit, 5-10 HCP)
│   ├── Value: Competitive advantage
│   └── Prerequisites: Understanding suit quality
│
└── 4. Takeout Doubles
    ├── Frequency: High (competitive bidding)
    ├── Complexity: Medium (shape requirements)
    ├── Value: Critical for competitive bidding
    └── Prerequisites: Understanding overcalls
```

**Learning Path:**
1. Learn Stayman → 10 practice hands → 80% accuracy to pass
2. Learn Jacoby → 10 practice hands → 80% accuracy to pass
3. Learn Weak Twos → 8 practice hands → 80% accuracy to pass
4. Learn Takeout Doubles → 12 practice hands → 80% accuracy to pass

---

### Level 2: Intermediate Conventions (SHOULD LEARN)
**For:** Intermediate players ready for more tools
**Prerequisites:** Master all Essential conventions
**Unlock:** After achieving 80%+ accuracy in all Level 1 conventions

```
Intermediate Conventions (5 conventions)
├── 5. Blackwood (4NT)
│   ├── Frequency: Medium (slam situations)
│   ├── Complexity: Medium (ace-asking)
│   ├── Value: Important for slam bidding
│   └── Prerequisites: Understanding game bidding
│
├── 6. Negative Doubles
│   ├── Frequency: Medium (after overcalls)
│   ├── Complexity: Medium-High (requires judgment)
│   ├── Value: Flexible competitive tool
│   └── Prerequisites: Takeout doubles, overcalls
│
├── 7. Michaels Cuebid
│   ├── Frequency: Medium (two-suited hands)
│   ├── Complexity: Medium (showing two suits)
│   ├── Value: Competitive/preemptive power
│   └── Prerequisites: Overcalls, suit quality
│
├── 8. Unusual 2NT
│   ├── Frequency: Medium (minor two-suiters)
│   ├── Complexity: Medium (showing minors)
│   ├── Value: Competitive tool
│   └── Prerequisites: Overcalls, Michaels
│
└── 9. Strong 2♣
    ├── Frequency: Low (very strong hands)
    ├── Complexity: Medium (game-forcing)
    ├── Value: Essential for strong hands
    └── Prerequisites: Understanding forcing bids
```

**Learning Path:**
1. Must complete ALL Essential conventions
2. Can learn in any order, but recommended sequence shown above
3. Each requires 12-15 practice hands at 80% accuracy

---

### Level 3: Advanced Conventions (EXPERT TOOLS)
**For:** Advanced players seeking expert techniques
**Prerequisites:** Master all Intermediate conventions
**Unlock:** After achieving 85%+ accuracy in all Level 2 conventions

```
Advanced Conventions (6 conventions)
├── 10. Fourth Suit Forcing
│   ├── Frequency: Medium (partnership auctions)
│   ├── Complexity: High (forcing to game)
│   ├── Value: Sophisticated bidding tool
│   └── Prerequisites: Rebids, game forcing
│
├── 11. Splinter Bids
│   ├── Frequency: Low (slam exploration)
│   ├── Complexity: High (shortness showing)
│   ├── Value: Slam bidding accuracy
│   └── Prerequisites: Slam bidding, control showing
│
├── 12. New Minor Forcing
│   ├── Frequency: Medium (after 1NT rebid)
│   ├── Complexity: High (artificial forcing)
│   ├── Value: Finding best contract
│   └── Prerequisites: Opener rebids
│
├── 13. Responsive Doubles
│   ├── Frequency: Low-Medium (competitive)
│   ├── Complexity: High (competitive judgment)
│   ├── Value: Advanced competitive tool
│   └── Prerequisites: Negative doubles, takeout doubles
│
├── 14. Lebensohl
│   ├── Frequency: Low (after interference over 1NT)
│   ├── Complexity: Very High (complex relay)
│   ├── Value: Precision after interference
│   └── Prerequisites: Stayman, transfers
│
└── 15. Gerber (4♣ ace-ask)
    ├── Frequency: Low (slam after NT)
    ├── Complexity: Medium (similar to Blackwood)
    ├── Value: Alternative ace-asking
    └── Prerequisites: Blackwood
```

**Learning Path:**
1. Must complete ALL Intermediate conventions
2. Recommended to learn in sequence (increasing complexity)
3. Each requires 15-20 practice hands at 85% accuracy

---

## Implementation Options

### Option 1: Convention Metadata System (RECOMMENDED)

**Overview:** Add metadata to each convention defining its level, prerequisites, and learning characteristics.

**Implementation:**

```python
# backend/engine/ai/conventions/convention_registry.py

from typing import Dict, List, Optional
from enum import Enum

class ConventionLevel(Enum):
    ESSENTIAL = 1      # Must learn
    INTERMEDIATE = 2   # Should learn
    ADVANCED = 3       # Expert tools

class ConventionCategory(Enum):
    NT_SYSTEM = "1NT System"
    COMPETITIVE = "Competitive Bidding"
    SLAM = "Slam Bidding"
    PREEMPTIVE = "Preemptive"
    FORCING = "Forcing Bids"

class ConventionMetadata:
    def __init__(
        self,
        id: str,
        name: str,
        level: ConventionLevel,
        category: ConventionCategory,
        frequency: str,  # "Very High", "High", "Medium", "Low"
        complexity: str,  # "Low", "Medium", "High", "Very High"
        prerequisites: List[str],  # List of convention IDs
        practice_hands_required: int,
        passing_accuracy: float,
        description: str,
        short_description: str,
        learning_time_minutes: int
    ):
        self.id = id
        self.name = name
        self.level = level
        self.category = category
        self.frequency = frequency
        self.complexity = complexity
        self.prerequisites = prerequisites
        self.practice_hands_required = practice_hands_required
        self.passing_accuracy = passing_accuracy
        self.description = description
        self.short_description = short_description
        self.learning_time_minutes = learning_time_minutes

# Convention Registry
CONVENTION_REGISTRY = {
    'stayman': ConventionMetadata(
        id='stayman',
        name='Stayman',
        level=ConventionLevel.ESSENTIAL,
        category=ConventionCategory.NT_SYSTEM,
        frequency='Very High',
        complexity='Low',
        prerequisites=['1nt_opening'],  # Skill IDs, not convention IDs
        practice_hands_required=10,
        passing_accuracy=0.80,
        description='Ask for 4-card majors after 1NT opening',
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
        description='Transfer to 5-card major after 1NT opening',
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
        description='Preemptive 2♥/2♠ opening with 6-card suit, 5-10 HCP',
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
        description='Double for takeout after opponent opens',
        short_description='X for takeout, shows support for unbid suits',
        learning_time_minutes=20
    ),

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
        description='4NT asks for aces, 5NT asks for kings',
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
        description='Double after partner opens and opponent overcalls',
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
        description='Cuebid shows 5-5 in two suits',
        short_description='2♦ over 1♦ = majors, etc.',
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
        description='2NT overcall shows 5-5 in minors',
        short_description='2NT = both minors (5-5+)',
        learning_time_minutes=18
    ),

    'strong_2c': ConventionMetadata(
        id='strong_2c',
        name='Strong 2♣',
        level=ConventionLevel.INTERMEDIATE,
        category=ConventionCategory.FORCING,
        frequency='Low',
        complexity='Medium',
        prerequisites=['opening_bids_basic', 'game_bidding'],
        practice_hands_required=10,
        passing_accuracy=0.80,
        description='2♣ opening shows 22+ HCP or game-forcing hand',
        short_description='2♣ = 22+ HCP, game forcing',
        learning_time_minutes=15
    ),

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
        description='Bidding the fourth suit is artificial and forcing',
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
        description='Jump in new suit shows shortness and support',
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
        description='After 1NT rebid, new minor is forcing',
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
        description='Double after partner makes takeout double',
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
        description='2NT relay after interference over 1NT',
        short_description='2NT relay after interference',
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
        description='4♣ asks for aces after NT bids',
        short_description='4♣ ace-ask after NT',
        learning_time_minutes=15
    )
}

class ConventionRegistry:
    """Manages convention metadata and progression"""

    def __init__(self):
        self.conventions = CONVENTION_REGISTRY

    def get_convention(self, convention_id: str) -> Optional[ConventionMetadata]:
        return self.conventions.get(convention_id)

    def get_by_level(self, level: ConventionLevel) -> List[ConventionMetadata]:
        """Get all conventions at a specific level"""
        return [c for c in self.conventions.values() if c.level == level]

    def get_essential_conventions(self) -> List[ConventionMetadata]:
        return self.get_by_level(ConventionLevel.ESSENTIAL)

    def get_intermediate_conventions(self) -> List[ConventionMetadata]:
        return self.get_by_level(ConventionLevel.INTERMEDIATE)

    def get_advanced_conventions(self) -> List[ConventionMetadata]:
        return self.get_by_level(ConventionLevel.ADVANCED)

    def get_by_category(self, category: ConventionCategory) -> List[ConventionMetadata]:
        """Get all conventions in a category"""
        return [c for c in self.conventions.values() if c.category == category]

    def check_prerequisites_met(self, convention_id: str, completed_skills: List[str]) -> bool:
        """Check if user has completed prerequisites for a convention"""
        convention = self.get_convention(convention_id)
        if not convention:
            return False

        return all(prereq in completed_skills for prereq in convention.prerequisites)

    def get_unlocked_conventions(self, completed_skills: List[str],
                                 mastered_conventions: List[str]) -> List[ConventionMetadata]:
        """Get conventions that are unlocked for the user"""
        unlocked = []

        for convention in self.conventions.values():
            # Already mastered
            if convention.id in mastered_conventions:
                continue

            # Check skill prerequisites
            if not self.check_prerequisites_met(convention.id, completed_skills):
                continue

            # Check convention level prerequisites
            if convention.level == ConventionLevel.INTERMEDIATE:
                # Must master all essential conventions first
                essential_ids = [c.id for c in self.get_essential_conventions()]
                if not all(eid in mastered_conventions for eid in essential_ids):
                    continue

            elif convention.level == ConventionLevel.ADVANCED:
                # Must master all intermediate conventions first
                intermediate_ids = [c.id for c in self.get_intermediate_conventions()]
                if not all(iid in mastered_conventions for iid in intermediate_ids):
                    continue

            unlocked.append(convention)

        return unlocked

    def get_next_recommended_convention(self, completed_skills: List[str],
                                       mastered_conventions: List[str]) -> Optional[ConventionMetadata]:
        """Get the next convention the user should learn"""
        unlocked = self.get_unlocked_conventions(completed_skills, mastered_conventions)

        if not unlocked:
            return None

        # Prioritize by level, then by frequency
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

        sorted_conventions = sorted(
            unlocked,
            key=lambda c: (level_priority[c.level], frequency_priority[c.frequency])
        )

        return sorted_conventions[0] if sorted_conventions else None
```

**Pros:**
- ✅ Centralized metadata management
- ✅ Easy to add/modify conventions
- ✅ Clear prerequisite tracking
- ✅ Flexible querying by level, category, etc.
- ✅ Automatic recommendation system

**Cons:**
- ❌ Requires migration of existing convention code
- ❌ Need to maintain metadata separately from convention logic

---

### Option 2: Skill Tree Integration

**Overview:** Integrate conventions directly into the skill tree as specialized skills.

**Implementation:**

```python
# backend/engine/learning/skill_tree.py

SKILL_TREE = {
    'level_1_foundations': {
        'skills': [
            {
                'id': 'opening_bids_basic',
                'name': 'Basic Opening Bids',
                'type': 'skill',
                'level': 1,
                'prerequisites': [],
                'passing_accuracy': 0.80,
                'practice_hands': 10
            },
            {
                'id': 'basic_responses',
                'name': 'Basic Responses',
                'type': 'skill',
                'level': 1,
                'prerequisites': ['opening_bids_basic'],
                'passing_accuracy': 0.80,
                'practice_hands': 10
            },
            {
                'id': '1nt_opening',
                'name': '1NT Opening',
                'type': 'skill',
                'level': 1,
                'prerequisites': ['opening_bids_basic'],
                'passing_accuracy': 0.80,
                'practice_hands': 8
            }
        ]
    },

    'level_2_essential_conventions': {
        'name': 'Essential Conventions',
        'unlock_requirement': 'Complete Level 1 with 80% average',
        'skills': [
            {
                'id': 'stayman',
                'name': 'Stayman Convention',
                'type': 'convention',
                'convention_level': 'essential',
                'level': 2,
                'prerequisites': ['1nt_opening'],
                'passing_accuracy': 0.80,
                'practice_hands': 10,
                'frequency': 'Very High',
                'category': '1NT System'
            },
            {
                'id': 'jacoby_transfers',
                'name': 'Jacoby Transfers',
                'type': 'convention',
                'convention_level': 'essential',
                'level': 2,
                'prerequisites': ['1nt_opening'],
                'passing_accuracy': 0.80,
                'practice_hands': 10,
                'frequency': 'Very High',
                'category': '1NT System'
            },
            {
                'id': 'weak_two',
                'name': 'Weak Two Bids',
                'type': 'convention',
                'convention_level': 'essential',
                'level': 2,
                'prerequisites': ['opening_bids_basic'],
                'passing_accuracy': 0.80,
                'practice_hands': 8,
                'frequency': 'High',
                'category': 'Preemptive'
            },
            {
                'id': 'takeout_double',
                'name': 'Takeout Doubles',
                'type': 'convention',
                'convention_level': 'essential',
                'level': 2,
                'prerequisites': ['overcalls'],
                'passing_accuracy': 0.80,
                'practice_hands': 12,
                'frequency': 'High',
                'category': 'Competitive'
            }
        ]
    },

    'level_3_intermediate_conventions': {
        'name': 'Intermediate Conventions',
        'unlock_requirement': 'Master all Essential Conventions',
        'skills': [
            {
                'id': 'blackwood',
                'name': 'Blackwood (4NT)',
                'type': 'convention',
                'convention_level': 'intermediate',
                'level': 3,
                'prerequisites': ['stayman', 'jacoby_transfers', 'game_bidding'],
                'passing_accuracy': 0.80,
                'practice_hands': 12,
                'frequency': 'Medium',
                'category': 'Slam Bidding'
            },
            # ... other intermediate conventions
        ]
    },

    'level_4_advanced_conventions': {
        'name': 'Advanced Conventions',
        'unlock_requirement': 'Master all Intermediate Conventions',
        'skills': [
            {
                'id': 'fourth_suit_forcing',
                'name': 'Fourth Suit Forcing',
                'type': 'convention',
                'convention_level': 'advanced',
                'level': 4,
                'prerequisites': ['rebids', 'game_bidding', 'blackwood'],
                'passing_accuracy': 0.85,
                'practice_hands': 15,
                'frequency': 'Medium',
                'category': 'Forcing Bids'
            },
            # ... other advanced conventions
        ]
    }
}
```

**Pros:**
- ✅ Conventions are part of learning progression
- ✅ Clear visual representation in skill tree
- ✅ Natural unlock mechanism
- ✅ Easy to see convention vs. skill

**Cons:**
- ❌ Mixes conventions with skills (might be confusing)
- ❌ Less flexible for querying convention-specific data

---

### Option 3: Hybrid Approach (BEST BALANCE)

**Overview:** Combine convention metadata with skill tree integration.

**Implementation:**

```python
# Use ConventionRegistry for metadata
# Link conventions to skill tree nodes

SKILL_TREE_WITH_CONVENTIONS = {
    'level_2_essential_conventions': {
        'name': 'Essential Conventions',
        'type': 'convention_group',
        'unlock_requirement': 'Complete Level 1 Foundations',
        'conventions': [
            'stayman',           # References ConventionRegistry
            'jacoby_transfers',
            'weak_two',
            'takeout_double'
        ],
        'completion_requirement': 'Master all 4 conventions at 80%+'
    },

    'level_3_intermediate_conventions': {
        'name': 'Intermediate Conventions',
        'type': 'convention_group',
        'unlock_requirement': 'Master all Essential Conventions',
        'conventions': [
            'blackwood',
            'negative_double',
            'michaels_cuebid',
            'unusual_2nt',
            'strong_2c'
        ],
        'completion_requirement': 'Master all 5 conventions at 80%+'
    },

    'level_4_advanced_conventions': {
        'name': 'Advanced Conventions',
        'type': 'convention_group',
        'unlock_requirement': 'Master all Intermediate Conventions',
        'conventions': [
            'fourth_suit_forcing',
            'splinter_bids',
            'new_minor_forcing',
            'responsive_double',
            'lebensohl',
            'gerber'
        ],
        'completion_requirement': 'Master all 6 conventions at 85%+'
    }
}

class LearningPathManager:
    def __init__(self):
        self.convention_registry = ConventionRegistry()
        self.skill_tree = SKILL_TREE_WITH_CONVENTIONS

    def get_user_convention_progress(self, user_id: str) -> Dict:
        """Get detailed convention learning progress"""
        # Get user's mastered skills and conventions
        mastered_skills = get_user_mastered_skills(user_id)
        mastered_conventions = get_user_mastered_conventions(user_id)

        progress = {
            'essential': {
                'total': 4,
                'mastered': 0,
                'unlocked': [],
                'locked': [],
                'in_progress': []
            },
            'intermediate': {
                'total': 5,
                'mastered': 0,
                'unlocked': [],
                'locked': [],
                'in_progress': []
            },
            'advanced': {
                'total': 6,
                'mastered': 0,
                'unlocked': [],
                'locked': [],
                'in_progress': []
            }
        }

        # Process each level
        for level_key, level_data in self.skill_tree.items():
            level_name = level_key.split('_')[-2]  # 'essential', 'intermediate', 'advanced'

            for conv_id in level_data['conventions']:
                convention = self.convention_registry.get_convention(conv_id)

                if conv_id in mastered_conventions:
                    progress[level_name]['mastered'] += 1
                elif self.convention_registry.check_prerequisites_met(conv_id, mastered_skills):
                    progress[level_name]['unlocked'].append(convention)
                else:
                    progress[level_name]['locked'].append(convention)

        return progress
```

**Pros:**
- ✅ Best of both worlds
- ✅ Metadata for convention properties
- ✅ Skill tree for learning progression
- ✅ Clear separation of concerns
- ✅ Easy to maintain and extend

**Cons:**
- ❌ Slightly more complex initial setup
- ❌ Need to keep registry and tree in sync

---

## Database Schema

```sql
-- Convention definitions (metadata)
CREATE TABLE conventions (
    convention_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    level TEXT NOT NULL,  -- 'essential', 'intermediate', 'advanced'
    category TEXT,
    frequency TEXT,
    complexity TEXT,
    description TEXT,
    short_description TEXT,
    learning_time_minutes INTEGER,
    practice_hands_required INTEGER,
    passing_accuracy REAL
);

-- Convention prerequisites
CREATE TABLE convention_prerequisites (
    convention_id TEXT,
    prerequisite_id TEXT,  -- Can be skill_id or convention_id
    prerequisite_type TEXT, -- 'skill' or 'convention'
    FOREIGN KEY (convention_id) REFERENCES conventions(convention_id)
);

-- User convention progress
CREATE TABLE user_convention_progress (
    user_id INTEGER,
    convention_id TEXT,
    status TEXT,  -- 'locked', 'unlocked', 'in_progress', 'mastered'
    attempts INTEGER DEFAULT 0,
    correct INTEGER DEFAULT 0,
    accuracy REAL DEFAULT 0,
    started_at TIMESTAMP,
    mastered_at TIMESTAMP,
    last_practiced TIMESTAMP,
    PRIMARY KEY (user_id, convention_id),
    FOREIGN KEY (convention_id) REFERENCES conventions(convention_id)
);

-- Practice sessions by convention
CREATE TABLE convention_practice_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    convention_id TEXT,
    hand_id TEXT,
    user_bid TEXT,
    correct_bid TEXT,
    was_correct BOOLEAN,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (convention_id) REFERENCES conventions(convention_id)
);
```

---

## Integration with Learning Platform

### Skill Tree Visualization

```javascript
// ConventionLevelView.js

function ConventionLevelView({ level, conventions, userProgress }) {
  const levelConfig = {
    essential: {
      title: 'Essential Conventions',
      subtitle: 'Must-learn conventions for every player',
      color: '#4CAF50',
      icon: '⭐'
    },
    intermediate: {
      title: 'Intermediate Conventions',
      subtitle: 'Important tools for competitive play',
      color: '#2196F3',
      icon: '🎯'
    },
    advanced: {
      title: 'Advanced Conventions',
      subtitle: 'Expert techniques for sophisticated bidding',
      color: '#9C27B0',
      icon: '👑'
    }
  };

  const config = levelConfig[level];

  return (
    <div className="convention-level" style={{ borderColor: config.color }}>
      <div className="level-header">
        <span className="level-icon">{config.icon}</span>
        <h2>{config.title}</h2>
        <p className="level-subtitle">{config.subtitle}</p>
      </div>

      <div className="level-progress">
        <ProgressBar
          current={userProgress.mastered}
          total={userProgress.total}
          color={config.color}
        />
        <span className="progress-text">
          {userProgress.mastered} / {userProgress.total} mastered
        </span>
      </div>

      <div className="conventions-grid">
        {conventions.map(convention => (
          <ConventionCard
            key={convention.id}
            convention={convention}
            userProgress={userProgress[convention.id]}
            onSelect={() => handleConventionSelect(convention)}
          />
        ))}
      </div>
    </div>
  );
}

function ConventionCard({ convention, userProgress, onSelect }) {
  const getCardStatus = () => {
    if (userProgress?.mastered) return 'mastered';
    if (userProgress?.unlocked) return 'unlocked';
    return 'locked';
  };

  const status = getCardStatus();

  return (
    <div className={`convention-card convention-${status}`}>
      <div className="card-header">
        <h3>{convention.name}</h3>
        {status === 'mastered' && <span className="mastered-badge">✓</span>}
        {status === 'locked' && <span className="locked-badge">🔒</span>}
      </div>

      <div className="card-badges">
        <span className="frequency-badge">{convention.frequency}</span>
        <span className="complexity-badge">{convention.complexity}</span>
      </div>

      <p className="card-description">{convention.short_description}</p>

      {status === 'unlocked' && userProgress && (
        <div className="card-progress">
          <small>Progress: {Math.round(userProgress.accuracy * 100)}%</small>
          <div className="mini-progress-bar">
            <div style={{ width: `${userProgress.accuracy * 100}%` }} />
          </div>
        </div>
      )}

      <div className="card-actions">
        {status === 'unlocked' && (
          <button onClick={onSelect} className="btn-practice">
            {userProgress?.attempts > 0 ? 'Continue' : 'Start Learning'}
          </button>
        )}
        {status === 'locked' && (
          <button disabled className="btn-locked">
            Complete prerequisites
          </button>
        )}
        {status === 'mastered' && (
          <button onClick={onSelect} className="btn-review">
            Review
          </button>
        )}
      </div>

      {convention.prerequisites?.length > 0 && status === 'locked' && (
        <div className="prerequisites">
          <small>Requires:</small>
          <ul>
            {convention.prerequisites.map(prereq => (
              <li key={prereq}>{getSkillName(prereq)}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
```

---

## Recommended Approach

**I recommend Option 3: Hybrid Approach** for the following reasons:

1. **Clean Separation**: Metadata in registry, progression in skill tree
2. **Flexibility**: Easy to query convention properties independently
3. **Maintainability**: Changes to one don't affect the other
4. **Scalability**: Easy to add new conventions or levels
5. **User Experience**: Clear visual progression in skill tree

---

## Implementation Steps

### Phase 1: Setup (Week 1)

**Step 1: Create Convention Registry**
```bash
# Create new file
touch backend/engine/ai/conventions/convention_registry.py

# Add ConventionMetadata class
# Add CONVENTION_REGISTRY dict
# Add ConventionRegistry manager class
```

**Step 2: Populate Convention Metadata**
```python
# For each existing convention, add metadata entry
# Define level (essential/intermediate/advanced)
# Define prerequisites
# Define learning characteristics
```

**Step 3: Create Database Schema**
```bash
# Create migration script
python backend/database/migrations/add_convention_levels.py

# Run migration
python backend/database/init_db.py
```

### Phase 2: Backend Integration (Week 2)

**Step 4: Update Scenarios**
```python
# Modify scenarios.json to include convention_level
# Group scenarios by convention level
# Add difficulty indicators
```

**Step 5: Create API Endpoints**
```python
@app.route('/api/conventions/by-level', methods=['GET'])
def get_conventions_by_level():
    """Get conventions grouped by level"""
    registry = ConventionRegistry()

    return jsonify({
        'essential': [c.__dict__ for c in registry.get_essential_conventions()],
        'intermediate': [c.__dict__ for c in registry.get_intermediate_conventions()],
        'advanced': [c.__dict__ for c in registry.get_advanced_conventions()]
    })

@app.route('/api/conventions/unlocked', methods=['GET'])
def get_unlocked_conventions():
    """Get conventions unlocked for user"""
    user_id = request.args.get('user_id')

    completed_skills = get_user_completed_skills(user_id)
    mastered_conventions = get_user_mastered_conventions(user_id)

    registry = ConventionRegistry()
    unlocked = registry.get_unlocked_conventions(completed_skills, mastered_conventions)

    return jsonify({'unlocked': [c.__dict__ for c in unlocked]})

@app.route('/api/conventions/next-recommended', methods=['GET'])
def get_next_recommended():
    """Get next recommended convention to learn"""
    user_id = request.args.get('user_id')

    completed_skills = get_user_completed_skills(user_id)
    mastered_conventions = get_user_mastered_conventions(user_id)

    registry = ConventionRegistry()
    next_conv = registry.get_next_recommended_convention(completed_skills, mastered_conventions)

    return jsonify({'recommended': next_conv.__dict__ if next_conv else None})
```

### Phase 3: Frontend UI (Week 3)

**Step 6: Create Convention Level Components**
```bash
# Create new components
touch frontend/src/components/learning/ConventionLevelView.js
touch frontend/src/components/learning/ConventionCard.js
touch frontend/src/components/learning/ConventionLevelView.css
```

**Step 7: Integrate with Main App**
```javascript
// Add route for convention learning
<Route path="/learn-conventions">
  <ConventionLearningPath user={user} />
</Route>

// ConventionLearningPath shows all three levels
function ConventionLearningPath({ user }) {
  const [conventionProgress, setConventionProgress] = useState(null);

  useEffect(() => {
    fetchConventionProgress();
  }, [user]);

  return (
    <div className="convention-learning-path">
      <h1>Learn Bridge Conventions</h1>

      <ConventionLevelView
        level="essential"
        conventions={conventionProgress?.essential}
        userProgress={user.convention_progress.essential}
      />

      <ConventionLevelView
        level="intermediate"
        conventions={conventionProgress?.intermediate}
        userProgress={user.convention_progress.intermediate}
      />

      <ConventionLevelView
        level="advanced"
        conventions={conventionProgress?.advanced}
        userProgress={user.convention_progress.advanced}
      />
    </div>
  );
}
```

### Phase 4: Testing & Polish (Week 4)

**Step 8: Test Convention Unlocking**
```python
# Test prerequisite checking
# Test level-based unlocking
# Test progression flow
```

**Step 9: Add Visual Polish**
```css
/* Add level-specific colors and styling */
/* Add unlock animations */
/* Add progress indicators */
```

---

## UI/UX Design

### Main Convention Learning Page

```
┌─────────────────────────────────────────────────────────────┐
│                  LEARN BRIDGE CONVENTIONS                   │
│                                                             │
│  Your Progress: 6 / 15 conventions mastered (40%)          │
│  ████████░░░░░░░░░░░░░░░░░░░░░░░                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  ⭐ LEVEL 1: ESSENTIAL CONVENTIONS                          │
│  Must-learn conventions for every player                    │
│                                                             │
│  Progress: 3 / 4 mastered  ███████████████░░░░░ 75%        │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Stayman  ✓  │  │   Jacoby  ✓  │  │ Weak Two  ✓  │     │
│  │              │  │              │  │              │     │
│  │ Very High    │  │ Very High    │  │ High         │     │
│  │ Complexity:  │  │ Complexity:  │  │ Complexity:  │     │
│  │ Low          │  │ Low          │  │ Low          │     │
│  │              │  │              │  │              │     │
│  │ [Review]     │  │ [Review]     │  │ [Review]     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌──────────────┐                                          │
│  │ Takeout Dbl  │  ← Next to master!                       │
│  │              │                                          │
│  │ High         │                                          │
│  │ Complexity:  │                                          │
│  │ Medium       │                                          │
│  │              │                                          │
│  │ Progress:    │                                          │
│  │ ██████░░░░   │                                          │
│  │ 60% (6/10)   │                                          │
│  │              │                                          │
│  │ [Continue]   │                                          │
│  └──────────────┘                                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  🎯 LEVEL 2: INTERMEDIATE CONVENTIONS                       │
│  Important tools for competitive play                       │
│                                                             │
│  🔒 Locked - Complete all Essential conventions first      │
│                                                             │
│  Progress: 0 / 5 mastered  ░░░░░░░░░░░░░░░░░░░░ 0%        │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Blackwood 🔒 │  │ Negative  🔒 │  │ Michaels  🔒 │     │
│  │              │  │ Double       │  │ Cuebid       │     │
│  │ Medium       │  │              │  │              │     │
│  │ Complexity:  │  │ Medium       │  │ Medium       │     │
│  │ Medium       │  │ Complexity:  │  │ Complexity:  │     │
│  │              │  │ High         │  │ Medium       │     │
│  │ Requires:    │  │              │  │              │     │
│  │ • Stayman    │  │ Requires:    │  │ Requires:    │     │
│  │ • Jacoby     │  │ • Takeout    │  │ • Overcalls  │     │
│  │ • Game bid   │  │   Double     │  │ • Takeout    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  👑 LEVEL 3: ADVANCED CONVENTIONS                           │
│  Expert techniques for sophisticated bidding                │
│                                                             │
│  🔒 Locked - Complete all Intermediate conventions first   │
│                                                             │
│  Progress: 0 / 6 mastered  ░░░░░░░░░░░░░░░░░░░░ 0%        │
│                                                             │
│  [6 advanced conventions shown when unlocked]               │
└─────────────────────────────────────────────────────────────┘
```

### Individual Convention Learning Page

```
┌─────────────────────────────────────────────────────────────┐
│  ← Back to Conventions                                      │
│                                                             │
│  STAYMAN CONVENTION                                         │
│  ⭐ Essential • 1NT System • Very High Frequency            │
│                                                             │
│  Status: ✓ MASTERED (90% accuracy)                         │
│  Practice: 15 hands completed                               │
│  Last practiced: 2 days ago                                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  📚 CONVENTION OVERVIEW                                     │
│                                                             │
│  When to Use:                                               │
│  • Partner opens 1NT                                        │
│  • You have 8+ total points                                 │
│  • You have at least one 4-card major                       │
│                                                             │
│  How it Works:                                              │
│  • Bid 2♣ to ask for 4-card majors                         │
│  • Opener responds:                                         │
│    - 2♥ = 4+ hearts                                         │
│    - 2♠ = 4+ spades                                         │
│    - 2♦ = no 4-card major                                   │
│                                                             │
│  [Watch 2-min Tutorial] [Quick Reference Card]             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  🎯 PRACTICE OPTIONS                                        │
│                                                             │
│  ┌────────────────────┐  ┌────────────────────┐            │
│  │ REVIEW PRACTICE    │  │ SPEED DRILL        │            │
│  │                    │  │                    │            │
│  │ 10 mixed hands     │  │ 20 hands, 30s each │            │
│  │ Maintain mastery   │  │ Test your speed    │            │
│  │                    │  │                    │            │
│  │ [Start]            │  │ [Start]            │            │
│  └────────────────────┘  └────────────────────┘            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  📊 YOUR PROGRESS                                           │
│                                                             │
│  Accuracy Over Time:                                        │
│  100% │                     ╱●                              │
│       │                ╱──●╱                                │
│   90% │           ╱──●╱                                     │
│       │      ╱──●╱                                          │
│   80% │ ╱──●╱                                               │
│       └─────────────────────────                            │
│        Hand 1   5   10   15                                 │
│                                                             │
│  Common Mistakes:                                           │
│  • 2 times: Bid Stayman with 5-card major (use Jacoby!)   │
│  • 1 time: Forgot to count points correctly                │
└─────────────────────────────────────────────────────────────┘
```

---

## Summary

**Recommended Implementation:**
- Use **Hybrid Approach (Option 3)**
- Implement **ConventionRegistry** for metadata
- Integrate with **Skill Tree** for progression
- Create **3-level visual hierarchy** (Essential → Intermediate → Advanced)
- Add **prerequisite checking** and **automatic unlocking**
- Include **progress tracking** per convention

**Timeline:** 4 weeks
**Effort:** Medium (building on existing architecture)
**Impact:** High (clear learning path, better UX, guided progression)

This approach provides:
1. ✅ Clear progression path for users
2. ✅ Automatic difficulty scaling
3. ✅ Prerequisite management
4. ✅ Visual feedback on progress
5. ✅ Integration with gamification (XP, badges, etc.)
6. ✅ Easy to extend with new conventions

---

**Document Version:** 1.0
**Created:** October 11, 2025
**Status:** Implementation Plan

"""
Learning Platform Module

Provides structured learning progression for bridge bidding:
- Convention registry with metadata
- Skill tree for learning paths
- API endpoints for frontend integration
- Progress tracking and recommendations

Usage:
    from engine.learning import get_convention_registry, get_skill_tree_manager
    from engine.learning.learning_path_api import register_learning_endpoints

    # In server.py
    register_learning_endpoints(app)
"""

from engine.ai.conventions.convention_registry import (
    get_convention_registry,
    ConventionRegistry,
    ConventionMetadata,
    ConventionLevel,
    ConventionCategory
)

from engine.learning.skill_tree import (
    get_skill_tree_manager,
    SkillTreeManager,
    SkillNode,
    SkillType
)

__all__ = [
    'get_convention_registry',
    'get_skill_tree_manager',
    'ConventionRegistry',
    'ConventionMetadata',
    'ConventionLevel',
    'ConventionCategory',
    'SkillTreeManager',
    'SkillNode',
    'SkillType'
]

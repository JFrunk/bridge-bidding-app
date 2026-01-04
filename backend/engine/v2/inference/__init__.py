"""
V2 Inference Module

Provides judgment layers for the schema-driven bidding engine:
- ConflictResolver: Monte Carlo integration for bid validation
"""

from .conflict_resolver import ConflictResolver

__all__ = ['ConflictResolver']

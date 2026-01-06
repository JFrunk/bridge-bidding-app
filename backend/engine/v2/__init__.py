"""
V2 Bidding Engine - Schema-Driven Architecture

This module provides a schema-driven bidding engine that uses JSON
configuration files instead of Python code for bidding rules.

Features:
- JSON-based bidding rules with priority system
- Forcing level state tracking
- Monte Carlo integration for bid validation (optional)
"""

from .bidding_engine_v2_schema import BiddingEngineV2Schema, get_schema_engine
from .features.enhanced_extractor import (
    extract_flat_features,
    hand_to_pbn,
    pbn_to_hand
)
from .interpreters.schema_interpreter import SchemaInterpreter, BidCandidate
from .inference.conflict_resolver import ConflictResolver, PassThroughResolver
from .sanity_checker import CompetitiveSafetyValidator, validate_competitive_bid

__all__ = [
    'BiddingEngineV2Schema',
    'get_schema_engine',
    'extract_flat_features',
    'hand_to_pbn',
    'pbn_to_hand',
    'SchemaInterpreter',
    'BidCandidate',
    'ConflictResolver',
    'PassThroughResolver',
    'CompetitiveSafetyValidator',
    'validate_competitive_bid'
]

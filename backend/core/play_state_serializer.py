"""
PlayState Serialization
=======================

Handles conversion between PlayState objects and JSON for database storage.

The PlayState object contains:
- hands: Dict of 4 hands (N/E/S/W) with Card objects
- auction: List of bid strings
- contract: Dict with level, strain, declarer, doubled
- current_trick: List of cards in current trick
- tricks_taken: Dict with NS and EW counts
- next_to_play: Position (N/E/S/W)
- play_history: List of all tricks played
- declarer, dummy, opening_leader
- vulnerability
- dealer
"""

from typing import Dict, List, Any, Optional
from dataclasses import asdict
import json


class PlayStateSerializer:
    """
    Serializes and deserializes PlayState objects for database storage.

    Handles:
    - Converting Card namedtuples to dicts
    - Converting Hand objects to serializable format
    - Preserving all game state information
    - Validating deserialized state
    """

    @staticmethod
    def serialize(play_state) -> Dict[str, Any]:
        """
        Convert PlayState object to JSON-serializable dict.

        Args:
            play_state: PlayState object from play_engine.py

        Returns:
            Dict suitable for JSON serialization
        """
        from engine.hand import Card

        def serialize_card(card) -> Dict[str, str]:
            """Convert Card namedtuple to dict."""
            if card is None:
                return None
            return {'rank': card.rank, 'suit': card.suit}

        def serialize_hand(hand) -> List[Dict[str, str]]:
            """Convert Hand object (list of Cards) to list of dicts."""
            if hand is None:
                return None
            return [serialize_card(card) for card in hand]

        def serialize_trick(trick) -> List[Dict]:
            """Convert trick (list of {player, card}) to serializable format."""
            if not trick:
                return []
            return [
                {
                    'player': item['player'],
                    'card': serialize_card(item['card'])
                }
                for item in trick
            ]

        # Serialize the complete play state
        serialized = {
            'hands': {
                position: serialize_hand(hand)
                for position, hand in play_state.hands.items()
            },
            'auction': play_state.auction if play_state.auction else [],
            'contract': play_state.contract,
            'current_trick': serialize_trick(play_state.current_trick),
            'tricks_taken': play_state.tricks_taken,
            'next_to_play': play_state.next_to_play,
            'play_history': [serialize_trick(trick) for trick in play_state.play_history],
            'declarer': play_state.declarer,
            'dummy': play_state.dummy,
            'opening_leader': play_state.opening_leader,
            'vulnerability': play_state.vulnerability,
            'dealer': play_state.dealer,
            'ai_level': getattr(play_state, 'ai_level', 8),  # Default to 8 if not set
        }

        return serialized

    @staticmethod
    def deserialize(serialized_state: Dict[str, Any]):
        """
        Convert JSON dict back to PlayState object.

        Args:
            serialized_state: Dict from database (deserialized JSON)

        Returns:
            PlayState object
        """
        from engine.hand import Card
        from engine.play_engine import PlayState

        def deserialize_card(card_dict: Optional[Dict]) -> Optional[Card]:
            """Convert dict to Card namedtuple."""
            if card_dict is None:
                return None
            return Card(rank=card_dict['rank'], suit=card_dict['suit'])

        def deserialize_hand(hand_list: Optional[List[Dict]]) -> Optional[List[Card]]:
            """Convert list of dicts to list of Cards."""
            if hand_list is None:
                return None
            return [deserialize_card(card_dict) for card_dict in hand_list]

        def deserialize_trick(trick_list: List[Dict]) -> List[Dict]:
            """Convert serialized trick to PlayState trick format."""
            if not trick_list:
                return []
            return [
                {
                    'player': item['player'],
                    'card': deserialize_card(item['card'])
                }
                for item in trick_list
            ]

        # Reconstruct PlayState
        play_state = PlayState()
        play_state.hands = {
            position: deserialize_hand(hand_list)
            for position, hand_list in serialized_state['hands'].items()
        }
        play_state.auction = serialized_state.get('auction', [])
        play_state.contract = serialized_state.get('contract')
        play_state.current_trick = deserialize_trick(serialized_state.get('current_trick', []))
        play_state.tricks_taken = serialized_state.get('tricks_taken', {'NS': 0, 'EW': 0})
        play_state.next_to_play = serialized_state.get('next_to_play')
        play_state.play_history = [
            deserialize_trick(trick) for trick in serialized_state.get('play_history', [])
        ]
        play_state.declarer = serialized_state.get('declarer')
        play_state.dummy = serialized_state.get('dummy')
        play_state.opening_leader = serialized_state.get('opening_leader')
        play_state.vulnerability = serialized_state.get('vulnerability', 'None')
        play_state.dealer = serialized_state.get('dealer')
        play_state.ai_level = serialized_state.get('ai_level', 8)

        return play_state

    @staticmethod
    def extract_quick_access_fields(play_state) -> Dict[str, Any]:
        """
        Extract denormalized fields for database indexing and quick access.

        These fields are stored separately in active_play_states table for:
        - Faster queries (no JSON parsing needed)
        - Database indexes
        - Quick status checks

        Returns:
            Dict with fields matching active_play_states table columns
        """
        contract_string = None
        if play_state.contract:
            level = play_state.contract.get('level')
            strain = play_state.contract.get('strain')
            declarer = play_state.contract.get('declarer')
            doubled = play_state.contract.get('doubled', 0)

            if level and strain and declarer:
                doubled_str = 'XX' if doubled == 2 else 'X' if doubled == 1 else ''
                contract_string = f"{level}{strain}{doubled_str} by {declarer}"

        return {
            'contract_string': contract_string,
            'declarer': play_state.declarer,
            'dummy': play_state.dummy,
            'next_to_play': play_state.next_to_play,
            'tricks_taken_ns': play_state.tricks_taken.get('NS', 0),
            'tricks_taken_ew': play_state.tricks_taken.get('EW', 0),
            'vulnerability': play_state.vulnerability,
            'ai_difficulty': f"level{play_state.ai_level}" if hasattr(play_state, 'ai_level') else 'expert',
            'dealer': play_state.dealer,
            'is_complete': len(play_state.current_trick) == 0 and len(play_state.play_history) == 13
        }


def serialize_play_state(play_state) -> str:
    """
    Convenience function to serialize PlayState to JSON string.

    Args:
        play_state: PlayState object

    Returns:
        JSON string suitable for database storage
    """
    serialized = PlayStateSerializer.serialize(play_state)
    return json.dumps(serialized)


def deserialize_play_state(json_str: str):
    """
    Convenience function to deserialize JSON string to PlayState.

    Args:
        json_str: JSON string from database

    Returns:
        PlayState object
    """
    # Handle case where database returns dict directly (PostgreSQL JSONB)
    if isinstance(json_str, dict):
        serialized = json_str
    else:
        serialized = json.loads(json_str)

    return PlayStateSerializer.deserialize(serialized)

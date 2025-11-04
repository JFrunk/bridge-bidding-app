"""
Unit Tests: PlayState Serialization
====================================

Tests the PlayState JSON serialization/deserialization for database storage.

Test coverage:
- Card serialization
- Hand serialization
- Trick serialization
- Full PlayState round-trip
- Quick access field extraction
"""

import pytest
from core.play_state_serializer import PlayStateSerializer, serialize_play_state, deserialize_play_state
from engine.hand import Card, Hand
from engine.play_engine import PlayState


def test_serialize_card():
    """Test Card namedtuple serialization."""
    serializer = PlayStateSerializer()

    card = Card(rank='A', suit='♠')
    serialized = serializer.serialize(
        create_minimal_play_state_with_card(card)
    )

    # Check that card was serialized in hands
    assert serialized['hands']['North'][0] == {'rank': 'A', 'suit': '♠'}


def test_serialize_hand():
    """Test full hand serialization."""
    serializer = PlayStateSerializer()

    hand = Hand([
        Card('A', '♠'),
        Card('K', '♠'),
        Card('Q', '♥')
    ])

    play_state = PlayState()
    play_state.hands = {'North': hand, 'East': None, 'South': None, 'West': None}

    serialized = serializer.serialize(play_state)

    assert len(serialized['hands']['North']) == 3
    assert serialized['hands']['North'][0] == {'rank': 'A', 'suit': '♠'}
    assert serialized['hands']['North'][1] == {'rank': 'K', 'suit': '♠'}
    assert serialized['hands']['North'][2] == {'rank': 'Q', 'suit': '♥'}


def test_serialize_trick():
    """Test trick serialization."""
    serializer = PlayStateSerializer()

    play_state = PlayState()
    play_state.hands = {'North': None, 'East': None, 'South': None, 'West': None}
    play_state.current_trick = [
        {'player': 'North', 'card': Card('A', '♠')},
        {'player': 'East', 'card': Card('2', '♠')}
    ]

    serialized = serializer.serialize(play_state)

    assert len(serialized['current_trick']) == 2
    assert serialized['current_trick'][0]['player'] == 'North'
    assert serialized['current_trick'][0]['card'] == {'rank': 'A', 'suit': '♠'}


def test_serialize_full_play_state():
    """Test complete PlayState serialization."""
    play_state = create_sample_play_state()

    serializer = PlayStateSerializer()
    serialized = serializer.serialize(play_state)

    # Verify all fields present
    assert 'hands' in serialized
    assert 'auction' in serialized
    assert 'contract' in serialized
    assert 'current_trick' in serialized
    assert 'tricks_taken' in serialized
    assert 'next_to_play' in serialized
    assert 'play_history' in serialized
    assert 'declarer' in serialized
    assert 'dummy' in serialized
    assert 'vulnerability' in serialized
    assert 'dealer' in serialized
    assert 'ai_level' in serialized


def test_deserialize_card():
    """Test Card deserialization from dict."""
    serializer = PlayStateSerializer()

    card_dict = {'rank': 'K', 'suit': '♥'}
    play_state_dict = create_minimal_serialized_state_with_card(card_dict)

    play_state = serializer.deserialize(play_state_dict)

    assert play_state.hands['North'][0].rank == 'K'
    assert play_state.hands['North'][0].suit == '♥'


def test_deserialize_hand():
    """Test Hand deserialization."""
    serializer = PlayStateSerializer()

    hand_data = [
        {'rank': 'A', 'suit': '♠'},
        {'rank': 'K', 'suit': '♠'},
        {'rank': 'Q', 'suit': '♥'}
    ]

    play_state_dict = {
        'hands': {'North': hand_data, 'East': None, 'South': None, 'West': None},
        'auction': [],
        'contract': None,
        'current_trick': [],
        'tricks_taken': {'NS': 0, 'EW': 0},
        'next_to_play': 'North',
        'play_history': [],
        'declarer': None,
        'dummy': None,
        'opening_leader': None,
        'vulnerability': 'None',
        'dealer': 'North'
    }

    play_state = serializer.deserialize(play_state_dict)

    assert len(play_state.hands['North']) == 3
    assert play_state.hands['North'][0].rank == 'A'
    assert play_state.hands['North'][2].suit == '♥'


def test_round_trip_serialization():
    """Test full round-trip: serialize then deserialize."""
    original = create_sample_play_state()

    serializer = PlayStateSerializer()

    # Serialize
    serialized = serializer.serialize(original)

    # Deserialize
    restored = serializer.deserialize(serialized)

    # Verify key fields match
    assert restored.declarer == original.declarer
    assert restored.dummy == original.dummy
    assert restored.next_to_play == original.next_to_play
    assert restored.vulnerability == original.vulnerability
    assert restored.dealer == original.dealer
    assert restored.tricks_taken == original.tricks_taken

    # Verify hands
    assert len(restored.hands['North']) == len(original.hands['North'])
    assert restored.hands['North'][0].rank == original.hands['North'][0].rank


def test_extract_quick_access_fields():
    """Test extraction of denormalized quick access fields."""
    play_state = create_sample_play_state()

    serializer = PlayStateSerializer()
    fields = serializer.extract_quick_access_fields(play_state)

    assert 'contract_string' in fields
    assert 'declarer' in fields
    assert 'dummy' in fields
    assert 'next_to_play' in fields
    assert 'tricks_taken_ns' in fields
    assert 'tricks_taken_ew' in fields
    assert 'vulnerability' in fields
    assert 'dealer' in fields
    assert 'is_complete' in fields

    # Verify values
    assert fields['declarer'] == 'South'
    assert fields['dummy'] == 'North'
    assert fields['next_to_play'] == 'West'
    assert fields['tricks_taken_ns'] == 3
    assert fields['tricks_taken_ew'] == 2


def test_contract_string_generation():
    """Test contract string formatting."""
    play_state = PlayState()
    play_state.contract = {
        'level': 3,
        'strain': 'NT',
        'declarer': 'South',
        'doubled': 0
    }
    play_state.declarer = 'South'
    play_state.hands = {'North': None, 'East': None, 'South': None, 'West': None}

    serializer = PlayStateSerializer()
    fields = serializer.extract_quick_access_fields(play_state)

    assert fields['contract_string'] == '3NT by South'


def test_contract_string_with_double():
    """Test contract string with double."""
    play_state = PlayState()
    play_state.contract = {
        'level': 4,
        'strain': '♠',
        'declarer': 'North',
        'doubled': 1
    }
    play_state.declarer = 'North'
    play_state.hands = {'North': None, 'East': None, 'South': None, 'West': None}

    serializer = PlayStateSerializer()
    fields = serializer.extract_quick_access_fields(play_state)

    assert fields['contract_string'] == '4♠X by North'


def test_convenience_functions():
    """Test serialize_play_state and deserialize_play_state convenience functions."""
    original = create_sample_play_state()

    # Serialize to JSON string
    json_str = serialize_play_state(original)
    assert isinstance(json_str, str)

    # Deserialize from JSON string
    restored = deserialize_play_state(json_str)

    assert restored.declarer == original.declarer
    assert restored.dummy == original.dummy


def test_deserialize_from_dict():
    """Test deserialization when database returns dict (PostgreSQL JSONB)."""
    play_state_dict = create_minimal_serialized_state()

    # Deserialize directly from dict (simulates PostgreSQL JSONB)
    restored = deserialize_play_state(play_state_dict)

    assert restored.declarer == 'South'
    assert restored.dummy == 'North'


# Helper functions

def create_minimal_play_state_with_card(card):
    """Create minimal PlayState with one card in North's hand."""
    play_state = PlayState()
    play_state.hands = {
        'North': Hand([card]),
        'East': None,
        'South': None,
        'West': None
    }
    return play_state


def create_minimal_serialized_state_with_card(card_dict):
    """Create minimal serialized state dict with one card."""
    return {
        'hands': {
            'North': [card_dict],
            'East': None,
            'South': None,
            'West': None
        },
        'auction': [],
        'contract': None,
        'current_trick': [],
        'tricks_taken': {'NS': 0, 'EW': 0},
        'next_to_play': 'North',
        'play_history': [],
        'declarer': None,
        'dummy': None,
        'opening_leader': None,
        'vulnerability': 'None',
        'dealer': 'North'
    }


def create_minimal_serialized_state():
    """Create minimal serialized state dict."""
    return {
        'hands': {'North': None, 'East': None, 'South': None, 'West': None},
        'auction': ['1NT', 'Pass', '3NT', 'Pass', 'Pass', 'Pass'],
        'contract': {'level': 3, 'strain': 'NT', 'declarer': 'South', 'doubled': 0},
        'current_trick': [],
        'tricks_taken': {'NS': 0, 'EW': 0},
        'next_to_play': 'West',
        'play_history': [],
        'declarer': 'South',
        'dummy': 'North',
        'opening_leader': 'West',
        'vulnerability': 'None',
        'dealer': 'North',
        'ai_level': 8
    }


def create_sample_play_state():
    """Create a sample PlayState for testing."""
    play_state = PlayState()

    # Hands
    play_state.hands = {
        'North': Hand([Card('A', '♠'), Card('K', '♠')]),
        'East': Hand([Card('Q', '♥')]),
        'South': Hand([Card('J', '♣')]),
        'West': Hand([Card('T', '♦')])
    }

    # Auction
    play_state.auction = ['1NT', 'Pass', '3NT', 'Pass', 'Pass', 'Pass']

    # Contract
    play_state.contract = {
        'level': 3,
        'strain': 'NT',
        'declarer': 'South',
        'doubled': 0
    }

    # Current trick
    play_state.current_trick = []

    # Tricks taken
    play_state.tricks_taken = {'NS': 3, 'EW': 2}

    # Other fields
    play_state.next_to_play = 'West'
    play_state.declarer = 'South'
    play_state.dummy = 'North'
    play_state.opening_leader = 'West'
    play_state.vulnerability = 'None'
    play_state.dealer = 'North'
    play_state.ai_level = 8

    # Play history
    play_state.play_history = []

    return play_state


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

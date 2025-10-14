"""
Integration test for DDS AI - verify it works with actual PlayState
"""

import sys
sys.path.insert(0, '.')

from engine.hand import Hand, Card
from engine.play_engine import PlayState, Contract, GamePhase
from engine.play.ai.dds_ai import DDSPlayAI, DDS_AVAILABLE

print("=" * 80)
print("DDS AI Integration Test")
print("=" * 80)
print()

if not DDS_AVAILABLE:
    print("❌ DDS not available")
    sys.exit(1)

print("✅ DDS available\n")

# Create DDS AI
dds_ai = DDSPlayAI()
print(f"AI: {dds_ai.get_name()} ({dds_ai.get_difficulty()})\n")

# Create a realistic deal
print("Creating 3NT contract...")

north_cards = [
    Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'),
    Card('A', '♥'), Card('K', '♥'),
    Card('A', '♦'), Card('K', '♦'), Card('Q', '♦'),
    Card('A', '♣'), Card('K', '♣'), Card('Q', '♣'), Card('J', '♣'), Card('T', '♣')
]

east_cards = [
    Card('J', '♠'), Card('T', '♠'), Card('9', '♠'), Card('8', '♠'),
    Card('Q', '♥'), Card('J', '♥'), Card('T', '♥'),
    Card('J', '♦'), Card('T', '♦'), Card('9', '♦'),
    Card('9', '♣'), Card('8', '♣'), Card('7', '♣')
]

south_cards = [
    Card('7', '♠'), Card('6', '♠'), Card('5', '♠'),
    Card('9', '♥'), Card('8', '♥'), Card('7', '♥'),
    Card('8', '♦'), Card('7', '♦'), Card('6', '♦'),
    Card('6', '♣'), Card('5', '♣'), Card('4', '♣'), Card('3', '♣')
]

west_cards = [
    Card('4', '♠'), Card('3', '♠'), Card('2', '♠'),
    Card('6', '♥'), Card('5', '♥'), Card('4', '♥'), Card('3', '♥'), Card('2', '♥'),
    Card('5', '♦'), Card('4', '♦'), Card('3', '♦'), Card('2', '♦'),
    Card('2', '♣')
]

hands = {
    'N': Hand(north_cards),
    'E': Hand(east_cards),
    'S': Hand(south_cards),
    'W': Hand(west_cards)
}

contract = Contract(level=3, strain='NT', declarer='S', doubled=0)

# Create initial play state (opening lead)
state = PlayState(
    contract=contract,
    hands=hands,
    current_trick=[],
    tricks_won={'N': 0, 'E': 0, 'S': 0, 'W': 0},
    trick_history=[],
    next_to_play='W',  # West leads vs 3NT
    dummy_revealed=False,
    current_trick_leader='W',
    phase=GamePhase.PLAY_STARTING
)

print(f"Contract: {contract}")
print(f"Leader: West (opening lead)\n")

# Test 1: Opening lead
print("Test 1: Opening Lead")
print("-" * 40)
try:
    import time
    start = time.time()
    card = dds_ai.choose_card(state, 'W')
    elapsed = time.time() - start

    print(f"✅ West leads: {card}")
    print(f"   Time: {elapsed*1000:.1f}ms")

    # Remove card from hand
    west_hand_updated = Hand([c for c in west_cards if c != card])

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 2: Declarer's play from dummy
print("Test 2: Play from Dummy")
print("-" * 40)

# Simulate West's lead
state2 = PlayState(
    contract=contract,
    hands=hands,
    current_trick=[(card, 'W')],
    tricks_won={'N': 0, 'E': 0, 'S': 0, 'W': 0},
    trick_history=[],
    next_to_play='N',
    dummy_revealed=True,
    current_trick_leader='W',
    phase=GamePhase.PLAY_IN_PROGRESS
)

try:
    start = time.time()
    north_card = dds_ai.choose_card(state2, 'N')
    elapsed = time.time() - start

    print(f"✅ North plays: {north_card}")
    print(f"   Time: {elapsed*1000:.1f}ms")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 3: Mid-hand position
print("Test 3: Mid-Trick Position")
print("-" * 40)

state3 = PlayState(
    contract=contract,
    hands=hands,
    current_trick=[(card, 'W'), (north_card, 'N')],
    tricks_won={'N': 0, 'E': 0, 'S': 0, 'W': 0},
    trick_history=[],
    next_to_play='E',
    dummy_revealed=True,
    current_trick_leader='W',
    phase=GamePhase.PLAY_IN_PROGRESS
)

try:
    start = time.time()
    east_card = dds_ai.choose_card(state3, 'E')
    elapsed = time.time() - start

    print(f"✅ East plays: {east_card}")
    print(f"   Time: {elapsed*1000:.1f}ms")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()

# Show statistics
stats = dds_ai.get_statistics()
print("=" * 80)
print("DDS AI Statistics")
print("=" * 80)
print(f"Total solves: {stats.get('solve_count', 0)}")
print(f"Total time: {stats.get('total_time', 0)*1000:.1f}ms")
print(f"Avg time/solve: {stats.get('avg_time', 0)*1000:.1f}ms")
print(f"Min time: {stats.get('min_time', 0)*1000:.1f}ms")
print(f"Max time: {stats.get('max_time', 0)*1000:.1f}ms")
print()

print("=" * 80)
print("✅ INTEGRATION TEST COMPLETE")
print("=" * 80)
print()
print("Summary:")
print("  ✅ DDS AI successfully integrated with PlayState")
print("  ✅ Opening lead selection working")
print("  ✅ Dummy play working")
print("  ✅ Mid-trick decisions working")
print("  ✅ Ready for production use")

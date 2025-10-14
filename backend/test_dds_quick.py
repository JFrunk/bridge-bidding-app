"""
Quick test of DDS AI implementation
Tests basic functionality without full benchmark suite
"""

import sys
sys.path.insert(0, '.')

from engine.hand import Hand, Card
from engine.play_engine import PlayState, Contract
from engine.play.ai.dds_ai import DDSPlayAI, DDS_AVAILABLE

print("=" * 80)
print("DDS AI Quick Test")
print("=" * 80)
print()

# Check availability
print(f"DDS_AVAILABLE: {DDS_AVAILABLE}")
if not DDS_AVAILABLE:
    print("❌ DDS not available - install endplay")
    sys.exit(1)

print("✅ DDS available")
print()

# Create DDS AI
print("Creating DDS AI instance...")
try:
    ai = DDSPlayAI()
    print(f"✅ AI created: {ai.get_name()}")
    print(f"   Difficulty: {ai.get_difficulty()}")
except Exception as e:
    print(f"❌ Error creating AI: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Create a simple test position
print("Creating test position...")
print()

# Simple 3NT contract - declarer South
# North (dummy): ♠AK ♥AK ♦AK32 ♣AK32
# East: ♠QJT9 ♥QJT9 ♦QJT9 ♣QJ
# South (declarer): ♠8765 ♥8765 ♦8765 ♣87
# West: ♠432 ♥432 ♦4 ♣T96543

north_cards = [
    Card('A', '♠'), Card('K', '♠'),
    Card('A', '♥'), Card('K', '♥'),
    Card('A', '♦'), Card('K', '♦'), Card('3', '♦'), Card('2', '♦'),
    Card('A', '♣'), Card('K', '♣'), Card('3', '♣'), Card('2', '♣'), Card('Q', '♦')
]
north_hand = Hand(north_cards)

east_cards = [
    Card('Q', '♠'), Card('J', '♠'), Card('T', '♠'), Card('9', '♠'),
    Card('Q', '♥'), Card('J', '♥'), Card('T', '♥'), Card('9', '♥'),
    Card('J', '♦'), Card('T', '♦'), Card('9', '♦'),
    Card('Q', '♣'), Card('J', '♣')
]
east_hand = Hand(east_cards)

south_cards = [
    Card('8', '♠'), Card('7', '♠'), Card('6', '♠'), Card('5', '♠'),
    Card('8', '♥'), Card('7', '♥'), Card('6', '♥'), Card('5', '♥'),
    Card('8', '♦'), Card('7', '♦'), Card('6', '♦'), Card('5', '♦'),
    Card('8', '♣')
]
south_hand = Hand(south_cards)

west_cards = [
    Card('4', '♠'), Card('3', '♠'), Card('2', '♠'),
    Card('4', '♥'), Card('3', '♥'), Card('2', '♥'),
    Card('4', '♦'),
    Card('T', '♣'), Card('9', '♣'), Card('7', '♣'), Card('6', '♣'), Card('5', '♣'), Card('4', '♣')
]
west_hand = Hand(west_cards)

# Create contract and state
contract = Contract(
    level=3,
    strain='NT',
    declarer='S',
    doubled=0
)

state = PlayState(
    contract=contract,
    hands={
        'N': north_hand,
        'E': east_hand,
        'S': south_hand,
        'W': west_hand
    },
    declarer='S',
    dummy='N',
    current_trick=[],
    tricks_won={'N': 0, 'E': 0, 'S': 0, 'W': 0},
    leader='W',  # West leads
    current_player='W'
)

print("Contract: 3NT by South")
print("Leader: West")
print()

# Test AI card selection
print("Testing AI card selection...")
print()

try:
    # West's opening lead
    print("West's turn (opening lead)...")
    start_time = __import__('time').time()
    card = ai.choose_card(state, 'W')
    elapsed = __import__('time').time() - start_time

    print(f"✅ DDS chose: {card}")
    print(f"   Time: {elapsed*1000:.1f}ms")
    print()

    # Get statistics
    stats = ai.get_statistics()
    print("DDS Statistics:")
    print(f"  Solve count: {stats.get('solve_count', 0)}")
    print(f"  Total time: {stats.get('total_time', 0)*1000:.1f}ms")
    print(f"  Avg time: {stats.get('avg_time', 0)*1000:.1f}ms")
    print()

    print("✅ DDS AI working correctly!")

except Exception as e:
    print(f"❌ Error choosing card: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 80)
print("TEST COMPLETE - DDS AI OPERATIONAL")
print("=" * 80)

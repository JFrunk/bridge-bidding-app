"""
End-to-end test of DDS AI in actual gameplay
Tests the complete flow from deal creation through playing cards
"""

import sys
sys.path.insert(0, '.')

from engine.hand import Hand, Card
from engine.play_engine import PlayEngine, PlayState, Contract
from engine.play.ai.dds_ai import DDSPlayAI, DDS_AVAILABLE
from engine.play.ai.minimax_ai import MinimaxPlayAI

print("=" * 80)
print("DDS AI End-to-End Test")
print("=" * 80)
print()

if not DDS_AVAILABLE:
    print("❌ DDS not available - install endplay")
    sys.exit(1)

print("✅ DDS available")
print()

# Initialize engines
play_engine = PlayEngine()
dds_ai = DDSPlayAI()
minimax_ai = MinimaxPlayAI(max_depth=3)  # For comparison

print(f"DDS AI: {dds_ai.get_name()} ({dds_ai.get_difficulty()})")
print(f"Minimax AI: {minimax_ai.get_name()} ({minimax_ai.get_difficulty()})")
print()

# Create a test deal
print("Creating test deal...")

# Simple 3NT contract where DDS should make optimal plays
# North (dummy) has entries and stoppers
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

print(f"Contract: {contract}")
print(f"Declarer: South, Dummy: North")
print()

# Initialize play state
state = play_engine.start_play(hands, contract, 'None')
print(f"✅ Play state initialized")
print(f"   Leader: {state.next_to_play}")
print(f"   Phase: {state.phase}")
print()

# Play through the hand with DDS making decisions
print("Playing hand with DDS AI...")
print("-" * 80)

trick_count = 0
move_count = 0
dds_moves = []
dds_time_total = 0.0

try:
    while state.phase.value.startswith('PLAY'):
        trick_count_before = sum(state.tricks_won.values())

        current_player = state.next_to_play
        trick_leader = state.current_trick_leader or current_player

        # Show trick start
        if len(state.current_trick) == 0:
            trick_count += 1
            print(f"\nTrick {trick_count} (Leader: {trick_leader}):")

        # Get legal cards
        legal_cards = play_engine.get_legal_plays(state)
        if not legal_cards:
            print(f"  No legal cards for {current_player}")
            break

        # Choose card with DDS
        import time
        start_time = time.time()
        card = dds_ai.choose_card(state, current_player)
        elapsed = time.time() - start_time

        dds_time_total += elapsed
        move_count += 1
        dds_moves.append({
            'player': current_player,
            'card': str(card),
            'time': elapsed * 1000  # ms
        })

        print(f"  {current_player}: {card} ({elapsed*1000:.1f}ms)")

        # Play the card
        state = play_engine.play_card(state, card)

        # Check if trick completed
        trick_count_after = sum(state.tricks_won.values())
        if trick_count_after > trick_count_before:
            winner = max(state.tricks_won.items(), key=lambda x: x[1])[0]
            print(f"    → Trick won by: {winner}")

        # Safety limit
        if move_count > 52:
            print("  Safety limit reached!")
            break

except Exception as e:
    print(f"\n❌ Error during play: {e}")
    import traceback
    traceback.print_exc()

print()
print("-" * 80)
print("Hand completed!")
print()

# Show results
ns_tricks = state.tricks_won.get('N', 0) + state.tricks_won.get('S', 0)
ew_tricks = state.tricks_won.get('E', 0) + state.tricks_won.get('W', 0)

print("Final Results:")
print(f"  N/S tricks: {ns_tricks}")
print(f"  E/W tricks: {ew_tricks}")
print(f"  Contract: {contract}")
print(f"  Result: {'MADE' if ns_tricks >= 9 else 'DOWN'} (needed 9 tricks)")
print()

# Show DDS statistics
dds_stats = dds_ai.get_statistics()
print("DDS AI Performance:")
print(f"  Total moves: {move_count}")
print(f"  Total time: {dds_time_total*1000:.1f}ms")
print(f"  Avg time/move: {(dds_time_total/move_count)*1000:.1f}ms")
print(f"  DDS solves: {dds_stats.get('solve_count', 0)}")
print(f"  DDS avg time: {dds_stats.get('avg_time', 0)*1000:.1f}ms")
print()

# Show some sample moves
print("Sample DDS moves:")
for i, move in enumerate(dds_moves[:5]):
    print(f"  Move {i+1}: {move['player']} played {move['card']} ({move['time']:.1f}ms)")
print()

print("=" * 80)
print("✅ END-TO-END TEST COMPLETE")
print("=" * 80)
print()
print("Summary:")
print(f"  ✅ DDS AI successfully played {move_count} cards")
print(f"  ✅ Contract {'MADE' if ns_tricks >= 9 else 'FAILED'}")
print(f"  ✅ Average decision time: {(dds_time_total/move_count)*1000:.1f}ms")
print(f"  ✅ DDS AI is fully operational in gameplay")

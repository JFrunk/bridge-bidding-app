#!/usr/bin/env python3
"""
Comprehensive test suite for Phase 1 critical convention fixes.

Tests:
1. Jacoby Transfers - Super-accept logic
2. Jacoby Transfers - Post-transfer continuations
3. Stayman - Responder rebids
4. Takeout Doubles - HCP requirement
5. Blackwood - Signoff logic
"""

from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine

def create_hand(cards_str):
    """Helper to create a hand from card string like '♠AK ♥QJ5 ♦AKQ106 ♣T98'"""
    cards = []
    parts = cards_str.split()
    for part in parts:
        suit = part[0]
        ranks = part[1:]
        for rank in ranks:
            cards.append(Card(rank, suit))
    return Hand(cards)

def run_test(test_name, test_func):
    """Run a test and report results."""
    try:
        test_func()
        print(f"✅ PASS: {test_name}")
        return True
    except AssertionError as e:
        print(f"❌ FAIL: {test_name}")
        print(f"   Error: {e}")
        return False
    except Exception as e:
        print(f"💥 ERROR: {test_name}")
        print(f"   Exception: {e}")
        return False

# ============================================================================
# TEST 1: Jacoby Transfers - Super-Accept Logic
# ============================================================================

def test_jacoby_super_accept_hearts():
    """Test super-accept with 17 HCP and 4-card heart support."""
    engine = BiddingEngine()

    # North: 17 HCP, 4 hearts
    north_hand = create_hand("♠AK8 ♥KJ94 ♦AQ7 ♣865")
    auction = ['1NT', 'Pass', '2♦', 'Pass']  # South transferred to hearts

    bid, explanation = engine.get_next_bid(north_hand, auction, 'North', 'None')

    assert bid == '3♥', f"Expected 3♥ (super-accept), got {bid}"
    assert '4-card' in explanation.lower() or 'support' in explanation.lower(), \
        f"Expected explanation about 4-card support, got: {explanation}"

def test_jacoby_no_super_accept_doubleton():
    """Test normal completion with doubleton (no super-accept)."""
    engine = BiddingEngine()

    # North: 17 HCP, only 2 hearts
    north_hand = create_hand("♠AKQ8 ♥K9 ♦AQ75 ♣865")
    auction = ['1NT', 'Pass', '2♦', 'Pass']

    bid, explanation = engine.get_next_bid(north_hand, auction, 'North', 'None')

    assert bid == '2♥', f"Expected 2♥ (normal completion), got {bid}"

def test_jacoby_no_super_accept_15hcp():
    """Test normal completion with 15 HCP (not maximum)."""
    engine = BiddingEngine()

    # North: 15 HCP, 4 hearts
    north_hand = create_hand("♠K85 ♥KJ94 ♦AQ7 ♣865")
    auction = ['1NT', 'Pass', '2♦', 'Pass']

    bid, explanation = engine.get_next_bid(north_hand, auction, 'North', 'None')

    assert bid == '2♥', f"Expected 2♥ (not maximum), got {bid}"

# ============================================================================
# TEST 2: Jacoby Transfers - Post-Transfer Continuations
# ============================================================================

def test_jacoby_continuation_weak_pass():
    """Test responder passes with weak hand after transfer."""
    engine = BiddingEngine()

    # South: 5 HCP, 5 hearts
    south_hand = create_hand("♠Q65 ♥QJ985 ♦732 ♣84")
    auction = ['1NT', 'Pass', '2♦', 'Pass', '2♥', 'Pass']

    bid, explanation = engine.get_next_bid(south_hand, auction, 'South', 'None')

    assert bid == 'Pass', f"Expected Pass with weak hand, got {bid}"

def test_jacoby_continuation_invitational():
    """Test responder invites with 8-9 HCP."""
    engine = BiddingEngine()

    # South: 8 HCP, 5 hearts (Q=2, J=1, K=3, Q=2 = 8 HCP)
    south_hand = create_hand("♠Q65 ♥KJ985 ♦Q73 ♣84")
    auction = ['1NT', 'Pass', '2♦', 'Pass', '2♥', 'Pass']

    bid, explanation = engine.get_next_bid(south_hand, auction, 'South', 'None')

    assert bid in ['2NT', '3♥'], f"Expected 2NT or 3♥ (invitational), got {bid}"

def test_jacoby_continuation_game_forcing():
    """Test responder bids game with 10+ HCP."""
    engine = BiddingEngine()

    # South: 11 HCP, 6 hearts
    south_hand = create_hand("♠Q6 ♥KJ9852 ♦A73 ♣84")
    auction = ['1NT', 'Pass', '2♦', 'Pass', '2♥', 'Pass']

    bid, explanation = engine.get_next_bid(south_hand, auction, 'South', 'None')

    assert bid == '4♥', f"Expected 4♥ (game with 6-card suit), got {bid}"

def test_jacoby_continuation_after_super_accept():
    """Test responder bids game after super-accept with 8 HCP."""
    engine = BiddingEngine()

    # South: 8 HCP, 5 hearts (Q=2, J=1, K=3, Q=2 = 8 HCP)
    south_hand = create_hand("♠Q65 ♥KJ985 ♦Q73 ♣84")
    auction = ['1NT', 'Pass', '2♦', 'Pass', '3♥', 'Pass']  # 3♥ = super-accept

    bid, explanation = engine.get_next_bid(south_hand, auction, 'South', 'None')

    assert bid == '4♥', f"Expected 4♥ (accepting super-accept), got {bid}"

# ============================================================================
# TEST 3: Stayman - Responder Rebids
# ============================================================================

def test_stayman_rebid_after_2d_weak():
    """Test responder passes 2♦ with weak hand."""
    engine = BiddingEngine()

    # South: 7 HCP, 4 spades (no fit)
    south_hand = create_hand("♠QJ85 ♥Q6 ♦7532 ♣984")
    auction = ['1NT', 'Pass', '2♣', 'Pass', '2♦', 'Pass']  # 2♦ = no major

    bid, explanation = engine.get_next_bid(south_hand, auction, 'South', 'None')

    assert bid == 'Pass', f"Expected Pass with weak hand after 2♦, got {bid}"

def test_stayman_rebid_after_2d_invitational():
    """Test responder bids 2NT with 8-9 HCP after 2♦."""
    engine = BiddingEngine()

    # South: 9 HCP, 4 spades (Q=2, J=1, K=3, Q=2, J=1 = 9 HCP)
    south_hand = create_hand("♠QJ85 ♥K6 ♦Q73 ♣J842")
    auction = ['1NT', 'Pass', '2♣', 'Pass', '2♦', 'Pass']

    bid, explanation = engine.get_next_bid(south_hand, auction, 'South', 'None')

    assert bid == '2NT', f"Expected 2NT (invitational) after 2♦, got {bid}"

def test_stayman_rebid_after_2d_game_forcing():
    """Test responder bids 3NT with 10+ HCP after 2♦."""
    engine = BiddingEngine()

    # South: 11 HCP, 4 spades (no fit)
    south_hand = create_hand("♠QJ85 ♥K6 ♦AQ7 ♣9842")
    auction = ['1NT', 'Pass', '2♣', 'Pass', '2♦', 'Pass']

    bid, explanation = engine.get_next_bid(south_hand, auction, 'South', 'None')

    assert bid == '3NT', f"Expected 3NT (game-forcing) after 2♦, got {bid}"

def test_stayman_rebid_fit_found_invitational():
    """Test responder invites with fit found."""
    engine = BiddingEngine()

    # South: 9 HCP, 4 spades (Q=2, J=1, K=3, Q=2, J=1 = 9 HCP)
    south_hand = create_hand("♠QJ85 ♥K6 ♦Q73 ♣J842")
    auction = ['1NT', 'Pass', '2♣', 'Pass', '2♠', 'Pass']  # 2♠ = 4 spades

    bid, explanation = engine.get_next_bid(south_hand, auction, 'South', 'None')

    assert bid == '3♠', f"Expected 3♠ (invitational with fit), got {bid}"

def test_stayman_rebid_fit_found_game():
    """Test responder bids game with fit found."""
    engine = BiddingEngine()

    # South: 11 HCP, 4 spades (fit found)
    south_hand = create_hand("♠QJ85 ♥K6 ♦AQ7 ♣9842")
    auction = ['1NT', 'Pass', '2♣', 'Pass', '2♠', 'Pass']

    bid, explanation = engine.get_next_bid(south_hand, auction, 'South', 'None')

    assert bid == '4♠', f"Expected 4♠ (game with fit), got {bid}"

# ============================================================================
# TEST 4: Takeout Doubles - HCP Requirement
# ============================================================================

def test_takeout_double_12hcp():
    """Test takeout double with exactly 12 HCP (should work now)."""
    engine = BiddingEngine()

    # East: 12 HCP, 3-1-5-4 shape (shortness in hearts, support for unbid suits)
    # A=4, Q=2, K=3, Q=2, J=1 = 12 HCP
    east_hand = create_hand("♠AQ8 ♥9 ♦KQ752 ♣J865")
    auction = ['1♥', 'Pass']  # Opponent opened 1♥

    bid, explanation = engine.get_next_bid(east_hand, auction, 'East', 'None')

    assert bid == 'X', f"Expected X (takeout double) with 12 HCP, got {bid}"

def test_takeout_double_11hcp():
    """Test no takeout double with 11 HCP (below minimum)."""
    engine = BiddingEngine()

    # East: 11 HCP, 3-3-4-3 shape
    east_hand = create_hand("♠Q98 ♥K94 ♦K752 ♣865")
    auction = ['1♥', 'Pass']

    bid, explanation = engine.get_next_bid(east_hand, auction, 'East', 'None')

    assert bid == 'Pass', f"Expected Pass with 11 HCP, got {bid}"

# ============================================================================
# TEST 5: Blackwood - Signoff Logic
# ============================================================================

def test_blackwood_signoff_missing_2_aces():
    """Test signoff at 5-level when missing 2 aces."""
    engine = BiddingEngine()

    # North: 2 aces, partner showed 0 aces
    north_hand = create_hand("♠AK985 ♥AKQ4 ♦K7 ♣65")
    auction = ['1♠', 'Pass', '3♠', 'Pass', '4NT', 'Pass', '5♣', 'Pass']  # 5♣ = 0 aces

    bid, explanation = engine.get_next_bid(north_hand, auction, 'North', 'None')

    assert bid == '5♠', f"Expected 5♠ (signoff missing 2 aces), got {bid}"

def test_blackwood_signoff_missing_1_ace():
    """Test small slam when missing 1 ace."""
    engine = BiddingEngine()

    # North: 3 aces, partner showed 0 aces
    north_hand = create_hand("♠AK985 ♥AKQ4 ♦A7 ♣65")
    auction = ['1♠', 'Pass', '3♠', 'Pass', '4NT', 'Pass', '5♣', 'Pass']

    bid, explanation = engine.get_next_bid(north_hand, auction, 'North', 'None')

    assert bid == '6♠', f"Expected 6♠ (small slam with 3 aces), got {bid}"

def test_blackwood_ace_response():
    """Test partner responds to Blackwood correctly."""
    engine = BiddingEngine()

    # South: 2 aces
    south_hand = create_hand("♠AK65 ♥Q984 ♦A73 ♣84")
    auction = ['1♠', 'Pass', '3♠', 'Pass', '4NT', 'Pass']

    bid, explanation = engine.get_next_bid(south_hand, auction, 'South', 'None')

    assert bid == '5♥', f"Expected 5♥ (2 aces), got {bid}"

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    print("=" * 70)
    print("PHASE 1 CRITICAL FIXES - COMPREHENSIVE TEST SUITE")
    print("=" * 70)

    tests = [
        # Jacoby Transfers - Super-Accept
        ("Jacoby: Super-accept with 17 HCP + 4-card support", test_jacoby_super_accept_hearts),
        ("Jacoby: No super-accept with doubleton", test_jacoby_no_super_accept_doubleton),
        ("Jacoby: No super-accept with 15 HCP", test_jacoby_no_super_accept_15hcp),

        # Jacoby Transfers - Continuations
        ("Jacoby: Weak hand passes after transfer", test_jacoby_continuation_weak_pass),
        ("Jacoby: Invitational with 8-9 HCP", test_jacoby_continuation_invitational),
        ("Jacoby: Game-forcing with 10+ HCP", test_jacoby_continuation_game_forcing),
        ("Jacoby: Accept super-accept with 8 HCP", test_jacoby_continuation_after_super_accept),

        # Stayman - Responder Rebids
        ("Stayman: Pass 2♦ with weak hand", test_stayman_rebid_after_2d_weak),
        ("Stayman: 2NT after 2♦ with 8-9 HCP", test_stayman_rebid_after_2d_invitational),
        ("Stayman: 3NT after 2♦ with 10+ HCP", test_stayman_rebid_after_2d_game_forcing),
        ("Stayman: Invite with fit found", test_stayman_rebid_fit_found_invitational),
        ("Stayman: Game with fit found", test_stayman_rebid_fit_found_game),

        # Takeout Doubles
        ("Takeout: Double with 12 HCP", test_takeout_double_12hcp),
        ("Takeout: Pass with 11 HCP", test_takeout_double_11hcp),

        # Blackwood
        ("Blackwood: Signoff at 5-level missing 2 aces", test_blackwood_signoff_missing_2_aces),
        ("Blackwood: Small slam missing 1 ace", test_blackwood_signoff_missing_1_ace),
        ("Blackwood: Respond with 2 aces", test_blackwood_ace_response),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        if run_test(test_name, test_func):
            passed += 1
        else:
            failed += 1
        print()

    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total Tests: {len(tests)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    if failed == 0:
        print("\n🎉 ALL PHASE 1 TESTS PASSED!")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review.")

    return failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

"""
Test 1NT overcall with marginal stoppers (Jxx, Qx) when holding 15+ HCP

This addresses the issue where West with 15 HCP and Jxx in opponent's suit
should bid 1NT, not Pass.

Test Case from hand_2025-10-16_14-30-15.json:
- North opens 1♥
- West holds: ♠A98 ♥J76 ♦Q74 ♣AKJ6 (15 HCP, balanced, Jxx in hearts)
- Expected: 1NT overcall (not Pass)
"""

import pytest
from engine.hand import Hand, Card
from engine.overcalls import OvercallModule


def create_hand(cards_str: str) -> Hand:
    """Helper to create hand from string like '♠A98 ♥J76 ♦Q74 ♣AKJ6'"""
    cards = []
    parts = cards_str.split()
    for part in parts:
        suit = part[0]
        ranks = part[1:]
        for rank in ranks:
            cards.append(Card(rank=rank, suit=suit))
    return Hand(cards)


class Test1NTOvercallMarginalStoppers:
    """Test 1NT overcalls with marginal stoppers when holding 15+ HCP"""

    def test_west_hand_from_actual_game_15hcp_jxx_stopper(self):
        """
        Real scenario from hand_2025-10-16_14-30-15.json
        West: 15 HCP, balanced, Jxx in hearts after 1♥ opening
        Should bid 1NT, not Pass
        """
        hand = create_hand('♠A98 ♥J76 ♦Q74 ♣AKJ6')
        module = OvercallModule()

        features = {
            'auction_history': ['1♥'],
            'auction_features': {
                'opener_relationship': 'Opponent',
                'opening_bid': '1♥'
            },
            'my_index': 1,
            'positions': ['North', 'East', 'South', 'West']
        }

        result = module.evaluate(hand, features)

        assert result is not None, "Should make a bid with 15 HCP balanced"
        bid, explanation = result
        assert bid == '1NT', f"Expected 1NT overcall, got {bid}"
        assert '15' in explanation, "Explanation should mention HCP count"
        assert 'stopper' in explanation.lower(), "Explanation should mention stopper"

    def test_15hcp_balanced_jxx_stopper_after_1h(self):
        """15 HCP balanced with Jxx in hearts - should bid 1NT after 1♥ opening"""
        # K=3 + J=1 + A=4 + Q=2 + K=3 + Q=2 = 15 HCP
        hand = create_hand('♠KT9 ♥J76 ♦AQ4 ♣KQ85')
        assert hand.hcp == 15
        assert hand.is_balanced

        module = OvercallModule()
        features = {
            'auction_history': ['1♥'],
            'auction_features': {
                'opener_relationship': 'Opponent',
                'opening_bid': '1♥'
            },
            'my_index': 1,
            'positions': ['North', 'East', 'South', 'West']
        }

        result = module.evaluate(hand, features)
        assert result is not None
        bid, _ = result
        assert bid == '1NT'

    def test_16hcp_balanced_qx_stopper_after_1s(self):
        """16 HCP balanced with Qx in spades - should bid 1NT after 1♠ opening"""
        hand = create_hand('♠Q9 ♥AK7 ♦KJ84 ♣QJ85')
        assert hand.hcp == 16
        assert hand.is_balanced

        module = OvercallModule()
        features = {
            'auction_history': ['1♠'],
            'auction_features': {
                'opener_relationship': 'Opponent',
                'opening_bid': '1♠'
            },
            'my_index': 1,
            'positions': ['North', 'East', 'South', 'West']
        }

        result = module.evaluate(hand, features)
        assert result is not None
        bid, _ = result
        assert bid == '1NT'

    def test_17hcp_balanced_txx_stopper_after_1d(self):
        """17 HCP balanced with Txx in diamonds - should bid 1NT after 1♦ opening"""
        # A=4 + K=3 + K=3 + Q=2 + A=4 + J=1 = 17 HCP
        hand = create_hand('♠AK9 ♥KQ7 ♦T84 ♣AJ85')
        assert hand.hcp == 17
        assert hand.is_balanced

        module = OvercallModule()
        features = {
            'auction_history': ['1♦'],
            'auction_features': {
                'opener_relationship': 'Opponent',
                'opening_bid': '1♦'
            },
            'my_index': 1,
            'positions': ['North', 'East', 'South', 'West']
        }

        result = module.evaluate(hand, features)
        assert result is not None
        bid, _ = result
        assert bid == '1NT'

    def test_14hcp_balanced_jxx_no_overcall(self):
        """
        14 HCP balanced with Jxx - should NOT bid 1NT (below 15 HCP threshold)
        Marginal stoppers only apply with 15+ HCP
        """
        # K=3 + J=1 + A=4 + K=3 + J=1 + Q=2 = 14 HCP
        hand = create_hand('♠KT9 ♥J76 ♦A94 ♣KJQ5')
        assert hand.hcp == 14
        assert hand.is_balanced

        module = OvercallModule()
        features = {
            'auction_history': ['1♥'],
            'auction_features': {
                'opener_relationship': 'Opponent',
                'opening_bid': '1♥'
            },
            'my_index': 1,
            'positions': ['North', 'East', 'South', 'West']
        }

        result = module.evaluate(hand, features)
        # Should either return None or a suit overcall (if 5+ card suit available)
        if result:
            bid, _ = result
            assert bid != '1NT', "Should not bid 1NT with 14 HCP and only Jxx stopper"

    def test_15hcp_balanced_jx_no_overcall(self):
        """
        15 HCP balanced with only Jx (doubleton J) - should NOT bid 1NT
        Need at least Jxx (3 cards) for marginal stopper
        """
        # A=4 + K=3 + J=1 + Q=2 + K=3 + Q=2 = 15 HCP
        hand = create_hand('♠AK9 ♥J7 ♦Q984 ♣KQ85')
        assert hand.hcp == 15

        module = OvercallModule()
        features = {
            'auction_history': ['1♥'],
            'auction_features': {
                'opener_relationship': 'Opponent',
                'opening_bid': '1♥'
            },
            'my_index': 1,
            'positions': ['North', 'East', 'South', 'West']
        }

        result = module.evaluate(hand, features)
        # Should not bid 1NT without proper stopper
        if result:
            bid, _ = result
            assert bid != '1NT', "Should not bid 1NT with only Jx (doubleton)"

    def test_full_stopper_always_works(self):
        """
        Verify that full stoppers (Kxx, Qxxx, etc.) still work with any HCP
        """
        # 12 HCP with Kxx stopper (below 1NT range but has full stopper)
        hand = create_hand('♠K98 ♥K76 ♦Q94 ♣KJ85')
        module = OvercallModule()

        has_stopper = module._has_stopper(hand, '♠')
        assert has_stopper, "Kxx should always be a stopper"

        # Even with low HCP, Qxxx is a stopper
        hand2 = create_hand('♠Q987 ♥K76 ♦94 ♣KJ85')
        has_stopper2 = module._has_stopper(hand2, '♠')
        assert has_stopper2, "Qxxx should always be a stopper"


class TestStopperFunction:
    """Direct tests of the _has_stopper function"""

    def test_jxx_with_15hcp(self):
        """Jxx should be a stopper with 15+ HCP"""
        hand = create_hand('♠A98 ♥J76 ♦Q74 ♣AKJ6')
        assert hand.hcp == 15
        module = OvercallModule()
        assert module._has_stopper(hand, '♥'), "Jxx should be stopper with 15 HCP"

    def test_jxx_with_14hcp(self):
        """Jxx should NOT be a stopper with 14 HCP"""
        # K=3 + J=1 + Q=2 + K=3 + A=4 + J=1 = 14 HCP
        hand = create_hand('♠K98 ♥J76 ♦Q74 ♣KAJ5')
        assert hand.hcp == 14
        module = OvercallModule()
        assert not module._has_stopper(hand, '♥'), "Jxx should not be stopper with 14 HCP"

    def test_qx_with_16hcp(self):
        """Qx should be a stopper with 15+ HCP"""
        hand = create_hand('♠Q9 ♥AK7 ♦KJ84 ♣QJ85')
        assert hand.hcp == 16
        module = OvercallModule()
        assert module._has_stopper(hand, '♠'), "Qx should be stopper with 16 HCP"

    def test_txx_with_16hcp(self):
        """Txx should be a stopper with 16+ HCP"""
        # A=4 + K=3 + K=3 + Q=2 + A=4 + J=1 = 17 HCP
        hand = create_hand('♠AK9 ♥KQ7 ♦T84 ♣AJ85')
        assert hand.hcp == 17
        module = OvercallModule()
        assert module._has_stopper(hand, '♦'), "Txx should be stopper with 17 HCP"

    def test_txx_with_15hcp(self):
        """Txx should NOT be a stopper with only 15 HCP (need 16+)"""
        # A=4 + K=3 + K=3 + K=3 + Q=2 = 15 HCP
        hand = create_hand('♠AK9 ♥K97 ♦T84 ♣KQ85')
        assert hand.hcp == 15
        module = OvercallModule()
        assert not module._has_stopper(hand, '♦'), "Txx should not be stopper with only 15 HCP"

    def test_full_stoppers(self):
        """Verify traditional full stoppers still work"""
        module = OvercallModule()

        # Ace always works (13 cards: A98 + K76 + Q74 + KJ85 = 3+3+3+4)
        hand = create_hand('♠A98 ♥K76 ♦Q74 ♣KJ85')
        assert module._has_stopper(hand, '♠')

        # Kx+ works (13 cards: K97 + K76 + Q74 + AJ85 = 3+3+3+4)
        hand = create_hand('♠K97 ♥K76 ♦Q74 ♣AJ85')
        assert module._has_stopper(hand, '♠')

        # Qxx+ works (13 cards: Q98 + K76 + K74 + AJ85 = 3+3+3+4)
        hand = create_hand('♠Q98 ♥K76 ♦K74 ♣AJ85')
        assert module._has_stopper(hand, '♠')

        # Jxxx+ works (with any HCP) (13 cards: J987 + K76 + K74 + AJ8 = 4+3+3+3)
        hand = create_hand('♠J987 ♥K76 ♦K74 ♣AJ8')
        assert module._has_stopper(hand, '♠')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

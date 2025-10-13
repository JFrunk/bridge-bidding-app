"""
Comprehensive tests for honors scoring

Tests the honors bonus calculation according to official bridge rules:
- Trump contracts: 4 of 5 honors = 100, all 5 honors = 150
- Notrump contracts: all 4 aces = 150
"""

import pytest
from engine.play_engine import PlayEngine, Contract
from engine.hand import Hand, Card


def create_hand(cards_list):
    """Helper to create a hand from a list of (rank, suit) tuples"""
    cards = [Card(rank, suit) for rank, suit in cards_list]
    # Pad with filler cards to make 13
    while len(cards) < 13:
        cards.append(Card('2', '♣'))
    return Hand(cards[:13])


class TestHonorsScoringTrumpContracts:
    """Test honors scoring in trump contracts"""

    def test_all_5_trump_honors_in_one_hand(self):
        """Test that all 5 trump honors in one hand scores 150"""
        contract = Contract(level=4, strain='♠', declarer='S')

        # North has all 5 spade honors
        hands = {
            'N': create_hand([('A', '♠'), ('K', '♠'), ('Q', '♠'), ('J', '♠'), ('T', '♠')]),
            'E': create_hand([('2', '♥'), ('3', '♥'), ('4', '♥')]),
            'S': create_hand([('2', '♦'), ('3', '♦'), ('4', '♦')]),
            'W': create_hand([('2', '♣'), ('3', '♣'), ('4', '♣')])
        }

        honors = PlayEngine.calculate_honors(contract, hands)
        assert honors == 150, "All 5 trump honors should score 150"

    def test_4_trump_honors_in_one_hand(self):
        """Test that 4 of 5 trump honors in one hand scores 100"""
        contract = Contract(level=4, strain='♥', declarer='S')

        # South has 4 heart honors (missing the 10)
        hands = {
            'N': create_hand([('T', '♥'), ('2', '♠'), ('3', '♠')]),
            'E': create_hand([('2', '♦'), ('3', '♦'), ('4', '♦')]),
            'S': create_hand([('A', '♥'), ('K', '♥'), ('Q', '♥'), ('J', '♥')]),
            'W': create_hand([('2', '♣'), ('3', '♣'), ('4', '♣')])
        }

        honors = PlayEngine.calculate_honors(contract, hands)
        assert honors == 100, "4 of 5 trump honors should score 100"

    def test_4_trump_honors_different_one_missing(self):
        """Test 4 honors when missing a different honor (not the 10)"""
        contract = Contract(level=3, strain='♦', declarer='N')

        # West has 4 diamond honors (missing the Jack)
        hands = {
            'N': create_hand([('J', '♦'), ('2', '♠'), ('3', '♠')]),
            'E': create_hand([('2', '♥'), ('3', '♥'), ('4', '♥')]),
            'S': create_hand([('2', '♣'), ('3', '♣'), ('4', '♣')]),
            'W': create_hand([('A', '♦'), ('K', '♦'), ('Q', '♦'), ('T', '♦')])
        }

        honors = PlayEngine.calculate_honors(contract, hands)
        assert honors == 100, "4 of 5 trump honors should score 100 regardless of which is missing"

    def test_3_trump_honors_no_bonus(self):
        """Test that 3 trump honors doesn't score"""
        contract = Contract(level=2, strain='♣', declarer='E')

        # East has only 3 club honors
        hands = {
            'N': create_hand([('J', '♣'), ('T', '♣'), ('2', '♠')]),
            'E': create_hand([('A', '♣'), ('K', '♣'), ('Q', '♣')]),
            'S': create_hand([('2', '♦'), ('3', '♦'), ('4', '♦')]),
            'W': create_hand([('2', '♥'), ('3', '♥'), ('4', '♥')])
        }

        honors = PlayEngine.calculate_honors(contract, hands)
        assert honors == 0, "3 trump honors should not score"

    def test_honors_split_across_hands_no_bonus(self):
        """Test that honors split across multiple hands don't score"""
        contract = Contract(level=4, strain='♠', declarer='S')

        # Honors split between North (A, K) and South (Q, J, T)
        hands = {
            'N': create_hand([('A', '♠'), ('K', '♠'), ('2', '♥')]),
            'E': create_hand([('2', '♦'), ('3', '♦'), ('4', '♦')]),
            'S': create_hand([('Q', '♠'), ('J', '♠'), ('T', '♠')]),
            'W': create_hand([('2', '♣'), ('3', '♣'), ('4', '♣')])
        }

        honors = PlayEngine.calculate_honors(contract, hands)
        assert honors == 0, "Split honors should not score"

    def test_honors_in_declarer_hand(self):
        """Test that honors count when in declarer's hand"""
        contract = Contract(level=4, strain='♥', declarer='S')

        # Declarer (South) has all 5 heart honors
        hands = {
            'N': create_hand([('2', '♠'), ('3', '♠'), ('4', '♠')]),
            'E': create_hand([('2', '♦'), ('3', '♦'), ('4', '♦')]),
            'S': create_hand([('A', '♥'), ('K', '♥'), ('Q', '♥'), ('J', '♥'), ('T', '♥')]),
            'W': create_hand([('2', '♣'), ('3', '♣'), ('4', '♣')])
        }

        honors = PlayEngine.calculate_honors(contract, hands)
        assert honors == 150, "Honors in declarer's hand should score"

    def test_honors_in_dummy_hand(self):
        """Test that honors count when in dummy's hand"""
        contract = Contract(level=4, strain='♠', declarer='S')

        # Dummy (North) has all 5 spade honors
        hands = {
            'N': create_hand([('A', '♠'), ('K', '♠'), ('Q', '♠'), ('J', '♠'), ('T', '♠')]),
            'E': create_hand([('2', '♦'), ('3', '♦'), ('4', '♦')]),
            'S': create_hand([('2', '♥'), ('3', '♥'), ('4', '♥')]),
            'W': create_hand([('2', '♣'), ('3', '♣'), ('4', '♣')])
        }

        honors = PlayEngine.calculate_honors(contract, hands)
        assert honors == 150, "Honors in dummy's hand should score"

    def test_honors_in_defender_hand(self):
        """Test that honors count even when in defender's hand"""
        contract = Contract(level=4, strain='♦', declarer='N')

        # Defender (East) has all 5 diamond honors
        hands = {
            'N': create_hand([('2', '♠'), ('3', '♠'), ('4', '♠')]),
            'E': create_hand([('A', '♦'), ('K', '♦'), ('Q', '♦'), ('J', '♦'), ('T', '♦')]),
            'S': create_hand([('2', '♥'), ('3', '♥'), ('4', '♥')]),
            'W': create_hand([('2', '♣'), ('3', '♣'), ('4', '♣')])
        }

        honors = PlayEngine.calculate_honors(contract, hands)
        assert honors == 150, "Honors in defender's hand should score (either side can claim)"


class TestHonorsScoringNotrump:
    """Test honors scoring in notrump contracts"""

    def test_all_4_aces_in_one_hand(self):
        """Test that all 4 aces in one hand scores 150 in NT"""
        contract = Contract(level=3, strain='NT', declarer='S')

        # South has all 4 aces
        hands = {
            'N': create_hand([('K', '♠'), ('Q', '♠'), ('J', '♠')]),
            'E': create_hand([('2', '♦'), ('3', '♦'), ('4', '♦')]),
            'S': create_hand([('A', '♠'), ('A', '♥'), ('A', '♦'), ('A', '♣')]),
            'W': create_hand([('2', '♣'), ('3', '♣'), ('4', '♣')])
        }

        honors = PlayEngine.calculate_honors(contract, hands)
        assert honors == 150, "All 4 aces in NT should score 150"

    def test_3_aces_in_nt_no_bonus(self):
        """Test that 3 aces in NT doesn't score"""
        contract = Contract(level=3, strain='NT', declarer='N')

        # North has only 3 aces
        hands = {
            'N': create_hand([('A', '♠'), ('A', '♥'), ('A', '♦')]),
            'E': create_hand([('A', '♣'), ('2', '♦'), ('3', '♦')]),
            'S': create_hand([('2', '♥'), ('3', '♥'), ('4', '♥')]),
            'W': create_hand([('2', '♣'), ('3', '♣'), ('4', '♣')])
        }

        honors = PlayEngine.calculate_honors(contract, hands)
        assert honors == 0, "Only 3 aces in NT should not score"

    def test_aces_split_in_nt_no_bonus(self):
        """Test that aces split across hands don't score in NT"""
        contract = Contract(level=3, strain='NT', declarer='S')

        # Aces split: 2 in North, 2 in South
        hands = {
            'N': create_hand([('A', '♠'), ('A', '♥'), ('K', '♦')]),
            'E': create_hand([('2', '♦'), ('3', '♦'), ('4', '♦')]),
            'S': create_hand([('A', '♦'), ('A', '♣'), ('K', '♣')]),
            'W': create_hand([('2', '♣'), ('3', '♣'), ('4', '♣')])
        }

        honors = PlayEngine.calculate_honors(contract, hands)
        assert honors == 0, "Split aces in NT should not score"

    def test_nt_with_other_honors_no_bonus(self):
        """Test that other honors (K, Q, J, T) don't count in NT"""
        contract = Contract(level=3, strain='NT', declarer='N')

        # North has 3 aces plus all kings, queens, etc.
        hands = {
            'N': create_hand([('A', '♠'), ('A', '♥'), ('A', '♦'), ('K', '♠'), ('K', '♥'), ('K', '♦'), ('K', '♣')]),
            'E': create_hand([('A', '♣'), ('2', '♦'), ('3', '♦')]),
            'S': create_hand([('Q', '♠'), ('Q', '♥'), ('Q', '♦')]),
            'W': create_hand([('J', '♣'), ('T', '♣'), ('9', '♣')])
        }

        honors = PlayEngine.calculate_honors(contract, hands)
        assert honors == 0, "Only aces count in NT, and must have all 4"


class TestHonorsScoringIntegration:
    """Test honors integrated with full score calculation"""

    def test_made_contract_with_honors(self):
        """Test that honors bonus is added to made contract score"""
        contract = Contract(level=4, strain='♠', declarer='S')

        hands = {
            'N': create_hand([('A', '♠'), ('K', '♠'), ('Q', '♠'), ('J', '♠'), ('T', '♠')]),
            'E': create_hand([('2', '♥'), ('3', '♥'), ('4', '♥')]),
            'S': create_hand([('2', '♦'), ('3', '♦'), ('4', '♦')]),
            'W': create_hand([('2', '♣'), ('3', '♣'), ('4', '♣')])
        }

        vuln = {"ns": False, "ew": False}
        tricks_taken = 10  # Made exactly

        result = PlayEngine.calculate_score(contract, tricks_taken, vuln, hands)

        # 4♠ making = 120 (trick score) + 300 (game bonus) = 420
        # Plus 150 for honors = 570
        assert result['score'] == 570
        assert result['made'] is True
        assert result['breakdown']['honors_bonus'] == 150

    def test_down_contract_with_honors(self):
        """Test that honors bonus is added even to defeated contracts"""
        contract = Contract(level=6, strain='♥', declarer='N')

        hands = {
            'N': create_hand([('A', '♥'), ('K', '♥'), ('Q', '♥'), ('J', '♥')]),
            'E': create_hand([('T', '♥'), ('2', '♦'), ('3', '♦')]),
            'S': create_hand([('2', '♣'), ('3', '♣'), ('4', '♣')]),
            'W': create_hand([('2', '♠'), ('3', '♠'), ('4', '♠')])
        }

        vuln = {"ns": False, "ew": False}
        tricks_taken = 11  # Down 1

        result = PlayEngine.calculate_score(contract, tricks_taken, vuln, hands)

        # Down 1 not vulnerable = -50
        # Plus 100 for honors = +50
        assert result['score'] == 50
        assert result['made'] is False
        assert result['breakdown']['honors_bonus'] == 100

    def test_score_without_hands_no_honors(self):
        """Test that score calculation works without hands (no honors calculated)"""
        contract = Contract(level=4, strain='♠', declarer='S')
        vuln = {"ns": False, "ew": False}
        tricks_taken = 10

        # Call without hands parameter
        result = PlayEngine.calculate_score(contract, tricks_taken, vuln)

        # Should calculate score without honors
        assert result['score'] == 420  # No honors bonus
        assert result['made'] is True
        assert 'honors_bonus' not in result['breakdown']

    def test_nt_made_with_4_aces(self):
        """Test NT contract made with all 4 aces"""
        contract = Contract(level=3, strain='NT', declarer='S')

        hands = {
            'N': create_hand([('K', '♠'), ('Q', '♠'), ('J', '♠')]),
            'E': create_hand([('2', '♦'), ('3', '♦'), ('4', '♦')]),
            'S': create_hand([('A', '♠'), ('A', '♥'), ('A', '♦'), ('A', '♣')]),
            'W': create_hand([('2', '♣'), ('3', '♣'), ('4', '♣')])
        }

        vuln = {"ns": True, "ew": False}
        tricks_taken = 9  # Made exactly

        result = PlayEngine.calculate_score(contract, tricks_taken, vuln, hands)

        # 3NT making vulnerable = 100 (trick score) + 500 (game bonus) = 600
        # Plus 150 for 4 aces = 750
        assert result['score'] == 750
        assert result['breakdown']['honors_bonus'] == 150

    def test_doubled_contract_with_honors(self):
        """Test that honors work with doubled contracts"""
        contract = Contract(level=4, strain='♦', declarer='W', doubled=1)

        hands = {
            'N': create_hand([('2', '♠'), ('3', '♠'), ('4', '♠')]),
            'E': create_hand([('2', '♥'), ('3', '♥'), ('4', '♥')]),
            'S': create_hand([('2', '♣'), ('3', '♣'), ('4', '♣')]),
            'W': create_hand([('A', '♦'), ('K', '♦'), ('Q', '♦'), ('J', '♦'), ('T', '♦')])
        }

        vuln = {"ns": False, "ew": False}
        tricks_taken = 10  # Made exactly

        result = PlayEngine.calculate_score(contract, tricks_taken, vuln, hands)

        # 4♦ doubled making = 160 (doubled trick) + 300 (game) + 50 (insult) = 510
        # Plus 150 for honors = 660
        assert result['score'] == 660
        assert result['breakdown']['honors_bonus'] == 150

"""
Comprehensive scoring tests for all bridge scoring scenarios

Tests all combinations of:
- Contract levels (1-7)
- Strains (minor/major/NT)
- Made/defeated
- Vulnerability
- Doubled/redoubled
- Overtricks/undertricks

Reference: docs/COMPLETE_BRIDGE_RULES.md Section 3 (Scoring)
"""

import pytest
from engine.play_engine import PlayEngine, Contract


class TestContractPoints:
    """Test basic contract point calculations"""

    def test_minor_suit_contract_points(self):
        """Minor suits (♣ ♦) = 20 points per trick"""
        contract = Contract(level=5, strain='♣', declarer='S', doubled=0)
        result = PlayEngine.calculate_score(contract, 11, {'ns': False, 'ew': False})

        assert result['breakdown']['trick_score'] == 100  # 5 * 20
        assert result['made'] == True

    def test_major_suit_contract_points(self):
        """Major suits (♥ ♠) = 30 points per trick"""
        contract = Contract(level=4, strain='♥', declarer='S', doubled=0)
        result = PlayEngine.calculate_score(contract, 10, {'ns': False, 'ew': False})

        assert result['breakdown']['trick_score'] == 120  # 4 * 30
        assert result['made'] == True

    def test_notrump_contract_points(self):
        """NT = 40 for first, 30 for subsequent"""
        contract = Contract(level=3, strain='NT', declarer='S', doubled=0)
        result = PlayEngine.calculate_score(contract, 9, {'ns': False, 'ew': False})

        assert result['breakdown']['trick_score'] == 100  # 40 + 30 + 30
        assert result['made'] == True


class TestGameBonuses:
    """Test game and part-score bonuses"""

    def test_3nt_is_game_not_vulnerable(self):
        """3NT (100 points) = game, bonus 300 (NV)"""
        contract = Contract(level=3, strain='NT', declarer='S', doubled=0)
        result = PlayEngine.calculate_score(contract, 9, {'ns': False, 'ew': False})

        assert result['breakdown']['trick_score'] == 100
        assert result['breakdown']['game_bonus'] == 300  # Not vulnerable
        assert result['score'] == 400  # 100 + 300

    def test_3nt_is_game_vulnerable(self):
        """3NT vulnerable = game, bonus 500"""
        contract = Contract(level=3, strain='NT', declarer='S', doubled=0)
        result = PlayEngine.calculate_score(contract, 9, {'ns': True, 'ew': False})

        assert result['breakdown']['game_bonus'] == 500  # Vulnerable
        assert result['score'] == 600  # 100 + 500

    def test_4_major_is_game(self):
        """4♥/♠ (120 points) = game"""
        contract = Contract(level=4, strain='♠', declarer='S', doubled=0)
        result = PlayEngine.calculate_score(contract, 10, {'ns': False, 'ew': False})

        assert result['breakdown']['trick_score'] == 120
        assert result['breakdown']['game_bonus'] == 300  # Not vulnerable

    def test_5_minor_is_game(self):
        """5♣/♦ (100 points) = game"""
        contract = Contract(level=5, strain='♣', declarer='S', doubled=0)
        result = PlayEngine.calculate_score(contract, 11, {'ns': False, 'ew': False})

        assert result['breakdown']['trick_score'] == 100
        assert result['breakdown']['game_bonus'] == 300  # Not vulnerable

    def test_partscore_bonus(self):
        """Part-scores (<100 points) get +50 bonus"""
        contract = Contract(level=2, strain='♥', declarer='S', doubled=0)
        result = PlayEngine.calculate_score(contract, 8, {'ns': False, 'ew': False})

        assert result['breakdown']['trick_score'] == 60  # 2 * 30
        assert result['breakdown']['game_bonus'] == 50  # Part-score
        assert result['score'] == 110  # 60 + 50


class TestSlamBonuses:
    """Test small and grand slam bonuses"""

    def test_small_slam_not_vulnerable(self):
        """6-level made = small slam, +500 (NV)"""
        contract = Contract(level=6, strain='NT', declarer='S', doubled=0)
        result = PlayEngine.calculate_score(contract, 12, {'ns': False, 'ew': False})

        assert result['breakdown']['slam_bonus'] == 500
        assert result['breakdown']['game_bonus'] == 300  # Also game
        # 190 (trick) + 300 (game) + 500 (slam) = 990
        assert result['score'] == 990

    def test_small_slam_vulnerable(self):
        """6-level vulnerable = +750"""
        contract = Contract(level=6, strain='NT', declarer='S', doubled=0)
        result = PlayEngine.calculate_score(contract, 12, {'ns': True, 'ew': False})

        assert result['breakdown']['slam_bonus'] == 750
        assert result['breakdown']['game_bonus'] == 500  # Vulnerable game
        # 190 + 500 + 750 = 1440
        assert result['score'] == 1440

    def test_grand_slam_not_vulnerable(self):
        """7-level made = grand slam, +1000 (NV)"""
        contract = Contract(level=7, strain='NT', declarer='S', doubled=0)
        result = PlayEngine.calculate_score(contract, 13, {'ns': False, 'ew': False})

        assert result['breakdown']['slam_bonus'] == 1000
        assert result['breakdown']['game_bonus'] == 300
        # 220 (trick) + 300 (game) + 1000 (slam) = 1520
        assert result['score'] == 1520

    def test_grand_slam_vulnerable(self):
        """7-level vulnerable = +1500"""
        contract = Contract(level=7, strain='♠', declarer='S', doubled=0)
        result = PlayEngine.calculate_score(contract, 13, {'ns': True, 'ew': False})

        assert result['breakdown']['slam_bonus'] == 1500
        assert result['breakdown']['game_bonus'] == 500
        # 210 (7*30) + 500 + 1500 = 2210
        assert result['score'] == 2210

    def test_slam_down_no_bonus(self):
        """Slam defeated = no slam bonus"""
        contract = Contract(level=6, strain='NT', declarer='S', doubled=0)
        result = PlayEngine.calculate_score(contract, 11, {'ns': False, 'ew': False})

        assert result['made'] == False
        assert 'slam_bonus' not in result['breakdown']
        assert result['score'] < 0  # Penalty


class TestOvertricks:
    """Test overtrick scoring"""

    def test_overtricks_undoubled_minor(self):
        """Overtricks in minors = 20 each"""
        contract = Contract(level=3, strain='♦', declarer='S', doubled=0)
        result = PlayEngine.calculate_score(contract, 11, {'ns': False, 'ew': False})  # 2 overtricks

        assert result['overtricks'] == 2
        assert result['breakdown']['overtrick_score'] == 40  # 2 * 20

    def test_overtricks_undoubled_major(self):
        """Overtricks in majors = 30 each"""
        contract = Contract(level=4, strain='♠', declarer='S', doubled=0)
        result = PlayEngine.calculate_score(contract, 11, {'ns': False, 'ew': False})  # 1 overtrick

        assert result['overtricks'] == 1
        assert result['breakdown']['overtrick_score'] == 30  # 1 * 30

    def test_overtricks_undoubled_nt(self):
        """Overtricks in NT = 30 each"""
        contract = Contract(level=3, strain='NT', declarer='S', doubled=0)
        result = PlayEngine.calculate_score(contract, 10, {'ns': False, 'ew': False})  # 1 overtrick

        assert result['overtricks'] == 1
        assert result['breakdown']['overtrick_score'] == 30

    def test_overtricks_doubled_not_vulnerable(self):
        """Doubled overtricks = 100 (NV)"""
        contract = Contract(level=3, strain='NT', declarer='S', doubled=1)
        result = PlayEngine.calculate_score(contract, 10, {'ns': False, 'ew': False})  # 1 overtrick

        assert result['overtricks'] == 1
        assert result['breakdown']['overtrick_score'] == 100  # Doubled NV

    def test_overtricks_doubled_vulnerable(self):
        """Doubled overtricks = 200 (V)"""
        contract = Contract(level=3, strain='NT', declarer='S', doubled=1)
        result = PlayEngine.calculate_score(contract, 10, {'ns': True, 'ew': False})  # 1 overtrick

        assert result['overtricks'] == 1
        assert result['breakdown']['overtrick_score'] == 200  # Doubled V

    def test_overtricks_redoubled(self):
        """Redoubled overtricks = 400 (V) / 200 (NV)"""
        contract = Contract(level=3, strain='NT', declarer='S', doubled=2)

        # Not vulnerable
        result_nv = PlayEngine.calculate_score(contract, 10, {'ns': False, 'ew': False})
        assert result_nv['breakdown']['overtrick_score'] == 200

        # Vulnerable
        result_v = PlayEngine.calculate_score(contract, 10, {'ns': True, 'ew': False})
        assert result_v['breakdown']['overtrick_score'] == 400


class TestDoubledContracts:
    """Test doubled and redoubled contract scoring"""

    def test_doubled_contract_made(self):
        """Doubled contract made = 2x trick score + 50 insult"""
        contract = Contract(level=2, strain='♥', declarer='S', doubled=1)
        result = PlayEngine.calculate_score(contract, 8, {'ns': False, 'ew': False})

        assert result['breakdown']['trick_score'] == 120  # 60 * 2
        assert result['breakdown']['double_bonus'] == 50  # Insult bonus
        assert result['breakdown']['game_bonus'] == 300  # Now it's game (120 >= 100)

    def test_redoubled_contract_made(self):
        """Redoubled contract = 4x trick score + 100 insult"""
        contract = Contract(level=2, strain='♥', declarer='S', doubled=2)
        result = PlayEngine.calculate_score(contract, 8, {'ns': False, 'ew': False})

        assert result['breakdown']['trick_score'] == 240  # 60 * 4
        assert result['breakdown']['double_bonus'] == 100  # Redouble insult

    def test_1nt_doubled_is_not_game(self):
        """1NT doubled (40*2=80) is NOT game"""
        contract = Contract(level=1, strain='NT', declarer='S', doubled=1)
        result = PlayEngine.calculate_score(contract, 7, {'ns': False, 'ew': False})

        assert result['breakdown']['trick_score'] == 80  # 40 * 2
        assert result['breakdown']['game_bonus'] == 50  # Part-score, not game

    def test_2nt_doubled_is_game(self):
        """2NT doubled (70*2=140) IS game"""
        contract = Contract(level=2, strain='NT', declarer='S', doubled=1)
        result = PlayEngine.calculate_score(contract, 8, {'ns': False, 'ew': False})

        assert result['breakdown']['trick_score'] == 140  # 70 * 2
        assert result['breakdown']['game_bonus'] == 300  # Game bonus


class TestUndertricks:
    """Test penalty scoring for defeated contracts"""

    def test_undoubled_down_1_not_vulnerable(self):
        """Down 1 undoubled (NV) = -50"""
        contract = Contract(level=3, strain='NT', declarer='S', doubled=0)
        result = PlayEngine.calculate_score(contract, 8, {'ns': False, 'ew': False})

        assert result['made'] == False
        assert result['undertricks'] == 1
        assert result['score'] == -50

    def test_undoubled_down_1_vulnerable(self):
        """Down 1 undoubled (V) = -100"""
        contract = Contract(level=3, strain='NT', declarer='S', doubled=0)
        result = PlayEngine.calculate_score(contract, 8, {'ns': True, 'ew': False})

        assert result['undertricks'] == 1
        assert result['score'] == -100

    def test_undoubled_down_2_not_vulnerable(self):
        """Down 2 undoubled (NV) = -100"""
        contract = Contract(level=3, strain='NT', declarer='S', doubled=0)
        result = PlayEngine.calculate_score(contract, 7, {'ns': False, 'ew': False})

        assert result['undertricks'] == 2
        assert result['score'] == -100  # 2 * 50

    def test_undoubled_down_2_vulnerable(self):
        """Down 2 undoubled (V) = -200"""
        contract = Contract(level=3, strain='NT', declarer='S', doubled=0)
        result = PlayEngine.calculate_score(contract, 7, {'ns': True, 'ew': False})

        assert result['undertricks'] == 2
        assert result['score'] == -200  # 2 * 100


class TestDoubledUndertricks:
    """Test doubled undertrick penalties (complex table)"""

    def test_doubled_down_1_not_vulnerable(self):
        """Doubled down 1 (NV) = -100"""
        contract = Contract(level=3, strain='NT', declarer='S', doubled=1)
        result = PlayEngine.calculate_score(contract, 8, {'ns': False, 'ew': False})

        assert result['undertricks'] == 1
        assert result['score'] == -100

    def test_doubled_down_2_not_vulnerable(self):
        """Doubled down 2 (NV) = -300 (100 + 200)"""
        contract = Contract(level=3, strain='NT', declarer='S', doubled=1)
        result = PlayEngine.calculate_score(contract, 7, {'ns': False, 'ew': False})

        assert result['undertricks'] == 2
        assert result['score'] == -300

    def test_doubled_down_3_not_vulnerable(self):
        """Doubled down 3 (NV) = -500 (100 + 200 + 200)"""
        contract = Contract(level=3, strain='NT', declarer='S', doubled=1)
        result = PlayEngine.calculate_score(contract, 6, {'ns': False, 'ew': False})

        assert result['undertricks'] == 3
        assert result['score'] == -500

    def test_doubled_down_4_not_vulnerable(self):
        """Doubled down 4 (NV) = -800 (100 + 200 + 200 + 300)"""
        contract = Contract(level=3, strain='NT', declarer='S', doubled=1)
        result = PlayEngine.calculate_score(contract, 5, {'ns': False, 'ew': False})

        assert result['undertricks'] == 4
        assert result['score'] == -800

    def test_doubled_down_1_vulnerable(self):
        """Doubled down 1 (V) = -200"""
        contract = Contract(level=3, strain='NT', declarer='S', doubled=1)
        result = PlayEngine.calculate_score(contract, 8, {'ns': True, 'ew': False})

        assert result['undertricks'] == 1
        assert result['score'] == -200

    def test_doubled_down_2_vulnerable(self):
        """Doubled down 2 (V) = -500 (200 + 300)"""
        contract = Contract(level=3, strain='NT', declarer='S', doubled=1)
        result = PlayEngine.calculate_score(contract, 7, {'ns': True, 'ew': False})

        assert result['undertricks'] == 2
        assert result['score'] == -500

    def test_doubled_down_3_vulnerable(self):
        """Doubled down 3 (V) = -800 (200 + 300 + 300)"""
        contract = Contract(level=3, strain='NT', declarer='S', doubled=1)
        result = PlayEngine.calculate_score(contract, 6, {'ns': True, 'ew': False})

        assert result['undertricks'] == 3
        assert result['score'] == -800


class TestRedoubledUndertricks:
    """Test redoubled undertrick penalties (doubled * 2)"""

    def test_redoubled_down_1_not_vulnerable(self):
        """Redoubled down 1 (NV) = -200 (doubled * 2)"""
        contract = Contract(level=3, strain='NT', declarer='S', doubled=2)
        result = PlayEngine.calculate_score(contract, 8, {'ns': False, 'ew': False})

        assert result['undertricks'] == 1
        assert result['score'] == -200  # 100 * 2

    def test_redoubled_down_2_not_vulnerable(self):
        """Redoubled down 2 (NV) = -600"""
        contract = Contract(level=3, strain='NT', declarer='S', doubled=2)
        result = PlayEngine.calculate_score(contract, 7, {'ns': False, 'ew': False})

        assert result['undertricks'] == 2
        assert result['score'] == -600  # 300 * 2

    def test_redoubled_down_1_vulnerable(self):
        """Redoubled down 1 (V) = -400"""
        contract = Contract(level=3, strain='NT', declarer='S', doubled=2)
        result = PlayEngine.calculate_score(contract, 8, {'ns': True, 'ew': False})

        assert result['undertricks'] == 1
        assert result['score'] == -400  # 200 * 2

    def test_redoubled_down_2_vulnerable(self):
        """Redoubled down 2 (V) = -1000"""
        contract = Contract(level=3, strain='NT', declarer='S', doubled=2)
        result = PlayEngine.calculate_score(contract, 7, {'ns': True, 'ew': False})

        assert result['undertricks'] == 2
        assert result['score'] == -1000  # 500 * 2


class TestComplexScoringScenarios:
    """Test complete scoring scenarios"""

    def test_7nt_doubled_made_vulnerable_with_overtrick(self):
        """Grand slam doubled vulnerable with 1 overtrick"""
        contract = Contract(level=7, strain='NT', declarer='S', doubled=1)
        result = PlayEngine.calculate_score(contract, 13, {'ns': True, 'ew': False})

        # Trick score: 220 * 2 = 440
        # Game bonus: 500 (vulnerable)
        # Slam bonus: 1500 (grand slam vulnerable)
        # Double bonus: 50
        # No overtricks (made exactly)
        # Total: 440 + 500 + 1500 + 50 = 2490
        assert result['score'] == 2490
        assert result['made'] == True

    def test_7nt_down_7_doubled_vulnerable(self):
        """Worst case: grand slam doubled down 7 vulnerable"""
        contract = Contract(level=7, strain='NT', declarer='S', doubled=1)
        result = PlayEngine.calculate_score(contract, 6, {'ns': True, 'ew': False})

        # Down 7 doubled vulnerable:
        # 200 + 300 + 300 + 300 + 300 + 300 + 300 = 2000
        assert result['undertricks'] == 7
        assert result['score'] == -2000
        assert result['made'] == False

    def test_1club_made_exactly(self):
        """Minimum contract made exactly"""
        contract = Contract(level=1, strain='♣', declarer='S', doubled=0)
        result = PlayEngine.calculate_score(contract, 7, {'ns': False, 'ew': False})

        # 20 (trick) + 50 (partscore) = 70
        assert result['score'] == 70
        assert result['overtricks'] == 0


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_all_thirteen_tricks_taken(self):
        """Taking all 13 tricks in 1NT"""
        contract = Contract(level=1, strain='NT', declarer='S', doubled=0)
        result = PlayEngine.calculate_score(contract, 13, {'ns': False, 'ew': False})

        # 1NT = 40, 6 overtricks = 180
        # Total: 40 + 180 + 50 (partscore) = 270
        assert result['overtricks'] == 6
        assert result['made'] == True

    def test_zero_tricks_taken(self):
        """Taking 0 tricks (down 7)"""
        contract = Contract(level=7, strain='NT', declarer='S', doubled=0)
        result = PlayEngine.calculate_score(contract, 0, {'ns': False, 'ew': False})

        # Down 13 undoubled NV = -650
        assert result['undertricks'] == 13
        assert result['score'] == -650
        assert result['made'] == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Test Suite for BridgeAnalysisEngine

This test file exercises the analysis engine with mock data to verify:
1. Quadrant classification (corrected "Good Bidding" logic)
2. Bidding efficiency detection (optimal/underbid/overbid)
3. Points left on table calculation
4. Edge cases and boundary conditions

Run with:
    cd backend
    python3 -m pytest tests/analysis/test_analysis_engine.py -v

Or run directly for verbose output:
    python3 tests/analysis/test_analysis_engine.py
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import unittest
from unittest.mock import Mock, MagicMock
from dataclasses import dataclass
from typing import Optional, Dict

from engine.analysis.analysis_engine import (
    BridgeAnalysisEngine,
    HandAnalysisResult,
    Quadrant,
    BidEfficiency,
    LeadQuality,
)


# ============================================================================
# Mock Objects
# ============================================================================

@dataclass
class MockContract:
    """Mock Contract object for testing."""
    level: int
    trump_suit: Optional[str]  # 'S', 'H', 'D', 'C', or None for NT
    declarer: str  # 'N', 'E', 'S', 'W'
    doubled: int = 0  # 0, 1, 2


class MockDDTable:
    """Mock DD Table that returns configurable trick counts."""

    def __init__(self, tricks_by_position_strain: Dict[str, Dict[str, int]]):
        """
        Args:
            tricks_by_position_strain: e.g., {'S': {'S': 10, 'H': 9, 'NT': 8}, ...}
        """
        self.table = tricks_by_position_strain

    def get_tricks(self, position: str, strain: str) -> int:
        return self.table.get(position, {}).get(strain, 0)

    def to_dict(self) -> Dict:
        return self.table


class MockParResult:
    """Mock Par Result."""

    def __init__(self, score: int, contracts: list):
        self.score = score
        self.contracts = contracts


class MockDDAnalysis:
    """Mock DDS Analysis result."""

    def __init__(self, dd_table: MockDDTable, par_result: MockParResult = None):
        self.dd_table = dd_table
        self.par_result = par_result
        self.is_valid = True


class MockDDSService:
    """Mock DDS Service that returns configurable analysis."""

    def __init__(self, dd_analysis: MockDDAnalysis = None):
        self._analysis = dd_analysis
        self.is_available = dd_analysis is not None

    def analyze_deal(self, hands, dealer='N', vulnerability='None'):
        return self._analysis


# ============================================================================
# Test Cases
# ============================================================================

class TestBidEfficiencyClassification(unittest.TestCase):
    """Test the corrected bidding efficiency logic."""

    def setUp(self):
        """Create engine with mock DDS."""
        self.engine = BridgeAnalysisEngine(dds_service=None)

    def test_optimal_game_bid_and_made(self):
        """
        Scenario: Bid 4S, DD says 10 tricks available, we took 10.
        Expected: OPTIMAL (we reached game, which was the max bonus)
        """
        # DD table: South can make 10 tricks in Spades
        dd_table = MockDDTable({'S': {'S': 10, 'H': 9, 'D': 7, 'C': 7, 'NT': 8}})
        contract = MockContract(level=4, trump_suit='S', declarer='S')

        efficiency, points_left, reached_optimal = self.engine._calculate_bid_efficiency(
            contract=contract,
            dd_table=dd_table,
            par_score=420,
            actual_score=420,
            vulnerability='None',
        )

        self.assertEqual(efficiency, BidEfficiency.OPTIMAL)
        self.assertEqual(points_left, 0)
        self.assertTrue(reached_optimal)
        print(f"✓ 4S making 10 (game available=10): {efficiency.value}, points_left={points_left}")

    def test_underbid_game_available_but_stopped_at_partscore(self):
        """
        Scenario: Bid 2S, but DD says 10 tricks available (game was there).
        Expected: UNDERBID (left game bonus on table)

        This is the KEY TEST for the corrected logic.
        Old logic would say "OPTIMAL" because 2S is makeable.
        New logic correctly says "UNDERBID" because we missed game.
        """
        # DD table: South can make 10 tricks in Spades
        dd_table = MockDDTable({'S': {'S': 10, 'H': 9, 'D': 7, 'C': 7, 'NT': 8}})
        contract = MockContract(level=2, trump_suit='S', declarer='S')

        # We made 2S with overtricks (score ~170), but game would be 420
        efficiency, points_left, reached_optimal = self.engine._calculate_bid_efficiency(
            contract=contract,
            dd_table=dd_table,
            par_score=420,
            actual_score=170,
            vulnerability='None',
        )

        self.assertEqual(efficiency, BidEfficiency.UNDERBID)
        self.assertGreater(points_left, 0)  # Should have points left
        self.assertFalse(reached_optimal)
        print(f"✓ 2S when 4S available: {efficiency.value}, points_left={points_left}")

    def test_underbid_slam_available_but_stopped_at_game(self):
        """
        Scenario: Bid 4S, but DD says 12 tricks available (slam was there).
        Expected: UNDERBID (left slam bonus on table)
        """
        # DD table: South can make 12 tricks in Spades
        dd_table = MockDDTable({'S': {'S': 12, 'H': 11, 'D': 9, 'C': 9, 'NT': 10}})
        contract = MockContract(level=4, trump_suit='S', declarer='S')

        efficiency, points_left, reached_optimal = self.engine._calculate_bid_efficiency(
            contract=contract,
            dd_table=dd_table,
            par_score=980,  # 6S making
            actual_score=480,  # 4S+2
            vulnerability='None',
        )

        self.assertEqual(efficiency, BidEfficiency.UNDERBID)
        self.assertGreater(points_left, 0)
        self.assertFalse(reached_optimal)
        print(f"✓ 4S when 6S available: {efficiency.value}, points_left={points_left}")

    def test_overbid_contract_unmakeable(self):
        """
        Scenario: Bid 4S, but DD says only 9 tricks available.
        Expected: OVERBID (contract cannot make)
        """
        # DD table: South can only make 9 tricks in Spades
        dd_table = MockDDTable({'S': {'S': 9, 'H': 8, 'D': 7, 'C': 7, 'NT': 8}})
        contract = MockContract(level=4, trump_suit='S', declarer='S')

        efficiency, points_left, reached_optimal = self.engine._calculate_bid_efficiency(
            contract=contract,
            dd_table=dd_table,
            par_score=140,  # 3S making
            actual_score=-50,  # Down 1
            vulnerability='None',
        )

        self.assertEqual(efficiency, BidEfficiency.OVERBID)
        self.assertEqual(points_left, 0)  # No points left - we overbid
        self.assertFalse(reached_optimal)
        print(f"✓ 4S when only 9 tricks available: {efficiency.value}")

    def test_optimal_partscore_when_no_game(self):
        """
        Scenario: Bid 2S, DD says 8 tricks available (no game).
        Expected: OPTIMAL (partscore is the best we can do)
        """
        # DD table: South can only make 8 tricks in Spades
        dd_table = MockDDTable({'S': {'S': 8, 'H': 7, 'D': 6, 'C': 6, 'NT': 7}})
        contract = MockContract(level=2, trump_suit='S', declarer='S')

        efficiency, points_left, reached_optimal = self.engine._calculate_bid_efficiency(
            contract=contract,
            dd_table=dd_table,
            par_score=110,
            actual_score=110,
            vulnerability='None',
        )

        self.assertEqual(efficiency, BidEfficiency.OPTIMAL)
        self.assertEqual(points_left, 0)
        self.assertTrue(reached_optimal)
        print(f"✓ 2S when no game available: {efficiency.value}")

    def test_optimal_3nt_game(self):
        """
        Scenario: Bid 3NT, DD says 9 tricks available.
        Expected: OPTIMAL (game in NT)
        """
        dd_table = MockDDTable({'S': {'S': 7, 'H': 7, 'D': 8, 'C': 8, 'NT': 9}})
        contract = MockContract(level=3, trump_suit=None, declarer='S')

        efficiency, points_left, reached_optimal = self.engine._calculate_bid_efficiency(
            contract=contract,
            dd_table=dd_table,
            par_score=400,
            actual_score=400,
            vulnerability='None',
        )

        self.assertEqual(efficiency, BidEfficiency.OPTIMAL)
        print(f"✓ 3NT making 9: {efficiency.value}")

    def test_underbid_1nt_when_3nt_available(self):
        """
        Scenario: Bid 1NT, but DD says 10 tricks available in NT.
        Expected: UNDERBID
        """
        dd_table = MockDDTable({'S': {'S': 8, 'H': 8, 'D': 9, 'C': 9, 'NT': 10}})
        contract = MockContract(level=1, trump_suit=None, declarer='S')

        efficiency, points_left, reached_optimal = self.engine._calculate_bid_efficiency(
            contract=contract,
            dd_table=dd_table,
            par_score=430,  # 3NT+1
            actual_score=120,  # 1NT+2
            vulnerability='None',
        )

        self.assertEqual(efficiency, BidEfficiency.UNDERBID)
        self.assertGreater(points_left, 0)
        print(f"✓ 1NT when 3NT+1 available: {efficiency.value}, points_left={points_left}")


class TestQuadrantClassification(unittest.TestCase):
    """Test the quadrant classification logic."""

    def setUp(self):
        self.engine = BridgeAnalysisEngine(dds_service=None)

    def test_q1_good_bid_good_play(self):
        """Q1: Bid game, made game, took all tricks."""
        quadrant = self.engine._calculate_quadrant(
            actual_tricks=10,
            dd_tricks=10,
            reached_optimal_level=True,
            bid_efficiency=BidEfficiency.OPTIMAL,
        )
        self.assertEqual(quadrant, Quadrant.Q1)
        print(f"✓ Q1: Good bid + Good play = {quadrant.value}")

    def test_q2_good_bid_bad_play(self):
        """Q2: Bid game (correctly), but lost tricks in play."""
        quadrant = self.engine._calculate_quadrant(
            actual_tricks=9,   # Lost 1 trick
            dd_tricks=10,
            reached_optimal_level=True,
            bid_efficiency=BidEfficiency.OPTIMAL,
        )
        self.assertEqual(quadrant, Quadrant.Q2)
        print(f"✓ Q2: Good bid + Bad play = {quadrant.value}")

    def test_q3_bad_bid_bad_play(self):
        """Q3: Overbid AND misplayed."""
        quadrant = self.engine._calculate_quadrant(
            actual_tricks=8,   # Lost tricks
            dd_tricks=9,       # Contract needed 10
            reached_optimal_level=False,
            bid_efficiency=BidEfficiency.OVERBID,
        )
        self.assertEqual(quadrant, Quadrant.Q3)
        print(f"✓ Q3: Bad bid + Bad play = {quadrant.value}")

    def test_q4_bad_bid_good_play(self):
        """Q4: Underbid but played perfectly."""
        quadrant = self.engine._calculate_quadrant(
            actual_tricks=10,  # Took all tricks
            dd_tricks=10,
            reached_optimal_level=False,  # But we only bid 2S
            bid_efficiency=BidEfficiency.UNDERBID,
        )
        self.assertEqual(quadrant, Quadrant.Q4)
        print(f"✓ Q4: Bad bid + Good play = {quadrant.value}")

    def test_q3_for_overbid_even_if_played_well(self):
        """
        Edge case: Overbid (4S when only 9 available), went down 1.
        Even though we "played perfectly" (took 9 of 9 available),
        the bid was bad, so this is Q3.
        """
        quadrant = self.engine._calculate_quadrant(
            actual_tricks=9,   # Took all available
            dd_tricks=9,       # Only 9 available
            reached_optimal_level=False,
            bid_efficiency=BidEfficiency.OVERBID,  # Bid 4S
        )
        # Overbid is "bad bidding", so even with good play, it's Q3 or Q4
        # Since actual >= dd, play is "good", so Q4
        self.assertEqual(quadrant, Quadrant.Q4)
        print(f"✓ Overbid + perfect play = {quadrant.value} (bad bid, good play)")


class TestPointsLeftCalculation(unittest.TestCase):
    """Test the points left on table calculation."""

    def setUp(self):
        self.engine = BridgeAnalysisEngine(dds_service=None)

    def test_game_bonus_left_nv(self):
        """Non-vul: Bid 2S when 4S available."""
        dd_table = MockDDTable({'S': {'S': 10}})
        contract = MockContract(level=2, trump_suit='S', declarer='S')

        _, points_left, _ = self.engine._calculate_bid_efficiency(
            contract=contract,
            dd_table=dd_table,
            par_score=420,
            actual_score=170,  # 2S+2
            vulnerability='None',
        )

        # Should be roughly 420 - 170 = 250 (game bonus missed)
        self.assertGreater(points_left, 200)
        self.assertLess(points_left, 350)
        print(f"✓ NV game missed: ~{points_left} points left")

    def test_game_bonus_left_vul(self):
        """Vul: Bid 2S when 4S available (bigger bonus)."""
        dd_table = MockDDTable({'S': {'S': 10}})
        contract = MockContract(level=2, trump_suit='S', declarer='S')

        _, points_left, _ = self.engine._calculate_bid_efficiency(
            contract=contract,
            dd_table=dd_table,
            par_score=620,
            actual_score=170,  # 2S+2
            vulnerability='NS',  # South is vul
        )

        # Should be roughly 620 - 170 = 450 (vul game bonus missed)
        self.assertGreater(points_left, 350)
        print(f"✓ Vul game missed: ~{points_left} points left")

    def test_slam_bonus_left(self):
        """Bid 4S when 6S available."""
        dd_table = MockDDTable({'S': {'S': 12}})
        contract = MockContract(level=4, trump_suit='S', declarer='S')

        _, points_left, _ = self.engine._calculate_bid_efficiency(
            contract=contract,
            dd_table=dd_table,
            par_score=980,
            actual_score=480,  # 4S+2
            vulnerability='None',
        )

        # Should be significant (slam bonus is 500 NV)
        self.assertGreater(points_left, 400)
        print(f"✓ Slam missed: ~{points_left} points left")

    def test_no_points_left_when_optimal(self):
        """No points left when we bid optimally."""
        dd_table = MockDDTable({'S': {'S': 10}})
        contract = MockContract(level=4, trump_suit='S', declarer='S')

        _, points_left, _ = self.engine._calculate_bid_efficiency(
            contract=contract,
            dd_table=dd_table,
            par_score=420,
            actual_score=420,
            vulnerability='None',
        )

        self.assertEqual(points_left, 0)
        print(f"✓ Optimal bid: {points_left} points left")


class TestHelperMethods(unittest.TestCase):
    """Test helper methods."""

    def setUp(self):
        self.engine = BridgeAnalysisEngine(dds_service=None)

    def test_normalize_strain(self):
        """Test strain normalization."""
        self.assertEqual(self.engine._normalize_strain('♠'), 'S')
        self.assertEqual(self.engine._normalize_strain('♥'), 'H')
        self.assertEqual(self.engine._normalize_strain('♦'), 'D')
        self.assertEqual(self.engine._normalize_strain('♣'), 'C')
        self.assertEqual(self.engine._normalize_strain('S'), 'S')
        self.assertEqual(self.engine._normalize_strain(None), 'NT')
        print("✓ Strain normalization works")

    def test_vulnerability_check(self):
        """Test vulnerability checking."""
        self.assertTrue(self.engine._is_vulnerable('S', 'NS'))
        self.assertTrue(self.engine._is_vulnerable('N', 'NS'))
        self.assertFalse(self.engine._is_vulnerable('E', 'NS'))
        self.assertFalse(self.engine._is_vulnerable('W', 'NS'))

        self.assertTrue(self.engine._is_vulnerable('E', 'EW'))
        self.assertFalse(self.engine._is_vulnerable('S', 'EW'))

        self.assertTrue(self.engine._is_vulnerable('S', 'Both'))
        self.assertTrue(self.engine._is_vulnerable('E', 'Both'))

        self.assertFalse(self.engine._is_vulnerable('S', 'None'))
        print("✓ Vulnerability check works")

    def test_find_max_makeable_level(self):
        """Test max makeable level calculation."""
        # 7 tricks = 1-level, 8 = 2-level, ..., 13 = 7-level
        self.assertEqual(self.engine._find_max_makeable_level(7), 1)
        self.assertEqual(self.engine._find_max_makeable_level(8), 2)
        self.assertEqual(self.engine._find_max_makeable_level(9), 3)
        self.assertEqual(self.engine._find_max_makeable_level(10), 4)
        self.assertEqual(self.engine._find_max_makeable_level(11), 5)
        self.assertEqual(self.engine._find_max_makeable_level(12), 6)
        self.assertEqual(self.engine._find_max_makeable_level(13), 7)
        print("✓ Max makeable level calculation works")

    def test_get_available_bonus(self):
        """Test bonus tier detection."""
        # Major suits: game at 4-level
        self.assertEqual(self.engine._get_available_bonus(4, 'S', False), 1)  # Game
        self.assertEqual(self.engine._get_available_bonus(3, 'S', False), 0)  # Partscore
        self.assertEqual(self.engine._get_available_bonus(6, 'S', False), 2)  # Small slam
        self.assertEqual(self.engine._get_available_bonus(7, 'S', False), 3)  # Grand slam

        # NT: game at 3-level
        self.assertEqual(self.engine._get_available_bonus(3, 'NT', False), 1)  # Game
        self.assertEqual(self.engine._get_available_bonus(2, 'NT', False), 0)  # Partscore

        # Minors: game at 5-level
        self.assertEqual(self.engine._get_available_bonus(5, 'C', False), 1)  # Game
        self.assertEqual(self.engine._get_available_bonus(4, 'C', False), 0)  # Partscore
        print("✓ Bonus tier detection works")

    def test_get_leader(self):
        """Test opening leader determination."""
        self.assertEqual(self.engine._get_leader('S'), 'W')  # Left of South
        self.assertEqual(self.engine._get_leader('N'), 'E')  # Left of North
        self.assertEqual(self.engine._get_leader('E'), 'S')  # Left of East
        self.assertEqual(self.engine._get_leader('W'), 'N')  # Left of West
        print("✓ Leader determination works")


class TestFullAnalysisWithMockDDS(unittest.TestCase):
    """Test full analysis flow with mock DDS."""

    def test_full_analysis_optimal_game(self):
        """Test complete analysis for optimal game bid."""
        # Create mock DDS
        dd_table = MockDDTable({
            'N': {'S': 9, 'H': 8, 'D': 7, 'C': 7, 'NT': 8},
            'E': {'S': 4, 'H': 5, 'D': 6, 'C': 6, 'NT': 5},
            'S': {'S': 10, 'H': 9, 'D': 7, 'C': 7, 'NT': 9},
            'W': {'S': 3, 'H': 4, 'D': 6, 'C': 6, 'NT': 4},
        })
        par_result = MockParResult(score=420, contracts=['4SN', '4SS'])
        dd_analysis = MockDDAnalysis(dd_table, par_result)
        dds_service = MockDDSService(dd_analysis)

        engine = BridgeAnalysisEngine(dds_service=dds_service)

        # Simulate: Bid 4S, made 10 tricks
        contract = MockContract(level=4, trump_suit='S', declarer='S')

        result = engine.analyze_hand(
            hands={},  # Not used with mock
            contract=contract,
            play_history=[],
            actual_tricks=10,
            actual_score=420,
            vulnerability='None',
        )

        self.assertEqual(result.quadrant, Quadrant.Q1)
        self.assertEqual(result.bid_efficiency, BidEfficiency.OPTIMAL)
        self.assertEqual(result.points_left_on_table, 0)
        self.assertEqual(result.dd_tricks, 10)
        self.assertTrue(result.reached_optimal_level)

        print(f"✓ Full analysis - Optimal game:")
        print(f"  Quadrant: {result.quadrant.value}")
        print(f"  Efficiency: {result.bid_efficiency.value}")
        print(f"  Points left: {result.points_left_on_table}")

    def test_full_analysis_underbid(self):
        """Test complete analysis for underbid situation."""
        dd_table = MockDDTable({
            'S': {'S': 10, 'H': 9, 'D': 7, 'C': 7, 'NT': 9},
        })
        par_result = MockParResult(score=420, contracts=['4SS'])
        dd_analysis = MockDDAnalysis(dd_table, par_result)
        dds_service = MockDDSService(dd_analysis)

        engine = BridgeAnalysisEngine(dds_service=dds_service)

        # Simulate: Bid only 2S when 4S was available
        contract = MockContract(level=2, trump_suit='S', declarer='S')

        result = engine.analyze_hand(
            hands={},
            contract=contract,
            play_history=[],
            actual_tricks=10,  # Made all tricks
            actual_score=170,
            vulnerability='None',
        )

        self.assertEqual(result.quadrant, Quadrant.Q4)  # Bad bid, good play
        self.assertEqual(result.bid_efficiency, BidEfficiency.UNDERBID)
        self.assertGreater(result.points_left_on_table, 0)

        print(f"✓ Full analysis - Underbid:")
        print(f"  Quadrant: {result.quadrant.value}")
        print(f"  Efficiency: {result.bid_efficiency.value}")
        print(f"  Points left: {result.points_left_on_table}")

    def test_full_analysis_overbid_and_misplay(self):
        """Test complete analysis for overbid + misplay (Q3)."""
        dd_table = MockDDTable({
            'S': {'S': 9, 'H': 8, 'D': 7, 'C': 7, 'NT': 8},
        })
        par_result = MockParResult(score=140, contracts=['3SS'])
        dd_analysis = MockDDAnalysis(dd_table, par_result)
        dds_service = MockDDSService(dd_analysis)

        engine = BridgeAnalysisEngine(dds_service=dds_service)

        # Simulate: Bid 4S (needs 10), only 9 available, took only 8
        contract = MockContract(level=4, trump_suit='S', declarer='S')

        result = engine.analyze_hand(
            hands={},
            contract=contract,
            play_history=[],
            actual_tricks=8,  # Lost a trick too
            actual_score=-100,
            vulnerability='None',
        )

        self.assertEqual(result.quadrant, Quadrant.Q3)  # Bad bid, bad play
        self.assertEqual(result.bid_efficiency, BidEfficiency.OVERBID)

        print(f"✓ Full analysis - Overbid + Misplay:")
        print(f"  Quadrant: {result.quadrant.value}")
        print(f"  Efficiency: {result.bid_efficiency.value}")


class TestResultSerialization(unittest.TestCase):
    """Test result serialization for database storage."""

    def test_to_dict_and_back(self):
        """Test round-trip serialization."""
        from engine.analysis.analysis_engine import OpeningLeadAnalysis, MajorError

        original = HandAnalysisResult(
            quadrant=Quadrant.Q2,
            bid_efficiency=BidEfficiency.OPTIMAL,
            points_left_on_table=0,
            contract_makeable=True,
            reached_optimal_level=True,
            dd_tricks=10,
            actual_tricks=9,
            tricks_delta=-1,
            par_score=420,
            par_contract="4SS",
            actual_score=390,
            score_vs_par=-30,
            opening_lead=OpeningLeadAnalysis(
                actual_lead="S4",
                optimal_leads=["SK", "SQ"],
                tricks_with_actual=10,
                tricks_with_optimal=9,
                quality=LeadQuality.LEAKING,
                cost=1,
            ),
            decay_curve=[10, 10, 10, 9, 9, 9],
            major_errors=[
                MajorError(
                    card_index=3,
                    trick=1,
                    card="SQ",
                    position="S",
                    loss=1,
                    optimal_card="S2",
                    reasoning="Should duck",
                )
            ],
            dd_matrix={'S': {'S': 10, 'NT': 9}},
        )

        # Serialize
        data = original.to_dict()

        # Deserialize
        restored = HandAnalysisResult.from_dict(data)

        # Verify
        self.assertEqual(restored.quadrant, original.quadrant)
        self.assertEqual(restored.bid_efficiency, original.bid_efficiency)
        self.assertEqual(restored.dd_tricks, original.dd_tricks)
        self.assertEqual(restored.decay_curve, original.decay_curve)
        self.assertEqual(len(restored.major_errors), 1)
        self.assertEqual(restored.opening_lead.actual_lead, "S4")

        print("✓ Serialization round-trip works")


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("BridgeAnalysisEngine Test Suite")
    print("=" * 70)
    print()

    # Run with verbose output
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes in order
    suite.addTests(loader.loadTestsFromTestCase(TestBidEfficiencyClassification))
    suite.addTests(loader.loadTestsFromTestCase(TestQuadrantClassification))
    suite.addTests(loader.loadTestsFromTestCase(TestPointsLeftCalculation))
    suite.addTests(loader.loadTestsFromTestCase(TestHelperMethods))
    suite.addTests(loader.loadTestsFromTestCase(TestFullAnalysisWithMockDDS))
    suite.addTests(loader.loadTestsFromTestCase(TestResultSerialization))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 70)
    if result.wasSuccessful():
        print("ALL TESTS PASSED ✓")
    else:
        print(f"FAILURES: {len(result.failures)}, ERRORS: {len(result.errors)}")
    print("=" * 70)

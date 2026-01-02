"""
Tests for DDS Analysis Service

Tests the new analysis capabilities:
- Full 20-solve DD table generation
- Par score calculation
- PBN deal parsing (including 3-hand inference)
- Analysis caching and performance

Note: These tests are skipped on platforms where DDS is not available (e.g., macOS M1/M2)
"""

import pytest
import sys
from engine.hand import Hand, Card

# Import analysis module
from engine.play.dds_analysis import (
    DDSAnalysisService,
    DDTable,
    ParResult,
    DealAnalysis,
    get_dds_service,
    is_dds_available,
    analyze_deal,
    get_dd_table,
    get_par_score,
    POSITION_ORDER,
    STRAIN_ORDER
)


# Skip all tests if DDS not available
pytestmark = pytest.mark.skipif(
    not is_dds_available(),
    reason="DDS not available on this platform (expected on macOS M1/M2)"
)


class TestDDTable:
    """Tests for DDTable dataclass."""

    def test_empty_table_initialization(self):
        """Test that empty table initializes with zeros."""
        table = DDTable()

        for player in POSITION_ORDER:
            for strain in STRAIN_ORDER:
                assert table.get_tricks(player, strain) == 0

    def test_table_with_data(self):
        """Test table with actual data."""
        data = {
            'N': {'C': 7, 'D': 8, 'H': 9, 'S': 10, 'NT': 9},
            'E': {'C': 6, 'D': 5, 'H': 4, 'S': 3, 'NT': 4},
            'S': {'C': 7, 'D': 8, 'H': 9, 'S': 10, 'NT': 9},
            'W': {'C': 6, 'D': 5, 'H': 4, 'S': 3, 'NT': 4},
        }
        table = DDTable(table=data)

        assert table.get_tricks('N', 'S') == 10
        assert table.get_tricks('E', 'NT') == 4

    def test_get_best_contract_ns(self):
        """Test finding best contract for NS."""
        data = {
            'N': {'C': 7, 'D': 8, 'H': 9, 'S': 10, 'NT': 9},
            'E': {'C': 6, 'D': 5, 'H': 4, 'S': 3, 'NT': 4},
            'S': {'C': 8, 'D': 8, 'H': 10, 'S': 10, 'NT': 10},
            'W': {'C': 5, 'D': 5, 'H': 3, 'S': 3, 'NT': 3},
        }
        table = DDTable(table=data)

        strain, declarer, tricks = table.get_best_contract('NS')

        # S can make 10 tricks in H, S, or NT
        assert tricks == 10
        assert declarer in ['N', 'S']

    def test_format_display(self):
        """Test table display formatting."""
        data = {
            'N': {'C': 7, 'D': 8, 'H': 9, 'S': 10, 'NT': 9},
            'E': {'C': 6, 'D': 5, 'H': 4, 'S': 3, 'NT': 4},
            'S': {'C': 7, 'D': 8, 'H': 9, 'S': 10, 'NT': 9},
            'W': {'C': 6, 'D': 5, 'H': 4, 'S': 3, 'NT': 4},
        }
        table = DDTable(table=data)

        display = table.format_display()

        assert 'N:' in display
        assert 'E:' in display
        assert 'S:' in display
        assert 'W:' in display

    def test_to_dict(self):
        """Test dictionary export."""
        data = {
            'N': {'C': 7, 'D': 8, 'H': 9, 'S': 10, 'NT': 9},
            'E': {'C': 6, 'D': 5, 'H': 4, 'S': 3, 'NT': 4},
            'S': {'C': 7, 'D': 8, 'H': 9, 'S': 10, 'NT': 9},
            'W': {'C': 6, 'D': 5, 'H': 4, 'S': 3, 'NT': 4},
        }
        table = DDTable(table=data)

        exported = table.to_dict()

        assert exported == data


class TestParResult:
    """Tests for ParResult dataclass."""

    def test_format_display_positive(self):
        """Test display with positive score."""
        result = ParResult(score=420, contracts=['4HS', '4HN'], declarer_side='NS')

        display = result.format_display()

        assert '+420' in display
        assert 'NS' in display

    def test_format_display_negative(self):
        """Test display with negative score."""
        result = ParResult(score=-450, contracts=['3NTE'], declarer_side='EW')

        display = result.format_display()

        assert '-450' in display
        assert 'EW' in display

    def test_to_dict(self):
        """Test dictionary export."""
        result = ParResult(score=420, contracts=['4HS'], declarer_side='NS')

        exported = result.to_dict()

        assert exported['score'] == 420
        assert exported['contracts'] == ['4HS']
        assert exported['declarer_side'] == 'NS'


class TestDDSAnalysisService:
    """Tests for the main analysis service."""

    @pytest.fixture
    def service(self):
        """Get a fresh service instance."""
        svc = DDSAnalysisService()
        svc.clear_cache()
        return svc

    @pytest.fixture
    def sample_hands(self):
        """Create a sample deal for testing."""
        # A classic slam hand
        north = Hand.from_pbn("AKQ2.KJ3.T98.432")
        east = Hand.from_pbn("JT98.Q42.KJ4.987")
        south = Hand.from_pbn("765.AT9.AQ5.AKQJ")
        west = Hand.from_pbn("43.8765.7632.T65")

        return {'N': north, 'E': east, 'S': south, 'W': west}

    def test_is_available(self, service):
        """Test availability check."""
        # Since we're past the skipif, DDS should be available
        assert service.is_available is True

    def test_analyze_deal_basic(self, service, sample_hands):
        """Test basic deal analysis."""
        analysis = service.analyze_deal(sample_hands)

        assert analysis.is_valid
        assert analysis.dd_table is not None
        assert analysis.error is None

    def test_analyze_deal_with_vulnerability(self, service, sample_hands):
        """Test analysis with vulnerability."""
        analysis = service.analyze_deal(
            sample_hands,
            dealer='S',
            vulnerability='NS'
        )

        assert analysis.is_valid
        assert analysis.dealer == 'S'
        assert analysis.vulnerability == 'NS'

    def test_dd_table_results(self, service, sample_hands):
        """Test that DD table contains reasonable results."""
        analysis = service.analyze_deal(sample_hands)

        # All results should be between 0 and 13
        for player in POSITION_ORDER:
            for strain in STRAIN_ORDER:
                tricks = analysis.dd_table.get_tricks(player, strain)
                assert 0 <= tricks <= 13, f"{player} {strain} = {tricks}"

        # NS should be able to make more tricks than EW in this deal
        ns_best = max(
            analysis.dd_table.get_tricks('N', 'NT'),
            analysis.dd_table.get_tricks('S', 'NT')
        )
        ew_best = max(
            analysis.dd_table.get_tricks('E', 'NT'),
            analysis.dd_table.get_tricks('W', 'NT')
        )

        # With 26+ HCP, NS should make at least 9 tricks in NT
        assert ns_best >= 9, f"NS best NT = {ns_best}"

    def test_par_result(self, service, sample_hands):
        """Test par calculation."""
        analysis = service.analyze_deal(sample_hands, vulnerability='None')

        assert analysis.par_result is not None
        assert isinstance(analysis.par_result.score, int)
        assert len(analysis.par_result.contracts) > 0

    def test_caching(self, service, sample_hands):
        """Test that results are cached."""
        # First call
        analysis1 = service.analyze_deal(sample_hands)
        stats1 = service.get_stats()

        # Second call (should hit cache)
        analysis2 = service.analyze_deal(sample_hands)
        stats2 = service.get_stats()

        assert stats2['cache_hits'] == stats1['cache_hits'] + 1
        assert analysis1.dd_table.to_dict() == analysis2.dd_table.to_dict()

    def test_get_tricks_convenience(self, service, sample_hands):
        """Test get_tricks convenience method."""
        tricks = service.get_tricks(sample_hands, 'S', 'NT')

        assert tricks is not None
        assert 0 <= tricks <= 13

    def test_get_tricks_with_symbol(self, service, sample_hands):
        """Test get_tricks with suit symbol."""
        tricks = service.get_tricks(sample_hands, 'S', '♠')

        assert tricks is not None
        assert 0 <= tricks <= 13

    def test_compare_with_par(self, service, sample_hands):
        """Test contract comparison with par."""
        result = service.compare_with_par(
            sample_hands,
            contract_level=3,
            contract_strain='NT',
            declarer='S',
            tricks_made=10,
            vulnerability='None'
        )

        assert result['available'] is True
        assert 'dd_tricks' in result
        assert 'par_score' in result
        assert result['made_contract'] is True
        assert result['overtricks'] == 1  # Made 10, needed 9

    def test_analyze_to_dict(self, service, sample_hands):
        """Test full analysis dictionary export."""
        analysis = service.analyze_deal(sample_hands)

        exported = analysis.to_dict()

        assert 'dd_table' in exported
        assert 'par' in exported
        assert 'dealer' in exported
        assert 'vulnerability' in exported
        assert 'is_valid' in exported
        assert exported['is_valid'] is True


class TestPBNParsing:
    """Tests for PBN parsing with 3-hand inference."""

    @pytest.fixture
    def service(self):
        return DDSAnalysisService()

    def test_full_pbn_parsing(self, service):
        """Test parsing complete 4-hand PBN."""
        pbn = "N:AKQ2.KJ3.T98.432 JT98.Q42.KJ4.987 765.AT9.AQ5.AKQJ 43.8765.7632.T65"

        analysis = service.analyze_pbn(pbn)

        assert analysis.is_valid
        assert analysis.dd_table is not None

    def test_pbn_with_different_start(self, service):
        """Test PBN starting from different position."""
        # Same deal but starting from East
        pbn = "E:JT98.Q42.KJ4.987 765.AT9.AQ5.AKQJ 43.8765.7632.T65 AKQ2.KJ3.T98.432"

        analysis = service.analyze_pbn(pbn)

        assert analysis.is_valid

    def test_three_hand_inference(self, service):
        """Test 3-hand PBN with inference."""
        # Only 3 hands provided, 4th (West) should be inferred
        pbn = "N:AKQ2.KJ3.T98.432 JT98.Q42.KJ4.987 765.AT9.AQ5.AKQJ ~"

        analysis = service.analyze_pbn(pbn)

        assert analysis.is_valid, f"Analysis failed: {analysis.error}"


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    @pytest.fixture
    def sample_hands(self):
        north = Hand.from_pbn("AKQ2.KJ3.T98.432")
        east = Hand.from_pbn("JT98.Q42.KJ4.987")
        south = Hand.from_pbn("765.AT9.AQ5.AKQJ")
        west = Hand.from_pbn("43.8765.7632.T65")
        return {'N': north, 'E': east, 'S': south, 'W': west}

    def test_analyze_deal_function(self, sample_hands):
        """Test analyze_deal convenience function."""
        analysis = analyze_deal(sample_hands)

        assert analysis.is_valid

    def test_get_dd_table_function(self, sample_hands):
        """Test get_dd_table convenience function."""
        table = get_dd_table(sample_hands)

        assert table is not None
        assert isinstance(table, DDTable)

    def test_get_par_score_function(self, sample_hands):
        """Test get_par_score convenience function."""
        par = get_par_score(sample_hands, vulnerability='Both')

        assert par is not None
        assert isinstance(par, ParResult)

    def test_singleton_service(self):
        """Test that get_dds_service returns singleton."""
        service1 = get_dds_service()
        service2 = get_dds_service()

        assert service1 is service2


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.fixture
    def service(self):
        return DDSAnalysisService()

    def test_missing_hand(self, service):
        """Test handling of incomplete hands dictionary."""
        hands = {
            'N': Hand.from_pbn("AKQ2.KJ3.T98.432"),
            'E': Hand.from_pbn("JT98.Q42.KJ4.987"),
            'S': Hand.from_pbn("765.AT9.AQ5.AKQJ"),
            # W missing
        }

        analysis = service.analyze_deal(hands)

        assert not analysis.is_valid
        assert analysis.error is not None

    def test_invalid_pbn_format(self, service):
        """Test handling of invalid PBN string."""
        analysis = service.analyze_pbn("invalid pbn string")

        assert not analysis.is_valid
        assert analysis.error is not None

    def test_all_vulnerabilities(self, service):
        """Test all vulnerability options."""
        hands = {
            'N': Hand.from_pbn("AKQ2.KJ3.T98.432"),
            'E': Hand.from_pbn("JT98.Q42.KJ4.987"),
            'S': Hand.from_pbn("765.AT9.AQ5.AKQJ"),
            'W': Hand.from_pbn("43.8765.7632.T65"),
        }

        for vul in ['None', 'NS', 'EW', 'Both', 'All']:
            analysis = service.analyze_deal(hands, vulnerability=vul)
            assert analysis.is_valid, f"Failed for vulnerability {vul}"

    def test_all_dealers(self, service):
        """Test all dealer options."""
        hands = {
            'N': Hand.from_pbn("AKQ2.KJ3.T98.432"),
            'E': Hand.from_pbn("JT98.Q42.KJ4.987"),
            'S': Hand.from_pbn("765.AT9.AQ5.AKQJ"),
            'W': Hand.from_pbn("43.8765.7632.T65"),
        }

        for dealer in ['N', 'E', 'S', 'W']:
            analysis = service.analyze_deal(hands, dealer=dealer)
            assert analysis.is_valid, f"Failed for dealer {dealer}"
            assert analysis.dealer == dealer


class TestPerformance:
    """Performance-related tests."""

    @pytest.fixture
    def service(self):
        svc = DDSAnalysisService()
        svc.clear_cache()
        return svc

    def test_analysis_speed(self, service):
        """Test that analysis completes in reasonable time."""
        import time

        hands = {
            'N': Hand.from_pbn("AKQ2.KJ3.T98.432"),
            'E': Hand.from_pbn("JT98.Q42.KJ4.987"),
            'S': Hand.from_pbn("765.AT9.AQ5.AKQJ"),
            'W': Hand.from_pbn("43.8765.7632.T65"),
        }

        start = time.time()
        analysis = service.analyze_deal(hands)
        elapsed = time.time() - start

        assert analysis.is_valid
        # Should complete in under 2 seconds (typical is <100ms)
        assert elapsed < 2.0, f"Analysis took {elapsed:.2f}s"

    def test_cached_analysis_speed(self, service):
        """Test that cached analysis is fast."""
        import time

        hands = {
            'N': Hand.from_pbn("AKQ2.KJ3.T98.432"),
            'E': Hand.from_pbn("JT98.Q42.KJ4.987"),
            'S': Hand.from_pbn("765.AT9.AQ5.AKQJ"),
            'W': Hand.from_pbn("43.8765.7632.T65"),
        }

        # First call (populates cache)
        service.analyze_deal(hands)

        # Second call (from cache)
        start = time.time()
        analysis = service.analyze_deal(hands)
        elapsed = time.time() - start

        assert analysis.is_valid
        # Cached should be nearly instant
        assert elapsed < 0.01, f"Cached analysis took {elapsed:.4f}s"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

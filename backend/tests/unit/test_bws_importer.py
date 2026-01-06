"""
Test suite for BWS (Bridge Wireless Scoring) File Importer.

Tests parsing of BWS files (Microsoft Access databases) from ACBLscore.
These files contain:
- ReceivedData: Contract results
- HandRecord: Deal distributions (when populated)
- BiddingData: Individual bids (when captured by BridgeMate)

Requires: mdbtools (brew install mdbtools)
"""

import pytest
from unittest.mock import patch, MagicMock
from engine.imports.bws_importer import (
    parse_bws_file,
    parse_bws_contracts,
    parse_received_data,
    parse_hand_record,
    parse_bidding_data,
    normalize_bws_bid,
    calculate_contract_score,
    merge_bws_with_pbn,
    BWSContract,
    BWSHandRecord,
    BWSBid,
    BWSFile
)


# =============================================================================
# SAMPLE DATA
# =============================================================================

SAMPLE_RECEIVED_DATA = [
    {
        'ID': '1',
        'Section': '1',
        'Table': '1',
        'Round': '1',
        'Board': '1',
        'PairNS': '1',
        'PairEW': '2',
        'Declarer': '1',
        'NS/EW': 'E',
        'Contract': '3 NT',
        'Result': '+1',
        'LeadCard': 'S5',
        'Erased': '0'
    },
    {
        'ID': '2',
        'Section': '1',
        'Table': '2',
        'Round': '1',
        'Board': '1',
        'PairNS': '3',
        'PairEW': '4',
        'Declarer': '3',
        'NS/EW': 'W',
        'Contract': '3 NT',
        'Result': '+2',
        'LeadCard': '',
        'Erased': '0'
    },
    {
        'ID': '3',
        'Section': '1',
        'Table': '3',
        'Round': '1',
        'Board': '2',
        'PairNS': '5',
        'PairEW': '6',
        'Declarer': '5',
        'NS/EW': 'S',
        'Contract': '4 H x',
        'Result': '-1',
        'LeadCard': 'CA',
        'Erased': '0'
    },
    {
        'ID': '4',
        'Section': '1',
        'Table': '4',
        'Round': '1',
        'Board': '3',
        'PairNS': '7',
        'PairEW': '8',
        'Declarer': '7',
        'NS/EW': 'N',
        'Contract': '6 S',
        'Result': '=',
        'LeadCard': 'DK',
        'Erased': '0'
    }
]

SAMPLE_HAND_RECORD = [
    {
        'Section': '1',
        'Board': '1',
        'NorthSpades': 'AKQ',
        'NorthHearts': 'J54',
        'NorthDiamonds': '987',
        'NorthClubs': '654',
        'EastSpades': 'JT9',
        'EastHearts': 'KQ3',
        'EastDiamonds': 'AKQ',
        'EastClubs': '987',
        'SouthSpades': '876',
        'SouthHearts': 'AT98',
        'SouthDiamonds': 'JT6',
        'SouthClubs': 'AKQ',
        'WestSpades': '5432',
        'WestHearts': '762',
        'WestDiamonds': '5432',
        'WestClubs': 'JT3'
    }
]

SAMPLE_BIDDING_DATA = [
    {'Section': '1', 'Table': '1', 'Round': '1', 'Board': '1', 'Counter': '1', 'Direction': 'N', 'Bid': 'P', 'Erased': '0'},
    {'Section': '1', 'Table': '1', 'Round': '1', 'Board': '1', 'Counter': '2', 'Direction': 'E', 'Bid': '1NT', 'Erased': '0'},
    {'Section': '1', 'Table': '1', 'Round': '1', 'Board': '1', 'Counter': '3', 'Direction': 'S', 'Bid': 'P', 'Erased': '0'},
    {'Section': '1', 'Table': '1', 'Round': '1', 'Board': '1', 'Counter': '4', 'Direction': 'W', 'Bid': '3NT', 'Erased': '0'},
    {'Section': '1', 'Table': '1', 'Round': '1', 'Board': '1', 'Counter': '5', 'Direction': 'N', 'Bid': 'P', 'Erased': '0'},
    {'Section': '1', 'Table': '1', 'Round': '1', 'Board': '1', 'Counter': '6', 'Direction': 'E', 'Bid': 'P', 'Erased': '0'},
    {'Section': '1', 'Table': '1', 'Round': '1', 'Board': '1', 'Counter': '7', 'Direction': 'S', 'Bid': 'P', 'Erased': '0'},
]


# =============================================================================
# CONTRACT PARSING TESTS
# =============================================================================

class TestContractParsing:
    """Tests for parsing ReceivedData table."""

    def test_parse_basic_contracts(self):
        """Test parsing basic contract data."""
        contracts = parse_received_data(SAMPLE_RECEIVED_DATA)
        assert len(contracts) == 4

    def test_declarer_from_ns_ew_column(self):
        """Test that declarer is extracted from NS/EW column."""
        contracts = parse_received_data(SAMPLE_RECEIVED_DATA)
        # First contract has NS/EW='E'
        assert contracts[0].declarer == 'E'
        # Second has NS/EW='W'
        assert contracts[1].declarer == 'W'
        # Third has NS/EW='S'
        assert contracts[2].declarer == 'S'
        # Fourth has NS/EW='N'
        assert contracts[3].declarer == 'N'

    def test_side_determination(self):
        """Test side (NS/EW) is correctly determined from declarer."""
        contracts = parse_received_data(SAMPLE_RECEIVED_DATA)
        assert contracts[0].side == 'EW'  # E declares
        assert contracts[1].side == 'EW'  # W declares
        assert contracts[2].side == 'NS'  # S declares
        assert contracts[3].side == 'NS'  # N declares

    def test_contract_properties(self):
        """Test contract level, strain extraction."""
        contracts = parse_received_data(SAMPLE_RECEIVED_DATA)

        # 3NT contract
        c1 = contracts[0]
        assert c1.level == 3
        assert c1.strain == 'NT'
        assert not c1.is_doubled
        assert not c1.is_redoubled

        # 4H doubled contract
        c3 = contracts[2]
        assert c3.level == 4
        assert c3.strain == 'H'
        assert c3.is_doubled
        assert not c3.is_redoubled

    def test_tricks_made_calculation(self):
        """Test tricks made calculation from result."""
        contracts = parse_received_data(SAMPLE_RECEIVED_DATA)

        # 3NT+1 = 9+1 = 10 tricks
        assert contracts[0].tricks_made == 10

        # 3NT+2 = 9+2 = 11 tricks
        assert contracts[1].tricks_made == 11

        # 4H-1 = 10-1 = 9 tricks
        assert contracts[2].tricks_made == 9

        # 6S= = 12 tricks
        assert contracts[3].tricks_made == 12

    def test_skip_erased_entries(self):
        """Test that erased entries are skipped."""
        data = SAMPLE_RECEIVED_DATA + [
            {
                'ID': '5',
                'Section': '1',
                'Table': '5',
                'Round': '1',
                'Board': '1',
                'PairNS': '9',
                'PairEW': '10',
                'Declarer': '9',
                'NS/EW': 'N',
                'Contract': '4 S',
                'Result': '=',
                'LeadCard': '',
                'Erased': '1'  # This should be skipped
            }
        ]
        contracts = parse_received_data(data)
        assert len(contracts) == 4  # Still 4, not 5

    def test_skip_empty_contracts(self):
        """Test that entries with empty contract are skipped."""
        data = SAMPLE_RECEIVED_DATA + [
            {
                'ID': '6',
                'Section': '1',
                'Table': '6',
                'Round': '1',
                'Board': '1',
                'PairNS': '11',
                'PairEW': '12',
                'Declarer': '11',
                'NS/EW': 'S',
                'Contract': '',  # Empty contract
                'Result': '',
                'LeadCard': '',
                'Erased': '0'
            }
        ]
        contracts = parse_received_data(data)
        assert len(contracts) == 4


class TestBWSContractProperties:
    """Tests for BWSContract class properties."""

    def test_strain_extraction_suits(self):
        """Test strain extraction for suit contracts."""
        c_spades = BWSContract(1, 1, 1, 1, 1, 2, 'N', 'NS', '4 S', '=')
        assert c_spades.strain == 'S'

        c_hearts = BWSContract(1, 1, 1, 1, 1, 2, 'E', 'EW', '3 H', '+1')
        assert c_hearts.strain == 'H'

        c_diamonds = BWSContract(1, 1, 1, 1, 1, 2, 'S', 'NS', '5 D', '-2')
        assert c_diamonds.strain == 'D'

        c_clubs = BWSContract(1, 1, 1, 1, 1, 2, 'W', 'EW', '2 C', '=')
        assert c_clubs.strain == 'C'

    def test_strain_extraction_notrump(self):
        """Test strain extraction for NT contracts."""
        c1 = BWSContract(1, 1, 1, 1, 1, 2, 'E', 'EW', '3 NT', '=')
        assert c1.strain == 'NT'

        c2 = BWSContract(1, 1, 1, 1, 1, 2, 'W', 'EW', '1NT', '=')
        assert c2.strain == 'NT'

    def test_doubled_detection(self):
        """Test doubled contract detection."""
        c_undoubled = BWSContract(1, 1, 1, 1, 1, 2, 'N', 'NS', '4 S', '=')
        assert not c_undoubled.is_doubled
        assert not c_undoubled.is_redoubled

        c_doubled = BWSContract(1, 1, 1, 1, 1, 2, 'E', 'EW', '4 S x', '-1')
        assert c_doubled.is_doubled
        assert not c_doubled.is_redoubled

        c_redoubled = BWSContract(1, 1, 1, 1, 1, 2, 'S', 'NS', '4 S xx', '=')
        assert not c_redoubled.is_doubled
        assert c_redoubled.is_redoubled

    def test_to_dict(self):
        """Test dictionary conversion."""
        c = BWSContract(1, 2, 3, 4, 5, 6, 'N', 'NS', '3 NT', '+1', 'H5')
        d = c.to_dict()

        assert d['section'] == 1
        assert d['table'] == 2
        assert d['round'] == 3
        assert d['board'] == 4
        assert d['declarer'] == 'N'
        assert d['contract'] == '3 NT'
        assert d['result'] == '+1'
        assert d['level'] == 3
        assert d['strain'] == 'NT'
        assert d['tricks_made'] == 10


# =============================================================================
# BID NORMALIZATION TESTS
# =============================================================================

class TestBidNormalization:
    """Tests for bid string normalization."""

    def test_pass_variants(self):
        """Test Pass normalization."""
        assert normalize_bws_bid('P') == 'Pass'
        assert normalize_bws_bid('PASS') == 'Pass'
        assert normalize_bws_bid('pass') == 'Pass'
        assert normalize_bws_bid('-') == 'Pass'

    def test_double_variants(self):
        """Test Double normalization."""
        assert normalize_bws_bid('X') == 'Double'
        assert normalize_bws_bid('DBL') == 'Double'
        assert normalize_bws_bid('DOUBLE') == 'Double'

    def test_redouble_variants(self):
        """Test Redouble normalization."""
        assert normalize_bws_bid('XX') == 'Redouble'
        assert normalize_bws_bid('RDBL') == 'Redouble'
        assert normalize_bws_bid('REDOUBLE') == 'Redouble'

    def test_suit_bids(self):
        """Test suit bid normalization."""
        assert normalize_bws_bid('1C') == '1♣'
        assert normalize_bws_bid('2D') == '2♦'
        assert normalize_bws_bid('3H') == '3♥'
        assert normalize_bws_bid('4S') == '4♠'

    def test_notrump_bids(self):
        """Test notrump bid normalization."""
        assert normalize_bws_bid('1NT') == '1NT'
        assert normalize_bws_bid('3NT') == '3NT'


# =============================================================================
# SCORE CALCULATION TESTS
# =============================================================================

class TestScoreCalculation:
    """Tests for contract score calculation."""

    def test_making_partscore_nonvul(self):
        """Test making a non-vulnerable part score."""
        # 2S making = 60 + 50 = 110
        score = calculate_contract_score(
            level=2, strain='S', tricks_made=8,
            doubled=0, vulnerable=False, declarer_ns=True
        )
        assert score == 110

    def test_making_game_nonvul(self):
        """Test making a non-vulnerable game."""
        # 4H making = 120 + 300 = 420
        score = calculate_contract_score(
            level=4, strain='H', tricks_made=10,
            doubled=0, vulnerable=False, declarer_ns=True
        )
        assert score == 420

    def test_making_3nt_nonvul(self):
        """Test making 3NT non-vulnerable."""
        # 3NT making = 100 + 300 = 400
        score = calculate_contract_score(
            level=3, strain='NT', tricks_made=9,
            doubled=0, vulnerable=False, declarer_ns=True
        )
        assert score == 400

    def test_down_one_nonvul(self):
        """Test going down one non-vulnerable."""
        # -1 = -50
        score = calculate_contract_score(
            level=4, strain='S', tricks_made=9,
            doubled=0, vulnerable=False, declarer_ns=True
        )
        assert score == -50

    def test_down_doubled_nonvul(self):
        """Test going down doubled non-vulnerable."""
        # -1 doubled = -100
        score = calculate_contract_score(
            level=4, strain='H', tricks_made=9,
            doubled=1, vulnerable=False, declarer_ns=True
        )
        assert score == -100

    def test_ew_declares_score_sign(self):
        """Test that EW declaring gives negative score for NS."""
        # 4H making by EW = -420 for NS
        score = calculate_contract_score(
            level=4, strain='H', tricks_made=10,
            doubled=0, vulnerable=False, declarer_ns=False
        )
        assert score == -420


# =============================================================================
# HAND RECORD PARSING TESTS
# =============================================================================

class TestHandRecordParsing:
    """Tests for parsing HandRecord table."""

    def test_parse_hand_record(self):
        """Test parsing hand record data."""
        records = parse_hand_record(SAMPLE_HAND_RECORD)
        assert len(records) == 1

        record = records[0]
        assert record.board == 1
        assert record.north['spades'] == ['A', 'K', 'Q']
        assert record.north['hearts'] == ['J', '5', '4']

    def test_to_pbn_deal(self):
        """Test conversion to PBN deal format."""
        records = parse_hand_record(SAMPLE_HAND_RECORD)
        pbn = records[0].to_pbn_deal()
        assert pbn.startswith('N:')
        assert 'AKQ' in pbn  # North's spades


# =============================================================================
# BIDDING DATA PARSING TESTS
# =============================================================================

class TestBiddingDataParsing:
    """Tests for parsing BiddingData table."""

    def test_parse_bidding_data(self):
        """Test parsing bidding data."""
        bids = parse_bidding_data(SAMPLE_BIDDING_DATA)
        assert len(bids) == 7

    def test_bid_sequence_order(self):
        """Test that bids are parsed in correct order."""
        bids = parse_bidding_data(SAMPLE_BIDDING_DATA)
        # Sort by counter
        bids.sort(key=lambda b: b.counter)

        assert bids[0].bid == 'Pass'  # N passes
        assert bids[1].bid == '1NT'   # E opens 1NT
        assert bids[2].bid == 'Pass'  # S passes
        assert bids[3].bid == '3NT'   # W raises to 3NT


# =============================================================================
# BWS FILE TESTS
# =============================================================================

class TestBWSFile:
    """Tests for BWSFile class."""

    def test_file_properties(self):
        """Test file-level properties."""
        contracts = parse_received_data(SAMPLE_RECEIVED_DATA)
        bws = BWSFile(
            filename='test.bws',
            contracts=contracts,
            tables_available=['ReceivedData', 'HandRecord']
        )

        assert bws.board_count == 3  # Boards 1, 2, 3
        assert bws.table_count == 4  # Tables 1, 2, 3, 4
        assert not bws.has_hand_records
        assert not bws.has_bidding_data

    def test_get_contracts_for_board(self):
        """Test filtering contracts by board number."""
        contracts = parse_received_data(SAMPLE_RECEIVED_DATA)
        bws = BWSFile(filename='test.bws', contracts=contracts)

        board1 = bws.get_contracts_for_board(1)
        assert len(board1) == 2  # Two tables played board 1

        board2 = bws.get_contracts_for_board(2)
        assert len(board2) == 1

    def test_to_dict(self):
        """Test dictionary conversion."""
        contracts = parse_received_data(SAMPLE_RECEIVED_DATA)
        bws = BWSFile(
            filename='test.bws',
            contracts=contracts,
            tables_available=['ReceivedData']
        )

        d = bws.to_dict()
        assert d['filename'] == 'test.bws'
        assert d['board_count'] == 3
        assert 'contracts' in d


# =============================================================================
# INTEGRATION TESTS (require mdbtools)
# =============================================================================

class TestIntegration:
    """Integration tests requiring actual BWS file and mdbtools."""

    @pytest.fixture
    def real_bws_file(self):
        """Path to test BWS file if available."""
        import os
        test_path = '/Users/simonroy/Desktop/bridge_bidding_app/test-results/1766528722-gmeDcSvigL@251223M.BWS'
        if os.path.exists(test_path):
            return test_path
        pytest.skip("Test BWS file not available")

    def test_parse_real_file(self, real_bws_file):
        """Test parsing a real BWS file."""
        bws = parse_bws_file(real_bws_file)

        assert bws.board_count > 0
        assert len(bws.contracts) > 0
        assert 'ReceivedData' in bws.tables_available

    def test_all_declarers_valid(self, real_bws_file):
        """Test that all declarers are valid directions."""
        bws = parse_bws_file(real_bws_file)

        valid_declarers = {'N', 'E', 'S', 'W'}
        for contract in bws.contracts:
            assert contract.declarer in valid_declarers, f"Invalid declarer: {contract.declarer}"

    def test_all_sides_valid(self, real_bws_file):
        """Test that all sides are NS or EW."""
        bws = parse_bws_file(real_bws_file)

        valid_sides = {'NS', 'EW'}
        for contract in bws.contracts:
            assert contract.side in valid_sides, f"Invalid side: {contract.side}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

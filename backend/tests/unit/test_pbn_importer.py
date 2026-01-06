"""
Test suite for ACBL PBN Importer.

Tests parsing of PBN files from different sources:
- ACBL tournament exports
- BBO (Bridge Base Online) hand records
- Common Game format

Validates:
- Multi-line auction parsing
- Deal string conversion
- Metadata extraction
- Error handling for malformed files
"""

import pytest
from engine.imports.pbn_importer import (
    parse_pbn_file,
    parse_pbn_hand,
    extract_acbl_auction,
    convert_pbn_deal_to_json,
    parse_pbn_deal_string,
    validate_pbn_hand_string,
    PBNFile,
    PBNHand
)


# =============================================================================
# SAMPLE PBN DATA
# =============================================================================

SAMPLE_ACBL_PBN = '''[Event "Thursday Open Pairs"]
[Site "Club #123"]
[Date "2026.01.05"]
[Board "1"]
[Dealer "N"]
[Vulnerable "None"]
[Deal "N:QJ6.K652.J85.T98 A932.T4.K96.AQJ2 KT87.AJ987.AT7.5 54.Q3.Q432.K8763"]
[Contract "4H"]
[Declarer "S"]
[Result "10"]
[Score "NS 420"]

[Auction "N"]
Pass 1C 1H 1S
2H Pass 4H Pass
Pass Pass

[Play "W"]
S5 S6 SA S7
'''

SAMPLE_BBO_PBN = '''[Event "BBO Instant Tournament"]
[Site "Bridge Base Online"]
[Date "2026.01.04"]
[Board "5"]
[Dealer "E"]
[Vulnerable "NS"]
[Deal "E:AKQ.JT9.8765.432 JT98.8765.432.AK 765.432.AKQ.JT98 432.AKQ.JT9.Q765"]
[Scoring "IMP"]
[Contract "3NT"]
[Declarer "W"]
[Result "9"]

[Auction "E"]
Pass  1D  Pass  1H
Pass  1NT Pass  3NT
Pass  Pass Pass

[Play "N"]
SJ  S2  S5  SA
'''

SAMPLE_COMMON_GAME_PBN = '''[Event "Common Game"]
[Board "12"]
[Dealer "W"]
[Vulnerable "EW"]
[Deal "W:J87.AK.QT9.AKJ32 AKQ.QJT.8765.T98 T9654.987.AK.Q76 32.65432.J432.54"]
[Contract "3NTX"]
[Declarer "W"]
[Result "8"]

[Auction "W"]
1NT Pass 2C !
X Pass Pass Pass

[Play "N"]
SA S4 S2 S7
'''

SAMPLE_MULTILINE_AUCTION = '''[Event "Test"]
[Board "1"]
[Dealer "S"]
[Vulnerable "Both"]
[Deal "S:AKQ.JT9.8765.432 JT98.8765.432.AK 765.432.AKQ.JT98 432.AKQ.JT9.Q765"]
[Contract "4S"]
[Declarer "S"]
[Result "10"]

[Auction "S"]
1S      Pass    2NT     Pass
{Forcing}
3S      Pass    4S      Pass
Pass    Pass
'''


# =============================================================================
# AUCTION EXTRACTION TESTS
# =============================================================================

class TestAuctionExtraction:
    """Tests for extracting and normalizing auctions from PBN."""

    def test_basic_auction(self):
        """Test basic single-line auction extraction."""
        pbn = '''[Auction "N"]
Pass 1C 1H 1S 2H Pass 4H Pass Pass Pass'''

        bids = extract_acbl_auction(pbn)
        assert bids == ['Pass', '1C', '1H', '1S', '2H', 'Pass', '4H', 'Pass', 'Pass', 'Pass']

    def test_multiline_auction(self):
        """Test multi-line auction extraction."""
        bids = extract_acbl_auction(SAMPLE_ACBL_PBN)
        assert bids == ['Pass', '1C', '1H', '1S', '2H', 'Pass', '4H', 'Pass', 'Pass', 'Pass']

    def test_auction_with_alerts(self):
        """Test auction with alert annotations stripped."""
        bids = extract_acbl_auction(SAMPLE_COMMON_GAME_PBN)
        # Alert annotation {!} should be stripped
        assert '2C' in bids
        assert 'Double' in bids

    def test_auction_with_comments(self):
        """Test auction with comments stripped."""
        bids = extract_acbl_auction(SAMPLE_MULTILINE_AUCTION)
        # Comment {Forcing} should be stripped
        assert 'Forcing' not in bids
        assert bids == ['1S', 'Pass', '2NT', 'Pass', '3S', 'Pass', '4S', 'Pass', 'Pass', 'Pass']

    def test_double_standardization(self):
        """Test that X is converted to Double."""
        pbn = '''[Auction "E"]
1H X 2H XX Pass Pass Pass'''

        bids = extract_acbl_auction(pbn)
        assert 'Double' in bids
        assert 'Redouble' in bids
        assert 'X' not in bids
        assert 'XX' not in bids

    def test_case_insensitive(self):
        """Test that auction parsing is case insensitive."""
        pbn = '''[Auction "N"]
pass 1c 1h PASS 2H Pass'''

        bids = extract_acbl_auction(pbn)
        # All should be standardized
        assert bids.count('Pass') == 3
        assert '1C' in bids
        assert '1H' in bids


# =============================================================================
# DEAL STRING TESTS
# =============================================================================

class TestDealParsing:
    """Tests for parsing deal strings."""

    def test_convert_pbn_to_json(self):
        """Test converting PBN hand to JSON format."""
        pbn_hand = "QJ6.K652.J85.T98"
        result = convert_pbn_deal_to_json(pbn_hand)

        assert result['spades'] == ['Q', 'J', '6']
        assert result['hearts'] == ['K', '6', '5', '2']
        assert result['diamonds'] == ['J', '8', '5']
        assert result['clubs'] == ['T', '9', '8']

    def test_convert_with_direction_prefix(self):
        """Test converting PBN with direction prefix."""
        pbn_hand = "N:QJ6.K652.J85.T98"
        result = convert_pbn_deal_to_json(pbn_hand)

        assert result['spades'] == ['Q', 'J', '6']

    def test_parse_deal_string(self):
        """Test parsing full 4-hand deal string."""
        deal = "QJ6.K652.J85.T98 A932.T4.K96.AQJ2 KT87.AJ987.AT7.5 54.Q3.Q432.K8763"
        hands = parse_pbn_deal_string(deal, 'N')

        assert len(hands) == 4
        assert hands['N'] == "QJ6.K652.J85.T98"
        assert hands['E'] == "A932.T4.K96.AQJ2"
        assert hands['S'] == "KT87.AJ987.AT7.5"
        assert hands['W'] == "54.Q3.Q432.K8763"

    def test_parse_deal_string_different_start(self):
        """Test deal parsing with different starting position."""
        deal = "A932.T4.K96.AQJ2 KT87.AJ987.AT7.5 54.Q3.Q432.K8763 QJ6.K652.J85.T98"
        hands = parse_pbn_deal_string(deal, 'E')

        assert hands['E'] == "A932.T4.K96.AQJ2"
        assert hands['S'] == "KT87.AJ987.AT7.5"
        assert hands['W'] == "54.Q3.Q432.K8763"
        assert hands['N'] == "QJ6.K652.J85.T98"

    def test_empty_suit(self):
        """Test hand with empty suit (void)."""
        pbn_hand = "AKQJT98765..43.2"  # Void in hearts
        result = convert_pbn_deal_to_json(pbn_hand)

        assert len(result['spades']) == 10
        assert result['hearts'] == []
        assert len(result['diamonds']) == 2
        assert len(result['clubs']) == 1


# =============================================================================
# HAND VALIDATION TESTS
# =============================================================================

class TestHandValidation:
    """Tests for PBN hand validation."""

    def test_valid_hand(self):
        """Test validation of a valid 13-card hand."""
        is_valid, error = validate_pbn_hand_string("QJ6.K652.J85.T98")
        assert is_valid
        assert error == ""

    def test_invalid_card_count(self):
        """Test validation fails for wrong card count."""
        is_valid, error = validate_pbn_hand_string("QJ6.K652.J85.T9")  # Only 12 cards
        assert not is_valid
        assert "13 cards" in error

    def test_invalid_rank(self):
        """Test validation fails for invalid rank."""
        is_valid, error = validate_pbn_hand_string("QJX.K652.J85.T98")  # X is invalid
        assert not is_valid
        assert "Invalid rank" in error

    def test_wrong_suit_count(self):
        """Test validation fails for wrong number of suits."""
        is_valid, error = validate_pbn_hand_string("QJ6.K652.J85")  # Only 3 suits
        assert not is_valid
        assert "4 suits" in error


# =============================================================================
# FULL HAND PARSING TESTS
# =============================================================================

class TestHandParsing:
    """Tests for parsing complete PBN hand blocks."""

    def test_parse_acbl_hand(self):
        """Test parsing an ACBL format hand."""
        hand = parse_pbn_hand(SAMPLE_ACBL_PBN)

        assert hand.board_number == 1
        assert hand.dealer == 'N'
        assert hand.vulnerability == 'None'
        assert hand.contract_level == 4
        assert hand.contract_strain == 'H'
        assert hand.tricks_taken == 10
        assert hand.is_valid

    def test_parse_bbo_hand(self):
        """Test parsing a BBO format hand."""
        hand = parse_pbn_hand(SAMPLE_BBO_PBN)

        assert hand.board_number == 5
        assert hand.dealer == 'E'
        assert hand.vulnerability == 'NS'
        assert hand.contract_level == 3
        assert hand.contract_strain == 'NT'

    def test_parse_doubled_contract(self):
        """Test parsing a doubled contract."""
        hand = parse_pbn_hand(SAMPLE_COMMON_GAME_PBN)

        assert hand.contract_level == 3
        assert hand.contract_strain == 'NT'
        assert hand.contract_doubled == 1  # Doubled

    def test_hands_parsed(self):
        """Test that all 4 hands are parsed correctly."""
        hand = parse_pbn_hand(SAMPLE_ACBL_PBN)

        assert len(hand.hands) == 4
        assert 'N' in hand.hands
        assert 'E' in hand.hands
        assert 'S' in hand.hands
        assert 'W' in hand.hands


# =============================================================================
# FILE PARSING TESTS
# =============================================================================

class TestFileParsing:
    """Tests for parsing complete PBN files."""

    def test_parse_single_hand_file(self):
        """Test parsing a file with one hand."""
        result = parse_pbn_file(SAMPLE_ACBL_PBN, "test.pbn")

        assert result.filename == "test.pbn"
        assert result.valid_hands == 1
        assert len(result.hands) == 1

    def test_parse_multi_hand_file(self):
        """Test parsing a file with multiple hands."""
        multi_pbn = SAMPLE_ACBL_PBN + "\n\n" + SAMPLE_BBO_PBN

        result = parse_pbn_file(multi_pbn, "multi.pbn")

        assert result.valid_hands >= 1  # At least one valid

    def test_source_detection_acbl(self):
        """Test source detection for ACBL files."""
        pbn = '''[Event "ACBL Open Pairs"]
[Board "1"]
[Dealer "N"]
[Vulnerable "None"]
[Deal "N:QJ6.K652.J85.T98 A932.T4.K96.AQJ2 KT87.AJ987.AT7.5 54.Q3.Q432.K8763"]'''

        result = parse_pbn_file(pbn)
        assert result.source == 'acbl'

    def test_source_detection_bbo(self):
        """Test source detection for BBO files."""
        result = parse_pbn_file(SAMPLE_BBO_PBN)
        assert result.source == 'bbo'

    def test_event_metadata_extraction(self):
        """Test extraction of event metadata."""
        result = parse_pbn_file(SAMPLE_ACBL_PBN)

        assert result.event_name == "Thursday Open Pairs"


# =============================================================================
# V3 API CONVERSION TESTS
# =============================================================================

class TestV3Conversion:
    """Tests for converting to V3 API format."""

    def test_to_v3_payload(self):
        """Test conversion to V3 payload format."""
        hand = parse_pbn_hand(SAMPLE_ACBL_PBN)
        payload = hand.to_v3_payload('S')

        assert 'hand' in payload
        assert 'auction_history' in payload
        assert 'vulnerability' in payload
        assert 'dealer' in payload
        assert payload['my_position'] == 'South'

    def test_get_hand_json(self):
        """Test getting JSON format for a specific hand."""
        hand = parse_pbn_hand(SAMPLE_ACBL_PBN)
        south_hand = hand.get_hand_json('S')

        assert 'spades' in south_hand
        assert 'hearts' in south_hand
        assert 'diamonds' in south_hand
        assert 'clubs' in south_hand


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_pbn(self):
        """Test handling of empty PBN content."""
        result = parse_pbn_file("")
        assert result.valid_hands == 0

    def test_malformed_deal(self):
        """Test handling of malformed deal string."""
        pbn = '''[Event "Test"]
[Board "1"]
[Dealer "N"]
[Vulnerable "None"]
[Deal "N:INVALID.DEAL.STRING"]'''

        hand = parse_pbn_hand(pbn)
        # Should handle gracefully without crashing
        assert hand is not None

    def test_missing_auction(self):
        """Test handling of missing auction."""
        pbn = '''[Event "Test"]
[Board "1"]
[Dealer "N"]
[Vulnerable "None"]
[Deal "N:QJ6.K652.J85.T98 A932.T4.K96.AQJ2 KT87.AJ987.AT7.5 54.Q3.Q432.K8763"]'''

        hand = parse_pbn_hand(pbn)
        assert hand.auction_history == []

    def test_passed_out_hand(self):
        """Test parsing of passed out hand."""
        pbn = '''[Event "Test"]
[Board "1"]
[Dealer "N"]
[Vulnerable "None"]
[Deal "N:QJ6.K652.J85.T98 A932.T4.K96.AQJ2 KT87.AJ987.AT7.5 54.Q3.Q432.K8763"]
[Contract "Pass"]

[Auction "N"]
Pass Pass Pass Pass'''

        hand = parse_pbn_hand(pbn)
        # Passed out should have auction but no contract level
        assert hand.auction_history == ['Pass', 'Pass', 'Pass', 'Pass']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

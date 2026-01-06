"""
ACBL PBN Importer - Stage 1 of the import pipeline.

Parses ACBL-style PBN (Portable Bridge Notation) files into the Bridge Bidding Master V3 schema.
Handles multi-line auctions, alert annotations, and various PBN format variations (ACBL, BBO, Common Game).

PBN Format Physics:
- Line-delimited text structure
- Key-value pairs: [Tag "Value"]
- Deal string in N-E-S-W compass order with dot notation
- Auction block follows [Auction] tag until next tag or EOF

Regex Pattern Set:
- Auction Block: Captures multi-line auction after [Auction "dir"] tag
- Bid Cleaner: Extracts valid bids (1-7 level + strain, Pass, X, XX)
- Metadata Stripper: Removes alerts, annotations, comments
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# REGEX PATTERN SET - Tested against ACBL, BBO, and Common Game exports
# =============================================================================

# Pattern 1: Tag Extraction - Captures [TagName "Value"] pairs
TAG_PATTERN = re.compile(r'\[(\w+)\s+"([^"]*)"\]')

# Pattern 2: Auction Block - Isolates multi-line auction after [Auction] tag
# Captures everything from [Auction "X"] until [Play or [Event or end of string
# Uses negative lookahead to stop at next major tag
AUCTION_BLOCK_PATTERN = re.compile(
    r'\[Auction\s+"([NESW])"\]\s*\n([\s\S]*?)(?=\[Play|\[Event|\[Board|\Z)',
    re.MULTILINE
)

# Pattern 3: Bid Cleaner - Extracts valid bids, ignoring annotations
# Matches: 1C, 2H, 3NT, Pass, X, XX (case insensitive)
# Does NOT match: alert markers, comments, annotations
BID_PATTERN = re.compile(
    r'\b([1-7][SHDCN]T?|Pass|X{1,2})\b',
    re.IGNORECASE
)

# Pattern 4: Deal String - Extracts 4-hand deal from [Deal] tag
# Format: "N:spades.hearts.diamonds.clubs spades.hearts.diamonds.clubs ..."
DEAL_PATTERN = re.compile(
    r'\[Deal\s+"([NESW]):([^"]+)"\]'
)

# Pattern 5: Contract - Extracts final contract with optional X/XX
CONTRACT_PATTERN = re.compile(
    r'\[Contract\s+"(\d)([SHDCN]T?)(X{0,2})"\]',
    re.IGNORECASE
)

# Pattern 6: Result - Extracts tricks taken (e.g., "9" for 3NT making 9 tricks)
RESULT_PATTERN = re.compile(r'\[Result\s+"(\d+)"\]')

# Pattern 7: Score - Extracts raw score (e.g., "-500", "+620")
SCORE_PATTERN = re.compile(r'\[Score\s+"([+-]?\d+)"\]')

# Pattern 8: Annotation Stripper - Removes {alerts}, !, =, + annotations
ANNOTATION_PATTERN = re.compile(r'\{[^}]*\}|[!=+]')

# Pattern 9: DoubleDummyTricks - 20-character hex string (4 players x 5 strains)
# Format: "2563225632b87abb87ab" where each char is tricks (0-9, a=10, b=11, c=12, d=13)
DDS_TRICKS_PATTERN = re.compile(r'\[DoubleDummyTricks\s+"([0-9a-dA-D]{20})"\]')

# Pattern 10: OptimumScore - Par score for the deal
OPTIMUM_SCORE_PATTERN = re.compile(r'\[OptimumScore\s+"(NS|EW)\s+([+-]?\d+)"\]')

# Pattern 11: ParContract - Par contract for the deal
PAR_CONTRACT_PATTERN = re.compile(r'\[ParContract\s+"(NS|EW)\s+(\d)([SHDCN]T?)([+-]\d)?"\]')

# Pattern 12: ScoreTable header - Identifies score table format
SCORE_TABLE_PATTERN = re.compile(r'\[ScoreTable\s+"([^"]+)"\]')

# Pattern 13: ScoreTable rows - Parse individual result rows
# Format: "A 1 1 3NT W - 11 - 460 - - Names..."
SCORE_ROW_PATTERN = re.compile(
    r'^([A-Z])\s+(\d+)\s+(\d+)\s+(\d?[SHDCN]T?X{0,2}|Pass)\s+([NESW-])\s+([A-Za-z0-9-]+)\s+(\d+|-)\s+([+-]?\d+|-)\s+([+-]?\d+|-)',
    re.MULTILINE
)


# =============================================================================
# DATA CLASSES
# =============================================================================

class Vulnerability(Enum):
    """Vulnerability states for scoring calculations."""
    NONE = "None"
    NS = "NS"
    EW = "EW"
    BOTH = "Both"

    @classmethod
    def from_pbn(cls, pbn_value: str) -> 'Vulnerability':
        """Convert PBN vulnerability string to enum."""
        mapping = {
            'none': cls.NONE,
            '-': cls.NONE,
            'ns': cls.NS,
            'n-s': cls.NS,
            'ew': cls.EW,
            'e-w': cls.EW,
            'both': cls.BOTH,
            'all': cls.BOTH,
        }
        return mapping.get(pbn_value.lower(), cls.NONE)


@dataclass
class PBNHand:
    """
    Represents a single hand/board from a PBN file.

    Maps PBN tags to V3 API payload format for the Decision Brain.
    """
    # Board identification
    board_number: int = 0
    event_name: str = ""
    date: str = ""

    # Core deal data (maps to V3 API)
    dealer: str = "N"  # N, E, S, W
    vulnerability: str = "None"  # None, NS, EW, Both

    # The four hands - keyed by position
    hands: Dict[str, str] = field(default_factory=dict)  # Position -> PBN string

    # Auction data
    auction_history: List[str] = field(default_factory=list)
    auction_raw: str = ""  # Original multi-line auction text

    # Contract and result
    contract_level: int = 0
    contract_strain: str = ""
    contract_doubled: int = 0  # 0=undoubled, 1=doubled, 2=redoubled
    contract_declarer: str = ""
    tricks_taken: int = 0
    score_ns: int = 0
    score_ew: int = 0

    # Play data (if available)
    play_history: List[str] = field(default_factory=list)

    # DDS Analysis (from hand record exports)
    dds_tricks: Dict[str, Dict[str, int]] = field(default_factory=dict)  # {position: {strain: tricks}}
    optimum_score: int = 0
    optimum_declarer: str = ""  # NS or EW
    par_contract: str = ""
    par_level: int = 0
    par_strain: str = ""
    par_modifier: str = ""  # +1, -2, etc.

    # Tournament results (from ScoreTable)
    score_table: List[Dict[str, Any]] = field(default_factory=list)

    # Validation
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)

    def to_v3_payload(self, hero_position: str = "S") -> Dict[str, Any]:
        """
        Convert to V3 API payload format for the Decision Brain.

        Args:
            hero_position: Which position to analyze from (default South)

        Returns:
            Dict suitable for enhanced_extractor.extract_flat_features()
        """
        position_map = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}

        return {
            'hand': self.hands.get(hero_position, ""),
            'auction_history': self.auction_history,
            'my_position': position_map.get(hero_position, 'South'),
            'vulnerability': self.vulnerability,
            'dealer': position_map.get(self.dealer, 'North'),
            # Additional context for audit
            'board_number': self.board_number,
            'contract': f"{self.contract_level}{self.contract_strain}{'X' * self.contract_doubled}",
            'result': self.tricks_taken,
            'score': self.score_ns if hero_position in ['N', 'S'] else self.score_ew
        }

    def get_hand_json(self, position: str) -> Dict[str, List[str]]:
        """
        Convert PBN hand string to JSON suit-array format.

        Args:
            position: Which hand to convert (N, E, S, W)

        Returns:
            Dict with suit arrays: {'spades': ['A','K',...], 'hearts': [...], ...}
        """
        pbn_hand = self.hands.get(position, "")
        return convert_pbn_deal_to_json(pbn_hand)


@dataclass
class PBNFile:
    """
    Represents a complete PBN file with multiple hands.

    Tracks tournament metadata and all boards.
    """
    # File metadata
    filename: str = ""
    source: str = "unknown"  # 'acbl', 'bbo', 'common_game'

    # Event metadata (from tags)
    event_name: str = ""
    event_date: str = ""
    event_site: str = ""
    scoring_method: str = ""  # 'Matchpoints', 'IMPs', etc.

    # Hands/boards
    hands: List[PBNHand] = field(default_factory=list)

    # Parsing statistics
    total_hands_found: int = 0
    valid_hands: int = 0
    invalid_hands: int = 0
    parsing_errors: List[str] = field(default_factory=list)

    def get_summary(self) -> Dict[str, Any]:
        """Return summary statistics for the import."""
        return {
            'filename': self.filename,
            'source': self.source,
            'event_name': self.event_name,
            'event_date': self.event_date,
            'total_hands': len(self.hands),
            'valid_hands': sum(1 for h in self.hands if h.is_valid),
            'invalid_hands': sum(1 for h in self.hands if not h.is_valid),
            'parsing_errors': len(self.parsing_errors)
        }


# =============================================================================
# CORE PARSING FUNCTIONS
# =============================================================================

def extract_acbl_auction(pbn_content: str) -> List[str]:
    """
    Isolates and cleans the multi-line auction sequence from a PBN file.

    Handles:
    - Multi-line auction blocks
    - Alert annotations ({...} and !)
    - Various bid formats (1H, 1h, pass, PASS, x, X)

    Args:
        pbn_content: Full PBN text content

    Returns:
        List of standardized bids: ['1H', 'Pass', 'Double', '2S', ...]
    """
    # 1. Isolate the block following the [Auction] tag
    match = AUCTION_BLOCK_PATTERN.search(pbn_content)

    if not match:
        # This is normal for hand record files (BridgeComposer exports)
        # Only log at debug level to avoid noise
        logger.debug("No [Auction] block found in PBN content (expected for hand record exports)")
        return []

    raw_auction = match.group(2)

    # 2. Strip annotations ({Alert}, !, =, + markers)
    cleaned = ANNOTATION_PATTERN.sub('', raw_auction)

    # 3. Extract valid bids using bid pattern
    bids = BID_PATTERN.findall(cleaned)

    # 4. Standardize to V3 API format
    standardized = []
    for bid in bids:
        bid_upper = bid.upper()

        if bid_upper == 'X':
            standardized.append('Double')
        elif bid_upper == 'XX':
            standardized.append('Redouble')
        elif bid_upper == 'PASS':
            standardized.append('Pass')
        else:
            # Convert strain letters to symbols for consistency
            # NT stays as NT, but single letters map to symbols
            strain_map = {'S': 'S', 'H': 'H', 'D': 'D', 'C': 'C', 'N': 'N'}
            level = bid_upper[0]
            strain = bid_upper[1:]

            # Handle NT vs N
            if strain == 'NT' or strain == 'N':
                standardized.append(f"{level}NT")
            else:
                standardized.append(f"{level}{strain[0]}")

    return standardized


def parse_dds_tricks_string(dds_string: str) -> Dict[str, Dict[str, int]]:
    """
    Parse the DoubleDummyTricks 20-character hex string.

    Format: "2563225632b87abb87ab"
    - 20 characters total (4 positions x 5 strains)
    - Order: N, S, E, W (each has NT, S, H, D, C)
    - Characters 0-9 = 0-9 tricks, a-d = 10-13 tricks

    Returns:
        Dict like {'N': {'NT': 2, 'S': 5, 'H': 6, 'D': 3, 'C': 2}, ...}
    """
    if not dds_string or len(dds_string) != 20:
        return {}

    def hex_to_tricks(char: str) -> int:
        """Convert hex char to trick count."""
        if char.isdigit():
            return int(char)
        return ord(char.lower()) - ord('a') + 10

    positions = ['N', 'S', 'E', 'W']
    strains = ['NT', 'S', 'H', 'D', 'C']
    result = {}

    for i, pos in enumerate(positions):
        result[pos] = {}
        for j, strain in enumerate(strains):
            char_idx = i * 5 + j
            result[pos][strain] = hex_to_tricks(dds_string[char_idx])

    return result


def parse_score_table_rows(pbn_block: str) -> List[Dict[str, Any]]:
    """
    Parse ScoreTable rows from a PBN block.

    Extracts tournament result rows following the [ScoreTable] tag.

    Returns:
        List of dicts with keys: section, pair_ns, pair_ew, contract, declarer, lead, result, score_ns, score_ew
    """
    results = []

    # Find all score rows
    for match in SCORE_ROW_PATTERN.finditer(pbn_block):
        section, pair_ns, pair_ew, contract, declarer, lead, result, score_ns, score_ew = match.groups()

        results.append({
            'section': section,
            'pair_ns': int(pair_ns),
            'pair_ew': int(pair_ew),
            'contract': contract if contract != 'Pass' else 'Passed',
            'declarer': declarer if declarer != '-' else None,
            'lead': lead if lead != '-' else None,
            'result': int(result) if result != '-' else None,
            'score_ns': int(score_ns) if score_ns not in ['-', ''] else 0,
            'score_ew': int(score_ew) if score_ew not in ['-', ''] else 0
        })

    return results


def convert_pbn_deal_to_json(pbn_hand: str) -> Dict[str, List[str]]:
    """
    Converts PBN "dot notation" hand string to JSON suit-array format.

    PBN Format: "QJ6.K652.J85.T98" (Spades.Hearts.Diamonds.Clubs)
    JSON Format: {'spades': ['Q','J','6'], 'hearts': ['K','6','5','2'], ...}

    Args:
        pbn_hand: PBN hand string (may include direction prefix like "N:")

    Returns:
        Dict with suit arrays keyed by suit name
    """
    # Strip direction prefix if present
    if len(pbn_hand) >= 2 and pbn_hand[1] == ':':
        pbn_hand = pbn_hand[2:]

    # Handle empty hand
    if not pbn_hand:
        return {'spades': [], 'hearts': [], 'diamonds': [], 'clubs': []}

    parts = pbn_hand.split('.')

    if len(parts) != 4:
        logger.warning(f"Invalid PBN hand format: {pbn_hand}")
        return {'spades': [], 'hearts': [], 'diamonds': [], 'clubs': []}

    # PBN order is always S.H.D.C
    suits = ['spades', 'hearts', 'diamonds', 'clubs']
    result = {}

    for i, suit_str in enumerate(parts):
        # Convert each character to a card rank
        cards = list(suit_str.upper())
        result[suits[i]] = cards

    return result


def parse_pbn_deal_string(deal_string: str, first_position: str) -> Dict[str, str]:
    """
    Parse a PBN deal string into individual hand PBN strings.

    Deal Format: "N:QJ6.K652.J85.T98 A932.T4.K96.AQJ2 KT87.AJ987.AT7.5 54.Q3.Q432.K8763"
    The first position indicates whose hand comes first, then clockwise.

    Args:
        deal_string: Full deal string from [Deal] tag
        first_position: Starting position (N, E, S, W)

    Returns:
        Dict mapping position to PBN hand string
    """
    # Position order is always clockwise: N -> E -> S -> W
    position_order = ['N', 'E', 'S', 'W']

    # Find starting index
    start_idx = position_order.index(first_position.upper())

    # Rotate to get correct order
    ordered_positions = position_order[start_idx:] + position_order[:start_idx]

    # Split hands (space-separated)
    hand_strings = deal_string.strip().split()

    if len(hand_strings) != 4:
        logger.warning(f"Expected 4 hands, got {len(hand_strings)}")
        return {}

    hands = {}
    for i, pos in enumerate(ordered_positions):
        hands[pos] = hand_strings[i]

    return hands


def parse_pbn_hand(pbn_block: str) -> PBNHand:
    """
    Parse a single PBN hand/board block into a PBNHand object.

    A block contains all tags for one board/hand.

    Args:
        pbn_block: Text block for one board

    Returns:
        PBNHand object with parsed data
    """
    hand = PBNHand()

    # Extract all tags
    tags = dict(TAG_PATTERN.findall(pbn_block))

    # Board identification
    hand.board_number = int(tags.get('Board', '0') or '0')
    hand.event_name = tags.get('Event', '')
    hand.date = tags.get('Date', '')

    # Dealer (required for auction ordering)
    hand.dealer = tags.get('Dealer', 'N')[0].upper()
    if hand.dealer not in 'NESW':
        hand.dealer = 'N'
        hand.validation_errors.append(f"Invalid dealer: {tags.get('Dealer')}")

    # Vulnerability
    vuln_raw = tags.get('Vulnerable', 'None')
    hand.vulnerability = Vulnerability.from_pbn(vuln_raw).value

    # Deal - parse the 4 hands
    deal_match = DEAL_PATTERN.search(pbn_block)
    if deal_match:
        first_pos = deal_match.group(1)
        deal_string = deal_match.group(2)
        hand.hands = parse_pbn_deal_string(deal_string, first_pos)
    else:
        hand.validation_errors.append("No [Deal] tag found")

    # Auction
    hand.auction_history = extract_acbl_auction(pbn_block)
    auction_match = AUCTION_BLOCK_PATTERN.search(pbn_block)
    if auction_match:
        hand.auction_raw = auction_match.group(2).strip()

    # Contract
    contract_match = CONTRACT_PATTERN.search(pbn_block)
    if contract_match:
        hand.contract_level = int(contract_match.group(1))
        strain = contract_match.group(2).upper()
        hand.contract_strain = 'NT' if strain in ['N', 'NT'] else strain
        doubled = contract_match.group(3)
        hand.contract_doubled = len(doubled)

    # Declarer
    hand.contract_declarer = tags.get('Declarer', '')[0].upper() if tags.get('Declarer') else ''

    # Result (tricks taken)
    result_match = RESULT_PATTERN.search(pbn_block)
    if result_match:
        hand.tricks_taken = int(result_match.group(1))

    # Score
    score_match = SCORE_PATTERN.search(pbn_block)
    if score_match:
        score_str = score_match.group(1)
        # Handle both "+620" and "620" formats
        score = int(score_str.replace('+', ''))
        # Assign to correct side based on declarer
        if hand.contract_declarer in ['N', 'S']:
            hand.score_ns = score
            hand.score_ew = -score
        else:
            hand.score_ew = score
            hand.score_ns = -score

    # DDS Analysis (from hand record exports)
    dds_match = DDS_TRICKS_PATTERN.search(pbn_block)
    if dds_match:
        hand.dds_tricks = parse_dds_tricks_string(dds_match.group(1))

    # Optimum Score
    optimum_match = OPTIMUM_SCORE_PATTERN.search(pbn_block)
    if optimum_match:
        hand.optimum_declarer = optimum_match.group(1)
        hand.optimum_score = int(optimum_match.group(2))

    # Par Contract
    par_match = PAR_CONTRACT_PATTERN.search(pbn_block)
    if par_match:
        par_declarer = par_match.group(1)
        hand.par_level = int(par_match.group(2))
        hand.par_strain = par_match.group(3).upper()
        if hand.par_strain == 'N':
            hand.par_strain = 'NT'
        hand.par_modifier = par_match.group(4) or ''
        hand.par_contract = f"{par_declarer} {hand.par_level}{hand.par_strain}{hand.par_modifier}"

    # ScoreTable rows (tournament results)
    hand.score_table = parse_score_table_rows(pbn_block)

    # Validate the hand
    hand.is_valid = len(hand.validation_errors) == 0 and len(hand.hands) == 4

    return hand


def parse_pbn_file(pbn_content: str, filename: str = "") -> PBNFile:
    """
    Parse a complete PBN file into a PBNFile object.

    Handles multiple hands/boards separated by empty lines.

    Args:
        pbn_content: Full PBN file text
        filename: Optional filename for tracking

    Returns:
        PBNFile object with all parsed hands
    """
    result = PBNFile(filename=filename)

    # Detect source format based on content patterns
    if 'BridgeComposer' in pbn_content:
        result.source = 'bridgecomposer'
    elif 'ACBL' in pbn_content or 'American Contract Bridge' in pbn_content:
        result.source = 'acbl'
    elif 'BBO' in pbn_content or 'Bridge Base' in pbn_content:
        result.source = 'bbo'
    elif 'Common Game' in pbn_content:
        result.source = 'common_game'

    # Extract file-level metadata from first occurrence
    all_tags = dict(TAG_PATTERN.findall(pbn_content))
    result.event_name = all_tags.get('Event', '')
    result.event_date = all_tags.get('Date', '')
    result.event_site = all_tags.get('Site', '')
    result.scoring_method = all_tags.get('Scoring', '')

    # Split into individual board blocks
    # Boards are typically separated by blank lines or start with [Event] or [Board]
    # Use regex to split on patterns that indicate new boards
    board_pattern = re.compile(r'(?=\[(?:Event|Board)\s+")', re.MULTILINE)
    blocks = board_pattern.split(pbn_content)

    # Filter out empty blocks and parse each
    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Must have at least a [Deal] tag to be a valid board
        if '[Deal' not in block and '[deal' not in block:
            continue

        result.total_hands_found += 1

        try:
            hand = parse_pbn_hand(block)
            result.hands.append(hand)

            if hand.is_valid:
                result.valid_hands += 1
            else:
                result.invalid_hands += 1
                result.parsing_errors.extend(hand.validation_errors)

        except Exception as e:
            result.invalid_hands += 1
            result.parsing_errors.append(f"Error parsing board: {str(e)}")
            logger.exception(f"Error parsing PBN block: {block[:100]}...")

    logger.info(f"Parsed PBN file: {result.valid_hands}/{result.total_hands_found} valid hands")

    return result


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def dealer_to_position_index(dealer: str) -> int:
    """Convert dealer letter to position index (0=N, 1=E, 2=S, 3=W)."""
    return {'N': 0, 'E': 1, 'S': 2, 'W': 3}.get(dealer.upper(), 0)


def position_index_to_letter(index: int) -> str:
    """Convert position index to dealer letter."""
    return ['N', 'E', 'S', 'W'][index % 4]


def normalize_strain(strain: str) -> str:
    """Normalize strain to standard format (S, H, D, C, NT)."""
    strain = strain.upper()
    if strain in ['N', 'NT', 'NOTRUMP', 'NO TRUMP']:
        return 'NT'
    if strain in ['S', 'SPADES', 'SPADE']:
        return 'S'
    if strain in ['H', 'HEARTS', 'HEART']:
        return 'H'
    if strain in ['D', 'DIAMONDS', 'DIAMOND']:
        return 'D'
    if strain in ['C', 'CLUBS', 'CLUB']:
        return 'C'
    return strain


def validate_pbn_hand_string(pbn_hand: str) -> Tuple[bool, str]:
    """
    Validate a PBN hand string.

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Strip direction prefix
    if len(pbn_hand) >= 2 and pbn_hand[1] == ':':
        pbn_hand = pbn_hand[2:]

    parts = pbn_hand.split('.')

    if len(parts) != 4:
        return False, f"Expected 4 suits, got {len(parts)}"

    total_cards = 0
    valid_ranks = set('AKQJT98765432')

    for i, part in enumerate(parts):
        for char in part.upper():
            if char not in valid_ranks:
                return False, f"Invalid rank '{char}' in suit {i+1}"
            total_cards += 1

    if total_cards != 13:
        return False, f"Expected 13 cards, got {total_cards}"

    return True, ""

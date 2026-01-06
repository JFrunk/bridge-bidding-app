"""
BWS File Importer for ACBL Tournament Data.

BWS (Bridge Wireless Scoring) files are Microsoft Access databases
used by ACBLscore for tournament scoring. This module extracts:

- ReceivedData: Contract results (declarer, contract, result)
- HandRecord: Deal distributions (if populated)
- BiddingData: Individual bids (if captured by BridgeMate)

Requires: mdbtools (brew install mdbtools on macOS)

Usage:
    from engine.imports.bws_importer import parse_bws_file

    result = parse_bws_file('/path/to/file.bws')
    print(result.contracts)  # List of played contracts
"""

import subprocess
import csv
import io
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path


@dataclass
class BWSContract:
    """Represents a single contract result from BWS ReceivedData."""
    section: int
    table: int
    round: int
    board: int
    pair_ns: int
    pair_ew: int
    declarer: str  # N, E, S, W
    side: str  # NS or EW
    contract: str  # e.g., "3 NT", "4 H x", "5 S xx"
    result: str  # e.g., "=", "+1", "-2"
    lead_card: str = ""

    @property
    def level(self) -> int:
        """Extract contract level (1-7)."""
        match = re.match(r'(\d)', self.contract)
        return int(match.group(1)) if match else 0

    @property
    def strain(self) -> str:
        """Extract strain (C, D, H, S, NT)."""
        strain_map = {'C': 'C', 'D': 'D', 'H': 'H', 'S': 'S', 'NT': 'NT', 'N': 'NT'}
        match = re.search(r'\d\s*([CDHSN]T?)', self.contract)
        if match:
            s = match.group(1).upper()
            return strain_map.get(s, s)
        return ""

    @property
    def is_doubled(self) -> bool:
        """Check if contract is doubled."""
        return ' x' in self.contract.lower() and 'xx' not in self.contract.lower()

    @property
    def is_redoubled(self) -> bool:
        """Check if contract is redoubled."""
        return 'xx' in self.contract.lower()

    @property
    def tricks_made(self) -> int:
        """Calculate total tricks made."""
        required = 6 + self.level
        if self.result == "=":
            return required
        elif self.result.startswith("+"):
            return required + int(self.result[1:])
        elif self.result.startswith("-"):
            return required - int(self.result[1:])
        return required

    @property
    def score(self) -> int:
        """Calculate score for NS (positive = NS gain)."""
        # Simplified scoring - full implementation would need vulnerability
        return calculate_contract_score(
            level=self.level,
            strain=self.strain,
            tricks_made=self.tricks_made,
            doubled=1 if self.is_doubled else (2 if self.is_redoubled else 0),
            vulnerable=False,  # Would need to determine from board number
            declarer_ns=(self.declarer in ['N', 'S'])
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'section': self.section,
            'table': self.table,
            'round': self.round,
            'board': self.board,
            'pair_ns': self.pair_ns,
            'pair_ew': self.pair_ew,
            'declarer': self.declarer,
            'side': self.side,
            'contract': self.contract,
            'result': self.result,
            'lead_card': self.lead_card,
            'level': self.level,
            'strain': self.strain,
            'is_doubled': self.is_doubled,
            'is_redoubled': self.is_redoubled,
            'tricks_made': self.tricks_made
        }


@dataclass
class BWSHandRecord:
    """Represents a hand record from BWS HandRecord table."""
    section: int
    board: int
    north: Dict[str, List[str]] = field(default_factory=dict)
    east: Dict[str, List[str]] = field(default_factory=dict)
    south: Dict[str, List[str]] = field(default_factory=dict)
    west: Dict[str, List[str]] = field(default_factory=dict)

    def to_pbn_deal(self) -> str:
        """Convert to PBN deal string format."""
        def hand_to_pbn(hand: Dict[str, List[str]]) -> str:
            return '.'.join([
                ''.join(hand.get('spades', [])),
                ''.join(hand.get('hearts', [])),
                ''.join(hand.get('diamonds', [])),
                ''.join(hand.get('clubs', []))
            ])

        return f"N:{hand_to_pbn(self.north)} {hand_to_pbn(self.east)} {hand_to_pbn(self.south)} {hand_to_pbn(self.west)}"


@dataclass
class BWSBid:
    """Represents a single bid from BWS BiddingData table."""
    section: int
    table: int
    round: int
    board: int
    counter: int  # Sequence number within auction
    direction: str  # N, E, S, W
    bid: str  # The actual bid


@dataclass
class BWSFile:
    """Represents a parsed BWS file."""
    filename: str
    contracts: List[BWSContract] = field(default_factory=list)
    hand_records: List[BWSHandRecord] = field(default_factory=list)
    bids: List[BWSBid] = field(default_factory=list)
    tables_available: List[str] = field(default_factory=list)

    @property
    def has_hand_records(self) -> bool:
        """Check if hand records are populated."""
        return len(self.hand_records) > 0

    @property
    def has_bidding_data(self) -> bool:
        """Check if bidding data is captured."""
        return len(self.bids) > 0

    @property
    def board_count(self) -> int:
        """Number of unique boards."""
        return len(set(c.board for c in self.contracts))

    @property
    def table_count(self) -> int:
        """Number of unique tables."""
        return len(set((c.section, c.table) for c in self.contracts))

    def get_contracts_for_board(self, board: int, section: int = None) -> List[BWSContract]:
        """Get all contract results for a specific board."""
        contracts = [c for c in self.contracts if c.board == board]
        if section is not None:
            contracts = [c for c in contracts if c.section == section]
        return contracts

    def get_auction_for_table(self, section: int, table: int, round: int, board: int) -> List[str]:
        """Get the auction sequence for a specific table/board."""
        table_bids = [
            b for b in self.bids
            if b.section == section and b.table == table
            and b.round == round and b.board == board
        ]
        # Sort by counter to get correct sequence
        table_bids.sort(key=lambda b: b.counter)
        return [b.bid for b in table_bids]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'filename': self.filename,
            'tables_available': self.tables_available,
            'has_hand_records': self.has_hand_records,
            'has_bidding_data': self.has_bidding_data,
            'board_count': self.board_count,
            'table_count': self.table_count,
            'contracts': [c.to_dict() for c in self.contracts]
        }


def check_mdbtools_available() -> Tuple[bool, str]:
    """Check if mdbtools is installed."""
    try:
        result = subprocess.run(
            ['mdb-tables', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return True, ""
    except FileNotFoundError:
        return False, "mdbtools not installed. Install with: brew install mdbtools"
    except subprocess.TimeoutExpired:
        return False, "mdbtools check timed out"
    except Exception as e:
        return False, f"Error checking mdbtools: {str(e)}"


def list_tables(bws_path: str) -> List[str]:
    """List all tables in a BWS file."""
    try:
        result = subprocess.run(
            ['mdb-tables', bws_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            return []
        return result.stdout.strip().split()
    except Exception:
        return []


def export_table(bws_path: str, table_name: str) -> List[Dict[str, str]]:
    """Export a table from BWS file as list of dictionaries."""
    try:
        result = subprocess.run(
            ['mdb-export', bws_path, table_name],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode != 0:
            return []

        # Parse CSV output
        reader = csv.DictReader(io.StringIO(result.stdout))
        return list(reader)
    except Exception:
        return []


def parse_received_data(rows: List[Dict[str, str]]) -> List[BWSContract]:
    """Parse ReceivedData table into BWSContract objects."""
    contracts = []

    for row in rows:
        try:
            # Skip erased entries
            if row.get('Erased', '0') == '1':
                continue

            # Skip empty contracts
            contract_str = row.get('Contract', '').strip()
            if not contract_str:
                continue

            # The NS/EW column contains the actual declarer direction (N, E, S, W)
            # The 'Declarer' column contains a pair number code, not direction
            declarer_raw = row.get('NS/EW', '').strip().strip('"')

            # Normalize to single character
            declarer_map = {
                'N': 'N', 'E': 'E', 'S': 'S', 'W': 'W',
                'NORTH': 'N', 'EAST': 'E', 'SOUTH': 'S', 'WEST': 'W'
            }
            declarer = declarer_map.get(declarer_raw.upper(), declarer_raw)

            # Determine which side (NS or EW) declares
            side = 'NS' if declarer in ['N', 'S'] else 'EW'

            contract = BWSContract(
                section=int(row.get('Section', 1)),
                table=int(row.get('Table', 0)),
                round=int(row.get('Round', 1)),
                board=int(row.get('Board', 0)),
                pair_ns=int(row.get('PairNS', 0)),
                pair_ew=int(row.get('PairEW', 0)),
                declarer=declarer,
                side=side,
                contract=contract_str,
                result=row.get('Result', '='),
                lead_card=row.get('LeadCard', '')
            )
            contracts.append(contract)
        except (ValueError, KeyError) as e:
            # Skip malformed rows
            continue

    return contracts


def parse_hand_record(rows: List[Dict[str, str]]) -> List[BWSHandRecord]:
    """Parse HandRecord table into BWSHandRecord objects."""
    records = []

    for row in rows:
        try:
            def parse_holding(holding: str) -> List[str]:
                """Parse a holding string like 'AKQ' into ['A', 'K', 'Q']."""
                if not holding:
                    return []
                # Handle both comma-separated and continuous formats
                if ',' in holding:
                    return [c.strip() for c in holding.split(',') if c.strip()]
                return list(holding.replace(' ', ''))

            record = BWSHandRecord(
                section=int(row.get('Section', 1)),
                board=int(row.get('Board', 0)),
                north={
                    'spades': parse_holding(row.get('NorthSpades', '')),
                    'hearts': parse_holding(row.get('NorthHearts', '')),
                    'diamonds': parse_holding(row.get('NorthDiamonds', '')),
                    'clubs': parse_holding(row.get('NorthClubs', ''))
                },
                east={
                    'spades': parse_holding(row.get('EastSpades', '')),
                    'hearts': parse_holding(row.get('EastHearts', '')),
                    'diamonds': parse_holding(row.get('EastDiamonds', '')),
                    'clubs': parse_holding(row.get('EastClubs', ''))
                },
                south={
                    'spades': parse_holding(row.get('SouthSpades', '')),
                    'hearts': parse_holding(row.get('SouthHearts', '')),
                    'diamonds': parse_holding(row.get('SouthDiamonds', '')),
                    'clubs': parse_holding(row.get('SouthClubs', ''))
                },
                west={
                    'spades': parse_holding(row.get('WestSpades', '')),
                    'hearts': parse_holding(row.get('WestHearts', '')),
                    'diamonds': parse_holding(row.get('WestDiamonds', '')),
                    'clubs': parse_holding(row.get('WestClubs', ''))
                }
            )

            # Only add if at least one hand has cards
            if any([record.north, record.east, record.south, record.west]):
                records.append(record)
        except (ValueError, KeyError):
            continue

    return records


def parse_bidding_data(rows: List[Dict[str, str]]) -> List[BWSBid]:
    """Parse BiddingData table into BWSBid objects."""
    bids = []

    for row in rows:
        try:
            # Skip erased bids
            if row.get('Erased', '0') == '1':
                continue

            bid_str = row.get('Bid', '').strip()
            if not bid_str:
                continue

            bid = BWSBid(
                section=int(row.get('Section', 1)),
                table=int(row.get('Table', 0)),
                round=int(row.get('Round', 1)),
                board=int(row.get('Board', 0)),
                counter=int(row.get('Counter', 0)),
                direction=row.get('Direction', ''),
                bid=normalize_bws_bid(bid_str)
            )
            bids.append(bid)
        except (ValueError, KeyError):
            continue

    return bids


def normalize_bws_bid(bid: str) -> str:
    """Normalize BWS bid format to standard format."""
    bid = bid.strip().upper()

    # Pass variants
    if bid in ['P', 'PASS', '-']:
        return 'Pass'

    # Double/Redouble
    if bid in ['X', 'DBL', 'DOUBLE']:
        return 'Double'
    if bid in ['XX', 'RDBL', 'REDOUBLE']:
        return 'Redouble'

    # Strain normalization
    bid = bid.replace('NT', 'NT').replace('N', 'NT') if bid.endswith('N') else bid
    bid = bid.replace(' ', '')  # Remove spaces

    # Convert suit symbols if present
    suit_map = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}
    for abbrev, symbol in suit_map.items():
        if len(bid) == 2 and bid[1] == abbrev:
            bid = bid[0] + symbol

    return bid


def calculate_contract_score(level: int, strain: str, tricks_made: int,
                            doubled: int, vulnerable: bool, declarer_ns: bool) -> int:
    """
    Calculate bridge contract score.

    Args:
        level: Contract level (1-7)
        strain: C, D, H, S, or NT
        tricks_made: Total tricks made (0-13)
        doubled: 0=undoubled, 1=doubled, 2=redoubled
        vulnerable: Whether declarer is vulnerable
        declarer_ns: True if NS declares

    Returns:
        Score from NS perspective (positive = NS gain)
    """
    required = 6 + level
    overtricks = tricks_made - required

    if overtricks < 0:
        # Down
        undertricks = -overtricks
        if doubled == 0:
            penalty = undertricks * (100 if vulnerable else 50)
        elif doubled == 1:
            if vulnerable:
                penalty = 200 + (undertricks - 1) * 300 if undertricks > 1 else 200
            else:
                if undertricks == 1:
                    penalty = 100
                elif undertricks == 2:
                    penalty = 300
                elif undertricks == 3:
                    penalty = 500
                else:
                    penalty = 500 + (undertricks - 3) * 300
        else:  # Redoubled
            penalty = calculate_contract_score(level, strain, tricks_made, 1, vulnerable, declarer_ns) * 2
            if declarer_ns:
                return -penalty
            return penalty

        score = -penalty if declarer_ns else penalty
    else:
        # Made
        # Trick score
        if strain in ['C', 'D']:
            trick_value = 20
        elif strain in ['H', 'S']:
            trick_value = 30
        else:  # NT
            trick_value = 40 + (level - 1) * 30 if level > 1 else 40
            trick_value = 40 + 30 * (level - 1)  # First trick 40, rest 30

        if strain == 'NT':
            base_score = 40 + 30 * (level - 1)
        else:
            base_score = level * trick_value

        if doubled == 1:
            base_score *= 2
        elif doubled == 2:
            base_score *= 4

        # Bonuses
        bonus = 0

        # Game bonus
        if base_score >= 100:
            bonus += 500 if vulnerable else 300
        else:
            bonus += 50  # Part score

        # Slam bonus
        if level == 6:
            bonus += 750 if vulnerable else 500
        elif level == 7:
            bonus += 1500 if vulnerable else 1000

        # Doubled/redoubled making bonus
        if doubled == 1:
            bonus += 50
        elif doubled == 2:
            bonus += 100

        # Overtrick value
        if doubled == 0:
            overtrick_value = trick_value
        elif doubled == 1:
            overtrick_value = 200 if vulnerable else 100
        else:
            overtrick_value = 400 if vulnerable else 200

        score = base_score + bonus + overtricks * overtrick_value
        if not declarer_ns:
            score = -score

    return score


def parse_bws_file(file_path: str) -> BWSFile:
    """
    Parse a BWS file and extract all available data.

    Args:
        file_path: Path to the .bws file

    Returns:
        BWSFile object with parsed data

    Raises:
        FileNotFoundError: If file doesn't exist
        RuntimeError: If mdbtools is not available
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"BWS file not found: {file_path}")

    # Check mdbtools availability
    available, error = check_mdbtools_available()
    if not available:
        raise RuntimeError(error)

    # Get available tables
    tables = list_tables(file_path)

    result = BWSFile(
        filename=path.name,
        tables_available=tables
    )

    # Parse ReceivedData (contract results)
    if 'ReceivedData' in tables:
        rows = export_table(file_path, 'ReceivedData')
        result.contracts = parse_received_data(rows)

    # Parse HandRecord (deal distributions)
    if 'HandRecord' in tables:
        rows = export_table(file_path, 'HandRecord')
        result.hand_records = parse_hand_record(rows)

    # Parse BiddingData (individual bids)
    if 'BiddingData' in tables:
        rows = export_table(file_path, 'BiddingData')
        result.bids = parse_bidding_data(rows)

    return result


def merge_bws_with_pbn(bws_file: BWSFile, pbn_hands: Dict[int, Any]) -> Dict[int, Dict]:
    """
    Merge BWS contract data with PBN hand records.

    Args:
        bws_file: Parsed BWS file with contracts
        pbn_hands: Dictionary mapping board number to PBN hand data

    Returns:
        Dictionary of merged data per board
    """
    merged = {}

    for board_num, pbn_hand in pbn_hands.items():
        board_contracts = bws_file.get_contracts_for_board(board_num)

        merged[board_num] = {
            'hand': pbn_hand,
            'contracts': [c.to_dict() for c in board_contracts],
            'contract_count': len(board_contracts),
            'dds_available': hasattr(pbn_hand, 'dds_tricks') and pbn_hand.dds_tricks
        }

        # If bidding data available, add auction for each table
        if bws_file.has_bidding_data:
            for contract in board_contracts:
                auction = bws_file.get_auction_for_table(
                    contract.section, contract.table,
                    contract.round, contract.board
                )
                if auction:
                    merged[board_num].setdefault('auctions', {})[
                        f"{contract.section}-{contract.table}"
                    ] = auction

    return merged


# Convenience function for direct use
def parse_bws_contracts(file_path: str) -> List[Dict[str, Any]]:
    """
    Simple function to extract just contract results from BWS file.

    Returns list of contract dictionaries.
    """
    bws = parse_bws_file(file_path)
    return [c.to_dict() for c in bws.contracts]

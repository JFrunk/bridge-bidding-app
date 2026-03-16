"""
Oracle Wrapper for External Bidding Engines

Provides a unified interface for comparing MBB bids against external oracles.
Supports:
1. WBridge5 via Table Manager Protocol (TCP/IP on port 2000)
2. Bridge Bot Analyzer (BBA) via CLI batch processing
3. Manual/CSV oracle for pre-computed reference auctions

The oracle interface returns a bid string in MBB format for a given hand + auction state.
"""

import csv
import json
import os
import socket
import subprocess
import tempfile
from typing import Dict, List, Optional, Tuple

from engine.hand import Hand
from qa.pbn_mapper import translate_bid, SUIT_ASCII_TO_UNICODE


class OracleBase:
    """Abstract base for oracle implementations."""

    def get_bid(self, hand: Hand, auction_history: List[str],
                position: str, vulnerability: str, dealer: str) -> Optional[str]:
        """
        Get the oracle's bid for this hand state.

        Returns:
            MBB-format bid string, or None if oracle cannot determine.
        """
        raise NotImplementedError

    def get_full_auction(self, hands: Dict[str, Hand],
                         vulnerability: str, dealer: str) -> List[str]:
        """
        Get the oracle's complete auction for a deal.

        Returns:
            List of MBB-format bid strings.
        """
        raise NotImplementedError


class WBridge5Oracle(OracleBase):
    """
    WBridge5 oracle using Table Manager Protocol (TCP/IP).

    WBridge5 runs as a client connecting to a Table Manager server.
    This wrapper acts as the server, sending hand/auction state and
    receiving bid responses.

    Requires:
    - WBridge5 installed and accessible (Windows binary, or via Wine on Linux/macOS)
    - Port 2000 available for TCP communication
    """

    def __init__(self, exe_path: str, host: str = 'localhost', port: int = 2000,
                 timeout: float = 5.0):
        self.exe_path = exe_path
        self.host = host
        self.port = port
        self.timeout = timeout
        self._process = None
        self._socket = None

    def start(self):
        """Start WBridge5 process and establish TCP connection."""
        # Start listening server first
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((self.host, self.port))
        self._server_socket.listen(1)
        self._server_socket.settimeout(self.timeout * 2)

        # Launch WBridge5 process
        self._process = subprocess.Popen(
            [self.exe_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Accept connection from WBridge5
        self._socket, _ = self._server_socket.accept()
        self._socket.settimeout(self.timeout)

    def stop(self):
        """Terminate WBridge5 process and close connections."""
        if self._socket:
            try:
                self._socket.close()
            except OSError:
                pass
        if self._server_socket:
            try:
                self._server_socket.close()
            except OSError:
                pass
        if self._process:
            self._process.terminate()
            self._process.wait(timeout=5)

    def _send(self, message: str):
        """Send a message to WBridge5 via Table Manager Protocol."""
        self._socket.sendall((message + '\r\n').encode('utf-8'))

    def _receive(self) -> str:
        """Receive a response from WBridge5."""
        data = b''
        while b'\r\n' not in data:
            chunk = self._socket.recv(4096)
            if not chunk:
                break
            data += chunk
        return data.decode('utf-8').strip()

    def _hand_to_tm_format(self, hand: Hand, position: str) -> str:
        """Convert Hand to Table Manager protocol format."""
        dir_map = {'North': 'N', 'East': 'E', 'South': 'S', 'West': 'W'}
        suit_map = {'♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C'}

        parts = []
        for suit_sym in ['♠', '♥', '♦', '♣']:
            cards = [c.rank for c in hand.cards if c.suit == suit_sym]
            parts.append(f"{suit_map[suit_sym]} {''.join(cards)}")

        return f"{dir_map[position]}: {' '.join(parts)}"

    def _bid_to_tm_format(self, bid: str) -> str:
        """Convert MBB bid to Table Manager format."""
        reverse_suit = {'♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C'}
        if bid == 'Pass':
            return 'P'
        if bid == 'X':
            return 'D'
        if bid == 'XX':
            return 'R'
        # Convert suit bids: "1♠" → "1S"
        for sym, letter in reverse_suit.items():
            bid = bid.replace(sym, letter)
        return bid

    def get_bid(self, hand: Hand, auction_history: List[str],
                position: str, vulnerability: str, dealer: str) -> Optional[str]:
        """Get WBridge5's bid via Table Manager Protocol."""
        try:
            # Send hand
            hand_msg = self._hand_to_tm_format(hand, position)
            self._send(hand_msg)

            # Send auction history
            tm_bids = [self._bid_to_tm_format(b) for b in auction_history]
            auction_msg = ' '.join(tm_bids) if tm_bids else ''
            self._send(f"Auction: {auction_msg}")

            # Receive bid response
            response = self._receive()
            # Parse response: typically "NORTH bids 1S" or similar
            bid_token = response.split()[-1] if response else None
            if bid_token:
                return translate_bid(bid_token)
        except (socket.timeout, ConnectionError, OSError):
            return None
        return None


class BBAOracle(OracleBase):
    """
    Bridge Bot Analyzer (BBA) oracle via CLI batch processing.

    BBA wraps WBridge5 and other engines, providing a CLI interface
    for batch PBN verification. This is the recommended approach for
    high-volume differential testing.

    Usage:
        BBA.exe --TEAM1 3 --HAND test_suite.pbn --AUTOBID --INVISIBLE
        --TEAM1 3: WBridge5 as oracle
        --HAND: PBN test file
        --AUTOBID: Auto-bid all hands
        --INVISIBLE: Headless mode
    """

    def __init__(self, exe_path: str, team: int = 3):
        """
        Args:
            exe_path: Path to BBA.exe (or Wine wrapper script)
            team: Engine ID (3 = WBridge5)
        """
        self.exe_path = exe_path
        self.team = team

    def run_batch(self, pbn_path: str, output_dir: str = None) -> List[Dict]:
        """
        Run BBA batch analysis on a PBN file.

        Returns list of dicts with board results including oracle's auction.
        """
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix='bba_')

        output_file = os.path.join(output_dir, 'bba_results.txt')

        cmd = [
            self.exe_path,
            '--TEAM1', str(self.team),
            '--HAND', pbn_path,
            '--AUTOBID',
            '--INVISIBLE',
            '--OUTPUT', output_file,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 min max for batch
            )
            if result.returncode != 0:
                raise RuntimeError(f"BBA failed: {result.stderr}")

            return self._parse_bba_output(output_file)
        except FileNotFoundError:
            raise RuntimeError(
                f"BBA executable not found at '{self.exe_path}'. "
                "Install BBA or provide correct path."
            )

    def _parse_bba_output(self, output_path: str) -> List[Dict]:
        """Parse BBA output file into structured results."""
        results = []
        if not os.path.exists(output_path):
            return results

        with open(output_path, 'r') as f:
            # BBA output format varies — this is a skeleton parser
            # that should be adapted to the actual BBA output format
            content = f.read()
            # Basic parsing of board-by-board results
            for block in content.split('\n\n'):
                if 'Board' in block:
                    result = {'raw': block}
                    results.append(result)

        return results

    def get_bid(self, hand: Hand, auction_history: List[str],
                position: str, vulnerability: str, dealer: str) -> Optional[str]:
        """
        Single-bid mode is not efficient for BBA.
        Use run_batch() for bulk comparisons instead.
        """
        return None

    def get_full_auction(self, hands: Dict[str, Hand],
                         vulnerability: str, dealer: str) -> List[str]:
        """Not supported in single-call mode. Use run_batch()."""
        return []


class CSVOracle(OracleBase):
    """
    Pre-computed oracle from a CSV file of reference auctions.

    CSV format:
        deal_pbn,dealer,vulnerability,auction
        "N:AKQ.T98.765.432 ...",North,None,"1♠ Pass 2♠ Pass Pass Pass"

    Useful for:
    - Manually curated test cases from SAYC reference
    - Vugraph data pre-processed by BBA
    - Regression test fixtures
    """

    def __init__(self, csv_path: str):
        self.records: Dict[str, Dict] = {}
        self._load(csv_path)

    def _load(self, csv_path: str):
        """Load reference auctions from CSV."""
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Key by deal PBN (canonical representation)
                key = row.get('deal_pbn', '').strip()
                if key:
                    auction_str = row.get('auction', '')
                    bids = [b.strip() for b in auction_str.split() if b.strip()]
                    self.records[key] = {
                        'dealer': row.get('dealer', 'North'),
                        'vulnerability': row.get('vulnerability', 'None'),
                        'auction': bids,
                    }

    def get_bid(self, hand: Hand, auction_history: List[str],
                position: str, vulnerability: str, dealer: str) -> Optional[str]:
        """Look up the next bid from reference data."""
        # This requires knowing the full deal PBN to look up — not practical
        # for single-hand queries. Use get_auction_for_deal() instead.
        return None

    def get_auction_for_deal(self, deal_pbn: str) -> Optional[List[str]]:
        """Get the reference auction for a specific deal."""
        record = self.records.get(deal_pbn)
        if record:
            return record['auction']
        return None

#!/usr/bin/env python3
"""
WBridge5 API Service

Provides a REST API wrapper around WBridge5 for automated testing.
WBridge5 runs via Wine in headless mode and this service communicates
with it to get bidding recommendations.

API Endpoints:
    POST /bid - Get single bid recommendation
    POST /batch - Process multiple hands in batch
    GET /health - Health check
    GET /info - Service information

Request format for /bid:
{
    "hand": "K92.QJT7.KQ4.AJ7",  // S.H.D.C notation
    "history": ["1D", "P"],      // Previous bids
    "vulnerability": "None",     // None, NS, EW, Both
    "dealer": "N"               // N, E, S, W
}

Response format:
{
    "bid": "1NT",
    "explanation": "WBridge5 recommendation",
    "source": "wbridge5",
    "elapsed_ms": 150
}
"""

import os
import sys
import json
import time
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# WBridge5 paths
WBRIDGE5_PATH = Path.home() / ".wine/drive_c/WBridge5"
WBRIDGE5_EXE = WBRIDGE5_PATH / "WBridge5.exe"

# PBN file template for WBridge5 input
PBN_TEMPLATE = """[Event "QA Test"]
[Site "Docker"]
[Date "{date}"]
[Board "1"]
[Dealer "{dealer}"]
[Vulnerable "{vul}"]
[Deal "N:{north} E:{east} S:{south} W:{west}"]
[Auction "{dealer}"]
{auction}
"""

# Bid notation conversion
BID_MAP_TO_PBN = {
    '♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C',
    'Pass': 'Pass', 'X': 'X', 'XX': 'XX', 'NT': 'NT'
}

BID_MAP_FROM_PBN = {
    'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣',
    'Pass': 'Pass', 'X': 'X', 'XX': 'XX', 'NT': 'NT'
}


class WBridge5Interface:
    """Interface for communicating with WBridge5."""

    def __init__(self, wbridge5_path: Path = WBRIDGE5_PATH):
        self.wbridge5_path = wbridge5_path
        self.exe_path = wbridge5_path / "WBridge5.exe"
        self._verify_installation()

    def _verify_installation(self):
        """Verify WBridge5 is installed and accessible."""
        if not self.exe_path.exists():
            logger.warning(f"WBridge5 not found at {self.exe_path}")
            logger.warning("Service will run in simulation mode")

    def _convert_hand_to_pbn(self, hand_str: str) -> str:
        """
        Convert our notation to PBN notation.

        Input: "K92.QJT7.KQ4.AJ7" (S.H.D.C)
        Output: "SK92.HQJ107.DKQ4.CAJ7"
        """
        parts = hand_str.split('.')
        if len(parts) != 4:
            raise ValueError(f"Invalid hand format: {hand_str}")

        pbn_parts = []
        suits = ['S', 'H', 'D', 'C']
        for suit, cards in zip(suits, parts):
            if cards:
                # Replace T with 10 for PBN
                cards_pbn = cards.replace('T', '10')
                pbn_parts.append(f"{suit}{cards_pbn}")
            else:
                pbn_parts.append(f"{suit}-")

        return '.'.join(pbn_parts)

    def _convert_history_to_pbn(self, history: List[str]) -> str:
        """Convert bid history to PBN auction format."""
        if not history:
            return ""

        pbn_bids = []
        for bid in history:
            if bid == 'Pass' or bid == 'P':
                pbn_bids.append('Pass')
            elif bid == 'X':
                pbn_bids.append('X')
            elif bid == 'XX':
                pbn_bids.append('XX')
            else:
                # Level + suit bids
                level = bid[0]
                strain = bid[1:]
                strain_pbn = strain.replace('♠', 'S').replace('♥', 'H').replace('♦', 'D').replace('♣', 'C')
                pbn_bids.append(f"{level}{strain_pbn}")

        # Format as PBN auction (4 bids per line)
        lines = []
        for i in range(0, len(pbn_bids), 4):
            lines.append(' '.join(pbn_bids[i:i+4]))
        return '\n'.join(lines)

    def _convert_bid_from_pbn(self, pbn_bid: str) -> str:
        """Convert PBN bid notation to our format."""
        if pbn_bid in ['Pass', 'X', 'XX']:
            return pbn_bid

        level = pbn_bid[0]
        strain = pbn_bid[1:]

        strain_ours = (strain.replace('S', '♠')
                           .replace('H', '♥')
                           .replace('D', '♦')
                           .replace('C', '♣'))

        return f"{level}{strain_ours}"

    def get_bid(
        self,
        hand: str,
        history: List[str],
        vulnerability: str = "None",
        dealer: str = "N",
        position: str = None
    ) -> Tuple[str, str]:
        """
        Get bid recommendation from WBridge5.

        Args:
            hand: Hand in S.H.D.C notation
            history: List of previous bids
            vulnerability: None, NS, EW, Both
            dealer: N, E, S, W
            position: Which position is bidding (derived from history if not provided)

        Returns:
            Tuple of (bid, explanation)
        """
        # Determine bidding position from history
        if position is None:
            positions = ['N', 'E', 'S', 'W']
            dealer_idx = positions.index(dealer[0].upper())
            position_idx = (dealer_idx + len(history)) % 4
            position = positions[position_idx]

        # For now, return simulation since WBridge5 requires actual Windows setup
        return self._simulate_bid(hand, history, vulnerability, dealer, position)

    def _simulate_bid(
        self,
        hand: str,
        history: List[str],
        vulnerability: str,
        dealer: str,
        position: str
    ) -> Tuple[str, str]:
        """
        Simulate WBridge5 response (for development/testing without actual WBridge5).

        This returns a placeholder until WBridge5 is properly integrated.
        """
        logger.debug(f"Simulating WBridge5 bid for position {position}")

        # Return placeholder
        return ("?", "WBridge5 simulation mode - actual integration pending")


# Create global interface instance
wbridge5 = WBridge5Interface()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'wbridge5-qa',
        'mode': 'simulation' if not WBRIDGE5_EXE.exists() else 'live'
    })


@app.route('/info', methods=['GET'])
def service_info():
    """Service information endpoint."""
    return jsonify({
        'service': 'WBridge5 QA API',
        'version': '1.0.0',
        'wbridge5_path': str(WBRIDGE5_PATH),
        'wbridge5_installed': WBRIDGE5_EXE.exists(),
        'mode': 'simulation' if not WBRIDGE5_EXE.exists() else 'live',
        'endpoints': {
            'POST /bid': 'Get single bid recommendation',
            'POST /batch': 'Process multiple hands',
            'GET /health': 'Health check',
            'GET /info': 'Service information'
        }
    })


@app.route('/bid', methods=['POST'])
def get_bid():
    """
    Get bid recommendation from WBridge5.

    Request body:
    {
        "hand": "K92.QJT7.KQ4.AJ7",
        "history": ["1D", "P"],
        "vulnerability": "None",
        "dealer": "N"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        hand = data.get('hand')
        if not hand:
            return jsonify({'error': 'Missing required field: hand'}), 400

        history = data.get('history', [])
        vulnerability = data.get('vulnerability', 'None')
        dealer = data.get('dealer', 'N')

        start_time = time.time()
        bid, explanation = wbridge5.get_bid(hand, history, vulnerability, dealer)
        elapsed_ms = (time.time() - start_time) * 1000

        return jsonify({
            'bid': bid,
            'explanation': explanation,
            'source': 'wbridge5',
            'elapsed_ms': round(elapsed_ms, 2),
            'input': {
                'hand': hand,
                'history': history,
                'vulnerability': vulnerability,
                'dealer': dealer
            }
        })

    except Exception as e:
        logger.error(f"Error processing bid request: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/batch', methods=['POST'])
def batch_bids():
    """
    Process multiple hands in batch.

    Request body:
    {
        "hands": [
            {"hand": "K92.QJT7.KQ4.AJ7", "history": ["1D", "P"]},
            {"hand": "AQ4.KJ5.T93.AKJ2", "history": []}
        ],
        "vulnerability": "None",
        "dealer": "N"
    }
    """
    try:
        data = request.get_json()

        if not data or 'hands' not in data:
            return jsonify({'error': 'Missing required field: hands'}), 400

        hands = data['hands']
        vulnerability = data.get('vulnerability', 'None')
        dealer = data.get('dealer', 'N')

        results = []
        start_time = time.time()

        for item in hands:
            hand = item.get('hand')
            history = item.get('history', [])

            if not hand:
                results.append({'error': 'Missing hand', 'input': item})
                continue

            try:
                bid, explanation = wbridge5.get_bid(hand, history, vulnerability, dealer)
                results.append({
                    'bid': bid,
                    'explanation': explanation,
                    'input': item
                })
            except Exception as e:
                results.append({'error': str(e), 'input': item})

        elapsed_ms = (time.time() - start_time) * 1000

        return jsonify({
            'results': results,
            'total': len(hands),
            'elapsed_ms': round(elapsed_ms, 2),
            'source': 'wbridge5'
        })

    except Exception as e:
        logger.error(f"Error processing batch request: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8081))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'

    logger.info(f"Starting WBridge5 QA Service on port {port}")
    logger.info(f"WBridge5 path: {WBRIDGE5_PATH}")
    logger.info(f"WBridge5 installed: {WBRIDGE5_EXE.exists()}")

    app.run(host='0.0.0.0', port=port, debug=debug)

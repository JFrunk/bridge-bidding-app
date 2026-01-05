#!/usr/bin/env python3
"""
WBridge5 Oracle Service - Blue Chip Bridge Protocol Implementation

ARCHITECTURE:
- We (Python) are the TABLE MANAGER (SERVER) - we listen on port 2000
- WBridge5 is the CLIENT - it connects TO us when launched with arguments
- WBridge5 SPEAKS FIRST after connection with identification message

Protocol Handshake:
1. We listen on port 2000
2. Launch WBridge5 with: wine WBridge5.exe Autoconnect 127.0.0.1 2000
3. WBridge5 connects and sends: 'Connecting "WBridge5" using protocol 18'
4. We respond with seat: 'NORTH'
5. WBridge5: 'NORTH ready for teams'
6. We send: 'Teams "Humans" "WBridge5"'
7. WBridge5: 'NORTH ready to start'
8. Bot is ready for cards and bidding
"""

import socket
import subprocess
import threading
import time
import os
import logging
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
EXE_PATH = "/app/WBridge5.exe"
TABLE_MANAGER_PORT = 3000  # We listen here, WBridge5 connects to us (use 3000 to avoid conflicts)
DISPLAY = ":99"

# Global state
wbridge5_process = None
client_conn = None
client_lock = threading.Lock()
server_socket = None
connected_event = threading.Event()
handshake_complete = threading.Event()
assigned_seat = None


def recv_line(conn, timeout=10):
    """Receive a line from the connection."""
    conn.settimeout(timeout)
    data = b""
    while True:
        chunk = conn.recv(1)
        if not chunk:
            break
        data += chunk
        if chunk == b'\n':
            break
    return data.decode('ascii', errors='ignore').strip()


def send_line(conn, msg):
    """Send a line to the connection."""
    logger.debug(f">> SEND: {msg}")
    conn.sendall((msg + "\r\n").encode('ascii'))


def handle_handshake(conn, seat_name="North"):
    """
    Performs the Blue Chip handshake with WBridge5.

    Blue Chip Protocol Handshake:
    1. Client sends: Connecting "WBridge5" as ANYPL using protocol version 18
    2. Server sends: North ("WBridge5") seated
    3. Client sends: NORTH ready for teams
    4. Server sends: Teams : N/S : "Humans". E/W : "WBridge5"
    5. Client sends: NORTH ready to start

    Returns True if handshake successful, False otherwise.
    """
    global assigned_seat
    import re

    try:
        # 1. Receive Connecting message from WBridge5
        # Format: Connecting "WBridge5" as ANYPL using protocol version 18
        data = recv_line(conn, timeout=30)
        logger.info(f"<< RECV: {data}")

        if "Connecting" not in data:
            logger.error(f"Invalid protocol header: {data}")
            return False

        # Parse team name from message
        match = re.search(r'"([^"]+)"', data)
        team_name = match.group(1) if match else "WBridge5"
        logger.info(f"Team name: {team_name}")

        # 2. Send Seated response
        # Format: North ("WBridge5") seated
        seated_msg = f'{seat_name} ("{team_name}") seated'
        send_line(conn, seated_msg)
        assigned_seat = seat_name.upper()

        # 3. Receive Ready for Teams
        # Format: NORTH ready for teams
        data = recv_line(conn, timeout=10)
        logger.info(f"<< RECV: {data}")

        if "ready for teams" not in data.lower():
            logger.warning(f"Unexpected response (expected 'ready for teams'): {data}")

        # 4. Send Team Names
        # Format: Teams : N/S : "Humans". E/W : "WBridge5"
        teams_msg = 'Teams : N/S : "Humans". E/W : "WBridge5"'
        send_line(conn, teams_msg)

        # 5. Receive Ready to Start
        # Format: NORTH ready to start
        data = recv_line(conn, timeout=10)
        logger.info(f"<< RECV: {data}")

        if "ready to start" in data.lower():
            logger.info(">>> Handshake Complete. Bot is ready!")
            return True
        else:
            logger.warning(f"Unexpected final message: {data}")
            return True  # Still consider it complete

    except socket.timeout:
        logger.error("Handshake timeout")
        return False
    except Exception as e:
        logger.error(f"Handshake failed: {e}")
        return False


def start_table_manager_server():
    """Start our Table Manager server that WBridge5 will connect to."""
    global server_socket, client_conn

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', TABLE_MANAGER_PORT))
    server_socket.listen(1)
    server_socket.settimeout(60)

    logger.info(f"Table Manager listening on port {TABLE_MANAGER_PORT}...")

    try:
        conn, addr = server_socket.accept()
        logger.info(f"WBridge5 connected from {addr}")

        with client_lock:
            client_conn = conn

        connected_event.set()

        # Perform Blue Chip handshake
        if handle_handshake(conn):
            handshake_complete.set()
            logger.info("WBridge5 handshake successful!")
        else:
            logger.error("WBridge5 handshake failed!")

    except socket.timeout:
        logger.error("Timeout waiting for WBridge5 to connect")
    except Exception as e:
        logger.error(f"Table Manager error: {e}")


def launch_wbridge5():
    """Launch WBridge5 as a client connecting to our Table Manager."""
    global wbridge5_process

    if wbridge5_process is not None and wbridge5_process.poll() is None:
        return

    env = os.environ.copy()
    env['DISPLAY'] = DISPLAY
    env['WINEDEBUG'] = '-all'

    # WBridge5 command with Autoconnect:
    # WBridge5.exe Autoconnect [Port] (just port number, connects to localhost)
    cmd = ["wine", EXE_PATH, "Autoconnect", str(TABLE_MANAGER_PORT)]

    logger.info(f"Launching WBridge5: {' '.join(cmd)}")
    wbridge5_process = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def ensure_connected():
    """Ensure WBridge5 is connected and handshake is complete."""
    global client_conn

    if handshake_complete.is_set():
        return True

    # Start server in background thread
    server_thread = threading.Thread(target=start_table_manager_server, daemon=True)
    server_thread.start()

    # Give server a moment to start listening
    time.sleep(0.5)

    # Launch WBridge5 (it will connect to our server)
    launch_wbridge5()

    # Wait for handshake to complete
    if handshake_complete.wait(timeout=45):
        logger.info("WBridge5 fully initialized!")
        return True
    else:
        logger.error("WBridge5 initialization failed")
        return False


def format_hand_for_protocol(hand_str):
    """
    Convert hand from 'AK32.QJ76.T98.54' format to Blue Chip protocol format.
    Input: 'AK32.QJ76.T98.54' (S.H.D.C)
    Output: 'S A K 3 2. H Q J 7 6. D T 9 8. C 5 4.'
    """
    suits = hand_str.split('.')
    suit_names = ['S', 'H', 'D', 'C']
    parts = []
    for i, suit in enumerate(suits):
        if suit == '' or suit == '-':
            parts.append(f"{suit_names[i]} -")
        else:
            cards = ' '.join(list(suit))
            parts.append(f"{suit_names[i]} {cards}")
    return '. '.join(parts) + '.'


def convert_dealer(dealer):
    """Convert dealer letter to full name."""
    mapping = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}
    return mapping.get(dealer.upper(), 'North')


def convert_vulnerability(vulnerability):
    """Convert vulnerability string to Blue Chip format."""
    vul = vulnerability.lower() if vulnerability else 'none'
    if vul in ['none', 'neither', '-']:
        return 'Neither vulnerable'
    elif vul in ['ns', 'n/s', 'n-s']:
        return 'N/S vulnerable'
    elif vul in ['ew', 'e/w', 'e-w']:
        return 'E/W vulnerable'
    elif vul in ['both', 'all']:
        return 'Both vulnerable'
    return 'Neither vulnerable'


def parse_bid_response(response):
    """
    Parse bid from WBridge5 response.
    Example: 'NORTH bids 1NT'
    Example: 'NORTH passes'
    Example: 'NORTH doubles'
    """
    response = response.lower()
    if 'passes' in response or 'pass' in response:
        return 'Pass'
    if 'doubles' in response:
        return 'X'
    if 'redoubles' in response:
        return 'XX'
    # Parse bid like "bids 1NT", "bids 2H"
    import re
    match = re.search(r'bids\s+(\d+)([CDHSN][T]?)', response, re.IGNORECASE)
    if match:
        level = match.group(1)
        strain = match.group(2).upper()
        # Convert NT if needed
        if strain == 'N':
            strain = 'NT'
        return f"{level}{strain}"
    return 'Pass'


# Board counter for unique board numbers
board_counter = 0


def get_bid_from_wbridge5(hand, history, dealer='N', vulnerability='None'):
    """
    Get a bid recommendation from WBridge5.

    Protocol for getting a bid:
    1. Send: start of board
    2. Wait for: NORTH ready for deal info
    3. Send: Board number X. Dealer {dealer}. {vulnerability}
    4. Wait for: NORTH ready for cards
    5. Send: North's cards : {cards}
    6. [If there's bidding history, send previous bids]
    7. Send: North ready for North's bid
    8. Wait for: NORTH {bid}
    """
    global client_conn, board_counter

    try:
        if not ensure_connected():
            return "Pass", "Failed to connect to WBridge5"

        with client_lock:
            if client_conn is None:
                return "Pass", "No connection to WBridge5"

            conn = client_conn
            board_counter += 1

            logger.info(f"=== Getting bid for hand: {hand}, history: {history} ===")

            # Step 1: Start a new board
            send_line(conn, "start of board")

            # Wait for ready for deal info
            response = recv_line(conn, timeout=10)
            logger.info(f"<< {response}")

            # Step 2: Send board info
            dealer_name = convert_dealer(dealer)
            vuln_str = convert_vulnerability(vulnerability)
            board_info = f"Board number {board_counter}. Dealer {dealer_name}. {vuln_str}"
            send_line(conn, board_info)

            # Wait for ready for cards
            response = recv_line(conn, timeout=10)
            logger.info(f"<< {response}")

            # Step 3: Send North's cards
            formatted_hand = format_hand_for_protocol(hand)
            cards_msg = f"North's cards : {formatted_hand}"
            send_line(conn, cards_msg)

            # If dealer is North and no history, WBridge5 will bid immediately!
            # Wait for response - this might be the bid itself
            response = recv_line(conn, timeout=10)
            logger.info(f"<< {response}")

            # Calculate if North is dealer
            seat_order = ['N', 'E', 'S', 'W']
            dealer_idx = seat_order.index(dealer.upper())
            north_is_dealer = (dealer_idx == 0)

            # Check if this response is already a bid
            if 'bids' in response.lower() or 'passes' in response.lower() or 'doubles' in response.lower():
                # WBridge5 already made a bid!
                # Only return this if there's no history to replay (first bid of auction)
                if not history or len(history) == 0:
                    bid = parse_bid_response(response)
                    logger.info(f"Parsed bid (immediate, no history): {bid}")
                    return bid, "WBridge5 recommendation"
                else:
                    # There's history - this is the first bid but we need to continue
                    # and tell WBridge5 about the rest of the auction
                    logger.info(f"(Initial bid, but history exists - continuing to replay...)")

            # Step 4: Replay bidding history if any
            # We need to fill in bids from dealer up to North's turn
            # Turn order from dealer: dealer -> +1 -> +2 -> +3
            # North is position 0 (N=0, E=1, S=2, W=3)
            seat_order = ['N', 'E', 'S', 'W']
            seat_names = ['North', 'East', 'South', 'West']
            dealer_idx = seat_order.index(dealer.upper())
            north_idx = 0

            # Calculate how many bids until North's turn
            bids_to_north = (north_idx - dealer_idx) % 4
            if bids_to_north == 0:
                bids_to_north = 0  # North is dealer, already handled above

            # Extend history with passes if needed to reach North's turn
            full_history = list(history) if history else []
            while len(full_history) < bids_to_north:
                full_history.append('Pass')

            logger.info(f"Full history (padded): {full_history}, bids_to_north: {bids_to_north}")

            if full_history:
                # Track which bids in the history are North's (we need to replay them, not return them)
                north_bids_in_history = set()
                for i in range(len(full_history)):
                    if (dealer_idx + i) % 4 == 0:  # North's position
                        north_bids_in_history.add(i)

                for i, bid in enumerate(full_history):
                    seat_idx = (dealer_idx + i) % 4
                    seat = seat_names[seat_idx]
                    is_history_bid = (i in north_bids_in_history)

                    # Format the bid
                    if bid.lower() == 'pass':
                        bid_msg = f"{seat} passes"
                    elif bid.upper() == 'X':
                        bid_msg = f"{seat} doubles"
                    elif bid.upper() == 'XX':
                        bid_msg = f"{seat} redoubles"
                    else:
                        bid_msg = f"{seat} bids {bid}"

                    send_line(conn, bid_msg)
                    # WBridge5 may acknowledge or make its own bid
                    try:
                        ack = recv_line(conn, timeout=5)
                        logger.info(f"<< {ack}")
                        # If it's a NEW bid from North (not replaying history), we're done
                        if 'north' in ack.lower() and ('bids' in ack.lower() or 'passes' in ack.lower() or 'doubles' in ack.lower()):
                            # Check if this is a new bid or just echoing history
                            if seat != 'North' or not is_history_bid:
                                # This is WBridge5's new bid, return it
                                bid = parse_bid_response(ack)
                                logger.info(f"Parsed bid (after history): {bid}")
                                return bid, "WBridge5 recommendation"
                            else:
                                # This is just WBridge5 echoing the history, continue
                                logger.info(f"(History echo, continuing...)")
                    except socket.timeout:
                        pass

            # Step 5: If we haven't gotten a bid yet, request it
            send_line(conn, "North ready for North's bid")

            # Wait for bid response
            response = recv_line(conn, timeout=30)
            logger.info(f"<< {response}")

            # Parse the bid
            bid = parse_bid_response(response)
            logger.info(f"Parsed bid: {bid}")

            return bid, f"WBridge5 recommendation"

    except socket.timeout:
        logger.error("Timeout waiting for WBridge5 response")
        return "Pass", "Timeout waiting for WBridge5"
    except Exception as e:
        logger.error(f"Error getting bid: {e}")
        import traceback
        traceback.print_exc()
        return "Pass", str(e)


@app.route('/bid', methods=['POST'])
def get_bid():
    """Get bid recommendation from WBridge5."""
    data = request.get_json() or {}
    hand = data.get('hand', '')
    history = data.get('history', [])
    dealer = data.get('dealer', 'N')
    vulnerability = data.get('vulnerability', 'None')

    bid, explanation = get_bid_from_wbridge5(hand, history, dealer, vulnerability)

    return jsonify({
        "bid": bid,
        "explanation": explanation,
        "source": "wbridge5",
        "input": {
            "hand": hand,
            "history": history,
            "dealer": dealer
        }
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    global wbridge5_process, client_conn

    process_running = wbridge5_process is not None and wbridge5_process.poll() is None
    is_connected = connected_event.is_set()
    is_ready = handshake_complete.is_set()

    return jsonify({
        "status": "healthy",
        "service": "wbridge5-oracle",
        "exe_exists": os.path.exists(EXE_PATH),
        "process_running": process_running,
        "client_connected": is_connected,
        "handshake_complete": is_ready,
        "assigned_seat": assigned_seat,
        "mode": "live" if is_ready else "initializing"
    })


@app.route('/test-connection', methods=['GET'])
def test_connection():
    """Test WBridge5 connection and handshake."""
    try:
        if ensure_connected():
            return jsonify({
                "status": "connected",
                "message": f"WBridge5 connected and ready at seat {assigned_seat}",
                "seat": assigned_seat
            })
        else:
            return jsonify({
                "status": "timeout",
                "message": "WBridge5 failed to connect within timeout"
            }), 500

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == '__main__':
    logger.info("Starting WBridge5 Oracle Service (Table Manager)...")
    logger.info(f"EXE path: {EXE_PATH}")
    logger.info(f"EXE exists: {os.path.exists(EXE_PATH)}")
    logger.info(f"Will listen on port {TABLE_MANAGER_PORT} for WBridge5 connections")

    app.run(host='0.0.0.0', port=5005, threaded=True)

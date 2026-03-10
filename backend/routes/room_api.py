"""
Room API - Endpoints for Team Practice Lobby

Provides room creation, joining, polling, and game management for
two human partners playing against AI opponents.

To add to server.py:
    from routes.room_api import register_room_endpoints
    register_room_endpoints(app, room_manager)
"""

import random
from flask import request, jsonify
from datetime import datetime
from typing import Optional

from core.room_state import RoomStateManager, RoomSettings, RoomState
from core.session_state import get_session_id_from_request
from engine.hand import Hand, Card
from engine.hand_constructor import generate_hand_for_convention, generate_hand_with_constraints
from engine.ai.bidding_state import BiddingStateBuilder
from utils.seats import (
    partner as seats_partner, lho, normalize, seat_index, SEAT_NAMES, SEATS
)


def get_ai_bid_for_room(room: RoomState, position: str) -> str:
    """
    Get AI bid for E/W position using the bidding engine

    Args:
        room: Current room state
        position: 'E' or 'W'

    Returns:
        Bid string (e.g., '1NT', 'Pass')
    """
    try:
        # Import bidding engine (lazy to avoid circular imports)
        from engine.v2 import BiddingEngineV2Schema
        engine = BiddingEngineV2Schema()

        # Get the hand for this position
        position_full = SEAT_NAMES[position]
        hand = room.deal.get(position_full)

        if not hand:
            return 'Pass'

        # Get bid from engine
        # get_next_bid returns (bid, explanation) tuple
        bid, explanation = engine.get_next_bid(
            hand=hand,
            auction_history=room.auction_history,
            my_position=position_full,
            vulnerability=room.vulnerability or 'None',
            dealer=SEAT_NAMES.get(normalize(room.dealer), room.dealer)
        )

        return bid or 'Pass'
    except Exception as e:
        print(f"⚠️ AI bid error for {position}: {e}")
        return 'Pass'


def auto_bid_for_ai(room: RoomState) -> list:
    """
    Auto-bid for E/W positions until a human's turn

    Returns:
        List of AI bids made: [{'position': 'E', 'bid': 'Pass'}, ...]
    """
    ai_bids = []

    while room.game_phase == 'bidding':
        current_bidder = room.get_current_bidder()

        if current_bidder not in ('E', 'W'):
            # Human's turn - stop
            break

        # AI's turn - get bid
        ai_bid = get_ai_bid_for_room(room, current_bidder)
        room.auction_history.append(ai_bid)
        ai_bids.append({'position': current_bidder, 'bid': ai_bid})
        room.increment_version()

        # Check if auction is complete
        if _check_auction_complete(room.auction_history):
            room.game_phase = 'complete'
            break

    return ai_bids


# Convention map for hand generation (mirrors server.py)
def get_convention_map():
    """Lazy import to avoid circular dependencies"""
    from engine.ai.conventions.preempts import PreemptConvention
    from engine.ai.conventions.jacoby_transfers import JacobyConvention
    from engine.ai.conventions.stayman import StaymanConvention
    from engine.ai.conventions.blackwood import BlackwoodConvention
    from engine.ai.conventions.strong_2c import Strong2CConvention

    return {
        "Preempt": PreemptConvention(),
        "JacobyTransfer": JacobyConvention(),
        "Stayman": StaymanConvention(),
        "Blackwood": BlackwoodConvention(),
        "Strong2C": Strong2CConvention(),
    }


def _get_user_id_from_request(req) -> Optional[str]:
    """Extract user ID from X-User-ID header (set by frontend sessionHelper)"""
    user_id = req.headers.get('X-User-ID')
    if user_id:
        return str(user_id)
    # Fallback: check JSON body
    data = req.get_json(silent=True) or {}
    if data.get('user_id'):
        return str(data['user_id'])
    return None


def _find_or_create_partnership(user_a: str, user_b: str) -> Optional[int]:
    """
    Find existing partnership or create new one between two users.

    Always stores with lexicographically smaller ID as player_a to ensure
    the UNIQUE(player_a_id, player_b_id) constraint works regardless of
    who creates vs joins.

    Returns partnership ID, or None if DB unavailable or users not registered.
    """
    try:
        from db import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Canonical ordering: smaller ID = player_a
        a, b = (user_a, user_b) if user_a < user_b else (user_b, user_a)

        # Check for existing partnership
        cursor.execute(
            "SELECT id FROM partnerships WHERE player_a_id = %s AND player_b_id = %s",
            (a, b)
        )
        row = cursor.fetchone()
        if row:
            partnership_id = row['id'] if isinstance(row, dict) else row[0]
            print(f"🤝 Found existing partnership {partnership_id} between {a} and {b}")
            conn.close()
            return partnership_id

        # Create new partnership
        cursor.execute(
            "INSERT INTO partnerships (player_a_id, player_b_id, status) VALUES (%s, %s, 'active') RETURNING id",
            (a, b)
        )
        row = cursor.fetchone()
        partnership_id = row['id'] if isinstance(row, dict) else row[0]
        conn.commit()
        print(f"🤝 Created new partnership {partnership_id} between {a} and {b}")
        conn.close()
        return partnership_id

    except Exception as e:
        print(f"⚠️ Partnership lookup/create failed (non-blocking): {e}")
        return None


def _save_room_hand(room: RoomState):
    """
    Save completed room hand to session_hands for both players.

    Called when game_phase transitions to 'complete' (13 tricks played or passed out).
    Tags hand with partnership_id if available.
    """
    try:
        from db import get_db_connection
        import json

        if not room.play_state and not room.auction_history:
            print("⚠️ No play state or auction — skipping room hand save")
            return

        conn = get_db_connection()
        cursor = conn.cursor()

        # Build hand data from room state
        contract = room.play_state.contract if room.play_state else None
        ps = room.play_state

        # Check if passed out (no contract)
        passed_out = contract is None

        # Calculate score
        hand_score = 0
        tricks_taken = 0
        made = False
        breakdown = {}

        if not passed_out and ps:
            tricks_taken = ps.tricks_won.get(contract.declarer, 0) + ps.tricks_won.get(
                {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}[contract.declarer], 0
            )
            tricks_needed = contract.level + 6
            made = tricks_taken >= tricks_needed

            # Calculate score using play engine
            try:
                from engine.play_engine import PlayEngine
                score_result = PlayEngine.calculate_score(
                    contract, tricks_taken, room.vulnerability
                )
                hand_score = score_result.get('score', 0)
                breakdown = score_result
            except Exception as e:
                print(f"⚠️ Score calculation failed: {e}")

        # Serialize deal data
        deal_data = {}
        for pos_name, hand in room.deal.items():
            if hand:
                try:
                    deal_data[pos_name] = [{'rank': c.rank, 'suit': c.suit} for c in hand.cards]
                except AttributeError:
                    deal_data[pos_name] = hand if isinstance(hand, list) else []

        # Serialize play history
        play_history = []
        if ps and ps.trick_history:
            for trick in ps.trick_history:
                play_history.append({
                    'cards': [{'rank': c.rank, 'suit': c.suit, 'position': p} for c, p in trick.cards],
                    'winner': trick.winner,
                    'leader': getattr(trick, 'leader', None),
                })

        # Save for each human player (host=S, guest=N)
        players = [
            (room.host_session_id, room.host_user_id, 'S'),
            (room.guest_session_id, room.guest_user_id, 'N'),
        ]

        for session_id, user_id, position in players:
            if not session_id:
                continue

            # Determine if this player was declarer/dummy
            declarer = contract.declarer if contract else None
            dummy = seats_partner(declarer) if declarer else None
            user_was_declarer = (position == declarer)
            user_was_dummy = (position == dummy)

            # Check if partnership_id column exists
            cursor.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'session_hands' AND column_name = 'partnership_id'"
            )
            has_partnership_col = cursor.fetchone() is not None

            # Build INSERT — include partnership_id if column exists
            if has_partnership_col and room.partnership_id:
                cursor.execute("""
                    INSERT INTO session_hands
                    (session_id, hand_number, dealer, vulnerability,
                     contract_level, contract_strain, contract_declarer, contract_doubled,
                     tricks_taken, tricks_needed, made,
                     hand_score, score_breakdown,
                     deal_data, auction_history, play_history,
                     user_played_position, user_was_declarer, user_was_dummy,
                     partnership_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    session_id,
                    1,  # hand_number within room (could track per-room)
                    room.dealer,
                    room.vulnerability,
                    contract.level if contract else None,
                    contract.strain if contract else None,
                    declarer,
                    contract.doubled if contract else 0,
                    tricks_taken,
                    (contract.level + 6) if contract else None,
                    made,
                    hand_score,
                    json.dumps(breakdown),
                    json.dumps(deal_data),
                    json.dumps(room.auction_history),
                    json.dumps(play_history),
                    position,
                    user_was_declarer,
                    user_was_dummy,
                    room.partnership_id,
                ))
            else:
                cursor.execute("""
                    INSERT INTO session_hands
                    (session_id, hand_number, dealer, vulnerability,
                     contract_level, contract_strain, contract_declarer, contract_doubled,
                     tricks_taken, tricks_needed, made,
                     hand_score, score_breakdown,
                     deal_data, auction_history, play_history,
                     user_played_position, user_was_declarer, user_was_dummy)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    session_id,
                    1,
                    room.dealer,
                    room.vulnerability,
                    contract.level if contract else None,
                    contract.strain if contract else None,
                    declarer,
                    contract.doubled if contract else 0,
                    tricks_taken,
                    (contract.level + 6) if contract else None,
                    made,
                    hand_score,
                    json.dumps(breakdown),
                    json.dumps(deal_data),
                    json.dumps(room.auction_history),
                    json.dumps(play_history),
                    position,
                    user_was_declarer,
                    user_was_dummy,
                ))

            print(f"✅ Room hand saved for {position} (session={session_id[:20]}..., partnership={room.partnership_id})")

        conn.commit()
        conn.close()

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"⚠️ Room hand save failed (non-blocking): {e}")


def register_room_endpoints(app, room_manager: RoomStateManager):
    """
    Register all room-related endpoints with the Flask app

    Args:
        app: Flask application instance
        room_manager: RoomStateManager instance for room state
    """

    # =========================================================================
    # ROOM LIFECYCLE ENDPOINTS
    # =========================================================================

    @app.route('/api/room/create', methods=['POST'])
    def create_room():
        """
        Create a new practice room

        Request JSON:
            {
                "deal_type": "random" | "convention",
                "convention_filter": "Stayman" | null,
                "ai_difficulty": "beginner" | "intermediate" | "advanced" | "expert"
            }

        Response:
            {
                "success": true,
                "room_code": "ABC123",
                "my_position": "S"
            }
        """
        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'No session ID provided'
            }), 400

        data = request.get_json() or {}

        # Parse settings
        settings = RoomSettings(
            deal_type=data.get('deal_type', 'random'),
            convention_filter=data.get('convention_filter'),
            ai_difficulty=data.get('ai_difficulty', 'advanced'),
        )

        # Create room
        room_code = room_manager.create_room(session_id, settings)

        # Store user ID on room for partnership tracking
        user_id = _get_user_id_from_request(request)
        if user_id:
            room = room_manager.get_room(room_code)
            if room:
                room.host_user_id = user_id

        return jsonify({
            'success': True,
            'room_code': room_code,
            'my_position': 'S',  # Host is always South
            'is_host': True,
        })

    @app.route('/api/room/join', methods=['POST'])
    def join_room():
        """
        Join an existing room

        Request JSON:
            {
                "room_code": "ABC123"
            }

        Response:
            {
                "success": true,
                "room_code": "ABC123",
                "my_position": "N"
            }
        """
        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'No session ID provided'
            }), 400

        data = request.get_json() or {}
        room_code = data.get('room_code', '').strip().upper()

        if not room_code:
            return jsonify({
                'success': False,
                'error': 'Room code required'
            }), 400

        success, message = room_manager.join_room(room_code, session_id)

        if success:
            # Store guest user ID and create partnership
            room = room_manager.get_room(room_code)
            guest_user_id = _get_user_id_from_request(request)
            if room and guest_user_id:
                room.guest_user_id = guest_user_id
                # Find or create partnership between host and guest
                if room.host_user_id:
                    room.partnership_id = _find_or_create_partnership(
                        room.host_user_id, guest_user_id
                    )

            # Auto-deal first hand immediately on join (no ready gate for first hand)
            deal_data = {}
            if room:
                try:
                    _deal_next_hand(room)
                    position_full = SEAT_NAMES['N']  # Guest is always North
                    deal_data = {
                        'dealer': room.dealer,
                        'vulnerability': room.vulnerability,
                        'my_hand': room._serialize_hand(room.deal[position_full]),
                        'auction_history': room.auction_history,
                        'current_bidder': room.get_current_bidder(),
                        'is_my_turn': room.is_session_turn(session_id),
                        'game_phase': room.game_phase,
                    }
                except Exception as e:
                    print(f"⚠️ Auto-deal on join failed: {e}")

            return jsonify({
                'success': True,
                'room_code': room_code,
                'my_position': 'N',  # Guest is always North
                'is_host': False,
                'message': message,
                'auto_dealt': bool(deal_data),
                **deal_data,
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400

    @app.route('/api/room/leave', methods=['POST'])
    def leave_room():
        """
        Leave current room

        Response:
            {
                "success": true
            }
        """
        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'No session ID provided'
            }), 400

        success = room_manager.leave_room(session_id)

        return jsonify({
            'success': success,
            'message': 'Left room' if success else 'Not in a room'
        })

    # =========================================================================
    # ROOM STATE ENDPOINTS
    # =========================================================================

    @app.route('/api/room/poll', methods=['GET'])
    def poll_room():
        """
        Poll current room state

        Supports ETag-style caching: if client sends If-None-Match header
        with current version, returns 304 if unchanged.

        Query params:
            version: (optional) Last known version for quick check

        Response:
            {
                "success": true,
                "room": { ... room state ... }
            }
        """
        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'No session ID provided'
            }), 400

        room = room_manager.get_room_by_session(session_id)
        if not room:
            return jsonify({
                'success': False,
                'error': 'Not in a room',
                'in_room': False
            }), 404

        # Record heartbeat (player is still connected)
        room.record_heartbeat(session_id)

        # Check for version match (ETag-style)
        client_version = request.args.get('version', type=int)
        if client_version is not None and client_version == room.version:
            return '', 304  # Not Modified

        # AI bidding is handled in /api/room/bid and _deal_next_hand only.
        # Do NOT trigger auto_bid_for_ai here — concurrent polls from both
        # players would race and produce duplicate AI bids.

        # Build room dict for response
        room_dict = room.to_dict(for_session=session_id)

        # Add beliefs for coaching support during bidding phase
        if room.game_phase == 'bidding' and room.auction_history:
            try:
                position = room.get_position_for_session(session_id)
                position_full = SEAT_NAMES.get(position, position)
                hand = room.deal.get(position_full)

                if hand:
                    # Get user's hand info for beliefs context
                    user_hcp = hand.hcp
                    user_suit_lengths = {
                        '♠': len([c for c in hand.cards if c.suit == '♠']),
                        '♥': len([c for c in hand.cards if c.suit == '♥']),
                        '♦': len([c for c in hand.cards if c.suit == '♦']),
                        '♣': len([c for c in hand.cards if c.suit == '♣']),
                    }

                    # Build bidding state and extract beliefs
                    dealer_full = SEAT_NAMES.get(normalize(room.dealer), room.dealer)
                    bidding_state = BiddingStateBuilder().build(room.auction_history, dealer_full)
                    beliefs = bidding_state.to_dict(position, my_hcp=user_hcp, my_suit_lengths=user_suit_lengths)
                    room_dict['beliefs'] = beliefs
            except Exception as e:
                # Don't fail the poll if beliefs computation fails
                print(f"⚠️ Could not compute beliefs for room {room.room_code}: {e}")

        return jsonify({
            'success': True,
            'in_room': True,
            'room': room_dict
        })

    @app.route('/api/room/status', methods=['GET'])
    def room_status():
        """
        Quick check if session is in a room

        Response:
            {
                "in_room": true,
                "room_code": "ABC123",
                "is_host": true,
                "partner_connected": true
            }
        """
        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({
                'in_room': False
            })

        room = room_manager.get_room_by_session(session_id)
        if not room:
            return jsonify({
                'in_room': False
            })

        return jsonify({
            'in_room': True,
            'room_code': room.room_code,
            'is_host': session_id == room.host_session_id,
            'my_position': room.get_position_for_session(session_id),
            'partner_connected': room.is_full(),
            'game_phase': room.game_phase,
            'version': room.version,
        })

    # =========================================================================
    # ROOM SETTINGS ENDPOINTS
    # =========================================================================

    @app.route('/api/room/settings', methods=['POST'])
    def update_room_settings():
        """
        Update room settings (host only)

        Request JSON:
            {
                "deal_type": "random" | "convention",
                "convention_filter": "Stayman" | null,
                "ai_difficulty": "beginner" | "intermediate" | "advanced" | "expert"
            }

        Response:
            {
                "success": true,
                "settings": { ... }
            }
        """
        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'No session ID provided'
            }), 400

        room = room_manager.get_room_by_session(session_id)
        if not room:
            return jsonify({
                'success': False,
                'error': 'Not in a room'
            }), 404

        data = request.get_json() or {}

        # Update settings
        if 'deal_type' in data:
            room.settings.deal_type = data['deal_type']
        if 'convention_filter' in data:
            room.settings.convention_filter = data['convention_filter']
        if 'ai_difficulty' in data:
            room.settings.ai_difficulty = data['ai_difficulty']

        room.increment_version()

        return jsonify({
            'success': True,
            'settings': {
                'deal_type': room.settings.deal_type,
                'convention_filter': room.settings.convention_filter,
                'ai_difficulty': room.settings.ai_difficulty,
            },
            'version': room.version
        })

    # =========================================================================
    # READINESS ENDPOINTS (Peer Model)
    # =========================================================================

    @app.route('/api/room/ready', methods=['POST'])
    def room_ready():
        """
        Signal readiness for next state transition (mutual readiness gate).

        Either player can signal ready. When both are ready:
        - In 'waiting' or 'complete' phase: auto-deals next hand
        - In 'review' phase: auto-deals next hand

        Request JSON:
            { "ready": true }  (optional, defaults to true)

        Response:
            {
                "success": true,
                "i_am_ready": true,
                "partner_ready": false,
                "both_ready": false,
                "action_taken": null | "deal"
            }
        """
        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({'success': False, 'error': 'No session ID provided'}), 400

        room = room_manager.get_room_by_session(session_id)
        if not room:
            return jsonify({'success': False, 'error': 'Not in a room'}), 404

        if not room.is_full():
            return jsonify({'success': False, 'error': 'Wait for partner to join'}), 400

        data = request.get_json() or {}
        ready = data.get('ready', True)

        room.set_ready(session_id, ready)

        action_taken = None

        # If both ready, trigger the state transition
        if room.are_both_ready():
            if room.game_phase in ('waiting', 'complete'):
                # Auto-deal next hand
                try:
                    _deal_next_hand(room)
                    action_taken = 'deal'
                except Exception as e:
                    return jsonify({'success': False, 'error': f'Deal failed: {str(e)}'}), 500

        response = {
            'success': True,
            'i_am_ready': room.ready_state.get(session_id, False),
            'partner_ready': room.ready_state.get(
                room.guest_session_id if session_id == room.host_session_id else room.host_session_id,
                False
            ),
            'both_ready': room.are_both_ready(),
            'action_taken': action_taken,
            'game_phase': room.game_phase,
            'version': room.version,
        }

        # If a deal happened, include hand data
        if action_taken == 'deal':
            position = room.get_position_for_session(session_id)
            position_full = SEAT_NAMES[position]
            response['dealer'] = room.dealer
            response['vulnerability'] = room.vulnerability
            response['my_hand'] = room._serialize_hand(room.deal[position_full])
            response['auction_history'] = room.auction_history
            response['current_bidder'] = room.get_current_bidder()
            response['is_my_turn'] = room.is_session_turn(session_id)

        return jsonify(response)

    @app.route('/api/room/unready', methods=['POST'])
    def room_unready():
        """Retract readiness signal"""
        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({'success': False, 'error': 'No session ID provided'}), 400

        room = room_manager.get_room_by_session(session_id)
        if not room:
            return jsonify({'success': False, 'error': 'Not in a room'}), 404

        room.set_ready(session_id, False)

        return jsonify({
            'success': True,
            'i_am_ready': False,
            'partner_ready': room.ready_state.get(
                room.guest_session_id if session_id == room.host_session_id else room.host_session_id,
                False
            ),
            'version': room.version,
        })

    def _deal_next_hand(room):
        """Deal next hand (shared logic for ready gate and legacy deal endpoint)"""
        hands = _generate_room_hands(room.settings)

        # Rotate dealer (next player clockwise)
        room.dealer = lho(normalize(room.dealer)) if room.dealer else 'N'

        # Update room state
        room.deal = hands
        room.original_deal = {pos: hand for pos, hand in hands.items()}
        room.auction_history = []
        room.play_state = None
        room.game_phase = 'bidding'
        room.clear_ready()
        room.increment_version()

        # Auto-bid for AI if dealer is E or W
        auto_bid_for_ai(room)

    # =========================================================================
    # CHAT ENDPOINT
    # =========================================================================

    @app.route('/api/room/chat', methods=['POST'])
    def room_chat():
        """
        Send a chat message to the room.

        Request JSON:
            { "text": "Nice bid!" }

        Response:
            { "success": true, "message_id": 5, "version": 12 }
        """
        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({'success': False, 'error': 'No session ID provided'}), 400

        room = room_manager.get_room_by_session(session_id)
        if not room:
            return jsonify({'success': False, 'error': 'Not in a room'}), 404

        data = request.get_json() or {}
        text = data.get('text', '').strip()

        if not text:
            return jsonify({'success': False, 'error': 'Message text required'}), 400

        if len(text) > 500:
            return jsonify({'success': False, 'error': 'Message too long (500 char max)'}), 400

        position = room.get_position_for_session(session_id)
        message = {
            'id': len(room.chat_messages),
            'sender': position,
            'text': text,
            'timestamp': datetime.now().isoformat(),
        }
        room.chat_messages.append(message)
        room.increment_version()

        return jsonify({
            'success': True,
            'message_id': message['id'],
            'version': room.version,
        })

    @app.route('/api/room/chat', methods=['GET'])
    def get_room_chat():
        """Get chat messages, optionally after a given message ID."""
        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({'success': False, 'error': 'No session ID provided'}), 400

        room = room_manager.get_room_by_session(session_id)
        if not room:
            return jsonify({'success': False, 'error': 'Not in a room'}), 404

        after_id = request.args.get('after', type=int, default=-1)
        messages = [m for m in room.chat_messages if m['id'] > after_id]

        return jsonify({
            'success': True,
            'messages': messages,
        })

    # =========================================================================
    # GAME CONTROL ENDPOINTS (legacy — prefer /api/room/ready for peer model)
    # =========================================================================

    @app.route('/api/room/deal', methods=['POST'])
    def room_deal():
        """
        Deal new hands (host only, requires partner to be connected)

        Request JSON:
            {
                "dealer": "N" | "E" | "S" | "W" (optional, default rotates)
            }

        Response:
            {
                "success": true,
                "dealer": "N",
                "vulnerability": "None",
                "my_hand": [...],
                "version": 5
            }
        """
        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'No session ID provided'
            }), 400

        room = room_manager.get_room_by_session(session_id)
        if not room:
            return jsonify({
                'success': False,
                'error': 'Not in a room'
            }), 404

        # Must have partner connected
        if not room.is_full():
            return jsonify({
                'success': False,
                'error': 'Wait for partner to join'
            }), 400

        data = request.get_json() or {}

        # Generate hands based on settings
        try:
            hands = _generate_room_hands(room.settings)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Hand generation failed: {str(e)}'
            }), 500

        # Set dealer (rotate or use provided)
        if 'dealer' in data and data['dealer'] in SEATS:
            room.dealer = data['dealer']
        else:
            # Rotate dealer (next player clockwise)
            room.dealer = lho(normalize(room.dealer)) if room.dealer else 'N'

        # Update room state
        room.deal = hands
        room.original_deal = {pos: hand for pos, hand in hands.items()}  # Deep copy
        room.auction_history = []
        room.play_state = None
        room.game_phase = 'bidding'
        room.increment_version()

        # Auto-bid for AI if dealer is E or W
        ai_bids = auto_bid_for_ai(room)

        # Return response with caller's hand
        position = room.get_position_for_session(session_id)
        position_full = SEAT_NAMES[position]

        return jsonify({
            'success': True,
            'dealer': room.dealer,
            'vulnerability': room.vulnerability,
            'my_hand': room._serialize_hand(room.deal[position_full]),
            'game_phase': room.game_phase,
            'current_bidder': room.get_current_bidder(),
            'is_my_turn': room.is_session_turn(session_id),
            'ai_bids': ai_bids,  # Include any AI bids made
            'auction_history': room.auction_history,
            'version': room.version
        })

    @app.route('/api/room/start', methods=['POST'])
    def start_room_game():
        """
        Start the game (deals hands if not already dealt)

        Same as /api/room/deal but with clearer semantics for UI
        """
        return room_deal()

    # =========================================================================
    # BIDDING ENDPOINTS
    # =========================================================================

    @app.route('/api/room/bid', methods=['POST'])
    def room_bid():
        """
        Submit a bid in room mode

        Request JSON:
            {
                "bid": "1NT" | "Pass" | "X" | "XX" | etc.
            }

        Response:
            {
                "success": true,
                "auction_history": ["1NT", "Pass", ...],
                "current_bidder": "E",
                "is_my_turn": false,
                "version": 6
            }
        """
        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'No session ID provided'
            }), 400

        room = room_manager.get_room_by_session(session_id)
        if not room:
            return jsonify({
                'success': False,
                'error': 'Not in a room'
            }), 404

        # Check game phase
        if room.game_phase != 'bidding':
            return jsonify({
                'success': False,
                'error': f'Cannot bid in {room.game_phase} phase'
            }), 400

        # Check it's this player's turn
        if not room.is_session_turn(session_id):
            return jsonify({
                'success': False,
                'error': 'Not your turn to bid'
            }), 403

        data = request.get_json() or {}
        bid = data.get('bid')

        if not bid:
            return jsonify({
                'success': False,
                'error': 'Bid required'
            }), 400

        # Add bid to auction history
        room.auction_history.append(bid)
        room.increment_version()

        # Evaluate bid using V2 unified feedback system (accumulate for review)
        position = room.get_position_for_session(session_id)
        position_full = SEAT_NAMES.get(position, position)
        dealer_full = SEAT_NAMES.get(normalize(room.dealer), room.dealer)
        hand = room.deal.get(position_full)
        if hand and bid != 'Pass':
            try:
                from engine.v2 import BiddingEngineV2Schema
                eval_engine = BiddingEngineV2Schema()
                # Evaluate against auction BEFORE this bid was added
                auction_before = room.auction_history[:-1]
                v2_fb = eval_engine.evaluate_user_bid(
                    hand=hand,
                    user_bid=bid,
                    auction_history=auction_before,
                    my_position=position_full,
                    vulnerability=room.vulnerability or 'None',
                    dealer=dealer_full
                )
                room.bid_feedback.append({
                    'position': position,
                    'bid': bid,
                    'bid_number': len(room.auction_history),
                    'score': v2_fb.score,
                    'correctness': v2_fb.correctness.value,
                    'optimal_bid': v2_fb.optimal_bid,
                    'optimal_explanation': v2_fb.optimal_explanation,
                    'key_concept': v2_fb.key_concept,
                    'helpful_hint': v2_fb.helpful_hint,
                    'learning_feedback': v2_fb.learning_feedback,
                })
            except Exception:
                pass  # Don't block bidding if evaluation fails

        # Check if auction is complete (3 consecutive passes after opening bid)
        auction_complete = _check_auction_complete(room.auction_history)

        if auction_complete:
            room.game_phase = 'complete'

        # Auto-bid for E/W using the actual bidding engine
        ai_bids = auto_bid_for_ai(room) if not auction_complete else []
        auction_complete = _check_auction_complete(room.auction_history)

        # Save passed-out hands (all passes, no contract — hand is done)
        if auction_complete and all(b == 'Pass' for b in room.auction_history):
            _save_room_hand(room)

        return jsonify({
            'success': True,
            'bid': bid,
            'ai_bids': ai_bids,
            'auction_history': room.auction_history,
            'current_bidder': room.get_current_bidder(),
            'is_my_turn': room.is_session_turn(session_id),
            'game_phase': room.game_phase,
            'auction_complete': auction_complete,
            'version': room.version
        })

    @app.route('/api/room/hint', methods=['POST'])
    def room_hint():
        """
        Get a bid suggestion for the requesting player using the room's deal.
        Uses the room's hand data (not solo session state).
        """
        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({'success': False, 'error': 'No session ID provided'}), 400

        room = room_manager.get_room_by_session(session_id)
        if not room:
            return jsonify({'success': False, 'error': 'Not in a room'}), 404

        if room.game_phase != 'bidding':
            return jsonify({'success': False, 'error': 'Not in bidding phase'}), 400

        if not room.is_session_turn(session_id):
            return jsonify({'success': False, 'error': 'Not your turn'}), 403

        position = room.get_position_for_session(session_id)
        position_full = SEAT_NAMES[position]
        hand = room.deal.get(position_full)

        if not hand:
            return jsonify({'success': False, 'error': 'No hand available'}), 400

        try:
            from engine.v2 import BiddingEngineV2Schema
            hint_engine = BiddingEngineV2Schema()

            dealer_full = SEAT_NAMES.get(normalize(room.dealer), room.dealer)
            bid, explanation = hint_engine.get_next_bid(
                hand=hand,
                auction_history=room.auction_history,
                my_position=position_full,
                vulnerability=room.vulnerability or 'None',
                explanation_level='detailed',
                dealer=dealer_full
            )

            # Normalize explanation
            if hasattr(explanation, 'description'):
                explanation = explanation.description
            elif hasattr(explanation, 'to_dict'):
                explanation = explanation.to_dict()
            elif not isinstance(explanation, str) and explanation is not None:
                explanation = str(explanation)

            return jsonify({
                'success': True,
                'bid': bid or 'Pass',
                'explanation': explanation or '',
            })
        except Exception as e:
            print(f"⚠️ Room hint error: {e}")
            return jsonify({'success': False, 'error': 'Could not generate hint'}), 500

    # =========================================================================
    # PLAY ENDPOINTS
    # =========================================================================

    @app.route('/api/room/start-play', methods=['POST'])
    def room_start_play():
        """
        Start card play phase (either peer)

        Transitions room from bidding complete to playing phase.
        Initializes shared PlayState for synchronized play.

        Response:
            {
                "success": true,
                "contract": "3NT by S",
                "declarer": "S",
                "dummy": "N",
                "opening_leader": "W",
                "play_state": { ... }
            }
        """
        from engine.play_engine import PlayEngine, Contract, PlayState

        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'No session ID provided'
            }), 400

        room = room_manager.get_room_by_session(session_id)
        if not room:
            return jsonify({
                'success': False,
                'error': 'Not in a room'
            }), 404

        # Must be in complete phase (bidding finished)
        if room.game_phase != 'complete':
            return jsonify({
                'success': False,
                'error': f'Cannot start play in {room.game_phase} phase'
            }), 400

        # Determine contract from auction
        dealer_idx = seat_index(normalize(room.dealer))
        contract = PlayEngine.determine_contract(room.auction_history, dealer_idx)

        if not contract:
            return jsonify({
                'success': False,
                'error': 'No valid contract (hand was passed out)'
            }), 400

        # Convert hands to format needed by PlayEngine
        hands = {}
        for pos_full, hand in room.deal.items():
            pos_short = pos_full[0]  # 'North' -> 'N'
            hands[pos_short] = hand

        # Create play state
        play_state = PlayEngine.create_play_session(contract, hands)

        # Determine dummy (partner of declarer)
        dummy = seats_partner(contract.declarer)

        room.play_state = play_state
        room.game_phase = 'playing'
        room.increment_version()

        # NO auto-play for AI — frontend drives AI plays one at a time
        # via /api/room/get-ai-play (matches solo play loop pattern)

        return jsonify({
            'success': True,
            'contract': str(contract),
            'declarer': contract.declarer,
            'dummy': dummy,
            'opening_leader': lho(contract.declarer),
            'next_to_play': room.play_state.next_to_play,
            'is_my_turn': room.is_session_turn(session_id),
            'version': room.version,
            'play_state': room._serialize_play_state(for_session=session_id),
            'game_phase': room.game_phase,
        })

    @app.route('/api/room/play-card', methods=['POST'])
    def room_play_card():
        """
        Play a card in room mode

        Request JSON:
            {
                "card": {"rank": "A", "suit": "♠"}
            }

        Response:
            {
                "success": true,
                "card_played": {"rank": "A", "suit": "♠"},
                "next_to_play": "E",
                "is_my_turn": false,
                "trick_complete": false,
                "trick_winner": null,
                "ai_plays": [...]
            }
        """
        from engine.play_engine import PlayEngine
        from engine.hand import Card

        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'No session ID provided'
            }), 400

        room = room_manager.get_room_by_session(session_id)
        if not room:
            return jsonify({
                'success': False,
                'error': 'Not in a room'
            }), 404

        # Must be in playing phase
        if room.game_phase != 'playing':
            return jsonify({
                'success': False,
                'error': f'Cannot play card in {room.game_phase} phase'
            }), 400

        if not room.play_state:
            return jsonify({
                'success': False,
                'error': 'No play state initialized'
            }), 400

        # Check it's this player's turn
        if not room.is_session_turn(session_id):
            return jsonify({
                'success': False,
                'error': 'Not your turn to play'
            }), 403

        data = request.get_json() or {}
        card_data = data.get('card')

        if not card_data or 'rank' not in card_data or 'suit' not in card_data:
            return jsonify({
                'success': False,
                'error': 'Card with rank and suit required'
            }), 400

        card = Card(rank=card_data['rank'], suit=card_data['suit'])
        player = room.play_state.next_to_play

        # Handle dummy play - declarer controls dummy
        actual_player = player
        declarer = room.play_state.contract.declarer
        dummy = seats_partner(declarer)

        if player == dummy:
            # Dummy's cards are played by declarer
            actual_player = declarer
            # Check if the session is declarer
            session_position = room.get_position_for_session(session_id)
            if session_position != declarer:
                return jsonify({
                    'success': False,
                    'error': 'Only declarer can play dummy\'s cards'
                }), 403

        # Get the hand for the player whose turn it is
        position_full = SEAT_NAMES[player]
        hand = room.play_state.hands[player]

        # Auto-clear stale completed trick if needed (safety net)
        # Normally frontend calls /api/room/clear-trick, but auto-clear prevents stuck state
        if len(room.play_state.current_trick) == 4:
            room.play_state.current_trick = []
            room.play_state.current_trick_leader = room.play_state.next_to_play

        # Validate card is legal
        trump_suit = None if room.play_state.contract.strain == 'NT' else room.play_state.contract.strain
        if not PlayEngine.is_legal_play(card, hand, room.play_state.current_trick, trump_suit):
            return jsonify({
                'success': False,
                'error': 'Illegal card play - must follow suit if able'
            }), 400

        # Play the card
        room.play_state.current_trick.append((card, player))
        hand.cards.remove(card)

        # Reveal dummy after opening lead
        if not room.play_state.dummy_revealed and len(room.play_state.trick_history) == 0:
            if len(room.play_state.current_trick) == 1:
                room.play_state.dummy_revealed = True

        trick_complete = False
        trick_winner = None

        # Check if trick is complete
        if len(room.play_state.current_trick) == 4:
            trick_complete = True
            trick_winner = PlayEngine.determine_trick_winner(
                room.play_state.current_trick,
                trump_suit
            )

            # Update tricks won
            room.play_state.tricks_won[trick_winner] += 1

            # Save trick to history
            from engine.play_engine import Trick
            trick = Trick(
                cards=list(room.play_state.current_trick),
                winner=trick_winner,
                leader=room.play_state.current_trick_leader or player
            )
            room.play_state.trick_history.append(trick)

            # DON'T clear trick yet - let frontend display it with winner
            # Frontend will call /api/room/clear-trick after showing winner
            room.play_state.next_to_play = trick_winner

            # Check if play is complete (13 tricks played)
            if len(room.play_state.trick_history) == 13:
                room.game_phase = 'complete'
                _save_room_hand(room)
        else:
            # Next player
            room.play_state.next_to_play = lho(player)

        room.increment_version()

        # NO auto-play for AI — frontend drives AI plays one at a time
        # via /api/room/get-ai-play (matches solo play loop pattern)

        return jsonify({
            'success': True,
            'card_played': {'rank': card.rank, 'suit': card.suit},
            'player': player,
            'next_to_play': room.play_state.next_to_play if room.game_phase == 'playing' else None,
            'is_my_turn': room.is_session_turn(session_id),
            'trick_complete': trick_complete,
            'trick_winner': trick_winner,
            'tricks_ns': room.play_state.tricks_won['N'] + room.play_state.tricks_won['S'],
            'tricks_ew': room.play_state.tricks_won['E'] + room.play_state.tricks_won['W'],
            'game_phase': room.game_phase,
            'dummy_revealed': room.play_state.dummy_revealed,
            'play_state': room._serialize_play_state(for_session=session_id),
            'version': room.version
        })

    @app.route('/api/room/play-state', methods=['GET'])
    def room_play_state():
        """
        Get current play state for room

        Response includes visible hands based on position and dummy status.
        """
        from engine.play_engine import PlayEngine

        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'No session ID provided'
            }), 400

        room = room_manager.get_room_by_session(session_id)
        if not room:
            return jsonify({
                'success': False,
                'error': 'Not in a room'
            }), 404

        if not room.play_state:
            return jsonify({
                'success': False,
                'error': 'No play state'
            }), 400

        # Use _serialize_play_state for consistent format with poll and play-card responses
        play_state = room._serialize_play_state(for_session=session_id)

        return jsonify({
            'success': True,
            'game_phase': room.game_phase,
            'version': room.version,
            **play_state
        })

    @app.route('/api/room/get-ai-play', methods=['POST'])
    def room_get_ai_play():
        """
        AI plays ONE card for an E/W position (matches solo /api/get-ai-play pattern).

        Frontend calls this in a loop with delays for visible card animation.
        Only plays if current next_to_play is E or W.

        Response:
            {
                "success": true,
                "card": {"rank": "A", "suit": "♠"},
                "position": "E",
                "trick_complete": false,
                "trick_winner": null,
                "next_to_play": "S",
                "tricks_won": {...},
                "dummy_revealed": true
            }
        """
        from engine.play_engine import PlayEngine
        from engine.play.ai.simple_ai import SimplePlayAI

        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({'success': False, 'error': 'No session ID provided'}), 400

        room = room_manager.get_room_by_session(session_id)
        if not room:
            return jsonify({'success': False, 'error': 'Not in a room'}), 404

        if room.game_phase != 'playing' or not room.play_state:
            return jsonify({'success': False, 'error': 'Not in playing phase'}), 400

        current_player = room.play_state.next_to_play

        # Only AI plays E/W
        if current_player not in ('E', 'W'):
            return jsonify({
                'success': False,
                'error': f'Not AI turn (next_to_play={current_player})',
                'next_to_play': current_player,
                'is_my_turn': room.is_session_turn(session_id),
            }), 403

        try:
            # Auto-clear stale completed trick if needed (safety net)
            if len(room.play_state.current_trick) == 4:
                room.play_state.current_trick = []
                room.play_state.current_trick_leader = room.play_state.next_to_play

            ai = SimplePlayAI()
            trump_suit = None if room.play_state.contract.strain == 'NT' else room.play_state.contract.strain

            card = ai.choose_card(room.play_state, current_player)
            hand = room.play_state.hands[current_player]

            # Play the card
            room.play_state.current_trick.append((card, current_player))
            hand.cards.remove(card)

            # Reveal dummy after opening lead
            if not room.play_state.dummy_revealed and len(room.play_state.trick_history) == 0:
                if len(room.play_state.current_trick) == 1:
                    room.play_state.dummy_revealed = True

            # Check if trick complete
            trick_complete = len(room.play_state.current_trick) == 4
            trick_winner = None

            if trick_complete:
                trick_winner = PlayEngine.determine_trick_winner(
                    room.play_state.current_trick,
                    trump_suit
                )
                room.play_state.tricks_won[trick_winner] += 1

                from engine.play_engine import Trick
                trick = Trick(
                    cards=list(room.play_state.current_trick),
                    winner=trick_winner,
                    leader=room.play_state.current_trick_leader or current_player
                )
                room.play_state.trick_history.append(trick)

                # DON'T clear trick - let frontend display it
                # Frontend will call /api/room/clear-trick after showing winner
                room.play_state.next_to_play = trick_winner

                if len(room.play_state.trick_history) == 13:
                    room.game_phase = 'complete'
                    _save_room_hand(room)
            else:
                room.play_state.next_to_play = lho(current_player)

            room.increment_version()

            return jsonify({
                'success': True,
                'card': {'rank': card.rank, 'suit': card.suit},
                'position': current_player,
                'trick_complete': trick_complete,
                'trick_winner': trick_winner,
                'next_to_play': room.play_state.next_to_play,
                'tricks_won': dict(room.play_state.tricks_won),
                'dummy_revealed': room.play_state.dummy_revealed,
                'game_phase': room.game_phase,
                'explanation': f"{current_player} played {card.rank}{card.suit}",
                'version': room.version
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': f'AI play error: {str(e)}'
            }), 500

    @app.route('/api/room/clear-trick', methods=['POST'])
    def room_clear_trick():
        """
        Clear completed trick after frontend has displayed it.
        Matches solo /api/clear-trick pattern.
        """
        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({'success': False, 'error': 'No session ID provided'}), 400

        room = room_manager.get_room_by_session(session_id)
        if not room:
            return jsonify({'success': False, 'error': 'Not in a room'}), 404

        if not room.play_state:
            return jsonify({'success': False, 'error': 'No play state'}), 400

        trick_size = len(room.play_state.current_trick)
        if trick_size > 0 and trick_size < 4:
            return jsonify({
                'success': False,
                'error': f'Cannot clear incomplete trick ({trick_size}/4 cards played)',
            }), 400

        # Clear the current trick
        room.play_state.current_trick = []
        room.play_state.current_trick_leader = room.play_state.next_to_play  # Winner leads next

        room.increment_version()

        return jsonify({
            'success': True,
            'message': 'Trick cleared',
            'next_to_play': room.play_state.next_to_play,
            'game_phase': room.game_phase,
            'version': room.version
        })

    # =========================================================================
    # HELPER FUNCTIONS
    # =========================================================================


def _auto_play_for_ai(room: RoomState) -> list:
    """
    Auto-play for E/W AI positions until a human's turn

    Returns:
        List of AI plays made: [{'player': 'E', 'card': {...}}, ...]
    """
    from engine.play_engine import PlayEngine
    from engine.play.ai.simple_ai import SimplePlayAI

    ai_plays = []

    while room.game_phase == 'playing' and room.play_state:
        current_player = room.play_state.next_to_play

        if current_player not in ('E', 'W'):
            # Human's turn - stop
            break

        # Get AI card selection
        try:
            ai = SimplePlayAI()
            trump_suit = None if room.play_state.contract.strain == 'NT' else room.play_state.contract.strain

            # Use choose_card which handles legal card filtering internally
            card = ai.choose_card(room.play_state, current_player)

            hand = room.play_state.hands[current_player]

            # Play the card
            room.play_state.current_trick.append((card, current_player))
            hand.cards.remove(card)
            ai_plays.append({'player': current_player, 'card': {'rank': card.rank, 'suit': card.suit}})

            # Reveal dummy after opening lead
            if not room.play_state.dummy_revealed and len(room.play_state.trick_history) == 0:
                if len(room.play_state.current_trick) == 1:
                    room.play_state.dummy_revealed = True

            # Check if trick complete
            if len(room.play_state.current_trick) == 4:
                trick_winner = PlayEngine.determine_trick_winner(
                    room.play_state.current_trick,
                    trump_suit
                )
                room.play_state.tricks_won[trick_winner] += 1

                from engine.play_engine import Trick
                trick = Trick(
                    cards=list(room.play_state.current_trick),
                    winner=trick_winner,
                    leader=room.play_state.current_trick_leader or current_player
                )
                room.play_state.trick_history.append(trick)

                room.play_state.current_trick = []
                room.play_state.next_to_play = trick_winner
                room.play_state.current_trick_leader = trick_winner

                if len(room.play_state.trick_history) == 13:
                    room.game_phase = 'complete'
                    break
            else:
                room.play_state.next_to_play = lho(current_player)

            room.increment_version()

        except Exception as e:
            import traceback
            print(f"⚠️ AI play error for {current_player}: {e}")
            traceback.print_exc()
            break

    return ai_plays


def _check_auction_complete(auction_history: list) -> bool:
    """
    Check if auction is complete (3 consecutive passes after opening bid,
    or 4 passes with no bids)
    """
    if len(auction_history) < 4:
        return False

    # All passes (passed out)
    if all(b == 'Pass' for b in auction_history):
        return len(auction_history) >= 4

    # Check for 3 consecutive passes after at least one non-pass bid
    non_pass_bids = [b for b in auction_history if b != 'Pass']
    if non_pass_bids and len(auction_history) >= 4:
        return auction_history[-3:] == ['Pass', 'Pass', 'Pass']

    return False


def _generate_room_hands(settings: RoomSettings) -> dict:
    """
    Generate 4 hands based on room settings

    Args:
        settings: RoomSettings with deal_type and convention_filter

    Returns:
        Dict mapping position names to Hand objects
    """
    # Create a fresh deck
    ranks = '23456789TJQKA'
    suits = ['♠', '♥', '♦', '♣']
    deck = [Card(rank=r, suit=s) for s in suits for r in ranks]
    random.shuffle(deck)

    if settings.deal_type == 'convention' and settings.convention_filter:
        # Generate convention-specific hands
        convention_map = get_convention_map()
        specialist = convention_map.get(settings.convention_filter)

        if specialist:
            # Generate South hand for convention (human partner plays South)
            try:
                south_hand, remaining = generate_hand_for_convention(specialist, deck, timeout_ms=500)
                if south_hand:
                    deck = remaining
                else:
                    # Fallback to random
                    south_hand = Hand(deck[:13])
                    deck = deck[13:]
            except Exception:
                south_hand = Hand(deck[:13])
                deck = deck[13:]
        else:
            south_hand = Hand(deck[:13])
            deck = deck[13:]

        # Deal remaining positions
        north_hand = Hand(deck[:13])
        east_hand = Hand(deck[13:26])
        west_hand = Hand(deck[26:39])
    else:
        # Random deal
        south_hand = Hand(deck[:13])
        north_hand = Hand(deck[13:26])
        east_hand = Hand(deck[26:39])
        west_hand = Hand(deck[39:52])

    return {
        'North': north_hand,
        'East': east_hand,
        'South': south_hand,
        'West': west_hand,
    }

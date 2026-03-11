"""
Room API - Endpoints for Team Practice Lobby

Provides room creation, joining, polling, and game management for
two human partners playing against AI opponents.

All state mutations use Redis WATCH/MULTI via RoomStateManager.mutate_room*()
to prevent race conditions across Gunicorn workers.

To add to server.py:
    from routes.room_api import register_room_endpoints
    register_room_endpoints(app, room_manager)
"""

import json
import random
from flask import request, jsonify
from datetime import datetime
from typing import Optional

from core.room_state import (
    RoomStateManager, RoomSettings, RoomState, RoomConflictError
)
from core.session_state import get_session_id_from_request
from engine.hand import Hand, Card
from engine.hand_constructor import generate_hand_for_convention, generate_hand_with_constraints
from utils.dealing import deal_four_hands, deal_remaining_hands, shuffled_deck
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
        from engine.v2 import BiddingEngineV2Schema
        engine = BiddingEngineV2Schema()

        position_full = SEAT_NAMES[position]
        hand = room.deal.get(position_full)

        if not hand:
            return 'Pass'

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
            break

        ai_bid = get_ai_bid_for_room(room, current_bidder)
        room.auction_history.append(ai_bid)
        ai_bids.append({'position': current_bidder, 'bid': ai_bid})
        room.increment_version()

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


def _resolve_user_id(session_id: str) -> Optional[str]:
    """
    Resolve user_id from session_id using the server-side auth store.

    Returns None if the session has no authenticated user (anonymous play).
    Never trusts client-supplied user_id headers or body fields.
    """
    try:
        from engine.auth.simple_auth_api import active_sessions
        # The auth token may differ from the X-Session-ID header.
        # Check if the session_id itself is registered as an auth token.
        session_data = active_sessions.get(session_id)
        if session_data:
            return session_data.get('user_id')
    except ImportError:
        pass
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

        a, b = (user_a, user_b) if user_a < user_b else (user_b, user_a)

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

        contract = room.play_state.contract if room.play_state else None
        ps = room.play_state

        passed_out = contract is None

        hand_score = 0
        tricks_taken = 0
        made = False
        breakdown = {}

        if not passed_out and ps:
            tricks_taken = ps.tricks_won.get(contract.declarer, 0) + ps.tricks_won.get(
                seats_partner(contract.declarer), 0
            )
            tricks_needed = contract.level + 6
            made = tricks_taken >= tricks_needed

            try:
                from engine.play_engine import PlayEngine
                score_result = PlayEngine.calculate_score(
                    contract, tricks_taken, room.vulnerability
                )
                hand_score = score_result.get('score', 0)
                breakdown = score_result
            except Exception as e:
                print(f"⚠️ Score calculation failed: {e}")

        deal_data = {}
        for pos_name, hand in room.deal.items():
            if hand:
                try:
                    deal_data[pos_name] = [{'rank': c.rank, 'suit': c.suit} for c in hand.cards]
                except AttributeError:
                    deal_data[pos_name] = hand if isinstance(hand, list) else []

        play_history = []
        if ps and ps.trick_history:
            for trick in ps.trick_history:
                play_history.append({
                    'cards': [{'rank': c.rank, 'suit': c.suit, 'position': p} for c, p in trick.cards],
                    'winner': trick.winner,
                    'leader': getattr(trick, 'leader', None),
                })

        players = [
            (room.host_session_id, room.host_user_id, 'S'),
            (room.guest_session_id, room.guest_user_id, 'N'),
        ]

        for session_id, user_id, position in players:
            if not session_id:
                continue

            declarer = contract.declarer if contract else None
            dummy = seats_partner(declarer) if declarer else None
            user_was_declarer = (position == declarer)
            user_was_dummy = (position == dummy)

            cursor.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'session_hands' AND column_name = 'partnership_id'"
            )
            has_partnership_col = cursor.fetchone() is not None

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
                    session_id, 1, room.dealer, room.vulnerability,
                    contract.level if contract else None,
                    contract.strain if contract else None,
                    declarer, contract.doubled if contract else 0,
                    tricks_taken,
                    (contract.level + 6) if contract else None,
                    made, hand_score, json.dumps(breakdown),
                    json.dumps(deal_data), json.dumps(room.auction_history),
                    json.dumps(play_history),
                    position, user_was_declarer, user_was_dummy,
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
                    session_id, 1, room.dealer, room.vulnerability,
                    contract.level if contract else None,
                    contract.strain if contract else None,
                    declarer, contract.doubled if contract else 0,
                    tricks_taken,
                    (contract.level + 6) if contract else None,
                    made, hand_score, json.dumps(breakdown),
                    json.dumps(deal_data), json.dumps(room.auction_history),
                    json.dumps(play_history),
                    position, user_was_declarer, user_was_dummy,
                ))

            print(f"✅ Room hand saved for {position} (session={session_id[:20]}..., partnership={room.partnership_id})")

        conn.commit()
        conn.close()

    except Exception as e:
        from utils.error_logger import log_error
        log_error(e, endpoint='room/save-hand', context={'room_code': room.room_code})


def register_room_endpoints(app, room_manager: RoomStateManager):
    """
    Register all room-related endpoints with the Flask app

    Args:
        app: Flask application instance
        room_manager: RoomStateManager instance for room state
    """

    def _conflict_response():
        """Standard 409 response for OCC failures"""
        return jsonify({
            'success': False,
            'error': 'Room was modified concurrently, please retry'
        }), 409

    # =========================================================================
    # ROOM LIFECYCLE ENDPOINTS
    # =========================================================================

    @app.route('/api/room/create', methods=['POST'])
    def create_room():
        """Create a new practice room"""
        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'No session ID provided'
            }), 400

        data = request.get_json() or {}

        settings = RoomSettings(
            deal_type=data.get('deal_type', 'random'),
            convention_filter=data.get('convention_filter'),
            ai_difficulty=data.get('ai_difficulty', 'advanced'),
        )

        room_code = room_manager.create_room(session_id, settings)

        # Store server-validated user ID for partnership tracking
        user_id = _resolve_user_id(session_id)
        if user_id:
            try:
                with room_manager.mutate_room(room_code) as room:
                    room.host_user_id = user_id
            except (KeyError, RoomConflictError):
                pass  # Non-critical — partnership tracking is optional

        return jsonify({
            'success': True,
            'room_code': room_code,
            'my_position': 'S',
            'is_host': True,
        })

    @app.route('/api/room/join', methods=['POST'])
    def join_room():
        """Join an existing room"""
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
            # Store server-validated guest user ID and create partnership
            guest_user_id = _resolve_user_id(session_id)
            deal_data = {}

            try:
                with room_manager.mutate_room(room_code) as room:
                    if guest_user_id:
                        room.guest_user_id = guest_user_id
                        if room.host_user_id:
                            room.partnership_id = _find_or_create_partnership(
                                room.host_user_id, guest_user_id
                            )

                    # Auto-deal first hand immediately on join
                    _deal_next_hand(room)
                    position_full = SEAT_NAMES['N']
                    deal_data = {
                        'dealer': room.dealer,
                        'vulnerability': room.vulnerability,
                        'my_hand': room._serialize_hand(room.deal[position_full]),
                        'auction_history': room.auction_history,
                        'current_bidder': room.get_current_bidder(),
                        'is_my_turn': room.is_session_turn(session_id),
                        'game_phase': room.game_phase,
                    }
            except (KeyError, RoomConflictError) as e:
                print(f"⚠️ Auto-deal on join failed: {e}")

            return jsonify({
                'success': True,
                'room_code': room_code,
                'my_position': 'N',
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
        """Leave current room"""
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
    # ROOM STATE ENDPOINTS (read-only — no OCC needed)
    # =========================================================================

    @app.route('/api/room/poll', methods=['GET'])
    def poll_room():
        """Poll current room state (long-poll with version check)"""
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

        # Record heartbeat (mutation — needs OCC)
        try:
            with room_manager.mutate_room(room.room_code) as mutable_room:
                mutable_room.record_heartbeat(session_id)
        except (KeyError, RoomConflictError):
            pass  # Non-critical — heartbeat can be missed occasionally

        # Version check (use the snapshot we already read)
        client_version = request.args.get('version', type=int)
        if client_version is not None and client_version == room.version:
            return '', 304

        room_dict = room.to_dict(for_session=session_id)

        # Add beliefs for coaching support during bidding phase
        if room.game_phase == 'bidding' and room.auction_history:
            try:
                position = room.get_position_for_session(session_id)
                position_full = SEAT_NAMES.get(position, position)
                hand = room.deal.get(position_full)

                if hand:
                    user_hcp = hand.hcp
                    user_suit_lengths = {
                        '♠': len([c for c in hand.cards if c.suit == '♠']),
                        '♥': len([c for c in hand.cards if c.suit == '♥']),
                        '♦': len([c for c in hand.cards if c.suit == '♦']),
                        '♣': len([c for c in hand.cards if c.suit == '♣']),
                    }

                    dealer_full = SEAT_NAMES.get(normalize(room.dealer), room.dealer)
                    bidding_state = BiddingStateBuilder().build(room.auction_history, dealer_full)
                    beliefs = bidding_state.to_dict(position, my_hcp=user_hcp, my_suit_lengths=user_suit_lengths)
                    room_dict['beliefs'] = beliefs
            except Exception as e:
                print(f"⚠️ Could not compute beliefs for room {room.room_code}: {e}")

        return jsonify({
            'success': True,
            'in_room': True,
            'room': room_dict
        })

    @app.route('/api/room/status', methods=['GET'])
    def room_status():
        """Quick check if session is in a room"""
        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({'in_room': False})

        room = room_manager.get_room_by_session(session_id)
        if not room:
            return jsonify({'in_room': False})

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
        """Update room settings (either peer)"""
        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'No session ID provided'
            }), 400

        data = request.get_json() or {}

        try:
            with room_manager.mutate_room_by_session(session_id) as room:
                if 'deal_type' in data:
                    room.settings.deal_type = data['deal_type']
                if 'convention_filter' in data:
                    room.settings.convention_filter = data['convention_filter']
                if 'ai_difficulty' in data:
                    room.settings.ai_difficulty = data['ai_difficulty']
                room.increment_version()

                response_data = {
                    'success': True,
                    'settings': room.settings.to_dict(),
                    'version': room.version
                }
        except KeyError:
            return jsonify({'success': False, 'error': 'Not in a room'}), 404
        except RoomConflictError:
            return _conflict_response()

        return jsonify(response_data)

    # =========================================================================
    # READINESS ENDPOINTS (Peer Model)
    # =========================================================================

    @app.route('/api/room/ready', methods=['POST'])
    def room_ready():
        """Signal readiness for next state transition (mutual readiness gate)."""
        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({'success': False, 'error': 'No session ID provided'}), 400

        data = request.get_json() or {}
        ready = data.get('ready', True)

        try:
            with room_manager.mutate_room_by_session(session_id) as room:
                if not room.is_full():
                    # Can't use return inside context manager for error —
                    # raise to exit, then handle outside
                    raise ValueError('Wait for partner to join')

                room.set_ready(session_id, ready)

                action_taken = None

                if room.are_both_ready():
                    if room.game_phase in ('waiting', 'complete'):
                        _deal_next_hand(room)
                        action_taken = 'deal'

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

                if action_taken == 'deal':
                    position = room.get_position_for_session(session_id)
                    position_full = SEAT_NAMES[position]
                    response['dealer'] = room.dealer
                    response['vulnerability'] = room.vulnerability
                    response['my_hand'] = room._serialize_hand(room.deal[position_full])
                    response['auction_history'] = room.auction_history
                    response['current_bidder'] = room.get_current_bidder()
                    response['is_my_turn'] = room.is_session_turn(session_id)

        except KeyError:
            return jsonify({'success': False, 'error': 'Not in a room'}), 404
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        except RoomConflictError:
            return _conflict_response()

        return jsonify(response)

    @app.route('/api/room/unready', methods=['POST'])
    def room_unready():
        """Retract readiness signal"""
        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({'success': False, 'error': 'No session ID provided'}), 400

        try:
            with room_manager.mutate_room_by_session(session_id) as room:
                room.set_ready(session_id, False)
                response_data = {
                    'success': True,
                    'i_am_ready': False,
                    'partner_ready': room.ready_state.get(
                        room.guest_session_id if session_id == room.host_session_id else room.host_session_id,
                        False
                    ),
                    'version': room.version,
                }
        except KeyError:
            return jsonify({'success': False, 'error': 'Not in a room'}), 404
        except RoomConflictError:
            return _conflict_response()

        return jsonify(response_data)

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
        """Send a chat message to the room."""
        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({'success': False, 'error': 'No session ID provided'}), 400

        data = request.get_json() or {}
        text = data.get('text', '').strip()

        if not text:
            return jsonify({'success': False, 'error': 'Message text required'}), 400

        if len(text) > 500:
            return jsonify({'success': False, 'error': 'Message too long (500 char max)'}), 400

        try:
            with room_manager.mutate_room_by_session(session_id) as room:
                position = room.get_position_for_session(session_id)
                message = {
                    'id': len(room.chat_messages),
                    'sender': position,
                    'text': text,
                    'timestamp': datetime.now().isoformat(),
                }
                room.chat_messages.append(message)
                room.increment_version()

                response_data = {
                    'success': True,
                    'message_id': message['id'],
                    'version': room.version,
                }
        except KeyError:
            return jsonify({'success': False, 'error': 'Not in a room'}), 404
        except RoomConflictError:
            return _conflict_response()

        return jsonify(response_data)

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
        """Deal new hands (requires partner to be connected)"""
        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'No session ID provided'
            }), 400

        data = request.get_json() or {}

        try:
            with room_manager.mutate_room_by_session(session_id) as room:
                if not room.is_full():
                    raise ValueError('Wait for partner to join')

                # Generate hands based on settings
                hands = _generate_room_hands(room.settings)

                # Set dealer (rotate or use provided)
                if 'dealer' in data and data['dealer'] in SEATS:
                    room.dealer = data['dealer']
                else:
                    room.dealer = lho(normalize(room.dealer)) if room.dealer else 'N'

                room.deal = hands
                room.original_deal = {pos: hand for pos, hand in hands.items()}
                room.auction_history = []
                room.play_state = None
                room.game_phase = 'bidding'
                room.increment_version()

                ai_bids = auto_bid_for_ai(room)

                position = room.get_position_for_session(session_id)
                position_full = SEAT_NAMES[position]

                response_data = {
                    'success': True,
                    'dealer': room.dealer,
                    'vulnerability': room.vulnerability,
                    'my_hand': room._serialize_hand(room.deal[position_full]),
                    'game_phase': room.game_phase,
                    'current_bidder': room.get_current_bidder(),
                    'is_my_turn': room.is_session_turn(session_id),
                    'ai_bids': ai_bids,
                    'auction_history': room.auction_history,
                    'version': room.version
                }

        except KeyError:
            return jsonify({'success': False, 'error': 'Not in a room'}), 404
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        except RoomConflictError:
            return _conflict_response()

        return jsonify(response_data)

    @app.route('/api/room/start', methods=['POST'])
    def start_room_game():
        """Start the game (deals hands if not already dealt)"""
        return room_deal()

    # =========================================================================
    # BIDDING ENDPOINTS
    # =========================================================================

    @app.route('/api/room/bid', methods=['POST'])
    def room_bid():
        """Submit a bid in room mode"""
        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'No session ID provided'
            }), 400

        data = request.get_json() or {}
        bid = data.get('bid')

        if not bid:
            return jsonify({
                'success': False,
                'error': 'Bid required'
            }), 400

        try:
            with room_manager.mutate_room_by_session(session_id) as room:
                if room.game_phase != 'bidding':
                    raise ValueError(f'Cannot bid in {room.game_phase} phase')

                if not room.is_session_turn(session_id):
                    raise PermissionError('Not your turn to bid')

                # Add bid to auction history
                room.auction_history.append(bid)
                room.increment_version()

                # Evaluate bid using V2 unified feedback system
                position = room.get_position_for_session(session_id)
                position_full = SEAT_NAMES.get(position, position)
                dealer_full = SEAT_NAMES.get(normalize(room.dealer), room.dealer)
                hand = room.deal.get(position_full)
                if hand and bid != 'Pass':
                    try:
                        from engine.v2 import BiddingEngineV2Schema
                        eval_engine = BiddingEngineV2Schema()
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

                # Check if auction is complete
                auction_complete = _check_auction_complete(room.auction_history)

                if auction_complete:
                    room.game_phase = 'complete'

                ai_bids = auto_bid_for_ai(room) if not auction_complete else []
                auction_complete = _check_auction_complete(room.auction_history)

                # Save passed-out hands
                if auction_complete and all(b == 'Pass' for b in room.auction_history):
                    _save_room_hand(room)

                # Include latest feedback for real-time display
                latest_feedback = None
                if room.bid_feedback:
                    for fb in reversed(room.bid_feedback):
                        if fb.get('position') == position:
                            latest_feedback = fb
                            break

                response_data = {
                    'success': True,
                    'bid': bid,
                    'ai_bids': ai_bids,
                    'auction_history': room.auction_history,
                    'current_bidder': room.get_current_bidder(),
                    'is_my_turn': room.is_session_turn(session_id),
                    'game_phase': room.game_phase,
                    'auction_complete': auction_complete,
                    'version': room.version,
                    'bid_feedback': latest_feedback,
                }

        except KeyError:
            return jsonify({'success': False, 'error': 'Not in a room'}), 404
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        except PermissionError as e:
            return jsonify({'success': False, 'error': str(e)}), 403
        except RoomConflictError:
            return _conflict_response()

        return jsonify(response_data)

    @app.route('/api/room/hint', methods=['POST'])
    def room_hint():
        """Get a bid suggestion for the requesting player."""
        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({'success': False, 'error': 'No session ID provided'}), 400

        # Read-only — no mutation needed
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
        """Start card play phase (either peer)"""
        from engine.play_engine import PlayEngine, Contract, PlayState

        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'No session ID provided'
            }), 400

        try:
            with room_manager.mutate_room_by_session(session_id) as room:
                if room.game_phase != 'complete':
                    raise ValueError(f'Cannot start play in {room.game_phase} phase')

                dealer_idx = seat_index(normalize(room.dealer))
                contract = PlayEngine.determine_contract(room.auction_history, dealer_idx)

                if not contract:
                    raise ValueError('No valid contract (hand was passed out)')

                hands = {}
                for pos_full, hand in room.deal.items():
                    pos_short = pos_full[0]
                    hands[pos_short] = hand

                play_state = PlayEngine.create_play_session(contract, hands)
                dummy = seats_partner(contract.declarer)

                room.play_state = play_state
                room.game_phase = 'playing'
                room.increment_version()

                response_data = {
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
                }

        except KeyError:
            return jsonify({'success': False, 'error': 'Not in a room'}), 404
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        except RoomConflictError:
            return _conflict_response()

        return jsonify(response_data)

    @app.route('/api/room/play-card', methods=['POST'])
    def room_play_card():
        """Play a card in room mode"""
        from engine.play_engine import PlayEngine
        from engine.hand import Card

        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'No session ID provided'
            }), 400

        data = request.get_json() or {}
        card_data = data.get('card')

        if not card_data or 'rank' not in card_data or 'suit' not in card_data:
            return jsonify({
                'success': False,
                'error': 'Card with rank and suit required'
            }), 400

        try:
            with room_manager.mutate_room_by_session(session_id) as room:
                if room.game_phase != 'playing':
                    raise ValueError(f'Cannot play card in {room.game_phase} phase')

                if not room.play_state:
                    raise ValueError('No play state initialized')

                if not room.is_session_turn(session_id):
                    raise PermissionError('Not your turn to play')

                card = Card(rank=card_data['rank'], suit=card_data['suit'])
                player = room.play_state.next_to_play

                declarer = room.play_state.contract.declarer
                dummy = seats_partner(declarer)

                if player == dummy:
                    session_position = room.get_position_for_session(session_id)
                    if session_position != declarer:
                        raise PermissionError("Only declarer can play dummy's cards")

                hand = room.play_state.hands[player]

                # Auto-clear stale completed trick if needed
                if len(room.play_state.current_trick) == 4:
                    room.play_state.current_trick = []
                    room.play_state.current_trick_leader = room.play_state.next_to_play

                # Validate card is legal
                trump_suit = None if room.play_state.contract.strain == 'NT' else room.play_state.contract.strain
                if not PlayEngine.is_legal_play(card, hand, room.play_state.current_trick, trump_suit):
                    raise ValueError('Illegal card play - must follow suit if able')

                # Play the card
                room.play_state.current_trick.append((card, player))
                hand.cards.remove(card)

                # Reveal dummy after opening lead
                if not room.play_state.dummy_revealed and len(room.play_state.trick_history) == 0:
                    if len(room.play_state.current_trick) == 1:
                        room.play_state.dummy_revealed = True

                trick_complete = False
                trick_winner = None

                if len(room.play_state.current_trick) == 4:
                    trick_complete = True
                    trick_winner = PlayEngine.determine_trick_winner(
                        room.play_state.current_trick,
                        trump_suit
                    )

                    room.play_state.tricks_won[trick_winner] += 1

                    from engine.play_engine import Trick
                    trick = Trick(
                        cards=list(room.play_state.current_trick),
                        winner=trick_winner,
                        leader=room.play_state.current_trick_leader or player
                    )
                    room.play_state.trick_history.append(trick)
                    room.play_state.next_to_play = trick_winner

                    if len(room.play_state.trick_history) == 13:
                        room.game_phase = 'complete'
                        _save_room_hand(room)
                else:
                    room.play_state.next_to_play = lho(player)

                room.increment_version()

                response_data = {
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
                }

        except KeyError:
            return jsonify({'success': False, 'error': 'Not in a room'}), 404
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        except PermissionError as e:
            return jsonify({'success': False, 'error': str(e)}), 403
        except RoomConflictError:
            return _conflict_response()

        return jsonify(response_data)

    @app.route('/api/room/play-state', methods=['GET'])
    def room_play_state():
        """Get current play state for room (read-only)"""
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

        play_state = room._serialize_play_state(for_session=session_id)

        return jsonify({
            'success': True,
            'game_phase': room.game_phase,
            'version': room.version,
            **play_state
        })

    @app.route('/api/room/get-ai-play', methods=['POST'])
    def room_get_ai_play():
        """AI plays ONE card for an E/W position"""
        from engine.play_engine import PlayEngine
        from engine.play.ai.simple_ai import SimplePlayAI

        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({'success': False, 'error': 'No session ID provided'}), 400

        try:
            with room_manager.mutate_room_by_session(session_id) as room:
                if room.game_phase != 'playing' or not room.play_state:
                    raise ValueError('Not in playing phase')

                current_player = room.play_state.next_to_play

                if current_player not in ('E', 'W'):
                    return jsonify({
                        'success': False,
                        'error': f'Not AI turn (next_to_play={current_player})',
                        'next_to_play': current_player,
                        'is_my_turn': room.is_session_turn(session_id),
                    }), 403

                # Auto-clear stale completed trick
                if len(room.play_state.current_trick) == 4:
                    room.play_state.current_trick = []
                    room.play_state.current_trick_leader = room.play_state.next_to_play

                ai = SimplePlayAI()
                trump_suit = None if room.play_state.contract.strain == 'NT' else room.play_state.contract.strain

                card = ai.choose_card(room.play_state, current_player)
                hand = room.play_state.hands[current_player]

                room.play_state.current_trick.append((card, current_player))
                hand.cards.remove(card)

                if not room.play_state.dummy_revealed and len(room.play_state.trick_history) == 0:
                    if len(room.play_state.current_trick) == 1:
                        room.play_state.dummy_revealed = True

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
                    room.play_state.next_to_play = trick_winner

                    if len(room.play_state.trick_history) == 13:
                        room.game_phase = 'complete'
                        _save_room_hand(room)
                else:
                    room.play_state.next_to_play = lho(current_player)

                room.increment_version()

                response_data = {
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
                }

        except KeyError:
            return jsonify({'success': False, 'error': 'Not in a room'}), 404
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        except RoomConflictError:
            return _conflict_response()
        except Exception as e:
            from utils.error_logger import log_error
            log_error(e, endpoint='room/get-ai-play')
            return jsonify({
                'success': False,
                'error': f'AI play error: {str(e)}'
            }), 500

        return jsonify(response_data)

    @app.route('/api/room/clear-trick', methods=['POST'])
    def room_clear_trick():
        """Clear completed trick after frontend has displayed it."""
        session_id = get_session_id_from_request(request)
        if not session_id:
            return jsonify({'success': False, 'error': 'No session ID provided'}), 400

        try:
            with room_manager.mutate_room_by_session(session_id) as room:
                if not room.play_state:
                    raise ValueError('No play state')

                trick_size = len(room.play_state.current_trick)
                if 0 < trick_size < 4:
                    raise ValueError(f'Cannot clear incomplete trick ({trick_size}/4 cards played)')

                room.play_state.current_trick = []
                room.play_state.current_trick_leader = room.play_state.next_to_play
                room.increment_version()

                response_data = {
                    'success': True,
                    'message': 'Trick cleared',
                    'next_to_play': room.play_state.next_to_play,
                    'game_phase': room.game_phase,
                    'version': room.version
                }
        except KeyError:
            return jsonify({'success': False, 'error': 'Not in a room'}), 404
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        except RoomConflictError:
            return _conflict_response()

        return jsonify(response_data)

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
            break

        try:
            ai = SimplePlayAI()
            trump_suit = None if room.play_state.contract.strain == 'NT' else room.play_state.contract.strain

            card = ai.choose_card(room.play_state, current_player)

            hand = room.play_state.hands[current_player]

            room.play_state.current_trick.append((card, current_player))
            hand.cards.remove(card)
            ai_plays.append({'player': current_player, 'card': {'rank': card.rank, 'suit': card.suit}})

            if not room.play_state.dummy_revealed and len(room.play_state.trick_history) == 0:
                if len(room.play_state.current_trick) == 1:
                    room.play_state.dummy_revealed = True

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
            from utils.error_logger import log_error
            log_error(e, endpoint='room/auto-play-ai', context={'position': current_player})
            break

    return ai_plays


def _check_auction_complete(auction_history: list) -> bool:
    """
    Check if auction is complete (3 consecutive passes after opening bid,
    or 4 passes with no bids)
    """
    if len(auction_history) < 4:
        return False

    if all(b == 'Pass' for b in auction_history):
        return len(auction_history) >= 4

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
    if settings.deal_type == 'convention' and settings.convention_filter:
        convention_map = get_convention_map()
        specialist = convention_map.get(settings.convention_filter)

        if specialist:
            deck = shuffled_deck()
            try:
                south_hand, deck = generate_hand_for_convention(specialist, deck, timeout_ms=500)
                if not south_hand:
                    south_hand = Hand(deck[:13])
                    deck = deck[13:]
            except Exception:
                south_hand = Hand(deck[:13])
                deck = deck[13:]
            return deal_remaining_hands({'South': south_hand})
        else:
            return deal_four_hands()
    else:
        return deal_four_hands()

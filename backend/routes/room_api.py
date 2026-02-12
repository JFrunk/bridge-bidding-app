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
            return jsonify({
                'success': True,
                'room_code': room_code,
                'my_position': 'N',  # Guest is always North
                'is_host': False,
                'message': message,
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

        # Check for version match (ETag-style)
        client_version = request.args.get('version', type=int)
        if client_version is not None and client_version == room.version:
            return '', 304  # Not Modified

        return jsonify({
            'success': True,
            'in_room': True,
            'room': room.to_dict(for_session=session_id)
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

        # Only host can change settings
        if session_id != room.host_session_id:
            return jsonify({
                'success': False,
                'error': 'Only host can change settings'
            }), 403

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
    # GAME CONTROL ENDPOINTS
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

        # Only host can deal
        if session_id != room.host_session_id:
            return jsonify({
                'success': False,
                'error': 'Only host can deal'
            }), 403

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
        dealer_positions = ['N', 'E', 'S', 'W']
        if 'dealer' in data and data['dealer'] in dealer_positions:
            room.dealer = data['dealer']
        else:
            # Rotate dealer
            current_idx = dealer_positions.index(room.dealer[0].upper()) if room.dealer else 0
            room.dealer = dealer_positions[(current_idx + 1) % 4]

        # Update room state
        room.deal = hands
        room.original_deal = {pos: hand for pos, hand in hands.items()}  # Deep copy
        room.auction_history = []
        room.play_state = None
        room.game_phase = 'bidding'
        room.increment_version()

        # Return response with caller's hand
        position = room.get_position_for_session(session_id)
        position_full = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}[position]

        return jsonify({
            'success': True,
            'dealer': room.dealer,
            'vulnerability': room.vulnerability,
            'my_hand': room._serialize_hand(room.deal[position_full]),
            'game_phase': room.game_phase,
            'current_bidder': room.get_current_bidder(),
            'is_my_turn': room.is_session_turn(session_id),
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
    # HELPER FUNCTIONS
    # =========================================================================


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

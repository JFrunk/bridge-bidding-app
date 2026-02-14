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
        engine = BiddingEngineV2Schema(use_v1_fallback=True)

        # Get the hand for this position
        position_full = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}[position]
        hand = room.deal.get(position_full)

        if not hand:
            return 'Pass'

        # Get bid from engine
        result = engine.get_bid(
            hand=hand,
            auction_history=room.auction_history,
            dealer=room.dealer,
            vulnerability=room.vulnerability or 'None'
        )

        return result.get('bid', 'Pass') if result else 'Pass'
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

        # Check for version match (ETag-style) BEFORE triggering AI
        # This prevents auto-bid from incrementing version on every poll
        client_version = request.args.get('version', type=int)
        if client_version is not None and client_version == room.version:
            return '', 304  # Not Modified

        # UNBLOCK AI: If it's an AI's turn (E/W), trigger auto-bidding now
        # Only runs when version has changed (i.e., after a human action)
        if room.game_phase == 'bidding':
            current_bidder = room.get_current_bidder()
            if current_bidder in ('E', 'W'):
                ai_bids = auto_bid_for_ai(room)
                if ai_bids:
                    print(f"🤖 Poll triggered AI bids: {ai_bids}")

        # Build room dict for response
        room_dict = room.to_dict(for_session=session_id)

        # Add beliefs for coaching support during bidding phase
        if room.game_phase == 'bidding' and room.auction_history:
            try:
                position = room.get_position_for_session(session_id)
                position_full = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}.get(position, position)
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
                    dealer_full = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}.get(room.dealer, room.dealer)
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

        # Auto-bid for AI if dealer is E or W
        ai_bids = auto_bid_for_ai(room)

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

        # Check if auction is complete (3 consecutive passes after opening bid)
        auction_complete = _check_auction_complete(room.auction_history)

        if auction_complete:
            room.game_phase = 'complete'  # Or 'playing' if we implement play

        # Auto-bid for E/W using the actual bidding engine
        ai_bids = auto_bid_for_ai(room) if not auction_complete else []
        auction_complete = _check_auction_complete(room.auction_history)

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

    # =========================================================================
    # PLAY ENDPOINTS
    # =========================================================================

    @app.route('/api/room/start-play', methods=['POST'])
    def room_start_play():
        """
        Start card play phase (host only)

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

        # Only host can start play
        if session_id != room.host_session_id:
            return jsonify({
                'success': False,
                'error': 'Only host can start play'
            }), 403

        # Must be in complete phase (bidding finished)
        if room.game_phase != 'complete':
            return jsonify({
                'success': False,
                'error': f'Cannot start play in {room.game_phase} phase'
            }), 400

        # Determine contract from auction
        dealer_positions = ['N', 'E', 'S', 'W']
        dealer_idx = dealer_positions.index(room.dealer[0].upper())
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
        dummy = PlayEngine.partner(contract.declarer)

        room.play_state = play_state
        room.game_phase = 'playing'
        room.increment_version()

        # If opening leader is AI (E or W), trigger AI play
        ai_plays = []
        if play_state.next_to_play in ('E', 'W'):
            ai_plays = _auto_play_for_ai(room)

        return jsonify({
            'success': True,
            'contract': str(contract),
            'declarer': contract.declarer,
            'dummy': dummy,
            'opening_leader': PlayEngine.next_player(contract.declarer),
            'next_to_play': room.play_state.next_to_play,
            'is_my_turn': room.is_session_turn(session_id),
            'ai_plays': ai_plays,
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
        dummy = PlayEngine.partner(declarer)

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
        position_full = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}[player]
        hand = room.play_state.hands[player]

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

            # Start new trick
            room.play_state.current_trick = []
            room.play_state.next_to_play = trick_winner
            room.play_state.current_trick_leader = trick_winner

            # Check if play is complete (13 tricks played)
            if len(room.play_state.trick_history) == 13:
                room.game_phase = 'complete'
        else:
            # Next player
            room.play_state.next_to_play = PlayEngine.next_player(player)

        room.increment_version()

        # Auto-play for AI if it's their turn
        ai_plays = []
        if room.game_phase == 'playing' and room.play_state.next_to_play in ('E', 'W'):
            ai_plays = _auto_play_for_ai(room)

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
            'ai_plays': ai_plays,
            'game_phase': room.game_phase,
            'dummy_revealed': room.play_state.dummy_revealed,
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

        position = room.get_position_for_session(session_id)
        ps = room.play_state
        declarer = ps.contract.declarer
        dummy = PlayEngine.partner(declarer)

        # Determine visible hands
        visible_hands = {}

        # Always see your own hand
        if position:
            visible_hands[position] = room._serialize_hand(ps.hands[position])

        # Dummy is visible after opening lead
        if ps.dummy_revealed:
            visible_hands[dummy] = room._serialize_hand(ps.hands[dummy])

        # Declarer sees both their hand and dummy
        if position == declarer:
            visible_hands[dummy] = room._serialize_hand(ps.hands[dummy])

        return jsonify({
            'success': True,
            'contract': str(ps.contract),
            'declarer': declarer,
            'dummy': dummy,
            'next_to_play': ps.next_to_play,
            'is_my_turn': room.is_session_turn(session_id),
            'current_trick': [{'rank': c.rank, 'suit': c.suit, 'player': p} for c, p in ps.current_trick],
            'trick_history': [
                {
                    'cards': [{'rank': c.rank, 'suit': c.suit, 'player': p} for c, p in t.cards],
                    'winner': t.winner
                } for t in ps.trick_history
            ],
            'tricks_ns': ps.tricks_won['N'] + ps.tricks_won['S'],
            'tricks_ew': ps.tricks_won['E'] + ps.tricks_won['W'],
            'visible_hands': visible_hands,
            'dummy_revealed': ps.dummy_revealed,
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
            ai = SimplePlayAI(difficulty=room.settings.ai_difficulty)

            # Determine trump suit
            trump_suit = None if room.play_state.contract.strain == 'NT' else room.play_state.contract.strain

            # Get legal cards
            hand = room.play_state.hands[current_player]
            legal_cards = [
                c for c in hand.cards
                if PlayEngine.is_legal_play(c, hand, room.play_state.current_trick, trump_suit)
            ]

            if not legal_cards:
                break  # Should never happen

            # Select card (simple AI for now)
            try:
                card = ai.select_card(
                    hand=hand,
                    current_trick=room.play_state.current_trick,
                    trump_suit=trump_suit,
                    legal_cards=legal_cards
                )
            except Exception as ai_err:
                print(f"⚠️ AI card selection error for {current_player}: {ai_err}")
                card = legal_cards[0]  # Fallback: play first legal card

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
                room.play_state.next_to_play = PlayEngine.next_player(current_player)

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

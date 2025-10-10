import random
import json
import traceback
import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine
from engine.hand_constructor import generate_hand_for_convention, generate_hand_with_constraints
from engine.ai.conventions.preempts import PreemptConvention
from engine.ai.conventions.jacoby_transfers import JacobyConvention
from engine.ai.conventions.stayman import StaymanConvention
from engine.ai.conventions.blackwood import BlackwoodConvention
from engine.play_engine import PlayEngine, PlayState, Contract
from engine.simple_play_ai import SimplePlayAI

app = Flask(__name__)
CORS(app)
engine = BiddingEngine()
play_engine = PlayEngine()
play_ai = SimplePlayAI()

current_deal = { 'North': None, 'East': None, 'South': None, 'West': None }
current_vulnerability = "None"
current_play_state = None  # Will hold PlayState during card play

CONVENTION_MAP = {
    "Preempt": PreemptConvention(),
    "JacobyTransfer": JacobyConvention(),
    "Stayman": StaymanConvention(),
    "Blackwood": BlackwoodConvention()
}

@app.route('/api/scenarios', methods=['GET'])
def get_scenarios():
    try:
        print(f"Current working directory: {os.getcwd()}")
        print(f"Files in directory: {os.listdir('.')}")
        with open('scenarios.json', 'r') as f: scenarios = json.load(f)
        scenario_names = [s['name'] for s in scenarios]
        return jsonify({'scenarios': scenario_names})
    except Exception as e:
        print(f"ERROR in /api/scenarios: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Could not load scenarios: {str(e)}'}), 500

@app.route('/api/convention-info', methods=['GET'])
def get_convention_info():
    try:
        convention_name = request.args.get('name')
        with open('convention_descriptions.json', 'r') as f:
            descriptions = json.load(f)

        if convention_name and convention_name in descriptions:
            return jsonify(descriptions[convention_name])
        elif convention_name:
            return jsonify({'error': f'Convention "{convention_name}" not found'}), 404
        else:
            # Return all conventions if no name specified
            return jsonify(descriptions)
    except (IOError, json.JSONDecodeError) as e:
        return jsonify({'error': f'Could not load convention descriptions: {e}'}), 500

@app.route('/api/load-scenario', methods=['POST'])
def load_scenario():
    global current_vulnerability
    current_vulnerability = "None"
    data = request.get_json()
    scenario_name = data.get('name')
    try:
        with open('scenarios.json', 'r') as f: scenarios = json.load(f)
        target_scenario = next((s for s in scenarios if s['name'] == scenario_name), None)
        if not target_scenario: return jsonify({'error': 'Scenario not found'}), 404
            
        ranks = '23456789TJQKA'
        suits = ['♠', '♥', '♦', '♣']
        deck = [Card(r, s) for r in ranks for s in suits]
        
        for pos in current_deal: current_deal[pos] = None
        
        for setup_rule in target_scenario.get('setup', []):
            position = setup_rule['position']
            hand = None
            if setup_rule.get('generate_for_convention'):
                specialist = CONVENTION_MAP.get(setup_rule['generate_for_convention'])
                if specialist:
                    hand, deck = generate_hand_for_convention(specialist, deck)
            elif setup_rule.get('constraints'):
                 hand, deck = generate_hand_with_constraints(setup_rule['constraints'], deck)
            if hand:
                current_deal[position] = hand
        
        remaining_cards = deck
        random.shuffle(remaining_cards)
        
        for position in ['North', 'East', 'South', 'West']:
            if not current_deal.get(position):
                current_deal[position] = Hand(remaining_cards[:13])
                remaining_cards = remaining_cards[13:]

        south_hand = current_deal['South']
        hand_for_json = [{'rank': card.rank, 'suit': card.suit} for card in south_hand.cards]
        points_for_json = { 'hcp': south_hand.hcp, 'dist_points': south_hand.dist_points, 'total_points': south_hand.total_points, 'suit_hcp': south_hand.suit_hcp, 'suit_lengths': south_hand.suit_lengths }
        return jsonify({'hand': hand_for_json, 'points': points_for_json, 'vulnerability': current_vulnerability})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Could not load scenario: {e}'}), 500

@app.route('/api/deal-hands', methods=['GET'])
def deal_hands():
    global current_vulnerability
    vulnerabilities = ["None", "NS", "EW", "Both"]
    try:
        current_idx = vulnerabilities.index(current_vulnerability)
        current_vulnerability = vulnerabilities[(current_idx + 1) % len(vulnerabilities)]
    except ValueError:
        current_vulnerability = "None"

    ranks = '23456789TJQKA'
    suits = ['♠', '♥', '♦', '♣']
    deck = [Card(rank, suit) for rank in ranks for suit in suits]
    random.shuffle(deck)
    
    current_deal['North'] = Hand(deck[0:13])
    current_deal['East'] = Hand(deck[13:26])
    current_deal['South'] = Hand(deck[26:39])
    current_deal['West'] = Hand(deck[39:52])
    
    south_hand = current_deal['South']
    hand_for_json = [{'rank': card.rank, 'suit': card.suit} for card in south_hand.cards]
    points_for_json = { 'hcp': south_hand.hcp, 'dist_points': south_hand.dist_points, 'total_points': south_hand.total_points, 'suit_hcp': south_hand.suit_hcp, 'suit_lengths': south_hand.suit_lengths }
    return jsonify({'hand': hand_for_json, 'points': points_for_json, 'vulnerability': current_vulnerability})

@app.route('/api/get-next-bid', methods=['POST'])
def get_next_bid():
    try:
        data = request.get_json()
        auction_history, current_player = data['auction_history'], data['current_player']
        player_hand = current_deal[current_player]
        if not player_hand: 
            return jsonify({'error': "Deal has not been made yet."}), 400
        
        bid, explanation = engine.get_next_bid(player_hand, auction_history, current_player, current_vulnerability)
        return jsonify({'bid': bid, 'explanation': explanation})
    
    except Exception as e:
        print("---!!! AN ERROR OCCURRED IN GET_NEXT_BID !!!---")
        traceback.print_exc()
        return jsonify({'error': f"A critical server error occurred: {e}"}), 500

@app.route('/api/get-feedback', methods=['POST'])
def get_feedback():
    data = request.get_json()
    try:
        auction_history = data['auction_history']
        user_bid, auction_before_user_bid = auction_history[-1], auction_history[:-1]
        user_hand = current_deal['South']
        optimal_bid, explanation = engine.get_next_bid(user_hand, auction_before_user_bid, 'South', current_vulnerability)
        if user_bid == optimal_bid:
            feedback = f"✅ Correct! Your bid of {user_bid} is optimal. {explanation}"
        else:
            feedback = f"⚠️ Your bid was {user_bid}. The recommended bid is {optimal_bid}. {explanation}"
        return jsonify({'feedback': feedback})
    except Exception as e:
        return jsonify({'error': f"Server error in get_feedback: {e}"}), 500

@app.route('/api/get-all-hands', methods=['GET'])
def get_all_hands():
    try:
        all_hands = {}
        for position in ['North', 'East', 'South', 'West']:
            hand = current_deal.get(position)
            if not hand:
                return jsonify({'error': f'Hand for {position} not available'}), 400

            hand_for_json = [{'rank': card.rank, 'suit': card.suit} for card in hand.cards]
            points_for_json = {
                'hcp': hand.hcp,
                'dist_points': hand.dist_points,
                'total_points': hand.total_points,
                'suit_hcp': hand.suit_hcp,
                'suit_lengths': hand.suit_lengths
            }
            all_hands[position] = {
                'hand': hand_for_json,
                'points': points_for_json
            }

        return jsonify({
            'hands': all_hands,
            'vulnerability': current_vulnerability
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Server error in get_all_hands: {e}'}), 500

@app.route('/api/request-review', methods=['POST'])
def request_review():
    try:
        data = request.get_json()
        auction_history = data.get('auction_history', [])
        user_concern = data.get('user_concern', '')

        # Prepare all hands data
        all_hands = {}
        for position in ['North', 'East', 'South', 'West']:
            hand = current_deal.get(position)
            if not hand:
                return jsonify({'error': f'Hand for {position} not available'}), 400

            hand_for_json = [{'rank': card.rank, 'suit': card.suit} for card in hand.cards]
            points_for_json = {
                'hcp': hand.hcp,
                'dist_points': hand.dist_points,
                'total_points': hand.total_points,
                'suit_hcp': hand.suit_hcp,
                'suit_lengths': hand.suit_lengths
            }
            all_hands[position] = {
                'cards': hand_for_json,
                'points': points_for_json
            }

        # Create review request object
        review_request = {
            'timestamp': datetime.now().isoformat(),
            'all_hands': all_hands,
            'auction': auction_history,
            'vulnerability': current_vulnerability,
            'dealer': 'North',
            'user_position': 'South',
            'user_concern': user_concern
        }

        # Create filename with timestamp
        timestamp_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f'hand_{timestamp_str}.json'

        # Check if we're on Render (ephemeral storage - files won't persist for user access)
        # Render sets RENDER or RENDER_SERVICE_NAME environment variables
        is_render = os.getenv('RENDER') or os.getenv('RENDER_SERVICE_NAME') or os.getenv('FLASK_ENV') == 'production'

        if is_render:
            # On Render: don't save to file, embed data in prompt instead
            print("Running on Render - will embed full data in prompt (files not accessible to users)")
            saved_to_file = False
        else:
            # Local development: save to file for reference
            try:
                filepath = os.path.join('review_requests', filename)
                os.makedirs('review_requests', exist_ok=True)
                with open(filepath, 'w') as f:
                    json.dump(review_request, indent=2, fp=f)
                saved_to_file = True
                print(f"Saved review request to {filepath}")
            except Exception as file_error:
                print(f"Could not save to file: {file_error}")
                saved_to_file = False

        # Return the full review data so frontend can display it
        return jsonify({
            'success': True,
            'filename': filename,
            'saved_to_file': saved_to_file,
            'review_data': review_request  # Include full data in response
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Server error in request_review: {e}'}), 500
# ============================================================================
# CARD PLAY ENDPOINTS
# ============================================================================

@app.route("/api/start-play", methods=["POST"])
def start_play():
    """
    Called when bidding completes (3 consecutive passes)
    Determines contract and sets up play state
    """
    global current_play_state
    
    try:
        data = request.get_json()
        auction = data.get("auction_history", [])
        vulnerability_str = data.get("vulnerability", "None")
        
        # Determine contract from auction
        contract = play_engine.determine_contract(auction, dealer_index=0)
        
        if not contract:
            return jsonify({"error": "No contract found (all passed)"}), 400
        
        # Set up vulnerability dict
        vuln_dict = {
            "ns": vulnerability_str in ["NS", "Both"],
            "ew": vulnerability_str in ["EW", "Both"]
        }

        # Get hands (from request or global current_deal)
        hands_data = data.get("hands")
        if hands_data:
            # Convert JSON hand data to Hand objects
            from engine.hand import Hand, Card
            hands = {}
            for pos in ["N", "E", "S", "W"]:
                if pos in hands_data:
                    cards = [Card(c['rank'], c['suit']) for c in hands_data[pos]]
                    hands[pos] = Hand(cards)
        else:
            # Use current deal from bidding phase
            hands = {}
            for pos in ["N", "E", "S", "W"]:
                hands[pos] = current_deal[pos]
        
        # Create play state
        current_play_state = PlayState(
            contract=contract,
            hands=hands,
            current_trick=[],
            tricks_won={"N": 0, "E": 0, "S": 0, "W": 0},
            trick_history=[],
            next_to_play=play_engine.next_player(contract.declarer),  # LHO of declarer leads
            dummy_revealed=False
        )
        
        # Opening leader (LHO of declarer)
        opening_leader = current_play_state.next_to_play
        dummy_position = current_play_state.dummy
        
        return jsonify({
            "success": True,
            "contract": str(contract),
            "contract_details": {
                "level": contract.level,
                "strain": contract.strain,
                "declarer": contract.declarer,
                "doubled": contract.doubled
            },
            "opening_leader": opening_leader,
            "dummy": dummy_position,
            "next_to_play": opening_leader
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error starting play: {e}"}), 500

@app.route("/api/play-card", methods=["POST"])
def play_card():
    """
    User plays a card
    """
    global current_play_state
    
    if not current_play_state:
        return jsonify({"error": "No play in progress"}), 400
    
    try:
        data = request.get_json()
        card_data = data.get("card")
        position = data.get("position", "South")
        
        # Create card object
        card = Card(rank=card_data["rank"], suit=card_data["suit"])
        hand = current_play_state.hands[position]
        
        # Validate legal play
        is_legal = play_engine.is_legal_play(
            card, hand, current_play_state.current_trick, 
            current_play_state.contract.trump_suit
        )
        
        if not is_legal:
            return jsonify({
                "legal": False,
                "error": "Must follow suit if able"
            }), 400
        
        # Play the card
        current_play_state.current_trick.append((card, position))
        
        # Remove card from hand
        hand.cards.remove(card)
        
        # Reveal dummy after opening lead
        if len(current_play_state.current_trick) == 1 and not current_play_state.dummy_revealed:
            current_play_state.dummy_revealed = True
        
        # Check if trick is complete
        trick_complete = len(current_play_state.current_trick) == 4
        trick_winner = None
        
        if trick_complete:
            # Determine winner
            trick_winner = play_engine.determine_trick_winner(
                current_play_state.current_trick,
                current_play_state.contract.trump_suit
            )
            
            # Update tricks won
            current_play_state.tricks_won[trick_winner] += 1
            
            # Save to history
            from engine.play_engine import Trick
            current_play_state.trick_history.append(
                Trick(
                    cards=list(current_play_state.current_trick),
                    leader=current_play_state.next_to_play,
                    winner=trick_winner
                )
            )
            
            # Clear current trick
            current_play_state.current_trick = []
            
            # Next player is the winner
            current_play_state.next_to_play = trick_winner
        else:
            # Next player clockwise
            current_play_state.next_to_play = play_engine.next_player(position)
        
        return jsonify({
            "legal": True,
            "trick_complete": trick_complete,
            "trick_winner": trick_winner,
            "next_to_play": current_play_state.next_to_play,
            "tricks_won": current_play_state.tricks_won,
            "dummy_revealed": current_play_state.dummy_revealed
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error playing card: {e}"}), 500

@app.route("/api/get-ai-play", methods=["POST"])
def get_ai_play():
    """
    AI plays a card
    """
    global current_play_state
    
    if not current_play_state:
        return jsonify({"error": "No play in progress"}), 400
    
    try:
        position = current_play_state.next_to_play
        
        # AI chooses card
        card = play_ai.choose_card(current_play_state, position)
        hand = current_play_state.hands[position]
        
        # Play the card
        current_play_state.current_trick.append((card, position))
        hand.cards.remove(card)
        
        # Reveal dummy after opening lead
        if len(current_play_state.current_trick) == 1 and not current_play_state.dummy_revealed:
            current_play_state.dummy_revealed = True
        
        # Check if trick is complete
        trick_complete = len(current_play_state.current_trick) == 4
        trick_winner = None
        
        if trick_complete:
            # Determine winner
            trick_winner = play_engine.determine_trick_winner(
                current_play_state.current_trick,
                current_play_state.contract.trump_suit
            )
            
            # Update tricks won
            current_play_state.tricks_won[trick_winner] += 1
            
            # Save to history
            from engine.play_engine import Trick
            current_play_state.trick_history.append(
                Trick(
                    cards=list(current_play_state.current_trick),
                    leader=current_play_state.next_to_play,
                    winner=trick_winner
                )
            )
            
            # Clear current trick
            current_play_state.current_trick = []
            
            # Next player is the winner
            current_play_state.next_to_play = trick_winner
        else:
            # Next player clockwise
            current_play_state.next_to_play = play_engine.next_player(position)
        
        return jsonify({
            "card": {"rank": card.rank, "suit": card.suit},
            "position": position,
            "trick_complete": trick_complete,
            "trick_winner": trick_winner,
            "next_to_play": current_play_state.next_to_play,
            "tricks_won": current_play_state.tricks_won,
            "explanation": f"{position} played {card.rank}{card.suit}"
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error with AI play: {e}"}), 500

@app.route("/api/get-play-state", methods=["GET"])
def get_play_state():
    """
    Get current play state
    """
    if not current_play_state:
        return jsonify({"error": "No play in progress"}), 400
    
    try:
        # Convert current trick to JSON
        current_trick_json = [
            {"card": {"rank": c.rank, "suit": c.suit}, "position": p}
            for c, p in current_play_state.current_trick
        ]
        
        # Get dummy hand if revealed
        dummy_hand = None
        if current_play_state.dummy_revealed:
            dummy_pos = current_play_state.dummy
            dummy_hand = {
                "cards": [{"rank": c.rank, "suit": c.suit} for c in current_play_state.hands[dummy_pos].cards],
                "position": dummy_pos
            }
        
        return jsonify({
            "contract": {
                "level": current_play_state.contract.level,
                "strain": current_play_state.contract.strain,
                "declarer": current_play_state.contract.declarer,
                "doubled": current_play_state.contract.doubled
            },
            "current_trick": current_trick_json,
            "tricks_won": current_play_state.tricks_won,
            "next_to_play": current_play_state.next_to_play,
            "dummy_revealed": current_play_state.dummy_revealed,
            "dummy_hand": dummy_hand,
            "is_complete": current_play_state.is_complete
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error getting play state: {e}"}), 500

@app.route("/api/complete-play", methods=["GET"])
def complete_play():
    """
    Get final results after play completes
    """
    if not current_play_state:
        return jsonify({"error": "No play in progress"}), 400
    
    try:
        # Determine declarer side
        declarer = current_play_state.contract.declarer
        if declarer in ["N", "S"]:
            tricks_taken = current_play_state.tricks_taken_ns
        else:
            tricks_taken = current_play_state.tricks_taken_ew
        
        # Calculate vulnerability
        vuln_dict = {
            "ns": current_vulnerability in ["NS", "Both"],
            "ew": current_vulnerability in ["EW", "Both"]
        }
        
        # Calculate score
        score_result = play_engine.calculate_score(
            current_play_state.contract,
            tricks_taken,
            vuln_dict
        )
        
        return jsonify({
            "contract": str(current_play_state.contract),
            "tricks_taken": tricks_taken,
            "tricks_needed": current_play_state.contract.tricks_needed,
            "score": score_result["score"],
            "made": score_result["made"],
            "overtricks": score_result.get("overtricks", 0),
            "undertricks": score_result.get("undertricks", 0),
            "breakdown": score_result.get("breakdown", {})
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error calculating final score: {e}"}), 500


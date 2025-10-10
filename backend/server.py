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

app = Flask(__name__)
CORS(app)
engine = BiddingEngine()
current_deal = { 'North': None, 'East': None, 'South': None, 'West': None }
current_vulnerability = "None"

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
        filepath = os.path.join('review_requests', filename)

        # Ensure directory exists
        os.makedirs('review_requests', exist_ok=True)

        # Save to file
        with open(filepath, 'w') as f:
            json.dump(review_request, indent=2, fp=f)

        return jsonify({
            'success': True,
            'filename': filename,
            'filepath': filepath
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Server error in request_review: {e}'}), 500
import random
import json
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

CONVENTION_MAP = {
    "Preempt": PreemptConvention(),
    "JacobyTransfer": JacobyConvention(),
    "Stayman": StaymanConvention(),
    "Blackwood": BlackwoodConvention()
}

@app.route('/api/scenarios', methods=['GET'])
def get_scenarios():
    try:
        with open('scenarios.json', 'r') as f: scenarios = json.load(f)
        scenario_names = [s['name'] for s in scenarios]
        return jsonify({'scenarios': scenario_names})
    except (IOError, json.JSONDecodeError) as e:
        return jsonify({'error': f'Could not load scenarios: {e}'}), 500

@app.route('/api/load-scenario', methods=['POST'])
def load_scenario():
    data = request.get_json()
    scenario_name = data.get('name')
    try:
        with open('scenarios.json', 'r') as f: scenarios = json.load(f)
        target_scenario = next((s for s in scenarios if s['name'] == scenario_name), None)
        if not target_scenario: return jsonify({'error': 'Scenario not found'}), 404
            
        ranks = '23456789TJQKA'
        suits = ['♠', '♥', '♦', '♣']
        full_deck_set = {Card(r, s) for r in ranks for s in suits}
        
        for pos in current_deal: current_deal[pos] = None
        generated_hands = {}

        for setup_rule in target_scenario.get('setup', []):
            position = setup_rule['position']
            hand = None
            if setup_rule.get('generate_for_convention'):
                specialist = CONVENTION_MAP.get(setup_rule['generate_for_convention'])
                if specialist: hand = generate_hand_for_convention(specialist)
            elif setup_rule.get('constraints'):
                 hand = generate_hand_with_constraints(setup_rule['constraints'])
            
            if hand:
                generated_hands[position] = hand
                full_deck_set -= set(hand.cards)

        remaining_cards = list(full_deck_set)
        random.shuffle(remaining_cards)
        
        for position in ['North', 'East', 'South', 'West']:
            if not current_deal.get(position):
                current_deal[position] = Hand(remaining_cards[:13])
                remaining_cards = remaining_cards[13:]

        south_hand = current_deal['South']
        hand_for_json = [{'rank': card.rank, 'suit': card.suit} for card in south_hand.cards]
        points_for_json = { 'hcp': south_hand.hcp, 'dist_points': south_hand.dist_points, 'total_points': south_hand.total_points, 'suit_hcp': south_hand.suit_hcp, 'suit_lengths': south_hand.suit_lengths }
        return jsonify({'hand': hand_for_json, 'points': points_for_json})
    except Exception as e:
        return jsonify({'error': f'Could not load scenario: {e}'}), 500

@app.route('/api/deal-hands', methods=['GET'])
def deal_hands():
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
    return jsonify({'hand': hand_for_json, 'points': points_for_json})

@app.route('/api/get-next-bid', methods=['POST'])
def get_next_bid():
    data = request.get_json()
    try:
        auction_history, current_player = data['auction_history'], data['current_player']
        player_hand = current_deal[current_player]
        if not player_hand: return jsonify({'error': "Deal has not been made yet."}), 400
        bid, explanation = engine.get_next_bid(player_hand, auction_history, current_player)
        return jsonify({'bid': bid, 'explanation': explanation})
    except Exception as e: return jsonify({'error': f"Server error in get_next_bid: {e}"}), 500

@app.route('/api/get-feedback', methods=['POST'])
def get_feedback():
    data = request.get_json()
    try:
        auction_history = data['auction_history']
        user_bid, auction_before_user_bid = auction_history[-1], auction_history[:-1]
        user_hand = current_deal['South']
        optimal_bid, explanation = engine.get_next_bid(user_hand, auction_before_user_bid, 'South')
        if user_bid == optimal_bid:
            feedback = f"✅ Correct! Your bid of {user_bid} is optimal. {explanation}"
        else:
            feedback = f"⚠️ Your bid was {user_bid}. The recommended bid is {optimal_bid}. {explanation}"
        return jsonify({'feedback': feedback})
    except Exception as e: return jsonify({'error': f"Server error in get_feedback: {e}"}), 500
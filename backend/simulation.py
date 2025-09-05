import random
import json
from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine
from engine.hand_constructor import generate_hand_for_convention, generate_hand_with_constraints
from engine.ai.conventions.preempts import PreemptConvention
from engine.ai.conventions.jacoby_transfers import JacobyConvention
from engine.ai.conventions.stayman import StaymanConvention
from engine.ai.conventions.blackwood import BlackwoodConvention

# --- SETUP ---
DEAL_COUNT = 100
SCENARIO_COUNT = 30
LOG_FILE = "simulation_log.txt"

CONVENTION_MAP = {
    "Preempt": PreemptConvention(), "JacobyTransfer": JacobyConvention(),
    "Stayman": StaymanConvention(), "Blackwood": BlackwoodConvention()
}

def deal_random_hand():
    ranks = '23456789TJQKA'
    suits = ['♠', '♥', '♦', '♣']
    deck = [Card(rank, suit) for rank in ranks for suit in suits]
    random.shuffle(deck)
    return {
        'North': Hand(deck[0:13]), 'East': Hand(deck[13:26]),
        'South': Hand(deck[26:39]), 'West': Hand(deck[39:52])
    }

import random
import json
from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine
from engine.hand_constructor import generate_hand_for_convention, generate_hand_with_constraints
from engine.ai.conventions.preempts import PreemptConvention
from engine.ai.conventions.jacoby_transfers import JacobyConvention
from engine.ai.conventions.stayman import StaymanConvention
from engine.ai.conventions.blackwood import BlackwoodConvention

# --- SETUP ---
DEAL_COUNT = 100
SCENARIO_COUNT = 30
LOG_FILE = "simulation_log.txt"

CONVENTION_MAP = {
    "Preempt": PreemptConvention(), "JacobyTransfer": JacobyConvention(),
    "Stayman": StaymanConvention(), "Blackwood": BlackwoodConvention()
}

def deal_random_hand():
    ranks = '23456789TJQKA'
    suits = ['♠', '♥', '♦', '♣']
    deck = [Card(rank, suit) for rank in ranks for suit in suits]
    random.shuffle(deck)
    return {
        'North': Hand(deck[0:13]), 'East': Hand(deck[13:26]),
        'South': Hand(deck[26:39]), 'West': Hand(deck[39:52])
    }

def deal_scenario_hand(scenario, deck):
    deal = {}
    remaining_deck = list(deck)
    for setup_rule in scenario.get('setup', []):
        position = setup_rule.get('position')
        convention_name = setup_rule.get('generate_for_convention')

        # --- THIS IS THE FIX ---
        # Ensure both position and convention_name exist before proceeding
        if position and convention_name:
            specialist = CONVENTION_MAP.get(convention_name)
            if specialist:
                hand, remaining_deck = generate_hand_for_convention(specialist, remaining_deck)
                deal[position] = hand
    
    random.shuffle(remaining_deck)
    for position in ['North', 'East', 'South', 'West']:
        if position not in deal:
            deal[position] = Hand(remaining_deck[:13])
            remaining_deck = remaining_deck[13:]
            
    return deal

# ... (The rest of the file: run_bidding_simulation, format_deal_for_log, main, etc. are unchanged) ...

def run_bidding_simulation(engine, deal, vulnerability):
    auction_history = []
    players = ['North', 'East', 'South', 'West']
    current_bidder_index = 0

    while True:
        if len(auction_history) >= 4 and all(b == "Pass" for b in auction_history[-3:]):
            break
        if len(auction_history) > 30: break # Safety break

        player_name = players[current_bidder_index]
        hand = deal[player_name]
        bid, _ = engine.get_next_bid(hand, auction_history, player_name, vulnerability)
        auction_history.append(bid)
        current_bidder_index = (current_bidder_index + 1) % 4
    
    return auction_history

def format_deal_for_log(deal, auction, deal_num, vulnerability, scenario_name="Random"):
    log_entry = [f"--- Hand {deal_num} (Scenario: {scenario_name}, Vulnerability: {vulnerability}) ---\n"]
    for player in ['North', 'East', 'South', 'West']:
        hand = deal[player]
        log_entry.append(f"[{player}] (HCP: {hand.hcp}, Total Pts: {hand.total_points})")
        log_entry.append(str(hand))
    
    log_entry.append("\nAuction:")
    bidding_str = ""
    for i, bid in enumerate(auction):
        if i % 4 == 0: bidding_str += "\n"
        bidding_str += f"{['N','E','S','W'][i%4]}: {bid:<7}"
    log_entry.append(bidding_str)
    log_entry.append("\n" + "-"*40 + "\n")
    return "\n".join(log_entry)


def main():
    print(f"Starting bidding simulation for {DEAL_COUNT} hands...")
    engine = BiddingEngine()
    
    try:
        with open('scenarios.json', 'r') as f:
            scenarios = json.load(f)
    except (IOError, json.JSONDecodeError):
        scenarios = []
        print("Warning: scenarios.json not found or corrupted. Running random hands only.")
    
    with open(LOG_FILE, 'w') as log_file:
        for i in range(1, DEAL_COUNT + 1):
            deal, scenario_name = None, "Random"
            if i <= SCENARIO_COUNT and scenarios:
                scenario = random.choice([s for s in scenarios if s.get("setup")])
                if scenario:
                    scenario_name = scenario['name']
                    deck = [Card(r, s) for r in '23456789TJQKA' for s in '♠♥♦♣']
                    deal = deal_scenario_hand(scenario, deck)
            if not deal:
                deal = deal_random_hand()

            auction = run_bidding_simulation(engine, deal, "None")
            log_entry = format_deal_for_log(deal, auction, i, "None", scenario_name)
            log_file.write(log_entry)
            print(f"  ... Hand {i} completed.")

    print(f"\nSimulation complete. Results saved to {LOG_FILE}")

# This is the line that was missing, which tells Python to run the simulation.
if __name__ == "__main__":
    main()
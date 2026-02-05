"""
Slam Diagnostic Test Suite

Curated hands for diagnosing and tracking slam bidding accuracy.
Each hand has known HCP distribution and expected bidding outcomes.

Categories:
  A. HCP-based small slams (33-36 combined HCP) - SHOULD bid 6-level
  B. HCP-based grand slams (37+ combined HCP) - SHOULD bid 7-level
  C. Near-slam stops (30-32 combined HCP) - should NOT bid slam
  D. Distribution slams (28-32 HCP + fit + shape) - SHOULD bid slam (stretch)
  E. Slam after strong 2C opening - SHOULD bid slam
  F. NT slams (balanced, 33+ HCP) - SHOULD bid 6NT+

Run with:
  cd backend && python -m pytest tests/regression/test_slam_diagnostics.py -v
  cd backend && python -m pytest tests/regression/test_slam_diagnostics.py -v -s  # with auction output

For diagnostic report only (no assertions):
  cd backend && python tests/regression/test_slam_diagnostics.py
"""

import pytest
from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ALL_RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
ALL_SUITS = ['♠', '♥', '♦', '♣']

FULL_DECK = {(r, s) for r in ALL_RANKS for s in ALL_SUITS}


def _hand_from_strings(spades: str, hearts: str, diamonds: str, clubs: str) -> Hand:
    """Create a Hand from suit strings like 'AKQ32'."""
    cards = []
    for suit, holding in [('♠', spades), ('♥', hearts), ('♦', diamonds), ('♣', clubs)]:
        for rank in holding:
            cards.append(Card(rank, suit))
    assert len(cards) == 13, f"Hand must have 13 cards, got {len(cards)}"
    return Hand(cards)


def _cards_set(hand: Hand) -> set:
    """Return set of (rank, suit) tuples from a Hand."""
    return {(c.rank, c.suit) for c in hand.cards}


def _deal_remaining(north: Hand, south: Hand) -> tuple:
    """Deal remaining cards evenly to East/West."""
    used = _cards_set(north) | _cards_set(south)
    remaining = list(FULL_DECK - used)
    suit_order = {'♠': 0, '♥': 1, '♦': 2, '♣': 3}
    rank_order = {r: i for i, r in enumerate(ALL_RANKS)}
    remaining.sort(key=lambda c: (suit_order[c[1]], rank_order[c[0]]))
    assert len(remaining) == 26, f"Expected 26 remaining cards, got {len(remaining)}"
    east_cards = [Card(r, s) for r, s in remaining[:13]]
    west_cards = [Card(r, s) for r, s in remaining[13:]]
    return Hand(east_cards), Hand(west_cards)


def _simulate_auction(engine, hands, dealer='North'):
    """Run full auction, return list of bids."""
    auction = []
    positions = ['North', 'East', 'South', 'West']
    dealer_index = positions.index(dealer)
    consecutive_passes = 0

    for _ in range(40):
        current_pos = positions[(dealer_index + len(auction)) % 4]
        bid, explanation = engine.get_next_bid(
            hands[current_pos], auction, current_pos, 'None'
        )
        auction.append(bid)
        if bid == 'Pass':
            consecutive_passes += 1
        else:
            consecutive_passes = 0
        if consecutive_passes >= 3 and len(auction) > 3:
            break

    return auction


def _final_contract(auction):
    """Extract final contract from auction."""
    for bid in reversed(auction):
        if bid not in ('Pass', 'X', 'XX'):
            return bid
    return None


def _contract_level(auction):
    """Get the numeric level of the final contract (0 if passed out)."""
    contract = _final_contract(auction)
    if contract and contract[0].isdigit():
        return int(contract[0])
    return 0


def _declarer_partnership(auction, dealer='North'):
    """Determine which partnership (NS/EW) won the contract."""
    positions = ['North', 'East', 'South', 'West']
    dealer_index = positions.index(dealer)
    contract = _final_contract(auction)
    if not contract:
        return None
    strain = contract[1:] if len(contract) > 1 else contract
    for i, bid in enumerate(auction):
        if bid in ('Pass', 'X', 'XX'):
            continue
        if len(bid) >= 2 and bid[1:] == strain:
            pos = positions[(dealer_index + i) % 4]
            return 'NS' if pos in ('North', 'South') else 'EW'
    return None


# ---------------------------------------------------------------------------
# All HCP verified by automated validation. Format:
#   north/south: (spades, hearts, diamonds, clubs)
# Remaining cards dealt automatically to East/West.
# ---------------------------------------------------------------------------

SLAM_SCENARIOS = [
    # ===== Category A: HCP Small Slams (33-36 combined) =====
    {
        'id': 'A1',
        'category': 'hcp_small_slam',
        'description': '1NT opener (16) + strong responder (18) = 34 HCP',
        'north': ('KQ52', 'AJ3', 'KJ4', 'Q32'),      # 16 HCP balanced
        'south': ('A93', 'KQ4', 'AQ52', 'K54'),       # 18 HCP
        'expected_min_level': 6,
        'dealer': 'North',
    },
    {
        'id': 'A2',
        'category': 'hcp_small_slam',
        'description': '1♠ opener (17) + strong responder (17) = 34 HCP, spade fit',
        'north': ('AKJ52', 'AQ3', 'Q42', 'J2'),       # 17 HCP, 5 spades
        'south': ('Q93', 'KJ4', 'AK53', 'A43'),       # 17 HCP, 3 spades
        'expected_min_level': 6,
        'dealer': 'North',
    },
    {
        'id': 'A3',
        'category': 'hcp_small_slam',
        'description': '2NT opener (20) + responder (14) = 34 HCP',
        'north': ('AK32', 'KQ3', 'AJ4', 'K32'),      # 20 HCP balanced
        'south': ('QJ4', 'A942', 'KQ2', 'Q54'),       # 14 HCP
        'expected_min_level': 6,
        'dealer': 'North',
    },
    {
        'id': 'A4',
        'category': 'hcp_small_slam',
        'description': '1♥ opener (15) + strong responder (18) = 33 HCP, heart fit',
        'north': ('KQ2', 'AKJ52', 'Q42', '32'),       # 15 HCP, 5 hearts
        'south': ('AJ4', 'Q93', 'AK53', 'KJ4'),       # 18 HCP, 3 hearts
        'expected_min_level': 6,
        'dealer': 'North',
    },
    {
        'id': 'A5',
        'category': 'hcp_small_slam',
        'description': '1NT opener (17) + strong responder (16) = 33 HCP, borderline',
        'north': ('AQ32', 'KJ3', 'AJ4', 'Q32'),      # 17 HCP balanced
        'south': ('KJ4', 'AQ42', 'K53', 'K54'),       # 16 HCP
        'expected_min_level': 6,
        'dealer': 'North',
    },

    # ===== Category B: HCP Grand Slams (37+ combined) =====
    {
        'id': 'B1',
        'category': 'hcp_grand_slam',
        'description': '2♣ opener (22) + positive responder (15) = 37 HCP',
        'north': ('AKQJ2', 'AK3', 'KQ2', '32'),      # 22 HCP
        'south': ('T3', 'QJ4', 'AJ53', 'AK54'),      # 15 HCP
        'expected_min_level': 7,
        'dealer': 'North',
    },
    {
        'id': 'B2',
        'category': 'hcp_grand_slam',
        'description': '1NT opener (17) + monster responder (20) = 37 HCP',
        'north': ('KQ32', 'AJ3', 'KQ4', 'Q32'),      # 17 HCP balanced
        'south': ('AJ4', 'K52', 'AJ53', 'AK4'),      # 20 HCP
        'expected_min_level': 7,
        'dealer': 'North',
    },
    {
        'id': 'B3',
        'category': 'hcp_grand_slam',
        'description': '2♣ opener (25) + positive responder (12) = 37 HCP',
        'north': ('AKQ2', 'AKQ', 'AK42', '32'),      # 25 HCP
        'south': ('J53', 'J42', 'QJ3', 'AK54'),      # 12 HCP
        'expected_min_level': 7,
        'dealer': 'North',
    },

    # ===== Category C: Near-Slam Stops (30-32 combined) =====
    {
        'id': 'C1',
        'category': 'near_slam_stop',
        'description': '1NT opener (16) + responder (15) = 31 HCP, should stop at game',
        'north': ('KQ32', 'AJ3', 'KJ4', 'Q32'),      # 16 HCP balanced
        'south': ('AJ4', 'KQ2', 'Q532', 'K54'),       # 15 HCP
        'expected_max_level': 5,
        'dealer': 'North',
    },
    {
        'id': 'C2',
        'category': 'near_slam_stop',
        'description': '1♠ opener (13) + responder (18) = 31 HCP, should stop at game',
        'north': ('AKJ52', 'Q32', 'K42', '32'),       # 13 HCP, 5 spades
        'south': ('Q93', 'AK4', 'AQ53', 'K54'),       # 18 HCP, 3 spades
        'expected_max_level': 5,
        'dealer': 'North',
    },
    {
        'id': 'C3',
        'category': 'near_slam_stop',
        'description': '2NT opener (20) + weak responder (10) = 30 HCP, should stop at game',
        'north': ('AK32', 'KQ3', 'AJ4', 'K32'),      # 20 HCP balanced
        'south': ('QJ4', 'A42', 'K852', '954'),       # 10 HCP
        'expected_max_level': 5,
        'dealer': 'North',
    },
    {
        'id': 'C4',
        'category': 'near_slam_stop',
        'description': '1♠ opener (14) + responder (16) = 30 HCP, should stop at game',
        'north': ('AK932', 'Q32', 'K42', 'Q2'),       # 14 HCP, 5 spades
        'south': ('QJ4', 'AK4', 'Q653', 'KJ3'),      # 16 HCP, 3 spades
        'expected_max_level': 5,
        'dealer': 'North',
    },

    # ===== Category D: Distribution Slams (28-32 HCP + fit + shape) =====
    {
        'id': 'D1',
        'category': 'distribution_slam',
        'description': '1♠ opener (17) + responder (11) with 10-card fit + singleton = 28 HCP',
        'north': ('AKQJ52', 'K32', 'A42', '2'),       # 17 HCP, 6 spades, singleton club
        'south': ('9843', 'AQ4', 'KQ3', '543'),       # 11 HCP, 4 spades
        'expected_min_level': 6,
        'slam_type': 'distribution',
    },
    {
        'id': 'D2',
        'category': 'distribution_slam',
        'description': '1♥ opener (13) + responder (16) with 9-card fit + doubleton = 29 HCP',
        'north': ('K2', 'AKJ52', 'Q642', '32'),       # 13 HCP, 5 hearts, doubleton clubs
        'south': ('AQ3', 'Q943', 'K3', 'AJ54'),       # 16 HCP, 4 hearts
        'expected_min_level': 6,
        'slam_type': 'distribution',
    },
    {
        'id': 'D3',
        'category': 'distribution_slam',
        'description': '1♠ opener (17) + responder (14) with 10-card fit + singleton = 31 HCP',
        'north': ('AKJ932', 'AQ3', 'K42', '2'),       # 17 HCP, 6 spades, singleton club
        'south': ('QT54', 'K42', 'AQ3', 'K43'),       # 14 HCP, 4 spades
        'expected_min_level': 6,
        'slam_type': 'distribution',
    },

    # ===== Category E: Slam After Strong 2♣ =====
    {
        'id': 'E1',
        'category': 'strong_2c_slam',
        'description': '2♣ opener (23) + 12 HCP responder = 35 HCP',
        'north': ('AKQ32', 'AK3', 'AK2', '32'),      # 23 HCP
        'south': ('J54', 'Q42', 'Q53', 'AK54'),       # 12 HCP
        'expected_min_level': 6,
        'dealer': 'North',
    },
    {
        'id': 'E2',
        'category': 'strong_2c_slam',
        'description': '2♣ opener (23) + 11 HCP responder = 34 HCP, heart fit',
        'north': ('AK2', 'AKQ32', 'AK3', '32'),      # 23 HCP, 5 hearts
        'south': ('J53', 'J94', 'Q42', 'AK54'),       # 11 HCP, 3 hearts
        'expected_min_level': 6,
        'dealer': 'North',
    },

    # ===== Category F: NT Slams =====
    {
        'id': 'F1',
        'category': 'nt_slam',
        'description': '1NT opener (17) + balanced responder (17) = 34 HCP',
        'north': ('AQ32', 'KJ3', 'AJ4', 'Q32'),      # 17 HCP balanced
        'south': ('K94', 'AQ42', 'KQ3', 'K54'),       # 17 HCP balanced
        'expected_min_level': 6,
        'dealer': 'North',
    },
    {
        'id': 'F2',
        'category': 'nt_slam',
        'description': '2NT opener (21) + responder (13) = 34 HCP',
        'north': ('AKJ2', 'KQ3', 'AJ4', 'K32'),      # 21 HCP balanced
        'south': ('Q93', 'A542', 'K52', 'A54'),       # 13 HCP
        'expected_min_level': 6,
        'dealer': 'North',
    },
]


# ---------------------------------------------------------------------------
# Validate all hands at import time
# ---------------------------------------------------------------------------

def _validate_scenarios():
    """Validate that all scenarios have valid card distributions."""
    errors = []
    for s in SLAM_SCENARIOS:
        try:
            north = _hand_from_strings(*s['north'])
            south = _hand_from_strings(*s['south'])
            n_cards = _cards_set(north)
            s_cards = _cards_set(south)
            overlap = n_cards & s_cards
            if overlap:
                errors.append(f"{s['id']}: N/S share cards: {overlap}")
                continue
            east, west = _deal_remaining(north, south)
            total_hcp = north.hcp + south.hcp + east.hcp + west.hcp
            if total_hcp != 40:
                errors.append(f"{s['id']}: Total HCP={total_hcp}, expected 40")
        except Exception as e:
            errors.append(f"{s['id']}: {e}")
    if errors:
        raise ValueError("Slam scenario validation errors:\n" + "\n".join(errors))


_validate_scenarios()


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

class TestSlamDiagnostics:
    """Curated slam hands for ongoing diagnostic tracking."""

    def _run_scenario(self, scenario):
        """Run a single scenario, return results dict."""
        north = _hand_from_strings(*scenario['north'])
        south = _hand_from_strings(*scenario['south'])
        east, west = _deal_remaining(north, south)
        hands = {'North': north, 'South': south, 'East': east, 'West': west}

        dealer = scenario.get('dealer', 'North')
        engine = BiddingEngine()
        auction = _simulate_auction(engine, hands, dealer)

        contract = _final_contract(auction)
        level = _contract_level(auction)
        partnership = _declarer_partnership(auction, dealer)

        return {
            'id': scenario['id'],
            'category': scenario['category'],
            'description': scenario['description'],
            'ns_hcp': north.hcp + south.hcp,
            'ew_hcp': east.hcp + west.hcp,
            'north_hcp': north.hcp,
            'south_hcp': south.hcp,
            'auction': auction,
            'contract': contract,
            'level': level,
            'declarer': partnership,
            'expected_min_level': scenario.get('expected_min_level'),
            'expected_max_level': scenario.get('expected_max_level'),
        }

    # --- Category A: HCP Small Slams ---

    @pytest.mark.parametrize("scenario", [s for s in SLAM_SCENARIOS if s['category'] == 'hcp_small_slam'],
                             ids=[s['id'] for s in SLAM_SCENARIOS if s['category'] == 'hcp_small_slam'])
    def test_hcp_small_slam(self, scenario):
        """Partnership with 33-36 combined HCP should bid small slam."""
        result = self._run_scenario(scenario)
        print(f"\n  {result['id']}: {result['description']}")
        print(f"  N={result['north_hcp']} S={result['south_hcp']} Combined={result['ns_hcp']} HCP")
        print(f"  Auction: {' - '.join(result['auction'])}")
        print(f"  Contract: {result['contract']} (level {result['level']})")

        assert result['declarer'] == 'NS', (
            f"{result['id']}: NS has {result['ns_hcp']} HCP but {result['declarer']} declared"
        )
        assert result['level'] >= 6, (
            f"{result['id']}: NS has {result['ns_hcp']} combined HCP but only reached "
            f"{result['contract']} (level {result['level']}). "
            f"Auction: {' - '.join(result['auction'])}"
        )

    # --- Category B: HCP Grand Slams ---

    @pytest.mark.parametrize("scenario", [s for s in SLAM_SCENARIOS if s['category'] == 'hcp_grand_slam'],
                             ids=[s['id'] for s in SLAM_SCENARIOS if s['category'] == 'hcp_grand_slam'])
    def test_hcp_grand_slam(self, scenario):
        """Partnership with 37+ combined HCP should bid grand slam."""
        result = self._run_scenario(scenario)
        print(f"\n  {result['id']}: {result['description']}")
        print(f"  N={result['north_hcp']} S={result['south_hcp']} Combined={result['ns_hcp']} HCP")
        print(f"  Auction: {' - '.join(result['auction'])}")
        print(f"  Contract: {result['contract']} (level {result['level']})")

        assert result['declarer'] == 'NS', (
            f"{result['id']}: NS has {result['ns_hcp']} HCP but {result['declarer']} declared"
        )
        assert result['level'] >= 7, (
            f"{result['id']}: NS has {result['ns_hcp']} combined HCP but only reached "
            f"{result['contract']} (level {result['level']}). "
            f"Auction: {' - '.join(result['auction'])}"
        )

    # --- Category C: Near-Slam Stops ---

    @pytest.mark.parametrize("scenario", [s for s in SLAM_SCENARIOS if s['category'] == 'near_slam_stop'],
                             ids=[s['id'] for s in SLAM_SCENARIOS if s['category'] == 'near_slam_stop'])
    def test_near_slam_stop(self, scenario):
        """Partnership with 30-32 combined HCP should NOT bid slam."""
        result = self._run_scenario(scenario)
        print(f"\n  {result['id']}: {result['description']}")
        print(f"  N={result['north_hcp']} S={result['south_hcp']} Combined={result['ns_hcp']} HCP")
        print(f"  Auction: {' - '.join(result['auction'])}")
        print(f"  Contract: {result['contract']} (level {result['level']})")

        if result['declarer'] == 'NS':
            assert result['level'] <= 5, (
                f"{result['id']}: NS has only {result['ns_hcp']} combined HCP but bid slam "
                f"{result['contract']}! Auction: {' - '.join(result['auction'])}"
            )

    # --- Category D: Distribution Slams ---

    @pytest.mark.parametrize("scenario", [s for s in SLAM_SCENARIOS if s['category'] == 'distribution_slam'],
                             ids=[s['id'] for s in SLAM_SCENARIOS if s['category'] == 'distribution_slam'])
    def test_distribution_slam(self, scenario):
        """Partnership with fit + distribution should explore slam (aspirational)."""
        result = self._run_scenario(scenario)
        print(f"\n  {result['id']}: {result['description']}")
        print(f"  N={result['north_hcp']} S={result['south_hcp']} Combined={result['ns_hcp']} HCP")
        print(f"  Auction: {' - '.join(result['auction'])}")
        print(f"  Contract: {result['contract']} (level {result['level']})")

        if result['declarer'] == 'NS' and result['level'] >= 6:
            print(f"  PASS: Distribution slam found!")
        else:
            print(f"  MISS: Distribution slam not reached (expected 6+, got {result['level']})")
            pytest.xfail(
                f"Distribution slam {result['id']}: {result['ns_hcp']} HCP + shape, "
                f"reached level {result['level']}"
            )

    # --- Category E: Strong 2C Slams ---

    @pytest.mark.parametrize("scenario", [s for s in SLAM_SCENARIOS if s['category'] == 'strong_2c_slam'],
                             ids=[s['id'] for s in SLAM_SCENARIOS if s['category'] == 'strong_2c_slam'])
    def test_strong_2c_slam(self, scenario):
        """After strong 2C opening with slam values, should reach slam."""
        result = self._run_scenario(scenario)
        print(f"\n  {result['id']}: {result['description']}")
        print(f"  N={result['north_hcp']} S={result['south_hcp']} Combined={result['ns_hcp']} HCP")
        print(f"  Auction: {' - '.join(result['auction'])}")
        print(f"  Contract: {result['contract']} (level {result['level']})")

        assert result['declarer'] == 'NS', (
            f"{result['id']}: NS has {result['ns_hcp']} HCP but {result['declarer']} declared"
        )
        assert result['level'] >= 6, (
            f"{result['id']}: NS has {result['ns_hcp']} combined HCP after 2C opening "
            f"but only reached {result['contract']}. "
            f"Auction: {' - '.join(result['auction'])}"
        )

    # --- Category F: NT Slams ---

    @pytest.mark.parametrize("scenario", [s for s in SLAM_SCENARIOS if s['category'] == 'nt_slam'],
                             ids=[s['id'] for s in SLAM_SCENARIOS if s['category'] == 'nt_slam'])
    def test_nt_slam(self, scenario):
        """Balanced partnership with 33+ HCP should reach slam in NT."""
        result = self._run_scenario(scenario)
        print(f"\n  {result['id']}: {result['description']}")
        print(f"  N={result['north_hcp']} S={result['south_hcp']} Combined={result['ns_hcp']} HCP")
        print(f"  Auction: {' - '.join(result['auction'])}")
        print(f"  Contract: {result['contract']} (level {result['level']})")

        assert result['declarer'] == 'NS', (
            f"{result['id']}: NS has {result['ns_hcp']} HCP but {result['declarer']} declared"
        )
        assert result['level'] >= 6, (
            f"{result['id']}: NS has {result['ns_hcp']} combined HCP balanced "
            f"but only reached {result['contract']}. "
            f"Auction: {' - '.join(result['auction'])}"
        )


# ---------------------------------------------------------------------------
# Standalone diagnostic report
# ---------------------------------------------------------------------------

def run_diagnostic_report():
    """Run all scenarios and print a diagnostic summary."""
    engine = BiddingEngine()

    categories = {}
    all_results = []

    for scenario in SLAM_SCENARIOS:
        north = _hand_from_strings(*scenario['north'])
        south = _hand_from_strings(*scenario['south'])
        east, west = _deal_remaining(north, south)
        hands = {'North': north, 'South': south, 'East': east, 'West': west}

        dealer = scenario.get('dealer', 'North')
        auction = _simulate_auction(engine, hands, dealer)
        contract = _final_contract(auction)
        level = _contract_level(auction)
        partnership = _declarer_partnership(auction, dealer)

        expected_min = scenario.get('expected_min_level')
        expected_max = scenario.get('expected_max_level')

        if expected_min is not None:
            passed = (partnership == 'NS' and level >= expected_min)
            target = f">=  {expected_min}"
        elif expected_max is not None:
            passed = (partnership != 'NS' or level <= expected_max)
            target = f"<= {expected_max}"
        else:
            passed = None
            target = '?'

        result = {
            'id': scenario['id'],
            'category': scenario['category'],
            'description': scenario['description'],
            'ns_hcp': north.hcp + south.hcp,
            'contract': contract or 'Passed Out',
            'level': level,
            'declarer': partnership,
            'target': target,
            'passed': passed,
            'auction': auction,
        }
        all_results.append(result)
        cat = scenario['category']
        if cat not in categories:
            categories[cat] = {'pass': 0, 'fail': 0, 'total': 0}
        categories[cat]['total'] += 1
        if passed:
            categories[cat]['pass'] += 1
        elif passed is False:
            categories[cat]['fail'] += 1

    # Print report
    print("\n" + "=" * 80)
    print("SLAM DIAGNOSTIC REPORT")
    print("=" * 80)

    current_cat = None
    for r in all_results:
        if r['category'] != current_cat:
            current_cat = r['category']
            print(f"\n--- {current_cat.upper().replace('_', ' ')} ---")

        status = 'PASS' if r['passed'] else ('FAIL' if r['passed'] is False else '????')
        marker = '  ' if r['passed'] else '>>'

        print(f"  {marker} [{status}] {r['id']}: {r['description']}")
        print(f"       NS={r['ns_hcp']} HCP | Contract: {r['contract']} | "
              f"Target: {r['target']} | Declarer: {r['declarer']}")
        print(f"       Auction: {' - '.join(r['auction'])}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    total_pass = sum(c['pass'] for c in categories.values())
    total_fail = sum(c['fail'] for c in categories.values())
    total = sum(c['total'] for c in categories.values())

    for cat, counts in categories.items():
        pct = counts['pass'] / counts['total'] * 100 if counts['total'] > 0 else 0
        print(f"  {cat:25s}: {counts['pass']}/{counts['total']} passed ({pct:.0f}%)")

    overall_pct = total_pass / total * 100 if total > 0 else 0
    print(f"\n  {'OVERALL':25s}: {total_pass}/{total} passed ({overall_pct:.0f}%)")
    print(f"  Failures: {total_fail}")
    print("=" * 80)

    return all_results


if __name__ == '__main__':
    run_diagnostic_report()

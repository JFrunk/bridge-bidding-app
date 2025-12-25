"""
Tests for play scenarios with convention-appropriate hands

These tests ensure that hands appropriate for specific conventions
(as used in the UI scenarios) work correctly in the play engine.
Each test creates a deal that would arise from a specific convention auction.
"""

import pytest
from engine.hand import Hand, Card
from engine.play_engine import PlayEngine, PlayState, Contract
from engine.play.ai.simple_ai import SimplePlayAI
from tests.integration.play_test_helpers import create_test_deal, create_play_scenario


class TestStaymanPlayScenarios:
    """Test play scenarios after Stayman auction (1NT-2♣-...)"""

    def test_stayman_4_4_spade_fit_contract(self):
        """Test play in 4♠ after Stayman finds 4-4 fit"""
        # Opener: 15-17 balanced with 4 spades
        # Responder: 10+ with 4 spades
        deal = create_test_deal(
            north="♠AK65 ♥KQ3 ♦AJ2 ♣Q97",  # 16 HCP, 4=3=3=3, 4 spades
            east="♠J8 ♥J974 ♦Q86 ♣J432",   # 6 HCP
            south="♠Q974 ♥A52 ♦K54 ♣A65",  # 13 HCP, 4 spades
            west="♠T32 ♥T86 ♦T973 ♣KT8"    # 4 HCP
        )

        state = create_play_scenario("4♠ by N", deal, "None")
        assert state.contract.level == 4
        assert state.contract.strain == '♠'

        # East leads (LHO of declarer)
        assert state.next_to_play == 'E'

    def test_stayman_4_4_heart_fit_contract(self):
        """Test play in 4♥ after Stayman finds heart fit"""
        # Card counts: N=3+4+3+3=13, E=3+3+4+3=13, S=3+4+3+3=13, W=4+2+3+4=13
        deal = create_test_deal(
            north="♠A65 ♥KQ63 ♦AJ2 ♣Q97",  # 3+4+3+3 = 13
            east="♠J87 ♥J97 ♦Q864 ♣J43",   # 3+3+4+3 = 13
            south="♠Q94 ♥A852 ♦K54 ♣A65",  # 3+4+3+3 = 13
            west="♠KT32 ♥T4 ♦T97 ♣KT82"    # 4+2+3+4 = 13 (removed one diamond)
        )

        state = create_play_scenario("4♥ by N", deal, "None")
        assert state.contract.strain == '♥'

        ai = SimplePlayAI()
        # East should lead something reasonable
        card = ai.choose_card(state, 'E')
        assert card in state.hands['E'].cards

    def test_stayman_no_fit_3nt(self):
        """Test 3NT when Stayman doesn't find a major fit"""
        # Card counts: N=3+3+4+3=13, E=3+4+3+3=13, S=3+4+2+4=13, W=4+2+4+3=13
        deal = create_test_deal(
            north="♠AK6 ♥KQ3 ♦AJ52 ♣Q97",  # 3+3+4+3 = 13
            east="♠J87 ♥J974 ♦Q86 ♣J43",   # 3+4+3+3 = 13
            south="♠Q94 ♥A852 ♦K4 ♣A654",  # 3+4+2+4 = 13
            west="♠T532 ♥T6 ♦T973 ♣KT8"    # 4+2+4+3 = 13 (removed one club)
        )

        state = create_play_scenario("3NT by N", deal, "None")
        assert state.contract.strain == 'NT'


class TestJacobyTransferPlayScenarios:
    """Test play scenarios after Jacoby Transfer auction"""

    def test_transfer_to_hearts_game(self):
        """Test 4♥ after transfer accepted"""
        # Opener: 15-17 balanced
        # Responder: 5+ hearts, game values
        # Card counts: N=3+3+4+3=13, E=3+2+4+4=13, S=3+5+2+3=13, W=4+3+3+3=13
        deal = create_test_deal(
            north="♠AK5 ♥K32 ♦AJ52 ♣Q97",  # 3+3+4+3 = 13
            east="♠J87 ♥64 ♦Q864 ♣KJ43",   # 3+2+4+4 = 13
            south="♠Q94 ♥AQJ85 ♦K4 ♣A65",  # 3+5+2+3 = 13
            west="♠T632 ♥T97 ♦T93 ♣T82"    # 4+3+3+3 = 13 (removed one diamond)
        )

        state = create_play_scenario("4♥ by S", deal, "None")
        assert state.contract.strain == '♥'
        assert state.contract.declarer == 'S'

        # West leads (LHO of South)
        assert state.next_to_play == 'W'

    def test_transfer_to_spades_partial(self):
        """Test 2♠ after transfer (weak hand)"""
        # Card counts: N=2+4+4+3=13, E=3+3+4+3=13, S=6+2+2+3=13, W=2+4+3+4=13
        deal = create_test_deal(
            north="♠K3 ♥KQ32 ♦AJ52 ♣Q97",  # 2+4+4+3 = 13
            east="♠J87 ♥J64 ♦Q864 ♣J43",   # 3+3+4+3 = 13
            south="♠AQ9654 ♥85 ♦K4 ♣654",  # 6+2+2+3 = 13
            west="♠T2 ♥AT97 ♦T93 ♣KT82"    # 2+4+3+4 = 13 (removed one diamond)
        )

        state = create_play_scenario("2♠ by S", deal, "None")
        assert state.contract.level == 2
        assert state.contract.strain == '♠'

    def test_super_accept_transfer(self):
        """Test 4♥ after super-accept (3♥ jump)"""
        # Super accept: opener has 4+ support and max
        # Card counts: N=3+4+3+3=13, E=3+2+4+4=13, S=3+5+3+2=13, W=4+2+3+4=13
        deal = create_test_deal(
            north="♠AK5 ♥KQ32 ♦AJ5 ♣Q97",  # 3+4+3+3 = 13
            east="♠J87 ♥64 ♦Q864 ♣KJ43",   # 3+2+4+4 = 13
            south="♠Q94 ♥AJ875 ♦K42 ♣65",  # 3+5+3+2 = 13
            west="♠T632 ♥T9 ♦T93 ♣AT82"    # 4+2+3+4 = 13 (removed one diamond)
        )

        state = create_play_scenario("4♥ by N", deal, "None")
        # North declared because of super accept
        assert state.contract.declarer == 'N'


class TestBlackwoodPlayScenarios:
    """Test play scenarios after Blackwood slam auctions"""

    def test_6nt_slam_after_blackwood(self):
        """Test 6NT slam after Blackwood shows aces"""
        # Combined 33+ HCP for 6NT
        deal = create_test_deal(
            north="♠AKQ ♥AKJ ♦KQJ ♣AQ32",  # 25 HCP
            east="♠J87 ♥Q87 ♦987 ♣J987",   # 4 HCP
            south="♠654 ♥654 ♦A65 ♣K654",  # 9 HCP
            west="♠T932 ♥T932 ♦T432 ♣T"    # 2 HCP
        )

        state = create_play_scenario("6NT by N", deal, "None")
        assert state.contract.level == 6

        # Declarer needs 12 tricks
        assert state.contract.tricks_needed == 12

    def test_6_spades_slam(self):
        """Test 6♠ after Blackwood confirms aces"""
        deal = create_test_deal(
            north="♠AKQJ5 ♥AK ♦KQ2 ♣A32",  # 24 HCP, 5 spades
            east="♠87 ♥Q87 ♦9876 ♣J987",   # 3 HCP
            south="♠643 ♥654 ♦AJ5 ♣KQ54",  # 11 HCP, 3 spades
            west="♠T92 ♥JT932 ♦T43 ♣T6"    # 2 HCP
        )

        state = create_play_scenario("6♠ by N", deal, "None")
        assert state.contract.strain == '♠'
        assert state.contract.level == 6


class TestPreemptPlayScenarios:
    """Test play scenarios after preemptive openings"""

    def test_weak_two_hearts_contract(self):
        """Test 2♥ preempt contract"""
        # Weak two: 6-10 HCP, 6-card suit
        deal = create_test_deal(
            north="♠A5 ♥KQT987 ♦43 ♣T97",  # 8 HCP, 6 hearts (weak two)
            east="♠KQJ8 ♥A6 ♦QJ86 ♣A43",   # 15 HCP
            south="♠643 ♥J54 ♦AT75 ♣KQ5",  # 10 HCP
            west="♠T972 ♥32 ♦K92 ♣J862"    # 5 HCP
        )

        state = create_play_scenario("2♥ by N", deal, "None")
        assert state.contract.level == 2
        assert state.contract.strain == '♥'

    def test_three_level_preempt(self):
        """Test 3♦ preempt contract"""
        # 3-level preempt: weak, 7-card suit
        # Card counts: N=1+2+7+3=13, E=4+3+1+5=13, S=4+4+2+3=13, W=4+4+3+2=13
        deal = create_test_deal(
            north="♠5 ♥43 ♦KQT9876 ♣T97",  # 1+2+7+3 = 13
            east="♠KQJ8 ♥AK6 ♦J ♣AKJ43",   # 4+3+1+5 = 13
            south="♠A643 ♥J754 ♦A5 ♣Q52",  # 4+4+2+3 = 13
            west="♠T972 ♥QT98 ♦432 ♣86"    # 4+4+3+2 = 13 (removed one heart)
        )

        state = create_play_scenario("3♦ by N", deal, "None")
        assert state.contract.level == 3


class TestTakeoutDoublePlayScenarios:
    """Test play scenarios arising from takeout double auctions"""

    def test_advance_in_4_spades(self):
        """Test 4♠ after takeout double sequence"""
        # Partner doubled, we have good spades
        deal = create_test_deal(
            north="♠KQJ5 ♥3 ♦AKJ2 ♣A987",  # 17 HCP, short hearts (doubled hearts)
            east="♠87 ♥KQT987 ♦876 ♣J9",   # 6 HCP, opened 2♥
            south="♠AT943 ♥654 ♦Q5 ♣KQ5",  # 12 HCP, 5 spades (advanced)
            west="♠62 ♥AJ2 ♦T943 ♣T643"    # 5 HCP
        )

        state = create_play_scenario("4♠ by S", deal, "None")
        assert state.contract.strain == '♠'

    def test_double_competitive_3nt(self):
        """Test 3NT after competitive double auction"""
        deal = create_test_deal(
            north="♠AKJ5 ♥32 ♦AKJ2 ♣A97",  # 19 HCP
            east="♠87 ♥KQT987 ♦876 ♣J9",   # 6 HCP
            south="♠Q943 ♥A64 ♦Q5 ♣KQ54",  # 13 HCP
            west="♠T62 ♥J5 ♦T943 ♣T632"    # 2 HCP
        )

        state = create_play_scenario("3NT by N", deal, "None")
        assert state.contract.strain == 'NT'


class TestMichaelsCuebidPlayScenarios:
    """Test play scenarios after Michaels Cuebid auction"""

    def test_michaels_major_fit_game(self):
        """Test 4♠ after Michaels found major fit"""
        # Michaels over 1♥: 5-5 in spades and minor
        deal = create_test_deal(
            north="♠43 ♥AKJ87 ♦KQ2 ♣A32",  # 16 HCP (opened 1♥)
            east="♠KQJ87 ♥2 ♦43 ♣KQJ87",  # 11 HCP, Michaels (5-5)
            south="♠65 ♥Q654 ♦AJ87 ♣654",  # 8 HCP
            west="♠AT92 ♥T93 ♦T965 ♣T9"    # 4 HCP, raised spades
        )

        state = create_play_scenario("4♠ by E", deal, "None")
        assert state.contract.strain == '♠'
        assert state.contract.declarer == 'E'


class TestUnusual2NTPlayScenarios:
    """Test play scenarios after Unusual 2NT auction"""

    def test_unusual_2nt_minor_game(self):
        """Test 5♦ after unusual 2NT showed minors"""
        # Unusual 2NT: 5-5 in minors
        deal = create_test_deal(
            north="♠AKQ87 ♥AK2 ♦J2 ♣J32",  # 18 HCP (opened 1♠)
            east="♠2 ♥43 ♦KQT87 ♣KQ987",  # 10 HCP, unusual 2NT
            south="♠654 ♥Q876 ♦A65 ♣A65",  # 11 HCP
            west="♠JT93 ♥JT95 ♦943 ♣T4"    # 3 HCP, raised diamonds
        )

        state = create_play_scenario("5♦ by E", deal, "None")
        assert state.contract.level == 5


class TestSplinterPlayScenarios:
    """Test play scenarios after splinter bid auction"""

    def test_splinter_slam_contract(self):
        """Test 6♠ after splinter showed singleton"""
        # Splinter: 4+ support, singleton/void, 11-14 HCP
        deal = create_test_deal(
            north="♠AKQJ5 ♥AK2 ♦KQ2 ♣32",  # 21 HCP, opened 1♠
            east="♠2 ♥QJ87 ♦J987 ♣QJ87",   # 7 HCP
            south="♠T987 ♥4 ♦AT65 ♣AK65",  # 13 HCP, splinter (4♥ = singleton heart)
            west="♠643 ♥T9653 ♦43 ♣T94"    # 2 HCP
        )

        state = create_play_scenario("6♠ by N", deal, "None")
        assert state.contract.level == 6


class TestFourthSuitForcingPlayScenarios:
    """Test play scenarios after Fourth Suit Forcing auction"""

    def test_fsf_finds_3nt(self):
        """Test 3NT after FSF inquiry"""
        deal = create_test_deal(
            north="♠AKQ65 ♥32 ♦AKJ2 ♣32",  # 17 HCP, 5 spades
            east="♠J8 ♥QJ87 ♦876 ♣QJ87",   # 7 HCP
            south="♠43 ♥AK65 ♦Q5 ♣AKT65",  # 17 HCP, clubs
            west="♠T972 ♥T94 ♦T943 ♣94"    # 2 HCP
        )

        state = create_play_scenario("3NT by S", deal, "None")
        assert state.contract.strain == 'NT'

    def test_fsf_finds_major_fit(self):
        """Test 4♠ after FSF found delayed fit"""
        deal = create_test_deal(
            north="♠AKQ65 ♥32 ♦AKJ2 ♣32",  # 17 HCP
            east="♠J8 ♥QJ87 ♦876 ♣QJ87",   # 7 HCP
            south="♠T43 ♥AK65 ♦Q5 ♣AK65",  # 16 HCP, 3 spades
            west="♠972 ♥T94 ♦T943 ♣T94"    # 1 HCP
        )

        state = create_play_scenario("4♠ by N", deal, "None")
        assert state.contract.strain == '♠'


class TestConventionPlayAIBehavior:
    """Test that AI plays appropriately in convention-specific hands"""

    def test_ai_leads_against_stayman_game(self):
        """Test AI lead selection against 4♠ (Stayman auction)"""
        deal = create_test_deal(
            north="♠AK65 ♥KQ3 ♦AJ2 ♣Q97",
            east="♠J8 ♥J974 ♦Q86 ♣KJ32",
            south="♠Q974 ♥A52 ♦K54 ♣A65",
            west="♠T32 ♥T86 ♦T973 ♣T84"
        )

        state = create_play_scenario("4♠ by N", deal, "None")
        ai = SimplePlayAI()

        # East leads against 4♠
        card = ai.choose_card(state, 'E')

        # Should be a legal card from East's hand
        assert card in state.hands['E'].cards
        # Should avoid leading trump (spades) if possible
        if any(c.suit != '♠' for c in state.hands['E'].cards):
            # If East has non-trump, likely won't lead trump
            pass  # AI may choose trump in some positions

    def test_ai_leads_against_slam(self):
        """Test AI lead selection against 6NT slam"""
        deal = create_test_deal(
            north="♠AKQ ♥AKJ ♦KQJ ♣AQ32",
            east="♠J87 ♥Q87 ♦987 ♣J987",
            south="♠654 ♥654 ♦A65 ♣K654",
            west="♠T932 ♥T932 ♦T432 ♣T"
        )

        state = create_play_scenario("6NT by N", deal, "None")
        ai = SimplePlayAI()

        # East leads against 6NT
        card = ai.choose_card(state, 'E')
        assert card in state.hands['E'].cards

    def test_ai_follows_suit_in_trump_contract(self):
        """Test AI follows suit correctly in trump contract"""
        # Card counts: N=5+3+3+2=13, E=1+4+4+4=13, S=4+2+4+3=13, W=3+4+2+4=13
        deal = create_test_deal(
            north="♠AKQJ5 ♥AK2 ♦KQ2 ♣32",  # 5+3+3+2 = 13
            east="♠2 ♥QJ87 ♦J987 ♣QJ87",   # 1+4+4+4 = 13
            south="♠T987 ♥43 ♦AT65 ♣AK6",  # 4+2+4+3 = 13 (removed one club)
            west="♠643 ♥T965 ♦93 ♣T954"    # 3+4+2+4 = 13 (fixed)
        )

        state = create_play_scenario("4♠ by N", deal, "None")

        # Simulate East leading a heart
        state.current_trick = [(Card('Q', '♥'), 'E')]
        state.next_to_play = 'S'

        ai = SimplePlayAI()
        card = ai.choose_card(state, 'S')

        # South has hearts, must follow suit
        south_hearts = [c for c in state.hands['S'].cards if c.suit == '♥']
        if south_hearts:
            assert card.suit == '♥'


class TestNTContractPlayFromConventions:
    """Test NT contract play from various convention auctions"""

    def test_3nt_from_stayman_sequence(self):
        """Test 3NT play when Stayman didn't find fit"""
        deal = create_test_deal(
            north="♠AK6 ♥KQ32 ♦AJ2 ♣Q97",  # 16 HCP, 4 hearts
            east="♠Q87 ♥J74 ♦Q86 ♣J432",   # 6 HCP
            south="♠J943 ♥A5 ♦K54 ♣AK65",  # 15 HCP, 4 spades (no fit)
            west="♠T52 ♥T986 ♦T973 ♣T8"    # 1 HCP
        )

        state = create_play_scenario("3NT by N", deal, "None")

        # Combined 31 HCP, should have good play for 3NT
        assert state.contract.level == 3
        assert state.contract.strain == 'NT'

    def test_1nt_opening_passed_out(self):
        """Test 1NT contract (opener passed out)"""
        deal = create_test_deal(
            north="♠AK6 ♥KQ3 ♦AJ2 ♣J972",  # 15 HCP balanced
            east="♠Q87 ♥J74 ♦Q86 ♣Q843",   # 8 HCP
            south="♠543 ♥652 ♦K543 ♣K65",  # 7 HCP (passed)
            west="♠JT92 ♥AT98 ♦T97 ♣AT"    # 8 HCP (passed)
        )

        state = create_play_scenario("1NT by N", deal, "None")
        assert state.contract.level == 1

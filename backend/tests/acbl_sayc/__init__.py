"""
ACBL SAYC Test Suite

This test suite contains canonical test cases derived from the ACBL Standard American
Yellow Card (SAYC) booklet. These tests serve as the authoritative reference for
correct bidding behavior according to SAYC conventions.

Test Organization:
- test_opening_bids.py: Opening bid requirements and hand evaluation
- test_responses.py: Responses to partner's opening bids
- test_rebids.py: Opener's and responder's rebids
- test_notrump.py: 1NT/2NT openings, responses, and conventions
- test_slam_bidding.py: Blackwood, control bids, and slam decisions
- test_competitive.py: Overcalls, doubles, and competitive situations

Each test case includes:
- Source reference to SAYC booklet section
- Clear hand description
- Expected bid with explanation
- Alternative acceptable bids where applicable

Usage:
    pytest backend/tests/acbl_sayc/ -v
    pytest backend/tests/acbl_sayc/test_opening_bids.py -v

These tests are considered CANONICAL - any failure indicates a potential
regression in bidding logic that must be investigated.
"""

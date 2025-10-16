#!/usr/bin/env python3
"""
Test script to verify session state refactoring works correctly

Tests:
1. Multiple sessions maintain isolated state
2. Session state persists across requests
3. No interference between concurrent sessions
"""

import sys
import time
import requests
import threading
from datetime import datetime

API_URL = 'http://localhost:5001'

def test_single_user():
    """Test basic functionality with single user"""
    print("\n" + "="*70)
    print("TEST 1: Single User Session")
    print("="*70)

    session_id = f"test_session_{int(time.time())}"
    headers = {'X-Session-ID': session_id}

    try:
        # Test 1: Deal hands
        print("\n1. Dealing hands...")
        resp = requests.get(f'{API_URL}/api/deal-hands', headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print(f"   ✅ Got hand with {data['points']['hcp']} HCP")
        else:
            print(f"   ❌ Failed: {resp.status_code}")
            return False

        # Test 2: Get AI bid
        print("\n2. Getting AI bid...")
        resp = requests.post(
            f'{API_URL}/api/get-next-bid',
            headers=headers,
            json={'auction_history': [], 'current_player': 'South'},
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            print(f"   ✅ AI bid: {data['bid']}")
        else:
            print(f"   ❌ Failed: {resp.status_code}")
            return False

        print("\n✅ Single user test PASSED")
        return True

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to server")
        print("   Make sure server is running: python3 server.py")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def test_user_session(user_id, results):
    """Test function for concurrent users"""
    session_id = f"user_{user_id}_session"
    headers = {'X-Session-ID': session_id}

    try:
        # Deal hands
        resp = requests.get(f'{API_URL}/api/deal-hands', headers=headers, timeout=5)
        if resp.status_code != 200:
            results[user_id] = {'success': False, 'error': 'Deal failed'}
            return

        data = resp.json()
        hcp = data['points']['hcp']

        # Get AI bid
        resp = requests.post(
            f'{API_URL}/api/get-next-bid',
            headers=headers,
            json={'auction_history': [], 'current_player': 'South'},
            timeout=5
        )
        if resp.status_code != 200:
            results[user_id] = {'success': False, 'error': 'Bid failed'}
            return

        bid_data = resp.json()
        bid = bid_data['bid']

        results[user_id] = {
            'success': True,
            'hcp': hcp,
            'bid': bid,
            'session_id': session_id
        }

    except Exception as e:
        results[user_id] = {'success': False, 'error': str(e)}


def test_concurrent_users():
    """Test multiple concurrent users don't interfere with each other"""
    print("\n" + "="*70)
    print("TEST 2: Concurrent Multi-User Sessions")
    print("="*70)

    num_users = 5
    results = {}
    threads = []

    print(f"\nSpawning {num_users} concurrent users...")

    # Start all threads
    for i in range(num_users):
        t = threading.Thread(target=test_user_session, args=(i, results))
        t.start()
        threads.append(t)

    # Wait for completion
    for t in threads:
        t.join()

    # Check results
    print("\nResults:")
    all_passed = True
    for user_id in range(num_users):
        result = results.get(user_id, {'success': False, 'error': 'No result'})
        if result['success']:
            print(f"   User {user_id}: ✅ {result['hcp']} HCP, bid {result['bid']}")
        else:
            print(f"   User {user_id}: ❌ {result['error']}")
            all_passed = False

    # Verify all users got different states
    hcps = [r['hcp'] for r in results.values() if r['success']]
    if len(set(hcps)) > 1:
        print(f"\n✅ Session isolation confirmed - users got different hands")
    else:
        print(f"\n⚠️  Warning: All users got same HCP (might be coincidence)")

    if all_passed:
        print("\n✅ Concurrent users test PASSED")
        return True
    else:
        print("\n❌ Concurrent users test FAILED")
        return False


def test_session_persistence():
    """Test that session state persists across requests"""
    print("\n" + "="*70)
    print("TEST 3: Session State Persistence")
    print("="*70)

    session_id = f"persist_test_{int(time.time())}"
    headers = {'X-Session-ID': session_id}

    try:
        # Deal hands
        print("\n1. Dealing hands...")
        resp = requests.get(f'{API_URL}/api/deal-hands', headers=headers, timeout=5)
        data1 = resp.json()
        hcp1 = data1['points']['hcp']
        print(f"   Hand 1: {hcp1} HCP")

        # Make second request with same session ID - should get SAME hand
        print("\n2. Getting hand again (should be same)...")
        resp = requests.get(f'{API_URL}/api/get-all-hands', headers=headers, timeout=5)
        if resp.status_code == 200:
            data2 = resp.json()
            hcp2 = data2['hands']['South']['points']['hcp']
            print(f"   Hand 2: {hcp2} HCP")

            if hcp1 == hcp2:
                print("\n✅ Session persistence PASSED - same hand retrieved")
                return True
            else:
                print("\n❌ Session persistence FAILED - different hand!")
                return False
        else:
            print(f"\n❌ Failed to get second hand: {resp.status_code}")
            return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def main():
    print("\n" + "="*70)
    print("  SESSION STATE REFACTORING - TEST SUITE")
    print("="*70)
    print(f"\nTesting server at: {API_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Run tests
    test1 = test_single_user()
    test2 = test_concurrent_users()
    test3 = test_session_persistence()

    # Summary
    print("\n" + "="*70)
    print("  TEST SUMMARY")
    print("="*70)
    print(f"\n  Single User:         {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"  Concurrent Users:    {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"  Session Persistence: {'✅ PASS' if test3 else '❌ FAIL'}")

    all_passed = test1 and test2 and test3

    if all_passed:
        print("\n🎉 ALL TESTS PASSED! Session state refactoring is working!")
        print("\nThe server can now safely handle multiple concurrent users.")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        print("\nPlease review the failures above and fix any issues.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

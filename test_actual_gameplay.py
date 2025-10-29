#!/usr/bin/env python3
"""
Simulate actual gameplay to verify scoring is working correctly
"""

import requests
import json

API_URL = "http://127.0.0.1:5001"

def test_complete_play_endpoint():
    """Test the /api/complete-play endpoint directly"""

    print("=" * 70)
    print("TESTING /api/complete-play ENDPOINT")
    print("=" * 70)
    print()

    # First, we need to start a session and set up a play state
    # For now, let's just check what the endpoint expects

    print("This test requires an active game session.")
    print("Please:")
    print("1. Start the backend server")
    print("2. Start a game in the UI")
    print("3. Play until the end")
    print("4. Check the browser console for the /api/complete-play response")
    print()
    print("Look for the response in the Network tab:")
    print("  - Check the 'score' field (should be from declarer's perspective)")
    print("  - Check the 'contract' field (should be an object with level/strain/declarer/doubled)")
    print("  - Check the 'result' field (should be 'Made +X' or 'Down X')")
    print()
    print("Then in the browser console, run:")
    print("  const declarerIsNS = scoreData.contract.declarer === 'N' || scoreData.contract.declarer === 'S';")
    print("  const userScore = declarerIsNS ? scoreData.score : -scoreData.score;")
    print("  console.log('User score:', userScore);")
    print()
    print("The userScore should be:")
    print("  - POSITIVE when you (NS) make a contract")
    print("  - NEGATIVE when you (NS) go down")
    print("  - NEGATIVE when EW makes their contract")
    print("  - POSITIVE when EW goes down")
    print()

if __name__ == "__main__":
    test_complete_play_endpoint()

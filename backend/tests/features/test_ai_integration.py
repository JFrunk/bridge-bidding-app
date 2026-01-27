"""
Test script for Phase 2 AI integration

Tests the new AI difficulty endpoints
"""

import requests
import json

BASE_URL = "http://localhost:5001/api"

def test_get_difficulties():
    """Test GET /api/ai-difficulties"""
    print("\n=== Test: Get AI Difficulties ===")
    response = requests.get(f"{BASE_URL}/ai-difficulties")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Current difficulty: {data['current']}")
    print(f"Available difficulties:")
    for diff in data['difficulties']:
        print(f"  - {diff['id']}: {diff['description']} (Level: {diff['level']})")
    return response.status_code == 200

def _test_set_difficulty(difficulty):
    """Test POST /api/set-ai-difficulty"""
    print(f"\n=== Test: Set AI Difficulty to '{difficulty}' ===")
    response = requests.post(
        f"{BASE_URL}/set-ai-difficulty",
        json={"difficulty": difficulty}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"AI Name: {data.get('ai_name')}")
        print(f"AI Level: {data.get('ai_level')}")
    else:
        print(f"Error: {response.json()}")
    return response.status_code == 200

def test_get_statistics():
    """Test GET /api/ai-statistics"""
    print("\n=== Test: Get AI Statistics ===")
    response = requests.get(f"{BASE_URL}/ai-statistics")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"AI Name: {data.get('ai_name')}")
    print(f"Difficulty: {data.get('difficulty')}")
    print(f"Has Statistics: {data.get('has_statistics')}")
    if data.get('has_statistics'):
        stats = data.get('statistics', {})
        print(f"Statistics:")
        for key, value in stats.items():
            print(f"  - {key}: {value}")
    return response.status_code == 200

def test_invalid_difficulty():
    """Test setting invalid difficulty"""
    print("\n=== Test: Set Invalid Difficulty ===")
    response = requests.post(
        f"{BASE_URL}/set-ai-difficulty",
        json={"difficulty": "impossible"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 400

def main():
    """Run all tests"""
    print("=" * 60)
    print("Phase 2 AI Integration Tests")
    print("=" * 60)
    print("\nMake sure the server is running on http://localhost:5001")
    print("Start with: cd backend && source venv/bin/activate && python server.py")

    input("\nPress Enter to start tests...")

    tests = [
        ("Get AI Difficulties", test_get_difficulties),
        ("Set Difficulty to 'beginner'", lambda: _test_set_difficulty("beginner")),
        ("Get Statistics (beginner - no stats)", test_get_statistics),
        ("Set Difficulty to 'advanced'", lambda: _test_set_difficulty("advanced")),
        ("Get Statistics (advanced - has stats)", test_get_statistics),
        ("Set Difficulty to 'expert'", lambda: _test_set_difficulty("expert")),
        ("Set Invalid Difficulty", test_invalid_difficulty),
        ("Set Difficulty back to 'advanced'", lambda: _test_set_difficulty("advanced")),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, "PASS" if success else "FAIL"))
        except requests.exceptions.ConnectionError:
            print(f"\nERROR: Cannot connect to server at {BASE_URL}")
            print("Make sure the server is running!")
            return
        except Exception as e:
            print(f"\nERROR: {e}")
            results.append((name, "ERROR"))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for name, result in results:
        status = "✓" if result == "PASS" else "✗"
        print(f"{status} {name}: {result}")

    passed = sum(1 for _, r in results if r == "PASS")
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")

if __name__ == "__main__":
    main()

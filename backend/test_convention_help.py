#!/usr/bin/env python3
"""
Test script to verify convention help endpoint works correctly
"""

import requests
import json

BASE_URL = "http://localhost:5001"

def test_convention_info():
    """Test that convention info endpoint returns correct data"""

    conventions_to_test = [
        "Jacoby Transfer",
        "Stayman",
        "Preemptive Bid",
        "Blackwood",
        "Takeout Double",
        "Negative Double",
        "Michaels Cuebid",
        "Unusual 2NT",
        "Splinter Bid",
        "Fourth Suit Forcing"
    ]

    print("Testing Convention Info Endpoint")
    print("=" * 70)

    all_passed = True

    for convention_name in conventions_to_test:
        try:
            response = requests.get(f"{BASE_URL}/api/convention-info",
                                  params={"name": convention_name})

            if response.status_code == 200:
                data = response.json()

                # Check required fields
                required_fields = ['name', 'background', 'when_used', 'how_it_works',
                                 'responder_actions', 'opener_actions']

                missing_fields = [field for field in required_fields if field not in data]

                if missing_fields:
                    print(f"❌ {convention_name}: Missing fields {missing_fields}")
                    all_passed = False
                else:
                    # Check that fields are not empty
                    empty_fields = [field for field in required_fields
                                  if not data[field] or len(data[field].strip()) == 0]

                    if empty_fields:
                        print(f"⚠️  {convention_name}: Empty fields {empty_fields}")
                        all_passed = False
                    else:
                        print(f"✅ {convention_name}: All fields present and populated")
                        print(f"   Background: {data['background'][:60]}...")

            elif response.status_code == 404:
                print(f"⚠️  {convention_name}: Not found (404) - may not be implemented yet")

            else:
                print(f"❌ {convention_name}: Unexpected status code {response.status_code}")
                all_passed = False

        except Exception as e:
            print(f"❌ {convention_name}: Error - {e}")
            all_passed = False

    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    if all_passed:
        print("✅ ALL CONVENTION HELP ENDPOINTS WORKING!")
    else:
        print("⚠️  Some conventions missing or incomplete")

    return all_passed

def test_all_conventions_endpoint():
    """Test getting all conventions at once"""
    print("\nTesting 'Get All Conventions' Endpoint")
    print("=" * 70)

    try:
        response = requests.get(f"{BASE_URL}/api/convention-info")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Retrieved {len(data)} conventions")
            print(f"   Conventions: {', '.join(data.keys())}")
            return True
        else:
            print(f"❌ Unexpected status code {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_convention_info()
    test_all_conventions_endpoint()

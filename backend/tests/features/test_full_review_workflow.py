#!/usr/bin/env python3
"""
Test the full AI Review workflow to verify:
1. The backend API works correctly on Render
2. The frontend would generate a complete prompt with all necessary context
3. The prompt can be used by Claude Code to analyze the hand
"""
import requests
import json

def test_workflow(base_url, environment_name):
    print(f"\n{'='*80}")
    print(f"Testing AI Review Workflow on {environment_name}")
    print(f"Base URL: {base_url}")
    print(f"{'='*80}\n")

    # Step 1: Deal hands
    print("1. Dealing hands...")
    response = requests.get(f"{base_url}/api/deal-hands")
    if response.status_code != 200:
        print(f"   ❌ Failed: {response.status_code}")
        return False
    print(f"   ✅ Success")

    # Step 2: Simulate an auction
    print("\n2. Simulating auction...")
    auction = []
    players = ["North", "East", "South", "West"]

    for i in range(6):  # Get 6 bids
        current_player = players[i % 4]
        bid_response = requests.post(
            f"{base_url}/api/get-next-bid",
            json={
                "auction_history": [a["bid"] for a in auction],
                "current_player": current_player
            }
        )

        if bid_response.status_code == 200:
            bid_data = bid_response.json()
            auction.append({"bid": bid_data["bid"], "explanation": bid_data["explanation"]})
            print(f"   {current_player}: {bid_data['bid']}")
        else:
            print(f"   ❌ Failed to get {current_player}'s bid")
            return False

    # Step 3: Request review with a user concern
    print("\n3. Requesting AI review...")
    user_concern = "I'm not sure if South's bid was correct given the vulnerability"

    review_response = requests.post(
        f"{base_url}/api/request-review",
        json={
            "auction_history": auction,
            "user_concern": user_concern
        }
    )

    if review_response.status_code != 200:
        print(f"   ❌ Failed: {review_response.status_code}")
        print(f"   Response: {review_response.text}")
        return False

    review_data = review_response.json()
    print(f"   ✅ Success")
    print(f"   Filename: {review_data['filename']}")
    print(f"   Saved to file: {review_data['saved_to_file']}")

    # Step 4: Simulate what the frontend would do
    print("\n4. Simulating frontend prompt generation...")

    if review_data['saved_to_file']:
        # Frontend would create this prompt (file reference)
        prompt = f"""Please analyze the bidding in backend/review_requests/{review_data['filename']} and identify any errors or questionable bids according to SAYC.{f'''

I'm particularly concerned about: {user_concern}''' if user_concern else ''}"""
        print(f"   📁 File-based prompt (expects file to exist)")

    else:
        # Frontend would create this prompt (full data embedded)
        rd = review_data['review_data']
        prompt = f"""Please analyze this bridge hand and identify any errors or questionable bids according to SAYC.

**Hand Data:**
{json.dumps(rd, indent=2)}

{f'''
**User's Concern:** {user_concern}''' if user_concern else ''}

Please provide a detailed analysis of the auction and identify any bidding errors."""
        print(f"   📋 Data-embedded prompt (all context included)")

    # Step 5: Verify the prompt has all necessary information
    print("\n5. Verifying prompt completeness...")

    checks = []

    # Check 1: User concern is present
    if user_concern and user_concern in prompt:
        checks.append(("✅", "User concern included"))
    elif user_concern:
        checks.append(("❌", f"User concern missing! Expected: '{user_concern}'"))
    else:
        checks.append(("✅", "No user concern to include"))

    # Check 2: If not file-based, verify full data is in prompt
    if not review_data['saved_to_file']:
        rd = review_data['review_data']

        # Should have all hands
        if 'all_hands' in json.dumps(rd):
            checks.append(("✅", "Hand data included"))
        else:
            checks.append(("❌", "Hand data missing"))

        # Should have vulnerability
        if rd.get('vulnerability') and rd['vulnerability'] in prompt:
            checks.append(("✅", f"Vulnerability ({rd['vulnerability']}) included"))
        else:
            checks.append(("❌", "Vulnerability missing"))

        # Should have auction
        if rd.get('auction'):
            checks.append(("✅", f"Auction ({len(rd['auction'])} bids) included"))
        else:
            checks.append(("❌", "Auction missing"))

        # Should have all 4 positions
        for position in ['North', 'East', 'South', 'West']:
            if position in json.dumps(rd.get('all_hands', {})):
                checks.append(("✅", f"{position}'s hand included"))
            else:
                checks.append(("❌", f"{position}'s hand missing"))

    else:
        # File-based: just verify the file reference is there
        if review_data['filename'] in prompt:
            checks.append(("✅", f"File reference included"))
        else:
            checks.append(("❌", "File reference missing"))

    # Print all checks
    for status, message in checks:
        print(f"   {status} {message}")

    # Step 6: Summary
    print("\n6. Summary...")
    all_passed = all(status == "✅" for status, _ in checks)

    if all_passed:
        print(f"   ✅ All checks passed!")
    else:
        print(f"   ❌ Some checks failed")
        return False

    print(f"\n7. Generated Prompt Preview:")
    print(f"   {'─'*76}")
    if len(prompt) <= 500:
        print(f"   {prompt}")
    else:
        print(f"   {prompt[:500]}")
        print(f"   ... ({len(prompt) - 500} more characters)")
    print(f"   {'─'*76}")

    print(f"\n   📊 Prompt Statistics:")
    print(f"      - Total length: {len(prompt)} characters")
    print(f"      - Auction bids: {len(auction)}")
    print(f"      - Mode: {'File reference' if review_data['saved_to_file'] else 'Embedded data'}")

    # Save to file for inspection
    output_file = f"/tmp/{environment_name.lower().replace(' ', '_')}_review_prompt.txt"
    with open(output_file, 'w') as f:
        f.write(f"Environment: {environment_name}\n")
        f.write(f"Base URL: {base_url}\n")
        f.write(f"Saved to file: {review_data['saved_to_file']}\n")
        f.write(f"{'='*80}\n\n")
        f.write(prompt)
    print(f"\n   💾 Full prompt saved to: {output_file}")

    return True

if __name__ == "__main__":
    print("\n" + "="*80)
    print("AI REVIEW FEATURE - COMPREHENSIVE WORKFLOW TEST")
    print("="*80)

    # Test both local and Render
    environments = [
        ("Local", "http://localhost:5001"),
        ("Render", "https://bridge-bidding-api.onrender.com"),
    ]

    results = {}
    for env_name, base_url in environments:
        try:
            results[env_name] = test_workflow(base_url, env_name)
        except Exception as e:
            print(f"\n❌ {env_name} test failed with error: {e}")
            import traceback
            traceback.print_exc()
            results[env_name] = False

    # Final summary
    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)
    for env_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{env_name}: {status}")
    print("="*80 + "\n")

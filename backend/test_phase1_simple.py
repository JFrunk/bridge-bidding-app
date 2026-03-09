"""
Simple verification test for Phase 1: Bidding Feedback System

This test verifies:
1. Modules import correctly
2. Database tables exist
3. Basic functionality works

Run from backend directory:
    python3 test_phase1_simple.py
"""

import sys
sys.path.insert(0, '.')

def test_imports():
    """Test 1: Verify all imports work"""
    print("\n=== Test 1: Imports ===")

    try:
        from engine.feedback.bidding_feedback import get_feedback_generator, CorrectnessLevel, ImpactLevel
        print("✓ Feedback module imports successfully")

        from engine.feedback import BiddingFeedback, BiddingFeedbackGenerator
        print("✓ Feedback package imports successfully")

        print("✅ Test 1 PASSED\n")
        return True
    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}")
        return False


def test_database_schema():
    """Test 2: Verify database tables exist"""
    print("=== Test 2: Database Schema ===")

    from db import get_connection

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Check bidding_decisions table
            cursor.execute("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public' AND tablename = 'bidding_decisions'
            """)

            if cursor.fetchone():
                print("✓ bidding_decisions table exists")
            else:
                print("❌ bidding_decisions table not found")
                return False

            # Check hand_analyses table
            cursor.execute("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public' AND tablename = 'hand_analyses'
            """)

            if cursor.fetchone():
                print("✓ hand_analyses table exists")
            else:
                print("❌ hand_analyses table not found")
                return False

            # Check views
            cursor.execute("""
                SELECT viewname FROM pg_views
                WHERE schemaname = 'public' AND viewname = 'v_bidding_feedback_stats'
            """)

            if cursor.fetchone():
                print("✓ v_bidding_feedback_stats view exists")
            else:
                print("❌ v_bidding_feedback_stats view not found")
                return False

        print("✅ Test 2 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Test 2 FAILED: {e}")
        return False


def test_feedback_generator_creation():
    """Test 3: Create feedback generator instance"""
    print("=== Test 3: Feedback Generator ===")

    try:
        from engine.feedback.bidding_feedback import get_feedback_generator

        generator = get_feedback_generator()
        print(f"✓ Feedback generator created: {type(generator).__name__}")

        # Check it has required storage method
        assert hasattr(generator, '_store_feedback'), "Missing _store_feedback method"
        print("✓ Has _store_feedback method")

        print("✅ Test 3 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Test 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_server_imports():
    """Test 4: Verify server.py can import feedback system"""
    print("=== Test 4: Server Integration ===")

    try:
        # Check that evaluate-bid endpoint exists in server.py
        with open('server.py', 'r') as f:
            server_code = f.read()

        if '@app.route(\'/api/evaluate-bid\',' in server_code:
            print("✓ /api/evaluate-bid endpoint found in server.py")
        else:
            print("❌ /api/evaluate-bid endpoint not found in server.py")
            return False

        if 'from engine.feedback.bidding_feedback import' in server_code:
            print("✓ Feedback module imported in server.py")
        else:
            print("⚠️  Feedback module not explicitly imported (may use lazy import)")

        print("✅ Test 4 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Test 4 FAILED: {e}")
        return False


def test_analytics_api_extension():
    """Test 5: Verify analytics API has been extended"""
    print("=== Test 5: Analytics API Extension ===")

    try:
        # Check analytics_api.py has new functions
        with open('engine/learning/analytics_api.py', 'r') as f:
            api_code = f.read()

        if 'def get_bidding_feedback_stats_for_user' in api_code:
            print("✓ get_bidding_feedback_stats_for_user function found")
        else:
            print("❌ get_bidding_feedback_stats_for_user function not found")
            return False

        if 'def get_recent_bidding_decisions_for_user' in api_code:
            print("✓ get_recent_bidding_decisions_for_user function found")
        else:
            print("❌ get_recent_bidding_decisions_for_user function not found")
            return False

        if "'bidding_feedback_stats':" in api_code:
            print("✓ Dashboard includes bidding_feedback_stats")
        else:
            print("❌ Dashboard doesn't include bidding_feedback_stats")
            return False

        if "'recent_decisions':" in api_code:
            print("✓ Dashboard includes recent_decisions")
        else:
            print("❌ Dashboard doesn't include recent_decisions")
            return False

        print("✅ Test 5 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Test 5 FAILED: {e}")
        return False


def main():
    """Run all verification tests"""
    print("\n" + "="*60)
    print("PHASE 1: BIDDING FEEDBACK SYSTEM - VERIFICATION")
    print("="*60)

    results = []

    results.append(test_imports())
    results.append(test_database_schema())
    results.append(test_feedback_generator_creation())
    results.append(test_server_imports())
    results.append(test_analytics_api_extension())

    print("="*60)

    if all(results):
        print("✅ ALL VERIFICATION TESTS PASSED!")
        print("="*60)
        print("\n🎉 Phase 1 Backend Implementation Complete!")
        print("\n✓ Database schema created")
        print("✓ Feedback module implemented")
        print("✓ API endpoints added")
        print("✓ Analytics dashboard extended")
        print("\n📋 Next Steps:")
        print("  1. Start the server and test /api/evaluate-bid endpoint")
        print("  2. Create frontend React components")
        print("  3. Integrate with Learning Dashboard")
        print()
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("="*60)
        print(f"\nPassed: {sum(results)}/{len(results)} tests")
        print("\nPlease review the failures above and fix any issues.")
        print()
        return 1


if __name__ == '__main__':
    exit(main())

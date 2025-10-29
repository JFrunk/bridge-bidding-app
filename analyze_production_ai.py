#!/usr/bin/env python3
"""
Production AI DDS Analysis Tool
Analyzes AI bidding and play performance from production database
"""
import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import sys

def analyze_ai_play_performance(db_path='backend/bridge.db'):
    """Analyze AI play performance from production logs"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("=" * 80)
    print("AI PLAY PERFORMANCE ANALYSIS (DDS)")
    print("=" * 80)
    print()

    # Overall statistics
    cursor.execute("""
        SELECT
            COUNT(*) as total_plays,
            COUNT(DISTINCT session_id) as unique_sessions,
            COUNT(DISTINCT date(timestamp)) as days_active,
            MIN(timestamp) as first_play,
            MAX(timestamp) as last_play
        FROM ai_play_log
    """)

    overall = cursor.fetchone()
    if overall['total_plays'] == 0:
        print("No AI play data found in production database.")
        conn.close()
        return

    print(f"Total AI plays logged: {overall['total_plays']}")
    print(f"Unique sessions: {overall['unique_sessions']}")
    print(f"Days active: {overall['days_active']}")
    print(f"Date range: {overall['first_play']} to {overall['last_play']}")
    print()

    # Performance by AI level
    print("=" * 80)
    print("PERFORMANCE BY AI LEVEL")
    print("=" * 80)
    print()

    cursor.execute("""
        SELECT
            ai_level,
            COUNT(*) as play_count,
            AVG(solve_time_ms) as avg_time_ms,
            MIN(solve_time_ms) as min_time_ms,
            MAX(solve_time_ms) as max_time_ms,
            SUM(used_fallback) as fallback_count,
            CAST(SUM(used_fallback) AS FLOAT) / COUNT(*) * 100 as fallback_rate
        FROM ai_play_log
        GROUP BY ai_level
        ORDER BY
            CASE ai_level
                WHEN 'beginner' THEN 1
                WHEN 'intermediate' THEN 2
                WHEN 'advanced' THEN 3
                WHEN 'expert' THEN 4
            END
    """)

    ai_levels = cursor.fetchall()
    for level in ai_levels:
        print(f"{level['ai_level'].upper()}:")
        print(f"  Plays: {level['play_count']}")
        print(f"  Avg solve time: {level['avg_time_ms']:.2f}ms")
        print(f"  Time range: {level['min_time_ms']:.2f}ms - {level['max_time_ms']:.2f}ms")
        print(f"  Fallback rate: {level['fallback_rate']:.2f}% ({level['fallback_count']} fallbacks)")
        print()

    # DDS reliability check
    print("=" * 80)
    print("DDS RELIABILITY CHECK")
    print("=" * 80)
    print()

    cursor.execute("""
        SELECT
            SUM(used_fallback) as total_fallbacks,
            COUNT(*) as total_plays,
            CAST(SUM(used_fallback) AS FLOAT) / COUNT(*) * 100 as fallback_rate
        FROM ai_play_log
        WHERE ai_level = 'expert'
    """)

    dds_stats = cursor.fetchone()
    if dds_stats and dds_stats['total_plays'] > 0:
        print(f"Expert level plays: {dds_stats['total_plays']}")
        print(f"DDS fallbacks: {dds_stats['total_fallbacks']}")
        print(f"DDS reliability: {100 - dds_stats['fallback_rate']:.2f}%")
        print()

        if dds_stats['fallback_rate'] > 5:
            print("⚠️  WARNING: DDS fallback rate > 5%")
            print("   Investigate potential DDS instability")
        elif dds_stats['fallback_rate'] == 0:
            print("✅ EXCELLENT: DDS running without fallbacks")
        else:
            print("✅ GOOD: DDS fallback rate acceptable")
    else:
        print("No expert level plays found (DDS not in use)")
    print()

    # Position analysis
    print("=" * 80)
    print("PLAY DISTRIBUTION BY POSITION")
    print("=" * 80)
    print()

    cursor.execute("""
        SELECT
            position,
            COUNT(*) as play_count,
            AVG(solve_time_ms) as avg_time_ms
        FROM ai_play_log
        GROUP BY position
        ORDER BY position
    """)

    positions = cursor.fetchall()
    for pos in positions:
        print(f"{pos['position']}: {pos['play_count']} plays (avg {pos['avg_time_ms']:.2f}ms)")
    print()

    # Contract analysis
    print("=" * 80)
    print("CONTRACT ANALYSIS")
    print("=" * 80)
    print()

    cursor.execute("""
        SELECT
            contract,
            trump_suit,
            COUNT(*) as play_count,
            AVG(solve_time_ms) as avg_time_ms
        FROM ai_play_log
        WHERE contract IS NOT NULL
        GROUP BY contract, trump_suit
        ORDER BY play_count DESC
        LIMIT 10
    """)

    contracts = cursor.fetchall()
    if contracts:
        print("Top 10 contracts played:")
        for contract in contracts:
            trump = contract['trump_suit'] or 'NT'
            print(f"  {contract['contract']} ({trump}): {contract['play_count']} plays")
    else:
        print("No contract data available")
    print()

    # Recent activity
    print("=" * 80)
    print("RECENT ACTIVITY (Last 24 hours)")
    print("=" * 80)
    print()

    cursor.execute("""
        SELECT
            COUNT(*) as recent_plays,
            COUNT(DISTINCT session_id) as recent_sessions
        FROM ai_play_log
        WHERE timestamp >= datetime('now', '-1 day')
    """)

    recent = cursor.fetchone()
    print(f"Plays in last 24h: {recent['recent_plays']}")
    print(f"Sessions in last 24h: {recent['recent_sessions']}")
    print()

    conn.close()


def analyze_bidding_decisions(db_path='backend/bridge.db'):
    """Analyze AI bidding recommendations from production logs"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("=" * 80)
    print("BIDDING DECISIONS ANALYSIS")
    print("=" * 80)
    print()

    # Overall statistics
    cursor.execute("""
        SELECT
            COUNT(*) as total_decisions,
            COUNT(DISTINCT session_id) as unique_sessions,
            COUNT(DISTINCT user_id) as unique_users,
            MIN(timestamp) as first_decision,
            MAX(timestamp) as last_decision
        FROM bidding_decisions
    """)

    overall = cursor.fetchone()
    if overall['total_decisions'] == 0:
        print("No bidding decisions found in production database.")
        conn.close()
        return

    print(f"Total bidding decisions: {overall['total_decisions']}")
    print(f"Unique sessions: {overall['unique_sessions']}")
    print(f"Unique users: {overall['unique_users']}")
    print(f"Date range: {overall['first_decision']} to {overall['last_decision']}")
    print()

    # Correctness analysis
    print("=" * 80)
    print("BIDDING CORRECTNESS ANALYSIS")
    print("=" * 80)
    print()

    cursor.execute("""
        SELECT
            correctness,
            COUNT(*) as count,
            AVG(score) as avg_score,
            CAST(COUNT(*) AS FLOAT) / (SELECT COUNT(*) FROM bidding_decisions) * 100 as percentage
        FROM bidding_decisions
        GROUP BY correctness
        ORDER BY
            CASE correctness
                WHEN 'optimal' THEN 1
                WHEN 'acceptable' THEN 2
                WHEN 'suboptimal' THEN 3
                WHEN 'error' THEN 4
            END
    """)

    correctness = cursor.fetchall()
    for c in correctness:
        print(f"{c['correctness'].upper()}: {c['count']} ({c['percentage']:.1f}%)")
        print(f"  Average score: {c['avg_score']:.2f}/10")
        print()

    # Error analysis
    print("=" * 80)
    print("ERROR CATEGORY ANALYSIS")
    print("=" * 80)
    print()

    cursor.execute("""
        SELECT
            error_category,
            error_subcategory,
            COUNT(*) as count,
            AVG(score) as avg_score
        FROM bidding_decisions
        WHERE error_category IS NOT NULL
        GROUP BY error_category, error_subcategory
        ORDER BY count DESC
    """)

    errors = cursor.fetchall()
    if errors:
        for error in errors:
            print(f"{error['error_category']}")
            if error['error_subcategory']:
                print(f"  Subcategory: {error['error_subcategory']}")
            print(f"  Count: {error['count']}")
            print(f"  Avg score: {error['avg_score']:.2f}/10")
            print()
    else:
        print("No errors categorized yet")
        print()

    # Concept analysis
    print("=" * 80)
    print("KEY CONCEPTS ENCOUNTERED")
    print("=" * 80)
    print()

    cursor.execute("""
        SELECT
            key_concept,
            COUNT(*) as count,
            AVG(score) as avg_score,
            difficulty
        FROM bidding_decisions
        WHERE key_concept IS NOT NULL
        GROUP BY key_concept, difficulty
        ORDER BY count DESC
        LIMIT 10
    """)

    concepts = cursor.fetchall()
    if concepts:
        for concept in concepts:
            print(f"{concept['key_concept']} ({concept['difficulty']})")
            print(f"  Count: {concept['count']}, Avg score: {concept['avg_score']:.2f}/10")
            print()
    else:
        print("No concept data available")
        print()

    # Position analysis
    print("=" * 80)
    print("BIDDING BY POSITION")
    print("=" * 80)
    print()

    cursor.execute("""
        SELECT
            position,
            COUNT(*) as count,
            AVG(score) as avg_score,
            SUM(CASE WHEN correctness = 'optimal' THEN 1 ELSE 0 END) as optimal_count
        FROM bidding_decisions
        GROUP BY position
        ORDER BY position
    """)

    positions = cursor.fetchall()
    for pos in positions:
        optimal_rate = (pos['optimal_count'] / pos['count'] * 100) if pos['count'] > 0 else 0
        print(f"{pos['position']}: {pos['count']} decisions")
        print(f"  Avg score: {pos['avg_score']:.2f}/10")
        print(f"  Optimal rate: {optimal_rate:.1f}%")
        print()

    # Recent sample decisions
    print("=" * 80)
    print("RECENT BIDDING DECISIONS (Last 5)")
    print("=" * 80)
    print()

    cursor.execute("""
        SELECT
            timestamp,
            position,
            user_bid,
            optimal_bid,
            correctness,
            score,
            key_concept
        FROM bidding_decisions
        ORDER BY timestamp DESC
        LIMIT 5
    """)

    recent = cursor.fetchall()
    for i, decision in enumerate(recent, 1):
        print(f"{i}. {decision['timestamp']} - {decision['position']}")
        print(f"   User bid: {decision['user_bid']} | Optimal: {decision['optimal_bid']}")
        print(f"   Result: {decision['correctness']} (score: {decision['score']:.1f}/10)")
        if decision['key_concept']:
            print(f"   Concept: {decision['key_concept']}")
        print()

    conn.close()


def export_detailed_report(db_path='backend/bridge.db', output_file='production_ai_analysis.json'):
    """Export detailed analysis to JSON for further processing"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    report = {
        'generated_at': datetime.now().isoformat(),
        'ai_play_performance': {},
        'bidding_decisions': {}
    }

    # Get all AI play data
    cursor.execute("SELECT * FROM ai_play_log ORDER BY timestamp DESC")
    plays = [dict(row) for row in cursor.fetchall()]
    report['ai_play_performance']['plays'] = plays
    report['ai_play_performance']['total_count'] = len(plays)

    # Get all bidding decisions
    cursor.execute("SELECT * FROM bidding_decisions ORDER BY timestamp DESC")
    decisions = [dict(row) for row in cursor.fetchall()]
    report['bidding_decisions']['decisions'] = decisions
    report['bidding_decisions']['total_count'] = len(decisions)

    # Save to file
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    print(f"Detailed report exported to: {output_file}")
    conn.close()


def main():
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "PRODUCTION AI ANALYSIS TOOL" + " " * 31 + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    # Parse command line arguments
    db_path = 'backend/bridge.db'
    export_report = False

    # Check for --db flag
    if '--db' in sys.argv:
        try:
            db_index = sys.argv.index('--db')
            if db_index + 1 < len(sys.argv):
                db_path = sys.argv[db_index + 1]
        except (ValueError, IndexError):
            print("❌ Error: --db flag requires a database path")
            print("   Usage: python analyze_production_ai.py --db path/to/database.db")
            sys.exit(1)

    # Check for --export flag
    if '--export' in sys.argv:
        export_report = True

    # Check if database exists
    import os
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        print("   Make sure the path is correct")
        print()
        print("   Examples:")
        print("     python analyze_production_ai.py")
        print("     python analyze_production_ai.py --db backend/bridge.db")
        print("     python analyze_production_ai.py --db production_bridge.db --export")
        sys.exit(1)

    print(f"📊 Analyzing database: {db_path}")
    print()

    try:
        # Run analyses
        analyze_ai_play_performance(db_path)
        print("\n")
        analyze_bidding_decisions(db_path)
        print("\n")

        # Export if requested
        if export_report:
            output_file = db_path.replace('.db', '_analysis.json')
            if output_file == db_path:  # Safety check
                output_file = 'production_ai_analysis.json'
            export_detailed_report(db_path, output_file)
            print()
        else:
            print("=" * 80)
            print("EXPORT OPTIONS")
            print("=" * 80)
            print()
            print("To export detailed JSON report, run:")
            print(f"  python analyze_production_ai.py --db {db_path} --export")
            print()

        print("=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)
        print()

    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

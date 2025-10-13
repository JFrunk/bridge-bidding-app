"""
Performance benchmarks for core shared components.

Validates that Phase 1 architecture doesn't degrade performance.
"""

import time
import statistics
from core.session_manager import SessionManager
from core.deal_generator import DealGenerator
from core.scenario_loader import ScenarioLoader


class PerformanceBenchmark:
    """Performance benchmarking utilities."""

    @staticmethod
    def time_function(func, iterations=100):
        """Time a function over multiple iterations."""
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            func()
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to milliseconds

        return {
            'mean': statistics.mean(times),
            'median': statistics.median(times),
            'min': min(times),
            'max': max(times),
            'stdev': statistics.stdev(times) if len(times) > 1 else 0,
            'iterations': iterations
        }


def benchmark_deal_generation():
    """Benchmark hand generation performance."""
    print("\n" + "="*70)
    print("BENCHMARK: Deal Generation Performance")
    print("="*70)

    # Test 1: Random deal generation
    print("\n1. Random Deal Generation")
    result = PerformanceBenchmark.time_function(
        lambda: DealGenerator.generate_random_deal(),
        iterations=100
    )
    print(f"   Mean:   {result['mean']:.2f}ms")
    print(f"   Median: {result['median']:.2f}ms")
    print(f"   Min:    {result['min']:.2f}ms")
    print(f"   Max:    {result['max']:.2f}ms")
    print(f"   StdDev: {result['stdev']:.2f}ms")

    assert result['mean'] < 50, f"Random deal generation too slow: {result['mean']:.2f}ms"
    print("   ✅ PASS: Within 50ms threshold")

    # Test 2: Constrained deal generation (1NT opening)
    print("\n2. Constrained Deal Generation (1NT)")
    constraints = {
        'S': {'hcp_range': (15, 17), 'is_balanced': True},
        'N': None,
        'E': None,
        'W': None
    }
    result = PerformanceBenchmark.time_function(
        lambda: DealGenerator.generate_constrained_deal(constraints),
        iterations=50
    )
    print(f"   Mean:   {result['mean']:.2f}ms")
    print(f"   Median: {result['median']:.2f}ms")
    print(f"   Min:    {result['min']:.2f}ms")
    print(f"   Max:    {result['max']:.2f}ms")

    assert result['mean'] < 200, f"Constrained deal generation too slow: {result['mean']:.2f}ms"
    print("   ✅ PASS: Within 200ms threshold")

    # Test 3: Contract-based generation
    print("\n3. Contract-Based Deal Generation (3NT)")
    result = PerformanceBenchmark.time_function(
        lambda: DealGenerator.generate_for_contract("3NT", "S"),
        iterations=50
    )
    print(f"   Mean:   {result['mean']:.2f}ms")
    print(f"   Median: {result['median']:.2f}ms")

    assert result['mean'] < 300, f"Contract-based generation too slow: {result['mean']:.2f}ms"
    print("   ✅ PASS: Within 300ms threshold")


def benchmark_session_management():
    """Benchmark session management performance."""
    print("\n" + "="*70)
    print("BENCHMARK: Session Management Performance")
    print("="*70)

    manager = SessionManager()

    # Test 1: Session creation
    print("\n1. Session Creation")
    result = PerformanceBenchmark.time_function(
        lambda: manager.create_session('bidding', user_id='test_user'),
        iterations=1000
    )
    print(f"   Mean:   {result['mean']:.2f}ms")
    print(f"   Median: {result['median']:.2f}ms")

    assert result['mean'] < 5, f"Session creation too slow: {result['mean']:.2f}ms"
    print("   ✅ PASS: Within 5ms threshold")

    # Test 2: Session retrieval
    print("\n2. Session Retrieval")
    session_id = manager.create_session('bidding')
    result = PerformanceBenchmark.time_function(
        lambda: manager.get_session(session_id),
        iterations=10000
    )
    print(f"   Mean:   {result['mean']:.3f}ms")
    print(f"   Median: {result['median']:.3f}ms")

    assert result['mean'] < 0.1, f"Session retrieval too slow: {result['mean']:.3f}ms"
    print("   ✅ PASS: Within 0.1ms threshold")

    # Test 3: Session update
    print("\n3. Session Update")
    result = PerformanceBenchmark.time_function(
        lambda: manager.update_session(session_id, {'test': 'data'}),
        iterations=1000
    )
    print(f"   Mean:   {result['mean']:.3f}ms")
    print(f"   Median: {result['median']:.3f}ms")

    assert result['mean'] < 1, f"Session update too slow: {result['mean']:.3f}ms"
    print("   ✅ PASS: Within 1ms threshold")

    # Test 4: Concurrent session handling
    print("\n4. Concurrent Session Handling (100 sessions)")
    start = time.perf_counter()
    session_ids = []
    for i in range(100):
        sid = manager.create_session('bidding', user_id=f'user{i}')
        manager.update_session(sid, {'deal': 'data', 'auction': []})
        session_ids.append(sid)

    # Retrieve all sessions
    for sid in session_ids:
        manager.get_session(sid)

    end = time.perf_counter()
    total_time = (end - start) * 1000
    print(f"   Total: {total_time:.2f}ms")
    print(f"   Per session: {total_time/100:.2f}ms")

    assert total_time < 1000, f"100 concurrent sessions too slow: {total_time:.2f}ms"
    print("   ✅ PASS: Within 1000ms threshold")


def benchmark_scenario_loading():
    """Benchmark scenario loading performance."""
    print("\n" + "="*70)
    print("BENCHMARK: Scenario Loading Performance")
    print("="*70)

    # Test 1: First load (with file I/O)
    print("\n1. First Load (with file I/O)")
    loader = ScenarioLoader()
    start = time.perf_counter()
    scenarios = loader.load_bidding_scenarios()
    end = time.perf_counter()
    load_time = (end - start) * 1000

    print(f"   Load time: {load_time:.2f}ms")
    print(f"   Scenarios loaded: {len(scenarios)}")

    assert load_time < 500, f"Scenario loading too slow: {load_time:.2f}ms"
    print("   ✅ PASS: Within 500ms threshold")

    # Test 2: Cached load (should be faster)
    print("\n2. Cached Load")
    result = PerformanceBenchmark.time_function(
        lambda: loader.load_bidding_scenarios(),
        iterations=100
    )
    print(f"   Mean:   {result['mean']:.2f}ms")

    # Cached should be much faster
    assert result['mean'] < 100, f"Cached load too slow: {result['mean']:.2f}ms"
    print("   ✅ PASS: Within 100ms threshold")

    # Test 3: Scenario validation
    print("\n3. Scenario Validation")
    if scenarios:
        result = PerformanceBenchmark.time_function(
            lambda: loader.validate_bidding_scenario(scenarios[0]),
            iterations=1000
        )
        print(f"   Mean:   {result['mean']:.3f}ms")

        assert result['mean'] < 1, f"Scenario validation too slow: {result['mean']:.3f}ms"
        print("   ✅ PASS: Within 1ms threshold")


def run_memory_test():
    """Basic memory usage test."""
    print("\n" + "="*70)
    print("MEMORY: Basic Memory Usage Test")
    print("="*70)

    import sys

    # Test 1: SessionManager memory with 1000 sessions
    print("\n1. SessionManager with 1000 sessions")
    manager = SessionManager()
    initial_size = sys.getsizeof(manager.sessions)

    for i in range(1000):
        session_id = manager.create_session('bidding', user_id=f'user{i}')
        manager.update_session(session_id, {
            'deal': 'some_data',
            'auction': [{'bid': '1NT', 'explanation': 'test'}] * 10
        })

    final_size = sys.getsizeof(manager.sessions)
    print(f"   Initial size: {initial_size} bytes")
    print(f"   Final size: {final_size} bytes")
    print(f"   Growth: {final_size - initial_size} bytes")
    print(f"   Per session: {(final_size - initial_size) / 1000:.1f} bytes")

    # Cleanup test
    print("\n2. Memory cleanup test")
    initial_count = len(manager.sessions)
    cleaned = manager.cleanup_expired_sessions()
    final_count = len(manager.sessions)

    print(f"   Sessions before cleanup: {initial_count}")
    print(f"   Sessions after cleanup: {final_count}")
    print(f"   Sessions cleaned: {cleaned}")


def generate_report():
    """Generate performance report."""
    print("\n" + "="*70)
    print("PERFORMANCE BENCHMARK REPORT")
    print("="*70)
    print("\n✅ All benchmarks completed successfully!")
    print("\nSummary:")
    print("  - Deal Generation: < 50ms (random), < 200ms (constrained)")
    print("  - Session Management: < 5ms (create), < 0.1ms (retrieve)")
    print("  - Scenario Loading: < 500ms (initial), < 100ms (cached)")
    print("  - Concurrent Sessions: 100 sessions in < 1000ms")
    print("\nConclusion: Performance is within acceptable thresholds.")
    print("Architecture changes have not degraded system performance.")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("PHASE 1 ARCHITECTURE PERFORMANCE VALIDATION")
    print("="*70)
    print("\nTesting core shared components performance...")

    try:
        benchmark_deal_generation()
        benchmark_session_management()
        benchmark_scenario_loading()
        run_memory_test()
        generate_report()

        print("\n" + "="*70)
        print("✅ ALL PERFORMANCE TESTS PASSED")
        print("="*70)

    except AssertionError as e:
        print(f"\n❌ PERFORMANCE TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

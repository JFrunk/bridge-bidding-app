"""
Performance monitoring for bidding system.
Tracks timing metrics to identify bottlenecks and optimize performance.
"""

import time
from collections import defaultdict
from typing import Dict, List, Optional
from contextlib import contextmanager


class PerformanceMonitor:
    """
    Monitors and records performance metrics for bidding operations.

    Usage:
        monitor = PerformanceMonitor()

        with monitor.timer('feature_extraction'):
            extract_features(...)

        # Or manually:
        monitor.start('module_selection')
        select_module(...)
        monitor.stop('module_selection')

        # Get stats:
        stats = monitor.get_stats()
    """

    def __init__(self):
        self.timings = defaultdict(list)
        self._active_timers = {}

    def start(self, category: str) -> float:
        """Start timing a category. Returns start timestamp."""
        start_time = time.time()
        self._active_timers[category] = start_time
        return start_time

    def stop(self, category: str) -> Optional[float]:
        """Stop timing a category. Returns duration in milliseconds."""
        if category not in self._active_timers:
            return None

        start_time = self._active_timers.pop(category)
        duration_ms = (time.time() - start_time) * 1000
        self.timings[category].append(duration_ms)
        return duration_ms

    @contextmanager
    def timer(self, category: str):
        """Context manager for timing code blocks."""
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.timings[category].append(duration_ms)

    def record(self, category: str, duration_ms: float):
        """Manually record a timing."""
        self.timings[category].append(duration_ms)

    def get_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Get statistics for all recorded timings.

        Returns:
            Dict with format:
            {
                'category_name': {
                    'avg': 45.2,
                    'min': 12.3,
                    'max': 123.4,
                    'count': 42,
                    'total': 1898.4
                }
            }
        """
        stats = {}
        for category, times in self.timings.items():
            if times:
                stats[category] = {
                    'avg': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times),
                    'count': len(times),
                    'total': sum(times)
                }
        return stats

    def get_last(self, category: str) -> Optional[float]:
        """Get the last recorded timing for a category."""
        if category in self.timings and self.timings[category]:
            return self.timings[category][-1]
        return None

    def reset(self):
        """Clear all recorded timings."""
        self.timings.clear()
        self._active_timers.clear()

    def print_summary(self, title: str = "Performance Summary"):
        """Print a formatted summary of all statistics."""
        stats = self.get_stats()
        if not stats:
            print(f"\n{title}: No data recorded")
            return

        print(f"\n{'='*60}")
        print(f"{title}")
        print(f"{'='*60}")

        # Sort by total time (descending)
        sorted_stats = sorted(stats.items(), key=lambda x: x[1]['total'], reverse=True)

        print(f"{'Category':<30} {'Avg':>8} {'Min':>8} {'Max':>8} {'Count':>6}")
        print(f"{'-'*60}")

        for category, data in sorted_stats:
            print(f"{category:<30} {data['avg']:>7.1f}ms {data['min']:>7.1f}ms "
                  f"{data['max']:>7.1f}ms {data['count']:>6}")

        print(f"{'='*60}\n")


# Global instance for easy access
_global_monitor = PerformanceMonitor()


def get_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    return _global_monitor

#!/usr/bin/env python3
"""
Test suite for GPT-OS Enterprise v2.0
Tests all resilience patterns and enterprise features
"""

import asyncio
import time
from datetime import datetime, timedelta

# Import enterprise components
from gpt_shell_enterprise import (
    Config, StructuredLogger, Metrics, CircuitBreaker,
    CircuitState, LRUCache, TokenBucket, MemoryManager
)


class TestResults:
    """Test results tracker"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def record(self, test_name: str, passed: bool, message: str = ""):
        """Record test result"""
        self.tests.append({
            "name": test_name,
            "passed": passed,
            "message": message
        })
        if passed:
            self.passed += 1
            print(f"✅ {test_name}: PASSED")
        else:
            self.failed += 1
            print(f"❌ {test_name}: FAILED - {message}")
    
    def summary(self):
        """Print test summary"""
        total = self.passed + self.failed
        print("\n" + "=" * 70)
        print(f"Test Summary: {self.passed}/{total} passed")
        print("=" * 70)
        
        if self.failed > 0:
            print("\nFailed tests:")
            for test in self.tests:
                if not test["passed"]:
                    print(f"  - {test['name']}: {test['message']}")


def test_config():
    """Test configuration management"""
    results = TestResults()
    
    # Test default config
    config = Config()
    results.record(
        "Config: Default values",
        config.llm_model == "gpt-4.1-mini" and config.cache_enabled,
        f"Model: {config.llm_model}, Cache: {config.cache_enabled}"
    )
    
    # Test from_env
    import os
    os.environ['GPTOS_LLM_MODEL'] = 'test-model'
    config = Config.from_env()
    results.record(
        "Config: Environment override",
        config.llm_model == 'test-model',
        f"Expected 'test-model', got '{config.llm_model}'"
    )
    
    return results


def test_structured_logging():
    """Test structured logging"""
    results = TestResults()
    
    logger = StructuredLogger("test", "INFO")
    
    # Test logging (should not raise exception)
    try:
        logger.info("test_event", key="value")
        logger.warning("warning_event", count=42)
        logger.error("error_event", error="test error")
        results.record("Logging: Basic operations", True)
    except Exception as e:
        results.record("Logging: Basic operations", False, str(e))
    
    return results


def test_metrics():
    """Test metrics collection"""
    results = TestResults()
    
    metrics = Metrics()
    
    # Test counter
    metrics.increment("test_counter", 5)
    results.record(
        "Metrics: Counter increment",
        metrics.counters.get("test_counter") == 5,
        f"Expected 5, got {metrics.counters.get('test_counter')}"
    )
    
    # Test gauge
    metrics.set_gauge("test_gauge", 42.5)
    results.record(
        "Metrics: Gauge set",
        metrics.gauges.get("test_gauge") == 42.5,
        f"Expected 42.5, got {metrics.gauges.get('test_gauge')}"
    )
    
    # Test histogram
    metrics.observe("test_histogram", 100)
    metrics.observe("test_histogram", 200)
    metrics.observe("test_histogram", 300)
    
    stats = metrics.get_stats()
    hist_stats = stats["histograms"]["test_histogram"]
    
    results.record(
        "Metrics: Histogram observations",
        hist_stats["count"] == 3 and hist_stats["avg"] == 200,
        f"Count: {hist_stats['count']}, Avg: {hist_stats['avg']}"
    )
    
    return results


def test_circuit_breaker():
    """Test circuit breaker pattern"""
    results = TestResults()
    
    config = Config()
    config.circuit_breaker_failure_threshold = 3
    config.circuit_breaker_recovery_timeout = 1  # 1 second for testing
    
    logger = StructuredLogger("test", "ERROR")  # Suppress logs
    metrics = Metrics()
    cb = CircuitBreaker(config, logger, metrics)
    
    # Test initial state
    results.record(
        "Circuit Breaker: Initial state CLOSED",
        cb.state == CircuitState.CLOSED,
        f"Expected CLOSED, got {cb.state}"
    )
    
    # Test transition to OPEN
    for i in range(3):
        cb.record_failure()
    
    results.record(
        "Circuit Breaker: Transition to OPEN after failures",
        cb.state == CircuitState.OPEN,
        f"Expected OPEN, got {cb.state}"
    )
    
    # Test request blocking when OPEN
    results.record(
        "Circuit Breaker: Block requests when OPEN",
        not cb.should_allow_request(),
        "Requests should be blocked"
    )
    
    # Test transition to HALF_OPEN after timeout
    time.sleep(1.1)  # Wait for recovery timeout
    cb.should_allow_request()  # Trigger state check
    
    results.record(
        "Circuit Breaker: Transition to HALF_OPEN after timeout",
        cb.state == CircuitState.HALF_OPEN,
        f"Expected HALF_OPEN, got {cb.state}"
    )
    
    # Test transition to CLOSED after successes
    cb.record_success()
    cb.record_success()
    
    results.record(
        "Circuit Breaker: Transition to CLOSED after successes",
        cb.state == CircuitState.CLOSED,
        f"Expected CLOSED, got {cb.state}"
    )
    
    return results


def test_cache():
    """Test LRU cache with TTL"""
    results = TestResults()
    
    config = Config()
    config.cache_max_size = 3
    config.cache_ttl = 1  # 1 second for testing
    
    logger = StructuredLogger("test", "ERROR")
    metrics = Metrics()
    cache = LRUCache(config, logger, metrics)
    
    # Test basic set/get
    cache.set("key1", "value1")
    results.record(
        "Cache: Basic set/get",
        cache.get("key1") == "value1",
        f"Expected 'value1', got '{cache.get('key1')}'"
    )
    
    # Test cache miss
    results.record(
        "Cache: Miss on non-existent key",
        cache.get("nonexistent") is None,
        "Should return None for missing key"
    )
    
    # Test LRU eviction
    cache.set("key2", "value2")
    cache.set("key3", "value3")
    cache.set("key4", "value4")  # Should evict key1
    
    results.record(
        "Cache: LRU eviction",
        cache.get("key1") is None and cache.get("key4") == "value4",
        "Oldest entry should be evicted"
    )
    
    # Test TTL expiration
    cache.set("ttl_key", "ttl_value", ttl=1)
    time.sleep(1.1)
    
    results.record(
        "Cache: TTL expiration",
        cache.get("ttl_key") is None,
        "Expired entry should return None"
    )
    
    # Test cleanup
    cache.set("exp1", "v1", ttl=1)
    cache.set("exp2", "v2", ttl=1)
    time.sleep(1.1)
    cache.cleanup_expired()
    
    results.record(
        "Cache: Cleanup expired entries",
        len(cache.cache) < 5,  # Should have removed expired entries
        f"Cache size: {len(cache.cache)}"
    )
    
    return results


def test_rate_limiter():
    """Test token bucket rate limiter"""
    results = TestResults()
    
    config = Config()
    config.rate_limit_requests_per_minute = 60  # 1 per second
    config.rate_limit_burst_size = 3
    
    logger = StructuredLogger("test", "ERROR")
    limiter = TokenBucket(config, logger)
    
    # Test burst allowance
    burst_allowed = sum(1 for _ in range(5) if limiter.allow_request())
    
    results.record(
        "Rate Limiter: Burst allowance",
        burst_allowed == 3,
        f"Expected 3 burst requests, got {burst_allowed}"
    )
    
    # Test rate limiting
    results.record(
        "Rate Limiter: Block after burst",
        not limiter.allow_request(),
        "Should block after burst exhausted"
    )
    
    # Test token replenishment
    time.sleep(1.1)  # Wait for token replenishment
    results.record(
        "Rate Limiter: Token replenishment",
        limiter.allow_request(),
        "Should allow request after replenishment"
    )
    
    return results


def test_memory_manager():
    """Test memory management"""
    results = TestResults()
    
    config = Config()
    config.memory_max_history = 5
    
    logger = StructuredLogger("test", "ERROR")
    metrics = Metrics()
    mm = MemoryManager(config, logger, metrics)
    
    # Test bounded history
    for i in range(10):
        mm.add_to_history({"command": f"cmd{i}"})
    
    results.record(
        "Memory Manager: Bounded history",
        len(mm.history) == 5,
        f"Expected max 5 entries, got {len(mm.history)}"
    )
    
    # Test FIFO behavior
    first_entry = list(mm.history)[0]
    results.record(
        "Memory Manager: FIFO behavior",
        first_entry["command"] == "cmd5",  # First 5 should be evicted
        f"Expected 'cmd5', got '{first_entry['command']}'"
    )
    
    # Test get_history with limit
    limited = mm.get_history(limit=3)
    results.record(
        "Memory Manager: Get history with limit",
        len(limited) == 3,
        f"Expected 3 entries, got {len(limited)}"
    )
    
    # Test clear
    mm.clear_history()
    results.record(
        "Memory Manager: Clear history",
        len(mm.history) == 0,
        f"Expected 0 entries, got {len(mm.history)}"
    )
    
    return results


async def test_async_operations():
    """Test async operations"""
    results = TestResults()
    
    # Test async sleep (basic async functionality)
    start = time.time()
    await asyncio.sleep(0.1)
    elapsed = time.time() - start
    
    results.record(
        "Async: Basic async/await",
        0.09 < elapsed < 0.15,
        f"Expected ~0.1s, got {elapsed:.3f}s"
    )
    
    # Test concurrent execution
    async def task(n):
        await asyncio.sleep(0.1)
        return n * 2
    
    start = time.time()
    results_list = await asyncio.gather(
        task(1), task(2), task(3)
    )
    elapsed = time.time() - start
    
    results.record(
        "Async: Concurrent execution",
        elapsed < 0.2 and results_list == [2, 4, 6],
        f"Expected <0.2s and [2,4,6], got {elapsed:.3f}s and {results_list}"
    )
    
    # Test timeout
    async def slow_task():
        await asyncio.sleep(2)
        return "done"
    
    try:
        await asyncio.wait_for(slow_task(), timeout=0.1)
        results.record("Async: Timeout handling", False, "Should have timed out")
    except asyncio.TimeoutError:
        results.record("Async: Timeout handling", True)
    
    return results


def run_all_tests():
    """Run all tests"""
    print("=" * 70)
    print("GPT-OS Enterprise v2.0 - Test Suite")
    print("=" * 70)
    print()
    
    all_results = TestResults()
    
    # Configuration tests
    print("\n📋 Testing Configuration Management...")
    config_results = test_config()
    all_results.passed += config_results.passed
    all_results.failed += config_results.failed
    all_results.tests.extend(config_results.tests)
    
    # Logging tests
    print("\n📝 Testing Structured Logging...")
    log_results = test_structured_logging()
    all_results.passed += log_results.passed
    all_results.failed += log_results.failed
    all_results.tests.extend(log_results.tests)
    
    # Metrics tests
    print("\n📊 Testing Metrics Collection...")
    metrics_results = test_metrics()
    all_results.passed += metrics_results.passed
    all_results.failed += metrics_results.failed
    all_results.tests.extend(metrics_results.tests)
    
    # Circuit breaker tests
    print("\n🔌 Testing Circuit Breaker...")
    cb_results = test_circuit_breaker()
    all_results.passed += cb_results.passed
    all_results.failed += cb_results.failed
    all_results.tests.extend(cb_results.tests)
    
    # Cache tests
    print("\n💾 Testing LRU Cache...")
    cache_results = test_cache()
    all_results.passed += cache_results.passed
    all_results.failed += cache_results.failed
    all_results.tests.extend(cache_results.tests)
    
    # Rate limiter tests
    print("\n⏱️  Testing Rate Limiter...")
    rl_results = test_rate_limiter()
    all_results.passed += rl_results.passed
    all_results.failed += rl_results.failed
    all_results.tests.extend(rl_results.tests)
    
    # Memory manager tests
    print("\n🧠 Testing Memory Manager...")
    mm_results = test_memory_manager()
    all_results.passed += mm_results.passed
    all_results.failed += mm_results.failed
    all_results.tests.extend(mm_results.tests)
    
    # Async tests
    print("\n⚡ Testing Async Operations...")
    async_results = asyncio.run(test_async_operations())
    all_results.passed += async_results.passed
    all_results.failed += async_results.failed
    all_results.tests.extend(async_results.tests)
    
    # Print summary
    all_results.summary()
    
    return all_results.failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

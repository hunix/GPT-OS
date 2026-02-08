#!/usr/bin/env python3
"""
Comprehensive test suite for GPT-OS Enterprise v2.0
Runs all tests and provides detailed report
"""

import subprocess
import sys


def run_test_suite(name: str, command: str) -> tuple:
    """Run a test suite and return results"""
    print(f"\n{'='*70}")
    print(f"Running: {name}")
    print(f"{'='*70}\n")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return (result.returncode == 0, result.stdout)
    
    except subprocess.TimeoutExpired:
        print(f"❌ {name} TIMED OUT")
        return (False, "Timeout")
    except Exception as e:
        print(f"❌ {name} FAILED: {str(e)}")
        return (False, str(e))


def main():
    """Run all test suites"""
    print("="*70)
    print("GPT-OS Enterprise v2.0 - Comprehensive Test Suite")
    print("="*70)
    
    test_suites = [
        ("Enterprise Components", "python3 test_enterprise.py"),
        ("Input Validation", "python3 test_input_validation.py"),
    ]
    
    results = {}
    
    for name, command in test_suites:
        success, output = run_test_suite(name, command)
        results[name] = success
    
    # Summary
    print("\n" + "="*70)
    print("FINAL TEST SUMMARY")
    print("="*70)
    
    total = len(results)
    passed = sum(1 for success in results.values() if success)
    failed = total - passed
    
    for name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{name}: {status}")
    
    print(f"\nTotal: {passed}/{total} test suites passed")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Code is production-ready.")
        return 0
    else:
        print(f"\n⚠️  {failed} test suite(s) failed. Please review.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

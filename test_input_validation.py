#!/usr/bin/env python3
"""
Test suite for input validation module
"""

from input_validator import InputValidator, ValidationResult


def test_input_validation():
    """Test input validation"""
    validator = InputValidator()
    results = {"passed": 0, "failed": 0}
    
    # Test 1: Valid input
    result = validator.validate("update my software")
    if result.is_valid and result.sanitized_input == "update my software":
        print("✅ Test 1: Valid input - PASSED")
        results["passed"] += 1
    else:
        print(f"❌ Test 1: Valid input - FAILED: {result.error_message}")
        results["failed"] += 1
    
    # Test 2: Empty input
    result = validator.validate("")
    if not result.is_valid:
        print("✅ Test 2: Empty input - PASSED")
        results["passed"] += 1
    else:
        print("❌ Test 2: Empty input - FAILED")
        results["failed"] += 1
    
    # Test 3: None input
    result = validator.validate(None)
    if not result.is_valid:
        print("✅ Test 3: None input - PASSED")
        results["passed"] += 1
    else:
        print("❌ Test 3: None input - FAILED")
        results["failed"] += 1
    
    # Test 4: Too long input
    result = validator.validate("a" * 20000)
    if not result.is_valid and "maximum length" in result.error_message:
        print("✅ Test 4: Too long input - PASSED")
        results["passed"] += 1
    else:
        print(f"❌ Test 4: Too long input - FAILED: {result.error_message}")
        results["failed"] += 1
    
    # Test 5: Suspicious pattern - command injection
    result = validator.validate("update && rm -rf /")
    if not result.is_valid and result.risk_level == "high":
        print("✅ Test 5: Suspicious pattern - PASSED")
        results["passed"] += 1
    else:
        print(f"❌ Test 5: Suspicious pattern - FAILED: {result.error_message}")
        results["failed"] += 1
    
    # Test 6: Command substitution
    result = validator.validate("show files $(rm -rf /)")
    if not result.is_valid and result.risk_level == "high":
        print("✅ Test 6: Command substitution - PASSED")
        results["passed"] += 1
    else:
        print(f"❌ Test 6: Command substitution - FAILED: {result.error_message}")
        results["failed"] += 1
    
    # Test 7: Null bytes
    result = validator.validate("test\x00input")
    if not result.is_valid:
        print("✅ Test 7: Null bytes - PASSED")
        results["passed"] += 1
    else:
        print("❌ Test 7: Null bytes - FAILED")
        results["failed"] += 1
    
    # Test 8: Whitespace normalization
    result = validator.validate("  update   my    software  ")
    if result.is_valid and result.sanitized_input == "update my software":
        print("✅ Test 8: Whitespace normalization - PASSED")
        results["passed"] += 1
    else:
        print(f"❌ Test 8: Whitespace normalization - FAILED: '{result.sanitized_input}'")
        results["failed"] += 1
    
    # Test 9: Multi-language input
    result = validator.validate("更新我的系统")
    if result.is_valid:
        print("✅ Test 9: Multi-language input - PASSED")
        results["passed"] += 1
    else:
        print(f"❌ Test 9: Multi-language input - FAILED: {result.error_message}")
        results["failed"] += 1
    
    # Test 10: Special characters (safe)
    result = validator.validate("find . -name '*.pdf'")
    if result.is_valid:
        print("✅ Test 10: Special characters (safe) - PASSED")
        results["passed"] += 1
    else:
        print(f"❌ Test 10: Special characters (safe) - FAILED: {result.error_message}")
        results["failed"] += 1
    
    # Test 11: Backtick command substitution
    result = validator.validate("echo `whoami`")
    if not result.is_valid and result.risk_level == "high":
        print("✅ Test 11: Backtick command substitution - PASSED")
        results["passed"] += 1
    else:
        print(f"❌ Test 11: Backtick command substitution - FAILED: {result.error_message}")
        results["failed"] += 1
    
    # Test 12: Pipe to shell
    result = validator.validate("cat file | sh")
    if not result.is_valid and result.risk_level == "high":
        print("✅ Test 12: Pipe to shell - PASSED")
        results["passed"] += 1
    else:
        print(f"❌ Test 12: Pipe to shell - FAILED: {result.error_message}")
        results["failed"] += 1
    
    # Test 13: Safe for LLM check
    if validator.is_safe_for_llm("update my software"):
        print("✅ Test 13: Safe for LLM (valid) - PASSED")
        results["passed"] += 1
    else:
        print("❌ Test 13: Safe for LLM (valid) - FAILED")
        results["failed"] += 1
    
    # Test 14: Unsafe for LLM check
    if not validator.is_safe_for_llm("; rm -rf / && echo done"):
        print("✅ Test 14: Unsafe for LLM (invalid) - PASSED")
        results["passed"] += 1
    else:
        print("❌ Test 14: Unsafe for LLM (invalid) - FAILED")
        results["failed"] += 1
    
    # Test 15: Risk assessment
    risk_level, explanation = validator.get_risk_assessment("update my software")
    if risk_level == "low":
        print("✅ Test 15: Risk assessment (low) - PASSED")
        results["passed"] += 1
    else:
        print(f"❌ Test 15: Risk assessment (low) - FAILED: {risk_level}")
        results["failed"] += 1
    
    # Summary
    total = results["passed"] + results["failed"]
    print(f"\n{'='*70}")
    print(f"Input Validation Test Summary: {results['passed']}/{total} passed")
    print(f"{'='*70}")
    
    return results["failed"] == 0


if __name__ == "__main__":
    success = test_input_validation()
    exit(0 if success else 1)

#!/usr/bin/env python3
"""
Input Validation Module for GPT-OS Enterprise
Provides comprehensive input sanitization and validation
"""

import re
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of input validation"""
    is_valid: bool
    sanitized_input: str
    error_message: Optional[str] = None
    risk_level: str = "low"  # low, medium, high


class InputValidator:
    """Comprehensive input validation and sanitization"""
    
    # Suspicious patterns that might indicate injection attempts
    SUSPICIOUS_PATTERNS = [
        r';\s*rm\s+-rf',  # Command chaining with rm -rf
        r'\$\(.*\)',  # Command substitution
        r'`.*`',  # Backtick command substitution
        r'&&\s*rm',  # AND operator with rm
        r'\|\s*sh',  # Pipe to shell
        r'>\s*/dev/',  # Redirect to device
        r'<\s*\(',  # Process substitution
        r'eval\s+',  # eval command
        r'exec\s+',  # exec command
    ]
    
    # Maximum input length
    MAX_INPUT_LENGTH = 10000
    
    # Minimum input length
    MIN_INPUT_LENGTH = 1
    
    def __init__(self):
        self.suspicious_pattern_regex = re.compile(
            '|'.join(self.SUSPICIOUS_PATTERNS),
            re.IGNORECASE
        )
    
    def validate(self, user_input: str) -> ValidationResult:
        """
        Validate and sanitize user input
        
        Args:
            user_input: Raw user input string
            
        Returns:
            ValidationResult with validation status and sanitized input
        """
        # Check for None or empty
        if user_input is None:
            return ValidationResult(
                is_valid=False,
                sanitized_input="",
                error_message="Input cannot be None",
                risk_level="low"
            )
        
        # Convert to string if not already
        user_input = str(user_input)
        
        # Check length constraints
        if len(user_input) < self.MIN_INPUT_LENGTH:
            return ValidationResult(
                is_valid=False,
                sanitized_input="",
                error_message="Input is too short",
                risk_level="low"
            )
        
        if len(user_input) > self.MAX_INPUT_LENGTH:
            return ValidationResult(
                is_valid=False,
                sanitized_input="",
                error_message=f"Input exceeds maximum length of {self.MAX_INPUT_LENGTH} characters",
                risk_level="medium"
            )
        
        # Check for suspicious patterns
        if self.suspicious_pattern_regex.search(user_input):
            return ValidationResult(
                is_valid=False,
                sanitized_input="",
                error_message="Input contains potentially dangerous patterns",
                risk_level="high"
            )
        
        # Check for null bytes
        if '\x00' in user_input:
            return ValidationResult(
                is_valid=False,
                sanitized_input="",
                error_message="Input contains null bytes",
                risk_level="high"
            )
        
        # Sanitize input
        sanitized = self._sanitize(user_input)
        
        return ValidationResult(
            is_valid=True,
            sanitized_input=sanitized,
            error_message=None,
            risk_level="low"
        )
    
    def _sanitize(self, user_input: str) -> str:
        """
        Sanitize user input
        
        Args:
            user_input: Raw input string
            
        Returns:
            Sanitized input string
        """
        # Strip leading/trailing whitespace
        sanitized = user_input.strip()
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        
        # Normalize whitespace
        sanitized = ' '.join(sanitized.split())
        
        return sanitized
    
    def is_safe_for_llm(self, user_input: str) -> bool:
        """
        Check if input is safe to send to LLM
        
        Args:
            user_input: User input string
            
        Returns:
            True if safe, False otherwise
        """
        result = self.validate(user_input)
        return result.is_valid and result.risk_level == "low"
    
    def get_risk_assessment(self, user_input: str) -> Tuple[str, str]:
        """
        Get risk assessment for input
        
        Args:
            user_input: User input string
            
        Returns:
            Tuple of (risk_level, explanation)
        """
        result = self.validate(user_input)
        
        if not result.is_valid:
            return (result.risk_level, result.error_message or "Invalid input")
        
        # Additional risk assessment
        if any(keyword in user_input.lower() for keyword in ['password', 'secret', 'token', 'key']):
            return ("medium", "Input may contain sensitive information")
        
        if len(user_input) > 1000:
            return ("low", "Input is unusually long")
        
        return ("low", "Input appears safe")


# Global validator instance
validator = InputValidator()


def validate_input(user_input: str) -> ValidationResult:
    """
    Convenience function for input validation
    
    Args:
        user_input: User input string
        
    Returns:
        ValidationResult
    """
    return validator.validate(user_input)

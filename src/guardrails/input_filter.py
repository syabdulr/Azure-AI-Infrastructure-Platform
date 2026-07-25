"""
Input filter for Azure AI Infrastructure Platform

This module provides:
- PII detection and redaction
- Content filtering
- Input validation
- SQL injection detection
- XSS detection
"""

from typing import Dict, Any, List, Optional
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PIIDetector:
    """Detect and handle Personally Identifiable Information"""
    
    def __init__(self):
        """Initialize PII detector with patterns"""
        self.patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "credit_card": r'\b(?:\d{4}[- ]?){3}\d{4}\b',
            "ip_address": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            "date_of_birth": r'\b(?:0[1-9]|1[0-2])/(?:0[1-9]|[12]\d|3[01])/\d{4}\b'
        }
    
    def detect(self, text: str) -> Dict[str, List[str]]:
        """
        Detect PII in text
        
        Args:
            text: Input text to scan
            
        Returns:
            Dictionary with PII types and detected values
        """
        detected = {}
        
        for pii_type, pattern in self.patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                detected[pii_type] = matches
        
        return detected
    
    def redact(
        self,
        text: str,
        method: str = "mask"
    ) -> Dict[str, Any]:
        """
        Redact PII from text
        
        Args:
            text: Input text
            method: Redaction method (mask, hash, partial)
            
        Returns:
            Dictionary with:
            - redacted_text: Text with PII redacted
            - detected_pii: Dictionary of detected PII
            - count: Number of PII instances redacted
        """
        detected = self.detect(text)
        redacted_text = text
        count = 0
        
        for pii_type, pattern in self.patterns.items():
            if pii_type in detected:
                count += len(detected[pii_type])
                
                if method == "mask":
                    redacted_text = re.sub(
                        pattern,
                        f"[REDACTED {pii_type.upper()}]",
                        redacted_text,
                        flags=re.IGNORECASE
                    )
                elif method == "partial":
                    # Show partial (e.g., a***@email.com)
                    redacted_text = re.sub(
                        pattern,
                        self._partial_redact,
                        redacted_text,
                        flags=re.IGNORECASE
                    )
                elif method == "hash":
                    # Replace with hash
                    redacted_text = re.sub(
                        pattern,
                        lambda m: f"[HASH:{hash(m.group()) % 10000:04d}]",
                        redacted_text,
                        flags=re.IGNORECASE
                    )
        
        return {
            "redacted_text": redacted_text,
            "detected_pii": detected,
            "count": count
        }
    
    def _partial_redact(self, match: re.Match) -> str:
        """
        Partially redact matched PII
        
        Args:
            match: Regex match object
            
        Returns:
            Partially redacted string
        """
        text = match.group()
        
        # Email: show first character and domain
        if '@' in text:
            parts = text.split('@')
            if len(parts) == 2:
                username = parts[0]
                domain = parts[1]
                return f"{username[0]}***@{domain}"
        
        # Phone: show area code
        if re.match(r'\d{3}[-.]?\d{3}[-.]?\d{4}', text):
            digits = re.sub(r'[^0-9]', '', text)
            return f"({digits[:3]}) ***-{digits[-4:]}"
        
        # Default: show first and last characters
        if len(text) > 4:
            return f"{text[:2]}***{text[-2:]}"
        
        return "***"


class ContentFilter:
    """Filter harmful content"""
    
    def __init__(self):
        """Initialize content filter"""
        # Simplified keyword lists (in production, use AI-based filtering)
        self.hate_speech_keywords = [
            "hate", "discrimination", "racist", "sexist", "homophobic"
        ]
        
        self.violence_keywords = [
            "kill", "murder", "violence", "attack", "threat", "bomb"
        ]
        
        self.profanity_keywords = [
            # Profanity list (simplified for example)
        ]
        
        self.spam_patterns = [
            r'(buy now|click here|free money|winner)',
            r'\$+\d+(,\d{3})*(\.\d{2})?'
        ]
    
    def filter_input(self, text: str) -> Dict[str, Any]:
        """
        Filter input content
        
        Args:
            text: Input text to filter
            
        Returns:
            Dictionary with:
            - is_safe: bool
            - violations: list of violations
            - severity: low/medium/high
            - filtered_text: str
        """
        violations = []
        severity = "none"
        filtered_text = text.lower()
        
        # Check hate speech
        for keyword in self.hate_speech_keywords:
            if keyword in filtered_text:
                violations.append({
                    "type": "hate_speech",
                    "keyword": keyword,
                    "severity": "high"
                })
                severity = "high"
        
        # Check violence
        for keyword in self.violence_keywords:
            if keyword in filtered_text:
                violations.append({
                    "type": "violence",
                    "keyword": keyword,
                    "severity": "medium"
                })
                if severity == "none":
                    severity = "medium"
        
        # Check profanity
        for keyword in self.profanity_keywords:
            if keyword in filtered_text:
                violations.append({
                    "type": "profanity",
                    "keyword": keyword,
                    "severity": "low"
                })
                if severity == "none":
                    severity = "low"
        
        # Check spam patterns
        for pattern in self.spam_patterns:
            if re.search(pattern, filtered_text, re.IGNORECASE):
                violations.append({
                    "type": "spam",
                    "pattern": pattern,
                    "severity": "medium"
                })
                if severity in ["none", "low"]:
                    severity = "medium"
        
        is_safe = len(violations) == 0
        
        return {
            "is_safe": is_safe,
            "violations": violations,
            "severity": severity,
            "filtered_text": text
        }
    
    def filter_output(self, text: str) -> Dict[str, Any]:
        """
        Filter output content
        
        Args:
            text: Output text to filter
            
        Returns:
            Dictionary with safety assessment
        """
        # For now, use same filtering as input
        result = self.filter_input(text)
        return result


class InputFilter:
    """Main input filter coordinating PII and content filtering"""
    
    def __init__(self):
        """Initialize input filter"""
        self.pii_detector = PIIDetector()
        self.content_filter = ContentFilter()
    
    def check(
        self,
        text: str,
        redact_pii: bool = False,
        pii_redaction_method: str = "mask"
    ) -> Dict[str, Any]:
        """
        Perform all input checks
        
        Args:
            text: Input text to check
            redact_pii: Whether to redact PII
            pii_redaction_method: Method for PII redaction
            
        Returns:
            Dictionary with safety assessment
        """
        # Detect PII
        pii_detected = self.pii_detector.detect(text)
        
        # Filter content
        content_result = self.content_filter.filter_input(text)
        
        # Redact PII if requested
        filtered_text = text
        if redact_pii:
            pii_result = self.pii_detector.redact(text, method=pii_redaction_method)
            filtered_text = pii_result["redacted_text"]
        
        # Determine overall safety
        has_pii = len(pii_detected) > 0
        is_content_safe = content_result["is_safe"]
        
        # Determine severity
        if content_result["severity"] == "high":
            overall_severity = "high"
        elif content_result["severity"] == "medium":
            overall_severity = "medium"
        elif has_pii:
            overall_severity = "low"
        else:
            overall_severity = "none"
        
        is_safe = is_content_safe
        
        return {
            "is_safe": is_safe,
            "filtered_text": filtered_text,
            "pii_detected": pii_detected,
            "content_violations": content_result["violations"],
            "severity": overall_severity,
            "has_pii": has_pii,
            "is_content_safe": is_content_safe
        }
    
    def validate_input(
        self,
        text: str,
        max_length: int = 4000,
        min_length: int = 1
    ) -> Dict[str, Any]:
        """
        Validate input format and length
        
        Args:
            text: Input text to validate
            max_length: Maximum allowed length
            min_length: Minimum allowed length
            
        Returns:
            Dictionary with validation result
        """
        errors = []
        
        # Check length
        if len(text) < min_length:
            errors.append({
                "type": "too_short",
                "message": f"Input must be at least {min_length} characters"
            })
        
        if len(text) > max_length:
            errors.append({
                "type": "too_long",
                "message": f"Input must be no more than {max_length} characters"
            })
        
        # Check for SQL injection
        sql_patterns = [
            r"(?i)(\bunion\b.*\bselect\b|';?\bdrop\b.*\btable\b|';?\bdelete\b.*\bfrom\b)",
            r"(?i)(\bexec\b.*\bxp_cmdshell\b|';?\bexec\b.*\bsp_spaceused\b)"
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, text):
                errors.append({
                    "type": "sql_injection",
                    "message": "Potential SQL injection detected"
                })
                break
        
        # Check for XSS
        xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'on\w+\s*=\s*["\']javascript:',
            r'javascript:\w+'
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                errors.append({
                    "type": "xss",
                    "message": "Potential XSS attack detected"
                })
                break
        
        is_valid = len(errors) == 0
        
        return {
            "is_valid": is_valid,
            "errors": errors
        }


# Global instances
pii_detector = PIIDetector()
content_filter = ContentFilter()
input_filter = InputFilter()
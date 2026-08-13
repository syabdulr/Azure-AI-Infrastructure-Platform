"""Content detector for PII, harmful content, and prompt injection."""

import re
from typing import Any, Dict, List

from .models import SeverityLevel, ViolationType


class ContentDetector:
    """Detects PII, harmful content, and prompt injection in text."""

    # PII patterns
    SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    PHONE_PATTERN = re.compile(r"\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
    CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d{4}[-\s]){3}\d{4}\b")

    # Harmful content keywords (case-insensitive)
    HARMFUL_KEYWORDS = [
        "hack",
        "exploit",
        "malware",
        "phishing",
        "ransomware",
        "steal data",
        "inject sql",
        "bypass security",
        "crack password",
        "ddos",
        "social engineer",
        "keylogger",
        "backdoor",
    ]

    # Prompt injection patterns
    INJECTION_PATTERNS = [
        r"ignore (all |previous )?instructions",
        r"ignore (all |previous )?prompts",
        r"disregard (all |previous )?instructions",
        r"reveal (your |the )?system prompt",
        r"show (your |the )?system prompt",
        r"you are now (a |an )?\w+",
        r"act as (a |an )?\w+",
        r"pretend (you are |to be )",
        r"override (your |the )?(safety |content )?(guidelines|rules|policy)",
        r"jailbreak",
    ]

    def detect(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect all violations in the given text.

        Args:
            text: Text to analyze.

        Returns:
            List of violation dicts with type, severity, and matched content.
        """
        violations: List[Dict[str, Any]] = []
        violations.extend(self._detect_pii(text))
        violations.extend(self._detect_harmful(text))
        violations.extend(self._detect_injection(text))
        return violations

    def redact(self, text: str) -> str:
        """Redact PII from text."""
        text = self.SSN_PATTERN.sub("[REDACTED_SSN]", text)
        text = self.EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
        text = self.PHONE_PATTERN.sub("[REDACTED_PHONE]", text)
        text = self.CREDIT_CARD_PATTERN.sub("[REDACTED_CARD]", text)
        return text

    def _detect_pii(self, text: str) -> List[Dict[str, Any]]:
        """Detect PII patterns."""
        violations: List[Dict[str, Any]] = []

        if self.SSN_PATTERN.search(text):
            violations.append(
                {
                    "type": ViolationType.PII.value,
                    "severity": SeverityLevel.HIGH.value,
                    "detail": "SSN detected",
                }
            )

        if self.EMAIL_PATTERN.search(text):
            violations.append(
                {
                    "type": ViolationType.PII.value,
                    "severity": SeverityLevel.MEDIUM.value,
                    "detail": "Email address detected",
                }
            )

        if self.PHONE_PATTERN.search(text):
            violations.append(
                {
                    "type": ViolationType.PII.value,
                    "severity": SeverityLevel.MEDIUM.value,
                    "detail": "Phone number detected",
                }
            )

        if self.CREDIT_CARD_PATTERN.search(text):
            violations.append(
                {
                    "type": ViolationType.PII.value,
                    "severity": SeverityLevel.HIGH.value,
                    "detail": "Credit card number detected",
                }
            )

        return violations

    def _detect_harmful(self, text: str) -> List[Dict[str, Any]]:
        """Detect harmful content."""
        violations: List[Dict[str, Any]] = []
        text_lower = text.lower()

        for keyword in self.HARMFUL_KEYWORDS:
            if keyword in text_lower:
                violations.append(
                    {
                        "type": ViolationType.HARMFUL_CONTENT.value,
                        "severity": SeverityLevel.CRITICAL.value,
                        "detail": f"Harmful keyword detected: {keyword}",
                    }
                )

        return violations

    def _detect_injection(self, text: str) -> List[Dict[str, Any]]:
        """Detect prompt injection attempts."""
        violations: List[Dict[str, Any]] = []

        for pattern in self.INJECTION_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                violations.append(
                    {
                        "type": ViolationType.PROMPT_INJECTION.value,
                        "severity": SeverityLevel.CRITICAL.value,
                        "detail": f"Prompt injection pattern: {match.group()}",
                    }
                )

        return violations

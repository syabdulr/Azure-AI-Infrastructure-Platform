"""
Output filter for Azure AI Infrastructure Platform

This module provides:
- Safety checks for AI responses
- Content moderation
- Response validation
- PII redaction in responses
- Hallucination detection
"""

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SafetyChecker:
    """Check safety of AI responses"""

    def __init__(self):
        """Initialize safety checker"""
        # Safety guidelines
        self.safety_guidelines = [
            "no_harmful_instructions",
            "no_misinformation",
            "no_bias_or_discrimination",
            "no_personal_medical_advice",
            "no_legal_advice",
        ]

    def check_response(
        self, response: str, query: Optional[str] = None, context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if response is safe

        Args:
            response: AI response to check
            query: Original query
            context: Provided context (for RAG)

        Returns:
            Dictionary with safety assessment
        """
        violations = []
        severity = "none"

        # Check for harmful instructions
        harmful_patterns = [
            r"(how to|instructions for|steps to)\s*(make|create|build|produce)\s*(bomb|weapon|poison|drug)",
            r"(how to|instructions for)\s*(hack|attack|exploit|bypass)",
            r"(how to|instructions for)\s*(steal|rob|break into)",
        ]

        for pattern in harmful_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                violations.append(
                    {"type": "harmful_instructions", "pattern": pattern, "severity": "high"}
                )
                severity = "high"
                break

        # Check for unsubstantiated claims (hallucination detection)
        if context:
            unsubstantiated = self._check_hallucinations(response, context)
            if unsubstantiated:
                violations.append(
                    {
                        "type": "hallucination",
                        "unsubstantiated_claims": unsubstantiated,
                        "severity": "medium",
                    }
                )
                if severity == "none":
                    severity = "medium"

        # Check for bias
        bias_patterns = [
            r"(all|every)\s+(men|women|people from)\s+(are|always)",
            r"(certain groups|those people)\s+(can\'t|cannot|aren\'t)",
        ]

        for pattern in bias_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                violations.append({"type": "bias", "pattern": pattern, "severity": "medium"})
                if severity in ["none", "low"]:
                    severity = "medium"
                break

        # Check for medical advice
        medical_patterns = [
            r"(you should|you must|take)\s+(this|these)\s+(medication|drug|pill)",
            r"(diagnosis|treatment|prescribe)",
        ]

        for pattern in medical_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                violations.append(
                    {"type": "medical_advice", "pattern": pattern, "severity": "high"}
                )
                severity = "high"
                break

        # Check for legal advice
        legal_patterns = [
            r"(you should|you must|you need to)\s+(sue|file a lawsuit|take legal action)",
            r"(legal|lawsuit|court case)\s+(advice|guidance)",
        ]

        for pattern in legal_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                violations.append({"type": "legal_advice", "pattern": pattern, "severity": "high"})
                severity = "high"
                break

        is_safe = len(violations) == 0

        return {"is_safe": is_safe, "violations": violations, "severity": severity}

    def _check_hallucinations(self, response: str, context: str) -> List[str]:
        """
        Check for hallucinations (unsubstantiated claims)

        Args:
            response: AI response
            context: Provided context

        Returns:
            List of potentially unsubstantiated claims
        """
        # Simple heuristic: look for specific numbers/facts not in context
        unsubstantiated = []

        # Extract numbers from response
        response_numbers = re.findall(r"\b\d+(?:,\d{3})*(?:\.\d+)?\b", response)
        context_numbers = re.findall(r"\b\d+(?:,\d{3})*(?:\.\d+)?\b", context)

        # Check for numbers in response not in context
        for num in response_numbers:
            if num not in context_numbers:
                # Simple check (in production, use semantic matching)
                unsubstantiated.append(f"Number {num} not found in context")

        return unsubstantiated


class OutputFilter:
    """Main output filter coordinating safety checks"""

    def __init__(self):
        """Initialize output filter"""
        self.safety_checker = SafetyChecker()

    def check(
        self,
        response: str,
        query: Optional[str] = None,
        context: Optional[str] = None,
        redact_pii: bool = False,
    ) -> Dict[str, Any]:
        """
        Perform all output checks

        Args:
            response: Output text to check
            query: Original query
            context: Provided context
            redact_pii: Whether to redact PII

        Returns:
            Dictionary with safety assessment
        """
        # Check safety
        safety_result = self.safety_checker.check_response(
            response=response, query=query, context=context
        )

        # Detect PII
        from src.guardrails.input_filter import pii_detector

        pii_detected = pii_detector.detect(response)

        # Redact PII if requested
        filtered_text = response
        redacted_pii = []

        if redact_pii and pii_detected:
            pii_result = pii_detector.redact(response, method="mask")
            filtered_text = pii_result["redacted_text"]
            redacted_pii = list(pii_detected.keys())

        # Determine overall safety
        has_pii = len(pii_detected) > 0
        is_safe = safety_result["is_safe"]

        # Determine severity
        if safety_result["severity"] == "high":
            overall_severity = "high"
        elif safety_result["severity"] == "medium":
            overall_severity = "medium"
        elif has_pii:
            overall_severity = "low"
        else:
            overall_severity = "none"

        return {
            "is_safe": is_safe,
            "filtered_text": filtered_text,
            "violations": safety_result["violations"],
            "pii_detected": pii_detected,
            "redacted_pii": redacted_pii,
            "severity": overall_severity,
        }


# Global instances
safety_checker = SafetyChecker()
output_filter = OutputFilter()

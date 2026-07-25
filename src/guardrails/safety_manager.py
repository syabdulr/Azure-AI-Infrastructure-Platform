"""
Safety manager for Azure AI Infrastructure Platform

This module provides:
- Coordinate input/output filters
- Manage safety policies
- Log violations
- Alert on critical issues
- Policy configuration
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class SafetyPolicy:
    """Safety policy configuration"""
    
    def __init__(
        self,
        name: str,
        pii_detection_enabled: bool = True,
        content_filtering_enabled: bool = True,
        output_safety_checks_enabled: bool = True,
        rate_limiting_enabled: bool = True,
        auto_redact_pii: bool = False,
        block_on_violation: bool = True,
        violation_thresholds: Optional[Dict[str, int]] = None
    ):
        """
        Initialize safety policy
        
        Args:
            name: Policy name
            pii_detection_enabled: Enable PII detection
            content_filtering_enabled: Enable content filtering
            output_safety_checks_enabled: Enable output safety checks
            rate_limiting_enabled: Enable rate limiting
            auto_redact_pii: Auto-redact detected PII
            block_on_violation: Block requests on violation
            violation_thresholds: Thresholds for different severity levels
        """
        self.name = name
        self.pii_detection_enabled = pii_detection_enabled
        self.content_filtering_enabled = content_filtering_enabled
        self.output_safety_checks_enabled = output_safety_checks_enabled
        self.rate_limiting_enabled = rate_limiting_enabled
        self.auto_redact_pii = auto_redact_pii
        self.block_on_violation = block_on_violation
        
        # Default violation thresholds
        self.violation_thresholds = violation_thresholds or {
            "low": 10,  # 10 low-severity violations per hour
            "medium": 5,  # 5 medium-severity violations per hour
            "high": 1  # 1 high-severity violation per hour
        }


class SafetyManager:
    """Coordinate all safety and guardrail checks"""
    
    def __init__(self):
        """Initialize safety manager"""
        from src.guardrails.input_filter import input_filter, pii_detector
        from src.guardrails.output_filter import output_filter, safety_checker
        from src.guardrails.rate_limiter import rate_limiter
        
        self.input_filter = input_filter
        self.pii_detector = pii_detector
        self.output_filter = output_filter
        self.safety_checker = safety_checker
        self.rate_limiter = rate_limiter
        
        # Default policy
        self.default_policy = SafetyPolicy("default")
        self.policies = {"default": self.default_policy}
        
        # Violation tracking
        self.violations: List[Dict[str, Any]] = []
        self.user_violations: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        logger.info("Safety manager initialized")
    
    def check_input(
        self,
        user_id: str,
        text: str,
        endpoint: str,
        policy: Optional[SafetyPolicy] = None
    ) -> Dict[str, Any]:
        """
        Perform all input safety checks
        
        Args:
            user_id: User identifier
            text: Input text to check
            endpoint: API endpoint
            policy: Safety policy to use
            
        Returns:
            Dictionary with safety assessment
        """
        policy = policy or self.default_policy
        
        result = {
            "user_id": user_id,
            "endpoint": endpoint,
            "is_safe": True,
            "violations": [],
            "filtered_text": text,
            "blocked": False,
            "block_reason": None
        }
        
        # Check rate limits
        if policy.rate_limiting_enabled:
            rate_check = self.rate_limiter.check_limit(user_id, endpoint)
            if not rate_check["allowed"]:
                result["blocked"] = True
                result["block_reason"] = "rate_limit_exceeded"
                result["violations"].append({
                    "type": "rate_limit",
                    "severity": "medium",
                    "details": rate_check
                })
                self._log_violation(
                    "rate_limit",
                    user_id,
                    {"endpoint": endpoint, "details": rate_check},
                    "medium"
                )
                return result
        
        # Check input safety
        input_check = self.input_filter.check(
            text=text,
            redact_pii=policy.auto_redact_pii
        )
        
        # Add content violations
        for violation in input_check["content_violations"]:
            result["violations"].append({
                "type": violation["type"],
                "severity": violation["severity"],
                "details": violation
            })
            
            self._log_violation(
                violation["type"],
                user_id,
                {"endpoint": endpoint, "violation": violation},
                violation["severity"]
            )
        
        # Add PII violations
        if input_check["has_pii"]:
            result["violations"].append({
                "type": "pii_detected",
                "severity": "low",
                "details": input_check["pii_detected"]
            })
            
            self._log_violation(
                "pii_detected",
                user_id,
                {"endpoint": endpoint, "pii": input_check["pii_detected"]},
                "low"
            )
        
        # Update result
        result["filtered_text"] = input_check["filtered_text"]
        result["is_safe"] = input_check["is_safe"]
        
        # Check if should block
        if policy.block_on_violation:
            if not input_check["is_safe"]:
                result["blocked"] = True
                result["block_reason"] = "content_violation"
            elif input_check["severity"] == "high":
                result["blocked"] = True
                result["block_reason"] = "high_severity_violation"
        
        return result
    
    def check_output(
        self,
        user_id: str,
        text: str,
        query: Optional[str] = None,
        context: Optional[str] = None,
        policy: Optional[SafetyPolicy] = None
    ) -> Dict[str, Any]:
        """
        Perform all output safety checks
        
        Args:
            user_id: User identifier
            text: Output text to check
            query: Original query
            context: Provided context
            policy: Safety policy to use
            
        Returns:
            Dictionary with safety assessment
        """
        policy = policy or self.default_policy
        
        result = {
            "user_id": user_id,
            "is_safe": True,
            "violations": [],
            "filtered_text": text,
            "blocked": False,
            "block_reason": None
        }
        
        # Check output safety
        if policy.output_safety_checks_enabled:
            output_check = self.output_filter.check(
                response=text,
                query=query,
                context=context,
                redact_pii=policy.auto_redact_pii
            )
            
            # Add violations
            for violation in output_check["violations"]:
                result["violations"].append({
                    "type": violation["type"],
                    "severity": violation["severity"],
                    "details": violation
                })
                
                self._log_violation(
                    violation["type"],
                    user_id,
                    {"violation": violation},
                    violation["severity"]
                )
            
            # Add PII violations
            if output_check["pii_detected"]:
                result["violations"].append({
                    "type": "pii_in_output",
                    "severity": "low",
                    "details": output_check["pii_detected"]
                })
                
                self._log_violation(
                    "pii_in_output",
                    user_id,
                    {"pii": output_check["pii_detected"]},
                    "low"
                )
            
            # Update result
            result["filtered_text"] = output_check["filtered_text"]
            result["is_safe"] = output_check["is_safe"]
            
            # Check if should block
            if policy.block_on_violation and not output_check["is_safe"]:
                result["blocked"] = True
                result["block_reason"] = "safety_violation"
        
        return result
    
    def _log_violation(
        self,
        violation_type: str,
        user_id: str,
        details: Dict[str, Any],
        severity: str
    ):
        """
        Log a safety violation
        
        Args:
            violation_type: Type of violation
            user_id: User identifier
            details: Violation details
            severity: Severity level (low/medium/high)
        """
        violation = {
            "id": f"viol-{len(self.violations) + 1}",
            "type": violation_type,
            "user_id": user_id,
            "severity": severity,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add to global list
        self.violations.append(violation)
        
        # Add to user-specific list
        self.user_violations[user_id].append(violation)
        
        # Log
        log_message = f"Safety violation: {violation_type} (severity: {severity}) for user {user_id}"
        if severity == "high":
            logger.error(log_message)
        elif severity == "medium":
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def get_violations(
        self,
        user_id: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get safety violations
        
        Args:
            user_id: Filter by user (optional)
            severity: Filter by severity (optional)
            limit: Maximum number of results
            
        Returns:
            List of violations
        """
        violations = self.violations
        
        # Filter by user
        if user_id:
            violations = [v for v in violations if v["user_id"] == user_id]
        
        # Filter by severity
        if severity:
            violations = [v for v in violations if v["severity"] == severity]
        
        # Sort by timestamp (newest first) and limit
        violations = sorted(violations, key=lambda x: x["timestamp"], reverse=True)
        return violations[:limit]
    
    def get_user_violation_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get violation summary for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with violation summary
        """
        user_violations = self.user_violations.get(user_id, [])
        
        # Count by type
        type_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for violation in user_violations:
            type_counts[violation["type"]] += 1
            severity_counts[violation["severity"]] += 1
        
        return {
            "user_id": user_id,
            "total_violations": len(user_violations),
            "by_type": dict(type_counts),
            "by_severity": dict(severity_counts),
            "recent_violations": sorted(user_violations, key=lambda x: x["timestamp"], reverse=True)[:5]
        }
    
    def check_user_thresholds(self, user_id: str, policy: Optional[SafetyPolicy] = None) -> Dict[str, Any]:
        """
        Check if user has exceeded violation thresholds
        
        Args:
            user_id: User identifier
            policy: Safety policy to use
            
        Returns:
            Dictionary with threshold check results
        """
        policy = policy or self.default_policy
        summary = self.get_user_violation_summary(user_id)
        
        # Check thresholds
        exceeded = []
        
        for severity, threshold in policy.violation_thresholds.items():
            count = summary["by_severity"].get(severity, 0)
            if count >= threshold:
                exceeded.append({
                    "severity": severity,
                    "count": count,
                    "threshold": threshold,
                    "exceeded_by": count - threshold
                })
        
        return {
            "user_id": user_id,
            "exceeded_thresholds": exceeded,
            "blocked": len(exceeded) > 0
        }
    
    def add_policy(self, policy: SafetyPolicy):
        """
        Add a safety policy
        
        Args:
            policy: SafetyPolicy to add
        """
        self.policies[policy.name] = policy
        logger.info(f"Added safety policy: {policy.name}")
    
    def get_policy(self, name: str) -> Optional[SafetyPolicy]:
        """
        Get a safety policy by name
        
        Args:
            name: Policy name
            
        Returns:
            SafetyPolicy or None
        """
        return self.policies.get(name)
    
    def list_policies(self) -> List[str]:
        """
        List all policy names
        
        Returns:
            List of policy names
        """
        return list(self.policies.keys())
    
    def cleanup_old_violations(self, max_age_hours: int = 24):
        """
        Clean up old violations to prevent memory leaks
        
        Args:
            max_age_hours: Maximum age in hours
        """
        cutoff = datetime.utcnow().replace(hour=datetime.utcnow().hour - max_age_hours)
        
        # Clean global list
        original_count = len(self.violations)
        self.violations = [
            v for v in self.violations
            if datetime.fromisoformat(v["timestamp"]) > cutoff
        ]
        
        cleaned = original_count - len(self.violations)
        
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} old violations")
        
        # Clean user-specific lists
        for user_id in self.user_violations:
            self.user_violations[user_id] = [
                v for v in self.user_violations[user_id]
                if datetime.fromisoformat(v["timestamp"]) > cutoff
            ]


# Global instance
safety_manager = SafetyManager()
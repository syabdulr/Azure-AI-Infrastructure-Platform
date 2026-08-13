"""Guardrail engine for content checking and enforcement."""

from typing import Any, Dict, List, Optional

from .audit import AuditLogger
from .detector import ContentDetector
from .models import GuardrailAction, GuardrailResult, GuardrailRule, SeverityLevel, ViolationType


class GuardrailEngine:
    """Engine for evaluating content against guardrail rules."""

    def __init__(
        self,
        mode: str = "block",
        detector: Optional[ContentDetector] = None,
        audit_logger: Optional[AuditLogger] = None,
    ) -> None:
        """
        Initialize the guardrail engine.

        Args:
            mode: 'block' to block violations, 'redact' to redact PII and pass.
            detector: Content detector instance.
            audit_logger: Audit logger instance.
        """
        self.mode = mode
        self.detector = detector or ContentDetector()
        self.audit = audit_logger or AuditLogger()
        self.rules: Dict[str, GuardrailRule] = {}

    def add_rule(self, rule: GuardrailRule) -> None:
        """Add a guardrail rule."""
        self.rules[rule.name] = rule

    def remove_rule(self, name: str) -> None:
        """Remove a guardrail rule."""
        self.rules.pop(name, None)

    def get_rule(self, name: str) -> GuardrailRule:
        """Get a guardrail rule by name."""
        return self.rules[name]

    def disable_rule(self, name: str) -> None:
        """Disable a guardrail rule."""
        if name in self.rules:
            self.rules[name].enabled = False

    def enable_rule(self, name: str) -> None:
        """Enable a guardrail rule."""
        if name in self.rules:
            self.rules[name].enabled = True

    def check(
        self,
        prompt: str,
        output: str,
        request_id: Optional[str] = None,
        provider: str = "unknown",
        model: str = "unknown",
    ) -> GuardrailResult:
        """
        Check a prompt and output against all active guardrail rules.

        Args:
            prompt: The user's input prompt.
            output: The model's output to check.
            request_id: Optional request ID for audit trail.
            provider: Provider name for audit.
            model: Model name for audit.

        Returns:
            GuardrailResult with violations and actions.
        """
        # Combine prompt and output for detection
        combined_text = f"{prompt}\n{output}"
        detected_violations = self.detector.detect(combined_text)

        # Map detected violations to active rules
        violations: List[Dict[str, Any]] = []
        triggered_rules: List[GuardrailRule] = []

        for dv in detected_violations:
            for rule in self.rules.values():
                if not rule.enabled:
                    continue
                if rule.violation_type.value == dv["type"]:
                    violations.append(
                        {
                            **dv,
                            "rule": rule.name,
                            "severity": rule.severity.value,
                        }
                    )
                    triggered_rules.append(rule)

        # Redact mode: redact PII and pass
        if self.mode == "redact":
            sanitized = self.detector.redact(output)
            has_pii = any(v["type"] == ViolationType.PII.value for v in violations)
            if has_pii:
                result = GuardrailResult(
                    passed=True,
                    violations=violations,
                    sanitized_output=sanitized,
                )
            else:
                result = GuardrailResult(
                    passed=True,
                    violations=[],
                    sanitized_output=output,
                )
        else:
            # Block mode
            if not violations:
                result = GuardrailResult(
                    passed=True,
                    violations=[],
                    sanitized_output=output,
                )
            else:
                # Determine action from highest severity rule
                redirect = any(r.action.redirect_to_human for r in triggered_rules)
                sanitized = output

                # Find the sanitized output from the first triggered rule that has one
                for r in triggered_rules:
                    if r.action.sanitized_output:
                        sanitized = r.action.sanitized_output
                        break

                # If no custom sanitized output, try redacting
                if sanitized == output and violations:
                    sanitized = self.detector.redact(output)

                result = GuardrailResult(
                    passed=False,
                    violations=violations,
                    sanitized_output=sanitized,
                    redirect_to_human=redirect,
                )

        # Audit log
        action = "allowed" if result.passed else "blocked"
        self.audit.log(
            request_id=request_id or "unknown",
            prompt=prompt,
            provider=provider,
            model=model,
            action=action,
            violations=violations,
        )

        return result

    def get_audit_log(self) -> AuditLogger:
        """Get the audit logger."""
        return self.audit

    def get_blocked_stats(self) -> Dict[str, Any]:
        """Get statistics on blocked vs allowed requests."""
        total = self.audit.entry_count
        blocked = len(self.audit.get_entries(action="blocked"))
        allowed = len(self.audit.get_entries(action="allowed"))
        return {
            "total_checks": total,
            "blocked": blocked,
            "allowed": allowed,
        }

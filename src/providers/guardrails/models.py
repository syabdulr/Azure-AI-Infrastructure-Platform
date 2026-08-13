"""Models for responsible AI guardrails module."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SeverityLevel(Enum):
    """Severity levels for guardrail violations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ViolationType(Enum):
    """Types of guardrail violations."""

    PII = "pii"
    HARMFUL_CONTENT = "harmful_content"
    PROMPT_INJECTION = "prompt_injection"
    OFF_TOPIC = "off_topic"


@dataclass
class GuardrailAction:
    """Action to take when a guardrail rule is triggered."""

    block: bool = False
    redirect_to_human: bool = False
    sanitized_output: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "block": self.block,
            "redirect_to_human": self.redirect_to_human,
            "sanitized_output": self.sanitized_output,
        }


@dataclass
class GuardrailRule:
    """A single guardrail rule."""

    name: str
    description: str
    violation_type: ViolationType
    severity: SeverityLevel
    action: GuardrailAction
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "violation_type": self.violation_type.value,
            "severity": self.severity.value,
            "action": self.action.to_dict(),
            "enabled": self.enabled,
        }


@dataclass
class GuardrailResult:
    """Result of a guardrail check."""

    passed: bool
    violations: List[Dict[str, Any]] = field(default_factory=list)
    sanitized_output: Optional[str] = None
    redirect_to_human: bool = False

    @property
    def is_blocked(self) -> bool:
        return not self.passed and any(
            v.get("severity") == SeverityLevel.HIGH.value
            or v.get("severity") == SeverityLevel.CRITICAL.value
            for v in self.violations
        )

    @property
    def needs_human_review(self) -> bool:
        return self.redirect_to_human

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "is_blocked": self.is_blocked,
            "violations": self.violations,
            "sanitized_output": self.sanitized_output,
            "redirect_to_human": self.redirect_to_human,
        }

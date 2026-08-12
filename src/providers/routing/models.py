"""Models for custom routing rules engine."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional, Set, Union

from src.providers.models import GatewayRequest, ModelCapability, RoutingStrategy


class RulePriority(Enum):
    """Priority level for routing rules."""

    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class RuleOperator(Enum):
    """Operators for rule conditions."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    HAS_CAPABILITY = "has_capability"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"


@dataclass
class RuleCondition:
    """A condition that must be met for a rule to match."""

    field: str
    operator: RuleOperator
    value: Any

    def matches(self, request: GatewayRequest) -> bool:
        """
        Check if this condition matches the given request.

        Args:
            request: The gateway request to evaluate

        Returns:
            True if condition matches
        """
        request_value = getattr(request, self.field, None)

        if self.operator == RuleOperator.EQUALS:
            return bool(request_value == self.value)

        elif self.operator == RuleOperator.NOT_EQUALS:
            return bool(request_value != self.value)

        elif self.operator == RuleOperator.CONTAINS:
            if request_value is None:
                return False
            return self.value in request_value

        elif self.operator == RuleOperator.NOT_CONTAINS:
            if request_value is None:
                return True
            return self.value not in request_value

        elif self.operator == RuleOperator.IN:
            if request_value is None:
                return False
            return request_value in self.value

        elif self.operator == RuleOperator.NOT_IN:
            if request_value is None:
                return True
            return request_value not in self.value

        elif self.operator == RuleOperator.HAS_CAPABILITY:
            if request_value is None:
                return False
            return self.value in request_value

        elif self.operator == RuleOperator.GREATER_THAN:
            if request_value is None:
                return False
            return bool(request_value > self.value)

        elif self.operator == RuleOperator.LESS_THAN:
            if request_value is None:
                return False
            return bool(request_value < self.value)

        return False


@dataclass
class RuleAction:
    """The action to take when a rule matches."""

    target_provider: str
    target_model: str
    reason: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "target_provider": self.target_provider,
            "target_model": self.target_model,
            "reason": self.reason,
        }


@dataclass
class RoutingRule:
    """A routing rule with conditions and an action."""

    name: str
    priority: RulePriority
    conditions: List[RuleCondition]
    action: RuleAction
    enabled: bool = True
    description: str = ""

    def matches(self, request: GatewayRequest) -> bool:
        """
        Check if all conditions in this rule match the request.

        Args:
            request: The gateway request to evaluate

        Returns:
            True if all conditions match (empty conditions = match all)
        """
        if not self.enabled:
            return False

        if not self.conditions:
            return True  # Catch-all rule

        return all(condition.matches(request) for condition in self.conditions)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "priority": self.priority.name,
            "conditions": [
                {"field": c.field, "operator": c.operator.value, "value": str(c.value)}
                for c in self.conditions
            ],
            "action": self.action.to_dict(),
            "enabled": self.enabled,
            "description": self.description,
        }


class RoutingRuleSet:
    """Manages a set of routing rules with priority ordering."""

    def __init__(self) -> None:
        """Initialize empty rule set."""
        self._rules: List[RoutingRule] = []

    @property
    def rules(self) -> List[RoutingRule]:
        """Get rules sorted by priority (highest first)."""
        return sorted(self._rules, key=lambda r: r.priority.value)

    def add_rule(self, rule: RoutingRule) -> None:
        """Add a rule to the set."""
        self._rules.append(rule)

    def remove_rule(self, name: str) -> bool:
        """Remove a rule by name. Returns True if removed."""
        for i, rule in enumerate(self._rules):
            if rule.name == name:
                self._rules.pop(i)
                return True
        return False

    def get_rule(self, name: str) -> Optional[RoutingRule]:
        """Get a rule by name."""
        for rule in self._rules:
            if rule.name == name:
                return rule
        return None

    def enable_rule(self, name: str) -> bool:
        """Enable a rule by name."""
        rule = self.get_rule(name)
        if rule:
            rule.enabled = True
            return True
        return False

    def disable_rule(self, name: str) -> bool:
        """Disable a rule by name."""
        rule = self.get_rule(name)
        if rule:
            rule.enabled = False
            return True
        return False

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {"rules": [r.to_dict() for r in self.rules]}

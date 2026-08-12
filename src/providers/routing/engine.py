"""Routing rule engine for evaluating custom routing rules."""

from typing import Optional

from src.providers.models import GatewayRequest, RoutingDecision, RoutingStrategy

from .models import RoutingRule, RoutingRuleSet, RulePriority

# Map priority to confidence score
PRIORITY_CONFIDENCE: dict = {
    RulePriority.CRITICAL: 1.0,
    RulePriority.HIGH: 0.9,
    RulePriority.MEDIUM: 0.75,
    RulePriority.LOW: 0.6,
}


class RoutingRuleEngine:
    """Evaluates custom routing rules against incoming requests."""

    def __init__(self, ruleset: RoutingRuleSet) -> None:
        """Initialize with a rule set."""
        self.ruleset = ruleset

    def evaluate(self, request: GatewayRequest) -> Optional[RoutingDecision]:
        """
        Evaluate rules against the request and return a routing decision.

        Rules are evaluated in priority order (highest first).
        The first matching rule wins.

        Args:
            request: The gateway request to route

        Returns:
            RoutingDecision if a rule matches, None otherwise
        """
        for rule in self.ruleset.rules:
            if rule.matches(request):
                return self._create_decision(rule)

        return None

    def _create_decision(self, rule: RoutingRule) -> RoutingDecision:
        """Create a routing decision from a matched rule."""
        confidence = PRIORITY_CONFIDENCE.get(rule.priority, 0.7)

        reason = rule.action.reason or f"Matched rule: {rule.name}"

        # Collect alternate providers from remaining rules
        alternate_providers: list = []
        for other_rule in self.ruleset.rules:
            if other_rule.name != rule.name:
                provider = other_rule.action.target_provider
                if provider not in alternate_providers:
                    alternate_providers.append(provider)

        return RoutingDecision(
            provider_name=rule.action.target_provider,
            model_name=rule.action.target_model,
            strategy=RoutingStrategy.CUSTOM_RULES,
            reason=reason,
            confidence=confidence,
            alternate_providers=alternate_providers,
        )

    def add_rule(self, rule: RoutingRule) -> None:
        """Add a rule to the engine's rule set."""
        self.ruleset.add_rule(rule)

    def remove_rule(self, name: str) -> bool:
        """Remove a rule by name."""
        return self.ruleset.remove_rule(name)

    def get_rule(self, name: str) -> Optional[RoutingRule]:
        """Get a rule by name."""
        return self.ruleset.get_rule(name)

    def list_rules(self) -> list:
        """List all rule names."""
        return [rule.name for rule in self.ruleset.rules]

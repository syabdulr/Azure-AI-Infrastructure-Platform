"""Tests for custom routing rules engine."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.providers.models import GatewayRequest, ModelCapability, RoutingStrategy
from src.providers.routing.engine import RoutingRuleEngine
from src.providers.routing.models import (
    RoutingRule,
    RoutingRuleSet,
    RuleAction,
    RuleCondition,
    RuleOperator,
    RulePriority,
)


class TestRuleCondition:
    """Test rule condition evaluation."""

    def test_condition_creation(self):
        """Test creating a rule condition."""
        condition = RuleCondition(
            field="tenant_id",
            operator=RuleOperator.EQUALS,
            value="tenant_acme",
        )
        assert condition.field == "tenant_id"
        assert condition.operator == RuleOperator.EQUALS
        assert condition.value == "tenant_acme"

    def test_condition_equals_match(self):
        """Test equals operator matches."""
        condition = RuleCondition(
            field="tenant_id",
            operator=RuleOperator.EQUALS,
            value="tenant_acme",
        )
        request = GatewayRequest(prompt="test", tenant_id="tenant_acme")
        assert condition.matches(request) is True

    def test_condition_equals_no_match(self):
        """Test equals operator does not match."""
        condition = RuleCondition(
            field="tenant_id",
            operator=RuleOperator.EQUALS,
            value="tenant_acme",
        )
        request = GatewayRequest(prompt="test", tenant_id="tenant_other")
        assert condition.matches(request) is False

    def test_condition_equals_none_value(self):
        """Test equals when request field is None."""
        condition = RuleCondition(
            field="tenant_id",
            operator=RuleOperator.EQUALS,
            value="tenant_acme",
        )
        request = GatewayRequest(prompt="test")
        assert condition.matches(request) is False

    def test_condition_contains_match(self):
        """Test contains operator matches substring."""
        condition = RuleCondition(
            field="prompt",
            operator=RuleOperator.CONTAINS,
            value="code",
        )
        request = GatewayRequest(prompt="Please write code for me")
        assert condition.matches(request) is True

    def test_condition_contains_no_match(self):
        """Test contains operator does not match."""
        condition = RuleCondition(
            field="prompt",
            operator=RuleOperator.CONTAINS,
            value="python",
        )
        request = GatewayRequest(prompt="Write some code")
        assert condition.matches(request) is False

    def test_condition_in_match(self):
        """Test 'in' operator matches list membership."""
        condition = RuleCondition(
            field="tenant_id",
            operator=RuleOperator.IN,
            value=["tenant_a", "tenant_b", "tenant_c"],
        )
        request = GatewayRequest(prompt="test", tenant_id="tenant_b")
        assert condition.matches(request) is True

    def test_condition_in_no_match(self):
        """Test 'in' operator does not match."""
        condition = RuleCondition(
            field="tenant_id",
            operator=RuleOperator.IN,
            value=["tenant_a", "tenant_b"],
        )
        request = GatewayRequest(prompt="test", tenant_id="tenant_x")
        assert condition.matches(request) is False

    def test_condition_has_capability_match(self):
        """Test has_capability operator matches."""
        condition = RuleCondition(
            field="model_requirements",
            operator=RuleOperator.HAS_CAPABILITY,
            value=ModelCapability.CODE,
        )
        request = GatewayRequest(
            prompt="test",
            model_requirements={ModelCapability.CODE},
        )
        assert condition.matches(request) is True

    def test_condition_has_capability_no_match(self):
        """Test has_capability does not match."""
        condition = RuleCondition(
            field="model_requirements",
            operator=RuleOperator.HAS_CAPABILITY,
            value=ModelCapability.CODE,
        )
        request = GatewayRequest(
            prompt="test",
            model_requirements={ModelCapability.CHAT},
        )
        assert condition.matches(request) is False


class TestRoutingRule:
    """Test routing rule evaluation."""

    def test_rule_single_condition_match(self):
        """Test rule with single matching condition."""
        rule = RoutingRule(
            name="enterprise_tenant",
            priority=RulePriority.HIGH,
            conditions=[
                RuleCondition(
                    field="tenant_id",
                    operator=RuleOperator.EQUALS,
                    value="enterprise",
                )
            ],
            action=RuleAction(
                target_provider="azure_openai",
                target_model="gpt-4",
            ),
        )
        request = GatewayRequest(prompt="test", tenant_id="enterprise")
        assert rule.matches(request) is True

    def test_rule_single_condition_no_match(self):
        """Test rule with non-matching condition."""
        rule = RoutingRule(
            name="enterprise_tenant",
            priority=RulePriority.HIGH,
            conditions=[
                RuleCondition(
                    field="tenant_id",
                    operator=RuleOperator.EQUALS,
                    value="enterprise",
                )
            ],
            action=RuleAction(
                target_provider="azure_openai",
                target_model="gpt-4",
            ),
        )
        request = GatewayRequest(prompt="test", tenant_id="free")
        assert rule.matches(request) is False

    def test_rule_multiple_conditions_all_match(self):
        """Test rule with multiple conditions, all matching."""
        rule = RoutingRule(
            name="enterprise_code_request",
            priority=RulePriority.HIGH,
            conditions=[
                RuleCondition(
                    field="tenant_id",
                    operator=RuleOperator.EQUALS,
                    value="enterprise",
                ),
                RuleCondition(
                    field="prompt",
                    operator=RuleOperator.CONTAINS,
                    value="code",
                ),
            ],
            action=RuleAction(
                target_provider="azure_openai",
                target_model="gpt-4",
            ),
        )
        request = GatewayRequest(prompt="write code", tenant_id="enterprise")
        assert rule.matches(request) is True

    def test_rule_multiple_conditions_partial_match(self):
        """Test rule with multiple conditions, only one matching."""
        rule = RoutingRule(
            name="enterprise_code_request",
            priority=RulePriority.HIGH,
            conditions=[
                RuleCondition(
                    field="tenant_id",
                    operator=RuleOperator.EQUALS,
                    value="enterprise",
                ),
                RuleCondition(
                    field="prompt",
                    operator=RuleOperator.CONTAINS,
                    value="code",
                ),
            ],
            action=RuleAction(
                target_provider="azure_openai",
                target_model="gpt-4",
            ),
        )
        request = GatewayRequest(prompt="write essay", tenant_id="enterprise")
        assert rule.matches(request) is False

    def test_rule_no_conditions_matches_all(self):
        """Test rule with no conditions matches everything (catch-all)."""
        rule = RoutingRule(
            name="catch_all",
            priority=RulePriority.LOW,
            conditions=[],
            action=RuleAction(
                target_provider="openai",
                target_model="gpt-3.5-turbo",
            ),
        )
        request = GatewayRequest(prompt="anything")
        assert rule.matches(request) is True


class TestRoutingRuleSet:
    """Test rule set management."""

    def test_ruleset_creation(self):
        """Test creating an empty rule set."""
        ruleset = RoutingRuleSet()
        assert len(ruleset.rules) == 0

    def test_ruleset_add_rule(self):
        """Test adding a rule to the set."""
        ruleset = RoutingRuleSet()
        rule = RoutingRule(
            name="test_rule",
            priority=RulePriority.MEDIUM,
            conditions=[],
            action=RuleAction(
                target_provider="openai",
                target_model="gpt-3.5-turbo",
            ),
        )
        ruleset.add_rule(rule)
        assert len(ruleset.rules) == 1
        assert ruleset.rules[0].name == "test_rule"

    def test_ruleset_sorted_by_priority(self):
        """Test rules are evaluated in priority order."""
        ruleset = RoutingRuleSet()
        low_rule = RoutingRule(
            name="low_priority",
            priority=RulePriority.LOW,
            conditions=[],
            action=RuleAction(target_provider="openai", target_model="gpt-3.5-turbo"),
        )
        high_rule = RoutingRule(
            name="high_priority",
            priority=RulePriority.HIGH,
            conditions=[],
            action=RuleAction(target_provider="azure_openai", target_model="gpt-4"),
        )
        ruleset.add_rule(low_rule)
        ruleset.add_rule(high_rule)
        # HIGH should come before LOW
        assert ruleset.rules[0].name == "high_priority"
        assert ruleset.rules[1].name == "low_priority"

    def test_ruleset_remove_rule(self):
        """Test removing a rule by name."""
        ruleset = RoutingRuleSet()
        rule = RoutingRule(
            name="test_rule",
            priority=RulePriority.MEDIUM,
            conditions=[],
            action=RuleAction(target_provider="openai", target_model="gpt-3.5-turbo"),
        )
        ruleset.add_rule(rule)
        assert len(ruleset.rules) == 1

        removed = ruleset.remove_rule("test_rule")
        assert removed is True
        assert len(ruleset.rules) == 0

    def test_ruleset_remove_nonexistent_rule(self):
        """Test removing a rule that doesn't exist."""
        ruleset = RoutingRuleSet()
        removed = ruleset.remove_rule("nonexistent")
        assert removed is False


class TestRoutingRuleEngine:
    """Test the rule engine that evaluates rules and makes decisions."""

    def test_engine_creation(self):
        """Test creating a rule engine."""
        ruleset = RoutingRuleSet()
        engine = RoutingRuleEngine(ruleset)
        assert engine.ruleset is not None

    def test_engine_no_rules_returns_none(self):
        """Test engine returns None when no rules match."""
        ruleset = RoutingRuleSet()
        engine = RoutingRuleEngine(ruleset)
        request = GatewayRequest(prompt="test")
        decision = engine.evaluate(request)
        assert decision is None

    def test_engine_matches_first_rule(self):
        """Test engine matches the first (highest priority) matching rule."""
        ruleset = RoutingRuleSet()
        ruleset.add_rule(
            RoutingRule(
                name="enterprise_route",
                priority=RulePriority.HIGH,
                conditions=[
                    RuleCondition(
                        field="tenant_id",
                        operator=RuleOperator.EQUALS,
                        value="enterprise",
                    )
                ],
                action=RuleAction(
                    target_provider="azure_openai",
                    target_model="gpt-4",
                    reason="Enterprise tenant routed to premium",
                ),
            )
        )
        engine = RoutingRuleEngine(ruleset)
        request = GatewayRequest(prompt="test", tenant_id="enterprise")
        decision = engine.evaluate(request)
        assert decision is not None
        assert decision.provider_name == "azure_openai"
        assert decision.model_name == "gpt-4"
        assert decision.strategy == RoutingStrategy.CUSTOM_RULES

    def test_engine_falls_through_to_lower_priority(self):
        """Test engine evaluates lower priority rules when higher don't match."""
        ruleset = RoutingRuleSet()

        # High priority rule that won't match
        ruleset.add_rule(
            RoutingRule(
                name="enterprise_only",
                priority=RulePriority.HIGH,
                conditions=[
                    RuleCondition(
                        field="tenant_id",
                        operator=RuleOperator.EQUALS,
                        value="enterprise",
                    )
                ],
                action=RuleAction(target_provider="azure_openai", target_model="gpt-4"),
            )
        )

        # Low priority catch-all
        ruleset.add_rule(
            RoutingRule(
                name="default",
                priority=RulePriority.LOW,
                conditions=[],
                action=RuleAction(target_provider="openai", target_model="gpt-3.5-turbo"),
            )
        )

        engine = RoutingRuleEngine(ruleset)
        request = GatewayRequest(prompt="test", tenant_id="free_tier")
        decision = engine.evaluate(request)
        assert decision is not None
        assert decision.provider_name == "openai"
        assert decision.model_name == "gpt-3.5-turbo"

    def test_engine_action_with_reason(self):
        """Test that engine passes reason from action to decision."""
        ruleset = RoutingRuleSet()
        ruleset.add_rule(
            RoutingRule(
                name="coded_rule",
                priority=RulePriority.MEDIUM,
                conditions=[
                    RuleCondition(
                        field="prompt",
                        operator=RuleOperator.CONTAINS,
                        value="code",
                    )
                ],
                action=RuleAction(
                    target_provider="azure_openai",
                    target_model="gpt-4",
                    reason="Code request routed to capable model",
                ),
            )
        )
        engine = RoutingRuleEngine(ruleset)
        request = GatewayRequest(prompt="write code please")
        decision = engine.evaluate(request)
        assert decision is not None
        assert "Code request" in decision.reason

    def test_engine_confidence_based_on_priority(self):
        """Test that higher priority rules have higher confidence."""
        ruleset = RoutingRuleSet()
        ruleset.add_rule(
            RoutingRule(
                name="critical_rule",
                priority=RulePriority.CRITICAL,
                conditions=[],
                action=RuleAction(target_provider="azure_openai", target_model="gpt-4"),
            )
        )
        engine = RoutingRuleEngine(ruleset)
        request = GatewayRequest(prompt="test")
        decision = engine.evaluate(request)
        assert decision is not None
        assert decision.confidence == 1.0

    def test_engine_capability_based_routing(self):
        """Test routing based on model capabilities."""
        ruleset = RoutingRuleSet()
        ruleset.add_rule(
            RoutingRule(
                name="code_capability",
                priority=RulePriority.HIGH,
                conditions=[
                    RuleCondition(
                        field="model_requirements",
                        operator=RuleOperator.HAS_CAPABILITY,
                        value=ModelCapability.CODE,
                    )
                ],
                action=RuleAction(target_provider="azure_openai", target_model="gpt-4"),
            )
        )
        engine = RoutingRuleEngine(ruleset)
        request = GatewayRequest(
            prompt="test",
            model_requirements={ModelCapability.CODE},
        )
        decision = engine.evaluate(request)
        assert decision is not None
        assert decision.provider_name == "azure_openai"

    def test_engine_in_operator_routing(self):
        """Test routing with 'in' operator for multi-tenant."""
        ruleset = RoutingRuleSet()
        ruleset.add_rule(
            RoutingRule(
                name="vip_tenants",
                priority=RulePriority.HIGH,
                conditions=[
                    RuleCondition(
                        field="tenant_id",
                        operator=RuleOperator.IN,
                        value=["vip_1", "vip_2", "vip_3"],
                    )
                ],
                action=RuleAction(target_provider="azure_openai", target_model="gpt-4"),
            )
        )
        engine = RoutingRuleEngine(ruleset)
        request = GatewayRequest(prompt="test", tenant_id="vip_2")
        decision = engine.evaluate(request)
        assert decision is not None
        assert decision.provider_name == "azure_openai"

    def test_engine_disabled_rule_skipped(self):
        """Test that disabled rules are skipped."""
        ruleset = RoutingRuleSet()
        rule = RoutingRule(
            name="disabled_rule",
            priority=RulePriority.HIGH,
            conditions=[],
            action=RuleAction(target_provider="azure_openai", target_model="gpt-4"),
            enabled=False,
        )
        ruleset.add_rule(rule)
        engine = RoutingRuleEngine(ruleset)
        request = GatewayRequest(prompt="test")
        decision = engine.evaluate(request)
        assert decision is None  # No matching rule since it's disabled

    def test_engine_add_rule_dynamically(self):
        """Test adding rules to the engine at runtime."""
        ruleset = RoutingRuleSet()
        engine = RoutingRuleEngine(ruleset)

        # Initially no match
        request = GatewayRequest(prompt="test")
        assert engine.evaluate(request) is None

        # Add a rule dynamically
        engine.add_rule(
            RoutingRule(
                name="dynamic_rule",
                priority=RulePriority.MEDIUM,
                conditions=[],
                action=RuleAction(target_provider="openai", target_model="gpt-3.5-turbo"),
            )
        )

        # Now it should match
        decision = engine.evaluate(request)
        assert decision is not None
        assert decision.provider_name == "openai"

    def test_engine_get_rule_by_name(self):
        """Test retrieving a rule by name."""
        ruleset = RoutingRuleSet()
        rule = RoutingRule(
            name="findable_rule",
            priority=RulePriority.MEDIUM,
            conditions=[],
            action=RuleAction(target_provider="openai", target_model="gpt-3.5-turbo"),
        )
        ruleset.add_rule(rule)
        engine = RoutingRuleEngine(ruleset)

        found = engine.get_rule("findable_rule")
        assert found is not None
        assert found.name == "findable_rule"

        not_found = engine.get_rule("nonexistent")
        assert not_found is None

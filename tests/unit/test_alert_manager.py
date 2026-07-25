"""Unit tests for alert manager"""

import pytest
from src.monitoring.alert_manager import (
    AlertRule,
    Alert,
    AlertManager
)


# ============================================================================
# AlertRule Tests
# ============================================================================

@pytest.mark.unit
class TestAlertRule:
    """Test AlertRule"""
    
    def test_alert_rule_init(self):
        """Test alert rule initialization"""
        rule = AlertRule(
            name="test_rule",
            metric_name="test_metric",
            condition="gt",
            threshold=0.9,
            window_seconds=300,
            severity="high",
            action="notify_team",
            enabled=True
        )
        
        assert rule.name == "test_rule"
        assert rule.metric_name == "test_metric"
        assert rule.condition == "gt"
        assert rule.threshold == 0.9
        assert rule.window_seconds == 300
        assert rule.severity == "high"
        assert rule.action == "notify_team"
        assert rule.enabled is True
    
    def test_alert_rule_evaluate_gt(self):
        """Test alert rule evaluate with gt condition"""
        rule = AlertRule(
            name="test_rule",
            metric_name="test_metric",
            condition="gt",
            threshold=0.9,
            window_seconds=300,
            severity="high",
            action="notify_team"
        )
        
        assert rule.evaluate(0.95) is True
        assert rule.evaluate(0.85) is False
    
    def test_alert_rule_evaluate_lt(self):
        """Test alert rule evaluate with lt condition"""
        rule = AlertRule(
            name="test_rule",
            metric_name="test_metric",
            condition="lt",
            threshold=0.1,
            window_seconds=300,
            severity="high",
            action="notify_team"
        )
        
        assert rule.evaluate(0.05) is True
        assert rule.evaluate(0.15) is False
    
    def test_alert_rule_evaluate_gte(self):
        """Test alert rule evaluate with gte condition"""
        rule = AlertRule(
            name="test_rule",
            metric_name="test_metric",
            condition="gte",
            threshold=0.9,
            window_seconds=300,
            severity="high",
            action="notify_team"
        )
        
        assert rule.evaluate(0.9) is True
        assert rule.evaluate(1.0) is True
        assert rule.evaluate(0.85) is False
    
    def test_alert_rule_evaluate_disabled(self):
        """Test alert rule when disabled"""
        rule = AlertRule(
            name="test_rule",
            metric_name="test_metric",
            condition="gt",
            threshold=0.9,
            window_seconds=300,
            severity="high",
            action="notify_team",
            enabled=False
        )
        
        assert rule.evaluate(0.95) is False
    
    def test_alert_rule_to_dict(self):
        """Test alert rule to dictionary"""
        rule = AlertRule(
            name="test_rule",
            metric_name="test_metric",
            condition="gt",
            threshold=0.9,
            window_seconds=300,
            severity="high",
            action="notify_team"
        )
        
        rule_dict = rule.to_dict()
        assert rule_dict["name"] == "test_rule"
        assert rule_dict["metric_name"] == "test_metric"
        assert rule_dict["condition"] == "gt"
        assert rule_dict["threshold"] == 0.9


# ============================================================================
# Alert Tests
# ============================================================================

@pytest.mark.unit
class TestAlert:
    """Test Alert"""
    
    def test_alert_init(self):
        """Test alert initialization"""
        alert = Alert(
            rule_name="test_rule",
            value=0.95,
            threshold=0.9,
            message="Test alert",
            severity="high",
            context={"metric": "test_metric"}
        )
        
        assert alert.rule_name == "test_rule"
        assert alert.value == 0.95
        assert alert.threshold == 0.9
        assert alert.message == "Test alert"
        assert alert.severity == "high"
        assert alert.active is True
        assert alert.resolved_at is None
    
    def test_alert_resolve(self):
        """Test alert resolution"""
        alert = Alert(
            rule_name="test_rule",
            value=0.95,
            threshold=0.9,
            message="Test alert",
            severity="high"
        )
        
        alert.resolve()
        assert alert.active is False
        assert alert.resolved_at is not None
    
    def test_alert_to_dict(self):
        """Test alert to dictionary"""
        alert = Alert(
            rule_name="test_rule",
            value=0.95,
            threshold=0.9,
            message="Test alert",
            severity="high"
        )
        
        alert_dict = alert.to_dict()
        assert alert_dict["rule_name"] == "test_rule"
        assert alert_dict["value"] == 0.95
        assert alert_dict["active"] is True


# ============================================================================
# AlertManager Tests
# ============================================================================

@pytest.mark.unit
class TestAlertManager:
    """Test AlertManager"""
    
    def test_alert_manager_init(self):
        """Test alert manager initialization"""
        manager = AlertManager()
        assert len(manager.rules) > 0
        assert len(manager.alerts) == 0
    
    def test_alert_manager_default_rules(self):
        """Test default alert rules are created"""
        manager = AlertManager()
        
        assert "high_error_rate" in manager.rules
        assert "high_latency" in manager.rules
        assert "high_cost" in manager.rules
        assert "high_rate_limit" in manager.rules
    
    def test_alert_manager_add_rule(self):
        """Test adding alert rule"""
        manager = AlertManager()
        rule = AlertRule(
            name="custom_rule",
            metric_name="custom_metric",
            condition="gt",
            threshold=0.5,
            window_seconds=60,
            severity="medium",
            action="log_warning"
        )
        
        manager.add_rule(rule)
        assert "custom_rule" in manager.rules
    
    def test_alert_manager_remove_rule(self):
        """Test removing alert rule"""
        manager = AlertManager()
        manager.remove_rule("high_error_rate")
        
        assert "high_error_rate" not in manager.rules
    
    def test_alert_manager_get_rule(self):
        """Test getting alert rule"""
        manager = AlertManager()
        rule = manager.get_rule("high_error_rate")
        
        assert rule is not None
        assert rule.name == "high_error_rate"
    
    def test_alert_manager_list_rules(self):
        """Test listing all rules"""
        manager = AlertManager()
        rules = manager.list_rules()
        
        assert isinstance(rules, list)
        assert len(rules) > 0
    
    def test_alert_manager_check_alerts_triggered(self):
        """Test alert triggering"""
        manager = AlertManager()
        
        # Provide metrics that should trigger alerts
        metrics = {
            "ai_error_rate": 0.95,  # Should trigger high_error_rate
            "api_request_duration_ms": 600,  # Should trigger high_latency
        }
        
        triggered_alerts = manager.check_alerts(metrics)
        
        # Should have triggered at least one alert
        assert len(triggered_alerts) > 0
        assert len(manager.alerts) > 0
    
    def test_alert_manager_check_alerts_no_trigger(self):
        """Test alert check with no triggers"""
        manager = AlertManager()
        
        # Provide metrics that shouldn't trigger alerts
        metrics = {
            "ai_error_rate": 0.05,  # Below threshold
            "api_request_duration_ms": 50,  # Below threshold
        }
        
        triggered_alerts = manager.check_alerts(metrics)
        
        # Should not have triggered any alerts
        assert len(triggered_alerts) == 0
    
    def test_alert_manager_trigger_manual_alert(self):
        """Test manual alert triggering"""
        manager = AlertManager()
        
        alert = manager.trigger_alert(
            rule_name="custom_rule",
            value=0.95,
            message="Manual test alert",
            severity="medium"
        )
        
        assert alert is not None
        assert alert.rule_name == "custom_rule"
        assert alert.value == 0.95
        assert len(manager.alerts) == 1
    
    def test_alert_manager_resolve_alert(self):
        """Test alert resolution"""
        manager = AlertManager()
        
        # Trigger an alert first
        alert = manager.trigger_alert(
            rule_name="custom_rule",
            value=0.95,
            message="Test alert",
            severity="medium"
        )
        
        alert_id = alert.id
        
        # Resolve the alert
        manager.resolve_alert(alert_id)
        
        # Check that alert is resolved
        for alert in manager.alerts:
            if alert.id == alert_id:
                assert alert.active is False
                break
    
    def test_alert_manager_get_alerts(self):
        """Test getting alerts"""
        manager = AlertManager()
        
        # Trigger some alerts
        manager.trigger_alert(
            rule_name="rule1",
            value=0.95,
            message="Alert 1",
            severity="high"
        )
        
        manager.trigger_alert(
            rule_name="rule2",
            value=0.85,
            message="Alert 2",
            severity="medium"
        )
        
        # Get all alerts
        alerts = manager.get_alerts()
        
        assert len(alerts) == 2
    
    def test_alert_manager_get_alerts_by_severity(self):
        """Test getting alerts filtered by severity"""
        manager = AlertManager()
        
        # Trigger alerts with different severities
        manager.trigger_alert("rule1", 0.95, "Alert 1", "high")
        manager.trigger_alert("rule2", 0.85, "Alert 2", "medium")
        manager.trigger_alert("rule3", 0.75, "Alert 3", "high")
        
        # Get only high severity alerts
        high_alerts = manager.get_alerts(severity="high")
        
        assert len(high_alerts) == 2
        for alert in high_alerts:
            assert alert["severity"] == "high"
    
    def test_alert_manager_get_alerts_active_only(self):
        """Test getting only active alerts"""
        manager = AlertManager()
        
        # Trigger an alert
        alert = manager.trigger_alert("rule1", 0.95, "Alert 1", "high")
        
        # Get active alerts
        active_alerts = manager.get_alerts(active_only=True)
        
        assert len(active_alerts) == 1
        
        # Resolve the alert
        manager.resolve_alert(alert.id)
        
        # Get active alerts again
        active_alerts = manager.get_alerts(active_only=True)
        
        assert len(active_alerts) == 0
    
    def test_alert_manager_get_alert_stats(self):
        """Test getting alert statistics"""
        manager = AlertManager()
        
        # Trigger some alerts
        manager.trigger_alert("rule1", 0.95, "Alert 1", "high")
        manager.trigger_alert("rule2", 0.85, "Alert 2", "medium")
        manager.trigger_alert("rule3", 0.75, "Alert 3", "high")
        
        stats = manager.get_alert_stats()
        
        assert "total_alerts" in stats
        assert "active_alerts" in stats
        assert "by_severity" in stats
        assert "by_rule" in stats
        
        assert stats["total_alerts"] == 3
        assert stats["active_alerts"] == 3
    
    def test_alert_manager_register_action(self):
        """Test registering custom action"""
        manager = AlertManager()
        
        # Register custom action
        custom_action_called = []
        
        def custom_action(alert):
            custom_action_called.append(alert)
        
        manager.register_action("custom", custom_action)
        
        # Trigger alert with custom action
        manager.trigger_alert(
            rule_name="custom_rule",
            value=0.95,
            message="Test alert",
            severity="medium",
            context={"action": "custom"}
        )
        
        # Check that custom action was called
        assert len(custom_action_called) == 1
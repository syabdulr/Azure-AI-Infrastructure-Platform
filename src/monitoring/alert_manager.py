"""
Alert manager for Azure AI Infrastructure Platform

This module provides:
- Alert rules management
- Threshold checking
- Alert notifications
- Alert history
- Alert severity levels
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class AlertRule:
    """Alert rule definition"""
    
    def __init__(
        self,
        name: str,
        metric_name: str,
        condition: str,
        threshold: float,
        window_seconds: int,
        severity: str,
        action: str,
        enabled: bool = True
    ):
        """
        Initialize alert rule
        
        Args:
            name: Rule name
            metric_name: Metric to monitor
            condition: Condition (gt, lt, gte, lte, eq)
            threshold: Threshold value
            window_seconds: Time window in seconds
            severity: Alert severity (low, medium, high, critical)
            action: Action to take
            enabled: Whether rule is enabled
        """
        self.name = name
        self.metric_name = metric_name
        self.condition = condition
        self.threshold = threshold
        self.window_seconds = window_seconds
        self.severity = severity
        self.action = action
        self.enabled = enabled
        
        self.last_triggered: Optional[str] = None
        self.trigger_count = 0
    
    def evaluate(self, value: float) -> bool:
        """
        Evaluate if alert should trigger
        
        Args:
            value: Current metric value
            
        Returns:
            True if alert should trigger
        """
        if not self.enabled:
            return False
        
        if self.condition == "gt":
            return value > self.threshold
        elif self.condition == "lt":
            return value < self.threshold
        elif self.condition == "gte":
            return value >= self.threshold
        elif self.condition == "lte":
            return value <= self.threshold
        elif self.condition == "eq":
            return value == self.threshold
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary
        
        Returns:
            Dictionary representation
        """
        return {
            "name": self.name,
            "metric_name": self.metric_name,
            "condition": self.condition,
            "threshold": self.threshold,
            "window_seconds": self.window_seconds,
            "severity": self.severity,
            "action": self.action,
            "enabled": self.enabled,
            "last_triggered": self.last_triggered,
            "trigger_count": self.trigger_count
        }


class Alert:
    """Alert instance"""
    
    def __init__(
        self,
        rule_name: str,
        value: float,
        threshold: float,
        message: str,
        severity: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize alert
        
        Args:
            rule_name: Rule name
            value: Triggered value
            threshold: Threshold value
            message: Alert message
            severity: Alert severity
            context: Additional context
        """
        self.id = f"alert-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        self.rule_name = rule_name
        self.value = value
        self.threshold = threshold
        self.message = message
        self.severity = severity
        self.context = context or {}
        self.triggered_at = datetime.utcnow().isoformat()
        self.active = True
        self.resolved_at = None
    
    def resolve(self):
        """Resolve alert"""
        self.active = False
        self.resolved_at = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary
        
        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "rule_name": self.rule_name,
            "value": self.value,
            "threshold": self.threshold,
            "message": self.message,
            "severity": self.severity,
            "context": self.context,
            "triggered_at": self.triggered_at,
            "active": self.active,
            "resolved_at": self.resolved_at
        }


class AlertManager:
    """Manage alerts and notifications"""
    
    def __init__(self):
        """Initialize alert manager"""
        self.rules: Dict[str, AlertRule] = {}
        self.alerts: List[Alert] = []
        self.alert_actions: Dict[str, Callable] = {}
        
        # Initialize default rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default alert rules"""
        # Error rate alert
        self.add_rule(AlertRule(
            name="high_error_rate",
            metric_name="ai_error_rate",
            condition="gt",
            threshold=0.9,
            window_seconds=300,
            severity="critical",
            action="notify_team"
        ))
        
        # Latency alert
        self.add_rule(AlertRule(
            name="high_latency",
            metric_name="api_request_duration_ms",
            condition="gt",
            threshold=500,
            window_seconds=60,
            severity="high",
            action="notify_team"
        ))
        
        # Cost alert
        self.add_rule(AlertRule(
            name="high_cost",
            metric_name="ai_cost_total",
            condition="gt",
            threshold=10.0,
            window_seconds=3600,
            severity="medium",
            action="log_warning"
        ))
        
        # Rate limit alert
        self.add_rule(AlertRule(
            name="high_rate_limit",
            metric_name="guardrails_rate_limited_total",
            condition="gt",
            threshold=10,
            window_seconds=60,
            severity="medium",
            action="log_warning"
        ))
    
    def add_rule(self, rule: AlertRule):
        """
        Add an alert rule
        
        Args:
            rule: AlertRule to add
        """
        self.rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_rule(self, rule_name: str):
        """
        Remove an alert rule
        
        Args:
            rule_name: Rule name to remove
        """
        if rule_name in self.rules:
            del self.rules[rule_name]
            logger.info(f"Removed alert rule: {rule_name}")
    
    def get_rule(self, rule_name: str) -> Optional[AlertRule]:
        """
        Get an alert rule
        
        Args:
            rule_name: Rule name
            
        Returns:
            AlertRule or None
        """
        return self.rules.get(rule_name)
    
    def list_rules(self) -> List[Dict[str, Any]]:
        """
        List all alert rules
        
        Returns:
            List of rule dictionaries
        """
        return [rule.to_dict() for rule in self.rules.values()]
    
    def check_alerts(self, metrics: Dict[str, Any]) -> List[Alert]:
        """
        Check all alert rules
        
        Args:
            metrics: Current metrics
            
        Returns:
            List of triggered alerts
        """
        triggered_alerts = []
        
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            # Get metric value
            metric_value = metrics.get(rule.metric_name)
            if metric_value is None:
                continue
            
            # Check if alert should trigger
            if rule.evaluate(metric_value):
                # Create alert
                alert = Alert(
                    rule_name=rule.name,
                    value=metric_value,
                    threshold=rule.threshold,
                    message=f"{rule.name}: {rule.metric_name} = {metric_value} {rule.condition} {rule.threshold}",
                    severity=rule.severity,
                    context={
                        "metric": rule.metric_name,
                        "condition": rule.condition,
                        "window_seconds": rule.window_seconds,
                        "action": rule.action  # Store action in context
                    }
                )
                
                triggered_alerts.append(alert)
                self.alerts.append(alert)
                
                # Update rule
                rule.last_triggered = alert.triggered_at  # type: ignore
                rule.trigger_count += 1
                
                # Execute action
                self._execute_action(alert)
                
                logger.warning(f"Alert triggered: {alert.message}")
        
        return triggered_alerts
    
    def trigger_alert(
        self,
        rule_name: str,
        value: float,
        message: str,
        severity: str = "medium",
        context: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """
        Manually trigger an alert
        
        Args:
            rule_name: Rule name
            value: Triggered value
            message: Alert message
            severity: Alert severity
            context: Additional context
            
        Returns:
            Alert instance
        """
        rule = self.rules.get(rule_name)
        threshold = rule.threshold if rule else 0.0
        
        alert = Alert(
            rule_name=rule_name,
            value=value,
            threshold=threshold,
            message=message,
            severity=severity,
            context=context
        )
        
        self.alerts.append(alert)
        
        # Execute action
        self._execute_action(alert)
        
        logger.warning(f"Manual alert triggered: {alert.message}")
        
        return alert
    
    def resolve_alert(self, alert_id: str):
        """
        Resolve an alert
        
        Args:
            alert_id: Alert ID to resolve
        """
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.resolve()
                logger.info(f"Resolved alert: {alert_id}")
                return
    
    def get_alerts(
        self,
        severity: Optional[str] = None,
        active_only: bool = False,
        rule_name: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get alerts
        
        Args:
            severity: Filter by severity
            active_only: Only return active alerts
            rule_name: Filter by rule name
            limit: Maximum number of results
            
        Returns:
            List of alert dictionaries
        """
        filtered = self.alerts
        
        # Filter by severity
        if severity:
            filtered = [a for a in filtered if a.severity == severity]
        
        # Filter by active status
        if active_only:
            filtered = [a for a in filtered if a.active]
        
        # Filter by rule name
        if rule_name:
            filtered = [a for a in filtered if a.rule_name == rule_name]
        
        # Sort by triggered time (newest first) and limit
        filtered = sorted(filtered, key=lambda x: x.triggered_at, reverse=True)
        return [alert.to_dict() for alert in filtered[:limit]]
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """
        Get alert statistics
        
        Returns:
            Dictionary with alert statistics
        """
        total_alerts = len(self.alerts)
        active_alerts = [a for a in self.alerts if a.active]
        
        # Count by severity
        severity_counts = defaultdict(int)
        rule_counts = defaultdict(int)
        
        for alert in self.alerts:
            severity_counts[alert.severity] += 1
            rule_counts[alert.rule_name] += 1
        
        return {
            "total_alerts": total_alerts,
            "active_alerts": len(active_alerts),
            "by_severity": dict(severity_counts),
            "by_rule": dict(rule_counts),
            "recent_alerts": [a.to_dict() for a in sorted(active_alerts, key=lambda x: x.triggered_at, reverse=True)[:10]]
        }
    
    def register_action(self, action_name: str, action_fn: Callable):
        """
        Register an alert action
        
        Args:
            action_name: Action name
            action_fn: Action function
        """
        self.alert_actions[action_name] = action_fn
        logger.info(f"Registered alert action: {action_name}")
    
    def _execute_action(self, alert: Alert):
        """
        Execute alert action
        
        Args:
            alert: Alert to execute action for
        """
        # Get action from alert context
        action_name = alert.context.get("action", "log_warning")
        
        action_fn = self.alert_actions.get(action_name)
        
        if action_fn:
            try:
                action_fn(alert)
            except Exception as e:
                logger.error(f"Failed to execute alert action {action_name}: {e}")
        else:
            # Default actions
            if action_name == "notify_team":
                logger.critical(f"ALERT: {alert.message}")
            elif action_name == "log_warning":
                logger.warning(f"ALERT: {alert.message}")


# Global instance
alert_manager = AlertManager()
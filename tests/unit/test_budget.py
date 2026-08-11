"""Tests for budget enforcement."""

import pytest
from datetime import datetime, timedelta

from src.providers.budget.models import (
    BudgetAlertType,
    BudgetStatus,
    BudgetConfig,
    BudgetAlert,
    BudgetUsage,
    BudgetReport
)
from src.providers.budget.manager import BudgetManager, get_budget_manager


class TestBudgetConfig:
    """Tests for BudgetConfig model."""

    def test_budget_config_creation(self):
        """Test creating a budget configuration."""
        config = BudgetConfig(
            provider_name="openai",
            daily_limit_usd=10.0,
            monthly_limit_usd=300.0,
            alerts_enabled=True,
            pause_on_exceed=True,
            auto_renewal=True
        )

        assert config.provider_name == "openai"
        assert config.daily_limit_usd == 10.0
        assert config.monthly_limit_usd == 300.0
        assert config.alerts_enabled is True

    def test_budget_config_validation(self):
        """Test budget configuration validation."""
        with pytest.raises(ValueError, match="Daily limit must be positive"):
            BudgetConfig(
                provider_name="openai",
                daily_limit_usd=0.0,
                monthly_limit_usd=300.0
            )

        with pytest.raises(ValueError, match="Monthly limit must be positive"):
            BudgetConfig(
                provider_name="openai",
                daily_limit_usd=10.0,
                monthly_limit_usd=0.0
            )


class TestBudgetUsage:
    """Tests for BudgetUsage model."""

    def test_budget_usage_creation(self):
        """Test creating budget usage."""
        usage = BudgetUsage(provider_name="openai")

        assert usage.provider_name == "openai"
        assert usage.daily_usage_usd == 0.0
        assert usage.monthly_usage_usd == 0.0
        assert usage.daily_request_count == 0
        assert usage.monthly_request_count == 0

    def test_budget_usage_add_cost(self):
        """Test adding cost to budget usage."""
        usage = BudgetUsage(provider_name="openai")

        usage.add_cost(0.5)
        usage.add_cost(0.3)

        assert usage.daily_usage_usd == 0.8
        assert usage.monthly_usage_usd == 0.8
        assert usage.daily_request_count == 2
        assert usage.monthly_request_count == 2

    def test_budget_usage_reset_daily(self):
        """Test resetting daily usage."""
        usage = BudgetUsage(provider_name="openai")
        usage.add_cost(1.0)
        usage.add_cost(0.5)

        usage.reset_daily()

        assert usage.daily_usage_usd == 0.0
        assert usage.daily_request_count == 0
        assert usage.monthly_usage_usd == 1.5  # Should remain
        assert usage.monthly_request_count == 2  # Should remain

    def test_budget_usage_reset_monthly(self):
        """Test resetting monthly usage."""
        usage = BudgetUsage(provider_name="openai")
        usage.add_cost(1.0)
        usage.add_cost(0.5)

        usage.reset_monthly()

        assert usage.daily_usage_usd == 1.5  # Should remain
        assert usage.daily_request_count == 2  # Should remain
        assert usage.monthly_usage_usd == 0.0
        assert usage.monthly_request_count == 0

    def test_budget_usage_percentage(self):
        """Test usage percentage calculation."""
        usage = BudgetUsage(provider_name="openai")
        usage.add_cost(5.0)

        daily_pct = usage.get_daily_percentage(10.0)
        monthly_pct = usage.get_monthly_percentage(100.0)

        assert daily_pct == 50.0
        assert monthly_pct == 5.0

    def test_budget_usage_exceeded(self):
        """Test budget exceeded check."""
        usage = BudgetUsage(provider_name="openai")
        usage.add_cost(10.0)

        assert usage.is_daily_exceeded(10.0) is True
        assert usage.is_monthly_exceeded(20.0) is False


class TestBudgetManager:
    """Tests for BudgetManager."""

    def test_budget_manager_creation(self):
        """Test creating budget manager."""
        manager = BudgetManager()

        assert manager is not None
        assert manager.default_daily_limit == 10.0
        assert manager.default_monthly_limit == 300.0

    def test_configure_provider(self):
        """Test configuring provider budget."""
        manager = BudgetManager()

        manager.configure_provider(
            provider_name="openai",
            daily_limit_usd=5.0,
            monthly_limit_usd=150.0
        )

        assert "openai" in manager._configs
        assert manager._configs["openai"].daily_limit_usd == 5.0
        assert manager._configs["openai"].monthly_limit_usd == 150.0

    def test_configure_provider_defaults(self):
        """Test configuring provider with default limits."""
        manager = BudgetManager()

        manager.configure_provider(provider_name="azure_openai")

        assert "azure_openai" in manager._configs
        assert manager._configs["azure_openai"].daily_limit_usd == 10.0
        assert manager._configs["azure_openai"].monthly_limit_usd == 300.0

    def test_record_usage(self):
        """Test recording usage."""
        manager = BudgetManager()

        manager.configure_provider(
            provider_name="openai",
            daily_limit_usd=10.0
        )

        alert = manager.record_usage("openai", 0.5)

        usage = manager.get_usage("openai")
        assert usage is not None
        assert usage.daily_usage_usd == 0.5
        assert usage.daily_request_count == 1

    def test_check_budget_ok(self):
        """Test budget check when OK."""
        manager = BudgetManager()

        manager.configure_provider(
            provider_name="openai",
            daily_limit_usd=10.0
        )

        manager.record_usage("openai", 0.5)

        can_proceed, reason = manager.check_budget("openai")

        assert can_proceed is True
        assert reason == "Budget OK"

    def test_check_budget_exceeded(self):
        """Test budget check when exceeded."""
        manager = BudgetManager()

        manager.configure_provider(
            provider_name="openai",
            daily_limit_usd=10.0,
            pause_on_exceed=True
        )

        manager.record_usage("openai", 10.0)

        can_proceed, reason = manager.check_budget("openai")

        assert can_proceed is False
        assert "exceeded" in reason.lower()

    def test_check_budget_unconfigured(self):
        """Test budget check for unconfigured provider."""
        manager = BudgetManager()

        can_proceed, reason = manager.check_budget("anthropic")

        assert can_proceed is True
        assert "not configured" in reason.lower()

    def test_get_usage(self):
        """Test getting usage for provider."""
        manager = BudgetManager()

        manager.configure_provider(provider_name="openai")
        manager.record_usage("openai", 0.5)

        usage = manager.get_usage("openai")

        assert usage is not None
        assert usage.provider_name == "openai"
        assert usage.daily_usage_usd == 0.5

    def test_get_all_usage(self):
        """Test getting usage for all providers."""
        manager = BudgetManager()

        manager.configure_provider(provider_name="openai")
        manager.configure_provider(provider_name="azure_openai")

        manager.record_usage("openai", 0.5)
        manager.record_usage("azure_openai", 0.3)

        all_usage = manager.get_all_usage()

        assert len(all_usage) == 2
        assert all_usage["openai"].daily_usage_usd == 0.5
        assert all_usage["azure_openai"].daily_usage_usd == 0.3

    def test_get_report(self):
        """Test generating budget report."""
        manager = BudgetManager()

        manager.configure_provider(
            provider_name="openai",
            daily_limit_usd=10.0,
            monthly_limit_usd=100.0
        )

        manager.record_usage("openai", 0.5)
        manager.record_usage("openai", 0.3)

        report = manager.get_report("openai")

        assert report is not None
        assert report.provider_name == "openai"
        assert report.daily_usage_usd == 0.8
        assert report.daily_limit_usd == 10.0
        assert report.daily_percentage == 8.0
        assert report.daily_request_count == 2

    def test_get_all_reports(self):
        """Test generating reports for all providers."""
        manager = BudgetManager()

        manager.configure_provider(provider_name="openai")
        manager.configure_provider(provider_name="azure_openai")

        manager.record_usage("openai", 0.5)
        manager.record_usage("azure_openai", 0.3)

        reports = manager.get_all_reports()

        assert len(reports) == 2
        assert reports[0].provider_name in ["openai", "azure_openai"]

    def test_budget_alert_80_percent(self):
        """Test 80% budget alert."""
        manager = BudgetManager()

        manager.configure_provider(
            provider_name="openai",
            daily_limit_usd=10.0,
            alerts_enabled=True
        )

        alert = manager.record_usage("openai", 8.0)

        assert alert is not None
        assert alert.alert_type == BudgetAlertType.WARNING_80
        assert alert.percentage == 80.0

    def test_budget_alert_90_percent(self):
        """Test 90% budget alert."""
        manager = BudgetManager()

        manager.configure_provider(
            provider_name="openai",
            daily_limit_usd=10.0,
            alerts_enabled=True
        )

        alert = manager.record_usage("openai", 9.0)

        assert alert is not None
        assert alert.alert_type == BudgetAlertType.WARNING_90
        assert alert.percentage == 90.0

    def test_budget_alert_100_percent(self):
        """Test 100% budget alert."""
        manager = BudgetManager()

        manager.configure_provider(
            provider_name="openai",
            daily_limit_usd=10.0,
            alerts_enabled=True
        )

        alert = manager.record_usage("openai", 10.0)

        assert alert is not None
        assert alert.alert_type == BudgetAlertType.EXCEEDED_100
        assert alert.percentage == 100.0

    def test_alert_callback(self):
        """Test alert callback registration."""
        manager = BudgetManager()
        alerts_received = []

        def callback(alert):
            alerts_received.append(alert)

        manager.register_alert_callback(callback)

        manager.configure_provider(
            provider_name="openai",
            daily_limit_usd=10.0,
            alerts_enabled=True
        )

        manager.record_usage("openai", 8.0)

        assert len(alerts_received) == 1
        assert alerts_received[0].alert_type == BudgetAlertType.WARNING_80

    def test_reset_daily(self):
        """Test resetting daily usage."""
        manager = BudgetManager()

        manager.configure_provider(provider_name="openai")
        manager.record_usage("openai", 0.5)

        manager.reset_daily("openai")

        usage = manager.get_usage("openai")
        assert usage.daily_usage_usd == 0.0
        assert usage.daily_request_count == 0

    def test_reset_monthly(self):
        """Test resetting monthly usage."""
        manager = BudgetManager()

        manager.configure_provider(provider_name="openai")
        manager.record_usage("openai", 0.5)

        manager.reset_monthly("openai")

        usage = manager.get_usage("openai")
        assert usage.monthly_usage_usd == 0.0
        assert usage.monthly_request_count == 0


class TestGlobalBudgetManager:
    """Tests for global budget manager."""

    def test_get_budget_manager_singleton(self):
        """Test global budget manager is a singleton."""
        manager1 = get_budget_manager()
        manager2 = get_budget_manager()

        assert manager1 is manager2

    def test_global_manager_operations(self):
        """Test operations on global manager."""
        manager = get_budget_manager()

        manager.configure_provider(provider_name="openai")
        manager.record_usage("openai", 0.5)

        usage = manager.get_usage("openai")

        assert usage is not None
        assert usage.daily_usage_usd == 0.5


class TestBudgetReport:
    """Tests for BudgetReport model."""

    def test_budget_report_creation(self):
        """Test creating a budget report."""
        report = BudgetReport(
            provider_name="openai",
            daily_usage_usd=5.0,
            monthly_usage_usd=50.0,
            daily_limit_usd=10.0,
            monthly_limit_usd=100.0,
            daily_percentage=50.0,
            monthly_percentage=50.0,
            daily_request_count=10,
            monthly_request_count=100,
            avg_cost_per_request=0.05
        )

        assert report.provider_name == "openai"
        assert report.daily_usage_usd == 5.0
        assert report.daily_percentage == 50.0
        assert report.avg_cost_per_request == 0.05

    def test_budget_report_to_dict(self):
        """Test converting report to dictionary."""
        report = BudgetReport(
            provider_name="openai",
            daily_usage_usd=5.0,
            monthly_usage_usd=50.0,
            daily_limit_usd=10.0,
            monthly_limit_usd=100.0,
            daily_percentage=50.0,
            monthly_percentage=50.0,
            daily_request_count=10,
            monthly_request_count=100,
            avg_cost_per_request=0.05
        )

        d = report.to_dict()

        assert d["provider_name"] == "openai"
        assert d["daily_usage_usd"] == 5.0
        assert d["daily_percentage"] == 50.0
        assert "generated_at" in d
"""Budget manager for multi-provider AI gateway."""

from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
import threading

from .models import (
    BudgetConfig,
    BudgetUsage,
    BudgetAlert,
    BudgetAlertType,
    BudgetStatus,
    BudgetReport
)


class BudgetManager:
    """Manages budgets for multi-provider gateway."""

    def __init__(self):
        """Initialize budget manager."""
        self._configs: Dict[str, BudgetConfig] = {}
        self._usage: Dict[str, BudgetUsage] = {}
        self._alerts: List[BudgetAlert] = []
        self._lock = threading.Lock()
        self._alert_callbacks: List[Callable[[BudgetAlert], None]] = []

        # Default budget limits (USD)
        self.default_daily_limit = 10.0  # $10/day per provider
        self.default_monthly_limit = 300.0  # $300/month per provider

    def configure_provider(
        self,
        provider_name: str,
        daily_limit_usd: Optional[float] = None,
        monthly_limit_usd: Optional[float] = None,
        alerts_enabled: bool = True,
        pause_on_exceed: bool = True,
        auto_renewal: bool = True
    ):
        """
        Configure budget for a provider.

        Args:
            provider_name: Provider name
            daily_limit_usd: Daily limit (uses default if None)
            monthly_limit_usd: Monthly limit (uses default if None)
            alerts_enabled: Enable budget alerts
            pause_on_exceed: Pause when budget exceeded
            auto_renewal: Auto-renew daily/monthly budgets
        """
        with self._lock:
            daily = daily_limit_usd or self.default_daily_limit
            monthly = monthly_limit_usd or self.default_monthly_limit

            config = BudgetConfig(
                provider_name=provider_name,
                daily_limit_usd=daily,
                monthly_limit_usd=monthly,
                alerts_enabled=alerts_enabled,
                pause_on_exceed=pause_on_exceed,
                auto_renewal=auto_renewal
            )

            self._configs[provider_name] = config

            # Initialize usage if not exists
            if provider_name not in self._usage:
                self._usage[provider_name] = BudgetUsage(provider_name=provider_name)

    def record_usage(
        self,
        provider_name: str,
        cost_usd: float,
        timestamp: Optional[datetime] = None
    ) -> Optional[BudgetAlert]:
        """
        Record usage for a provider.

        Args:
            provider_name: Provider name
            cost_usd: Cost in USD
            timestamp: Timestamp of usage (now if None)

        Returns:
            BudgetAlert if triggered, None otherwise
        """
        if timestamp is None:
            timestamp = datetime.now()

        with self._lock:
            # Check if provider is configured
            if provider_name not in self._configs:
                # Auto-configure with defaults
                self.configure_provider(provider_name)

            config = self._configs[provider_name]
            usage = self._usage[provider_name]

            # Check if we need to reset daily/monthly usage
            self._check_and_reset_usage(usage, config)

            # Check if provider is paused
            if usage.daily_status == BudgetStatus.PAUSED:
                return self._create_alert(
                    BudgetAlertType.EXCEEDED_100,
                    provider_name,
                    'daily',
                    usage.daily_usage_usd,
                    config.daily_limit_usd,
                    "Provider paused due to budget exceeded"
                )

            # Add cost
            usage.add_cost(cost_usd)

            # Update status
            self._update_status(usage, config)

            # Check for alerts
            if config.alerts_enabled:
                alert = self._check_for_alerts(usage, config)
                if alert:
                    self._alerts.append(alert)
                    self._trigger_alert_callbacks(alert)
                    return alert

            return None

    def check_budget(self, provider_name: str) -> tuple[bool, str]:
        """
        Check if provider can make a request.

        Args:
            provider_name: Provider name

        Returns:
            Tuple of (can_proceed, reason)
        """
        with self._lock:
            # Check if provider is configured
            if provider_name not in self._configs:
                return True, "Provider not configured, proceeding with default limits"

            config = self._configs[provider_name]
            usage = self._usage[provider_name]

            # Check if we need to reset
            self._check_and_reset_usage(usage, config)

            # Check if paused
            if usage.daily_status == BudgetStatus.PAUSED:
                return False, f"Provider paused: daily budget exceeded (${usage.daily_usage_usd:.2f}/${config.daily_limit_usd:.2f})"

            # Check if exceeded
            if config.pause_on_exceed:
                if usage.is_daily_exceeded(config.daily_limit_usd):
                    return False, f"Daily budget exceeded: ${usage.daily_usage_usd:.2f}/${config.daily_limit_usd:.2f}"

                if usage.is_monthly_exceeded(config.monthly_limit_usd):
                    return False, f"Monthly budget exceeded: ${usage.monthly_usage_usd:.2f}/${config.monthly_limit_usd:.2f}"

            return True, "Budget OK"

    def get_usage(self, provider_name: str) -> Optional[BudgetUsage]:
        """
        Get usage for a provider.

        Args:
            provider_name: Provider name

        Returns:
            BudgetUsage or None if not configured
        """
        with self._lock:
            return self._usage.get(provider_name)

    def get_all_usage(self) -> Dict[str, BudgetUsage]:
        """
        Get usage for all providers.

        Returns:
            Dictionary of provider name to BudgetUsage
        """
        with self._lock:
            return self._usage.copy()

    def get_report(self, provider_name: str) -> Optional[BudgetReport]:
        """
        Generate budget report for a provider.

        Args:
            provider_name: Provider name

        Returns:
            BudgetReport or None if not configured
        """
        with self._lock:
            if provider_name not in self._configs:
                return None

            config = self._configs[provider_name]
            usage = self._usage[provider_name]

            # Calculate average cost per request
            total_requests = usage.daily_request_count + usage.monthly_request_count
            avg_cost = (usage.daily_usage_usd + usage.monthly_usage_usd) / total_requests if total_requests > 0 else 0.0

            # Get today's alerts
            today = datetime.now().date()
            alerts_today = [
                alert for alert in self._alerts
                if alert.provider_name == provider_name and alert.timestamp.date() == today
            ]

            return BudgetReport(
                provider_name=provider_name,
                daily_usage_usd=usage.daily_usage_usd,
                monthly_usage_usd=usage.monthly_usage_usd,
                daily_limit_usd=config.daily_limit_usd,
                monthly_limit_usd=config.monthly_limit_usd,
                daily_percentage=usage.get_daily_percentage(config.daily_limit_usd),
                monthly_percentage=usage.get_monthly_percentage(config.monthly_limit_usd),
                daily_request_count=usage.daily_request_count,
                monthly_request_count=usage.monthly_request_count,
                avg_cost_per_request=avg_cost,
                alerts_today=alerts_today
            )

    def get_all_reports(self) -> List[BudgetReport]:
        """
        Generate budget reports for all providers.

        Returns:
            List of BudgetReport
        """
        with self._lock:
            reports = []
            for provider_name in self._configs:
                report = self.get_report(provider_name)
                if report:
                    reports.append(report)
            return reports

    def get_alerts(
        self,
        provider_name: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[BudgetAlert]:
        """
        Get budget alerts.

        Args:
            provider_name: Filter by provider name (optional)
            since: Filter alerts since this timestamp (optional)

        Returns:
            List of BudgetAlert
        """
        with self._lock:
            alerts = self._alerts

            if provider_name:
                alerts = [a for a in alerts if a.provider_name == provider_name]

            if since:
                alerts = [a for a in alerts if a.timestamp >= since]

            return alerts

    def register_alert_callback(self, callback: Callable[[BudgetAlert], None]):
        """
        Register a callback for budget alerts.

        Args:
            callback: Function to call when alert is triggered
        """
        with self._lock:
            self._alert_callbacks.append(callback)

    def reset_daily(self, provider_name: str):
        """
        Reset daily usage for a provider.

        Args:
            provider_name: Provider name
        """
        with self._lock:
            if provider_name in self._usage:
                self._usage[provider_name].reset_daily()

    def reset_monthly(self, provider_name: str):
        """
        Reset monthly usage for a provider.

        Args:
            provider_name: Provider name
        """
        with self._lock:
            if provider_name in self._usage:
                self._usage[provider_name].reset_monthly()

    def _check_and_reset_usage(self, usage: BudgetUsage, config: BudgetConfig):
        """
        Check if we need to reset daily/monthly usage.

        Args:
            usage: Budget usage
            config: Budget configuration
        """
        now = datetime.now()

        # Check daily reset (if auto-renewal enabled)
        if config.auto_renewal:
            last_daily = usage.last_reset_daily

            # Reset if it's a new day
            if last_daily.date() != now.date():
                usage.reset_daily()

        # Check monthly reset (if auto-renewal enabled)
        if config.auto_renewal:
            last_monthly = usage.last_reset_monthly

            # Reset if it's a new month
            if last_monthly.month != now.month or last_monthly.year != now.year:
                usage.reset_monthly()

    def _update_status(self, usage: BudgetUsage, config: BudgetConfig):
        """
        Update budget status based on usage.

        Args:
            usage: Budget usage
            config: Budget configuration
        """
        # Update daily status
        daily_pct = usage.get_daily_percentage(config.daily_limit_usd)
        if daily_pct >= 100:
            usage.daily_status = BudgetStatus.PAUSED if config.pause_on_exceed else BudgetStatus.EXCEEDED
        elif daily_pct >= 90:
            usage.daily_status = BudgetStatus.WARNING
        else:
            usage.daily_status = BudgetStatus.ACTIVE

        # Update monthly status
        monthly_pct = usage.get_monthly_percentage(config.monthly_limit_usd)
        if monthly_pct >= 100:
            usage.monthly_status = BudgetStatus.PAUSED if config.pause_on_exceed else BudgetStatus.EXCEEDED
        elif monthly_pct >= 90:
            usage.monthly_status = BudgetStatus.WARNING
        else:
            usage.monthly_status = BudgetStatus.ACTIVE

    def _check_for_alerts(self, usage: BudgetUsage, config: BudgetConfig) -> Optional[BudgetAlert]:
        """
        Check for budget alerts.

        Args:
            usage: Budget usage
            config: Budget configuration

        Returns:
            BudgetAlert if alert triggered, None otherwise
        """
        daily_pct = usage.get_daily_percentage(config.daily_limit_usd)
        monthly_pct = usage.get_monthly_percentage(config.monthly_limit_usd)

        # Check 100% exceeded (daily)
        if daily_pct >= 100:
            return self._create_alert(
                BudgetAlertType.EXCEEDED_100,
                config.provider_name,
                'daily',
                usage.daily_usage_usd,
                config.daily_limit_usd,
                f"Daily budget exceeded: ${usage.daily_usage_usd:.2f}/${config.daily_limit_usd:.2f}"
            )

        # Check 100% exceeded (monthly)
        if monthly_pct >= 100:
            return self._create_alert(
                BudgetAlertType.EXCEEDED_100,
                config.provider_name,
                'monthly',
                usage.monthly_usage_usd,
                config.monthly_limit_usd,
                f"Monthly budget exceeded: ${usage.monthly_usage_usd:.2f}/${config.monthly_limit_usd:.2f}"
            )

        # Check 90% warning
        if daily_pct >= 90 and daily_pct < 100:
            return self._create_alert(
                BudgetAlertType.WARNING_90,
                config.provider_name,
                'daily',
                usage.daily_usage_usd,
                config.daily_limit_usd,
                f"Daily budget at {daily_pct:.1f}%: ${usage.daily_usage_usd:.2f}/${config.daily_limit_usd:.2f}"
            )

        if monthly_pct >= 90 and monthly_pct < 100:
            return self._create_alert(
                BudgetAlertType.WARNING_90,
                config.provider_name,
                'monthly',
                usage.monthly_usage_usd,
                config.monthly_limit_usd,
                f"Monthly budget at {monthly_pct:.1f}%: ${usage.monthly_usage_usd:.2f}/${config.monthly_limit_usd:.2f}"
            )

        # Check 80% warning
        if daily_pct >= 80 and daily_pct < 90:
            return self._create_alert(
                BudgetAlertType.WARNING_80,
                config.provider_name,
                'daily',
                usage.daily_usage_usd,
                config.daily_limit_usd,
                f"Daily budget at {daily_pct:.1f}%: ${usage.daily_usage_usd:.2f}/${config.daily_limit_usd:.2f}"
            )

        if monthly_pct >= 80 and monthly_pct < 90:
            return self._create_alert(
                BudgetAlertType.WARNING_80,
                config.provider_name,
                'monthly',
                usage.monthly_usage_usd,
                config.monthly_limit_usd,
                f"Monthly budget at {monthly_pct:.1f}%: ${usage.monthly_usage_usd:.2f}/${config.monthly_limit_usd:.2f}"
            )

        return None

    def _create_alert(
        self,
        alert_type: BudgetAlertType,
        provider_name: str,
        limit_type: str,
        usage_usd: float,
        limit_usd: float,
        message: str
    ) -> BudgetAlert:
        """
        Create a budget alert.

        Args:
            alert_type: Alert type
            provider_name: Provider name
            limit_type: Limit type ('daily' or 'monthly')
            usage_usd: Current usage
            limit_usd: Limit
            message: Alert message

        Returns:
            BudgetAlert
        """
        percentage = (usage_usd / limit_usd) * 100.0 if limit_usd > 0 else 0.0

        return BudgetAlert(
            alert_type=alert_type,
            provider_name=provider_name,
            limit_type=limit_type,
            usage_usd=usage_usd,
            limit_usd=limit_usd,
            percentage=percentage,
            timestamp=datetime.now(),
            message=message
        )

    def _trigger_alert_callbacks(self, alert: BudgetAlert):
        """
        Trigger alert callbacks.

        Args:
            alert: Alert to trigger callbacks for
        """
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                print(f"Alert callback error: {e}")


# Global budget manager instance
_budget_manager: Optional[BudgetManager] = None


def get_budget_manager() -> BudgetManager:
    """
    Get the global budget manager instance.

    Returns:
        Global BudgetManager instance
    """
    global _budget_manager

    if _budget_manager is None:
        _budget_manager = BudgetManager()

    return _budget_manager
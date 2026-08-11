"""Budget models for multi-provider AI gateway."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any


class BudgetAlertType(Enum):
    """Budget alert types."""
    WARNING_80 = "warning_80"
    WARNING_90 = "warning_90"
    EXCEEDED_100 = "exceeded_100"
    RECOVERED = "recovered"


class BudgetStatus(Enum):
    """Budget status."""
    ACTIVE = "active"
    WARNING = "warning"
    EXCEEDED = "exceeded"
    PAUSED = "paused"


@dataclass
class BudgetConfig:
    """Budget configuration for a provider."""

    provider_name: str
    daily_limit_usd: float
    monthly_limit_usd: float
    alerts_enabled: bool = True
    pause_on_exceed: bool = True
    auto_renewal: bool = True

    def __post_init__(self):
        """Validate budget configuration."""
        if self.daily_limit_usd <= 0:
            raise ValueError("Daily limit must be positive")
        if self.monthly_limit_usd <= 0:
            raise ValueError("Monthly limit must be positive")


@dataclass
class BudgetAlert:
    """A budget alert."""

    alert_type: BudgetAlertType
    provider_name: str
    limit_type: str  # 'daily' or 'monthly'
    usage_usd: float
    limit_usd: float
    percentage: float
    timestamp: datetime
    message: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "alert_type": self.alert_type.value,
            "provider_name": self.provider_name,
            "limit_type": self.limit_type,
            "usage_usd": self.usage_usd,
            "limit_usd": self.limit_usd,
            "percentage": self.percentage,
            "timestamp": self.timestamp.isoformat(),
            "message": self.message
        }


@dataclass
class BudgetUsage:
    """Budget usage tracking."""

    provider_name: str
    daily_usage_usd: float = 0.0
    monthly_usage_usd: float = 0.0
    daily_request_count: int = 0
    monthly_request_count: int = 0
    last_reset_daily: datetime = field(default_factory=datetime.now)
    last_reset_monthly: datetime = field(default_factory=datetime.now)
    daily_status: BudgetStatus = BudgetStatus.ACTIVE
    monthly_status: BudgetStatus = BudgetStatus.ACTIVE

    def add_cost(self, cost_usd: float):
        """
        Add cost to usage tracking.

        Args:
            cost_usd: Cost to add
        """
        self.daily_usage_usd += cost_usd
        self.monthly_usage_usd += cost_usd
        self.daily_request_count += 1
        self.monthly_request_count += 1

    def reset_daily(self):
        """Reset daily usage."""
        self.daily_usage_usd = 0.0
        self.daily_request_count = 0
        self.last_reset_daily = datetime.now()
        self.daily_status = BudgetStatus.ACTIVE

    def reset_monthly(self):
        """Reset monthly usage."""
        self.monthly_usage_usd = 0.0
        self.monthly_request_count = 0
        self.last_reset_monthly = datetime.now()
        self.monthly_status = BudgetStatus.ACTIVE

    def get_daily_percentage(self, limit: float) -> float:
        """
        Get daily usage as percentage of limit.

        Args:
            limit: Daily limit

        Returns:
            Usage percentage
        """
        if limit == 0:
            return 0.0
        return (self.daily_usage_usd / limit) * 100.0

    def get_monthly_percentage(self, limit: float) -> float:
        """
        Get monthly usage as percentage of limit.

        Args:
            limit: Monthly limit

        Returns:
            Usage percentage
        """
        if limit == 0:
            return 0.0
        return (self.monthly_usage_usd / limit) * 100.0

    def is_daily_exceeded(self, limit: float) -> bool:
        """
        Check if daily budget is exceeded.

        Args:
            limit: Daily limit

        Returns:
            True if exceeded
        """
        return self.daily_usage_usd >= limit

    def is_monthly_exceeded(self, limit: float) -> bool:
        """
        Check if monthly budget is exceeded.

        Args:
            limit: Monthly limit

        Returns:
            True if exceeded
        """
        return self.monthly_usage_usd >= limit

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "provider_name": self.provider_name,
            "daily_usage_usd": self.daily_usage_usd,
            "monthly_usage_usd": self.monthly_usage_usd,
            "daily_request_count": self.daily_request_count,
            "monthly_request_count": self.monthly_request_count,
            "last_reset_daily": self.last_reset_daily.isoformat(),
            "last_reset_monthly": self.last_reset_monthly.isoformat(),
            "daily_status": self.daily_status.value,
            "monthly_status": self.monthly_status.value
        }


@dataclass
class BudgetReport:
    """Comprehensive budget report."""

    provider_name: str
    daily_usage_usd: float
    monthly_usage_usd: float
    daily_limit_usd: float
    monthly_limit_usd: float
    daily_percentage: float
    monthly_percentage: float
    daily_request_count: int
    monthly_request_count: int
    avg_cost_per_request: float
    alerts_today: List[BudgetAlert] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "provider_name": self.provider_name,
            "daily_usage_usd": self.daily_usage_usd,
            "monthly_usage_usd": self.monthly_usage_usd,
            "daily_limit_usd": self.daily_limit_usd,
            "monthly_limit_usd": self.monthly_limit_usd,
            "daily_percentage": round(self.daily_percentage, 2),
            "monthly_percentage": round(self.monthly_percentage, 2),
            "daily_request_count": self.daily_request_count,
            "monthly_request_count": self.monthly_request_count,
            "avg_cost_per_request": round(self.avg_cost_per_request, 6),
            "alerts_count": len(self.alerts_today),
            "generated_at": self.generated_at.isoformat()
        }
#!/usr/bin/env python3
"""
Budget Enforcement Demo
========================
Demonstrates the budget enforcement system with real-time alerts
"""

import time
from src.providers.budget.manager import BudgetManager
from src.providers.budget.models import BudgetAlertType


def print_header(title):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def print_success(message):
    """Print a success message."""
    print(f"✓ {message}")


def print_warning(message):
    """Print a warning message."""
    print(f"⚠️  ALERT: {message}")


def print_error(message):
    """Print an error message."""
    print(f"✗ {message}")


def print_info(message):
    """Print an info message."""
    print(f"ℹ️  {message}")


def demo_budget_enforcement():
    """Demonstrate budget enforcement features."""

    # Create manager
    manager = BudgetManager()

    # Register alert callback for visual feedback
    def alert_callback(alert):
        if alert.alert_type == BudgetAlertType.WARNING_80:
            print_warning(f"Daily budget at {alert.percentage:.1f}% - ${alert.usage_usd:.2f}/${alert.limit_usd:.2f}")
        elif alert.alert_type == BudgetAlertType.WARNING_90:
            print_warning(f"Daily budget at {alert.percentage:.1f}% - ${alert.usage_usd:.2f}/${alert.limit_usd:.2f}")
        elif alert.alert_type == BudgetAlertType.EXCEEDED_100:
            print_warning(f"Daily budget exceeded - ${alert.usage_usd:.2f}/${alert.limit_usd:.2f}")

    manager.register_alert_callback(alert_callback)

    # Step 1: Configure provider
    print_header("Step 1: Configure Provider Budget")

    manager.configure_provider(
        provider_name="openai",
        daily_limit_usd=10.00,
        monthly_limit_usd=100.00,
        alerts_enabled=True,
        pause_on_exceed=True
    )

    config = manager._configs["openai"]
    print_success(f"Provider configured: openai")
    print(f"  - Daily limit: ${config.daily_limit_usd:.2f}")
    print(f"  - Monthly limit: ${config.monthly_limit_usd:.2f}")
    print(f"  - Alerts enabled: {config.alerts_enabled}")
    print(f"  - Pause on exceed: {config.pause_on_exceed}")

    time.sleep(1)

    # Step 2: Check budget (should be OK)
    print_header("Step 2: Initial Budget Check")

    can_proceed, reason = manager.check_budget("openai")
    if can_proceed:
        print_success(f"Budget check: {reason}")
    else:
        print_error(f"Budget check: {reason}")

    time.sleep(1)

    # Step 3: Record usage - 80% threshold
    print_header("Step 3: Record Usage - 80% Threshold")

    print_info("Recording $8.00 of usage...")
    alert = manager.record_usage("openai", 8.00)

    # Alert callback will print the warning

    # Check current status
    usage = manager.get_usage("openai")
    if usage:
        print(f"  - Daily usage: ${usage.daily_usage_usd:.2f}/${config.daily_limit_usd:.2f}")
        print(f"  - Requests: {usage.daily_request_count}")
        print(f"  - Status: {usage.daily_status.value.upper()}")

    time.sleep(1)

    # Step 4: Record more usage - 90% threshold
    print_header("Step 4: Record Usage - 90% Threshold")

    print_info("Recording $1.00 more of usage...")
    alert = manager.record_usage("openai", 1.00)

    # Alert callback will print the warning

    # Check current status
    usage = manager.get_usage("openai")
    if usage:
        print(f"  - Daily usage: ${usage.daily_usage_usd:.2f}/${config.daily_limit_usd:.2f}")
        print(f"  - Requests: {usage.daily_request_count}")
        print(f"  - Status: {usage.daily_status.value.upper()}")

    time.sleep(1)

    # Step 5: Record more usage - 100% exceeded
    print_header("Step 5: Record Usage - Budget Exceeded")

    print_info("Recording $1.00 more of usage...")
    alert = manager.record_usage("openai", 1.00)

    # Alert callback will print the exceeded alert

    # Check current status
    usage = manager.get_usage("openai")
    if usage:
        print(f"  - Daily usage: ${usage.daily_usage_usd:.2f}/${config.daily_limit_usd:.2f}")
        print(f"  - Requests: {usage.daily_request_count}")
        print(f"  - Status: {usage.daily_status.value.upper()}")

    time.sleep(1)

    # Step 6: Check budget (should be blocked)
    print_header("Step 6: Budget Check After Exceeding")

    can_proceed, reason = manager.check_budget("openai")
    if can_proceed:
        print_success(f"Budget check: {reason}")
    else:
        print_error(f"Budget check: {reason}")

    time.sleep(1)

    # Step 7: Generate usage report
    print_header("Step 7: Usage Report")

    report = manager.get_report("openai")
    if report:
        print(f"Provider: {report.provider_name}")
        print(f"Daily Usage: ${report.daily_usage_usd:.2f}/${report.daily_limit_usd:.2f} ({report.daily_percentage:.1f}%)")
        print(f"Monthly Usage: ${report.monthly_usage_usd:.2f}/${report.monthly_limit_usd:.2f} ({report.monthly_percentage:.1f}%)")
        print(f"Daily Requests: {report.daily_request_count}")
        print(f"Monthly Requests: {report.monthly_request_count}")
        print(f"Average Cost per Request: ${report.avg_cost_per_request:.6f}")
        print(f"Alerts Today: {len(report.alerts_today)}")
        daily_status = "EXCEEDED" if report.daily_usage_usd >= report.daily_limit_usd else "OK"
        monthly_status = "EXCEEDED" if report.monthly_usage_usd >= report.monthly_limit_usd else "OK"
        print(f"Daily Status: {daily_status}")
        print(f"Monthly Status: {monthly_status}")

    time.sleep(1)

    # Step 8: Reset and demonstrate recovery
    print_header("Step 8: Reset Budget & Recovery")

    print_info("Resetting daily budget...")
    manager.reset_daily("openai")

    usage = manager.get_usage("openai")
    if usage:
        print(f"  - Daily usage: ${usage.daily_usage_usd:.2f}/${config.daily_limit_usd:.2f}")
        print(f"  - Daily requests: {usage.daily_request_count}")
        print(f"  - Status: {usage.daily_status.value.upper()}")

    # Check budget again
    can_proceed, reason = manager.check_budget("openai")
    if can_proceed:
        print_success(f"Budget check: {reason}")
    else:
        print_error(f"Budget check: {reason}")

    print_success("Budget enforcement system is ready for production use!")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  MULTI-PROVIDER AI GATEWAY: BUDGET ENFORCEMENT DEMO")
    print("=" * 60)

    demo_budget_enforcement()

    print("\n" + "=" * 60)
    print("  Demo Complete!")
    print("=" * 60 + "\n")
"""Unit tests for health checker"""

import asyncio

import pytest

from src.monitoring.health_checker import Dependency, HealthCheck, HealthChecker

# ============================================================================
# HealthCheck Tests
# ============================================================================


@pytest.mark.unit
class TestHealthCheck:
    """Test HealthCheck"""

    def test_health_check_init(self):
        """Test health check initialization"""

        def mock_check():
            return {"status": "healthy"}

        check = HealthCheck(name="test_check", check_fn=mock_check, timeout=5, critical=True)

        assert check.name == "test_check"
        assert check.timeout == 5
        assert check.critical is True


# ============================================================================
# Dependency Tests
# ============================================================================


@pytest.mark.unit
class TestDependency:
    """Test Dependency"""

    def test_dependency_init(self):
        """Test dependency initialization"""
        dep = Dependency(
            name="test_dep", url="https://example.com", type="http", timeout=5, critical=True
        )

        assert dep.name == "test_dep"
        assert dep.url == "https://example.com"
        assert dep.type == "http"
        assert dep.timeout == 5
        assert dep.critical is True


# ============================================================================
# HealthChecker Tests
# ============================================================================


@pytest.mark.unit
class TestHealthChecker:
    """Test HealthChecker"""

    @pytest.mark.asyncio
    async def test_health_checker_init(self):
        """Test health checker initialization"""
        checker = HealthChecker()

        assert len(checker.checks) > 0
        assert len(checker.dependencies) == 0

    @pytest.mark.asyncio
    async def test_health_checker_default_checks(self):
        """Test default health checks are created"""
        checker = HealthChecker()

        assert "disk_space" in checker.checks
        assert "memory" in checker.checks
        assert "cpu" in checker.checks

    @pytest.mark.asyncio
    async def test_health_checker_add_check(self):
        """Test adding health check"""
        checker = HealthChecker()

        def mock_check():
            return {"status": "healthy"}

        check = HealthCheck(name="custom_check", check_fn=mock_check, timeout=5, critical=False)

        checker.add_check(check)
        assert "custom_check" in checker.checks

    @pytest.mark.asyncio
    async def test_health_checker_remove_check(self):
        """Test removing health check"""
        checker = HealthChecker()
        checker.remove_check("disk_space")

        assert "disk_space" not in checker.checks

    @pytest.mark.asyncio
    async def test_health_checker_add_dependency(self):
        """Test adding dependency"""
        checker = HealthChecker()

        dep = Dependency(
            name="azure_openai",
            url="https://test.openai.azure.com",
            type="api",
            timeout=5,
            critical=True,
        )

        checker.add_dependency(dep)
        assert "azure_openai" in checker.dependencies

    @pytest.mark.asyncio
    async def test_health_checker_remove_dependency(self):
        """Test removing dependency"""
        checker = HealthChecker()

        dep = Dependency(name="test_dep", url="https://example.com", type="http")

        checker.add_dependency(dep)
        checker.remove_dependency("test_dep")

        assert "test_dep" not in checker.dependencies

    @pytest.mark.asyncio
    async def test_health_checker_check_health(self):
        """Test checking application health"""
        checker = HealthChecker()
        health = await checker.check_health()

        assert "status" in health
        assert "checks" in health
        assert "uptime_seconds" in health
        assert "timestamp" in health

        assert health["status"] in ["healthy", "degraded", "unhealthy"]

    @pytest.mark.asyncio
    async def test_health_checker_check_dependencies(self):
        """Test checking dependencies"""
        checker = HealthChecker()

        # Add a dependency
        dep = Dependency(
            name="test_dep", url="https://example.com", type="http", timeout=1, critical=False
        )

        checker.add_dependency(dep)

        # Check dependencies
        deps = await checker.check_dependencies()

        assert "status" in deps
        assert "dependencies" in deps
        assert "timestamp" in deps

    @pytest.mark.asyncio
    async def test_health_checker_get_system_status(self):
        """Test getting system status"""
        checker = HealthChecker()
        status = checker.get_system_status()

        assert "status" in status
        assert "metrics" in status
        assert "uptime_seconds" in status
        assert "timestamp" in status

        assert "cpu_usage_percent" in status["metrics"]
        assert "memory_usage_percent" in status["metrics"]
        assert "disk_usage_percent" in status["metrics"]

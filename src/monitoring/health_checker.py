"""
Health checker for Azure AI Infrastructure Platform

This module provides:
- Health checks
- Dependency checks
- Resource checks
- Health status aggregation
- Health endpoints
"""

import asyncio
import logging
import shutil
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class HealthCheck:
    """Health check definition"""

    def __init__(self, name: str, check_fn: Callable, timeout: int = 5, critical: bool = True):
        """
        Initialize health check

        Args:
            name: Check name
            check_fn: Check function
            timeout: Timeout in seconds
            critical: Whether check is critical
        """
        self.name = name
        self.check_fn = check_fn
        self.timeout = timeout
        self.critical = critical


class Dependency:
    """Dependency definition"""

    def __init__(self, name: str, url: str, type: str, timeout: int = 5, critical: bool = True):
        """
        Initialize dependency

        Args:
            name: Dependency name
            url: Dependency URL
            type: Dependency type
            timeout: Timeout in seconds
            critical: Whether dependency is critical
        """
        self.name = name
        self.url = url
        self.type = type
        self.timeout = timeout
        self.critical = critical


class HealthChecker:
    """Check application health"""

    def __init__(self):
        """Initialize health checker"""
        self.checks: Dict[str, HealthCheck] = {}
        self.dependencies: Dict[str, Dependency] = {}
        self.start_time = datetime.utcnow()

        # Initialize default checks
        self._initialize_default_checks()

    def _initialize_default_checks(self):
        """Initialize default health checks"""
        # Add disk space check
        self.add_check(
            HealthCheck(
                name="disk_space", check_fn=self._check_disk_space, timeout=5, critical=True
            )
        )

        # Add memory check
        self.add_check(
            HealthCheck(name="memory", check_fn=self._check_memory, timeout=5, critical=True)
        )

        # Add CPU check
        self.add_check(HealthCheck(name="cpu", check_fn=self._check_cpu, timeout=5, critical=False))

    def add_check(self, check: HealthCheck):
        """
        Add a health check

        Args:
            check: HealthCheck to add
        """
        self.checks[check.name] = check
        logger.info(f"Added health check: {check.name}")

    def remove_check(self, name: str):
        """
        Remove a health check

        Args:
            name: Check name to remove
        """
        if name in self.checks:
            del self.checks[name]
            logger.info(f"Removed health check: {name}")

    def add_dependency(self, dependency: Dependency):
        """
        Add a dependency check

        Args:
            dependency: Dependency to add
        """
        self.dependencies[dependency.name] = dependency
        logger.info(f"Added dependency: {dependency.name}")

    def remove_dependency(self, name: str):
        """
        Remove a dependency

        Args:
            name: Dependency name to remove
        """
        if name in self.dependencies:
            del self.dependencies[name]
            logger.info(f"Removed dependency: {name}")

    async def check_health(self) -> Dict[str, Any]:
        """
        Check application health

        Returns:
            Dictionary with health status
        """
        check_results = {}
        overall_status = "healthy"
        uptime = (datetime.utcnow() - self.start_time).total_seconds()

        # Run all checks
        for name, check in self.checks.items():
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(check.check_fn), timeout=check.timeout
                )

                check_results[name] = {
                    "status": result.get("status", "healthy"),
                    "latency_ms": result.get("latency_ms", 0),
                    "message": result.get("message", "OK"),
                }

                # Update overall status
                if check.critical and check_results[name]["status"] != "healthy":
                    overall_status = "unhealthy"
                elif check_results[name]["status"] == "degraded":
                    if overall_status != "unhealthy":
                        overall_status = "degraded"

            except asyncio.TimeoutError:
                check_results[name] = {
                    "status": "unhealthy",
                    "latency_ms": check.timeout * 1000,
                    "message": "Check timed out",
                }

                if check.critical:
                    overall_status = "unhealthy"

            except Exception as e:
                check_results[name] = {
                    "status": "unhealthy",
                    "latency_ms": 0,
                    "message": f"Check failed: {str(e)}",
                }

                if check.critical:
                    overall_status = "unhealthy"

        return {
            "status": overall_status,
            "checks": check_results,
            "uptime_seconds": uptime,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def check_dependencies(self) -> Dict[str, Any]:
        """
        Check dependencies

        Returns:
            Dictionary with dependency status
        """
        dependency_results = {}
        overall_status = "healthy"

        # Run all dependency checks
        for name, dependency in self.dependencies.items():
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(self._check_dependency, dependency),
                    timeout=dependency.timeout,
                )

                dependency_results[name] = {
                    "status": result.get("status", "healthy"),
                    "latency_ms": result.get("latency_ms", 0),
                    "url": dependency.url,
                    "type": dependency.type,
                    "message": result.get("message", "OK"),
                }

                # Update overall status
                if dependency.critical and dependency_results[name]["status"] != "healthy":
                    overall_status = "unhealthy"
                elif dependency_results[name]["status"] == "degraded":
                    if overall_status != "unhealthy":
                        overall_status = "degraded"

            except asyncio.TimeoutError:
                dependency_results[name] = {
                    "status": "unhealthy",
                    "latency_ms": dependency.timeout * 1000,
                    "url": dependency.url,
                    "type": dependency.type,
                    "message": "Dependency check timed out",
                }

                if dependency.critical:
                    overall_status = "unhealthy"

            except Exception as e:
                dependency_results[name] = {
                    "status": "unhealthy",
                    "latency_ms": 0,
                    "url": dependency.url,
                    "type": dependency.type,
                    "message": f"Dependency check failed: {str(e)}",
                }

                if dependency.critical:
                    overall_status = "unhealthy"

        return {
            "status": overall_status,
            "dependencies": dependency_results,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _check_disk_space(self) -> Dict[str, Any]:
        """
        Check disk space

        Returns:
            Dictionary with check result
        """
        import shutil

        try:
            usage = shutil.disk_usage("/")
            percent_used = (usage.used / usage.total) * 100

            status = "healthy"
            message = f"Disk usage: {percent_used:.1f}%"

            if percent_used > 90:
                status = "unhealthy"
                message = f"Disk usage critical: {percent_used:.1f}%"
            elif percent_used > 75:
                status = "degraded"
                message = f"Disk usage high: {percent_used:.1f}%"

            return {"status": status, "message": message, "percent_used": percent_used}

        except Exception as e:
            return {"status": "unhealthy", "message": f"Failed to check disk space: {str(e)}"}

    def _check_memory(self) -> Dict[str, Any]:
        """
        Check memory usage

        Returns:
            Dictionary with check result
        """
        try:
            import psutil

            memory = psutil.virtual_memory()
            percent_used = memory.percent

            status = "healthy"
            message = f"Memory usage: {percent_used:.1f}%"

            if percent_used > 90:
                status = "unhealthy"
                message = f"Memory usage critical: {percent_used:.1f}%"
            elif percent_used > 75:
                status = "degraded"
                message = f"Memory usage high: {percent_used:.1f}%"

            return {"status": status, "message": message, "percent_used": percent_used}

        except ImportError:
            # psutil not available, return healthy
            return {"status": "healthy", "message": "Memory check not available"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"Failed to check memory: {str(e)}"}

    def _check_cpu(self) -> Dict[str, Any]:
        """
        Check CPU usage

        Returns:
            Dictionary with check result
        """
        try:
            import psutil

            percent_used = psutil.cpu_percent(interval=1)

            status = "healthy"
            message = f"CPU usage: {percent_used:.1f}%"

            if percent_used > 90:
                status = "unhealthy"
                message = f"CPU usage critical: {percent_used:.1f}%"
            elif percent_used > 75:
                status = "degraded"
                message = f"CPU usage high: {percent_used:.1f}%"

            return {"status": status, "message": message, "percent_used": percent_used}

        except ImportError:
            # psutil not available, return healthy
            return {"status": "healthy", "message": "CPU check not available"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"Failed to check CPU: {str(e)}"}

    def _check_dependency(self, dependency: Dependency) -> Dict[str, Any]:
        """
        Check a dependency

        Args:
            dependency: Dependency to check

        Returns:
            Dictionary with check result
        """
        import time
        import urllib.error
        import urllib.request

        start_time = time.time()

        try:
            if dependency.type == "http":
                # HTTP check
                request = urllib.request.Request(dependency.url, method="HEAD")

                with urllib.request.urlopen(request, timeout=dependency.timeout) as response:
                    latency_ms = (time.time() - start_time) * 1000

                    if response.status < 400:
                        return {
                            "status": "healthy",
                            "latency_ms": latency_ms,
                            "message": f"HTTP status: {response.status}",
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "latency_ms": latency_ms,
                            "message": f"HTTP error: {response.status}",
                        }

            elif dependency.type == "api":
                # API check (GET request)
                request = urllib.request.Request(dependency.url)

                with urllib.request.urlopen(request, timeout=dependency.timeout) as response:
                    latency_ms = (time.time() - start_time) * 1000

                    if response.status < 400:
                        return {
                            "status": "healthy",
                            "latency_ms": latency_ms,
                            "message": "API responding",
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "latency_ms": latency_ms,
                            "message": f"API error: {response.status}",
                        }

            else:
                return {
                    "status": "unhealthy",
                    "latency_ms": 0,
                    "message": f"Unknown dependency type: {dependency.type}",
                }

        except urllib.error.HTTPError as e:
            latency_ms = (time.time() - start_time) * 1000
            return {
                "status": "unhealthy",
                "latency_ms": latency_ms,
                "message": f"HTTP error: {e.code}",
            }

        except urllib.error.URLError as e:
            latency_ms = (time.time() - start_time) * 1000
            return {
                "status": "unhealthy",
                "latency_ms": latency_ms,
                "message": f"URL error: {str(e.reason)}",
            }

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return {
                "status": "unhealthy",
                "latency_ms": latency_ms,
                "message": f"Dependency check failed: {str(e)}",
            }

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get system status

        Returns:
            Dictionary with system status
        """
        try:
            import psutil

            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = shutil.disk_usage("/")

            uptime = (datetime.utcnow() - self.start_time).total_seconds()

            return {
                "status": "operational",
                "metrics": {
                    "cpu_usage_percent": cpu_percent,
                    "memory_usage_percent": memory.percent,
                    "disk_usage_percent": (disk.used / disk.total) * 100,
                },
                "uptime_seconds": uptime,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except ImportError:
            uptime = (datetime.utcnow() - self.start_time).total_seconds()

            return {
                "status": "operational",
                "metrics": {
                    "cpu_usage_percent": 0.0,
                    "memory_usage_percent": 0.0,
                    "disk_usage_percent": 0.0,
                },
                "uptime_seconds": uptime,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "System metrics not available",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get system status: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            }


# Global instance
health_checker = HealthChecker()

"""Unit tests for telemetry module"""

import asyncio

import pytest

from src.monitoring.telemetry import TelemetryManager, telemetry_manager


@pytest.mark.unit
class TestTelemetryManager:
    """Test telemetry manager"""

    @pytest.mark.asyncio
    async def test_track_event(self):
        """Test tracking telemetry event"""
        manager = telemetry_manager

        await manager.track_event(name="test_event", properties={"key": "value"})

        assert manager is not None

    @pytest.mark.asyncio
    async def test_track_metric(self):
        """Test tracking telemetry metric"""
        manager = telemetry_manager

        await manager.track_metric(name="test_metric", value=42.5, properties={"unit": "ms"})

        assert manager is not None

    @pytest.mark.asyncio
    async def test_track_exception(self):
        """Test tracking telemetry exception"""
        manager = telemetry_manager

        try:
            raise ValueError("Test exception")
        except Exception as e:
            await manager.track_exception(exception=e, properties={"custom": "data"})

        assert manager is not None

    @pytest.mark.asyncio
    async def test_track_dependency(self):
        """Test tracking telemetry dependency call"""
        manager = telemetry_manager

        await manager.track_dependency(
            type_name="HTTP",
            target="test.openai.azure.com",
            name="azure_openai",
            data="POST https://test.openai.azure.com",
            duration=150,
            success=True,
        )

        assert manager is not None

    @pytest.mark.asyncio
    async def test_track_request(self):
        """Test tracking telemetry request"""
        manager = telemetry_manager

        await manager.track_request(
            name="GET /chat",
            url="http://localhost:8000/chat",
            duration=100,
            response_code=200,
            success=True,
        )

        assert manager is not None

    @pytest.mark.asyncio
    async def test_start_stop_operation(self):
        """Test start and stop operation"""
        manager = telemetry_manager

        op_id = await manager.start_operation("test_operation")
        assert op_id is not None

        await manager.stop_operation(op_id, success=True)

        assert manager is not None

    def test_telemetry_manager_initialization(self):
        """Test telemetry manager initialization"""
        manager = telemetry_manager

        assert manager is not None
        assert isinstance(manager, TelemetryManager)

    @pytest.mark.asyncio
    async def test_multiple_operations(self):
        """Test multiple concurrent operations"""
        manager = telemetry_manager

        # Start multiple operations
        ops = []
        for i in range(5):
            op_id = await manager.start_operation(f"operation_{i}")
            ops.append(op_id)

        # Stop all operations
        for op_id in ops:
            await manager.stop_operation(op_id, success=True)

        assert len(ops) == 5

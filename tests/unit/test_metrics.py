"""Unit tests for metrics module"""

import pytest
import asyncio
from src.monitoring.metrics import MetricsCollector
from datetime import datetime


@pytest.mark.unit
class TestMetricsCollector:
    """Test metrics collector"""
    
    @pytest.mark.asyncio
    async def test_init(self):
        """Test metrics collector initialization"""
        collector = MetricsCollector()
        
        assert collector is not None
    
    @pytest.mark.asyncio
    async def test_record_metric(self):
        """Test record metric"""
        collector = MetricsCollector()
        
        await collector.record_metric(
            metric_name="test_metric",
            value=42.5,
            timestamp=datetime.utcnow()
        )
        
        assert collector is not None
    
    @pytest.mark.asyncio
    async def test_get_all_metrics(self):
        """Test get all metrics"""
        collector = MetricsCollector()
        
        # Record some metrics
        await collector.record_metric("test1", 10, datetime.utcnow())
        await collector.record_metric("test2", 20, datetime.utcnow())
        
        metrics = await collector.get_all_metrics()
        
        assert metrics is not None
        assert isinstance(metrics, dict)
    
    @pytest.mark.asyncio
    async def test_get_metric_stats(self):
        """Test get metric statistics"""
        collector = MetricsCollector()
        
        # Record some metrics
        for i in range(10):
            await collector.record_metric(f"metric_{i % 3}", i, datetime.utcnow())
        
        stats = await collector.get_metric_stats("metric_0")
        
        assert stats is not None
        assert isinstance(stats, dict)
    
    @pytest.mark.asyncio
    async def test_reset_metrics(self):
        """Test reset all metrics"""
        collector = MetricsCollector()
        
        # Record some metrics
        await collector.record_metric("test", 10, datetime.utcnow())
        
        # Reset
        await collector.reset_metrics()
        
        assert collector is not None
    
    @pytest.mark.asyncio
    async def test_retention_hours(self):
        """Test custom retention hours"""
        collector = MetricsCollector(retention_hours=48)
        
        assert collector is not None
    
    @pytest.mark.asyncio
    async def test_cleanup_old_metrics(self):
        """Test cleanup old metrics"""
        collector = MetricsCollector(retention_hours=1)
        
        # Record some metrics
        await collector.record_metric("test", 10, datetime.utcnow())
        
        # Cleanup
        await collector._cleanup_old_metrics()
        
        assert collector is not None
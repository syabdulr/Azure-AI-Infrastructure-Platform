# Step 7: Monitoring & Observability - Build Plan

## 🎯 Step Overview

**Commit:** `feat: Implement advanced monitoring and observability framework`  
**Estimated Time:** 2 hours  
**Goal:** Build production-ready monitoring and observability features

---

## 🏗️ Monitoring & Observability Architecture

```
┌─────────────────┐
│   Application   │
│                 │
│  • Metrics      │
│  • Logs         │
│  • Traces       │
│  • Events       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Metrics       │
│   Collector     │
│                 │
│  • Counters     │
│  • Gauges       │
│  • Histograms   │
│  • Summaries    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Prometheus    │
│   Exporter      │
│                 │
│  • /metrics     │
│  • Exposition   │
│  • Format       │
└─────────────────┘
```

---

## 📋 Files to Create (5 files, ~1,200 lines)

### 1. Create Metrics Collector
- `src/monitoring/metrics_collector.py` (New: 300 lines)
  - Custom metrics collection
  - Counter metrics
  - Gauge metrics
  - Histogram metrics
  - Summary metrics
  - Metric labels and tags

### 2. Create Log Aggregator
- `src/monitoring/log_aggregator.py` (New: 250 lines)
  - Log collection
  - Log filtering
  - Log aggregation
  - Log format standardization
  - Log export

### 3. Create Alert Manager
- `src/monitoring/alert_manager.py` (New: 250 lines)
  - Alert rules
  - Threshold checking
  - Alert notifications
  - Alert history
  - Alert severity levels

### 4. Create Health Checker
- `src/monitoring/health_checker.py` (New: 200 lines)
  - Health checks
  - Dependency checks
  - Resource checks
  - Health status aggregation
  - Health endpoints

### 5. Create Observability API
- `src/api/routes/observability.py` (New: 200 lines)
  - Metrics query API
  - Logs query API
  - Alerts query API
  - Health status API
  - System status API

---

## 🎯 Key Features to Implement

### 1. Metrics Collector

```python
class MetricsCollector:
    """Collect and manage application metrics"""
    
    def __init__(self):
        """Initialize metrics collector"""
        self.counters = {}
        self.gauges = {}
        self.histograms = {}
        self.summaries = {}
    
    def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None
    ):
        """
        Increment a counter metric
        
        Args:
            name: Metric name
            value: Value to increment by
            labels: Metric labels
        """
        pass
    
    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """
        Set a gauge metric
        
        Args:
            name: Metric name
            value: Value to set
            labels: Metric labels
        """
        pass
    
    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """
        Observe a histogram metric
        
        Args:
            name: Metric name
            value: Value to observe
            labels: Metric labels
        """
        pass
    
    def observe_summary(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """
        Observe a summary metric
        
        Args:
            name: Metric name
            value: Value to observe
            labels: Metric labels
        """
        pass
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics
        
        Returns:
            Dictionary with all metrics
        """
        pass
    
    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus format
        
        Returns:
            Prometheus-formatted metrics string
        """
        pass
```

### 2. Log Aggregator

```python
class LogAggregator:
    """Aggregate and manage application logs"""
    
    def __init__(self):
        """Initialize log aggregator"""
        self.logs = []
        self.max_logs = 10000
    
    def add_log(
        self,
        level: str,
        message: str,
        source: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Add a log entry
        
        Args:
            level: Log level (INFO, WARNING, ERROR)
            message: Log message
            source: Log source
            context: Additional context
        """
        pass
    
    def query_logs(
        self,
        level: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query logs
        
        Args:
            level: Filter by level
            source: Filter by source
            limit: Maximum number of results
            
        Returns:
            List of log entries
        """
        pass
    
    def get_log_stats(self) -> Dict[str, Any]:
        """
        Get log statistics
        
        Returns:
            Dictionary with log statistics
        """
        pass
```

### 3. Alert Manager

```python
class AlertManager:
    """Manage alerts and notifications"""
    
    def __init__(self):
        """Initialize alert manager"""
        self.alerts = []
        self.alert_rules = []
    
    def add_alert_rule(
        self,
        name: str,
        condition: str,
        threshold: float,
        severity: str,
        action: str
    ):
        """
        Add an alert rule
        
        Args:
            name: Rule name
            condition: Condition to check
            threshold: Threshold value
            severity: Alert severity (low, medium, high, critical)
            action: Action to take
        """
        pass
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """
        Check all alert rules
        
        Returns:
            List of triggered alerts
        """
        pass
    
    def trigger_alert(
        self,
        rule_name: str,
        value: float,
        message: str
    ):
        """
        Trigger an alert
        
        Args:
            rule_name: Rule name
            value: Triggered value
            message: Alert message
        """
        pass
    
    def get_alerts(
        self,
        severity: Optional[str] = None,
        active_only: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get alerts
        
        Args:
            severity: Filter by severity
            active_only: Only return active alerts
            limit: Maximum number of results
            
        Returns:
            List of alerts
        """
        pass
```

### 4. Health Checker

```python
class HealthChecker:
    """Check application health"""
    
    def __init__(self):
        """Initialize health checker"""
        self.checks = {}
        self.dependencies = []
    
    def add_check(
        self,
        name: str,
        check_fn: callable,
        timeout: int = 5
    ):
        """
        Add a health check
        
        Args:
            name: Check name
            check_fn: Check function
            timeout: Timeout in seconds
        """
        pass
    
    def add_dependency(
        self,
        name: str,
        url: str,
        timeout: int = 5
    ):
        """
        Add a dependency check
        
        Args:
            name: Dependency name
            url: Dependency URL
            timeout: Timeout in seconds
        """
        pass
    
    def check_health(self) -> Dict[str, Any]:
        """
        Check application health
        
        Returns:
            Dictionary with health status
        """
        pass
    
    def check_dependencies(self) -> Dict[str, Any]:
        """
        Check dependencies
        
        Returns:
            Dictionary with dependency status
        """
        pass
```

---

## 📊 API Enhancements

### Observability Endpoints

```python
GET /observability/metrics
Description: Get all metrics

Response:
{
  "counters": {
    "api_requests_total": {
      "value": 1000,
      "labels": {"endpoint": "/chat", "method": "POST"}
    }
  },
  "gauges": {
    "active_connections": {
      "value": 50,
      "labels": {}
    }
  },
  "histograms": {
    "request_duration_ms": {
      "count": 1000,
      "sum": 50000,
      "buckets": {
        "5ms": 100,
        "10ms": 300,
        "50ms": 800,
        "100ms": 950,
        "500ms": 990,
        "1000ms": 1000
      }
    }
  },
  "summaries": {
    "response_time_ms": {
      "count": 1000,
      "sum": 50000,
      "quantiles": {
        "0.5": 45,
        "0.9": 95,
        "0.95": 120,
        "0.99": 200
      }
    }
  }
}
```

```python
GET /observability/metrics/prometheus
Description: Get metrics in Prometheus format

Response: (text/plain)
# TYPE api_requests_total counter
api_requests_total{endpoint="/chat",method="POST"} 1000

# TYPE active_connections gauge
active_connections 50

# TYPE request_duration_ms histogram
request_duration_ms_bucket{le="5"} 100
request_duration_ms_bucket{le="10"} 300
request_duration_ms_bucket{le="50"} 800
request_duration_ms_bucket{le="100"} 950
request_duration_ms_bucket{le="+Inf"} 1000
request_duration_ms_sum 50000
request_duration_ms_count 1000

# TYPE response_time_ms summary
response_time_ms{quantile="0.5"} 45
response_time_ms{quantile="0.9"} 95
response_time_ms{quantile="0.95"} 120
response_time_ms{quantile="0.99"} 200
response_time_ms_sum 50000
response_time_ms_count 1000
```

```python
GET /observability/logs
Description: Query logs

Query Parameters:
- level: Filter by level (INFO, WARNING, ERROR)
- source: Filter by source
- limit: Maximum number of results (default: 100)

Response:
{
  "logs": [
    {
      "timestamp": "2026-07-25T12:00:00Z",
      "level": "INFO",
      "message": "API request received",
      "source": "api",
      "context": {
        "endpoint": "/chat",
        "user_id": "user-123"
      }
    }
  ],
  "total": 1000,
  "count": 100
}
```

```python
GET /observability/alerts
Description: Get alerts

Query Parameters:
- severity: Filter by severity (low, medium, high, critical)
- active_only: Only return active alerts (default: false)
- limit: Maximum number of results (default: 50)

Response:
{
  "alerts": [
    {
      "id": "alert-123",
      "rule_name": "high_error_rate",
      "severity": "critical",
      "value": 0.95,
      "threshold": 0.9,
      "message": "Error rate exceeded 90%",
      "triggered_at": "2026-07-25T12:00:00Z",
      "active": true
    }
  ],
  "total": 10,
  "count": 5
}
```

```python
GET /observability/health
Description: Get health status

Response:
{
  "status": "healthy",
  "checks": {
    "database": {
      "status": "healthy",
      "latency_ms": 5,
      "message": "Database connection OK"
    },
    "redis": {
      "status": "healthy",
      "latency_ms": 2,
      "message": "Redis connection OK"
    },
    "azure_openai": {
      "status": "healthy",
      "latency_ms": 150,
      "message": "Azure OpenAI API responding"
    }
  },
  "dependencies": {
    "azure_openai": {
      "status": "healthy",
      "url": "https://...openai.azure.com",
      "latency_ms": 150
    },
    "cognitive_search": {
      "status": "healthy",
      "url": "https://...search.windows.net",
      "latency_ms": 50
    }
  },
  "uptime": 86400,
  "version": "1.0.0"
}
```

```python
GET /observability/system
Description: Get system status

Response:
{
  "status": "operational",
  "metrics": {
    "cpu_usage_percent": 45.2,
    "memory_usage_percent": 62.5,
    "disk_usage_percent": 58.3,
    "network_in_bytes": 1000000,
    "network_out_bytes": 500000
  },
  " uptime": 86400,
  "timestamp": "2026-07-25T12:00:00Z"
}
```

---

## 📈 Custom Metrics

### API Metrics
- `api_requests_total` - Counter (endpoint, method, status)
- `api_request_duration_ms` - Histogram (endpoint, method)
- `api_response_time_ms` - Summary (endpoint, method)
- `active_connections` - Gauge

### AI Metrics
- `ai_requests_total` - Counter (model, endpoint)
- `ai_tokens_total` - Counter (model, type)
- `ai_cost_total` - Gauge (model, currency)
- `ai_latency_ms` - Histogram (model)
- `ai_error_rate` - Gauge (model)

### RAG Metrics
- `rag_queries_total` - Counter
- `rag_retrieval_time_ms` - Histogram
- `rag_generation_time_ms` - Histogram
- `rag_total_time_ms` - Histogram
- `rag_documents_retrieved` - Summary
- `rag_relevance_score` - Summary

### Guardrails Metrics
- `guardrails_input_checks_total` - Counter (result)
- `guardrails_output_checks_total` - Counter (result)
- `guardrails_violations_total` - Counter (type, severity)
- `guardrails_rate_limited_total` - Counter (user_id)
- `guardrails_pii_detected_total` - Counter (type)

### System Metrics
- `system_cpu_usage_percent` - Gauge
- `system_memory_usage_percent` - Gauge
- `system_disk_usage_percent` - Gauge
- `system_uptime_seconds` - Counter

---

## 🚨 Alert Rules

### Error Rate Alert
```python
{
  "name": "high_error_rate",
  "condition": "error_rate",
  "threshold": 0.9,
  "window": "5m",
  "severity": "critical",
  "action": "notify_team"
}
```

### Latency Alert
```python
{
  "name": "high_latency",
  "condition": "p99_latency",
  "threshold": 500,
  "window": "1m",
  "severity": "high",
  "action": "notify_team"
}
```

### Cost Alert
```python
{
  "name": "high_cost",
  "condition": "hourly_cost",
  "threshold": 10.0,
  "window": "1h",
  "severity": "medium",
  "action": "log_warning"
}
```

### Rate Limit Alert
```python
{
  "name": "high_rate_limit",
  "condition": "rate_limit_rate",
  "threshold": 0.1,
  "window": "1m",
  "severity": "medium",
  "action": "log_warning"
}
```

---

## 📝 Success Criteria

✅ Metrics collector with 4 metric types  
✅ Prometheus export endpoint  
✅ Log aggregation with filtering  
✅ Alert manager with rules  
✅ Health checker with dependencies  
✅ Observability API (6+ endpoints)  
✅ 20+ custom metrics  
✅ 5+ alert rules  
✅ Health checks for all dependencies  
✅ System status monitoring  

---

## 🚀 What This Will Add

**New Functionality:**
- ✅ Complete metrics collection framework
- ✅ Prometheus integration
- ✅ Log aggregation
- ✅ Alert management
- ✅ Health checking
- ✅ System monitoring

**Recruiter Impact:**
- ✅ Demonstrates observability expertise
- ✅ Shows production-ready monitoring
- ✅ Prometheus/Grafana readiness
- ✅ Proactive alerting
- ✅ Operational excellence

---

## 📊 Progress After Step 7

- **Files Created:** 5 new files (~1,200 lines)
- **Files Updated:** 2 files (~20 lines)
- **Total New Code:** ~1,220 lines
- **Commits:** 7 total
- **Steps Complete:** 7/13 (53.8%)

---

## ⏭️ Ready to Build?

**Next Action:** Implement monitoring and observability framework

**Estimated Time:** 2 hours

**Type "yes" to start building Step 7!** 🚀
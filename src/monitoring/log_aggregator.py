"""
Log aggregator for Azure AI Infrastructure Platform

This module provides:
- Log collection
- Log filtering
- Log aggregation
- Log format standardization
- Log export
"""

import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class LogAggregator:
    """Aggregate and manage application logs"""

    def __init__(self, max_logs: int = 10000):
        """
        Initialize log aggregator

        Args:
            max_logs: Maximum number of logs to keep
        """
        self.logs = []
        self.max_logs = max_logs
        self.log_counts = defaultdict(int)

        # Log levels in order of severity
        self.level_severity = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}

    def add_log(
        self, level: str, message: str, source: str, context: Optional[Dict[str, Any]] = None
    ):
        """
        Add a log entry

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            source: Log source (module/component)
            context: Additional context
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level.upper(),
            "message": message,
            "source": source,
            "context": context or {},
        }

        self.logs.append(log_entry)
        self.log_counts[level.upper()] += 1

        # Trim logs if over limit
        if len(self.logs) > self.max_logs:
            # Remove oldest logs
            excess = len(self.logs) - self.max_logs
            for i in range(excess):
                removed = self.logs.pop(0)
                self.log_counts[removed["level"]] -= 1

    def query_logs(
        self,
        level: Optional[str] = None,
        source: Optional[str] = None,
        search: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Query logs

        Args:
            level: Filter by level
            source: Filter by source
            search: Search in message
            start_time: Start time (ISO format)
            end_time: End time (ISO format)
            limit: Maximum number of results

        Returns:
            List of log entries
        """
        filtered = self.logs

        # Filter by level
        if level:
            filtered = [log for log in filtered if log["level"] == level.upper()]

        # Filter by source
        if source:
            filtered = [log for log in filtered if source.lower() in log["source"].lower()]

        # Search in message
        if search:
            filtered = [log for log in filtered if search.lower() in log["message"].lower()]

        # Filter by time range
        if start_time:
            filtered = [log for log in filtered if log["timestamp"] >= start_time]

        if end_time:
            filtered = [log for log in filtered if log["timestamp"] <= end_time]

        # Sort by timestamp (newest first) and limit
        filtered = sorted(filtered, key=lambda x: x["timestamp"], reverse=True)
        return filtered[:limit]

    def get_log_stats(self) -> Dict[str, Any]:
        """
        Get log statistics

        Returns:
            Dictionary with log statistics
        """
        # Count by level
        level_counts = defaultdict(int)
        source_counts = defaultdict(int)

        for log in self.logs:
            level_counts[log["level"]] += 1
            source_counts[log["source"]] += 1

        # Calculate error rate
        total_logs = len(self.logs)
        error_count = level_counts.get("ERROR", 0) + level_counts.get("CRITICAL", 0)
        error_rate = error_count / total_logs if total_logs > 0 else 0.0

        # Get recent errors
        recent_errors = [log for log in self.logs if log["level"] in ["ERROR", "CRITICAL"]][:10]

        return {
            "total_logs": total_logs,
            "by_level": dict(level_counts),
            "by_source": dict(source_counts),
            "error_rate": error_rate,
            "recent_errors": recent_errors,
            "max_logs": self.max_logs,
            "current_logs": len(self.logs),
        }

    def get_recent_logs(self, level: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent logs

        Args:
            level: Filter by level (optional)
            limit: Maximum number of results

        Returns:
            List of recent log entries
        """
        return self.query_logs(level=level, limit=limit)

    def get_error_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get error logs

        Args:
            limit: Maximum number of results

        Returns:
            List of error log entries
        """
        return self.query_logs(level="ERROR", limit=limit)

    def clear_logs(self):
        """Clear all logs"""
        self.logs.clear()
        self.log_counts.clear()

    def export_logs(
        self,
        level: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        format: str = "json",
    ) -> str:
        """
        Export logs

        Args:
            level: Filter by level (optional)
            start_time: Start time (ISO format)
            end_time: End time (ISO format)
            format: Export format (json, text)

        Returns:
            Exported logs string
        """
        logs = self.query_logs(
            level=level, start_time=start_time, end_time=end_time, limit=self.max_logs
        )

        if format == "json":
            import json

            return json.dumps(logs, indent=2)
        elif format == "text":
            lines = []
            for log in logs:
                lines.append(
                    f"[{log['timestamp']}] {log['level']} [{log['source']}] {log['message']}"
                )
            return "\n".join(lines)
        else:
            raise ValueError(f"Unknown format: {format}")


class LogHandler(logging.Handler):
    """Custom log handler that sends logs to aggregator"""

    def __init__(self, aggregator: LogAggregator):
        """
        Initialize log handler

        Args:
            aggregator: LogAggregator instance
        """
        super().__init__()
        self.aggregator = aggregator

    def emit(self, record: logging.LogRecord):
        """
        Emit a log record

        Args:
            record: Log record
        """
        try:
            # Get source from module
            source = getattr(record, "module", record.name)

            # Get context if available
            context = {}
            if hasattr(record, "context"):
                context = record.context

            # Add to aggregator
            self.aggregator.add_log(
                level=record.levelname, message=record.getMessage(), source=source, context=context
            )
        except Exception:
            self.handleError(record)


# Global instance
log_aggregator = LogAggregator()

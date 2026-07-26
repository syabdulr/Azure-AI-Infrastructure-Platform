"""Test helper utilities for Azure AI Infrastructure Platform"""

import json
from datetime import datetime
from typing import Any, Dict, List


class TestDataGenerator:
    """Generate test data for various components"""

    @staticmethod
    def generate_chat_message(content: str = "Test message", role: str = "user") -> Dict[str, Any]:
        """Generate chat message

        Args:
            content: Message content
            role: Message role

        Returns:
            Chat message dictionary
        """
        return {"role": role, "content": content, "timestamp": datetime.utcnow().isoformat()}

    @staticmethod
    def generate_document(
        title: str = "Test Document", content: str = "Test content", metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate document

        Args:
            title: Document title
            content: Document content
            metadata: Document metadata

        Returns:
            Document dictionary
        """
        return {
            "id": f"doc-{datetime.utcnow().timestamp()}",
            "title": title,
            "content": content,
            "source": f"/docs/{title.lower().replace(' ', '-')}.md",
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def generate_documents(count: int = 5) -> List[Dict[str, Any]]:
        """Generate multiple documents

        Args:
            count: Number of documents to generate

        Returns:
            List of document dictionaries
        """
        documents = []
        for i in range(count):
            documents.append(
                TestDataGenerator.generate_document(
                    title=f"Document {i + 1}", content=f"Content for document {i + 1}"
                )
            )
        return documents

    @staticmethod
    def generate_embedding(dimension: int = 3072) -> List[float]:
        """Generate test embedding

        Args:
            dimension: Embedding dimension

        Returns:
            List of embedding values
        """
        return [0.1, 0.2, 0.3, 0.4, 0.5] * (dimension // 5)


class TestAssertions:
    """Custom test assertions"""

    @staticmethod
    def assert_metrics_present(metrics: Dict[str, Any], metric_names: List[str]):
        """Assert that metrics are present

        Args:
            metrics: Metrics dictionary
            metric_names: List of metric names to check

        Raises:
            AssertionError: If any metric is missing
        """
        missing = [name for name in metric_names if name not in metrics]
        if missing:
            raise AssertionError(f"Missing metrics: {missing}")

    @staticmethod
    def assert_alert_triggered(alerts: List[Dict[str, Any]], rule_name: str):
        """Assert that an alert was triggered for a rule

        Args:
            alerts: List of alerts
            rule_name: Rule name to check

        Raises:
            AssertionError: If alert not found
        """
        triggered = [a for a in alerts if a.get("rule_name") == rule_name]
        if not triggered:
            raise AssertionError(f"No alert triggered for rule: {rule_name}")

    @staticmethod
    def assert_log_present(logs: List[Dict[str, Any]], level: str, message_contains: str):
        """Assert that a log entry is present

        Args:
            logs: List of log entries
            level: Log level to check
            message_contains: Message substring to check

        Raises:
            AssertionError: If log not found
        """
        found = [
            log
            for log in logs
            if log.get("level") == level and message_contains in log.get("message", "")
        ]

        if not found:
            raise AssertionError(
                f"No log found with level={level} and message containing '{message_contains}'"
            )


class TestHelpers:
    """Test helper functions"""

    @staticmethod
    def wait_for_condition(
        condition: callable, timeout: float = 5.0, interval: float = 0.1
    ) -> bool:
        """Wait for a condition to become true

        Args:
            condition: Condition function to check
            timeout: Maximum wait time in seconds
            interval: Check interval in seconds

        Returns:
            True if condition became true, False otherwise
        """
        import time

        start = time.time()
        while time.time() - start < timeout:
            if condition():
                return True
            time.sleep(interval)

        return False

    @staticmethod
    def measure_execution_time(func: callable, *args, **kwargs) -> float:
        """Measure execution time of a function

        Args:
            func: Function to measure
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Execution time in seconds
        """
        import time

        start = time.time()
        func(*args, **kwargs)
        return time.time() - start

    @staticmethod
    def count_occurrences(text: str, pattern: str) -> int:
        """Count occurrences of a pattern in text

        Args:
            text: Text to search
            pattern: Pattern to find

        Returns:
            Number of occurrences
        """
        return text.count(pattern)


class MockResponse:
    """Mock HTTP response for testing"""

    def __init__(self, status_code: int = 200, json_data: Dict[str, Any] = None, text: str = None):
        """Initialize mock response

        Args:
            status_code: HTTP status code
            json_data: Response JSON data
            text: Response text
        """
        self.status_code = status_code
        self._json_data = json_data or {}
        self._text = text or json.dumps(json_data) if json_data else ""

    def json(self):
        """Return JSON data"""
        return self._json_data

    @property
    def text(self) -> str:
        """Return text"""
        return self._text

    def raise_for_status(self):
        """Raise HTTP error if status code indicates error"""
        if self.status_code >= 400:
            raise Exception(f"HTTP Error: {self.status_code}")


class MockStream:
    """Mock streaming response for testing"""

    def __init__(self, chunks: List[Dict[str, Any]]):
        """Initialize mock stream

        Args:
            chunks: List of stream chunks
        """
        self.chunks = chunks
        self.index = 0

    def __iter__(self):
        """Return iterator"""
        return self

    def __next__(self):
        """Get next chunk"""
        if self.index >= len(self.chunks):
            raise StopIteration

        chunk = self.chunks[self.index]
        self.index += 1

        return chunk

    async def __aiter__(self):
        """Return async iterator"""
        for chunk in self.chunks:
            yield chunk

"""Audit logger for guardrail decisions."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import GuardrailResult


class AuditLogger:
    """Logs all guardrail decisions for compliance and auditing."""

    def __init__(self) -> None:
        self._entries: List[Dict[str, Any]] = []

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    def log(
        self,
        request_id: str,
        prompt: str,
        provider: str,
        model: str,
        action: str,
        violations: List[Dict[str, Any]],
    ) -> None:
        """Log a guardrail decision."""
        self._entries.append(
            {
                "request_id": request_id,
                "prompt": prompt[:200],
                "provider": provider,
                "model": model,
                "action": action,
                "violations": violations,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def get_entries(self, action: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get audit entries, optionally filtered by action."""
        if action:
            return [e for e in self._entries if e["action"] == action]
        return list(self._entries)

    def get_violation_summary(self) -> Dict[str, Any]:
        """Get a summary of all violations."""
        by_type: Dict[str, int] = {}
        total = 0

        for entry in self._entries:
            for v in entry.get("violations", []):
                vtype = v.get("type", "unknown")
                by_type[vtype] = by_type.get(vtype, 0) + 1
                total += 1

        return {
            "total_violations": total,
            "by_type": by_type,
        }

    def clear(self) -> None:
        """Clear all audit entries."""
        self._entries.clear()

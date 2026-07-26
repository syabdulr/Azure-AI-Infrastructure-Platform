"""
Utilities Module - AI-powered utilities business processes

This module provides end-to-end AI workflows for utilities companies:
- Utility bill processing (PDF extraction, data parsing)
- Regulation document search (RAG-based semantic search)
- Customer support automation (AI-powered ticket classification and routing)
- Usage analytics (cost tracking, anomaly detection)

Use Cases:
1. Automated utility bill processing (save 80% manual effort)
2. Regulation compliance queries (reduce research time by 70%)
3. Customer support automation (reduce response time by 60%)
4. Usage analytics (detect anomalies and cost optimization)

Author: Abdul Syed
Email: syabdulr6@gmail.com
GitHub: syabdulr
"""

from .bill_processor import BillProcessor
from .regulation_search import RegulationSearch
from .support_automation import SupportAutomation
from .analytics import UsageAnalytics

__all__ = [
    "BillProcessor",
    "RegulationSearch",
    "SupportAutomation",
    "UsageAnalytics"
]

__version__ = "1.0.0"
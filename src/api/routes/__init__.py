"""
API routes module for Azure AI Infrastructure Platform

This module contains all FastAPI route handlers.
"""

from . import chat, health, monitoring, rag

__all__ = ["chat", "rag", "health", "monitoring"]

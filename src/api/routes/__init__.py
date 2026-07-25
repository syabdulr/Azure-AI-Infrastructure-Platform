"""
API routes module for Azure AI Infrastructure Platform

This module contains all FastAPI route handlers.
"""

from . import chat, rag, health, monitoring

__all__ = ["chat", "rag", "health", "monitoring"]
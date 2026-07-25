"""
Prompt template manager for Azure AI Infrastructure Platform

This module provides:
- Template management
- Version control
- Prompt validation
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PromptManager:
    """Manage prompt templates with versioning"""

    def __init__(self):
        """Initialize prompt manager"""
        self.templates: Dict[str, Dict[str, Any]] = {}
        self._initialize_default_templates()

    def _initialize_default_templates(self):
        """Initialize default prompt templates"""
        self.templates = {
            "chat_system": {
                "template": "You are a helpful AI assistant for the Azure AI Infrastructure Platform. Provide clear, accurate, and concise responses.",
                "version": "1.0",
                "created_at": datetime.utcnow().isoformat()
            },
            "rag_system": {
                "template": "You are a helpful AI assistant that answers questions based on provided context. Use only the information from the sources. If the answer is not in the context, say 'I don't have enough information to answer this question.'",
                "version": "1.0",
                "created_at": datetime.utcnow().isoformat()
            },
            "rag_user": {
                "template": """Based on the following context, answer the question.

Context:
{context}

Question: {question}

Answer:""",
                "version": "1.0",
                "created_at": datetime.utcnow().isoformat()
            }
        }

    def get_template(
        self,
        template_name: str,
        version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a prompt template

        Args:
            template_name: Name of the template
            version: Specific version (optional)

        Returns:
            Template dictionary or None
        """
        template = self.templates.get(template_name)
        if template:
            if version and template.get("version") != version:
                # Version mismatch - could return None or latest
                logger.warning(f"Template {template_name} version {version} not found, returning latest")
            return template
        return None

    def render_template(
        self,
        template_name: str,
        **kwargs
    ) -> Optional[str]:
        """
        Render a template with provided variables

        Args:
            template_name: Name of the template
            **kwargs: Variables to substitute in template

        Returns:
            Rendered template string or None
        """
        template_data = self.get_template(template_name)
        if not template_data:
            return None

        try:
            template = template_data["template"]
            return template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing variable in template {template_name}: {e}")
            return None

    def add_template(
        self,
        name: str,
        template: str,
        version: str = "1.0"
    ) -> bool:
        """
        Add a new prompt template

        Args:
            name: Template name
            template: Template string
            version: Template version

        Returns:
            True if successful, False otherwise
        """
        if name in self.templates:
            logger.warning(f"Template {name} already exists, overwriting")

        self.templates[name] = {
            "template": template,
            "version": version,
            "created_at": datetime.utcnow().isoformat()
        }

        logger.info(f"Template {name} version {version} added")
        return True

    def validate_template(self, template: str) -> bool:
        """
        Validate a template string

        Args:
            template: Template string to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check if template can be formatted
            template.format()
            return True
        except (KeyError, ValueError):
            return False
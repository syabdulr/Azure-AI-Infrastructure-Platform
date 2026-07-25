"""
Prompt versioning system for Azure AI Infrastructure Platform

This module provides:
- Version tracking for prompt templates
- A/B testing support
- Rollback capability
- Metrics comparison
- Active version management
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


class PromptVersion:
    """Represents a single version of a prompt template"""
    
    def __init__(
        self,
        version: str,
        template: str,
        created_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_active: bool = False
    ):
        """
        Initialize prompt version
        
        Args:
            version: Version identifier (e.g., "v1", "v2")
            template: Template string
            created_at: Creation timestamp
            metadata: Version metadata
            is_active: Whether this is the active version
        """
        self.version = version
        self.template = template
        self.created_at = created_at or datetime.utcnow()
        self.metadata = metadata or {}
        self.is_active = is_active
        self.metrics = {
            "usage_count": 0,
            "avg_quality": 0.0,
            "avg_relevance": 0.0,
            "avg_coherence": 0.0,
            "avg_completeness": 0.0
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "version": self.version,
            "template": self.template,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
            "is_active": self.is_active,
            "metrics": self.metrics
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptVersion":
        """Create from dictionary"""
        return cls(
            version=data["version"],
            template=data["template"],
            created_at=datetime.fromisoformat(data["created_at"]),
            metadata=data.get("metadata", {}),
            is_active=data.get("is_active", False)
        )


class PromptVersionManager:
    """Manage prompt versions and A/B testing"""
    
    def __init__(self):
        """Initialize version manager"""
        self.templates: Dict[str, Dict[str, PromptVersion]] = {}
        self.active_versions: Dict[str, str] = {}
    
    def register_template(self, template_name: str):
        """
        Register a new template
        
        Args:
            template_name: Name of the template
        """
        if template_name not in self.templates:
            self.templates[template_name] = {}
            logger.info(f"Registered template: {template_name}")
    
    def add_version(
        self,
        template_name: str,
        version: str,
        template: str,
        metadata: Optional[Dict[str, Any]] = None,
        set_as_active: bool = False
    ) -> PromptVersion:
        """
        Add a new version to a template
        
        Args:
            template_name: Template name
            version: Version identifier
            template: Template string
            metadata: Version metadata
            set_as_active: Set as active version
            
        Returns:
            Created PromptVersion
        """
        # Register template if not exists
        self.register_template(template_name)
        
        # Check if version already exists
        if version in self.templates[template_name]:
            raise ValueError(f"Version {version} already exists for template {template_name}")
        
        # Create new version
        prompt_version = PromptVersion(
            version=version,
            template=template,
            metadata=metadata,
            is_active=set_as_active
        )
        
        # Add to template
        self.templates[template_name][version] = prompt_version
        
        # Set as active if requested
        if set_as_active:
            self.set_active_version(template_name, version)
        
        logger.info(f"Added version {version} to template {template_name}")
        return prompt_version
    
    def get_version(
        self,
        template_name: str,
        version: str
    ) -> Optional[PromptVersion]:
        """
        Get a specific version of a template
        
        Args:
            template_name: Template name
            version: Version identifier
            
        Returns:
            PromptVersion or None
        """
        if template_name not in self.templates:
            return None
        
        return self.templates[template_name].get(version)
    
    def get_active_version(self, template_name: str) -> Optional[PromptVersion]:
        """
        Get the active version for a template
        
        Args:
            template_name: Template name
            
        Returns:
            Active PromptVersion or None
        """
        active_version_id = self.active_versions.get(template_name)
        
        if not active_version_id:
            return None
        
        return self.get_version(template_name, active_version_id)
    
    def set_active_version(self, template_name: str, version: str):
        """
        Set the active version for a template
        
        Args:
            template_name: Template name
            version: Version identifier
        """
        # Validate template and version exist
        if template_name not in self.templates:
            raise ValueError(f"Template {template_name} not found")
        
        if version not in self.templates[template_name]:
            raise ValueError(f"Version {version} not found for template {template_name}")
        
        # Deactivate current active version
        current_active = self.active_versions.get(template_name)
        if current_active:
            self.templates[template_name][current_active].is_active = False
        
        # Set new active version
        self.active_versions[template_name] = version
        self.templates[template_name][version].is_active = True
        
        logger.info(f"Set active version for {template_name} to {version}")
    
    def list_versions(self, template_name: str) -> List[str]:
        """
        List all versions for a template
        
        Args:
            template_name: Template name
            
        Returns:
            List of version identifiers
        """
        if template_name not in self.templates:
            return []
        
        return sorted(
            self.templates[template_name].keys(),
            key=lambda v: self._parse_version(v)
        )
    
    def _parse_version(self, version: str) -> tuple:
        """
        Parse version string for sorting
        
        Args:
            version: Version string (e.g., "v1", "v2.1")
            
        Returns:
            Tuple for sorting
        """
        # Remove 'v' prefix and split
        version = version.lstrip('v')
        parts = version.split('.')
        
        # Convert to integers
        try:
            return tuple(int(p) for p in parts)
        except ValueError:
            # If conversion fails, return original string
            return (version,)
    
    def record_metrics(
        self,
        template_name: str,
        version: str,
        metrics: Dict[str, float]
    ):
        """
        Record metrics for a prompt version
        
        Args:
            template_name: Template name
            version: Version identifier
            metrics: Metrics dictionary (quality, relevance, coherence, completeness)
        """
        prompt_version = self.get_version(template_name, version)
        
        if not prompt_version:
            logger.warning(f"Version {version} not found for template {template_name}")
            return
        
        # Update usage count
        prompt_version.metrics["usage_count"] += 1
        
        # Update averages
        usage_count = prompt_version.metrics["usage_count"]
        
        for metric_name, value in metrics.items():
            if metric_name in prompt_version.metrics:
                current_avg = prompt_version.metrics[metric_name]
                # Calculate new average
                new_avg = (current_avg * (usage_count - 1) + value) / usage_count
                prompt_version.metrics[metric_name] = round(new_avg, 4)
        
        logger.info(f"Recorded metrics for {template_name} v{version}: {metrics}")
    
    def compare_versions(
        self,
        template_name: str,
        versions: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Compare metrics across versions
        
        Args:
            template_name: Template name
            versions: List of versions to compare (all if None)
            
        Returns:
            Dictionary of version metrics
        """
        if versions is None:
            versions = self.list_versions(template_name)
        
        comparison = {}
        
        for version in versions:
            prompt_version = self.get_version(template_name, version)
            
            if prompt_version:
                comparison[version] = {
                    **prompt_version.metrics,
                    "created_at": prompt_version.created_at.isoformat(),
                    "is_active": prompt_version.is_active
                }
        
        return comparison
    
    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """
        Get information about a template
        
        Args:
            template_name: Template name
            
        Returns:
            Template information dictionary
        """
        if template_name not in self.templates:
            return {}
        
        versions = self.list_versions(template_name)
        active_version = self.active_versions.get(template_name)
        
        return {
            "name": template_name,
            "versions": versions,
            "active_version": active_version,
            "total_versions": len(versions),
            "comparison": self.compare_versions(template_name, versions)
        }
    
    def rollback(self, template_name: str, version: str):
        """
        Rollback to a previous version
        
        Args:
            template_name: Template name
            version: Version to rollback to
        """
        logger.info(f"Rolling back {template_name} to version {version}")
        self.set_active_version(template_name, version)
    
    def export_template(self, template_name: str) -> Dict[str, Any]:
        """
        Export template data
        
        Args:
            template_name: Template name
            
        Returns:
            Exported template data
        """
        template_info = self.get_template_info(template_name)
        
        # Convert versions to dictionaries
        versions_data = {}
        for version_str in template_info["versions"]:
            version_obj = self.get_version(template_name, version_str)
            if version_obj:
                versions_data[version_str] = version_obj.to_dict()
        
        return {
            "name": template_name,
            "versions": versions_data,
            "active_version": template_info["active_version"],
            "exported_at": datetime.utcnow().isoformat()
        }
    
    def import_template(self, data: Dict[str, Any]):
        """
        Import template data
        
        Args:
            data: Exported template data
        """
        template_name = data["name"]
        versions_data = data["versions"]
        active_version = data.get("active_version")
        
        # Register template
        self.register_template(template_name)
        
        # Import versions
        for version_str, version_data in versions_data.items():
            self.add_version(
                template_name=template_name,
                version=version_str,
                template=version_data["template"],
                metadata=version_data.get("metadata", {}),
                set_as_active=False
            )
        
        # Set active version
        if active_version:
            self.set_active_version(template_name, active_version)
        
        logger.info(f"Imported template {template_name} with {len(versions_data)} versions")


# Global version manager instance
version_manager = PromptVersionManager()


# Initialize with default templates
def initialize_default_templates():
    """Initialize version manager with default templates"""
    from src.llm.prompts.templates import (
        get_rag_system_prompt,
        get_rag_user_prompt,
        get_rag_user_cot_prompt,
        get_rag_user_fewshot_prompt,
        get_chat_system_prompt,
        get_chat_code_assistant_prompt,
        get_chat_analyst_prompt,
        get_summarization_prompt,
        get_extraction_prompt
    )
    
    # Register RAG templates
    version_manager.add_version("rag_system", "v1", get_rag_system_prompt(), set_as_active=True)
    version_manager.add_version("rag_user", "v1", get_rag_user_prompt(), set_as_active=True)
    version_manager.add_version("rag_user_cot", "v1", get_rag_user_cot_prompt(), set_as_active=False)
    version_manager.add_version("rag_user_fewshot", "v1", get_rag_user_fewshot_prompt(), set_as_active=False)
    
    # Register chat templates
    version_manager.add_version("chat_system", "v1", get_chat_system_prompt(), set_as_active=True)
    version_manager.add_version("chat_code_assistant", "v1", get_chat_code_assistant_prompt(), set_as_active=True)
    version_manager.add_version("chat_analyst", "v1", get_chat_analyst_prompt(), set_as_active=True)
    
    # Register specialized templates
    version_manager.add_version("summarization", "v1", get_summarization_prompt(), set_as_active=True)
    version_manager.add_version("extraction", "v1", get_extraction_prompt(), set_as_active=True)
    
    logger.info("Initialized default prompt templates")


# Initialize on import
try:
    initialize_default_templates()
except Exception as e:
    logger.warning(f"Failed to initialize default templates: {e}")
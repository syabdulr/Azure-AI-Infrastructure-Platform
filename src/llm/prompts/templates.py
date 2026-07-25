"""
Prompt template library for Azure AI Infrastructure Platform

This module provides:
- Prompt template classes
- RAG-specific templates
- Chat-specific templates
- Chain-of-thought templates
- Few-shot learning support
"""

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class PromptTemplate(ABC):
    """Base class for prompt templates"""
    
    def __init__(
        self,
        name: str,
        template: str,
        variables: List[str],
        version: str = "v1"
    ):
        """
        Initialize prompt template
        
        Args:
            name: Template name
            template: Template string with variables
            variables: List of variable names in template
            version: Template version
        """
        self.name = name
        self.template = template
        self.variables = variables
        self.version = version
    
    @abstractmethod
    def render(self, context: Dict[str, Any]) -> str:
        """
        Render template with context
        
        Args:
            context: Dictionary with variable values
            
        Returns:
            Rendered template string
        """
        pass
    
    def validate_context(self, context: Dict[str, Any]) -> bool:
        """
        Validate that all required variables are in context
        
        Args:
            context: Context dictionary
            
        Returns:
            True if valid, False otherwise
        """
        missing_vars = [var for var in self.variables if var not in context]
        if missing_vars:
            logger.warning(f"Missing variables in context: {missing_vars}")
            return False
        return True


class RAGPromptTemplate(PromptTemplate):
    """RAG-specific prompt template"""
    
    def __init__(
        self,
        name: str,
        template: str,
        variables: List[str],
        version: str = "v1",
        chain_of_thought: bool = False,
        few_shot: bool = False
    ):
        """
        Initialize RAG prompt template
        
        Args:
            name: Template name
            template: Template string
            variables: List of variables
            version: Template version
            chain_of_thought: Enable chain-of-thought
            few_shot: Enable few-shot learning
        """
        super().__init__(name, template, variables, version)
        self.chain_of_thought = chain_of_thought
        self.few_shot = few_shot
    
    def render(
        self,
        context: Dict[str, Any],
        examples: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Render RAG template with context and examples
        
        Args:
            context: Context dictionary with variables
            examples: Few-shot examples
            
        Returns:
            Rendered template
        """
        if not self.validate_context(context):
            raise ValueError("Missing required variables in context")
        
        rendered = self.template
        
        # Replace variables
        for var in self.variables:
            placeholder = f"{{{var}}}"
            value = context.get(var, "")
            rendered = rendered.replace(placeholder, str(value))
        
        # Add few-shot examples if enabled
        if self.few_shot and examples:
            examples_text = self._format_examples(examples)
            rendered = rendered.replace("{examples}", examples_text)
        
        return rendered
    
    def _format_examples(self, examples: List[Dict[str, str]]) -> str:
        """Format few-shot examples"""
        formatted = "\n\nExamples:\n"
        for i, example in enumerate(examples, 1):
            formatted += f"\nExample {i}:\n"
            formatted += f"Question: {example.get('question', '')}\n"
            formatted += f"Context: {example.get('context', '')}\n"
            formatted += f"Answer: {example.get('answer', '')}\n"
        return formatted


class ChatPromptTemplate(PromptTemplate):
    """Chat-specific prompt template"""
    
    def render(self, context: Dict[str, Any]) -> str:
        """
        Render chat template with context
        
        Args:
            context: Context dictionary with variables
            
        Returns:
            Rendered template
        """
        if not self.validate_context(context):
            raise ValueError("Missing required variables in context")
        
        rendered = self.template
        
        # Replace variables
        for var in self.variables:
            placeholder = f"{{{var}}}"
            value = context.get(var, "")
            rendered = rendered.replace(placeholder, str(value))
        
        return rendered


# ============================================================================
# RAG Templates
# ============================================================================

def get_rag_system_prompt() -> str:
    """
    Get standard RAG system prompt
    
    Returns:
        System prompt string
    """
    return """You are a helpful AI assistant that answers questions based on the provided context.

Your task:
1. Carefully read the provided context from the knowledge base
2. Answer the user's question based ONLY on the provided context
3. If the context doesn't contain enough information to answer the question, say so
4. Provide clear, concise answers
5. When relevant, reference the sources you used in your answer (e.g., "According to Source 1...")
6. Do not make up information or use outside knowledge beyond the provided context

Remember:
- Accuracy is more important than completeness
- It's okay to say "I don't have enough information to answer this question"
- Always ground your answers in the provided sources"""


def get_rag_user_prompt() -> str:
    """
    Get standard RAG user prompt
    
    Returns:
        User prompt template
    """
    return """Context from the knowledge base:
{context}

Question: {query}

Based on the provided context, answer the question. If the context doesn't contain enough information, say so."""


def get_rag_user_cot_prompt() -> str:
    """
    Get chain-of-thought RAG user prompt
    
    Returns:
        Chain-of-thought user prompt template
    """
    return """You are a helpful AI assistant that thinks step-by-step when answering questions based on context.

Context from the knowledge base:
{context}

Question: {query}

Think through this step-by-step:
1. Analyze what the question is asking
2. Search through the provided context for relevant information
3. Identify which sources contain relevant information
4. Synthesize the information from the sources
5. Formulate your answer based only on the context
6. If the context is insufficient, state that clearly

Provide your reasoning and then your final answer.

Reasoning:
<Your step-by-step reasoning here>

Answer:
<Your final answer here>"""


def get_rag_user_fewshot_prompt() -> str:
    """
    Get few-shot RAG user prompt
    
    Returns:
        Few-shot user prompt template
    """
    return """Context from the knowledge base:
{context}

Question: {query}

{examples}

Now answer the question following the same format as the examples above."""


def get_fewshot_rag_examples() -> List[Dict[str, str]]:
    """
    Get few-shot examples for RAG
    
    Returns:
        List of example dictionaries
    """
    return [
        {
            "question": "What is the deployment process?",
            "context": "[Source 1: Deployment Guide]\nTo deploy the AI platform to Azure:\n1. Set up Azure resources\n2. Configure infrastructure\n3. Deploy application\n4. Configure monitoring\n\n[Source 2: Infrastructure Setup]\nInfrastructure requires Azure Container Apps, Azure OpenAI Service, and Azure Cognitive Search.",
            "answer": "According to Source 1 (Deployment Guide) and Source 2 (Infrastructure Setup), the deployment process involves: (1) setting up Azure resources including Azure Container Apps, Azure OpenAI Service, and Azure Cognitive Search, (2) configuring the infrastructure, (3) deploying the application, and (4) configuring monitoring."
        },
        {
            "question": "How do I configure monitoring?",
            "context": "[Source 1: Monitoring Guide]\nMonitoring is configured through Azure Monitor and Application Insights. You need to set up metrics collection, log aggregation, and alerting.\n\n[Source 2: Configuration]\nConfigure monitoring by adding the Application Insights instrumentation key to your environment variables.",
            "answer": "Based on Source 1 (Monitoring Guide) and Source 2 (Configuration), monitoring is configured by: (1) setting up Azure Monitor and Application Insights, (2) configuring metrics collection, (3) setting up log aggregation, (4) creating alerting rules, and (5) adding the Application Insights instrumentation key to your environment variables."
        }
    ]


# ============================================================================
# Chat Templates
# ============================================================================

def get_chat_system_prompt() -> str:
    """
    Get standard chat system prompt
    
    Returns:
        System prompt string
    """
    return """You are a helpful AI assistant. Your goal is to provide clear, accurate, and helpful responses to user questions.

Guidelines:
- Be friendly and professional
- Provide accurate information
- If you're unsure about something, say so
- Keep responses concise and to the point
- Use clear and simple language"""


def get_chat_code_assistant_prompt() -> str:
    """
    Get code assistant system prompt
    
    Returns:
        Code assistant system prompt
    """
    return """You are an expert code assistant with deep knowledge of programming, software development, and best practices.

Your role:
- Help users write, debug, and understand code
- Explain complex concepts clearly
- Follow best practices and coding standards
- Suggest improvements and optimizations
- Provide working examples when relevant

Guidelines:
- Write clean, well-commented code
- Explain your reasoning
- Consider edge cases and error handling
- Suggest testing approaches
- Keep code maintainable and readable"""


def get_chat_analyst_prompt() -> str:
    """
    Get data analyst system prompt
    
    Returns:
        Data analyst system prompt
    """
    return """You are a data analyst with expertise in data analysis, statistics, and data visualization.

Your role:
- Help users analyze data
- Provide insights and recommendations
- Explain statistical concepts
- Suggest appropriate analysis methods
- Help interpret results

Guidelines:
- Be thorough in your analysis
- Explain your methodology
- Consider limitations and assumptions
- Provide actionable insights
- Use clear visualizations when relevant"""


# ============================================================================
# Specialized Templates
# ============================================================================

def get_summarization_prompt() -> str:
    """
    Get text summarization prompt
    
    Returns:
        Summarization prompt template
    """
    return """Summarize the following text concisely while preserving the key information:

Text:
{text}

Summary:"""


def get_extraction_prompt() -> str:
    """
    Get information extraction prompt
    
    Returns:
        Extraction prompt template
    """
    return """Extract the following information from the text:
{fields}

Text:
{text}

Extracted Information:"""


# ============================================================================
# Template Factory
# ============================================================================

class PromptTemplateFactory:
    """Factory for creating prompt templates"""
    
    _templates = {
        # RAG templates
        "rag_system": RAGPromptTemplate(
            name="rag_system",
            template=get_rag_system_prompt(),
            variables=[],
            version="v1"
        ),
        "rag_user": RAGPromptTemplate(
            name="rag_user",
            template=get_rag_user_prompt(),
            variables=["context", "query"],
            version="v1"
        ),
        "rag_user_cot": RAGPromptTemplate(
            name="rag_user_cot",
            template=get_rag_user_cot_prompt(),
            variables=["context", "query"],
            version="v1",
            chain_of_thought=True
        ),
        "rag_user_fewshot": RAGPromptTemplate(
            name="rag_user_fewshot",
            template=get_rag_user_fewshot_prompt(),
            variables=["context", "query"],
            version="v1",
            few_shot=True
        ),
        
        # Chat templates
        "chat_system": ChatPromptTemplate(
            name="chat_system",
            template=get_chat_system_prompt(),
            variables=[],
            version="v1"
        ),
        "chat_code_assistant": ChatPromptTemplate(
            name="chat_code_assistant",
            template=get_chat_code_assistant_prompt(),
            variables=[],
            version="v1"
        ),
        "chat_analyst": ChatPromptTemplate(
            name="chat_analyst",
            template=get_chat_analyst_prompt(),
            variables=[],
            version="v1"
        ),
        
        # Specialized templates
        "summarization": ChatPromptTemplate(
            name="summarization",
            template=get_summarization_prompt(),
            variables=["text"],
            version="v1"
        ),
        "extraction": ChatPromptTemplate(
            name="extraction",
            template=get_extraction_prompt(),
            variables=["fields", "text"],
            version="v1"
        )
    }
    
    @classmethod
    def get_template(cls, name: str) -> Optional[PromptTemplate]:
        """
        Get a prompt template by name
        
        Args:
            name: Template name
            
        Returns:
            PromptTemplate or None if not found
        """
        return cls._templates.get(name)
    
    @classmethod
    def list_templates(cls) -> List[str]:
        """
        List all available template names
        
        Returns:
            List of template names
        """
        return list(cls._templates.keys())
    
    @classmethod
    def register_template(cls, template: PromptTemplate):
        """
        Register a new template
        
        Args:
            template: PromptTemplate to register
        """
        cls._templates[template.name] = template
        logger.info(f"Registered template: {template.name} v{template.version}")


# Global factory instance
template_factory = PromptTemplateFactory()
"""LLM module for Azure AI Infrastructure Platform"""
from .azure_openai_client import AzureOpenAIClient
from .prompt_evaluator import evaluator
from .prompt_manager import PromptManager
from .prompt_versioning import version_manager
from .prompts import (
    ChatPromptTemplate,
    PromptTemplate,
    RAGPromptTemplate,
    get_chat_analyst_prompt,
    get_chat_code_assistant_prompt,
    get_chat_system_prompt,
    get_extraction_prompt,
    get_fewshot_rag_examples,
    get_rag_system_prompt,
    get_rag_user_cot_prompt,
    get_rag_user_fewshot_prompt,
    get_rag_user_prompt,
    get_summarization_prompt,
)
from .response_evaluator import ResponseEvaluator

__all__ = [
    "AzureOpenAIClient",
    "PromptManager",
    "ResponseEvaluator",
    "PromptTemplate",
    "RAGPromptTemplate",
    "ChatPromptTemplate",
    "get_rag_system_prompt",
    "get_rag_user_prompt",
    "get_rag_user_cot_prompt",
    "get_rag_user_fewshot_prompt",
    "get_chat_system_prompt",
    "get_chat_code_assistant_prompt",
    "get_chat_analyst_prompt",
    "get_summarization_prompt",
    "get_extraction_prompt",
    "get_fewshot_rag_examples",
    "version_manager",
    "evaluator",
]

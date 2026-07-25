"""Prompt templates module"""
from .templates import (
    PromptTemplate,
    RAGPromptTemplate,
    ChatPromptTemplate,
    get_rag_system_prompt,
    get_rag_user_prompt,
    get_rag_user_cot_prompt,
    get_rag_user_fewshot_prompt,
    get_chat_system_prompt,
    get_chat_code_assistant_prompt,
    get_chat_analyst_prompt,
    get_summarization_prompt,
    get_extraction_prompt,
    get_fewshot_rag_examples
)

__all__ = [
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
    "get_fewshot_rag_examples"
]
"""Cache key generation for multi-provider AI gateway."""

import hashlib
import json
from typing import Any, Dict, List


def generate_cache_key(
    provider: str,
    model: str,
    messages: List[Dict[str, Any]],
    temperature: float = 0.7,
    max_tokens: int = 1000,
    **kwargs: Any,
) -> str:
    """
    Generate a cache key from request parameters.

    Args:
        provider: Provider name
        model: Model name
        messages: Messages array (conversation)
        temperature: Temperature parameter
        max_tokens: Max tokens parameter
        **kwargs: Additional parameters

    Returns:
        Cache key string
    """
    # Normalize messages (sort keys to ensure consistent ordering)
    normalized_messages = [{k: msg[k] for k in sorted(msg.keys())} for msg in messages]

    # Normalize additional kwargs (sort keys)
    normalized_kwargs = {k: kwargs[k] for k in sorted(kwargs.keys())}

    # Create cache key components
    key_components = {
        "provider": provider,
        "model": model,
        "messages": normalized_messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        **normalized_kwargs,
    }

    # Serialize to JSON
    key_string = json.dumps(key_components, sort_keys=True)

    # Hash with SHA-256
    key_hash = hashlib.sha256(key_string.encode("utf-8")).hexdigest()

    return f"{provider}:{model}:{key_hash[:16]}"


def generate_cache_key_from_request(provider: str, model: str, request: Dict[str, Any]) -> str:
    """
    Generate a cache key from a request dictionary.

    Args:
        provider: Provider name
        model: Model name
        request: Request dictionary with messages and parameters

    Returns:
        Cache key string
    """
    messages = request.get("messages", [])
    temperature = request.get("temperature", 0.7)
    max_tokens = request.get("max_tokens", 1000)

    # Extract additional parameters (exclude messages, temperature, max_tokens)
    additional_params = {
        k: v for k, v in request.items() if k not in ["messages", "temperature", "max_tokens"]
    }

    return generate_cache_key(
        provider=provider,
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        **additional_params,
    )


def normalize_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize messages for cache key generation.

    Args:
        messages: Messages array

    Returns:
        Normalized messages
    """
    normalized = []

    for msg in messages:
        # Sort keys for consistent ordering
        normalized_msg = {k: msg[k] for k in sorted(msg.keys())}
        normalized.append(normalized_msg)

    return normalized


def hash_string(value: str) -> str:
    """
    Hash a string to create a short identifier.

    Args:
        value: String to hash

    Returns:
        Hashed string (16 chars)
    """
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]

"""
Chat routes for Azure AI Infrastructure Platform
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
import logging
import uuid

from src.api.schemas import ChatRequest, ChatResponse, ErrorCode, ErrorResponse
from src.llm.azure_openai_client import AzureOpenAIClient
from src.llm.prompt_manager import PromptManager
from src.config.settings import get_settings
from src.api.routes.monitoring import record_request_metrics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize components
prompt_manager = PromptManager()


@router.post("", response_model=ChatResponse)
async def chat_completion(request: ChatRequest) -> ChatResponse:
    """
    Chat completion endpoint using GPT-4

    Args:
        request: ChatRequest with message, conversation_id, max_tokens, temperature, stream

    Returns:
        ChatResponse with response, model, tokens, cost, latency

    Raises:
        HTTPException: If request fails
    """
    start_time = datetime.utcnow()
    settings = get_settings()
    
    try:
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Initialize OpenAI client
        client = AzureOpenAIClient()
        
        # Get system prompt
        system_prompt = prompt_manager.render_template("chat_system")
        if not system_prompt:
            system_prompt = "You are a helpful AI assistant."
        
        # Build messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.message}
        ]
        
        # Call Azure OpenAI
        result = await client.chat_completion(
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stream=request.stream
        )
        
        if request.stream:
            # Streaming responses not implemented in this endpoint
            # Use /chat/stream endpoint for streaming
            raise HTTPException(
                status_code=400,
                detail="Streaming not supported on this endpoint. Use /chat/stream"
            )
        
        # Record metrics
        record_request_metrics(
            tokens=result["tokens_used"],
            cost=result["cost"],
            latency_ms=result["latency_ms"],
            error=False
        )
        
        return ChatResponse(
            response=result["response"],
            model=result["model"],
            conversation_id=conversation_id,
            tokens_used=result["tokens_used"],
            prompt_tokens=result["prompt_tokens"],
            completion_tokens=result["completion_tokens"],
            cost=result["cost"],
            latency_ms=result["latency_ms"],
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Chat completion failed: {e}")
        
        # Record error metrics
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        record_request_metrics(
            tokens=0,
            cost=0.0,
            latency_ms=latency_ms,
            error=True
        )
        
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error_code=ErrorCode.AZURE_ERROR,
                message=f"Chat completion failed: {str(e)}",
                details={"conversation_id": conversation_id},
                timestamp=datetime.utcnow()
            )
        )


@router.post("/stream")
async def chat_completion_stream(request: ChatRequest):
    """
    Streaming chat completion endpoint using GPT-4

    Args:
        request: ChatRequest with message, conversation_id, max_tokens, temperature, stream

    Returns:
        Streaming response chunks
    """
    try:
        # Initialize OpenAI client
        client = AzureOpenAIClient()
        
        # Get system prompt
        system_prompt = prompt_manager.render_template("chat_system")
        if not system_prompt:
            system_prompt = "You are a helpful AI assistant."
        
        # Build messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.message}
        ]
        
        # Return streaming response
        async def generate():
            tokens_generated = 0
            async for chunk in client.chat_completion_stream(
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            ):
                tokens_generated += 1
                yield f"data: {chunk}\n\n"
            
            yield f"data: [DONE]\n\n"
        
        return generate()
        
    except Exception as e:
        logger.error(f"Streaming chat completion failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Streaming chat completion failed: {str(e)}"
        )
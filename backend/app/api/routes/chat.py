"""
Chat endpoint.

POST /api/chat

Accepts a plain-text message and returns Gemini's response.
Each request is fully independent — no conversation history is maintained.

The CNN model is never involved in text-only chat.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.gemini_service import GeminiAPIError, GeminiConfigError, gemini_service

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# System context injected before every user message.
# Keeps Gemini focused on the application's purpose without rigid keyword
# matching — Gemini is still free to interpret vague or conversational input.
# ---------------------------------------------------------------------------
_SYSTEM_CONTEXT = (
    "You are a helpful assistant for a brain tumor MRI classification application. "
    "You answer questions about brain tumors, MRI scans, medical imaging concepts, "
    "and how this application works. "
    "You do not provide personal medical diagnoses, treatment recommendations, "
    "or clinical advice. "
    "Respond clearly and helpfully to whatever the user asks."
)


@router.post(
    "/api/chat",
    response_model=ChatResponse,
    summary="Chat with Gemini",
    description=(
        "Send a text message and receive a Gemini-generated response. "
        "Intended for general questions about brain tumors, MRI imaging, "
        "and how the application works. "
        "Each request is stateless — no conversation history is stored."
    ),
    tags=["Chat"],
)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Forward the user's message to Gemini and return the response.

    The system context is prepended to every request so that Gemini stays
    relevant to the application without restricting it to rigid keyword lists.
    """
    prompt = f"{_SYSTEM_CONTEXT}\n\nUser: {request.message}"

    logger.info("Chat request received (message length=%d).", len(request.message))

    try:
        response_text = gemini_service.send_text(prompt)
    except GeminiConfigError as exc:
        logger.error("Gemini configuration error: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=(
                "The AI service is not configured. "
                "Please contact the administrator."
            ),
        ) from exc
    except GeminiAPIError as exc:
        logger.error("Gemini API error during chat: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="The AI service is temporarily unavailable. Please try again later.",
        ) from exc

    if not response_text.strip():
        logger.warning("Gemini returned an empty response for chat request.")
        raise HTTPException(
            status_code=502,
            detail="The AI service returned an empty response. Please try again.",
        )

    logger.info("Chat response generated (length=%d).", len(response_text))
    return ChatResponse(response=response_text)

"""
Pydantic schemas for the /api/chat endpoint.
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="The user's message or question.",
        examples=["What is a glioma?"],
    )


class ChatResponse(BaseModel):
    response: str = Field(
        ...,
        description="Gemini's response to the user's message.",
    )

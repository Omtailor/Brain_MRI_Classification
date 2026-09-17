"""
Health check endpoint.

GET /health

Returns the current status of the API and the loaded CNN model.
No inference is performed during this check.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.cnn_service import cnn_service

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    device: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description=(
        "Returns the current operational status of the API and whether the "
        "CNN model has been loaded successfully. No inference is performed."
    ),
    tags=["Health"],
)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok" if cnn_service.is_loaded else "model_not_loaded",
        model_loaded=cnn_service.is_loaded,
        device=cnn_service.device_name,
    )

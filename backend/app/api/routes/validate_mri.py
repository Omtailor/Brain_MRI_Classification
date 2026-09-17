"""
MRI validation endpoint.

POST /api/validate-mri

Accepts a multipart file upload (JPEG, PNG, or PDF) and uses Gemini to
determine whether it contains a brain MRI suitable for CNN classification.

No CNN inference is performed here. That is Part 3.

Pipeline (Part 2):
    Upload → file validation → Gemini MRI suitability check → response
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.schemas.validation import MRIValidationResponse
from app.services.gemini_service import GeminiAPIError, GeminiConfigError
from app.services.mri_validator import mri_validator
from app.utils.file_handler import validate_upload

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/api/validate-mri",
    response_model=MRIValidationResponse,
    summary="Validate MRI suitability",
    description=(
        "Upload a JPEG, PNG, or PDF file. "
        "Gemini inspects the content and determines whether it contains a brain MRI "
        "that is suitable for automated classification. "
        "No tumor classification is performed at this stage. "
        "Uploaded files are processed in memory and never stored permanently."
    ),
    tags=["Validation"],
)
async def validate_mri(
    file: UploadFile = File(..., description="Brain MRI image (JPEG/PNG) or PDF."),
) -> MRIValidationResponse:
    """
    Validate whether the uploaded file is a suitable brain MRI.

    Steps
    -----
    1. File validation — extension, size, MIME type, decodability.
    2. Gemini MRI suitability check (image or PDF path).
    3. Structured response indicating valid/invalid with reason.
    """

    # ------------------------------------------------------------------
    # Step 1: File validation
    # ------------------------------------------------------------------
    validated = await validate_upload(file)

    # ------------------------------------------------------------------
    # Step 2: Gemini MRI validation
    # ------------------------------------------------------------------
    logger.info(
        "MRI validation request: file='%s', mime='%s', size=%d bytes.",
        validated.filename,
        validated.mime_type,
        len(validated.content),
    )

    try:
        if validated.is_pdf:
            result = mri_validator.validate_pdf(validated.content)
        else:
            result = mri_validator.validate_image(validated.content, validated.mime_type)

    except GeminiConfigError as exc:
        logger.error("Gemini configuration error during MRI validation: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=(
                "The AI validation service is not configured. "
                "Please contact the administrator."
            ),
        ) from exc
    except GeminiAPIError as exc:
        logger.error("Gemini API error during MRI validation: %s", exc)
        raise HTTPException(
            status_code=502,
            detail=(
                "The AI validation service is temporarily unavailable. "
                "Please try again later."
            ),
        ) from exc

    # ------------------------------------------------------------------
    # Step 3: Build response
    # ------------------------------------------------------------------
    is_valid = result.is_brain_mri and result.is_suitable_for_classification

    if is_valid:
        message = "Valid brain MRI detected."
    elif result.is_brain_mri and not result.is_suitable_for_classification:
        message = "A brain MRI was detected but it is not suitable for classification."
    else:
        message = "The uploaded file is not a suitable brain MRI."

    logger.info(
        "MRI validation result: valid=%s, reason='%.100s'",
        is_valid,
        result.reason,
    )

    return MRIValidationResponse(
        valid=is_valid,
        message=message,
        reason=result.reason,
    )

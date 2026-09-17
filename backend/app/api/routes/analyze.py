"""
MRI analysis endpoint — the main production pipeline.

POST /api/analyze

Full pipeline
-------------
1. Validate upload  (extension, size, MIME, Pillow decode)
2. Gemini MRI suitability validation
   → not suitable: return rejection response immediately, no CNN called
3. Prepare a PIL image for the CNN
   • image upload: open directly from bytes
   • PDF upload:   extract first usable image via pdf_extractor
4. CNN inference  (SmallCNN, existing cnn_service)
5. Gemini explanation of the CNN result
6. Return structured AnalysisResponse

Privacy guarantees
------------------
- No files written to disk at any point.
- No images or PDFs retained after the response is sent.
- No conversation history stored.
- No authentication or user identity required.
"""

from __future__ import annotations

import io
import logging

from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image

from app.schemas.analysis import AnalysisResponse, PredictionResult
from app.services.cnn_service import cnn_service
from app.services.gemini_service import GeminiAPIError, GeminiConfigError, gemini_service
from app.services.mri_validator import mri_validator
from app.services.pdf_extractor import PDFExtractionError, extract_first_image
from app.utils.file_handler import validate_upload

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/api/analyze",
    response_model=AnalysisResponse,
    summary="Analyze a brain MRI scan",
    description=(
        "Upload a brain MRI image (JPEG/PNG) or a PDF containing an MRI scan. "
        "The backend validates the file, uses Gemini to confirm it is a suitable "
        "brain MRI, runs the SmallCNN classifier to produce a four-class prediction, "
        "then asks Gemini to generate a plain-language explanation of the result. "
        "Uploaded files are processed entirely in memory and never stored permanently. "
        "The CNN result is never overridden by Gemini."
    ),
    tags=["Analysis"],
    responses={
        200: {"description": "Analysis complete (may be success=True or success=False)."},
        400: {"description": "Empty or unreadable file."},
        413: {"description": "File exceeds the 20 MB size limit."},
        415: {"description": "Unsupported file type."},
        422: {"description": "Corrupted or undecodable image."},
        500: {"description": "CNN inference failed or internal server error."},
        502: {"description": "Gemini API error."},
        503: {"description": "CNN model not loaded or Gemini not configured."},
    },
)
async def analyze(
    file: UploadFile = File(..., description="Brain MRI image (JPEG/PNG) or PDF."),
) -> AnalysisResponse:
    """
    End-to-end MRI analysis pipeline.

    Returns AnalysisResponse with success=True on a completed analysis,
    or success=False if the MRI validation step rejects the upload.
    All other failure modes raise an HTTPException.
    """

    # ------------------------------------------------------------------
    # Step 1 — Validate upload
    # ------------------------------------------------------------------
    validated = await validate_upload(file)
    logger.info(
        "Analyze request: file='%s', mime='%s', size=%d bytes.",
        validated.filename,
        validated.mime_type,
        len(validated.content),
    )

    # ------------------------------------------------------------------
    # Step 2 — Gemini MRI suitability validation
    # ------------------------------------------------------------------
    try:
        if validated.is_pdf:
            mri_result = mri_validator.validate_pdf(validated.content)
        else:
            mri_result = mri_validator.validate_image(
                validated.content, validated.mime_type
            )
    except GeminiConfigError as exc:
        logger.error("Gemini config error during MRI validation: %s", exc)
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

    # Reject immediately if not a suitable brain MRI — CNN must not run
    if not (mri_result.is_brain_mri and mri_result.is_suitable_for_classification):
        logger.info(
            "MRI validation rejected: reason='%.120s'", mri_result.reason
        )
        if mri_result.is_brain_mri and not mri_result.is_suitable_for_classification:
            msg = "A brain MRI was detected but it is not suitable for classification."
        else:
            msg = "The uploaded file is not a suitable brain MRI."

        return AnalysisResponse(
            success=False,
            valid_mri=False,
            message=f"{msg} {mri_result.reason}".strip(),
        )

    logger.info("MRI validation passed: reason='%.120s'", mri_result.reason)

    # ------------------------------------------------------------------
    # Step 3 — Prepare PIL image for the CNN
    # ------------------------------------------------------------------
    pil_image: Image.Image

    if validated.is_pdf:
        # Extract the first usable image from the PDF in memory
        try:
            pil_image = extract_first_image(validated.content)
        except PDFExtractionError as exc:
            logger.warning("PDF extraction failed: %s", exc)
            raise HTTPException(
                status_code=422,
                detail=(
                    "A brain MRI was detected in the PDF but no image could be "
                    "extracted for classification. "
                    "Please try uploading the MRI as a JPEG or PNG image."
                ),
            ) from exc
        except Exception as exc:
            logger.error("Unexpected error during PDF extraction: %s", exc)
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while processing the PDF.",
            ) from exc
    else:
        # Image upload — open directly from in-memory bytes
        try:
            pil_image = Image.open(io.BytesIO(validated.content))
            pil_image.load()  # Force full decode before CNN
        except Exception as exc:
            logger.warning("Failed to open image for CNN: %s", exc)
            raise HTTPException(
                status_code=422,
                detail="The image could not be decoded for classification.",
            ) from exc

    # ------------------------------------------------------------------
    # Step 4 — CNN inference
    # ------------------------------------------------------------------
    if not cnn_service.is_loaded:
        raise HTTPException(
            status_code=503,
            detail=(
                "The classification model is not available. "
                "Please check that cnn_baseline_best.pth is present and "
                "restart the server."
            ),
        )

    try:
        # cnn_service.predict() handles RGB conversion and preprocessing
        cnn_result = cnn_service.predict_with_grad_cam(pil_image)
    except ValueError as exc:
        logger.warning("CNN preprocessing error: %s", exc)
        raise HTTPException(
            status_code=422,
            detail=f"The image could not be preprocessed for classification: {exc}",
        ) from exc
    except RuntimeError as exc:
        logger.error("CNN inference failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Classification failed due to an internal model error.",
        ) from exc
    except Exception as exc:
        logger.error("Unexpected CNN error: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during classification.",
        ) from exc
    finally:
        # Release the PIL image immediately — no persistent reference needed
        pil_image.close()

    class_name: str = cnn_result["class_name"]
    confidence: float = cnn_result["confidence"]
    probabilities: dict[str, float] = cnn_result["probabilities"]

    logger.info(
        "CNN result: class='%s', confidence=%.4f.", class_name, confidence
    )

    # ------------------------------------------------------------------
    # Step 5 — Gemini explanation
    # ------------------------------------------------------------------
    explanation: str
    try:
        explanation = gemini_service.send_explanation(
            class_name=class_name,
            confidence=confidence,
            probabilities=probabilities,
        )
        if not explanation.strip():
            raise GeminiAPIError("Empty explanation returned.")
    except GeminiConfigError as exc:
        logger.error("Gemini config error during explanation: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=(
                "The AI explanation service is not configured. "
                "Please contact the administrator."
            ),
        ) from exc
    except GeminiAPIError as exc:
        logger.warning(
            "Gemini explanation failed, using fallback: %s", exc
        )
        # Non-fatal: return the CNN result with a safe fallback explanation
        # rather than failing the whole request.
        confidence_pct = round(confidence * 100, 1)
        explanation = (
            f"The CNN model classified this MRI scan as {class_name} "
            f"with a confidence of {confidence_pct}%. "
            "This is a model prediction and should not be interpreted as a "
            "medical diagnosis. Please consult a qualified medical professional "
            "for further evaluation."
        )

    # ------------------------------------------------------------------
    # Step 6 — Build and return response
    # ------------------------------------------------------------------
    return AnalysisResponse(
        success=True,
        valid_mri=True,
        prediction=PredictionResult(
            class_id=cnn_result["class_id"],
            class_name=class_name,
            confidence=confidence,
        ),
        probabilities=probabilities,
        explanation=explanation,
        grad_cam_image=cnn_result["grad_cam_image"],
    )

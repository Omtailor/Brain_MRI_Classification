"""
Pydantic schemas for the POST /api/analyze endpoint.

Two response shapes are possible:

1. Success — MRI is valid, CNN ran, Gemini explained:
   {
     "success": true,
     "valid_mri": true,
     "prediction": { "class_id": 1, "class_name": "Glioma", "confidence": 0.94 },
     "probabilities": { "No Tumor": 0.01, "Glioma": 0.94, ... },
     "explanation": "..."
   }

2. Rejection — upload invalid or MRI not suitable:
   {
     "success": false,
     "valid_mri": false,
     "message": "The uploaded file is not a suitable brain MRI."
   }

Both shapes are unified in AnalysisResponse with Optional fields so that
the React frontend always receives the same top-level structure and can
branch on the `success` flag.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class PredictionResult(BaseModel):
    """CNN classification result for a single image."""

    class_id: int = Field(
        ...,
        ge=0,
        le=3,
        description="Predicted class index (0=No Tumor, 1=Glioma, 2=Meningioma, 3=Pituitary Tumor).",
    )
    class_name: str = Field(
        ...,
        description="Human-readable predicted class label.",
        examples=["Glioma"],
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Softmax probability for the predicted class. "
            "This is a model confidence score, not a medical certainty or diagnosis probability."
        ),
    )


class AnalysisResponse(BaseModel):
    """
    Unified response body for POST /api/analyze.

    Always present
    --------------
    success   : bool — True when the full pipeline completed successfully.
    valid_mri : bool — True when Gemini confirmed a suitable brain MRI was present.

    Present on success (success=True)
    ----------------------------------
    prediction    : PredictionResult
    probabilities : dict[str, float] — all four class probabilities
    explanation   : str — Gemini plain-language explanation of the CNN result

    Present on failure (success=False)
    ------------------------------------
    message : str — human-readable reason for rejection
    """

    success: bool = Field(..., description="True when the full analysis pipeline completed.")
    valid_mri: bool = Field(..., description="True when a suitable brain MRI was detected.")

    # --- Success fields ---
    prediction: Optional[PredictionResult] = Field(
        default=None,
        description="CNN classification result. Present only when success=True.",
    )
    probabilities: Optional[dict[str, float]] = Field(
        default=None,
        description=(
            "Softmax probability for each of the four classes. "
            "Present only when success=True."
        ),
    )
    explanation: Optional[str] = Field(
        default=None,
        description=(
            "Gemini-generated plain-language explanation of the CNN result. "
            "Present only when success=True."
        ),
    )
    grad_cam_image: Optional[str] = Field(
        default=None,
        description=(
            "Base64 PNG Grad-CAM overlay. Present only after a suitable brain MRI "
            "has been validated and classified."
        ),
    )

    # --- Failure field ---
    message: Optional[str] = Field(
        default=None,
        description="Reason for rejection. Present only when success=False.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "valid_mri": True,
                    "prediction": {
                        "class_id": 1,
                        "class_name": "Glioma",
                        "confidence": 0.94,
                    },
                    "probabilities": {
                        "No Tumor": 0.01,
                        "Glioma": 0.94,
                        "Meningioma": 0.03,
                        "Pituitary Tumor": 0.02,
                    },
                    "explanation": (
                        "The CNN model classified this MRI scan as Glioma with a "
                        "confidence of 94.0%. Gliomas are tumors that arise from the "
                        "glial cells of the brain. This result is a model prediction "
                        "and should not be interpreted as a medical diagnosis. Please "
                        "consult a qualified medical professional for further evaluation."
                    ),
                },
                {
                    "success": False,
                    "valid_mri": False,
                    "message": "The uploaded file is not a suitable brain MRI.",
                },
            ]
        }
    }

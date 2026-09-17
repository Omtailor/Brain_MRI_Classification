"""
Pydantic schemas for the /api/validate-mri endpoint.
"""

from pydantic import BaseModel, Field


class MRIValidationResult(BaseModel):
    """
    Structured result returned by Gemini's MRI suitability check.
    Parsed internally by mri_validator.py before being wrapped in MRIValidationResponse.
    """

    is_brain_mri: bool = Field(
        ...,
        description="Whether the content appears to be a brain MRI.",
    )
    is_suitable_for_classification: bool = Field(
        ...,
        description=(
            "Whether the brain MRI is suitable for passing to the CNN classifier."
        ),
    )
    reason: str = Field(
        ...,
        description="Short explanation of the validation decision.",
    )


class MRIValidationResponse(BaseModel):
    """
    HTTP response body for POST /api/validate-mri.
    """

    valid: bool = Field(
        ...,
        description=(
            "True only when both is_brain_mri and is_suitable_for_classification "
            "are True."
        ),
    )
    message: str = Field(
        ...,
        description="Human-readable summary suitable for display in the frontend.",
    )
    reason: str = Field(
        ...,
        description="Gemini's explanation of why the file was accepted or rejected.",
    )

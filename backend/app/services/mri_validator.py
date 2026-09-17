"""
MRI suitability validation service.

Uses Gemini to determine whether an uploaded image or PDF contains a brain MRI
that is suitable for passing to the CNN classifier.

Gemini's role here is STRICTLY limited to:
  • detecting whether brain MRI content is present
  • assessing whether the image quality / content is suitable for classification

Gemini must NOT perform the four-class tumor classification.
The CNN remains the authoritative classifier (Part 3).
"""

from __future__ import annotations

import json
import logging
import re

from app.schemas.validation import MRIValidationResult
from app.services.gemini_service import GeminiAPIError, GeminiConfigError, gemini_service

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal validation prompt
# ---------------------------------------------------------------------------

_VALIDATION_PROMPT = """You are a medical imaging quality-control assistant.

Your ONLY task is to determine whether the supplied content contains a brain MRI
image that is suitable for automated classification by a CNN model.

Evaluate the content and respond with a JSON object — nothing else, no markdown,
no explanation outside the JSON.

Use exactly this structure:
{
  "is_brain_mri": <true|false>,
  "is_suitable_for_classification": <true|false>,
  "reason": "<one or two sentences>"
}

Guidelines for your evaluation:
- is_brain_mri: true only if the content clearly shows a brain MRI scan
  (T1, T2, FLAIR, or similar MRI modality). CT scans, X-rays, ultrasounds,
  photographs, or non-medical images must return false.
- is_suitable_for_classification: true only when is_brain_mri is true AND
  the brain region is clearly visible, adequately framed, and not heavily
  artefact-corrupted. A blurry, cropped, or low-contrast image that would
  likely confuse a classifier should return false.
- reason: a brief, neutral, factual explanation of your decision.

You MUST NOT:
- predict tumor class or type
- provide a diagnosis
- estimate cancer probability
- assess treatment or prognosis
- make any clinical judgment beyond image suitability

Respond only with the JSON object described above."""


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

class MRIValidator:
    """
    Wraps the Gemini service to perform MRI suitability checks.

    Accepts raw bytes for both images and PDFs.
    Returns a structured MRIValidationResult.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate_image(self, image_bytes: bytes, mime_type: str) -> MRIValidationResult:
        """
        Validate whether image bytes contain a suitable brain MRI.

        Parameters
        ----------
        image_bytes : bytes
            Raw image content (JPEG or PNG).
        mime_type : str
            MIME type, e.g. 'image/jpeg' or 'image/png'.

        Returns
        -------
        MRIValidationResult
        """
        logger.info("Validating image (mime=%s, size=%d bytes).", mime_type, len(image_bytes))
        raw_response = gemini_service.send_image(
            image_bytes=image_bytes,
            mime_type=mime_type,
            prompt=_VALIDATION_PROMPT,
        )
        return self._parse_response(raw_response)

    def validate_pdf(self, pdf_bytes: bytes) -> MRIValidationResult:
        """
        Validate whether a PDF contains a suitable brain MRI image.

        Parameters
        ----------
        pdf_bytes : bytes
            Raw PDF file bytes.

        Returns
        -------
        MRIValidationResult
        """
        logger.info("Validating PDF (size=%d bytes).", len(pdf_bytes))
        raw_response = gemini_service.send_pdf(
            pdf_bytes=pdf_bytes,
            prompt=_VALIDATION_PROMPT,
        )
        return self._parse_response(raw_response)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_response(self, raw: str) -> MRIValidationResult:
        """
        Parse Gemini's JSON response into a MRIValidationResult.

        Falls back to a safe rejection result if the response cannot be parsed,
        rather than propagating a crash to the HTTP layer.
        """
        text = raw.strip()

        # Strip markdown code fences if Gemini wrapped its JSON
        # e.g.  ```json\n{...}\n```
        fenced = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
        if fenced:
            text = fenced.group(1).strip()

        try:
            data: dict = json.loads(text)
            return MRIValidationResult(
                is_brain_mri=bool(data.get("is_brain_mri", False)),
                is_suitable_for_classification=bool(
                    data.get("is_suitable_for_classification", False)
                ),
                reason=str(data.get("reason", "No reason provided.")),
            )
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            logger.warning(
                "Failed to parse Gemini validation response: %s. Raw: %.200s",
                exc,
                raw,
            )
            return MRIValidationResult(
                is_brain_mri=False,
                is_suitable_for_classification=False,
                reason=(
                    "The validation service returned an unreadable response. "
                    "Please try again or upload a different file."
                ),
            )


# Module-level singleton
mri_validator = MRIValidator()

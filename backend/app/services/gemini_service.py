"""
Gemini API service.

Responsibilities
----------------
- Initialize and hold a single Gemini client.
- Provide focused helpers for:
    • text-only prompts  (send_text)
    • image + text prompts  (send_image)
    • PDF bytes + text prompts  (send_pdf)
- Translate SDK/network errors into clean application exceptions so callers
  never need to import google.genai directly.

The client is initialised lazily on first use so that missing or empty
GEMINI_API_KEY values produce a clear error at request time, not at import
time (which would crash every startup).
"""

from __future__ import annotations

import logging
from typing import Any

from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class GeminiConfigError(Exception):
    """Raised when GEMINI_API_KEY is missing or empty."""


class GeminiAPIError(Exception):
    """Raised when the Gemini SDK returns an error or times out."""


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class GeminiService:
    """
    Thin wrapper around the google-genai SDK client.

    One instance is created at module level and shared across all requests.
    The underlying HTTP client is thread-safe.
    """

    def __init__(self) -> None:
        self._client: genai.Client | None = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_client(self) -> genai.Client:
        """Return the cached client, initialising it on first call."""
        if self._client is not None:
            return self._client

        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise GeminiConfigError(
                "GEMINI_API_KEY is not set. "
                "Add it to your .env file or environment variables."
            )

        self._client = genai.Client(api_key=api_key)
        logger.info("Gemini client initialised (model: %s).", settings.GEMINI_MODEL)
        return self._client

    def _call(self, contents: Any) -> str:
        """
        Execute a generate_content call and return the response text.

        Parameters
        ----------
        contents:
            Any value accepted by client.models.generate_content — a string,
            a list of Parts, or a list of Content objects.

        Raises
        ------
        GeminiConfigError
            GEMINI_API_KEY missing.
        GeminiAPIError
            SDK raised an exception (network, quota, safety block, etc.).
        """
        client = self._get_client()
        try:
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=contents,
            )
            return response.text or ""
        except GeminiConfigError:
            raise
        except Exception as exc:
            logger.error("Gemini API error: %s", exc)
            raise GeminiAPIError(
                "The Gemini API returned an error. Please try again later."
            ) from exc

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def send_text(self, prompt: str) -> str:
        """
        Send a plain text prompt and return the response text.

        Parameters
        ----------
        prompt : str
            The full prompt string to send.

        Returns
        -------
        str
            Gemini's response text.
        """
        logger.debug("Gemini text request (length=%d).", len(prompt))
        return self._call(prompt)

    def send_image(self, image_bytes: bytes, mime_type: str, prompt: str) -> str:
        """
        Send an image together with a text prompt.

        Parameters
        ----------
        image_bytes : bytes
            Raw image bytes (JPEG or PNG).
        mime_type : str
            MIME type of the image, e.g. 'image/jpeg'.
        prompt : str
            Text instruction to accompany the image.

        Returns
        -------
        str
            Gemini's response text.
        """
        logger.debug("Gemini image request (mime=%s, size=%d bytes).", mime_type, len(image_bytes))
        contents = [
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            types.Part.from_text(text=prompt),
        ]
        return self._call(contents)

    def send_pdf(self, pdf_bytes: bytes, prompt: str) -> str:
        """
        Send a PDF together with a text prompt.

        The PDF is passed as inline bytes with MIME type 'application/pdf',
        which the Gemini multimodal API can process directly.

        Parameters
        ----------
        pdf_bytes : bytes
            Raw PDF file bytes.
        prompt : str
            Text instruction to accompany the PDF.

        Returns
        -------
        str
            Gemini's response text.
        """
        logger.debug("Gemini PDF request (size=%d bytes).", len(pdf_bytes))
        contents = [
            types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
            types.Part.from_text(text=prompt),
        ]
        return self._call(contents)

    def send_explanation(
        self,
        class_name: str,
        confidence: float,
        probabilities: dict[str, float],
    ) -> str:
        """
        Ask Gemini to generate a plain-language explanation of a CNN result.

        Gemini receives only the structured prediction — it must NOT override
        the CNN's classification.

        Parameters
        ----------
        class_name : str
            The CNN's predicted class label (e.g. "Glioma").
        confidence : float
            Softmax confidence for the predicted class (0.0–1.0).
        probabilities : dict[str, float]
            Full per-class probability dict from the CNN.

        Returns
        -------
        str
            A user-friendly explanation paragraph.
        """
        confidence_pct = round(confidence * 100, 1)

        # Format the probability breakdown for the prompt
        prob_lines = "\n".join(
            f"  - {name}: {round(prob * 100, 1)}%"
            for name, prob in probabilities.items()
        )

        prompt = f"""You are a helpful assistant for a brain tumor MRI classification application.

A CNN model has analysed an MRI scan and produced the following result:

Predicted class : {class_name}
Confidence      : {confidence_pct}%

Full class probabilities:
{prob_lines}

Your task:
- Explain this result clearly and accessibly to a general (non-medical) user.
- State the predicted class and the confidence value accurately.
- Do NOT change or reinterpret the predicted class.
- Do NOT claim this is a medical diagnosis or confirmed finding.
- Do NOT describe the confidence percentage as a cancer probability, \
a measure of medical certainty, or a tumor likelihood.
- Do NOT invent clinical details, symptoms, or treatment recommendations.
- Do NOT suggest the user take or avoid any medical action.
- You MAY briefly describe what the predicted class generally refers to \
(e.g., what glioma is in general terms).
- Keep the explanation concise (3–5 sentences) and compassionate in tone.
- End with a note that this result is a model prediction and should be \
reviewed by a qualified medical professional."""

        logger.debug(
            "Gemini explanation request (class=%s, confidence=%.1f%%).",
            class_name,
            confidence_pct,
        )
        return self._call(prompt)


# Module-level singleton — imported by validators and routes
gemini_service = GeminiService()

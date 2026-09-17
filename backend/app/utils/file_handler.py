"""
Upload file validation utilities.

Responsibilities
----------------
- Enforce maximum upload size (default 20 MB from settings).
- Validate file extension against the allowed set.
- Detect MIME type from the actual file content (not just the filename).
- Ensure image files can be decoded by Pillow.
- Return raw bytes and resolved MIME type for downstream processing.
- Never write files to disk permanently.

All validation errors raise fastapi.HTTPException with an appropriate
status code and a client-safe message.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from app.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result dataclass — carries everything callers need
# ---------------------------------------------------------------------------

@dataclass
class ValidatedFile:
    """
    Holds the validated upload contents and resolved metadata.

    Attributes
    ----------
    content : bytes
        Raw file bytes (entire file read into memory).
    mime_type : str
        Resolved MIME type (from content, not filename).
    extension : str
        Lower-case file extension including the dot, e.g. '.jpg'.
    filename : str
        Original filename as supplied by the client.
    is_pdf : bool
        True when the file is a PDF.
    is_image : bool
        True when the file is an image (JPEG or PNG).
    """

    content: bytes
    mime_type: str
    extension: str
    filename: str
    is_pdf: bool
    is_image: bool


# ---------------------------------------------------------------------------
# MIME helpers
# ---------------------------------------------------------------------------

# Mapping from Pillow format names to MIME types
_PILLOW_FORMAT_TO_MIME: dict[str, str] = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
}

_PDF_MAGIC = b"%PDF"


def _detect_mime(data: bytes) -> str:
    """
    Detect MIME type from file content.

    Returns the resolved MIME type string or raises HTTPException(415)
    if the content does not match a supported type.
    """
    # PDF: check magic bytes
    if data[:4] == _PDF_MAGIC:
        return "application/pdf"

    # Image: identify the actual file format with Pillow, not the filename.
    try:
        with Image.open(io.BytesIO(data)) as image:
            mime_type = _PILLOW_FORMAT_TO_MIME.get(image.format or "")
    except (UnidentifiedImageError, OSError):
        mime_type = None

    if mime_type is not None:
        return mime_type

    raise HTTPException(
        status_code=415,
        detail=(
            "Unsupported file type. "
            "Please upload a JPEG image, PNG image, or PDF document."
        ),
    )


# ---------------------------------------------------------------------------
# Main validation entry point
# ---------------------------------------------------------------------------

async def validate_upload(file: UploadFile) -> ValidatedFile:
    """
    Read and validate a multipart file upload.

    Checks performed (in order):
    1. Filename present.
    2. Extension allowed.
    3. Content read successfully.
    4. File not empty.
    5. Size within MAX_UPLOAD_SIZE_BYTES.
    6. MIME type detected from content.
    7. For images: Pillow can decode the file.

    Parameters
    ----------
    file : UploadFile
        The FastAPI upload file object from a multipart request.

    Returns
    -------
    ValidatedFile
        Populated dataclass ready for downstream processing.

    Raises
    ------
    HTTPException(400) : empty file, unreadable content.
    HTTPException(413) : file exceeds size limit.
    HTTPException(415) : unsupported extension or unrecognised content.
    HTTPException(422) : image content is corrupt or undecodable.
    """
    # 1. Filename
    filename: str = file.filename or "upload"
    extension: str = Path(filename).suffix.lower()
    if not extension:
        extension = ""

    # 2. Extension check
    if extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=(
                f"File extension '{extension}' is not supported. "
                f"Allowed: {', '.join(sorted(settings.ALLOWED_EXTENSIONS))}."
            ),
        )

    # 3. Read content
    try:
        content: bytes = await file.read()
    except Exception as exc:
        logger.warning("Failed to read upload '%s': %s", filename, exc)
        raise HTTPException(
            status_code=400,
            detail="Could not read the uploaded file. Please try again.",
        ) from exc
    finally:
        # Always close the upload stream
        await file.close()

    # 4. Empty file
    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    # 5. Size limit
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        max_mb = settings.MAX_UPLOAD_SIZE_MB
        raise HTTPException(
            status_code=413,
            detail=(
                f"File is too large. "
                f"Maximum allowed size is {max_mb} MB."
            ),
        )

    # 6. MIME detection from content
    mime_type = _detect_mime(content)

    is_pdf = mime_type == "application/pdf"
    is_image = mime_type in {"image/jpeg", "image/png"}

    # 7. For images: verify Pillow can decode them
    if is_image:
        try:
            img = Image.open(io.BytesIO(content))
            img.verify()  # Raises on corrupt files
        except UnidentifiedImageError:
            raise HTTPException(
                status_code=422,
                detail="The uploaded file could not be identified as a valid image.",
            )
        except Exception as exc:
            logger.warning("Image verification failed for '%s': %s", filename, exc)
            raise HTTPException(
                status_code=422,
                detail="The uploaded image appears to be corrupted or unreadable.",
            )

    logger.info(
        "Upload validated: file='%s', mime='%s', size=%d bytes.",
        filename,
        mime_type,
        len(content),
    )

    return ValidatedFile(
        content=content,
        mime_type=mime_type,
        extension=extension,
        filename=filename,
        is_pdf=is_pdf,
        is_image=is_image,
    )

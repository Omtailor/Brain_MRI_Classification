"""
PDF image extraction service.

Extracts raster images from a PDF so the CNN classifier can process them.

Strategy (deterministic)
------------------------
1. Open the PDF from bytes using pypdf.
2. Walk pages in order (page 0, 1, 2, …).
3. For each page, walk the page's XObject resources in iteration order.
4. Return the FIRST image whose raw data Pillow can decode as a valid
   RGB-convertible image.
5. If no page yields a usable image, raise PDFExtractionError.

This "first usable image" strategy is intentional and documented:
- It is deterministic — the same PDF always yields the same image.
- MRI PDFs typically contain one image per page or a single scan.
- Ambiguous multi-image cases are handled by stopping at the first success.

No images are written to disk. All processing is in-memory.
"""

from __future__ import annotations

import io
import logging

from PIL import Image

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class PDFExtractionError(Exception):
    """Raised when no usable image can be extracted from the PDF."""


# ---------------------------------------------------------------------------
# Extractor
# ---------------------------------------------------------------------------

def extract_first_image(pdf_bytes: bytes) -> Image.Image:
    """
    Extract the first decodable image from a PDF given as raw bytes.

    Parameters
    ----------
    pdf_bytes : bytes
        Raw PDF file content.

    Returns
    -------
    PIL.Image.Image
        The first usable image found in the PDF, in its original mode
        (caller should convert to RGB before CNN preprocessing).

    Raises
    ------
    PDFExtractionError
        If the PDF cannot be parsed, contains no images, or no image
        can be decoded by Pillow.
    """
    try:
        import pypdf  # noqa: PLC0415 — lazy import; pypdf is an optional dep
    except ImportError as exc:
        raise PDFExtractionError(
            "pypdf is required for PDF image extraction. "
            "Install it with: pip install pypdf"
        ) from exc

    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    except Exception as exc:
        logger.warning("Failed to open PDF: %s", exc)
        raise PDFExtractionError(
            "The PDF file could not be opened. It may be corrupted or password-protected."
        ) from exc

    num_pages = len(reader.pages)
    if num_pages == 0:
        raise PDFExtractionError("The PDF contains no pages.")

    logger.info("PDF has %d page(s). Scanning for usable MRI image.", num_pages)

    for page_index, page in enumerate(reader.pages):
        resources = page.get("/Resources")
        if resources is None:
            continue

        xobjects = resources.get("/XObject")
        if xobjects is None:
            continue

        # Resolve indirect references so we can iterate key/value pairs
        if hasattr(xobjects, "get_object"):
            xobjects = xobjects.get_object()

        for name, obj_ref in xobjects.items():
            # Resolve each XObject to its actual dictionary/stream
            try:
                xobj = obj_ref.get_object() if hasattr(obj_ref, "get_object") else obj_ref
            except Exception:
                continue

            # Only process image XObjects
            subtype = xobj.get("/Subtype")
            if subtype != "/Image":
                continue

            # Attempt to get raw image bytes from the stream
            try:
                raw_data: bytes = xobj.get_data()
            except Exception as exc:
                logger.debug(
                    "Page %d, object %s: could not get stream data: %s",
                    page_index,
                    name,
                    exc,
                )
                continue

            # Try to decode with Pillow
            try:
                image = Image.open(io.BytesIO(raw_data))
                image.load()  # Force decode — catches lazy-load failures
                logger.info(
                    "Extracted image from PDF page %d, object '%s' "
                    "(mode=%s, size=%dx%d).",
                    page_index,
                    name,
                    image.mode,
                    image.width,
                    image.height,
                )
                return image
            except Exception as exc:
                logger.debug(
                    "Page %d, object %s: Pillow could not decode image: %s",
                    page_index,
                    name,
                    exc,
                )
                # Try to interpret raw bytes as a compressed stream that
                # Pillow's JPEG/PNG decoders can handle directly via BytesIO
                #
                # Some PDF viewers encode JPEG images directly in the stream;
                # the raw bytes are already a complete JPEG file in that case.
                try:
                    image = Image.open(io.BytesIO(raw_data))
                    image.load()
                    logger.info(
                        "Extracted image (fallback decode) from PDF page %d, "
                        "object '%s'.",
                        page_index,
                        name,
                    )
                    return image
                except Exception:
                    continue

    raise PDFExtractionError(
        "No usable image could be extracted from the PDF. "
        "Ensure the PDF contains an embedded brain MRI image."
    )

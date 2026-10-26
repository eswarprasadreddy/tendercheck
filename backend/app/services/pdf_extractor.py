"""
PDF text extraction service.

Strategy (per page)
-------------------
1. PyMuPDF ``page.get_text()`` — fast, accurate for text-based PDFs.
2. If the extracted text has fewer characters than ``settings.ocr_threshold``,
   the page is likely a scanned image.  Render it to a 300-DPI pixmap and run
   Tesseract OCR.

The function is synchronous (CPU-bound) and is expected to be called in a
FastAPI ``BackgroundTasks`` worker or a thread-pool executor.
"""
from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field
from pathlib import Path

import fitz  # PyMuPDF

from app.config import settings

logger = logging.getLogger(__name__)

# Tesseract is imported lazily so the app starts even if it is not installed.
_tesseract_available: bool | None = None


def _check_tesseract() -> bool:
    global _tesseract_available
    if _tesseract_available is None:
        try:
            import pytesseract  # noqa: F401
            _tesseract_available = True
        except ImportError:
            logger.warning("pytesseract not found — OCR fallback disabled.")
            _tesseract_available = False
    return _tesseract_available


def _ocr_page(page: "fitz.Page") -> str:
    """Render *page* at 300 DPI and run Tesseract OCR on the image."""
    try:
        import pytesseract
        from PIL import Image  # noqa: PLC0415
    except ImportError:
        return ""

    mat = fitz.Matrix(300 / 72, 300 / 72)  # scale to 300 DPI
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    text = pytesseract.image_to_string(img, lang="eng")
    return text


@dataclass
class PageContent:
    page_number: int           # 1-indexed
    text: str
    char_count: int = field(init=False)
    extraction_method: str = "direct"   # "direct" | "ocr"

    def __post_init__(self) -> None:
        self.char_count = len(self.text.strip())


@dataclass
class PDFExtractionResult:
    pages: list[PageContent]
    full_text: str              # concatenation of all page texts
    page_count: int
    ocr_page_count: int         # how many pages needed OCR

    @classmethod
    def from_pages(cls, pages: list[PageContent]) -> "PDFExtractionResult":
        full_text = "\n\n".join(
            f"[Page {p.page_number}]\n{p.text}" for p in pages if p.text.strip()
        )
        return cls(
            pages=pages,
            full_text=full_text,
            page_count=len(pages),
            ocr_page_count=sum(1 for p in pages if p.extraction_method == "ocr"),
        )


def extract_pdf(pdf_path: Path) -> PDFExtractionResult:
    """
    Extract text from every page of *pdf_path*.

    Returns a ``PDFExtractionResult`` with per-page content and the full
    concatenated text.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = fitz.open(str(pdf_path))
    pages: list[PageContent] = []
    has_tesseract = _check_tesseract()

    for idx in range(len(doc)):
        page = doc[idx]
        page_number = idx + 1
        text = page.get_text("text")  # type: ignore[attr-defined]

        method = "direct"
        if len(text.strip()) < settings.ocr_threshold:
            if has_tesseract:
                logger.info("Page %d: sparse text (%d chars) — trying OCR", page_number, len(text.strip()))
                text = _ocr_page(page)
                method = "ocr"
                if not text.strip():
                    logger.warning("Page %d: OCR returned empty text", page_number)
            else:
                logger.warning(
                    "Page %d: sparse text (%d chars) and Tesseract unavailable",
                    page_number, len(text.strip()),
                )

        pages.append(PageContent(page_number=page_number, text=text, extraction_method=method))

    doc.close()
    logger.info(
        "Extracted %d pages from %s (%d via OCR)",
        len(pages), pdf_path.name, sum(1 for p in pages if p.extraction_method == "ocr"),
    )
    return PDFExtractionResult.from_pages(pages)

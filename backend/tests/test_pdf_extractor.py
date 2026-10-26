import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.services.pdf_extractor import extract_pdf, PDFExtractionResult, _ocr_page


def test_extract_pdf_sample_tender(sample_pdf_path: Path):
    """Verify PyMuPDF extracts text from every page of the generated sample tender."""
    result = extract_pdf(sample_pdf_path)

    assert isinstance(result, PDFExtractionResult)
    assert result.page_count == 3
    assert result.ocr_page_count == 0  # Generated PDF has real text, no OCR needed
    assert len(result.pages) == 3

    # Check per-page contents
    p1 = result.pages[0]
    assert p1.page_number == 1
    assert p1.extraction_method == "direct"
    assert "Minimum Average Annual Turnover" in p1.text
    assert "INR 1.50 Crore" in p1.text
    assert "Years in Business" in p1.text
    assert "Past Similar Orders" in p1.text
    assert "MSME & Startup Policy Exemption" in p1.text

    p2 = result.pages[1]
    assert p2.page_number == 2
    assert p2.extraction_method == "direct"
    assert "Processor" in p2.text
    assert "RAM / Memory" in p2.text
    assert "16 GB" in p2.text
    assert "Storage (SSD)" in p2.text
    assert "512 GB" in p2.text
    assert "Display Size" in p2.text

    p3 = result.pages[2]
    assert p3.page_number == 3
    assert p3.extraction_method == "direct"
    assert "ISO 9001:2015" in p3.text
    assert "GST Registration" in p3.text
    assert "BIS Registration" in p3.text
    assert "Make in India (MII)" in p3.text
    assert "90 days" in p3.text

    # Check concatenated full text
    assert "[Page 1]" in result.full_text
    assert "[Page 2]" in result.full_text
    assert "[Page 3]" in result.full_text


def test_extract_pdf_not_found():
    with pytest.raises(FileNotFoundError):
        extract_pdf(Path("non_existent_tender.pdf"))


def test_ocr_fallback_triggered_on_sparse_page(sample_pdf_path: Path, monkeypatch):
    """When a page text length is below ocr_threshold, verify OCR path is attempted."""
    # Force ocr_threshold higher than page 1 length
    from app.config import settings
    monkeypatch.setattr(settings, "ocr_threshold", 50000)

    # Mock _ocr_page to return OCR extracted text
    with patch("app.services.pdf_extractor._ocr_page", return_value="[OCR EXTRACTED TEXT]") as mock_ocr:
        with patch("app.services.pdf_extractor._check_tesseract", return_value=True):
            result = extract_pdf(sample_pdf_path)

            assert mock_ocr.called
            assert result.ocr_page_count == 3
            assert result.pages[0].extraction_method == "ocr"
            assert result.pages[0].text == "[OCR EXTRACTED TEXT]"

import unittest
from pathlib import Path
import tempfile
from app.services.pdf_service import (
    PDFGenerationError,
    generate_pdf_from_jpeg_bytes,
)


class TestPDFService(unittest.TestCase):
    def test_empty_frames_raises_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "output.pdf"
            with self.assertRaises(PDFGenerationError):
                generate_pdf_from_jpeg_bytes([], pdf_path)

    def test_none_frames_raises_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "output.pdf"
            with self.assertRaises(PDFGenerationError):
                generate_pdf_from_jpeg_bytes([None, None], pdf_path)


if __name__ == "__main__":
    unittest.main()

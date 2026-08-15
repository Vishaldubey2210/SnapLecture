from pathlib import Path

from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


class PDFGenerationError(Exception):
    """Raised when PDF generation fails."""


def generate_pdf(
    frames_directory: Path,
    output_path: Path,
) -> int:

    frame_files = sorted(
        frames_directory.glob("frame_*.jpg")
    )

    if not frame_files:
        raise PDFGenerationError("No frames found.")

    pdf = canvas.Canvas(
        str(output_path),
        pagesize=A4,
    )

    page_width, page_height = A4

    processed = 0

    try:
        for frame_path in frame_files:

            with Image.open(frame_path) as image:
                image_width, image_height = image.size

                max_width = page_width - 60
                max_height = page_height - 60

                scale = min(
                    max_width / image_width,
                    max_height / image_height,
                )

                display_width = image_width * scale
                display_height = image_height * scale

                x = (page_width - display_width) / 2
                y = (page_height - display_height) / 2

                pdf.drawImage(
                    str(frame_path),
                    x,
                    y,
                    width=display_width,
                    height=display_height,
                    preserveAspectRatio=True,
                    anchor="c",
                )

                pdf.showPage()

                processed += 1

        pdf.save()

    except Exception as exc:
        raise PDFGenerationError(
            f"PDF generation failed: {exc}"
        ) from exc

    return processed
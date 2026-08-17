from pathlib import Path

import img2pdf
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


class PDFGenerationError(Exception):
    """Raised when PDF generation fails."""


def generate_pdf_from_jpeg_bytes(
    frames: list[bytes | None],
    output_path: Path,
) -> int:
    """Embed ordered JPEG buffers directly, without re-encoding their pixels."""

    ordered_frames = [frame for frame in frames if frame]

    if not ordered_frames:
        raise PDFGenerationError("No frames found.")

    try:
        with output_path.open("wb") as output:
            img2pdf.convert(ordered_frames, outputstream=output)
    except Exception as exc:
        raise PDFGenerationError(
            f"PDF generation failed: {exc}"
        ) from exc

    return len(ordered_frames)


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
    columns = 2
    rows = 2
    margin = 36
    gutter = 12
    cell_width = (page_width - 2 * margin - gutter) / columns
    cell_height = (page_height - 2 * margin - gutter) / rows

    try:
        for index, frame_path in enumerate(frame_files):

            with Image.open(frame_path) as image:
                image_width, image_height = image.size

                scale = min(
                    cell_width / image_width,
                    cell_height / image_height,
                )

                display_width = image_width * scale
                display_height = image_height * scale

                cell_index = index % (columns * rows)
                column = cell_index % columns
                row = cell_index // columns
                cell_x = margin + column * (cell_width + gutter)
                cell_y = page_height - margin - (row + 1) * cell_height - row * gutter

                x = cell_x + (cell_width - display_width) / 2
                y = cell_y + (cell_height - display_height) / 2

                pdf.drawImage(
                    str(frame_path),
                    x,
                    y,
                    width=display_width,
                    height=display_height,
                    preserveAspectRatio=True,
                    anchor="c",
                )

                processed += 1

                if cell_index == columns * rows - 1 or index == len(frame_files) - 1:
                    pdf.showPage()

        pdf.save()

    except Exception as exc:
        raise PDFGenerationError(
            f"PDF generation failed: {exc}"
        ) from exc

    return processed

from pathlib import Path
from uuid import uuid4

from app.services.frame_service import extract_frames
from app.services.pdf_service import generate_pdf
from app.utils.cleanup import cleanup_directory


class VideoProcessingError(Exception):
    """Raised when video processing fails."""


def process_video_to_pdf(
    video_path: Path,
    workspace: Path,
    interval_seconds: int,
) -> tuple[Path, int]:

    workspace.mkdir(
        parents=True,
        exist_ok=True,
    )

    frames_directory = workspace / "frames"
    pdf_path = workspace / f"snaplecture_{uuid4().hex}.pdf"

    try:
        frame_count = extract_frames(
            video_path=video_path,
            output_directory=frames_directory,
            interval_seconds=interval_seconds,
        )

        generate_pdf(
            frames_directory=frames_directory,
            output_path=pdf_path,
        )

        return pdf_path, frame_count

    except Exception as exc:
        raise VideoProcessingError(
            f"Video processing failed: {exc}"
        ) from exc
from pathlib import Path
from uuid import uuid4

import cv2

from app.services.frame_service import extract_frames
from app.services.pdf_service import generate_pdf


class VideoProcessingError(Exception):
    """Raised when video processing fails."""


def get_video_duration_seconds(video_path: Path) -> float:
    """
    Return the duration of a video in seconds.

    Raises VideoProcessingError when the video metadata
    cannot be read reliably.
    """

    capture = cv2.VideoCapture(str(video_path))

    if not capture.isOpened():
        raise VideoProcessingError(
            "Unable to open the uploaded video."
        )

    try:
        fps = capture.get(cv2.CAP_PROP_FPS)
        frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT)

        if fps <= 0 or frame_count < 0:
            raise VideoProcessingError(
                "Unable to determine video duration."
            )

        return frame_count / fps

    finally:
        capture.release()


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

    pdf_path = (
        workspace
        / f"snaplecture_{uuid4().hex}.pdf"
    )

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
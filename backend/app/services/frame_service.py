from pathlib import Path

import cv2


class FrameExtractionError(Exception):
    """Raised when video frame extraction fails."""


def extract_frames(
    video_path: Path,
    output_directory: Path,
    interval_seconds: int,
) -> int:
    output_directory.mkdir(parents=True, exist_ok=True)

    capture = cv2.VideoCapture(str(video_path))

    if not capture.isOpened():
        raise FrameExtractionError("Unable to open the video.")

    fps = capture.get(cv2.CAP_PROP_FPS)
    frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT)

    if fps <= 0:
        capture.release()
        raise FrameExtractionError("Unable to determine video FPS.")

    duration_seconds = frame_count / fps

    frame_interval = max(int(fps * interval_seconds), 1)

    current_frame = 0
    saved_frames = 0

    try:
        while True:
            success, frame = capture.read()

            if not success:
                break

            if current_frame % frame_interval == 0:
                output_path = (
                    output_directory
                    / f"frame_{saved_frames + 1:06d}.jpg"
                )

                success = cv2.imwrite(
                    str(output_path),
                    frame,
                    [cv2.IMWRITE_JPEG_QUALITY, 82],
                )

                if success:
                    saved_frames += 1

            current_frame += 1

    finally:
        capture.release()

    if saved_frames == 0:
        raise FrameExtractionError(
            "No frames could be extracted from the video."
        )

    return saved_frames
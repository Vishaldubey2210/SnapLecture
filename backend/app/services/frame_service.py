from math import ceil
from pathlib import Path
from shutil import which
from subprocess import DEVNULL, CalledProcessError, run

import cv2


class FrameExtractionError(Exception):
    """Raised when video frame extraction fails."""


def _extract_frames_with_ffmpeg(
    video_path: Path,
    output_directory: Path,
    interval_seconds: int,
) -> int | None:
    """Use FFmpeg's native sequential decoder when it is available."""

    ffmpeg = which("ffmpeg")
    if not ffmpeg:
        return None

    output_pattern = output_directory / "frame_%06d.jpg"
    video_filter = (
        f"fps=1/{interval_seconds},"
        "scale='min(1280,iw)':-2:force_original_aspect_ratio=decrease"
    )

    try:
        run(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-threads",
                "0",
                "-i",
                str(video_path),
                "-vf",
                video_filter,
                "-q:v",
                "5",
                "-start_number",
                "1",
                str(output_pattern),
            ],
            check=True,
            stdout=DEVNULL,
            stderr=DEVNULL,
        )
    except CalledProcessError:
        return None

    frame_count = len(list(output_directory.glob("frame_*.jpg")))
    return frame_count or None


def extract_frames(
    video_path: Path,
    output_directory: Path,
    interval_seconds: int,
) -> int:
    output_directory.mkdir(parents=True, exist_ok=True)

    ffmpeg_frame_count = _extract_frames_with_ffmpeg(
        video_path,
        output_directory,
        interval_seconds,
    )

    if ffmpeg_frame_count:
        return ffmpeg_frame_count

    capture = cv2.VideoCapture(str(video_path))

    if not capture.isOpened():
        raise FrameExtractionError("Unable to open the video.")

    fps = capture.get(cv2.CAP_PROP_FPS)
    frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT)

    if fps <= 0:
        capture.release()
        raise FrameExtractionError("Unable to determine video FPS.")

    duration_seconds = frame_count / fps

    saved_frames = 0

    try:
        # Seeking directly to the requested timestamp avoids decoding every
        # frame of a long video just to keep one screenshot.
        for timestamp_seconds in range(
            0,
            ceil(duration_seconds),
            interval_seconds,
        ):
            capture.set(
                cv2.CAP_PROP_POS_MSEC,
                timestamp_seconds * 1000,
            )

            success, frame = capture.read()

            if not success:
                continue

            height, width = frame.shape[:2]
            max_dimension = 1280
            largest_dimension = max(width, height)

            if largest_dimension > max_dimension:
                scale = max_dimension / largest_dimension
                frame = cv2.resize(
                    frame,
                    (
                        round(width * scale),
                        round(height * scale),
                    ),
                    interpolation=cv2.INTER_AREA,
                )

            output_path = (
                output_directory
                / f"frame_{saved_frames + 1:06d}.jpg"
            )

            success = cv2.imwrite(
                str(output_path),
                frame,
                [cv2.IMWRITE_JPEG_QUALITY, 70],
            )

            if success:
                saved_frames += 1

    finally:
        capture.release()

    if saved_frames == 0:
        raise FrameExtractionError(
            "No frames could be extracted from the video."
        )

    return saved_frames

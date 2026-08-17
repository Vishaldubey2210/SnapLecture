from pathlib import Path
from urllib.parse import urlparse


ALLOWED_VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm",
    ".m4v",
}


def validate_video_extension(filename: str) -> bool:
    extension = Path(filename).suffix.lower()
    return extension in ALLOWED_VIDEO_EXTENSIONS


def validate_interval(interval_seconds: int) -> int:
    if interval_seconds < 1:
        raise ValueError("Interval must be at least 1 second.")

    if interval_seconds > 300:
        raise ValueError("Interval cannot exceed 300 seconds.")

    return interval_seconds


def validate_youtube_url(video_url: str) -> bool:
    """Return whether a URL belongs to an accepted YouTube host."""

    try:
        parsed = urlparse(video_url.strip())
    except ValueError:
        return False

    hostname = (parsed.hostname or "").lower()

    return (
        parsed.scheme in {"http", "https"}
        and hostname in {
            "youtube.com",
            "www.youtube.com",
            "m.youtube.com",
            "youtu.be",
            "www.youtu.be",
        }
    )

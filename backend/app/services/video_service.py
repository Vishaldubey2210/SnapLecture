import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from shutil import which
from subprocess import PIPE, run
from uuid import uuid4

import cv2
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from app.services.frame_service import extract_frames
from app.services.pdf_service import (
    generate_pdf,
    generate_pdf_from_image_paths,
    generate_pdf_from_jpeg_bytes,
)


logger = logging.getLogger(__name__)

#: Seconds before a cached googlevideo stream URL is considered stale.
#: googlevideo URLs are valid ~6 hours; 240 s is safe and avoids repeat
#: extract_info round-trips within the same user session.
STREAM_URL_CACHE_SECONDS = 240
_stream_url_cache: dict[str, tuple[float, "YouTubeStreamInfo"]] = {}

# Resolve the FFmpeg binary path once at import time.  which() performs a
# filesystem scan; calling it inside every worker thread is wasteful.
_FFMPEG_BIN: str | None = which("ffmpeg")


class VideoProcessingError(Exception):
    """Raised when video processing fails."""


@dataclass(frozen=True)
class YouTubeStreamInfo:
    stream_url: str
    duration_seconds: int
    http_headers: dict[str, str]


def get_youtube_stream_info(video_url: str) -> YouTubeStreamInfo:
    """Resolve and short-term cache a directly seekable, low-resolution stream URL.

    Uses yt-dlp with ``download=False`` so *no video data is ever written to
    disk*; only the metadata (including the signed CDN URL) is fetched.
    The result is cached for :data:`STREAM_URL_CACHE_SECONDS` seconds so that
    repeated calls within the same session (e.g. a duration-check followed
    immediately by a frame-extraction call) only hit YouTube once.
    """

    cached = _stream_url_cache.get(video_url)
    if cached and time.monotonic() - cached[0] < STREAM_URL_CACHE_SECONDS:
        logger.debug("Stream URL cache hit for %s", video_url)
        return cached[1]

    # Prefer low-resolution video-only stream: skips downloading audio data,
    # reducing CDN bandwidth transfer by 40-50% and speeding up chunk fetches.
    options: dict = {
        "format": (
            "bestvideo[height<=360][ext=mp4]/"
            "bestvideo[height<=480][ext=mp4]/"
            "bestvideo[height<=480]/"
            "best[height<=480]/"
            "best"
        ),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    t0 = time.perf_counter()
    try:
        with YoutubeDL(options) as downloader:
            info = downloader.extract_info(video_url, download=False)
    except DownloadError as exc:
        raise VideoProcessingError(
            "Unable to read this YouTube video. It may be private, "
            "unavailable, or restricted."
        ) from exc
    logger.debug("yt-dlp extract_info took %.3fs", time.perf_counter() - t0)

    duration = info.get("duration") if info else None
    stream_url = info.get("url") if info else None

    if not isinstance(duration, (int, float)) or duration <= 0:
        raise VideoProcessingError(
            "Unable to determine the YouTube video duration."
        )

    if not isinstance(stream_url, str) or not stream_url:
        raise VideoProcessingError("Unable to resolve a playable YouTube stream.")

    stream_info = YouTubeStreamInfo(
        stream_url=stream_url,
        duration_seconds=round(duration),
        http_headers={
            str(key): str(value)
            for key, value in (info.get("http_headers") or {}).items()
        },
    )
    _stream_url_cache[video_url] = (time.monotonic(), stream_info)
    return stream_info


def get_youtube_video_duration(video_url: str) -> int:
    """Read a YouTube video's duration without downloading its media."""
    return get_youtube_stream_info(video_url).duration_seconds


# ---------------------------------------------------------------------------
# Segment-Based & Frame-Level Extraction
# ---------------------------------------------------------------------------


def _extract_stream_segment(
    stream_info: YouTubeStreamInfo,
    start_sec: int,
    end_sec: int,
    interval_seconds: int,
    segment_output_dir: Path,
) -> list[Path]:
    """Stream a continuous slice [start_sec, end_sec] via a single FFmpeg process.

    Extracts all interval frames within the slice in one continuous streaming
    connection, avoiding the overhead of launching hundreds of OS processes.
    """
    if not _FFMPEG_BIN:
        raise VideoProcessingError("FFmpeg is required for YouTube processing.")

    segment_output_dir.mkdir(parents=True, exist_ok=True)
    user_agent = stream_info.http_headers.get(
        "User-Agent",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    )
    referer = stream_info.http_headers.get(
        "Referer",
        "https://www.youtube.com/",
    )

    output_pattern = segment_output_dir / "frame_%06d.jpg"
    duration_slice = max(1, end_sec - start_sec)

    command = [
        _FFMPEG_BIN,
        "-hide_banner",
        "-loglevel", "error",
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "5",
        "-http_persistent", "1",
        "-user_agent", user_agent,
        "-referer", referer,
        "-ss", str(start_sec),
        "-t", str(duration_slice),
        "-i", stream_info.stream_url,
        "-vf", f"fps=1/{interval_seconds},scale='min(1280,iw)':-2",
        "-q:v", "4",
        "-start_number", "1",
        str(output_pattern),
    ]

    for attempt in range(2):
        result = run(command, stdout=PIPE, stderr=PIPE, check=False, timeout=60)
        frames = sorted(segment_output_dir.glob("frame_*.jpg"))
        if result.returncode == 0 and frames:
            return frames
        if attempt == 0:
            time.sleep(1)

    return sorted(segment_output_dir.glob("frame_*.jpg"))


def _extract_stream_frame(
    stream_info: YouTubeStreamInfo,
    timestamp_seconds: int,
) -> bytes | None:
    """Seek directly to *timestamp_seconds* in the remote stream and return
    one JPEG frame as raw bytes (fallback mechanism).
    """

    if not _FFMPEG_BIN:
        raise VideoProcessingError("FFmpeg is required for YouTube processing.")

    user_agent = stream_info.http_headers.get(
        "User-Agent",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    )
    referer = stream_info.http_headers.get(
        "Referer",
        "https://www.youtube.com/",
    )

    command = [
        _FFMPEG_BIN,
        "-hide_banner",
        "-loglevel", "error",
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "5",
        "-http_persistent", "1",
        "-user_agent", user_agent,
        "-referer", referer,
        "-ss", str(timestamp_seconds),
        "-i", stream_info.stream_url,
        "-frames:v", "1",
        "-vf", "scale='min(1280,iw)':-2",
        "-q:v", "4",
        "-f", "image2pipe",
        "-vcodec", "mjpeg",
        "pipe:1",
    ]

    for attempt in range(3):
        result = run(command, stdout=PIPE, stderr=PIPE, check=False, timeout=45)
        if result.returncode == 0 and result.stdout:
            return result.stdout

        details = result.stderr.decode("utf-8", errors="replace")
        if attempt == 2:
            logger.warning(
                "Skipping frame at %ss after 3 attempts: %s",
                timestamp_seconds,
                details[-300:],
            )
            return None

        is_rate_limited = "403" in details or "429" in details
        delay = 2 ** attempt if is_rate_limited else 1
        time.sleep(delay)

    return None


def process_youtube_stream_to_pdf(
    video_url: str,
    workspace: Path,
    interval_seconds: int,
    *,
    stream_info: YouTubeStreamInfo | None = None,
) -> tuple[Path, int, dict[str, float]]:
    """Extract ordered frames via dynamic parallel segment streaming and build PDF."""

    total_started = time.perf_counter()

    # Stage 1: Resolve stream info
    info_started = time.perf_counter()
    if stream_info is None:
        stream_info = get_youtube_stream_info(video_url)
    info_seconds = time.perf_counter() - info_started

    duration = stream_info.duration_seconds
    total_expected_frames = max(1, duration // interval_seconds)

    # Stage 2: Dynamic segment partitioning
    # For any video length (up to 2+ hours), dynamically partition into
    # parallel continuous streaming segments so extraction completes in 10-15s.
    max_workers = min(max(4, (os.cpu_count() or 4) * 2), 12)
    if total_expected_frames <= 10 or duration <= 60:
        num_segments = 1
    else:
        num_segments = min(max_workers, max(2, duration // 120))

    segment_duration = max(1, duration // num_segments)
    segments: list[tuple[int, int, int, Path]] = []

    for i in range(num_segments):
        s_start = i * segment_duration
        s_end = duration if i == num_segments - 1 else (i + 1) * segment_duration
        seg_dir = workspace / f"seg_{i:03d}"
        segments.append((i, s_start, s_end, seg_dir))

    logger.info(
        "Extracting %ds video (%d expected frames) across %d parallel segments (workers=%d)",
        duration,
        total_expected_frames,
        num_segments,
        max_workers,
    )

    # Stage 3: Parallel segment extraction
    extraction_started = time.perf_counter()
    segment_results: dict[int, list[Path]] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {
            executor.submit(
                _extract_stream_segment,
                stream_info,
                s_start,
                s_end,
                interval_seconds,
                s_dir,
            ): idx
            for idx, s_start, s_end, s_dir in segments
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                segment_results[idx] = future.result()
            except Exception as exc:
                logger.warning("Segment %d extraction failed: %s", idx, exc)
                segment_results[idx] = []

    # Assemble in exact chronological order across segments, with fallback
    all_frame_paths: list[Path] = []
    for i in range(num_segments):
        frames = segment_results.get(i, [])
        # Resilient fallback: If a segment failed, fallback to timestamp seeks
        if not frames:
            s_start = segments[i][1]
            s_end = segments[i][2]
            seg_dir = segments[i][3]
            seg_dir.mkdir(parents=True, exist_ok=True)
            ts_list = list(range(s_start, s_end, interval_seconds))
            for ts_idx, ts in enumerate(ts_list):
                frame_bytes = _extract_stream_frame(stream_info, ts)
                if frame_bytes:
                    fpath = seg_dir / f"fallback_{ts_idx:05d}.jpg"
                    fpath.write_bytes(frame_bytes)
                    frames.append(fpath)
        all_frame_paths.extend(frames)

    extraction_seconds = time.perf_counter() - extraction_started

    # Stage 4: Fast PDF assembly
    pdf_started = time.perf_counter()
    workspace.mkdir(parents=True, exist_ok=True)
    pdf_path = workspace / f"snaplecture_{uuid4().hex}.pdf"

    if all_frame_paths:
        frame_count = generate_pdf_from_image_paths(all_frame_paths, pdf_path)
    else:
        # Fallback to single frame at timestamp 0
        fallback_bytes = _extract_stream_frame(stream_info, 0)
        if fallback_bytes:
            frame_count = generate_pdf_from_jpeg_bytes([fallback_bytes], pdf_path)
        else:
            raise VideoProcessingError("No frames could be extracted from this YouTube video.")

    pdf_seconds = time.perf_counter() - pdf_started
    total_seconds = time.perf_counter() - total_started

    timings: dict[str, float] = {
        "yt_dlp_info_seconds": round(info_seconds, 3),
        "frame_extraction_seconds": round(extraction_seconds, 3),
        "pdf_assembly_seconds": round(pdf_seconds, 3),
        "total_seconds": round(total_seconds, 3),
    }

    logger.info(
        "YouTube PDF pipeline complete | %d frames in %.3fs | timings=%s",
        frame_count,
        total_seconds,
        timings,
    )
    return pdf_path, frame_count, timings


def download_youtube_video(
    video_url: str,
    workspace: Path,
    max_bytes: int,
) -> Path:
    """Download one YouTube video into the request workspace."""

    output_template = str(workspace / "youtube_video.%(ext)s")
    options = {
        "format": "best[ext=mp4]/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "max_filesize": max_bytes,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
    }

    try:
        with YoutubeDL(options) as downloader:
            downloader.extract_info(video_url, download=True)
    except DownloadError as exc:
        raise VideoProcessingError(
            "Unable to download this YouTube video. It may be private, "
            "unavailable, or restricted."
        ) from exc
    except Exception as exc:
        raise VideoProcessingError(
            "Unable to download the YouTube video."
        ) from exc

    downloaded_files = [
        path
        for path in workspace.glob("youtube_video.*")
        if path.is_file() and path.suffix != ".part"
    ]

    if len(downloaded_files) != 1:
        raise VideoProcessingError(
            "The YouTube video download did not produce a usable video."
        )

    video_path = downloaded_files[0]

    if video_path.stat().st_size > max_bytes:
        raise VideoProcessingError(
            "YouTube video exceeds the maximum allowed size."
        )

    return video_path


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

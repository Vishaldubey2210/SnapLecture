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

    # Prefer a <=480p MP4 stream: lower-resolution decode is faster for
    # individual frame seeks and produces smaller JPEG output at comparable
    # text/slide legibility.
    options: dict = {
        "format": "best[height<=480][ext=mp4]/best[height<=480]/best",
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


def _extract_stream_frame(
    stream_info: YouTubeStreamInfo,
    timestamp_seconds: int,
) -> bytes | None:
    """Seek directly to *timestamp_seconds* in the remote stream and return
    one JPEG frame as raw bytes.

    Design notes
    ~~~~~~~~~~~~
    * ``-ss`` is placed **before** ``-i`` (input-level seek) so FFmpeg sends
      an HTTP range request to the CDN rather than decoding every packet up
      to that point.
    * ``-reconnect`` flags instruct FFmpeg's HTTPS demuxer to transparently
      retry on dropped CDN connections.
    * ``-http_persistent 1`` reuses the underlying TCP/TLS connection where
      possible, saving one handshake per frame on the happy path.
    * Resolution is capped at 1 280 px wide via ``scale='min(1280,iw)':-2``.
      For sources already ≤ 480 p this is a no-op; no upscale or two-pass
      resize occurs.
    * Up to **3 attempts** (initial + 2 retries).  403/429 responses receive
      exponential back-off (1 s then 2 s); other transient errors get a flat
      1-second pause.  A single failed frame never aborts the whole job.
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
    # Input-level seek flags come BEFORE -i so FFmpeg uses the fast HTTP
    # range-request path instead of decoding from the start of the stream.
    command = [
        _FFMPEG_BIN,
        "-hide_banner",
        "-loglevel", "error",
        # Reconnect / persistence flags (apply to the HTTP source demuxer)
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "5",
        "-http_persistent", "1",
        # Spoof browser identity so YouTube CDN accepts the request
        "-user_agent", user_agent,
        "-referer", referer,
        # Fast seek — sent as HTTP range header, not decode-and-drop
        "-ss", str(timestamp_seconds),
        # Remote stream — no local file is ever written
        "-i", stream_info.stream_url,
        # Single JPEG frame, quality band 4, width capped at 1 280 px
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

        # 403 / 429 → CDN rate-limit: exponential back-off (1 s, 2 s).
        # Any other transient failure → flat 1-second pause before retry.
        is_rate_limited = "403" in details or "429" in details
        delay = 2 ** attempt if is_rate_limited else 1
        logger.debug(
            "Frame @%ss attempt %d failed (%s), retrying in %ds",
            timestamp_seconds,
            attempt + 1,
            "rate-limited" if is_rate_limited else "error",
            delay,
        )
        time.sleep(delay)

    return None  # unreachable, but satisfies the type checker


def process_youtube_stream_to_pdf(
    video_url: str,
    workspace: Path,
    interval_seconds: int,
    *,
    stream_info: YouTubeStreamInfo | None = None,
) -> tuple[Path, int, dict[str, float]]:
    """Extract ordered frames from a remote stream and assemble them into a PDF.

    Parameters
    ----------
    video_url:
        The YouTube video URL.
    workspace:
        Directory where the output PDF will be written.
    interval_seconds:
        One frame is captured every this many seconds of video.
    stream_info:
        Optional pre-resolved :class:`YouTubeStreamInfo`.  Pass this when the
        caller has already called :func:`get_youtube_stream_info` (e.g. to
        check the duration) so a second ``extract_info`` round-trip is avoided.
        If *None*, stream info is resolved here (cache is checked first).

    Returns
    -------
    tuple[Path, int, dict[str, float]]
        ``(pdf_path, frame_count, timings)``

        ``timings`` keys:

        * ``yt_dlp_info_seconds`` – time in ``extract_info`` (≈0 on cache hit)
        * ``frame_extraction_seconds`` – wall time of the parallel block
        * ``pdf_assembly_seconds`` – time to write the final PDF
        * ``total_seconds`` – end-to-end elapsed time for this call
    """

    total_started = time.perf_counter()

    # ------------------------------------------------------------------
    # Stage 1 – resolve stream URL (may be a near-zero-cost cache hit)
    # ------------------------------------------------------------------
    info_started = time.perf_counter()
    if stream_info is None:
        stream_info = get_youtube_stream_info(video_url)
    info_seconds = time.perf_counter() - info_started
    logger.info(
        "Stream URL resolved in %.3fs | duration=%ds",
        info_seconds,
        stream_info.duration_seconds,
    )

    # ------------------------------------------------------------------
    # Stage 2 – build timestamp list
    # ------------------------------------------------------------------
    timestamps = list(range(0, stream_info.duration_seconds, interval_seconds))
    if not timestamps:
        timestamps = [0]
    logger.info(
        "Extracting %d frames at %ds intervals from a %ds video",
        len(timestamps),
        interval_seconds,
        stream_info.duration_seconds,
    )

    # ------------------------------------------------------------------
    # Stage 3 – parallel frame extraction
    #
    # * ThreadPoolExecutor (not asyncio) because workers call subprocess.run()
    #   which is blocking by nature.
    # * max_workers capped at 12 to stay under YouTube CDN rate limits.
    # * Results stored into a pre-allocated list by index so the PDF always
    #   contains frames in chronological order regardless of completion order.
    # ------------------------------------------------------------------
    results: list[bytes | None] = [None] * len(timestamps)
    max_workers = min((os.cpu_count() or 1) * 2, 12)
    logger.info("Using %d worker threads for frame extraction", max_workers)

    extraction_started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_index = {
            executor.submit(_extract_stream_frame, stream_info, ts): idx
            for idx, ts in enumerate(timestamps)
        }
        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            try:
                results[idx] = future.result()
            except Exception as exc:
                logger.warning("Skipping frame index %d: %s", idx, exc)

    extraction_seconds = time.perf_counter() - extraction_started
    extracted_count = sum(1 for r in results if r)
    logger.info(
        "Frame extraction finished in %.3fs | %d/%d frames captured",
        extraction_seconds,
        extracted_count,
        len(timestamps),
    )

    # ------------------------------------------------------------------
    # Stage 4 – PDF assembly via img2pdf (lossless JPEG embedding, no
    #           pixel re-encoding — significantly faster than reportlab)
    # ------------------------------------------------------------------
    pdf_started = time.perf_counter()
    workspace.mkdir(parents=True, exist_ok=True)
    pdf_path = workspace / f"snaplecture_{uuid4().hex}.pdf"
    frame_count = generate_pdf_from_jpeg_bytes(results, pdf_path)
    pdf_seconds = time.perf_counter() - pdf_started

    total_seconds = time.perf_counter() - total_started
    timings: dict[str, float] = {
        "yt_dlp_info_seconds": round(info_seconds, 3),
        "frame_extraction_seconds": round(extraction_seconds, 3),
        "pdf_assembly_seconds": round(pdf_seconds, 3),
        "total_seconds": round(total_seconds, 3),
    }
    logger.info(
        "YouTube PDF pipeline complete | frames=%d | timings=%s",
        frame_count,
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

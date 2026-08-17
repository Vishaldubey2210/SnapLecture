import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from app.core.config import settings
from app.core.errors import (
    InvalidVideoError,
    SnapLectureError,
    VideoProcessingFailedError,
    VideoTooLargeError,
    VideoTooLongError,
)
from app.services.video_service import (
    VideoProcessingError,
    YouTubeStreamInfo,
    download_youtube_video,
    get_video_duration_seconds,
    get_youtube_stream_info,
    get_youtube_video_duration,
    process_video_to_pdf,
    process_youtube_stream_to_pdf,
)
from app.utils.cleanup import cleanup_directory
from app.utils.validators import (
    validate_interval,
    validate_video_extension,
    validate_youtube_url,
)


router = APIRouter(
    prefix="/pdf",
    tags=["PDF"],
)


async def save_upload_with_limit(
    upload: UploadFile,
    destination: Path,
    max_bytes: int,
) -> int:
    """
    Stream the uploaded file to disk while enforcing
    a hard maximum size.
    """

    total_bytes = 0
    chunk_size = 1024 * 1024

    with destination.open("wb") as output:
        while True:
            chunk = await upload.read(chunk_size)

            if not chunk:
                break

            total_bytes += len(chunk)

            if total_bytes > max_bytes:
                raise VideoTooLargeError(
                    message=(
                        "Video exceeds the maximum allowed size "
                        f"of {settings.max_video_size_mb} MB."
                    )
                )

            output.write(chunk)

    return total_bytes


@router.post("/generate")
async def generate_pdf_from_video(
    video: UploadFile = File(...),
    interval_seconds: int = Form(5),
):
    """
    Process an authorized video upload and return a generated PDF.
    """

    if not video.filename:
        raise InvalidVideoError(
            "Video filename is required."
        )

    filename = Path(video.filename).name

    if not validate_video_extension(filename):
        raise InvalidVideoError(
            (
                "Unsupported video format. "
                "Use MP4, MOV, AVI, MKV, WEBM or M4V."
            )
        )

    try:
        validate_interval(interval_seconds)

    except ValueError as exc:
        await video.close()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    workspace = Path(
        tempfile.mkdtemp(
            prefix="snaplecture_",
            dir=settings.temp_directory,
        )
    )

    video_path = workspace / filename

    try:
        await save_upload_with_limit(
            upload=video,
            destination=video_path,
            max_bytes=(
                settings.max_video_size_mb
                * 1024
                * 1024
            ),
        )

        await video.close()

        duration_seconds = get_video_duration_seconds(
            video_path
        )

        max_duration_seconds = (
            settings.max_video_duration_minutes * 60
        )

        if duration_seconds > max_duration_seconds:
            raise VideoTooLongError(
                (
                    "Video exceeds the maximum allowed "
                    f"duration of "
                    f"{settings.max_video_duration_minutes} minutes."
                )
            )

        pdf_path, frame_count = process_video_to_pdf(
            video_path=video_path,
            workspace=workspace,
            interval_seconds=interval_seconds,
        )

        if not pdf_path.exists():
            raise VideoProcessingFailedError(
                "PDF generation failed."
            )

        cleanup_task = BackgroundTask(
            cleanup_directory,
            workspace,
        )

        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename="SnapLecture.pdf",
            background=cleanup_task,
        )

    except SnapLectureError:
        await video.close()
        cleanup_directory(workspace)
        raise

    except VideoProcessingError as exc:
        await video.close()
        cleanup_directory(workspace)

        raise VideoProcessingFailedError(
            str(exc)
        ) from exc

    except Exception as exc:
        await video.close()
        cleanup_directory(workspace)

        raise VideoProcessingFailedError() from exc


@router.post("/generate-youtube")
async def generate_pdf_from_youtube(
    youtube_url: str = Form(...),
    interval_seconds: int = Form(5),
):
    """Extract frames from a YouTube video stream and return them as a PDF.

    No video file is downloaded to disk; only individual frame bytes are
    fetched from the remote CDN stream URL.
    """

    if not validate_youtube_url(youtube_url):
        raise InvalidVideoError("Enter a valid YouTube video link.")

    try:
        validate_interval(interval_seconds)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    workspace = Path(
        tempfile.mkdtemp(
            prefix="snaplecture_youtube_",
            dir=settings.temp_directory,
        )
    )

    try:
        # Resolve the stream URL once — this is the only extract_info call.
        # The result is cached for STREAM_URL_CACHE_SECONDS so the subsequent
        # call inside process_youtube_stream_to_pdf is a near-zero cache hit.
        stream_info = get_youtube_stream_info(youtube_url)

        pdf_path, frame_count, timings = process_youtube_stream_to_pdf(
            video_url=youtube_url,
            workspace=workspace,
            interval_seconds=interval_seconds,
            stream_info=stream_info,
        )

        if not pdf_path.exists():
            raise VideoProcessingFailedError("PDF generation failed.")

        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename="SnapLecture-YouTube.pdf",
            background=BackgroundTask(cleanup_directory, workspace),
            headers={
                "X-SnapLecture-Ytdlp-Info-Seconds": str(timings["yt_dlp_info_seconds"]),
                "X-SnapLecture-Frame-Extraction-Seconds": str(timings["frame_extraction_seconds"]),
                "X-SnapLecture-Pdf-Assembly-Seconds": str(timings["pdf_assembly_seconds"]),
                "X-SnapLecture-Total-Seconds": str(timings["total_seconds"]),
                "X-SnapLecture-Frame-Count": str(frame_count),
            },
        )

    except SnapLectureError:
        cleanup_directory(workspace)
        raise
    except VideoProcessingError as exc:
        cleanup_directory(workspace)
        raise VideoProcessingFailedError(str(exc)) from exc
    except Exception as exc:
        cleanup_directory(workspace)
        raise VideoProcessingFailedError() from exc


@router.post("/youtube-info")
async def get_youtube_info(youtube_url: str = Form(...)):
    """Return duration metadata for a YouTube URL to estimate PDF processing."""

    if not validate_youtube_url(youtube_url):
        raise InvalidVideoError("Enter a valid YouTube video link.")

    try:
        duration_seconds = get_youtube_video_duration(youtube_url)
    except VideoProcessingError as exc:
        raise VideoProcessingFailedError(str(exc)) from exc

    return {"duration_seconds": duration_seconds}

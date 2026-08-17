import shutil
import tempfile
from pathlib import Path

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from app.core.config import settings
from app.services.video_service import (
    VideoProcessingError,
    get_video_duration_seconds,
    process_video_to_pdf,
)
from app.utils.cleanup import cleanup_directory
from app.utils.validators import (
    validate_interval,
    validate_video_extension,
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

    Returns the total number of bytes written.
    """

    total_bytes = 0
    chunk_size = 1024 * 1024  # 1 MB

    with destination.open("wb") as output:

        while True:
            chunk = await upload.read(chunk_size)

            if not chunk:
                break

            total_bytes += len(chunk)

            if total_bytes > max_bytes:
                raise ValueError(
                    "Video exceeds the maximum allowed size."
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

    Security limits:
    - file extension validation
    - maximum upload size
    - maximum video duration
    - temporary workspace cleanup
    """

    if not video.filename:
        raise HTTPException(
            status_code=400,
            detail="Video filename is required.",
        )

    filename = Path(video.filename).name

    if not validate_video_extension(filename):
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported video format. "
                "Use MP4, MOV, AVI, MKV, WEBM or M4V."
            ),
        )

    try:
        validate_interval(interval_seconds)

    except ValueError as exc:
        await video.close()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    max_size_bytes = (
        settings.max_video_size_mb
        * 1024
        * 1024
    )

    workspace = Path(
        tempfile.mkdtemp(
            prefix="snaplecture_",
            dir=settings.temp_directory,
        )
    )

    video_path = workspace / filename

    try:
        # --------------------------------------------------
        # 1. Stream upload with hard size limit
        # --------------------------------------------------

        await save_upload_with_limit(
            upload=video,
            destination=video_path,
            max_bytes=max_size_bytes,
        )

        await video.close()

        # --------------------------------------------------
        # 2. Check video duration
        # --------------------------------------------------

        duration_seconds = get_video_duration_seconds(
            video_path
        )

        max_duration_seconds = (
            settings.max_video_duration_minutes
            * 60
        )

        if duration_seconds > max_duration_seconds:
            raise HTTPException(
                status_code=413,
                detail=(
                    "Video exceeds the maximum allowed "
                    f"duration of "
                    f"{settings.max_video_duration_minutes} minutes."
                ),
            )

        # --------------------------------------------------
        # 3. Process video
        # --------------------------------------------------

        pdf_path, frame_count = process_video_to_pdf(
            video_path=video_path,
            workspace=workspace,
            interval_seconds=interval_seconds,
        )

        if not pdf_path.exists():
            raise HTTPException(
                status_code=500,
                detail=(
                    "PDF generation completed but "
                    "the PDF file was not created."
                ),
            )

        # --------------------------------------------------
        # 4. Delete workspace after response is sent
        # --------------------------------------------------

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

    except ValueError as exc:
        await video.close()
        cleanup_directory(workspace)

        raise HTTPException(
            status_code=413,
            detail=(
                f"Maximum upload size is "
                f"{settings.max_video_size_mb} MB."
            ),
        ) from exc

    except HTTPException:
        await video.close()
        cleanup_directory(workspace)
        raise

    except VideoProcessingError as exc:
        await video.close()
        cleanup_directory(workspace)

        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        await video.close()
        cleanup_directory(workspace)

        raise HTTPException(
            status_code=500,
            detail="Unable to process the video.",
        ) from exc
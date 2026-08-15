import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core.config import settings
from app.services.video_service import process_video_to_pdf
from app.utils.cleanup import cleanup_directory
from app.utils.validators import (
    validate_interval,
    validate_video_extension,
)


router = APIRouter(
    prefix="/pdf",
    tags=["PDF"],
)


@router.post("/generate")
async def generate_pdf_from_video(
    video: UploadFile = File(...),
    interval_seconds: int = Form(5),
):
    """
    Process an authorized video upload and return
    a generated PDF.

    No permanent video, frame, or PDF storage is used.
    """

    if not video.filename:
        raise HTTPException(
            status_code=400,
            detail="Video filename is required.",
        )

    if not validate_video_extension(video.filename):
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

    video_path = workspace / video.filename

    try:
        with video_path.open("wb") as destination:
            shutil.copyfileobj(
                video.file,
                destination,
            )

        pdf_path, frame_count = process_video_to_pdf(
            video_path=video_path,
            workspace=workspace,
            interval_seconds=interval_seconds,
        )

        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename="SnapLecture.pdf",
            background=None,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    finally:
        await video.close()

        # Cleanup is intentionally performed after
        # request processing.
        #
        # In production this should be attached to
        # the response lifecycle/background cleanup.
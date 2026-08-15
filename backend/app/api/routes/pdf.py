import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

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
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    interval_seconds: int = Form(5),
):
    """
    Process an authorized video upload and return a generated PDF.

    Processing files are stored only inside a temporary workspace.
    The workspace is deleted after the PDF response is completed.
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

    video_path = workspace / Path(video.filename).name

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

        if not pdf_path.exists():
            raise HTTPException(
                status_code=500,
                detail="PDF generation completed but the file was not created.",
            )

        # Close the uploaded file before returning the response.
        await video.close()

        # Cleanup runs AFTER FileResponse has finished sending
        # the PDF to the client.
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

    except HTTPException:
        await video.close()
        cleanup_directory(workspace)
        raise

    except Exception as exc:
        await video.close()
        cleanup_directory(workspace)

        raise HTTPException(
            status_code=500,
            detail="Unable to generate PDF.",
        ) from exc
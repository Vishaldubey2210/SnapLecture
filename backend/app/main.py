from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.health import router as health_router
from app.api.routes.pdf import router as pdf_router
from app.core.config import settings
from app.core.errors import SnapLectureError
from app.core.logging import configure_logging


configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting {settings.app_name}")
    print(f"Environment: {settings.environment}")

    yield

    print("Shutting down SnapLecture")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Privacy-focused video-to-PDF processing API.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(SnapLectureError)
async def snaplecture_exception_handler(
    request: Request,
    exc: SnapLectureError,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message,
            },
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred.",
            },
        },
    )


app.include_router(
    health_router,
    prefix=settings.api_prefix,
)

app.include_router(
    pdf_router,
    prefix=settings.api_prefix,
)


@app.get("/", tags=["Root"])
async def root() -> dict[str, Any]:
    return {
        "name": "SnapLecture API",
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
    }
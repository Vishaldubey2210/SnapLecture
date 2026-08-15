from pydantic import BaseModel, Field


class PDFGenerationResponse(BaseModel):
    success: bool
    filename: str
    frames_processed: int
    message: str


class PDFGenerationOptions(BaseModel):
    interval_seconds: int = Field(
        default=5,
        ge=1,
        le=300,
        description="Interval between captured frames in seconds.",
    )
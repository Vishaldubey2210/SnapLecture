from fastapi import status


class SnapLectureError(Exception):
    """Base exception for known SnapLecture application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: str = "APPLICATION_ERROR",
    ) -> None:
        super().__init__(message)

        self.message = message
        self.status_code = status_code
        self.error_code = error_code


class InvalidVideoError(SnapLectureError):
    def __init__(self, message: str = "Unsupported video format.") -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_VIDEO",
        )


class VideoTooLargeError(SnapLectureError):
    def __init__(
        self,
        message: str = "Video exceeds the maximum allowed size.",
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            error_code="VIDEO_TOO_LARGE",
        )


class VideoTooLongError(SnapLectureError):
    def __init__(
        self,
        message: str = "Video exceeds the maximum allowed duration.",
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            error_code="VIDEO_TOO_LONG",
        )


class VideoProcessingFailedError(SnapLectureError):
    def __init__(
        self,
        message: str = "Unable to process the video.",
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VIDEO_PROCESSING_FAILED",
        )
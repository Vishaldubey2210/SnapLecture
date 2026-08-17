import unittest
from app.core.errors import (
    InvalidVideoError,
    VideoTooLongError,
    VideoTooLargeError,
    VideoProcessingFailedError,
)


class TestCustomErrors(unittest.TestCase):
    def test_invalid_video_error(self):
        err = InvalidVideoError("Test invalid format")
        self.assertEqual(err.status_code, 400)
        self.assertEqual(err.error_code, "INVALID_VIDEO")

    def test_video_too_long_error(self):
        err = VideoTooLongError("Exceeds max duration")
        self.assertEqual(err.status_code, 413)
        self.assertEqual(err.error_code, "VIDEO_TOO_LONG")

    def test_video_too_large_error(self):
        err = VideoTooLargeError("Exceeds max size")
        self.assertEqual(err.status_code, 413)
        self.assertEqual(err.error_code, "VIDEO_TOO_LARGE")

    def test_video_processing_failed_error(self):
        err = VideoProcessingFailedError()
        self.assertEqual(err.status_code, 422)
        self.assertEqual(err.error_code, "VIDEO_PROCESSING_FAILED")


if __name__ == "__main__":
    unittest.main()

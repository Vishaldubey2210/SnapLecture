import unittest
from pathlib import Path
from app.services.video_service import VideoProcessingError, get_video_duration_seconds


class TestDurationHelpers(unittest.TestCase):
    def test_nonexistent_file_raises_error(self):
        fake_path = Path("temp/nonexistent_sample_video.mp4")
        with self.assertRaises(VideoProcessingError):
            get_video_duration_seconds(fake_path)


if __name__ == "__main__":
    unittest.main()

import unittest
from app.services.video_service import YouTubeStreamInfo


class TestYouTubeStreamInfo(unittest.TestCase):
    def test_youtube_stream_info_dataclass(self):
        info = YouTubeStreamInfo(
            stream_url="https://rr1---sn-example.googlevideo.com/videoplayback",
            duration_seconds=300,
            http_headers={"User-Agent": "SnapLecture-Test"},
        )
        self.assertEqual(info.duration_seconds, 300)
        self.assertTrue(info.stream_url.startswith("https://"))
        self.assertEqual(info.http_headers["User-Agent"], "SnapLecture-Test")


if __name__ == "__main__":
    unittest.main()

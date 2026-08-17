import time
import unittest
from app.services.video_service import (
    STREAM_URL_CACHE_SECONDS,
    YouTubeStreamInfo,
    _stream_url_cache,
)


class TestStreamCache(unittest.TestCase):
    def setUp(self):
        _stream_url_cache.clear()

    def test_cache_storage_and_validity(self):
        url = "https://www.youtube.com/watch?v=mock123"
        info = YouTubeStreamInfo("https://stream.googlevideo.com/mock", 120, {})
        _stream_url_cache[url] = (time.monotonic(), info)

        cached = _stream_url_cache.get(url)
        self.assertIsNotNone(cached)
        self.assertLess(time.monotonic() - cached[0], STREAM_URL_CACHE_SECONDS)
        self.assertEqual(cached[1].duration_seconds, 120)

    def test_cache_expiration(self):
        url = "https://www.youtube.com/watch?v=expired123"
        info = YouTubeStreamInfo("https://stream.googlevideo.com/mock", 120, {})
        _stream_url_cache[url] = (time.monotonic() - (STREAM_URL_CACHE_SECONDS + 10), info)

        cached = _stream_url_cache.get(url)
        self.assertIsNotNone(cached)
        self.assertGreater(time.monotonic() - cached[0], STREAM_URL_CACHE_SECONDS)


if __name__ == "__main__":
    unittest.main()

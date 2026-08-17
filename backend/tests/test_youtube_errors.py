import unittest

from yt_dlp.utils import DownloadError

from app.services.video_service import (
    _is_youtube_rate_limited,
    _youtube_download_error_message,
)


class TestYoutubeDownloadErrorMessages(unittest.TestCase):
    def test_network_error_is_not_reported_as_a_private_video(self):
        error = DownloadError(
            "Unable to download API page: [WinError 10013] "
            "An attempt was made to access a socket"
        )

        self.assertEqual(
            _youtube_download_error_message(error),
            "Unable to connect to YouTube. Check the backend network or proxy settings.",
        )

    def test_private_video_error_is_explained(self):
        error = DownloadError("Private video. Sign in if you've been granted access")

        self.assertEqual(
            _youtube_download_error_message(error),
            "This YouTube video is private and cannot be processed.",
        )

    def test_rate_limit_error_is_explained(self):
        error = DownloadError("HTTP Error 429: Too Many Requests")

        self.assertEqual(
            _youtube_download_error_message(error),
            "YouTube temporarily rate-limited this request. Please try again shortly.",
        )
        self.assertTrue(_is_youtube_rate_limited(error))

    def test_non_rate_limit_error_is_not_retried(self):
        error = DownloadError("Private video")

        self.assertFalse(_is_youtube_rate_limited(error))


if __name__ == "__main__":
    unittest.main()

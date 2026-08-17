import unittest
from app.utils.validators import (
    validate_video_extension,
    validate_interval,
    validate_youtube_url,
)


class TestValidators(unittest.TestCase):
    def test_video_extensions(self):
        self.assertTrue(validate_video_extension("lecture.mp4"))
        self.assertTrue(validate_video_extension("presentation.MOV"))
        self.assertTrue(validate_video_extension("clip.webm"))
        self.assertTrue(validate_video_extension("screen.mkv"))
        self.assertTrue(validate_video_extension("sample.AVI"))
        self.assertTrue(validate_video_extension("video.M4V"))
        self.assertFalse(validate_video_extension("document.pdf"))
        self.assertFalse(validate_video_extension("script.py"))
        self.assertFalse(validate_video_extension("archive.zip"))

    def test_interval_validation(self):
        self.assertEqual(validate_interval(5), 5)
        self.assertEqual(validate_interval(1), 1)
        self.assertEqual(validate_interval(300), 300)
        with self.assertRaises(ValueError):
            validate_interval(0)
        with self.assertRaises(ValueError):
            validate_interval(301)
        with self.assertRaises(ValueError):
            validate_interval(-5)

    def test_youtube_url_validation(self):
        self.assertTrue(validate_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))
        self.assertTrue(validate_youtube_url("https://youtu.be/dQw4w9WgXcQ"))
        self.assertTrue(validate_youtube_url("https://m.youtube.com/watch?v=dQw4w9WgXcQ"))
        self.assertTrue(validate_youtube_url("http://www.youtube.com/watch?v=dQw4w9WgXcQ"))
        self.assertFalse(validate_youtube_url("https://vimeo.com/123456"))
        self.assertFalse(validate_youtube_url("https://dailymotion.com/video/x123"))
        self.assertFalse(validate_youtube_url("not a url"))
        self.assertFalse(validate_youtube_url(""))


if __name__ == "__main__":
    unittest.main()

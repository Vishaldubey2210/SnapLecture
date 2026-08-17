import unittest
from app.core.config import settings
from app.main import app


class TestHealthAndConfig(unittest.TestCase):
    def test_app_metadata(self):
        self.assertEqual(app.title, settings.app_name)
        self.assertEqual(app.version, settings.app_version)

    def test_settings_defaults(self):
        self.assertEqual(settings.max_video_size_mb, 500)
        self.assertEqual(settings.max_video_duration_minutes, 120)
        self.assertTrue(settings.api_prefix.startswith("/"))


if __name__ == "__main__":
    unittest.main()

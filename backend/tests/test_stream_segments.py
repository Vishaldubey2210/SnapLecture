import tempfile
import unittest
from pathlib import Path

from app.services.video_service import (
    STREAM_SEGMENT_SECONDS,
    _build_stream_segments,
)


class TestStreamSegments(unittest.TestCase):
    def test_longer_videos_receive_more_chunks(self):
        workspace = Path(tempfile.gettempdir())

        short = _build_stream_segments(STREAM_SEGMENT_SECONDS, workspace)
        long = _build_stream_segments(STREAM_SEGMENT_SECONDS * 10 + 1, workspace)

        self.assertEqual(len(short), 1)
        self.assertEqual(len(long), 11)

    def test_chunks_cover_the_full_duration_without_gaps(self):
        workspace = Path(tempfile.gettempdir())
        duration = STREAM_SEGMENT_SECONDS * 2 + 17

        segments = _build_stream_segments(duration, workspace)

        self.assertEqual(segments[0][1], 0)
        self.assertEqual(segments[-1][2], duration)
        self.assertEqual(
            [(start, end) for _, start, end, _ in segments],
            [(0, 90), (90, 180), (180, 197)],
        )


if __name__ == "__main__":
    unittest.main()

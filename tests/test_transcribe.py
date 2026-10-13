import sys
import unittest

from helpers import PARTS

sys.path.insert(0, str(PARTS / "transcribe-srt" / "server"))
import ppm_transcribe as tr  # noqa: E402


class TranscribeTests(unittest.TestCase):
    def test_engine_choice(self):
        has = lambda names: (lambda mod: object() if mod in names else None)
        self.assertEqual(tr.choose_engine("darwin", "arm64", has({"mlx_whisper", "faster_whisper"})), "mlx")
        self.assertEqual(tr.choose_engine("darwin", "x86_64", has({"mlx_whisper", "faster_whisper"})), "faster")
        self.assertEqual(tr.choose_engine("win32", "AMD64", has({"faster_whisper"})), "faster")
        self.assertIsNone(tr.choose_engine("win32", "AMD64", has(set())))

    def test_install_hint_mentions_consent_and_size(self):
        hint = tr.install_hint("win32", "AMD64")
        self.assertIn("faster-whisper", hint)
        self.assertIn("許可", hint)
        self.assertIn("GB", hint)
        self.assertIn("mlx-whisper", tr.install_hint("darwin", "arm64"))

    def test_srt_time(self):
        self.assertEqual(tr.srt_time(62.3456), "00:01:02,346")
        self.assertEqual(tr.srt_time(3600), "01:00:00,000")

    def test_split_lines(self):
        self.assertEqual(tr.split_lines("短い"), ["短い"])
        self.assertEqual(tr.split_lines("これは長い文です、ここで区切ると読みやすくなります", 14), ["これは長い文です、", "ここで区切ると読みやすくなります"])
        self.assertEqual(len(tr.split_lines("あ" * 50, 18)), 2)

    def test_to_srt(self):
        srt = tr.to_srt([{"start": 0, "end": 1.5, "text": "こんにちは"}, {"start": 1.5, "end": 3, "text": "  "}, {"start": 3, "end": 4, "text": "またね"}])
        self.assertEqual(srt, "1\n00:00:00,000 --> 00:00:01,500\nこんにちは\n\n2\n00:00:03,000 --> 00:00:04,000\nまたね\n")

    def test_shift_segments_follows_the_cut(self):
        segs = [{"start": 0.5, "end": 1.5, "text": "a"}, {"start": 2.2, "end": 2.8, "text": "消えた所"}, {"start": 3.5, "end": 4.5, "text": "b"}]
        keep = [(0.0, 2.0, 0.0), (3.0, 5.0, 2.0)]
        self.assertEqual(tr.shift_segments(segs, keep), [{"start": 0.5, "end": 1.5, "text": "a"}, {"start": 2.5, "end": 3.5, "text": "b"}])


if __name__ == "__main__":
    unittest.main()

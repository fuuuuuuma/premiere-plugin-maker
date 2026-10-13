import array
import math
import shutil
import subprocess
import sys
import unittest

from helpers import PARTS, temp_dir

sys.path.insert(0, str(PARTS / "media-tools" / "server"))
import ppm_media  # noqa: E402


class MediaToolsTests(unittest.TestCase):
    def test_rms_db_silence_and_full_scale(self):
        silence = array.array("h", [0] * 1600)
        self.assertEqual(ppm_media.rms_db(silence, 800), [-120.0, -120.0])
        tone = array.array("h", [int(32767 * math.sin(2 * math.pi * 440 * i / 16000)) for i in range(1600)])
        for v in ppm_media.rms_db(tone, 800):
            self.assertAlmostEqual(v, -3.0, delta=0.2)

    def test_find_tool_checks_that_it_runs(self):
        ok = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, "ffmpeg version", "")
        broken = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, "", "bad")
        self.assertEqual(ppm_media.find_tool("ffmpeg", which=lambda n: "/x/ffmpeg", run=ok, extra=[]), "/x/ffmpeg")
        self.assertIsNone(ppm_media.find_tool("ffmpeg", which=lambda n: "/x/ffmpeg", run=broken, extra=[]))

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg が無い")
    def test_extract_and_probe_with_real_ffmpeg(self):
        wav = temp_dir() / "音 テスト.wav"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=1", str(wav)], check=True)
        self.assertAlmostEqual(ppm_media.probe_duration(wav), 1.0, delta=0.05)
        pcm = ppm_media.extract_pcm16(wav, rate=16000)
        self.assertAlmostEqual(len(pcm) / 2, 16000, delta=200)


if __name__ == "__main__":
    unittest.main()

import importlib.util
import shutil
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET

from helpers import PARTS, temp_dir
from server_helpers import LiveServer, make_server_dir
from xml_fixtures import write_wav, write_xmeml

VENDOR = PARTS / "silence-cut" / "server" / "vendor" / "silence_cut.py"
HAS_DEPS = bool(shutil.which("ffmpeg")) and importlib.util.find_spec("numpy") is not None


def audio_ranges(xml_path):
    root = ET.parse(xml_path).getroot()
    return [(int(c.findtext("start")), int(c.findtext("end"))) for c in root.findall(".//media/audio/track/clipitem")]


@unittest.skipUnless(HAS_DEPS, "ffmpeg と numpy が要る")
class SilenceCutTests(unittest.TestCase):
    def setUp(self):
        d = temp_dir()
        self.wav = write_wav(d / "素材.wav")
        self.xml = write_xmeml(d / "元.xml", self.wav)
        self.out = d / "out"

    def run_vendor(self, *extra):
        return subprocess.run([sys.executable, str(VENDOR), str(self.xml), "--output-dir", str(self.out), *extra],
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)

    def test_cuts_the_quiet_second(self):
        proc = self.run_vendor()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        produced = list(self.out.glob("*_カット済み.xml"))
        self.assertEqual(len(produced), 1)
        ranges = audio_ranges(produced[0])
        self.assertEqual(len(ranges), 2)
        self.assertLess(ranges[-1][1], 150)

    def test_no_cut_is_exit_code_3(self):
        proc = self.run_vendor("--threshold", "-70")
        self.assertEqual(proc.returncode, 3)

    def test_job_reports_reason_for_no_cut(self):
        server = LiveServer(make_server_dir(extra_dirs=[PARTS / "silence-cut" / "server"]))
        try:
            _, start = server.call("/jobs/silence_cut", {"xmlPath": str(self.xml), "threshold": -70})
            job = server.wait_job(start["jobId"], timeout=600)
            self.assertEqual(job["status"], "error")
            self.assertIn("カットする所", job["error"]["message"])
            _, start = server.call("/jobs/silence_cut", {"xmlPath": str(self.xml)})
            job = server.wait_job(start["jobId"], timeout=600)
            self.assertEqual(job["status"], "done", job)
            self.assertTrue(job["result"]["outputXml"].endswith("_カット済み.xml"))
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()

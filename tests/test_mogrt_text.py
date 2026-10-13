import json
import sys
import unittest
import zipfile

from helpers import PARTS, temp_dir
from server_helpers import LiveServer, make_server_dir

sys.path.insert(0, str(PARTS / "mogrt-text" / "server"))
from mogrt import build_mogrt, textstyle_fb  # noqa: E402

STYLES = PARTS / "mogrt-text" / "server" / "mogrt" / "styles"
try:
    DONOR = build_mogrt.find_donor()
except build_mogrt.BuildError:
    DONOR = ""


class StyleTests(unittest.TestCase):
    def test_sample_styles_have_the_documented_keys(self):
        for path in STYLES.glob("*.json"):
            style = json.loads(path.read_text(encoding="utf-8"))
            for key in ("id", "name", "font", "size", "fill", "strokes", "position"):
                self.assertIn(key, style, f"{path.name} に {key} がありません")

    def test_transplant_route_is_gone(self):
        src = (PARTS / "mogrt-text" / "server" / "mogrt" / "build_mogrt.py").read_text(encoding="utf-8")
        self.assertNotIn("_apply_transplant_variant", src)

    def test_donor_override_by_env(self):
        import os
        fake = temp_dir() / "Basic Title.mogrt"
        fake.write_bytes(b"x")
        old = os.environ.get("PPM_MOGRT_DONOR")
        os.environ["PPM_MOGRT_DONOR"] = str(fake)
        try:
            self.assertEqual(build_mogrt.find_donor(), str(fake))
        finally:
            if old is None:
                del os.environ["PPM_MOGRT_DONOR"]
            else:
                os.environ["PPM_MOGRT_DONOR"] = old


@unittest.skipUnless(DONOR, "Premiere の中の Basic Title.mogrt が無い")
class BuildTests(unittest.TestCase):
    def test_build_and_verify(self):
        style = json.loads((STYLES / "yellow-red-white.json").read_text(encoding="utf-8"))
        out = temp_dir() / "テロップ.mogrt"
        info = build_mogrt.build(style, "まさかの大逆転！", str(out), duration=3.0)
        self.assertTrue(build_mogrt.verify(str(out))["ok"])
        self.assertAlmostEqual(info["durationSeconds"], 3.0, places=3)
        with zipfile.ZipFile(out) as z:
            self.assertIn("definition.json", z.namelist())

    def test_job_builds_one_per_item(self):
        server = LiveServer(make_server_dir(extra_dirs=[PARTS / "mogrt-text" / "server"]))
        try:
            _, start = server.call("/jobs/build_mogrt", {"styleName": "white-black", "items": [{"text": "一つ目", "duration": 2}, {"text": "二つ目", "duration": 1.5}]})
            job = server.wait_job(start["jobId"], timeout=120)
            self.assertEqual(job["status"], "done", job)
            self.assertEqual([m["text"] for m in job["result"]["mogrts"]], ["一つ目", "二つ目"])
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()

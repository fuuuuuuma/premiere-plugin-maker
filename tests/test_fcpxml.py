import sys
import unittest
import xml.etree.ElementTree as ET

from helpers import PARTS, temp_dir
from server_helpers import LiveServer, make_server_dir
from xml_fixtures import file_url, write_wav, write_xmeml

sys.path.insert(0, str(PARTS / "fcpxml" / "server"))
import ppm_fcpxml as fx  # noqa: E402


class FcpXmlTests(unittest.TestCase):
    def setUp(self):
        d = temp_dir()
        self.wav = write_wav(d / "素材 1.wav")
        self.xml = write_xmeml(d / "seq.xml", self.wav, graphic_texts=["こんにちは", "まさかの大逆転！"])

    def test_load_reads_sequence_rate_not_first_rate_in_document(self):
        root = fx.load(self.xml).getroot()
        seq = fx.main_sequence(root)
        self.assertEqual(fx.rate_of(seq), (30, False))

    def test_only_first_reference_has_the_definition(self):
        root = fx.load(self.xml).getroot()
        self.assertEqual(set(fx.definitions(root)), {"file-1", "gfile-0", "gfile-1"})
        self.assertEqual(fx.dangling(root), [])

    def test_dangling_reference_is_detected_and_fixed(self):
        root = fx.load(self.xml).getroot()
        video_clip = root.find(".//video/track/clipitem")
        video_clip.remove(video_clip.find("file"))
        ET.SubElement(video_clip, "file", {"id": "file-1"})
        audio_file = root.find(".//audio/track/clipitem/file")
        ET.SubElement(audio_file, "name").text = "src"
        self.assertEqual(fx.dangling(root), ["file-1"])
        self.assertEqual(fx.ensure_first_definition(root), 2)
        self.assertEqual(fx.dangling(root), [])
        self.assertTrue(fx.is_definition(root.find(".//video/track/clipitem/file")))
        self.assertFalse(fx.is_definition(root.find(".//audio/track/clipitem/file")))

    def test_time_conversion_uses_declared_timebase(self):
        self.assertEqual(fx.seconds_to_frames(10, 30, True), 300)
        self.assertAlmostEqual(fx.frames_to_seconds(300, 30, True), 10.01, places=2)
        self.assertEqual(fx.ticks_per_frame(30, False), 8467200000)
        self.assertEqual(fx.ticks_per_frame(30, True), 8475667200)
        self.assertEqual(fx.seconds_to_frames(1, 24, True), 24)

    def test_clip_text_and_find_clip(self):
        seq = fx.main_sequence(fx.load(self.xml).getroot())
        second = fx.find_clip(seq, "video", 1, 75)
        self.assertEqual(fx.clip_text(second), "まさかの大逆転！")
        self.assertIsNone(fx.clip_text(fx.find_clip(seq, "video", 0, 0)))

    def test_media_path_mac_and_windows(self):
        el = ET.fromstring(f"<file><pathurl>{file_url(self.wav)}</pathurl></file>")
        self.assertEqual(fx.media_path(el).replace("\\", "/"), str(self.wav.resolve()).replace("\\", "/"))
        win = ET.fromstring("<file><pathurl>file://localhost/C%3a/Users/%E5%B1%B1%E7%94%B0/a%20b.mov</pathurl></file>")
        self.assertEqual(fx.media_path(win), "C:/" + "Users/山田/a b.mov")

    def test_load_rejects_entities_and_other_xml(self):
        bad = temp_dir() / "bad.xml"
        bad.write_text('<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "b">]><xmeml/>', encoding="utf-8")
        with self.assertRaises(fx.XmlError):
            fx.load(bad)
        other = temp_dir() / "other.xml"
        other.write_text("<project/>", encoding="utf-8")
        with self.assertRaises(fx.XmlError):
            fx.load(other)

    def test_save_keeps_doctype(self):
        out = temp_dir() / "out.xml"
        fx.save(fx.load(self.xml), out)
        self.assertTrue(out.read_text(encoding="utf-8").startswith('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>'))

    def test_read_texts_job_through_the_server(self):
        server = LiveServer(make_server_dir(extra_dirs=[PARTS / "fcpxml" / "server"]))
        try:
            tpf = fx.ticks_per_frame(30, False)
            # 2 つ目はクリップの始まりではない位置（30 フレーム目）なので、本文は None になる
            _, start = server.call("/jobs/read_texts", {"xmlPath": str(self.xml), "clips": [{"trackIndex": 1, "startTicks": 75 * tpf}, {"trackIndex": 1, "startTicks": 30 * tpf}]})
            job = server.wait_job(start["jobId"])
            self.assertEqual(job["status"], "done", job)
            self.assertEqual([t["text"] for t in job["result"]["texts"]], ["まさかの大逆転！", None])
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()

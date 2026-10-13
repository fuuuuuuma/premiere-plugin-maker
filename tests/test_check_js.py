import copy
import unittest

from check_helpers import GOOD_MANIFEST, findings, make_project, rules


def js(code, manifest=None):
    return make_project({"index.js": code + "\nif (document.readyState === 'loading') {} else { boot(); }\n"}, manifest=manifest)


def with_perm(**perms):
    data = copy.deepcopy(GOOD_MANIFEST)
    data["requiredPermissions"].update(perms)
    return data


class JsRuleTests(unittest.TestCase):
    def test_j001_await_inside_transaction(self):
        bad = "project.lockedAccess(() => { project.executeTransaction(async (ca) => { await x(); }, 'u'); });"
        self.assertIn("J001", rules(js(bad)))
        ok = "const v = await x();\nproject.lockedAccess(() => { project.executeTransaction((ca) => { ca.addAction(v); }, 'u'); });"
        self.assertNotIn("J001", rules(js(ok)))

    def test_j002_action_outside_transaction(self):
        bad = "const a = clip.createSetEndAction(t);\nproject.lockedAccess(() => { const ok = project.executeTransaction((ca) => { ca.addAction(a); }, 'u'); });"
        self.assertIn("J002", rules(js(bad)))
        builder = "// ppm: action-builder\nfunction acts(add, c, t) { add('e', () => c.createSetEndAction(t)); }"
        self.assertNotIn("J002", rules(js(builder)))

    def test_j003_get_track_items_without_args(self):
        self.assertIn("J003", rules(js("const items = await track.getTrackItems();")))
        self.assertNotIn("J003", rules(js("const items = await sel.getTrackItems();")))
        self.assertNotIn("J003", rules(js("const items = await track.getTrackItems(1, false);")))

    def test_j004_new_track_item_selection(self):
        self.assertIn("J004", rules(js("const s = new ppro.TrackItemSelection();")))

    def test_j005_frame_rate_property(self):
        self.assertIn("J005", rules(js("const fps = settings.videoFrameRate;")))
        self.assertNotIn("J005", rules(js("const fr = await settings.getVideoFrameRate(); // ppm-ignore: J014")))

    def test_j006_relative_require(self):
        self.assertIn("J006", rules(js("const u = require('./util.js');")))

    def test_j007_mutation_observer_guard(self):
        self.assertIn("J007", rules(js("new MutationObserver(() => {});")))
        self.assertNotIn("J007", rules(js("if (typeof MutationObserver === 'function') { new MutationObserver(() => {}); }")))

    def test_j008_alerts(self):
        self.assertIn("J008", rules(js("confirm('消しますか');")))
        self.assertNotIn("J008", rules(js("PPM.ui.confirm('x');")))

    def test_j009_unchecked_transaction(self):
        self.assertIn("J009", rules(js("project.lockedAccess(() => {\n  project.executeTransaction((ca) => { ca.addAction(a); }, 'u');\n});")))
        self.assertNotIn("J009", rules(js("project.lockedAccess(() => {\n  ok = project.executeTransaction((ca) => { ca.addAction(a); }, 'u');\n});")))

    def test_j010_ticks_direct_read(self):
        self.assertIn("J010", rules(js("const t = start.ticks;")))
        self.assertNotIn("J010", rules(js("const t = ppro.TickTime.createWithTicks('1'); const n = start.ticksNumber;")))

    def test_j011_eval_needs_permission(self):
        self.assertIn("J011", rules(js("eval('1');")))
        self.assertNotIn("J011", rules(js("eval('1');", manifest=with_perm(allowCodeGenerationFromStrings=True))))

    def test_j012_boot_not_at_end(self):
        code = "if (document.readyState === 'loading') {} else { boot(); }\n" + "\n".join(f"const v{i} = {i};" for i in range(30))
        root = make_project({"index.js": code})
        self.assertIn("J012", rules(root))

    def test_j013_loopback_needs_network_all(self):
        code = "const r = await fetch('http://127.0.0.1:3850/ping');"
        self.assertIn("J013", rules(js(code)))
        self.assertNotIn("J013", rules(js(code, manifest=with_perm(network={"domains": "all"}))))

    def test_j014_api_newer_than_min_version(self):
        code = "const ok = await ppro.ProjectConverter.exportAsFinalCutProXML(seq, p, true);"
        self.assertIn("J014", rules(js(code)))
        data = copy.deepcopy(GOOD_MANIFEST)
        data["host"]["minVersion"] = "26.2"
        self.assertNotIn("J014", rules(js(code, manifest=data)))
        beta = [f for f in findings(js("editor.createRazorTrackAction(a);")) if f.rule == "J014"]
        self.assertEqual(beta[0].severity, "warn")

    def test_j015_media_type_compare(self):
        self.assertIn("J015", rules(js("if ((await item.getMediaType()) === 1) {}")))

    def test_m010_m011_m012_permission_use(self):
        self.assertIn("M010", rules(js("const a = 1;", manifest=with_perm(localFileSystem="fullAccess"))))
        self.assertNotIn("M010", rules(js("const fs = require('fs');", manifest=with_perm(localFileSystem="fullAccess"))))
        self.assertIn("M011", rules(js("const r = await fetch('https://example.com');")))
        self.assertIn("M011", rules(js("const a = 1;", manifest=with_perm(network={"domains": "all"}))))
        self.assertIn("M012", rules(js("const a = 1;", manifest=with_perm(allowCodeGenerationFromStrings=True))))

    def test_ignore_comment(self):
        self.assertNotIn("J010", rules(js("const t = start.ticks; // ppm-ignore: J010")))

    def test_cep_and_server_js_are_not_checked_as_panel(self):
        root = make_project({"cep/client/main.js": "var t = start.ticks; confirm('x');"})
        self.assertFalse({"J010", "J008"} & rules(root))


if __name__ == "__main__":
    unittest.main()

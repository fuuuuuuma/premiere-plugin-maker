import plistlib
import unittest
from pathlib import Path

from helpers import temp_dir
from lib import osinfo


def make_mac_app(root: Path, folder: str, app: str, version: str) -> None:
    contents = root / folder / app / "Contents"
    contents.mkdir(parents=True)
    with open(contents / "Info.plist", "wb") as f:
        plistlib.dump({"CFBundleShortVersionString": version}, f)


class DetectOsTests(unittest.TestCase):
    def test_platform_names(self):
        self.assertEqual(osinfo.detect_os("darwin"), "mac")
        self.assertEqual(osinfo.detect_os("win32"), "windows")
        self.assertEqual(osinfo.detect_os("cygwin"), "windows")
        self.assertEqual(osinfo.detect_os("linux"), "linux")


class MacPathTests(unittest.TestCase):
    def setUp(self):
        self.root = temp_dir()
        self.env = {"HOME": str(self.root / "home 山田"), "PPM_APPLICATIONS": str(self.root / "Applications"),
                    "PPM_SYSTEM_LIBRARY": str(self.root / "Library")}

    def test_home_and_kit_dirs_keep_spaces_and_japanese(self):
        self.assertEqual(osinfo.kit_home(self.env, "mac"), Path(self.env["HOME"]) / ".premiere-plugin-maker")
        self.assertEqual(osinfo.default_projects_dir(self.env, "mac"), Path(self.env["HOME"]) / "PremierePlugins")
        self.assertEqual(osinfo.notes_dir(self.env, "mac"), Path(self.env["HOME"]) / ".premiere-plugin-maker" / "notes")

    def test_premiere_installs_lists_release_and_beta_newest_first(self):
        apps = Path(self.env["PPM_APPLICATIONS"])
        make_mac_app(apps, "Adobe Premiere Pro 2025", "Adobe Premiere Pro 2025.app", "25.6.4")
        make_mac_app(apps, "Adobe Premiere Pro 2026", "Adobe Premiere Pro 2026.app", "26.5.2")
        make_mac_app(apps, "Adobe Premiere Pro (Beta)", "Adobe Premiere Pro (Beta).app", "27.1.0")
        found = osinfo.premiere_installs(self.env, "mac")
        self.assertEqual([f.version for f in found], ["27.1.0", "26.5.2", "25.6.4"])
        self.assertEqual([f.beta for f in found], [True, False, False])

    def test_no_premiere_returns_empty_list(self):
        self.assertEqual(osinfo.premiere_installs(self.env, "mac"), [])

    def test_upia_and_udt_settings(self):
        self.assertEqual(
            osinfo.upia_path(self.env, "mac"),
            Path(self.env["PPM_SYSTEM_LIBRARY"]) / "Application Support/Adobe/Adobe Desktop Common/RemoteComponents/UPI/UnifiedPluginInstallerAgent/UnifiedPluginInstallerAgent.app/Contents/MacOS/UnifiedPluginInstallerAgent",
        )
        self.assertEqual(osinfo.udt_settings_file(self.env, "mac"),
                         Path(self.env["PPM_SYSTEM_LIBRARY"]) / "Application Support/Adobe/UXP/Developer/settings.json")

    def test_uxp_log_dirs_newest_first_and_only_existing(self):
        logs = Path(self.env["HOME"]) / "Library/Logs/Adobe"
        (logs / "Adobe Premiere Pro 2024").mkdir(parents=True)
        (logs / "Adobe Premiere Pro 2026").mkdir(parents=True)
        (logs / "Adobe Premiere Pro (Beta)").mkdir(parents=True)
        names = [p.name for p in osinfo.uxp_log_dirs(self.env, "mac")]
        self.assertEqual(names, ["Adobe Premiere Pro (Beta)", "Adobe Premiere Pro 2026", "Adobe Premiere Pro 2024"])


class WindowsPathTests(unittest.TestCase):
    """Windows の場所は環境変数から組み立てる。Mac の上でも POSIX のパスを入れて試せる。"""

    def setUp(self):
        self.root = temp_dir()
        self.env = {
            "USERPROFILE": str(self.root / "Users" / "山田 太郎"),
            "APPDATA": str(self.root / "Users" / "山田 太郎" / "AppData" / "Roaming"),
            "LOCALAPPDATA": str(self.root / "Users" / "山田 太郎" / "AppData" / "Local"),
            "ProgramFiles": str(self.root / "Program Files"),
            "CommonProgramFiles": str(self.root / "Program Files" / "Common Files"),
        }

    def test_kit_home_uses_userprofile(self):
        self.assertEqual(osinfo.kit_home(self.env, "windows"), Path(self.env["USERPROFILE"]) / ".premiere-plugin-maker")

    def test_upia_path(self):
        self.assertEqual(
            osinfo.upia_path(self.env, "windows"),
            Path(self.env["CommonProgramFiles"]) / "Adobe/Adobe Desktop Common/RemoteComponents/UPI/UnifiedPluginInstallerAgent/UnifiedPluginInstallerAgent.exe",
        )

    def test_udt_settings_file(self):
        self.assertEqual(osinfo.udt_settings_file(self.env, "windows"),
                         Path(self.env["CommonProgramFiles"]) / "Adobe/UXP/Developer/settings.json")

    def test_premiere_installs_on_windows_uses_injected_version_reader(self):
        (Path(self.env["ProgramFiles"]) / "Adobe" / "Adobe Premiere Pro 2026").mkdir(parents=True)
        found = osinfo.premiere_installs(self.env, "windows", read_version=lambda os_name, path: "26.5.2")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].name, "Adobe Premiere Pro 2026")
        self.assertEqual(found[0].version, "26.5.2")

    def test_windows_version_falls_back_to_year_in_folder_name(self):
        (Path(self.env["ProgramFiles"]) / "Adobe" / "Adobe Premiere Pro 2026").mkdir(parents=True)
        found = osinfo.premiere_installs(self.env, "windows", read_version=lambda os_name, path: "")
        self.assertEqual(found[0].version, "26.x")

    def test_plugin_storage_and_cep_dirs(self):
        roots = osinfo.plugin_storage_roots(self.env, "windows")
        self.assertIn(Path(self.env["APPDATA"]) / "Adobe/UXP/PluginsStorage", roots)
        self.assertEqual(osinfo.cep_extensions_dir(self.env, "windows"), Path(self.env["APPDATA"]) / "Adobe/CEP/extensions")
        self.assertEqual(osinfo.adobe_fonts_dir(self.env, "windows"), Path(self.env["APPDATA"]) / "Adobe/CoreSync/plugins/livetype")

    def test_python_command(self):
        self.assertEqual(osinfo.python_command("windows"), "py -3")
        self.assertEqual(osinfo.python_command("mac"), "python3")


if __name__ == "__main__":
    unittest.main()

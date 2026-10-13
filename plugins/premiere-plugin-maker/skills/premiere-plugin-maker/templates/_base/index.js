/* {{PLUGIN_NAME}} — パネルの本体。
 * 部品（lib/ の PPM.*）は index.html の <script> で先に読み込まれている。require の相対パスは使わない。
 * 起動の処理はこのファイルの末尾で 1 回だけ行う（UXP は読み込みの途中で起動することがあり、
 * 途中で起動すると、後ろで宣言した const を踏んで止まるため）。 */
"use strict";

let ppro = null;
let uxp = null;
try {
  uxp = require("uxp");
  ppro = require("premierepro");
} catch (e) {
  // Premiere の外（下見など）では、画面だけ動かす
}

const APP = { tag: "{{LOG_TAG}}", booted: false };

function $(id) { return document.getElementById(id); }

async function onRun() {
  const out = $("result");
  PPM.ui.busy($("run"), true, "処理中…");
  try {
    const { sequence } = await PPM.getProjectAndSequence();
    const clips = await PPM.getSelectedClips(sequence);
    if (clips.length === 0) {
      throw PPM.err("クリップが選ばれていません", "この操作は選んだクリップに対して行います", "タイムラインでクリップを選んでから、もう一度押してください");
    }
    // ここに、このプラグインの処理を書く（knowledge/core/core-api-patterns.md の型に合わせる）
    PPM.ui.showOk(out, `${clips.length} 本のクリップを確認しました`);
    PPM.log.info("run ok", { count: clips.length });
  } catch (e) {
    PPM.ui.showError(out, e);
    PPM.log.error("run failed", { message: String((e && e.message) || e) });
  } finally {
    PPM.ui.busy($("run"), false);
  }
}

async function showVersion() {
  try {
    const folder = await uxp.storage.localFileSystem.getPluginFolder();
    const entry = await folder.getEntry("build_info.json");
    const info = JSON.parse(await entry.read({ format: uxp.storage.formats.utf8 }));
    $("version").textContent = `v${info.version}`;
  } catch (e) {
    $("version").textContent = "";
  }
}

function boot() {
  if (APP.booted) return;
  APP.booted = true;
  PPM.init({ ppro, uxp, tag: APP.tag });
  $("run").addEventListener("click", onRun);
  $("probe").addEventListener("click", () => { PPM.probe.runAndShow($("result")); });
  showVersion();
  PPM.log.info("boot", PPM.hostInfo());
}

if (uxp && uxp.entrypoints && typeof uxp.entrypoints.setup === "function") {
  const commands = PPM.commands ? (PPM.commands.define("runMain", onRun), PPM.commands.table()) : {};
  try {
    uxp.entrypoints.setup({
      panels: { "{{PANEL_ID}}": { create() {}, show() {}, hide() {}, destroy() {} } },
      commands,
    });
  } catch (e) {
    // 2 回目の setup は失敗するので無視する
  }
}

// ここから下は動かさない（起動はファイルの末尾で 1 回だけ）
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}

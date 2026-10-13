/* Silence Cut — パネルの本体。
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

const APP = { tag: "silence-cut", booted: false };

function $(id) { return document.getElementById(id); }

async function onRun() {
  const out = $("result");
  PPM.ui.busy($("run"), true, "カットしています…");
  try {
    await PPM.server.connect({ tries: 2, intervalMs: 1000 });
    PPM.ui.showInfo(out, "シーケンスを書き出しています…");
    const xmlPath = await PPM.fcpxml.exportActiveSequence(`ppm-cut-${Date.now()}.xml`);
    const result = await PPM.server.runJob("silence_cut", {
      xmlPath,
      threshold: PPM.ui.numberValue($("threshold"), -48),
      minSilence: PPM.ui.numberValue($("minSilence"), 0.2),
      padding: Math.round(PPM.ui.numberValue($("padding"), 2)),
    }, { onProgress: (p, m) => PPM.ui.showInfo(out, `${m || "処理中"}（${p}%）`) });
    const seq = await PPM.fcpxml.importAndOpen(result.outputXml);
    PPM.ui.showOk(out, `カットした新しいシーケンス「${seq && seq.name ? seq.name : ""}」を開きました（元のシーケンスはそのままです）`);
    PPM.log.info("cut ok", { output: result.outputXml });
  } catch (e) {
    PPM.ui.showError(out, e);
    PPM.log.error("cut failed", { message: String((e && e.message) || e) });
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
      panels: { "mainPanel": { create() {}, show() {}, hide() {}, destroy() {} } },
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

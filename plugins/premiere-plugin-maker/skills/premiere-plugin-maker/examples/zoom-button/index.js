/* Zoom Button — パネルの本体。
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

const APP = { tag: "zoom-button", booted: false };

function $(id) { return document.getElementById(id); }

async function onRun() {
  const out = $("result");
  PPM.ui.busy($("run"), true, "付けています…");
  try {
    const { project, sequence } = await PPM.getProjectAndSequence();
    const clips = (await PPM.getSelectedClips(sequence)).filter((c) => c.kind === "video");
    if (clips.length === 0) {
      throw PPM.err("映像のクリップが選ばれていません", "ズームは映像のクリップに付けます", "タイムラインで映像のクリップを選んでから、もう一度押してください");
    }
    const from = PPM.ui.numberValue($("from"), 100);
    const to = PPM.ui.numberValue($("to"), 110);
    const seconds = Math.max(0.1, PPM.ui.numberValue($("seconds"), 2));
    const fr = await PPM.getFrameRate(sequence);
    if (!fr.detected) PPM.log.warn("フレームレートを読めないので 30 コマで焼きます", {});
    const frame = 1 / (fr.detected ? fr.fps : 30);
    const keys = PPM.motion.bakeTrack([{ t: 0, value: from, interp: "bezier" }, { t: seconds, value: to, interp: "linear" }], frame);
    // 非同期の取得（スケールの項目・入点）は取引の前に全部済ませる
    const targets = [];
    for (const c of clips) {
      const found = await PPM.findParam(c.item, ["AE.ADBE Motion"], ["Scale", "スケール"]);
      if (!found) { PPM.log.warn("スケールが見つかりません", { name: c.name }); continue; }
      targets.push({ param: found.param, inPoint: PPM.secondsOf(await c.item.getInPoint()) });
    }
    if (targets.length === 0) {
      throw PPM.err("スケールの項目が見つかりません", "モーションの「スケール」を探せませんでした", "診断を押して、表示を AI に伝えてください");
    }
    const result = PPM.transact(project, "ゆっくりズームを付ける", (add) => {
      for (const t of targets) PPM.keyframeActions(add, t.param, t.inPoint, keys);
    });
    PPM.ui.showOk(out, `${targets.length} 本に付けました（取り消しは Cmd+Z / Ctrl+Z を 1 回）`);
    PPM.log.info("zoom ok", { clips: targets.length, keys: keys.length, warnings: result.warnings });
  } catch (e) {
    PPM.ui.showError(out, e);
    PPM.log.error("zoom failed", { message: String((e && e.message) || e) });
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

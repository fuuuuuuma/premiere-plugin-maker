/* Telop Restyle — パネルの本体。
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

const APP = { tag: "telop-restyle", booted: false };

function $(id) { return document.getElementById(id); }

async function onRun() {
  const out = $("result");
  PPM.ui.busy($("run"), true, "差し替えています…");
  try {
    const { project, sequence } = await PPM.getProjectAndSequence();
    const clips = (await PPM.getSelectedClips(sequence)).filter((c) => c.kind === "video");
    if (clips.length === 0) {
      throw PPM.err("テロップが選ばれていません", "選んだテロップの見た目を差し替えます", "タイムラインでテロップを選んでから、もう一度押してください");
    }
    await PPM.server.connect({ tries: 2, intervalMs: 1000 });
    PPM.ui.showInfo(out, "本文を読んでいます…");
    const xmlPath = await PPM.fcpxml.exportActiveSequence(`ppm-telop-${Date.now()}.xml`);
    const read = await PPM.server.runJob("read_texts", { xmlPath, clips: clips.map((c) => ({ trackIndex: c.trackIndex, startTicks: c.startTicks })) });
    const targets = clips.map((c, i) => ({ clip: c, text: read.texts[i] && read.texts[i].text })).filter((t) => t.text);
    const skipped = clips.length - targets.length;
    if (targets.length === 0) {
      throw PPM.err("本文を読めるテロップがありません", "選んだクリップがテロップ（グラフィック）ではないか、本文が空です", "テロップを選び直してください");
    }
    const built = await PPM.server.runJob("build_mogrt", {
      styleName: PPM.ui.textValue($("style")) || "white-black",
      items: targets.map((t) => ({ text: t.text, duration: t.clip.endSeconds - t.clip.startSeconds })),
    }, { onProgress: (p, m) => PPM.ui.showInfo(out, `${m || "作っています"}（${p}%）`) });
    let steps = 0;
    for (let i = 0; i < targets.length; i++) {
      try {
        const r = await PPM.mogrt.replaceClip(project, sequence, targets[i].clip, built.mogrts[i].path);
        steps += r.undoSteps;
      } catch (e) {
        const p = (e && e.ppm) || { symptom: String((e && e.message) || e), why: "", next: "" };
        // 途中で止まったときは、何本まで済んだかと、ここまでを戻す取り消しの回数を伝える
        throw PPM.err(`${i} 本まで差し替え、${i + 1} 本目で止まりました: ${p.symptom}`, p.why,
          `${p.next}${p.next ? "。" : ""}ここまでを全部戻すなら、Cmd+Z / Ctrl+Z をあと ${steps} 回`);
      }
    }
    const lines = [`${targets.length} 本を差し替えました（元に戻すには Cmd+Z / Ctrl+Z を ${steps} 回）`];
    if (skipped) lines.push(`${skipped} 本は本文を読めず、飛ばしました`);
    if (built.warnings && built.warnings.length) lines.push(...built.warnings);
    PPM.ui.showOk(out, lines.join("\n"));
    PPM.log.info("restyle ok", { replaced: targets.length, skipped, steps });
  } catch (e) {
    PPM.ui.showError(out, e);
    PPM.log.error("restyle failed", { message: String((e && e.message) || e) });
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
  PPM.ui.protectSelect($("style"));
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

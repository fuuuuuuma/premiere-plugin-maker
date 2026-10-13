/* ppm-probe — 診断ボタン。使う API が、この Premiere に本当にあるかを確かめてログに残す。
 * 公式の文書に載っていても、実装されているとは限らない。実装する前に、ここで確かめてから使う。
 * API の名前は文字列で持つ（check.py の版の検査が、名前だけの記述を誤って拾わないため）。 */
(function (root) {
  "use strict";
  const PPM = (root.PPM = root.PPM || {});
  const STATIC = [
    "Project.getActiveProject", "SequenceEditor.getEditor", "Markers.getMarkers", "Exporter.exportSequenceFrame",
    "ProjectConverter.exportAsFinalCutProXML", "VideoFilterFactory.createComponent", "TransitionFactory.createVideoTransition",
    "TickTime.createWithSeconds", "EncoderManager.getManager", "ProjectUtils.getSelection", "WorkAreaUtils",
  ];
  const LIVE = [
    "sequence.getSettings", "sequence.getSelection", "sequence.getVideoTrack", "sequence.getVideoTrackCount",
    "sequence.getPlayerPosition", "settings.getVideoFrameRate", "editor.insertMogrtFromPath",
    "editor.createOverwriteItemAction", "editor.createRazorTrackAction",
  ];

  function kindOf(obj, path) {
    try {
      let cur = obj;
      for (const key of path) {
        if (cur === null || cur === undefined) return "missing";
        cur = cur[key];
      }
      return cur === undefined ? "missing" : typeof cur;
    } catch (e) {
      return "error: " + String((e && e.message) || e);
    }
  }

  async function run(extraStatic) {
    const { ppro } = PPM.modules();
    const report = { at: new Date().toISOString(), host: PPM.hostInfo(), statics: {}, live: {}, logFile: "", notes: [] };
    for (const name of STATIC.concat(extraStatic || [])) report.statics[name] = ppro ? kindOf(ppro, name.split(".")) : "missing";
    try {
      const { project, sequence } = await PPM.getProjectAndSequence();
      const settings = await sequence.getSettings();
      const editor = await ppro.SequenceEditor.getEditor(sequence);
      const live = { project, sequence, settings, editor };
      for (const name of LIVE) {
        const parts = name.split(".");
        report.live[name] = kindOf(live[parts[0]], parts.slice(1));
      }
    } catch (e) {
      report.notes.push("シーケンスを開いてから押すと、もっと詳しく調べられます（" + String((e && e.message) || e) + "）");
    }
    report.logFile = PPM.log ? await PPM.log.filePath() : "";
    if (PPM.log) PPM.log.info("probe", report);
    return report;
  }

  async function runAndShow(el) {
    const r = await run();
    const missing = Object.keys(r.statics).filter((k) => r.statics[k] === "missing")
      .concat(Object.keys(r.live).filter((k) => r.live[k] === "missing"));
    const lines = [
      `Premiere ${r.host.version || "?"}（UXP ${r.host.uxp || "?"}・${r.host.os || "?"}）`,
      `無い API: ${missing.length ? missing.join("、") : "なし"}`,
      `ログ: ${r.logFile || "（場所を確かめられませんでした）"}`,
    ].concat(r.notes);
    if (PPM.ui) PPM.ui.showInfo(el, lines.join("\n"));
    else if (el) el.textContent = lines.join("\n");
    if (PPM.log) { try { await PPM.log.flush(); } catch (e) { /* 書けなくても表示は出す */ } }
    return r;
  }

  PPM.probe = { STATIC, LIVE, kindOf, run, runAndShow };
  if (typeof module === "object" && module && module.exports) module.exports = PPM;
})(typeof globalThis !== "undefined" ? globalThis : this);

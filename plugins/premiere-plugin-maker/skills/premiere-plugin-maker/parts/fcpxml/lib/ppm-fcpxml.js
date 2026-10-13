/* ppm-fcpxml — パネル側の FCP7 XML の往復（書き出し → サーバーで加工 → 読み込んで新しいシーケンスを開く）。
 * ProjectConverter は Premiere 26.2 から。UXP にはクリップの分割が無いので、カットは「XML を作り直して読み込む」で行う。 */
(function (root) {
  "use strict";
  const PPM = (root.PPM = root.PPM || {});

  async function exportActiveSequence(fileName) {
    const { ppro } = PPM.modules();
    const { sequence } = await PPM.getProjectAndSequence();
    const path = PPM.server.tmpPath(fileName);
    const conv = ppro && ppro.ProjectConverter;
    if (!conv || typeof conv.exportAsFinalCutProXML !== "function") {
      throw PPM.err("FCP XML を書き出せません", "この Premiere には ProjectConverter がありません（26.2 から）", "Premiere を 26.2 以降に更新してください");
    }
    const ok = await PPM.resolve(conv.exportAsFinalCutProXML(sequence, path, true));
    if (!ok) throw PPM.err("FCP XML を書き出せません", "Premiere が書き出しを受け付けませんでした", "シーケンスを開き直してから、もう一度押してください");
    return path;
  }

  async function importAndOpen(path) {
    const { project } = await PPM.getProjectAndSequence();
    const before = (await project.getSequences()) || [];
    const rootItem = await project.getRootItem();
    const ok = await PPM.resolve(project.importFiles([path], true, rootItem, false));
    const after = (await project.getSequences()) || [];
    const fresh = after.filter((s) => before.indexOf(s) < 0 && !before.some((b) => b && s && b.name === s.name && b.guid && b.guid === s.guid));
    if (!ok || after.length <= before.length || !fresh.length) {
      throw PPM.err("XML を読み込めませんでした", "新しいシーケンスが増えませんでした", `Premiere の［ファイル］→［読み込み］で ${path} を手で読み込んでください`);
    }
    const seq = fresh[fresh.length - 1];
    await project.openSequence(seq);
    if (typeof project.setActiveSequence === "function") await PPM.resolve(project.setActiveSequence(seq));
    return seq;
  }

  PPM.fcpxml = { exportActiveSequence, importAndOpen };
  if (typeof module === "object" && module && module.exports) module.exports = PPM;
})(typeof globalThis !== "undefined" ? globalThis : this);

/* ppm-mogrt — 作った MOGRT をタイムラインに入れる・テロップを差し替える。
 * - insertMogrtFromPath は Action を返さないので取引に入れられない（取り消しは別の 1 回）
 * - 同じトラックに重なると上書きされる／されないの記録が割れている → 上書きに頼らず、先に元を外してから入れる
 * - 削除の createRemoveItemsAction は引数 4 つが必須（26.3）。選択は sequence.getSelection() を使い、new TrackItemSelection は使わない */
(function (root) {
  "use strict";
  const PPM = (root.PPM = root.PPM || {});

  async function insertAt(project, sequence, path, startSeconds, videoTrackIndex, audioTrackIndex) {
    const { ppro } = PPM.modules();
    const editor = await ppro.SequenceEditor.getEditor(sequence);
    if (!editor || typeof editor.insertMogrtFromPath !== "function") {
      throw PPM.err("MOGRT を入れられません", "この Premiere には insertMogrtFromPath がありません", "Premiere を 25.6 以降に更新してください");
    }
    const r = await PPM.resolve(editor.insertMogrtFromPath(path, PPM.time(startSeconds), videoTrackIndex, audioTrackIndex || 0));
    if (!r || (Array.isArray(r) && r.length === 0)) {
      throw PPM.err("MOGRT を入れられません", "Premiere が何も返しませんでした（トラックのロックやファイルの壊れ）", "トラックのロックを外し、もう一度試してください");
    }
    return Array.isArray(r) ? r[0] : r;
  }

  async function replaceClip(project, sequence, clip, mogrtPath) {
    const { ppro } = PPM.modules();
    const editor = await ppro.SequenceEditor.getEditor(sequence);
    const live = await PPM.findClip(sequence, clip.kind, clip.trackIndex, clip.startTicks);
    if (!live) throw PPM.err("元のテロップが見つかりません", "選んだ後にタイムラインが変わりました", "テロップを選び直してから押してください");
    const sel = await sequence.getSelection();
    const current = (await PPM.resolve(sel.getTrackItems())) || [];
    for (const it of current) if (typeof sel.removeItem === "function") sel.removeItem(it);
    if (typeof sel.addItem === "function") sel.addItem(live);
    const videoType = (ppro.Constants.MediaType && (ppro.Constants.MediaType.VIDEO !== undefined ? ppro.Constants.MediaType.VIDEO : ppro.Constants.MediaType.Video));
    PPM.transact(project, "元のテロップを外す", (add) => {
      add("remove", () => editor.createRemoveItemsAction(sel, false, videoType, false));
    });
    await insertAt(project, sequence, mogrtPath, clip.startSeconds, clip.trackIndex, 0);
    let steps = 2;
    const placed = await PPM.findClip(sequence, "video", clip.trackIndex, clip.startTicks);
    if (placed) {
      const end = await placed.getEndTime();
      if (PPM.ticksOf(end) !== clip.endTicks) {
        PPM.transact(project, "長さを合わせる", (add) => { add("end", () => placed.createSetEndAction(PPM.timeFromTicks(clip.endTicks))); });
        steps += 1;
      }
    }
    return { undoSteps: steps };
  }

  PPM.mogrt = { insertAt, replaceClip };
  if (typeof module === "object" && module && module.exports) module.exports = PPM;
})(typeof globalThis !== "undefined" ? globalThis : this);

/* ppm-agent-bridge — AI（MCP）からの命令をパネルで受ける。2 秒ごとに手元のサーバーへ取りに行く。
 * 命令は register で足す。Premiere を変える命令を足すときは、取り消し 1 回で戻る作りにする（PPM.transact）。 */
(function (root) {
  "use strict";
  const PPM = (root.PPM = root.PPM || {});
  const handlers = {};
  const state = { timer: null, busy: false };

  function register(name, description, handler) { handlers[name] = { description, handler }; }

  function list() { return Object.keys(handlers).map((name) => ({ name, description: handlers[name].description })); }

  async function pollOnce() {
    if (state.busy) return;
    state.busy = true;
    try {
      const next = await PPM.server.call("/panel/next", { method: "POST", body: { commands: list() } });
      const cmd = next && next.command;
      if (!cmd) return;
      let body;
      try {
        const h = handlers[cmd.name];
        if (!h) throw new Error(`知らない命令: ${cmd.name}`);
        body = { id: cmd.id, ok: true, result: await h.handler(cmd.args || {}) };
      } catch (e) {
        body = { id: cmd.id, ok: false, error: e && e.ppm ? `${e.ppm.symptom}（${e.ppm.why}）` : String((e && e.message) || e) };
      }
      await PPM.server.call("/panel/result", { method: "POST", body });
    } finally {
      state.busy = false;
    }
  }

  function start(opts) {
    const ms = (opts && opts.intervalMs) || 2000;
    if (state.timer) return;
    const tick = () => { pollOnce().catch(() => {}).then(() => { state.timer = setTimeout(tick, ms); }); };
    tick();
  }

  function stop() { if (state.timer) clearTimeout(state.timer); state.timer = null; }

  register("probe", "診断（使える API・Premiere の版・ログの場所）", () => PPM.probe.run());
  register("get_selection", "選んだクリップ（名前・トラック・開始と終了の秒）", async () => {
    const { sequence } = await PPM.getProjectAndSequence();
    const clips = await PPM.getSelectedClips(sequence);
    return { count: clips.length, clips: clips.map((c) => ({ name: c.name, trackIndex: c.trackIndex, kind: c.kind, start: c.startSeconds, end: c.endSeconds })) };
  });
  register("sequence_overview", "シーケンスの映像トラックとクリップの一覧", async () => {
    const { sequence } = await PPM.getProjectAndSequence();
    const count = await PPM.resolve(sequence.getVideoTrackCount());
    const tracks = [];
    for (let i = 0; i < count; i++) {
      const items = await PPM.listTrackClips(sequence, "video", i);
      const clips = [];
      for (const it of items) clips.push(await PPM.describeClip(it));
      tracks.push({ index: i, clips: clips.map((c) => ({ name: c.name, start: c.startSeconds, end: c.endSeconds })) });
    }
    return { videoTracks: tracks };
  });
  register("log_tail", "パネルのログの最後の 50 行", async () => ({ lines: PPM.log ? PPM.log.lines().slice(-50) : [] }));

  PPM.agent = { register, list, pollOnce, start, stop };
  if (typeof module === "object" && module && module.exports) module.exports = PPM;
})(typeof globalThis !== "undefined" ? globalThis : this);

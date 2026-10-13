/* ppm-server-client — パネルから手元のサーバーを呼ぶ。
 * - 合言葉は server.json から読む（サーバーを起動し直すと変わるので、403 なら読み直して 1 回だけやり直す）
 * - ジョブは「始める → 状態を見に行く」。最初の 5 回は 0.3 秒、その後 1.5 秒ごと。通信が 3 回続けて切れたら諦める
 * - 127.0.0.1 へつなぐには manifest の network.domains が "all" であること（個別の許可では通信が起きなかった） */
(function (root) {
  "use strict";
  const PPM = (root.PPM = root.PPM || {});
  const APP = "SilenceCut";
  const PROTOCOL = 1;
  const state = { handshake: null };

  function handshakePath() {
    const os = require("os");
    const home = os.homedir();
    if (os.platform() === "win32") return `${home}\\AppData\\Roaming\\${APP}\\server.json`;
    return `${home}/Library/Application Support/${APP}/server.json`;
  }

  async function readHandshake() {
    const fs = require("fs");
    let raw;
    try {
      raw = await fs.readFile(handshakePath(), { encoding: "utf-8" });
    } catch (e) {
      throw PPM.err("サーバーが動いていません", "server.json が見つかりません（まだ入れていないか、止まっています）",
        "作業フォルダの server の install（Mac は install_mac.command、Windows は install_windows.bat）を実行してから、パネルを開き直してください");
    }
    const h = JSON.parse(raw);
    if (!h.token || !h.httpPort) throw PPM.err("サーバーの情報が壊れています", "server.json に合言葉かポートがありません", "サーバーを入れ直してください");
    if (Number(h.protocol) !== PROTOCOL) {
      throw PPM.err("パネルとサーバーの版が合いません", `サーバーの約束の番号が ${h.protocol}（パネルは ${PROTOCOL}）です`, "パネルとサーバーを同じ版で入れ直してください");
    }
    state.handshake = h;
    return h;
  }

  async function call(path, opts, retried) {
    const o = opts || {};
    if (!state.handshake) await readHandshake();
    const h = state.handshake;
    const res = await fetch(`http://127.0.0.1:${h.httpPort}${path}`, {
      method: o.method || "GET",
      headers: { "Content-Type": "application/json", "X-PPM-Token": h.token },
      body: o.body ? JSON.stringify(o.body) : undefined,
    });
    if (res.status === 403 && !retried) {
      await readHandshake();
      return call(path, o, true);
    }
    let data = {};
    try { data = await res.json(); } catch (e) { data = {}; }
    if (res.status >= 400) {
      throw PPM.err(data.error || `サーバーがエラーを返しました（${res.status}）`, data.why || "", data.next || "パネルを開き直してから、もう一度試してください");
    }
    return data;
  }

  async function connect(opts) {
    const o = opts || {};
    const tries = o.tries || 5;
    let last = null;
    for (let i = 0; i < tries; i++) {
      try {
        await readHandshake();
        await call("/ping");
        return state.handshake;
      } catch (e) {
        last = e;
        if (i < tries - 1) await new Promise((r) => setTimeout(r, o.intervalMs === undefined ? 4000 : o.intervalMs));
      }
    }
    throw last;
  }

  async function runJob(kind, params, opts) {
    const o = opts || {};
    const start = await call(`/jobs/${kind}`, { method: "POST", body: params || {} });
    let polls = 0;
    let failures = 0;
    for (;;) {
      await new Promise((r) => setTimeout(r, polls < 5 ? (o.fastMs || 300) : (o.slowMs || 1500)));
      polls += 1;
      let job;
      try {
        job = await call(`/jobs/${start.jobId}`);
        failures = 0;
      } catch (e) {
        failures += 1;
        if (failures >= 3) throw e;
        continue;
      }
      if (o.onProgress) o.onProgress(job.percent || 0, job.message || "");
      if (job.status === "done") return job.result;
      if (job.status === "cancelled") throw PPM.err("処理を止めました", "途中で止めたので、結果はありません", "必要なら、もう一度実行してください");
      if (job.status === "error") {
        const e = job.error || {};
        throw PPM.err(e.message || "サーバーの処理が失敗しました", e.why || "", e.next || "");
      }
    }
  }

  function tmpPath(name) {
    if (!state.handshake) throw PPM.err("サーバーにつながっていません", "まだ connect していません", "先に PPM.server.connect() を呼んでください");
    return PPM.joinPath(state.handshake.tmpDir, name);
  }

  PPM.server = { connect, call, runJob, tmpPath, handshakePath, readHandshake };
  if (typeof module === "object" && module && module.exports) module.exports = PPM;
})(typeof globalThis !== "undefined" ? globalThis : this);

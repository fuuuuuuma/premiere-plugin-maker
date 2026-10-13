/* ppm-logger — パネルのログを 2 か所に書く。
 *  1) console.log（Mac では Premiere の UXP ログ UXPLogs_*.log に出る）
 *  2) プラグインのデータフォルダの ppm-log.txt（Windows でも場所が決まる。AI は logs.py で読む）
 * ファイルへは最後の maxLines 行を 0.3 秒ごとにまとめて書き直す（追記の作法に頼らない）。 */
(function (root) {
  "use strict";
  const PPM = (root.PPM = root.PPM || {});
  const state = { uxp: null, tag: "ppm", fileName: "ppm-log.txt", maxLines: 500, lines: [], timer: null, folder: null, path: "" };

  function safeJson(data) {
    if (data === undefined) return "";
    try { return " " + JSON.stringify(data); } catch (e) { return " [文字にできないデータ]"; }
  }

  function write(level, msg, data) {
    const line = `${new Date().toISOString()} [${state.tag}] ${level} ${msg}${safeJson(data)}`;
    try { console.log(line); } catch (e) { /* 出せなくても続ける */ }
    state.lines.push(line);
    if (state.lines.length > state.maxLines) state.lines.splice(0, state.lines.length - state.maxLines);
    schedule();
    return line;
  }

  function schedule() {
    if (state.timer || !state.uxp) return;
    state.timer = setTimeout(() => { state.timer = null; flush().catch(() => {}); }, 300);
  }

  async function dataFolder() {
    if (state.folder) return state.folder;
    const lfs = state.uxp && state.uxp.storage && state.uxp.storage.localFileSystem;
    if (!lfs || typeof lfs.getDataFolder !== "function") return null;
    state.folder = await lfs.getDataFolder();
    return state.folder;
  }

  async function flush() {
    const folder = await dataFolder();
    if (!folder) return false;
    const file = await folder.createFile(state.fileName, { overwrite: true });
    const formats = state.uxp.storage.formats;
    await file.write(state.lines.join("\n") + "\n", formats ? { format: formats.utf8 } : undefined);
    state.path = file.nativePath || "";
    return true;
  }

  async function filePath() {
    if (state.path) return state.path;
    let folder = null;
    try { folder = await dataFolder(); } catch (e) { folder = null; }
    if (!folder || !folder.nativePath) return "";
    const sep = String(folder.nativePath).indexOf("\\") >= 0 ? "\\" : "/";
    return folder.nativePath + sep + state.fileName;
  }

  PPM.log = {
    init(opts) {
      const o = opts || {};
      state.uxp = o.uxp || null;
      if (o.tag) state.tag = o.tag;
      if (o.fileName) state.fileName = o.fileName;
      if (o.maxLines) state.maxLines = o.maxLines;
    },
    info(msg, data) { return write("INFO", msg, data); },
    warn(msg, data) { return write("WARN", msg, data); },
    error(msg, data) { return write("ERROR", msg, data); },
    flush,
    filePath,
    lines() { return state.lines.slice(); },
  };
  if (typeof module === "object" && module && module.exports) module.exports = PPM;
})(typeof globalThis !== "undefined" ? globalThis : this);

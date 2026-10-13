/* ppm-cep — パネルから CEP の補助（再生・停止・分割）を呼ぶ。補助が名乗った命令だけを送る。 */
(function (root) {
  "use strict";
  const PPM = (root.PPM = root.PPM || {});

  async function status() { return PPM.server.call("/cep/status"); }

  async function call(name, args) {
    const s = await status();
    if (!s.connected) {
      throw PPM.err("補助（CEP）が動いていません", "補助が入っていないか、Premiere を再起動していません",
        "作業フォルダの cep/install_cep.py で補助を入れ、Premiere を再起動してください（Windows では動作未確認）");
    }
    if ((s.features || []).indexOf(name) < 0) {
      throw PPM.err(`補助が「${name}」に対応していません`, "古い補助が動いています（新しい命令を知らない補助に送ると、別の動きをすることがあります）",
        "Premiere を再起動すると新しい補助が読み込まれます。分割なら代わりにマーカーを置いて手で切る方法もあります");
    }
    const r = await PPM.server.call("/cep/commands", { method: "POST", body: { name, args: args || {}, timeoutMs: 15000 } });
    if (!r.ok) throw PPM.err("補助の処理が失敗しました", String(r.error || ""), "Premiere の画面を前に出してから、もう一度試してください");
    return r.result;
  }

  PPM.cep = { status, call };
  if (typeof module === "object" && module && module.exports) module.exports = PPM;
})(typeof globalThis !== "undefined" ? globalThis : this);

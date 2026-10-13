/* ppm-commands — メニューのコマンド（［ウィンドウ］→［UXP プラグイン］の下に出る）。
 * Premiere の［キーボードショートカット］には UXP のコマンドを割り当てられない。
 * Mac はシステム設定の「キーボードショートカット → アプリのショートカット」で、メニュー名と同じ名前を書けば割り当てられる
 * （名前が 1 文字違うと黙って効かない）。 */
(function (root) {
  "use strict";
  const PPM = (root.PPM = root.PPM || {});
  const table = {};
  PPM.commands = {
    define(id, handler) {
      table[id] = async function () {
        try { await handler(); }
        catch (e) { if (PPM.log) PPM.log.error("command failed", { id, message: String((e && e.message) || e) }); }
      };
    },
    table() { return Object.assign({}, table); },
  };
  if (typeof module === "object" && module && module.exports) module.exports = PPM;
})(typeof globalThis !== "undefined" ? globalThis : this);

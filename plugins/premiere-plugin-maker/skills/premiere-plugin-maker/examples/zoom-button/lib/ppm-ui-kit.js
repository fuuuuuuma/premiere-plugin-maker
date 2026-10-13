/* ppm-ui-kit — 結果の表示・ボタンの処理中・空欄の値・select の誤操作（Cut & SRT で実機で踏んだ対策）。 */
(function (root) {
  "use strict";
  const PPM = (root.PPM = root.PPM || {});

  function setState(el, state, text) {
    if (!el) return;
    el.setAttribute("data-state", state);
    el.textContent = text;
  }
  function showOk(el, text) { setState(el, "ok", text); }
  function showInfo(el, text) { setState(el, "info", text); }
  function showError(el, e) {
    const p = e && e.ppm;
    const text = p ? `${p.symptom}\nなぜ: ${p.why}\n次の一手: ${p.next}` : `うまくいきませんでした: ${String((e && e.message) || e)}`;
    setState(el, "error", text);
  }
  function busy(button, on, label) {
    if (!button) return;
    if (on) {
      if (!button.getAttribute("data-label")) button.setAttribute("data-label", button.textContent);
      button.textContent = label || "処理中…";
      button.setAttribute("disabled", "");
    } else {
      const saved = button.getAttribute("data-label");
      if (saved) button.textContent = saved;
      button.removeAttribute("data-label");
      button.removeAttribute("disabled");
    }
  }
  // UXP の空欄の value は null のことがある（"null" が混ざる・NaN が設定を壊す事故があった）
  function textValue(el) {
    if (!el) return "";
    const v = el.value;
    return v === null || v === undefined ? "" : String(v);
  }
  function numberValue(el, fallback) {
    const n = parseFloat(textValue(el));
    return Number.isFinite(n) ? n : fallback;
  }
  // select の上でホイールを回すと値が勝手に変わる。ホイールから 300ms 以内の変更は戻す
  function protectSelect(select) {
    if (!select) return;
    let lastWheel = 0;
    let committed = select.value;
    select.addEventListener("wheel", () => { lastWheel = Date.now(); });
    select.addEventListener("change", () => {
      if (Date.now() - lastWheel < 300) { select.value = committed; return; }
      committed = select.value;
    });
  }

  PPM.ui = { showOk, showInfo, showError, busy, textValue, numberValue, protectSelect };
  if (typeof module === "object" && module && module.exports) module.exports = PPM;
})(typeof globalThis !== "undefined" ? globalThis : this);

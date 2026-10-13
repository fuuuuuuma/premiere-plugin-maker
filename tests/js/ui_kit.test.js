"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { loadParts } = require("./load_parts");

function el(initial = {}) {
  const attrs = {};
  const handlers = {};
  return Object.assign({
    textContent: "", value: null,
    setAttribute(k, v) { attrs[k] = String(v); }, getAttribute(k) { return k in attrs ? attrs[k] : null; },
    removeAttribute(k) { delete attrs[k]; }, addEventListener(t, f) { (handlers[t] = handlers[t] || []).push(f); },
    fire(t) { (handlers[t] || []).forEach((f) => f()); }, attrs,
  }, initial);
}

test("showError は症状・なぜ・次の一手の 3 行にする", () => {
  const ctx = loadParts(["ui-kit/lib/ppm-ui-kit.js"]);
  const box = el();
  const e = new Error("x");
  e.ppm = { symptom: "クリップが選ばれていません", why: "選んだクリップに対して行います", next: "選んでから押してください" };
  ctx.PPM.ui.showError(box, e);
  assert.equal(box.attrs["data-state"], "error");
  assert.equal(box.textContent.split("\n").length, 3);
});

test("空欄や null は既定値にする", () => {
  const ctx = loadParts(["ui-kit/lib/ppm-ui-kit.js"]);
  assert.equal(ctx.PPM.ui.numberValue(el({ value: null }), 2), 2);
  assert.equal(ctx.PPM.ui.numberValue(el({ value: "" }), 2), 2);
  assert.equal(ctx.PPM.ui.numberValue(el({ value: "1.5" }), 2), 1.5);
  assert.equal(ctx.PPM.ui.textValue(el({ value: null })), "");
});

test("busy はボタンの文字を戻す", () => {
  const ctx = loadParts(["ui-kit/lib/ppm-ui-kit.js"]);
  const b = el({ textContent: "実行" });
  ctx.PPM.ui.busy(b, true, "処理中…");
  assert.equal(b.textContent, "処理中…");
  ctx.PPM.ui.busy(b, false);
  assert.equal(b.textContent, "実行");
  assert.equal(b.getAttribute("disabled"), null);
});

test("ホイール直後の select の変更は戻す", () => {
  const ctx = loadParts(["ui-kit/lib/ppm-ui-kit.js"]);
  const s = el({ value: "a" });
  ctx.PPM.ui.protectSelect(s);
  s.fire("wheel");
  s.value = "b";
  s.fire("change");
  assert.equal(s.value, "a");
});

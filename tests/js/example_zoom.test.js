"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { makeFake } = require("./fake_ppro");

const EX = path.resolve(__dirname, "../../plugins/premiere-plugin-maker/skills/premiere-plugin-maker/examples/zoom-button");

function load() {
  const fake = makeFake();
  const elements = {};
  const el = (id) => (elements[id] = elements[id] || { id, value: null, textContent: "", h: {}, attrs: {},
    addEventListener(t, f) { this.h[t] = f; }, setAttribute(k, v) { this.attrs[k] = v; }, getAttribute(k) { return this.attrs[k] || null; }, removeAttribute(k) { delete this.attrs[k]; } });
  const document = { readyState: "complete", getElementById: el, addEventListener() {} };
  const uxp = { entrypoints: { setup() {} }, host: {}, versions: {}, storage: { formats: {}, localFileSystem: { async getPluginFolder() { throw new Error("x"); } } } };
  const ctx = vm.createContext({ console, setTimeout, clearTimeout, Promise, Date, Math, JSON, document,
    require: (n) => (n === "uxp" ? uxp : n === "premierepro" ? fake.ppro : (() => { throw new Error(n); })()) });
  const html = fs.readFileSync(path.join(EX, "index.html"), "utf8");
  const scripts = [...html.matchAll(/<script src="([^"]+)"/g)].map((m) => m[1]);
  for (const s of scripts) vm.runInContext(fs.readFileSync(path.join(EX, s), "utf8"), ctx);
  return { fake, el };
}

test("押すと、選んだ映像のクリップのスケールに焼いたキーを取引 1 回で打つ", async () => {
  const { fake, el } = load();
  // 入力欄はパネルが押されたときに初めて読むことがあるので、el() で作ってから値を入れる
  el("from").value = "100";
  el("to").value = "110";
  el("seconds").value = "2";
  await el("run").h.click();
  assert.equal(fake.log.transactions.length, 1);
  const keys = fake.log.actions.filter((a) => a.__action === "addKeyframe");
  assert.ok(keys.length > 2 * 30 * 2 * 0.9, `キーの数 ${keys.length}`);
  assert.equal(el("result").attrs["data-state"], "ok");
});

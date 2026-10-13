"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { makeFake } = require("./fake_ppro");

const EX = path.resolve(__dirname, "../../plugins/premiere-plugin-maker/skills/premiere-plugin-maker/examples/silence-cut");

test("書き出し → silence_cut のジョブ → 読み込んで開く、の順に呼ぶ", async () => {
  const fake = makeFake();
  const order = [];
  const elements = {};
  const el = (id) => (elements[id] = elements[id] || { id, value: null, textContent: "", h: {}, attrs: {},
    addEventListener(t, f) { this.h[t] = f; }, setAttribute(k, v) { this.attrs[k] = v; }, getAttribute(k) { return this.attrs[k] || null; }, removeAttribute(k) { delete this.attrs[k]; } });
  const document = { readyState: "complete", getElementById: el, addEventListener() {} };
  const uxp = { entrypoints: { setup() {} }, host: {}, versions: {}, storage: { formats: {}, localFileSystem: { async getPluginFolder() { throw new Error("x"); } } } };
  const ctx = vm.createContext({ console, setTimeout, clearTimeout, Promise, Date, Math, JSON, document,
    require: (n) => (n === "uxp" ? uxp : n === "premierepro" ? fake.ppro : (() => { throw new Error(n); })()) });
  const html = fs.readFileSync(path.join(EX, "index.html"), "utf8");
  for (const s of [...html.matchAll(/<script src="([^"]+)"/g)].map((m) => m[1])) vm.runInContext(fs.readFileSync(path.join(EX, s), "utf8"), ctx);
  ctx.PPM.server.connect = async () => { order.push("connect"); return {}; };
  ctx.PPM.server.runJob = async (kind, params) => { order.push(`job:${kind}:${params.threshold}`); return { outputXml: "/tmp/out_カット済み.xml" }; };
  ctx.PPM.fcpxml.exportActiveSequence = async () => { order.push("export"); return "/tmp/in.xml"; };
  ctx.PPM.fcpxml.importAndOpen = async (p) => { order.push(`import:${p}`); return { name: "新しいシーケンス" }; };
  el("threshold").value = "-45";
  await el("run").h.click();
  assert.deepEqual(order, ["connect", "export", "job:silence_cut:-45", "import:/tmp/out_カット済み.xml"]);
  assert.equal(el("result").attrs["data-state"], "ok");
});

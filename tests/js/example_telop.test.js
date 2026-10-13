"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { makeFake } = require("./fake_ppro");

const EX = path.resolve(__dirname, "../../plugins/premiere-plugin-maker/skills/premiere-plugin-maker/examples/telop-restyle");

test("本文が読めたテロップだけを、選んだデザインで差し替える", async () => {
  const fake = makeFake();
  const elements = {};
  const el = (id) => (elements[id] = elements[id] || { id, value: null, textContent: "", h: {}, attrs: {},
    addEventListener(t, f) { this.h[t] = f; }, setAttribute(k, v) { this.attrs[k] = v; }, getAttribute(k) { return this.attrs[k] || null; }, removeAttribute(k) { delete this.attrs[k]; } });
  const document = { readyState: "complete", getElementById: el, addEventListener() {} };
  const uxp = { entrypoints: { setup() {} }, host: {}, versions: {}, storage: { formats: {}, localFileSystem: { async getPluginFolder() { throw new Error("x"); } } } };
  const ctx = vm.createContext({ console, setTimeout, clearTimeout, Promise, Date, Math, JSON, document,
    require: (n) => (n === "uxp" ? uxp : n === "premierepro" ? fake.ppro : (() => { throw new Error(n); })()) });
  const html = fs.readFileSync(path.join(EX, "index.html"), "utf8");
  for (const s of [...html.matchAll(/<script src="([^"]+)"/g)].map((m) => m[1])) vm.runInContext(fs.readFileSync(path.join(EX, s), "utf8"), ctx);
  const jobs = [];
  const replaced = [];
  ctx.PPM.server.connect = async () => ({});
  ctx.PPM.fcpxml.exportActiveSequence = async () => "/tmp/in.xml";
  ctx.PPM.server.runJob = async (kind, params) => {
    jobs.push({ kind, params });
    if (kind === "read_texts") return { texts: [{ text: "一つ目" }, { text: null }] };
    return { mogrts: params.items.map((it, i) => ({ text: it.text, path: `/tmp/${i}.mogrt` })), warnings: [] };
  };
  ctx.PPM.mogrt.replaceClip = async (project, sequence, clip, p) => { replaced.push(p); return { undoSteps: 2 }; };
  el("style").value = "yellow-red-white";
  await el("run").h.click();
  assert.deepEqual(jobs.map((j) => j.kind), ["read_texts", "build_mogrt"]);
  assert.equal(jobs[1].params.styleName, "yellow-red-white");
  assert.deepEqual(replaced, ["/tmp/0.mogrt"]);
  assert.match(el("result").textContent, /1 本を差し替え/);
  assert.match(el("result").textContent, /1 本は本文を読めず/);
});

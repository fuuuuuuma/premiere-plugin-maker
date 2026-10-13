"use strict";
// 最後のレビューで見つかった型を固定する（古いコマを返す・差し替えの途中で止まる・件数の上限・フレームレートを詰めない）
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { loadParts } = require("./load_parts");
const { makeFake } = require("./fake_ppro");

test("コマの書き出しは、前の同じ名前のファイルを消してから書き出す（古い画像を返さない）", async () => {
  const fake = makeFake();
  const order = [];
  const files = new Set(["frame.png"]);
  const folder = {
    nativePath: "/tmp/data",
    async getEntry(name) {
      if (!files.has(name)) throw new Error("無い");
      return { name, async delete() { order.push(`delete:${name}`); files.delete(name); } };
    },
  };
  fake.ppro.Exporter.exportSequenceFrame = async (seq, t, name) => { order.push("export"); files.add(name); return true; };
  const ctx = loadParts(["logger/lib/ppm-logger.js", "ppro-kit/lib/ppm-ppro-kit.js"]);
  ctx.PPM.init({ ppro: fake.ppro, uxp: { storage: { localFileSystem: { async getDataFolder() { return folder; } } } }, tag: "t" });
  const p = await ctx.PPM.exportFrame(fake.sequence, 1, "frame.png", { timeoutMs: 2000 });
  assert.equal(p, "/tmp/data/frame.png");
  assert.deepEqual(order.slice(0, 2), ["delete:frame.png", "export"]);
});

test("コマの書き出しを Premiere が断ったら、ファイルを待たずにエラーにする", async () => {
  const fake = makeFake();
  const folder = { nativePath: "/tmp/data", async getEntry() { throw new Error("無い"); } };
  fake.ppro.Exporter.exportSequenceFrame = async () => false;
  const ctx = loadParts(["logger/lib/ppm-logger.js", "ppro-kit/lib/ppm-ppro-kit.js"]);
  ctx.PPM.init({ ppro: fake.ppro, uxp: { storage: { localFileSystem: { async getDataFolder() { return folder; } } } }, tag: "t" });
  const started = Date.now();
  await assert.rejects(ctx.PPM.exportFrame(fake.sequence, 1, "x.png", { timeoutMs: 5000 }), (e) => e.ppm && /受け付けません/.test(e.ppm.why));
  assert.ok(Date.now() - started < 2000);
});

test("差し替えで MOGRT を入れられなかったら、外した元を Cmd+Z 1 回で戻せると伝える", async () => {
  const fake = makeFake();
  const ctx = loadParts(["logger/lib/ppm-logger.js", "ppro-kit/lib/ppm-ppro-kit.js", "mogrt-text/lib/ppm-mogrt.js"]);
  ctx.PPM.init({ ppro: fake.ppro, uxp: null, tag: "t" });
  fake.ppro.Constants.MediaType = { VIDEO: 1 };
  fake.ppro.SequenceEditor.getEditor = async () => ({ insertMogrtFromPath() { return []; }, createRemoveItemsAction() { return { __action: "remove", args: [] }; } });
  const { project, sequence } = await ctx.PPM.getProjectAndSequence();
  const clip = (await ctx.PPM.getSelectedClips(sequence))[0];
  sequence.getSelection = async () => ({ async getTrackItems() { return []; }, removeItem() {}, addItem() {} });
  await assert.rejects(ctx.PPM.mogrt.replaceClip(project, sequence, clip, "/tmp/0.mogrt"), (e) => e.ppm && /Cmd\+Z/.test(e.ppm.next) && /外れ/.test(e.ppm.why));
});

function loadExample(name, fake) {
  const EX = path.resolve(__dirname, "../../plugins/premiere-plugin-maker/skills/premiere-plugin-maker/examples", name);
  const elements = {};
  const el = (id) => (elements[id] = elements[id] || { id, value: null, textContent: "", h: {}, attrs: {},
    addEventListener(t, f) { this.h[t] = f; }, setAttribute(k, v) { this.attrs[k] = v; }, getAttribute(k) { return this.attrs[k] || null; }, removeAttribute(k) { delete this.attrs[k]; } });
  const document = { readyState: "complete", getElementById: el, addEventListener() {} };
  const uxp = { entrypoints: { setup() {} }, host: {}, versions: {}, storage: { formats: {}, localFileSystem: { async getPluginFolder() { throw new Error("x"); } } } };
  const ctx = vm.createContext({ console, setTimeout, clearTimeout, Promise, Date, Math, JSON, document,
    require: (n) => (n === "uxp" ? uxp : n === "premierepro" ? fake.ppro : (() => { throw new Error(n); })()) });
  const html = fs.readFileSync(path.join(EX, "index.html"), "utf8");
  for (const s of [...html.matchAll(/<script src="([^"]+)"/g)].map((m) => m[1])) vm.runInContext(fs.readFileSync(path.join(EX, s), "utf8"), ctx);
  return { ctx, el };
}

test("テロップの差し替えが途中で止まったら、何本まで済んだかと取り消しの回数を出す", async () => {
  const fake = makeFake();
  const { ctx, el } = loadExample("telop-restyle", fake);
  ctx.PPM.server.connect = async () => ({});
  ctx.PPM.fcpxml.exportActiveSequence = async () => "/tmp/in.xml";
  ctx.PPM.server.runJob = async (kind, params) => (kind === "read_texts"
    ? { texts: [{ text: "一つ目" }, { text: "二つ目" }] }
    : { mogrts: params.items.map((it, i) => ({ text: it.text, path: `/tmp/${i}.mogrt` })), warnings: [] });
  let n = 0;
  ctx.PPM.mogrt.replaceClip = async () => { n += 1; if (n === 2) throw ctx.PPM.err("MOGRT を入れられません", "テスト", "やり直す"); return { undoSteps: 2 }; };
  el("style").value = "white-black";
  await el("run").h.click();
  assert.equal(el("result").attrs["data-state"], "error");
  assert.match(el("result").textContent, /1 本まで/);
  assert.match(el("result").textContent, /2 回/);
});

test("ズームは選んだクリップが多すぎると、取引を作らずに止める", async () => {
  const base = makeFake();
  const many = Array.from({ length: 201 }, (_, i) => new base.VideoClipTrackItem(`C${i}`, i, i + 1, 0, 0));
  const fake = makeFake({ clips: many });
  const { el } = loadExample("zoom-button", fake);
  await el("run").h.click();
  assert.equal(fake.log.transactions.length, 0);
  assert.match(el("result").textContent, /200/);
});

test("ズームはフレームレートを読めなければ、30 コマと決めつけずに止める", async () => {
  const fake = makeFake({ noFrameRateMethod: true });
  const { el } = loadExample("zoom-button", fake);
  await el("run").h.click();
  assert.equal(fake.log.transactions.length, 0);
  assert.match(el("result").textContent, /フレームレート/);
});

"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { loadParts } = require("./load_parts");
const { makeFake } = require("./fake_ppro");

function setup({ before = 1, after = 2, exportOk = true } = {}) {
  const fake = makeFake();
  const seqs = Array.from({ length: before }, (_, i) => ({ name: `s${i}` }));
  const opened = [];
  fake.project.getSequences = async () => seqs.slice();
  fake.project.getRootItem = async () => ({ name: "root" });
  fake.project.importFiles = async () => { while (seqs.length < after) seqs.push({ name: `new${seqs.length}` }); return true; };
  fake.project.openSequence = async (s) => { opened.push(s); };
  fake.project.setActiveSequence = async () => {};
  fake.ppro.ProjectConverter = { async exportAsFinalCutProXML(seq, p, suppress) { fake.exported = { p, suppress }; return exportOk; } };
  const ctx = loadParts(["logger/lib/ppm-logger.js", "ppro-kit/lib/ppm-ppro-kit.js", "fcpxml/lib/ppm-fcpxml.js"]);
  ctx.PPM.init({ ppro: fake.ppro, uxp: null });
  ctx.PPM.server = { tmpPath: (n) => `/tmp/ppm/${n}` };
  return { PPM: ctx.PPM, fake, opened };
}

test("書き出しは server の tmp に、suppressUI を付けて行う", async () => {
  const { PPM, fake } = setup();
  const p = await PPM.fcpxml.exportActiveSequence("a.xml");
  assert.equal(p, "/tmp/ppm/a.xml");
  assert.equal(fake.exported.suppress, true);
});

test("書き出しが false なら理由つきのエラー", async () => {
  const { PPM } = setup({ exportOk: false });
  await assert.rejects(PPM.fcpxml.exportActiveSequence("a.xml"), (e) => e.ppm && e.ppm.symptom.includes("書き出せません"));
});

test("読み込んで増えたシーケンスを開く", async () => {
  const { PPM, opened } = setup({ before: 1, after: 2 });
  const s = await PPM.fcpxml.importAndOpen("/tmp/ppm/out.xml");
  assert.equal(s.name, "new1");
  assert.equal(opened.length, 1);
});

test("増えなければ、手で読み込む案内を出す", async () => {
  const { PPM } = setup({ before: 1, after: 1 });
  await assert.rejects(PPM.fcpxml.importAndOpen("/tmp/ppm/out.xml"), (e) => e.ppm.next.includes("読み込み"));
});

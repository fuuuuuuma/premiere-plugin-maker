"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { loadParts } = require("./load_parts");
const { makeFake, TPS } = require("./fake_ppro");

function setup({ insertResult = [{ inserted: true }] } = {}) {
  const fake = makeFake();
  const calls = [];
  fake.ppro.SequenceEditor = {
    async getEditor() {
      return {
        insertMogrtFromPath(path, time, v, a) { calls.push({ path, seconds: time.seconds, v, a }); return insertResult; },
        createRemoveItemsAction(sel, ripple, type, shift) { if (arguments.length < 4) throw new Error("Not Enough Parameters"); return { __action: "remove", args: [sel, ripple, type, shift] }; },
      };
    },
  };
  fake.ppro.Constants.MediaType = { VIDEO: "video" };
  const ctx = loadParts(["logger/lib/ppm-logger.js", "ppro-kit/lib/ppm-ppro-kit.js", "mogrt-text/lib/ppm-mogrt.js"]);
  ctx.PPM.init({ ppro: fake.ppro, uxp: null });
  return { PPM: ctx.PPM, fake, calls };
}

test("insertAt は取引の外で insertMogrtFromPath を呼ぶ", async () => {
  const { PPM, calls, fake } = setup();
  const { project, sequence } = await PPM.getProjectAndSequence();
  await PPM.mogrt.insertAt(project, sequence, "/tmp/a.mogrt", 2, 1, 0);
  assert.deepEqual(calls, [{ path: "/tmp/a.mogrt", seconds: 2, v: 1, a: 0 }]);
  assert.equal(fake.log.locked, 0);
});

test("空の結果は失敗として扱う", async () => {
  const { PPM } = setup({ insertResult: [] });
  const { project, sequence } = await PPM.getProjectAndSequence();
  await assert.rejects(PPM.mogrt.insertAt(project, sequence, "/tmp/a.mogrt", 0, 1, 0), (e) => e.ppm && e.ppm.symptom.includes("入れられません"));
});

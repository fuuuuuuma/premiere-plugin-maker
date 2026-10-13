"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { loadParts } = require("./load_parts");

function setup(status) {
  const ctx = loadParts(["logger/lib/ppm-logger.js", "ppro-kit/lib/ppm-ppro-kit.js", "cep-helper/lib/ppm-cep.js"]);
  const calls = [];
  ctx.PPM.server = { async call(path, opts) { calls.push({ path, opts }); return path === "/cep/status" ? status : { ok: true, result: { done: true } }; } };
  return { PPM: ctx.PPM, calls };
}

test("名乗っていない命令は送らず、代わりの手を出す", async () => {
  const { PPM, calls } = setup({ connected: true, features: ["play"] });
  await assert.rejects(PPM.cep.call("razor", {}), (e) => e.ppm && e.ppm.next.includes("Premiere を再起動"));
  assert.equal(calls.filter((c) => c.path === "/cep/commands").length, 0);
});

test("つながっていなければ、入れ方を案内する", async () => {
  const { PPM } = setup({ connected: false, features: [] });
  await assert.rejects(PPM.cep.call("play", {}), (e) => e.ppm.symptom.includes("補助"));
});

test("名乗った命令は送る", async () => {
  const { PPM, calls } = setup({ connected: true, features: ["play"] });
  const r = await PPM.cep.call("play", { seconds: 1 });
  assert.equal(r.done, true);
  assert.equal(calls.at(-1).opts.body.name, "play");
});

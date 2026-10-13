"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const vectors = require("../fixtures/motion_vectors.json");
const { loadParts, plain } = require("./load_parts");

const ctx = loadParts(["motion-bake/lib/ppm-motion-bake.js"]);
const M = ctx.PPM.motion;

test("Premiere の bezier の実測: 0→100 を 1 秒、t=0.5 で 43.75", () => {
  assert.ok(Math.abs(M.easeBezier(0.5) - 0.4375) < 1e-6);
  assert.equal(M.fraction("hold", 0.7), 0);
  assert.equal(M.fraction("linear", 0.7), 0.7);
});

for (const [name, v] of Object.entries(vectors)) {
  test(`移植元と同じ焼き込み: ${name}`, () => {
    assert.deepEqual(plain(M.bakeTrack(v.keys, v.frame)), v.baked);
  });
}

test("焼いたキーは全部 linear", () => {
  const baked = M.bakeTrack(vectors.scale_bezier.keys, 1 / 30);
  assert.ok(baked.every((k) => k.interp === "linear"));
  assert.ok(baked.length > 20);
});

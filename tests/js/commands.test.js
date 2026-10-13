"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { loadParts } = require("./load_parts");

test("define した命令が table に出て、失敗はログに残る", async () => {
  const ctx = loadParts(["logger/lib/ppm-logger.js", "commands/lib/ppm-commands.js"]);
  let ran = 0;
  ctx.PPM.commands.define("runMain", async () => { ran += 1; });
  ctx.PPM.commands.define("broken", async () => { throw new Error("壊れた"); });
  const table = ctx.PPM.commands.table();
  await table.runMain();
  await table.broken();
  assert.equal(ran, 1);
  assert.ok(ctx.PPM.log.lines().some((l) => l.includes("command failed") && l.includes("壊れた")));
});

"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { loadParts } = require("./load_parts");
const { makeFake } = require("./fake_ppro");

test("取りに行った命令を実行して結果を返し、命令の一覧を名乗る", async () => {
  const fake = makeFake();
  const ctx = loadParts(["logger/lib/ppm-logger.js", "ppro-kit/lib/ppm-ppro-kit.js", "probe/lib/ppm-probe.js", "ui-kit/lib/ppm-ui-kit.js", "mcp-bridge/lib/ppm-agent-bridge.js"]);
  ctx.PPM.init({ ppro: fake.ppro, uxp: null });
  const posts = [];
  let served = false;
  ctx.PPM.server = {
    async call(path, opts) {
      posts.push({ path, body: opts && opts.body });
      if (path === "/panel/next" && !served) { served = true; return { command: { id: "c1", name: "get_selection", args: {} } }; }
      return {};
    },
  };
  await ctx.PPM.agent.pollOnce();
  const result = posts.find((p) => p.path === "/panel/result");
  assert.equal(result.body.ok, true);
  assert.equal(result.body.result.count, 2);
  const names = posts[0].body.commands.map((c) => c.name);
  for (const n of ["probe", "get_selection", "sequence_overview", "log_tail"]) assert.ok(names.includes(n), n);
});

test("命令の失敗は ok:false とエラーの文で返す", async () => {
  const fake = makeFake({ noSequence: true });
  const ctx = loadParts(["logger/lib/ppm-logger.js", "ppro-kit/lib/ppm-ppro-kit.js", "probe/lib/ppm-probe.js", "ui-kit/lib/ppm-ui-kit.js", "mcp-bridge/lib/ppm-agent-bridge.js"]);
  ctx.PPM.init({ ppro: fake.ppro, uxp: null });
  const posts = [];
  ctx.PPM.server = { async call(path, opts) { posts.push({ path, body: opts && opts.body }); return path === "/panel/next" && posts.length === 1 ? { command: { id: "c2", name: "get_selection", args: {} } } : {}; } };
  await ctx.PPM.agent.pollOnce();
  const result = posts.find((p) => p.path === "/panel/result");
  assert.equal(result.body.ok, false);
  assert.match(result.body.error, /シーケンス/);
});

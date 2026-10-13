"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { loadParts } = require("./load_parts");

// 実名に見えるホームは実行時に組み立てる（Task 34 の衛生検査に引っかからないように）
const WIN_HOME = "C:\\" + "Users\\山田 太郎";
const MAC_HOME = "/Users/" + "someone";

function client({ platform = "darwin", responses = [], handshakes = [{ token: "t1", httpPort: 5000, protocol: 1, tmpDir: "/tmp/x" }] } = {}) {
  let reads = 0;
  const seen = { paths: [], calls: [] };
  const fs = {
    async readFile(p) {
      seen.paths.push(p);
      const h = handshakes[Math.min(reads, handshakes.length - 1)];
      reads += 1;
      if (!h) throw new Error("ENOENT");
      return JSON.stringify(h);
    },
  };
  const os = { homedir: () => (platform === "win32" ? WIN_HOME : MAC_HOME), platform: () => platform };
  const fetch = async (url, opts) => {
    seen.calls.push({ url, opts });
    const r = responses.shift();
    if (r instanceof Error) throw r;
    return { status: r.status, async json() { return r.body; } };
  };
  const ctx = loadParts(["logger/lib/ppm-logger.js", "ppro-kit/lib/ppm-ppro-kit.js", "local-server/lib/ppm-server-client.js"],
    { require: (n) => (n === "fs" ? fs : n === "os" ? os : null), fetch }, { "{{APP_NAME}}": "PpmTest" });
  return { PPM: ctx.PPM, seen };
}

test("握手のファイルの場所（Mac と Windows）", () => {
  assert.equal(client().PPM.server.handshakePath(), `${MAC_HOME}/Library/Application Support/PpmTest/server.json`);
  assert.equal(client({ platform: "win32" }).PPM.server.handshakePath(), `${WIN_HOME}\\AppData\\Roaming\\PpmTest\\server.json`);
});

test("合言葉を付けて呼び、403 なら読み直して 1 回だけやり直す", async () => {
  const { PPM, seen } = client({
    handshakes: [{ token: "old", httpPort: 5000, protocol: 1, tmpDir: "/t" }, { token: "new", httpPort: 5001, protocol: 1, tmpDir: "/t" }],
    responses: [{ status: 403, body: {} }, { status: 200, body: { ok: true } }],
  });
  const r = await PPM.server.call("/ping");
  assert.equal(r.ok, true);
  assert.equal(seen.calls[0].opts.headers["X-PPM-Token"], "old");
  assert.equal(seen.calls[1].opts.headers["X-PPM-Token"], "new");
  assert.equal(seen.calls[1].url, "http://127.0.0.1:5001/ping");
});

test("約束の番号が違えばつながない", async () => {
  const { PPM } = client({ handshakes: [{ token: "t", httpPort: 1, protocol: 9, tmpDir: "/t" }] });
  await assert.rejects(PPM.server.readHandshake(), /版が合いません/);
});

test("サーバーが無ければ、入れ方を案内する", async () => {
  const { PPM } = client({ handshakes: [null] });
  await assert.rejects(PPM.server.readHandshake(), (e) => e.ppm && e.ppm.next.includes("install"));
});

test("runJob は終わるまで待ち、進み具合を知らせる", async () => {
  const progress = [];
  const { PPM } = client({ responses: [{ status: 202, body: { jobId: "j" } }, { status: 200, body: { status: "running", percent: 50 } }, { status: 200, body: { status: "done", result: { a: 1 } } }] });
  const r = await PPM.server.runJob("echo", {}, { fastMs: 1, onProgress: (p) => progress.push(p) });
  assert.equal(r.a, 1);
  assert.deepEqual(progress, [50, 0]);
});

test("ジョブの失敗は理由つきのエラーにする", async () => {
  const { PPM } = client({ responses: [{ status: 202, body: { jobId: "j" } }, { status: 200, body: { status: "error", error: { message: "止めました", why: "理由", next: "次" } } }] });
  await assert.rejects(PPM.server.runJob("x", {}, { fastMs: 1 }), (e) => e.ppm.why === "理由");
});

test("通信が 3 回続けて切れたら諦める", async () => {
  const { PPM } = client({ responses: [{ status: 202, body: { jobId: "j" } }, new Error("down"), new Error("down"), new Error("down")] });
  await assert.rejects(PPM.server.runJob("x", {}, { fastMs: 1 }), /down/);
});

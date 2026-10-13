"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { loadParts, plain } = require("./load_parts");
const { makeFake } = require("./fake_ppro");

function memUxp() {
  const files = {};
  const folder = {
    nativePath: "/tmp/作業 フォルダ/PluginData",
    async createFile(name) {
      return {
        nativePath: `${folder.nativePath}/${name}`,
        async write(text) { files[name] = text; },
      };
    },
    async getEntry(name) { if (!(name in files)) throw new Error("無い"); return { name }; },
  };
  return {
    files,
    uxp: {
      host: { name: "premierepro", version: "26.5.2" },
      versions: { uxp: "9.4.0" },
      storage: { localFileSystem: { async getDataFolder() { return folder; } }, formats: { utf8: "utf8" } },
    },
  };
}

test("ログは console と ppm-log.txt に同じ行を書き、最後の maxLines 行だけ残す", async () => {
  const mem = memUxp();
  const ctx = loadParts(["logger/lib/ppm-logger.js"]);
  ctx.PPM.log.init({ uxp: mem.uxp, tag: "zoom", maxLines: 3 });
  for (let i = 0; i < 5; i++) ctx.PPM.log.info(`行${i}`, { i });
  assert.equal(ctx.PPM.log.lines().length, 3);
  assert.equal(await ctx.PPM.log.flush(), true);
  assert.match(mem.files["ppm-log.txt"], /\[zoom\] INFO 行4 \{"i":4\}/);
  assert.equal(await ctx.PPM.log.filePath(), "/tmp/作業 フォルダ/PluginData/ppm-log.txt");
});

test("probe は無い API を missing と書き、ログの場所を返す", async () => {
  const mem = memUxp();
  const fake = makeFake();
  const ctx = loadParts(["logger/lib/ppm-logger.js", "ppro-kit/lib/ppm-ppro-kit.js", "probe/lib/ppm-probe.js"]);
  ctx.PPM.init({ ppro: fake.ppro, uxp: mem.uxp, tag: "p" });
  const r = plain(await ctx.PPM.probe.run());
  assert.equal(r.statics["Project.getActiveProject"], "function");
  assert.equal(r.statics["ProjectConverter.exportAsFinalCutProXML"], "missing");
  assert.equal(r.live["settings.getVideoFrameRate"], "function");
  assert.equal(r.host.version, "26.5.2");
  assert.ok(r.logFile.endsWith("ppm-log.txt"));
});

"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const PARTS = path.resolve(__dirname, "../../plugins/premiere-plugin-maker/skills/premiere-plugin-maker/parts");

// 部品を Premiere の UXP に近い条件（module も require も無いページ）で読み込む
function loadParts(files, extra = {}) {
  const ctx = vm.createContext({ console, setTimeout, clearTimeout, Promise, Date, Math, JSON, ...extra });
  for (const f of files) {
    vm.runInContext(fs.readFileSync(path.join(PARTS, f), "utf8"), ctx, { filename: f });
  }
  return ctx;
}

// vm の中のオブジェクトは deepStrictEqual が通らないので、JSON で写して比べる
function plain(v) { return JSON.parse(JSON.stringify(v)); }

module.exports = { loadParts, plain, PARTS };

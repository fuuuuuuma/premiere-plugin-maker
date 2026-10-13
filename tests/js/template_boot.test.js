"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { PARTS } = require("./load_parts");
const { makeFake } = require("./fake_ppro");

const BASE = path.resolve(__dirname, "../../plugins/premiere-plugin-maker/skills/premiere-plugin-maker/templates/_base");

function element(id) {
  const handlers = {};
  const attrs = {};
  return {
    id, textContent: "", value: null, handlers,
    addEventListener(t, f) { (handlers[t] = handlers[t] || []).push(f); },
    setAttribute(k, v) { attrs[k] = String(v); }, getAttribute(k) { return k in attrs ? attrs[k] : null; }, removeAttribute(k) { delete attrs[k]; },
  };
}

function boot(readyState) {
  const fake = makeFake();
  const setupCalls = [];
  const elements = {};
  const document = {
    readyState,
    listeners: {},
    getElementById(id) { return (elements[id] = elements[id] || element(id)); },
    addEventListener(t, f) { (this.listeners[t] = this.listeners[t] || []).push(f); },
  };
  const uxp = {
    entrypoints: { setup(o) { setupCalls.push(o); } },
    host: { name: "premierepro", version: "26.5.2" },
    versions: { uxp: "9.4.0" },
    storage: {
      formats: { utf8: "utf8" },
      localFileSystem: {
        async getDataFolder() { return { nativePath: "/tmp/d", async createFile() { return { async write() {}, nativePath: "/tmp/d/ppm-log.txt" }; }, async getEntry() { throw new Error("無い"); } }; },
        async getPluginFolder() { return { async getEntry() { return { async read() { return '{"name":"T","version":"0.1.0"}'; } }; } }; },
      },
    },
  };
  const requireFake = (name) => { if (name === "uxp") return uxp; if (name === "premierepro") return fake.ppro; throw new Error("Module not found: " + name); };
  const ctx = vm.createContext({ console, setTimeout, clearTimeout, Promise, Date, Math, JSON, document, require: requireFake });
  for (const f of ["logger/lib/ppm-logger.js", "ppro-kit/lib/ppm-ppro-kit.js", "ui-kit/lib/ppm-ui-kit.js", "probe/lib/ppm-probe.js"]) {
    vm.runInContext(fs.readFileSync(path.join(PARTS, f), "utf8"), ctx);
  }
  const src = fs.readFileSync(path.join(BASE, "index.js"), "utf8").replace(/\{\{PANEL_ID\}\}/g, "mainPanel").replace(/\{\{LOG_TAG\}\}/g, "t").replace(/\{\{PLUGIN_NAME\}\}/g, "T");
  vm.runInContext(src, ctx);
  return { ctx, document, elements, setupCalls };
}

test("読み込み済みなら、その場で 1 回だけ起動し、パネルを登録する", () => {
  const { elements, setupCalls, document } = boot("complete");
  assert.equal(setupCalls.length, 1);
  assert.ok(setupCalls[0].panels.mainPanel);
  assert.equal(elements.run.handlers.click.length, 1);
  (document.listeners.DOMContentLoaded || []).forEach((f) => f());
  assert.equal(elements.run.handlers.click.length, 1);
});

test("読み込み中なら DOMContentLoaded を待つ", () => {
  const { elements, document } = boot("loading");
  assert.equal(elements.run, undefined);
  document.listeners.DOMContentLoaded.forEach((f) => f());
  assert.equal(elements.run.handlers.click.length, 1);
});

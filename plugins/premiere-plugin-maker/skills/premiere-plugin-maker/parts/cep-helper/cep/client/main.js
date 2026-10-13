/* {{APP_NAME}} の補助（CEP 側）。手元のサーバーに 0.4 秒ごとに命令を取りに行き、ExtendScript で実行して結果を返す。
 * - Adobe の CSInterface.js は同梱しない。window.__adobe_cep__.evalScript を直接使う
 * - CEP の Node では child_process の非同期の返事が来ないことがある。ここでは fs の同期読みだけを使う
 * - 起動したら、自分ができる命令を名乗る（古い補助に新しい命令を送らないため） */
(function () {
  "use strict";
  var APP = "{{APP_NAME}}";
  var nodeRequire = (window.cep_node && window.cep_node.require) || window.require;
  var fs = nodeRequire("fs");
  var os = nodeRequire("os");
  var statusEl = document.getElementById("status");

  function handshake() {
    var home = os.homedir();
    var file = os.platform() === "win32" ? home + "\\AppData\\Roaming\\" + APP + "\\server.json" : home + "/Library/Application Support/" + APP + "/server.json";
    return JSON.parse(fs.readFileSync(file, "utf8"));
  }

  function post(path, body, done) {
    var h;
    try { h = handshake(); } catch (e) { statusEl.textContent = "サーバーが動いていません"; done(null); return; }
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "http://127.0.0.1:" + h.httpPort + path);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("X-PPM-Token", h.token);
    xhr.onload = function () { try { done(JSON.parse(xhr.responseText || "{}")); } catch (e) { done(null); } };
    xhr.onerror = function () { done(null); };
    xhr.send(JSON.stringify(body || {}));
  }

  function evalScript(script, done) {
    var answered = false;
    var timer = setTimeout(function () { if (!answered) { answered = true; done(null); } }, 15000);
    window.__adobe_cep__.evalScript(script, function (raw) {
      if (answered) return;
      answered = true;
      clearTimeout(timer);
      try { done(JSON.parse(raw)); } catch (e) { done({ ok: false, error: String(raw) }); }
    });
  }

  function quote(v) { return JSON.stringify(v === undefined ? null : v); }

  function run(command, done) {
    var a = command.args || {};
    var script;
    if (command.name === "play") script = "ppmPlay(" + quote(a.seconds) + "," + quote(a.speed || 1) + ")";
    else if (command.name === "stop") script = "ppmStop()";
    else if (command.name === "razor") script = "ppmRazor(" + quote(a.kind || "video") + "," + quote(a.trackIndex) + "," + quote(a.seconds) + ")";
    else { done({ ok: false, error: "知らない命令: " + command.name }); return; }
    evalScript(script, function (r) { done(r || { ok: false, error: "ExtendScript の返事がありません" }); });
  }

  function loop() {
    post("/cep/next", {}, function (data) {
      if (data && data.command) {
        var cmd = data.command;
        run(cmd, function (r) {
          post("/cep/result", { id: cmd.id, ok: !!(r && r.ok), result: r, error: r && r.error }, function () { setTimeout(loop, 50); });
        });
        return;
      }
      setTimeout(loop, 400);
    });
  }

  evalScript("ppmFeatures()", function (r) {
    var features = (r && r.features) || [];
    post("/cep/hello", { features: features }, function (ok) {
      statusEl.textContent = ok ? "補助は動いています（" + features.join("・") + "）" : "サーバーにつながりません";
      loop();
    });
  });
})();

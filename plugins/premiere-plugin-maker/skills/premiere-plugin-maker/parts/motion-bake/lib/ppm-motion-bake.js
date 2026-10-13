/* ppm-motion-bake — Premiere が描く補間の曲がり方を、1 コマごとの直線のキーにする（Effect & Design の client/motion.js から移植）。
 * UXP では、キーを足すのと同じ取引の中で補間を変えられない（無言で効かない）。取引を分けると Cmd+Z が 2 回要るので、
 * 曲がり方を直線のキーに焼いて 1 回の取引で書く。
 * 実測の式（Premiere 26.5）: 区間の形は始まりのキーの補間だけで決まる。bezier の制御点は (0,0)(1/6,0)(5/6,5/6)(1,1)。
 * 位置などの [x, y] は道筋そのものが曲がる（中のキーの接線 = (次 − 前)/6）。 */
(function (root) {
  "use strict";
  const PPM = (root.PPM = root.PPM || {});
  function round(v) { return Math.round(v * 1e6) / 1e6; }

  /* ---- 焼き込み（補助プラグイン用）----
   * UXP では、キーを足すのと同じ取引の中で補間を変えられない（まだ無いキーを指すので効かない・実機 2026-09-19）。
   * 取引を分けると ⌘Z が 2 回要るので、Premiere が描く曲がり方を 1 コマごとの直線のキーにして 1 回で書く。
   * Premiere の曲がり方（ExtendScript で打ったキーを getValueAtTime で読んで当てはめた・docs/qa/phase6-undo.md）:
   *   時間: 区間の形は始まりのキーの補間だけで決まる。linear = 直線、hold = 次のキーまで一定、
   *         bezier = 制御点 (0,0)(1/6,0)(5/6,5/6)(1,1)（出だしがゆっくり、終わりは区間の傾き）
   *   空間（位置などの [x, y]）: 各区間は 3 次ベジェ。中のキーの接線 = (次 − 前)/6、端のキーは隣のキーへ 1/6。
   *         時間の形は道のりの割合に掛かる（bezier の区間だけ、道筋に沿った進み方に最大 0.005 ほどのずれが残る） */
  var MAX_BAKED = 1200;

  function easeBezier(x) {
    if (x <= 0) { return 0; }
    if (x >= 1) { return 1; }
    function cubic(a, b, u) { var v = 1 - u; return 3 * v * v * u * a + 3 * v * u * u * b + u * u * u; }
    var lo = 0, hi = 1;
    for (var i = 0; i < 48; i++) { var mid = (lo + hi) / 2; if (cubic(1 / 6, 5 / 6, mid) < x) { lo = mid; } else { hi = mid; } }
    return cubic(0, 5 / 6, (lo + hi) / 2);
  }
  function fraction(interp, u) { return interp === "hold" ? 0 : interp === "bezier" ? easeBezier(u) : u; }

  function bezPoint(S, u) {
    var v = 1 - u, a = v * v * v, b = 3 * v * v * u, c = 3 * v * u * u, d = u * u * u;
    return [a * S[0][0] + b * S[1][0] + c * S[2][0] + d * S[3][0], a * S[0][1] + b * S[1][1] + c * S[2][1] + d * S[3][1]];
  }
  function spatialSegments(P) {
    var segs = [], n = P.length;
    function sub(a, b, k) { return [(a[0] - b[0]) * k, (a[1] - b[1]) * k]; }
    for (var k = 0; k < n - 1; k++) {
      var out = k > 0 ? sub(P[k + 1], P[k - 1], 1 / 6) : sub(P[1], P[0], 1 / 6);
      var inn = k + 2 < n ? sub(P[k + 2], P[k], 1 / 6) : sub(P[k + 1], P[k], 1 / 6);
      segs.push([P[k], [P[k][0] + out[0], P[k][1] + out[1]], [P[k + 1][0] - inn[0], P[k + 1][1] - inn[1]], P[k + 1]]);
    }
    return segs;
  }
  /* 道のりの割合 f の点（区間を 400 に分けた折れ線の長さで測る） */
  function pointAlong(S, f) {
    var N = 400, us = [0], L = [0], prev = bezPoint(S, 0);
    for (var i = 1; i <= N; i++) {
      var u = i / N, p = bezPoint(S, u);
      L.push(L[i - 1] + Math.sqrt((p[0] - prev[0]) * (p[0] - prev[0]) + (p[1] - prev[1]) * (p[1] - prev[1])));
      us.push(u); prev = p;
    }
    var total = L[N];
    if (total <= 0) { return [S[0][0], S[0][1]]; }
    var target = f * total, j = 1;
    while (j < N && L[j] < target) { j++; }
    var w = L[j] === L[j - 1] ? 0 : (target - L[j - 1]) / (L[j] - L[j - 1]);
    return bezPoint(S, us[j - 1] + (us[j] - us[j - 1]) * w);
  }

  /* 1 本のキー列 [{t, value, interp}] → 直線でつなげば Premiere と同じ値になるキー列（t は秒、frame は 1 コマの秒） */
  function bakeTrack(list, frame) {
    if (!list || list.length < 2) { return (list || []).map(function (k) { return { t: k.t, value: k.value, interp: "linear" }; }); }
    var is2d = Object.prototype.toString.call(list[0].value) === "[object Array]";
    var segs = is2d ? spatialSegments(list.map(function (k) { return k.value; })) : null;
    /* 1 コマごとに打つ区間（位置は全部、数値は bezier だけ）のキーの数を見積もり、多すぎれば何コマおきかにする */
    var dense = 0;
    for (var s = 0; s < list.length - 1; s++) {
      if (list[s].interp !== "hold" && (is2d || list[s].interp === "bezier")) { dense += Math.max(0, (list[s + 1].t - list[s].t) / frame); }
    }
    var every = Math.max(1, Math.ceil(dense / MAX_BAKED));
    var out = [{ t: list[0].t, value: list[0].value, interp: "linear" }];
    for (var k = 0; k < list.length - 1; k++) {
      var a = list[k], b = list[k + 1], dt = b.t - a.t;
      if (!(dt > 0)) {                                 // 同じ時刻のキーは後ろの値（ExtendScript で同じ時刻に打ったときと同じ）
        if (dt === 0) { out[out.length - 1] = { t: b.t, value: b.value, interp: "linear" }; }
        continue;
      }
      if (a.interp === "hold") {
        var last = (Math.ceil(b.t / frame - 1e-6) - 1) * frame;          // 次のキーの直前のコマ
        if (last > a.t + 1e-9) { out.push({ t: round(last), value: a.value, interp: "linear" }); }
      } else if (is2d || a.interp === "bezier") {
        for (var f = Math.floor(a.t / frame + 1e-6) + every; f * frame < b.t - 1e-6; f += every) {
          var t = f * frame;
          if (t <= a.t + 1e-6) { continue; }
          var fr = fraction(a.interp, (t - a.t) / dt);
          var v = is2d ? pointAlong(segs[k], fr).map(round) : round(a.value + (b.value - a.value) * fr);
          out.push({ t: round(t), value: v, interp: "linear" });
        }
      }
      out.push({ t: b.t, value: b.value, interp: "linear" });
    }
    return out;
  }

  PPM.motion = { easeBezier, fraction, bakeTrack };
  if (typeof module === "object" && module && module.exports) module.exports = PPM;
})(typeof globalThis !== "undefined" ? globalThis : this);

/* ppm-ppro-kit — Premiere の UXP API を安全に使うための型（Cut & SRT と Effect & Design で実機確認した書き方）。
 * 決まり:
 *  - 取引（lockedAccess → executeTransaction）のコールバックは完全に同期。中で await しない。
 *  - Action は取引の中で作る（Premiere 26.3 から必須）。非同期の取得は取引の前に済ませる。
 *  - Action は 1 つずつ足して、失敗を個別に拾う（まとめると 1 つ弾かれただけで全部落ちる）。
 *  - executeTransaction の戻り値 false を必ず見る。全部失敗したら成功と言わない。
 *  - TrackItem のハンドルは保存しない。使う直前に取り直す。 */
(function (root) {
  "use strict";
  const PPM = (root.PPM = root.PPM || {});
  const TICKS_PER_SECOND = 254016000000;
  const BIG_SECONDS = 100000; // 素材時間の上限（MOGRT の入点は約 3600 秒）
  const state = { ppro: null, uxp: null };

  function init(opts) {
    const o = opts || {};
    state.ppro = o.ppro || null;
    state.uxp = o.uxp || null;
    if (PPM.log && typeof PPM.log.init === "function") PPM.log.init({ uxp: o.uxp, tag: o.tag });
  }
  function modules() { return { ppro: state.ppro, uxp: state.uxp }; }

  function err(symptom, why, next) {
    const e = new Error(symptom);
    e.ppm = { symptom, why: why || "", next: next || "" };
    return e;
  }

  function ppro() {
    if (!state.ppro) {
      throw err("Premiere の機能が使えません", "Premiere の外で開いているか、PPM.init が呼ばれていません",
        "Premiere の［ウィンドウ］→［UXP プラグイン］から開き直してください");
    }
    return state.ppro;
  }

  async function resolve(v) { return v && typeof v.then === "function" ? await v : v; }

  function ticksOf(t) {
    if (!t) return 0;
    if (typeof t.ticksNumber === "number") return t.ticksNumber;
    if (t.ticks !== undefined && t.ticks !== null && t.ticks !== "") return Number(t.ticks); // ppm-ignore: J010
    if (typeof t.seconds === "number") return Math.round(t.seconds * TICKS_PER_SECOND);
    return 0;
  }
  function secondsOf(t) {
    if (!t) return 0;
    if (typeof t.seconds === "number") return t.seconds;
    return ticksOf(t) / TICKS_PER_SECOND;
  }
  function time(seconds) { return ppro().TickTime.createWithSeconds(Number(seconds)); }
  function timeFromTicks(ticks) { return ppro().TickTime.createWithTicks(String(Math.round(Number(ticks)))); }

  async function getProjectAndSequence() {
    const project = await ppro().Project.getActiveProject();
    if (!project) {
      throw err("プロジェクトが開かれていません", "この操作は開いているプロジェクトに対して行います", "Premiere でプロジェクトを開いてから、もう一度押してください");
    }
    const sequence = await project.getActiveSequence();
    if (!sequence) {
      throw err("シーケンスが開かれていません", "この操作はタイムラインに出ているシーケンスに対して行います", "シーケンスをタイムラインに開いてから、もう一度押してください");
    }
    return { project, sequence };
  }

  function clipKind(item) {
    // getMediaType は Guid を返すので数値で比べられない。クラス名で分ける
    const n = item && item.constructor && item.constructor.name;
    if (n === "VideoClipTrackItem") return "video";
    if (n === "AudioClipTrackItem") return "audio";
    return "unknown";
  }

  async function describeClip(item) {
    const start = await item.getStartTime();
    const end = await item.getEndTime();
    return {
      item,
      name: (await resolve(item.getName())) || "",
      trackIndex: await resolve(item.getTrackIndex()),
      kind: clipKind(item),
      startTicks: ticksOf(start),
      endTicks: ticksOf(end),
      startSeconds: secondsOf(start),
      endSeconds: secondsOf(end),
    };
  }

  async function getSelectedClips(sequence) {
    const sel = await sequence.getSelection();
    const items = sel ? (await resolve(sel.getTrackItems())) || [] : [];
    const out = [];
    for (const item of items) {
      try { out.push(await describeClip(item)); }
      catch (e) { if (PPM.log) PPM.log.warn("選択の読み取りに失敗", { message: String((e && e.message) || e) }); }
    }
    return out;
  }

  function clipType() {
    const C = state.ppro && state.ppro.Constants && state.ppro.Constants.TrackItemType;
    return C && C.CLIP !== undefined ? C.CLIP : 1;
  }

  async function listTrackClips(sequence, kind, trackIndex) {
    const track = kind === "audio" ? await sequence.getAudioTrack(trackIndex) : await sequence.getVideoTrack(trackIndex);
    if (!track) return [];
    return (await resolve(track.getTrackItems(clipType(), false))) || [];
  }

  async function findClip(sequence, kind, trackIndex, startTicks) {
    for (const it of await listTrackClips(sequence, kind, trackIndex)) {
      if (ticksOf(await it.getStartTime()) === Number(startTicks)) return it;
    }
    return null;
  }

  function transact(project, label, build) {
    const result = { ok: false, added: 0, warnings: [] };
    project.lockedAccess(() => {
      result.ok = project.executeTransaction((ca) => {
        const add = (what, make) => {
          try { ca.addAction(make()); result.added += 1; return true; }
          catch (e) { result.warnings.push(`${what}: ${String((e && e.message) || e)}`); return false; }
        };
        build(add);
      }, label) !== false;
    });
    if (!result.ok) {
      throw err("Premiere が変更を受け付けませんでした", "トラックがロックされているか、対象のクリップが消えた可能性があります",
        "トラックのロックを外し、対象を選び直してから、もう一度押してください");
    }
    if (result.added === 0 && result.warnings.length) {
      throw err("どの変更も受け付けられませんでした", result.warnings.slice(0, 3).join(" / "), "診断ボタンを押し、表示された内容を AI に伝えてください");
    }
    return result;
  }

  function toValue(v) {
    const P = state.ppro && state.ppro.PointF;
    if (Array.isArray(v) && v.length === 2 && P) return new P(Number(v[0]), Number(v[1]));
    return v;
  }

  async function findParam(item, componentMatchNames, paramNames) {
    const chain = await item.getComponentChain();
    const count = await resolve(chain.getComponentCount());
    for (let i = 0; i < count; i++) {
      const comp = await resolve(chain.getComponentAtIndex(i));
      const mn = await resolve(comp.getMatchName());
      if (componentMatchNames.indexOf(mn) < 0) continue;
      const pc = await resolve(comp.getParamCount());
      for (let k = 0; k < pc; k++) {
        const param = await resolve(comp.getParam(k));
        if (param && paramNames.indexOf(param.displayName) >= 0) return { component: comp, param, index: k, chain };
      }
    }
    return null;
  }

  // ppm: action-builder
  function keyframeActions(add, param, inPointSeconds, keys) {
    add("キーを消す", () => param.createRemoveKeyframeRangeAction(time(0), time(BIG_SECONDS)));
    add("時間変化をオン", () => param.createSetTimeVaryingAction(true));
    let n = 0;
    for (const k of keys) {
      const at = inPointSeconds + Number(k.t); // キーの時刻は素材時間（クリップの入点からの位置）
      if (add("キー", () => { const kf = param.createKeyframe(toValue(k.value)); kf.position = time(at); return param.createAddKeyframeAction(kf); })) n += 1;
    }
    // 時間変化をオンにすると時刻 0 に余分なキーが増える（再生ヘッドが 0 のとき）。入点より前を範囲で消す
    if (inPointSeconds > 0.001) add("余分なキーを消す", () => param.createRemoveKeyframeRangeAction(time(0), time(inPointSeconds - 0.0005)));
    return n;
  }

  // ppm: action-builder
  function setValueAction(add, param, value) {
    return add("値", () => param.createSetValueAction(param.createKeyframe(toValue(value)), false));
  }

  async function textComponentIndex(chain) {
    const count = await resolve(chain.getComponentCount());
    for (let i = 0; i < count; i++) {
      const comp = await resolve(chain.getComponentAtIndex(i));
      if ((await resolve(comp.getMatchName())) === "AE.ADBE Text") return i;
    }
    return -1;
  }

  async function addEffect(project, item, matchName) {
    const filter = await ppro().VideoFilterFactory.createComponent(matchName); // 部品は取引の外で作る
    const chain = await item.getComponentChain();
    const at = await textComponentIndex(chain); // テキストの部品の手前に差す（末尾だと文字の下になる）
    // 足した効果は取引が確定するまで設定項目を持たない。値を変えるときは、別の取引で取り直してから
    return transact(project, `効果を追加: ${matchName}`, (add) => {
      if (at >= 0) add("効果", () => chain.createInsertComponentAction(filter, at));
      else add("効果", () => chain.createAppendComponentAction(filter));
    });
  }

  async function addTransition(project, item, matchName, seconds, atStart) {
    const P = ppro();
    const transition = await resolve(P.TransitionFactory.createVideoTransition(String(matchName)));
    const opt = new P.AddTransitionOptions();
    if (typeof opt.setApplyToStart === "function") opt.setApplyToStart(!!atStart);
    // 長さは ticks で渡す（秒で渡すとコマ単位に切り捨てられた: 0.5 秒 → 14 コマ）
    if (typeof opt.setDuration === "function") opt.setDuration(timeFromTicks(Number(seconds) * TICKS_PER_SECOND));
    if (typeof opt.setForceSingleSided === "function") opt.setForceSingleSided(true);
    return transact(project, `トランジション: ${matchName}`, (add) => {
      add("トランジション", () => item.createAddVideoTransitionAction(transition, opt));
    });
  }

  async function addMarkers(project, sequence, markers) {
    const P = ppro();
    const api = await P.Markers.getMarkers(sequence);
    const type = (P.Marker && P.Marker.MARKER_TYPE_COMMENT) || "Comment";
    return transact(project, "マーカーを追加", (add) => {
      for (const m of markers) {
        add(m.name || "マーカー", () => api.createAddMarkerAction(String(m.name || ""), type, time(m.seconds), time(m.duration || 0), String(m.comment || "")));
      }
    });
  }

  function joinPath(folder, name) {
    const f = String(folder);
    const sep = f.indexOf("\\") >= 0 ? "\\" : "/";
    return f.replace(/[\\/]+$/, "") + sep + name;
  }

  async function exportFrame(sequence, seconds, fileName, opts) {
    const o = opts || {};
    const lfs = state.uxp && state.uxp.storage && state.uxp.storage.localFileSystem;
    if (!lfs) throw err("書き出し先を用意できません", "UXP の保存の機能が見つかりません", "Premiere の中で開いてください");
    const folder = await lfs.getDataFolder();
    // 前に書き出した同じ名前のファイルが残っていると、それを「できた」と見誤る。先に消す
    for (const name of [fileName, fileName + ".png"]) {
      try { const old = await folder.getEntry(name); if (old && typeof old.delete === "function") await old.delete(); } catch (e) { /* 無ければよい */ }
    }
    const ok = await resolve(ppro().Exporter.exportSequenceFrame(sequence, time(seconds), fileName, folder.nativePath, o.width || 1920, o.height || 1080));
    if (ok === false) {
      throw err("コマを書き出せませんでした", "Premiere が書き出しを受け付けませんでした", "プレイヘッドをその時刻に置いてから、もう一度試してください");
    }
    // 返事が来ても書き終わっていないことがある（Cut&SRT 2026-10-05）。ファイルができるのを待つ
    const deadline = Date.now() + (o.timeoutMs || 15000);
    while (Date.now() < deadline) {
      for (const name of [fileName, fileName + ".png"]) {
        try { if (await folder.getEntry(name)) return joinPath(folder.nativePath, name); } catch (e) { /* まだ無い */ }
      }
      await new Promise((r) => setTimeout(r, 300));
    }
    throw err("コマの書き出しが終わりませんでした", ok === false ? "Premiere が書き出しを受け付けませんでした" : "待ってもファイルができませんでした",
      "プレイヘッドをその時刻に置いてから、もう一度試してください");
  }

  async function getFrameRate(sequence) {
    try {
      const settings = await sequence.getSettings();
      if (settings && typeof settings.getVideoFrameRate === "function") { // ppm-ignore: J014
        const fr = await settings.getVideoFrameRate(); // ppm-ignore: J014
        const fps = fr && typeof fr.value === "number" ? fr.value : NaN;
        if (Number.isFinite(fps) && fps > 0) {
          // 許容 0.01（60 と 59.94 の差 0.06 を同じと見なさない）
          let timebase = Math.round(fps);
          let ntsc = false;
          if (Math.abs(fps - 29.97) < 0.01) { timebase = 30; ntsc = true; }
          else if (Math.abs(fps - 23.976) < 0.01) { timebase = 24; ntsc = true; }
          else if (Math.abs(fps - 59.94) < 0.01) { timebase = 60; ntsc = true; }
          return { fps: ntsc ? (timebase * 1000) / 1001 : timebase, timebase, ntsc, detected: true };
        }
      }
    } catch (e) {
      if (PPM.log) PPM.log.warn("フレームレートを読めません", { message: String((e && e.message) || e) });
    }
    return { fps: NaN, timebase: null, ntsc: null, detected: false }; // 読めないときに 30 を詰めない（30 決め打ちで壊した事故あり）
  }

  function hostInfo() {
    const u = state.uxp;
    const host = (u && u.host) || {};
    let os = "";
    try { os = require("os").platform(); } catch (e) { os = ""; }
    return { app: host.name || "", version: host.version || "", uxp: (u && u.versions && u.versions.uxp) || "", os };
  }

  Object.assign(PPM, {
    TICKS_PER_SECOND, init, modules, err, resolve, ticksOf, secondsOf, time, timeFromTicks, getProjectAndSequence,
    describeClip, getSelectedClips, listTrackClips, findClip, transact, toValue, findParam, keyframeActions,
    setValueAction, addEffect, addTransition, addMarkers, exportFrame, getFrameRate, hostInfo, joinPath,
  });
  if (typeof module === "object" && module && module.exports) module.exports = PPM;
})(typeof globalThis !== "undefined" ? globalThis : this);

// 本物の premierepro の「形」をまねた偽物。
// 取得は Promise、Action は lockedAccess の中でだけ作れる、executeTransaction は boolean を返す、
// getTrackItems は引数が無いと失敗する、getVideoFrameRate は {value} を返すメソッド。
"use strict";

const TPS = 254016000000;

class TickTime {
  constructor(ticks) {
    this.ticksNumber = Number(ticks);
    this.ticks = String(ticks);
    this.seconds = Number(ticks) / TPS;
  }
  static createWithSeconds(s) { return new TickTime(Math.round(Number(s) * TPS)); }
  static createWithTicks(t) {
    if (typeof t !== "string") throw new Error("createWithTicks には文字列を渡す");
    return new TickTime(Number(t));
  }
}

class PointF { constructor(x, y) { this.x = x; this.y = y; } }

function makeFake(opts = {}) {
  const log = { actions: [], transactions: [], locked: 0, exports: [] };
  let inLock = false;
  const guard = (name) => {
    if (!inLock) throw new Error(`The script object is no longer valid (${name} を lockedAccess の外で作った)`);
  };
  const action = (name, args) => { guard(name); return { __action: name, args }; };

  const makeParam = (displayName, value) => ({
    displayName,
    value,
    createKeyframe(v) { return { value: v, position: null }; },
    createAddKeyframeAction(kf) { return action("addKeyframe", [kf]); },
    createSetTimeVaryingAction(on) { return action("setTimeVarying", [on]); },
    createRemoveKeyframeRangeAction(a, b) { return action("removeKeyframeRange", [a, b]); },
    createSetValueAction(kf, safe) { return action("setValue", [kf, safe]); },
  });
  const motion = {
    params: [makeParam("Position", new PointF(0.5, 0.5)), makeParam("Scale", 100), makeParam("Rotation", 0)],
    async getMatchName() { return "AE.ADBE Motion"; },
    getParamCount() { return 3; },
    getParam(i) { return this.params[i]; },
  };
  const text = { async getMatchName() { return "AE.ADBE Text"; }, getParamCount() { return 0; }, getParam() { return null; } };
  const components = opts.withText ? [motion, text] : [motion];
  const chain = {
    getComponentCount() { return components.length; },
    getComponentAtIndex(i) { return components[i]; },
    createAppendComponentAction(c) { return action("appendComponent", [c]); },
    createInsertComponentAction(c, i) { return action("insertComponent", [c, i]); },
  };

  class VideoClipTrackItem {
    constructor(name, start, end, inPoint, track) { Object.assign(this, { _n: name, _s: start, _e: end, _in: inPoint, _t: track }); }
    async getName() { return this._n; }
    async getStartTime() { return TickTime.createWithSeconds(this._s); }
    async getEndTime() { return TickTime.createWithSeconds(this._e); }
    async getInPoint() { return TickTime.createWithSeconds(this._in); }
    async getTrackIndex() { return this._t; }
    async getComponentChain() { return chain; }
    createSetEndAction(t) { return action("setEnd", [t]); }
    createAddVideoTransitionAction(tr, opt) { return action("addTransition", [tr, opt]); }
  }

  const clips = opts.clips || [new VideoClipTrackItem("A", 0, 2, 3600, 0), new VideoClipTrackItem("B", 2, 5, 0, 1)];
  const selection = { async getTrackItems() { return opts.selected || clips; } };
  const track = {
    getTrackItems(type, includeEmpty) {
      if (type === undefined || includeEmpty === undefined) throw new Error("Not Enough Parameters");
      return clips.filter((c) => c._t === 0);
    },
  };
  const settings = { async getVideoFrameRate() { return { value: opts.fps === undefined ? 30000 / 1001 : opts.fps }; } };
  const sequence = {
    async getSelection() { return selection; },
    async getVideoTrack() { return track; },
    async getVideoTrackCount() { return 1; },
    async getAudioTrack() { return track; },
    async getSettings() { return opts.noFrameRateMethod ? {} : settings; },
    async getPlayerPosition() { return TickTime.createWithSeconds(0); },
  };
  const project = {
    lockedAccess(cb) {
      if (cb.constructor.name === "AsyncFunction") throw new Error("lockedAccess のコールバックは同期のみ");
      inLock = true;
      log.locked += 1;
      try { cb(); } finally { inLock = false; }
    },
    executeTransaction(cb, label) {
      guard("executeTransaction");
      if (cb.constructor.name === "AsyncFunction") throw new Error("executeTransaction のコールバックは同期のみ");
      const added = [];
      const ca = {
        addAction(a) {
          if (!a || !a.__action || opts.rejectAction === a.__action) throw new Error("Invalid parameter.");
          added.push(a);
        },
      };
      cb(ca);
      log.transactions.push({ label, actions: added });
      log.actions.push(...added);
      return opts.commitResult === undefined ? true : opts.commitResult;
    },
    async getActiveSequence() { return opts.noSequence ? null : sequence; },
  };
  const markersApi = {
    createAddMarkerAction(name, type, start, duration, comment) { return action("addMarker", [name, type, start, duration, comment]); },
  };
  class AddTransitionOptions {
    setApplyToStart(v) { this.start = v; }
    setDuration(t) { this.duration = t; }
    setForceSingleSided(v) { this.single = v; }
  }
  const ppro = {
    TickTime,
    PointF,
    AddTransitionOptions,
    Constants: { TrackItemType: { CLIP: 1 } },
    Marker: { MARKER_TYPE_COMMENT: "Comment" },
    Project: { async getActiveProject() { return opts.noProject ? null : project; } },
    Markers: { async getMarkers() { return markersApi; } },
    VideoFilterFactory: { async createComponent(mn) { return { matchName: mn }; } },
    TransitionFactory: { async createVideoTransition(mn) { return { matchName: mn }; } },
    SequenceEditor: { async getEditor() { return { insertMogrtFromPath() {}, createOverwriteItemAction() {} }; } },
    Exporter: { async exportSequenceFrame(seq, t, name, folder, w, h) { log.exports.push({ name, folder, w, h }); return true; } },
  };
  return { ppro, project, sequence, clips, log, chain, motion, VideoClipTrackItem };
}

module.exports = { makeFake, TickTime, PointF, TPS };

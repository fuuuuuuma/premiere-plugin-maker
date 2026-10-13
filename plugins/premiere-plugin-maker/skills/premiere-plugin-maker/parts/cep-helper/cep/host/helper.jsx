/* {{APP_NAME}} の補助（ExtendScript 側）。QE DOM は非公式で、版によって在り処が違うので候補を順に試し、
 * どの呼び方で動いたかを戻り値に入れる。ES3 には JSON が無いので、文字列は自前で作る。 */
var PPM_TICKS = 254016000000;

function ppmEscape(text) {
    return String(text).replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/[\r\n]/g, " ");
}

function ppmSerialize(obj) {
    var parts = [];
    for (var key in obj) {
        if (!obj.hasOwnProperty(key)) { continue; }
        var v = obj[key];
        if (v instanceof Array) {
            var items = [];
            for (var i = 0; i < v.length; i++) { items.push('"' + ppmEscape(v[i]) + '"'); }
            parts.push('"' + key + '":[' + items.join(",") + "]");
        } else if (typeof v === "boolean") {
            parts.push('"' + key + '":' + (v ? "true" : "false"));
        } else if (typeof v === "number") {
            parts.push('"' + key + '":' + v);
        } else {
            parts.push('"' + key + '":"' + ppmEscape(v) + '"');
        }
    }
    return "{" + parts.join(",") + "}";
}

function ppmQeSequence() {
    if (typeof app.enableQE === "function") { app.enableQE(); }
    if (typeof qe === "undefined" || !qe || !qe.project) { return null; }
    if (typeof qe.project.getActiveSequence === "function") { return qe.project.getActiveSequence(); }
    return qe.project.activeSequence || null;
}

function ppmFeatures() {
    return ppmSerialize({ ok: true, features: ["play", "stop", "razor"] });
}

function ppmSeek(seconds) {
    var seq = app.project ? app.project.activeSequence : null;
    if (!seq) { return false; }
    seq.setPlayerPosition(String(Math.round(seconds * PPM_TICKS)));
    return true;
}

function ppmPlay(seconds, speed) {
    var r = { ok: false, method: "", error: "" };
    try {
        if (seconds !== null && seconds !== undefined && seconds >= 0) { ppmSeek(seconds); }
        var qs = ppmQeSequence();
        if (qs && qs.player && typeof qs.player.play === "function") { qs.player.play(speed || 1); r.ok = true; r.method = "qe.sequence.player.play"; }
        else { r.error = "QE の再生が見つかりません"; }
    } catch (e) { r.error = String(e); }
    return ppmSerialize(r);
}

function ppmStop() {
    var r = { ok: false, method: "", error: "" };
    try {
        var qs = ppmQeSequence();
        if (qs && qs.player && typeof qs.player.stop === "function") { qs.player.stop(); r.ok = true; r.method = "qe.sequence.player.stop"; }
        else { r.error = "QE の停止が見つかりません"; }
    } catch (e) { r.error = String(e); }
    return ppmSerialize(r);
}

function ppmRazor(kind, trackIndex, seconds) {
    var r = { ok: false, method: "", error: "" };
    try {
        var qs = ppmQeSequence();
        if (!qs) { r.error = "QE のシーケンスがありません"; return ppmSerialize(r); }
        var track = kind === "audio" ? qs.getAudioTrackAt(trackIndex) : qs.getVideoTrackAt(trackIndex);
        if (!track || typeof track.razor !== "function") { r.error = "QE の razor が見つかりません"; return ppmSerialize(r); }
        var seq = app.project.activeSequence;
        var tpf = Number(seq.timebase);
        // フレームの境目ちょうどではなく 1/4 フレーム内側を渡す（境目の丸めで隣のフレームを切らないため）
        var ticks = Math.round(seconds * PPM_TICKS + tpf / 4);
        var time = new Time();
        time.ticks = String(ticks);
        track.razor(time.getFormatted(seq.getSettings().videoFrameRate, app.project.activeSequence.videoDisplayFormat));
        r.ok = true;
        r.method = "qe.track.razor";
    } catch (e) { r.error = String(e); }
    return ppmSerialize(r);
}

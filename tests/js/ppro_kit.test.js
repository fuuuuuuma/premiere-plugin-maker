"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { loadParts } = require("./load_parts");
const { makeFake, TPS } = require("./fake_ppro");

function kit(opts) {
  const fake = makeFake(opts);
  const ctx = loadParts(["logger/lib/ppm-logger.js", "ppro-kit/lib/ppm-ppro-kit.js"]);
  ctx.PPM.init({ ppro: fake.ppro, uxp: null, tag: "t" });
  return { PPM: ctx.PPM, fake };
}

test("プロジェクトが無いと 3 点つきのエラー", async () => {
  const { PPM } = kit({ noProject: true });
  await assert.rejects(PPM.getProjectAndSequence(), (e) => e.ppm && e.ppm.symptom.includes("プロジェクト") && e.ppm.next.length > 0);
});

test("選択したクリップを ticks と秒で返す", async () => {
  const { PPM } = kit();
  const { sequence } = await PPM.getProjectAndSequence();
  const clips = await PPM.getSelectedClips(sequence);
  assert.equal(clips.length, 2);
  assert.equal(clips[0].kind, "video");
  assert.equal(clips[1].startTicks, 2 * TPS);
  assert.equal(clips[1].endSeconds, 5);
});

test("transact はロックの中で Action を作り、件数を返す", async () => {
  const { PPM, fake } = kit();
  const { project } = await PPM.getProjectAndSequence();
  const r = PPM.transact(project, "終わりを動かす", (add) => { add("end", () => fake.clips[0].createSetEndAction(PPM.time(1))); });
  assert.equal(r.ok, true);
  assert.equal(r.added, 1);
  assert.equal(fake.log.transactions[0].label, "終わりを動かす");
});

test("Premiere が受け付けないとエラーにする", async () => {
  const { PPM, fake } = kit({ commitResult: false });
  const { project } = await PPM.getProjectAndSequence();
  assert.throws(() => PPM.transact(project, "u", (add) => add("end", () => fake.clips[0].createSetEndAction(PPM.time(1)))), /受け付けませんでした/);
});

test("1 つ弾かれても残りは足す。全部弾かれたら成功と言わない", async () => {
  const { PPM, fake } = kit({ rejectAction: "setEnd" });
  const { project } = await PPM.getProjectAndSequence();
  assert.throws(() => PPM.transact(project, "u", (add) => add("end", () => fake.clips[0].createSetEndAction(PPM.time(1)))), /どの変更も/);
  const r = PPM.transact(project, "u2", (add) => {
    add("end", () => fake.clips[0].createSetEndAction(PPM.time(1)));
    add("tr", () => fake.clips[0].createAddVideoTransitionAction({}, {}));
  });
  assert.equal(r.added, 1);
  assert.equal(r.warnings.length, 1);
});

test("キーは入点を足した素材時間に打ち、余分なキーを範囲で消す", async () => {
  const { PPM, fake } = kit();
  const { project } = await PPM.getProjectAndSequence();
  const scale = fake.motion.params[1];
  PPM.transact(project, "zoom", (add) => { PPM.keyframeActions(add, scale, 3600, [{ t: 0, value: 100 }, { t: 2, value: 110 }]); });
  const names = fake.log.actions.map((a) => a.__action);
  assert.deepEqual(names, ["removeKeyframeRange", "setTimeVarying", "addKeyframe", "addKeyframe", "removeKeyframeRange"]);
  assert.equal(fake.log.actions[3].args[0].position.seconds, 3602);
});

test("findParam は表示名の日本語・英語どちらでも見つける", async () => {
  const { PPM, fake } = kit();
  const found = await PPM.findParam(fake.clips[0], ["AE.ADBE Motion"], ["Scale", "スケール"]);
  assert.equal(found.index, 1);
  assert.equal(await PPM.findParam(fake.clips[0], ["AE.ADBE Opacity"], ["Opacity"]), null);
});

test("効果はテキストの部品の手前に差す", async () => {
  const { PPM, fake } = kit({ withText: true });
  const { project } = await PPM.getProjectAndSequence();
  await PPM.addEffect(project, fake.clips[0], "AE.ADBE Geometry2");
  const a = fake.log.actions[0];
  assert.equal(a.__action, "insertComponent");
  assert.equal(a.args[1], 1);
});

test("トランジションの長さは ticks で渡す", async () => {
  const { PPM, fake } = kit();
  const { project } = await PPM.getProjectAndSequence();
  await PPM.addTransition(project, fake.clips[0], "AE.ADBE Cross Dissolve New", 0.5, true);
  assert.equal(fake.log.actions[0].args[1].duration.ticksNumber, 0.5 * TPS);
});

test("マーカーは 1 件ずつ Action にする", async () => {
  const { PPM, fake } = kit();
  const { project, sequence } = await PPM.getProjectAndSequence();
  await PPM.addMarkers(project, sequence, [{ seconds: 1, name: "a" }, { seconds: 2, name: "b", comment: "c" }]);
  assert.equal(fake.log.actions.length, 2);
  assert.equal(fake.log.actions[1].args[4], "c");
});

test("フレームレート: 29.97 は 30 の NTSC。読めなければ 30 を詰めない", async () => {
  let { PPM } = kit();
  let { sequence } = await PPM.getProjectAndSequence();
  const fr = await PPM.getFrameRate(sequence);
  assert.equal(fr.timebase, 30);
  assert.equal(fr.ntsc, true);
  ({ PPM } = kit({ noFrameRateMethod: true }));
  ({ sequence } = await PPM.getProjectAndSequence());
  const none = await PPM.getFrameRate(sequence);
  assert.equal(none.detected, false);
  assert.ok(Number.isNaN(none.fps));
});

test("findClip は getTrackItems に引数 2 つを渡す", async () => {
  const { PPM } = kit();
  const { sequence } = await PPM.getProjectAndSequence();
  const found = await PPM.findClip(sequence, "video", 0, 0);
  assert.equal(await found.getName(), "A");
});

test("ticksOf は ticksNumber → ticks → seconds の順に読む", () => {
  const { PPM } = kit();
  assert.equal(PPM.ticksOf({ ticksNumber: 5, ticks: "0" }), 5);
  assert.equal(PPM.ticksOf({ ticks: "7" }), 7);
  assert.equal(PPM.ticksOf({ seconds: 1 }), TPS);
  assert.equal(PPM.ticksOf(null), 0);
});

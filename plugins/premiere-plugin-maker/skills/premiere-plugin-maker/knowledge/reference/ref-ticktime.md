---
id: ref-ticktime
title: TickTime と時間の単位
kind: reference
tags: [TickTime, ticks, 時間, フレーム, timebase, ntsc, BigInt, 素材時間, ExtendScript, キーフレーム]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: 1 秒は 254016000000 ticks。生成は文字列で、読み取りは ticksNumber を先に。フレームへの換算は宣言の timebase で。ExtendScript のキーの時刻は素材時間
parts: [ppro-kit, fcpxml]
related: [ref-fcp7-xml, ref-keyframe-interpolation]
---
## 仕様

**Premiere の時間は「ticks（ティック）」という細かい単位で数えます。**

- 1 秒 ＝ 254016000000 ticks。この数は UXP でも ExtendScript でも同じです。
- 1 コマ ＝ 254016000000 ÷ fps ticks。たとえば 29.97 fps なら 8475667200 ticks、30 fps なら 8467200000 ticks です。iPhone で撮った素材のシーケンスは約 29.997 fps になることがあり、その場合 1 コマは 8467978982 ticks のように割り切れない値になります。

**UXP（premierepro モジュール）の TickTime**

| 操作 | 書き方 | 注意 |
|---|---|---|
| 秒から作る | `ppro.TickTime.createWithSeconds(sec)` | コマ単位に丸められることがある |
| ticks から作る | `ppro.TickTime.createWithTicks(String(ticks))` | **引数は文字列**。数値のまま渡さない |
| 足す・引く | `t.add(other)`、`t.subtract(other)` | TickTime どうしで計算する |
| 読む | `t.ticksNumber`（数値）→ `t.ticks`（文字列）→ `t.seconds` の順に試す | 下の「注意」を見てください |

ticks は大きな整数です。JavaScript の数値（約 9×10^15 まで正確）を超える長さのシーケンスもあり得るので、足し引きをするときは `BigInt` を使うか、`ticksNumber` で扱える範囲かを確かめます。ExtendScript の `Time` オブジェクトでは `t.ticks = "文字列"` と**文字列で代入**します。上限は int64（約 9.2×10^18）で、`1e9` 秒のような巨大な値を入れると失敗するか、折り返します。

**フレームとの換算**

- フレームから秒に直すときは、**宣言された timebase と ntsc の値**を使います。`ntsc` が真なら fps は `timebase × 1000 ÷ 1001`（30 → 29.97、24 → 23.976、60 → 59.94）、偽なら `timebase` そのものです。
- 実際の fps（29.998 のような値）は使いません。可変フレームレートの素材は、宣言の timebase が整数に切り捨てられます。実際の fps で換算すると、後ろへ行くほどずれが積もります（FCP XML の話は ref-fcp7-xml）。
- シーケンス上のフレーム番号は `round(start.ticks ÷ シーケンスの timebase ticks)` で出します。FCP XML の `<start>` と同じ物差しなので、XML の中のクリップを特定する鍵にできます。

**ExtendScript のキーフレームの時刻は「素材時間」**

`addKey` などに渡す時刻の基準は、タイムラインの先頭ではなく、クリップの**素材側の入点**です。クリップの頭から t 秒の場所は `入点の ticks ＋ t × 254016000000` と書きます。MOGRT（モーショングラフィックステンプレート）のクリップは入点が約 3600 秒の所にあるので、基準を間違えると 1 時間ずれた場所にキーが打たれます。

## 例

```js
// UXP: 秒の値を ticks にして、TickTime を作る（引数は文字列）
const TPS = 254016000000;
const t = ppro.TickTime.createWithTicks(String(Math.round(1.5 * TPS)));

// 読み取りは防御して順に試す（ticks だけを信用しない）
function ticksOf(t) {
  if (typeof t.ticksNumber === "number") return t.ticksNumber;
  if (t.ticks !== undefined && t.ticks !== "") return Number(t.ticks);
  return Math.round(t.seconds * TPS);
}
```

```js
// ExtendScript: クリップの頭から 0.4 秒の場所（素材時間）
var tm = new Time();
tm.ticks = String(Math.round(Number(item.inPoint.ticks) + 0.4 * 254016000000));
```

## 注意

- **記録が割れている点**：Cut & SRT の実機では `.ticks` が常に 0 を返し（Premiere 26.3）、`.ticksNumber` が正しい値でした。一方、Effect & Design は 26.5 で `.ticks` を文字列として使って動いています。原因（版の違いか、使い方の違いか）は確かめていません。キットの部品（ppro-kit の `ticksOf`）は `.ticksNumber` を先に読む順にしています。
- 長さを秒で渡すと、コマ単位に切り捨てられます（0.5 秒が 14 コマになった記録）。トランジションの長さなど正確さが要る所は、ticks で渡します。
- クリップのハンドルを保存して後で使わないでください。使う直前に、開始 ticks などの情報からタイムラインを数え直して取り直します。
- XML の `<timebase>29</timebase>` が実際の約 29.997 fps と違うように、宣言と実際は一致しません。XML から換算せず、Premiere 側（ExtendScript または UXP）で出したフレーム番号を使う場面もあります。

## 出どころ

- Cut & SRT の API 一覧と失敗記録（Premiere 26.3、2026-07：`.ticks` が 0 を返した件、TickTime の作り方）
- Effect & Design の実機の記録（Premiere 26.5、2026-09：素材時間の基準、MOGRT の入点、int64 の上限、秒指定がコマに切り捨てられる件）
- キットの部品 ppro-kit と fcpxml の実装

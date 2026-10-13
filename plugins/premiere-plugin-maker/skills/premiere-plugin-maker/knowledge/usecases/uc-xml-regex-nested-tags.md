---
id: uc-xml-regex-nested-tags
title: クリップ情報の取り出しが V1 の途中で止まる（正規表現で XML を切った）
kind: usecase
tags: [XML, FCP7 XML, 正規表現, ElementTree, clipitem, パーサ]
os: [mac, windows]
premiere: ">=25.6"
status: verified
summary: clipitem の中に同名のタグ（video）が入れ子になるので、正規表現は最初の閉じタグで止まる。XML は必ず XML パーサで読む
parts: [fcpxml]
related: [uc-xml-dangling-file, uc-xml-invalid-input-fail-closed, ref-fcp7-xml]
---
## 症状

タイムラインのクリップ情報を XML から取り出す処理が、V1 の途中で止まる。V3 のクリップが読めない。

## 原因

FCP7 XML の `<clipitem>` の中には、`<file><media><video>` のように、外側と同じ名前（`video`）のタグが入れ子で出てくる。`<video> … </video>` を正規表現で切ると、最初に出てくる閉じタグ `</video>` で終わってしまい、本来の外側のかたまりを最後まで読めない。

## 直し方

1. 正規表現をやめ、XML パーサ（Python の `xml.etree.ElementTree` など）で木として辿る。
2. XML に外部の読み込みが混ざる危険を避けるため、読む前に `DOCTYPE` を取り除き、`<!ENTITY` を含む入力は拒否する。
3. 実際の Premiere が書いた XML の抜粋を、試験用に保存しておく（シーケンスの `clipitem` の例）。

## 再発防止

- 「XML は正規表現で読まない」を、プラグインの決まりにする。
- 新しい項目を読むときは、実際の XML で場所を確かめてから書く。たとえば MOGRT の本文は、`effectid` が `GraphicAndType` の effect（名前が「本文」）に入っている（`uc-mogrt-telop-text-not-greppable`）。

## 出典

- Effect & Design の実機の記録（Premiere 26.5）。実際の XML でテロップの本文を取り出せることまで確認した

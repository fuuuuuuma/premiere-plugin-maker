---
id: uc-install-udt-package-stale
title: UDT の Package が古い版の .ccx を作る。上書きの入れ直しでは古い版が動き続ける
kind: usecase
tags: [UDT, UPIA, ccx, 導入, 更新, remove, install]
os: [mac, windows]
premiere: ">=25.6"
status: unverified
summary: .ccx は上書きでなく「remove してから install」で入れる。UDT の Package は同じ ID の登録済みの古いエントリを掴むので、先に Remove してから Add し、できた物の版を確かめる
parts: [packaging]
related: [core-versioning-release, uc-install-same-version, uc-install-cc-signin-wipes, uc-install-udt-connects-once]
---
## 症状

.ccx を上書きで入れ直しても、古い版が動き続ける。登録簿（UXP のプラグイン一覧）に、同じ ID の古い版が並ぶ。UDT の Package で .ccx を作ると、古い版の物ができる。

## 原因

パネルは、.ccx から外部プラグインのフォルダ（`UXP/Plugins/External/<ID>_<版>`）に写されたコピーが読まれる。上書きでは古いコピーが残る。UDT の Package は、同じ ID の登録済みのエントリを掴んで、古い内容の .ccx を作る。

## 直し方

1. 導入は、`UnifiedPluginInstallerAgent`（UPIA）で `--remove "<プラグイン名>"` をしてから `--install <.ccx>` する。
2. UDT で作るときは、先に既存の登録を Remove してから Add する。できた物の `build_info.json` で版を確かめる。
3. 自作の .ccx が入るかどうかは、記録が割れている。ある時点の記録は「自作 .ccx は不可」、後の記録は「`--staging-only` で出した staging から .ccx を作り、検査に通せば可」と覆した。キットは後者を使うが、導入までは実機で通していない。

## 再発防止

- 更新機構が無い UXP の配布は、remove → install を手順にし、成果物で版を確かめる。
- UPIA で導入したあとの再起動が要るかどうかも記録が割れている（補助プラグインでは不要、パネルでは要る、という記録）。再起動して確かめる。

## 出どころ

- Cut & SRT と Effect & Design の作業記録（2026-08-25〜09-27）

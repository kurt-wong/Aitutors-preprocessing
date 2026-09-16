# IMPLEMENTATION GAP LIST — preprocessing → Contract v0.2

> Status: **v1.6(2026-09-16,DEC-027 冻结收口轮:Freeze Evidence v1 + 最终一致性检查 C1-C9 全 PASS(VERIFIED)= READY FOR CONTRACT FREEZE(Producer 侧))** · Basis: Owner Decision Record v1.8(§1 总纲 + §1bis + §1ter + §1quater + §1quinquies DEC-023 + §1septies DEC-025 + §1octies DEC-026 + **§1novies DEC-027**)+ Freeze Candidate Final v1 + Step1-Step2 Verification Report v1 + **Freeze Evidence v1**
> **DEC-027 冻结收口结果(最高优先,2026-09-16)**:Freeze Evidence = `INTEGRATION/PREPROCESSING-CONTRACT-v0.2-FREEZE-EVIDENCE-v1.md`;最终一致性检查(`scripts/freeze_evidence_final_check.py`,只读,全部从当前磁盘字节独立重推导)= C1-C9 全 PASS,overall **VERIFIED,零 BLOCKER**;文档交叉核验完成(Facts v2 → v2.5 现行态消歧 / DepMap / Alignment v4 行内废止标识);Decision ≠ Implementation(V3 D-7/D-8/D-9/D-11 仍全部 not started,不得因契约冻结声称 V3 已具验证能力)。
> **DEC-026 执行结果(最高优先,2026-09-16)**:Step 1 接口快照冻结(`data/interface_scope_snapshot_step1.json` + audit `interface_scope_prebackfill` corpus `4ad3458b…`;87/87 R50 manifest+source 双成员 sha 全一致,IR 71/71 一致)+ Step 2 回填 **`source_content_sha256` × 87/87 DONE,验证 PASS**(Manifest hash == IR hash 71/71;全量 87/87 == source bytes;剥键重序列化 sha == R50 基线 87/87 = 仅追加一键的内容寻址证明;source 字节零漂移;R50 DRIFT = 恰 87 manifest / missing 0;新配对基线 = audit `interface_scope_postbackfill` corpus `24af8f56…` verify ok)。详件 = `PREPROCESSING-STEP1-STEP2-VERIFICATION-REPORT-v1.md`。
> **DEC-025 命名变更(最高优先,覆盖本文件一切旧引用)**:跨系统 Source Identity 字段 = **`source_content_sha256`**(= SHA256(raw bytes),64 小写 hex 不变);原契约键 `source_version_id` 一名**此后仅指 V3 内部 UUID FK**(保持内部含义,不作跨系统身份键;OQ-8′ 关闭);path 禁参与 identity 判断不变;Review v1 的 N-1~N-4(V3 侧改名)方案**作废**。另:bytes 能力要求已冻结(Decision 2:V3 须获取 raw bytes + 独立重算 SHA256 + 与 `source_content_sha256` 比较 + 不一致 fail-closed;传输方式不冻结)。
> DEC-023 生效更新(沿用):①**G1 格式已裁 = 64 字符小写 hex**(算法/格式不变,字段名按 DEC-025 切换);②**path 非身份原则**:`source_file` = locator,任何文档不得暗示 path 参与身份判断(交付形态问题收窄为"bytes 传输方式");③**G3/G4 再生成已裁 = 允许但四约束**(bytes 不变/id 一致/新 IR 绑定 id/重过 identity verification + semantic validation)+ 四禁,执行待令;④**G5 词表终局**:semantic = ready/incomplete/unknown,decision = pending_review/approved/rejected;unknown 路由已裁 = reviewable record → pending_review workflow(载体仍未裁);⑤16 份状态 = **Identity Available / Semantic Pending(可恢复)**。
> Purpose: 逐缺口列出"是什么 / 差多少 / 谁批 / 什么顺序"。每条含:现状证据、目标态(裁决锚定)、实施动作性质、批准依赖、验收判据。
> 纪律:全部为 producer 侧动作;零执行;UNKNOWN 明示。

---

## G1 — manifest 缺 source identity 字段(**DEC-026 已执行:87/87 回填 DONE + 验证 PASS**)

| 属性 | 内容 |
|---|---|
| 现状 | **已执行(DEC-026 Step 2)**:接口面 87/87 manifest 携 `source_content_sha256`(回填前 0/166;79 份 v1 legacy 面未回填,属隔离面不入接口) |
| 目标态 | 每份入接口面的 manifest 携 **`source_content_sha256`** = SHA-256(源 md raw bytes),**格式 = 64 字符小写 hex(DEC-023 已裁,与现有 `ir.source_sha256` 实证形态一致;字段名 = DEC-025 Decision 1)**;与 IR `source_sha256` / `provenance.source_version` 同值;**身份自足性(DEC-B1)**:该字段独立可验证,不需要 IR 在场 —— **已达成(16 份无 IR 者身份自足)** |
| 生产侧就绪度 | 算法+代码就绪(`resolver_reference.py:52-53`);执行脚本 = `scripts/interface_scope_step2_backfill.py`(确定性 / fail-closed / 可重入) |
| 实施动作 | ①schema 字段定义(Contract v0.2 正文,= FC-1 照录)→ ②回填(数据写入)—— **②已执行 87/87** |
| 批准依赖 | **已全部下达**:字段名/算法/格式(DEC-023 + DEC-025)+ Step 2 回填执行令(DEC-026 二) |
| **硬约束(E2,已落地)** | 87/87 manifest 为 R50 基线成员 → 回填致 R50 DRIFT **已发生且已对账**:drift 集合 = 恰 87 manifest,missing 0;Step 1 快照(pre)+ post 快照承接接口面基线角色,R50 保留为历史基线(血统注记 = Verification Report §1/§3.5) |
| 验收判据 | **已验证 PASS**:`source_content_sha256` == sha256(当前 md 字节)87/87;== IR `source_sha256` 71/71(有 IR 者);剥键重序列化 sha == R50 基线 87/87(仅追加一键的内容寻址证明);Step 1/post 双快照 verify PASS |

## G2 — 双层关联键升级(B1;**DEC-B1 已裁唯一键**)

| 属性 | 内容 |
|---|---|
| 现状 | IR ↔ manifest 关联 = `ir.source_file == manifest.source_file`(绝对路径字符串值相等,probe_v2 `p4`) |
| 目标态(**已裁,DEC-B1 + DEC-025**) | 关联 = **`source_content_sha256`** **唯一**关联键;路径值相等不是合规关联 |
| 实施动作 | IR 侧字段已具备(`source_sha256` 即该值);manifest 侧随 G1;**无独立数据动作** |
| 批准依赖 | 随 G1;**DEC-023 已裁**:`source_file` 保留 = locator(相对路径化不再是身份议题,若做属 locator 改善另议);bytes 能力要求**已冻结(DEC-025 Decision 2)**,传输方式不冻结(delivery logistics) |
| 验收判据 | **已验证 PASS(DEC-026)**:87 份接口面 `manifest.source_content_sha256 == ir.source_sha256` 全量成立(有 IR 者 71/71);无 IR 者(16)身份自足(DEC-B1) |

## G3 — IR 覆盖面 71/166(B1;**当前面已裁 = 71 冻结面**)

| 属性 | 内容 |
|---|---|
| 现状 | 88 记录 / 71 ADMITTED(v2 目录面全集);95 份 manifest(166−71)无语义承载;接口面 87 内 16 份无 IR |
| 目标态(DEC-023 Part 3 更新) | **IR semantic consumption current frozen scope = 71 ADMITTED**;16 份接口面内无 IR 成员 = **Identity Available / Semantic Pending(可恢复,非永久缺失)**;**再生成已裁 = 允许**,但四约束:①source bytes 不允许改变 ②source_version_id 保持一致 ③新 IR 必须绑定 source_version_id ④生成后必须重过 identity verification + semantic validation |
| **DEC-B1 语义** | source 身份不依赖 IR 存在 → **IR 现状 71 不阻塞身份权威性**;16 份无 IR 的接口面成员仍在接口面内 |
| **四禁(DEC-023 Part 3)** | 禁修改原 source / 禁重新 OCR 覆盖原 source / 禁生成新 identity / 禁用新 hash 替代旧 hash——IR 再生成不得触碰身份层 |
| 实施动作(若执行) | 重跑 `resolver_reference.py` 扩批 = 新数据生成动作;替换 r52 工件 = 基线治理问题(冻结工件不可回改纪律) |
| 批准依赖 | **允许已裁;执行仍待 Owner 令**(范围/批次/R52 工件版本策略未裁)——本轮禁执行(DEC-023 Part 8) |
| 验收判据(裁决已给方向) | 新 IR 逐份:`source_sha256` == 原 `source_version_id`(bytes 不变复证)+ identity verification + semantic validation 双通过 |

## G4 — IR 持续产出机制(B1)

| 属性 | 内容 |
|---|---|
| 现状 | R52 一次性工件,自冻结未再生成;daemon 只产 md,不产 IR |
| 目标态 | **持续产出机制仍 UNKNOWN**(未裁是否需要;DEC-022 Part 6 暂缓 daemon)。注:16 份 Semantic Pending 的**单次再生成已裁允许**(G3,四约束)——"允许再生成"≠"建立持续机制",两者分裁 |
| 批准依赖 | Owner 令 |
| 备注 | 若不要求,IR 权威性 = 冻结 + sha 自洽(现状语义,v0.2 披露即可) |

## G5 — B3 守卫与语义状态机载体(**词表已裁 DEC-021 D3,载体未裁**)

| 属性 | 内容 |
|---|---|
| 现状 | 生成链零 unit_type 值域检查;恰 1 例非标值原样进 ADMITTED(行为符合"显式保留/禁转换/禁丢弃",但无机制保证);状态机无载体 |
| 目标态(**DEC-023 Part 5-6 词表终局 + 路由已裁**) | semantic = `ready/incomplete/unknown`;decision = `pending_review/approved/rejected`;两体系禁止合并。unknown semantic unit:禁 silent skip / automatic conversion / silent fallback,**必须产生 reviewable record → 进入 pending_review workflow**;生产侧守卫 fail-closed 目标 = 值域外单元显式产 reviewable record 落 pending_review |
| 生产侧实施动作 | ①生成链(`resolver_reference.py` unit_type 复制点 `:152` 前)引入值域检查;②标记载体字段随 v0.2 定义(**载体未裁**) |
| 批准依赖 | A6 载体定义(v0.2 正文)+ A7 守卫实施令 |
| **硬约束** | 存量 1 例所在 manifest 亦为 R50 成员 + IR 冻结工件成员——**存量处置**必须配对基线决策;按 D3 口径该存量单元非 READY,其在接口上的呈现态 = UNKNOWN(需 v0.2 明示冻结工件中非标值的接口语义) |
| 验收判据 | ①构造值域外单元过生成链 → 必产显式态(测试钉);②存量 1 例在接口上呈现 v0.2 规定态 |

## G6 — v1 legacy 面 79 份接口地位(**已裁 DEC-021 D2 = 隔离**)

| 属性 | 内容 |
|---|---|
| 现状 | 79 份 `identity_version` 缺失;C-IN-1 下必拒;另有 1 份"目录 v2 / 字段 legacy"混入件已被 IR 拒收(REJECTED_V1) |
| 目标态(**已裁**) | **historical asset,not part of v0.2 interface**;四禁 = 禁自动迁移/补齐/重生成 IR/加入 87 接口;未来处置 = 独立 Legacy Migration Plan |
| 剩余动作 | v0.2 文字层披露形态(C.6,弱) |

## G7 — D2 恢复产物的接口地位(OQ-3,弱缺口)

| 属性 | 内容 |
|---|---|
| 现状 | 1,394 份待恢复;`_imgs/` 资产是否入接口面未定义 |
| 目标态 | **UNKNOWN**(v0.2 定) |
| 关联 | D2 就地改写 md 字节 → 改变该 md 的 sha256 → 若已回填 `source_version_id` 则失配(见 Dependency Map) |

---

## 汇总矩阵

| Gap | 裁决 | 类型 | 批准项 | 阻塞 v0.2 冻结? |
|---|---|---|---|---|
| G1 | B1 + DEC-023(算法/格式)+ **DEC-025(字段名 = `source_content_sha256`)**,范围 87 | schema + 数据 | **全部已下达并执行(DEC-026)** | **否 —— DONE(87/87 回填 + 验证 PASS)** |
| G2 | B1(**唯一键已裁**)+ DEC-023(path 非身份) | 派生(随 G1) | — | 否 —— **验证 PASS(71/71)** |
| G3 | B1 + **DEC-023(再生成允许+四约束)** | 数据生成 | 执行令(批次/R52 版本策略) | 否 |
| G4 | B1(持续机制仍未裁;单次再生成 ≠ 持续机制) | 机制 | Owner 令 | 否 |
| G5 | B3 + **DEC-023(词表终局 + unknown 路由已裁)** | 机制 + 数据 | **仅剩载体(字段名/落点/reviewable record 形态)**+ 执行令 | **载体定义是**(守卫实施可后置) |
| G6 | **DEC-021 已裁 = 隔离** | 文字层披露 | — | 否(披露形态随 v0.2) |
| G7 | B1 弱 | 文字层 | 随 v0.2 | 否 |
| C.1 | DEC-021 D4 | 接口面表达 + Step 1 快照载体/血统 | **执行令已下达并执行(DEC-026)**:载体 = `data/interface_scope_snapshot_step1.json` + pre/post 双 audit 快照;v0.2 正文对该载体的引用形态待 Owner/Claude 追认 | **否**(表达已物化) |

**最小冻结集(DEC-026 后终版)**:接口面 87 的表达(C.1)**已物化**(Step 1 快照工件;正文引用形态待追认);**唯一剩余必须落字项 = G5 两层状态载体(含 reviewable record 形态)**;G1/G2 数据动作已执行完毕。G1 字段定义三要素(名 = `source_content_sha256` / 算法 SHA256(raw bytes) / 格式 64 小写 hex)v0.2 直接照录 Freeze Candidate Final FC-1;bytes 能力要求已定稿(FC-2)。面口径以"87 接口面 / IR 71 当前消费面 / 16 Semantic Pending / 79 historical"写入 v0.2。

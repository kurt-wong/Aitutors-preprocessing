# IMPLEMENTATION GAP LIST — preprocessing → Contract v0.2

> Status: **v1.3(2026-09-16,DEC-023 Interface Finalization Revision v1 后更新)** · Basis: Owner Decision Record v1.4(§1 总纲 + §1bis + §1ter + §1quater + **§1quinquies DEC-023**)+ Producer Alignment v5
> DEC-023 生效更新:①**G1 格式已裁 = 64 字符小写 hex**(DEC-SOURCE-IDENTITY,字段名/算法/格式三者全部关闭);②**path 非身份原则**:`source_file` = locator,任何文档不得暗示 path 参与身份判断(交付形态问题收窄为"bytes 传输方式");③**G3/G4 再生成已裁 = 允许但四约束**(bytes 不变/id 一致/新 IR 绑定 id/重过 identity verification + semantic validation)+ 四禁,执行待令;④**G5 词表终局**:semantic = ready/incomplete/unknown,decision = pending_review/approved/rejected;unknown 路由已裁 = reviewable record → pending_review workflow(载体仍未裁);⑤16 份状态 = **Identity Available / Semantic Pending(可恢复)**。
> Purpose: 逐缺口列出"是什么 / 差多少 / 谁批 / 什么顺序"。每条含:现状证据、目标态(裁决锚定)、实施动作性质、批准依赖、验收判据。
> 纪律:全部为 producer 侧动作;零执行;UNKNOWN 明示。

---

## G1 — manifest 缺 `source_version_id`(B1 核心缺口)

| 属性 | 内容 |
|---|---|
| 现状 | 0/166 manifest 携 `source_version_id`;0/166 携任何 sha 键(probe_v2 `p1b`) |
| 目标态 | 每份入接口面的 manifest 携 `source_version_id` = SHA-256(源 md raw bytes),**格式 = 64 字符小写 hex(DEC-023 已裁,与现有 `ir.source_sha256` 实证形态一致)**;与 IR `source_sha256` / `provenance.source_version` 同值;**身份自足性(DEC-B1)**:该字段独立可验证,不需要 IR 在场 |
| 生产侧就绪度 | 算法+代码就绪(`resolver_reference.py:52-53`);71 份值已存在(IR 面),manifest 侧字段为空;**DEC-B1 后 G1 不再等待 G3(扩产)** |
| 实施动作 | ①schema 字段定义(Contract v0.2 正文)→ ②回填(数据写入) |
| 批准依赖 | **字段名/算法/格式三者已裁(DEC-023 Part 1)**;剩 = Step 2 回填执行令(A3) |
| **硬约束** | **v2 接口面 87/87 manifest 全部是 R50 基线成员**(probe_v3)——回填 87 份 = R50 必然 DRIFT;DEC-021 D4 五步序中 **Step 1 Freeze interface snapshot 先于 Step 2 回填**,该快照的基线形态与 R50 血统关系需执行令明确(Alignment D.1) |
| 验收判据 | 回填后逐 manifest:`source_version_id` == sha256(当前 md 字节)== IR 同文件 `source_sha256`(有 IR 者);Step 1 快照/新基线 verify PASS;旧基线血统注记留痕 |

## G2 — 双层关联键升级(B1;**DEC-B1 已裁唯一键**)

| 属性 | 内容 |
|---|---|
| 现状 | IR ↔ manifest 关联 = `ir.source_file == manifest.source_file`(绝对路径字符串值相等,probe_v2 `p4`) |
| 目标态(**已裁,DEC-B1**) | 关联 = `source_version_id` **唯一**关联键;路径值相等不是合规关联 |
| 实施动作 | IR 侧字段已具备(`source_sha256` 即该值);manifest 侧随 G1;**无独立数据动作** |
| 批准依赖 | 随 G1;**DEC-023 已裁**:`source_file` 保留 = locator(相对路径化不再是身份议题,若做属 locator 改善另议);残余未裁 = source bytes 交付方式(v0.2 交付面) |
| 验收判据 | 87 份接口面:`manifest.source_version_id == ir.source_sha256` 全量成立(有 IR 者);无 IR 者身份自足(DEC-B1) |

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
| G1 | B1 + **DEC-023(名/算法/格式全裁,范围 87)** | schema + 数据 | 仅剩 Step 2 回填执行令 | **否(定义已齐,v0.2 直接写死)** |
| G2 | B1(**唯一键已裁**)+ DEC-023(path 非身份) | 派生(随 G1) | — | 否(随 G1) |
| G3 | B1 + **DEC-023(再生成允许+四约束)** | 数据生成 | 执行令(批次/R52 版本策略) | 否 |
| G4 | B1(持续机制仍未裁;单次再生成 ≠ 持续机制) | 机制 | Owner 令 | 否 |
| G5 | B3 + **DEC-023(词表终局 + unknown 路由已裁)** | 机制 + 数据 | **仅剩载体(字段名/落点/reviewable record 形态)**+ 执行令 | **载体定义是**(守卫实施可后置) |
| G6 | **DEC-021 已裁 = 隔离** | 文字层披露 | — | 否(披露形态随 v0.2) |
| G7 | B1 弱 | 文字层 | 随 v0.2 | 否 |
| C.1 | DEC-021 D4 | 接口面表达 + Step 1 快照载体/血统 | Step 1 执行令 | **是**(scope 表达属 v0.2 正文) |

**最小冻结集(DEC-023 后再收敛)**:**G5 两层状态载体(含 reviewable record 形态)+ 接口面 87 的表达(C.1)**——仅此两项属 v0.2 正文必须写死且尚未落字;**G1 字段定义三要素(名/算法/格式)全部已裁,v0.2 可直接照录 DEC-SOURCE-IDENTITY**。数据动作全部可后置于冻结 + 执行令。面口径以"87 接口面 / IR 71 当前消费面 / 16 Semantic Pending / 79 historical"写入 v0.2。

# IMPLEMENTATION GAP LIST — preprocessing → Contract v0.2

> Status: **v1.1(2026-09-16,DEC-B1 后更新)** · Basis: Owner Decision Record v1(§1 总纲 + **§1bis DEC-B1**)+ Producer Readiness v3(同批交付)
> DEC-B1 生效更新:①唯一关联键裁定 → G2 从"待定义"变为"已裁待实施";②**source 身份不依赖 IR 存在** → **G1 与 G3 正式解耦**:身份面可先行完备,IR 现状 71 不阻塞身份权威性。
> Purpose: 逐缺口列出"是什么 / 差多少 / 谁批 / 什么顺序"。每条含:现状证据、目标态(裁决锚定)、实施动作性质、批准依赖、验收判据。
> 纪律:全部为 producer 侧动作;零执行;UNKNOWN 明示。

---

## G1 — manifest 缺 `source_version_id`(B1 核心缺口)

| 属性 | 内容 |
|---|---|
| 现状 | 0/166 manifest 携 `source_version_id`;0/166 携任何 sha 键(probe_v2 `p1b`) |
| 目标态 | 每份入接口面的 manifest 携 `source_version_id` = SHA-256(源 md raw bytes);与 IR `source_sha256` / `provenance.source_version` 同值;**身份自足性(DEC-B1)**:该字段独立可验证,不需要 IR 在场 |
| 生产侧就绪度 | 算法+代码就绪(`resolver_reference.py:52-53`);71 份值已存在(IR 面),manifest 侧字段为空;**DEC-B1 后 G1 不再等待 G3(扩产)** |
| 实施动作 | ①schema 字段定义(Contract v0.2 正文,Owner 裁决)→ ②回填(数据写入,范围 87 vs 166 待令) |
| 批准依赖 | A1 字段定义 + A2 范围 + A3 执行令(Readiness v3 §4) |
| **硬约束(本轮新固化)** | **v2 接口面 87/87 manifest 全部是 R50 基线成员**(probe_v3)——回填 87 份 = 修改 87 个冻结基线文件 = R50 必然 DRIFT,**必须配对基线再冻结决策**(新 audit_id + R50 血统注记),不得只改数据不改基线 |
| 验收判据 | 回填后逐 manifest:`source_version_id` == sha256(当前 md 字节)== IR 同文件 `source_sha256`(有 IR 者);R50 新基线 verify PASS;旧基线退役/血统注记留痕 |

## G2 — 双层关联键升级(B1;**DEC-B1 已裁唯一键**)

| 属性 | 内容 |
|---|---|
| 现状 | IR ↔ manifest 关联 = `ir.source_file == manifest.source_file`(绝对路径字符串值相等,probe_v2 `p4`) |
| 目标态(**已裁,DEC-B1**) | 关联 = `source_version_id` **唯一**关联键;路径值相等不是合规关联 |
| 实施动作 | IR 侧字段已具备(`source_sha256` 即该值);manifest 侧随 G1;**无独立数据动作** |
| 批准依赖 | 随 G1;若 v0.2 要求改 `source_file` 为相对路径则另裁 |
| 验收判据 | 87 份接口面:`manifest.source_version_id == ir.source_sha256` 全量成立(有 IR 者);无 IR 者身份自足(DEC-B1) |

## G3 — IR 覆盖面 71/166(B1;**DEC-B1 后与身份面解耦**)

| 属性 | 内容 |
|---|---|
| 现状 | 88 记录 / 71 ADMITTED(v2 目录面全集);95 份 manifest(166−71)无语义承载 |
| 目标态 | **UNKNOWN**(v0.2 未定 IR 权威覆盖面是 71 还是全语料) |
| **DEC-B1 语义** | source 身份不依赖 IR 存在 → **IR 现状 71 不阻塞身份权威性**;G3 扩产是语义面独立议题,不再耦合 G1 |
| 实施动作(若扩产) | 重跑 `resolver_reference.py` 扩批 = 新数据生成动作;替换 r52 工件 = 基线治理问题(冻结工件不可回改纪律) |
| 批准依赖 | Owner 显式令(范围/批次/工件版本策略) |
| 验收判据 | 待令后定义 |

## G4 — IR 持续产出机制(B1)

| 属性 | 内容 |
|---|---|
| 现状 | R52 一次性工件,自冻结未再生成;daemon 只产 md,不产 IR |
| 目标态 | **UNKNOWN**(未裁是否需要) |
| 批准依赖 | Owner 令 |
| 备注 | 若不要求,IR 权威性 = 冻结 + sha 自洽(现状语义,v0.2 披露即可) |

## G5 — B3 守卫与 UNKNOWN/PENDING 载体

| 属性 | 内容 |
|---|---|
| 现状 | 生成链零 unit_type 值域检查;恰 1 例非标值原样进 ADMITTED(行为符合"显式保留/禁转换/禁丢弃",但无机制保证);UNKNOWN/PENDING 无载体 |
| 目标态(裁决) | 非标值 → 显式 UNKNOWN/PENDING 态;永不自动修复、永不静默丢弃 |
| 生产侧实施动作 | ①生成链(`resolver_reference.py` unit_type 复制点 `:152` 前)引入值域检查,值域外单元携带显式标记;②标记载体字段随 v0.2 定义 |
| 批准依赖 | A6 载体定义(v0.2)+ A7 守卫实施令 |
| **硬约束** | 存量 1 例所在 manifest 亦为 R50 成员 + IR 冻结工件成员——**存量处置**(改数据 or 只加守卫不动存量)必须配对基线决策;IR 永不回改纪律下,IR 面存量 1 例的处置 = UNKNOWN(需 v0.2 明示冻结工件中非标值的接口语义) |
| 验收判据 | ①构造值域外单元过生成链 → 必产显式态(测试钉);②存量 1 例在接口上呈现 v0.2 规定态 |

## G6 — v1 legacy 面 79 份接口地位(B1 面口径)

| 属性 | 内容 |
|---|---|
| 现状 | 79 份 `identity_version` 缺失;C-IN-1 下必拒;无接口地位定义;另有 1 份"目录 v2 / 字段 legacy"混入件已被 IR 拒收(REJECTED_V1) |
| 目标态 | **UNKNOWN**(排除/迁移/披露三选一未裁) |
| 备注 | 排除 = 最小动作;迁移 = 数据写入 + 基线问题;披露 = v0.2 文字层 |

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
| G1 | B1(DEC-B1 已裁身份语义) | schema + 数据 | A2+A3(字段名/格式细节) | **是**(authority 无字段则裁决无法落地) |
| G2 | B1(**唯一键已裁**) | 派生(随 G1) | — | 是(随 G1) |
| G3 | B1(**已与身份面解耦**) | 数据生成 | A4 | 否(v0.2 可冻结于现状 71 + 扩产条款) |
| G4 | B1 | 机制 | A4 | 否 |
| G5 | B3 | 机制 + 数据 | A6+A7 | **载体定义是**(守卫实施可后置) |
| G6 | B1 面 | 面口径 | A5 | 是(接口面边界必须写死) |
| G7 | B1 弱 | 文字层 | 随 v0.2 | 否 |

**最小冻结集(DEC-B1 后不变)**:G1(字段定义,回填可后置)+ G5 载体 + G6 口径——三者是 v0.2 正文必须写死的;数据动作全部可后置于冻结 + 执行令。**DEC-B1 增量**:G1 的目标态新增"身份自足性"验收(无 IR 者独立可验),G3 敞口从冻结路径上移除。

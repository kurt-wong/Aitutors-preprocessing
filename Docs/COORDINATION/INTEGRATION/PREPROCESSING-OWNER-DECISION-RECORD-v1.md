# OWNER DECISION RECORD v1 — Integration Contract B1/B2/B3

> Status: **v1(2026-09-16)** · Authority: Owner 直接指令(聊天原文,DSH 自记)
> Ledger anchor: `state.yaml.decisions[DEC-019]` + `state.yaml.integration_contract.owner_decision_b1b3`
> Purpose: 裁决原文固化,作为 Producer Readiness v3 / Implementation Gap List / Execution Dependency Map 的唯一裁决基准。本文件不新增裁决内容;凡本文件未载,均为未裁。

---

## 1. 裁决原文(Owner 2026-09-16,逐条照录)

### B1 Transport

> 正式生产接口:
> **Manifest + IR 双层接口。**
> 职责:
> **Manifest: Source Identity Authority**
> **IR: Semantic Consumption Authority**
> 两者必须通过明确 **source_version_id** 关联。

### B2 Identity

> source identity:
> **Original Source Bytes SHA-256**
> 算法:**SHA-256(raw bytes)**
> 其他 hash:
> - body_hash
> - line_hash
> - integrity_hash
> - norm_sha256
>
> 只能作为内部校验。不能作为跨系统 source identity。

### B3 Semantic Boundary(生产侧责任,2026-09-16 第二轮指令扩展)

> unknown unit_type:
> **不得自动修正。**
> **不得静默转换。**
> 进入:**UNKNOWN/PENDING**

> (第二轮补充)针对 B3,只定义生产侧责任:
> unknown unit_type **必须显式保留**。
> 禁止:**自动转换。**
> 禁止:**静默丢弃。**

### 同令约束(两轮合并)

1. 数据治理四项(unit_type 修复 / 图片恢复 / flags registry / D5-C·D5-D)**暂缓**——接口冻结优先;
2. 不修改:V3 代码 / Contract 正文 / 数据文件 / schema / daemon;
3. DSH 职责:**保证 producer 能稳定输出 Owner 冻结的接口**。

---

## 2. 生产侧责任解释边界(非裁决,DSH 自我约束声明)

B3 生产侧责任按裁决文字取最大保守义:

| 责任 | 生产侧落实语义 |
|---|---|
| 显式保留 | 非标准 `unit_type` 值**原样写入**输出面(manifest / IR),不改字符、不改键名、不删除单元 |
| 禁止自动转换 | 生成链任何环节不得将非标准值映射为标准值(含"看起来是 typo 就修"类推断) |
| 禁止静默丢弃 | 非标准单元不得因值异常而被生成链跳过/过滤/置 null;若接口需要 UNKNOWN/PENDING 态,该态必须是**显式字段/显式状态**,不是缺席 |
| UNKNOWN/PENDING 态 | 具体载体(字段名/状态机/落点)属 Contract v0.2 定义面——**未裁**,producer 不预设 |

## 3. 未裁事项登记(引用本文件时必须一并引用)

- `source_version_id` 的载体字段名、格式(裸 hex vs 带前缀)、回填范围(接口面 87 vs 全语料 166):**未裁**;
- IR 权威覆盖面(现状 71 vs 扩产)与持续产出机制:**未裁**;
- v1 legacy 面 79 份处置(排除/迁移/披露):**未裁**;
- UNKNOWN/PENDING 状态机落点:**未裁**。

*v1 · 2026-09-16 · DSH 自记(Owner 聊天原文照录)。如有文字冲突,以 Owner 原文为准。*

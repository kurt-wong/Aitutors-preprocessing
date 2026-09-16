# OWNER DECISION RECORD v1 — Integration Contract B1/B2/B3

> Status: **v1.3(2026-09-16,追加 §1quater Interface Decision Finalization v1 四方固化裁决)** · Authority: Owner 直接指令(聊天原文,DSH 自记)
> Ledger anchor: `state.yaml.decisions[DEC-019]`(总纲)+ `[DEC-020]`(DEC-B1 分项)+ `[DEC-021]`(本文件 §1ter 四项)+ `[DEC-022]`(本文件 §1quater)+ `state.yaml.integration_contract.owner_decision_b1b3` / `.owner_interface_finalization`
> Purpose: 裁决原文固化,作为 Producer Readiness / Implementation Gap List / Execution Dependency Map 的唯一裁决基准。本文件不新增裁决内容;凡本文件未载,均为未裁。
> 分项裁决计划:Owner 以 DEC-B1 / DEC-B2 / DEC-B3 分项下达,依序追加于本文件 §1bis 起。

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

## 1bis. 分项裁决 DEC-B1(Owner 2026-09-16 第三轮,原文照录)

> **DEC-B1:**
> Transport 采用双层模型。
> **Manifest:负责 Source Identity Authority。**
> **IR:负责 Semantic Consumption Authority。**
> **source_version_id:作为两者唯一关联键。**
> **V3 消费语义来自 IR,**
> **但 source 身份不依赖 IR 存在。**

### DEC-B1 生产侧语义(DSH 解释,保守义)

| 条款 | 生产侧落实语义 |
|---|---|
| 唯一关联键 | 双层间关联只有 `source_version_id` 一种;路径值相等(`source_file`)是现状,**不是**合规关联 |
| **source 身份不依赖 IR 存在** | ①manifest 的身份字段必须**自足**:任何一份入接口面的 manifest,其 `source_version_id` 可独立验证(sha256(md 字节)当场可算),**不需要 IR 在场**;②IR 缺席(未扩产/拒收/未生成)不使 manifest 身份失效;③反向不成立:IR 的语义承载依赖 manifest 身份锚定 |
| 与覆盖面的关系 | 该条使 **G1(身份回填)与 G3(IR 扩产)解耦**:身份面可以先行完备,语义面维持现状 71 不阻塞身份权威性 |
| V3 消费语义来自 IR | 消费侧陈述,DSH 侧无动作;producer 只须保证 IR 面语义稳定(现状 71 sha 零漂移) |

---

## 1ter. 分项裁决 — PREPROCESSING-V3-CONTRACT-DECISION-FINALIZATION v1(Owner 2026-09-16 第四轮,原文照录要点)

> Owner 令:本轮 = 裁决入册 + Contract v0.2 起草准备阶段;Contract 保持 **v0.2 DRAFT / NOT FROZEN**;禁止修改代码 / 修改数据 / 执行数据清洗 / 执行图片恢复 / 修改数据库 schema / 冻结 Contract。

### Decision 1 — Interface Scope

> 正式进入 V3 Preprocessing Interface 的范围定义为:
> **Interface Scope = v2 standard interface set,Current size = 87 records**。
> - 166 = 全部历史资产规模,不等于正式接口;
> - 87 = 当前正式接口范围;
> - 71 = 当前已生成 IR 的 semantic consumption 面,不代表完整 interface。
>
> 正式定义:
> **Manifest interface scope: 87**
> **IR semantic consumption current frozen scope: 71 ADMITTED records**

配套要求(Owner 令原文结构):OBSERVED = v2 interface 87 / IR ADMITTED 71 / historical manifest inventory 166;DECISION = v0.2 Contract 以 87 为接口范围,IR 71 为当前语义消费冻结面;IMPLEMENTATION GAP(不得认为已实现)= manifest interface scope 如何表达 / source_version_id 如何覆盖 87 / IR 后续扩展机制未定义。

### Decision 2 — Legacy v1 Handling

> v1 legacy 数据:**status = historical asset,not part of v0.2 interface**。当前规模:v1 legacy = 79。
> 禁止:自动迁移 / 自动补齐 / 自动重新生成 IR / 自动加入 87 接口。
> 未来如需处理:单独建立 **Legacy Migration Plan**,不得混入当前 Contract。

### Decision 3 — Semantic Boundary

> 系统必须明确区分四个状态:
> **READY / INCOMPLETE / PENDING_REVIEW / REJECTED**。
>
> - **READY**:semantic annotation 完整、unit_type 合法、可进入后续消费;
> - **INCOMPLETE**:输入不足(缺 stem、缺必要字段等);
> - **PENDING_REVIEW**:系统无法安全判断(unknown unit_type、semantic ambiguity、多种解释均可能);
> - **REJECTED**:明确违反接口要求。
>
> 强制规则:任何 unknown semantic **禁止 automatic conversion、禁止 silent fallback、禁止 silent skip**,必须进入 **PENDING_REVIEW 或 REJECTED**,由明确规则决定。

### Decision 4 — Execution Ordering

> 所有数据动作必须遵循:
> **Step 1 Freeze interface snapshot → Step 2 Generate / backfill source_version_id → Step 3 Freeze Contract v0.2 → Step 4 Execute data hygiene → Step 5 Execute image recovery / historical cleanup**。
>
> 原因:source identity 必须早于内容修改;任何图片恢复 / OCR 修复 / markdown 修改都可能导致 content change → hash change → source_version_id invalid。**身份冻结优先。**

### §1ter 生产侧保守义(DSH 解释,非裁决)

| 条款 | 生产侧落实语义 |
|---|---|
| Scope = 87 | G6(面口径)由"未裁"变"已裁 = 87(字段口径)";166/79 不入接口;与既有字段口径事实(`identity_version=="2"`)一致 |
| IR 冻结面 = 71 | A4 之"当前面"已裁(维持 71);**扩展机制仍未裁**(DEC-B1 已保证其不阻塞身份面) |
| v1 legacy 79 = historical asset | A5 已裁 = 隔离(非排除动作、非迁移);四禁 = 禁自动迁移/补齐/重生成 IR/入 87;未来处置走独立 Legacy Migration Plan |
| 四状态机 | A6 之"状态词表"已裁(READY/INCOMPLETE/PENDING_REVIEW/REJECTED,取代 DEC-019 的 UNKNOWN/PENDING 泛称);**载体(字段名/落点)仍未裁**;unknown semantic 路由 = PENDING_REVIEW 或 REJECTED,由明确规则决定——生产侧对应 G5 守卫的目标态 |
| 五步顺序 | D-1/D-5 已裁:Step 1 接口快照冻结先于回填;D2 图片恢复 = Step 5(最后);**E2 硬约束不变**:Step 2 回填 87 份 manifest(全部 R50 成员)必致 R50 DRIFT,Step 1 的接口快照如何与 R50 配对再冻结 = 仍需执行令细化(见 Alignment 报告 GAP 节) |

---

## 1quater. 分项裁决 — PREPROCESSING / V3 Interface Decision Finalization v1(Owner 2026-09-16 第五轮,原文照录要点;canonical 引用面)

> Owner 令:本轮目标 = ①固化 Owner Decision ②更新双方事实基线 ③明确 Manifest、IR 责任边界 ④为 Contract v0.2 Frozen Candidate 做准备。本轮**不修改代码 / 不执行数据清洗 / 不执行数据迁移 / 不冻结数据库实现 / 不提前实现未裁事项**。下一阶段从"讨论架构"进入"冻结接口契约前验证"。

### Part 1 — Manifest 与 IR 双层职责模型(正式采用)

> **Manifest = Source Identity Authority;IR = Semantic Consumption Authority。**
> Manifest 负责回答"这个东西是谁?"(source identity / source version / raw bytes hash / 文件版本关系);
> IR 负责回答"这个文件里面有什么?"(question structure / semantic annotation / knowledge information / unit information)。
> 禁止:用 Manifest 替代 IR 描述题目;用 IR 替代 Manifest 证明文件身份。

### Part 2 — 生产与消费责任边界

> Manifest:Producer = Preprocessing(DSH)——生成 Manifest / 计算 source_version_id / 保证字段正确;Consumer = V3——验证 Manifest / **重新计算 hash** / 判断是否接受。
> IR:Producer = Preprocessing(DSH)——OCR 后结构化 / LLM 语义解析 / 生成 IR;Consumer = V3——验证 IR 是否符合契约 / Gate 判断是否进入正式题库 / 拒绝不符合的数据。
> 固化原则:**Preprocessing 负责解释,V3 负责接受或拒绝解释。**

### Part 3 — Scope 裁决

> **Interface Scope = 87**(87 份文件具备接口身份);**IR Consumption Scope = 71 ADMITTED**(当前 71 份文件具备可消费语义结构)。二者允许不同。
> 禁止(为让数字一致):强制生成 IR / 删除 identity 文件 / 修改历史数据。

### Part 4 — 16 份 Identity-only 文件处理

> "Manifest 有、IR 无"的文件属于正常状态,定义:**Identity Available / Semantic Unavailable**。
> 不得:自动补 IR / LLM 猜测生成 / 静默进入题库。
> 后续是否重新生成 IR:**另行批准**。

### Part 5 — Semantic Unknown 处理原则

> 对 unit_type unknown / semantic unclear / annotation uncertain:禁止 ①自动转换 ②静默 fallback ③静默 skip。必须保留事实状态,进入 **UNKNOWN** 语义状态。
> 注意:**不要合并现有 semantic_status 与 decision_status 两个状态体系**。本轮只确认:UNKNOWN 属于语义层。

### Part 6 — Contract v0.2 编写范围

> 冻结内容(仅三件):
> ① **Identity:`source_version_id = SHA256(original source bytes)`**;
> ② **Scope:Manifest 87 / IR 71 snapshot**;
> ③ **Semantic Boundary:`Unknown ≠ Ready`;Unknown 不得自动进入正式题库。**
>
> 暂缓冻结(不属于 v0.2 interface contract):数据库字段最终设计 / UI 展示 / 自动补全机制 / IR 扩产计划 / 图片恢复流程 / daemon 持续生产策略。

### Part 7–9 — 双侧任务与共同输出

> Claude 任务 = **V3 Consumer Alignment v2**(更新消费侧事实基线 / 检查 V3 实现只报告不改码 / **更新 Contract v0.2 Draft 形成 Frozen Candidate,状态 DRAFT NOT FROZEN** / Implementation Gap 表)。
> DSH 任务 = **Producer Alignment v4**(更新 Producer Interface Facts 固化职责与 87/71 scope / Producer Implementation Gap / 明确哪些动作需 Owner 批准;禁自行数据修改 / schema 修改 / 清洗 / IR 重新生成)。
> 共同输出四件:ODR v1.3(唯一裁决来源)/ Consumer Alignment v2 / Producer Alignment v4 / Contract v0.2 Frozen Candidate(双方引用同一版本)。

### 最终原则(Owner 原文)

> 文件身份由生产侧证明,系统侧验证。
> 文件内容由生产侧解释,系统侧裁决。
> 宁可缺少结构化数据,也不能制造未经确认的结构化数据。

### §1quater 生产侧保守义(DSH 解释,非裁决;详件 = `PREPROCESSING-PRODUCER-ALIGNMENT-v4.md` §B)

| 条款 | 生产侧落实语义 |
|---|---|
| Part 2 责任边界 | "V3 重算 hash" 前提 = source bytes 可达;同算法对账已在生产侧 71/71 实证;`source_file` 绝对路径形态使可达性存疑 → 归 v0.2 落字(GAP G-4) |
| Part 3 三禁 | 叠加硬约束:任何"补齐 87−71=16 份"的动作违反裁决 |
| Part 4 | **关闭 D-2**(16 份无 IR 成员消费语义);IR 重生成 = 另行批准(GAP G-5 机制未裁) |
| Part 5 与 §1ter D3 关系 | 四状态机(READY/INCOMPLETE/PENDING_REVIEW/REJECTED)= 决策层词表;UNKNOWN = 语义层事实呈现;两层并存不合并;unknown semantic 仍按 D3 路由 PENDING_REVIEW/REJECTED;**两层载体均未裁** |
| Part 6 | **字段名 `source_version_id` + 算法 SHA256(raw bytes)已裁**(§3 未裁清单相应更新);格式细节(裸 hex)DSH 建议沿用现有实践 = PROPOSED |
| Part 7 Contract v0.2 正文 | **本轮起草责任在 Claude 侧**;DSH 侧 Contract 正文继续零改动,以 Producer Alignment v4 + Interface Facts v2.1 为生产侧输入 |

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

- **字段名与算法已裁(§1quater Part 6)**:`source_version_id = SHA256(original source bytes)`;格式细节(裸 64 hex vs 带前缀;大小写):**未裁**(DSH 建议沿用 `ir.source_sha256` 现有裸小写 hex 实践 = PROPOSED);
- ~~回填范围(接口面 87 vs 全语料 166)~~ **已裁(§1ter D1,§1quater Part 3 再确认)= 87**;
- IR 权威覆盖面:**当前面已裁 = 71 ADMITTED snapshot**;扩展机制与持续产出:**仍未裁**(Part 4:重生成 = 另行批准;Part 6:IR 扩产计划暂缓冻结);
- v1 legacy 面 79 份处置:**已裁 = historical asset 隔离**;未来走独立 Legacy Migration Plan;披露形态(文字层):**未裁**;
- 语义状态机:**决策层词表已裁(§1ter D3 四状态)+ 语义层 UNKNOWN 已裁(§1quater Part 5,两体系不合并)**;载体(字段名/落点/生产侧标记形态)与 PENDING_REVIEW→REJECTED 路由规则文本:**未裁**;
- 16 份 Identity-only 文件:**已裁(§1quater Part 4)= Identity Available / Semantic Unavailable 正常态**(D-2 关闭);接口面是否设呈现字段:**未裁**;
- 执行顺序:**已裁五步**;Step 1 接口快照与 R50 基线的配对关系(D-6)、存量 1 例原子性(D-3)、2 份三重成员(D-4):**未裁**;
- Contract v0.2 正文起草:**已裁(§1quater Part 7)由 Claude 执行**(DRAFT NOT FROZEN);冻结:**未裁**(Owner 冻结令)。

*v1 · 2026-09-16 · DSH 自记(Owner 聊天原文照录)。如有文字冲突,以 Owner 原文为准。*

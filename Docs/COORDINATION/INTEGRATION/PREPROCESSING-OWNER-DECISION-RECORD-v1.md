# OWNER DECISION RECORD v1 — Integration Contract B1/B2/B3

> Status: **v1.6(2026-09-16,追加 §1septies Contract v0.2 Freeze Candidate Finalization:契约键改名 `source_content_sha256` + bytes 能力冻结 + 文字收口五项)** · Authority: Owner 直接指令(聊天原文,DSH 自记)
> Ledger anchor: `state.yaml.decisions[DEC-019]`(总纲)+ `[DEC-020]`(DEC-B1 分项)+ `[DEC-021]`(§1ter)+ `[DEC-022]`(§1quater)+ `[DEC-023]`(§1quinquies)+ `[DEC-024]`(§1sexies)+ `[DEC-025]`(§1septies)+ `state.yaml.integration_contract.owner_decision_b1b3` / `.owner_interface_finalization` / `.owner_interface_revision` / `.owner_contract_freeze_review` / `.owner_contract_freeze_finalization`
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

## 1quinquies. 分项裁决 — Interface Finalization Revision v1(Owner 2026-09-16 第六轮,原文照录要点;canonical 引用面)

> Owner 令:本轮目标 = ①修正之前过度保守或不准确的表述 ②固化最终接口原则 ③关闭 source identity / 16 份 Identity-only / path 定位问题 ④两侧文档同步 ⑤保持代码、数据、Contract 冻结状态不变。仅更新决策记录、契约草案、Gap 文档和台账;禁改代码 / schema / preprocessing 数据 / 重新生成 IR / 图片恢复 / daemon / 冻结 Contract v0.2;全部 implementation 状态保持 not started。本轮结束标准(Owner Final Boundary):**Source Identity Frozen + Scope Frozen + Semantic Boundary Frozen + Path Non-Identity Frozen + Identity-only Recovery Rule Frozen** → 之后进入 Contract v0.2 Freeze Candidate Review,不再扩展接口讨论。

### Part 1 — Source Identity 原则修正(新增正式裁决 DEC-SOURCE-IDENTITY)

> 文件身份定义:`source_version_id = SHA256(original source bytes)`;**格式:64 字符小写 hex 字符串**。
> Identity 由 `source_version_id` **唯一决定**;Location 由 `source_file` / path / locator 表达。
> **强制禁止**:任何文档不得暗示 `source_file` / path / absolute path / directory 参与:文件唯一判断 / source identity 判断 / version 判断 / hash identity 判断。
> 固化原则:**Source identity belongs to content hash, not storage location.**(文件身份属于内容哈希,不属于存储位置。)

### Part 2 — source_file / path 处理规则

> `source_file` **保留**,但重新定义:`source_file = locator information`,**不是** identity information。
> 文档要求:错误表述"source_file 用于识别 source"→ 改为"**source_file 用于辅助定位 source,source_version_id 用于跨系统唯一识别 source**"。
> 未来 Windows / NAS / Linux / Object Storage / Cloud Storage 路径变化:**不得导致 source_version_id 变化**。

### Part 3 — Identity-only 16 份文件重新定义

> 16 份**不是永久缺失**。状态定义:**Identity Available / Semantic Pending**(取代上一轮 "Semantic Unavailable" 表述)。
> 允许后续动作:允许重新执行 preprocessing 生成 IR,但必须满足四约束:
> - Constraint 1:source bytes 不允许改变;
> - Constraint 2:source_version_id 必须保持一致;
> - Constraint 3:新 IR 必须绑定 `source_version_id`;
> - Constraint 4:生成后的 IR 必须重新经过 identity verification + semantic validation。
>
> 禁止:修改原 source / 重新 OCR 覆盖原 source / 生成新的 identity / 用新 hash 替代旧 hash。

### Part 4 — Interface Scope 保持

> `Interface Scope = 87` **不修改为 71**。定义表:87 = 正式身份接口范围;71 = 当前已有 IR 语义消费范围;16 = 等待 semantic processing。
> 禁止:将 "IR available" 等同于 "Interface available"。

### Part 5 — Semantic Unknown 状态补充(两状态体系终局词表)

> 保持两状态体系分离,**禁止合并**。
> **Semantic Status 最终词表:`ready` / `incomplete` / `unknown`**;
> **Decision Status 词表:`pending_review` / `approved` / `rejected`**。

### Part 6 — Unknown 处理(明确规则)

> 任何 unknown semantic unit:禁止 silent skip / automatic conversion / silent fallback;**必须产生 `reviewable record`,进入 `pending_review` workflow**。

### Part 7 — Contract v0.2 Draft 更新要求(Claude 负责 `PREPROCESSING-V3-CONTRACT-v0.2-DRAFT`)

> 必须加入四章节:**Identity**(source_version_id 定义 / hash 唯一性 / path 非身份)、**Scope**(87 interface / 71 semantic available / 16 semantic pending)、**Semantic**(unknown / pending_review / no silent skip)、**Boundary**(Manifest = Source Identity Authority,IR = Semantic Consumption Authority;Manifest 证明是谁,IR 说明是什么)。

### Part 8 — DSH 任务

> 更新 Producer Alignment / Producer Interface Facts / Owner Decision Record / Gap List / Dependency Map;同步四规则(Identity 规则 / 16 份状态调整 / Path 非身份原则 / IR 重新生成允许但必须保持 identity)。禁止执行:IR 重生成 / 数据回填 / schema 修改——等待后续 Owner 执行令。

### Part 9 — Claude 任务

> 更新 Consumer Alignment / Contract Draft / V3 Gap Matrix / V3 Decision Alignment;重点检查:V3 未来消费逻辑**不得依赖 source_file path,必须依赖 source_version_id**;同时登记当前代码事实:**"V3 identity verification capability not implemented" = not started**。

### Part 10 — 输出要求(双方)

> ①Changed Documents(文件/修改内容/commit);②Decision Alignment Summary(| Decision | Current | Final Rule |);③Remaining UNKNOWN(**只保留真正未裁事项,不重复已关闭问题**)。

### §1quinquies 生产侧保守义(DSH 解释,非裁决;详件 = `PREPROCESSING-PRODUCER-ALIGNMENT-v5.md`)

| 条款 | 生产侧落实语义 |
|---|---|
| Part 1 格式 | **修正上一轮表述**:Alignment v4 的 G-1"格式细节 PROPOSED 未裁"已关闭——已裁 = 64 字符小写 hex(与现有 `ir.source_sha256` 71 份实证形态完全一致,零格式迁移) |
| Part 1-2 path 非身份 | 现有文档中"`source_file` 绝对路径"相关缺口表述(G-4/交付形态)**收窄**:path 是 locator 问题不是 identity 问题;相对路径化不再是身份议题。残余未裁 = **bytes 本身如何交付给 V3 重算 hash**(locator 之外的传输/获取方式) |
| Part 3 16 份 | "Semantic Unavailable(正常态)" → **"Semantic Pending(可恢复)"**;G3 扩产由"机制未裁"推进为"**允许 + 四约束已裁**";四禁使"身份冻结优先"在 IR 再生成场景下成立(bytes 不变 → id 不变);执行仍待 Owner 令 |
| Part 4 | 87/71/16 三数字定义表写入 v0.2 Scope 章;"IR available ≠ Interface available" 禁令与 DEC-021 D1 一致 |
| Part 5 词表终局 | **取代 DEC-021 D3 四状态机的合并记法**:READY/INCOMPLETE 归 semantic 层(ready/incomplete),PENDING_REVIEW 归 decision 层(pending_review),REJECTED → decision 层 rejected,新增 decision 层 approved;引用以本 Part 为准 |
| Part 6 | unknown semantic → reviewable record → pending_review workflow(DEC-021 D3 遗留的路由规则已给:进 pending_review,不再"或 REJECTED 由规则决定");reviewable record 的载体形态 = 仍未裁 |

---

## 1sexies. 分项裁决 — Contract v0.2 Freeze Candidate Review 启动令(Owner 2026-09-16 第七轮,原文照录;canonical 引用面)

> Owner 令:进入 PREPROCESSING Contract v0.2 Freeze Candidate Review。基于 Owner 已确认原则(原文照录):

### Part 1 — source identity

> `source_version_id = SHA256(raw bytes)`;path(`source_file`)仅作为 locator,**禁止参与 identity 判断**。

### Part 2 — 双层职责

> Manifest 负责 Source Identity Authority;IR 负责 Semantic Consumption Authority;V3 消费语义来自 IR,但**身份验证独立于 IR**。

### Part 3 — 16 份文件

> 状态定义:**Identity Available + Semantic Pending**;允许重新生成 IR。必须保证:①source bytes hash 不变 ②source identity 不变 ③IR 版本可追踪 ④**禁止覆盖历史事实**。

### Part 4 — 状态体系

> Semantic:`ready/incomplete/unknown`;Decision:`pending_review/approved/rejected`;**禁止合并**。

### Part 5 — `source_version_id` 命名问题(新裁决面)

> **提出最终命名方案。避免:Producer hash identity 与 V3 UUID FK 同名。**

### Part 6 — source bytes 交付(新裁决面)

> **只冻结能力要求**:V3 必须能够获得 raw bytes 并验证 hash。**不要冻结具体传输方案**。

### 输出要求

> A. Contract v0.2 Freeze Candidate;B. 剩余未决问题列表;C. Implementation Gap;**D. 禁止修改任何代码和数据**。

### §1sexies 生产侧保守义(DSH 解释,非裁决;详件 = `PREPROCESSING-CONTRACT-v0.2-FREEZE-CANDIDATE-REVIEW-v1.md`)

| 条款 | 生产侧落实语义 |
|---|---|
| Part 1-4 | 与 §1quinquies Part 1-5 完全一致的再确认(无新裁决);DSH 对 Claude v0.2 DRAFT 全文亲读核验 = **PASS** |
| Part 5 命名 | **新裁决面**:DSH 提出 PROPOSED-NAMING N-1~N-4——契约键 `source_version_id` 冻结不改名(零迁移),V3 内部 UUID FK 改名 `source_version_row_id`(N-2),绑定列 CHAR(64) UNIQUE(N-3),过渡期引用双向限定语(N-4);采纳后 OQ-8′ 关闭 |
| Part 6 bytes | **新裁决面**:能力要求升格为 REQUIREMENT(PROPOSED-BYTES 条款草案 A.3:V3 必须获得 raw bytes + 独立重算 SHA256 对账,fail-closed),传输/获取机制明确不冻结(OQ-12′ 降级为 delivery logistics) |
| 评审结论 | **CONDITIONAL READY**:六原则 1-4 PASS,5/6 = 文字层落字项 + F-4 旧表述修正;冻结 = 五步序 Step 3,前置 Step 1/Step 2 执行令未下达,冻结令权在 Owner;本轮零代码零数据 |

---

## 1septies. 分项裁决 — Contract v0.2 Freeze Candidate Finalization(Owner 2026-09-16 第八轮,原文照录;canonical 引用面)

> Owner 令:本轮进入 Contract v0.2 Freeze Candidate Finalization。已确认裁决四项(原文照录):

### Decision 1 — Identity Field Naming

> 采用:**`source_content_sha256`**。定义:**`SHA256(raw bytes)`**。作为跨系统 Source Identity 字段。
> 禁止:`source_file`/path 参与 identity 判断。
> V3 内部 `source_version_id` 保持内部含义,**不作为跨系统身份键**。

### Decision 2 — Source Bytes Capability

> Contract 冻结能力要求:V3 必须能够:①获取 raw bytes ②独立计算 SHA256 ③与 `source_content_sha256` 比较 ④不一致 fail-closed。**不冻结具体传输方式。**

### Decision 3 — State Boundary

> 采用双状态体系:Semantic = `ready`/`incomplete`/`unknown`;Decision = `pending_review`/`approved`/`rejected`;**禁止合并**。
> unknown 语义单元必须:生成 reviewable record,进入 pending_review 流程。禁止:silent skip / silent conversion / silent fallback。

### Decision 4 — Contract Freeze Preparation

> 进入 Freeze Candidate Finalization。完成:①Contract v0.2 文字收口 ②删除旧的:Semantic Unavailable 等错误表述 ③`source_version_id` 歧义全部消除 ④补充 bytes capability requirement ⑤确认 87/71/16 范围表达。

### 约束与输出

> 继续禁止:修改业务代码 / 修改 schema / 修改数据 / IR 重新生成 / 图片恢复 / daemon 执行。
> 输出:A. Contract v0.2 Freeze Candidate Final 版;B. 最终 Remaining UNKNOWN 列表;C. Freeze 前执行步骤清单;D. Implementation Gap Matrix。**完成后等待 Owner Freeze 令。**

### §1septies 生产侧保守义(DSH 解释,非裁决;详件 = `PREPROCESSING-CONTRACT-v0.2-FREEZE-CANDIDATE-FINAL-v1.md`)

| 条款 | 生产侧落实语义 |
|---|---|
| Decision 1 | **命名变更面 = 仅契约侧字段名**:`source_version_id`(契约键)→ `source_content_sha256`;算法 SHA256(raw bytes)、格式 64 小写 hex、"值即 sha"语义全部不变;OQ-8′ 关闭,消歧方式 = **契约侧让名**(取代 §1sexies 回应中 N-1~N-4「V3 侧改名」PROPOSED,该方案作废;V3 UUID 列无需改名);存量零迁移(71 份 `ir.source_sha256` 即该值);Step 2 回填直接写新名,**无二次迁移**;文档引用纪律:契约键旧名一律读作 `source_content_sha256`,`source_version_id` 此后仅指 V3 内部 UUID FK |
| Decision 2 | 能力要求 = 义务面冻结(四项),传输方式 = 实现面不冻结(OQ-12′ 降级 delivery logistics);Review v1 §A.3 PROPOSED-BYTES **已被采纳**;V3 侧四项能力 not started(如实登记,不阻塞冻结) |
| Decision 3 | 与 DEC-023 Part 5/6 逐字一致,无新裁决;reviewable record 载体形态与两层状态字段落点仍未裁 |
| Decision 4 | 文字收口五项 = Claude 执行面(C-0a);DSH 侧同步本轮完成(Freeze Candidate Final v1 + Gap List v1.4 + Facts v2.3 + DepMap v2.4 + Review v1 承接注记) |
| 程序边界 | 本文件不是冻结令;冻结 = 五步序 Step 3,前置 = Step 1 快照 + Step 2 回填(执行令未下达);DSH 输出 A/B/C/D 已交付,**等待 Owner Freeze 令** |

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

- **字段名/算法/格式全部已裁(§1quinquies Part 1 DEC-SOURCE-IDENTITY)**:`source_version_id = SHA256(original source bytes)`,**64 字符小写 hex 字符串**;
- **path 身份地位已裁(§1quinquies Part 1-2)**:`source_file` = locator information(保留),**非 identity**;任何文档不得暗示 path/absolute path/directory 参与唯一/身份/version/hash 判断;**bytes 交付已裁(§1septies Decision 2)= 能力要求冻结**(获取 raw bytes + 独立重算 SHA256 + 与 `source_content_sha256` 比较 + fail-closed),传输方式不冻结;条款文本已定稿(FC-2),待 Claude 合入;
- ~~回填范围~~ **已裁 = 87**;
- IR 权威覆盖面:**当前面已裁 = 71 ADMITTED**;**再生成已裁(§1quinquies Part 3)= 允许但四约束**(bytes 不变 / id 一致 / 新 IR 绑定 id / 重过 identity verification + semantic validation)+ 四禁(禁改原 source / 禁重 OCR 覆盖 / 禁新 identity / 禁新 hash 替代);**执行令与 R52 工件版本策略仍未裁**;
- v1 legacy 面 79 份:**已裁 = historical asset 隔离**;披露形态(文字层):**未裁**(弱);
- 语义/决策状态机:**词表终局已裁(§1quinquies Part 5)**——semantic = `ready/incomplete/unknown`,decision = `pending_review/approved/rejected`(取代 §1ter D3 四状态合并记法);unknown 路由**已裁(§1quinquies Part 6)**= 产 reviewable record → pending_review workflow;**两层载体(字段名/落点)与 reviewable record 形态:未裁**;
- 16 份 Identity-only:**已裁(§1quinquies Part 3)= Identity Available / Semantic Pending(可恢复)**;接口面呈现字段:**未裁**(随载体);
- 执行顺序:**已裁五步**;Step 1 接口快照载体与 R50 血统(D-6)、存量 1 例原子性(D-3)、2 份三重成员(D-4)、全部数据动作执行令:**未裁**;
- **命名已终裁(§1septies Decision 1)**:跨系统身份字段 = **`source_content_sha256`**(SHA256(raw bytes),64 小写 hex 不变);原契约键 `source_version_id` 此后仅指 V3 内部 UUID FK;OQ-8′ 关闭;Review v1 N-1~N-4 作废;IR 侧字段名对齐(`source_sha256` 是否改名)= producer 实现动作待令;
- Contract v0.2 正文起草:**已裁由 Claude 执行**(四章节要求 = §1quinquies Part 7);Freeze Candidate Review v1 已交付(DEC-024);**Freeze Candidate Final v1 已交付(DEC-025 回应 = `PREPROCESSING-CONTRACT-v0.2-FREEZE-CANDIDATE-FINAL-v1.md`,FC-1~FC-5 终稿条款文本 + B/C/D)**;冻结:**未裁**(Owner Freeze 令 = 五步序 Step 3,前置 Step 1/Step 2 执行令未下达);等 Claude:C-0a 文字收口五项落字。

*v1 · 2026-09-16 · DSH 自记(Owner 聊天原文照录)。如有文字冲突,以 Owner 原文为准。*

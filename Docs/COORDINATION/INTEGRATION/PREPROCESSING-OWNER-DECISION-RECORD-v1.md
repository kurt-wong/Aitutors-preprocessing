# OWNER DECISION RECORD v1 — Integration Contract B1/B2/B3

> Status: **v1.25(2026-09-16,追加 §1sexvicies Closure Guardian Review DEC-044(登记挂起待 push)+ §1septenvicies DSH 自身全任务对抗性自审 DEC-045(完成:基线全 PASS 零漂移 + 0 BLOCKER/5 WARNING/5 NOTE + 存量修复 5 处);v1.24 = §1quinvicies DEC-043;v1.23 = §1quadvicies DEC-042;v1.22 = §1tervicies DEC-041)** · Authority: Owner 直接指令(聊天原文,DSH 自记)
> Ledger anchor: `state.yaml.decisions[DEC-019]`(总纲)+ `[DEC-020]`(DEC-B1 分项)+ `[DEC-021]`(§1ter)+ `[DEC-022]`(§1quater)+ `[DEC-023]`(§1quinquies)+ `[DEC-024]`(§1sexies)+ `[DEC-025]`(§1septies)+ `[DEC-026]`(§1octies)+ `[DEC-027]`(§1novies)+ `[DEC-028]`(§1decies)+ `[DEC-029]`(§1undecies)+ `[DEC-030]`(§1duodecies)+ `[DEC-031]`(§1tredecies;与 V3 侧 DEC-031 撞号,已知 R5-03 面)+ `[DEC-032]`(§1quaterdecies;与 V3 侧 DEC-032 撞号,已知 R5-03 面)+ `[DEC-033]`(§1quindecies;与 V3 侧编号潜在撞号,已知 R5-03 面)+ `[DEC-034]`(§1sexdecies;与 V3 侧编号潜在撞号,已知 R5-03 面)+ `[DEC-035]`(§1septendecies;与 V3 侧 DEC-035 撞号,已知 R5-03 面)+ `[DEC-036]`(§1octodecies;与 V3 侧 DEC-036 撞号,已知 R5-03 面)+ `[DEC-037]`(§1undevicies;与 V3 侧编号潜在撞号,已知 R5-03 面)+ `[DEC-038]`(§1vicies;与 V3 侧编号潜在撞号,已知 R5-03 面)+ `[DEC-039]`(§1semelvicies;与 V3 侧编号潜在撞号,已知 R5-03 面)+ `[DEC-040]`(§1bisvicies;与 V3 侧编号潜在撞号,已知 R5-03 面)+ `[DEC-041]`(§1tervicies;与 V3 侧编号潜在撞号,已知 R5-03 面)+ `[DEC-042]`(§1quadvicies;与 V3 侧编号潜在撞号,已知 R5-03 面)+ `[DEC-043]`(§1quinvicies;与 V3 侧编号潜在撞号,已知 R5-03 面)+ `[DEC-044]`(§1sexvicies;Closure Review,登记挂起待 push)+ `[DEC-045]`(§1septenvicies;DSH 自审)+ `state.yaml.integration_contract.owner_decision_b1b3` / `.owner_interface_finalization` / `.owner_interface_revision` / `.owner_contract_freeze_review` / `.owner_contract_freeze_finalization` / `.owner_step1_step2_execution` / `.owner_contract_freeze_closeout` / `.owner_freeze_confirmation` / `.owner_freeze_final_audit` / `.owner_freeze_object_verification` / `.owner_freeze_remote_verification` / `.owner_contract_frozen` / `.producer_baseline_finalized` / `.producer_baseline_archive_final` / `.producer_baseline_guardian` / `.producer_guardian_phase1`
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

## 1octies. 分项裁决 — Owner Final Decision Instruction v1(Owner 2026-09-16 第九轮,原文照录;canonical 引用面)

> Owner 令:四项最终确认 + Step 1/Step 2 执行授权 + 继续六禁 + Claude/DSH 任务 + Freeze 条件 + 延期五项。

### 一、最终确认事项(原文照录)

1. **Identity Authority**:跨系统文件身份唯一字段 = `source_content_sha256`;定义 = `SHA256(original source bytes)`;格式 = 64 字符 lowercase hex;规则 = 内容 hash 决定身份,path/source_file 仅为 locator,path 变化不得影响 identity,**禁止任何系统使用 path 作为唯一身份判断**。
2. **双层职责模型**:Manifest = Source Identity Authority(「这是哪个文件?」)/ IR = Semantic Consumption Authority(「这个文件表达了什么?」);V3 消费方向 = Manifest 验证身份 + IR 提供语义,两者不得混淆。
3. **命名确认**:跨系统 = `source_content_sha256`;V3 内部 = `source_version_id` 保持现状;禁止两个概念继续使用同名字段。
4. **16 份 Identity-only**:状态 = Identity Available / Semantic Pending;允许重新执行 preprocessing 生成 IR;约束 = `source_content_sha256` 必须保持一致 / 不创建新的 identity / 不修改历史 manifest / 不删除已有记录。

### 二、执行授权(原文照录)

> Step 1:Producer 生成接口快照——冻结 87 接口范围;记录:文件列表 / `source_content_sha256` / R50 关联关系。
> Step 2:Producer 执行 87 份 manifest 补齐 `source_content_sha256`;完成后逐份验证:Manifest hash = IR hash。

### 三、禁止事项(原文照录)

> 禁止:修改原始文件 / 修改 IR 语义内容 / 修改 Question 数据 / 图片恢复 / daemon 自动运行 / schema 变更。

### 四、Claude 任务(原文照录)

> 合并最终契约:`source_content_sha256` / path non identity / Identity Pending / bytes verification requirement;删除旧描述:全部替换 Semantic Unavailable → Semantic Pending;保持 V3 代码不修改。

### 五、DSH 任务(原文照录)

> 执行 Step 1 接口快照;执行 Step 2 Manifest 字段补齐;输出验证报告:必须包含 87 份文件列表 / hash 一致性检查 / IR 覆盖情况 / 16 份 pending 状态。

### 六、Freeze 条件 + 延期建议(原文照录)

> Step 2 完成并验证后:进入 Contract v0.2 Freeze。
> 建议继续延期(非架构阻塞点):legacy 79 份披露 / 17 拒收记录 / OCR/PDF 扩展面 / DEC 编号统一 / bytes 传输方式。
> 「目前 V3 最大的架构风险已经不是 preprocessing,而是未来 V3 消费端必须真正实现:拿到 bytes → 自己计算 SHA256 → 验证 Manifest → 验证 IR → 失败关闭。」

### §1octies 生产侧保守义(DSH 解释,非裁决;执行详件 = `PREPROCESSING-STEP1-STEP2-VERIFICATION-REPORT-v1.md`)

| 条款 | 生产侧落实语义 |
|---|---|
| 一、四项确认 | 与 DEC-025 FC-1~FC-4 逐条一致,无新裁决面;§1quater Part 4「不修改历史 manifest」保守义 = **不改既有键/语义**,不排斥 Owner 明令的追加身份键(否则 Step 2 授权自相矛盾) |
| 二、执行授权 | **已执行完毕**:Step 1 = `data/interface_scope_snapshot_step1.json` + audit `interface_scope_prebackfill`(corpus `4ad3458b…`);Step 2 = 87/87 回填(仅追加一键,内容寻址证明 = 剥键重序列化 sha 逐份 == R50 基线);R50 DRIFT = 恰 87 manifest(missing 0,预期);接口面新配对基线 = audit `interface_scope_postbackfill`(corpus `24af8f56…`,verify ok) |
| 三、六禁 | 全部保持:原始文件/IR 语义/Question 数据零改动;回填面 = Owner 明令授权字段,与「禁 schema 变更」不冲突 |
| 四、Claude 任务 | = C-0a(V3 侧,REPORTED 直至 V3 commit);DSH 零代做 |
| 六、延期五项 | 按建议不处理,登记于 §3;下一阶段核心 = V3 消费端 bytes→自算→验证→fail-closed 链条实现(Gap Matrix D-7~D-9) |
| 程序边界 | Freeze 令仍属 Owner:DSH 侧 Step 1/Step 2 前置**已全部满足**;剩余前置 = Claude 正文合并 |

## 1novies. 分项裁决 — Contract v0.2 最终冻结收口(DSH/Producer 侧)(Owner 2026-09-16 第十轮,原文照录;canonical 引用面)

### 一、Owner 已最终确认的原则(原文照录要点)

1. **跨系统唯一身份字段**:`source_content_sha256 = SHA256(original source bytes)`,64 位小写 hex;身份由源内容决定,**与文件存储路径完全无关**;`source_file` / path 只能作为 locator,禁止参与 identity 判断 / 唯一性判断 / 版本判断 / hash 判断。
2. **双层权威职责**:`Manifest = Source Identity Authority`;`IR = Semantic Consumption Authority`——Manifest 回答"这是哪个源文件",IR 回答"这个源文件表达了什么",两者不得混用。
3. **16 份文件** = Identity Available / Semantic Pending;允许未来重新运行 preprocessing 生成 IR;重新生成必须:复用原 `source_content_sha256` / 不创建新的 source identity / 不修改历史 Manifest 身份 / 不删除已有历史记录 / 不覆盖或篡改已有历史 IR 语义 / 保留完整血统关系。
4. **Contract v0.2 冻结后,上述原则不得在实现阶段自行改变。**

### 二、DSH 任务(原文照录要点)

- **Task 1 — Freeze Evidence 最终收口**:基于 Step 1 snapshot + Step 2 backfill + Step 2 verification report,建立明确的 Contract v0.2 Freeze Evidence;必须能够追溯 Contract v0.2 → Step 1 snapshot → Step 2 backfill → verification report,并记录实际 commit / 工件。
- **Task 2 — Producer 侧最终一致性检查**:逐项检查 87/87 interface scope、87/87 `source_content_sha256`、87/87 source bytes、71/71 IR hash 对账、16/16 Semantic Pending、R50 血统关系、path 不参与 identity;全部通过明确标记 **VERIFIED**;发现任何不一致**不要自行修复**,直接列为 **BLOCKER**。
- **Task 3 — Contract 文档交叉核验**:检查 Producer 侧所有相关文档,确保不再出现会导致歧义的旧定义;尤其检查 `source_version_id` / `source_content_sha256` / `source_file` / `path` / `Semantic Unavailable` / `Semantic Pending`;要求 `source_content_sha256` = 跨系统内容身份、`source_version_id` = V3 内部 UUID FK、path = locator、`Semantic Unavailable` 不得作为现行状态使用;历史审计注记可以保留,但必须明确标识为废止/历史。
- **Task 4 — 不做实现**:继续禁止 IR 重生成 / 图片恢复 / Question 修改 / schema 修改 / daemon / V3 业务代码修改 / 任何未经 Owner 授权的数据清洗。

### 三、输出要求(原文照录要点)

提交:①Freeze Evidence ②Producer 最终一致性检查报告 ③文档交叉核验结果 ④明确结论 = `READY FOR CONTRACT FREEZE` 或 `BLOCKED`(若 BLOCKED 必须给出具体证据)。**不要把"理论上应该如此"当成 VERIFIED。**

### 四、重要纪律(原文照录)

> 从本轮开始:**Decision ≠ Implementation。** 已经裁决的原则可以冻结,但尚未实现的 V3 能力仍必须标记 `not implemented / not started`。不要因为 Contract 已冻结,就声称 V3 已经具备身份验证、bytes 校验或 IR 验证能力。

### §1novies 生产侧保守义(DSH 解释,非裁决;执行详件 = `PREPROCESSING-CONTRACT-v0.2-FREEZE-EVIDENCE-v1.md`)

| 条款 | 生产侧落实语义 |
|---|---|
| 一、四项原则 | 与 DEC-025 FC-1~FC-4 / DEC-026 ①~④ 逐条一致,本轮性质 = **最终确认 + 实现阶段锁定**,无新裁决面 |
| Task 1 | Freeze Evidence v1 已建:追溯链 + 工件 sha256 全值 + commit(ff04f47 → e70807b → 本轮) |
| Task 2 | `scripts/freeze_evidence_final_check.py` 只读复核(全部从当前磁盘字节独立重推导,不信先前报告结论):**C1-C9 全 PASS,overall = VERIFIED,零 BLOCKER**;unique identities 87 / duplicate 0 |
| Task 3 | 交叉核验完成:Facts v2 → v2.5 现行态消歧(历史时点标识)、DepMap 两处更新、Alignment v4 行内**已废止**标识;剩余 `rg` 命中全部属允许保留的四类语境(原文照录 / 取代注记 / Claude 修正指令 / V3 UUID FK) |
| Task 4 | 零实现动作;数据写入面 = 零(唯一新数据文件 = 只读复核报告 JSON,属证据登记) |
| Decision ≠ Implementation | Freeze Evidence §5 钉死:V3 D-7/D-8/D-9/D-11 = **not started**;V3 现自算 hash 为 canonical_json 包裹(`runner.py:71-73`/`hashing.py:60-62`),非 raw bytes,不满足 FC-2 |
| 结论 | **READY FOR CONTRACT FREEZE**(Producer/DSH 侧证据结论;冻结令权在 Owner,正文合并义务在 Claude) |

## 1decies. 分项裁决 — Producer 侧 Contract Freeze 最终确认(Owner 2026-09-16 第十一轮,原文照录;canonical 引用面)

### 任务(原文照录要点)

> 本轮不执行任何新数据动作。
> **任务1:确认 Claude Contract 合并结果**——检查 Contract v0.2 最终文本是否包含:`source_content_sha256` / path non identity / Manifest·IR 职责 / 87·71·16 范围 / Semantic Pending / bytes verification requirement / fail-closed。
> **任务2:确认 Step1/Step2 证据链引用**——确认 Contract → Step1 snapshot → Step2 backfill → Verification report 链路完整。
> **任务3:保持实现边界**——明确记录以下仍为 NOT IMPLEMENTED:V3 raw bytes acquisition / SHA256 独立验证 / Manifest identity verification / IR identity verification / identity gate。
> **禁止事项**:不要重跑 IR / 修改 manifest / 修改 schema / 修改 V3 代码 / 扩展 Freeze 范围。
> **输出要求**:确认 `Producer READY FOR OWNER FREEZE` 或指出具体 BLOCKER。**不得提出新的架构裁决。**

### §1decies 生产侧保守义(DSH 解释,非裁决;执行详件 = `PREPROCESSING-CONTRACT-FREEZE-PRODUCER-CONFIRMATION-v1.md`)

| 条款 | 生产侧落实语义 |
|---|---|
| 任务1 | **七项全部 PASS**(逐项锚点行号在确认报告 §1;核验对象 = V3 仓契约工作树版本(Claude V3 `DEC-032` Consumer 收口稿,DSH 只读)):"Semantic Unavailable" 全文仅存废止/取代语境,无现行态使用 |
| 任务2 | **链路完整 PASS**(Contract v0.2 FC-1~FC-5 → Step 1 snapshot(pre audit `4ad3458b…`)→ Step 2 backfill(post audit `24af8f56…`)→ Verification report → Final check `aad2237`,工件 sha256 全值登记于 Freeze Evidence §1);另记两项 Claude 侧 WARNING(F-1 契约文本未引用工件 + 状态注记仍为执行前时点;F-2 收口稿 V3 工作树未提交) |
| 任务3 | 五项 **NOT IMPLEMENTED** 显式记录(确认报告 §3;与契约 §5.6.1 五项表逐项一致,双侧同判);契约冻结不交付任何能力 |
| 禁止事项 | 全部遵守:零数据动作、V3 仓只读、Freeze 范围未扩展、零新架构裁决 |
| 结论 | **Producer READY FOR OWNER FREEZE**(零 BLOCKER;F-1/F-2 供 Owner 在 Freeze 令中一并处置) |

## 1undecies. 分项裁决 — Contract v0.2 Freeze Producer Final Audit(Owner 2026-09-16 第十二轮,原文照录;canonical 引用面)

### 任务(原文照录要点)

> **Task 1 — Freeze Evidence Final Review**:重新确认 Step1 snapshot / Step2 backfill / Verification report / Final check 四者关联;输出 artifact / commit / sha256 / timestamp,形成最终证据链。
> **Task 2 — Contract 一致性检查**:确认 `source_content_sha256` / path non identity / 87·71·16 / Semantic Pending / bytes verification / fail closed 全部一致。
> **Task 3 — 协助冻结对象确定**:Producer 侧认可 Contract v0.2 Freeze Version 对应 repo / commit / document / hash,避免未来版本歧义。
> **Task 4 — 输出 Freeze Recommendation**(Producer Freeze Confirmation 格式:Status / Evidence / Remaining non-blocking items / Implementation boundary)。
> **禁止**:修改 source bytes / IR / Question / schema / pipeline。
> **建议流程**:Claude 修正 F-1/F-2 → DSH 最终确认 → Owner Freeze 令 → Contract v0.2 Frozen → 进入 V3 Consumer Identity Verification 实现阶段。
> **不再重开**:path 是否 identity / `source_version_id` 命名 / 16 份是否重跑 / hash 是否唯一;下一阶段转向 V3 消费链(bytes → SHA256 → Manifest 验证 → IR 验证 → fail-closed)。

### §1undecies 生产侧保守义(DSH 解释,非裁决;执行详件 = `PREPROCESSING-CONTRACT-v0.2-FREEZE-RECOMMENDATION-v1.md`)

| 条款 | 生产侧落实语义 |
|---|---|
| Task 1 | final check 本轮重跑 **C1-C9 全 PASS = VERIFIED**,产出字节与 DEC-027 登记 sha256 **1:1 复现**;五工件 sha256 复算 5/5 相符;证据链表(artifact/commit/sha256/timestamp)见推荐件 §1 |
| Task 2 | 六项在 **commit 化文本**(`c6e771c`,与工作树零差异)上全部一致,零不一致项(推荐件 §2) |
| Task 3 | 冻结对象四元组 = `kurt-wong/AITutors-v3` @ `c6e771cea6757043ee34307ec0ce1a7a0a62266d` / `PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` / sha256 `c8d89586…1032`;V3 工作树未跟踪文件均非冻结对象;**F-2 本地 commit 已闭合,但 `c6e771c` 未 push(origin/main = `69a6c0b`,领先 18 commits)→ 记 F-2′** |
| Task 4 | 输出 = **READY FOR FREEZE**;Remaining non-blocking = F-1(状态注记仍为执行前时点 + 零工件引用)/ F-2′(push)/ 长开项清单;Implementation boundary = 五项 NOT IMPLEMENTED |
| 禁止 | 零数据动作、零代码改动、V3 仓只读(fetch/ls-remote 仅读)、Freeze 范围未扩展、零新架构裁决;已裁四题未重开 |
| 结论 | **Producer READY FOR FREEZE**;建议 Freeze 令一并要求 Claude 处置 F-1(增补注记,不改条款正文)与 F-2′(push 后以远端 commit+hash 复核) |

## 1duodecies. 分项裁决 — Producer Final Freeze Object Verification(Owner 2026-09-16 第十三轮,原文照录;canonical 引用面)

### 任务(原文照录要点)

> **Task 1 — Confirm Freeze Artifact**:确认 Contract 实际冻结对象 repository / commit / document / sha256,必须与 Claude 侧一致;如发现 Artifact commit ≠ Registration commit,分别记录。禁改数据 / IR / source / 扩大冻结范围。
> **Task 2 — Verify Remote Availability**:remote reachable / commit exists / content hash matches;输出 Remote verification PASS/FAIL。
> **Task 3 — Evidence Chain Final Seal**:Contract → Step1 snapshot → Step2 backfill → Verification → Freeze Artifact 链路完整。
> **Task 4 — Producer Freeze Recommendation**(Producer Final Freeze Confirmation 格式)。
> **阶段定位**:冻结前不扩展设计范围;唯一待解 = 冻结对象唯一化 + remote 可复现性;下一阶段 = V3 Identity Verification Implementation。

### §1duodecies 生产侧保守义(DSH 解释,非裁决;执行详件 = `PREPROCESSING-CONTRACT-v0.2-PRODUCER-FINAL-FREEZE-CONFIRMATION-v1.md`)

| 条款 | 生产侧落实语义 |
|---|---|
| Task 1 | 冻结对象四元组**更新为 `f4941ff`**(V3 DEC-033;document sha256 = `9c6b9063…7528`);三方一致 = DSH 工作树字节 == commit tree blob 重导 == Claude 登记(EB-009/§9.2)。**Artifact commit(`f4941ff`)≠ Registration commit(`c6e771c`,DSH DEC-029 登记)→ 分别记录**:`c6e771c` 四元组降级为历史,唯一有效 = `f4941ff`;两者 diff 经 DSH 全量亲读 = 仅事实状态修正 + §9 登记新增,六项冻结内容零改动 |
| Task 2 | **Remote verification = FAIL**:reachable PASS / commit exists **FAIL**(origin/main = `69a6c0b`,本地领先 19 commits,`f4941ff` 未 push)/ content hash remote 比对 N/A。远端可复现性当前不成立 |
| Task 3 | 证据链 Final Seal **PASS**:契约 §9.1 内嵌登记值与 DSH 工件逐项相符;五工件 sha256 复算 5/5 零漂移;链路 Contract → Step1 → Step2 → Verification → Final Check → Freeze Artifact 完整闭合 |
| Task 4 | 输出 = 内容面 READY + remote 面 FAIL;**Remaining blockers = B-1(唯一,未 push)**;Implementation boundary = 五项 NOT IMPLEMENTED |
| 纪律 | 零数据动作 / 零代码改动 / V3 仓只读 / 冻结范围未扩展 / 零新架构裁决 / 已裁四题未重开;diff 判定亲读非 Claude 自述 |
| 结论 | 冻结对象内容面唯一且双侧一致;**B-1(Claude push)闭合前远端不可复现**——建议 Freeze 令与「push + DSH 远端复核(ls-remote HEAD == f4941ff + blob hash == 9c6b9063…)」并行或作为机械前置 |

## 1tredecies. 分项裁决 — Contract v0.2 Freeze Artifact 最终远端复核(Owner 2026-09-16 第十四轮,原文照录;canonical 引用面)

### 任务(原文照录要点)

> 验证 Claude push 后 Freeze Artifact 达到 remote reproducibility。严格限制:不修改 producer 数据 / manifest / IR / schema / Contract。
> 执行:① 获取 V3 origin/main 最新状态,`git merge-base --is-ancestor f4941ff origin/main` 必须包含;② `git show f4941ff:<Contract path>` 计算 sha256,必须等于 `9c6b9063e81fb2a66d85794b280c9d931f1b0074b39abf472033218149b17528`;③ 验证冻结对象四元组;④ 全部 PASS → 输出 `STATUS: CONTRACT FREEZE READY` + `B-1: CLOSED` 并提交 Producer Freeze Final Verification Report;失败 → 只报告具体失败项。
> 禁止重新讨论:identity key / path / `source_version_id` / Semantic Pending / 87·71·16 / bytes requirement。

### §1tredecies 生产侧保守义(DSH 解释,非裁决;执行详件 = `PREPROCESSING-CONTRACT-v0.2-PRODUCER-FREEZE-FINAL-VERIFICATION-REPORT-v1.md`)

| 检查 | 结果 |
|---|---|
| ① 远端包含性 | **PASS**——`origin/main` = `305bd81`(DEC-034);`merge-base --is-ancestor f4941ff origin/main` = TRUE;远端历史亲验 `305bd81 → f4941ff → c6e771c → …` |
| ② 文档 hash | **PASS**——commit 内容重导 = `9c6b9063…7528` == 必须值;补充:`f4941ff..origin/main` 对契约文件 diff 零差异(DEC-034 仅改四份协调文档,未触碰契约) |
| ③ 四元组 | **PASS**——repo / commit / document / sha256 四点互相钉死,远端可复现 |
| ④ 结论 | **STATUS: CONTRACT FREEZE READY;B-1: CLOSED**——Producer 侧 blocker 清零;冻结令权在 Owner(READY ≠ FROZEN);Implementation boundary = NOT IMPLEMENTED 不变 |
| 纪律 | 五类目标全部未修改;V3 仓只读;已裁六项未重开;零新架构裁决 |

## 1quaterdecies. 分项裁决 — Contract v0.2 Frozen 状态最终登记确认(Owner 2026-09-16 第十五轮,原文照录;canonical 引用面)

### 任务(原文照录要点)

> 任务:完成 Contract v0.2 Frozen 状态最终登记确认。目标:确认 Freeze Event 后 Producer 侧账本一致。
> 严格限制:①不修改 producer 数据 ②不修改 manifest ③不修改 IR ④不修改 schema ⑤不修改 Contract Artifact。
> 执行:① 验证 Freeze Artifact——commit `f4941ff`,hash `9c6b9063e81fb2a66d85794b280c9d931f1b0074b39abf472033218149b17528`,确认 remote reachable = TRUE;② 更新 Producer 侧登记——state.yaml / CURRENT.md / log,记录 Contract v0.2: **FROZEN**;③ 输出最终状态:`STATUS: CONTRACT FROZEN`。
> 同时明确:Freeze does not include——bytes verification implementation / identity gate implementation / IR verification implementation。
> 下一阶段:**V3 Consumer Identity Verification Implementation**。

### §1quaterdecies 生产侧保守义(DSH 解释,非裁决;执行记录)

| 检查 | 结果 |
|---|---|
| Freeze Artifact 验证 | **PASS**——`git ls-remote origin main` = `4daecf0b…`(remote reachable = TRUE);`merge-base --is-ancestor f4941ff origin/main` = TRUE(远端历史 `4daecf0b → 305bd81 → f4941ff → c6e771c`,新增 `4daecf0b` = V3 DEC-035 文档轮,契约零触碰);`git show f4941ff:<contract>` **字节级重导 sha256 = `9c6b9063…7528`** == 必须值(92,197 bytes);`f4941ff..origin/main` 契约文件 diff 零差异 |
| Producer 侧登记 | **Contract v0.2: FROZEN**——state.yaml(DEC-032 + `owner_contract_frozen` 块)/ CURRENT.md / log.md 三件同步;冻结对象四元组 = `kurt-wong/AITutors-v3` @ `f4941ff87c0130ee0b79ff6b807c4ec2826b8ff1` / `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` / sha256 `9c6b9063…7528`(唯一有效;`c6e771c`/`c8d89586…1032` = 历史登记) |
| Freeze 不含(明确登记) | bytes verification implementation / identity gate implementation / IR verification implementation(契约 REQUIREMENT ≠ 现状;五项 V3 消费能力仍全部 NOT IMPLEMENTED) |
| 下一阶段 | **V3 Consumer Identity Verification Implementation**(bytes → SHA256 → Manifest 验证 → IR 验证 → fail-closed → Gate → Admission;实现排期属 V3 侧) |
| 纪律 | 五类目标(producer 数据 / manifest / IR / schema / Contract Artifact)全部零修改;V3 仓只读(fetch / ls-remote / show / diff);已裁六项未重开;零新架构裁决 |

## 1quindecies. 分项裁决 — Producer Frozen Baseline Final Integrity Record 收口(Owner 2026-09-16 第十六轮,原文照录;canonical 引用面)

### 任务(原文照录要点)

> 任务:Producer Frozen Baseline Final Integrity Record 收口。目标:完成 Frozen Producer Baseline 的最终登记。
> 允许:只读验证、文档登记。
> 禁止:代码修改、数据修改、Manifest 修改、IR 修改。
> 执行:① 提交当前 `PREPROCESSING-PRODUCER-FROZEN-BASELINE-INTEGRITY-REPORT-v1.md`;② 登记 state.yaml / CURRENT.md / log.md——记录 DEC / FACT / evidence location / git status;③ 对 git remote 状态重新执行:`git fetch origin` / `git ls-remote origin main` / `git merge-base --is-ancestor f4941ff origin/main`——如失败必须记录真实错误,**不得引用历史结果作为本轮观察**;④ 最终确认 Producer Baseline:source bytes immutable / manifest immutable / IR immutable / evidence immutable。
> 输出:`STATUS: PRODUCER BASELINE FINALIZED`,并明确:Consumer Identity Verification **NOT IMPLEMENTED**。

### §1quindecies 生产侧保守义(DSH 解释,非裁决;执行详件 = `PREPROCESSING-PRODUCER-FROZEN-BASELINE-INTEGRITY-REPORT-v1.md`)

| 检查 | 结果 |
|---|---|
| ① 报告提交 | `PREPROCESSING-PRODUCER-FROZEN-BASELINE-INTEGRITY-REPORT-v1.md` = commit **`8fc4d60`**(Task 1-3 完成:证据可访问性 PASS / C1-C9 复跑 VERIFIED / 不可变性证明) |
| ② 三账登记 | state.yaml(DEC-033 + FACT-036 + `producer_baseline_finalized` 块)/ CURRENT.md(状态头 + 快速恢复节 + agent 表)/ log.md(DEC-033 条目)同步;evidence location = 报告 + 六工件登记表;git status = 提交前工作树仅报告一项 untracked→已提交,数据面零改动 |
| ③ 远端状态(本轮真实观察) | 首试:`git fetch origin` **FAIL**(沙箱 `.git/FETCH_HEAD` Permission denied,exit 255)+ `git ls-remote origin main` **FAIL**(schannel `SEC_E_NO_CREDENTIALS`,exit 128)+ is-ancestor 对**本地 ref**(`72af28d`)TRUE——真实错误如实入账,未引用 DEC-031/032 历史结果;宽模式重试:**fetch OK** / `ls-remote origin main` = **`72af28d5854b56fc605e1897fb757703826a6233`**(remote reachable = TRUE,较 DEC-032 时点 `4daecf0b` 前进,Claude 侧持续推进属预期)/ `merge-base --is-ancestor f4941ff origin/main` = **TRUE**(冻结对象仍包含于远端 main) |
| ④ 四项 immutable | **source bytes immutable**(C4:87/87 零漂移 vs Step 1 快照 + R50)/ **manifest immutable**(C8:差异恰 = 追加一键;证据工件 sha 登记值 6/6 相符)/ **IR immutable**(C5:71/71 对账零漂移,未再生成未改写)/ **evidence immutable**(六工件 Get-FileHash 实测与登记 sha256 全数相符;复跑输出与已登记 final check 字节级一致 `a707738e…5c33`) |
| 最终状态 | **STATUS: PRODUCER BASELINE FINALIZED**;**Consumer Identity Verification NOT IMPLEMENTED**(raw bytes acquisition / SHA256 独立验证 / Manifest identity verification / IR identity verification / identity gate 五项全部不变;Freeze 不含三项实现) |
| 纪律 | 零代码 / 零数据 / 零 Manifest / 零 IR 修改;写入面 = 台账 + 文档登记;Freeze 范围未扩展;零新架构裁决;已裁六项未重开 |

## 1sexdecies. 分项裁决 — Producer Frozen Baseline Archive Final Check(Owner 2026-09-16 第十七轮,原文照录;canonical 引用面)

### 任务(原文照录要点)

> 任务:Producer Frozen Baseline Archive Final Check。目标:完成 Producer Frozen Baseline 的最终归档。
> 允许:只读验证、文档登记。
> 禁止:代码修改、数据修改、Manifest 修改、IR 修改。
> 执行:① 确认:source bytes immutable / manifest immutable / IR immutable / evidence immutable;② 登记 state.yaml / CURRENT.md / log.md,记录 **PRODUCER BASELINE FINALIZED**;③ 记录远端验证结果——必须区分:**Observed(本轮实际执行结果)/ Historical(之前验证结果)**;④ 输出最终状态:`PRODUCER BASELINE: FINALIZED` + `CONSUMER IDENTITY: NOT IMPLEMENTED`。
> 提交:Producer Baseline Archive Final Report。

### §1sexdecies 生产侧保守义(DSH 解释,非裁决;执行详件 = `PREPROCESSING-PRODUCER-BASELINE-ARCHIVE-FINAL-REPORT-v1.md`)

| 检查 | 结果 |
|---|---|
| ① 四项 immutable 终检 | **全 PASS**(本轮只读复跑,从当前磁盘字节独立重推导):source bytes(C4:87/87 零漂移 vs Step 1 快照 + R50)/ manifest(C8:剥键重序列化 == R50 回填前 sha 87/87,差异恰 = 追加一键;工件 sha 全数不变)/ IR(C5:71/71 零漂移)/ evidence(六工件登记 sha 6/6 相符 + 复跑输出与已登记 final check 字节级一致 `a707738e…5c33`);C1-C9 全 PASS = VERIFIED;测试 338 passed / 1 xfailed |
| ② 三账登记 | state.yaml(DEC-034 + FACT-037 + `producer_baseline_archive_final` 块 + next 追加)/ CURRENT.md(更新头 + 快速恢复节 + 状态头 + agent 表)/ log.md(DEC-034 条目);报告提交 = commit **`56f95f2`** |
| ③ 远端验证分账 | **Observed(本轮实际执行)**:V3 `git fetch origin` OK(沙箱升级后执行;本会话早前同命令曾被 `.git/FETCH_HEAD` 写权限拒绝,属沙箱策略非仓库问题)/ `git ls-remote origin main` = **`72af28d5854b56fc605e1897fb757703826a6233`**(reachable = TRUE,与 DEC-033 轮一致未再前进)/ `merge-base --is-ancestor f4941ff origin/main` = **TRUE**;**Historical(仅存档引用,不冒充本轮观察)**:DEC-031 = `305bd81` + 契约 blob 重导 `9c6b9063…7528` / DEC-032 = `4daecf0b` + 字节级重导同值 / DEC-033 = 首试 fetch·ls-remote FAIL(真实错误已入账)+ 升级重试 `72af28d` TRUE |
| ④ 最终状态 | `PRODUCER BASELINE: FINALIZED` / `CONSUMER IDENTITY: NOT IMPLEMENTED`(五项 V3 消费能力不变;Freeze 不含三项实现) |
| 归档声明 | 基线以 Archive Final Report §1.1 工件表字节为准;任何后续变化必须先有 Owner 令并产生新快照配对,不得就地改写;R50 血统解释不变(drift == 恰 87 为预期);长开项与延期五项不因归档而关闭 |
| 纪律 | 零代码 / 零数据 / 零 Manifest / 零 IR 修改;已登记工件零覆盖(复跑后再验 hash 不变);Freeze 范围未扩展;零新架构裁决;已裁六项未重开 |

## 1septendecies. 分项裁决 — Producer Frozen Baseline Guardian Mode(Owner 2026-09-16 第十八轮,原文照录;canonical 引用面)

### 任务(原文照录要点)

> 阶段定位:已跨过 V3 Contract Design → Contract Freeze → Producer Baseline Freeze → Consumer Identity Design Freeze;下一阶段真正风险已从「设计错误」转移到「实现纪律」;重点不是继续讨论 Contract,而是确保实现严格满足:raw bytes → SHA256(raw bytes) → Manifest verification → IR consistency check → Consumer Identity Gate → existing Gate/Admission;并保持 Requirement ≠ Capability / Design ≠ Implementation / Consumer ≠ Producer。
> 状态:Producer baseline 已 FINALIZED;Contract v0.2 已 FROZEN。
> 下一阶段禁止:修改 producer 数据 / manifest / source bytes / IR / freeze artifact。
> Task:Producer Frozen Baseline Guardian Mode。执行:① 建立 Consumer Implementation Boundary Audit(确认 Consumer implementation 不会改变 frozen baseline);② 建立 immutable monitoring checklist(监控 source bytes hash / manifest hash / IR hash / evidence artifact hash);③ 不参与 Consumer Identity Verification 代码实现;④ 输出 `PREPROCESSING-PRODUCER-FROZEN-BASELINE-CONSUMER-BOUNDARY-CHECK-v1.md`。
> 要求:只读检查。零代码。零数据。零 schema。等待 Owner 后续指令。

### §1septendecies 生产侧保守义(DSH 解释,非裁决;执行详件 = `PREPROCESSING-PRODUCER-FROZEN-BASELINE-CONSUMER-BOUNDARY-CHECK-v1.md`)

| 检查 | 结果 |
|---|---|
| ① Consumer Implementation Boundary Audit | **通过(BOUNDARY HOLDING,零违例)**:边界模型 = Consumer 实现合法写面仅 V3 仓代码,对 Producer 基线五类禁改对象全部只读;六步链(S1 bytes / S2 SHA256 / S3 Manifest 验证 / S4 IR 对账 / S5 Identity Gate / S6 既有 Gate·Admission)逐项登记边界不变式,五项能力全部 NOT IMPLEMENTED;本轮证据 = post-backfill audit 177 锚定文件全量比对 **checked=177 bad=0** + 六证据工件 6/6 + IR 工件 `fbcf41ab…b04a5` 相符 |
| ② Immutable Monitoring Checklist | **M1~M6 全 PASS**(source bytes / manifest / IR / evidence / 聚合指纹 corpus 双值 / 冻结对象四元组跨仓);期望值全值入册;触发点(每轮开工前 / Consumer 实现里程碑后 / 疑似接触事件后)+ 偏差协议(任一 mismatch → STOP 只报告不自修,处置权 = Owner)在位 |
| ③ Non-Participation | DSH 不参与 Consumer Identity Verification 代码实现(不写 V3 代码、不代写、不提供补丁);角色 = Producer Frozen Baseline Guardian;复核 ≠ 实现 |
| ④ 输出 | `INTEGRATION/PREPROCESSING-PRODUCER-FROZEN-BASELINE-CONSUMER-BOUNDARY-CHECK-v1.md`(docs-only) |
| Observed(本轮) | 本仓 `origin/main` = `e1584bd`(== HEAD);V3 `origin/main` = `72af28d`(reachable TRUE);测试 338 passed / 1 xfailed |
| 纪律 | 只读检查;零代码 / 零数据 / 零 schema;基线工件零覆盖;零新架构裁决;已裁六项未重开;衔接 DEC-033/DEC-034 结论不重复不推翻 |

### §1octodecies Producer Frozen Baseline Guardian During Consumer Phase 1(DEC-036,Owner 原文照录 2026-09-16)

> Task:Producer Frozen Baseline Guardian During Consumer Phase 1。
>
> 状态:
> Producer Baseline FINALIZED。
> Consumer Implementation 即将开始。
>
> 保持 Guardian Mode。
>
> 执行:
>
> 1. Phase 1 开始前 baseline snapshot check。
> 验证:
> - source bytes hash
> - manifest hash
> - IR hash
> - evidence artifact
>
> 2. Consumer Phase 1 完成后:
> 执行只读检查:
> 确认:
> Consumer 代码提交没有修改:
> - producer data
> - manifest
> - IR
> - freeze artifact
>
> 3. 若发现:
> 任何 hash mismatch
> 立即:
> STOP
> 仅报告。
> 禁止:
> 自动修复。
>
> 4. 输出:
> PREPROCESSING-PRODUCER-GUARDIAN-PHASE1-CHECK-v1.md
>
> 限制:
> 零代码修改。
> 零数据修改。
> 零 schema 修改。
>
> 角色:
> Guardian only。

### §1octodecies 生产侧保守义(DSH 解释,非裁决;执行详件 = `PREPROCESSING-PRODUCER-GUARDIAN-PHASE1-CHECK-v1.md`)

| 检查 | 结果 |
|---|---|
| ① Phase 1 开工前 baseline snapshot | **PASS 零 mismatch(OBSERVED 本轮)**:M1~M6 全量只读核验——177 锚定文件全量比对 checked=177 / missing=0 / mismatch=0(锚 = post-backfill audit files map,快照自身 sha = `2cb980c7…4096` 相符;md=87 / manifest=87);证据六工件 + R50 辅助锚 **7/7** match;M6 冻结对象跨仓字节重导 bytes=92,197 sha256 = **`9c6b9063…7528`** MATCH + is-ancestor `f4941ff` TRUE + `f4941ff..origin/main` 契约 diff empty(临时重导文件即时清理) |
| ② Phase 1 完成后只读检查 | **ARMED 未执行**:触发 = V3 远端出现 Phase 1 实现提交(Owner 令复核或疑似接触事件);检查面 = producer data(M1)/ manifest(M2)/ IR(M3,`fbcf41ab…b04a5`)/ freeze artifact(M6)+ M4 辅助;判读纪律 = Consumer 侧新增代码提交本身非违例(合法写面 = V3 仓代码),违例仅指只读对象字节变化 |
| ③ 偏差协议 | 任何 mismatch → **STOP 仅报告(对象/期望值/实测值),禁止自动修复**(不自修 / 不重写 / 不回滚 / 不改锚);处置权 = Owner(变化须 Owner 令 + 新配对快照) |
| ④ 输出 | `INTEGRATION/PREPROCESSING-PRODUCER-GUARDIAN-PHASE1-CHECK-v1.md`(docs-only) |
| Observed(本轮) | 本仓 `origin/main` = `27727c4`(开工时工作树干净);V3 `origin/main` = `72af28d`(fetch 首试 Recv failure 重试 OK 后亲验;与 DEC-033/034 同值未前进,均为 docs 轮,**尚无 Consumer Phase 1 实现提交** → 本轮即开工前锚点);Observed/Historical 分账 |
| 纪律 | 只读检查;零代码 / 零数据 / 零 schema;基线工件零覆盖;零新架构裁决;已裁六项未重开;DSH 不参与 Consumer 实现代码(Guardian only) |

### §1undevicies Consumer Phase 2 开工前 Baseline Check(DEC-037,Owner 原文照录 2026-09-16)

> 继续 Producer Frozen Baseline Guardian。
>
> 任务:
> Consumer Phase 2 开工前 Baseline Check。
>
> 要求:
>
> 1. 只读检查:
> - source bytes
> - manifest
> - producer IR
> - evidence artifacts
> - freeze artifact
>
> 2. 不修改任何内容。
>
> 3. 输出:
> PREPROCESSING-PRODUCER-GUARDIAN-PHASE2-CHECK-v1.md
>
> 报告必须区分:
>
> Observed:
> 本轮实际执行结果
>
> Historical:
> 历史登记结果
>
> 禁止:
> - 使用历史结果冒充当前观察
> - 自动修复 mismatch
> - 修改producer数据
>
> 若发现 mismatch:
> 立即 STOP,仅报告。
>
> 否则:
> 登记 Guardian checkpoint。
>
> 不要参与 Consumer 代码实现。

### §1undevicies 生产侧保守义(DSH 解释,非裁决;执行详件 = `PREPROCESSING-PRODUCER-GUARDIAN-PHASE2-CHECK-v1.md`)

| 检查 | 结果 |
|---|---|
| ① source bytes / manifest / IR(M1~M3) | **PASS 零 mismatch(OBSERVED 本轮)**:177 锚定文件全量比对 checked=177 / missing=0 / mismatch=0(锚 = post-backfill audit files map,快照自身 sha = `2cb980c7…4096` 相符;md=87 / manifest=87);M3 IR `fbcf41ab…b04a5` 独立散列相符 |
| ② evidence artifacts(M4)+ corpus(M5) | 六证据工件 + R50 辅助锚 **7/7** match=True(逐项全值见报告 §1.2);M5 双值 pre `4ad3458b…19160` / post `24af8f56…0a10` 相符 |
| ③ freeze artifact(M6,跨仓) | 字节重导 bytes=92,197 sha256 = **`9c6b9063…7528`** MATCH + `merge-base --is-ancestor f4941ff origin/main` TRUE + `f4941ff..origin/main` 契约 diff empty(临时重导即时清理,不落仓) |
| ④ Observed / Historical 分账 | **Observed(本轮)**:本仓 `HEAD` = `bebd9e1`(== origin/main);V3 `origin/main` = `72af28d`(fetch 首试沙箱拒绝,宽模式重试 OK 后亲验;未前进,远端提交链全 docs,**尚无 Phase 1/Phase 2 实现提交**);REPORTED(Owner 宣告 Phase 2 开工)与 OBSERVED 分账不混写。**Historical**:DEC-032~036 各轮观测仅存档引用,未混入本轮判定 |
| ⑤ mismatch 处置 | 零触发;偏差协议不变 = 任一 mismatch → STOP 仅报告,禁止自动修复,处置权 = Owner |
| ⑥ Guardian checkpoint | 已登记(state.yaml `producer_guardian_phase2` 块 + DEC-037 + CURRENT.md + log.md + 本 ODR v1.18);Trigger ②(post-Phase1 recheck)继续 ARMED |
| 纪律 | 只读检查;零代码 / 零数据 / 零 schema;基线工件零覆盖;零新架构裁决;已裁六项未重开;DSH 不参与 Consumer 实现代码(Guardian only) |

### §1vicies Consumer Phase 2 开发期间 Guardian checkpoint(DEC-038,Owner 原文照录 2026-09-16)

> 继续 Producer Frozen Baseline Guardian。
>
> 目标:
> Consumer Phase 2 开发期间保持 Producer Frozen Baseline 完整性。
>
> 当前状态:
> - Contract v0.2 = FROZEN
> - Freeze Artifact = f4941ff
> - Consumer Phase 1 已完成
> - Consumer Phase 2 = M1 Manifest Reader
>
> 一、检查范围
> 执行 Guardian checkpoint:
> - G1 source bytes
> - G2 manifest
> - G3 producer IR
> - G4 evidence artifacts
> - G5 corpus snapshots
> - G6 freeze artifact
>
> 注意:Guardian 编号不得使用 Consumer M1/M2/M3/M4/M5。后续统一:G = Guardian Check,M = Consumer Module。避免两个体系混淆。
>
> 二、只读纪律
> 允许:hash 计算 / diff 检查 / 文件读取 / git 验证。
> 禁止修改:source bytes / manifest / IR / evidence artifacts / freeze artifact。
> 禁止:自动修复 mismatch。
>
> 三、报告纪律
> 必须严格区分:Observed = 本轮实际执行结果;Historical = 历史登记结果。
> 禁止:使用历史 commit/hash 冒充当前观察。
>
> 四、Consumer 边界纪律
> Consumer 新增代码:不是违例。合法写面:V3 Consumer implementation。
> 违例:Frozen Producer baseline 发生字节变化。
> 判断标准:不是"代码是否新增",而是"冻结对象是否变化"。
>
> 五、术语纪律
> 避免:IR hash OK。改为:Producer IR artifact hash unchanged。
> 区分:Producer IR artifact / Consumer IR reader output / Derived verification result。避免 IR 概念污染。
>
> 六、异常协议
> 如果发现 bytes / manifest / IR / evidence / freeze artifact mismatch:立即 STOP,报告 Owner。
> 禁止:自动恢复。禁止:重新生成。禁止:覆盖旧工件。
>
> 七、输出
> 输出:PREPROCESSING-PRODUCER-GUARDIAN-PHASE2-CHECK-v1.md。并登记:state.yaml / CURRENT.md / log.md。
> 保持 Guardian only。不要参与 Consumer 实现。

### §1vicies 生产侧保守义(DSH 解释,非裁决;执行详件 = `PREPROCESSING-PRODUCER-GUARDIAN-PHASE2-CHECK-v1.md` 轮次 2)

| 检查 | 结果 |
|---|---|
| ① G1 source bytes / G2 manifest | **PASS 零 mismatch(OBSERVED 本轮)**:177 锚定文件全量比对 checked=177 / missing=0 / mismatch=0(锚 = post-backfill audit files map,快照自身 sha = `2cb980c7…4096` 相符;md=87 / manifest=87) |
| ② G3 producer IR artifact | **Producer IR artifact hash unchanged**(`data/resolver_ref_r52/resolver_ir.json` = `fbcf41ab…b04a5`;与 Consumer IR reader output / Derived verification result 严格区分) |
| ③ G4 evidence artifacts + G5 corpus snapshots | 六证据工件 + R50 辅助锚 **7/7** match=True(逐项全值见报告 §1.2);G5 双快照 pre `4ad3458b…19160` / post `24af8f56…0a10` 相符 |
| ④ G6 freeze artifact(跨仓) | 字节重导 bytes=92,197 sha256 = **`9c6b9063…7528`** MATCH + `merge-base --is-ancestor f4941ff origin/main` TRUE + `f4941ff..origin/main` 契约 diff empty(临时重导即时清理,不落仓) |
| ⑤ Observed / Historical 分账 | **Observed(本轮)**:本仓 `HEAD` = `056b6d6`(== origin/main);V3 `origin/main` = `72af28d`(fetch 首试沙箱拒绝,宽模式重试 OK 后亲验;未前进,远端无实现提交);V3 本地工作树 = untracked Consumer 实现文件(OBSERVED 文件清单;REPORTED = Phase 1 IMPLEMENTED / Phase 2 M1 COMPLETE 待 Phase 3 授权,untracked 未 commit = REPORTED 级)。**Historical**:DEC-032~037 各轮观测仅存档引用,未混入本轮判定 |
| ⑥ Consumer 边界纪律 | 新增代码全部落在 V3 仓合法写面,**非违例**;本轮 G1~G6 实测五类冻结对象零变化 → **零违例**;CONSUMER IDENTITY: NOT IMPLEMENTED 口径 = V3 远端已提交实现,本地 REPORTED 实现 commit+push 前不改变登记 |
| ⑦ 异常协议 | 零触发;任一 mismatch → STOP 仅报告(对象/期望值/实测值),禁自动恢复 / 禁重新生成 / 禁覆盖旧工件,处置权 = Owner |
| ⑧ Guardian checkpoint | 已登记(state.yaml `producer_guardian_phase2_round2` 块 + DEC-038 + CURRENT.md + log.md + 本 ODR v1.19);Trigger ② 继续 ARMED(实现仅存 V3 本地 untracked);测试 338 passed / 1 xfailed |
| 纪律 | 只读检查;零代码 / 零数据 / 零 schema;基线工件零覆盖;术语纪律(G/M 编号隔离);零新架构裁决;已裁六项未重开;DSH 不参与 Consumer 实现代码(Guardian only) |

### §1semelvicies Producer Frozen Baseline Guardian During Phase 2-M3(DEC-039,Owner 原文照录 2026-09-16)

> Task: Producer Frozen Baseline Guardian During Phase 2-M3
>
> 继续保持 Guardian Mode。
>
> 目标:监督 Consumer Identity Verification Phase 2-M3 实现期间,Producer Frozen Baseline 不发生任何变化。
>
> 检查范围,仅检查:G1 source bytes / G2 manifest / G3 producer IR artifact / G4 freeze evidence artifacts / G5 corpus snapshots / G6 freeze artifact。
>
> 判定规则
> 允许:Consumer 新增代码 / Consumer 新增测试 / Consumer 新增设计文档。
> 禁止:source bytes 修改 / manifest 内容修改 / producer IR 修改 / freeze artifact 修改 / schema 修改。
>
> 特别关注
> 本阶段重点关注:IR 文件是否被 Consumer 读取后产生污染。注意:读取 IR ≠ 修改 IR。仅 bytes mismatch 才触发 STOP。
>
> 输出要求
> 完成后报告:G1-G6 状态 / Observed 与 Historical 分离 / 是否触发 STOP / Consumer 代码提交是否影响冻结对象。
> 禁止:修改 Consumer 实现 / 提供代码补丁 / 自行修复 mismatch。若发现 mismatch:STOP,仅报告 Owner。

### §1semelvicies 生产侧保守义(DSH 解释,非裁决;执行详件 = `PREPROCESSING-PRODUCER-GUARDIAN-PHASE2-CHECK-v1.md` 轮次 3)

| 检查 | 结果 |
|---|---|
| ① G1~G6 状态 | **全 PASS 零 mismatch(OBSERVED 本轮)**:G1+G2 177 锚定文件全量比对 checked=177 / missing=0 / mismatch=0(快照自身 sha `2cb980c7…4096` 相符;md=87 / manifest=87);G3 Producer IR artifact hash unchanged(`fbcf41ab…b04a5`);G4 证据 7/7 match=True;G5 pre `4ad3458b…19160` / post `24af8f56…0a10`;G6 字节重导 bytes=92,197 sha `9c6b9063…7528` MATCH + is-ancestor TRUE + 契约 diff empty |
| ② 特别关注 = IR 污染 | **无污染**:G3 字节零变化(读取 ≠ 修改);旁证 = V3 本地 `ir_identity.py` 亲读(仅 `read_text` 提取,无写路径) |
| ③ Observed / Historical 分离 | **Observed(本轮)**:本仓 `HEAD` = `40c06c9`(== origin/main);V3 `origin/main` = `72af28d`(fetch 本轮直接成功;未前进,远端无实现提交);V3 本地较 DEC-038 新增 `ir_identity.py` + `test_adversarial_manifest.py`(untracked = REPORTED)。**Historical**:轮次 2/1、DEC-036~032 仅存档引用 |
| ④ STOP 状态 | **NOT TRIGGERED**(零 mismatch) |
| ⑤ Consumer 提交影响判定 | **未影响冻结对象**:新增代码/测试全部落在 V3 合法写面;五类冻结对象实测零变化;零违例 |
| ⑥ Guardian checkpoint | 已登记(state.yaml `producer_guardian_phase2_m3` 块 + DEC-039 + CURRENT.md + log.md + 本 ODR v1.20);测试 338 passed / 1 xfailed |
| 纪律 | 只读检查;零代码 / 零数据 / 零 schema;基线工件零覆盖;未修改 Consumer 实现 / 未提供代码补丁 / 未自行修复 mismatch;零新架构裁决;已裁六项未重开;Guardian only |

### §1bisvicies Producer Frozen Baseline Guardian During Phase 2-M4(DEC-040,Owner 原文照录 2026-09-16)

> # Phase 2-M4 Guardian Check — Producer Frozen Baseline
>
> 继续保持:GUARDIAN MODE = ACTIVE / BOUNDARY = HOLDING。本轮 Consumer 将实现 M4 Identity Verifier。
>
> 一、Guardian 目标:确保 M4 实现期间以下冻结对象完全不发生变化:1. source bytes 2. Manifest 3. Producer IR artifact 4. Freeze evidence artifacts 5. corpus snapshots 6. Contract Freeze Artifact。
>
> 二、特别关注 M4 的 Authority Boundary:本轮重点不是判断 Consumer 代码好不好。重点检查:Consumer 是否试图修改、重写或重新生成 Producer 的身份/语义事实。特别检查:Producer IR 是否仅被读取 / Manifest 是否仅被读取 / source bytes 是否保持不变 / 是否出现任何"修复 IR / 回写 Manifest / 重生成 Producer artifact"的行为。
>
> 三、必须坚持的判断纪律:以下均不是违规 —— 新增 Consumer code / 新增 Consumer tests / 新增 Consumer documentation。真正的 Guardian violation 是:Frozen Producer Asset bytes changed。因此不要因为看到新的 M4 Python 文件就判定违规。
>
> 四、重点复核对象:G1 source bytes / G2 Manifest / G3 Producer IR artifact / G4 Freeze evidence / G5 corpus snapshots / G6 Freeze artifact。
>
> 五、特别检查 duplicate/path 问题:Consumer 不得因为 same SHA + different locator 而要求 Producer 数据重新生成或修改。同一内容多个 locator 是合法情况。不要把 path uniqueness 当作 Producer integrity violation。
>
> 六、触发 STOP 的条件:只有出现实际冻结对象 mismatch 才 STOP,并:记录 Observed / 保留证据 / 不自行修复 / 不修改 Producer 数据 / 不提供 Consumer patch / 等待 Owner 裁决。
>
> 七、输出:完成 M4 开工/开发期间 Guardian Check 后报告:G1-G6 / Observed 与 Historical 分离 / 是否触发 STOP / Producer IR 是否保持 immutable / Manifest 是否保持 immutable / source bytes 是否保持 immutable / Freeze Artifact 是否保持 immutable / Consumer 新增代码是否仅位于合法写面。并提交 Guardian 报告及三账登记。
>
> 继续保持:DSH = Producer Frozen Baseline Guardian / NOT = Consumer implementer。不得参与 M4 代码实现。

### §1bisvicies 生产侧保守义(DSH 解释,非裁决;执行详件 = `PREPROCESSING-PRODUCER-GUARDIAN-PHASE2-CHECK-v1.md` 轮次 4)

| 检查 | 结果 |
|---|---|
| ① G1~G6 状态 | **全 PASS 零 mismatch(OBSERVED 本轮)**:G1+G2 177 锚定文件全量比对 checked=177 / missing=0 / mismatch=0(快照自身 sha `2cb980c7…4096` 相符;md=87 / manifest=87);G3 Producer IR artifact hash unchanged(`fbcf41ab…b04a5`);G4 证据 7/7 match=True;G5 pre `4ad3458b…19160` / post `24af8f56…0a10`;G6 字节重导 bytes=92,197 sha `9c6b9063…7528` MATCH + is-ancestor TRUE + 契约 diff empty |
| ② Authority Boundary(本轮重点) | **HOLDS**:Producer IR / Manifest / source bytes 仅被读取(字节零变化);**未出现**修复 IR / 回写 Manifest / 重生成 Producer artifact 行为 —— V3 `backend/` 全树写路径排查,命中项全落合法面(测试 tmp_path / 既有 scripts / 既有 import 上传目录),`app/core/` 身份链三模块零写路径;M4 模块未落树(设计层 = 零 IO 纯函数,READINESS = IMPLEMENTATION READY,REPORTED 级);四项 immutable 全部实测保持 |
| ③ duplicate/path 特别检查 | **无违规倾向**:Consumer 设计 F8a 明确 same content + different locator = 允许,各文件独立进入验证链,不要求 Producer 重新生成/修改;与已裁"path 非身份"一致 |
| ④ Observed / Historical 分离 | **Observed(本轮)**:本仓 `HEAD` = `3916852`(== origin/main);V3 `origin/main` = `72af28d`(fetch 首试沙箱拒绝如实入账,宽模式重试 OK;未前进,远端无实现提交);V3 本地较 DEC-039 新增 3 件测试(`test_ir_identity.py` / `test_adversarial_ir_identity.py` / `test_adversarial_ir_round2.py`,untracked = REPORTED)。**Historical**:轮次 3/2/1、DEC-036~032 仅存档引用 |
| ⑤ STOP 状态 | **NOT TRIGGERED**(零 mismatch) |
| ⑥ Consumer 新增代码写面 | **仅位于合法写面**:新增 3 件全在 V3 仓 `backend/tests/`;五类冻结对象实测零变化;零违例 |
| ⑦ Guardian checkpoint | 已登记(state.yaml `producer_guardian_phase2_m4` 块 + DEC-040 + CURRENT.md + log.md + 本 ODR v1.21);测试 338 passed / 1 xfailed |
| 纪律 | 只读检查;零代码 / 零数据 / 零 schema;基线工件零覆盖;未修改 Consumer 实现 / 未提供代码补丁 / 未自行修复 mismatch;零新架构裁决;已裁六项未重开;Guardian only,未参与 M4 代码实现 |

### §1tervicies 对 DEC-040 轮结果的第一性原理对抗性审查(DEC-041,Owner 原文照录 2026-09-16)

> 从第一性原理出发,针对本轮结果开启一轮严格的对抗性审查,每个结论必须有真实测试作为证据。不要降低测试和验证标准,不要自我合理化任何问题,不要强行解释未通过测试的内容,不要靠推测输出结论。

### §1tervicies 生产侧保守义(DSH 解释,非裁决;执行详件 = `PREPROCESSING-PRODUCER-GUARDIAN-M4-ADVERSARIAL-REVIEW-v1.md`)

| 检查 | 结果 |
|---|---|
| ① 总判定 | DEC-040 冻结对象结论(G1~G6 / 四项 immutable / Authority Boundary / 零违例)**全部经对抗性复测维持且加强**;STOP 未触发(审查全程零冻结对象字节变化) |
| ② 覆盖面加强(新实测) | R50 356 逐文件活测首次执行 = **269 MATCH / 87 预期 DRIFT / 0 unexpected**(87 与 177 锚 manifest 名单 **SET_EQUAL=True**,键级抽验证实单键 `source_content_sha256` 追加 = 已裁 Step-2 回填);原面 source_file 层活测 = **87/87 decl == 活 sha == Step2 报告值**(三方比对);扩展写路径清扫 + Producer 路径引用检索 + 三身份模块全文亲读 = 全部纯读零写路径 |
| ③ 发现 F-A(更正) | DEC-040"untracked 文档计数差 1"**证伪**:本轮 9 件与 DEC-038 名单 9 件 SET_EQUAL=True 零增删;真实来源 = DEC-038 自称 10 实列 9 的历史计数错误;更正登记 = 文档面自 DEC-038 起即 9 件零增删(REPORTED 事实层错误,不涉冻结对象字节) |
| ④ 发现 F-B(方法学,已修复) | G5 原执行强度弱于名称所示(仅读快照 `corpus_sha256` 字段,活语料未实测),已升级为逐文件活测并建议常态化(待令) |
| ⑤ 发现 F-C(未复现,挂账) | `corpus_sha256` 聚合构造 7 种候选(含原始字节全拼接)均未复现,如实挂账不推测;操作性锚 = 逐文件 map(已实测) |
| ⑥ 证据纪律 | 两次失败测试原样入账:0/87 错路径比对(审查方构造错误,以 source_file 指针三方比对 87/87 纠正)+ digest 构造未复现;测试基线独立第 3 次复跑 338 passed / 1 xfailed;G4 7/7 复跑;G6 残留 False + 亲缘 TRUE + 契约 diff EMPTY |
| 纪律 | 全程只读(docs-only 登记除外);未改 Consumer 实现 / 未改 Producer 数据 / 未提供补丁 / 未自行修复;零新架构裁决;已裁六项未重开 |

### §1quadvicies Consumer M5 Boundary Guardian Review(DEC-042,Owner 原文照录 2026-09-16)

> 进入下一轮:**Consumer M5 Boundary Guardian Review**。Claude 本轮将从 M4 转入 M5 Consumer Gate Integration。你的职责仍然保持 Guardian/Adversarial Reviewer 定位:**只审查,不替 Claude 实现;不自动修复;不修改 Producer;不改变冻结 Contract。**
>
> **一、审查对象必须是 Claude 实际 push 的 Consumer commit**:不要仅审查本地 untracked 文件,也不要用 Claude 报告中的测试结果作为证据。必须:1 获取 Claude 实际 push 的 V3 commit;2 记录 exact commit SHA;3 从该 commit 重新检查 Consumer implementation;4 独立运行必要测试;5 所有结论都以本轮真实证据收口。如果 Claude 尚未 push M5:**不要提前宣布 M5 通过。**
> **二、继续执行 Producer Guardian 基线**:保留现有 G1–G6。重点确认 source bytes 未变化 / Manifest 未变化 / Producer IR 未变化 / evidence artifacts 未变化 / freeze artifacts 未变化 / Producer baseline hash·逐文件 map 未变化 / Contract freeze object 未被 Consumer 修改。任何 Producer 对象变化:**STOP。**
> **三、重点审查 Consumer → Producer Boundary**:针对 M5 以及 M1–M4 全链路做静态 + 动态审查。确认 Consumer 只能 READ Producer artifacts,不能 WRITE / REWRITE / REGENERATE / NORMALIZE-IN-PLACE / DELETE / RENAME / TOUCH-MTIME。尤其搜索 open(..., "w") / write_bytes / write_text / os.replace / shutil.move / unlink / rename / tempfile + replace / pickle·np.save 等潜在落盘方式 / Producer path references / manifest mutation / IR mutation。继续保持"发现即登记,不自行修复"的纪律。
> **四、必须新增 M5 语义边界攻击**:独立验证 Truth Table(FAILED+None→BLOCK;FAILED+PENDING→BLOCK;VERIFIED+PENDING→BLOCK;VERIFIED+AVAILABLE→PASS;VERIFIED+None→BLOCK)。最高优先级:**VERIFIED + PENDING → BLOCK**,必须有真实测试证据。
> **五、重点攻击 stale IR**:构造 raw bytes = A / Manifest SHA = SHA(A) / IR source SHA = SHA(B),要求确认 Identity = VERIFIED / Semantic = PENDING / M5 = BLOCK,并继续检查 stale IR 是否有任何路径能够进入 Gate / Admission / semantic consumer。如果存在 bypass:**记录为 Consumer Boundary failure。不要修改代码。**
> **六、攻击 Missing/Invalid Manifest**:分别测试 Manifest missing / source_content_sha256 missing / = null / = "" / invalid SHA / Manifest SHA != actual raw bytes。必须确认这些情况不会因为 M1 Reader 返回 None 而被错误解释成 Semantic PENDING 或者 Identity VERIFIED。
> **七、攻击 Missing / Malformed IR**:区分 1 IR missing;2 IR source identity missing;3 IR source identity mismatch;4 malformed JSON;5 wrong type。不要自行规定语义。严格按照当前 Frozen Contract / Design v1.1 判断:哪些应该 PENDING;哪些应该 ERROR/BLOCK;哪些绝不能继续 semantic consumption。如果实现与 Contract 不一致:**登记为 discrepancy,不要替 Claude 修改。**
> **八、检查"Identity Authority 不被 IR 劫持"**:验证 IR = arbitrary value 不能改变 Identity State。保持 M4 已建立的核心不变量:Identity ↑ Raw Bytes + Manifest;Semantic ↑ IR。不能反过来。
> **九、检查真实调用链,而不是只检查 M5 返回值**:重点检查 M1→M2→M3→M4→M5→Gate→Admission。必须证明 M5 BLOCK 后面不会继续发生 semantic Gate / Compiler consumption / Admission / materialization / instance creation。尤其关注 runner_b2.py 以及任何实际入口。
> **十、不要把 Producer Guardian 结论扩大解释**:Producer Guardian 可以证明 Producer unchanged / Producer boundary holds / Frozen artifacts unchanged;不能单独证明 M5 correct / Consumer semantics correct / IR correctly consumed / Admission safe。如果 Consumer code 审查证据不足,就明确写 NOT VERIFIED。不要用 Producer G1–G6 代替 Consumer correctness。
> **十一、历史方法学改进继续保留**:逐文件活测(不只读 aggregate corpus_sha256)/ source_file 指针目标三方比对 / SET_EQUAL / 错误路径攻击原样入账 / 未复现问题原样登记 / 不做无证据归因。特别注意:不要因为测试失败就猜测根因;证据不足只写 OBSERVED / NOT REPRODUCED / ROOT CAUSE UNKNOWN。
> **十二、最终报告必须给出**:1 exact Claude commit SHA;2 Producer baseline SHA;3 G1–G6;4 Producer immutable check;5 Consumer boundary check;6 M5 Truth Table 实测结果;7 stale IR attack;8 missing IR attack;9 invalid Manifest attack;10 bypass attack;11 full pytest result;12 STOP / NOT STOP;13 VERIFIED / NOT VERIFIED 项目清单。最终结论必须明确区分 PRODUCER BOUNDARY 和 CONSUMER SEMANTIC CORRECTNESS,不得合并成一个结论。Guardian 原则继续保持:**只读、独立、证据驱动、不替 Claude 修复、不修改 Producer。**

### §1quadvicies 生产侧保守义(DSH 解释,非裁决;执行详件 = `PREPROCESSING-PRODUCER-GUARDIAN-M5-BOUNDARY-REVIEW-v1.md`)

| 检查 | 结果 |
|---|---|
| ① 审查对象 | V3 `origin/main` = **`72af28d…6233`**(ls-remote 亲验,远端零新提交);`ls-tree`/`git grep` 证实该 commit **零身份链代码** —— **M5 未 push,不宣布 M5 通过**(NOT VERIFIED,无对象) |
| ② Producer 基线 | G1~G6 **全 PASS 零漂移**(177/177 mismatch=0;R50 356 活测 269/87 SET_EQUAL/0 unexpected;source_file 三方 87/87;G6 重导 MATCH + 亲缘 TRUE + 契约 diff EMPTY);四项 immutable 全成立;**STOP NOT TRIGGERED** |
| ③ Boundary 静态 | core 五模块写面清扫零命中(全纯读/纯函数);scripts 写点全部 V3 内部报告输出;Producer 路径引用全部只读 |
| ④ Truth Table | 五格(含最高优先级 **VERIFIED+PENDING→BLOCK**)经真实文件链实测全符合;越域伪造值 6/6 fail-closed BLOCK;PASS 可达条件唯一 |
| ⑤ stale IR | 函数层实测 VERIFIED/PENDING/**BLOCK** 唯一出口,无函数层 bypass;**真实链层面 M5 零集成(runner_b2 不调用 M1–M5)= '阻断下游' NOT VERIFIED(INTEGRATION PENDING)** |
| ⑥ Manifest 6 变体 | 全部 fail-closed:None 路径只流向 FAILED/BLOCK,无一误读为 PENDING/VERIFIED;invalid 5 例全抛 ManifestReadError |
| ⑦ IR 5 变体 | **D1 discrepancy(行为级)**:IR missing 实现抛 `IRReadError`,vs Design v1.1 §4.4/F5 = None(PENDING 正常态)与 Contract 16 份 Semantic Pending 语义 —— 登记不代改;其余 4 变体与 Design 一致 |
| ⑧ IR 劫持 | 7 ir 变体 × 2 身份情形 = 14/14 不变量成立;M4 结构亲读确认单向 |
| ⑨ 真实调用链 | runner.py / runner_b2.py / runner_b3.py / p32 全部零身份链调用;runner_b2 `input_identity` 无 sha —— 集成缺口登记,下轮必查 |
| ⑩ 两结论分离 | **PRODUCER BOUNDARY = HOLDS(VERIFIED)**;**CONSUMER SEMANTIC CORRECTNESS = NOT VERIFIED(对 push commit 无对象;本地快照 = 语义电池 27/27 PASS + 4 discrepancy + 集成缺口)** |
| ⑪ pytest | 全量 642 passed / 959 errors(全部 = 环境无 PostgreSQL 的 ConnectionRefused at setup,原样入账);身份链子集 642 passed / 122 errors(同因,Claude 新 M5 测试不可复验,ROOT CAUSE = 环境 DB 缺失);自建电池 27/27 |
| ⑫ 移动目标 | 审查期间 `identity_gate.py` 3602→4391 B(+值域白名单 fail-closed)、两个新测试文件出现 —— 原样入账,动态结论锚定 `f3636b35…` 快照;此即"必须以 push commit 为对象"的实证 |
| 纪律 | 全程只读(docs-only 登记除外);未改 Consumer 实现 / 未改 Producer 数据 / 未提供补丁 / 未自行修复 D1~D4;零新架构裁决;已裁六项未重开 |

### §1quinvicies 对 DEC-042 轮(代码本轮结果)的第一性原理对抗性审查(DEC-043,Owner 原文照录 2026-09-16)

> 针对代码本轮结果开启一轮严格的对抗性审查,每个结论必须有真实测试作为证据。不要降低测试和验证标准,不要自我合理化任何问题,不要强行解释未通过测试的内容,不要靠推测输出结论。

### §1quinvicies 生产侧保守义(DSH 解释,非裁决;执行详件 = `PREPROCESSING-PRODUCER-GUARDIAN-M5-REVIEW-ADVERSARIAL-v1.md`)

| 检查 | 结果 |
|---|---|
| ① 总判定 | DEC-042 冻结对象与语义结论(G1~G6 / 四项 immutable / M5 push ABSENT / Truth Table 五格 / 零写面 / runner 零集成)**全部复测维持且加强**;STOP 未触发 |
| ② 证据加强 | push commit 零身份链代码换方法三重证实(`ls-tree -r` 434 文件 / 全仓 `git grep` / preprocessing_consumer 枚举);v2 电池 27/27 复现 ×2;盲区补测 13/13(manifest 顶层非对象/目录/BOM/前后空白全 fail-closed;IR 嵌套键不读;链确定性 5x);本地快照五模块散列与 DEC-042 锚逐项相等 |
| ③ F-1(撤回) | DEC-042「ROOT CAUSE = 环境 DB 缺失」= **超证据归因,撤回**:实测 port 5432 不监听(事实),但同进程内 `migrated_db` 按文件确定性分化(`test_hashing` 5/5 全错 / `test_raw_bytes` 4/4 全过,顺序无关,--setup-show 亲证 fixture 归属),机制不可复现 → 更正为 **OBSERVED 分化 + ROOT CAUSE UNKNOWN** |
| ④ F-2(时效) | errors 959→1036(总用例 1603→1680,增量相容 `m5_round2` 被收集);errors 计数**非基线**,passed=642 三轮稳定;子集 122/122 errors 全量普查唯一异常类型 = ConnectionRefusedError at setup(证实),全量面维持抽样级证据 |
| ⑤ F-3(证伪) | DEC-042 untracked 记「10 docs(REPORT-PHASE2-M4 新增)+ 15 tests」错误:实测 **9 docs + 5 core + 14 tests = 28**(docs 与已裁 9 件名单 SET_EQUAL=True);REPORT-PHASE2-M4 在全部工具输出零记录,不推测来源 |
| ⑥ F-4(升级) | 「642==642 巧合 OBSERVED」→ 已解释:verbose 普查全量 passed 642 **精确来自 10 个身份链文件合计 642**(m4_round2 355 等;m5_integration/m5_round1/identity_gate 三文件 0 passed 全 error) |
| ⑦ D5(新 discrepancy) | M5 对 None/无 identity 对象输入抛 `AttributeError`,与 M5 docstring 及 Design v1.1 §4.6「不抛异常」矛盾(M4 正常输出不可达;失败方向 = raise 非 bypass);登记不代改;累计 D1~D5 |
| 纪律 | 全程只读(docs-only 登记 + 临时 scratch 除外,轮末清理);未改 Consumer 实现 / 未改 Producer 数据 / 未提供补丁 / 未自行修复;自我错误原样入账并撤回/更正;不可复现机制写 UNKNOWN 零推测;已裁六项未重开 |

### §1sexvicies Consumer Boundary Closure Guardian Review(DEC-044,Owner 原文照录 2026-09-16)

> 进入下一轮:**Consumer Boundary Closure Guardian Review**。本轮重点从 Producer-only Guardian 扩展到:**在 Claude 实际提交的 V3 Consumer commit 上,独立验证 Producer Boundary + Consumer Semantic Boundary。**仍然保持:只读;独立复测;不替 Claude 修改;不修改 Producer;不修改 Frozen Contract;不用 Claude 的测试输出代替自己的证据;无证据不得推断 root cause。
> **一、第一步必须锁定 Claude 的实际 remote commit**:Claude push 后获取 exact commit SHA;`ls-remote` 亲验;以该 commit 作为 Consumer 审查对象;**不接受 local untracked 状态作为最终证据**。如果 Claude 尚未 push:**不得宣布 Consumer Boundary Verified。**
> **二、Producer Guardian G1–G6 继续执行**(source bytes / Manifest / Producer IR / evidence / freeze artifacts / contract freeze / source_file target / producer path zero write;保留 177/177 逐文件 active check 与 356 active artifact checks + SET_EQUAL + 0 unexpected;基线不变则只报告实际结果,不机械重复历史结论)。
> **三、重点审查 M3 discrepancy**:IR missing / IR identity missing / IR identity null / IR identity empty / malformed IR / wrong type / stale/mismatch IR,严格依据 Frozen Design v1.1 判断;**不要因为 Claude 把 malformed IR 归为 PENDING 就默认接受**,必须核对 Contract 是否允许。
> **四、重点审查 M5 discrepancy D5**:None identity / None semantic / missing identity attribute / wrong type / fake enum-like object / custom `__eq__`;检查是否抛异常、是否产生 PASS、是否可能 bypass、是否符合 Design v1.1 §4.6;如果「不抛异常」是冻结要求而实现仍抛异常:登记为 Consumer Contract discrepancy,不要自行修。
> **五、最高优先级:真实 Runner Boundary**:actual Runner → M1 → M2 → M3 → M4 → M5 → semantic Gate → Admission;确认 M5 不是旁路测试模块;确认 `runner_b2.py` 及其他实际入口不存在绕过路径。
> **六、必须做真实 downstream bypass attack**:不要只调用 `evaluate_identity_gate(...)`,必须攻击真实执行链,至少验证 A Manifest mismatch / B raw bytes mismatch / C IR missing / D IR stale / E IR malformed / F Identity VERIFIED + Semantic PENDING;对所有 BLOCK 情况独立证明 Compiler/Gate/Admission/Materialization/Question·Instance write 全部 not called;**只要有一个 semantic consumer 在 M5 BLOCK 后执行:Consumer Boundary failure。**
> **七、验证最关键不变量**:VERIFIED+AVAILABLE→PASS / VERIFIED+PENDING→BLOCK / FAILED+None→BLOCK / FAILED+PENDING→BLOCK;并特别验证 IR mismatch 不能 Identity VERIFIED → bypass Semantic Gate。
> **八、继续检查 Authority 分离**:Identity Authority = Raw Bytes + Manifest;Semantic Authority = Producer IR;不存在 IR→Identity 或 Path→Identity 反向污染。
> **九、Producer mutation attack**:Consumer 执行前后重新比较 source bytes / Manifest / IR / evidence / freeze artifacts;特别关注 write_text / write_bytes / os.replace / rename / unlink / tempfile+replace / shutil.move / accidental cache write 到 Producer 路径;静态搜索 + 动态前后 hash 双重证据。
> **十、最终报告必须严格分层**(不要用一个总的 PASS 覆盖所有结论):Producer Boundary(VERIFIED/NOT VERIFIED)/ Consumer Module(M1/M2/M3/M4/M5)/ Consumer System Boundary(VERIFIED/NOT VERIFIED)/ Real Runner Bypass(PASS/FAIL)/ Producer Mutation(PASS/FAIL)/ Contract Discrepancies(D1–D5 及新增逐项最终状态)/ STOP(只有 Producer 或 Frozen Boundary 被实际破坏才触发;Consumer correctness 问题登记为 Consumer Boundary failure/discrepancy,不混淆两者)。
> 最终要求:**不要因为 Producer G1–G6 全 PASS,就把 Consumer M5 判定为通过。**Consumer correctness 必须有 Consumer-side 独立证据。本轮目标不是增加测试数量,而是回答唯一关键问题:**在真实 V3 执行链中,任何未经 Identity + Semantic 双重验证的数据,是否绝对无法进入 semantic Gate / Admission?**

### §1sexvicies 生产侧保守义(DSH 解释,非裁决;状态 = 登记挂起,待 Claude push 后执行)

| 项 | 保守义 |
|---|---|
| 登记状态 | DEC-044 已登记 state.yaml `decisions`(status: active,执行挂起);触发 = Claude push exact SHA + `ls-remote` 亲验;**push 前不判 Consumer Boundary Verified,亦不启动** |
| 审查对象纪律 | local untracked 一律 OBSERVED-LOCAL 级;最终证据 = 从 push commit 重检 + 独立测试;DEC-042/043 期间本地锚两度失效(gate/ir 模块)已实证该纪律 |
| 强制检查面 | 集成缺口(runner_b2 等真实入口是否接入 M1–M5)+ downstream bypass A~F 的「BLOCK 后全链 not called」证明 + M3/M5-D5 专项 + Authority 分离 + mutation 前后 hash 双证据 |
| 分层输出 | 七面分别判定;G1–G6 全 PASS ≠ M5 通过;STOP 触发条件仅 = Producer/Frozen Boundary 实际破坏 |
| 顺延项 | D1~D5 最终状态逐项核对(Claude 收口情况);攻击套件复跑依赖 aitutor-postgres(DEC-045 D-045-4) |

### §1septenvicies DSH 自身全任务对抗性自审(DEC-045,Owner 原文照录 2026-09-16)

> 在等候claude的过程中,我们先完成自身全任务的对抗性审查。看是否仍有遗留问题。一切从项目文档和第一性原理出发。

### §1septenvicies 生产侧保守义(DSH 解释,非裁决;执行详件 = `PREPROCESSING-DSH-SELF-ADVERSARIAL-AUDIT-v1.md`)

| 项 | 结果 |
|---|---|
| 基线复测 | 全部本轮独立执行 PASS 零漂移:177/177 mismatch=0;R50 356 = 269/87 SET_EQUAL 双向/0;source_file 三方 87/87;工件 8/8 MATCH;G6 重导 MATCH + 亲缘 TRUE + diff EMPTY;pytest 338/1 ×2;log.md append-only 亲验;git 卫生干净 |
| 发现 | 0 BLOCKER / 5 WARNING / 5 NOTE(S-1 双 conftest 冲突;S-2 攻击套件复跑面缺口;S-3 G6 假 MISMATCH 方法错误当场纠正;S-4 DEC-014 七章节格式系统性缺口;R-1/R-2/R-6 更正指针缺失;L-10 归属漂移;R-3 子代理误报驳回;R-4/5/7 NOTE) |
| 存量修复 | 5 处(报告 A 勘误指针 / state.yaml 行内 F-1 指针 / CURRENT.md 归属修正 / conftest 复跑命令落字 / 指令链补 294c7fe);历史文本零删改 |
| Owner Decision Points | D-045-1 攻击套件治理(推荐 attacks 独立 ini)/ D-045-2 今后轮次强制七章节(推荐 是)/ D-045-3 更正回指规则入 PROTOCOL(推荐 是)/ D-045-4 DB 恢复后攻击套件复验是否下令 |
| 纪律 | V3 仓零写入;未改 Consumer 实现 / Producer 数据;自我错误与子代理误报原样入账;不可复现机制写 UNKNOWN |

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
- 执行顺序:**已裁五步**;**Step 1/Step 2 执行令已下达并执行完毕(§1octies 二)**——接口快照载体 = `data/interface_scope_snapshot_step1.json` + pre/post 双 audit 快照(R50 血统 = 成员超集保留为历史基线,接口面基线角色由双快照承接);**存量 1 例(D-3)、2 份三重成员(D-4)、16 份 IR 再生成批次与 R52 工件版本策略:未裁**;
- **命名已终裁(§1septies Decision 1)**:跨系统身份字段 = **`source_content_sha256`**(SHA256(raw bytes),64 小写 hex 不变);原契约键 `source_version_id` 此后仅指 V3 内部 UUID FK;OQ-8′ 关闭;Review v1 N-1~N-4 作废;IR 侧字段名对齐(`source_sha256` 是否改名)= producer 实现动作待令;
- Contract v0.2 正文起草:**已裁由 Claude 执行**(四章节要求 = §1quinquies Part 7;合并清单更新 = §1octies 四);Freeze Candidate Review v1 已交付(DEC-024);**Freeze Candidate Final v1 已交付(DEC-025 回应 = `PREPROCESSING-CONTRACT-v0.2-FREEZE-CANDIDATE-FINAL-v1.md`,FC-1~FC-5 终稿条款文本 + B/C/D)**;**Step 1/Step 2 已执行 + 验证 PASS(DEC-026 回应 = `PREPROCESSING-STEP1-STEP2-VERIFICATION-REPORT-v1.md`)**;冻结:**未裁**(Freeze 条件已具备,等 Claude 正文合并 + Owner Freeze 令 = 五步序 Step 3)。
- **延期五项(§1octies 六,Owner 建议)**:legacy 79 份披露 / 17 拒收记录治理 / OCR-PDF 扩展面 / DEC 编号统一 / bytes 传输方式——不处理,非架构阻塞点。

*v1 · 2026-09-16 · DSH 自记(Owner 聊天原文照录)。如有文字冲突,以 Owner 原文为准。*

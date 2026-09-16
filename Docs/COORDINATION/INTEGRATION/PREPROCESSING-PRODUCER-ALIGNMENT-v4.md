# PREPROCESSING PRODUCER ALIGNMENT v4(Owner 指定编号)

> Status: **v4(2026-09-16,PREPROCESSING / V3 Interface Decision Finalization v1 回应轮)** · Authority: Owner 统一版指令(2026-09-16,聊天原文照录于 `PREPROCESSING-OWNER-DECISION-RECORD-v1.md` §1quater;ledger = `state.yaml.decisions[DEC-022]`)
> Role: DSH = Source Evidence Producer 侧对齐件。本轮目标 = **决策固化 + 双侧对齐基线**,不是实现。
> 本轮纪律(Owner 令原文):不修改代码 / 不执行数据清洗 / 不执行数据迁移 / 不冻结数据库实现 / 不提前实现未裁事项;DSH 另守:不修改数据文件、不修改 schema、不改 Contract 正文(v0.2 正文本轮起草责任在 Claude 侧,见 §B.7)。
> 前序版本(编号沿革):Producer Interface Facts v1/v2 + B1B3 Readiness v1 + Producer Readiness v3 + Producer Decision Alignment v1(`PREPROCESSING-PRODUCER-DECISION-ALIGNMENT-v1.md`,保留原文,本文件承接)。
> Discipline: OBSERVED / DECISION(生产侧生效解释)/ IMPLEMENTATION GAP / UNKNOWN 四段;所有实现状态 = **not started**;无证据一律标 UNKNOWN。

---

## A. OBSERVED(生产侧事实,全部既有工件复用,零新数据动作)

| # | 事实 | 证据 |
|---|---|---|
| A-1 | Manifest 166 份全量字段面:**0/166 携任何 sha/hash 键,0/166 携 `source_version_id`** | `data/producer_interface_probe_v2.json.p1b_manifest_identity_gap`;Facts v2 §2.2 |
| A-2 | raw bytes SHA-256 单点生产已在库且双语料实证:md `resolver_reference.py:52-53`(→`:249` 文件级 / `:167` 单元级),PDF `r67_manifest_bootstrap.py:181`(OCR 清单 1,801 条,**语义不同不可混用**) | Facts v2 §4.1 |
| A-3 | IR `resolver_ir.json` = 88 记录(71 ADMITTED / 1,664 单元 + 16 QC_FAIL + 1 REJECTED_V1);71 份 `ir.source_sha256` == provenance == 当前磁盘 md 原始字节 sha256,**71/71 零漂移**——"V3 重算 hash 验证"在生产侧已用同算法全量实证可行 | Facts v2 §3.1/§3.2 |
| A-4 | 接口面口径:字段口径 `identity_version=="2"` = **87**(= v1 legacy 79);IR 当前消费面 = **71 ADMITTED**;接口面内无 IR 成员 = **16 份**(87 − 71) | Facts v2 §2.4/§3.1;Readiness v3 |
| A-5 | 双层现有关联 = `source_file` 绝对路径值相等(**非 id**);且绝对路径为本机绑定,跨机不可解析 | Facts v2 §2.1/§3.4 |
| A-6 | 非标 `unit_type` 存量恰 **1 例**(`andalone_question`),manifest 面与 IR 面原样保留(生成器 `resolver_reference.py:152` 逐字复制),但 producer 链**零守卫**;按 DEC-021 D3 口径该存量单元非 READY | Facts v2 §5;FACT-033⑥ |
| A-7 | v0.1 Contract 现状与新裁决的差距 = 七项清单(DECISION-ALIGNMENT-v1 §E),本轮继续有效 | `PREPROCESSING-PRODUCER-DECISION-ALIGNMENT-v1.md` §E |

---

## B. DECISION — Interface Decision Finalization v1 生产侧生效解释(DSH 保守义,非新增裁决)

> 裁决原文照录见 ODR §1quater(Part 1–6 + 最终原则三条)。以下仅记录生产侧生效后果。

### B.1 Part 1 — 双层职责模型(与 DEC-020 一致,本轮升为正式采用)

- Manifest 回答 **"这个东西是谁"**(source identity / source version / raw bytes hash / 文件版本关系);
- IR 回答 **"文件里面有什么"**(question structure / semantic annotation / knowledge / unit information);
- 双禁成立:Manifest 不得替代 IR 描述题目;IR 不得替代 Manifest 证明文件身份。生产侧零新增动作,现有两工件职责天然分层。

### B.2 Part 2 — 生产/消费责任边界(本轮核心新增)

| 面 | Producer(DSH) | Consumer(V3) |
|---|---|---|
| Manifest | 生成 Manifest / 计算 `source_version_id` / 保证字段正确 | 验证 Manifest / **重新计算 hash** / 判断是否接受 |
| IR | OCR 后结构化 / LLM 语义解析 / 生成 IR | 验证 IR 符合契约 / Gate 判断 / 拒绝不符合数据 |

- 总原则固化:**Preprocessing 负责解释,V3 负责接受或拒绝解释。**
- 生产侧推论(保守义):"V3 重新计算 hash" 成立的前提是 **source bytes 对 V3 可达**——`source_version_id = SHA256(original source bytes)` 意味着 V3 拿到源字节即可当场重算对账。现状 manifest `source_file` 为本机绝对路径(A-5),交付形态(v0.2 面)未裁,列入 GAP G-4。

### B.3 Part 3 — Scope 冻结 + 三禁(数字对齐禁令)

- `Interface Scope = 87`(87 份文件具备接口身份);`IR Consumption Scope = 71 ADMITTED`(71 份具备可消费语义结构);**二者允许不同**。
- **新三禁(本轮生效,叠加既有)**:禁止为让数字一致而 ①强制生成 IR / ②删除 identity 文件 / ③修改历史数据。生产侧记为硬约束:任何"补齐 87 − 71 = 16 份"的冲动动作均违反 Owner 裁决。

### B.4 Part 4 — 16 份 Identity-only 文件 = 正常态(关闭 D-2)

- 定义固化:**Identity Available / Semantic Unavailable** 属正常状态,不是缺陷;
- 三禁:不得自动补 IR / 不得 LLM 猜测生成 / 不得静默进入题库;
- 是否重新生成 IR:**另行批准**(与 DEC-020 "G1×G3 解耦"一致:身份面完备不依赖这 16 份有 IR)。
- 生效后果:Dependency Map 决策点 **D-2(16 份无 IR 成员消费语义)关闭**。

### B.5 Part 5 — Semantic Unknown 处理原则(与 DEC-021 D3 的分层关系)

- 对 `unit_type unknown` / `semantic unclear` / `annotation uncertain`:禁自动转换 / 禁静默 fallback / 禁静默 skip(与既有 B3 一致);
- **必须保留事实状态,进入 `UNKNOWN` 语义状态**;
- **不合并 `semantic_status` 与 `decision_status` 两个状态体系**——本轮只确认 UNKNOWN 属语义层。
- 生产侧保守解释(如实标注为 DSH 解释,非裁决):DEC-021 D3 四状态机(READY/INCOMPLETE/PENDING_REVIEW/REJECTED)= **决策层**词表;`UNKNOWN` = **语义层**事实呈现;两层并存不互斥——unknown semantic 在语义层呈现为 UNKNOWN(事实保留),在决策层按 D3 强制规则路由到 PENDING_REVIEW 或 REJECTED。**两层载体(字段名/落点)均未裁**,v0.2 落字前 producer 不预设。

### B.6 Part 6 — Contract v0.2 只冻结三件 + 暂缓清单

**冻结内容(v0.2 Frozen Candidate 范围)**:

1. **Identity**:`source_version_id = SHA256(original source bytes)`(**字段名 + 算法本轮已裁**,格式细节见 GAP G-1);
2. **Scope**:Manifest 87 / IR 71 snapshot;
3. **Semantic Boundary**:`Unknown ≠ Ready`;Unknown 不得自动进入正式题库。

**暂缓冻结(明确不属于 v0.2 interface contract)**:数据库字段最终设计 / UI 展示 / 自动补全机制 / IR 扩产计划 / 图片恢复流程 / daemon 持续生产策略。

### B.7 Part 7–9 — 双侧分工(本轮变化如实入账)

- **Contract v0.2 Draft 本轮由 Claude 更新为 Frozen Candidate(状态 DRAFT NOT FROZEN)**——与前一轮"DSH 备料等起草令"的预期不同,以本轮 Owner 指令为准:DSH 侧 Contract 正文**继续零改动**,以本文件 + Interface Facts v2.1 作为生产侧输入交 Claude 引用;
- 双方共同输出四件:ODR v1.3(canonical,DSH 维护)/ Consumer Alignment v2(Claude)/ **Producer Alignment v4(本文件)**/ Contract v0.2 Frozen Candidate(Claude 起草,双方引用同一版本)。

### B.8 最终原则三条(Owner 原文,生产侧自我约束)

> 文件身份由生产侧证明,系统侧验证。
> 文件内容由生产侧解释,系统侧裁决。
> 宁可缺少结构化数据,也不能制造未经确认的结构化数据。

第三条与 B.3 三禁、B.4 三禁同构:生产侧**不做任何"看起来更完整"的自动生成**。

---

## C. IMPLEMENTATION GAP(全部 = **not started**;| Decision | Current | Gap | 格式,Owner Part 7.4 同款)

| Decision | Current | Gap |
|---|---|---|
| `source_version_id = SHA256(original source bytes)`(Part 6/Part 1-2) | 算法在库且 71 份 IR 已实证(A-2/A-3);manifest **0/166** 携该字段(A-1) | **G-1**:字段缺失,须新增 + 回填(范围已裁 = 87)。**格式细节**:Owner 裁到"SHA256"层;现有生产实践 = 64 位裸小写 hex(`ir.source_sha256` 71 份全为此形态)——DSH 建议沿用裸 hex,**PROPOSED,待 v0.2 落字**。写入 = 数据动作,须 Step 1 快照 + Owner 执行令(五步序) |
| Manifest 验证责任:V3 重算 hash 判断接受(Part 2) | 同算法对账 71/71 实证可行(A-3);但 `source_file` = 本机绝对路径(A-5) | **G-4**:source bytes 的交付形态(相对路径化 / 打包方式)未裁——V3 重算 hash 的可达性前提,v0.2 需落字 |
| Interface Scope = 87 如何表达(Part 3;DEC-021 D1 遗留 C.1) | 今天**只有口径没有承载物**(字段口径 87 无目录/清单工件物化) | **G-3**:接口面 87 的表达载体(快照文件 / 目录约定 / 清单)未裁;且与五步序 Step 1 接口快照同题(D-6) |
| IR Consumption Scope = 71 snapshot(Part 3/4) | 71 冻结工件 sha 零漂移(A-3);**无持续产出机制** | **G-5**:IR 重生成/扩产机制未裁(Part 4 明确"另行批准");本轮无动作 |
| Identity Available / Semantic Unavailable = 正常态(Part 4) | 16 份无 IR 成员已在接口面,靠身份自足成立 | **G-6**:该状态是否需要**接口面呈现字段**(如 semantic availability 标记)供 V3 Gate 消费,未裁;现状 V3 只能靠"IR 面有无该 source_version_id"自行判断 |
| Unknown ≠ Ready;UNKNOWN 属语义层(Part 5/6) | 存量 1 例非 READY(A-6);链零守卫 | **G-2**:语义层载体 + 决策层载体(四状态机字段名/落点)+ PENDING_REVIEW→REJECTED 路由规则文本,三者均未裁;守卫引入时机 = v0.2 冻结后 |
| 五步执行序(DEC-021 D4,本轮 Part 6 暂缓清单与之相容) | Step 1 快照载体形态未裁 | **G-7(D-6)**:Step 1 接口快照与 R50 冻结基线(87/87 manifest 为成员,回填必致 DRIFT)的配对/血统形态待执行令 |

**实现面状态:以上 G-1~G-7 全部 `not started`。** 生产侧在 Owner 执行令 + v0.2 冻结前保持零数据动作。

---

## D. UNKNOWN(如实登记,禁推测)

1. **载体类(三件)**:`source_version_id` 格式细节(裸 hex 已建议未裁)/ 语义层与决策层状态载体 / 接口面 87 表达载体——均为 v0.2 落字面,producer 不预设;
2. **路由规则**:PENDING_REVIEW → REJECTED 的"明确规则"文本仍未给(DEC-021 D3 遗留);
3. **D-3 存量 1 例原子性**(修复是否允许脱离 R50 配对)、**D-4 2 份三重成员**(接口面+IR+R50,Step 5 排除件)处置:未裁;
4. **PDF 面角色**:OCR 清单(`ocr_output_manifest.jsonl`,1,801 条,钉 PDF raw bytes)是否纳入 v0.2 双层接口——Part 6 未提,维持 Facts v2 §4.3 立场(B1 未裁决其角色,事实备查);
5. **legacy 79 披露形态**(v0.2 是否需要披露句):未裁(隔离已裁,文字层形态未裁);
6. **消费侧**:V3 当前能否表达 semantic_status/decision_status 双层、四状态机、Gate 对 UNKNOWN 的行为——归 Claude Consumer Alignment v2,DSH 不陈述。

---

## E. 需 Owner 批准的动作清单(禁止自行执行,Part 8.3)

| # | 动作 | 性质 | 依赖 |
|---|---|---|---|
| 1 | manifest 增加 `source_version_id` + 87 份回填 | 数据写入 + schema 变更 | Step 1 快照执行令(D-6)+ v0.2 冻结(五步序 Step 2/3) |
| 2 | `source_file` 形态调整(相对路径化) | schema/数据变更 | v0.2 落字 + Owner 令 |
| 3 | 接口面 87 快照/清单生成 | 新工件生成 | Step 1 执行令(载体形态未裁) |
| 4 | 语义/决策状态机字段引入(含 B3 守卫) | schema + 代码 | v0.2 冻结(载体 + 路由规则落字) |
| 5 | 数据清洗(unit_type 单点修复等) | 数据写入(破坏 R50 基线成员) | 五步序 Step 4 令 |
| 6 | 图片恢复批跑 | 数据写入 | 五步序 Step 5 令(排除 2 份三重成员) |
| 7 | IR 重新生成 / 扩产 | 新数据生成 | Owner **另行批准**(Part 4 原文) |
| 8 | legacy 79 任何处置 | 数据/迁移 | 独立 Legacy Migration Plan(DEC-021 D2) |
| 9 | Contract v0.2 冻结 | 契约状态变更 | Owner 冻结令(本轮 Claude 起草,DRAFT NOT FROZEN) |

---

## F. 纪律自查

1. 零代码 / 零数据 / 零清洗 / 零迁移 / 零 schema / 零 Contract 正文改动:本轮写入面 = 本文档 + ODR v1.3 + Interface Facts v2.1 + 台账三件(state.yaml / CURRENT.md / log.md);✅
2. DECISION 段全部为保守义解释,与 ODR §1quater 原文逐条对应,无引申裁决;✅
3. 实现状态全部 `not started`,未提前宣称任何完成;✅
4. OBSERVED 全部复用既有工件(零新数据探针);✅
5. Claude 侧行为与消费能力零陈述(V3 侧事实归 Consumer Alignment v2)。✅

*v4 · 2026-09-16 · DSH(Source Evidence Producer)。裁决基准 = ODR v1.3;如有文字冲突,以 Owner 原文为准。*

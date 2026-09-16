# PREPROCESSING PRODUCER INTERFACE FACTS v2

> Status: **v2.2(2026-09-16,Interface Finalization Revision v1 固化增量:DEC-SOURCE-IDENTITY 格式已裁 / path 非身份注记 / 16 份 Semantic Pending;实测事实面零改动)** · Authority: Owner B1-B3 + Interface Decision Finalization + Interface Finalization Revision(2026-09-16,DSH 自记于 `state.yaml.integration_contract.owner_decision_b1b3` / `.owner_interface_finalization` / `.owner_interface_revision`)
> Role: preprocessing Producer Owner —— 回答"producer 能提供什么 / 不能提供什么 / 缺口在哪里",并作为 Contract v0.2 的生产侧输入。
> Discipline: 只写实测事实(路径 + commit 可复现);不假设 V3 消费方式;不提出 V3 实现方案;不修改 Contract 正文 / 数据文件 / 两仓代码。无证据一律标 UNKNOWN。
> Evidence artifacts: `data/producer_interface_census.json`(v1 全语料普查,commit `17c55d8`)+ `data/producer_interface_probe_v2.json`(v2 定向探针,本轮 commit)。
> Probe scripts(确定性只读,可复跑): `.pytest_work/pif2_probe*.py` / `pif2_final.py`(工件由 `pif2_final.py` 单脚本重建)。

---

## 0. Owner 裁决原文要点(锚定,不复述扩展)

| 项 | 裁决 |
|---|---|
| **B1 Transport** | 正式生产接口 = **Manifest + IR 双层**。Manifest = **Source Identity Authority**;IR = **Semantic Consumption Authority**;两者必须通过明确 **source_version_id** 关联 |
| **B2 Identity** | source identity = **SHA-256(raw bytes)**(原始字节 SHA-256);body_hash / line_hash / integrity_hash / norm_sha256 **只能作为内部校验**,不能作为跨系统 source identity |
| **B3 Semantic Boundary** | unknown unit_type **不得自动修正、不得静默转换**,必须进入 **UNKNOWN/PENDING** |

---

## 0bis. Owner 裁决固化表(Interface Decision Finalization v1,DEC-022;职责 + Scope;不扩展原文,原文 = ODR §1quater)

### 0bis.1 职责固化(双层,正式采用)

| 面 | 回答的问题 | Producer(DSH) | Consumer(V3) |
|---|---|---|---|
| **Manifest = Source Identity Authority** | "这个东西是谁?"(source identity / version / raw bytes hash / 版本关系) | 生成 Manifest / 计算 `source_version_id` / 保证字段正确 | 验证 Manifest / **重新计算 hash** / 判断是否接受 |
| **IR = Semantic Consumption Authority** | "文件里面有什么?"(structure / semantic annotation / knowledge / unit) | OCR 后结构化 / LLM 语义解析 / 生成 IR | 验证 IR 符合契约 / Gate 判断 / 拒绝不符合数据 |

总原则:**Preprocessing 负责解释,V3 负责接受或拒绝解释。** 双禁:Manifest 不替代 IR 描述题目;IR 不替代 Manifest 证明身份。

### 0bis.2 Scope 固化(三数字永久分开,引用不得互换)

| 面 | 冻结值 | 含义 | 关键比例(本文件实测口径) |
|---|---|---|---|
| 全语料历史资产 | 166 | manifest 全部历史资产规模,**≠ 正式接口** | 分母 |
| **Interface Scope** | **87** | 具备接口身份的文件(字段口径 `identity_version=="2"`;§2.4) | 87/166 = 52.4% |
| **IR Consumption Scope** | **71 ADMITTED** | 当前具备可消费语义结构(冻结 snapshot,§3) | 71/87 = 81.6%(接口面内) |
| Semantic Pending | **16**(87−71) | **Identity Available / Semantic Pending**——等待 semantic processing,**不是永久缺失**(DEC-023 Part 3);IR 再生成允许但四约束(bytes 不变/id 一致/新 IR 绑定 id/重过双验证)+ 四禁 | —— |
| v1 legacy | 79 | historical asset,不入 v0.2 接口(DEC-021 D2) | —— |

**数字对齐三禁(Part 3,叠加既有)**:禁强制生成 IR / 禁删除 identity 文件 / 禁改历史数据凑一致。**新增禁令(DEC-023 Part 4)**:"IR available" 不得等同于 "Interface available";Interface Scope = 87 不得修改为 71。

### 0bis.3 Identity 定义固化(DEC-023 Part 1 DEC-SOURCE-IDENTITY 终局)

`source_version_id = SHA256(original source bytes)`,**格式 = 64 字符小写 hex 字符串**——与现有 `ir.source_sha256` 71 份实证形态完全一致(§4.1),零格式迁移。**Identity 由 `source_version_id` 唯一决定。Source identity belongs to content hash, not storage location(文件身份属于内容哈希,不属于存储位置)。**

### 0bis.4 path 非身份原则(DEC-023 Part 1-2)

`source_file` **保留** = **locator information(辅助定位),不是 identity information**。正确表述:"source_file 用于辅助定位 source,source_version_id 用于跨系统唯一识别 source"。**本文件 §2.1/§3.4 中 `source_file` 绝对路径相关事实全部按此定性引用**——路径形态是 locator 缺口(跨机解析),**不是身份缺口**;路径变化(Windows/NAS/Linux/Object/Cloud)不得导致 `source_version_id` 变化;任何文档不得暗示 path/absolute path/directory 参与文件唯一判断 / source identity 判断 / version 判断 / hash identity 判断。

---

## 1. 合取摘要(一页版)

| 问题 | 答案(状态) |
|---|---|
| Manifest 能当 Source Identity Authority 吗? | **今天不能**。166/166 manifest 不携带任何 sha/hash 键、不携带 `source_version_id`(`p1b`:0/166、0/166)。缺的是字段,**不是能力**(见 §2.2) |
| IR 能当 Semantic Consumption Authority 吗? | **部分能**。sha 自洽 71/71(与 provenance 一致 + 与当前 md 原始字节一致,零漂移);但覆盖 = **88 份记录 / 71 份有 IR**(v2 目录面 88 的子集),语料面 166 的 43%,且为 R52 一次性冻结工件,**无持续产出机制** |
| source_version_id 存在吗? | **不存在**(0/166)。当前双层间唯一关联值 = `source_file` 绝对路径字符串(§2.1.4)——不是 id |
| 唯一 source identity 是什么? | **raw bytes SHA-256**,已实证单点生产且语义一致:`scripts/resolver_reference.py:52-53`(md)、`scripts/r67_manifest_bootstrap.py:181`(PDF,经 `file_sha256`) |
| unknown unit_type 现状? | 全语料恰 **1 例**(`andalone_question`,manifest 面与 IR 面各 1,同一文件 Q1);producer 链**零守卫**——该值原样进入 IR ADMITTED 工件(B3 约束今天未被任何机制保证,见 §4) |

---

## 2. Manifest 层(Source Identity Authority 裁决角色)

### 2.1 当前字段(实测,166/166 穷举,`producer_interface_census.json` + `producer_interface_probe_v2.json.p4_key_faces`)

**文件级键**(每份 manifest):

| 键 | 出现 | 内容形态 |
|---|---|---|
| `source_file` | 166 | **str = 本机绝对路径**(示例:`D:\Project\Papers\Ocr-markdown\会考\历史\2018北京夏季高中会考历史（教师版）(1).md`) |
| `units` | 166 | 数组,合计 4,609 单元 |
| `annotation_meta` | 166 | `{model, prompt_version, validation_issues, warnings}`(+`bug22_migration` 8 份) |
| `model` | 166 | 标量 |
| `sections` | 87 | 仅 identity v2 面 |
| `identity_version` | 87 | 值 `"2"`;79 份缺失(v1 legacy 面) |

**单元级键**(4,609 单元穷举,15 键):`unit_id` / `unit_type` / `question_numbers` / `printed_number` / `section` / `section_ref` / `basis` / `basis_evidence` / `printed_provenance` / `stem_lines` / `options_lines` / `answer_lines` / `explanation_lines` / `material_lines` / `questions_lines` / `extra_lines` / `answer_evidence` / `original_question_type`(键面计数见 census `manifest.unit_level_keys`;游离键恰 1 例 = `explanation_lines_note`)。

### 2.2 是否满足 Source Identity Authority —— **不满足(GAP)**

硬事实(`p1b_manifest_identity_gap`):

- 携带任何 `*sha*` / `*hash*` 键的 manifest:**0 / 166**;
- 携带 `source_version_id` 的 manifest:**0 / 166**;
- 结论:**Manifest 层今天零 source identity 字段**。裁决要求的"Source Identity Authority"角色,当前 schema 无承载点。

### 2.3 需要增加的字段(生产侧需求,提交 Contract v0.2,不自行实施)

| 需增字段 | 生产侧依据 | producer 能力 |
|---|---|---|
| `source_version_id` | Owner B1 裁决明文;当前 0/166 | **可提供**:定义 = `sha256(md 原始字节)`(`resolver_reference.py:52-53` 算法在库,IR 面 71/71 已实证与实际字节一致);为 166 份 manifest 逐份计算属数据写入动作,**须 Contract 冻结后按令执行** |
| 建议同批处理 `source_file` 形态 | 绝对路径本机绑定(实测值见 §2.1),跨机不可解析 | 形态改 relative 属 schema/数据变更,归 v0.2 裁决,producer 侧零动作 |

### 2.4 identity 面双口径(本轮新固化,影响"哪些 manifest 入接口面")

| 口径 | v2 面 | v1 面 | 判定依据 |
|---|---|---|---|
| **字段口径**(`identity_version == "2"`) | **87** | 79 | IR 生成器与 C-IN-1 实际判定口径(`resolver_reference.py` 拒收 REJECTED_V1 即此规则) |
| **目录口径**(reslice-batch-C / reslice-pac-annotated / resliced-pilot) | 88 | 78 | 目录位置 |

差 1 实例(`p1_identity_face.v2_dir_legacy_hybrids`,恰 1 份):`resliced-pilot\高一\化学\2021北京三十一中高一（下）期中化学（教师版）(1).manifest.json` —— 位于 v2 目录但 `identity_version=null`、文件级键仅 4 个(无 `sections`)。该份在 IR 中 disposition = **REJECTED_V1(reasons: `identity_version < 2 (C-IN-1)`)**(§3.2)。

**接口面口径结论(生产侧事实)**:若 Contract v0.2 以 manifest 为 Source Identity Authority,"可接口面"应锚定**字段口径 87**,不是目录口径 88,更不是 166。

---

## 3. IR 层(Semantic Consumption Authority 裁决角色)

工件:`data/resolver_ref_r52/resolver_ir.json`(顶层 `{ir_version: "resolver-ir-0.1", files: [88]}`;commit 面 = R52 冻结)。

### 3.1 覆盖范围(实测)

| 维度 | 数值 |
|---|---|
| 记录数 | **88**(v2 目录面 88 份 manifest 一一对应:`p2_ir_coverage.manifest_file_resolves = 88`,全部 v2 目录) |
| 携 `ir` 对象(ADMITTED) | **71** |
| 拒收 | **17** = 16 × REJECTED_QC_FAIL + 1 × REJECTED_V1(逐条 reasons 在 `p7_rejected_records`) |
| 单元 | **1,664**(全部在 71 份 ADMITTED 内) |
| 对 manifest 全语料 166 的覆盖 | **71/166 = 43.4%**(以"可语义消费"计);88/166 = 53.0%(以"有记录"计) |
| 对字段口径 v2 面 87 的覆盖 | 71/87 ADMITTED;88 记录含 1 份 REJECTED_V1 实为 v1 面混入(§2.4) |

### 3.2 稳定性(实测)

- **sha 自洽 71/71**(`p3_ir_sha_self_consistency`):`ir.source_sha256` == 各单元 `provenance.source_version`(71/71)== **当前磁盘 md 原始字节 sha256**(71/71,mismatch 列表为空)。即自 R52 冻结以来**零漂移**,本轮(裁决当日)复验仍然成立。
- **产出机制**:R52 一次性工件;生成器 `scripts/resolver_reference.py` 在库(行 249 = `source_sha256` 生产点,行 167 = 单元级 `source_version` 生产点,行 152 = `unit_type` 逐字复制点)。**自 R52 起未再生成,无持续产出机制**(v1 FACT-032 结论,本轮无新事实推翻)。

### 3.3 provenance 能力(实测)

- 单元级 `provenance` 七键(1,664/1,664 全量):`source_file` / `source_version` / `source_lines` / `manifest_file` / `qc_verdict` / `extraction_method` / `confidence_state`;
- `source_version` 语义 = 源 md 原始字节 sha256(生成点 `resolver_reference.py:167`,值与 `ir.source_sha256` 一致 71/71);
- `source_lines` = 行区间数组(span 级溯源);
- **能力边界**:provenance 只覆盖 ADMITTED 71 份的 1,664 单元;17 份拒收记录**无 provenance**(ir=null,仅顶层 reasons)。

### 3.4 IR 作为 Semantic Consumption Authority 的边界(明确)

1. IR 的身份字段(`source_sha256` / `source_version`)今天**已经满足 B2 算法定义**(raw bytes SHA-256,实证 71/71);
2. IR 的覆盖面是**样本级(71/166)**,不是全语料——IR 层若承担 Semantic Consumption Authority,消费面即 71 份(1,664 单元),其余 95 份 manifest 的语义单元**无 IR 承载**;
3. IR 与 Manifest 的关联键今天 = `ir.manifest_file`(绝对路径字符串)+ `ir.source_file`(与 manifest `source_file` 值相等)——**路径关联,非 source_version_id 关联**;
4. IR 是冻结工件:"权威性"来自冻结 + sha 自洽,不来自持续生成;重产 IR 属新增数据生成动作,须 Owner 显式令(权限边界,沿 Interface Facts v1 §3)。

---

## 4. Identity 层(B2 裁决确认)

### 4.1 producer 唯一 source identity(OBSERVED)

**SHA-256(raw bytes)**。单一算法、双语料类型、生产点唯一:

| 语料 | 生产点(路径:行) | 字段名 | 出现处 |
|---|---|---|---|
| 源 md | `scripts/resolver_reference.py:52-53`(`_sha256 = hashlib.sha256(p.read_bytes())`) | `source_sha256`(文件级,`:249`)/ `source_version`(单元级 provenance,`:167`) | IR 工件 71/71 |
| 源 PDF | `scripts/r67_manifest_bootstrap.py:181`(`file_sha256(source_pdf)`) | `source_sha256` | OCR 清单 `data/ocr_output_manifest.jsonl` 1,801/1,801 条 |

与 Owner B2 裁决**完全一致**:producer 输出面的 source identity 就是 raw bytes SHA-256,无第二算法、无歧义。

### 4.2 其他 hash 字段的实际用途(逐一定性,均= 内部校验)

| hash | 算法定义位置 | 实际用途(实测) | 跨系统身份资格 |
|---|---|---|---|
| `norm_sha256` | `scripts/r64_data_inventory.py:61`(NORM_ALGO = NFC + 换行归一 + rstrip + strip) | 审计内部内容身份(`r64:258`;`r65:151`;`r66:39` IDENTITY_FIELDS) | **无**(从未发布为接口字段) |
| `corpus_sha256` | `scripts/audit_integrity.py:134`(语料集摘要) | 语料集完整性审计(`r50:97` digest_match) | **无**(集合级摘要,非单源身份) |
| manifest 清单指纹 `base_manifest_sha256` / `entries_sha256` | `scripts/r67_manifest_bootstrap.py:316-321, 309-313` | r67 dry-run/apply 防重放内部护栏 | **无** |
| `body_hash` / `line_hash` / `integrity_hash` | —— | **producer 零产出**(v1 FACT-032;本轮全语料探针 0 命中复验) | **无**(不存在于 producer 输出面) |

### 4.3 OCR 清单(第三输出面,B1 未裁决其角色,事实备查)

`data/ocr_output_manifest.jsonl`:1,801 条 append-only;键面 = `source_rel` / `output_rel` / `source_sha256`(PDF raw bytes)1,801/1,801 + `source_size` / `pages` / `written_at`(1,801)+ `audit_line` / `log_ok_lines` / `processed_at` / `provenance`(698)。**它钉 PDF,不钉 md**;是否纳入双层接口由 Contract v0.2 定,producer 侧无既有承诺。

---

## 5. B3 现状:unknown unit_type 处理链(裁决 vs 现状)

| 层 | 事实 |
|---|---|
| 裁决要求 | unknown unit_type 不得自动修正、不得静默转换,进 UNKNOWN/PENDING |
| 现状值域 | manifest 面恰 1 例非标准值(`andalone_question`,batch-C 合格考化学 Q1;`p6_nonstandard_unit_type`);IR 面同一文件同一单元原样携带同值(生成器 `resolver_reference.py:152` 逐字复制,零转换) |
| producer 链守卫 | **零守卫**(v1 Interface Facts §3 已固化):生成链无任何 unit_type 值域检查;该单元 disposition = ADMITTED |
| 与"不得静默转换"的关系 | 现状**没有**静默转换(值原样保留),但也**没有**进 UNKNOWN/PENDING —— 裁决的隔离语义今天无执行面 |
| 执行动作性质 | 单点修复属数据写入 + 破坏 R50 冻结基线成员(sha `58058c4f…`,closure plan v1 §B),**本轮暂缓**(Owner 令:接口冻结优先) |

---

## 6. 能提供 / 不能提供 / 缺口(总裁决表)

### 6.1 能提供(今天即具备,只读可复现)

| # | 能力 | 证据 |
|---|---|---|
| C1 | raw bytes SHA-256 单一算法身份(md + PDF 双语料) | §4.1;IR 71/71 + OCR 1,801/1,801 |
| C2 | IR 71 份 / 1,664 单元的稳定语义消费面(sha 零漂移) | §3.2 |
| C3 | 单元级 provenance 七字段(行区间溯源) | §3.3 |
| C4 | manifest 166 / 4,609 单元的标注面(键面确定性) | §2.1 |
| C5 | 为任意 md/PDF 即时计算 raw bytes sha 的代码能力(在库) | `resolver_reference.py:52-53` / `r67_manifest_bootstrap.py:181` |

### 6.2 不能提供(结构性,非意愿问题)

| # | 不能 | 原因 |
|---|---|---|
| N1 | 今天交付携带 `source_version_id` 的 manifest | 字段不存在(0/166);写入 = 数据变更,须 Contract 冻结 + Owner 令 |
| N2 | 全语料 166 的 IR | 现存 IR = 88 记录 / 71 ADMITTED;95 份(166−71)无语义承载,重产 = 新数据生成动作 |
| N3 | 持续产出的 IR | R52 一次性冻结工件,无 daemon/流水线(FACT-032) |
| N4 | body_hash / line_hash / integrity_hash | producer 从未产出(B2 裁决下也**不应**产出为身份) |
| N5 | B3 隔离(UNKNOWN/PENDING)的现行保证 | 链上零守卫(§5) |

### 6.3 缺口清单(v0.2 需求输入,按裁决映射)

| 缺口 | 对应裁决 | 生产侧动作性质 | 依赖 |
|---|---|---|---|
| G1:manifest 无 `source_version_id` | B1 | 字段新增 + 166 份回填(数据写入) | **Contract v0.2 冻结 + Owner 令** |
| G2:双层关联仅靠绝对路径 | B1 | 同 G1(或 v0.2 另定关联键) | 同上 |
| G3:IR 覆盖 71/166 | B1(IR = Semantic Consumption Authority 的覆盖面) | 扩产 = 新数据生成 | Owner 令(范围/批次) |
| G4:IR 无持续产出 | B1(接口稳定性) | 机制建设 | Owner 令(是否要) |
| G5:unit_type 无守卫、隔离无执行面 | B3 | 守卫引入 + 1 例处置 | Contract v0.2 冻结(B3 语义落字)后 |
| G6:v1 面 79 份处置未定 | B1(接口面口径) | 排除 / 迁移 / 披露,三选一 | Owner 裁决(独立事实问题,Interface Facts v1 §3 遗留) |

---

## 7. 本轮不承诺 / 不执行(Owner 令:接口冻结优先)

- **不执行**:unit_type 修复 / 图片恢复(recover_images)/ flags registry / D5-C·D5-D —— 执行计划见 `PREPROCESSING-B1B3-READINESS.md` §5(逐项标注 Contract 冻结依赖);
- **不修改**:V3 代码 / Contract 正文 / 任何数据文件(本轮写入面 = 文档 + 台账 + 探针工件);
- **不假设** V3 消费方式;**不提出** V3 代码方案。

## 8. 五纪律自查

1. 只写实测事实:全部数字有工件路径(census v1 / probe v2)与代码行锚;✅
2. 不假设 V3 消费:全文无 V3 行为陈述(V3 hash 亲验结论已移入 v1 Reconciliation,本轮零新增);✅
3. 不提 V3 方案:§6.3 全部为 producer 侧动作;✅
4. 不执行清洗:语料零写入(探针只读,工件写 `data/producer_interface_probe_v2.json` 属证据登记非语料);✅
5. Contract 零改动:`PREPROCESSING-INTEGRATION-CONTRACT.md` 保持 v0.1 DRAFT 一字未动。✅

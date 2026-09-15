# Preprocessing Integration Contract v0.1(DRAFT)

> **状态**:DRAFT,待 Owner 裁决 + Claude(V3)确认后升 FROZEN。
> **定位**:AITutors-preprocessing(producer)→ AITutors-v3(consumer)的**跨项目输出契约**。preprocessing = V3 的 Data Admission Layer(`resolver_contract_design.md` G-BOUND-1),本契约定义"稳定输出契约供 V3 消费"的机器可检条款。
> **本契约不做什么**:不定义 V3 内部设计(Resolver/IR/Authority/Admission 实现归 V3);不重新裁决已冻结的仓内契约(C-IN/C-OUT/C-FAIL、Identity v2、G-RES-1);不新增任何 preprocessing 规则——只**如实描述当前产物的真实形态**并标注验证状态。
> **证据纪律**:每条款标注 OBSERVED(有实测锚)/ INFERRED(推断)/ UNPROVEN(未证)。语料基线 = `R50_input_baseline@sha256:795ee1e7663424c1245e651d2139573d3bd2322f06662cc677bc0e7e3bc89beb`(88 份,356 文件);IR 样本 = `data/resolver_ref_r52/resolver_ir.json`(resolver-ir-0.1,71 ADMITTED / 16 REJECTED_QC_FAIL / 1 REJECTED_V1)。

---

## §1 Source Version

### 1.1 Identity(OBSERVED)

- **source_version 的唯一身份 = 源 OCR markdown 文件字节的 SHA-256(hex,小写,64 字符)**。
- IR 文件级字段 `source_sha256`、单元级 `provenance.source_version` 均承载该值(同一文件内逐单元一致,F1 审计 2403/2403 核验过一致性)。
- **V3 侧对应物**:`source_versions` 行的 identity 应当就是这个 sha。V3 可附加 path/corpus/subject 等 metadata,但**跨系统对账只认 sha**。

### 1.2 Immutable 内容(OBSERVED)

- sha 一经发布,对应文件字节**冻结**:任何内容变更(重 OCR、修复、re-slice)必须产生**新 sha = 新 source_version**,禁止原地改写已发布文件。
- 保障机制(producer 侧已实装):Input Integrity Gate(`scripts/audit_integrity.py`,执行前后原件集 sha256 对账,漂移即 fail-closed)+ Audit Snapshot Manifest(356 文件冻结基线)。
- **V3 义务**:消费前可独立重算 sha 与声明值比对;不一致 → 阻断(§3.3)。

### 1.3 Version 关系(如实声明:当前不存在)

- **preprocessing 当前不产出任何 version→version 关系指针**(supersede/successor/latest)。同一文档的两个版本 = 两个**互不相关**的独立 source_version 实体,仅有文档身份(filename/语料元数据)可作人工关联。
- 这是已入册的事实边界(EB-008 R-4:source_version supersede 生产流程未建)。**跨版本 lineage 属开放项**(§6 OQ-1),在建立之前,V3 不得假设存在任何"旧版本权威可迁移到新版本"的机制——迁移必须显式重新走 evidence 链。

---

## §2 Semantic Annotation

载体 = 两层产物:**manifest v2**(annotation 原始事实层,`identity_version: 2`)+ **IR(resolver-ir-0.1)**(结构解析 + provenance 层)。V3 消费以 IR 为准,manifest 为回源凭据。

### 2.1 Annotation 结构(OBSERVED,逐字段实测)

**文件级**:`{ir_version, source_file, source_sha256, manifest_file, qc_verdict, materials, units}`。

**单元级**(IR `units[]`):

| 字段 | 形态 | 实测值域/备注 |
|---|---|---|
| `unit_id` | string | **display alias,禁止作任何跨系统键**(汇编卷内可重复,专题十六实测 78 单元重复) |
| `unit_type` | string | `standalone_question`(1385)/ `composite_question`(278);**另实测 1 例 `"andalone_question"` 拼写噪声**(§6 OQ-2) |
| `question_numbers` | int[] | canonical 编号(manifest scope);canonical 身份成分 |
| `printed_number` | int[] \| null | Source Fact;unknown → null,**禁止猜测回填**(402 单元 27.1% 为 null) |
| `printed_provenance` | string | `source_line` / `migration_report` / `unknown` |
| `basis` | string | 闭集 6 值:`answer_key\|shift\|keep\|printed_as_is\|explicit\|unverified` |
| `basis_evidence` | string | keep 豁免必须可回源(`L{行号}`,界内 + 承载编号语义) |
| `section_ref` / `section_title` | string | `section_ref` 指向 SectionLocator(`sections[{id,title,ordinal,start_line,end_line,occurrence,derived?}]`);title 仅 display |
| `content` | {stem_lines, options_lines, answer_lines, explanation_lines} | 文本行数组,行号锚定见 §2.2 |
| `material_ref` | string \| null | 见 §2.3 |
| `answers` | 表对象 \| null | `{cells, method, answers{}, unresolved[]}`;`method` 实测 `td_positional` |
| `answer_text` | string[] | 答案区原文行 |
| `flags` | string[] | 实测:`answer_table_unresolved`(502 单元)/ `answer_number_mismatch`(91) |
| `provenance` | 对象 | 见 §2.2,一等公民,不埋 metadata |

### 2.2 Claim/Span 绑定(OBSERVED)

- **每个内容区都锚定源行号**:`provenance.source_lines.{stem|options|answer|explanation|material|questions}_lines = [start, end]`,1-based、闭区间(实测单行区 = `[9,9]` 承载第 9 行文本),`extraction_method = line_span_v1`,`confidence_state = structural_only`。
- **跨系统 claim 身份 = `(source_version_sha, section_ref, question_numbers)`**;`unit_id` 仅展示。任一成分缺失或 sha 不可对账 → 该 claim 不得获得 authority(§4)。
- 结构一致性可独立复证:F1 Audit Invariant 四项对账(`source_version_sha / start_line / end_line / span hash`),88 份 2403/2403 单元 MATCH(producer 侧已实装,`scripts/audit_f1_consistency.py`)。**V3 可在自己侧重实现同一对账**,无需信任 preprocessing 的自检结论。

### 2.3 Material 引用(OBSERVED)

- composite 单元经 `material_ref`(如 `"L536-567"`)引用文件级 `materials` 映射:`{"L536-567": {lines: [536,567], text: [...]}}`。
- 共享材料**不复制**(多单元同 ref 指向同一对象),单题材料不丢失——R-ACC-13 消费审计实测 consumers 集合精确(278 composite 单元)。
- **V3 义务**:按 ref 消费,不得重塑/合并/重切材料内容;ref 悬空 → 阻断。

### 2.4 Figure 引用(OBSERVED)

- 图片 = 内容行内的**内联 HTML** `<img src="../../_imgs/...">`(相对路径,相对源 md 所在目录解析);**没有独立 figure 注册表/对象**。
- BUG-18 治理后语料中孤立 img 已显式处置(keep 148 条,`data/bug18_orphan_img_fix_log.json`)。
- **V3 义务**:figure 引用只能按行锚 + 相对路径原样搬运;preprocessing 不重托管图片、不提供图片 sha(§6 OQ-3)。

---

## §3 V3 消费要求

### 3.1 必须提供(producer 保证每单元齐全,V3 拒绝缺失)

`source_sha256`(文件级+单元级 provenance)、`qc_verdict`、`disposition`、`section_ref`、`question_numbers`、`basis`、`printed_provenance`、`provenance` 全块(source_file / source_version / source_lines / manifest_file / qc_verdict / extraction_method / confidence_state,七字段完备,R-ACC-11 实测)、`content` 各区行文本、`material_ref` 键(可为 null 但字段必须在)。

### 3.2 允许为空(null/empty 是合法终态,V3 不得"补全")

| 字段 | 空值语义 | 实测规模 |
|---|---|---|
| `printed_number` | 卷面印刷号不可证(unknown) | 402 单元(27.1%) |
| `answers`(表对象)/ `answer_text` | 源卷面就没有答案 | c09-01 6 题等,忠实反映 |
| `answers.answers` 映射中的槽位 | `unresolved[]` 显式列出 | **596 槽位 / 502 单元** |
| `explanation_lines` / `options_lines` / `extra_lines` | 源面无该区 | — |
| `material_ref` | standalone 单元天然 null | 1385 单元 |
| `section_title`(title) | OCR 丢标题,fallback 链合成(derived=true)+ 显式 warning | 禁止静默降级 |

**特别条款(消费禁令,R-ACC-14 已量化攻击面)**:V3 对 unresolved 答案槽位**禁止** `answers.get(q, "")` 类静默默认——596 个槽位会被洗成"已解为空"。unresolved 必须走显式通道。

### 3.3 必须阻断(fail-closed,不得降级消化)

1. `identity_version ≠ 2` 的输入(含 v1 存量)→ 拒收(C-IN-1;实测 REJECTED_V1 1 例);
2. `qc_verdict ∈ {FAIL}` 或 `disposition` 为任何 `REJECTED_*` 态 → 不进自动消费路径;人工放行必须走显式 Admission 记录(C-FAIL-2);
3. **sha 不一致**:V3 重算源文件 sha ≠ 声明 `source_sha256` → source binding 已断,阻断;
4. **span 越界**:`source_lines` 超出源文件行数 → STALE,阻断(C-FAIL-3);
5. `material_ref` 悬空;
6. `unit_type` 超出 `{standalone_question, composite_question}` → 隔离(PENDING 通道;实测已有 1 例拼写噪声,不得静默当 standalone 吃);
7. `basis` 超出 6 值闭集 → **schema violation surfaced as PENDING_REVIEW**(R50 裁定:检测已批准、不得转自动 FAIL、不得静默 PASS;producer 侧实现排期③ 未实施 → **V3 现阶段须自行做值域检测**);
8. 任何将 `MISSING / STALE / PENDING_REVIEW / unresolved` 静默转 PASS 的路径(C-FAIL-1)。

---

## §4 EB-008 跨边界约束(annotation→evidence / source binding / authority 追溯)

DSH 在 EB-008 中的角色 = **验证 preprocessing 输出满足 V3 可信输入要求**,不是 V3 攻击测试团队。本节是该角色下的契约面:

1. **annotation 如何成为 evidence**:V3 侧 candidate/claim 必须绑定 `(source_sha256, section_ref, question_numbers)` 或等价 payload 全量 + sha;**裸 `unit_id`(如 "Q1")跨文档必然撞号**(每份卷都有 Q1,汇编卷内亦可重复),不得单独作为 claim 身份——这是 preprocessing 侧能提供的最重要身份事实。
2. **source binding 如何保持**:唯一连接点 = sha256。V3 `validation_events.source_version_id` ↔ preprocessing `source_sha256` 一一对应;sha 可被任一方独立重算,不需要相互信任。
3. **authority 如何追溯**:每单元 provenance 七字段 + F1 四项对账使 authority 的证据基础可离线重建。**任何对不上 sha/行号的既有 authority 必须失效**(新 sha = 新 source_version,authority 不迁移,§1.3)。
4. **producer 侧承诺的边界(如实)**:preprocessing 只证明"结构 + 出处"(G-RES-1),**不证明语义真值**(G-TRUTH-1);语义正确性归 V3 Admission/人工层。V3 不得反过来要求 preprocessing 做语义判定,也不得重复判定已由本层证明的结构事实(G-BOUND-1:重复判断即边界污染)。

---

## §5 与仓内已冻结契约的关系

本契约是 C-IN/C-OUT/C-FAIL(`resolver_contract_design.md`)、Identity v2(`question_identity_design.md`)、G-RES-1/G-BOUND-1/G-TRUTH-1 的**跨项目投影**,不替代、不放宽任何一条;冲突时以仓内冻结契约为准并登记冲突。本契约条款的验证状态与上述文档同源:结构面已多轮对抗实测(标注 OBSERVED),语义面明确不在承诺范围。

## §6 开放项(不隐瞒,待 Owner/Claude 裁决后入册)

| # | 开放项 | 现状 |
|---|---|---|
| OQ-1 | source_version supersede/lineage 指针 | 未建(R-4);V3 需要何种版本关系语义,待 Claude 提出、Owner 裁决 |
| OQ-2 | `unit_type` 值域闭集化 | 实测 1 例噪声;producer 侧修复 vs 消费侧隔离策略待定 |
| OQ-3 | 图片资产交付形态(相对路径引用 vs 独立资产清单+sha) | 当前仅行内相对路径;V3 若需离线解析图片,须提出需求 |
| OQ-4 | basis 值域校验 producer 侧落地(R50 已批准,排期③) | 未实施;期间 V3 自检(§3.3-7) |

---

*v0.1 DRAFT — 2026-09-15,DSH(preprocessing)。待 Owner 裁决冻结;Claude 确认 §3 消费面与 V3 实际 schema 的映射缺口。*

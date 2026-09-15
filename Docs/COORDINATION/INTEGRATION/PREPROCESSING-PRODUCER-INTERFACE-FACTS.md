# PREPROCESSING-PRODUCER-INTERFACE-FACTS v1

> **角色**:preprocessing **Producer Owner**(DSH)。本文件是生产侧接口事实档——**Owner 裁决 B1/B2/B3 的生产侧输入**。
> **上游**:基于 Reconciliation v0.2(`ad1abdd`)固化;基线 `4d78513`(语料自该点起仅 daemon 产出增量,本轮复扫确认)。
> **五条纪律(本文件逐条遵守)**:①只固化 producer 当前**真实输出**的实测事实;②**不假设 V3 消费方式**;③**不提出 V3 实现方案**(本文件无任何"建议/应该");④**不执行清洗**(语料零写入,唯一新工件 = 只读普查 JSON);⑤**不冻结 Contract**(v0.1 DRAFT 一字未动)。
> **本轮工件**:`data/producer_interface_census.json`(全语料只读普查,确定性;探针 `.pytest_work/pif_census.py` 一次性,数字以工件为准)。全部事实 OBSERVED。

---

## §0 结论摘要

| # | 输出面 | 覆盖 | sha 锚 | 冻结态 |
|---|---|---|---|---|
| S1 | 源 OCR md 树 | 4,224 份(DQE 口径;`4d78513` 时点 4,223,+1 = daemon 产出) | R50 快照钉其中 356 文件 | 356 冻结 + 其余运行面 |
| S2 | manifest(annotation 事实层) | **166 份全语料**(identity v2 = **87** / v1 legacy = **79**) | **0/166** | 运行面 + R50 成员冻结 |
| S3 | IR(resolver-ir-0.1) | **88 条记录(R50 基线样本面)**,71 含 IR 对象 / 1,664 单元 | `source_sha256`(源 md),71/71 零漂移 | **冻结工件,自 R52 起未再生成** |
| S4 | OCR 输出清单 | 1,801 条 append-only | `source_sha256`(源 **PDF**) | append-only |
| S5 | R50 审计快照 | 356 文件 | `corpus_sha256` | 冻结 |

**核心合取事实(B1 的生产侧硬约束)**:**没有任何单一输出面同时具备"全语料覆盖 + md sha 锚 + 持续产出"**——S2 全覆盖但零 sha;S3 有 sha + provenance 但只是 88 条一次性样本工件;S4 锚的是 PDF 不是 md。这是实测事实,本文件不由此推导任何消费方案。

---

## §1 输出面清点(Interface Inventory)

### S1 源 OCR markdown 树(原件)

- 载体:`Ocr-markdown/`(排除政策单一来源 = `recover_images` 常量:`_imgs`/`.cache`/`auto-annotated*`/`reslice*`);今日 4,224 份;
- 冻结:R50_input_baseline 356 文件(sha 快照,`audit_integrity verify` 零漂移);其余为运行面(daemon 持续产出,快照即过期,冻结面/运行面分离是既定设计)。

### S2 manifest(annotation 事实层,166 份全语料普查)

**文件级键面(键 → 携带份数/166)**:

| 键 | 份数 | 备注 |
|---|---|---|
| `annotation_meta` / `model` / `source_file` / `units` | 166 | `source_file` 166/166 为 string(BUG-31/32 修复后形态) |
| `identity_version` | **87** | 值全部 = 2;**缺失 79 份**(按 C-IN-1 `(identity_version or 1) < 2` 语义 = v1) |
| `sections` | **87** | SectionLocator,仅 v2 面存在 |
| (任何 sha 键) | **0** | 复证(Reconciliation B1-Q2 同口径) |

**identity 面分布(OBSERVED,本轮新固化)**:

- **v2 面 = 87 份**:`reslice-batch-C` 50 / `reslice-pac-annotated` 22 / `resliced-pilot` 15;
- **v1 legacy 面 = 79 份**:`reslice-p2-b1` 38 / `reslice-stress10` 9 / `reslice-p2-2-fix` 8 / `reslice-p2-b2` 8 / `reslice-p2-fix1` 6 / `reslice-p2-b2-rerun` 4 / `reslice-test-v21` 3 / `reslice-audit-a5` 2 / `resliced-pilot` 1;
- `resliced-pilot` 跨两面(15 v2 + 1 v1);
- **79 份 v1 在 C-IN-1 下必被拒收**——这是生产侧现状事实:当前"可消费面"= 87 份,不是 166 份。

**annotation_meta 键面**:`prompt_version` 166 / `validation_issues` 166(**非空 17**)/ `warnings` 166(**非空 12**)/ `bug22_migration` 8(迁移标记)。

**单元级键面(4,609 单元;键 → 出现单元数)**:

| 键 | 单元数 | 面 |
|---|---|---|
| `unit_id` / `unit_type` / `question_numbers` / `original_question_type` / `answer_lines` / `explanation_lines` | 4,609 | 两面必在 |
| `stem_lines` / `options_lines` | 3,936 | |
| `extra_lines` | 3,621 | |
| `printed_number` / `section` | 4,068 | |
| `material_lines` / `questions_lines` | 673 | = composite 数 |
| `answer_evidence` | 906 | |
| `basis` / `basis_evidence` / `printed_provenance` / `section_ref` | 2,347 | **= v2 面单元总数**;v1 面单元 2,262 无这四键 |

**值域(OBSERVED)**:

- `unit_type`:`standalone_question` 3,935 / `composite_question` 673 / **`andalone_question` 1**(噪声,v2 面内);
- `printed_provenance`:`source_line` 1,546 / `unknown` 667 / `migration_report` 134 / 缺失 2,262(v1 面);
- `basis`:6 值闭集在 v2 面成立——`printed_as_is` 1,546 / `unverified` 667 / `keep` 93 / `shift` 31 / `answer_key` 9 / `explicit` 1 / 缺失 2,262(v1 面)。
- **游离键恰 1 例**:`explanation_lines_note`(value = null;`reslice-batch-C\其他汇编\理综\14_2023届…哈尔滨三中…理综答案.manifest.json`,unit Q24)——**schema 噪声第 2 例**(与 `andalone_question` 并列;证明噪声不只 unit_type 一处,属类级事实)。

### S3 IR(resolver-ir-0.1,冻结工件亲验)

- 工件结构:顶层 `{ir_version, files[88]}`;记录键 `{disposition, file, ir, qc_verdict, reasons}`;
- **仅 ADMITTED 71 条记录携带 `ir` 对象**(`REJECTED_QC_FAIL` 16 + `REJECTED_V1` 1 的 `ir` = null);1,664 单元全部在 71 条 ADMITTED 记录内;
- inner `ir` 键(7):`ir_version` / `source_file` / `source_sha256` / `manifest_file` / `qc_verdict` / `materials` / `units`;
- 单元键(15):`unit_id` / `unit_type` / `question_numbers` / `printed_number` / `printed_provenance` / `basis` / `basis_evidence` / `section_ref` / `section_title` / `content` / `material_ref` / `answers` / `answer_text` / `flags` / `provenance`;
- `provenance` 七字段:`source_file` / `source_version` / `source_lines` / `manifest_file` / `qc_verdict` / `extraction_method` / `confidence_state`;
- `content` 六区:`stem_lines` / `options_lines` / `answer_lines` / `explanation_lines` / `material_lines` / `questions_lines`;
- 值域:`unit_type` 1,385 / 278 / 1(andle,噪声忠实携带);disposition = 71 ADMITTED / 16 QC_FAIL / 1 V1;
- **覆盖与生命周期事实**:IR = R52 对 R50 基线 88 文件的**一次性运行产物**;生成器(`scripts/resolver_reference.py`)在库且经 R52/R53 验证,但**自 R52 起未再对全语料运行**;工件冻结永不回改;71/71 `source_sha256` 与当前源对账零漂移(DQE @`4d78513`,本轮复证工件在位)。

### S4 OCR 输出清单(1,801 条普查)

- 全量键(1,801/1,801):`source_rel` / `source_sha256`(源 PDF)/ `source_size` / `pages` / `output_rel` / `written_at`;
- R66 批次 698 条另携:`audit_line` / `log_ok_lines` / `processed_at` / `provenance`;
- append-only;**语义 = 钉 PDF,不钉 md**(与 S3 的 sha 语义不同,不可混用)。

### S5 R50 审计快照

`data/audit_snapshot_R50_input_baseline.json`:356 文件逐文件 sha + `corpus_sha256`;冻结;verify 零漂移。

---

## §2 hash 语义登记(B2 生产侧输入)

**producer 输出面上的 hash 全集(穷举,本轮复证)**:

| hash | 对象字节 | 算法 | 生成点 | 出现在 | 面向 |
|---|---|---|---|---|---|
| `source_sha256`(md) | 源 OCR md **原始字节** | SHA-256,hex 小写 | `resolver_reference.py:249`(文件级)/ `:167`(provenance) | S3(IR) | 输出面 |
| `source_sha256`(PDF) | 源 **PDF** 原始字节 | 同上 | `r67_manifest_bootstrap.py:181` | S4(OCR 清单) | 输出面 |
| `corpus_sha256` | 快照全体条目 canonical 指纹 | SHA-256 | `audit_integrity.py:128-134` | S5 | 输出面(审计) |
| `norm_sha256` | 归一化文本(`sha256(NFC; CRLF/CR→LF; per-line rstrip; whole strip)`,`r64` NORM_ALGO) | 见左 | `r64_data_inventory.py` | 仅审计内部工件 | **非输出面** |
| `manifest_sha256` / `entries_sha256` / `plan_sha256` 等 | 工具自证指纹 | SHA-256 | r67/d5b 审计工具族 | 内部报告 | **非输出面** |

**不产出(全仓 grep = 0,Reconciliation B2 复证)**:`body_hash`、`line_hash`、任何图片 hash、任何文本规范化 hash 的**接口输出**(norm_sha256 只存在于审计工具内部,从未发布为接口字段)。

**生产侧事实归纳(不推导方案)**:①输出面 hash 全部是"原始字节 SHA-256"单一家族,可被任一方用标准库独立重算(无共享密钥、无版本化算法参数);②md 与 PDF 两种 `source_sha256` 语义并存,靠所在输出面区分;③文本级 hash(body/line/归一化)在 producer 侧**不存在接口输出**——若任何裁决需要它们,属**新增产出 = 接口变更**(受契约变更治理管辖,本文件不提案)。

---

## §3 对 B1/B2/B3 的生产侧输入

> 以下每项只给**事实约束与权限边界**;不选边、不提案、不假设 V3 侧任何行为。

### B1(传输层)的生产侧输入

1. 三个候选载体的存在性/完备性 = §0 合取事实:**全语料覆盖**只在 S2(manifest,零 sha);**md sha + provenance** 只在 S3(88 条样本面,冻结);**持续产出**只在 S1/S2/S4(daemon 面),S3 无增长机制在运行;
2. IR 生成器存在且验证过(R52/R53、F1 2403/2403),但"全语料 IR"**当前不存在**——重新产出属**数据生成动作 + 新工件面**,按仓内纪律须 Owner 显式令(这是权限事实,不是方案);
3. manifest 零 sha 是**生成链事实**(标注→落盘链从未写入 sha),不是损坏或遗漏;给 manifest 加 sha 同样是接口变更(同上受变更治理管辖);
4. identity 面分裂(87 v2 / 79 v1)意味着**任何载体裁决的覆盖面以 87 份 v2 为上限**,79 份 v1 的处置是独立事实问题(C-IN-1 现状 = 拒收)。

### B2(hash 对账口径)的生产侧输入

1. producer 能提供的对账锚 = §2 表内四个输出面 hash;**算法族唯一**(原始字节 SHA-256)+ corpus 指纹;
2. `body_hash` / `line_hash` **producer 零产出**——不存在"算法是否一致"的 producer 侧对应物;
3. `norm_sha256` 的归一化算法**已在仓内定义**(r64 NORM_ALGO,可查、确定性),但从未作为接口发布——若口径裁决涉及文本规范化,生产侧事实是"算法定义存在、接口输出不存在";
4. sha 无密钥、可独立重算——对账的全部前提是"载体上有该字段 + 双方对'钉什么字节'达成一致"。

### B3(unit_type 隔离执行面)的生产侧输入

1. 值域事实:v2 面 2,347 单元内 canonical 恰 2 值 + 噪声恰 1(`andalone_question`,batch-C Q1);另有第 2 例 schema 噪声(`explanation_lines_note`,§1)——**噪声是类级现象,不是单点**;
2. producer 链零守卫事实:LLM 输出 → 落盘原样(`write_outputs` 无值域校验)→ resolver 逐字复制(`resolver_reference.py:152`)——**生产侧今天没有任何一层检查 `unit_type`**;
3. 已登记的 producer 侧处置选项(**既有登记的引用,非新提案**;详见 DQE §1 B/C 与 closure plan §2/§5):单点确定性修复 = 数据修复,**破坏 R50 冻结面成员,必须配对基线再冻结决策**;值域守卫 = 已建议并入 basis schema-only(排期③),未实施;
4. 噪声实例的双分布事实:`andalone_question` 在 v2 面单元内(可消费面),`explanation_lines_note` 同样在 v2 面(batch-C)——两例均不在 v1 legacy 面。

---

## §4 不承诺清单(producer 今天**不**输出什么)

| 不输出项 | 事实来源 |
|---|---|
| `body_hash` / `line_hash` | 全仓 grep 0(Reconciliation B2) |
| 图片字段(`figure_id`/`page_no`/`bbox`/`placement`/`source`/`object_key`/`figure_hash` 任一) | 契约 §2.4 / DQE §2 / Review C.3 |
| version→version lineage 指针(supersede/successor/latest) | 契约 §1.3(OQ-1,R-4) |
| per-label options(`options_labels[]`) | 契约 §2.3 gap |
| `sub_question_units[]`(composite 子题拆分) | 契约 §2.3 gap |
| 全语料 IR(仅 88 条样本工件) | §1 S3 |
| manifest 内任何 sha | §1 S2(0/166) |
| 文本规范化 hash 的接口输出 | §2(norm_sha256 仅审计内部) |
| 图片资产在位性声明(27,240 处悬空引用是已量化事实,交付面不含资产保证) | DQE §2 / closure plan §3 / Review N1 |

---

## §5 边界声明

**本文件做了**:全语料只读普查(manifest 166/IR 88 记录/OCR 清单 1,801 条,工件 `data/producer_interface_census.json`);五输出面字段级固化(含两项本轮新固化事实:identity 面 87/79 分裂、schema 噪声第 2 例);hash 语义全集登记;B1/B2/B3 生产侧输入(事实约束 + 权限边界)。

**本文件没做(五纪律自查)**:未假设 V3 消费方式(全文无一处描述 V3 应如何读);未提出 V3 实现方案(全文无"建议/应该/推荐",§3 仅引用既有登记项);未执行清洗(语料零写入,零修复,零迁移);未冻结/修改 Contract(v0.1 DRAFT 未动);未修改任何代码(两仓)。

**裁决权**:B1/B2/B3 及 closure plan §5 六项全部归 Owner。本文件结束生产侧事实生产;裁决下达前,producer 不启动任何数据动作。

---

*v1 — 2026-09-16,DSH(preprocessing Producer Owner)。基线 `4d78513`;上游 Reconciliation v0.2(`ad1abdd`);普查工件 `data/producer_interface_census.json`。供 Owner 裁决 B1/B2/B3。*

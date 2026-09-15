# PREPROCESSING-PRODUCER-FACT-RECONCILIATION v0.2

> **触发**:Owner 指令(2026-09-16)——回应 Claude Consumer Review v0.2 的 B1/B2/B3。
> **性质**:Producer 侧事实核对(逐行亲验,不采信转述)。**四禁零触碰:未修改代码、未修改数据、未执行清洗、未修改 Contract(保持 v0.1 DRAFT)**。
> **证据基线**:
> | 仓 | 基线 | 说明 |
> |---|---|---|
> | preprocessing(`D:/Project/Papers`) | **`4d78513`**(任务指定);工作树 HEAD = `4fdbb70` | `git diff --stat 4d78513 HEAD` = 仅 5 个文档/测量工件,数据零变化;今日复扫全语料 166 份 manifest(与 DQE 时点同数),携带 sha 键仍 = 0 |
> | V3(`AITutors-v3`) | 代码面 = `b5ddbe3`~`938535d` 等价(`b5ddbe3..938535d` diff 仅 +1 份 review 文档) | 本轮全部 V3 代码引用为 DSH 逐行亲读 |
>
> 被核对文档:Claude `PREPROCESSING-V3-CONTRACT-CONSUMER-REVIEW-v0.2.md`(V3 `938535d`,COMMITTED 级)。
> 附带台账事实:V3 仓 `CONTRACTS/PREPROCESSING-V3-CONTRACT.md`(Claude 需求侧契约稿)与 v0.1 review、handoff 007 目前为 **untracked(`??`)未 commit**——按台账纪律(prohibitions:未 commit = REPORTED 级),本文件引用它们时只作"存在性/文本"事实,不作双方 ack 事实。

---

## B1 Source Identity

### 问题 1:`source_sha256` 在哪里生成?

**OBSERVED**——生产点唯一,位于 preprocessing Reference Resolver(`scripts/resolver_reference.py`),语义 = **源 OCR markdown 文件字节的 SHA-256(hex,小写,64 字符)**:

| 位置 | 写入什么 | 行号 |
|---|---|---|
| `_sha256(p)` | `hashlib.sha256(p.read_bytes()).hexdigest()`(原始字节,无规范化) | `resolver_reference.py:52-53` |
| IR 文件级 | `"source_sha256": _sha256(src)` | `resolver_reference.py:249` |
| IR 单元级 | `provenance.source_version = _sha256(src)`(同文件逐单元一致,F1 审计 2403/2403 验过) | `resolver_reference.py:167` |

**另一枚同名字段、不同语义(不可混用,DQE §4 已披露,本轮复述以防误引)**:OCR 输出清单 `data/ocr_output_manifest.jsonl` 的 `source_sha256` = 源 **PDF** 字节 sha(生成点 `scripts/r67_manifest_bootstrap.py:181` `file_sha256(source_pdf)`)。审计脚本(`audit_f1_consistency.py:326`、`r67_apply_gate.py:191` 等)只做只读重算校验,不生产新值。

**VERIFIED**:全仓 grep + 生成点逐行亲读;两处语义边界与 DQE §4 分层钉链一致。

### 问题 2:manifest 是否携带?

**OBSERVED / VERIFIED**——**不携带**。今日复扫(与 DQE @`4d78513` 同口径,精确键遍历):全语料 **166 份 manifest,携带任何 sha 键 = 0,键名集合 = 空**。manifest v2 只钉 `source_file` 路径 + 行号锚;其 sha 语义只能来自相邻层(IR 71/71 源对账 / R50 基线 356/356 / OCR 清单 PDF sha)。

与 Claude Review §A.2 一致,无异议。

### 问题 3:IR 是正式消费接口还是内部产物?

**OBSERVED**——三个事实并存,必须分开陈述:

1. **仓内冻结契约面**:`resolver_contract_design.md`(C-IN/C-OUT/C-FAIL)定义 IR = Reference Resolver 的**输出工件**(C-OUT-1 派生路径 / C-OUT-2 provenance 必携 / C-OUT-3 报告口径)。该文档的"消费"语境是 preprocessing 仓内的消费纪律,不是 V3 传输接口。
2. **方向性设计陈述**:同文件 G-BOUND-1 段落(L167)写"Backend 消费面 = 验证过的 IR + provenance + unresolved 显式通道"——这是设计方向,**无字段级传输定义、未经 V3 ack**。
3. **现实消费面**:V3 backend **零消费**(DSH 独立复核:`Grep resolver_ir|resolver-ir|source_sha256 @ backend/` = **0 命中**);真实 IR 工件全仓仅一份(`data/resolver_ref_r52/resolver_ir.json`,88 文件/1,664 单元,冻结审计工件,永不回改——今日亲验其 `andalone_question` 恰 1 例 = Q1,与 DQE 一致)。

**VERIFIED**:IR 当前状态 = **producer 内部产物 + 消费接口候选**;"正式消费接口"从未被任何一方 ack。Integration Contract v0.1 §2 的"V3 消费以 IR 为准"是 DRAFT 条款(Owner 明令保持 DRAFT),不是既成事实。

**UNKNOWN**:V3 是否排期 IR loader——无代码、无排期记录(与 Review §A.5 一致;传输层裁定权归 Owner)。

### 问题 4:是否存在文档定义 `IR → manifest → V3` 或 `IR → V3`?

**OBSERVED**——逐文档清点(不存在 `IR → manifest → V3`:manifest 先于 IR,producer 链方向是 manifest → resolver → IR;该写法在任何文档中零命中):

| 文档 | 状态 | 定义了什么链 |
|---|---|---|
| preprocessing `INTEGRATION/PREPROCESSING-INTEGRATION-CONTRACT.md` §2 | v0.1 **DRAFT**(未 ack、Owner 令不冻结) | **IR → V3**("V3 消费以 IR 为准,manifest 为回源凭据") |
| V3 `CONTRACTS/PREPROCESSING-V3-CONTRACT.md` §2.1 | Claude 需求侧稿,**untracked 未 commit(REPORTED 级)** | **manifest → V3**(字段级 = stem_lines/options_lines 等 manifest 形态;§1.1 body_hash/line_hash 标注"消费侧计算") |
| `resolver_contract_design.md` | 仓内冻结 | preprocessing 内部 manifest → resolver → IR,**不含 V3** |
| Claude Consumer Review v0.2 §A.5 | COMMITTED(`938535d`) | 不定义链,登记"传输层未定"为 BLOCK |

**VERIFIED**:①**不存在任何双方 ack 的传输链定义**;②两份 DRAFT 互斥(IR→V3 vs manifest→V3),这正是 B1 BLOCK 的实质;③无文档定义 `IR → manifest → V3`。

**UNKNOWN**:Owner 将裁定哪条链(三条互斥路径见 Review §A.5,本文件不提案)。

---

## B2 Hash

### 四列核对表(至少覆盖 source_sha256 / body_hash / line_hash)

| 字段 | 算法 | 生成位置 | 消费位置 |
|---|---|---|---|
| `source_sha256` | SHA-256(**文件原始字节**),hex 小写 64 | preprocessing:`resolver_reference.py:249`(IR 文件级)+ `:167`(单元 provenance);旁系:`r67_manifest_bootstrap.py:181`(OCR 清单,**PDF** 字节,语义不同) | 契约面:Integration Contract §3.1(必须提供)/ §3.3-3(sha 不符即阻断)——**DRAFT**;V3 代码:**零消费**(grep 0 命中) |
| `body_hash` | **preprocessing 不产出**。算法只存在于 V3 侧:消费脚本 = `splitlines()` 取行(`source_loader.py:27`)→ `"\n".join` → SHA-256(`source_loader.py:43-46`);生产 seal 路径 = 对"line index 按 seq `\n` join 重建的 body_text"做 raw UTF-8 SHA-256(`line_index.py:70-72`,与消费脚本同算法) | **preprocessing 全仓 grep `body_hash` = 0 命中**;V3:`runner.py:72` / `runner_b2.py:144`(consumer)→ `document_source_versions.body_hash` + `integrity_hash`(consumer 路径 integrity_hash=body_hash);`seal.py:126`(生产) | V3 内部:seal 校验、IS-4 重建核验(`test_seal_dbflow` 重建 hash 匹配落库)、documents API;**跨系统对账 = 无载体** |
| `line_hash` | **preprocessing 不产出**。V3 两套算法并存:①consumer 脚本 = 单行 `sha256(text)` raw(`source_loader.py:38`);②生产 seal = canonical 复合 `sha256_hex({text, raw_sources, selected_source, evidence})`(`line_index.py:75-90`) | preprocessing 全仓 grep `line_hash` = 0 命中;V3:`source_loader.py:38`(consumer 写库)/ `seal.py:177`(生产写库) | V3 内部 `document_source_lines.line_hash`(同一张表,两条 ingest 路径写入**两种语义**);跨系统 = 无 |

### 与 V3 当前算法一致性确认

| 对比 | 结论 | 证据(亲验) |
|---|---|---|
| `source_sha256` vs V3 自算 `file_sha`(`documents.original_sha256`) | **不一致,且永不相等**。V3 `runner.py:73`/`runner_b2.py:145`:`file_sha = sha256_hex(body_text)`;`sha256_hex` 先 `canonical_json`(字符串被 JSON 引号包裹)再 hash(`hashing.py:60-62`)——与原始字节 sha 是两个函数族 | `hashing.py:39-62` 逐行亲读 |
| `source_sha256` vs V3 `body_hash` | **定义不同**。body_hash 丢弃行终止符(splitlines)+ 尾随换行,仅在"LF-only 且无尾随换行"文件上偶然相等;v0.1 实测 12 份 ADMITTED 样本 6/12 DIFFER(Claude 侧测量,DSH 采信数字、亲验机制成立)。**行号勘误**:`splitlines()` 在 `source_loader.py:27`(`load_source_lines` 内),不在 `compute_body_hash`(其本身只做 `"\n".join` + sha256);漂移结论不变 | `source_loader.py:24-46` 逐行亲读 |
| `body_hash` / `line_hash` vs producer | **无可比对象**——preprocessing 不产出这两个字段(全仓 0 命中),"算法是否一致"在 producer 侧不成立。真正的断点是复合的:B1(跨系统锚 `source_sha256` 在 V3 消费路径上无载体)+ B2(V3 自算值算法与 producer 定义不同) | 本文件 B1 + 上表 |

**VERIFIED**:Review §A.3 的"两路对不上"结论成立(canonical_json 引号 / splitlines 规范化),DSH 逐行复核确认,仅一处行号勘误(见上)。

**附带 OBSERVED(登记,不提案)**:V3 `document_source_lines.line_hash` 同表两算法并存——consumer 脚本写 raw 单行 sha,生产 seal 写 canonical 复合 sha;`integrity_hash` 在 consumer 路径被退化为 `= body_hash`(`runner.py:93`,生产路径则是 body+lines+figures+provenance 的复合,`line_index.py:93-108`)。**UNKNOWN**:V3 是否有意允许两路径数据同库共存——属 V3 内部治理,不在本文件处置范围。

---

## B3 unit_type(`andalone_question` 逐层追踪)

**唯一实例**:`Ocr-markdown\reslice-batch-C\合格考\化学\2020北京高中合格考化学（第一次）（教师版）(1).manifest.json`,unit `Q1`(亲读:`question_numbers=[1]`,`original_question_type=single_choice`,`stem_lines=[16,16]`,`options_lines=[19,19]`,`answer_lines=[378,380]`,`explanation_lines=null`,无 material/questions 字段)。

| 层 | 实际行为(逐行亲验) | 证据 |
|---|---|---|
| **manifest** | LLM 标注输出原样落盘,producer 链零值域守卫(`write_outputs` 原样);值 = `"andalone_question"` | manifest Q1 亲读;DQE §1 |
| **resolver**(preprocessing Reference Resolver) | **逐字复制**:`"unit_type": u.get("unit_type")`(`resolver_reference.py:152`),零校验;IR 忠实携带该值(冻结工件亲验恰 1 例) | `resolver_reference.py:150-153`;`resolver_ir.json` 亲扫 |
| **annotation**(V3 `annotation_adapter`) | `== "composite_question"?` 否 → `_build_standalone`;**payload 的 `unit_type` 被重写为 canonical `"standalone_question"`(`annotation_adapter.py:42`)——噪声在 annotation 层被静默洗白,V3 payload 自此不含异常值,且无任何信号 | `annotation_adapter.py:100-104,40-46` |
| **span**(V3) | 两处均按**原始 manifest 值**分支:`== "standalone_question"?` 否 → composite 路径。Track B(`resolved_span_adapter.py:77-90`):走 material/questions/answer/explanation 角色——本单元 material/questions 为 null,实际仅产 `sp-Q1.answer`;Track B2(`runner_b2.py:116-127`):产 `sp-Q1.sub.answer`。**两轨都不产 `sp-Q1.stem`**(composite 分支无 stem 角色)——与 annotation 层的 standalone 编排**互相矛盾** | `resolved_span_adapter.py:77-90`;`runner_b2.py:97-127`;manifest Q1 字段亲读 |
| **runner**(V3) | Track B2:IRBuilder 拿洗白 payload(standalone,声明 stem+answer)+ composite 式 spans 组装 → `sp-Q1.stem` 不在 resolved(`compile/ir.py:108,151`)→ validate_ir 记 "stem unresolved"(choice 型无 options 声明另记 "options missing for choice type",`ir.py:201-218`)→ **`semantic_status = incomplete`** → `runner_b2.py:232` `!= "ready"` → skip,continue。Track A:`GateService.run` 用 V3 自有 `SourceResolver`(搜索式,不消费 manifest 行号,`gate/service.py:156-158`)解析洗白后的 payload,能否 ready 静态不可判定 → **UNKNOWN**;GateService 对非 ready 同样跳过(`service.py:182-184`) | `compile/ir.py:105-138,141-163,187-251`;`runner_b2.py:231-239`;`gate/service.py:181-184` |
| **candidate** | **Track B2:无 candidate 行产生**——`runner_b2.py:252` 的三元式仅对 ready 单元可达,本单元永不到达;即便到达,其输入 `root.unit_type` 来自洗白 payload = `"standalone_question"`(IRBuilder 从 payload 取值,`ir.py:108`),会落 **`"standalone_unit"`**。GateService 路径同样仅 ready 进 candidate(`service.py:210-224`)。全链无 unknown/PENDING 信号 | `runner_b2.py:231-252`;`gate/service.py:181-224`;`compile/ir.py:108` |

### 特别确认:DQE "消费侧隔离已生效" 是否准确?

**判定:不准确。DSH 正式更正 DQE §1 选项 A 该句(只修正事实,不提出方案)**:

1. **更正 DQE**:契约 §3.3-6 是 **DRAFT 条款**(v0.1,未 ack、未冻结)——是"要求",不是"已生效的现状"。DQE §1-A 把"契约条款存在"误写为"消费侧机制已生效,无需动作"。**该句撤回**。V3 四消费点零隔离信号(上表),与 Claude Review §B.2/B.4 一致,DSH 确认。
2. **实际终态(Track B2)= 无信号的 incomplete→skip,不是 PENDING 通道隔离**:记录在案的原因是 "stem unresolved"/"options missing for choice type",真实原因(unknown unit_type)在任何一层都不出现——这是"静默失败掩盖",比"静默当 standalone 吃"更隐蔽(消费方看到的是格式类错误,不会想到值域噪声)。
3. **对 Claude Review §B.2 candidate 行的更正(事实层)**:`runner_b2.py:252` 记 "composite_unit" 的数据流推断有误——该行消费的是 `IRNode.unit_type`,而 IRBuilder 从 annotation payload 取值(`ir.py:108`),该值已被 `annotation_adapter.py:42` 洗白为 `"standalone_question"`;且本单元因 incomplete 永不到达该行。**candidate 层实际行为 = 零落库**,既非 `composite_unit` 也非 `standalone_unit`。"三处解释互相矛盾"修正为:**annotation 层(洗白为 standalone 且重写 payload)与 span 层(按 composite 解析)两层矛盾成立**;candidate 层是"无记录"而非"第三种解释"。
4. **对 Review §A.3 一处行号勘误**:`splitlines()` 规范化发生在 `source_loader.py:27`(`load_source_lines`),`compute_body_hash`(`:43-46`)本身只做 join+hash;漂移结论(6/12 DIFFER)不变。

---

## 边界声明

**本文件做了**:B1 四问逐答(OBSERVED/VERIFIED/UNKNOWN);B2 三字段四列核对 + V3 算法一致性逐行确认;B3 六层追踪 + DQE §1-A 陈述更正 + Review candidate 层推断更正。全部 V3 代码引用为 DSH 逐行亲读(`b5ddbe3`~`938535d` 代码面等价)。

**本文件没做(任务禁止项)**:未修改任何代码(两仓);未修改任何数据;未执行任何清洗;未修改 Contract(保持 v0.1 DRAFT,零编辑);未对 B1/B2/B3 提出修复方案——传输层裁定(B1)归 Owner,消费面措辞归后续 Contract 修订协商。

**对三 BLOCK 的态度**:B1/B2/B3 的**事实面**经本轮核对后 producer/consumer 两侧已对齐(差异仅剩上述两处更正 + 一处行号勘误);**裁决面**(传输层选择、hash 对账口径、隔离执行面)不变,归 Owner。

---

*v0.2 — 2026-09-16,DSH(preprocessing)。基线 `4d78513`(任务指定)/ V3 代码面 `b5ddbe3`~`938535d`。回应:PREPROCESSING-V3-CONTRACT-CONSUMER-REVIEW-v0.2 B1/B2/B3。*

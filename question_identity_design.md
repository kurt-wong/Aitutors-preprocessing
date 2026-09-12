# QuestionIdentity 第一性原理设计(R32 提出 / R33 对抗审查修订 / R34 实施落地)

> 状态:🟢 v0.3 已实施(R34)。四项一体全部落地:basis 字段、SectionLocator schema、C13 升级、存量确定性回填;P2-01~P2-08 全部有真实测试(见 §9)。
> 输入:第五轮审查对 R31(`e3e4e47`)的裁决——Phase 1 PASS,BUG-22 分层关闭(Prompt/QC/迁移 🟢,resolver identity 模型 🟡),下一步优先进入 Phase 2。
> R33:对抗性审查,v0.1 不变量 1 被回迁突变证伪(登记 BUG-23),修订为 v0.2。
> R34:按第五轮审查冻结的 4 项实施条件 + P2-01~P2-08 验收标准实施;裁决三态(FAIL/PENDING_REVIEW/PASS)落地。
> 原则:每个设计决定必须回指真实试卷证据,不允许"为了让系统简单"而篡改源事实。

---

## 0. 先记账:BUG-22 的根因升级

R31 之前我们把根因概括为"Question Number Namespace 没有被正确建模"。R31 修复时在 prompt v2.1 第 247 行找到明确条款("有的试卷分节各自从 1 编号…按原样照抄题号即可"),因果链应正式更正为:

```
真实试卷存在局部编号空间
        +
Prompt v2.1 明确允许/要求保留局部编号
        ↓
LLM 正确遵循 Prompt(模型没有错)
        ↓
Manifest 跨 section 重号
        +
下游把 number 当全局身份
        ↓
Silent mis-segmentation(BUG-22)
```

**定性:Prompt Contract 与下游 Identity Contract 不一致(Prompt Specification Defect),不是模型理解错误。**
这条教训直接约束 Phase 2:identity 契约必须单一出处,下游永远不得默默假设上游字段的语义。

## 0.1 概念漂移防火墙(必须先写死的一句话)

> **C13 的 `(section, number)` 是 preprocessing manifest scope 内的 identity invariant,不是数据库 Question 的最终 canonical identity。**

V3 跨试卷体系的最终身份至少是 `DocumentSourceVersion + SectionIdentity + LocalQuestionNumber`,甚至需要 `Occurrence` 维度。本设计中出现的所有"身份"字样,若无特别注明,均指 manifest scope。

---

## 1. 问题一:Question Identity 的层级

必须拆成两个不可混用的实体:

### 1.1 SourceOccurrenceIdentity —— "源卷面上的这一次出现"

```
SourceOccurrence
    ├── source_version   # 哪份源文档的哪个版本(OCR md + 哈希)
    ├── section_ref      # 指向 SectionLocator(见 §2),不是标题字符串
    ├── printed_number   # 卷面实际印刷题号,字符串,永不重写(见 §3)
    └── span             # 源文档行区间 [start_line, end_line)
```

这是 **Source Fact**:一旦写入,任何下游解释都不得覆盖它。它回答的问题是:"这段文字在源卷面上是第几题、出现在哪里"。

### 1.2 CanonicalQuestionIdentity —— "当前编号体系下的规范题号"

```
CanonicalLabel
    ├── section_ref
    ├── canonical_number # 当前 manifest/编号体系内的规范编号(int)
    └── basis            # 推导依据:answer_key | running_max | printed_as_is
```

这是 **Preprocessing Interpretation**:它回答的问题是:"在本套编号规则下,这道题的规范编号是什么"。它可以被重新推导、被迁移脚本改写,但每一次改写必须留下 basis 证据(R31 迁移报告即此模式)。

### 1.3 两者关系

```
SourceOccurrence  --(推导,可审计,可重推)-->  CanonicalLabel
```

- 一个 SourceOccurrence 在不同编号体系下可以推出不同 CanonicalLabel(例:化学 2018 非选择卷面印刷 1,答案区键位 26——见 §4);
- CanonicalLabel **永远不能反向覆盖** SourceOccurrence;
- unit_id(R31 踩坑:`U1`/`Q1` 在汇编中大量重复)已被证明 **既不能当 SourceOccurrence 也不能当 Canonical identity**,它降级为纯展示别名(display alias)。

**长期 locator 契约(回应 R31 踩坑一)**:list position 只能作为迁移过程中的临时 locator;长期 locator 必须是 `(source_span, semantic_role, ordinal)` 三元组——可回到源证据、可审计、不依赖数组下标。

## 2. 问题二:Section 到底是什么

**Section identity 不能只靠 title。** 真实反例:同一文档出现两个"选择题"分部、汇编中同名"实验题"考点块重复出现。R31 迁移脚本已经实测:同名标题必须按**标题出现次序**消歧(`f"{title}#{occ}"`),按 unit 计数消歧会把同一块拆散。

### SectionLocator(定位器,title 只是展示元数据)

```
SectionLocator
    ├── source_version
    ├── ordinal          # 本文档内分节出现序号(1-based)
    ├── start_line       # 分节标题行
    └── end_line         # 下一分节标题行(或文档末尾)
```

- `title` 字段仍保留,但语义明确为 **display metadata**,可重复、可为空、可被 OCR 损坏;
- 等价表述:section 由 `(source_version, ordinal)` 唯一定位,`start_line/end_line` 提供可回源的 span 证据。二者冗余但互为校验:ordinal 与 span 在确定性构建时必须一致;
- **现实约束(A7 实测)**:现有 50 份 manifest 无任何 locator 字段,section 仅是裸 title 字符串——Phase 2 实施必须扩展 manifest schema 并对存量回填,否则本节设计只是纸面模型。

### Section 缺失时的 fallback(OCR 丢标题,真实存在)

地理 U13-14 实测:OCR 把"14."吞成"4."。同理 OCR 会丢 `##` 标题(R31 `SECTION_RE` 已被迫接纳裸"考点/考向/微专题"行)。Fallback 链:

1. 有显式标题 → SectionLocator 正常构建;
2. 无标题但有答案区全局键位 → 以"答案区键位覆盖区间"合成隐式分节(synthetic section),标记 `derived=true`;
3. 两者皆无 → 整卷视为单节,paper-global 检查(R30 行为),**并在 QC 中显式报 warning 而不是静默降级**。

## 3. 问题三:printed_number 与 canonical_number

**必须分离,`number` 一个字段承担三种语义的时代结束。** 目标 schema(prompt v2.3 / manifest v3 目标形态,Phase 2 实施时落地):

```json
{
  "section": "二、非选择题",
  "printed_number": "1",
  "canonical_number": 26,
  "canonical_basis": "answer_key"
}
```

| 字段 | 语义 | 可变性 |
|---|---|---|
| `printed_number` | 卷面实际印刷题号,**Source Fact** | 永不可改写;字符串(印刷可能是"1""(1)""A"等) |
| `canonical_number` | 当前 manifest 编号体系内规范编号 | 可重推导,每次变更留 basis + 迁移报告 |
| `section` | 编号作用域,指向 SectionLocator | 同 canonical |

反例驱动(为什么必须分):化学 2018 非选择题卷面印刷 `1..9`,答案区键位 `26..34`。若 manifest 只存 `number: 26`,则 **"源卷面印的是 1"这一事实永久丢失**,违背 Source-first 原则,且未来无法回答"学生在卷面上看到的是几号"。

### 兼容性策略(Phase 2 实施约束)

- 现有 `number` 字段语义 = `canonical_number`(R31 迁移后已满足),**不得静默改义**;
- 新增 `printed_number` 采用**只增不改**原则:R31 迁移报告中保存了每单元 old 值,可确定性回填(化学 N1-N9 的 old=1..9 即 printed);`shift`/`keep` 类同;
- **现实约束(A5 实测)**:迁移报告含 old 值的仅 41/1484 单元(2.8%)。v2.1 存量产物的 printed 无法从 manifest 恢复——Phase 2 须新增从源 md 的确定性 printed 推导(如题干行首印刷题号);推导不出即显式标 `provenance=unknown`,**禁止把 canonical 回填成 printed**(那会伪造 Source Fact,比缺失更糟);
- `answer_key` 类迁移的 printed_number 一律取 old 值;`keep` 类的 printed == canonical;
- C13 的身份键在过渡期为 `(section, canonical_number)`,printed_number 进入后**不参与** C13(印刷号允许跨节重复,这正是选考模块的合法结构)。

## 4. 问题四:答案区键位 "26." 到底是什么

必须显式定义,否则 Phase 2 会再造一次 BUG-22。裁定:

> **答案区键位是"全卷答案编排编号(canonical answer-key slot)",它是 canonical_number 的最强证据源,但它不是数据库 identity,也不是答案顺序。**

分层回答:

| 问 | 答 |
|---|---|
| 是 Question 26 吗? | 仅在"全卷连续编号体系"下成立;它是该体系下的 canonical_number 证据 |
| 是非选择题第 1 题的答案键吗? | 是——它是同一 SourceOccurrence 的另一个编号面(canonical 侧),与 printed "1" 并存 |
| 是答案顺序吗? | 否。顺序只是排版副产品,不得进入任何 identity |
| 是数据库 identity 吗? | 否。数据库身份属 V3 `DocumentSourceVersion + SectionLocator + LocalQuestionNumber` |

工程推论(已部分实现,R31 三规则,Phase 2 升格为正式契约):

- `answer_key` 证据强度最高(Source-derived),键位即 canonical_number;
- 无键位时用 `running-max` 顺延推导,LLM unit_id 命名作旁证(R31:生物+40、地理+50 均双证据链互印);
- `keep`(选考模块/汇编):canonical_number 保持印刷号,身份由 section 消歧——**这正是 scoped identity 存在的原因**;
- 任何推导必须产出 `canonical_basis`,不允许无证据编号。

## 5. 不变量清单(R33 修订版,Phase 2 验收将逐条测)

1. **canonical 全卷唯一 + 显式豁免**(v0.1 原表述"跨节同号 = LEGAL"已被 A3 突变实测证伪,见 §5.1):
   - `canonical_number` 在单 manifest 内**全卷唯一**;
   - 唯一例外:`canonical_basis == "keep"`(选考模块/汇编块的合法局部编号)——豁免必须**显式标记**,不得仅凭"分节不同"推定合法;
   - 同分节重复无论何时都是 FAIL;
   - 由此:跨分节重号且双方均无 keep 依据 = FAIL(这正是 BUG-22 的原始回归形态)。
2. `printed_number` 一经写入永不变化(任何工具改写它 = 违约,测试拦截);
3. `canonical_number` 的每次变化必有 `canonical_basis` + 迁移报告条目;
4. `unit_id` 不参与任何唯一性断言(仅 display alias);
5. SectionLocator 的 ordinal 与 span 在确定性构建下一致,且 **manifest 必须记录 locator 字段**(ordinal/span),仅有 title 字符串不满足本设计;
6. 无 section 降级必须产生显式 warning,禁止静默;
7. 答案区键位只作为 canonical 证据,永不直接成为跨系统 identity。

### 5.1 R33 对抗性审查结果(每条含真实测量,证据 `data/phase2_adversarial_review.json`)

| 探针 | 测量(真实 batch-C 50 份产物,生产代码) | 裁定 |
|---|---|---|
| A3 BUG-22 回迁突变 | 7 份迁移产物题号全部回退 old 值后跑生产 C13:**保留 section → 仅 1/7 被拦**(博雅语文是回退后恰成同分节重复才命中);**删除 section → 7/7 全拦** | 🔴 **v0.1 不变量 1 证伪**:scoped C13 一旦有 section 就对 BUG-22 跨分节形态失去守卫。已修订为 canonical 全卷唯一 + keep 显式豁免;生产侧登记 **BUG-23**,修复依赖 basis 字段,并入 Phase 2 实施 |
| A1 section 覆盖率 | 1484 单元中仅 **291(19.6%)** 带 section;**42/50 文件零 section** | 🟠 scoped identity 现实生效面不足两成,其余 84% 数据 C13 处于全卷退化模式。Phase 2 必须包含存量回填/标注,不得只设计新链路 |
| A4 静默降级 | 删 section 后 8 份产物 QC 输出中,**0 份**出现任何"缺 section"类显式告警 | 🔴 不变量 6 当前未实现(生产静默降级)。列为 Phase 2 实施必测项 |
| A5 printed 回填覆盖 | migration report 含 old 值的单元 **41/1484(2.8%)**,7/50 文件 | 🟠 §3 回填策略仅覆盖 2.8%。修订:迁移件回填;v2.1 存量产物的 printed 无法从 manifest 恢复,须新增从源 md 的确定性推导,推导不出则显式标 `provenance=unknown`,**禁止把 canonical 当 printed 猜测回填** |
| A6 unit_id 重复 | 1/50 文件(专题十六汇编)**78 个单元** unit_id 重复 | ✅ §1.3 "unit_id 不可作键"声称成立,已量化 |
| A7 SectionLocator 字段 | 50 份 manifest 全部单元字段普查:**无任何 ordinal/span/locator 类字段**;section 仅是 291 个裸 title 字符串 | 🔴 §2 SectionLocator 在现有产物上不可实现,manifest schema 必须扩展(不变量 5 已补要求) |
| A2 scoped 不变量普查 | 真实 50 份产物 (section,题号) 零冲突 | ✅ 成立,但注意此检查与 C13 同源,不构成独立证据 |

**测试固化**:`tests/test_question_identity_adversarial.py`——xfail(strict) 锁定"BUG-22 回归形态必须被拦"的修复义务(修复后 XPASS 强制转绿),另一用例锁定"section 字段是唯一分叉点"。

## 6. Phase 3 预告:Question Identity Adversarial Corpus

Phase 2 验收后,Phase 3 不写普通 fixture,建专门对抗语料,每条 fixture 全链路测 `Prompt 输出 → Manifest → C13 → Resolver Identity → Migration → Question IR`:

| Fixture | 攻击目标 |
|---|---|
| 选择题 1–9 + 非选择题 1–9 | 局部编号 |
| 三个选考模块均 1–3 | 多 scope 合法重号 |
| 分节标题重复出现 | SectionLocator ordinal |
| OCR 丢失分节标题 | fallback 链 + 显式 warning |
| 答案区全局键位 | canonical 映射 |
| 答案区局部键位 | ambiguous 映射 |
| 汇编多考点块独立编号 | repeated local numbering |
| unit_id 重复 | locator collision(unit_id 不可作键) |
| 同名 section | occurrence 顺序消歧 |
| 空 section 字段 | 边界 |
| 跨页分节 | span 连续性 |

## 7. 明确不在 Phase 2 范围

- V3 数据库层 canonical identity 的最终设计(只预留字段与防火墙语句);
- 全量 rollout(按裁定排在 Phase 2+3 之后);
- resolver 具体实现代码(本设计验收后另起实施任务)。

## 8. 证据索引

- R31 迁移报告:`data/bug22_migration_report.json`(每单元 old/new/mode/evidence);
- R31 batch-C QC:`data/reslice_batch_c_qc_r31.json`(C13 残留 0,38/50 PASS);
- R31 三坑(unit_id 重复 / 同名标题消歧 / `[答案]` 字符类误伤"方案"):见 `log.md` R31 条目与 `tests/test_bug22_migration.py`;
- 选考模块合法重号:会考化学 2018 三模块印刷均 1–3;汇编独立编号:专题十六;
- OCR 丢字:地理 U13-14 "14."→"4."(`log.md` resolver 入库前置清单)。

---

## 9. R34 实施记录与 P2 验收证据

### 9.1 实施语义修正(实施中发现并当场裁定的一处边界)

v0.2 的"canonical 全卷唯一 + keep 豁免"在真实数据上遇到:**会考化学选择题 1-25 与选考模块 keep 1-3 天然同号**——豁免不能要求"重复各方全部 keep"。裁定为**划分语义**:

- **非 keep 持有者之间**必须全卷唯一(BUG-22 回归形态 = 两个非 keep 跨节重号 → FAIL);
- **keep 为个体豁免**(可与非 keep 同号),但每个 keep 必须携带可回源证据(`basis_evidence` 含 `L{行号}` 且在源文件界内),否则 PENDING_REVIEW;
- 同分节重复永远 FAIL,keep 不能救。

### 9.2 落地形态

| 组件 | 位置 |
|---|---|
| 共用身份模型(构建+验证,杜绝各处自行推断合法性) | `scripts/question_identity.py` |
| C13/C14 v2 + 三态裁决 | `scripts/reslice_qc.py`(v1 存量保留 R31 scoped 语义) |
| 存量确定性回填(零 LLM,默认 dry-run) | `scripts/phase2_identity_backfill.py` |
| manifest 落盘不丢身份字段(实施中抓到的真缺陷:write_outputs 自组装洗掉 identity 字段) | `scripts/reslice_pipeline.py` write_outputs |
| Prompt v2.3(printed_number 必填,源事实与入库编号分离) | `scripts/reslice_pipeline.py` |

schema:`identity_version:2` + 顶层 `sections[{id,title,ordinal,start_line,end_line,occurrence,derived?}]`;单元 `section_ref / printed_number / printed_provenance / basis / basis_evidence`。

### 9.3 存量回填结果(batch-C 50 份,`data/phase2_identity_backfill_report.json`)

- 50/50 apply,check_identity **0 fail / 0 review**;共建 612 个 SectionLocator;
- printed provenance:**source_line 948(63.9%)/ migration_report 134 / unknown 402(27.1%)**——unknown 一律 printed=null,禁止猜测回填;
- basis:printed_as_is 948 / keep 93 / shift 31 / answer_key 9 / explicit 1 / unverified 402;
- 回填后 batch-C QC(`data/reslice_batch_c_qc_r34.json`):**38 PASS / 0 PENDING_REVIEW / 12 FAIL**(与 R31 PASS 集完全一致,零回归;12 份 FAIL 均为既有 C3/C5/C6/C7/C9 缺陷)。

### 9.4 P2-01~P2-08 验收证据(冻结标准逐条)

| ID | 证据 | 结果 |
|---|---|---|
| P2-01 | `test_p2_01_unique_canonical_passes` | ✅ |
| P2-02 | `test_p2_02_keep_duplicate_with_evidence_allowed` + `test_p2_02_keep_colliding_with_non_keep_allowed`(划分语义) | ✅ |
| P2-03 | `test_p2_03_bug22_regression_caught` + 真实数据回迁突变 `phase2_adversarial_review_r34.json` A3:**7/7 全拦**(修复前 1/7) | ✅ |
| P2-04 | `test_p2_04_legal_local_numbering_not_falsely_flagged` + `test_p2_04_keep_cannot_excuse_same_section_duplicate`;真实 keep 93 单元零误杀(回填 0 fail) | ✅ |
| P2-05 | `test_p2_05_missing_section_not_silently_passing`;真实 A4:**8/8 显式告警**(修复前 0/8) | ✅ |
| P2-06 | `test_p2_06_section_locator_disambiguates_duplicate_titles` + `test_p2_06b`(同名标题 ordinal/span 消歧;跨节同印刷号仍需 keep) | ✅ |
| P2-07 | `test_p2_07_printed_unknown_not_guessed` + `test_p2_07_backfill_marks_unknown_provenance`(>1000 单元普查:unknown→null) | ✅ |
| P2-08 | `test_p2_08_duplicate_unit_ids_no_collision`(专题十六同 unit_id 按位置分配,回填 0 fail) | ✅ |
| 第三方向(证据不足) | `test_fake_keep_without_evidence_pending_review` / `test_keep_evidence_line_out_of_bounds_pending_review` → PENDING_REVIEW,不误判非法 | ✅ |
| 变异校验 | `test_mutation_sanity_keep_evidence_is_enforced[-1/-2/-3]`(空证据/越界证据/双非 keep 重号三处破坏均被拦截) | ✅ |

### 9.5 已知残留(不隐瞒)

- **v1 存量语义保留**:无 `identity_version` 的历史产物(pilot 16 份、归档)仍走 R31 scoped 旧路径,该路径对 BUG-22 回归无守卫(BUG-23 语义仅 v2 生效)。batch-C 已全部回填 v2;pilot 回填列为后续任务。
- unverified 402 单元(27.1%)printed 缺证据:多为综合题(多题号单元,无单一印刷号)与题干首行非题号的单元;按设计显式标 unknown,不猜。
- `basis_evidence` 的行号存在性可机器验证,**语义充分性**(证据是否真的证明局部编号)仍需人工/Phase 3 对抗语料覆盖——PENDING_REVIEW 通道就是为此存在。

---

## 10. R35 / Phase 3:Evidence Soundness(对抗语料)

第五轮审查裁定:Phase 3 不继续堆规则,攻击"PASS 为什么成立";裁决语义升级为——**PASS = 机器能够证明,FAIL = 机器能够证伪,PENDING_REVIEW = 机器无法证明也无法证伪**。

### 10.1 第二层证据语义检查(机器可证的增量,不越界宣称)

`question_identity.evidence_semantic_reason()`:keep 豁免引用的行不再只要求"存在且界内",还必须——

1. **承载编号语义**:题号式(`26.`/`一、`)、结构性(模块/任选/考点/汇编/针对训练/X 组…)、或为分节标题行(SECTION_RE 命中,编号语义由分节结构承载);纯 prose/OCR 噪声行 → PENDING_REVIEW;
2. **题号相关性**:非标题引用行的行首题号若与本单元(印刷号 ∪ canonical)完全无关(如 keep 单元引用"26.【答案】"行)→ PENDING_REVIEW。

诚实边界:该检查把"引用存在"升级为"引用内容承载编号语义且题号相关",但**仍不宣称语义证明**——"该行是否真的表明本块使用独立 1-3 编号体系"机器无法判定,保留 PENDING_REVIEW。真实数据复验:batch-C 50 份第二层检查 **0 新增 review**(全部既有 keep 证据确实引用分节标题行)。

### 10.2 对抗语料(`tests/test_identity_adversarial_corpus.py`,16/16)

| # | 攻击面 | 期望 | 结果 |
|---|---|---|---|
| c01 | 正常全局编号 baseline | 无问题 | ✅ |
| c02 | 合法独立模块(keep+标题证据) | PASS | ✅ |
| c03 | 非法跨 section 重号(BUG-22 原型) | FAIL | ✅ |
| c04 | 同 section 重号(keep 不得成万能 bypass) | FAIL | ✅ |
| c05 | 同名 section occurrence 消歧 | PASS | ✅ |
| c06 | section 缺失 | PENDING_REVIEW | ✅ |
| c07/08 | evidence 越界 / 缺失 | PENDING_REVIEW | ✅ |
| **c09** | **evidence 行存在但无编号语义(核心攻击)** | PENDING_REVIEW | ✅ |
| **c10** | **evidence 指向题号无关行(核心攻击)** | PENDING_REVIEW | ✅ |
| c11 | OCR 行号正确但内容错 | PENDING_REVIEW | ✅ |
| c12 | printed 无证据保持 unknown | 不猜测 | ✅ |
| c13 | duplicate unit_id 与身份解耦 | 无碰撞 | ✅ |
| c14 | section 顺序变化重派 | ordinal 确定性 | ✅ |
| c15 | locator 漂移(源截断/span 越界) | FAIL | ✅ |
| c16 | **回填重跑幂等(真实 batch-C)** | 字节一致 | ✅ |

**变异验证**:短路 `evidence_semantic_reason` → 恰好 c09/c10/c11 三条核心攻击用例失败 → 回退。套件 **80 passed + 1 xfailed**。

### 10.3 Phase 3 残留(仍不宣称完成的部分)

- 证据**语义真值**("该行确实证明局部编号体系")本质上需要人工复核或更强的语义判定,PENDING_REVIEW 是显式出口而非缺陷;
- c11 的 OCR 噪声与 c09 同机制拦截,更细粒度的 OCR 内容纠错不属 identity 层职责(归 OCR 质检);
- 三态裁决模型(PASS/FAIL/PENDING_REVIEW)经本轮验证适用于 identity 层,向其它 preprocessing 检查推广属后续决策,不在本轮扩大范围。

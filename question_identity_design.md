# QuestionIdentity 第一性原理设计(R32 / Phase 2 设计评审稿)

> 状态:🟡 设计评审稿,未实现。本文档不改任何生产代码;实现属 Phase 2 实施任务,须在本设计被验收后进行。
> 输入:第五轮审查对 R31(`e3e4e47`)的裁决——Phase 1 PASS,BUG-22 分层关闭(Prompt/QC/迁移 🟢,resolver identity 模型 🟡),下一步优先进入 Phase 2。
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
- 等价表述:section 由 `(source_version, ordinal)` 唯一定位,`start_line/end_line` 提供可回源的 span 证据。二者冗余但互为校验:ordinal 与 span 在确定性构建时必须一致。

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

## 5. 不变量清单(Phase 2 验收将逐条测)

1. `(section_ref, canonical_number)` 在单 manifest 内唯一(同节重复 = FAIL;跨节同号 = LEGAL,warning 级记录);
2. `printed_number` 一经写入永不变化(任何工具改写它 = 违约,测试拦截);
3. `canonical_number` 的每次变化必有 `canonical_basis` + 迁移报告条目;
4. `unit_id` 不参与任何唯一性断言(仅 display alias);
5. SectionLocator 的 ordinal 与 span 在确定性构建下一致;
6. 无 section 降级必须产生显式 warning,禁止静默;
7. 答案区键位只作为 canonical 证据,永不直接成为跨系统 identity。

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

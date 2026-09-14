# Phase P2 阶段章程(phase_p2_charter.md)

> 来源:用户 2026-09-14「DSH 后续开发方向调整裁定」。本文件为裁定落盘,效力高于后续任何轮次的自行扩展冲动。

## 0. 总原则

preprocessing 项目定位:**为 AITutor-V3 提供高质量、可追溯、可消费的数据输入**。
不是建设企业级数据治理平台。当前阶段纪律:

> **够用的可靠性 + 快速业务闭环 > 极致工程完整性。**

> **【2026-09-15 §12 重校准后的一句话定位】** preprocessing = **Source Evidence Producer**:
> 从异构考试文档生产可验证、可定位、可追溯的 Source Evidence(Evidence Manifest),**不负责**解释为最终知识资产;
> V3 负责 Resolve / IR / Gate / Admission。详见 §12。

个人系统优势:数据规模有限 / 使用者单一 / 迭代快 / 可人工纠错。
禁止按百万级数据平台、多人协作 SaaS、企业数据湖的标准继续扩展。

## 1. R67 收口声明

R66–R67 基础治理阶段**到此收口**,已交付且足够支撑长期运行:

- OCR 重复执行风险已消除(manifest processing history + daemon 零重证);
- 文件整理安全性已达标(D5-B 三批 70/70 四闸迁移 + 审计 768 条);
- 基础追溯能力已具备(原始 PDF → OCR 输出 → 处理记录可查)。

## 2. 立即冻结清单(不再深化)

| 冻结项 | 边界 |
|---|---|
| 审计体系扩张 | R68/R69 类审查轮、审查工具自审、审计框架企业化升级,全部暂停(收益已递减) |
| collision 深度治理 | 72 家族只做**事实整理**;禁自动合并 / canonical identity / 复杂版本选择——归宿是 V3 的 Question/QuestionInstance/Material 模型 |
| daemon 工程化增强 | 保持"能运行 + 有日志 + 出错可发现"即可;禁企业级监控 / 服务编排 / 复杂恢复机制(含此前挂起的 worker heartbeat 治理项) |

既有冻结继续有效:canonical identity / semantic dedup / BUG-14-CHAIN / needs_ruling 6 份人工裁定。

## 3. Phase P2 目标:从文件管理转向知识生产

### P2.1 OCR Markdown → Question 单元切分

输入 `xxx_exam.md` → 输出 `QuestionCandidate[]`:

```json
{ "question_no": "1", "stem": "...", "options": [], "materials": [],
  "figures": [], "source_span": {} }
```

不要求一次 100% 正确;要求**规则可解释、错误可发现、可人工修正**。

### P2.2 图片/公式绑定

题干 → 图片 / 表格 / 化学结构式 / 几何图 的绑定,形成 `Question → Material[]`,直接对应 V3。此为项目真正壁垒之一。

### P2.3 输出 V3 Admission 格式

> **【已被 §12 取代(2026-09-15)】** 本节"直接生成 V3 可消费链 Source → … → Question"的方向已作废:
> preprocessing 不再承诺输出 Question IR,改为输出 Source Evidence(Document Evidence Manifest);
> P2.3 更名为 **P3 Evidence Contract Validation**(见 §12.5)。以下原表述仅存档参考。

目标不是漂亮 markdown,而是直接生成 V3 可消费链:

`Source → Resolved Span → Question Candidate → Admission Candidate → Question`

## 4. 开发纪律:先闭环,再优化

```
实现最小版本 → 跑真实 100 份数据 → 发现问题 → 修正
```

禁止:设计完整框架 → 覆盖所有异常 → 所有恢复机制 → 最后才运行。

## 5. 两周目标(2026-09-14 起)

- 输入:100–500 份真实试卷;
- 输出:题目切片 + 图片关联 + 答案区域 + 基础 metadata;
- 验收指标(看结果不看代码量):

| 指标 | 目标 |
|---|---|
| 成功解析试卷比例 | >90% |
| 题目切分准确率 | >90% |
| 图片绑定准确率 | >95% |
| 人工修正时间 | 明显低于手工整理 |

## 6. 已有资产(不重复造轮子)

- `reslice_pipeline.py`:锚点式 LLM 切片(v2.1 嵌套格式,试点 16/16 用户签核);
- `reslice_qc.py`:切片质检 C1–C15;
- `recover_images.py`:43,463 张配图恢复,悬空引用已修;
- `render_lint.py` / `render_preview.py`:渲染质检;
- question identity phase2 / resolver / F1:身份链路(PAC 阶段冻结,P2 先只消费其产出格式,不扩面)。

P2 的实质 = 把既有切片链路推到**真实批量**并输出 V3 可消费结构,用真实错误推动迭代。

## 7. 用户方向裁定(2026-09-15,P2.1 当前方向批准)

> 原文要点转达:P2.1 当前方向批准。继续保持"先闭环再优化"。39 卷批次的核心产物**不是通过率,而是真实错误分布**。禁止新增治理、防线、审计框架。preprocessing 当前目标是输出 V3 Admission 可消费 Question IR,不再扩展为独立数据治理平台。

### 7.1 P2.1 必须回答的三个问题

1. 真实卷能不能被稳定解析?
2. LLM 结构化输出是否达到进入 V3 Admission 的质量?
3. 失败模式是否可分类、可修复?

### 7.2 面向 V3 的度量口径(用户指定,补充进 measure)

| 指标 | 定义 |
|---|---|
| `admission_ready_rate` | 题单元满足:stem 非空 ∧ answer 可定位 ∧ 图片引用合法(计数,P2.2 校验)∧ source anchor 存在(stem_lines 有效)∧ 题型可判断(original_question_type 非空) |
| `sub_question_integrity` | 小问层级完整:composite 题不得丢失 (1)(2)(3) 层级、不得拍平成独立题 |
| 图片绑定基线 | 多少题天然依赖图片 / 多少图片已随切片保留 / 多少无法定位(P2.2 的目标输入) |
| 答案可信度分桶 | exact(明确)/ partial(部分小问)/ inferred(推断)/ missing(缺失)——V3 最忌"LLM 补全一个看似合理但错误的答案",推断必须显式标注 |
| 人工抽检 | 每学科抽卷、每卷随机 10 题,形成 `human_review_390_questions`,估计"自动指标 → 实际质量"偏差 |

### 7.3 P2.1 收口标准(用户版,不追求 100%)

| 指标 | 目标 |
|---|---|
| 卷级成功率 | ≥95% |
| 题目切分准确率 | ≥90% |
| 答案完整率 | ≥90% |
| 图片绑定 | 单独统计 |
| 人工修复时间 | <10 分钟/卷 |

### 7.4 下一轮决策树(只基于 p2_1_measure 结果)

1. 主要问题是切题 → 优化 reslice;
2. 主要问题是答案定位 → 优化 LLM schema;
3. 主要问题是图片 → 进入 P2.2;
4. 主要问题是复杂材料题 → 增加题型策略。

### 7.5 明令禁止

- 不得回到 `P2.1.1 / P2.1.2 / R68 / R69 / R70` 式治理扩展;
- 允许真实错误暴露——没有错误就不知道系统是否真实工作;
- 卷级独立状态(逐卷 `status`,可恢复),禁止"batch failed"整体污染(现状已满足:批内单卷 FAIL 不影响其余卷,`--resume` 可续跑)。

## 8. 用户裁定(2026-09-15):P2.1-b1 收口,进入针对性优化

> 原文要点:P2.1-b1 收口。当前 preprocessing 已达到进入 V3 联调条件。下一轮不扩基础设施,仅针对真实错误分布优化。优先级:① 答案 evidence/schema(26 题,最大确定性收益);② 人工抽检组合题 suspect(71 条,不预设修复方向);③ 图片绑定进入 P2.2(240 题基线)。禁止重新引入 R 系列治理扩展。

### 8.1 路线(P2.1-c → P2.2 → P2.3)

| 轮次 | 目标 | 范围约束 |
|---|---|---|
| **P2.1-c** | 答案定位:answer extraction schema + evidence mapping | 只改答案抽取/evidence;不碰图片/identity/semantic dedup |
| **P2.2** | 图片绑定:Question → Material → Figure 稳定关联 | 输入 = 240 题图片依赖基线;目标不是"所有图片 OCR" |
| **P2.3** | 组合题策略 | 基于 384 题人工抽检结果,不预设修复方向 |

### 8.2 用户指定设计要点

- **Answer Evidence Schema**(替代裸 `answer`):`{source_span, answer_type, confidence, mapping_method}`——答案必须带证据区间与映射方法,符合 V3 Source-first;
- 答案区现实形态至少四类:集中答案表(A)/ 答案与解析混合(B)/ 分节答案串(C)/ 小问分散(D);数学"选择集中 + 解答分散 + 解析混合"最易失败;
- **组合题 suspect ≠ 错误**:大量"材料 + (1)(2)"是正常一题多小问(V3 = 一个 QuestionInstance + 多 role content),不得为提拆分率破坏 material/role 结构;抽检标签 = **KEEP / SPLIT / LOST / UNCERTAIN** 四值,不只记对错;
- 92.31%→95% 卷级不专门追:失败是网络抖动/JSON 异常非 pipeline 结构问题,禁为指标设计复杂机制;
- 节奏:**小批量 → 测量 → 针对性修复 → 接入 V3**。

## 9. 用户裁定(2026-09-15,P2.1-c 收口后):答案域冻结,suspect 人工分类优先

> 原文要点:P2.1 remaining ONLY ① suspect 71 人工分类 ② 根据分类结果决定是否修改 reslice ③ P2.2 图片绑定 baseline。禁止:新治理框架/新审计体系/新生命周期管理/新数据迁移/新身份系统。当前最大风险不是"不够可靠",而是把个人数据整理工具建成企业 ETL 平台。

### 9.1 答案域冻结

- 状态:**Answer extraction: DONE (P2.1), only bug fix**;
- parse_success 97.44% / answer_rate 100% / admission_ready 100%,继续投入收益很低;
- 禁止:更多 answer type / 更多 fallback / 更多 heuristic(V2 规则膨胀陷阱);
- 原则固化:**可信答案 > 完整答案**——`value:null + evidence span` 优于无证据的"合理答案"。

### 9.2 P2.1 剩余优先级(组合题 > 图片)

1. **suspect 71 条人工分类(禁 LLM 自动判断)**:分类结果直接决定 V3 核心模型(Question / QuestionInstance / Material / SubQuestion)——"材料+多小问"到底是 Question+sub_questions 还是多个 Question 共享 Material,是 V3 数据结构正确性的验证点,不是 preprocessing 小问题;
2. 根据分类结果决定是否修改 reslice;
3. P2.2 图片绑定(暂缓合理:图片影响面 ⊂ 组合题对 identity/instance/知识映射/答案粒度的影响面)。

### 9.3 Known Limitation 登记

- **P2.1 known limitation: large prompt provider truncation**——平谷生物 49,485 字符 prompt 重跑 4 连败,其中 3 次固定 `IncompleteRead(59 bytes read)`(字节数一致),判定为 provider/request limit 而非网络抖动;
- 不加重试设施(失败→重试→失败→加成本);P2.1 全部结束后统一决策:prompt 压缩 / 分段请求 / provider 切换,禁局部修。

## 10. 用户裁定(2026-09-15,71/71 人工标注后):答案区间污染 bug fix,直接实施

> 原文要点:71/71 标注推翻"组合题需要拆分"假设——KEEP 52(73%)/UNCERTAIN 0;17 条 SPLIT 的备注语义全部是"答案区混入多余答案",正式更名 **Answer Span Contamination(答案区间污染)**,不得再称"SPLIT 问题"。批准直接进入小修复闭环,不开设计轮。

### 10.1 实证结论(标注结果)

- **组合题拆成多个 QuestionInstance:证据不支持**;**Question + 多小问 + 共享 Material:实证支持**(V3 主体模型方向确认,不需要重构身份模型);
- 污染三形态(同一缺陷族,不拆企业化 BUG 编号):**整表污染**(101 地理 10 单元,整张答案表单行 HTML 被圈进每个单元)/ **相邻串题**(综合英语 4 + 通州地理 1 + 上地英语 3,答案连写行含他题答案)/ **题干混入**(交大英语 U-trans-60-62 题区内联答案块混入 questions_lines;丰台历史 U28 answer_lines 吞入答案区里复述的题干);
- LOST 2 条**分别处理,不建通用框架**:延庆语文 U10 = 复核后判定源卷【答案】块本身如此(第二问为作答指引,完整示例答案在【详解】内已随 explanation_lines 入库),非 answer span 缺陷,不动;交大英语 U-gram-A = **source defect / upstream OCR-source issue**(PDF 有 "3.that",源 md 缺),reslice 无法凭空恢复,**禁止**为它让 LLM 补答案。

### 10.2 批准的修复边界(严格最小)

1. **prompt v2.5 只改答案边界语义**:answer_lines 只圈本单元实际消费的答案证据;共享答案表/连写串允许多 Unit 引用,但不得伪装成某 Unit 私有答案区——`answer_evidence` 增加极轻量 `shared: true|false`,shared=true 必须给逐题明文 value;
2. **最小确定性校验**:题干区含未圈定的【答案】行(题干混入答案)/答案区含本单元题号的题干标题行(答案混入题干)/共享区未标 shared 或 shared 缺 value → issue;重复答案块(同题两处【答案】)未覆盖第二处 → warning(不逼 LLM 切碎答案表制造边界漂移);
3. **问题卷小批重跑**(约 7 卷:SPLIT 所在 5 卷 + KEEP 备注污染 1 卷 + LOST 真实切分缺陷卷复核),**禁全库重跑**;
4. **measure 只看**:contamination 下降 / exact 不受损 / admission 不回退 / sub_question_integrity 变化 / 新 issue——不发明新质量指标。

### 10.3 明令禁止(本轮)

- ❌ 组合题身份重构 / QuestionInstance 拆分策略 / 新治理体系 / 新审计体系 / 新生命周期机制 / 全库重跑 / 为两个 LOST 个案建通用框架;
- ❌ AnswerTable / AnswerGroup / AnswerReference / AnswerOwnership / AnswerMapping / AnswerResolver 等任何"共享答案子系统"——最小模型只有 `answer_evidence{type, lines, value, shared}`;
- 当前 preprocessing 只解决一个问题:**进入 V3 的每个 Question/SubQuestion 能否找到准确且可追溯的答案证据**。

## 11. 用户裁定(2026-09-15,P2.1-e 验收后):P2.1 正式结束,答案域冻结,进入 P2.2

> 原文要点:P2.1-e 闭环质量很好——"没有把答案污染问题扩大成新的数据治理系统,而是用最小 schema 增强解决了实际问题",是 preprocessing 目前最正确的一次迭代方式。contamination 76→3(−96%)且 answer_rate / admission 不降,说明修复方向正确。P2.1 可以正式结束,批准进入 P2.2。

### 11.1 P2.1-e 终局裁定

- **contamination 76→3 = DONE**;剩余 3 例(通州地理 Q19/Q20 C-A2、上地英语 U16 C-A3,两轮同形、确定性不达标、已被校验显式拦截)= **accepted exception,登记 known limitation,禁止继续 prompt 迭代**(76→0 的收益抵不过 v2.6/v2.7 对已稳定卷的不可预测影响);
- `shared` 字段 = **事实表达,不是复杂化**(高中试卷存在"一组题共享答案表"的出版排版事实);同时冻结:不得再扩展 answer_group / answer_owner / answer_relation / answer_resolution graph;
- C-A4(重复答案块降 warning)方向确认:正确方向是"保留共享事实 → 明确消费关系",不是强行切碎源文本;
- LOST 2 条处置确认:延庆语文 U10 非缺陷(answer/explanation 语义分层不得为塞满 answer.value 而破坏);交大英语 U-gram-A = source defect,**不得让 LLM 成为 OCR 修复器**,否则 preprocessing 失去事实边界;
- 误提交历史文件(f8a6d09 经 `git add -A` 扫入):按"不删除、恢复有意不入库状态"处理——`git rm --cached` + .gitignore(RS.MD / r54_f1/f1_report.json / resolver_ref_r52/resolver_ir.json / pac-annotated log / ocr_child_err.log),本地保留;仓库定位是 AI 协作仓库,信噪比重要,陈旧恢复提示词不得再入库。

### 11.2 P2.2 第一轮(图片绑定 baseline)目标——只回答三个问题

1. **图片识别率**:需要图片的题(223 题口径)中,有多少真正持有可解析的图片(source_figure 类事实);
2. **图片归属准确率**:重点不是"OCR 能不能识别图片",而是"这张图是不是属于这个题";
3. **V3 消费方式**:`Question → Material → Figure` 是否成立。

第一轮只做:`PDF → 图片抽取 → 题目绑定 → V3 可引用`。

### 11.3 P2.2 明令禁止

- ❌ 图片治理平台 / 图片语义理解 / 图片自动分类 / 图像知识抽取 / 视觉 embedding / 图谱预设计;
- 保持纪律:小批量 → 测量 → 针对性修复 → 收口,不设计平台。

---

## 12. 用户裁定(2026-09-15,P2.2 收口后):项目定位重校准——preprocessing = Source Evidence Producer

> 裁定背景:P2.2 收口(题面图 lost=0、admission 100%)+ V3 Phase 0 / 0.2-R2 / 0.3-B 真实对接实验共同证明:
> 两项目的真正接口**不是"Question IR",而是"Source Evidence / Resolved Evidence"**。据此重新校准 preprocessing 的终点定义,
> 防止其滑向"半个 V3"或企业化无限建设。本轮是**职责归位 + 减法**,不是新增功能。

### 12.1 项目目标重定义(取代 §3 的"输出 V3 Admission 格式")

**preprocessing 一句话**:

> **从异构考试文档中生产可验证、可定位、可追溯的 Source Evidence,不负责将其解释为最终知识资产。**
> (原文有什么、在哪里。)

**V3 一句话**:

> **将可信 Source Evidence 解析、编译、验证并准入为结构化知识资产。**
> (它意味着什么、能不能进知识库。)

精确版(防止把 preprocessing 误限为纯 OCR):preprocessing 负责**发现并表达"文档中的结构事实"**;
V3 负责把这些结构事实**解释为领域语义**,并决定是否构成可信知识资产。
——"如图所示引用了图片""这个 region 是答案区"本身就是文档结构语义,属 preprocessing;但"这是否构成一道题"属 V3。

**preprocessing 不再承诺输出 V3 Admission 可消费的 Question IR**(§11.2/§3 原表述作废,以本节为准)。

### 12.2 最终分层(Evidence Manifest 是边界,不是 Question IR)

```
原始 PDF / DOCX / OCR
        │
        ▼
┌──────────────────────────────┐
│ AITutors-preprocessing        │
│  Source Evidence Producer     │
│  • source identity            │
│  • unit boundary              │
│  • stem span                  │
│  • options region             │
│  • answer evidence            │
│  • explanation span           │
│  • material                   │
│  • figure reference           │
│  • provenance                 │
│  输出:Document Evidence Manifest│
└──────────────┬───────────────┘
               │ Evidence Manifest(项目边界)
               ▼
┌──────────────────────────────┐
│ AITutors-V3                   │
│  EvidenceAdapter → Canonical  │
│  Resolver → Resolved Evidence │
│  → Semantic IR → Gate →       │
│  Admission → Question/Instance│
└──────────────────────────────┘
```

### 12.3 已实证的 Evidence 类型(P3 冻结候选,只列事实不列 V3 Domain Object)

`source_identity` / `producer_provenance` / `unit_boundary` / `question_numbers` / `unit_type` /
`stem_region` / `options_region` / `answer_evidence` / `explanation_region` / `material_region` / `figure_reference`。

P2 已 CLOSED 的两块证据边界:P2.1 = Question/Answer Evidence Boundary;P2.2 = Figure Evidence Boundary。
provenance 保持轻量:`source_hash` + `manifest_version` + `producer_version` + `generated_at` 即可,**不建**版本图/血缘平台/事件溯源。

### 12.4 四条冻结边界

- **Boundary 1(preprocessing 可做)**:OCR/文档解析、source normalization、question/unit boundary、material boundary、
  answer evidence、figure reference、source span、document structure classification、source-grounded options region/marker discovery、provenance。
- **Boundary 2(preprocessing 不做,禁)**:Question canonicalization、dedup、similarity/family、knowledge mapping、
  canonical Question identity、QuestionInstance identity、Admission/Gate decision、semantic correctness judgment、V3 domain lifecycle。
  **不得因为 preprocessing"知道两道题一样"就在此合并 Question。**
- **Boundary 3(V3 不重猜已存在的 Source Fact)**:preprocessing 已给 `options_region=L45-L52` 时,
  V3 不得再问"options 大概在哪",只在 authoritative region 内做细粒度解析(0.3-B 实测 527/548 的价值所在)。
  **【精确化,见 §13】** Resolver **可以读取并解析 Producer 已声明 Evidence Region 内的 Source**,
  但**不得重新承担 document structure interpretation**(不得扫全 Source 找 option / 重找题目边界 / 重判 material 结构)。
  即:**Resolver may inspect Source, but only inside declared Evidence scope。**
- **Boundary 4(Evidence Contract 当前仍是 Candidate)**:**不改 V3 Frozen L0**;
  走 Candidate → 真实消费验证 → 发现缺口 → 必要时才 normative,避免"实验设计反过来绑架架构"。

### 12.5 阶段改名:P2.3 → P3 Evidence Contract Validation(P4 小批真实 Admission)

- **P3.1 Producer Output Candidate Freeze(措辞按用户裁定:不是"大冻结"/永久 API Contract,而是"确认当前集合")**:
  确认 preprocessing 当前真正承诺输出的 Evidence 集合(见 12.3),只定义事实。**不为"完整"再发明新 Evidence Type**
  (禁加入 canonical option / semantic answer / knowledge node / question identity / similarity / family / difficulty /
  subject knowledge classification——这些属 V3 后半段)。集合已足够启动 P3.2。
- **P3.2 V3 Consumer Compatibility**:用真实产物 + 小批真实卷 + V3 实际 Gate/Admission 验证
  `Manifest → EvidenceAdapter → Resolved Evidence → IR → Gate → Admission`,**不立刻建正式 import API**。
- **P3.3 Gap-driven Repair**:只修真实 gap,**问题在哪层就在哪层修**
  (source span 不可映射→preprocessing;options marker 解析不足→V3 Resolver;Evidence role 不够表达→Manifest schema;IR 表达不了组合结构→V3 IR;Admission policy 不合理→V3 Gate)。
  不能因为 V3 不会消费就让 preprocessing 多做一层,也不能因为 preprocessing 产出方便就污染 V3 Domain Model。
- **P4 Small-scale Real Admission**:小批真实卷 + 实际 V3 Gate + 实际 Admission + Question/Instance 产物验证;
  之后再决定是否扩大数据规模 / 全量重跑 / 正式 import path。

### 12.6 新增功能准入原则(减法纪律)

> **preprocessing 的任何新功能必须回答:它是不是为了生产 V3 当前实际缺失的 Source Evidence?不是就不做。**

- ❌ Question Similarity / 自动题族识别 / 提前把 A/B/C/D 变成最终 IR;
- ✅ V3 消费发现 figure provenance 缺 source identity / 某类 material 无明确 boundary / 新的 options region 表达方式。

### 12.7 长期仓库形态:暂不裁定(取代任何"preprocessing 进 V3 生产模块"的表述)

> **不规划仓库合并。** 当前只验证 Evidence Producer → V3 Consumer 的稳定接口;
> 只要跨仓库消费成本可接受,保持两仓库独立。未来合并/嵌入/独立**依据真实维护成本决定,不提前设计**
> (不设计 monorepo / domains/preprocessing / internal package migration / service extraction)。
> 理由:preprocessing 仍高频实验(prompt/OCR/parsing/数据集验证),V3 是稳定 Domain Model,变化节奏不同;
> 当前实验只证明"preprocessing 的 Evidence 可被 V3 消费",**未证明**"OCR/reslice/QC 应搬进 V3 仓库"。

### 12.8 本轮明令禁止(P3 阶段,叠加既有冻结)

- ❌ 正式企业级集成:Import Service / Import API / Message Queue / Workflow Engine / Task Scheduler / Distributed Worker;
- ❌ 复杂治理体系:Evidence Event Store / Contract Registry / Schema Governance Platform / Version Graph / Producer Registry Service;
- ❌ 因 38 卷验证成功就数千卷全量重跑(等 V3 Consumer Path 基本稳定再定,避免 V2 式"上游大量跑、架构一改全返工");
- ❌ preprocessing 生产最终 Question(manifest → LLM → Question JSON → 直接入库),这会破坏已验证的 Evidence Producer → Canonical V3 Consumer 边界。

---

## 13. Boundary Decision Record(2026-09-15,V3 Phase 0.3-B 复盘后)——Resolver 的 Source 访问边界

> 背景:V3 Phase 0.3-B 实测 option resolution `527/548 = 96.2%`,但高风险歧义层抽样 `0/10` 正确。
> 用户裁定纠正一个"下过头"的结论:**不是"Resolver 不能读 Source",而是"Resolver 不得重新解释文档结构"。**
> 本轮**不改代码、不改 V3 Frozen L0、不增强 Resolver、不冻结 Phase 0.3-B 最终 Contract**,只钉死边界原则。

### 13.1 一句话架构边界(两仓库共同遵守)

> **Preprocessing determines where and what structural evidence exists;**
> **V3 determines how that bounded evidence resolves into canonical domain evidence and whether it is admissible as knowledge.**
>
> 中文:**preprocessing 负责发现并声明文档中的结构证据及其位置;V3 负责在这些有界证据内进行确定性解析,将其转换为 canonical evidence,并最终决定它能否成为可信知识资产。**

关键不在"Resolver 能不能读 Source",而在:**谁拥有对 Source 结构的解释权,以及 Resolver 的解释活动允许发生在什么范围内。**

### 13.2 Evidence Region ≠ Evidence(本轮钉死的核心概念)

- Producer 给 `options_region=[85,92]` 只声明"第 85–92 行是 options 相关 Evidence",**没有**说 `A=85 / B=87 / C=89 / D=91`;
- 但 V3 IR 需要 per-option evidence,故中间必有 `Evidence Region → Evidence Resolution → Resolved Evidence` 一跳;
- **这一跳放 V3 Resolver 是合理的**,否则等于把 `_region → per-option` 从 V3 偷搬到 preprocessing,违背 §12(Producer 不做第二个 V3)。

### 13.3 Evidence Region / Evidence Resolver 定义

- **Evidence Region**:preprocessing 在 Source 上声明的、有明确边界的事实区域,回答 **"Where is the evidence?"**;
  **不必**回答 "What is the final canonical evidence structure?"。
- **Evidence Resolver**:V3 中基于 Producer 已声明 Evidence Region,对该 Region 内 Source Evidence 做**确定性解析**、
  形成 V3 所需 canonical evidence spans 的组件;回答 **"How does this bounded evidence become canonical evidence?"**,
  **不回答** "Where is the evidence in the document?"。

### 13.4 Resolver 绝对边界表

| 行为 | 判定 |
|---|---|
| 读取声明的 `options_region` 对应 Source lines | ✅ |
| 在 Region 内寻找真实 A/B/C/D marker | ✅ |
| 根据 Region 内 marker 确定 option span | ✅ |
| 根据 Region 内相邻结构确定边界 | ✅ |
| 检查 marker 顺序/重复/缺失 | ✅ |
| 检查 span 是否越过 Region | ✅ |
| 在整个 Source 中搜索 options | ❌ |
| 重新寻找题目边界 | ❌ |
| 重新识别 material/question structure | ❌ |
| 根据题型制造 A/B/C/D | ❌ |
| 根据 expected count 补造 option | ❌ |
| 按长度均分 Region | ❌ |
| 依赖学科知识消歧(如"F 是氟元素故非选项") | ❌ |
| 无证据猜测缺失 marker | ❌ |

**核心约束一句话:Resolver may inspect Source, but only inside declared Evidence scope。**

### 13.5 Resolver 的三种合法解析 + 一种出口(deterministic ≠ 只做 lexical)

> **不要把"Resolver 必须 deterministic"误解为"Resolver 只能做纯 lexical parsing"。**
> 只要判断能被限定在 **Region 内 Source Evidence + 已冻结规则** 上,仍属 deterministic resolution。

- **lexical resolution**:字符模式(`A.`/`B)`/`(C)`);
- **structural resolution**:Region 内 `A. … B. … C. … D. …` 的确定性切分;
- **deterministic contextual resolution**:Region 内相邻结构/顺序推边界;
- **ambiguity detection 出口**:需真正语义知识才能判断(如 L85 `F` L87 `B` 究竟是元素还是选项)→ **`pending_review`**,
  **不"智能判断"**。

**Rule(用户五条,固化)**:
1. Producer declares regions, not interpretations(不得直接决定 `A=line85-86`,除非未来 Contract 明确增能力);
2. Resolver may inspect Source, **only inside declared Evidence scope**;
3. Resolver may resolve, but may not reinterpret(需语义→pending_review);
4. **Uncertainty must decrease resolution, never decrease truth**——宁可 unresolved 不可错误 resolved
   (核心是 `P(correct|resolved) → 1`,**不是** `P(resolved) → 1`;与高风险层 0/10 的发现一致);
5. Producer 与 Resolver 不得重复 structural intelligence(需理解 DOM/表格/视觉布局/题目语义→优先 preprocessing;
   仅在已定 Region 内做确定性边界解析→可属 Resolver)。

### 13.6 越界判定 + "回到 preprocessing"的归因

- **读取 Region 内 Source ✅ / 解析 Region 内 option span ✅**;
- **扫全 Source 找 option ❌ / 重找题目边界 ❌ / 学科语义消歧 ❌ / 猜测缺失 marker ❌ / 制造不存在的 option ❌**;
- **HTML DOM 解析归属:暂不裁决(不冻结实现,只冻结原则)**——真正问题不是"HTML 谁解析",而是
  **解析结果有没有改变 Evidence ownership / boundary interpretation**:
  - 仅在 Region 内利用已可见的 Source representation 定 A 的 span → 没问题(Resolver);
  - 必须遍历整个 DOM / 判断 td 属于哪题 / 建视觉布局 / 推 option ownership → 已重新承担 document structure
    interpretation → 回 preprocessing。
- **应回到 preprocessing 的失败类型**:HTML DOM 未正确转化成可定位 Source Region、视觉结构丢失、
  题目/材料边界错误、role region 错误、source mapping 错误。

### 13.7 Phase 0.3-B 重新命名 + 指标口径(不冻结最终 Contract)

- **Phase 0.3-B 更名为「Evidence Resolution Boundary Discovery」**(不是 Final Resolver Contract)。
  它证明的是三个**架构事实**:① Producer 能提供足够 Evidence Region → ② V3 Resolver 可在 Region 内恢复
  canonical sub-evidence → ③ 剩余失败暴露的是 resolution boundary / source representation 问题。
- **三个数字必须严格分开表述**(不得混称 "option resolution quality"):
  - `527/548 = 96.2%` = **当前 Canonical Resolver 在现有 Producer Evidence Region 上的 resolution coverage**;
  - `103/113 = 91.2%` = **observed sampled correctness**;
  - `517/527 ≈ 98.1%` = **sampling 口径下 resolved population 的 estimated correctness**。
- **高风险层 0/10 = 一个 detector precision failure class**,比 96.2% 本身更重要。
- 现在可冻结**架构方向**,**不冻结最终 Contract**(Region → canonical option evidence 的边界规则尚未闭合)。

### 13.8 下一步(不写代码):Failure Classification → Boundary Decision Record 闭合

对 0.3-B 现有失败(16 `no_labels` / 5 `incomplete` / 10 高风险歧义样本 / HTML table / `<div>A.</div>` /
单行首个 marker 无标点 / chemical formula false positive)按五类**重新归因**:
**A.** Producer Region 不完整 / **B.** Source representation 不足 / **C.** Resolver deterministic rule 不足 /
**D.** 真正需要 semantic interpretation / **E.** Source 本身缺陷。
**不为提高 96.2% 去修 resolver**,先问"这个失败证明哪一层缺失了什么能力"。

### 13.9 P3.2 负面验收标准(新增,防止架构退化)

> **Consumer Compatibility 必须通过,但不得以复制 preprocessing document-structure intelligence 为代价。**
> 允许 `Region → canonical evidence`;**不允许** `Manifest → V3 再造一套 document parser / HTML question detector`。
> 即使最终 Admission 成功,只要 V3 为了处理 Manifest 又长出第二套 preprocessing,即判定**架构退化**。

P3.2 只看四类指标:**A. Evidence coverage**(required vs available)、**B. Resolution**(resolved/unresolved/ambiguous)、
**C. Gate**(auto_approve/pending_review/rejected)、**D. Root cause**(失败发生在 Producer/Source representation/
Adapter/Resolver/IR/Gate 哪一层)。**不以最终 Admission 率为核心 KPI。**

### 13.10 收敛期停止条件

> **除非 V3 的真实消费实验暴露新的 Source Evidence 缺口,否则 preprocessing 不再增加能力。**

当前暂停项(等 P3.2 结果):优化 option detector / 增加 marker regex / 追 96.2% / 处理 21 pending /
扩大 P2.2 / 设计 import API / 讨论仓库合并 / 增加 provenance·governance / 全库重跑。
preprocessing 项目已从"不断增加能力"进入**收敛期**——停止条件是明确的,不是人为宣布"做到这里"。

---

## 14. 跨仓库协调基线对齐 + DSH 源侧归因(2026-09-15)

> 来源:用户下发《Evidence Boundary 协同架构与下一阶段工作报告》(v2026-09-15),DSH = 本仓库(AITutors-preprocessing),
> Claude = AITutors-V3 仓库。本节是 DSH 对该协调基线的**对齐确认 + 源侧归因执行**。
> **本轮零代码、零 prompt 变更、零重跑**,严格遵守 §13.10 收敛期停止条件。

### 14.1 DSH 对协调基线的对齐确认

- 该报告的架构定位 = §12(Source Evidence Producer)+ §13(Resolver bounded Source access)**完全一致**,DSH 无需推翻任何既有结论;
- DSH 在此**确认接受**共同边界模型:① Producer declares regions, not interpretations;② Resolver may inspect Source, only inside declared Evidence scope;③ may resolve but may not reinterpret;④ Uncertainty must decrease resolution, never decrease truth;⑤ 两侧不重复 structural intelligence;
- **协同纪律**:DSH 任何新结论必须先与本边界模型对照;若与 Claude 侧冲突,**先报告冲突,不自行修改另一方职责**。
- DSH-1/2/3/6/7/8(定位收敛为 Source Evidence Producer、核心输出清单、保留 `options_region` 不强推 per-option、
  不反向固化 V3 实现为 Contract、不扩张到 Question/IR/Gate/Admission、新字段一律 candidate)——**已由 §12/§13 落地,本轮复核确认成立**。
- **DSH-4(失败案例逐例归因)为本轮唯一实质执行项**,见 §14.2–§14.4。

### 14.2 DSH-4 的证据边界声明(不凭空归因)

- V3 Phase 0.3-B 的 **21 pending(16 no_labels + 5 incomplete)与 10 高风险样本的逐例清单属 V3 侧证据,本仓库不持有**;
- 按 Rule"无法证明 → 不臆断",DSH **不对不存在于本仓库的 case 做 unit 级归因**;
- DSH 侧改用**本仓库真实持有的证据**(b2 8 卷 manifest + 源 md)做**源侧可自证归因**,回答 Producer 层:
  *每个 choice-type unit 的 options_region 是否完整、Region 内源侧呈现方式如何*——为 A/B/C/D/E 五类归因提供 Producer/Source 侧输入。

### 14.3 DSH 源侧归因实测(b2 8 卷,227 choice-type units,prompt 全 v2.7)

探针(只读,gitignored `.pytest_work/bdr_attribution.py`、`bdr_a_class.py`)**不做 option resolution、不判定 A=哪行、不制造 per-option spans**,只读 manifest + 源行。

| 归因类 | 实测 | 逐例定性 | 归属层 |
|---|---|---|---|
| **A. Producer Region 不完整(真缺口)** | **1** | 生物汇编 **Q51**:options 真实存在但为 **HTML `<table>` 表格型选项**(A/B/C/D 在 `<td>` 单元格内,非 `A.`/`(A)` 行文本),v2.7 未圈入 → `options_lines=null` | **A**(Producer 圈定未覆盖表格版式) |
| A′(非本轮缺口) | 10 | 101 地理 U2-3/U4-6/…/U52-55,全部 `composite_question`(`questions_lines` 有、`options_lines` null),源 L11–27 子题选项为标准 `A.` 文本、真实存在 | 组合题子选项圈定**已冻结**(§10.3 身份重构禁令),**不在本轮修复面** |
| **B. Source representation 不足** | 2 | 101 地理 **Q13 / Q37**:选项为**图片型**——A/B/C/D 是四张 `<div>` 居中图,标记 `<div>A</div>` 独立成行 | **B**(Region 已声明,但"标记↔图"边界属视觉/图片语义),按 §11.3 图片语义理解**铁令冻结** |
| C. Resolver deterministic rule 不足 | 0 | DSH 侧不持有 Resolver 执行证据,不由 DSH 判定 | (留 Claude 侧) |
| D. 真需 semantic interpretation | 0 | 同上;图片型 Q13/Q37 若需"哪张图配哪个字母"属 D,但已被 §11.3 冻结不碰 | (留 Claude 侧) |
| E. Source 本身缺陷 | 0 | 8 卷源文件均存在、可读,B 类"有 region 但源缺失"= 0 | — |

**其余 214/216 region 内含 canonical 标记(`(A)`/`A.`/`A、`)**,Producer 圈定对常规行文本选项成立。

### 14.4 DSH 源侧归因结论 + 处置(全部不修)

- **本轮 DSH 修复数 = 0**。三个非平凡 finding 全部落在已冻结边界内:
  - **Q51 表格型选项**(真 A 类缺口):**登记为 candidate known limitation,不修**。理由:修它 = 扩 prompt 覆盖表格版式 = §13.10 收敛期停止条件明令暂停项("优化 option detector");且属 `Region → per-option` 边界问题,应先由 P3.2 真实消费实验确认是否构成 V3 实际 Source Evidence 缺口,再决定是否解冻。
  - **Q13/Q37 图片型选项**(B 类):**登记不修**,§11.3 图片语义理解禁令冻结。
  - **10 条 composite**(冻结):不动,§10.3。
- **对协调基线的回执**:DSH 侧**未发现任何"必须 Producer 现在补 per-option / 补 observed option labels / 补 expected_option_count"的证据**——与报告 §19/§20 结论一致,`options_region` 仍是充分的最小 Evidence handoff。
- **下一步交还 P3.2**(V3 Consumer Compatibility):由 V3 用真实 b2 产物走完 `Manifest → EvidenceAdapter → Canonical Resolver → Resolved Evidence → IR → Gate → Admission`,采集四类指标 + 执行 §13.9 负面验收。DSH 在 P3.2 结果暴露**新的 Source Evidence 缺口**前,不增加任何能力。

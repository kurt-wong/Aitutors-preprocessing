# Phase P2 阶段章程(phase_p2_charter.md)

> 来源:用户 2026-09-14「DSH 后续开发方向调整裁定」。本文件为裁定落盘,效力高于后续任何轮次的自行扩展冲动。

## 0. 总原则

preprocessing 项目定位:**为 AITutor-V3 提供高质量、可追溯、可消费的数据输入**。
不是建设企业级数据治理平台。当前阶段纪律:

> **够用的可靠性 + 快速业务闭环 > 极致工程完整性。**

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

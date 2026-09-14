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

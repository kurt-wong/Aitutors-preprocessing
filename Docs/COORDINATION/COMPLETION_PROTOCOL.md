# Agent Completion & Synchronization Protocol(固化版)

> 来源:Owner 2026-09-15 聊天原文(完整原文见 log.md 当日轮次)。canonical ledger 固化,两侧 Agent 全部任务适用。
> 效力:Owner 裁定(DEC-014)。冲突时以 Owner 聊天原文为准。

## 0. 职责定位

- Review/审计 Agent 职责 = **寻找设计失败模式**,不是重新设计;
- 发现问题必须指出:①哪个假设失败;②哪个证据不足;③哪个问题需要设计方回答;
- 所有 EB 项目中 Agent 同时负责维护 **"Owner 可裁决性"**:发现隐藏假设 / 架构冲突 / 关键证据遗漏时,**必须主动在 Completion Report 建立反馈项**,不等下一轮交互。

## 1. Completion Report 七章节(强制)

1. **Executive Summary**(≤10 行):完成什么 / 阶段状态 / 是否达标 / 可否进下一阶段。
   `STATUS: READY | BLOCKED | PARTIAL` · `CURRENT_PHASE:` · `OWNER_ATTENTION_REQUIRED: YES | NO`
2. **Deliverables** 表:`| Item | Location | Status |`(文件/commit/文档位置/测试结果)。
3. **Evidence Summary**,四级分类,禁混写:
   - **OBSERVED**:已存在事实(来源 + 文件位置 + 行号/章节);
   - **VERIFIED**:已验证结论(必须说明验证方法);
   - **INFERRED**:推导(必须给出推导链);
   - **PROPOSED**:未冻结建议。
4. **Owner Decision Points**(必须存在,没有则明写 `NO OWNER DECISION REQUIRED`):
   `D-00x: Question / Available options(A/B…含 Impact)/ Recommended direction / Reason`
5. **Risks & Unknowns**:`RISK-ID / Description / Severity(CRITICAL|HIGH|MEDIUM|LOW) / Why it matters / Blocked component`
6. **Cross-Agent Feedback**(强制项):`Feedback to Claude` 或 `Feedback to DSH`,
   `TARGET / Issue / Evidence / Expected response / Deadline-Next checkpoint`;禁"请注意""可能存在问题"式模糊反馈,必须明确要对方回答什么。
7. **Recommended Next Action**:Owner / Claude / DSH 各自的下一步。

## 2. 跨 Agent 同步规则

- Claude 完成 Design → 主动同步:`HANDOFF TO DSH: Please verify / Potential weak points`(Review Targets + 未证明假设 + 希望被攻击的位置);
- DSH 完成 Review → 主动同步:`HANDOFF TO CLAUDE: Required Revision / RDQ-00x: Problem / Evidence`(修订要求 + 必须回答的问题 + 阻断项)。

## 3. 禁止行为(任务完成后)

❌ 只报 commit hash ❌ 只报测试通过 ❌ 只说"已完成" ❌ INFERRED 冒充 FACT ❌ PROPOSED 冒充 DECISION ❌ 默认 Owner 理解隐藏风险 ❌ 等待 Owner 主动发现问题

## 4. 严重程度标记(必须使用)

- `## BLOCKER`:没有解决不能进入下一阶段;
- `## WARNING`:可以继续,但 Owner 必须知道;
- `## NOTE`:记录信息。

## 5. 最终完成状态(每次任务结束必须选择其一)

- `[ ] COMPLETE_READY_FOR_NEXT_PHASE`
- `[ ] COMPLETE_WAITING_FOR_REVIEW`
- `[ ] BLOCKED_OWNER_DECISION_REQUIRED`
- `[ ] BLOCKED_DESIGN_REVISION_REQUIRED`
- `[ ] BLOCKED_EXTERNAL_DEPENDENCY`

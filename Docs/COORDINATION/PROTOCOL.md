# Cross-Agent Coordination Protocol v0.1

> 版本:v0.1(2026-09-15)· 性质:**工作协调层(Work Coordination Layer),不是架构权威层**
> 适用:DSH(AITutors-preprocessing)× Claude(AITutors-V3)跨仓库协作
> 铁律:本层**永远不产生** L0/L1/L2 约束。架构权威仍在各仓库既有治理(`governance/` charter、V3 L0/L1/L2 体系)。

## 0. 设计原则(与两仓库哲学同构)

**Source 是事实源;Evidence 是可验证证据;Decision 才产生约束;Code 是 Decision 的实现。**

跨 Agent 协作遵循同一链条:

```text
Agent 行为 → Git Evidence → Coordination Ledger → (人工/L2) Decision → 另一 Agent 感知
```

两个 Agent **不共享记忆,只共享事实**。任何一方的推理不得直接成为另一方的输入——中间必须隔着 Git 里可验证的 Evidence。

## 1. 目录结构(本仓库 = canonical ledger)

```text
Docs/COORDINATION/
├── PROTOCOL.md      # 本文件,协议定义
├── CURRENT.md       # 人 + Agent 快速阅读的当前快照
├── state.yaml       # 机器可读状态(tests/test_coordination_state.py 钉住 schema)
└── HANDOFFS/
    └── YYYY-MM-DD-<from>-to-<to>-NNN.md   # 结构化工作交接(非聊天记录)
```

## 2. 单主规则(v0.1 关键裁定,防双主冲突)

- **canonical ledger = 本仓库(prepo,D.S.H 维护)**。EB ID、FACT ID、DEC ID 只由此 ledger 单调分配,禁止两侧各自编号;
- V3 侧 handoff **先 commit 进 V3 自己的仓库**,DSH 在同步时**原样镜像**入 `HANDOFFS/` 并更新 `state.yaml`(镜像文件头注明 V3 侧 commit);
- 冲突处理:两侧结论冲突时,**先登记 DISPUTED,报告给用户裁决**——任何一方不得自行修改对方职责或覆盖对方事实行。

## 3. 共享状态机(每个跨 Agent 工作项 EB-NNN 只能沿此推进)

```text
DISCOVERED → EVIDENCED → ATTRIBUTED → PROPOSED → DECIDED → IMPLEMENTED → VERIFIED → CLOSED
```

**禁止跳级**(逐条,机器可校验 status 值但语义由本协议约束):

| 当前态 | 禁止直接到达 |
|---|---|
| DISCOVERED | IMPLEMENTED / DECIDED / CLOSED(无证据不得决策) |
| EVIDENCED | DECIDED / CLOSED(有证据未归因不得决策) |
| ATTRIBUTED | IMPLEMENTED(归因未提案不得动代码/契约) |
| PROPOSED | IMPLEMENTED / CLOSED(提案未裁决不得实施) |
| DECIDED | CLOSED(决策未实施不得关闭) |
| IMPLEMENTED | CLOSED(实施未重新产生 Evidence(复测)不得关闭) |

**状态语义**:
- `DISCOVERED` 现象被任一侧观察到,尚无 Git Evidence;
- `EVIDENCED` 已有可验证证据(具体 commit + 具体文件 + 可复现口径);
- `ATTRIBUTED` 已按 A(Producer)/B(Source representation)/C(Resolver rule)/D(Semantic)/E(Source defect)/F(Unknown)完成归因;
- `PROPOSED` 已有 Proposal 文档(含预期收益 + 边界 + 禁止事项),等待人工/L2 裁决;
- `DECIDED` 人工/L2 已裁决(记录权威来源);
- `IMPLEMENTED` 按 Decision 完成实现;
- `VERIFIED` 实现后重新产生 Evidence(复测通过);
- `CLOSED` 全链闭合归档。

## 4. Claim → Evidence → Decision 协议

任何跨仓库结论**不得**直接写成主张(如"Resolver 应该支持 HTML table"),必须分级:

```yaml
CLAIM: <EB-NNN>.<序号>
statement: <可证伪的陈述>
observed: <直接观察到的事实>
evidence: <repo + commit + 文件路径 + 复现口径>
confidence: OBSERVED | INFERRED | REPORTED
impact: <影响哪个边界问题>
decision: UNDECIDED | ACCEPTED(附权威来源) | REJECTED(附理由)
```

`confidence` 语义:**OBSERVED** = 本侧亲自跑过测试/读过源文件;**INFERRED** = 从证据推断但未直接验证;**REPORTED** = 对侧报告、本侧未复核(REPORTED 不得单独作为 DECIDED 依据)。

## 5. Agent 启动同步流程(每次开工前必执行,7 步)

```text
1. git fetch + 读 Docs/COORDINATION/state.yaml
2. 读 Docs/COORDINATION/CURRENT.md
3. 读最新 HANDOFFS/ 交接文件
4. 核验交接中引用的 commit / 证据文件真实存在(不采信未验证引用)
5. 只在 OPEN 状态的 EB 项上工作
6. 完成后更新 state.yaml + 写出自己侧的 handoff
7. commit + push(CI 绿为收口条件)
```

## 6. 明令禁止(本协议层)

- ❌ 实时双向消息 / Agent 直接互调 API / 无限讨论线程;
- ❌ 把 Coordination Ledger 内容当作 L2 Decision(要升 L2,走各仓库既有治理路径);
- ❌ 任一 Agent 修改对方仓库文件 / 对 EB 项跳级推进 / 用 REPORTED 冒充 OBSERVED;
- ❌ 为本层建 orchestration 平台 / 服务 / 数据库——**只有 4 个纯文本文件**;
- ❌ 合并两侧不同语料的统计分母(见 state.yaml `prohibitions`)。

## 7. 版本演进

v0.1 只承诺:4 个文件 + 单主规则 + 状态机 + Claim 协议 + 启动 7 步。任何扩展(自动校验、跨仓镜像 bot、更多 Agent)必须先作为 EB 项走完状态机,**不得静默升级协议**。

# CURRENT — 跨 Agent 协调快照(人 + Agent 快速阅读)

> 机器可读状态见 `state.yaml`;协议见 `PROTOCOL.md`。本文件是镜像快照,**权威以 state.yaml 为准**。
> 更新:2026-09-15 · canonical ledger = kurt-wong/Aitutors-preprocessing(main)

## 当前工作项:EB / Evidence Resolution Boundary Discovery

| Agent | 仓库 | 角色 | 最近动作 |
|---|---|---|---|
| **DSH** | kurt-wong/Aitutors-preprocessing | Source Evidence Producer | `6b9b5b3`:跨侧互证入册(§14.5);`3f9d32b`:源侧归因 227 choice units,修复数 0 |
| **Claude** | kurt-wong/AITutors-V3 | Resolution + IR + Gate + Admission | Claude-2 bounded access 审计 + Claude-3 31 case 归因(B14/C8/D6/F1,A=0) |

## 共享事实(摘要,id 以 state.yaml 为准)

- `527/548 = 96.2%` 是 **resolution coverage,不是 correctness**(FACT-001);
- 三数字分开:96.2% coverage / 91.2% observed sampled / 98.1% estimated(FACT-002);
- 高风险层 0/10 = detector precision failure class(FACT-003);
- DSH 源侧归因:A 真缺口 1(Q51 表格型)/ B 图片型 2 / composite 10(冻结),**修复数 0**(FACT-004/005);
- **跨侧互证**:HTML table / div 图片型选项 = 系统性 B 类 Source representation 缺口,**跨语料(b1 38 卷 vs b2 8 卷)case 零重叠但 pattern 相同**(FACT-006/007);
- 两侧一致:**options_region 是充分的最小 Evidence handoff,无 Producer 补 per-option 的证据**(FACT-005)。

## 开放问题(EB 项)

| ID | 问题 | Owner | 状态 |
|---|---|---|---|
| EB-001 | HTML table 型选项:Producer 扩圈定 vs Resolver Region 内解析 | joint | ATTRIBUTED |
| EB-002 | 图片型选项 `<div>A</div>`+图:标记↔图边界归属(§11.3 冻结线) | joint | ATTRIBUTED |
| EB-003 | `region_upper=None` bounded access 越界风险处置 | v3 | EVIDENCED |
| EB-004 | P3.2 真实消费实验(四类指标 + 负面验收) | v3 | DISCOVERED(待用户放行) |

## 当前禁止(两侧共同)

不改 V3 Frozen Spec / 不冻结 Producer Contract / 不修 Resolver heuristics · 不为 96.2% 修补 · 不合并两侧语料分母 · REPORTED 不冒充 OBSERVED · 不建互调平台 · Coordination ≠ L2。

## 接收方启动动作

按 PROTOCOL §5 七步:fetch → 读 state.yaml → 读本文件 → 读最新 HANDOFF → 核验证据引用 → 只做 OPEN 项 → 更新 + handoff + commit + CI 绿。

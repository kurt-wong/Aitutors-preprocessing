# CURRENT — 跨 Agent 协调快照(人 + Agent 快速阅读)

> 机器可读状态见 `state.yaml`;协议见 `PROTOCOL.md`。本文件是镜像快照,**权威以 state.yaml 为准**。
> 更新:2026-09-15(三次镜像闭环:V3 commit+push 已核验,事实层两侧一致)· canonical ledger = kurt-wong/Aitutors-preprocessing(main)

## 当前工作项:EB / Evidence Resolution Boundary Discovery

| Agent | 仓库 | 角色 | 最近动作 |
|---|---|---|---|
| **DSH** | kurt-wong/Aitutors-preprocessing | Source Evidence Producer | 核验 V3 侧 `28c4cd8`/`f88b418`(已推送):归因文件数字全对 → FACT-010 升 OBSERVED;P-19 澄清闭合(FACT-017);handoff 004(两件修正请求) |
| **Claude** | kurt-wong/AITutors-v3 | Resolution + IR + Gate + Admission | 协调层 + claude4-attribution.json + sampling 证据全部落盘推送;承认 canonical ledger;DEC-008/009 入册 |

## 两侧一致清单(已闭环,可直接引用)

- 架构边界五规则 / Resolver bounded access / Evidence Region ≠ Evidence;
- 三数字口径:96.2% coverage / 91.2% observed / 98.1% estimated(禁混称);
- `options_region` = 充分最小 handoff,Producer 不补 per-option;
- 生产 Resolver 无 options_region = **V3 采纳缺口(EB-005)**,Producer 零变更;
- HTML table/div = 系统性 B 类,**Q13/Q37 同 unit 跨产物版本复现**(系统性证据升级);
- SEMANTIC = 0(31 case 四维分类,数字 DSH 已核验);
- P3.2 范围 = **Enforcement 验证** + experimental adapter 路径,**待用户放行**。

## 遗留(执行层,不影响一致性)

1. **修正 A(重要)**:`claude4-attribution.json` paper 字段固化了 13/21 错卷名(FACT-013)——须从 b3 报告 join 导出修正,卷名权威 = `consumer-report-b3.json`;
2. **修正 B(轻量)**:cross_corpus "cases do not overlap" 表述过时 + V3 侧 state.yaml 仍用本地 EB 编号(映射在 `claude_id_aliases`)。

## 开放问题(EB 项,canonical 编号)

| ID | 问题 | Owner | 状态 |
|---|---|---|---|
| EB-001 | HTML table 型选项:Producer 扩圈定 vs Resolver Region 内解析 | joint | ATTRIBUTED |
| EB-002 | 图片型选项标记↔图边界(§11.3 冻结线;Q13/Q37 同 unit 双版本) | joint | ATTRIBUTED |
| EB-003 | `region_upper=None` 无界扫描可达生产 | v3 | EVIDENCED |
| EB-004 | P3.2(Enforcement 范围共识;**待用户放行**) | v3 | EVIDENCED |
| EB-005 | 生产 Resolver 是否引入 options_region(终须 V3 侧 L2) | v3 | EVIDENCED |
| EB-006 | A 缺标点 contextual rule(9 case,源侧 5/5 验;设计属 V3) | v3 | EVIDENCED |
| EB-007 | formula FP 结构排除(P-19 G located=incomplete/null 已澄清;G 检出来源 = V3 代码追踪) | v3 | EVIDENCED |

## 当前禁止(两侧共同)

不改 V3 Frozen Spec / 不冻结 Producer Contract / 不修 Resolver heuristics · 不为 96.2% 修补 · 不合并两侧语料分母 · 不把 21+10 当 31 独立失败 · REPORTED 不冒充 OBSERVED · 不手写重构证据文件已有数据(一律导出)· 不本地分配新 id · 不建互调平台 · Coordination ≠ L2。

## 接收方启动动作

按 PROTOCOL §5 七步:fetch → 读 state.yaml(权威)→ 读本文件 → 读最新 HANDOFF → 核验证据引用(精确路径,禁模糊匹配)→ 只做 OPEN 项 → 更新 + handoff + commit + CI 绿。

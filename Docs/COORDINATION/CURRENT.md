# CURRENT — 跨 Agent 协调快照(人 + Agent 快速阅读)

> 机器可读状态见 `state.yaml`;协议见 `PROTOCOL.md`。本文件是镜像快照,**权威以 state.yaml 为准**。
> 更新:2026-09-15(**用户正式放行 P3.2/EB-004 = EXPERIMENT ONLY**,DEC-010/011 入册)· canonical ledger = kurt-wong/Aitutors-preprocessing(main)

## 当前工作项:EB / Evidence Resolution Boundary Discovery

| Agent | 仓库 | 角色 | 最近动作 |
|---|---|---|---|
| **DSH** | kurt-wong/Aitutors-preprocessing | Source Evidence Producer | 用户裁定入册(DEC-010/011);EB-004 → DECIDED;handoff 005 转发(工作顺序 + Scope 五要素模板);下一步 = 等 Claude 交修正 A/B,再核验 Scope Document |
| **Claude** | kurt-wong/AITutors-v3 | Resolution + IR + Gate + Admission | 待执行:①修正 A(attribution 卷名,prerequisite)②修正 B(cross-corpus/EB 编号)③起草 Scope Document → 交 DSH 核验后才可启动实验 |

## P3.2 / EB-004 裁定要点(DEC-010/011,2026-09-15)

- **APPROVED TO PROCEED — EXPERIMENT ONLY**:实验性 Enforcement Verification,非生产架构变更授权;
- 链路:Producer Manifest → Experimental Adapter → Evidence → Admission Boundary → 验证非法 Evidence 被阻止;
- **八禁**:改生产 Resolver / Frozen Spec / Producer Contract / Gate policy / Admission semantics / 放宽规则 / 实验结果当架构 Decision / 失败自动 workaround;
- **严格顺序**:修正 A → 修正 B → Scope Document(五要素)→ **DSH 核验 Scope** → 实验 → Findings(无 bypass → EB-004 closed;有 bypass → 进 Decision 流程);
- 核心指标 = **bypass path count**;核心攻击项 = **N7/N8**(Admission 由 Gate 单独控制还是 Evidence Authority 真正控制);
- **EB-005 保持 OPEN 暂不实现,不得与 P3.2 合并**(输入链路缺口 ≠ 准入约束缺口)。

## 两侧一致清单(已闭环,可直接引用)

- 架构边界五规则 / Resolver bounded access / Evidence Region ≠ Evidence;
- 三数字口径:96.2% coverage / 91.2% observed / 98.1% estimated(禁混称);
- `options_region` = 充分最小 handoff,Producer 不补 per-option;
- 生产 Resolver 无 options_region = **V3 采纳缺口(EB-005)**,Producer 零变更;
- HTML table/div = 系统性 B 类,**Q13/Q37 同 unit 跨产物版本复现**;
- SEMANTIC = 0(31 case 四维分类,数字 DSH 已核验);
- P3.2 范围 = Enforcement 验证 + experimental adapter 路径(**已放行,EXPERIMENT ONLY**)。

## 遗留(执行层,均属 Claude 侧;修正 A/B 是 P3.2 前置)

1. **修正 A(重要,prerequisite)**:`claude4-attribution.json` paper 字段固化了 13/21 错卷名(FACT-013)——须从 `consumer-report-b3.json` join 导出修正(权威链:consumer-report-b3.json → paper identity → attribution,不得倒置);
2. **修正 B(轻量)**:cross_corpus "cases do not overlap" 表述过时(Q13/Q37 已证同 unit)+ V3 侧 state.yaml 仍用本地 EB 编号(映射在 `claude_id_aliases`)。

## 开放问题(EB 项,canonical 编号)

| ID | 问题 | Owner | 状态 |
|---|---|---|---|
| EB-001 | HTML table 型选项:Producer 扩圈定 vs Resolver Region 内解析 | joint | ATTRIBUTED |
| EB-002 | 图片型选项标记↔图边界(§11.3 冻结线;Q13/Q37 同 unit 双版本) | joint | ATTRIBUTED |
| EB-003 | `region_upper=None` 无界扫描可达生产 | v3 | EVIDENCED |
| EB-004 | P3.2 Enforcement Verification(**已放行 EXPERIMENT ONLY**;先修正 A/B → Scope 核验 → 实验) | v3 | **DECIDED** |
| EB-005 | 生产 Resolver 是否引入 options_region(**OPEN 暂不实现,不与 P3.2 合并**) | v3 | EVIDENCED |
| EB-006 | A 缺标点 contextual rule(9 case,源侧 5/5 验;设计属 V3) | v3 | EVIDENCED |
| EB-007 | formula FP 结构排除(P-19 G located=incomplete/null 已澄清;G 检出来源 = V3 代码追踪) | v3 | EVIDENCED |

## 当前禁止(两侧共同)

不改 V3 Frozen Spec / 不冻结 Producer Contract / 不修 Resolver heuristics · 不为 96.2% 修补 · 不合并两侧语料分母 · 不把 21+10 当 31 独立失败 · REPORTED 不冒充 OBSERVED · 不手写重构证据文件已有数据(一律导出)· 不本地分配新 id · 不建互调平台 · Coordination ≠ L2 · **P3.2 八禁(DEC-010)**。

## 接收方启动动作

按 PROTOCOL §5 七步:fetch → 读 state.yaml(权威)→ 读本文件 → 读最新 HANDOFF → 核验证据引用(精确路径,禁模糊匹配)→ 只做 OPEN 项 → 更新 + handoff + commit + CI 绿。

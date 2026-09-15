# CURRENT — 跨 Agent 协调快照(人 + Agent 快速阅读)

> 机器可读状态见 `state.yaml`;协议见 `PROTOCOL.md`。本文件是镜像快照,**权威以 state.yaml 为准**。
> 更新:2026-09-15(步骤④核验完成:修正 A PASS / 修正 B PARTIAL / Scope PASS → **实验获授权启动**)· canonical ledger = kurt-wong/Aitutors-preprocessing(main)

## 当前工作项:EB / Evidence Resolution Boundary Discovery

| Agent | 仓库 | 角色 | 最近动作 |
|---|---|---|---|
| **DSH** | kurt-wong/Aitutors-preprocessing | Source Evidence Producer | 核验 V3 `84fd39f`/`779814e`/`07269f2`:修正 A 机器对账 21/21+10/10 全对;发现 case ID 重编号(新裁定:id 不得重编号,别名已入册);Scope 五要素 PASS;handoff 006 = **实验授权** |
| **Claude** | kurt-wong/AITutors-v3 | Resolution + IR + Gate + Admission | **P3.2 实验获授权(步骤⑤)**;待:修正 B 一行(correspondence_type)+ case id 稳定性确认 + N1–N8 执行方式回执 |

## P3.2 / EB-004 进度板(DEC-010/011)

```
① 修正 A ✓ PASS(paper 21/21 + 10/10 机器对账;case ID 重编号 → case_id_aliases 消歧)
② 修正 B ◐ PARTIAL("different unit sets" 与 FACT-014 矛盾,一行修正非阻塞)
③ Scope Document ✓(p32_scope.md,五要素 + Adapter UNTRUSTED + bypass 定义冻结)
④ DSH 核验 ✓ PASS(FACT-019)
⑤ 实验 ★ AUTHORIZED TO PROCEED(八禁;发现问题只能 OBSERVED→EVIDENCE→REPORT)
⑥ Findings → ⑦ 无 bypass → EB-004 closed;有 bypass → Decision 流程
```

**核心指标**:bypass path count = 0(定义:Admission.success==true AND Authority invalid/absent)。**核心攻击项**:N7(绕过 promotion 直连 Admission)/ N8(gate approve 但 Authority 无效)。**EB-005 保持 OPEN,不与 P3.2 合并。**

## 新裁定(2026-09-15,已入 canonical prohibitions)

**evidence artifact 的 case id 一经分配不得重编号——修内容不改 id。**(本轮实证:重生成 attribution 文件时 P-xx 整体重排,旧引用全部错锚;完整旧→新映射在 state.yaml `case_id_aliases`。)

## 两侧一致清单(已闭环,可直接引用)

- 架构边界五规则 / Resolver bounded access / Evidence Region ≠ Evidence;
- 三数字口径:96.2% coverage / 91.2% observed / 98.1% estimated(禁混称);
- `options_region` = 充分最小 handoff,Producer 不补 per-option;
- 生产 Resolver 无 options_region = **V3 采纳缺口(EB-005)**,Producer 零变更;
- HTML table/div = 系统性 B 类,**Q13/Q37 同 unit 跨产物版本复现**;
- SEMANTIC = 0(31 case 四维分类,数字 DSH 已核验)。

## 开放问题(EB 项,canonical 编号)

| ID | 问题 | Owner | 状态 |
|---|---|---|---|
| EB-001 | HTML table 型选项:Producer 扩圈定 vs Resolver Region 内解析 | joint | ATTRIBUTED |
| EB-002 | 图片型选项标记↔图边界(§11.3 冻结线;Q13/Q37 同 unit 双版本) | joint | ATTRIBUTED |
| EB-003 | `region_upper=None` 无界扫描可达生产 | v3 | EVIDENCED |
| EB-004 | P3.2 Enforcement Verification(**实验已授权,步骤⑤进行中**) | v3 | **DECIDED** |
| EB-005 | 生产 Resolver 是否引入 options_region(**OPEN 暂不实现,不与 P3.2 合并**) | v3 | EVIDENCED |
| EB-006 | A 缺标点 contextual rule(9 case = 新编号 P-03/04/05/08/18 + H-03/05/09/10;设计属 V3) | v3 | EVIDENCED |
| EB-007 | formula FP 结构排除(G case = 新编号 P-20;G located=null 已澄清;检出来源 = V3 代码追踪) | v3 | EVIDENCED |

## 当前禁止(两侧共同)

不改 V3 Frozen Spec / 不冻结 Producer Contract / 不修 Resolver heuristics · 不为 96.2% 修补 · 不合并两侧语料分母(Q13/Q37 同 unit,其余 pattern 级)· 不把 21+10 当 31 独立失败 · REPORTED 不冒充 OBSERVED · 不手写重构证据文件数据(一律导出)· **case id 不得重编号** · 不本地分配新 id · 不建互调平台 · Coordination ≠ L2 · **P3.2 八禁(DEC-010)**。

## 接收方启动动作

按 PROTOCOL §5 七步:fetch → 读 state.yaml(权威)→ 读本文件 → 读最新 HANDOFF → 核验证据引用(精确路径,禁模糊匹配)→ 只做 OPEN 项 → 更新 + handoff + commit + CI 绿。

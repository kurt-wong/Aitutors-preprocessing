# CURRENT — 跨 Agent 协调快照(人 + Agent 快速阅读)

> 机器可读状态见 `state.yaml`;协议见 `PROTOCOL.md`。本文件是镜像快照,**权威以 state.yaml 为准**。
> 更新:2026-09-15(Claude 首次镜像入册 + DSH 三问回复)· canonical ledger = kurt-wong/Aitutors-preprocessing(main)

## 当前工作项:EB / Evidence Resolution Boundary Discovery

| Agent | 仓库 | 角色 | 最近动作 |
|---|---|---|---|
| **DSH** | kurt-wong/Aitutors-preprocessing | Source Evidence Producer | `6a78e80`:协调层 v0.1 + schema 测试;本轮:镜像 Claude handoff 001、亲验 FACT-008/009 升 OBSERVED、FACT-011(Q51 精确形态)、回复三问(handoff 002) |
| **Claude** | kurt-wong/AITutors-v3 | Resolution + IR + Gate + Admission | handoff 001(Claude-2/3/4 审计);**协调文件未 commit,内容按 REPORTED 入册,待其补交** |

## 共享事实(摘要,id 以 state.yaml 为准)

- 三数字永久分开:96.2% coverage(FACT-001)/ 91.2% observed sampled(FACT-002)/ 98.1% estimated;高风险层 0/10 = detector precision failure class(FACT-003);
- DSH 源侧归因 227 choice units:A 真缺口 1 / B 图片型 2 / composite 10(冻结),修复数 0(FACT-004/005);
- **跨侧互证**:HTML table / div 图片型选项 = 系统性 B 类缺口,跨语料(b1 38 卷 vs b2 8 卷)case 零重叠但 pattern 相同(FACT-006/007);
- **FACT-008/009(DSH 亲验升 OBSERVED)**:生产 Resolver **无 options_region 概念**,边界全靠 Source 自推断;`region_upper=None` 无界扫描路径可达生产;
- **FACT-011**:Q51 不是"region 错",是"region 缺失、选项内容(L540 表格行)被 stem_lines 吸收";
- FACT-010(REPORTED 待落盘):Claude-4 重分类 21 pending = 10 STRUCTURAL + 9 CONTEXTUAL_DETERMINISTIC + 1 LEXICAL + 1 UNKNOWN,SEMANTIC=0;
- 两侧一致:`options_region` 是充分的最小 Evidence handoff(FACT-005)。

## 开放问题(EB 项,canonical 编号)

| ID | 问题 | Owner | 状态 |
|---|---|---|---|
| EB-001 | HTML table 型选项:Producer 扩圈定 vs Resolver Region 内解析 | joint | ATTRIBUTED |
| EB-002 | 图片型选项 `<div>A</div>`+图:标记↔图边界归属(§11.3 冻结线) | joint | ATTRIBUTED |
| EB-003 | `region_upper=None` 无界扫描可达生产,处置 | v3 | EVIDENCED |
| EB-004 | P3.2 真实消费实验(四类指标 + 负面验收;**须走 experimental adapter 路径**,生产 Resolver 不消费 options_region) | v3 | DISCOVERED(待用户放行) |
| EB-005 | 生产 Resolver 是否引入 options_region 概念(V3 架构演进,终须 L2) | v3 | EVIDENCED |
| EB-006 | 单行首 marker 无标点:bounded contextual deterministic rule 是否存在 | v3 | DISCOVERED |
| EB-007 | formula/chemical FP:纯结构上下文能否排除(不依赖语义) | v3 | DISCOVERED |

## 互操作状态(2026-09-15 首次)

- **ID 撞号已解决**:Claude 本地编号(写于 PROTOCOL 推送前,同步时差非违规)全部别名映射(`claude_id_aliases`),内容零覆盖;此后直接引用 canonical id;
- **待办(Claude)**:① commit + push 侧协调文件(现 untracked = REPORTED 级);② Claude-4 归因落盘;③ 回复 handoff 002 三问(P3.2 消费条件 / 31 case unit 级清单 / 重分类文件)。

## 当前禁止(两侧共同)

不改 V3 Frozen Spec / 不冻结 Producer Contract / 不修 Resolver heuristics(含 region_upper=None——先提案后裁决)· 不为 96.2% 修补 · 不合并两侧语料分母 · 不把 21+10 当 31 独立失败 · REPORTED 不冒充 OBSERVED · 不本地分配新 id · 不建互调平台 · Coordination ≠ L2。

## 接收方启动动作

按 PROTOCOL §5 七步:fetch → 读 state.yaml(权威)→ 读本文件 → 读最新 HANDOFF → 核验证据引用 → 只做 OPEN 项 → 更新 + handoff + commit + CI 绿。

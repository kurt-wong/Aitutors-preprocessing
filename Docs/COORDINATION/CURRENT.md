# CURRENT — 跨 Agent 协调快照(人 + Agent 快速阅读)

> 机器可读状态见 `state.yaml`;协议见 `PROTOCOL.md`。本文件是镜像快照,**权威以 state.yaml 为准**。
> 更新:2026-09-15(31 case 清单核验轮)· canonical ledger = kurt-wong/Aitutors-preprocessing(main)

## 当前工作项:EB / Evidence Resolution Boundary Discovery

| Agent | 仓库 | 角色 | 最近动作 |
|---|---|---|---|
| **DSH** | kurt-wong/Aitutors-preprocessing | Source Evidence Producer | 31 case 清单全量核验(b3 报告对账 + 源侧亲验):unit/result 21/21 全对,13/21 卷名漂移已修正;FACT-012~017 入册;handoff 003 |
| **Claude** | kurt-wong/AITutors-v3 | Resolution + IR + Gate + Admission | handoff 002(31 case 清单 + 4 Claim + P3.2 范围判断);**协调文件仍未 commit,清单未落盘** |

## 共享事实(摘要,id 以 state.yaml 为准)

- 三数字永久分开:96.2% coverage(FACT-001)/ 91.2% observed(FACT-002)/ 98.1% estimated;高风险 0/10(FACT-003);
- **FACT-009(DSH 亲验)**:生产 Resolver 无 options_region 概念,V3 采纳缺口(EB-005),Producer 零变更;
- **FACT-012/013(本轮)**:b3 报告权威对账 21 pending unit/result 全对;**聊天转述卷名 13/21 漂移**——转述层不可信,引用必须回到证据文件;
- **FACT-007 修正**:P-06/P-07 = Q13/Q37 **同源卷同 unit** 跨产物版本复现("零重叠"仅对 Q51 成立;同 unit 双版本失败 = pattern 对 prompt 演进稳定,系统性证据升级);
- **FACT-015**:21 pending 源侧呈现全部亲验(A 缺标点 5/5、H:O:H 行内、数学模式、`---` 前缀、table/td、div marker);
- **FACT-017(新)**:P-19 region 内未见字面 G 但 detected 含 G——located 待 V3 澄清;
- FACT-016(方法论):跨卷核验禁用 glob 模糊匹配(DSH 首轮错卷实证)。

## 开放问题(EB 项,canonical 编号)

| ID | 问题 | Owner | 状态 |
|---|---|---|---|
| EB-001 | HTML table 型选项:Producer 扩圈定 vs Resolver Region 内解析 | joint | ATTRIBUTED |
| EB-002 | 图片型选项标记↔图边界(§11.3 冻结线;Q13/Q37 同 unit 双版本复现) | joint | ATTRIBUTED |
| EB-003 | `region_upper=None` 无界扫描可达生产 | v3 | EVIDENCED |
| EB-004 | P3.2(范围 = Enforcement 验证,DSH 同意;**待用户放行**;须走 experimental adapter) | v3 | EVIDENCED |
| EB-005 | 生产 Resolver 是否引入 options_region(终须 V3 侧 L2) | v3 | EVIDENCED |
| EB-006 | A 缺标点 contextual rule(9 case,DSH 源侧 5/5 验;规则设计属 V3) | v3 | EVIDENCED |
| EB-007 | formula FP 结构排除(INFERRED;P-19 G located 待澄清) | v3 | EVIDENCED |

## 互操作状态

- ID 撞号:别名映射运行中(`claude_id_aliases`,含 Claim 映射);此后直接引用 canonical id;
- **待办(Claude)**:① commit 协调文件;② 31 case 清单以 b3 报告为准落盘;③ P-19 G located 答复;④ P3.2 范围文档起草(不启动);
- **待用户**:P3.2 放行裁定。

## 当前禁止(两侧共同)

不改 V3 Frozen Spec / 不冻结 Producer Contract / 不修 Resolver heuristics · 不为 96.2% 修补 · 不合并两侧语料分母 · 不把 21+10 当 31 独立失败 · REPORTED 不冒充 OBSERVED · **不手写重构证据文件已有数据(一律导出)** · 不本地分配新 id · 不建互调平台 · Coordination ≠ L2。

## 接收方启动动作

按 PROTOCOL §5 七步:fetch → 读 state.yaml(权威)→ 读本文件 → 读最新 HANDOFF → 核验证据引用(精确路径,禁模糊匹配)→ 只做 OPEN 项 → 更新 + handoff + commit + CI 绿。

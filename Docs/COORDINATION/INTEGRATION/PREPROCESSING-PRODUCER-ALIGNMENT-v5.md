# PREPROCESSING PRODUCER ALIGNMENT v5(Interface Finalization Revision v1 回应)

> Status: **v5(2026-09-16)** · Authority: Owner 统一任务指令 Interface Finalization Revision v1(原文照录于 `PREPROCESSING-OWNER-DECISION-RECORD-v1.md` §1quinquies;ledger = `state.yaml.decisions[DEC-023]`)
> Role: DSH = Source Evidence Producer 侧对齐件(Part 8 任务:同步五文档 = Producer Alignment / Interface Facts / ODR / Gap List / Dependency Map)。
> 本轮纪律(Owner 令):仅更新决策记录、契约草案、Gap 文档和台账;禁改代码 / schema / preprocessing 数据 / 执行 IR 重生成 / 图片恢复 / daemon / 冻结 Contract v0.2;全部 implementation 状态 = **not started**。
> 承接:`PREPROCESSING-PRODUCER-ALIGNMENT-v4.md`(保留原文;本文件按 Owner Part 10 格式输出,并修正 v4 中已被本轮裁决关闭的表述)。
> Discipline:DECISION 段 = 保守义解释,非新增裁决;OBSERVED 复用既有工件,零新测量。

---

## A. Changed Documents(Owner Part 10.1;本文件 commit 见 git log)

| 文件 | 修改内容 |
|---|---|
| `PREPROCESSING-OWNER-DECISION-RECORD-v1.md` v1.4 | 新增 §1quinquies(Part 1–10 原文照录 + 生产侧保守义);§3 未裁清单按 DEC-023 重写 |
| `PREPROCESSING-PRODUCER-ALIGNMENT-v5.md`(本文件,新) | v4 承接件:决策对齐表 + 剩余 UNKNOWN + Changed Documents |
| `PREPROCESSING-PRODUCER-INTERFACE-FACTS-v2.md` v2.2 | §0bis 固化表更新(identity 格式已裁 / path 非身份注记 / 16 份 Semantic Pending);§2.1 `source_file` 行加 locator 定性注 |
| `PREPROCESSING-IMPLEMENTATION-GAP-LIST.md` v1.3 | G1 格式已裁 / G2 path 非身份收窄 / G3 再生成"允许+四约束" / G5 词表终局 + unknown 路由已裁 / 汇总矩阵与最小冻结集更新 |
| `PREPROCESSING-EXECUTION-DEPENDENCY-MAP.md` v2.3 | E8 由"若扩产"变"已允许(四约束),执行待令";16 份 Semantic Pending 注记;DEC-023 增量头注 |
| `PREPROCESSING-PRODUCER-DECISION-ALIGNMENT-v1.md` / `…-ALIGNMENT-v4.md` | 承接注记(v4 中 G-1 格式 PROPOSED、G-4 交付形态等表述按本裁决收窄,以 v5 为准) |
| `Docs/COORDINATION/state.yaml` / `CURRENT.md` / `log.md` | DEC-023 入册 + `owner_interface_revision` 块 + 快照/台账 |

## B. Decision Alignment Summary(Owner Part 10.2;| Decision | Current | Final Rule |)

| Decision | Current | Final Rule |
|---|---|---|
| **DEC-SOURCE-IDENTITY**(Part 1) | 算法已实证(71 份 IR);v4 中格式为 PROPOSED(裸 hex 建议) | `source_version_id = SHA256(original source bytes)`,**64 字符小写 hex 字符串**;Identity 由 `source_version_id` **唯一决定**;**Source identity belongs to content hash, not storage location** |
| path 身份地位(Part 1-2) | 旧表述把绝对路径列为"交付形态缺口"(G-4),身份/locator 未分层 | `source_file` **保留** = **locator information,非 identity information**;"source_file 用于辅助定位,source_version_id 用于跨系统唯一识别";路径变化(Windows/NAS/Linux/Object/Cloud)不得导致 id 变化;**任何文档不得暗示 path 参与唯一/身份/version/hash 判断** |
| 16 份 Identity-only(Part 3) | v4 定义 = Identity Available / Semantic Unavailable"正常态";IR 再生成"另行批准"(机制未裁) | 状态 = **Identity Available / Semantic Pending(可恢复)**;**允许重新执行 preprocessing 生成 IR**,四约束:①bytes 不变 ②id 一致 ③新 IR 绑定 `source_version_id` ④重过 identity verification + semantic validation;四禁:改原 source / 重 OCR 覆盖 / 生成新 identity / 新 hash 替代旧 hash |
| Interface Scope(Part 4) | 87/71/16 已有口径 | **87 不得修改为 71**;87 = 正式身份接口范围 / 71 = 当前 IR 语义消费范围 / 16 = 等待 semantic processing;**禁止 IR available = Interface available** |
| 状态机(Part 5) | DEC-021 D3 四状态机合并记法 + DEC-022"不合并"原则 | **词表终局**:semantic = `ready/incomplete/unknown`;decision = `pending_review/approved/rejected`;两体系禁止合并(取代 D3 四状态合并记法,引用以本裁决为准) |
| Unknown 处理(Part 6) | D3 路由"pending_review 或 rejected 由明确规则决定"(规则未给) | unknown semantic unit:禁 silent skip / automatic conversion / silent fallback;**必须产生 reviewable record → 进入 pending_review workflow**(路由规则已给) |
| Contract v0.2(Part 7) | Claude 起草(DEC-022);本轮禁冻结 | v0.2 DRAFT 必须含四章节:Identity / Scope / Semantic / Boundary;本轮保持 DRAFT NOT FROZEN;下阶段 = **v0.2 Freeze Candidate Review**,不再扩展接口讨论 |
| V3 消费逻辑(Part 9,Claude 侧,此处只登记约束) | —— | V3 未来消费**不得依赖 source_file path,必须依赖 source_version_id**;"V3 identity verification capability not implemented" = not started(由 Claude 登记) |

**Final Boundary 达成核对(DSH 侧)**:Source Identity Frozen ✅(Part 1)/ Scope Frozen ✅(Part 4)/ Semantic Boundary Frozen ✅(Part 5-6)/ Path Non-Identity Frozen ✅(Part 1-2)/ Identity-only Recovery Rule Frozen ✅(Part 3)。**五项全达成 → 接口原则讨论关闭,进入 v0.2 Freeze Candidate Review。**

## C. 生产侧现状对照(OBSERVED,零新测量)

- 格式裁决与现有生产实践**零迁移**:IR `source_sha256` 71 份已是 64 字符小写 hex;`resolver_reference.py:52-53` 产出即此形态;
- path 非身份裁决与现有实证一致:71 份身份对账全部以字节 sha 成立(`ir.source_sha256` == provenance == 当前磁盘字节),从未依赖路径;现状"路径值相等"关联(FACT: `ir.source_file == manifest.source_file`)恰是裁决禁止的合规关联替代 → G2 升级路径不变(随 G1 回填);
- 16 份清单在接口面内确定(87 − 71;`producer_interface_probe_v2.json`);其 source bytes 在位(v2 面 87 source md 零缺失,FACT-035④)→ 四约束的 Constraint 1 当前可满足,是否执行 = Owner 令;
- 存量 1 例 `andalone_question`:按 Part 5 词表 = semantic 层非 ready(unknown/需 reviewable record),decision 层 pending_review 目标态;载体与存量处置仍未裁(D-3)。

## D. Remaining UNKNOWN(Owner Part 10.3;只保留真正未裁事项)

| # | 事项 | 性质 |
|---|---|---|
| 1 | 两层状态载体(字段名/落点)+ reviewable record 形态 | v0.2 正文落字面 |
| 2 | Step 1 接口快照载体形态与 R50 血统(D-6)+ 全部数据动作执行令(回填 87 / 守卫实施 / 存量 1 例 D-3 / 2 份三重成员 D-4 / 16 份 IR 再生成批次与 R52 工件版本策略) | Owner 执行令 |
| 3 | source bytes 本身交付给 V3 的方式(locator 之外的传输/获取;path 问题已裁非身份,bytes 可达性仍属 v0.2 交付面) | v0.2 交付面 |
| 4 | legacy 79 披露形态(文字层,弱)/ `_imgs/` 恢复产物接口地位(OQ-3,弱) | v0.2 文字层 |

## E. 纪律自查

零代码 / 零 schema / 零数据 / 零 IR 重生成 / 零图片恢复 / 零 daemon / 零 Contract 冻结;写入面 = 本文档 + ODR v1.4 + Facts v2.2 + Gap List v1.3 + Dependency Map v2.3 + 台账三件;全部 implementation 状态 = not started;DECISION 段全部与 §1quinquies 原文逐条对应。

*v5 · 2026-09-16 · DSH(Source Evidence Producer)。裁决基准 = ODR v1.4;如有文字冲突,以 Owner 原文为准。*

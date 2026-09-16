# EXECUTION DEPENDENCY MAP — G1 identity 固化 × D2 figure recovery(重整理)

> Status: **v2.6(2026-09-16,DEC-027 冻结收口轮:Freeze Evidence v1 建立,最终一致性检查 C1-C9 全 PASS = VERIFIED,READY FOR CONTRACT FREEZE(Producer 侧))** · 取代 IF-v2 §6.3 与 Readiness v1 中"互斥时序"的初步表述
> **DEC-027 增量(冻结收口结果)**:Task 1 Freeze Evidence = `INTEGRATION/PREPROCESSING-CONTRACT-v0.2-FREEZE-EVIDENCE-v1.md`(Contract v0.2(ff04f47+e70807b)→ Step 1 → Step 2 → 验证报告 → final check 全链可追溯 + 工件 sha256 全值登记);Task 2 = `scripts/freeze_evidence_final_check.py` 只读复核(从当前磁盘字节独立重推导)C1-C9 全 PASS(87 scope / 87 唯一身份键 / 87 bytes==R50 / IR 71·71 / pending 16·16 / R50 血统 / 剥键 87·87 / locator 87·87;unique identities 87 dups 0);Task 3 = 文档交叉核验完成(Facts v2.5 消歧 / Alignment v4 废止标识);Task 4 = 零实现动作。**五步序 Step 3 前置 = Claude 正文合并 + Owner 正式 Freeze 令,DSH 侧已 READY**。
> **DEC-026 增量(执行结果)**:Step 1 接口快照已冻结(`data/interface_scope_snapshot_step1.json` + audit `interface_scope_prebackfill` corpus `4ad3458b…`;载体与血统 = 执行令已细化,E2' 关闭);Step 2 回填 `source_content_sha256` × 87/87 DONE;**E2 配对再冻结已落地**——R50 DRIFT = 恰 87 manifest(missing 0,预期),接口面新配对基线 = audit `interface_scope_postbackfill`(corpus `24af8f56…`,verify ok),R50 保留为历史基线;详件 = `PREPROCESSING-STEP1-STEP2-VERIFICATION-REPORT-v1.md`。主链(G1×D2×R50)与交集定量不变(Step 5 两份三重成员仍单独裁决)。
> **DEC-025 增量(沿用)**:跨系统身份字段名 = **`source_content_sha256`**(= SHA256(raw bytes),64 小写 hex 不变;OQ-8′ 关闭,V3 内部 UUID `source_version_id` 无需改名);本图中"backfill source_version_id / G1 回填"一律指回填 `source_content_sha256`;bytes 能力要求已冻结(传输方式不冻结)。主链(G1×D2×R50)与交集定量不变。
> **DEC-023 增量**:①**Path 非身份原则**——id 钉的是 bytes 不是 path;D2 改写 md 使 id 失配的机理 = **bytes 变**,与路径/目录无关(表述同步修正);②**16 份接口面内无 IR 成员 = Identity Available / Semantic Pending(可恢复)**;IR 再生成**允许但四约束**(bytes 不变/id 一致/新 IR 绑定 id/重过双验证)+ 四禁(禁改原 source/禁重 OCR 覆盖/禁新 identity/禁新 hash 替代)→ **E8 由"若扩产"变"已允许,执行待令"**;③G1 字段名/算法/格式三裁,仅剩回填执行令。本图主链(G1×D2×R50)与交集定量不变。
> DEC-B1 增量:source 身份不依赖 IR 存在 → E8(G3 扩产治理)与 G1 路径彻底解耦;本图主链(G1×D2×R50)不受影响,交集定量不变。
> **DEC-021 增量**:Owner 裁定五步序 = ①Freeze interface snapshot → ②backfill source_version_id(范围已裁 87)→ ③Freeze Contract v0.2 → ④data hygiene → ⑤image recovery——**D-1/D-2/D-5 关闭**(见 §5);快照先行变体下 E2 的配对对象从"R50 再冻结"转为"Step 1 接口快照与 R50 的血统关系"(执行令细化,UNKNOWN)。
> Basis: Owner Decision Record v1(§1bis DEC-B1 + **§1ter DEC-021**)+ `data/producer_readiness_probe_v3.json`(三点交集定量)+ R50 成员资格亲验
> Purpose: 用实测交集数据取代定性判断,给出 G1 与 D2 的**精确**依赖关系与可行执行序。

---

## 1. 关键定量输入(probe_v3,全部 OBSERVED)

| 集合 | 大小 | 说明 |
|---|---|---|
| V = v2 接口面 source md | 87 | 字段口径 `identity_version == "2"` |
| I = IR ADMITTED source md | 71 | ⊂ V |
| D = dangling figure 文件 | 1,396 | 自算,与 DQE 口径一致 |
| R = R50 基线成员 | 356 = 88 manifest.json + 88 annotated.md + 176 source md + 4 其他 | 冻结输入面 |

**交集(本轮钉死)**:

| 交集 | 数量 | 文件 |
|---|---|---|
| D ∩ V | **2** | 首师大附中高一化学月考 / 首师大附中高三物理月考 |
| D ∩ I | **2** | 同上 |
| D ∩ R | **2** | 同上(closure plan v1 "R50 交集恰 2 份"三点闭合验证) |
| V∩ R(manifest) | **87/87** | v2 接口面 manifest **全部**是 R50 成员 |
| V ∩ R(source md) | 87/87 | — |
| I ∩ R(source md) | 71/71 | — |

## 2. 上一版表述的修正

**上一版(IF-v2 §6.3 / FACT-034)**:G1 回填与 D2 恢复构成"互斥时序",理由是 D2 就地改写 md → id 失配。

**修正(基于交集定量)**:互斥**不是全量的,是精确 2 文件的**:

- D2 的 1,396 份中,**只有 2 份**落在 v2 接口面(= 同 2 份也在 IR 71 与 R50 内);其余 1,394 份与接口面零交集,D2 改写它们**不影响任何已回填的 `source_content_sha256`**;
- 但这 2 份是**三重成员**(接口面 + IR 冻结工件 + R50 基线)——D2 触碰它们的代价不是"id 失配"一个,而是**三重 DRIFT**:md sha 变 → IR `source_sha256`/`provenance.source_version` 悬空 + R50 基线 DRIFT + 回填 id 失配;
- closure plan v1 已决定批跑默认**排除这 2 份**(当时理由 = R50 交集;现在理由升级为三重成员)。**排除生效时,D2 与 G1 零冲突,顺序自由。**

## 3. 依赖图(节点 = 动作,边 = 约束)

```
[v0.2 冻结] ──定义字段──> [G1a 字段定义] ──范围令──> [G1b 回填 87|166]
    │                                                 │
    │ 落字 B3 载体                                      │ 必然:R50 DRIFT(87 manifest 均为成员)
    ▼                                                 ▼
[G5a 守卫实施] ──存量处置令──> [G5b 存量 1 例]    [R50 再冻结] <──必须配对── [G1b]
                                                         ▲
[D2 批跑(排除 2 三重成员 + 2 无 PDF)] ──零冲突──X       │ 若解禁 2 份,则:
    │                                                   │
    └── 改写 1,394 份 md(其中 0 份在接口面)─────────────┘ 三重 DRIFT 联动处置
```

### 边表(每条 = 一个硬约束)

| # | 从 → 到 | 约束 | 强度 |
|---|---|---|---|
| E1 | v0.2 冻结 → G1b | 字段未定义不得回填 | 硬(治理) |
| E2 | G1b → 基线再冻结 | **已落地(DEC-026)**:DRIFT = 恰 87 manifest(missing 0),配对再冻结 = pre/post 双快照(新 audit_id + 血统注记齐备) | 硬(事实) |
| E2' | Step 1 快照 → E2 配对对象 | **关闭(DEC-026)**:载体 = `interface_scope_snapshot_step1.json`;血统 = R50 成员超集保留为历史基线,接口面基线角色由 `interface_scope_prebackfill`/`interface_scope_postbackfill` 双快照承接 | 硬(已落地) |
| E3 | v0.2 冻结 → G5a | B3 载体未定义,守卫无落点 | 硬(治理) |
| E4 | G5a → G5b | 存量处置须在守卫就位后(否则无验收标准) | 硬(方法) |
| E5 | D2(排除模式)→ G1 | **无约束**(排除 2 三重成员后,1,394 份与接口面零交集) | 无 |
| E6 | D2(含 2 份)→ 三重 DRIFT | md sha 变 → IR 悬空 + R50 DRIFT + id 失配,须三重联动处置 | 硬(事实) |
| E7 | D2 → OQ-3 | 恢复产物 `_imgs/` 是否入接口面未定义 | 弱(文字层) |
| E8 | G3 扩产 → R52 工件治理 | 重产 IR = 冻结工件版本问题 | 硬(治理,若 G3 启动) |

## 4. 执行序(DEC-021 D4 已裁五步;原序 A/B 保留为历史参考)

**Owner 裁定五步序(现行,取代序 A/B)**:
1. **Step 1 Freeze interface snapshot** —— **DONE(DEC-026)**:`data/interface_scope_snapshot_step1.json` + audit `interface_scope_prebackfill`(载体/血统 = 执行令已细化,E2' 关闭);
2. **Step 2 Generate / backfill source_version_id** —— **DONE(DEC-026,验证 PASS)**:`source_content_sha256` 回填 87/87,Manifest hash == IR hash 71/71;
3. **Step 3 Freeze Contract v0.2** —— 待 Claude 正文合并 + Owner Freeze 令;
4. **Step 4 Execute data hygiene**;
5. **Step 5 Execute image recovery / historical cleanup**(D2 在此步:批跑默认排除 2 份三重成员 + 2 无 PDF 件,E5 零冲突)。

**裁决理由(Owner 原文)**:source identity 必须早于内容修改——图片恢复/OCR 修复/markdown 修改都可能导致 content change → hash change → `source_content_sha256` invalid。**身份冻结优先。**

**与本图定量的兼容性**:五步序与交集定量零冲突——Step 2 回填的 87 份全部 R50 成员(E2 硬约束由 Step 1 快照承担配对角色);Step 5 D2 排除模式下 1,394 份与接口面零交集(E5);2 份三重成员仍单独裁决。

(历史参考:原序 A = 冻结→回填+再冻结→D2→守卫;原序 B = 先清洗后冻结——序 B 与 Owner 令顺序相反,**已被 D4 否决**;序 A 与五步序同构,差异 = 快照时点前移。)

## 5. 决策点(Owner)

| # | 决策 | 状态(DEC-021 后) |
|---|---|---|
| D-1 | 执行序 A vs B | **关闭:均不采纳,Owner 自裁五步序(快照先行)** |
| D-2 | G1b 回填范围 87 vs 166 | **关闭:已裁 87(DEC-021 D1);79 legacy = historical asset(D2)** |
| D-3 | 存量 1 例(unit_type)与回填是否同一原子再冻结 | 未裁(存量呈现态随 G5 载体) |
| D-4 | 2 份三重成员恢复:做 / 不做 / 排除到底 | 未裁(Step 5 前须裁) |
| D-5 | D2 是否可先于 v0.2 冻结解禁 | **关闭:否——D2 = Step 5 最后(DEC-021 D4)** |
| D-6(新增) | Step 1 接口快照的载体形态与 R50 血统关系(新基线工件?audit_id 规则?) | **关闭(DEC-026)**:载体 = `data/interface_scope_snapshot_step1.json`;血统 = R50 保留历史基线 + pre/post 双快照承接接口面基线角色 |

## 6. 纪律

本文档零执行、零数据修改(注:Step 1/Step 2 的执行发生在 DEC-026 Owner 执行令之下,执行记录 = `PREPROCESSING-STEP1-STEP2-VERIFICATION-REPORT-v1.md`,不在本文档内进行);全部数字来自 `data/producer_readiness_probe_v3.json` 与 R50 快照亲验;替代此前 IF-v2/Readiness v1 的定性"互斥"表述(修正记录见 §2)。

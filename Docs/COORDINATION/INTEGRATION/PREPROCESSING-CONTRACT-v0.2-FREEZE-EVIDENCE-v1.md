# PREPROCESSING CONTRACT v0.2 — FREEZE EVIDENCE v1

> Status: **READY FOR CONTRACT FREEZE(Producer/DSH 侧)**(2026-09-16,Owner 冻结收口令 Task 1-4 执行轮)
> Authority: Owner Final Decision Instruction v1(DEC-026)+ 本轮「Contract v0.2 最终冻结收口(DSH/Producer 侧)」指令
> Role: Contract v0.2 冻结的 Producer 侧证据总账——把「契约文本 → Step 1 快照 → Step 2 回填 → 验证报告 → 最终复核」钉成一条可追溯链。
> 纪律: 本文件只登记已发生、可复现的事实;**Decision ≠ Implementation**——契约冻结不代表 V3 已具备任何验证能力(§5)。

---

## 0. 冻结对象与权威链

```text
Contract v0.2(条文 = PREPROCESSING-CONTRACT-v0.2-FREEZE-CANDIDATE-FINAL-v1.md,
             FC-1~FC-5,commit ff04f47;执行记录注记 commit e70807b)
   ↓ FC-1 定义:source_content_sha256 = SHA256(original source bytes), 64 lowercase hex
Step 1 interface snapshot(commit e70807b;data/interface_scope_snapshot_step1.json
                          + audit interface_scope_prebackfill)
   ↓ 冻结 87 接口面:文件清单 + 回填前 sha + R50 双成员关联 + IR 关联
Step 2 backfill(commit e70807b;scripts/interface_scope_step2_backfill.py
                + data/interface_scope_step2_backfill_report.json
                + audit interface_scope_postbackfill)
   ↓ 87/87 追加 source_content_sha256 一键;内容寻址证明 = 剥键重序列化 == R50 基线
Verification Report(commit e70807b;
                    PREPROCESSING-STEP1-STEP2-VERIFICATION-REPORT-v1.md)
   ↓ 四项验证(87 清单 / hash 一致 / IR 覆盖 / 16 pending)+ R50 DRIFT 对账
Freeze Evidence Final Check(本轮;scripts/freeze_evidence_final_check.py
                           + data/freeze_evidence_final_check.json)
   = 全部判定从当前磁盘字节重新推导,不信先前报告结论 → overall VERIFIED(C1-C9)
```

## 1. 工件登记表(sha256 = 本轮提交时点实测)

| 工件 | sha256(全值) | 说明 |
|---|---|---|
| `data/interface_scope_snapshot_step1.json` | `b4f14524473d97b86f5d6a2f8bb03ee794727652a68fa4df4b00d794de98ad99` | Step 1 接口快照(87 行) |
| `data/audit_snapshot_interface_scope_prebackfill.json` | `b11874c472a9fad3051f58c5fc46367dc8d7fc3e5ad961b266edfa55c142dd9c` | 回填前 audit 快照;corpus_sha256 = `4ad3458ba11752d53b5885eb727e9da6ee5726b8eac2a5f0b0d81ca22fd19160`(177 files) |
| `data/interface_scope_step2_backfill_report.json` | `d430cc2f6ebdf6553464f9751ade4b02eac6423f0509222a96c4c4666fb6eec1` | Step 2 逐份回填报告(87 行) |
| `data/audit_snapshot_interface_scope_postbackfill.json` | `2cb980c7ca421f5a2c3615053cd3308d5ad1aa078083928724af88d4663a4096` | 回填后 audit 快照(接口面完整性基线承接者);corpus_sha256 = `24af8f566e8e2356c29aa99e6b185c5f6f8eaf2df983bd4b6b0669684c240a10`(177 files,verify ok) |
| `data/audit_snapshot_R50_input_baseline.json` | `963cd6b1350956e2…`(历史基线,commit 面钉住) | R50 历史基线(356 files);DRIFT = 恰 87 manifest,missing 0(E2 已预期) |
| `data/freeze_evidence_final_check.json` | `a707738e5ceae7008eef7a7744d38b7b7ca1c052d936b49e0b31e59f1c5a5c33` | 本轮最终复核报告(C1-C9 + 87 行明细) |

脚本(确定性只读,可复跑):`scripts/interface_scope_step1_snapshot.py`(Step 1;回填后重跑会因 pre-backfill invariant fail-closed,属正确行为)/ `scripts/interface_scope_step2_backfill.py`(Step 2,幂等可重入)/ `scripts/freeze_evidence_final_check.py`(本轮复核,只读)。

## 2. Producer 最终一致性检查(Owner Task 2)—— 全部 PASS,标记 VERIFIED

复核方式:不采信 Step 2 报告结论,`freeze_evidence_final_check.py` 从当前磁盘字节独立重新枚举、重新计算 SHA256、与 Step 1 快照/Step 2 报告/R50 基线/audit 快照交叉对账。

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| C1 | 接口面 = 87(字段口径 `identity_version==2`,独立重枚举) | **PASS** | found = 87 |
| C2 | 87/87 manifest 携 `source_content_sha256` 且为面内唯一 sha/hash 键 | **PASS** | 87/87 |
| C3 | 87/87 值 == SHA256(当前 source bytes),64 位小写 hex | **PASS** | bytes match 87/87;format 87/87 |
| C4 | 87/87 source bytes 自 Step 1 快照起零漂移且 == R50 记录值 | **PASS** | match step1 87/87;match R50 87/87 |
| C5 | IR 对账:ADMITTED 71/71 且 `ir.source_sha256` == `manifest.source_content_sha256` | **PASS** | 71/71 |
| C6 | 16/16 Semantic Pending(REJECTED_QC_FAIL)身份自足 | **PASS** | 16/16 均携 64-hex 身份且字节可达(清单见 §2.1) |
| C7 | R50 血统:87 manifest + 87 source 双成员;DRIFT == 恰 87 manifest、missing 0;post audit verify ok;pre 漂移集 ⊆ scope;corpus 值与 Step 2 报告一致 | **PASS** | 见 §3 |
| C8 | 仅追加一键再证:剥去新键重序列化 sha == R50 基线记录 manifest sha | **PASS** | 87/87 |
| C9 | path 非身份:locator(`source_file`)与 Step 1 快照一致;身份只按内容 hash 判定 | **PASS** | locator unchanged 87/87;**unique identities = 87,duplicate = 0** |

**overall = VERIFIED**(`data/freeze_evidence_final_check.json`)。本轮无任何不一致,无 BLOCKER。

### 2.1 16 份 Semantic Pending 逐份(Identity Available / Semantic Pending)

1. `reslice-batch-C\会考\化学\2018北京春季高中会考化学（教师版）(1)`
2. `reslice-batch-C\会考\语文\2018北京春季高中会考语文（教师版）(1)`
3. `reslice-batch-C\合格考\英语\2020北京高中合格考英语（第二次）（教师版）(1)`
4. `reslice-batch-C\学业水平考试\化学\12_T8联盟2023年…化学答案`
5. `reslice-batch-C\高一\历史\2020北京平谷高一（上）期末历史含答案`
6. `reslice-batch-C\高一\政治\2021北京四十三中高一（上）期中政治（教师版）`
7. `reslice-batch-C\高一\生物\2021北京四中高一（上）期中生物（教师版）`
8. `reslice-batch-C\高一\英语\2019北京三十五中新高一分班考试英语含答案(1)`
9. `reslice-batch-C\高三\化学\1_16_专题十六　化学实验综合　教师用书PDF`
10. `reslice-batch-C\高三\化学\2017-2019北京高三化学上学期期末汇编：化学实验（教师版）(1)`
11. `reslice-batch-C\高三\数学\2017-2019北京高三数学上学期期末汇编：立体几何（教师版）(1)`
12. `reslice-batch-C\高考真题\数学\2012-2021高考真题数学汇编：统计与概率（分布列）（1）（教师版）(1)`
13. `reslice-pac-annotated\reslice-pac\ocr\pac-c07-01`
14. `reslice-pac-annotated\reslice-pac\ocr\pac-c09-01`
15. `reslice-pac-annotated\reslice-pac\ocr\pac-c09-02`
16. `reslice-pac-annotated\reslice-pac\ocr\pac-c11-02`

(完整路径以 `.manifest.json` 结尾;逐份明细在 final check JSON `rows`。)IR 再生成**允许但须另令**,四约束(复用原 `source_content_sha256` / 不新建 identity / 不改历史 Manifest 身份 / 不删历史记录、不覆盖历史 IR 语义、保留完整血统)。

## 3. R50 血统关系(冻结解释,防后续误读)

- R50_input_baseline(356 files)为**历史基线**,回填后其 87 份 manifest 成员 DRIFT = **预期行为**,不是数据事故;
- 接口面完整性基线的**现行承接者 = pre/post 配对双快照**(`interface_scope_prebackfill` corpus `4ad3458b…` → `interface_scope_postbackfill` corpus `24af8f56…`,均 177 files);
- 任何未来审计若对 R50 跑 verify,应预期 drift == 恰 87 份接口面 manifest、missing 0;偏离此预期才是异常。

## 4. 文档交叉核验(Owner Task 3)—— 完成,现行态零歧义

核验面 = Producer 侧全部 INTEGRATION 文档 + state.yaml + CURRENT.md。判定标准:`source_content_sha256` = 跨系统内容身份;`source_version_id` = 仅 V3 内部 UUID FK;path = locator;"Semantic Unavailable" 不得作为现行状态。

| 文档 | 结果 | 处置 |
|---|---|---|
| `PREPROCESSING-PRODUCER-INTERFACE-FACTS-v2.md` | 发现现行态残留(B1 原文引用/职责表/§1 摘要两行/§2.1 时点/§3.4 关联键/N1/G1) | **本轮修订 → v2.5**:现行态全部按 DEC-025 命名;历史时点事实(0/166 等)保留但明确标识为回填前时点 |
| `PREPROCESSING-EXECUTION-DEPENDENCY-MAP.md` | 两处现行描述用旧名 | 本轮改 `source_content_sha256`(DEC-025 增量注已覆盖其余映射) |
| `PREPROCESSING-PRODUCER-ALIGNMENT-v4.md` | §B.4 "Semantic Unavailable 正常态" + G-6 行 | 本轮加**已废止**行内标识(v4 = 历史基准文件,承接注记已在位) |
| `PREPROCESSING-OWNER-DECISION-RECORD-v1.md` | 合规 | 逐处有取代注(§1octies/§1quinquies Part 3 修订行);决策原文照录属审计记录 |
| `PREPROCESSING-CONTRACT-v0.2-FREEZE-CANDIDATE-FINAL-v1.md` / `…-REVIEW-v1.md` | 合规 | 命名纪律(FC-1)与 F-4 修正指令在位;Review 为历史评审记录 |
| `PREPROCESSING-STEP1-STEP2-VERIFICATION-REPORT-v1.md` / GAP-LIST v1.5 | 合规 | 无 `source_version_id` 契约键用法、无现行 "Semantic Unavailable" |
| `state.yaml` / `CURRENT.md` | 合规 | DEC-022 决策原文为历史记录;CURRENT 中 "Semantic Unavailable" 仅出现在「Claude 修正指令」语境 |
| `PREPROCESSING-PRODUCER-ALIGNMENT-v5.md` | 合规 | 修订表语义(v4 旧定义 → 新定义) |

复核命令(可复跑):`rg "Semantic Unavailable|source_version_id" Docs/COORDINATION` ——剩余命中全部位于 ①Owner/DEC 原文照录 ②取代/废止注记 ③Claude 修正指令 ④V3 内部 UUID FK 语境,四类均属允许保留的历史审计注记。

## 5. Decision ≠ Implementation(硬边界,冻结不得误读)

Contract v0.2 冻结 = **裁决冻结**,不是能力交付。V3 侧全部消费能力仍为 **not implemented / not started**:

| V3 能力(契约义务) | 状态 |
|---|---|
| D-7 获取 source bytes + 独立计算 SHA256 + 与 `source_content_sha256` 比对 + 不一致 fail-closed | **not started** |
| D-8 六消费义务(M 验身份 / IR 验语义等) | **not started** |
| D-9 unknown → reviewable record → pending_review 路由 | **not started** |
| D-11 Identity Verification 机制 | **not started** |
| (现状)V3 自算 hash | canonical_json 包裹(`runner.py:71-73`,`hashing.py:60-62`),**非 raw bytes**,不满足 FC-2 |

Producer 侧同样:16 份 IR 再生成、legacy 79 迁移、图片恢复、数据治理 = **未执行,须 Owner 另令**。

## 6. 纪律自查(Owner Task 4)

本轮零实现动作:未重生成 IR / 未恢复图片 / 未改 Question 数据 / 未改 schema / 未动 daemon / 未改 V3 任何代码 / 未做任何未授权数据清洗。数据写入面 = 零(唯一新数据文件 `data/freeze_evidence_final_check.json` 属证据登记,由只读复核脚本生成);manifest/IR/原始文件字节零改动(C3/C4/C8 再证)。全量测试 338 passed / 1 xfailed(与基线一致)。

## 7. 结论

```text
READY FOR CONTRACT FREEZE
```

(权责边界:此为 **Producer/DSH 侧证据结论**;冻结令本身属 Owner,契约正文合并义务属 Claude。DSH 侧前置与证据链已全部闭合,无 BLOCKER、无遗留验证缺口。)

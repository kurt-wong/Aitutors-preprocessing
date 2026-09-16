# PRODUCER FROZEN BASELINE × CONSUMER IMPLEMENTATION BOUNDARY CHECK v1

> Status: **GUARDIAN MODE ACTIVE — BOUNDARY HOLDING(零违例)**(2026-09-16,DEC-035 轮,DSH 侧编号;V3 侧 DEC-035 = 既有文档轮,R5-03 撞号面)
> Authority: Owner 本轮指令「Task: Producer Frozen Baseline Guardian Mode」(①建立 Consumer Implementation Boundary Audit ②建立 immutable monitoring checklist ③不参与 Consumer Identity Verification 代码实现 ④输出本文件;要求 = 只读检查、零代码、零数据、零 schema,等待 Owner 后续指令)
> Role: Consumer Identity Implementation 阶段启动时的 **Producer 侧守护文件**——冻结基线四类 immutable 的监控清单(M1~M6)+「Consumer 实现不得改变冻结基线」的边界审计。
> 纪律: 本轮唯一新文件 = 本报告(docs-only)+ 台账登记;零脚本、零数据、零 schema、零基线工件覆盖;沿用并衔接 DEC-033(Integrity Record 收口)/ DEC-034(Archive Final Check)结论,不重复、不推翻。

---

## 0. 状态与阶段定位

```text
PRODUCER BASELINE: FINALIZED + ARCHIVED(DEC-033 收口 / DEC-034 归档终检)
CONTRACT v0.2: FROZEN(DEC-032)
CONSUMER IDENTITY: NOT IMPLEMENTED
BOUNDARY: HOLDING(本轮只读审计,零违例)
GUARDIAN MODE: ACTIVE
```

Owner 阶段定位(原文要点):跨过 Contract Design → Contract Freeze → Producer Baseline Freeze → Consumer Identity Design Freeze 节点后,**下一阶段真正风险已从「设计错误」转移到「实现纪律」**。重点不再是继续讨论 Contract,而是确保实现严格满足验证链:

```text
raw bytes → SHA256(raw bytes) → Manifest verification → IR consistency check
   → Consumer Identity Gate → existing Gate/Admission
```

并保持三不变:**Requirement ≠ Capability / Design ≠ Implementation / Consumer ≠ Producer**。

下一阶段禁止(Owner 本轮重申):修改 producer 数据 / manifest / source bytes / IR / freeze artifact。

---

## 1. Consumer Implementation Boundary Audit(Owner Task 1)

### 1.1 边界模型

冻结基线对象全部位于 Producer 仓(`kurt-wong/Aitutors-preprocessing`)并以字节锚定(DEC-034 归档声明:以工件表字节为准,后续变化须 Owner 令 + 新配对快照,不得就地改写)。Consumer Identity Verification 实现的**合法写面 = 仅 V3 仓(`kurt-wong/AITutors-v3`)代码**;对 Producer 基线的一切接触 = **只读**。

| # | 实现步(契约义务链) | Consumer 侧动作 | 对 Producer 基线的接触 | 边界不变式 | 当前状态 |
|---|---|---|---|---|---|
| S1 | raw bytes acquisition | 获取 87 份 source md 原始字节(传输方式未冻结,OQ-12′ = delivery logistics) | 只读 | 任何传输/缓存/落盘副本不得回写 Producer 仓 | **NOT IMPLEMENTED** |
| S2 | SHA256(raw bytes) | 独立重算,与 `manifest.source_content_sha256` 比较 | 只读 | 比较失败 → Consumer 侧 fail-closed;**禁**改 Producer 数据/manifest「对齐」hash | **NOT IMPLEMENTED** |
| S3 | Manifest verification | 身份验证(M = Source Identity Authority) | 只读 | 验证失败 = 拒收/上报;**禁**修补 manifest | **NOT IMPLEMENTED** |
| S4 | IR consistency check | `ir.source_sha256` == `source_content_sha256` 对账(71 ADMITTED / 16 Semantic Pending) | 只读 | 16 Semantic Pending **禁**自动补 IR / LLM 猜测生成 / 静默入题库(DEC-022 Part4);IR 再生成须 Owner 另令 + 新配对快照,**禁** Consumer 实现触发 | **NOT IMPLEMENTED** |
| S5 | Consumer Identity Gate | 不一致 → fail-closed → 拒收 | 无接触 | Gate 逻辑属 V3;**禁**以「修数据」代替「拒收」 | **NOT IMPLEMENTED** |
| S6 | existing Gate/Admission | 既有链不变 | 无接触 | 与基线零耦合(EB-008 P1 已验,属既有能力) | 既有 |

### 1.2 审计确认(本轮 OBSERVED)

1. **基线本体零变化**:post-backfill audit(`2cb980c7…4096`)files map 全量 177 个锚定文件(87 source md + 87 manifest + IR 工件 + R50 基线 + Step1 快照)本轮 `Get-FileHash` 逐一比对 = **checked=177,missing 0,mismatch 0**;
2. **六证据工件 sha256 实测 == 登记值 6/6**(FREEZE-EVIDENCE v1 §1 + Archive Final Report v1 §1.1,见 §2.1);
3. **IR 工件** `data/resolver_ref_r52/resolver_ir.json` sha256 = **`fbcf41ab025fd786614b52d63270160868a2f49ab63121f012905c79f65b04a5`** == post-backfill audit 锚定值(未再生成、未改写);
4. **远端**:本仓 `origin/main` = `e1584bd`(== 本地 HEAD,工作树干净);V3 `origin/main` Observed(本轮)= **`72af28d`**(reachable = TRUE);
5. **结论:Consumer implementation(当前 NOT IMPLEMENTED)不存在任何已发生的基线接触;边界 HOLDING,零违例。**

### 1.3 实现阶段边界条件(前瞻重申,零新裁决)

- bytes 传输方式无论最终形态(git clone / 文件共享 / 对象存储 / API),必须对 Producer 基线**只读**;
- Consumer 侧一切验证失败的唯一合法出口 = **fail-closed + 上报**;修复属 Owner 令 + Producer 侧新配对快照(DEC-034 归档声明),禁 Consumer 侧或协调层自行处置;
- 16 Semantic Pending = Identity Available / Semantic Pending(身份自足,16/16 携 64-hex 身份且字节可达),Consumer 实现须按此消费,禁触发再生成;
- IR 字段名对齐(`source_sha256` → `source_content_sha256`)属 Producer 侧长开项,须令才动,与 Consumer 实现**解耦**——Consumer 实现不得以其未改为由放宽对账,也不得代 Producer 改;
- 以上均为契约与既有裁决(DEC-022/023/025/026/032/034)的重申。

---

## 2. Immutable Monitoring Checklist(Owner Task 2,可复跑)

| 类 | 监控对象 | 锚定载体(权威) | 期望值 | 只读验证方法 | 本轮状态 |
|---|---|---|---|---|---|
| **M1 source bytes hash** | 接口面 87 份 source md | post-backfill audit files map(87 md 行)+ Step1 快照 + R50 基线 | 与锚定值逐文件相等(零漂移) | `Get-FileHash` 逐文件对照 audit files map(本轮已全量跑,§1.2) | **PASS(87/87)** |
| **M2 manifest hash** | 接口面 87 份 manifest(回填后形态) | post-backfill audit files map(87 manifest 行) | == 锚定值;且剥去 `source_content_sha256` 键重序列化 sha == R50 记录值(C8 不变式:差异恰 = 追加一键) | `Get-FileHash` 对照(本轮);剥键复算经 `freeze_evidence_final_check.py` C8 逻辑(DEC-034 轮复跑,输出字节级复现) | **PASS(87/87)** |
| **M3 IR hash** | `data/resolver_ref_r52/resolver_ir.json` | post-backfill audit files map + FREEZE-EVIDENCE 链 | `fbcf41ab025fd786614b52d63270160868a2f49ab63121f012905c79f65b04a5` | `Get-FileHash` 单文件比对 | **PASS(本轮实测相符)** |
| **M4 evidence artifact hash** | 六证据工件(§2.1) | FREEZE-EVIDENCE v1 §1 + Archive Final Report v1 §1.1 | 登记 sha256 全值 | `Get-FileHash` 六文件比对 | **PASS(6/6)** |
| **M5 聚合指纹(辅助)** | 接口面 177 文件 corpus | pre/post audit `corpus_sha256` | pre `4ad3458ba11752d53b5885eb727e9da6ee5726b8eac2a5f0b0d81ca22fd19160` → post `24af8f566e8e2356c29aa99e6b185c5f6f8eaf2df983bd4b6b0669684c240a10` | corpus 算法见 audit 快照;逐文件比对(本轮)为其等价覆盖 | **PASS** |
| **M6 冻结对象四元组(跨仓)** | Contract v0.2 Freeze Artifact | `kurt-wong/AITutors-v3` @ `f4941ff87c0130ee0b79ff6b807c4ec2826b8ff1` / `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` | sha256 `9c6b9063e81fb2a66d85794b280c9d931f1b0074b39abf472033218149b17528`(92,197 bytes) | V3 仓只读:`git show f4941ff:<path>` 字节重导 + `Get-FileHash`;`git merge-base --is-ancestor f4941ff origin/main` | **PASS(Historical 锚 = DEC-031/032 字节重导;is-ancestor 亲验 = DEC-033/034;`f4941ff..origin/main` 契约零 diff 亲验 = DEC-032/034)** |

### 2.1 M4 证据工件锚定表(期望值全值)

| 工件 | sha256 |
|---|---|
| `data/interface_scope_snapshot_step1.json` | `b4f14524473d97b86f5d6a2f8bb03ee794727652a68fa4df4b00d794de98ad99` |
| `data/interface_scope_step2_backfill_report.json` | `d430cc2f6ebdf6553464f9751ade4b02eac6423f0509222a96c4c4666fb6eec1` |
| `data/audit_snapshot_interface_scope_prebackfill.json` | `b11874c472a9fad3051f58c5fc46367dc8d7fc3e5ad961b266edfa55c142dd9c` |
| `data/audit_snapshot_interface_scope_postbackfill.json` | `2cb980c7ca421f5a2c3615053cd3308d5ad1aa078083928724af88d4663a4096` |
| `data/freeze_evidence_final_check.json` | `a707738e5ceae7008eef7a7744d38b7b7ca1c052d936b49e0b31e59f1c5a5c33` |
| `Docs/COORDINATION/INTEGRATION/PREPROCESSING-STEP1-STEP2-VERIFICATION-REPORT-v1.md` | `da97a2f388b8596091bbb9a51fe794a3243515f69680ea231fd3bb4772aebb7c` |

辅助锚:`data/audit_snapshot_R50_input_baseline.json` = `963cd6b1350956e2bbf7427bc5354748aba0ba5e4548864d3658f58608f4ee77`(本轮实测补齐全值;FREEZE-EVIDENCE v1 原登记为前缀)。

### 2.2 监控触发点与偏差协议

- **触发**:①每个协调轮开工前;②V3 Consumer Identity Implementation 每个里程碑后(Owner 令 DSH 复核时);③任何疑似接触基线的事件后;
- **偏差协议**:任一 M 项 mismatch / missing → **STOP**:只报告具体差异(对象 / 期望值 / 实测值),**不自行修复、不重写、不回滚**;处置权 = Owner(基线变化须 Owner 令 + 新配对快照,禁就地改写);
- **复跑纪律**:`scripts/freeze_evidence_final_check.py` 输出路径硬编码为 `data/freeze_evidence_final_check.json`,直接复跑会覆盖已登记工件——复跑须经 scratch 重定向(DEC-034 先例),已登记工件零覆盖;本轮采用的 PowerShell 逐文件比对法零写入,可任意复跑。

---

## 3. Non-Participation Declaration(Owner Task 3)

**DSH 不参与 Consumer Identity Verification 代码实现**——不写 V3 仓代码、不代写实现、不提供实现补丁;DSH 侧角色 = **Producer Frozen Baseline Guardian**(只读验证 + 边界审计 + 监控清单维护)。若 Owner 令 DSH 复核实现成果,复核 ≠ 实现,核验基准 = 契约 §2.3/§5.6.2 验证链 + 五项 NOT IMPLEMENTED 边界不得因 FROZEN / FINALIZED 而松动。

---

## 4. 本轮 Observed 记录(命令 → 结果,2026-09-16)

| 动作 | 结果 |
|---|---|
| `Get-FileHash` × 7(5 数据工件 + R50 + IR 工件) | 全数 == 登记/锚定值 |
| `Get-FileHash`(verification report) | `da97a2f3…bb7c` == 登记值 → **M4 = 6/6** |
| 177 文件全量比对(post-backfill audit files map) | **checked=177, bad=0** |
| 本仓 `git ls-remote origin main` | `e1584bd`(== 本地 HEAD,工作树干净) |
| V3 仓 `git ls-remote origin main` | `72af28d`(reachable = TRUE) |
| 全量测试 | 338 passed / 1 xfailed(与基线一致) |

---

## 5. 结论

```text
BOUNDARY: HOLDING(零违例)
GUARDIAN MODE: ACTIVE
CONSUMER IDENTITY: NOT IMPLEMENTED(五项能力不变)
```

- Consumer Implementation Boundary Audit:**通过**——Consumer 实现的合法写面 = 仅 V3 仓代码;对冻结基线五类禁改对象(producer 数据 / manifest / source bytes / IR / freeze artifact)零接触、零违例;
- Immutable Monitoring Checklist:**M1~M6 全 PASS**(本轮 OBSERVED),触发点与偏差协议在位;
- DSH 不参与 Consumer Identity Verification 代码实现(§3 声明)。

**等待 Owner 后续指令。**

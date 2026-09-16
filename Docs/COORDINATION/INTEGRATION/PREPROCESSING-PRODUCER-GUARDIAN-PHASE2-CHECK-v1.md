# PREPROCESSING-PRODUCER-GUARDIAN-PHASE2-CHECK-v1

> **轮次登记**:本文件承载多轮 Guardian checkpoint —— **轮次 2 = DEC-038(本轮,2026-09-16,G1~G6 新编号体系)**;轮次 1 = DEC-037(2026-09-16,Phase 2 开工前锚点,M1~M6 旧编号,原文存档见**附录 A**)。每轮 Observed 各自独立成立,历史轮次仅存档引用。
> Owner 指令(DEC-038):Consumer Phase 2 开发期间保持 Producer Frozen Baseline 完整性,执行 Guardian checkpoint G1~G6;检查体系改名 —— **G = Guardian Check,M = Consumer Module**(避免与 Consumer M1~M6 模块编号混淆);全程只读(hash 计算 / diff / 读取 / git 验证);报告严格区分 Observed / Historical;Consumer 新增代码不是违例,违例 = Frozen Producer baseline 字节变化;术语纪律(禁 "IR hash OK" 式模糊表述,须区分 Producer IR artifact / Consumer IR reader output / Derived verification result);异常协议 = 任一 mismatch 立即 STOP 仅报告,禁自动恢复 / 禁重新生成 / 禁覆盖旧工件;输出本文档并登记 state.yaml / CURRENT.md / log.md;Guardian only,不参与 Consumer 实现。
> 限制:零代码修改 / 零数据修改 / 零 schema 修改。角色:Guardian only。

## 0. 状态、编号与术语纪律

- `PRODUCER BASELINE: FINALIZED + ARCHIVED`(DEC-033/034)· `CONTRACT v0.2: FROZEN`(DEC-032)· `CONSUMER IDENTITY: NOT IMPLEMENTED`(五项 V3 消费能力,不因 Consumer 侧实现进展自动改变,见 §3);
- `GUARDIAN MODE: ACTIVE`(DEC-035)· `BOUNDARY: HOLDING` · `PHASE 2 SNAPSHOT: ANCHORED`(DEC-037 轮次 1,零 mismatch);
- **编号体系(本轮起强制)**:`G1~G6` = Guardian Check(G1 source bytes / G2 manifest / G3 producer IR / G4 evidence artifacts / G5 corpus snapshots / G6 freeze artifact);`M1~M5(Consumer 侧)` = Consumer Module(如 Phase 2 的 M1 = Manifest Reader)。**Guardian 编号不得使用 Consumer M 系列**;DEC-035 建立的 M1~M6 监控清单自此在 Guardian 语境改称 G1~G6,监控对象与锚定值不变;
- **术语纪律**:禁用 "IR hash OK" 式模糊表述;正确表述 = "**Producer IR artifact hash unchanged**"。三个概念严格区分:**Producer IR artifact**(`data/resolver_ref_r52/resolver_ir.json`,本报告 G3 检查对象)/ **Consumer IR reader output**(V3 侧实现产物,不属基线)/ **Derived verification result**(派生核验结果,不落仓);
- 方法 = 零写入逐文件 sha256 比对法(`Get-FileHash` 只读散列,可任意复跑)+ G6 跨仓字节重导(`cmd /c "git show … > %TEMP%"` + `Get-FileHash` + 即时清理,不落仓);
- 全程只读:基线零接触,已登记工件零覆盖,临时重导不落仓。

## 1. Observed(本轮 = 轮次 2 / DEC-038 实际执行结果,2026-09-16)

### 1.1 G1~G6 全量核验结果(全部本轮重新执行)

| 类 | Guardian 检查对象 | 期望值 | 本轮实测 | 判定 |
|---|---|---|---|---|
| **G1 source bytes** | 接口面 87 份 source md | post-backfill audit files map 锚定值逐文件相等 | 全量比对(md 计数 = 87),逐文件实测 sha256 == 锚定值 | **PASS** |
| **G2 manifest** | 接口面 87 份 manifest(回填后形态)+ audit 快照自身 | 锚定值逐文件相等 + 快照自身 sha 不变 | 全量比对(manifest 计数 = 87);快照自身 sha256 实测 = `2cb980c7ca421f5a2c3615053cd3308d5ad1aa078083928724af88d4663a4096` 相符 | **PASS** |
| **G3 producer IR artifact** | `data/resolver_ref_r52/resolver_ir.json` | `fbcf41ab025fd786614b52d63270160868a2f49ab63121f012905c79f65b04a5` | **Producer IR artifact hash unchanged**(实测 = 期望值,单文件独立散列) | **PASS** |
| **G4 evidence artifacts** | 六证据工件 + R50 辅助锚 | 登记 sha256 全值(§1.2) | **7/7 match=True**(全部本轮重散列) | **PASS** |
| **G5 corpus snapshots** | 接口面 177 文件 corpus 双快照 | pre `4ad3458b…19160` / post `24af8f56…0a10` | pre 快照 `corpus_sha256` 字段实测 = `4ad3458ba11752d53b5885eb727e9da6ee5726b8eac2a5f0b0d81ca22fd19160`;post 快照字段实测 = `24af8f566e8e2356c29aa99e6b185c5f6f8eaf2df983bd4b6b0669684c240a10` | **PASS** |
| **G6 freeze artifact(跨仓)** | Contract v0.2 Freeze Artifact 四元组 | sha256 `9c6b9063e81fb2a66d85794b280c9d931f1b0074b39abf472033218149b17528`(92,197 bytes)+ f4941ff 亲缘 + 契约零 diff | 字节重导 **bytes=92,197 sha256 = `9c6b9063e81fb2a66d85794b280c9d931f1b0074b39abf472033218149b17528` MATCH=True**;`merge-base --is-ancestor f4941ff origin/main` = TRUE(exit 0);`f4941ff..origin/main` 契约 diff = empty(空输出);临时重导文件即时删除,不落仓 | **PASS** |

**聚合计数(OBSERVED 本轮)**:`checked=177 / missing=0 / mismatch=0`(锚 = `data/audit_snapshot_interface_scope_postbackfill.json` files map,n_files=177,其自身 sha256 实测相符;md=87 / manifest=87)。

### 1.2 G4 证据工件逐项实测(期望值 == 实测值,全部本轮重散列)

| 工件 | sha256(期望 == 实测) | match |
|---|---|---|
| `data/interface_scope_snapshot_step1.json` | `b4f14524473d97b86f5d6a2f8bb03ee794727652a68fa4df4b00d794de98ad99` | True |
| `data/interface_scope_step2_backfill_report.json` | `d430cc2f6ebdf6553464f9751ade4b02eac6423f0509222a96c4c4666fb6eec1` | True |
| `data/audit_snapshot_interface_scope_prebackfill.json` | `b11874c472a9fad3051f58c5fc46367dc8d7fc3e5ad961b266edfa55c142dd9c` | True |
| `data/audit_snapshot_interface_scope_postbackfill.json` | `2cb980c7ca421f5a2c3615053cd3308d5ad1aa078083928724af88d4663a4096` | True |
| `data/freeze_evidence_final_check.json` | `a707738e5ceae7008eef7a7744d38b7b7ca1c052d936b49e0b31e59f1c5a5c33` | True |
| `Docs/COORDINATION/INTEGRATION/PREPROCESSING-STEP1-STEP2-VERIFICATION-REPORT-v1.md` | `da97a2f388b8596091bbb9a51fe794a3243515f69680ea231fd3bb4772aebb7c` | True |
| 辅助锚 `data/audit_snapshot_R50_input_baseline.json` | `963cd6b1350956e2bbf7427bc5354748aba0ba5e4548864d3658f58608f4ee77` | True |

### 1.3 双仓时点 Observed(本轮亲验)

- **本仓(canonical ledger)**:开工时 `HEAD` = `056b6d6`(== `origin/main`,`git status -sb` 同步,工作树干净;`056b6d6` = DEC-037 轮记账提交);
- **V3 远端**:`git fetch origin` 首试 **FAIL**(沙箱 `.git/FETCH_HEAD` Permission denied + `schannel SEC_E_NO_CREDENTIALS`,exit 255/128 —— 如实入账,未引用历史结果);宽模式重试 **OK**(exit 0);`git ls-remote origin main` = **`72af28d5854b56fc605e1897fb757703826a6233`**(remote reachable = TRUE);与 DEC-033/034/036/037 同值,**未前进**;远端仍无任何 Consumer 实现提交(全部 docs 提交);
- **V3 本地工作树(本轮只读观察,新事实)**:V3 本地 `main` 与 `origin/main` 无领先/落后(tracked 面同步),但工作树存在 **untracked Consumer 实现文件与文档**,包括:代码 `backend/app/core/raw_bytes_identity.py`、`backend/app/core/manifest_identity.py`、`backend/tests/test_raw_bytes_identity.py`、`backend/tests/test_manifest_identity.py`、`backend/tests/test_adversarial_raw_bytes.py`;文档 `PREPROCESSING-V3-CONSUMER-IDENTITY-VERIFICATION-DESIGN-v1.md / -v1.1.md`、`-IMPLEMENTATION-PLAN-v1.md`、`-IMPLEMENTATION-READINESS-v1.md`、`-IMPLEMENTATION-REPORT-PHASE1.md`、`-IMPLEMENTATION-REPORT-PHASE2.md`、`PREPROCESSING-V3-CONTRACT-CONSUMER-REVIEW.md`、`PREPROCESSING-V3-CONTRACT.md`、`PREPROCESSING-V3-CONTRACT-v0.2-DRAFT-SKELETON.md`;
- **REPORTED(V3 本地报告自述,untracked 未 commit 未 push,按台账纪律属 REPORTED 级)**:Phase 1 实现报告 = `Status: IMPLEMENTED / TESTS PASS / PHASE 1 ONLY`(模块 `raw_bytes_identity.py` v1.0.0);Phase 2 实现报告 = `PHASE 2 COMPLETE / WAITING OWNER PHASE 3 AUTHORIZATION`(M1 Manifest Reader = `manifest_identity.py`,自称 17/17 单元测试 PASS);
- **REPORTED vs OBSERVED 分账**:Owner 宣告 "Consumer Phase 1 已完成 / Phase 2 = M1 Manifest Reader"(REPORTED);V3 远端实测无实现提交(OBSERVED),实现仅存于 V3 本地工作树(OBSERVED 文件清单,REPORTED 完成度自述)。三者不混写;
- **Consumer 边界判读**:上述新增代码与文档**全部落在 V3 仓**(合法写面),**不构成违例**;违例判断标准 = 冻结对象是否变化,而非代码是否新增 —— 本轮 G1~G6 实测冻结对象零变化(§1.1),**零违例**。

### 1.4 测试基线(OBSERVED 本轮)

- 本轮复跑全量测试:`338 passed, 1 xfailed`(与登记基线一致)。

## 2. Historical(历史登记结果,仅存档引用,不冒充本轮观察)

- **DEC-037 轮(轮次 1,Phase 2 开工前锚点,M1~M6 旧编号)**:全 PASS 零 mismatch;本仓 `HEAD` = `bebd9e1`,V3 `origin/main` = `72af28d`(fetch 首试沙箱拒绝,宽模式重试 OK);全文见附录 A;
- **DEC-036 轮(Phase 1 开工前快照)**:M1~M6 全 PASS;本仓 `origin/main` = `27727c4`,V3 `origin/main` = `72af28d`(Recv failure 重试);
- **DEC-035 轮(Guardian Mode 启动)**:BOUNDARY HOLDING 零违例,bad=0;本仓 `e1584bd` / V3 `72af28d`;
- **DEC-034 轮(Archive Final Check)**:四项 immutable 终检全 PASS;V3 `72af28d`;
- **DEC-033 轮(Frozen Baseline Final Integrity)**:六工件 6/6 + C1-C9 全 PASS;V3 `72af28d`;
- **DEC-032 轮(CONTRACT FROZEN 登记)**:V3 `4daecf0b`,契约重导 `9c6b9063…7528`;
- 上述历史观测**均未被用作本轮判定依据**;§1 全部结论均出自本轮实际执行的散列比对与 git 实测。

## 3. 冻结与禁改重申(Phase 2 开发期间持续有效)

- 冻结对象唯一有效四元组:`kurt-wong/AITutors-v3` @ `f4941ff87c0130ee0b79ff6b807c4ec2826b8ff1` / `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` / sha256 `9c6b9063…7528`(92,197 bytes);`c6e771c` / `c8d89586…1032` = 历史登记,勿引用;
- Phase 2 期间五类禁改对象(Consumer 实现合法写面 = 仅 V3 仓代码):**producer 数据 / manifest / source bytes / Producer IR artifact / freeze artifact**;
- **CONSUMER IDENTITY: NOT IMPLEMENTED 的登记口径**:五项能力(raw bytes acquisition / SHA256 独立验证 / Manifest identity verification / IR identity verification / identity gate)是 **V3 远端已提交实现**口径;V3 本地 REPORTED 的 Phase 1/Phase 2 实现在 commit + push 前不改变该登记(Requirement ≠ Capability;REPORTED ≠ OBSERVED);后续以 Owner 令触发的只读复核为准;
- 基线任何后续变化须 **Owner 令 + 新配对快照**,不得就地改写(DEC-034 归档声明持续有效)。

## 4. Trigger 状态与复检预案

- **Trigger ②(post-Phase 1 recheck)= ARMED,未按实现面执行**:Phase 1 实现目前仅存于 V3 本地工作树(untracked,未 push;§1.3),远端无实现提交;本轮已对基线五类对象执行全量 G1~G6 复检(覆盖 Trigger ② 的检查面),结果全 PASS;
- **触发点(持续有效)**:每轮开工前 + Consumer 实现里程碑后(如 V3 实现 push 至远端)+ 疑似接触事件后 + Owner 令;
- **判读纪律**:Consumer 侧新增代码提交本身不构成违例(合法写面 = V3 仓代码);违例仅指五类只读对象出现任何字节变化;判断标准 = "冻结对象是否变化",不是"代码是否新增"。

## 5. 偏差协议(红线)

- 任何 hash mismatch / missing → **STOP**:仅报告具体差异(对象 / 期望值 / 实测值);**禁止自动恢复、禁止重新生成、禁止覆盖旧工件**;
- 处置权 = **Owner**(基线变化须 Owner 令 + 新配对快照);
- 复跑纪律:`scripts/freeze_evidence_final_check.py` 输出路径硬编码,禁直接复跑(会覆盖已登记工件);本轮沿用零写入比对法,可任意复跑;
- Observed / Historical 分账、REPORTED ≠ OBSERVED、case id 不重编号,持续有效。

## 6. 结论(轮次 2 / DEC-038)

- **G1~G6:全 PASS,零 mismatch,零 missing,零 STOP 触发,零违例**;
- 检查性质:只读;**零代码修改 / 零数据修改 / 零 schema 修改**;基线工件零覆盖(G6 临时重导写系统临时目录并即时删除,不落仓);
- 零新架构裁决;已裁六项未重开;DSH 不参与 Consumer 代码实现(Guardian only)。

**结论:`BOUNDARY: HOLDING` —— Consumer Phase 2 开发期间 Frozen Baseline 完整性检查通过,Guardian checkpoint(轮次 2)已登记。等待 Owner 下一步指令。**

---

## 附录 A:轮次 1 存档(DEC-037,2026-09-16,原文保留;M1~M6 = 当时编号,即今 G1~G6)

> DEC-037(DSH 侧编号;与 V3 侧编号潜在撞号,R5-03 面已知)· Owner 指令:Consumer Phase 2 开工前 Baseline Check —— ①只读检查 source bytes / manifest / producer IR / evidence artifacts / freeze artifact;②不修改任何内容;③输出本文档;④报告必须区分 Observed 与 Historical;⑤禁用历史结果冒充当前观察 / 禁自动修复 mismatch / 禁修改 producer 数据;⑥若发现 mismatch 立即 STOP 仅报告,否则登记 Guardian checkpoint;⑦不参与 Consumer 代码实现。

### A.0 状态与阶段定位(轮次 1)

- `PRODUCER BASELINE: FINALIZED + ARCHIVED`(DEC-033/034)· `CONTRACT v0.2: FROZEN`(DEC-032)· `CONSUMER IDENTITY: NOT IMPLEMENTED`;
- `GUARDIAN MODE: ACTIVE`(DEC-035)· `BOUNDARY: HOLDING`· DEC-036 `PHASE 1 SNAPSHOT: ANCHORED`(零 mismatch);
- 本轮 = Consumer Phase 2 开工前 Baseline Check(Trigger ①:每轮开工前);方法 = DEC-035 M1~M6 监控清单零写入逐文件 sha256 比对法 + M6 跨仓字节重导;
- 全程只读:基线零接触,已登记工件零覆盖,临时重导不落仓。

### A.1 Observed(轮次 1 实际执行结果,2026-09-16 Phase 2 开工前)

| 类 | 监控对象 | 期望值 | 该轮实测 | 判定 |
|---|---|---|---|---|
| **M1 source bytes** | 接口面 87 份 source md | post-backfill audit files map 锚定值逐文件相等 | 全量比对(md 计数 = 87),逐文件实测 sha256 == 锚定值 | **PASS** |
| **M2 manifest** | 接口面 87 份 manifest(回填后形态) | 锚定值逐文件相等 + audit 快照自身 sha 不变 | 全量比对(manifest 计数 = 87);快照自身 sha256 实测 = `2cb980c7…4096` 相符 | **PASS** |
| **M3 producer IR** | `data/resolver_ref_r52/resolver_ir.json` | `fbcf41ab…b04a5` | 实测 = 期望值(单文件独立散列 + 锚定表内含双重覆盖) | **PASS** |
| **M4 evidence artifacts** | 六证据工件 + R50 辅助锚 | 登记 sha256 全值 | **7/7 match=True** | **PASS** |
| **M5 corpus 聚合** | 接口面 177 文件 corpus 双值 | pre `4ad3458b…19160` / post `24af8f56…0a10` | 双快照字段实测相符;逐文件 177/177 等价覆盖 | **PASS** |
| **M6 freeze artifact(跨仓)** | Contract v0.2 Freeze Artifact 四元组 | sha256 `9c6b9063…7528`(92,197 bytes)+ f4941ff 亲缘 + 契约零 diff | 字节重导 bytes=92,197 sha256 = `9c6b9063…7528` MATCH=True;is-ancestor TRUE;契约 diff empty;临时重导即时删除 | **PASS** |

**聚合计数(轮次 1 OBSERVED)**:`checked=177 / missing=0 / mismatch=0`(锚快照自身 sha256 = `2cb980c7ca421f5a2c3615053cd3308d5ad1aa078083928724af88d4663a4096` 实测相符)。M4 逐项全值与轮次 2 §1.2 表一致(两轮独立重散列,均 match=True)。

**轮次 1 时点双仓 Observed**:本仓 `HEAD` = `bebd9e1`(== `origin/main`,工作树干净);V3 `git fetch origin` 首试 FAIL(沙箱 `.git/FETCH_HEAD` Permission denied,宽模式重试 OK);`origin/main` = **`72af28d5854b56fc605e1897fb757703826a6233`**(reachable = TRUE);远端提交链 `72af28d`(restart-prompt v1.66 治理轮)→ `2a723a6` → `3b3b397` → `4daecf0` → `305bd81` → `f4941ff`,全部 docs 提交,**尚无 Consumer Phase 1 / Phase 2 实现提交**。REPORTED(Owner 宣告 Phase 2 开工)与 OBSERVED 分账;DEC-036 锚点后远端零新增提交 → 该快照构成 **Phase 2 开工前基线锚点**。

**轮次 1 测试基线**:`338 passed, 1 xfailed`。

### A.2 轮次 1 Historical(当时存档引用)

DEC-036(M1~M6 全 PASS,`27727c4` / `72af28d`)· DEC-035(BOUNDARY HOLDING,`e1584bd`)· DEC-034(四项 immutable 终检)· DEC-033(六工件 6/6)· DEC-032(`4daecf0b`)。

### A.3 轮次 1 结论

`BOUNDARY: HOLDING` —— Consumer Phase 2 开工前基线检查通过,Guardian checkpoint(轮次 1)已登记(state.yaml `producer_guardian_phase2` 块 + DEC-037 + CURRENT.md + log.md + ODR v1.18)。

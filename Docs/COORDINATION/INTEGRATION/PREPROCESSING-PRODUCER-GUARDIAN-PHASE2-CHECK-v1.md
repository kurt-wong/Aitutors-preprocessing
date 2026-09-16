# PREPROCESSING-PRODUCER-GUARDIAN-PHASE2-CHECK-v1

> DEC-037(DSH 侧编号;与 V3 侧编号潜在撞号,R5-03 面已知)· 2026-09-16 · DSH = Producer Frozen Baseline Guardian(Guardian only)
> Owner 指令:Consumer Phase 2 开工前 Baseline Check —— ①只读检查 source bytes / manifest / producer IR / evidence artifacts / freeze artifact;②不修改任何内容;③输出本文档;④报告必须区分 Observed(本轮实际执行结果)与 Historical(历史登记结果);⑤禁用历史结果冒充当前观察 / 禁自动修复 mismatch / 禁修改 producer 数据;⑥若发现 mismatch 立即 STOP 仅报告,否则登记 Guardian checkpoint;⑦不参与 Consumer 代码实现。
> 限制:零代码修改 / 零数据修改 / 零 schema 修改。角色:Guardian only。

## 0. 状态与阶段定位

- `PRODUCER BASELINE: FINALIZED + ARCHIVED`(DEC-033/034)· `CONTRACT v0.2: FROZEN`(DEC-032)· `CONSUMER IDENTITY: NOT IMPLEMENTED`;
- `GUARDIAN MODE: ACTIVE`(DEC-035)· `BOUNDARY: HOLDING`· DEC-036 `PHASE 1 SNAPSHOT: ANCHORED`(零 mismatch);
- **本轮 = Consumer Phase 2 开工前 Baseline Check(Trigger ①:每轮开工前)**;方法 = DEC-035 M1~M6 监控清单零写入逐文件 sha256 比对法(Python 只读散列,与 `Get-FileHash` 法等价,零写入可任意复跑)+ M6 跨仓字节重导(`cmd /c "git show … > %TEMP%"` + `Get-FileHash` + 即时清理);
- 全程只读:基线零接触,已登记工件零覆盖,临时重导不落仓。

## 1. Observed(本轮实际执行结果,2026-09-16 Phase 2 开工前)

### 1.1 M1~M6 全量核验结果

| 类 | 监控对象 | 期望值 | 本轮实测 | 判定 |
|---|---|---|---|---|
| **M1 source bytes** | 接口面 87 份 source md | post-backfill audit files map 锚定值逐文件相等 | 全量比对(md 计数 = 87),逐文件实测 sha256 == 锚定值 | **PASS** |
| **M2 manifest** | 接口面 87 份 manifest(回填后形态) | 锚定值逐文件相等 + audit 快照自身 sha 不变 | 全量比对(manifest 计数 = 87);快照自身 sha256 实测 = `2cb980c7…4096` 相符 | **PASS** |
| **M3 producer IR** | `data/resolver_ref_r52/resolver_ir.json` | `fbcf41ab025fd786614b52d63270160868a2f49ab63121f012905c79f65b04a5` | 实测 = 期望值(单文件独立散列 + 锚定表内含双重覆盖) | **PASS** |
| **M4 evidence artifacts** | 六证据工件 + R50 辅助锚 | 登记 sha256 全值(§1.2) | **7/7 match=True** | **PASS** |
| **M5 corpus 聚合** | 接口面 177 文件 corpus 双值 | pre `4ad3458b…19160` / post `24af8f56…0a10` | pre 快照 `corpus_sha256` 字段 = `4ad3458ba11752d53b5885eb727e9da6ee5726b8eac2a5f0b0d81ca22fd19160`;post 快照字段 = `24af8f566e8e2356c29aa99e6b185c5f6f8eaf2df983bd4b6b0669684c240a10`;逐文件 177/177 等价覆盖 | **PASS** |
| **M6 freeze artifact(跨仓)** | Contract v0.2 Freeze Artifact 四元组 | sha256 `9c6b9063e81fb2a66d85794b280c9d931f1b0074b39abf472033218149b17528`(92,197 bytes)+ f4941ff 亲缘 + 契约零 diff | 字节重导 **bytes=92,197 sha256 = `9c6b9063e81fb2a66d85794b280c9d931f1b0074b39abf472033218149b17528` MATCH=True**;`merge-base --is-ancestor f4941ff origin/main` = TRUE(exit 0);`f4941ff..origin/main` 契约 diff = empty(exit 0,空输出);临时重导文件即时删除 | **PASS** |

**聚合计数(OBSERVED)**:`checked=177 / missing=0 / mismatch=0`(锚 = `data/audit_snapshot_interface_scope_postbackfill.json` files map,n_files=177,其自身 sha256 = `2cb980c7ca421f5a2c3615053cd3308d5ad1aa078083928724af88d4663a4096` 实测相符)。

### 1.2 M4 证据工件逐项实测(期望值 == 实测值,全部本轮重散列)

| 工件 | sha256(期望 == 实测) | match |
|---|---|---|
| `data/interface_scope_snapshot_step1.json` | `b4f14524473d97b86f5d6a2f8bb03ee794727652a68fa4df4b00d794de98ad99` | True |
| `data/interface_scope_step2_backfill_report.json` | `d430cc2f6ebdf6553464f9751ade4b02eac6423f0509222a96c4c4666fb6eec1` | True |
| `data/audit_snapshot_interface_scope_prebackfill.json` | `b11874c472a9fad3051f58c5fc46367dc8d7fc3e5ad961b266edfa55c142dd9c` | True |
| `data/audit_snapshot_interface_scope_postbackfill.json` | `2cb980c7ca421f5a2c3615053cd3308d5ad1aa078083928724af88d4663a4096` | True |
| `data/freeze_evidence_final_check.json` | `a707738e5ceae7008eef7a7744d38b7b7ca1c052d936b49e0b31e59f1c5a5c33` | True |
| `Docs/COORDINATION/INTEGRATION/PREPROCESSING-STEP1-STEP2-VERIFICATION-REPORT-v1.md` | `da97a2f388b8596091bbb9a51fe794a3243515f69680ea231fd3bb4772aebb7c` | True |
| 辅助锚 `data/audit_snapshot_R50_input_baseline.json` | `963cd6b1350956e2bbf7427bc5354748aba0ba5e4548864d3658f58608f4ee77` | True |

### 1.3 Phase 2 开工时点 Observed(双仓,本轮亲验)

- 本仓(canonical ledger):开工时 `HEAD` = `bebd9e1`(== `origin/main`,工作树干净;`bebd9e1` = DEC-036 轮后的 RS.MD 刷新记账提交 `b4367e7` + 1);
- V3 仓:`git fetch origin` = **OK**(首试沙箱 `.git/FETCH_HEAD` Permission denied,宽模式重试成功——沙箱文件策略,非仓库问题,如实入账);`origin/main` = **`72af28d5854b56fc605e1897fb757703826a6233`**(remote reachable = TRUE);
- V3 远端最新提交链(本轮 `git log origin/main` 实测,自上而下):`72af28d`(restart-prompt v1.67 治理轮)→ `2a723a6`(会话 bootstrap 文档)→ `3b3b397`(V3 侧 DEC-036 Contract FROZEN 登记)→ `4daecf0`(V3 侧 DEC-035)→ `305bd81`(DEC-034)→ `f4941ff`(DEC-033 Freeze Artifact)→ … ——**全部为 docs 提交,V3 远端尚无 Consumer Phase 1 / Phase 2 实现提交**;
- **REPORTED vs OBSERVED 分账**:Owner 指令宣告"Consumer Phase 2 开工"(REPORTED);V3 远端实测未见任何实现提交(OBSERVED)。二者不混写:Guardian 仅记录事实——远端字节面未出现实现提交,若 Phase 1 工作存在于 V3 本地未 push,则不属本轮可观察范围;
- 判读:DEC-036 的 Phase 1 开工前基线锚点在本轮依然有效(远端 `72af28d` 未前进,锚点后零新增提交),故本快照同时构成 **Phase 2 开工前基线锚点**。

### 1.4 测试基线(OBSERVED)

- 本轮复跑全量测试:`338 passed, 1 xfailed`(与登记基线一致)。

## 2. Historical(历史登记结果,仅存档引用,不冒充本轮观察)

- **DEC-036 轮(Phase 1 开工前快照)**:M1~M6 全 PASS,177/177 + 证据 7/7 + 冻结四元组字节级相符;本仓 `origin/main` = `27727c4`,V3 `origin/main` = `72af28d`(fetch 首试 Recv failure 重试 OK);
- **DEC-035 轮(Guardian Mode 启动)**:BOUNDARY HOLDING 零违例,177 锚定文件全量比对 bad=0;M1~M6 清单建立;本仓 `origin/main` = `e1584bd`,V3 `origin/main` = `72af28d`;
- **DEC-034 轮(Archive Final Check)**:四项 immutable 终检全 PASS;V3 `origin/main` = `72af28d`(Observed 当轮),Historical = DEC-031 `305bd81` / DEC-032 `4daecf0b` / DEC-033 首试失败 + 重试;
- **DEC-033 轮(Frozen Baseline Final Integrity)**:六工件 6/6 相符,C1-C9 复跑全 PASS;V3 `origin/main` = `72af28d`;
- **DEC-032 轮(CONTRACT FROZEN 登记)**:V3 `origin/main` = `4daecf0b`,契约字节重导 `9c6b9063…7528`;
- 上述历史观测**均未被用作本轮判定依据**;本轮 §1 全部结论均出自本轮实际执行的散列比对与 git 实测。

## 3. 冻结与禁改重申(Phase 2 期间持续有效)

- 冻结对象唯一有效四元组:`kurt-wong/AITutors-v3` @ `f4941ff87c0130ee0b79ff6b807c4ec2826b8ff1` / `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` / sha256 `9c6b9063…7528`(92,197 bytes);`c6e771c` / `c8d89586…1032` = 历史登记,勿引用;
- Phase 2 期间五类禁改对象(Consumer 实现合法写面 = 仅 V3 仓代码):**producer 数据 / manifest / source bytes / IR / freeze artifact**;
- 基线任何后续变化须 **Owner 令 + 新配对快照**,不得就地改写(DEC-034 归档声明持续有效);
- 五项 V3 消费能力 NOT IMPLEMENTED 不因 FROZEN / FINALIZED / 本轮快照而松动(Requirement ≠ Capability;Freeze 不含 bytes verification / identity gate / IR verification 三项实现)。

## 4. Phase 1 Trigger ② 状态与 Phase 2 复检预案

- **Trigger ②(post-Phase 1 recheck)状态 = ARMED,未执行**:本轮实测 V3 远端无任何 Phase 1 实现提交(§1.3),无实现对象可复核;若 Phase 1 实现后续 push 至 V3 远端,按 DEC-036 既定预案执行只读复检(检查面 = M1 producer data / M2 manifest / M3 IR / M6 freeze artifact + M4 辅助);
- **Phase 2 触发点**:每轮开工前 + Consumer 实现里程碑后 + 疑似接触事件后(DEC-035 清单持续有效);本轮为 Phase 2 开工前锚点;
- **判读纪律**:Consumer 侧新增代码提交本身不构成违例(合法写面 = V3 仓代码);违例仅指五类只读对象出现任何字节变化。

## 5. 偏差协议(红线)

- 任何 hash mismatch / missing → **STOP**:仅报告具体差异(对象 / 期望值 / 实测值),禁止自动修复——不自修、不重写、不回滚、不改锚;
- 处置权 = **Owner**(基线变化须 Owner 令 + 新配对快照);
- 复跑纪律:`scripts/freeze_evidence_final_check.py` 输出路径硬编码,禁直接复跑(会覆盖已登记工件);本轮沿用零写入比对法,可任意复跑;
- Observed / Historical 分账、REPORTED ≠ OBSERVED、case id 不重编号,持续有效。

## 6. 结论

- **M1~M6:全 PASS,零 mismatch,零 missing,零 STOP 触发**;
- 检查性质:只读;**零代码修改 / 零数据修改 / 零 schema 修改**;基线工件零覆盖(M6 临时重导写系统临时目录并即时删除,不落仓);
- 零新架构裁决;已裁六项未重开;DSH 不参与 Consumer 代码实现(Guardian only)。

**结论:`BOUNDARY: HOLDING` —— Consumer Phase 2 开工前基线检查通过,Guardian checkpoint 已登记。等待 Owner 下一步指令。**

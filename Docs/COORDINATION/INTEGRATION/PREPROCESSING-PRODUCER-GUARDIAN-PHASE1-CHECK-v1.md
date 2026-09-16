# PREPROCESSING-PRODUCER-GUARDIAN-PHASE1-CHECK-v1

> DEC-036(DSH 侧编号;与 V3 侧 DEC-036 撞号,R5-03 面已知)· 2026-09-16 · DSH = Producer Frozen Baseline Guardian(Guardian only)
> Owner 指令:Producer Frozen Baseline Guardian During Consumer Phase 1 —— ①Phase 1 开工前 baseline snapshot check(source bytes hash / manifest hash / IR hash / evidence artifact);②Consumer Phase 1 完成后只读检查(确认 Consumer 代码提交未修改 producer data / manifest / IR / freeze artifact);③任何 hash mismatch → STOP 仅报告,禁止自动修复;④输出本文档。
> 限制:零代码修改 / 零数据修改 / 零 schema 修改。角色:Guardian only。

## 0. 状态与阶段定位

- `PRODUCER BASELINE: FINALIZED + ARCHIVED`(DEC-033/034)· `CONTRACT v0.2: FROZEN`(DEC-032)· `CONSUMER IDENTITY: NOT IMPLEMENTED`;
- `GUARDIAN MODE: ACTIVE`(DEC-035)· `BOUNDARY: HOLDING`;
- **本轮 = Consumer Phase 1 开工前基线快照(Trigger ①:每轮开工前)**;Phase 1 完成后复检(Trigger ②)已armed,见 §3;
- 验证方法 = DEC-035 M1~M6 监控清单的零写入 PowerShell 逐文件 `Get-FileHash` 比对法 + M6 跨仓字节重导(`cmd /c "git show … > %TEMP%"` + `Get-FileHash` + 即时清理);全程只读,基线零接触。

## 1. Phase 1 开工前 Baseline Snapshot(OBSERVED,本轮实测)

### 1.1 M1~M6 全量核验结果

| 类 | 监控对象 | 期望值 | 本轮实测 | 判定 |
|---|---|---|---|---|
| **M1 source bytes** | 接口面 87 份 source md | post-backfill audit files map 锚定值逐文件相等 | 全量比对(md 计数 = 87) | **PASS** |
| **M2 manifest** | 接口面 87 份 manifest(回填后形态) | 锚定值逐文件相等(C8 剥键不变式承接于 pre/post 双快照) | 全量比对(manifest 计数 = 87) | **PASS** |
| **M3 IR** | `data/resolver_ref_r52/resolver_ir.json` | `fbcf41ab025fd786614b52d63270160868a2f49ab63121f012905c79f65b04a5` | 实测相符(锚定表逐项比对内含) | **PASS** |
| **M4 evidence** | 六证据工件 + R50 辅助锚 | 登记 sha256 全值(§1.2) | 6/6 + R50 全部 match=True | **PASS** |
| **M5 corpus 聚合** | 接口面 177 文件 corpus | post `24af8f566e8e2356c29aa99e6b185c5f6f8eaf2df983bd4b6b0669684c240a10` | post-backfill audit 快照 `corpus_sha256` 字段 = 期望值;逐文件 177/177 等价覆盖 | **PASS** |
| **M6 冻结对象四元组** | Contract v0.2 Freeze Artifact(跨仓) | sha256 `9c6b9063…7528`(92,197 bytes)+ f4941ff 亲缘 + 契约零 diff | 字节重导 bytes=92,197 sha256=**`9c6b9063e81fb2a66d85794b280c9d931f1b0074b39abf472033218149b17528`** MATCH=True;`merge-base --is-ancestor f4941ff origin/main` = TRUE(exit 0);`f4941ff..origin/main` 契约 diff = empty;临时重导文件已清理 | **PASS** |

**聚合计数(OBSERVED)**:`checked=177 / missing=0 / mismatch=0`(锚 = `data/audit_snapshot_interface_scope_postbackfill.json` files map,其自身 sha256 = `2cb980c7…4096` 实测相符)。

### 1.2 M4 证据工件逐项实测(期望值 == 实测值)

| 工件 | sha256(期望 == 实测) | match |
|---|---|---|
| `data/interface_scope_snapshot_step1.json` | `b4f14524473d97b86f5d6a2f8bb03ee794727652a68fa4df4b00d794de98ad99` | True |
| `data/interface_scope_step2_backfill_report.json` | `d430cc2f6ebdf6553464f9751ade4b02eac6423f0509222a96c4c4666fb6eec1` | True |
| `data/audit_snapshot_interface_scope_prebackfill.json` | `b11874c472a9fad3051f58c5fc46367dc8d7fc3e5ad961b266edfa55c142dd9c` | True |
| `data/audit_snapshot_interface_scope_postbackfill.json` | `2cb980c7ca421f5a2c3615053cd3308d5ad1aa078083928724af88d4663a4096` | True |
| `data/freeze_evidence_final_check.json` | `a707738e5ceae7008eef7a7744d38b7b7ca1c052d936b49e0b31e59f1c5a5c33` | True |
| `Docs/COORDINATION/INTEGRATION/PREPROCESSING-STEP1-STEP2-VERIFICATION-REPORT-v1.md` | `da97a2f388b8596091bbb9a51fe794a3243515f69680ea231fd3bb4772aebb7c` | True |
| 辅助锚 `data/audit_snapshot_R50_input_baseline.json` | `963cd6b1350956e2bbf7427bc5354748aba0ba5e4548864d3658f58608f4ee77` | True |

### 1.3 Phase 1 开工时点 Observed(双仓)

- 本仓(canonical ledger)`origin/main` = `27727c4`(`27727c46dfbc7127cee0d60031c66c6027d9484c`,DEC-035 轮 push 后亲验一致;本轮开工时工作树干净);
- V3 仓 `origin/main` = **`72af28d`**(`72af28d5854b56fc605e1897fb757703826a6233`;fetch 首试 Recv failure: Connection was reset,重试 OK 后亲验;与 DEC-033/034 轮 Observed 同值,**未前进**);
- **判读:`72af28d` = `docs:` 提交(V3 侧 DEC-036 Contract FROZEN 登记后治理轮),V3 远端尚无 Consumer Phase 1 实现提交 → 本快照即为 Phase 1 开工前基线锚点**;Historical 分账:DEC-032 时点 `4daecf0b` 等历史观测仅存档引用,不混入本轮 Observed。

## 2. 冻结与禁改重申(Phase 1 期间持续有效)

- 冻结对象唯一有效四元组:`kurt-wong/AITutors-v3` @ `f4941ff87c0130ee0b79ff6b807c4ec2826b8ff1` / `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` / sha256 `9c6b9063…7528`(92,197 bytes);任何契约文本变更 = 新 document sha256 = 不再是本冻结对象;
- Phase 1 期间五类禁改对象(Consumer 实现合法写面 = 仅 V3 仓代码):**producer 数据 / manifest / source bytes / IR / freeze artifact**;
- 基线任何后续变化须 **Owner 令 + 新配对快照**,不得就地改写(DEC-034 归档声明持续有效);
- 五项 V3 消费能力 NOT IMPLEMENTED 不因 FROZEN / FINALIZED / 本轮快照而松动。

## 3. Consumer Phase 1 完成后只读检查预案(Trigger ②,已 armed)

**触发条件**:V3 远端出现 Consumer Phase 1 实现提交(Owner 令 DSH 复核,或疑似接触事件)。

**检查项(Owner 指令原文映射)**:

| Owner 确认项 | 只读检查方法 | 通过标准 |
|---|---|---|
| Consumer 代码提交未修改 **producer data** | M1:177 锚定文件全量 `Get-FileHash` 比对(87 md 行) | checked=87 / mismatch=0 / missing=0 |
| 未修改 **manifest** | M2:同表 87 manifest 行比对 + audit 快照自身 sha | checked=87 / mismatch=0;快照 sha 不变 |
| 未修改 **IR** | M3:`resolver_ir.json` 单文件比对 | == `fbcf41ab…b04a5` |
| 未修改 **freeze artifact** | M6:跨仓字节重导 + is-ancestor + `f4941ff..origin/main` 契约 diff | sha == `9c6b9063…7528` + 亲缘 TRUE + diff empty |
| (辅助)证据工件 | M4 六工件 + R50 逐项比对 | 7/7 match |

**判读纪律**:Consumer 侧新增代码提交本身不构成违例(合法写面 = V3 仓代码);违例仅指上述只读对象出现任何字节变化。检查输出 = 只读 Observed 记录,不修改任何被检对象。

## 4. 偏差协议(红线)

- 任何 hash mismatch / missing → **STOP**:仅报告具体差异(对象 / 期望值 / 实测值),**禁止自动修复**——不自修、不重写、不回滚、不改锚;
- 处置权 = **Owner**(基线变化须 Owner 令 + 新配对快照);
- 复跑纪律:`scripts/freeze_evidence_final_check.py` 输出路径硬编码,禁直接复跑(会覆盖已登记工件);本轮沿用零写入比对法,可任意复跑;
- Observed/Historical 分账、REPORTED ≠ OBSERVED、case id 不重编号,持续有效。

## 5. 本轮 Observed 记录与结论

- 检查性质:只读;**零代码修改 / 零数据修改 / 零 schema 修改**;基线工件零覆盖(M6 临时重导写入系统临时目录并即时删除,不落仓);
- 双仓 Observed:本仓 `origin/main` = `27727c4`;V3 `origin/main` = `72af28d`(reachable TRUE,无 Consumer Phase 1 提交);
- M1~M6:**全 PASS**(177/177 + 证据 7/7 + 冻结四元组字节级相符);
- 零新架构裁决;已裁六项未重开;DSH 不参与 Consumer Identity Verification 代码实现(Guardian only)。

**结论:`BOUNDARY: HOLDING` —— Consumer Phase 1 开工前基线快照已锚定,零 mismatch,零 STOP 触发。等待 Phase 1 完成后 Trigger ② 复检或 Owner 下一步指令。**

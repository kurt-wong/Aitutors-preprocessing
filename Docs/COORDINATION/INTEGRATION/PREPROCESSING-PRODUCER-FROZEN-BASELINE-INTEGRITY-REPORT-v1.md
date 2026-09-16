# PRODUCER FROZEN BASELINE INTEGRITY REPORT v1

> Status: **PRODUCER BASELINE FROZEN — INTEGRITY VERIFIED**(2026-09-16,Contract v0.2 FROZEN(DEC-032)后保全确认轮)
> Authority: Owner 本轮指令「Contract v0.2 Frozen 后,Producer Baseline 保全确认」(Task 1-3)
> Role: 冻结后 Producer 数据基线不可变性确认——证据工件可访问性 + 只读一致性复验 + 不可变性证明。
> 纪律: 本轮**零数据动作**——未修改任何数据 / manifest / IR / Contract;未触碰任何已登记工件字节;唯一新文件 = 本报告(docs-only)。

---

## 0. 一句话结论

```text
Producer baseline frozen — 全部 PASS,零漂移、零 BLOCKER。
Consumer implementation separate — 五项 V3 消费能力仍 NOT IMPLEMENTED,与本基线保全互不构成状态变化。
```

复验方式:不信任何先前报告的结论,本轮从当前磁盘字节独立重新枚举、重新计算 SHA256、与 Step 1 快照 / Step 2 报告 / R50 基线 / pre+post audit 快照交叉对账(复跑 `scripts/freeze_evidence_final_check.py` 判定逻辑,输出重定向 scratch,已登记工件零覆盖)。

---

## 1. Artifact References(Task 1:Freeze 后四类证据全部可访问)

六工件本轮逐一 `Test-Path` 可达 + `Get-FileHash SHA256` 实测 + `git ls-files` 确认在 HEAD 跟踪,实测值与 FREEZE-EVIDENCE v1 §1 登记值**逐一相符**:

| 工件(角色) | 路径 | 登记 sha256 == 本轮实测 | bytes | commit |
|---|---|---|---|---|
| Step 1 snapshot | `data/interface_scope_snapshot_step1.json` | `b4f14524473d97b86f5d6a2f8bb03ee794727652a68fa4df4b00d794de98ad99` ✅ | 75,185 | `e70807b`(2026-09-16 15:56:43 +0800) |
| Step 2 backfill report | `data/interface_scope_step2_backfill_report.json` | `d430cc2f6ebdf6553464f9751ade4b02eac6423f0509222a96c4c4666fb6eec1` ✅ | 38,561 | `e70807b` |
| Verification report | `Docs/COORDINATION/INTEGRATION/PREPROCESSING-STEP1-STEP2-VERIFICATION-REPORT-v1.md` | `da97a2f388b8596091bbb9a51fe794a3243515f69680ea231fd3bb4772aebb7c` ✅ | 6,735 | `e70807b` |
| Final check evidence | `data/freeze_evidence_final_check.json` | `a707738e5ceae7008eef7a7744d38b7b7ca1c052d936b49e0b31e59f1c5a5c33` ✅ | 41,317 | `aad2237`(2026-09-16 17:52:18 +0800) |
| pre-backfill audit 快照 | `data/audit_snapshot_interface_scope_prebackfill.json` | `b11874c472a9fad3051f58c5fc46367dc8d7fc3e5ad961b266edfa55c142dd9c` ✅ | 30,200 | `e70807b` |
| post-backfill audit 快照 | `data/audit_snapshot_interface_scope_postbackfill.json` | `2cb980c7ca421f5a2c3615053cd3308d5ad1aa078083928724af88d4663a4096` ✅ | 30,197 | `e70807b` |

辅助引用:证据链登记账 = `PREPROCESSING-CONTRACT-v0.2-FREEZE-EVIDENCE-v1.md`(commit `67f564c`);确定性只读复核脚本 = `scripts/freeze_evidence_final_check.py`(唯一输出路径原为 `data/freeze_evidence_final_check.json`,本轮经 scratch 重定向复跑);账本基准 = `Docs/COORDINATION/state.yaml` + `CURRENT.md`(DEC-032,STATUS: CONTRACT FROZEN)。

**结论:Task 1 PASS — Step1 snapshot / Step2 backfill / verification report / final check evidence 四类证据(含 pre/post 配对双快照)全部在位、可访问、哈希与登记值零偏差。**

环境注记(OBSERVED vs 未执行,勿混):本轮 `git ls-remote origin main` **未执行成功**——环境凭据错误(`SEC_E_NO_CREDENTIALS`,schannel),属本机 git 凭据面问题,非数据/仓库问题;远端可达性上一次亲验 = DEC-031(`5b0552d`)/ DEC-032(`9cf35e3`)轮(remote = TRUE,`origin/main = 4daecf0b` 含 `f4941ff`)。本轮不改写该历史结论,亦不冒充本轮 OBSERVED。

---

## 2. Hash Verification Result(Task 2:只读一致性检查)

复跑判定 = 冻结时同一套 C1-C9(fail-closed,任何一项不过即 BLOCKED、不修复)。**九项全 PASS,overall = VERIFIED**:

| # | 检查项 | 结果 | 本轮证据 |
|---|---|---|---|
| C1 | 接口面 = 87(字段口径 `identity_version==2`,独立重枚举) | **PASS** | found = 87 |
| C2 | 87/87 manifest 携 `source_content_sha256` 且为面内唯一 sha/hash 键 | **PASS** | 87/87 |
| **C3** | **87/87 `source_content_sha256` == SHA256(当前 source bytes),64 位小写 hex** | **PASS** | bytes match 87/87;format 87/87 |
| C4 | 87/87 source bytes 自 Step 1 快照起零漂移且 == R50 记录值 | **PASS** | match step1 87/87;match R50 87/87 |
| C5 | IR 对账:ADMITTED 71/71 且 `ir.source_sha256` == `manifest.source_content_sha256` | **PASS** | 71/71 |
| C6 | 16/16 Semantic Pending(REJECTED_QC_FAIL)身份自足 | **PASS** | 16/16 携 64-hex 身份 |
| C7 | R50 血统:87 manifest + 87 source 双成员;DRIFT == 恰 87 manifest、missing 0;post audit verify ok;pre 漂移集 ⊆ scope;corpus 与 Step 2 报告一致 | **PASS** | 全项符合预期 |
| C8 | 仅追加一键再证:剥去新键重序列化 sha == R50 基线记录 manifest sha | **PASS** | 87/87 |
| C9 | path 非身份:locator(`source_file`)与 Step 1 快照一致;身份只按内容 hash 判定 | **PASS** | locator unchanged 87/87;**unique identities 87,duplicates 0** |

针对本轮 Owner 问题的直接回答:

- **`source_content_sha256` 仍满足 == SHA256(source bytes)**:C3 = 87/87 实测相符(逐份重读源文件原始字节、重算 SHA-256、与 manifest 值比对);
- **并与 Manifest identity 一致**:C2(唯一身份键在位,面内无第二 sha/hash 键)+ C3(值即内容 hash)+ C5(IR 侧 `ir.source_sha256` 与 manifest 身份 71/71 对齐)+ C9(身份判定不含 path;unique 87 / dups 0)四链闭合——Manifest = Source Identity Authority 现状与 DEC-026/冻结契约一致。

---

## 3. Data Immutability Result(冻结后不可变性)

| 证明面 | 手段 | 结果 |
|---|---|---|
| 已登记工件零触碰 | 六工件 `Get-FileHash` 实测 vs 登记 sha256 | **6/6 相符**(§1)——字节未变 |
| 数据面(source bytes) | C4:87/87 vs Step 1 快照 + R50 基线 | **零漂移** |
| Manifest 面 | C8:剥键重序列化 == R50 回填前 sha 87/87 | 回填后 manifest 与基线差异**恰 = 追加一键**,无其它任何改动 |
| IR 面 | C5:71/71 `ir.source_sha256` 对账 | **零漂移**(IR 工件未再生成、未改写) |
| 复验确定性 | scratch 复跑输出 vs 已登记 `data/freeze_evidence_final_check.json` | **字节级一致**(两者 sha256 同为 `a707738e5ceae7008eef7a7744d38b7b7ca1c052d936b49e0b31e59f1c5a5c33`) |
| 工作树 | `git status --porcelain`(scratch 清理后) | 干净(本轮唯一落盘 = 本报告) |

R50 血统防误读(承接 FREEZE-EVIDENCE v1 §3,不变):R50_input_baseline(356 files)中恰 87 份接口面 manifest 的 DRIFT = **预期行为**;接口面完整性基线现行承接者 = pre/post 配对双快照(`b11874c4…dd9c` → `2cb980c7…4096`,corpus `4ad3458b…` → `24af8f56…`,均 177 files);未来审计偏离「drift == 恰 87、missing 0」预期才是异常。

**结论:Freeze 后 Producer 数据基线保持不可变——零修改、零漂移、可第三方复现。**

---

## 4. 边界声明(硬边界,不得误读)

```text
Producer baseline frozen — 本报告只确认保全,不产生任何新裁决、不扩展 Freeze 范围。
Consumer implementation separate — 契约冻结 ≠ 能力交付;五项 V3 消费能力
(raw bytes acquisition / SHA256 独立验证 / Manifest identity verification /
 IR identity verification / identity gate)全部 NOT IMPLEMENTED 不变;
Freeze 不含三项实现(bytes verification / identity gate / IR verification)。
```

- 已裁六项(identity key / path / `source_version_id` / Semantic Pending / 87·71·16 / bytes requirement)**不重开**;
- Producer 侧长开项(16 份 IR 再生成 / D-3 存量 1 例 / D-4 两份三重成员 / IR 字段名对齐 / 两层状态载体 / C.1 追认)**仍须令才动**;
- 下一阶段 = **V3 Consumer Identity Verification Implementation**(bytes → SHA256 → Manifest 验证 → IR 验证 → fail-closed → Gate → Admission),排期属 V3 侧。

---

## 5. 纪律自查(本轮)

- 零实现动作、零数据动作:未重生成 IR / 未改 manifest / 未改 Contract / 未改 schema / 未动 Question / 未动 daemon / 未做任何清洗;
- 已登记工件写入面 = 零:复跑经 scratch 重定向(`reports/` gitignored 临时输出,已清理),`data/freeze_evidence_final_check.json` 未被覆盖(哈希前后一致再证);
- OBSERVED / 未执行分离:远端核验本轮未执行(凭据错误),如实标注(§1 环境注记),不冒充 OBSERVED。

---

## 6. 结论

```text
PRODUCER BASELINE FROZEN — INTEGRITY VERIFIED(零 BLOCKER)
```

Task 1 证据可访问性 **PASS**;Task 2 一致性检查 **PASS(C1-C9 全过,overall VERIFIED)**;Task 3 本报告即交付物。冻结四元组(`kurt-wong/AITutors-v3` @ `f4941ff…` / `PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` / `9c6b9063…7528`)不在本轮改动面内,状态不变(CONTRACT FROZEN,DEC-032)。

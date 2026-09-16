# PRODUCER BASELINE ARCHIVE FINAL REPORT v1

> Status: **PRODUCER BASELINE: FINALIZED(归档终检完成)**(2026-09-16,DEC-034 轮)
> Authority: Owner 本轮指令「Producer Frozen Baseline Archive Final Check」(允许 = 只读验证 + 文档登记;禁止 = 代码 / 数据 / Manifest / IR 修改)
> Role: Frozen Producer Baseline 的**最终归档**文件——四项 immutable 终检 + 远端验证(Observed / Historical 分账)+ 归档状态登记。
> 纪律: 本轮零数据动作;已登记工件零覆盖(复跑经 scratch 重定向);唯一新文件 = 本报告(docs-only)。

---

## 0. 归档终态(Owner 指定输出格式)

```text
PRODUCER BASELINE:
FINALIZED

CONSUMER IDENTITY:
NOT IMPLEMENTED
```

---

## 1. 四项 Immutable 终检(本轮只读复验,全部 PASS)

复验方式:从当前磁盘字节独立重新枚举、重算 SHA256、与 Step 1 快照 / Step 2 报告 / R50 基线 / pre+post audit 快照交叉对账(`scripts/freeze_evidence_final_check.py` 判定逻辑经 scratch 重定向复跑,输出路径 = gitignored 临时文件,已登记工件零覆盖)。

| 项 | 判定 | 本轮证据(OBSERVED) |
|---|---|---|
| **source bytes immutable** | **PASS** | C4:87/87 source bytes == Step 1 快照记录值 == R50 基线记录值(零漂移);C3:87/87 `source_content_sha256` == SHA256(当前字节),64 位小写 hex |
| **manifest immutable** | **PASS** | C8:剥去回填键重序列化 sha == R50 基线记录 manifest sha 87/87(差异恰 = 追加一键,其余字节零改动);C2:面内唯一 sha/hash 键 87/87;Step 1/Step 2 工件字节与登记 sha 全数相符 |
| **IR immutable** | **PASS** | C5:ADMITTED 71/71 `ir.source_sha256` == `manifest.source_content_sha256`;IR 工件(`data/resolver_ref_r52/resolver_ir.json`)未再生成、未改写 |
| **evidence immutable** | **PASS** | 六证据工件 `Get-FileHash` 实测与 FREEZE-EVIDENCE v1 登记 sha256 **6/6 相符**(下表);复跑输出与已登记 `data/freeze_evidence_final_check.json` **字节级一致**(`a707738e…5c33`) |

全项复跑结果:**C1-C9 全 PASS,overall = VERIFIED**(C1 接口面 87 / C6 pending 16 身份自足 / C7 R50 血统 DRIFT == 恰 87 missing 0 / C9 locator 不变、unique identities 87 dups 0)。

### 1.1 证据工件归档表(sha256 = 本轮实测 == 历次登记值)

| 工件 | sha256 | commit |
|---|---|---|
| `data/interface_scope_snapshot_step1.json` | `b4f14524473d97b86f5d6a2f8bb03ee794727652a68fa4df4b00d794de98ad99` | `e70807b` |
| `data/interface_scope_step2_backfill_report.json` | `d430cc2f6ebdf6553464f9751ade4b02eac6423f0509222a96c4c4666fb6eec1` | `e70807b` |
| `data/audit_snapshot_interface_scope_prebackfill.json` | `b11874c472a9fad3051f58c5fc46367dc8d7fc3e5ad961b266edfa55c142dd9c` | `e70807b` |
| `data/audit_snapshot_interface_scope_postbackfill.json` | `2cb980c7ca421f5a2c3615053cd3308d5ad1aa078083928724af88d4663a4096` | `e70807b` |
| `data/freeze_evidence_final_check.json` | `a707738e5ceae7008eef7a7744d38b7b7ca1c052d936b49e0b31e59f1c5a5c33` | `aad2237` |
| `Docs/COORDINATION/INTEGRATION/PREPROCESSING-STEP1-STEP2-VERIFICATION-REPORT-v1.md` | `da97a2f388b8596091bbb9a51fe794a3243515f69680ea231fd3bb4772aebb7c` | `e70807b` |

归档关联件:Freeze Evidence 登记账(`PREPROCESSING-CONTRACT-v0.2-FREEZE-EVIDENCE-v1.md`)/ Frozen Baseline Integrity Report v1(`PREPROCESSING-PRODUCER-FROZEN-BASELINE-INTEGRITY-REPORT-v1.md`,`8fc4d60`)/ 冻结对象四元组(`kurt-wong/AITutors-v3` @ `f4941ff…` / `PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` / `9c6b9063…7528`,DEC-032,不在本轮改动面内)。

---

## 2. 远端验证(Observed / Historical 严格分账)

### 2.1 Observed(本轮实际执行,2026-09-16 DEC-034 轮)

| 命令(V3 仓 `kurt-wong/AITutors-v3`) | 本轮结果 |
|---|---|
| `git fetch origin` | **成功**(exit 0;沙箱升级一次后执行——本会话早前同命令曾被 `.git/FETCH_HEAD` 写权限拒绝,属沙箱文件策略非仓库问题) |
| `git ls-remote origin main` | **`72af28d5854b56fc605e1897fb757703826a6233`**(exit 0;remote reachable = TRUE;与 DEC-033 轮实测一致,远端未再前进) |
| `git merge-base --is-ancestor f4941ff origin/main` | **TRUE**(exit 0;冻结对象 commit 仍包含于远端 main) |

本仓(`kurt-wong/Aitutors-preprocessing`)远端:本轮 push 后 `git ls-remote origin main` 亲验(见 §4 登记行)。

### 2.2 Historical(之前验证结果,仅存档引用,不冒充本轮观察)

| 轮次(时点) | 观察值 | 出处 |
|---|---|---|
| DEC-031(2026-09-16) | V3 `origin/main` = `305bd81`;is-ancestor TRUE;`git show f4941ff:<contract>` 重导 sha256 = `9c6b9063…7528` | `PREPROCESSING-CONTRACT-v0.2-PRODUCER-FREEZE-FINAL-VERIFICATION-REPORT-v1.md` |
| DEC-032(2026-09-16) | V3 `origin/main` = `4daecf0b`;is-ancestor TRUE;字节级重导 sha256 = `9c6b9063…7528`(92,197 bytes) | state.yaml `owner_contract_frozen` 块 + log.md DEC-032 条目 |
| DEC-033(2026-09-16) | 首试 fetch FAIL(沙箱 `.git/FETCH_HEAD` Permission denied)/ ls-remote FAIL(`SEC_E_NO_CREDENTIALS`)(真实错误已入账);升级重试:`origin/main` = `72af28d`,is-ancestor TRUE | `PREPROCESSING-PRODUCER-FROZEN-BASELINE-INTEGRITY-REPORT-v1.md` + log.md DEC-033 条目 |

---

## 3. 归档声明

- **Producer baseline = 归档终态**:接口面 87(87/87 携 `source_content_sha256`,unique 87 / dups 0)/ IR 71 ADMITTED(1,664 单元)/ 16 Semantic Pending / v1 legacy 79(隔离)/ R50 基线 356(DRIFT = 恰 87 为预期,承接者 = pre/post audit 双快照)——全部以 §1.1 工件表字节为准,任何后续变化必须先有 Owner 令并产生新快照配对,不得就地改写;
- **R50 血统防误读(冻结解释)**:R50_input_baseline 中恰 87 份接口面 manifest 的 DRIFT = 预期行为;未来审计偏离「drift == 恰 87、missing 0」预期才是异常;
- **长开项与延期五项不因归档而关闭**:16 份 IR 再生成 / D-3 / D-4 / IR 字段名对齐 / 两层状态载体 / C.1 追认仍须令才动;legacy 79 披露 / 17 拒收 / OCR-PDF 扩展 / DEC 编号统一 / bytes 传输方式维持延期;
- **Decision ≠ Implementation(归档不得误读)**:契约冻结 + 基线归档 ≠ 能力交付。

---

## 4. 最终状态与边界

```text
PRODUCER BASELINE:
FINALIZED

CONSUMER IDENTITY:
NOT IMPLEMENTED
```

- **Consumer Identity Verification = NOT IMPLEMENTED**:五项 V3 消费能力(raw bytes acquisition / SHA256 独立验证 / Manifest identity verification / IR identity verification / identity gate)全部不变;Freeze 不含 bytes verification / identity gate / IR verification 三项实现;下一阶段 = V3 Consumer Identity Verification Implementation(排期属 V3 侧);
- **本轮纪律自查**:零代码 / 零数据 / 零 Manifest / 零 IR 修改;写入面 = 本报告 + 台账登记;Freeze 范围未扩展;零新架构裁决;已裁六项未重开;已登记工件零覆盖(复跑后再验 `data/freeze_evidence_final_check.json` 哈希不变)。

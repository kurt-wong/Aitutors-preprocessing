# PREPROCESSING-PRODUCER-GUARDIAN-M4-ADVERSARIAL-REVIEW-v1

> Status: **v1(2026-09-16,DEC-041)** · Authority: Owner 直接指令(聊天原文照录见 ODR §1tervicies)
> 性质:**对 DEC-040(Phase 2-M4 Guardian Check,轮次 4)全部结论的第一性原理对抗性审查**。纪律 = 每个结论必须有真实测试作为证据;不降低测试与验证标准;不自我合理化;不强行解释未通过测试的内容;不靠推测输出结论。审查自身全程只读(零代码 / 零数据 / 零 schema;唯一写面 = 本报告与四账登记)。
> 审查对象提交 = 本仓 `6a48d21`(DEC-040 轮记账)。本审查在 DEC-040 提交与 push **之后**独立执行,不复用 DEC-040 轮的任何测试输出。

## 0. 审查结论摘要

| # | 被审结论(DEC-040) | 审查判定 | 证据(本轮实测) |
|---|---|---|---|
| V1 | G1~G6 全 PASS 零 mismatch | **维持,且覆盖面被实质加强** | §1(177/177 重测)+ §2(R50 356 逐文件活测,层判据 269 MATCH / 87 预期 DRIFT / 0 unexpected)+ §5 |
| V2 | G5 corpus snapshots 相符 | **维持但降级表述**:原执行 = 读快照内 `corpus_sha256` 字段(依赖 G4 工件锚);本轮升级为 **R50 356 逐文件活测**;`corpus_sha256` 聚合构造 **7 种候选均未复现**(如实记为未复现,不强行解释) | §2 |
| V3 | Producer IR / Manifest / source bytes / Freeze Artifact 四项 immutable 保持 | **维持,且新增原面(source_file 面)活测层**:87/87 decl == source_file 目标活 sha == Step2 报告值 | §3 |
| V4 | Authority Boundary HOLDS(无修复 IR / 回写 Manifest / 重生成 artifact) | **维持,证据升级**:扩展模式清扫 + 三模块全文亲读 + Producer 路径引用检索 | §4 |
| V5 | duplicate/path 无违规倾向 | **维持,但证据等级如实限定 = Consumer 设计层(REPORTED)**:M4 模块未落树,行为面证据尚不存在,不可超范围引用 | §4.3 |
| V6 | V3 untracked 文档"与 DEC-038 自述 10 件计数差 1" | **证伪(自我更正)**:本轮 9 件与 DEC-038 名单 9 件 **SET_EQUAL=True**,无任何文档消失;真实来源 = DEC-038 轮文本自称"10 份"但其名单实列 9 件(历史计数错误),DEC-040 沿用该错误数字并作了无证据归因("V3 文档自整理") | §6 |
| V7 | 测试基线 338 passed / 1 xfailed | **维持**:独立第 3 次复跑一致 | §5 |
| V8 | STOP 未触发 / 零违例 | **维持**(审查全程未发现任何冻结对象字节变化) | 全篇 |

**总体判定:DEC-040 的冻结对象完整性结论(G1~G6 / 四项 immutable / Authority Boundary / 零违例)全部经对抗性复测维持;发现并更正 1 项 REPORTED 事实错误(文档计数差 1)+ 1 项方法学弱点(G5 原执行强度弱于其名称所示,已升级)+ 1 项未复现项(corpus_sha256 聚合构造,如实挂账)。零 STOP 触发,零冻结对象违例。**

## 1. 攻击 A:锚定面完备性(177 map 构成解剖)

**攻击问题**:DEC-040 的 G1~G6 只测了 177 锚定文件 —— 冻结对象是否存在游离于锚外的部分?177 是如何构成的,是否被如实表述?

**实测**(本轮重跑):
- `data/audit_snapshot_interface_scope_postbackfill.json` files map = **177 条**,构成 = **87 × source md + 87 × manifest.json + 3 × 工件**(`data/audit_snapshot_R50_input_baseline.json` / `data/interface_scope_snapshot_step1.json` / `data/resolver_ref_r52/resolver_ir.json`);
- **Producer IR artifact 在锚内**(G1+G2 与 G3 双重覆盖);
- `step2_backfill_report` / `prebackfill` / `postbackfill` / `freeze_evidence_final_check` / `STEP1-STEP2-VERIFICATION-REPORT` 五件**不在** 177 内,由 G4 单独锚定 —— 无覆盖空洞;
- 177 全量逐文件活测:checked=177 / missing=0 / **mismatch=0**;快照自身 sha = `2cb980c7…4096` 相符。

**判定:V1 维持**。锚定面无游离冻结对象;"other=90" 此前未被逐项展开表述(87 manifest + 3 工件),本轮补齐。

## 2. 攻击 B:G5 语料快照的真实强度(本轮最重要加强)

**攻击问题**:DEC-040 的 G5 实为"读快照 JSON 里的 `corpus_sha256` 字段比对登记值" —— 这只证明快照工件未变(该结论其实已由 G4 覆盖),**并未对活语料文件做任何实测**。活语料(R50 基线 356 件)是否真的未变?

**实测 1 —— R50 356 逐文件活测**(利用 `data/audit_snapshot_R50_input_baseline.json` 内嵌 path→sha256 逐文件 map,356 条):
- 第一遍:checked=356 / missing=0 / **mismatch=87**,全部为 `*.manifest.json`;
- **判据检验(禁止自我合理化)**:对 87 条 mismatch 与 177 锚内 87 条 manifest 名单做**严格集合相等性测试** —— `SET_EQUAL=True`,only-in-R50-mismatch = 0,only-in-anchor = 0;
- 抽样 3 份(mismatch 首/中/尾)键级实测:活 manifest 均含回填键 `source_content_sha256`(键集 = source_file, model, annotation_meta, units, identity_version, sections, **source_content_sha256**);Step2 报告逐文件记录 `n_keys_before=6 → n_keys_after=7, key_appended=source_content_sha256` —— 与已裁的 Step-2 回填 DRIFT(恰 87,预期)机制一致;
- 第二遍(层判据复测):**match=269 / expected_manifest_drift=87 / unexpected=0**。

**判定**:`87 mismatch` 是**已裁预期 DRIFT 的活文件级实证**(R50 层 → post-backfill 层的单键追加),不是本轮或 M4 期间的字节变化;87 份回填后 manifest 由 177 锚逐一钉死(mismatch=0)。**V1 维持且加强**:此前各轮从未对 R50 356 件做过逐文件活测,本轮起该检查面被实际打开。

**实测 2 —— `corpus_sha256` 聚合构造复算(未复现,如实挂账)**:对 R50 files map 尝试 7 种构造(排序/存储序 × 哈希拼接 / path+hash 拼接 / 换行分隔 / 尾随换行 / **原始文件字节全拼接**),无一等于 `795ee1e7…beb`。**结论:聚合 digest 构造未复现,不推测其构造,不引用其自证能力**;操作性锚 = 逐文件 map(已实测)。台账既有表述"corpus 双快照字段相符"应读作"快照工件(含字段)字节未变"(G4 已覆盖),而非"语料经该 digest 被独立验证"。

## 3. 攻击 B2(新增检查面):原面 source_file 层活测 + 一次自我纠错

**攻击问题**:`source_content_sha256` 定义 = "SHA256(original source bytes)"。接口面 md 是 reslice 副本;原面文件(`manifest.source_file` 指向 `Ocr-markdown\会考\...` 等)是否与声明一致?该层此前从未被活测。

**实测过程(含一次失败测试,如实入账)**:
- 第一测试(构造错误):以 reslice 面同名 md(`X.manifest.json → X.md`)比对 decl —— **ok=0 / bad=87**。这是**本审查方的测试构造错误**(测错对象),不是数据缺陷;
- 第二测试(按定义构造):读每份 manifest 的 `source_file` 指针,散列**指针目标活文件**,与 decl 及 Step2 报告值三方比对 —— **ok=87 / bad=0 / missing=0**。

**判定:V3 维持并扩展**。87 份原面源文件的活字节与冻结 decl 逐份相符(锚链 = 177 锚 manifest → decl → source_file 目标);原面层自此具备可复跑的活测方法(建议后续各 Guardian 轮常态化,见 §7)。

## 4. 攻击 C:Authority Boundary(写路径与引用面)

**攻击问题**:DEC-040 的写路径排查模式集有限,可能漏掉 `os.replace` / `subprocess` / `to_csv` / `np.save` / `pickle.dump` / `open('x')` 等写法;V3 代码中对 Producer 路径的引用是否全部只读?

**实测**:
- 扩展模式清扫(`subprocess|os.system|os.replace|shutil.copy|copyfile|to_csv|to_json|np.save|pickle.dump|.write(|open(`)覆盖 V3 `backend/` 全树:命中全部为 ① 既有 scripts(`i5g_emit_audit.py` 等写自有 OUT 目录;`gate_b/*`、`preprocessing_consumer/*` 写自有报告参数路径)② 测试读语料(`open(..., 'r')`)+ pytest tmp 写;**零命中指向 Producer 资产的写路径;无 subprocess/os.system 命中**;
- Producer 路径引用检索(`Aitutors-preprocessing|resolver_ref|audit_snapshot|interface_scope|freeze_evidence|Project\Papers|Ocr-markdown`):命中全部位于既有 `gate_b/*` / `preprocessing_consumer/*` 语料读取器(读模式 `open(mp, "r")` 等)与历史报告 JSON;**身份链三模块与新增测试零命中**;
- 三模块全文亲读:`raw_bytes_identity.py`(54 行,唯一 IO = `read_bytes()` + `hashlib.sha256`)、`manifest_identity.py`(78 行,唯一 IO = `read_text`)、`ir_identity.py`(48 行,唯一 IO = `read_text`)—— **全部纯读,零写路径,零可写依赖**;
- M4 模块状态复核:`backend/app/core/` 仍无 `identity_verifier.py`(M4 未落树)。

**判定:V4 维持,证据升级**。

### 4.3 duplicate/path 判定的证据等级限定

F8a(same content + different locator = 允许)证据来源 = V3 本地 READINESS 设计文档(untracked,REPORTED 级)。**M4 行为面代码尚不存在,故该判定只能维持在设计层,不得引申为"行为已验证"**。V5 维持但按此限定表述。

## 5. 攻击 E/F:环境残留、跨仓锚、测试基线

| 检查 | 实测 | 判定 |
|---|---|---|
| G6 临时重导残留 | `%TEMP%\freeze_g6_DEC040.md` **不存在** | 通过 |
| 冻结四元组亲缘 | `merge-base --is-ancestor f4941ff origin/main` = TRUE(exit 0,复测) | 通过 |
| 契约零 diff | `f4941ff..origin/main -- <contract>` = EMPTY(复测) | 通过 |
| V3 远端现状 | `HEAD` = `72af28d`(复测,未前进) | 通过 |
| G4 证据再散列 | **7/7 match**(独立复跑) | 通过 |
| 测试基线 | **338 passed / 1 xfailed**(独立第 3 次复跑,22.77s) | 通过 |
| 写后完整性 | 177/177 mismatch=0 + G3 `fbcf41ab…b04a5`(审查前后各一次) | 通过 |

## 6. 攻击 D:V3 untracked 文档计数(自我证伪)

**实测**:本轮 `git status` untracked docs = **9 件**;与 DEC-038 报告 §1.3 逐名列出的 9 件做集合比对 —— **SET_EQUAL=True**(双向零多余)。

**判定:V6 证伪**。DEC-040 报告"untracked 文档面本轮实测 9 件(与 DEC-038 轮自述 10 件计数差 1,属 V3 合法写面内文档自整理)"为**错误表述**:
1. 不存在任何文档增删 —— 两轮名单集合相等;
2. 差异真实来源 = DEC-038 轮文本自称"10 份文档"但其名单实列 9 件(历史计数错误);
3. DEC-040 沿用了该错误基数,并作出了未经测试的归因("文档自整理")—— 违反"不靠推测输出结论"纪律。

**更正(以本报告为准)**:V3 untracked 文档面 = DEC-038 起即为 9 件,至本轮零增删。该错误属 REPORTED 事实层记账错误,**不涉及任何冻结对象字节**,不触发 STOP。

## 7. 审查产出的改进建议(非裁决,待 Owner 令)

1. **G5 升级**:后续 Guardian 轮将 R50 356 逐文件活测(层判据:269 MATCH / 87 预期 DRIFT / 0 unexpected)纳入常规检查面,替代仅读 `corpus_sha256` 字段的弱执行;
2. **原面层常态化**:`source_file` 指针三方比对(decl == 活 sha == Step2 报告值,87/87)纳入常规;
3. **`corpus_sha256` 聚合构造**:挂账未复现项,若 Owner 需要字节级复现,须回溯生成脚本确认构造(涉及旧工件生成逻辑回查,须令);
4. DEC-038 轮"10 份文档"表述在历史报告中保留原文(append-only),由本报告承担更正登记。

## 8. 纪律声明

本审查全程只读:未修改任何 Consumer 实现 / 未修改任何 Producer 数据 / 未提供代码补丁 / 未自行修复任何发现;唯一例外 = 台账更正登记(docs-only)。审查中出现的两次"失败测试"(0/87 错路径比对、7 种 digest 构造未复现)均按原样入账,未降标准、未合理化、未强行解释。零新架构裁决;已裁六项未重开。

**结论:`BOUNDARY: HOLDING` 维持;DEC-040 冻结对象结论全部经对抗性复测成立;1 项 REPORTED 事实错误已更正(§6);1 项方法学弱点已升级修复(§2);1 项未复现项如实挂账(§2)。等待 Owner 下一步指令。**

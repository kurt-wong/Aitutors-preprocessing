# PREPROCESSING-PRODUCER-GUARDIAN-M5-BOUNDARY-REVIEW-v1

- **轮次**:DEC-042(Consumer M5 Boundary Guardian Review,Owner 指令 2026-09-16 原文照录 = ODR v1.23 §1quadvicies)
- **审查方**:DSH(Producer Frozen Baseline Guardian / Adversarial Reviewer)——只审查、不替 Claude 实现、不自动修复、不修改 Producer、不改变冻结 Contract
- **执行时间窗**:2026-09-16(V3 本地工作树处于 Claude 实时开发中,见 §1.3 移动目标登记)

> **⚠ 勘误指针(DEC-044-S 追加,append-only,原文零删改)**:本报告以下两处表述已被 DEC-043 对抗性审查更正,引用时以更正为准:
> ① §11 及相关处「ROOT CAUSE = 环境 DB 缺失」= **已撤回的超证据归因**(DEC-043 F-1;正确口径 = OBSERVED 按文件确定性分化 + ROOT CAUSE UNKNOWN);
> ② §1.3「untracked = 10 docs(REPORT-PHASE2-M4 新增)+ 15 tests」= **已证伪**(DEC-043 F-3;实测 9 docs + 5 core + 14 tests = 28,REPORT-PHASE2-M4 零证据)。
> 完整更正清单见 `PREPROCESSING-PRODUCER-GUARDIAN-M5-REVIEW-ADVERSARIAL-v1.md` §7 与 state.yaml `producer_guardian_m5_adversarial.corrections`。

---

## §0 结论总表(严格两分,不合并)

| 结论面 | 判定 | 依据 |
|---|---|---|
| **PRODUCER BOUNDARY** | **HOLDS** | G1–G6 全 PASS;四项 immutable 全部成立;冻结对象零字节变化;STOP 未触发(§2) |
| **CONSUMER M5(对 push commit)** | **NOT VERIFIED — 无 push 对象** | 远端 `origin/main` = `72af28d…6233` 未前进;该 commit 内 `ls-tree`/`git grep` 证实**零**身份链代码(§1.1)。按 Owner 指令「如果 Claude 尚未 push M5,不要提前宣布 M5 通过」——本轮不宣布 M5 通过 |
| **CONSUMER M5(本地 untracked 快照)** | **OBSERVED-LOCAL:语义电池 27/27 符合 Owner Truth Table;接口与 Design v1.1 存在 4 项偏离(D1~D4);真实调用链零集成** | §4–§9;本地状态未 push、未过 CI、且审查期间仍在变化(§1.3),不构成 VERIFIED 证据 |
| **STOP** | **NOT TRIGGERED** | 全轮零冻结对象字节 mismatch |

> **范围声明(Owner §十)**:Producer Guardian 只能证明 *Producer unchanged / boundary holds / frozen artifacts unchanged*。它**不能**证明 *M5 correct / Consumer semantics correct / IR correctly consumed / Admission safe*。后者在本轮的证据状态 = 本地 untracked 快照级 OBSERVED + NOT VERIFIED(对 push commit)。

---

## §1 审查对象

### 1.1 Claude 实际 push 的 commit(Owner §一.1–3)

- `git fetch` + `git ls-remote origin` 实测:V3 `origin/main` = **`72af28d5854b56fc605e1897fb757703826a6233`**(与 DEC-037/038/039/040/041 各轮一致,**远端零新提交**;远端仅 main 一分支 + 两个旧 tag)。
- 从该 commit 重新检查:`git ls-tree 72af28d backend/app/core/` = 仅 `__init__.py / config.py / errors.py / hashing.py`;`git grep -l "identity_(gate|verifier)|manifest_identity|ir_identity|raw_bytes_identity" 72af28d -- backend` = **空**。
- **事实:push commit 内不存在 M1–M5 任何代码,包括 M4**。V3 侧全部身份链实现目前仅存在于本地 untracked 文件。

### 1.2 本地 untracked 快照(OBSERVED-LOCAL,证据锚 = 文件散列)

| 文件(backend/) | sha256 前 16 位 | bytes | mtime |
|---|---|---|---|
| `app/core/identity_gate.py`(M5) | `f3636b35f3c8126d` | 4391 | 08:38:08 |
| `app/core/identity_verifier.py`(M4) | `1306105c6c3d2b8b` | 3725 | 06:25:35 |
| `app/core/ir_identity.py`(M3) | `9315c22e1d74ff95` | 1730 | 00:46:12 |
| `app/core/manifest_identity.py`(M1) | `1ca33a45a101de8c` | 2811 | 00:37:16 |
| `app/core/raw_bytes_identity.py`(M2) | `803c4ed8a93f59b5` | 1877 | 23:47:02 |
| `tests/test_identity_gate.py` | `e1796df796120e6d` | 5407 | 08:26:34 |
| `tests/test_adversarial_m5_integration.py` | `eee31b8f8c7ca864` | 22247 | 08:30:06 |
| `tests/test_adversarial_m5_round1.py` | `4fa4c6b4b92a48b4` | 22923 | 08:38:33 |
| `tests/test_adversarial_identity_verifier.py` | `0a7a7dbb2e46bbb3` | 24465 | 06:25:41 |
| `tests/test_adversarial_m4_round2.py` | `4913aeca08d52e9d` | 20055 | 06:29:44 |

untracked 终态(轮末):**10 docs**(`REPORT-PHASE2-M4` 于审查窗口内新增,较 DEC-041 轮 9 件 +1,Claude 侧写面,如实入账)+ 5 core + **15 tests**(`test_adversarial_m5_round2.py` 于 pytest 之后出现)。

### 1.3 移动目标登记(原样入账,不归因)

- 审查期间 `identity_gate.py` 由 3602 B(08:25:55 版,已亲读)变为 **4391 B(08:38:08 版)**,增量 = identity/semantic 值域白名单校验(`invalid_state` fail-closed 分支);
- `test_adversarial_m5_round1.py`(08:38:33)与 `test_adversarial_m5_round2.py`(pytest 之后出现)在审查窗口内新增;
- 五个 core 模块在 08:38 后三次连续快照散列不变。**本报告全部动态结论锚定 `f3636b35…`(08:38 版 M5)**;这正是 Owner §一要求以 push commit 为审查对象的原因——本地态不可作为终局证据。

---

## §2 Producer Guardian 基线(Owner §二)——独立复测,全部本轮实测

| 项 | 对象 | 实测 | 判定 |
|---|---|---|---|
| **G1 source bytes** | 87 接口面源文件(经 R50 逐文件 map + source_file 三方比对双覆盖) | R50 356 逐文件活测:269 MATCH / 87 DRIFT / **0 missing / 0 unexpected**;87 DRIFT 与 177 锚 manifest 名单 **SET_EQUAL=True(双向 A−B=0, B−A=0)**,md 面 drift=0;漂移根因键级抽验 = 单键 `source_content_sha256` 追加(`n_keys_after` 全 = 7,`key_appended` 全真)= 已裁 Step-2 回填 | **PASS** |
| **G2 manifest** | 87 manifest(回填后形态)+ audit 快照自身 | 177 锚逐文件活测 **checked=177 / missing=0 / mismatch=0**;post 快照自身 sha = `2cb980c7…4096` 相符 | **PASS** |
| **G3 producer IR artifact** | `data/resolver_ref_r52/resolver_ir.json` | 独立散列 = `fbcf41ab025fd786…b04a5` == 锚定值(**Producer IR artifact hash unchanged**) | **PASS** |
| **G4 freeze evidence artifacts** | 7 件 | step1 `b4f14524…ad99` / step2 `d430cc2f…eec1` / pre `b11874c4…dd9c` / post `2cb980c7…4096` / final check `a707738e…5c33` / 验证报告 `da97a2f3…bb7c` / R50 自身 `963cd6b1…ee77` —— **7/7 match=True** | **PASS** |
| **G5 corpus snapshots** | pre/post 双快照 | 字段实测 pre `4ad3458b…19160` / post `24af8f56…0a10` 相符;逐文件 177/177 等价覆盖(R50 356 面见 G1) | **PASS** |
| **G6 freeze artifact(跨仓)** | Contract v0.2 冻结四元组 | 从 V3 @`72af28d` 字节重导:**bytes=92,197 / sha256=`9c6b9063…7528` MATCH=True**;`merge-base --is-ancestor f4941ff 72af28d` exit 0(TRUE);`f4941ff..72af28d` 契约 diff = **empty**;临时重导即时删除(TEMP_DELETED=True) | **PASS** |
| source_file 三方比对(方法学常态化) | 87 接口 manifest 的 `source_file` 指针目标 | **ok=87 / bad=0 / missing=0**(manifest 声明值 == Step2 报告值 == 活文件 sha256) | **PASS** |

**四项 immutable 分答(Owner §二)**:source bytes 未变化 ✅ / Manifest 未变化 ✅ / Producer IR 未变化 ✅ / evidence artifacts 未变化 ✅ / freeze artifacts 未变化 ✅ / 逐文件 map 未变化(R50 工件自身 sha 相符 + 356 活测零 unexpected)✅ / Contract freeze object 未被 Consumer 修改 ✅。**任何 Producer 对象变化 = 无,未触发 STOP。**

---

## §3 Consumer → Producer Boundary(Owner §三)——静态审查

### 3.1 写面清扫

- `backend/app/core/`(五个身份模块全目录):`open(...,"w"/"a") / write_bytes / write_text / os.replace / shutil.move|copy / unlink / rename / tempfile+replace / pickle / np.save / to_json|to_csv / touch` = **零命中**;五模块全文亲读:M1 `read_text`、M2 `read_bytes`+`hashlib`、M3 `read_text`、M4/M5 纯函数零 IO——全部 **READ only**。
- `scripts/preprocessing_consumer/`:6 处写点(`runner.py:305` / `runner_b2.py:364` / `runner_b3.py:238` / `sampling_analyzer.py:195` / `generate_correctness_report.py:209` / `p32_enforcement_experiment.py:256`)——全部为 **V3 内部报告输出**(默认落 `scripts/preprocessing_consumer/*.json`),无一指向 Producer 目录。
- `scripts/gate_b/`:10 处 `open(...,"w")+json.dump`——默认输出全部落 `scripts/gate_b/` 内部(如 `gate_b_comparison.py:440` `os.path.dirname(__file__)`)。
- 测试面:全部使用 `tmp_path`,零 Producer 写入。

### 3.2 Producer path 引用检索

全库 `Papers|Ocr-markdown|resolver_ref_r52|resolver_ir.json` 命中 = gate_b 语料加载器(`load_corpus` 只读)、runner 默认 `--corpus` 只读、`test_bug044`(`glob` + `open` 只读)、测试 tmp 文件名。**全部只读,零写回路径,零 manifest mutation,零 IR mutation。**

### 3.3 判定

Consumer(本地 untracked 快照)对 Producer 的写面 = **零**;`READ Producer artifacts` 边界在静态面上成立;`WRITE/REWRITE/REGENERATE/NORMALIZE-IN-PLACE/DELETE/RENAME/TOUCH-MTIME` = 均未发现。与 G1–G6 零漂移互证。

---

## §4 M5 Truth Table 实测(Owner §四)——独立动态测试,27/27 PASS

自建攻击脚本(落 DSH 临时区,V3 仓零写入;真实 tmp 文件链 M1→M2→M3→M4→M5,源字节含 CRLF/unicode/trailing newline):

| Identity | Semantic | Expected | 实测(经真实文件链) | 判定 |
|---|---|---|---|---|
| FAILED | None | BLOCK | `FAILED(computed_manifest_mismatch) / None / BLOCK` | ✅ |
| FAILED | PENDING | BLOCK | 直接伪造 VerificationResult 枚举:`BLOCK` | ✅ |
| **VERIFIED** | **PENDING** | **BLOCK** | **raw=A, manifest=SHA(A), IR=SHA(B) → `VERIFIED / PENDING(ir_manifest_mismatch) / BLOCK`(`reason=semantic_pending`)** | ✅ 最高优先级行 |
| VERIFIED | AVAILABLE | PASS | `VERIFIED / AVAILABLE / PASS` | ✅ |
| VERIFIED | None | BLOCK | 伪造态枚举:`BLOCK` | ✅ |

附加实测:① 2×3 全叉积枚举(含伪造不可达态)与 Owner 表逐格相符;② 越域伪造值(`"GARBAGE"/"verified"/""/` 整型语义值等 6 例)全部 **BLOCK(`invalid_state`)**,fail-closed,不抛异常;③ **PASS 可达条件唯一 = VERIFIED+AVAILABLE**。

---

## §5 stale IR 攻击(Owner §五)

按 Owner 构造(raw bytes=A / Manifest SHA=SHA(A) / IR source SHA=SHA(B)):

- **实测:`Identity=VERIFIED` / `Semantic=PENDING(ir_manifest_mismatch)` / `M5=BLOCK`** —— 与要求完全一致(M4 判定顺序亲读:identity 仅比对 computed vs manifest,IR 不参与;semantic 独立轴)。
- **bypass 检查**:stale IR 在 M5 层无任何路径进入语义消费——M5 对 VERIFIED+PENDING 唯一出口 = BLOCK;ir_sha 取 7 种变体(含大写/空串/任意串)均不能改变 identity 轴(§8)。
- **但真实调用链层面存在结构性 bypass 状态(见 §9)**:M5 尚未被任何生产入口调用,stale IR 今天仍可经 `runner_b2.py` 旧链(manifest 直喂 IRBuilder→Compiler→Gate→AdmissionCandidate)被消费——**该链不含也不校验任何身份轴**。这不是 M5 函数的缺陷,而是**集成缺口**;按 Owner §五口径登记为:**Consumer Boundary enforcement = NOT VERIFIED(集成未完成)**。不修改代码。

---

## §6 Missing / Invalid Manifest 攻击(Owner §六)——6 变体全实测

| 变体 | M1 实测 | 下游实测 | 是否被误读为 PENDING/VERIFIED |
|---|---|---|---|
| manifest 文件缺失 | `ManifestReadError` 抛出 | (异常路径,caller 须 ERROR/BLOCK) | 否 |
| `source_content_sha256` 缺失 | `None` | M4 `FAILED(manifest_sha_missing)` + semantic=**None** + BLOCK | **否** |
| = `null` | `None` | 同上 BLOCK | 否 |
| = `""` | `None` | 同上 BLOCK | 否 |
| invalid SHA(63 位 / 大写 / 非 hex / int / 带 `\n`,5 例) | 全部 `ManifestReadError` 抛出 | (异常路径) | 否 |
| Manifest SHA ≠ actual raw bytes(IR 与 manifest 一致) | 正常读出 | M4 `FAILED(computed_manifest_mismatch)` + BLOCK(**IR 一致不能救 identity**) | 否 |

**结论:M1 返回 `None` 的任何路径都只流向 `identity=FAILED / semantic=None / BLOCK`,不存在被解释为 Semantic PENDING 或 Identity VERIFIED 的路径。**

---

## §7 Missing / Malformed IR 攻击(Owner §七)——5 变体区分 + 契约一致性

| # | 场景 | 实现实测 | Frozen Contract / Design v1.1 口径 | 一致性 |
|---|---|---|---|---|
| 1 | **IR missing(文件不存在)** | M3 **抛 `IRReadError`** | Design v1.1 §4.4 行 361 + 异常矩阵 F5:「IR 不存在 → source_sha256=None(Semantic Pending 正常态,**不抛异常**)」;Contract v0.2:16 份 = 无 IR 语义承载的**正常态** | **❌ DISCREPANCY D1(行为级)** |
| 2 | IR source identity 缺失(key 无 / null / 空串) | `None` → PENDING → BLOCK | None → PENDING | ✅ |
| 3 | IR source identity mismatch | PENDING(`ir_manifest_mismatch`)→ BLOCK | PENDING | ✅ |
| 4 | malformed JSON | `IRReadError` 抛出 | Design §4.4:抛 `IRReadError` | ✅ |
| 5 | wrong type(顶层 list / 非法 sha) | `IRReadError` 抛出 | 抛 `IRReadError` | ✅ |

**D1 处置**:按 Owner 指令「实现与 Contract 不一致 → 登记为 discrepancy,不替 Claude 修改」。影响面:接口面 87 中 16 份 Semantic Pending(无 IR)在当前 M3 下会走异常路径而非 PENDING 正常路径——错误语义方向是 fail-closed(异常≠放行),但与冻结设计文本不一致,须 V3 侧收口或 Owner 裁决。**DSH 不代改。**

---

## §8 Identity Authority 不被 IR 劫持(Owner §八)

- 枚举实测:固定 `computed==manifest`,ir_sha 取 `{None, "", SHA_A, SHA_B, "A"*64, SHA_A.upper(), "garbage"}` 七变体 → identity 恒 `VERIFIED`;固定 `computed≠manifest` 同七变体 → identity 恒 `FAILED`。**14/14 不变量成立。**
- 结构亲读:M4 `verify_identity` Step 1 仅 `computed_sha` vs `manifest_sha`,ir_sha 在 Step 1 作用域内不可达;semantic 判定在 identity 之后且单向。
- **不变量保持:`Identity ↑ (Raw Bytes + Manifest)`;`Semantic ↑ (IR)`;无反向路径。**

---

## §9 真实调用链(Owner §九)——M1→M2→M3→M4→M5→Gate→Admission

**OBSERVED(本地树)**:全库 `evaluate_identity_gate / verify_identity / read_manifest_identity / read_ir_identity / load_raw_bytes_identity` 的 import 面 = **仅 `app/core` 模块自身 + tests**。生产入口核查:

- `scripts/preprocessing_consumer/runner_b2.py`(Track B 全链入口):`find_manifests → load_manifest(manifest_reader) → load_source_lines → IRBuilder → Compiler → evaluate(Gate) → create_admission_candidate`,**全程未调用 M1–M5 任何模块**;`runner_b2.py:259` `input_identity={"source": "preprocessing_manifest"}` 不含任何 sha 身份。
- `runner.py` / `runner_b3.py` / `p32_enforcement_experiment.py` 同:零身份链调用。

**结论**:
1. 「M5 BLOCK 后面不会继续发生 semantic Gate / Compiler consumption / Admission / materialization / instance creation」——对**已集成的链**无法验证,因为**尚无任何链集成 M5**。判定 = **NOT VERIFIED(INTEGRATION PENDING)**。
2. 这与 Owner 本轮定位一致(Claude「将从 M4 转入 M5 Consumer Gate **Integration**」),且全部为 untracked 本地态——**不构成冻结对象违例,不触发 STOP**;但在 M5 集成落地并 push 之前,stale IR / missing manifest 在真实入口层面**当前无强制阻断面**。此项为下一轮必查重点。

---

## §10 接口/设计偏离登记(REPORTED 层,V3 内部文档 vs 本地实现;不涉冻结对象)

Design v1.1(V3 untracked,自述「接口已冻结,任何修改须 Owner 另行下令」)与本地实现比对:

| # | 面 | Design v1.1(冻结文本) | 本地实现 | 性质 |
|---|---|---|---|---|
| D1 | M3 IR missing | None(PENDING 正常态,不抛) | 抛 `IRReadError` | **行为级,见 §7** |
| D2 | M2 接口 | `RawBytesIdentity(raw_bytes, sha256)` + `SourceBytesNotFoundError/SourceBytesReadError`(§4.3) | `(bytes_source, sha256)`(不保留 bytes)+ 裸 `FileNotFoundError/OSError` | 接口偏离 |
| D3 | M3 字段名 | `source_sha256`(§4.4) | `source_content_sha256` | 接口偏离 |
| D4 | M5 接口+语义 | `evaluate_identity` @ `scripts/preprocessing_consumer/identity/identity_gate.py`;输出无 `gate` 字段;`mismatches: list`;**VERIFIED+PENDING → 进入 Gate/Admission + 语义层标记 PENDING**(§1.3/§3.1 F4·F5·F13/§4.6) | `evaluate_identity_gate` @ `app/core/identity_gate.py`;输出**增 `gate: PASS|BLOCK` 字段**;`mismatches: tuple`;**VERIFIED+PENDING → BLOCK** | 语义偏离与 **Owner DEC-042 Truth Table 一致**(实现 docstring 已明注「Owner 指令优先于 Design v1.1 §4.6」);接口偏离(路径/函数名/字段)待收口 |

M1(`read_manifest_identity`/`ManifestReadError`/None 语义)与 M4(双轴正交语义)与 Design 一致。**处置:全部登记,不代改;D4 语义方向以 Owner 本轮指令为准,接口面请 Owner/V3 二选一收口(改 Design 或改实现)。**

---

## §11 全量 pytest(独立运行,不引用 Claude 报告)

| 范围 | 结果 | 说明 |
|---|---|---|
| 全量 `pytest -q`(V3 backend,363.29s) | **642 passed, 1 skipped, 1 xfailed, 1 warning, 959 errors** | 959 errors **全部** = `ConnectionRefusedError [WinError 1225]` at **fixture setup**(DSH 环境无 PostgreSQL)——环境性限制,非测试失败;逐条 `--tb=line` 抽验错误原因一致 |
| 身份链 13 文件子集(47.06s) | **642 passed, 1 skipped, 122 errors** | 122 errors 同为 DB fixture `ConnectionRefused`(含新文件 `test_adversarial_m5_round1.py` 全部 69 项 setup 错误)——**Claude 新增 M5 测试在 DSH 环境不可执行**,其自报结果本轮**不可复验**(ROOT CAUSE = 环境 DB 缺失,证据 = 错误类型/位置;非测试内容问题) |
| DSH 自建动态电池(§4–§8) | **27/27 PASS** | 纯函数链,零 DB 依赖,全部本轮实测 |

**OBSERVED(不归因)**:全量与子集 passed 数同为 642,原样记录。

---

## §12 VERIFIED / NOT VERIFIED 清单

**VERIFIED(本轮真实证据)**:
1. Producer 六类冻结对象零变化(G1–G6 全 PASS + 逐文件活测 + source_file 三方比对 87/87);
2. Producer 四项 immutable 全部成立;Contract freeze object 未被修改;
3. Consumer 静态写面对 Producer = 零;全部 Producer 路径引用只读;
4. M5 Truth Table 五格(含 VERIFIED+PENDING→BLOCK)对本地快照 `f3636b35…` 动态实测全部符合 Owner 指令;
5. stale IR 在 M1–M5 函数层唯一出口 = BLOCK;Identity 不被 IR 劫持(14/14);
6. Missing/Invalid Manifest 6 变体 fail-closed,无一误读为 PENDING/VERIFIED;
7. M5 越域伪造值 fail-closed(6/6 BLOCK)。

**NOT VERIFIED**:
1. **M5(乃至 M1–M4)对 push commit 的验证:无对象可验(远端零提交)**——不宣布 M5 通过;
2. 「M5 BLOCK 阻断下游 Gate/Compiler/Admission/materialization」——真实调用链零集成(§9),无从验证;
3. Claude 自报 M5 测试结果——DSH 环境 DB 缺失,不可复验;
4. corpus_sha256 聚合构造——延续 DEC-041 F-C 挂账(本轮未重开,操作性锚 = 逐文件 map,已实测)。

**DISCREPANCY(登记不代改)**:D1(IR missing 语义,行为级)/ D2 / D3 / D4(接口面;D4 语义与 Owner 指令一致)。

**STOP:NOT TRIGGERED**(零冻结对象 mismatch)。

---

## §13 纪律执行记录

- 全程只读(docs-only 登记除外);未改 Consumer 实现一个字符;未改 Producer 数据;未提供补丁;未自行修复 D1~D4;
- 错误路径与不可复验项原样入账(M5 测试不可执行 = 环境限制如实写明,不猜内容层面根因);
- 无证据处写 NOT VERIFIED / OBSERVED,零推测归因;
- DSH 攻击脚本与产物仅落 DSH 临时区,审查后清理,**V3 仓零写入**(untracked 集合变化全部来自 Claude 侧,§1.3);
- 历史方法学保留:逐文件活测 / source_file 三方比对 / SET_EQUAL 双向 / 错误路径原样入账 / 不做无证据归因;
- Trigger ②(post-Phase-1 复检)继续 **ARMED**。

**STATUS:`BOUNDARY: HOLDING / M5 PUSH: ABSENT / M5 LOCAL SNAPSHOT: SEMANTICS PASS + 4 DISCREPANCIES + INTEGRATION PENDING / GUARDIAN MODE: ACTIVE`**

# PREPROCESSING-V3 CONSUMER BOUNDARY CLOSURE GUARDIAN REVIEW v1(DEC-044 执行)

> 轮次:DEC-044 Consumer Boundary Closure Guardian Review(Owner 本轮指令执行,ODR §1novies)
> 审查方:DSH(Frozen Baseline Guardian,只读独立复测;不用 Claude 测试输出代替自己的证据)
> 审查对象:**V3 commit `6c4e3ffd65db50d9522a62db094cf26d3b9cab30`**(唯一审查对象)
> 日期:2026-09-17 · 判定基准:Frozen Contract v0.2(字节亲验 `9c6b9063…7528`/92,197B)+ Owner Truth Table + Design v1.1(参考)

---

## §0 分层结论(TL;DR)

| 层 | 结论 |
|---|---|
| **Producer Boundary** | **VERIFIED**(G1–G6 全 PASS 零漂移,详见 §2) |
| **Consumer Module M1** | VERIFIED(行为矩阵 fail-closed 全过;接口面偏差 D2 族不变) |
| **Consumer Module M2** | VERIFIED(行为正确;接口面偏差 D2 保持 OPEN) |
| **Consumer Module M3** | VERIFIED(行为矩阵 fail-closed 全过;D1 已闭;命名偏差 D3 保持 OPEN) |
| **Consumer Module M4** | VERIFIED(纯函数;str/None 契约域 343 组合零抛异常;判定规则与冻结一致) |
| **Consumer Module M5** | VERIFIED(Truth Table 五格 + 对抗 19 项全 BLOCK/受控 PASS;不抛异常性质达成;D5 已闭;**新增 D-044-1 hardening**) |
| **Consumer System Boundary(真实链)** | **VERIFIED(scoped)**——runner_b2 真实链 A–F 全 BLOCK 且下游零调用;scope 限定见 §5 |
| **Real Runner Bypass** | **PASS**(A–F 攻击 + PASS 控制组,spy 计数证据,§4) |
| **Producer Mutation** | **PASS**(静态零写路径 + 356 面/114 树前后 hash 零漂移 + git 干净,§6) |
| **Contract Discrepancies** | D1 **CLOSED** / D2 **OPEN** / D3 **OPEN** / D4 **OPEN(语义部分 Owner 已裁,接口面待收口)** / D5 **CLOSED** / 新增 D-044-1(WARNING-hardening)、D-044-2(NOTE)、O-1(OBSERVATION) |
| **STOP** | **NOT TRIGGERED**(Producer 与 Frozen Boundary 零破坏;全部遗留为 Consumer correctness/接口面问题,已按 discrepancy 登记) |

**关键问题应答**:「在真实 V3 执行链中,任何未经 Identity + Semantic 双重验证的数据,是否绝对无法进入 semantic Gate / Admission?」
→ **是(在 runner_b2 真实链 scope 内,以 DSH 自采 spy 证据判定)**:六类攻击(manifest mismatch / raw bytes mismatch / IR missing / IR stale / IR malformed / VERIFIED+PENDING)全部 BLOCK,`session_factory`、`_run_full_chain`、`Compiler`、`IRBuilder`、`evaluate`(semantic Gate)、`build_payload`、`SnapshotRepository`/Admission 计数**全部为 0**;PASS 控制组证明门是唯一通道(仅全匹配时打开下游)。

---

## §1 审查对象锁定(11 点清单 ①②)

1. `git ls-remote https://github.com/kurt-wong/AITutors-v3.git` **亲验(本轮实测)**:`refs/heads/main` = `6c4e3ffd65db50d9522a62db094cf26d3b9cab30`(Owner 提供前缀 `6c4e3ff` 相符)。
2. 以该 commit 建**独立临时克隆**(不在 V3 工作区做任何写操作),全部审查/攻击在克隆上执行;**本地 untracked 状态未用作最终证据**。
3. commit 内容:`feat: Phase 2 Consumer Boundary Closure — M1-M5 identity verification + runner integration`,21 files / +6,058 行 = 五模块(`app/core/` M1–M5)+ **`runner_b2.py` 修改(集成)** + 16 份测试。
4. 五模块 hash 与 DEC-045 观察的本地 untracked 锚**逐项相等**(gate `13812a74e12b3fe9`/5,707B · verifier `1306105c6c3d2b8b`/3,725B · ir `1e9ab5fdd7e1fd5f`/4,306B · manifest `1ca33a45a101de8c`/2,811B · raw `803c4ed8a93f59b5`/1,877B)——Claude 本地最终状态即 push 状态,漂移疑虑解除。
5. Frozen Contract 字节从 `f4941ff` 重导(命令重定向法):92,197B / `9c6b9063e81fb2a66d85794b280c9d931f1b0074b39abf472033218149b17528` **MATCH**;`merge-base --is-ancestor f4941ff 6c4e3ff` = **TRUE**;契约文件 `f4941ff..6c4e3ff` diff = **EMPTY**。

## §2 Producer Guardian G1–G6(独立复测,本轮实测)

| 项 | 本轮实测 | 结论 |
|---|---|---|
| G1+G2(source bytes + Manifest)| canonical `freeze_evidence_final_check.py` scratch 重跑:**C1–C9 全 PASS,overall = VERIFIED**(87 接口面 / 87 唯一 sha 键 / 87 值==SHA256(当前字节) / 87 零漂移 / 剥键重序列化 87/87 / locator 87/87)| PASS |
| G3(Producer IR artifact)| `data/resolver_ref_r52/resolver_ir.json` sha256 = `fbcf41ab025fd786614b52d63270160868a2f49ab63121f012905c79f65b04a5` **MATCH** 锚 | PASS |
| G4(证据工件)| step1 `b4f14524…ad99` / step2 `d430cc2f…eec1` / R50 `963cd6b1…ee77` / final-check `a707738e…5c33` 实测 **4/4 MATCH**(+C7 内含 pre/post audit 快照对账)| PASS |
| G5(corpus snapshots)| C4/C7 等价覆盖(接口面 177 文件逐文件;pre/post corpus 双值对账 ok)| PASS |
| G6(freeze artifact)| §1.5 三项全过(MATCH + 亲缘 TRUE + diff EMPTY)| PASS |
| R50 356 逐文件活测 | **269 MATCH / 87 DRIFT / 0 missing**;DRIFT 恰 = 87 份 manifest(已裁 Step-2 回填追加键),0 unexpected(C7 SET_EQUAL 断言)| PASS |
| canonical 测试 | `python -m pytest` = **338 passed / 1 xfailed**(与基线一致)| PASS |
| source_file 目标 | C3 + C9:87/87(声明 == 活字节 sha;locator 与 Step 1 快照一致)| PASS |

**Producer Boundary = VERIFIED;四项 immutable 全成立;基线未变,仅报告实际结果,不机械重复历史结论。**

## §3 Consumer Modules M1–M5(独立静态 + 动态矩阵)

### M1 `manifest_identity.py`(v1.0.0)
直接行为矩阵(自采):valid→sha / absent→None / null→None / empty→None / int→**ManifestReadError** / UPPER-hex→**ManifestReadError** / 顶层 array→**ManifestReadError** / 文件不存在→**ManifestReadError**。只读顶层 `source_content_sha256`,`path`/`source_file` 字段实测不参与 identity。**与 Design §4.2 一致,fail-closed。**

### M2 `raw_bytes_identity.py`(v1.0.0)
`read_bytes()` + `hashlib.sha256` 原语正确(禁 read_text/canonical_json 约束实测遵守);同字节不同路径 → 同 sha;异字节同名 → 异 sha。**接口面偏差(D2)保持 OPEN**:`RawBytesIdentity(bytes_source, sha256)` 字段名 + 裸 `FileNotFoundError/OSError` vs 冻结 `(raw_bytes, sha256)` + `SourceBytes*Error`。runner 侧按 `(FileNotFoundError, OSError)` 捕获 → BLOCK,行为方向安全。**登记不代改。**

### M3 `ir_identity.py`(v1.1.0)——Owner 专项 ③
行为矩阵(自采,20 项):IR missing → None(PENDING 正常态,**D1 已闭**)· null/empty/字段缺失 → None · 单文档双字段名兼容 · batch 条目定位(file 键 locator 匹配)· malformed JSON → **IRReadError** · sha 非 64hex/int/63 长/UPPER → **IRReadError** · 顶层 array → **IRReadError**。
**关键判定(Owner「malformed 归 PENDING 不默认接受」)**:runner 对 `IRReadError` 的处置 = 记录 `ir_error` 且 `ir_sha=None` → M4 semantic=PENDING → M5 **BLOCK**。即 malformed IR 的**最终闸门结果是 BLOCK 而非放行**,满足 Contract §5.6.2 fail-closed(任何关键验证失败 → 阻断消费,不得继续向下游);reason 码精度问题另见 D-044-2。
**stale IR**:batch IR sha ≠ manifest sha → semantic=PENDING(`ir_manifest_mismatch`)→ BLOCK(§4 攻击 D)。IR 只进 semantic 轴,identity 轴实测不受污染(§4 Authority)。

### M4 `identity_verifier.py`(v1.0.0)
str/None 契约域 7×7×7=343 组合零抛异常;判定规则与冻结逐行一致(manifest None→FAILED;computed≠manifest→FAILED;semantic 仅在 VERIFIED 后判定);**实测 verify_identity 永不产出 FAILED+PENDING / VERIFIED+None**(与 Claude 测试无关,DSH 自采)。契约域外 adversarial 类型(自定义抛异常 `__eq__`)可致抛出 —— 输入契约为 str,记 NOTE 不判违规。

### M5 `identity_gate.py`(v1.1.0)——Owner 专项 ④(D5)
- Truth Table 五格实测:VERIFIED+AVAILABLE→**PASS**;VERIFIED+PENDING→**BLOCK**;VERIFIED+None→**BLOCK**(`semantic_absent`);FAILED+任意→**BLOCK**;白名单外值→**BLOCK**(`invalid_state`)。Owner 表逐格相符。
- 对抗 19 项全过:`None` 输入 / 无 identity 属性 / identity=None / 无 value / value 为 int·None·object·list·bytes / 白名单外字符串 / semantic 缺失·错型·越域 / 非 str 自定义 `__eq__` 对象 / 恒 True `EvilStr` → 全 BLOCK;混沌 100 项零抛异常 —— **「不抛异常」冻结要求达成,D5 CLOSED**。
- **D-044-1(本轮新增,WARNING-hardening)**:选择性 `__eq__` 的 `str` 子类(`eq` 仅对 "VERIFIED"/"AVAILABLE" 返真)实测可伪造 **PASS**(garbage 值通过白名单)。真实链风险 = 低:M5 唯一合法输入源是 M4 的字面常量,伪造需进程内代码执行(已构成更高威胁)。建议(不代修):值域检查改 `type(x) is str`。
- **Design v1.1 §4.6 文本 vs 实现**:design 原文「identity_state=VERIFIED → 进入 Gate/Admission(semantic PENDING 仅标记)」被 **Owner Truth Table 显式超越**(VERIFIED+PENDING→BLOCK),实现 docstring 已注 Owner 优先 —— 与本轮 Owner 指令一致,**以 Owner 表为准**;design 文本待 v1.2 收口(随 D4 接口面)。

## §4 Consumer System Boundary —— 真实链攻击(Owner ⑥⑦⑧)

方法:导入真实 `runner_b2` 模块(不打行为补丁),以 **spy 计数**替换下游符号(`async_session_maker` / `_run_full_chain` / `Compiler` / `IRBuilder.build` / `evaluate` / `build_payload` / `SnapshotRepository`),经真实入口 `run_corpus()` 攻击。临时合成语料 + 真实语料双轨。

| 攻击 | 构造 | 实测结果 | 下游计数 |
|---|---|---|---|
| A Manifest mismatch | 声明 sha ≠ 真实字节 sha | BLOCK/FAILED/`identity_verification_failed` | **全 0** |
| B raw bytes mismatch | 声明正确 sha,文件后篡改 | BLOCK/FAILED | **全 0** |
| C IR missing | 无 resolver IR | BLOCK/VERIFIED+PENDING/`semantic_pending` | **全 0** |
| D IR stale | batch IR sha ≠ manifest sha | BLOCK/VERIFIED+PENDING | **全 0** |
| E IR malformed | resolver IR 非法 JSON | BLOCK/VERIFIED+PENDING + `ir_error` 记录 | **全 0** |
| F manifest sha 缺失 | 无 `source_content_sha256` 键 | BLOCK/FAILED | **全 0** |
| PASS 控制组 | 三方全匹配 | **PASS**/VERIFIED+AVAILABLE,`session_factory=1`,`_run_full_chain=1` | 门开(唯一通道证明)|

**四不变量(M4+M5 独立复现)**:VERIFIED+AVAILABLE→PASS ✅ / VERIFIED+PENDING→BLOCK ✅ / FAILED+None→BLOCK ✅ / FAILED+PENDING→BLOCK(直接构造)✅;VERIFIED+None→BLOCK ✅。
**IR mismatch 不得绕过**:identity=VERIFIED、semantic=PENDING(`ir_manifest_mismatch`)→ BLOCK —— IR 失配无法以 VERIFIED 身份绕过 semantic Gate ✅。

**真实语料实测**(零合成):`reslice-p2-b1`(38 manifests)× 2 跑(无 IR / 真实 resolver IR)= **38/38 identity_blocked,0 completed,0 error**;接口 87 面三目录(50+22+16=88)× 真实 resolver IR = **88/88 blocked**(87 = VERIFIED+PENDING,1 = FAILED `manifest_sha_missing`,恰为面外第 88 份)。
**O-1(OBSERVATION)**:71 份 ADMITTED 在真实语料上全部落 semantic PENDING —— 根因实测 = manifest `source_file` 定位符(`Ocr-markdown\会考\…`)与 resolver IR `file` 键(`Ocr-markdown\reslice-batch-C\会考\…`)为不同副本路径,绝对路径字符串等值匹配失败 → `ir_absent`。**方向 = fail-closed(安全侧),无 bypass;但真实数据 semantic availability 当前不可达** —— 集成可用性问题,归 Claude 处置,DSH 不代修、不猜其余根因。

## §5 真实入口普查(Runner Bypass)

| 入口 | M1–M5 | 分类 |
|---|---|---|
| `runner_b2.py` | **已接线**(M1→M5 先于一切 semantic consumption;BLOCK 在 DB session 打开之前短路;`_run_full_chain` 内有二次防御)| **真实生产链入口 —— 本轮验证对象** |
| `runner.py` | 无(历史 Phase 0 报告器,「输出是报告,不是入库结果」)| 报告脚本,不产生 Admission 写 |
| `runner_b3.py` | 无(实验脚本,冻结规则明言「不写生产数据库」)| 实验脚本 |
| `p32_enforcement_experiment.py` | 无(直写 `create_admission_candidate`,合成数据实验)| **NOTE:实验脚本未门控**(非语料摄入链;建议 Claude 在脚本头显式标注 experimental-only)|
| `scripts/gate_b/*probe*.py` | 无(审计探针)| NOTE 同上 |

**scope 声明**:Consumer System Boundary VERIFIED 的 scope = `runner_b2` 语料摄入链(Contract §5.6.2 面向的「preprocessing → V3 消费」路径)。实验/探针脚本不在门控内,已登记 NOTE;V3 通用 API 的用户上传流属 V3 内部边界,不在 preprocessing Consumer Boundary 范围。
**Materialization**:runner_b2 链内 Materialization = AdmissionCandidate 创建,位于 M5 PASS 之后同一 try 块内;BLOCK 路径实测零到达。Question/Instance 写入 = 同一通道,零到达。

## §6 Producer Mutation Attack(Owner ⑨)

- **静态**:五模块所在 `app/core/` 全目录对 `write_text/write_bytes/os.replace/rename/unlink/shutil/tempfile/mkstemp/NamedTemporary/move` **零命中**;`preprocessing_consumer/` 面仅 4 处 `write_text`,全部 = 报告输出到调用方指定路径(runner_b2 默认落 V3 仓自身,本轮全部重定向至 DSH 临时区)。Consumer 代码对 Producer 路径**无任何写路径**。
- **动态(前后 hash 双证据)**:R50 356 键面 + `reslice-p2-b1` 114 文件树,三轮真实链执行(2×p2-b1 + 1×接口面)前后散列对比 = **drift 0 / 增删 0**;`Ocr-markdown` 内零新文件(报告全部落临时区);Papers `git status --porcelain` 前后均为空;canonical pytest 复跑 338/1(测试执行本身亦零写)。
- **Producer Mutation = PASS。**

## §7 Discrepancy 终态(D1–D5 + 本轮新增)

| # | 内容 | 终态(6c4e3ff 实测)|
|---|---|---|
| D1 | M3 IR missing 抛 IRReadError(vs Design = None)| **CLOSED**(实测 None → PENDING 正常态)|
| D2 | M2 接口偏离(字段名 + 异常类型)| **OPEN**(行为安全,接口面待收口;登记不代改)|
| D3 | M3 dataclass 字段名 `source_content_sha256` vs design `source_sha256` | **OPEN**(命名,不影响行为)|
| D4 | M5 路径/命名/输出字段/mismatches 类型偏离 + PENDING 语义 vs design §4.6 | **OPEN(部分已裁)**:语义部分(VERIFIED+PENDING→BLOCK)= Owner Truth Table 生效,design 文本被超越;接口面(路径/命名/字段)待 Claude 与 design v1.2 收口 |
| D5 | M5 对 None/缺属性输入抛 AttributeError | **CLOSED**(v1.1.0 fail-closed,混沌 100 零抛)|
| **D-044-1** | M5 白名单可被选择性 `__eq__` 的 str 子类伪造 PASS(实测复现)| **NEW / WARNING-hardening**(真实链输入源为 M4 字面常量,威胁有限;建议 `type(x) is str`;不代修)|
| **D-044-2** | batch IR `files` 非 list → 静默 None(非 IRReadError)| **NEW / NOTE**(outcome 仍 BLOCK fail-closed;reason 码精度;不代修)|
| **O-1** | resolver IR 绝对路径 locator 与 manifest `source_file` 不一致 → 真实数据 semantic 全 PENDING(71 ADMITTED 不可达)| **NEW / OBSERVATION**(fail-closed 安全侧;可用性归 Claude)|
| 集成缺口(旧)| runner_b2 零 M1–M5 调用 / M5 无生产 caller | **CLOSED**(本轮实测已接线 + 攻击验证)|

## §8 STOP 判定与纪律

- **STOP = NOT TRIGGERED**:Producer 四项 immutable 成立、Frozen Contract 字节 MATCH、R50 面 356 前后零漂移、Papers 工作树干净 —— Producer 与 Frozen Boundary **零破坏**。全部遗留项(D2/D3/D4 接口面、D-044-1/2、O-1)均为 Consumer correctness / 接口收口 / 可用性问题,按 discrepancy 登记,**不与 STOP 混淆**。
- 纪律:全程只读(docs-only 登记除外);未修改 Producer;未修改 V3 Consumer(审查在临时克隆上进行,V3 工作区零写入);未提供补丁;**NO SELF-FIX**;不用 Claude 测试输出代替自己的证据(全部数据本轮自采);无证据处(如 PASS 路径下游 DB 实际执行,因 DB down = 已知 S-2)如实写环境限制,不作推断。
- 环境限制(如实登记):PASS 控制组与真实数据 PASS 路径的 **DB 层实际执行未活体验证**(攻击环境 DB down);已用 spy 证明门控位置与短路行为,DB 执行属 V3 既有 Gate/Admission 链(Contract §5.6.1 明言不因本阶段变动)。D-045-4(attacks 套件复跑)维持 DEFERRED。

*v1 · 2026-09-17 · DSH Guardian(DEC-044 执行)。证据工件存 DSH 临时区(`dec044_attack_out` / `dec044_g6`),按纪律不入 Producer 面;本文件即证据账本。*

# PREPROCESSING — Phase 2.5 Consumer Data Activation & Interface Closure Guardian Review v1

- **Review ID**: DEC-048(Owner 指令:Phase 2.5 closure review,exact SHA `cc12d79`)
- **Reviewer**: DSH(Producer Evidence Producer + Frozen Baseline Guardian)
- **Review date**: 2026-09-17
- **审查对象(唯一)**: `kurt-wong/AITutors-v3` @ `cc12d79e9a22f6274100ea0bb61f92493ba88509`
  - ls-remote 亲验 = `refs/heads/main`;独立临时克隆 `v3_review_cc12d79` checkout 精确 SHA
  - ancestry: `f4941ff(freeze) → … → 6c4e3ff(DEC-047 审查对象) → cc12d79(本轮)` 直接后继
- **前置基线**: DEC-047(`9480985`)对 `6c4e3ff` 的 Closure Review
- **纪律**: independent audit / exact SHA / no self-fix / no Producer mutation / no premature closure;不因 Claude 900+ tests 降低强度;审查重心 = 「坏输入挡得住 + 合法真实输入确实能通过 + 不因 locator/legacy/data-readiness 被错误挡住」

---

## 0. 分层结论(不以单一 VERIFIED 覆盖)

| 层 | 结论 | 核心证据 |
|---|---|---|
| **Producer Boundary** | **VERIFIED** | G1–G6 全 PASS(C1–C9 overall VERIFIED;R50 356 = 269 MATCH / 87 已登记回填 drift / 0 missing;G6 契约重导 `9c6b9063…7528`/92,197B MATCH + `f4941ff ⊂ cc12d79` + 契约路径 diff EMPTY;resolver_ir `fbcf41ab…b04a5` MATCH;canonical pytest 见 §2.5;Papers schema 9 passed) |
| **Consumer Module Boundary** | **VERIFIED(带 hardening 发现)** | M1–M5 全模块独立复测 + 15 项 locator 对抗 + M5 subclass 攻击;发现 D-048-1(M5 残留绕过 WARNING-hardening)、D-048-2(positional fallback NOTE) |
| **Consumer Runner Boundary** | **VERIFIED** | 真实 `run_corpus()` 入口,攻击 A–F 全 BLOCK,spy(session/full_chain/IRBuilder/Compiler/evaluate/build_payload/SnapshotRepository)全 0 |
| **Real PASS Path** | **VERIFIED(活体 DB 首次达成)** | 真实 Producer 工件 71 份文档全链 PASS → 真实下游执行(spy 全正)→ rollback 后 DB 计数不变 |
| **Real BLOCK Path** | **VERIFIED** | 真实语料 17 份 BLOCK(16 PENDING + 1 FAILED)+ 合成攻击 6/6 BLOCK,零下游 |
| **Data Readiness** | **71/88 可达,17 fail-closed** | 71 ADMITTED 全部活体 PASS;16 REJECTED_QC_FAIL → PENDING(设计内);1 out-of-scope → FAILED;Claude prerequisite 报告与 Producer 事实一致 |
| **Locator Contract** | **VERIFIED(PATH ≠ IDENTITY 成立)** | 15 项对抗:无宽松匹配、无 false association;sha-first 确定性内容关联;2 项 NOTE 级观察(§7) |

**STOP**: NOT TRIGGERED。Producer 与 Frozen Boundary 零破坏;全部发现位于 Consumer hardening 面,无 fail-closed 逃逸。

---

## 1. 对象锁定与变更面

- `6c4e3ff..cc12d79` = 8 files / +1,125 / −28:
  - 模块:`identity_gate.py`(v1.1.0→**v1.2.0**,`_normalize_str` str-subclass 防御)、`ir_identity.py`(v1.1.0→**v1.2.0**,batch IR locator closure:source_sha 优先 / path fallback / positional fallback)、`runner_b2.py`(M3 调用传入 `computed_sha`)
  - 新测试:`test_adversarial_m5_str_subclass.py`(285 行)、`test_adversarial_ir_locator.py`(336 行)、`test_real_producer_activation.py`(390 行);既有 2 个测试微调
- 模块 hash @ `cc12d79`:
  - manifest_identity `1ca33a45a101de8c`/2811B、raw_bytes_identity `803c4ed8a93f59b5`/1877B、identity_verifier `1306105c6c3d2b8b`/3725B —— **与 DEC-047 锚逐字节一致(未动)**
  - identity_gate `8a5d267e285800f0`/6163B、ir_identity `f960b513a935c8ca`/6430B —— 本轮变更(见上)
- entry census:无新增入口;`runner_b2.py` 仍为唯一 gated 生产摄入链(runner.py 报表 / runner_b3 实验 / p32 实验 / probe 审计脚本均未触碰)

---

## 2. Producer Guardian(G1–G6 全量重推,DSH 自采)

### 2.1 C1–C9(freeze_evidence_final_check 重导,输出重定向临时区,登记工件零覆盖)
C1 PASS(scope 87,identity_version==2)/ C2 PASS(87/87 sole key)/ C3 PASS(87/87 == SHA256 当前源字节)/ C4 PASS(源字节自 Step1 快照未变)/ C5 PASS(ADMITTED 71/71 == manifest sha)/ C6 PASS(Pending 16/16)/ C7 PASS(R50 谱系:drift 恰为 87 manifest 回填集,missing 0)/ C8 PASS(strip-key 重序列化 == R50 基线 87/87)/ C9 PASS(path 非身份,locator 自快照未变)→ **overall: VERIFIED**

### 2.2 R50 live
`audit_integrity.verify(R50_input_baseline)`:n_files 356,drift 87(全部 manifest,= 登记回填集),missing 0 —— 与 DEC-047 登记谱系完全一致。

### 2.3 G3/G4
resolver_ir.json sha256 = `fbcf41ab025fd786614b52d63270160868a2f49ab63121f012905c79f65b04a5` MATCH;G4 既有工件锚未被触碰(Papers 工作树 clean,git status porcelain 空)。

### 2.4 G6 Freeze Object
`f4941ff:PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` 重导 = 92,197 bytes,sha256 `9c6b9063e81fb2a66d85794b280c9d931f1b0074b39abf472033218149b17528` MATCH;`git merge-base --is-ancestor f4941ff cc12d79` = TRUE;`f4941ff..cc12d79` 契约路径 diff = **EMPTY**(冻结契约字节零变化)。

### 2.5 canonical tests
- V3 克隆 `python -m pytest -q -p no:cacheprovider`(testpaths=tests,无 ACL 限制对照环境):**1780 passed / 1 skipped / 1 xfailed / 0 failed / 0 errors(49.08s)** —— 相对 DEC-047(338/1,DB down)因 DB 恢复 + 新增测试而大幅上探,零回归。
- 同套件在 DSH 沙箱(workspace-write)下 = 1539 passed / 1 skipped / 1 xfailed / **3 failed + 238 errors**;逐项定性:**全部 241 个非通过 = 同一环境怪癖**(487 处 PermissionError;每个失败/报错测试均使用 `tmp_path` 或 `tempfile.TemporaryDirectory`)。机制探针 4 格矩阵:pathlib `mkdir` OK / `os.mkdir` OK / **`tempfile.mkdtemp`(0o700)PermissionError** / **`TemporaryDirectory`PermissionError** —— 沙箱 ACL 与 tempfile 受限权限建目录互斥。对照复测(失败子集 206 例,无 ACL)= **206 passed 全绿**。零代码回归。同根因附带发现:沙箱下 pytest cacheprovider 收尾 `mkdtemp` 自旋,进程跑完测试后不退出(实测卡 2.5h+,py-spy 栈证实位于 `pytest_sessionfinish`)—— 复跑 canonical 需 `-p no:cacheprovider`。
- Papers `tests/test_coordination_state.py`:**9 passed**(DEC-048 四账登记后复跑)。

---

## 3. Consumer M1–M5 独立复测

### 3.1 M5(str subclass 专项,Owner 重点)
| 攻击 | v1.1.0(前) | v1.2.0(本轮实测) | 判定 |
|---|---|---|---|
| EvilEq:无差别 `__eq__`→True + 垃圾值 | **PASS(绕过,D-044-1)** | **BLOCK**(invalid_state) | ✅ 修复生效 |
| EvilStrOnly:`__str__`→self,无自定义 `__eq__` | — | **BLOCK**(invalid_state) | ✅ |
| **EvilSel:`__str__`→self + 选择性 `__eq__`** | — | **⚠️ PASS(VERIFIED/AVAILABLE,垃圾值)** | ❌ **D-048-1 残留绕过** |
| EvilRaise:`__str__` 抛 RuntimeError | 不触发(v1.1.0 不调用 str()) | **⚠️ 异常逃逸 evaluate_identity_gate** | ❌ **D-048-1b 边界回归** |
| int/bytes/None 伪装 / Truth Table 五格 / 输出 plain str | — | 全 BLOCK / 全符 / type 全 str | ✅ |

- **根因(静态定位)**:`_normalize_str` 的 `str(val)` 对「`__str__` 返回自身 subclass 实例」不产生 plain str 副本(CPython 接受 str subclass 作为 `__str__` 返回值),白名单 `in` 比较随后调用 subclass 自定义 `__eq__` → 绕过;`__str__` 抛异常则直接穿透(违反模块自述「不抛异常」纯函数边界)。
- **可达性**:真实链中 M5 输入恒为 M4 冻结 dataclass 的 plain-literal 字面量(runner 不接受外部对象)→ **威胁等级 = hardening-only,非真实链逃逸**;但 Claude 自述的「str subclass 防御」并不完备。
- **建议(登记不代改)**:`if type(val) is not str: return None`(exact type gate),可同时消除两条;或 `try/except` 包裹规范化 + exact-type 比较。**DSH 不修改 Consumer**。

### 3.2 M3 locator 15 项对抗(全部 DSH 自建 fixture)
L1 绝对/相对不匹配→None ✓;L1b 同场景带 sha→命中(PATH≠IDENTITY 正例)✓;L2 正反斜杠→None ✓;L3 大小写→None ✓;L4 路径篡改+sha→命中 ✓;L5 同路径异内容→返回条目 sha,下游 M4 判 **VERIFIED+PENDING→BLOCK**(身份轴不受污染)✓;L6 同内容异路径→sha 命中 ✓;L7 重复 sha+路径不匹配→None ✓;L7b 重复 sha+路径匹配→sha ✓;L9 顺序投毒(伪条目前置)+sha-first→仍取真条目 ✓;L9b 同场景无 sha→取到伪 sha→下游 BLOCK(可用性损失,安全侧)✓;L10 大写 hex→IRReadError(记录后 PENDING,不放行)✓;L11 非 str file 字段→无崩溃 ✓;L12 files 非 list→None(D-044-2 维持,fail-closed)✓;L13 空 batch→None ✓;L14 ir 非 dict→跳过无崩溃 ✓;L15 sha-only→命中 ✓。**无任何宽松字符串匹配,false association 零成立。**

### 3.3 M1/M2/M4
未改动(hash 锚一致);真数据抽查:PAC `pac-c01-01` 与 batch-C 历史卷,M1==M2、M3(sha 定位)==M2、M4=VERIFIED/AVAILABLE、M5=PASS —— DSH 独立重导,与 Claude 测试断言一致。

---

## 4. Consumer Runner Boundary — BLOCK proof(真实 `run_corpus()` + spy)

合成攻击语料(独立构造 manifest+source+IR,走真实入口;spy=委托计数器,不替换真实执行):

| 攻击 | 结果 | spy(session/chain/irbuilder/compiler/evaluate/payload/snaprepo) |
|---|---|---|
| A manifest sha 篡改 | BLOCK(identity FAILED) | 全 0 |
| B source bytes 篡改 | BLOCK(identity FAILED) | 全 0 |
| C 无 IR | BLOCK(VERIFIED+PENDING) | 全 0 |
| D stale IR(路径对、sha 旧) | BLOCK(VERIFIED+PENDING) | 全 0 |
| E malformed IR(JSON 损坏) | BLOCK(PENDING,ir_error 记录) | 全 0 |
| F IR 无对应条目 | BLOCK(VERIFIED+PENDING) | 全 0 |
| PASS 对照(三方匹配) | completed | session/chain/irbuilder/compiler/snaprepo = 1 |

Question/QuestionInstance:整条 preprocessing 消费链零引用(属更后段),「未执行」平凡成立;链内唯一写入点 = SnapshotRepository(create_admission_candidate),已 spy 覆盖。

---

## 5. Real PASS Path — 活体全链(本轮新增重点,DB 已恢复)

`run_corpus()` × 真实三语料(reslice-pac-annotated 22 / reslice-batch-C 50 / resliced-pilot 16)+ 真实 resolver_ir(r52):

| 语料 | manifests | PASS 全链 | BLOCK | spy(正向下游) |
|---|---|---|---|---|
| PAC | 22 | **18** | 4(PENDING) | session=chain=irbuilder=compiler=snaprepo=18;evaluate=payload=120 |
| batch-C | 50 | **38** | 12(PENDING) | =38;evaluate=payload=309 |
| pilot | 16 | **15** | 1(FAILED) | =15;evaluate=payload=113 |
| **合计** | **88** | **71** | **17** | compiled leaves = 542,全部经真实 Compiler/Gate |

- **71 = 恰好 resolver IR 的 ADMITTED 71**;17 = 16 REJECTED_QC_FAIL(PENDING,fail-closed 设计内)+ 1 out-of-scope(FAILED)。数字与登记的 87·71·16 结构闭合。
- PASS 文档:M1→M2→M3(sha 定位)→M4→M5 PASS → 真实 DB session → SourceRepository 建档/seal → IRBuilder → Compiler → semantic evaluate → build_payload → SnapshotRepository.create_admission_candidate —— **全部真实执行,非 synthetic fixture,非 mock**。
- DB 活体计数(documents / admission_candidates)运行前后相等 —— run_corpus 的 rollback 生效,审查零残留。
- 对照:Claude 的 `test_real_producer_activation` 用真实数据做 M1–M5 边界(可信)但 downstream 证据为 mock;本轮以活体证据补足该层。

---

## 6. Data Readiness 与 prerequisite 报告核对

- Producer 事实:87 manifest 已回填 identity_version==2(C1–C3 PASS),resolver IR 88 条(71 ADMITTED with sha / 16 REJECTED_QC_FAIL)。
- Claude 报告(test_real_producer_activation docstring):「identity_version: 2,source_content_sha256 已回填」「数据 readiness 前提已满足(87 manifests 已回填)」—— **与 Producer 事实一致,无夸大**。
- Consumer correctness 与 Producer data readiness 已分账:17 份 BLOCK 全部因数据侧(IR 缺失/QC fail/out-of-scope),Consumer 无一处因放宽 fail-closed 而放行;亦无合法真实输入被错误挡住(71/71 ADMITTED 全达 PASS;87 VERIFIED 的 manifest 全部正确判定身份轴)。

---

## 7. Discrepancy 终态

| ID | 级别 | 内容 | 状态 |
|---|---|---|---|
| **D-048-1** | WARNING(hardening) | M5 `_normalize_str` 可被「`__str__`→self + 选择性 `__eq__`」subclass 绕过(实测 PASS 垃圾值);`__str__` 抛异常逃逸,违反不抛异常边界 | **NEW,登记不代改**;建议 `type(val) is not str` exact-type gate |
| **D-048-2** | NOTE | M3 无 locator 参数时 positional fallback 返回首条目 sha(宽松关联仅存在于省略双 locator 的调用点;runner 恒传双 locator,下游身份相等约束仍强制) | **NEW,登记不代改**;建议要求 ≥1 locator |
| D-044-1 | WARNING→部分修复 | EvilEq 路径已修复;残留并入 D-048-1 | 部分 CLOSED |
| D-044-2 | NOTE | batch `files` 非 list 静默 None(结果仍 BLOCK/PENDING fail-closed) | 维持 |
| **O-1** | OBSERVATION | resolver IR 绝对路径 locator ≠ manifest source_file → 真实数据语义不可达 | **CLOSED by Phase 2.5**:sha-first locator 使 71/88 活体可达 PASS(§5) |
| D2 | OPEN(接口面) | M2 `bytes_source/sha256` + 裸 FileNotFoundError/OSError vs 冻结设计 `(raw_bytes,sha256)` + SourceBytes*Error | 维持(hash 未动),待 Owner 裁决 |
| D3 | OPEN(接口面) | M3 dataclass 字段 `source_content_sha256` vs 设计 `source_sha256` | 维持,待 Owner 裁决 |
| D4 | OPEN(文本面) | M5 输出面语义已 Owner 裁决;design §4.6 文本待 v1.2 | 维持 |

Claude 本 commit 未改动任何设计/契约文档,未自称 OWNER DECISION,无越权重定义规范。

---

## 8. STOP 检查与纪律

- Producer:零字节破坏(G1–G6 PASS);Frozen Contract:零变化(diff EMPTY);两仓工作树:DSH 零写入(全部证据在独立临时克隆 + %TEMP% scratch)。
- 本轮升级目标应答:「坏输入挡得住(A–F + 6 攻击 BLOCK,spy 全 0)✅;合法真实输入确实能通过(71 活体 PASS 全链)✅;不因 locator/legacy/data-readiness 被错误挡住(87 VERIFIED 全正确、17 BLOCK 全数据侧、locator 15 项无误伤)✅」。
- 唯一残留风险 = D-048-1/2,均 hardening/NOTE 级,不影响 fail-closed 主张。

### 8.1 OBSERVATION(审查窗口内工作树未知删除事件,D-048-3)

- **事实**:2026-09-17 **15:09:26–15:09:29**(目录 mtime 亲测),Papers 工作树出现 9 个 tracked 文件被删:`data/bug24_{after_batch_c,after_pilot,before_batch_c}_qc.json`、`data/r66_d5a_snapshot_check.json`、`data/reslice_pilot_qc.json`、`tests/samples/artifact/` 3 件、`tests/samples/source/` 1 件(整个 source 目录消失)。开工时(本审查首轮)`git status --porcelain` 为**空**,删除发生于审查窗口内。
- **排查(穷尽,无证据不推断根因)**:DSH 本窗口全部命令逐条核对,写面仅 = 5 件 docs 登记 + %TEMP% scratch,对上述路径零写;V3 临时克隆全仓 grep(`samples`/`bug24`/`r66`/`reslice_pilot_qc`/Papers 路径 + 删除符号)= 零命中;运行中进程表(提升权限枚举)= 唯一 python 为克隆 pytest(`-m pytest -q`,cwd 在克隆内),另有 MCP filesystem server(rooted `D:\`,属他方会话)——**行为者不可证,ROOT CAUSE = UNKNOWN,不推断**。
- **处置**:上述文件均为 committed 工件且非 G1–G6 冻结对象(R50 356 面不含它们,删除后 R50 复验仍 269/87/0);已 `git checkout --` **恢复至 HEAD 字节态**(保守回正,可逆);恢复后工作树 = 仅本轮 5 件 docs。**建议 Owner 知悉并排查是否有并行会话/清理脚本在 Papers 面活动。**

```
BOUNDARY: HOLDING / GUARDIAN: ACTIVE
PHASE 2.5 REVIEW: COMPLETE
PRODUCER MUTATION: NONE / FROZEN CONTRACT: UNCHANGED
STOP: NOT TRIGGERED / NO SELF-FIX
```

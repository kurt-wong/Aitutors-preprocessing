# PREPROCESSING-PRODUCER-GUARDIAN-M5-REVIEW-ADVERSARIAL-v1

- **轮次**:DEC-043(对 DEC-042 = Consumer M5 Boundary Guardian Review 全部结论的第一性原理对抗性审查;Owner 指令原文照录 = ODR v1.24 §1quinvicies)
- **纪律**:每个结论必须有本轮真实测试证据;不降标准;不自我合理化;不强行解释未通过项;不靠推测输出结论;全程只读(docs-only 登记除外)
- **审查基点**:本仓 `HEAD` = `3e5b3b5`(DEC-042 登记提交,== origin/main);V3 工作树 = Claude 实时开发中(移动目标纪律同前)

---

## §0 总判定

| 结论面 | DEC-042 原结论 | 对抗性复测 | 判定 |
|---|---|---|---|
| PRODUCER BOUNDARY | HOLDS(G1~G6 PASS,四项 immutable) | G1~G6 独立重跑全 PASS;G6 残留 False + 亲缘 TRUE + diff EMPTY | **维持** |
| M5 push 状态 | ABSENT,不宣布通过 | 重 fetch + ls-remote:`72af28d…6233` 未变;**换方法**(全树 `ls-tree -r` 434 文件 + 全仓 `git grep` 符号 + preprocessing_consumer 目录枚举)三重证实该 commit 零身份链代码 | **维持(证据加强)** |
| M5 本地语义(Truth Table 等) | 电池 27/27 PASS | v2 电池独立复跑 **27/27 ×2**;盲区补测 **13/13**;快照散列与 DEC-042 锚逐项一致(`f3636b35…` 等) | **维持且加强** |
| 真实链零集成 | NOT VERIFIED(INTEGRATION PENDING) | 扩展清扫(importlib/`__import__`/getattr 全仓)scripts 面零身份链引用,复证 | **维持** |
| Boundary 静态零写面 | core 零写面 | 二轮扩展模式(`os.utime/touch/rmtree/os.remove/NamedTemporaryFile/mkstemp`)全仓零命中 | **维持** |
| pytest 诸结论 | 642 passed / 959 errors /「全部 ConnectionRefused」/「ROOT CAUSE = 环境 DB 缺失」/「642==642 巧合 OBSERVED」 | 复跑:642 passed 稳定(3/3);**errors 959→1036**(收集面变化,见 F-2);**「ROOT CAUSE」归因被推翻(见 F-1)**;「巧合」被普查解释(见 F-4) | **部分更正** |
| untracked 计数 | 「10 docs(REPORT-PHASE2-M4 新增)+ 15 tests」 | 实测 **9 docs + 5 core + 14 tests = 28**;REPORT-PHASE2-M4 在全部工具输出中从未出现 | **证伪,更正(见 F-3)** |

**STOP:NOT TRIGGERED**(本轮全程零冻结对象字节变化)。

---

## §1 审查对象与快照复核

- 重 `git fetch` + `ls-remote origin`:V3 `origin/main` = `72af28d5854b56fc605e1897fb757703826a6233`(未变);本仓 = `3e5b3b5`(== origin/main,工作树干净)。
- 本地身份链快照重散列:五 core 模块 + 关键测试 sha 前缀与 DEC-042 登记值**逐项相等**(`identity_gate f3636b35…` / `identity_verifier 1306105c…` / `ir_identity 9315c22e…` / `manifest_identity 1ca33a45…` / `raw_bytes_identity 803c4ed8…`;测试 5 件同值)——审查窗口内本轮未再漂移。
- **换方法复验「push commit 零身份链代码」**:① `git ls-tree -r 72af28d` 全树 434 文件,身份类名命中仅 3 件既有 V3 内部件(`compile/identity_normalization.py`、`test_identity_projection.py`、OQ1 决策文档,均非 M1–M5 身份链);② 全仓 `git grep` 六个身份链符号 = 空;③ `backend/scripts/preprocessing_consumer` 目录枚举 21 件,无 `identity/` 子目录。三法一致。

---

## §2 攻击一:电池本身(v2 复现 + v3 盲区)

### 2.1 v2 电池(27 项)独立复跑 = 27/27 ×2 次一致

Truth Table 五格(含 VERIFIED+PENDING→BLOCK 真实文件链)/ stale IR / Manifest 6 变体 / IR 变体 / 劫持 14/14 / 叉积枚举 / 越域 6/6 —— 全部复现,零翻转。

### 2.2 v3 盲区补测(DEC-042 未覆盖)= 13/13 执行,新发现 1 项 discrepancy(D5)

| # | 用例 | 实测 | 判定 |
|---|---|---|---|
| B1 | manifest 顶层 JSON 数组 | `ManifestReadError` | fail-closed ✅ |
| B2 | manifest 路径 = 目录 | `ManifestReadError`(OSError 包裹) | fail-closed ✅ |
| B3 | manifest 带 UTF-8 BOM | `ManifestReadError` | fail-closed ✅ |
| B4 | manifest 重复键(两值不同) | last-wins(`json.loads` 语义),值 = 后键 | OBSERVED(无契约条款,记录不裁) |
| B5 | **M5 输入 = None** | **抛 `AttributeError`** | **D5**:与 M5 docstring 及 Design v1.1 §4.6「M5 是纯函数…**不抛异常**」矛盾;M4 正常输出不可达此路径;失败方向 = raise(非 bypass),登记不代改 |
| B6 | M5 输入 = 无 identity 属性对象 | 抛 `AttributeError`(同类) | 同 D5 |
| B7 | 伪造 VERIFIED+非空 mismatches+AVAILABLE | PASS 且 mismatches 透传 | OBSERVED(M4 不可达:VERIFIED 恒空 mismatches) |
| B8 | M4 单独:non-hex 相等串 | VERIFIED/PENDING | OBSERVED;**B8b**:M1 对该 manifest 抛 `ManifestReadError` —— 真实链上游阻断,链安全 |
| B9 | M2 输入 = 目录 | OSError 族抛出 | fail-closed ✅ |
| B10 | 同输入 5 次链式判定 | 输出集合基数 = 1 | 确定性 ✅ |
| B11 | sha 带前导空格 | `ManifestReadError`(严格) | fail-closed ✅ |
| B12 | IR sha 藏于嵌套键 | 不读取 → None(PENDING 路径) | 顶层-only 语义 ✅ |

---

## §3 攻击二:pytest 诸结论(重点,发现 F-1/F-2/F-4)

### 3.1 F-1(方法学自我更正):DEC-042「ROOT CAUSE = 环境 DB 缺失」= 超证据归因,推翻

本轮实测事实链(全部真实测试):

1. `Get-NetTCPConnection -LocalPort 5432` = **不监听**(事实);
2. `tests/conftest.py:21` `migrated_db` = **session autouse**(alembic upgrade → asyncpg);单测 traceback 亲证错误源自 `migrated_db`(非 `session` fixture);
3. **但行为与「无 DB → 全部失败」不相容**:`test_raw_bytes_identity.py` 单跑 **4/4 全 passed**(10 passed,0.04s,--setup-show 亲见 `migrated_db` SETUP 成功);`test_hashing.py`(纯函数、零 fixture 请求)单跑 **5/5 全 error**(10/10 ConnectionRefused);两者组合(两种顺序)均为「raw_bytes 全过 + hashing 全错」——**同进程内、顺序无关、按文件确定性分化**;
4. 同一 session fixture 在同进程内对前一批测试成功、后一批失败,机制无法用「环境无 DB」统一解释。

**更正**:DEC-042「ROOT CAUSE = 环境 DB 缺失」属**未充分证据的根因归因**(违反"不要因为测试失败就猜测根因"),予以撤回;正确口径 = **OBSERVED(按文件确定性分化:hashing 5/5 失败 / raw_bytes 4/4 通过,顺序无关,机制不可复现)/ ROOT CAUSE UNKNOWN**。「port 5432 不监听」保留为事实层观测。

### 3.2 F-2:「959 errors」非稳定值(时效性说明)

全量复跑(本轮,--tb=line / -v):**642 passed / 1 skipped / 1 xfailed / 1036 errors(17.3~17.4s)** vs DEC-042 的 959 errors(363s)。总用例数 1603→1680(+77)——增量与 DEC-042 跑后 Claude 新增 `test_adversarial_m5_round2.py` 被收集相容(该文件 DEC-042 轮已在 status 中出现于 pytest 之后)。DEC-042 数字为当时真实工具输出,如实保留;**登记口径修正 = errors 计数随收集面与环境变化,非基线**;passed=642 才是三轮稳定值。

### 3.3 「errors 全部 ConnectionRefused」证据等级修正

- 子集面:**122/122 全量普查证实**(逐行解析,唯一异常类型 = `ConnectionRefusedError [WinError 1225]`,全部 at setup)——DEC-042 结论在子集面**升级为全量证实**;
- 全量面(1036):尾部行一致 + 子集全量证实,但全量逐行普查文件因后台任务 TEMP 路径差异丢失,**维持抽样级证据,如实标注**。

### 3.4 F-4(解释升级):642==642 非巧合

verbose 普查(`--tb=no -v`,逐 PASSED 行解析):全量 642 passed 的文件分布 = `test_adversarial_m4_round2` 355 / `test_adversarial_identity_verifier` 60 / `test_adversarial_manifest` 52 / `test_adversarial_ir_identity` 47 / `test_adversarial_ir_round2` 33 / `test_identity_verifier` 27 / `test_adversarial_raw_bytes` 23 / `test_ir_identity` 18 / `test_manifest_identity` 17 / `test_raw_bytes_identity` 10 = **精确合计 642,全部 ∈ 13 身份链文件**;`test_identity_gate` / `test_adversarial_m5_integration` / `test_adversarial_m5_round1` 三文件 **0 passed(全 error)**。DEC-042「OBSERVED 巧合」升级为**已解释事实**:全量通过面 = 身份链子集通过面。

---

## §4 攻击三:计数账本(F-3 证伪更正)

- 本轮实测 V3 untracked = **28 件 = 9 docs + 5 core + 14 tests**(逐名枚举,docs 与 DEC-038/041 已裁 9 件名单比对 **SET_EQUAL=True**);
- DEC-042 登记「untracked 终态 = 10 docs(REPORT-PHASE2-M4 窗口内新增)+ 15 tests」:**证伪**——(a)docs 实为 9 件;(b)`PREPROCESSING-V3-CONSUMER-IDENTITY-VERIFICATION-IMPLEMENTATION-REPORT-PHASE2-M4.md` 在 DEC-042 轮全部工具输出与本轮 status 中**均无任何记录**,无证据支持其存在(其来源不作推测);(c)tests 实为 14 件非 15 件。
- **性质**:REPORTED 事实层计账错误(与 DEC-041 F-A 同族),不涉冻结对象字节,不触发 STOP;历史报告 append-only 保留原文,更正由本条承担。

---

## §5 攻击四:G1–G6 与 Boundary(全部独立重跑)

- G1/G2:177 锚逐文件活测 checked=177 / missing=0 / **mismatch=0**;G4 7/7 match=True;G5 双快照字段相符;
- R50 356 逐文件活测:**269 MATCH / 87 DRIFT / 0 missing / 0 unexpected**,SET_EQUAL=True 双向,md drift=0;
- source_file 三方比对:**ok=87 / bad=0 / missing=0**;`n_keys_after` 全 7、`key_appended` 全真;
- G3:`fbcf41ab…b04a5` MATCH;G6:重导 bytes=92,197 sha `9c6b9063…7528` MATCH=True + TEMP_DELETED=True + is-ancestor TRUE + 契约 diff EMPTY + 冻结路径 git status 干净;
- 写面二轮扩展清扫(`os.utime|touch|rmtree|os.remove|NamedTemporaryFile|mkstemp|importlib|__import__|exec(|eval(`)全仓:命中仅 2 处测试侧 `importlib`(读自身模块),**零写/删/touch 命中**;scripts 面零身份链引用(runner 零集成结论复证)。

---

## §6 discrepancy 状态(累计 5 项,全部登记不代改)

D1(IR missing 抛错 vs Design None 正常态,行为级)/ D2(M2 接口)/ D3(M3 字段名)/ D4(M5 路径·函数名·字段·类型;语义 BLOCK 与 Owner 指令一致)——四项维持 DEC-042 登记;**新增 D5**(M5 None 输入抛异常 vs「不抛异常」冻结表述)。

---

## §7 VERIFIED / NOT VERIFIED / 更正清单

**VERIFIED(本轮)**:G1–G6 全 PASS(独立重跑)/ push commit 零身份链代码(三法)/ 本地快照零漂移 / v2 电池 27/27 复现 ×2 / 盲区 13/13 / runner 零集成复证 / 写面零命中复证 / passed=642 三轮稳定且全部来自身份链文件。

**更正(F)**:F-1 撤回「ROOT CAUSE = 环境 DB 缺失」→ OBSERVED 按文件确定性分化 + ROOT CAUSE UNKNOWN;F-2 errors 计数非基线(959→1036,收集面变化);F-3 untracked 计数证伪(10 docs/15 tests → 9/14;REPORT-PHASE2-M4 无证据);F-4 642==642 由「巧合 OBSERVED」升级为已解释。

**NOT VERIFIED**:migrated_db 按文件确定性分化的机制(不推测);全量 1036 errors 的逐行异常普查(证据等级 = 抽样);CONSUMER SEMANTIC CORRECTNESS 对 push commit(无对象,维持)。

**STOP:NOT TRIGGERED**。

---

## §8 纪律记录

- 全程只读(docs-only 登记 + 临时 scratch 除外,scratch 轮末清理,V3 仓零写入);
- 未改 Consumer 实现 / 未改 Producer 数据 / 未提供补丁 / 未自行修复 D1~D5;
- 三项自我错误(F-1/F-3 及 F-2 时效)原样入账并撤回/更正,未合理化;
- 不可复现机制一律写 UNKNOWN,零推测归因;
- 已裁六项未重开;零新架构裁决。

**STATUS:`BOUNDARY: HOLDING / DEC-042 CONCLUSIONS UPHELD WITH 4 CORRECTIONS + 1 NEW DISCREPANCY / GUARDIAN MODE: ACTIVE`**

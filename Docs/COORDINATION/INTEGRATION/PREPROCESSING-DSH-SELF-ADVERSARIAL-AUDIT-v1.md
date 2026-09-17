# PREPROCESSING-DSH-SELF-ADVERSARIAL-AUDIT v1(DEC-045 自审 / DEC-044 Closure 挂起)

> Owner 指令(2026-09-16,原文):「在等候claude的过程中,我们先完成自身全任务的对抗性审查。看是否仍有遗留问题。一切从项目文档和第一性原理出发。」
> 性质:DSH 对自身已完成全部任务的对抗性自审(等待 Claude push 期间执行);全程只读(账本登记与自身文档勘误指针除外);V3 仓零写入(仅 fetch/ls-remote/show/diff 级只读)。
> 每个结论均带本轮真实测试证据;自我错误原样入账;不可复现机制写 UNKNOWN,零推测。

---

## 1. Executive Summary(≤10 行)

- **STATUS: COMPLETE_WAITING_FOR_REVIEW**
- **CURRENT_PHASE: Guardian Mode(Claude 开发中,DEC-044 Consumer Closure Review 挂起待 push;本轮 = DEC-045 自审)**
- **OWNER_ATTENTION_REQUIRED: YES**(2 项 WARNING 需 Owner 知悉:S-4 DEC-014 格式合规缺口 / S-1+S-2 攻击套件复跑面缺口;均非阻塞)
- 完成什么:DSH 自身全任务面(基线工件 / 四账本 / 两份 Guardian 报告 / 测试与攻击套件 / git 卫生 / 长开项账面)对抗性自审。
- 是否达标:基线数据面 **全部复测 PASS 零漂移**;发现自身问题 **10 项(0 BLOCKER / 5 WARNING / 5 NOTE)**,其中 4 项当场修复(账本勘误指针 + 归属修正 + 复跑命令落字),其余登记待 Owner。
- 可否进下一阶段:可以 —— 不阻塞 DEC-044(Closure Review 待 Claude push 后启动;编号 = Closure DEC-044 / 自审 DEC-045,与对话公示顺序一致)。

## 2. Deliverables

| Item | Location | Status |
|---|---|---|
| 本报告 | `Docs/COORDINATION/INTEGRATION/PREPROCESSING-DSH-SELF-ADVERSARIAL-AUDIT-v1.md` | 本轮 |
| 基线复测脚本(确定性只读,跑毕清理) | `.pytest_work/selfaudit_dec044.py` + `selfaudit_srcfile3way.py` | scratch,轮末删除 |
| 账本登记 | state.yaml(DEC-045 自审 + DEC-044 Closure pending + 块 + F-1 指针修正)/ CURRENT.md(归属修正 + 指令链 + DEC-044 块)/ log.md / ODR v1.25 §1sexvicies | 本轮 |
| 报告 A 勘误指针 | `PREPROCESSING-PRODUCER-GUARDIAN-M5-BOUNDARY-REVIEW-v1.md` 文首(append-only 注记,原文零删改) | 本轮 |
| 攻击套件复跑命令落字 | `attacks/conftest.py` docstring | 本轮 |

## 3. Evidence Summary(四级分账)

### OBSERVED(本轮实际执行的观测)

- V3 `git ls-remote origin main` = **`72af28d5854b56fc605e1897fb757703826a6233`**(未前进;首试 SEC_E_NO_CREDENTIALS 如实入账,宽模式重试成功)。
- V3 本地 HEAD = `72af28d`(与远端一致),untracked 集合 = **9 docs + 5 core + 14 tests = 28**(与 DEC-043 F-3 更正后数字一致,零增删)。
- **V3 本地五模块漂移检出**(移动目标再现实,仅 OBSERVED-LOCAL):`identity_gate.py` `f3636b35…`/4391B → **`13812a74…`/5707B**;`ir_identity.py` `9315c22e…`/1730B → **`1e9ab5fd…`/4306B**(新增 batch resolver IR 格式支持);`identity_verifier.py`/`manifest_identity.py`/`raw_bytes_identity.py` 与 DEC-043 锚逐字节相等。**DEC-042/043 的本地快照锚自此对前两模块失效**,下轮以新观测为准。
- 本仓工作树审计开始时干净(HEAD = `294c7fe`);0 tracked pyc;根目录无 stray;`.pytest_work` = 既定 gitignore 探针区。
- `pytest`(canonical,testpaths=tests)独立 2 次:**338 passed / 1 xfailed**(exit 0)。
- `pytest tests attacks` 合并运行:**12 个 tests/ 文件收集期 ImportError**(S-1,详见 §4)。
- `pytest attacks`:23 failed(异步插件未启用,S-2);`--asyncio-mode=auto` 下 23 failed 全部 = `ConnectionRefusedError WinError 1225`(DB 容器未启动,环境性,原样入账)。
- log.md 最近两 commit append-only 亲验:`294c7fe` 24 insertions/0 deletions;`3e5b3b5` 28/0。

### VERIFIED(已验证结论 + 验证方法)

| 结论 | 方法 | 结果 |
|---|---|---|
| G1+G2 冻结面零漂移 | 177 锚定文件全量活测 sha256 vs post-backfill audit map(自写脚本,不信历史结论) | checked=177 / missing=0 / **mismatch=0** |
| R50 356 逐文件活测 | 自写脚本全量比对 + drift 集合与 177 锚 manifest 名单双向 SET_EQUAL | 269 MATCH / 87 DRIFT / 0 missing / **SET_EQUAL=True(双向差集皆空)** |
| source_file 三方 | manifest decl == 活字节 sha == Step2 报告值(87 份) | **ok=87 / bad=0 / missing=0** |
| G4+G5+G3 证据工件 | Get-FileHash × 8 vs 登记锚(step1/pre/step2/post/R50/final-check/verification-report/resolver_ir) | **8/8 MATCH** |
| G6 冻结对象 | `git show f4941ff:<contract>` 字节级重导(cmd 重定向)+ is-ancestor + diff | bytes=**92,197** sha=`9c6b9063…7528` **MATCH**;`f4941ff ⊂ 72af28d` TRUE;`f4941ff..72af28d` 契约 diff **EMPTY**;临时文件即时删除 |
| 四账本交叉一致 | 双子代理独立逐行核对(state.yaml/CURRENT.md/log.md/ODR) | SHA 链/冻结四元组/F-1~F-4/D5/状态行/ODR v1.24/agent 表数字全一致;唯一偏离 = L-10 归属漂移(已修复) |
| 报告过度断言审查 | 双子代理 + 本人对关键争议行亲验 | 无越证据断言;红线(M5 不得判 Verified)未触碰;R-3 经亲验**证伪**(子代理误读) |
| 长开项账面 | state.yaml 各 owner_* 块 still_open 字段互核 | 16 IR batch / D-3 / D-4 / IR 字段改名 / 两层状态载体 / C.1 全部保持 OPEN,无误关闭 |

### INFERRED(推导,给出推导链)

- S-1 机制推导:`attacks/conftest.py` 与 `tests/conftest.py` 均无包结构保护,pytest 把两个目录都插入 sys.path 后,顶层模块名 `conftest` 二义;`tests/` 内 12 个文件 `from conftest import …` 解析到 attacks 版 → ImportError。推导链 = 错误文本亲读(`cannot import name 'make_repo' from 'conftest' (…attacks\conftest.py)`)+ 单文件运行 12 passed 对照。canonical 运行(testpaths=tests)与 CI(`pytest tests/`)不收集 attacks/**,不受影响**。
- S-4 范围推导:EVIDENCE/ 7 件 + Guardian 报告 3 件对 DEC-014 七章节标记全部 0 命中 → 缺口为系统性(自 DEC-014 起所有轮次),非个别轮次退化。

### PROPOSED(未冻结建议,待 Owner)

- P-1:attacks 复跑纪律固化 = `python -m pytest attacks --asyncio-mode=auto`(已落字 conftest docstring;是否入 pytest.ini 待 Owner,改 ini 影响面 = 全仓收集语义,不自行改)。
- P-2:今后轮次的 task-completion 输出对齐 DEC-014 七章节(本轮 §1 已按此结构输出)。
- P-3:更正体系规则补一条 —— 更正必须回指被更正文本所在层(报告/账本行内指针),不得只写在后继报告(根治 R-1/R-2/R-6 同族问题)。

## 4. Findings 清单(全部带证据;0 BLOCKER)

| ID | 严重度 | 发现 | 证据 | 处置 |
|---|---|---|---|---|
| **S-1** | WARNING | `pytest tests attacks` 合并运行收集期 12 个 tests/ 文件 ImportError(双 conftest 顶层模块名冲突);canonical 与 CI 不受影响 | 错误 traceback 亲读 + 单跑对照(§3 INFERRED) | 登记 + conftest docstring 落字;不重构(改名/import-mode 均有 fixture 语义风险,待 Owner) |
| **S-2** | WARNING | 攻击套件(`attacks/test_eb008_impl_attack.py`)需 `--asyncio-mode=auto`(pytest-asyncio 1.4.0 strict;用例为裸 async def,无 marker,仓内无 ini 配置);`EB008-IMPLEMENTATION-REVIEW-1.md` 称「复跑命令见套件文件头」但文件头**无命令** = 复现文档缺口;加正确参数后 23/23 = ConnectionRefused(DB down,环境性) | 裸跑报 async unsupported 亲读;加参数后 traceback = WinError 1225 亲读;两文件 grep 零命令 | 复跑命令本轮落字(P-1);DB 恢复后攻击套件复验列入待办 |
| **S-3** | NOTE | 本轮 G6 首次重导 = 方法错误假 MISMATCH:PowerShell `Out-File -Encoding utf8` 管道污染字节(91,415B / `a788b07e…`);`git show --output=` 未落盘(bytes=0);cmd 重定向重导 = 92,197B / `9c6b9063…` MATCH | 三次实测值均入账 | 自我错误当场纠正;该环境纪律 CURRENT.md L25 原已有载,本轮亲证其必要性 |
| **S-4** | WARNING | DEC-014 七章节 Completion Report 格式自裁决起**从未在任何报告文件落地**(EVIDENCE 7 件 + Guardian 3 件标记全 0 命中);实质内容(Owner attention/next action/反馈项)一直在聊天与报告中,缺的是强制结构 | 逐文件 Select-String 0 命中 | 登记为常设缺口;本轮 §1 起按七章节输出(P-2);历史轮不追补 |
| **S-5** | NOTE | `294c7fe`(DEC-043 自身 commit)在四账本零登记 —— 结构性(账本先写后 commit),非缺陷 | 四账本 grep | 本轮指令链补登(§7) |
| **R-1** | WARNING | 报告 A(M5-BOUNDARY-REVIEW)保留已撤回的 F-1「ROOT CAUSE = 环境 DB 缺失」与已证伪的 F-3 计数,全文对 DEC-043/更正零指针 | 子代理 grep + 本人复核 | 本轮文首补 append-only 勘误指针(原文零删改) |
| **R-6** | WARNING | state.yaml DEC-042 块 `test_evidence` 行残留同一已撤回断言且无 F-1 标注(同文件 `local_snapshot` 行已补 F-3 更正,标准不一) | state.yaml L773 vs L770 | 本轮行内补 F-1 指针 |
| **L-10** | WARNING | CURRENT.md 状态头把「D1~D5」归属给 DEC-042 标签(应 = DEC-042:D1~D4;D5 属 DEC-043);累计总数各账本均正确,同文件 DEC-042 块又写「4 discrepancy」,自相含混 | CURRENT.md:28 vs :49⑧ vs state.yaml:775/783 | 本轮修正状态头归属 |
| **R-3** | —(证伪) | 子代理指控报告 B L66「4/4 全 passed(10 passed)」与「5/5 全 error(10/10)」数字矛盾 —— **误报**:两组数字分属两个不同文件的重复运行(raw_bytes 10 用例 × 4 跑全过;hashing 10 用例 × 5 跑全错),与 B L82 普查(raw_bytes=10)吻合 | 本人亲读 B L55-84 | 驳回;仅存表述歧义(NOTE 级,不改历史文本) |
| **R-4/5/7** | NOTE | R-4:报告 B §3.3 证据降级实为第五项更正未编号;R-5:报告 B 散列锚仅 8 位前缀(全值在 state.yaml/FREEZE-EVIDENCE,单文件可复核性弱);R-7:报告 B L130 STATUS 行丢 `M5 PUSH: ABSENT` 限定语(§0 仍持,未违红线) | 子代理行号引文 + 本人抽查 | 登记;后续轮报告锚值给全值或指明全值所在 |

**遗留问题总答(Owner 之问)**:数据面(冻结对象/基线工件/账本数字)零遗留;**流程面遗留 3 类** = ①攻击套件复跑面(S-1/S-2,已落字缓解,结构修复待 Owner)②DEC-014 格式缺口(S-4,本轮起执行)③更正回指机制缺失(R-1/R-2/R-6 同族,本轮修复存量 + P-3 提规则)。

## 5. Owner Decision Points

- **D-045-1(S-1/S-2 攻击套件治理)**:A = 维持现状(命令落字 + known-issue 登记,零风险);B = pytest.ini 增 `asyncio_mode = auto`(攻击套件裸跑可用,但改全仓收集语义);C = attacks/ 独立 ini(最小影响面)。**推荐 C**。Impact:仅影响攻击套件复跑便利性,不影响 338/1 基线与 CI。
- **D-045-2(S-4 格式)**:是否要求今后所有轮次(含 Guardian)强制七章节结构?**推荐:是**(本轮已示范);历史轮不追补。
- **D-045-3(P-3 更正回指规则)**:是否将「更正必须回指被更正文本所在层」写入 PROTOCOL?**推荐:是**。
- **D-045-4(攻击套件复验)**:DB 容器(aitutor-postgres)恢复后是否令 DSH 复跑 23 用例攻击套件(EB-008 面)?当前无法执行(ConnectionRefused,原样入账)。

## 6. Risks & Unknowns

| ID | 描述 | 严重度 | 为什么重要 |
|---|---|---|---|
| RK-1 | 攻击套件(EB-008 验收产物)当前不可复跑(环境 DB + 异步配置双因) | MEDIUM | DEC-018 顺序⑤ 的验收证据处于"历史 VERIFIED、今日不可复验"状态;DB 恢复前无法排除 V3 侧后续改动破坏该面 |
| RK-2 | V3 本地身份链持续漂移(gate/ir 两模块本轮再变,锚失效) | LOW | 佐证 Owner「以 push commit 为对象」纪律;本地快照锚生命周期 < 一个开发窗口 |
| RK-3 | corpus_sha256 聚合构造仍未复现(F-C 挂账) | LOW | 操作性锚 = 逐文件 map(已实测),不影响判定效力 |

## 7. Cross-Agent Feedback(强制项)

**Feedback to Claude(经 Owner 转达)**:
- TARGET:D1~D5 五项 discrepancy 的收口口径。Issue:D1(M3 IR missing 抛 IRReadError vs Design §4.4/F5 None 正常态)/ D5(M5 None 输入抛异常 vs「不抛异常」冻结表述)为行为级,D2/D3/D4 为接口面偏离。Evidence:`PREPROCESSING-PRODUCER-GUARDIAN-M5-BOUNDARY-REVIEW-v1.md` §10 + `…-ADVERSARIAL-v1.md` §6。Expected response:push 后在 Consumer commit 内给出逐项处置(采纳修正 or 以 Owner 裁决维持并更新 Design 文档),两文档口径必须一致。
- TARGET:push 时点。Issue:DEC-044(Closure Review)在等 exact commit SHA;本地 untracked 不作为最终证据。Expected response:实现收口后 commit + push 并回执 SHA。
- TARGET:攻击套件复跑环境。Issue:V3 测试库(aitutor-postgres,5432)未启动,DSH 侧 EB-008 攻击套件与 V3 身份链 DB fixture 测试均不可复验(前者 ConnectionRefused 亲证;后者机制 UNKNOWN 不归因)。Expected response:联调窗口开启时恢复容器并在 handoff 中说明。

## 8. Recommended Next Action

- **Owner**:裁决 D-045-1~4;知悉 5 项 WARNING(无阻塞)。
- **Claude**:继续 M5 Gate Integration;push 后回执 SHA。
- **DSH**:保持 Guardian 待命;Claude push 后启动 DEC-044 Consumer Boundary Closure Review(以 exact commit 为对象;集成缺口 = 强制检查面);DB 恢复后复跑攻击套件(若 Owner 令)。

---

## 纪律声明

全程只读(V3 仓零写入;本仓写入面 = 报告/账本/conftest docstring/scratch 且 scratch 轮末清理);未改 Consumer 实现;未改 Producer 数据/manifest/IR/冻结工件(全部字节级复测零漂移);未提供补丁;不可复现机制写 UNKNOWN;失败与方法错误原样入账(S-3);子代理误报经亲验驳回(R-3)。**STOP:NOT APPLICABLE(零冻结对象字节变化,本轮为 DSH 自身面审计)。**

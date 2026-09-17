# CURRENT — 跨 Agent 协调快照(人 + Agent 快速阅读)

> 机器可读状态见 `state.yaml`;协议见 `PROTOCOL.md`。本文件是镜像快照,**权威以 state.yaml 为准**。
> 更新:2026-09-16(**DEC-045 DSH 自身全任务对抗性自审**:基线全部独立复测 **PASS 零漂移**(177/177 + R50 269/87 SET_EQUAL/0 + 三方 87/87 + 工件 8/8 + G6 MATCH + 测试 338/1 ×2);发现 **0 BLOCKER / 5 WARNING / 5 NOTE**(S-1 双 conftest 冲突 / S-2 攻击套件复跑面缺口(命令已落字)/ S-3 G6 假 MISMATCH 方法错误当场纠正 / S-4 DEC-014 七章节格式系统性缺口 / R-1·R-2·R-6 更正指针缺失(已修复)/ L-10 状态头归属漂移(已修正)/ R-3 子代理误报驳回);存量修复 5 处;V3 本地五模块漂移检出(gate `13812a74…`/5707B、ir `1e9ab5fd…`/4306B,旧锚失效))· **DEC-044 Closure Review 已登记挂起(push 后启动)** · 前轮 = DEC-043 对抗性审查 / DEC-042 M5 Boundary Review / DEC-041 / DEC-040 · canonical ledger = kurt-wong/Aitutors-preprocessing(main)

## 🧭 新会话快速恢复(新会话先读本节,30 秒回到工作状态)

**一句话状态**:Contract v0.2 = **FROZEN**(DEC-032);Frozen Baseline = **PRODUCER BASELINE FINALIZED + ARCHIVED**(DEC-033/034);**GUARDIAN MODE ACTIVE — BOUNDARY HOLDING**;**DEC-045 DSH 自审完成(2026-09-16):基线复测全 PASS 零漂移,自身发现 10 项(0 BLOCKER)存量修复 5 处**;**DEC-044 Closure Review 登记挂起(待 Claude push exact SHA 后启动,未 push 不判 Consumer Boundary Verified)**;V3 远端仍零实现提交(全部身份链 = 本地 untracked,本地 gate/ir 两模块持续漂移);累计 discrepancy D1~D5 待 V3 收口;Trigger ② 继续 ARMED;DSH 令前保持零新数据动作,**不参与 Consumer 代码实现(含 M4/M5)**,等 Owner 下一步指令。

- **指令链末端**:… → DEC-041(`9cffd0f`)→ DEC-042(`3e5b3b5`)→ DEC-043(`294c7fe`)→ **DEC-044 Closure(登记挂起)/ DEC-045 自审(本轮)**;ODR = **v1.25**(§1sexvicies DEC-044 + §1septenvicies DEC-045 原文照录);工作树干净(提交后);
- **冻结对象(唯一有效四元组)**:`kurt-wong/AITutors-v3` @ `f4941ff87c0130ee0b79ff6b807c4ec2826b8ff1` / `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` / sha256 **`9c6b9063e81fb2a66d85794b280c9d931f1b0074b39abf472033218149b17528`**(92,197 bytes)。`c6e771c` / `c8d89586…1032` = 历史登记,**勿引用**。V3 远端 main 最新观测值 = **`72af28d`**(DEC-045 亲验;`4daecf0b` 为 DEC-032 时点历史值;一切以 fetch/ls-remote 实测为准);
- **关键数字**:manifest 166 / 接口面 87(87/87 携 `source_content_sha256`,unique 87 · dups 0)/ IR 71 ADMITTED(1,664 单元,71/71 对账零漂移)/ 16 Semantic Pending / v1 legacy 79(隔离,C-IN-1 下必拒)/ R50 基线 356(**DRIFT = 恰 87 为预期**,承接者 = pre/post audit 双快照 `b11874c4…` / `2cb980c7…`);
- **Frozen Baseline 归档终态(DEC-034)**:四项 immutable 终检全过——source bytes 零漂移(87/87 vs Step1+R50)/ manifest 差异恰 = 追加一键 / IR 71·71 零漂移 / 证据六工件登记 sha 6/6 相符 + 复跑字节级复现(`a707738e…5c33`);归档报告 = `INTEGRATION/PREPROCESSING-PRODUCER-BASELINE-ARCHIVE-FINAL-REPORT-v1.md`;**基线以工件表字节为准,后续变化须 Owner 令 + 新配对快照,不得就地改写**;**CONSUMER IDENTITY: NOT IMPLEMENTED 不变**;
- **Guardian Mode(DEC-035)**:Consumer Implementation Boundary Audit = **BOUNDARY HOLDING 零违例**(Consumer 实现合法写面 = 仅 V3 仓代码,对基线五类禁改对象全部只读;177 锚定文件全量比对 bad=0);immutable monitoring checklist 在位——**DEC-038 起改称 G1~G6(G = Guardian Check,M = Consumer Module,与 Consumer M 系列编号隔离)**:source bytes / manifest / IR `fbcf41ab…b04a5` / evidence 六工件 / corpus 双值 / 冻结对象四元组,偏差协议 = 任一 mismatch → STOP 只报告不自修;详件 = `INTEGRATION/PREPROCESSING-PRODUCER-FROZEN-BASELINE-CONSUMER-BOUNDARY-CHECK-v1.md`;DSH 不参与 Consumer 实现代码(复核 ≠ 实现);
- **Guardian Phase 1(DEC-036)**:Phase 1 开工前 baseline snapshot = **M1~M6 全 PASS 零 mismatch**(177/177 checked·missing 0·mismatch 0;证据 6 工件 + R50 锚 7/7;M6 冻结四元组字节重导 `9c6b9063…7528` MATCH + is-ancestor TRUE + 契约 diff empty);当轮 Observed:本仓 `origin/main` = `27727c4`,V3 `origin/main` = `72af28d`(未前进,均为 docs 轮,**尚无 Phase 1 实现提交**);详件 = `INTEGRATION/PREPROCESSING-PRODUCER-GUARDIAN-PHASE1-CHECK-v1.md`;
- **DSH 自审(DEC-045,最新)**:Owner 令「等待 Claude 期间完成自身全任务对抗性审查」——**基线全部本轮独立复测 PASS 零漂移**(177/177 mismatch=0 / R50 356 = 269/87 SET_EQUAL 双向/0 missing / source_file 三方 87/87 / 证据工件 8/8 Get-FileHash MATCH / G6 cmd 重导 92,197B `9c6b9063…7528` MATCH + 亲缘 TRUE + diff EMPTY / canonical pytest 338·1 ×2 / log.md append-only 亲验 / git 卫生 0 tracked pyc);**发现 0 BLOCKER / 5 WARNING / 5 NOTE**(要点:S-1 `pytest tests attacks` 合并收集被双 conftest 顶层名冲突打灭(canonical+CI 不受影响);S-2 攻击套件需 `--asyncio-mode=auto` 且历史报告引用的复跑命令缺失(已落字 conftest);S-3 G6 首次重导 = PowerShell 管道编码污染**假 MISMATCH**(cmd 重导纠正,自我错误入账);S-4 DEC-014 七章节格式自裁决起从未落地(系统性);R-1/R-2/R-6 已撤回断言缺更正指针(已修复);L-10 状态头 D1~D5 归属漂移(已修正);R-3 子代理误报经亲验驳回);**V3 本地五模块漂移检出**:`identity_gate.py` → `13812a74…`/5707B、`ir_identity.py` → `1e9ab5fd…`/4306B(旧锚失效),其余三模块不变;详件 = `INTEGRATION/PREPROCESSING-DSH-SELF-ADVERSARIAL-AUDIT-v1.md`;
- **Closure Review(DEC-044,挂起)**:Owner 十项指令已登记(state.yaml decisions DEC-044):以 Claude **实际 push commit** 为对象(exact SHA + ls-remote 亲验;**未 push 不得宣布 Consumer Boundary Verified**)+ G1-G6 + M3/M5-D5 专项 + 真实 Runner 链 + downstream bypass A~F(任一 semantic consumer 在 BLOCK 后执行 = Consumer Boundary failure)+ Authority 分离 + Producer mutation 双证据 + 分层报告(不因 G1-G6 全 PASS 判 M5 通过);**触发 = Claude push 后**;
- **M5 Boundary Review(DEC-042)**:审查对象 = V3 `origin/main` **`72af28d…6233`**(ls-remote 亲验,远端零新提交;`ls-tree`+`git grep` 证实该 commit **零身份链代码**)→ **M5 未 push,不宣布 M5 通过(NOT VERIFIED,无对象)**;本地 untracked 快照(**OBSERVED-LOCAL,移动目标**:`identity_gate.py` 审查期间 3602→4391 B(+值域白名单 fail-closed),`test_adversarial_m5_round1/round2.py` 窗口内新增;动态结论锚定 `f3636b35…` 三次快照稳定〔DEC-045:该锚现已失效,gate → `13812a74…`/5707B〕):自建动态电池 **27/27 PASS**——Truth Table 五格全符合(含最高优先级 **VERIFIED+PENDING→BLOCK** 真实文件链实测)/ stale IR 唯一出口 BLOCK / IR 劫持 **14/14** 免疫 / Manifest 6 变体 fail-closed(无一误读为 PENDING/VERIFIED)/ IR 5 变体 / 越域伪造值 6/6 BLOCK;**4 项 discrepancy 登记不代改**(D1 行为级 = M3 IR missing 抛 `IRReadError` vs Design v1.1 §4.4/F5 None 正常态 + Contract 16 份 Semantic Pending 语义;D2 M2 接口偏离;D3 M3 字段名;D4 M5 路径/函数名/字段/类型 + 语义 BLOCK vs Design 放行+标记——语义与 Owner 指令一致,接口面待收口);**真实调用链零集成**(runner.py/b2/b3/p32 全部不调用 M1–M5,runner_b2 `input_identity` 无 sha →「M5 BLOCK 阻断下游 Gate/Compiler/Admission」**NOT VERIFIED(INTEGRATION PENDING)**,stale IR 今天在真实入口无强制阻断面——非违例,下轮必查);pytest 全量 **642 passed / 959 errors**(~~全部 = 环境无 PostgreSQL 的 ConnectionRefused at setup~~〔F-1 已撤回该根因归因:实为按文件确定性分化,机制 UNKNOWN〕,原样入账;身份链子集 642 passed / 122 errors 同因,Claude 新 M5 测试不可复验);Boundary 静态 = core 五模块零写面、Producer 路径引用全只读;详件 = `INTEGRATION/PREPROCESSING-PRODUCER-GUARDIAN-M5-BOUNDARY-REVIEW-v1.md`(文首已补 DEC-045 勘误指针);
- **对抗性审查(DEC-041)**:对 DEC-040 全部结论的第一性原理审查 —— **冻结对象结论全部维持且加强**:177/177 复测 mismatch=0;**R50 356 逐文件活测首次执行** = 269 MATCH / 87 预期 DRIFT(与 177 锚 manifest 名单 **SET_EQUAL=True**,键级抽验证实单键 `source_content_sha256` 追加 = 已裁 Step-2 回填)/ 0 unexpected;**原面 source_file 层活测 87/87**(decl == 活 sha == Step2 报告值三方比对);扩展写路径清扫 + 三身份模块全文亲读 = 零写路径;G4 7/7 / G6 残留 False + 亲缘 TRUE + diff EMPTY / 测试独立第 3 次复跑 338·1;**发现与更正**:F-A = DEC-040"文档计数差 1"**证伪**(SET_EQUAL=True 零增删;根因 = DEC-038 自称 10 实列 9 的历史计数错误;更正已登记)/ F-B = G5 方法学弱点已升级 / F-C = `corpus_sha256` 构造 7 候选未复现如实挂账;失败测试原样入账(0/87 错路径比对 = 审查方构造错误,以 source_file 三方比对纠正);详件 = `INTEGRATION/PREPROCESSING-PRODUCER-GUARDIAN-M4-ADVERSARIAL-REVIEW-v1.md`;
- **Guardian Phase 2-M4(DEC-040,轮次 4)**:M4 实现期间监护 = **G1~G6 全 PASS 零 mismatch 零违例**;**Authority Boundary 特别关注 = HOLDS**(G3 Producer IR artifact hash unchanged `fbcf41ab…b04a5`;Manifest / source bytes 字节零变化;V3 `backend/` 全树写路径排查命中项全落合法面(测试 tmp_path / 既有 scripts / 既有 import 上传目录),`app/core/` 身份链三模块零写路径;未出现修复 IR / 回写 Manifest / 重生成 Producer artifact 行为;四项 immutable 实测保持);**duplicate/path 检查无违规倾向**(Consumer 设计 F8a = same SHA + different locator 合法,独立进入验证链,不要求 Producer 重新生成;证据等级 = 设计层 REPORTED,M4 行为面未落树);本轮 Observed:本仓 `HEAD` = `3916852`,V3 `origin/main` = `72af28d`(未前进,远端仍无实现提交);V3 本地较 DEC-039 **新增 3 件** = `test_ir_identity.py` / `test_adversarial_ir_identity.py` / `test_adversarial_ir_round2.py`(全测试面,untracked = REPORTED);**M4 模块未落树**(设计层 = 零 IO 纯函数,READINESS = IMPLEMENTATION READY);**Consumer 新增代码仅位于合法写面,STOP 未触发**;~~untracked 文档计数差 1~~(该表述已被 DEC-041 证伪更正,实际零增删);详件 = `INTEGRATION/PREPROCESSING-PRODUCER-GUARDIAN-PHASE2-CHECK-v1.md` 轮次 4 节;
- **Guardian Phase 2-M3(DEC-039,轮次 3)**:M3 实现期间监护 = **G1~G6 全 PASS 零 mismatch 零违例**;**IR 污染特别关注项 = 无污染**(G3 Producer IR artifact hash unchanged `fbcf41ab…b04a5`,字节零变化;读取 ≠ 修改;旁证 = V3 本地 `ir_identity.py` 亲读,仅 `read_text` 提取,无写路径);本轮 Observed:本仓 `HEAD` = `40c06c9`,V3 `origin/main` = `72af28d`(fetch 本轮直接成功;未前进,远端仍无实现提交);V3 本地工作树较 DEC-038 **新增 2 件** = `backend/app/core/ir_identity.py`(M3 IR Identity Reader v1.0.0)+ `backend/tests/test_adversarial_manifest.py`(untracked = REPORTED);**Consumer 提交未影响冻结对象,STOP 未触发**;详件 = `INTEGRATION/PREPROCESSING-PRODUCER-GUARDIAN-PHASE2-CHECK-v1.md` 轮次 3 节;
- **Guardian Phase 2 轮次 2(DEC-038)**:Consumer Phase 2 开发期间 checkpoint = **G1~G6 全 PASS 零 mismatch 零违例**(G1+G2 177/177 checked·missing 0·mismatch 0;G3 Producer IR artifact hash unchanged `fbcf41ab…b04a5`;G4 证据 7/7;G5 corpus 双值 `4ad3458b…19160` / `24af8f56…0a10`;G6 冻结四元组 bytes=92,197 sha `9c6b9063…7528` MATCH + 亲缘 TRUE + 契约 diff empty;测试 338 passed / 1 xfailed);当轮 Observed:本仓 `HEAD` = `056b6d6`,V3 `origin/main` = `72af28d`(**未前进,远端无实现提交**);**V3 本地工作树出现 untracked Consumer 实现文件**(raw_bytes_identity.py / manifest_identity.py + 三测试 + 10 份文档;REPORTED = Phase 1 IMPLEMENTED / Phase 2 M1 COMPLETE 待 Phase 3 授权)——**合法写面非违例,判违例标准 = 冻结对象是否变化**;详件 = `INTEGRATION/PREPROCESSING-PRODUCER-GUARDIAN-PHASE2-CHECK-v1.md`;
- **Guardian Phase 2 轮次 1(DEC-037)**:Consumer Phase 2 开工前 baseline check = **M1~M6 全 PASS 零 mismatch**(177/177 + 证据 7/7 + M6 冻结四元组 bytes=92,197 sha `9c6b9063…7528` MATCH + 亲缘 TRUE + 契约 diff empty;测试 338 passed / 1 xfailed);当轮 Observed:本仓 `HEAD` = `bebd9e1`,V3 `origin/main` = `72af28d`(**未前进,远端提交链全 docs,尚无 Phase 1/Phase 2 实现提交**);REPORTED(Owner 宣告 Phase 2 开工)与 OBSERVED 分账不混写;**Trigger ② 继续 ARMED**(远端无实现提交可复核);详件 = 同报告附录 A;
- **边界纪律(新会话必守)**:①Freeze 不含三项实现——bytes verification / identity gate / IR verification;五项 V3 消费能力全部 **NOT IMPLEMENTED**,契约 REQUIREMENT ≠ 现状(Decision ≠ Implementation);②已裁六项(identity key / path / `source_version_id` / Semantic Pending / 87·71·16 / bytes requirement)**不重开**;③DSH 令前零新数据动作——Step 4 数据治理 / Step 5 图片恢复 / IR 重生成 / schema 变更 / daemon 仍禁;④case id 不重编号;REPORTED ≠ OBSERVED;转述层会漂移,引用必须回到证据文件;
- **下一阶段**:V3 Consumer Identity Verification Implementation(bytes → SHA256 → Manifest 验证 → IR 验证 → fail-closed → Gate → Admission)——实现排期属 V3 侧;若 Owner 令 DSH 复核实现,核验基准 = 契约 §2.3/§5.6.2 验证链 + 五项 NOT IMPLEMENTED 边界不得因 FROZEN 松动;
- **长开项(不阻塞 FROZEN,须令才动)**:16 份 IR 再生成批次 / D-3 存量 1 例 `andalone_question` / D-4 两份三重成员 / IR 字段名对齐(`source_sha256` → `source_content_sha256`)/ 两层状态载体 + reviewable record / C.1 载体正文引用形态追认;延期五项(legacy 79 披露 / 17 拒收 / OCR-PDF 扩展 / DEC 编号统一(R5-03)/ bytes 传输方式)不处理;
- **环境纪律**:`PYTHONIOENCODING=utf-8`;PowerShell `>` 重定向写 UTF-16 且管道 `Out-File -Encoding utf8` 会 BOM+解码污染字节(**字节级导出唯一可靠法 = `cmd /c "git show … > file"` + `Get-FileHash`**;`git show --output=` 在 pwsh 内不落盘,DEC-045 S-3 亲证假 MISMATCH);push / gh 需 `sandbox_permissions: danger-full-access` + justification;push 后必须 `git ls-remote origin main` 亲验 + `gh run list` 对账;测试基线 = **338 passed / 1 xfailed**(canonical `python -m pytest`,testpaths=tests;DEC-045 独立 ×2 复验);V3 身份链面 = **642 passed / 1 skipped / 1 xfailed + DB-fixture errors**(errors 计数非基线:959→1036 随收集面变化〔DEC-043 F-2〕;`migrated_db` 按文件确定性分化机制 UNKNOWN〔F-1〕;passed=642 全部来自身份链文件〔F-4〕);DSH 自建动态电池 27/27 + 盲区 13/13;攻击套件复跑 = `python -m pytest attacks --asyncio-mode=auto`(S-2 落字;依赖 aitutor-postgres,勿与 tests/ 合并收集 = S-1);
- **阅读顺序**(PROTOCOL §5):state.yaml(权威)→ 本文件 → ODR v1.25 → log.md 尾部 → 最新 HANDOFF;裁决原文全集 = `INTEGRATION/PREPROCESSING-OWNER-DECISION-RECORD-v1.md`。

## ⏭ 当前状态:GUARDIAN MODE ACTIVE — DSH SELF-AUDIT COMPLETE(DEC-045:BASELINE ALL PASS ZERO DRIFT + 10 FINDINGS 0 BLOCKER + 5 FIXES APPLIED)/ CLOSURE REVIEW PENDING PUSH(DEC-044:对象 = Claude 实际 push commit,未 push 不判 Consumer Boundary Verified)/ DEC-043 ADVERSARIAL REVIEW COMPLETE(DEC-042 CONCLUSIONS UPHELD + 4 CORRECTIONS + 1 NEW DISCREPANCY D5)/ DEC-042 M5 BOUNDARY REVIEW(M5 PUSH ABSENT / LOCAL SNAPSHOT SEMANTICS PASS;该轮 discrepancy = D1~D4,D5 由 DEC-043 新增)/ BOUNDARY HOLDING / POST-PHASE1 RECHECK ARMED(2026-09-16;前状态链 = DEC-043 / DEC-042 / DEC-041 / DEC-040 M4 PASSED / DEC-032 CONTRACT FROZEN)→ 下一阶段 = Claude push 后启动 DEC-044 Closure Review(集成缺口 + M3/M5 D5 专项 = 强制检查面;D1~D5 待 V3 收口)

**裁决基准**:`INTEGRATION/PREPROCESSING-OWNER-DECISION-RECORD-v1.md`(**v1.25**:… + §1quadvicies DEC-042 + §1quinvicies DEC-043 + **§1sexvicies DEC-044 Closure + §1septenvicies DEC-045 自审**)。

**DEC-045 = DSH 自身全任务对抗性自审(等待 Claude push 期间;一切从项目文档与第一性原理出发)**:
- **① 基线复测(全部本轮独立执行,不信历史结论)**:177/177 mismatch=0;R50 356 = 269 MATCH / 87 DRIFT / 0 missing,drift 与 177 锚 manifest 名单**双向 SET_EQUAL=True**;source_file 三方 87/87;证据工件 **8/8** Get-FileHash MATCH(step1/pre/step2/post/R50/final-check/verification-report/resolver_ir);G6 = cmd 字节重导 92,197B `9c6b9063…7528` MATCH + `f4941ff ⊂ 72af28d` TRUE + 契约 diff EMPTY + 残留删除;canonical pytest **338/1 ×2**;log.md append-only 亲验(24/0、28/0);git 卫生 0 tracked pyc / 开工工作树干净;
- **② 发现(0 BLOCKER / 5 WARNING / 5 NOTE)**:S-1 = 双 conftest 顶层模块名冲突(`pytest tests attacks` 合并收集 12 文件 ImportError;canonical+CI 不受影响);S-2 = 攻击套件需 `--asyncio-mode=auto` 且 REVIEW-1 所称「复跑命令见套件文件头」缺失(复现文档缺口;命令本轮落字 conftest);S-3 = 本轮 G6 首次重导 = PowerShell 管道编码污染**假 MISMATCH**(91,415B/`a788b07e…`),cmd 重导纠正 —— 自我错误原样入账;S-4 = **DEC-014 七章节格式自裁决起从未在报告文件落地**(EVIDENCE 7 件 + Guardian 3 件 0 命中,系统性);R-1/R-2/R-6 = 已撤回 F-1 / 已证伪 F-3 在报告 A 与 state.yaml 无更正指针(本轮全部补指针,append-only);L-10 = CURRENT.md 状态头曾把 D1~D5 归属 DEC-042 标签(本轮修正 = DEC-042:D1~D4 / DEC-043:+D5);R-3 = 子代理指控报告 B 数字矛盾**经亲验驳回**(两组数字分属两文件重复运行);R-4/5/7 = NOTE(更正未编号/8 位前缀复核性弱/STATUS 行丢限定语);
- **③ 存量修复 5 处**:报告 A 文首勘误指针 / state.yaml L773 F-1 行内指针 / CURRENT.md 状态头归属 / attacks conftest 复跑命令落字 / 指令链补登 `294c7fe`;历史文本零删改;
- **④ V3 本地漂移(仅 OBSERVED-LOCAL)**:origin/main = `72af28d` 未前进;untracked 28 件零增删;`identity_gate.py` → `13812a74…`/5707B、`ir_identity.py` → `1e9ab5fd…`/4306B(新增 batch IR 格式支持)—— **DEC-042/043 本地快照锚对这两模块失效**,下轮以新观测为准;
- **⑤ Owner Decision Points**:D-045-1 攻击套件治理(推荐 attacks 独立 ini)/ D-045-2 今后轮次强制七章节(推荐 是)/ D-045-3 更正回指规则入 PROTOCOL(推荐 是)/ D-045-4 DB 恢复后攻击套件复验是否下令;详件 = `INTEGRATION/PREPROCESSING-DSH-SELF-ADVERSARIAL-AUDIT-v1.md`(本轮首个七章节示范)。

**DEC-043 = 对 DEC-042 轮的对抗性审查(每结论真实测试;自我错误原样入账)**:
- **① 维持且加强**:G1~G6 独立重跑全 PASS(177/177 mismatch=0;R50 356 = 269/87 SET_EQUAL/0 unexpected;source_file 三方 87/87;G6 MATCH + 亲缘 TRUE + diff EMPTY + 残留 False);push commit 零身份链代码**换方法三重证实**(`ls-tree -r` 434 文件 / 全仓 `git grep` / preprocessing_consumer 枚举);v2 电池 **27/27 复现 ×2**;盲区补测 **13/13**(manifest 顶层非对象/目录/BOM/前后空白全 fail-closed;IR 嵌套键不读;链确定性 5x);本地快照五模块散列与 DEC-042 锚逐项相等;
- **② F-1(撤回)**:DEC-042「ROOT CAUSE = 环境 DB 缺失」= 超证据归因 —— port 5432 不监听(事实),但同进程内 `migrated_db` **按文件确定性分化**(`test_hashing` 5/5 全错 / `test_raw_bytes` 4/4 全过,顺序无关,--setup-show 亲证 fixture 归属)→ 更正为 **OBSERVED 分化 + ROOT CAUSE UNKNOWN**;
- **③ F-2(时效)**:errors 959→1036(总用例 1603→1680,增量相容 `m5_round2` 被收集);errors 计数**非基线**,passed=642 三轮稳定;子集 122/122 errors 全量普查唯一异常 = ConnectionRefusedError at setup(证实);全量面 = 抽样级证据(如实标注);
- **④ F-3(证伪)**:DEC-042 untracked 记「10 docs(REPORT-PHASE2-M4 新增)+ 15 tests」错误 → 实测 **9 docs + 5 core + 14 tests = 28**(docs 与已裁 9 件名单 SET_EQUAL=True);REPORT-PHASE2-M4 全部工具输出零记录,不推测来源;
- **⑤ F-4(升级)**:「642==642 巧合」→ 已解释:verbose 普查全量 passed 642 **精确来自 10 个身份链文件合计 642**;`test_identity_gate` / `m5_integration` / `m5_round1` 三文件 0 passed 全 error;
- **⑥ D5(新 discrepancy)**:M5 对 None/无 identity 对象输入抛 `AttributeError`,与 M5 docstring 及 Design v1.1 §4.6「不抛异常」矛盾(M4 正常输出不可达;失败方向 = raise 非 bypass);登记不代改;**累计 D1~D5**;
- **⑦ STOP:NOT TRIGGERED**;详件 = `INTEGRATION/PREPROCESSING-PRODUCER-GUARDIAN-M5-REVIEW-ADVERSARIAL-v1.md`(docs-only)。

**DEC-042 = Consumer M5 Boundary Guardian Review(以 push commit 为对象;PRODUCER BOUNDARY 与 CONSUMER SEMANTIC CORRECTNESS 两结论严格分离)**:
- **① 审查对象**:V3 `origin/main` = **`72af28d5854b56fc605e1897fb757703826a6233`**(远端零新提交);`ls-tree 72af28d backend/app/core/` = 仅 4 个既有文件,`git grep` 身份链符号 = 空 —— **push commit 内不存在 M1–M5 任何代码;不宣布 M5 通过**;
- **② Producer 基线**:G1~G6 **全 PASS**(177/177 mismatch=0;R50 356 = 269 MATCH / 87 SET_EQUAL DRIFT / 0 unexpected;source_file 三方 87/87;G4 7/7;G6 92,197 B sha `9c6b9063…7528` MATCH + 亲缘 TRUE + 契约 diff EMPTY);四项 immutable 全成立;**STOP NOT TRIGGERED**;
- **③ M5 语义(本地快照 `f3636b35…`,OBSERVED-LOCAL)**:Truth Table 五格 + stale IR + Manifest 6 变体 + IR 5 变体 + IR 劫持 + 越域伪造值 = **27/27 PASS**;PASS 可达条件唯一 = VERIFIED+AVAILABLE;
- **④ discrepancy(登记不代改)**:D1 = M3 IR missing 抛 `IRReadError`(vs Design v1.1 §4.4/F5 None = PENDING 正常态,Contract 16 份 Semantic Pending 同向)——行为级;D2 = M2 接口(`bytes_source`+裸异常 vs 冻结 `raw_bytes`+`SourceBytes*Error`);D3 = M3 字段名;D4 = M5 路径/函数名/`gate` 字段/tuple + 语义 BLOCK vs Design §4.6 放行+标记(语义与 Owner 指令一致,docstring 已注 Owner 优先;接口面待 Owner/V3 收口);
- **⑤ 集成缺口(下轮必查)**:runner.py / **runner_b2.py** / runner_b3.py / p32 全部**零 M1–M5 调用**(runner_b2 全链 manifest→IRBuilder→Compiler→Gate→AdmissionCandidate 不含身份轴,`input_identity` 无 sha)→「M5 BLOCK 阻断下游」**NOT VERIFIED**;stale IR 今天在真实入口无强制阻断面(非冻结对象违例);
- **⑥ 测试**:全量 pytest = 642 passed / 1 skipped / 1 xfailed / **959 errors(~~全部 ConnectionRefusedError WinError 1225 at fixture setup = Guardian 环境无 PostgreSQL~~〔F-1 已撤回该根因:实测按文件确定性分化,机制 UNKNOWN〕,环境性限制原样入账)**;身份链 13 文件子集 = 642 passed / 122 errors(同因;Claude 新 M5 测试不可复验);自建电池 27/27(零 DB 依赖);
- **⑦ 移动目标入账**:审查窗口内 `identity_gate.py` 3602→4391 B、`test_adversarial_m5_round1.py`/`round2.py` 相继出现 —— 本地态不可作终局证据,此即 Owner「必须以 push commit 为对象」的实证;
- **⑧ 两结论**:**PRODUCER BOUNDARY = HOLDS(VERIFIED)**;**CONSUMER SEMANTIC CORRECTNESS = NOT VERIFIED(对 push commit 无对象;本地快照 = 语义 PASS + 4 discrepancy + 集成缺口)**;详件 = `INTEGRATION/PREPROCESSING-PRODUCER-GUARDIAN-M5-BOUNDARY-REVIEW-v1.md`(docs-only)。

**DEC-041 = 对 DEC-040 轮的第一性原理对抗性审查(每结论必有真实测试;不降标准/不自我合理化/不强行解释/不推测)**:
- **① 总判定**:DEC-040 冻结对象结论(G1~G6 / 四项 immutable / Authority Boundary HOLDS / 零违例)**全部经对抗性复测维持且加强**;**STOP 未触发**(审查全程零冻结对象字节变化);
- **② 覆盖面加强(新实测)**:**R50 356 逐文件活测首次执行** = 269 MATCH / **87 预期 DRIFT**(与 177 锚 manifest 名单 **SET_EQUAL=True**;键级抽验 = 单键 `source_content_sha256` 追加,Step2 报告 `n_keys 6→7` 实证 = 已裁回填)/ **0 unexpected**;**原面 source_file 层活测 = 87/87**(decl == 活 sha == Step2 报告值,三方比对;锚链 = 177 锚 manifest → decl → source_file 目标);扩展写路径清扫 + Producer 路径引用检索 + 三身份模块全文亲读 = **全部纯读零写路径**;
- **③ F-A(更正,已登记)**:DEC-040"untracked 文档计数差 1"**证伪** —— 本轮 9 件与 DEC-038 名单 9 件 SET_EQUAL=True 零增删;根因 = DEC-038 自称 10 实列 9 的历史计数错误;更正 = 文档面自 DEC-038 起即 9 件零增删(REPORTED 事实层错误,不涉冻结对象字节);
- **④ F-B(方法学,已修复)**:G5 原执行仅读快照 `corpus_sha256` 字段(强度弱于名称),已升级为逐文件活测,常态化待 Owner 令;
- **⑤ F-C(未复现,挂账)**:`corpus_sha256` 聚合构造 7 种候选(含原始字节全拼接)均未复现,不推测;操作性锚 = 逐文件 map(已实测);
- **⑥ 证据纪律**:失败测试原样入账(0/87 错路径比对 = 审查方构造错误,以 source_file 三方比对 87/87 纠正);G4 7/7 复跑;G6 残留 False + 亲缘 TRUE + 契约 diff EMPTY;测试独立第 3 次复跑 **338 passed / 1 xfailed**;详件 = `INTEGRATION/PREPROCESSING-PRODUCER-GUARDIAN-M4-ADVERSARIAL-REVIEW-v1.md`(docs-only)。

**DEC-040 = Phase 2-M4 Guardian Check(只读监护 + Authority Boundary 特别关注,Observed/Historical 分账)**:
- **① G1~G6 全 PASS 零 mismatch(OBSERVED 本轮)**:G1+G2 177 锚定文件全量比对 checked=177 / missing=0 / mismatch=0(快照自身 sha `2cb980c7…4096` 相符;md=87 / manifest=87);G3 **Producer IR artifact hash unchanged**(`fbcf41ab…b04a5`);G4 证据六工件 + R50 辅助锚 7/7 match=True;G5 pre `4ad3458b…19160` / post `24af8f56…0a10` 相符;G6 冻结四元组字节重导 bytes=92,197 sha `9c6b9063…7528` MATCH + is-ancestor TRUE + 契约 diff empty(临时重导即时删除);测试 **338 passed / 1 xfailed**;
- **② Authority Boundary 特别关注(本轮重点)= HOLDS**:Producer IR / Manifest / source bytes 仅被读取(字节零变化);**未出现**修复 IR / 回写 Manifest / 重生成 Producer artifact 行为 —— V3 `backend/` 全树写路径排查,命中项全落合法面;`app/core/` 身份链三模块零写路径;M4 模块未落树(设计层 = 零 IO 纯函数);**四项 immutable(Producer IR / Manifest / source bytes / Freeze Artifact)全部实测保持**;
- **③ duplicate/path 特别检查 = 无违规倾向**:Consumer 设计 F8a 明确 same content + different locator = 允许(各文件独立进入验证链),不要求 Producer 重新生成/修改;与已裁"path 非身份"一致;
- **④ 本轮 Observed(双仓)**:本仓 `HEAD` = `3916852`(== origin/main,开工时工作树干净);V3 fetch 首试沙箱拒绝(如实入账)宽模式重试 OK,`ls-remote origin main` = **`72af28d`**(未前进,远端仍无实现提交);V3 本地较 DEC-039 **新增 3 件** = `test_ir_identity.py` / `test_adversarial_ir_identity.py` / `test_adversarial_ir_round2.py`(全测试面,untracked = REPORTED 级);
- **⑤ 输出八项分答**:G1-G6 = 全 PASS;Observed/Historical 已分离(Historical = 轮次 3/2/1、DEC-036~032 仅存档引用);**STOP 未触发**;**Producer IR = immutable 保持 / Manifest = immutable 保持 / source bytes = immutable 保持 / Freeze Artifact = immutable 保持**;**Consumer 新增代码仅位于合法写面**(V3 仓 `backend/tests/`);纪律 = 未修改 Consumer 实现 / 未提供代码补丁 / 未自行修复 mismatch;零代码 / 零数据 / 零 schema。

**DEC-039 = Producer Frozen Baseline Guardian During Phase 2-M3**(只读监护,Observed/Historical 分账):
- **① G1~G6 全 PASS 零 mismatch(OBSERVED 本轮)**:G1+G2 177 锚定文件全量比对 checked=177 / missing=0 / mismatch=0(快照自身 sha `2cb980c7…4096` 相符;md=87 / manifest=87);G3 **Producer IR artifact hash unchanged**(`fbcf41ab…b04a5`);G4 证据六工件 + R50 辅助锚 7/7 match=True;G5 pre `4ad3458b…19160` / post `24af8f56…0a10` 相符;G6 冻结四元组字节重导 bytes=92,197 sha `9c6b9063…7528` MATCH + is-ancestor TRUE + 契约 diff empty(临时重导即时删除);测试 **338 passed / 1 xfailed**;
- **② 特别关注项(IR 污染)= 无污染**:G3 字节零变化(读取 ≠ 修改,仅 bytes mismatch 触发 STOP,本轮未触发);旁证 = V3 本地 `backend/app/core/ir_identity.py` L1-40 亲读(仅 `read_text` 提取 `source_content_sha256`,自declare仅 extraction 不计算不验证,全文无写路径);
- **③ 本轮 Observed(双仓)**:本仓 `HEAD` = `40c06c9`(== origin/main,开工时工作树干净);V3 fetch 本轮直接成功,`ls-remote origin main` = **`72af28d`**(未前进,远端仍无实现提交);V3 本地工作树较 DEC-038 **新增 2 件** = `ir_identity.py`(M3 IR Identity Reader v1.0.0)+ `test_adversarial_manifest.py`(untracked = REPORTED 级);
- **④ Consumer 提交影响判定**:未影响 —— 新增代码/测试全部落在 V3 仓合法写面,五类冻结对象实测零变化,**零违例**;
- **⑤ 输出四项**:G1-G6 状态(全 PASS)/ Observed·Historical 分离(Historical = 轮次 2/1、DEC-036~032 仅存档引用)/ **STOP 未触发** / Consumer 代码提交未影响冻结对象;纪律 = 未修改 Consumer 实现 / 未提供代码补丁 / 未自行修复 mismatch;零代码 / 零数据 / 零 schema。

**DEC-038 = Consumer Phase 2 开发期间 Guardian checkpoint(轮次 2,G1~G6 新编号体系,只读,Observed/Historical 分账)**:
- **① 编号与术语纪律(本轮起强制)**:**G = Guardian Check(G1 source bytes / G2 manifest / G3 producer IR / G4 evidence artifacts / G5 corpus snapshots / G6 freeze artifact);M = Consumer Module(Phase 2 的 M1 = Manifest Reader)**;Guardian 编号不得使用 Consumer M 系列;术语 = 禁 "IR hash OK" 式表述,改 "**Producer IR artifact hash unchanged**",区分 Producer IR artifact / Consumer IR reader output / Derived verification result;
- **② G1~G6 全 PASS 零 mismatch(OBSERVED 本轮)**:G1+G2 177 锚定文件全量比对 checked=177 / missing=0 / mismatch=0(锚 = post-backfill audit files map,快照自身 sha `2cb980c7…4096` 相符;md=87 / manifest=87);G3 Producer IR artifact hash unchanged(`fbcf41ab…b04a5`);G4 证据六工件 + R50 辅助锚 **7/7 match=True**;G5 corpus 双快照 pre `4ad3458b…19160` / post `24af8f56…0a10` 相符;G6 冻结对象跨仓字节重导 bytes=92,197 sha256 = **`9c6b9063…7528`** MATCH + `merge-base --is-ancestor f4941ff origin/main` TRUE + `f4941ff..origin/main` 契约 diff empty(临时重导即时删除,不落仓);测试 **338 passed / 1 xfailed**;
- **③ 本轮 Observed(双仓)**:本仓 `HEAD` = `056b6d6`(== origin/main,开工时工作树干净);V3 `origin/main` = **`72af28d`**(fetch 首试沙箱拒绝,宽模式重试 OK 后亲验;**未前进,远端仍无实现提交**);**V3 本地工作树新事实 = untracked Consumer 实现文件**(`raw_bytes_identity.py` / `manifest_identity.py` + 三测试文件 + DESIGN v1/v1.1 等 10 份文档,本地 main 与 origin/main tracked 面同步);REPORTED(V3 本地报告自述:Phase 1 = IMPLEMENTED / Phase 2 M1 = COMPLETE,17/17 测试,待 Phase 3 授权;untracked 未 commit = REPORTED 级)与 OBSERVED 分账不混写;
- **④ Consumer 边界判读**:新增代码与文档全部落在 V3 仓**合法写面,非违例**;判违例标准 = **冻结对象是否变化**而非代码是否新增 —— 本轮 G1~G6 实测五类冻结对象零变化,零违例;**CONSUMER IDENTITY: NOT IMPLEMENTED 口径 = V3 远端已提交实现**,本地 REPORTED 实现在 commit+push 前不改变登记;
- **⑤ Trigger ②(post-Phase1 recheck)= ARMED 未按实现面执行**(实现仅存 V3 本地 untracked);本轮已对基线五类对象执行全量 G1~G6 复检(覆盖 Trigger ② 检查面)全 PASS;触发点 = 每轮开工前 + 实现里程碑后(如 push 至远端)+ 疑似接触事件后 + Owner 令;
- **⑥ 偏差协议**:任一 mismatch → **STOP 仅报告(对象/期望值/实测值);禁自动恢复 / 禁重新生成 / 禁覆盖旧工件**;处置权 = Owner(变化须 Owner 令 + 新配对快照);本轮零触发;
- **⑦ 输出**:`INTEGRATION/PREPROCESSING-PRODUCER-GUARDIAN-PHASE2-CHECK-v1.md`(轮次 2 主体;轮次 1 = DEC-037 原文存档附录 A);纪律 = 零代码 / 零数据 / 零 schema / 基线工件零覆盖 / Guardian only,不参与 Consumer 实现代码。

**DEC-037 = Consumer Phase 2 开工前 Baseline Check(轮次 1,Guardian 只读,Observed/Historical 分账)**:
- **① M1~M6 全 PASS 零 mismatch(OBSERVED 本轮)**:177 锚定文件全量比对 checked=177 / missing=0 / mismatch=0(锚 = post-backfill audit files map,快照自身 sha `2cb980c7…4096` 相符;md=87 / manifest=87);M3 IR `fbcf41ab…b04a5` 独立散列相符;M4 证据六工件 + R50 辅助锚 **7/7 match=True**;M5 corpus 双值 pre `4ad3458b…19160` / post `24af8f56…0a10` 相符;M6 冻结对象跨仓字节重导 bytes=92,197 sha256 = **`9c6b9063…7528`** MATCH + `merge-base --is-ancestor f4941ff origin/main` TRUE + `f4941ff..origin/main` 契约 diff empty(临时重导即时删除,不落仓);测试 **338 passed / 1 xfailed**;
- **② 本轮 Observed(双仓)**:本仓 `HEAD` = `bebd9e1`(== origin/main,开工时工作树干净);V3 `origin/main` = **`72af28d`**(fetch 首试沙箱 `.git/FETCH_HEAD` Permission denied,宽模式重试 OK 后亲验;与 DEC-033/034/036 同值**未前进**;远端提交链 `72af28d→2a723a6→3b3b397→4daecf0→305bd81→f4941ff` 全部 docs,**尚无 Phase 1/Phase 2 实现提交**);REPORTED(Owner 宣告 Phase 2 开工)与 OBSERVED 分账不混写;
- **③ Trigger ②(post-Phase1 recheck)= ARMED 未执行**:远端无 Phase 1 实现提交可复核;若实现后续 push,按 DEC-036 预案只读复检(M1/M2/M3/M6 + M4 辅助);**判读纪律 = Consumer 新增代码提交本身非违例,违例仅指五类只读对象字节变化**;
- **④ 偏差协议**:任何 mismatch → **STOP 仅报告(对象/期望值/实测值),禁止自动修复**;处置权 = Owner(变化须 Owner 令 + 新配对快照);本轮零触发;
- **⑤ 输出**:`INTEGRATION/PREPROCESSING-PRODUCER-GUARDIAN-PHASE2-CHECK-v1.md`;Historical 分账(DEC-032~036 各轮历史观测仅存档引用,未混入本轮判定);纪律 = 零代码 / 零数据 / 零 schema / 基线工件零覆盖 / Guardian only,不参与 Consumer 实现代码。

**DEC-036 = Producer Frozen Baseline Guardian During Consumer Phase 1**(开工前基线快照 + Phase 1 后复检预案,只读):
- **① Phase 1 开工前 baseline snapshot = PASS 零 mismatch**:M1~M6 全量只读核验——177 锚定文件全量比对 checked=177 / missing=0 / mismatch=0(锚 = post-backfill audit files map,快照自身 sha `2cb980c7…4096` 相符;md=87 / manifest=87);证据六工件 + R50 辅助锚 7/7 match;M6 冻结对象跨仓字节重导 bytes=92,197 sha256 = **`9c6b9063…7528`** MATCH + `merge-base --is-ancestor f4941ff origin/main` TRUE + `f4941ff..origin/main` 契约 diff empty(临时重导即时清理,不落仓);
- **② Phase 1 完成后只读检查 = ARMED 未执行**:触发 = V3 远端出现 Phase 1 实现提交(Owner 令复核或疑似接触事件);检查面 = producer data(M1)/ manifest(M2)/ IR(M3)/ freeze artifact(M6)+ M4 辅助;**判读纪律 = Consumer 侧新增代码提交本身非违例(合法写面 = V3 仓代码),违例仅指只读对象字节变化**;
- **③ 偏差协议**:任何 mismatch → **STOP 仅报告(对象/期望值/实测值),禁止自动修复**;处置权 = Owner(变化须 Owner 令 + 新配对快照);
- **④ 输出**:`INTEGRATION/PREPROCESSING-PRODUCER-GUARDIAN-PHASE1-CHECK-v1.md`;本轮 Observed:本仓 `origin/main` = `27727c4`(开工时工作树干净),V3 `origin/main` = `72af28d`(fetch 首试 Recv failure 重试 OK 后亲验;与 DEC-033/034 同值未前进,**尚无 Consumer Phase 1 实现提交** → 本轮即开工前锚点);纪律 = 零代码 / 零数据 / 零 schema / 基线工件零覆盖 / Guardian only。

**DEC-035 = Producer Frozen Baseline Guardian Mode**(Consumer 实现阶段 Producer 侧守护,只读):
- **① Consumer Implementation Boundary Audit = BOUNDARY HOLDING,零违例**:边界模型 = Consumer 实现合法写面仅 V3 仓代码,对基线五类禁改对象(producer 数据/manifest/source bytes/IR/freeze artifact)全部只读;六步链逐项边界不变式登记;证据 = 177 锚定文件全量比对 **checked=177 bad=0** + 六证据工件 6/6 + IR 工件 `fbcf41ab…b04a5` 相符;
- **② Immutable Monitoring Checklist M1~M6 建立,本轮全 PASS**:source bytes / manifest(C8 剥键不变式)/ IR / evidence 六工件 / corpus 双值(`4ad3458b…` → `24af8f56…`)/ 冻结对象四元组(`9c6b9063…7528`);触发点 = 每轮开工前 + Consumer 实现里程碑后 + 疑似接触事件后;**偏差协议 = 任一 mismatch → STOP 只报告不自修,处置权 = Owner**;
- **③ Non-Participation**:DSH 不参与 Consumer Identity Verification 代码实现(复核 ≠ 实现);
- **④ 输出**:`INTEGRATION/PREPROCESSING-PRODUCER-FROZEN-BASELINE-CONSUMER-BOUNDARY-CHECK-v1.md`;本轮 Observed:本仓 `origin/main` = `e1584bd`(== HEAD),V3 `origin/main` = `72af28d`(reachable TRUE),测试 338 passed / 1 xfailed。

**DEC-034 = Producer Frozen Baseline Archive Final Check**(最终归档,只读验证 + 文档登记):
- **① 四项 immutable 终检全 PASS**:source bytes(C4 87/87 零漂移)/ manifest(C8 剥键 87/87 + 工件 sha 不变)/ IR(C5 71·71)/ evidence(6/6 登记 sha 相符 + 复跑字节级一致);C1-C9 全 PASS = VERIFIED;测试 338 passed / 1 xfailed;
- **② 三账登记**:state.yaml(DEC-034 + FACT-037 + `producer_baseline_archive_final` 块)/ CURRENT.md / log.md;报告 = `INTEGRATION/PREPROCESSING-PRODUCER-BASELINE-ARCHIVE-FINAL-REPORT-v1.md`(commit `56f95f2`);
- **③ 远端验证分账**:**Observed(本轮)**= V3 fetch OK / `git ls-remote origin main` = **`72af28d`**(reachable = TRUE)/ `merge-base --is-ancestor f4941ff origin/main` = **TRUE**;**Historical(仅存档引用)**= DEC-031 `305bd81` / DEC-032 `4daecf0b` / DEC-033 首试失败 + 升级重试 `72af28d`;
- **④ 最终状态**:`PRODUCER BASELINE: FINALIZED` / `CONSUMER IDENTITY: NOT IMPLEMENTED`;归档声明 = 基线以工件表字节为准,后续变化须 Owner 令 + 新配对快照,不得就地改写。

**DEC-033 = Producer Frozen Baseline Final Integrity Record 收口**(Frozen 后 Producer 数据基线最终登记):
- **① Integrity Report 提交**:`INTEGRATION/PREPROCESSING-PRODUCER-FROZEN-BASELINE-INTEGRITY-REPORT-v1.md`(commit `8fc4d60`);
- **② 三账登记**:state.yaml(DEC-033 + FACT-036 + `producer_baseline_finalized` 块)/ CURRENT.md / log.md 同步;
- **③ 远端状态本轮真实重验**:首试 `fetch` FAIL(沙箱 `.git/FETCH_HEAD` Permission denied)+ `ls-remote` FAIL(`SEC_E_NO_CREDENTIALS`)——真实错误如实入账,未引用历史结果;宽模式重试 `fetch` OK / `git ls-remote origin main` = **`72af28d`**(reachable = TRUE,较 DEC-032 时点 `4daecf0b` 前进)/ `merge-base --is-ancestor f4941ff origin/main` = **TRUE**;
- **④ 四项 immutable 最终确认**:source bytes / manifest / IR / evidence 全部 immutable(C1-C9 复跑全 PASS = VERIFIED,零漂移)→ **STATUS: PRODUCER BASELINE FINALIZED**;**Consumer Identity Verification NOT IMPLEMENTED**(五项 V3 消费能力不变)。

**DEC-032 = Contract v0.2 Frozen 状态最终登记确认**(Freeze Event 后 Producer 侧账本一致):
- **① Freeze Artifact 验证 PASS**:`git ls-remote origin main` = **`4daecf0b`**(remote reachable = TRUE;`4daecf0b` = V3 DEC-035 文档轮,`305bd81 → f4941ff → c6e771c` 链保持);`merge-base --is-ancestor f4941ff origin/main` = TRUE;`git show f4941ff:<contract>` **字节级重导 sha256 = `9c6b9063e81fb2a66d85794b280c9d931f1b0074b39abf472033218149b17528`** == 必须值(92,197 bytes);`f4941ff..origin/main` 契约文件 diff 零差异;
- **② Producer 侧登记 = Contract v0.2: FROZEN**:state.yaml(DEC-032 + `owner_contract_frozen` 块)/ CURRENT / log 三件同步;冻结对象四元组 = `kurt-wong/AITutors-v3` @ `f4941ff87c0130ee0b79ff6b807c4ec2826b8ff1` / `PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` / `9c6b9063…7528`(唯一有效;`c6e771c`/`c8d89586…1032` = 历史登记勿引用);
- **③ 最终状态 = `STATUS: CONTRACT FROZEN`**。

**Freeze does not include(明确登记)**:bytes verification implementation / identity gate implementation / IR verification implementation——契约 REQUIREMENT 不得读作现状;五项 V3 消费能力(raw bytes acquisition / SHA256 独立验证 / Manifest identity verification / IR identity verification / identity gate)全部 **NOT IMPLEMENTED** 不变。
**下一阶段**:**V3 Consumer Identity Verification Implementation**(bytes → SHA256 → Manifest 验证 → IR 验证 → fail-closed → Gate → Admission;实现排期属 V3 侧);**已裁六项(identity key / path / `source_version_id` / Semantic Pending / 87·71·16 / bytes requirement)不重开**;长开项与延期五项不变;DSH 侧令前保持零新数据动作(Step 4 数据治理 / Step 5 图片恢复仍禁)。

## 主线:preprocessing 内部收口(数据卫生,Owner 令)

- **收口计划(当前决策入口)**:`PREPROCESSING-CLOSURE-PLAN.md` v1——**A 必须修复才能冻结 Contract = 0 项**(披露路线 vs 清洁路线二选一待裁);B 清洗序 = unit_type 单点 / recover_images 批跑(1,394 份,PDF 在位 99.86%,**R50 基线交集恰 2 份已隔离**,无 PDF 恰 2 份单列)/ flags 登记 / 6 needs_ruling / D5-C~E;C 消费限制 = unresolved 596 槽位 / 悬空 figure / 四态空值 / manifest 不钉 sha。**关键硬事实:异常 manifest 是 R50 冻结基线成员(sha 58058c4f…),修复必致基线 DRIFT,须配对再冻结决策**;
- **DQE 四重点测量完成(只读)**:`EVIDENCE/PREPROCESSING-DATA-QUALITY-REPORT.md` v1——①unit_type:全语料 166 manifest 穷举,**恰 1 例非标准值**(batch-C 合格考化学 Q1,v2 可消费面内)→ 单点修复待批;②figure:70,838 引用(行内 HTML 相对路径 99.99%),悬空 27,240 处/1,396 份**全部 = 未恢复 `imgs/` 原始形态**(recover_images 积压,daemon 产出使其自 R58 的 499 份增长),已改写形态悬空 = 0 → 批量恢复待批,最小 registry 不需要;③flags:值域天然闭合 2 值 + 596 unresolved 槽位,登记册零注册 → 登记待批;④稳定性:**IR 71/71 源 sha 零漂移 + R50 基线 356/356 + OCR 清单 append-only**,manifest 0/166 钉 sha(分层事实非缺陷);
- **Integration Contract v0.1 = DRAFT;B1/B2/B3 已裁(DEC-019,2026-09-16)**:Manifest+IR 双层 / raw-bytes SHA-256 唯一 source identity / unknown unit_type → UNKNOWN/PENDING。**主线 = Contract v0.2 起草**(输入两侧齐备:生产侧 = `PREPROCESSING-B1B3-READINESS.md` §3,消费侧 = Claude Consumer Review v0.2);DSH 侧事实基线 = Interface Facts v2 + Reconciliation v0.2;OQ-1~4 在册;
- **BUG-14-DATA 收口进度**:D5-A ✅ / D5-B ✅ 70/70 / D5-C·D5-D 待跑(DQE 四账 = D5-D 输入口径)/ D5-E 🔒 / **6 份 needs_ruling 等 Owner 逐份裁定**。

## 当前工作项:EB / Evidence Resolution Boundary Discovery

| Agent | 仓库 | 角色 | 最近动作 |
|---|---|---|---|
| **DSH** | kurt-wong/Aitutors-preprocessing | Source Evidence Producer(输入事实生产:OCR/Annotation/Source Version)+ **Frozen Baseline Guardian** | **DEC-045 自身全任务对抗性自审:基线复测全 PASS 零漂移,发现 0 BLOCKER / 5 WARNING / 5 NOTE,存量修复 5 处**(V3 仓零写入;子代理误报经亲验驳回;S-3 假 MISMATCH 方法错误当场纠正并入账);**DEC-044 Closure Review 登记挂起(待 push)**;令前保持零新数据动作,不参与 Consumer 实现 |
| **Claude** | kurt-wong/AITutors-v3 | 教学系统构建(Resolver/IR/Authority/Admission) | V3 `origin/main` = **`72af28d`**(DEC-043 亲验,未前进,远端零身份链代码);**V3 本地工作树 = untracked Consumer 实现**(core 五模块 M1–M5 全落树;测试 14 件含 `test_adversarial_m5_round1/round2.py`;untracked 实测 **9 docs + 5 core + 14 tests = 28**〔DEC-043 F-3 更正 DEC-042 计数〕;合法写面);**M5 未集成真实链(runner_b2 零调用)**;设计/接口偏离待收口 = D1~D5;遗留:R5-03 DEC 编号冲突 + DEC-017/018 同步 |

## P3.2 / EB-004 终局(VERIFIED)

```
①修正 A ✓  ②修正 B ◐  ③Scope ✓  ④DSH 核验 ✓  ⑤实验 ✓  ⑥DSH 亲验 ✓  ⑦bypass = YES
→ 架构问题进 Decision 流程:EB-008(Admission 是否引入 Evidence Authority enforcement)
```

- **结果(FACT-021)**:执行的 4 个向量(N1/N2/N7/N8)全部 BYPASS;DSH 亲读 admission.py 全文确认 **approve() 无任何 Evidence Authority 依赖**(连 import 都没有)——**enforcement 机制不存在**(非"存在但可绕过"),BUG-V3-048 实锤;
- **两处精确化(必须随 findings 引用)**:①FACT-022:**8 向量只执行了 4 个**(N3–N6 未执行,"4/4 bypass" 措辞误导);②FACT-023:**4 个攻击实例 / 1 条 bypass 路径**(调用同构,实例计数合法但独立路径 ≥1);
- 实验纪律合规:生产代码零修改 / 结果未当架构 Decision / OBSERVED–INFERENCE 分离。

## 基础设施状态(FACT-024,Docker 事故后重建)

| 容器 | 镜像 | 端口 | 状态 |
|---|---|---|---|
| aitutor-postgres | pgvector/pgvector:pg16 | 5432 | healthy;**数据完好**(卷 backend_postgres_data 幸存,25 张表) |
| aitutor-redis | redis:alpine | 6379 | healthy |
| aitutor-minio | quay.io/minio/minio:latest | 9000/9001 | healthy |

注意:minio Docker Hub 源已停止分发(改 quay.io);`vector` 扩展未装(embedding 接线时需 CREATE EXTENSION);minio bucket 未初始化(非阻塞)。V3 compose 变更 = commit `3d0cb21`。

## 两侧一致清单(已闭环)

- 架构边界五规则 / 三数字口径(96.2/91.2/98.1)/ options_region = 最小充分 handoff / 生产 Resolver 采纳缺口归 V3(EB-005)/ HTML B 类系统性(Q13/Q37 同 unit 跨版本)/ SEMANTIC=0 / **Admission 无 Evidence Authority enforcement(bypass 实锤,DSH 独立亲验)**。

## 开放问题(EB 项,canonical 编号)

| ID | 问题 | Owner | 状态 |
|---|---|---|---|
| EB-001 | HTML table 型选项:Producer 扩圈定 vs Resolver Region 内解析 | joint | ATTRIBUTED |
| EB-002 | 图片型选项标记↔图边界(§11.3 冻结线) | joint | ATTRIBUTED |
| EB-003 | `region_upper=None` 无界扫描可达生产 | v3 | EVIDENCED |
| EB-004 | P3.2 Enforcement Verification(**bypass = YES,问题有答案**) | v3 | **VERIFIED** |
| EB-005 | 生产 Resolver 是否引入 options_region(**OPEN 暂不实现,不与 EB-008 合并**) | v3 | EVIDENCED |
| EB-006 | A 缺标点 contextual rule(设计属 V3) | v3 | EVIDENCED |
| EB-007 | formula FP 结构排除(检出来源 = V3 代码追踪) | v3 | EVIDENCED |
| EB-008 | **Admission Evidence Authority enforcement** | v3 | **DECIDED**(2026-09-15 DEC-018 Design Frozen,即 DEC-013 终裁落地;设计链 = Rev-1 未 commit → Rev-2 `9bf8878` 4 BLOCKER → Rev-3 `a80d555` VERIFIED → Rev-4 `2ad6f99` Review-5 VERIFIED 0 BLOCKER → Owner DEC-017 确认 → DEC-018 冻结;**实现顺序: ①validation_events → ②proof → ③Admission enforcement → ④invalidate → ⑤DSH 代码攻击测试 → ⑥完整 V3 业务链**;验收标准 = `EVIDENCE/EB008-DSH-IMPL-ACCEPTANCE.md`(四攻击域 A~D);**①~⑤ 已完成**:P1 = `88aeae8`/`b5ddbe3`,Review-1 = VERIFIED 0 BLOCKER(`EVIDENCE/EB008-IMPLEMENTATION-REVIEW-1.md`,产物均在 preprocessing 仓;**Owner 再校准:该报告不再作为推进状态依据**,EB-008 定位收敛为跨项目契约,详见 `INTEGRATION/PREPROCESSING-INTEGRATION-CONTRACT.md` §4);⑥ 完整 V3 业务链仍待 Owner 放行) |

## 实现阶段进行中(EB-008 DECIDED 后)

1. **P1 实现 + 顺序⑤ 攻击验收已完成**:Claude 单 commit 交付顺序①~④(V3 `88aeae8`)+ 实现说明(`b5ddbe3`);DSH 四域攻击测试(23 用例)全收敛 = **VERIFIED 0 BLOCKER**;P3.2 N1/N2/N7/N8 复跑**全部 BLOCKED**(基线 FACT-021 = 全 BYPASS,BUG-V3-048 闭合);报告 = `EVIDENCE/EB008-IMPLEMENTATION-REVIEW-1.md`;
2. **待 Owner 定性(Review-1 WARNING/NOTE)**:F-1 DB 直连把 human_review 行洗成 machine 外观绕过 proof 校验(R-3 冻结边界内)/ F-2 latest-by-validated_at 潜在时间戳复活面(当前生产路径零暴露)/ F-3 invalidate 不回溯撤销已物化 Question;
3. **实现期义务状态**:持久化/invalidate 状态机/replay/proof/enforcement 五项 DONE;source_version supersede 接线未接(R-4 已接受);DB 触发器 Phase-2;
4. **设计阶段已关闭**(DEC-018):不重开设计讨论;残余风险处置属 Owner 裁决;
5. Claude 遗留治理项:R5-03 DEC 编号冲突(handoff 012/013)+ DEC-017/DEC-018 同步;N3–N6 仍 deferred(DEC-012),实现未预留 bypass 后门(亲验)。

## 当前禁止(两侧共同)

不改 V3 Frozen Spec / 不冻结 Producer Contract / 不修 Resolver heuristics · 不为 96.2% 修补 · 不合并语料分母 · 不把 21+10 当 31 独立失败 · REPORTED 不冒充 OBSERVED · 不手写重构证据文件数据 · **case id 不得重编号** · 不本地分配新 id · Coordination ≠ L2 · **P3.2 八禁(实验结果≠架构 Decision,不自动 workaround)**。

## 接收方启动动作

按 PROTOCOL §5 七步:fetch → 读 state.yaml(权威)→ 读本文件 → 读最新 HANDOFF → 核验证据引用(精确路径,禁模糊匹配)→ 只做 OPEN 项 → 更新 + handoff + commit + CI 绿。

# CURRENT — 跨 Agent 协调快照(人 + Agent 快速阅读)

> 机器可读状态见 `state.yaml`;协议见 `PROTOCOL.md`。本文件是镜像快照,**权威以 state.yaml 为准**。
> 更新:2026-09-16(**DEC-033 Producer Frozen Baseline Final Integrity Record 收口**:Integrity Report v1 提交(`8fc4d60`)+ 三账登记 + 远端状态本轮真实重验(fetch OK / `origin/main` = `72af28d` reachable = TRUE / `f4941ff` 亲缘 TRUE;首试失败已如实入账)+ 四项 immutable 复验零漂移 → **STATUS: PRODUCER BASELINE FINALIZED**;Consumer Identity Verification NOT IMPLEMENTED 不变)· 前轮 = Contract v0.2 Frozen 最终登记确认(DEC-032)· canonical ledger = kurt-wong/Aitutors-preprocessing(main)

## 🧭 新会话快速恢复(新会话先读本节,30 秒回到工作状态)

**一句话状态**:Contract v0.2 = **FROZEN**(DEC-032);Frozen Baseline 保全复验完成 = **PRODUCER BASELINE FINALIZED**(DEC-033,2026-09-16);DSH 指令链全部闭环,**令前保持零新数据动作**,等 Owner 下一步指令。

- **指令链末端**:… → DEC-030(`a899adf`)→ DEC-031(`5b0552d`)→ DEC-032(`9cf35e3`)→ **DEC-033(`8fc4d60` + 三账收口 commit = main HEAD)**;ODR = **v1.14**(§1quindecies 原文照录);工作树干净(提交后);
- **冻结对象(唯一有效四元组)**:`kurt-wong/AITutors-v3` @ `f4941ff87c0130ee0b79ff6b807c4ec2826b8ff1` / `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` / sha256 **`9c6b9063e81fb2a66d85794b280c9d931f1b0074b39abf472033218149b17528`**(92,197 bytes)。`c6e771c` / `c8d89586…1032` = 历史登记,**勿引用**。V3 远端 main 观测值 = `4daecf0b`(DEC-032 时点;Claude 可能继续推进,一切以 fetch/ls-remote 实测为准);
- **关键数字**:manifest 166 / 接口面 87(87/87 携 `source_content_sha256`,unique 87 · dups 0)/ IR 71 ADMITTED(1,664 单元,71/71 对账零漂移)/ 16 Semantic Pending / v1 legacy 79(隔离,C-IN-1 下必拒)/ R50 基线 356(**DRIFT = 恰 87 为预期**,承接者 = pre/post audit 双快照 `b11874c4…` / `2cb980c7…`);
- **Frozen Baseline 保全(DEC-033,最新)**:四项 immutable 复验全过——source bytes 零漂移(87/87 vs Step1+R50)/ manifest 差异恰 = 追加一键 / IR 71·71 零漂移 / 证据六工件登记 sha 6/6 相符 + 复跑字节级复现(`a707738e…5c33`);报告 = `INTEGRATION/PREPROCESSING-PRODUCER-FROZEN-BASELINE-INTEGRITY-REPORT-v1.md`;本轮远端实测(V3)`origin/main` = `72af28d`,`f4941ff` 亲缘 TRUE;**Consumer Identity Verification NOT IMPLEMENTED 不变**;
- **边界纪律(新会话必守)**:①Freeze 不含三项实现——bytes verification / identity gate / IR verification;五项 V3 消费能力全部 **NOT IMPLEMENTED**,契约 REQUIREMENT ≠ 现状(Decision ≠ Implementation);②已裁六项(identity key / path / `source_version_id` / Semantic Pending / 87·71·16 / bytes requirement)**不重开**;③DSH 令前零新数据动作——Step 4 数据治理 / Step 5 图片恢复 / IR 重生成 / schema 变更 / daemon 仍禁;④case id 不重编号;REPORTED ≠ OBSERVED;转述层会漂移,引用必须回到证据文件;
- **下一阶段**:V3 Consumer Identity Verification Implementation(bytes → SHA256 → Manifest 验证 → IR 验证 → fail-closed → Gate → Admission)——实现排期属 V3 侧;若 Owner 令 DSH 复核实现,核验基准 = 契约 §2.3/§5.6.2 验证链 + 五项 NOT IMPLEMENTED 边界不得因 FROZEN 松动;
- **长开项(不阻塞 FROZEN,须令才动)**:16 份 IR 再生成批次 / D-3 存量 1 例 `andalone_question` / D-4 两份三重成员 / IR 字段名对齐(`source_sha256` → `source_content_sha256`)/ 两层状态载体 + reviewable record / C.1 载体正文引用形态追认;延期五项(legacy 79 披露 / 17 拒收 / OCR-PDF 扩展 / DEC 编号统一(R5-03)/ bytes 传输方式)不处理;
- **环境纪律**:`PYTHONIOENCODING=utf-8`;PowerShell `>` 重定向写 UTF-16(字节级导出用 `cmd /c "git show … > file"` + `Get-FileHash`);push / gh 需 `sandbox_permissions: danger-full-access` + justification;push 后必须 `git ls-remote origin main` 亲验 + `gh run list` 对账;测试基线 = **338 passed / 1 xfailed**;
- **阅读顺序**(PROTOCOL §5):state.yaml(权威)→ 本文件 → ODR v1.14 → log.md 尾部 → 最新 HANDOFF;裁决原文全集 = `INTEGRATION/PREPROCESSING-OWNER-DECISION-RECORD-v1.md`。

## ⏭ 当前状态:PRODUCER BASELINE FINALIZED(2026-09-16,DEC-033;上一状态 = CONTRACT FROZEN,DEC-032)→ 下一阶段 = V3 Consumer Identity Verification Implementation

**裁决基准**:`INTEGRATION/PREPROCESSING-OWNER-DECISION-RECORD-v1.md`(**v1.14**:… + §1quaterdecies DEC-032 + **§1quindecies DEC-033**)。

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
| **DSH** | kurt-wong/Aitutors-preprocessing | Source Evidence Producer(输入事实生产:OCR/Annotation/Source Version) | **DEC-033 收口完毕:PRODUCER BASELINE FINALIZED**(Integrity Report v1 + 三账登记 + 远端本轮真实重验 `72af28d`/`f4941ff` 亲缘 TRUE + 四项 immutable 零漂移;零代码零数据零 manifest 零 IR 修改);令前保持零新数据动作 |
| **Claude** | kurt-wong/AITutors-v3 | 教学系统构建(Resolver/IR/Authority/Admission) | Freeze Artifact 已 push 且远端可复现(`4daecf0b` 含 `f4941ff`,DEC-035 文档轮契约零触碰);**下一阶段 = V3 Consumer Identity Verification Implementation**;遗留:R5-03 DEC 编号冲突 + DEC-017/018 同步 |

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

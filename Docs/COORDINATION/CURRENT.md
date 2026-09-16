# CURRENT — 跨 Agent 协调快照(人 + Agent 快速阅读)

> 机器可读状态见 `state.yaml`;协议见 `PROTOCOL.md`。本文件是镜像快照,**权威以 state.yaml 为准**。
> 更新:2026-09-16(**Contract v0.2 最终冻结收口(DEC-027,DSH/Producer 侧)**:Freeze Evidence v1 建立(Contract v0.2 → Step 1 → Step 2 → 验证报告 → 最终复核,全链可追溯 + 工件 sha256 登记);最终一致性检查 **C1-C9 全 PASS = VERIFIED,零 BLOCKER**(只读脚本从当前磁盘字节独立重推导);文档交叉核验完成(Facts v2.5 消歧 / DepMap / Alignment v4 废止标识);结论 = **READY FOR CONTRACT FREEZE(Producer 侧)**;Decision ≠ Implementation:V3 能力全部 not started)· canonical ledger = kurt-wong/Aitutors-preprocessing(main)

## ⏭ 当前状态:Freeze Evidence 收口完毕 READY FOR CONTRACT FREEZE(Producer 侧)→ 等 Claude 正文合并 + Owner 正式 Freeze 令(2026-09-16,DEC-027)

**裁决基准**:`INTEGRATION/PREPROCESSING-OWNER-DECISION-RECORD-v1.md`(**v1.8**:… + §1octies DEC-026 + **§1novies DEC-027**)。

**DEC-027 = Contract v0.2 最终冻结收口(DSH/Producer 侧)**:四项原则最终确认(source_content_sha256 Identity Authority / 双层职责 / 16 份 Semantic Pending 四约束 / 冻结后实现阶段不得改)+ Task 1 Freeze Evidence + Task 2 最终一致性检查(全过 VERIFIED / 不一致 BLOCKED 不自修)+ Task 3 文档交叉核验 + Task 4 继续不做实现 + **Decision ≠ Implementation** 纪律。

**DSH 本轮交付**:
- **Freeze Evidence**:`INTEGRATION/PREPROCESSING-CONTRACT-v0.2-FREEZE-EVIDENCE-v1.md`(追溯链 Contract v0.2(ff04f47+e70807b)→ Step 1 snapshot → Step 2 backfill → verification report → final check;工件 sha256 全值 + R50 血统解释 + 16 pending 逐份);
- **最终一致性检查**:`scripts/freeze_evidence_final_check.py`(只读,不信先前报告结论,全部从当前磁盘字节重推导)→ `data/freeze_evidence_final_check.json`:**C1-C9 全 PASS,overall VERIFIED**(87 scope / 87 唯一身份键 / 87 bytes+64hex / 87 零漂移==R50 / IR 71·71 / pending 16·16 / R50 血统+audit 对账 / 剥键 87·87 / locator 87·87;unique identities 87, dups 0);测试 338 passed / 1 xfailed;
- **文档交叉核验**:Facts v2 → **v2.5**(现行态按 DEC-025 命名消歧,历史时点明确标识)、DepMap 现行描述更新、Alignment v4 行内**已废止**标识;`rg` 复核剩余命中全部属允许保留语境(原文照录 / 取代注记 / Claude 修正指令 / V3 UUID FK)。

**等 Claude**:合并最终契约(`source_content_sha256` / path non identity / Identity Pending / bytes verification requirement;全部替换 Semantic Unavailable → Semantic Pending;V3 代码零修改)。
**等 Owner**:**正式 Freeze 令(= 五步序 Step 3)**——DSH 侧证据与前置已全部闭合(READY FOR CONTRACT FREEZE)。
**Decision ≠ Implementation**:V3 D-7(bytes 四能力)/ D-8 六消费义务 / D-9 unknown+reviewable record / D-11 identity verification **全部 not started**;V3 现自算 hash = canonical_json 包裹(`runner.py:71-73`),非 raw bytes。
**仍开**:16 份 IR 再生成批次(须另令)/ D-3 存量 1 例 / D-4 2 份三重成员 / IR 字段名对齐 / 两层状态载体 + reviewable record / C.1 载体形态追认;**延期五项**(legacy 79 披露 / 17 拒收 / OCR-PDF 扩展 / DEC 编号统一 / bytes 传输方式)按 Owner 建议不处理。
**下一阶段核心风险(Owner 原文)**:V3 消费端必须真正实现「拿到 bytes → 自己计算 SHA256 → 验证 Manifest → 验证 IR → 失败关闭」。

## 主线:preprocessing 内部收口(数据卫生,Owner 令)

- **收口计划(当前决策入口)**:`PREPROCESSING-CLOSURE-PLAN.md` v1——**A 必须修复才能冻结 Contract = 0 项**(披露路线 vs 清洁路线二选一待裁);B 清洗序 = unit_type 单点 / recover_images 批跑(1,394 份,PDF 在位 99.86%,**R50 基线交集恰 2 份已隔离**,无 PDF 恰 2 份单列)/ flags 登记 / 6 needs_ruling / D5-C~E;C 消费限制 = unresolved 596 槽位 / 悬空 figure / 四态空值 / manifest 不钉 sha。**关键硬事实:异常 manifest 是 R50 冻结基线成员(sha 58058c4f…),修复必致基线 DRIFT,须配对再冻结决策**;
- **DQE 四重点测量完成(只读)**:`EVIDENCE/PREPROCESSING-DATA-QUALITY-REPORT.md` v1——①unit_type:全语料 166 manifest 穷举,**恰 1 例非标准值**(batch-C 合格考化学 Q1,v2 可消费面内)→ 单点修复待批;②figure:70,838 引用(行内 HTML 相对路径 99.99%),悬空 27,240 处/1,396 份**全部 = 未恢复 `imgs/` 原始形态**(recover_images 积压,daemon 产出使其自 R58 的 499 份增长),已改写形态悬空 = 0 → 批量恢复待批,最小 registry 不需要;③flags:值域天然闭合 2 值 + 596 unresolved 槽位,登记册零注册 → 登记待批;④稳定性:**IR 71/71 源 sha 零漂移 + R50 基线 356/356 + OCR 清单 append-only**,manifest 0/166 钉 sha(分层事实非缺陷);
- **Integration Contract v0.1 = DRAFT;B1/B2/B3 已裁(DEC-019,2026-09-16)**:Manifest+IR 双层 / raw-bytes SHA-256 唯一 source identity / unknown unit_type → UNKNOWN/PENDING。**主线 = Contract v0.2 起草**(输入两侧齐备:生产侧 = `PREPROCESSING-B1B3-READINESS.md` §3,消费侧 = Claude Consumer Review v0.2);DSH 侧事实基线 = Interface Facts v2 + Reconciliation v0.2;OQ-1~4 在册;
- **BUG-14-DATA 收口进度**:D5-A ✅ / D5-B ✅ 70/70 / D5-C·D5-D 待跑(DQE 四账 = D5-D 输入口径)/ D5-E 🔒 / **6 份 needs_ruling 等 Owner 逐份裁定**。

## 当前工作项:EB / Evidence Resolution Boundary Discovery

| Agent | 仓库 | 角色 | 最近动作 |
|---|---|---|---|
| **DSH** | kurt-wong/Aitutors-preprocessing | Source Evidence Producer(输入事实生产:OCR/Annotation/Source Version) | **DEC-027 收口完毕:Freeze Evidence v1 + 最终一致性检查 C1-C9 全 PASS(VERIFIED)+ 文档交叉核验完成 = READY FOR CONTRACT FREEZE(Producer 侧)**;零实现动作、数据写入面 = 零 |
| **Claude** | kurt-wong/AITutors-v3 | 教学系统构建(Resolver/IR/Authority/Admission) | **待办:合并最终契约**(`source_content_sha256` / path non identity / Identity Pending / bytes verification requirement;Semantic Unavailable → Semantic Pending 全部替换;V3 代码零修改);遗留:R5-03 DEC 编号冲突 + DEC-017/018 同步 + 契约稿 untracked(REPORTED 级) |

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

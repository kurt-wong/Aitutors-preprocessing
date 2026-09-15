# EB-008 Review-3 — Adversarial Validation of L2 Design Revision-2

- **Date**: 2026-09-15
- **Reviewer**: DSH(preprocessing 侧)
- **Target**: `AITutors-v3/Docs/DECISIONS/89_EB008_EVIDENCE_AUTHORITY_ENFORCEMENT_REVISION2.md`
- **Anchor**: commit `9bf8878d278a34cee12ef7097ffaa56e1609b1ad`(V3 repo,**已 commit**,首次达到 COMMITTED 级)/ sha256 `213CC3EB4CB5B5206E6AE42DC3AB02C3A4501A7ACA47F0906310647D1199980B`
- **Authority**: DEC-013(方向)+ DEC-015(五验证点 + UNPROVEN 红线 + "不重新设计,只验证")
- **Code base**: V3 local HEAD `9bf8878`(backend/app,零修改)

**Verdict: REQUIRES_REVISION — 4 BLOCKER。不足够进入 DEC-013 终裁。**

---

## T1. Bootstrap Authority(冷启动循环依赖)

### OBSERVED
- Rev-2 §RDQ-001 提出 Phase 划分:Phase 1 IR 创建(无 Authority 要求)→ Phase 2 Gate 生产 ValidationEvent → Phase 3 Admission 消费 Authority;Bootstrap Protocol B1-B6。
- 代码生产顺序(`gate/service.py` L171-246):IRBuilder.build → Compiler → `evaluate()` → `record_validation()` → create/复用 candidate → auto 路径立即 `approve()`。Gate 生产 Authority 时确实不需要任何 Authority 输入(`promotion.py` L122-180 纯函数式构造)。

### VERIFIED
- **自动路径的循环依赖已被打破**(验证方法:数据流追踪)。Gate 是纯 Producer——`record_validation_event()` 输入仅为 gate_decision dict,无任何 Authority/ValidationEvent 消费。"IR 创建需要 Authority → Authority 需要 Gate → Gate 需要 IR" 的环在自动路径上不存在。此项 Rev-2 **成立**。

### ATTACK(A-3-1,与 T5 交叉)
- **人工路径的 Authority 生产机制不存在,Rev-2 只断言未定义**。B3 声称"Human Review 是 Authority Producer(通过 ValidationEvent)",但唯一 OBSERVED 的人工生产点是 `candidates.py` L58-64:写 `review_trail`(JSONB list),**不创建 ValidationEvent**。Rev-2 全文没有给出 review_trail → ValidationEvent 的投影步骤、执行者、触发点。人工冷启动(pending_review 首例)在设计层无出路。

### UNPROVEN
- **Authority 持久化**:`EvidencePromotionService` 是 per-run 内存对象(`service.py` L160,fresh per run;`promotion.py` L206-209 in-memory tuple)。run 结束 Authority 即消失。Rev-2 未解决项表把持久化归为"设计已定,实现后补"——按 DEC-015 红线("实现阶段再增加字段/后续 migration"一律 UNPROVEN),**Admission 时点能否读到 Authority = UNPROVEN**。当前 OBSERVED 事实:API 人工 approve 发生在 run 结束后,届时 ledger 已不存在,Authority 检查在物理上无对象可查。

---

## T2. Run Identity(candidate_id 替代 run_id)

### OBSERVED
- `snapshot.py` L42-48:`AdmissionCandidate.__table_args__ = UniqueConstraint("logical_execution_stage", "logical_execution_hash")`。
- `snapshot_repository.py` L118-156:`create_admission_candidate()` 用 `ON CONFLICT DO NOTHING` 锚 (stage, hash);冲突 → **re-read 既有行返回**(docstring:"冲突 → re-read existing(恒 pending_review,idempotent success)")。
- `service.py` L214-231:每次 run 先 `find_candidate_by_le_hash()`,命中即**复用既有 candidate,不创建新行**。
- le_hash 输入(`service.py` L265-296):contract_domain(4 项版本号)+ input_domain(annotation_id、annotation_payload_hash、unit_id)。**相同文档 + 相同 annotation + 相同版本 → 相同 le_hash**。

### ATTACK(A-3-2,BLOCKER)
- **Rev-2 核心声明 I2"每次 Run 创建新 Candidate(新 UUID)"与代码直接矛盾**。真实行为:同一逻辑执行 replay → 命中 (stage,hash) UNIQUE → 复用同一 candidate_id。
- 由此**Rev-2 的 Run A/B replay 证明整体失效**:证明第 1 步"Run B 创建 Candidate_Y(UUID_B)← 新 Candidate"为假;实际 Candidate_Y = Candidate_X,于是 AuthorityIdentity `(sv, candidate_id, claim_id)` 在 Run A 与 Run B **逐位相同**。I6"Authority 不跨 Candidate 转移"在"两个 Candidate 是同一行"时为空洞真——**cross-run authority transfer 按构造发生**,正是 Rev-2 宣称已排除的场景。

### ATTACK(A-3-3,BLOCKER,状态机回归)
- Rev-1 阻断项 RDQ-2 的状态机冲突被 Rev-2 "绕开"而非解决:当前 `record_validation` 幸免 ValueError 仅因 ledger 是 per-run 内存(fresh log 无既有事件,`models.py` L281-287 首事件分支)。一旦按设计所需持久化 ledger(见 T1 UNPROVEN),同 candidate 重跑将对已 VALIDATED 的 claim 再 append `validated` → `models.py` L299-304 ValueError。**设计自相矛盾:要么 Authority 不持久(Admission 无从检查),要么持久后重跑崩溃。二者不可同时回避。**

### REQUIRED_DECISION
- Run Identity 必须基于真实身份机制重述:候选身份 = (stage, le_hash) 的**逻辑执行身份**(这本身是合理的幂等设计),Rev-2 须改为在该身份上定义 Authority 语义(包括幂等 replay 时 Authority 的期望行为),而不是建立在"每 run 新 UUID"的假前提上。

---

## T3. Human Authority Trust Root

### OBSERVED
- Rev-2 Issuer Contract C1-C7:`validator` 非空(H1)、human_review 不得以 `"gate/"` 开头(H2)、非 human_review 必须以 `"gate/"` 开头(H3);C7 明示"不要求 IAM;validator 真实性由后续 Phase 验证"。
- 生产点现状(`candidates.py` L58-64):`verified_by` 硬编码 `"human"`,`reviewer_id` = 请求体字符串,端点无认证。
- ValidationEvent 与 review_trail 之间**零绑定字段**(OBSERVED:`models.py` L184-191 无 review_trail 引用;`snapshot.py` L64 review_trail 无 event 引用)。

### ATTACK(A-3-4,BLOCKER)
- **C2-C4 就是"非空字符串 + prefix = trusted",即 Owner 明令禁止接受的形态**。H2 只能阻止字面 `"gate/"` 前缀;攻击者提交 `validator="张三"` 或任意非 gate 字符串即获得 human authority,无需任何身份证明。前缀约束防的是**误标**,不是**冒充**——任何人不需要冒充即可通过 H2。
- C7"真实性由后续 Phase 验证"与"后续 migration 解决"同构 → 按 DEC-015 红线 = **UNPROVEN,不能计为已回应 RDQ-003**。

### ATTACK(A-3-5,BLOCKER)
- **review_trail ↔ ValidationEvent 绑定缺失**:Rev-2 的 issuance_event(C5)"ValidationEvent 本身就是 issuance 记录"对自动路径成立,但人工路径的 issuance 记录是 review_trail 条目,两者无任何交叉引用机制(字段、投影规则、写入顺序均未定义)。事件真实性(event authenticity)无锚:无法证明某 ValidationEvent(human_review)对应哪次人工审查。

---

## T4. Two Boundary Independence(IR Boundary / Admission Boundary)

### OBSERVED
- Rev-2 B4:"Authority 检查点在 Admission Boundary,不在 IR Creation";Phase 3 标题为"IR Admission(Authority Consumer):Admission 检查"。
- Rev-1 的双 Boundary(IR Boundary 6 条件 + Admission Boundary 4 检查)在 Rev-2 中**只剩一个检查点**;Rev-2 未保留任何 IR 层 Authority 检查,也未说明 "IR Admission" 与 Knowledge Asset Admission 是同一个还是两个。

### ATTACK(A-3-6,BLOCKER)
- **双层防线已被消解,且与 DEC-013 相抵触**。DEC-013 原文:Authority 必须作为 "**Semantic IR** 与最终 Knowledge Asset Admission 的准入前置条件"——两个前置。Rev-2 以解除冷启动为名把检查点从 IR 层移除(B1"IR 是 provisional artifact"),等于把 Owner 裁决改写为单前置。要么 Rev-2 明示 provisional IR 在获得 Authority 前**不可被任何下游消费**(并给出该约束的 enforcement 位置),要么承认偏离 DEC-013 请 Owner 裁决——不能静默改写。
- 即使接受单检查点,Independence 论证仍缺:Authority 由**同一次 evaluate 产生、同一进程、同一 run 内**被 Admission 消费(`service.py` L183-246 顺序调用)——同源 event、同源投影、无独立触发。这是 **duplicate check(同一判定查两遍),不是 independent enforcement(两套独立机制互为防线)**。Rev-2 全文未使用 independence 论证,也未撤回 Rev-1 的相关主张,状态不明。

### UNPROVEN
- "Phase 3 IR Admission"作为独立于 Knowledge Asset Admission 的关卡:代码中不存在该关卡(OBSERVED:approve() 是唯一准入入口,`admission.py` L63-114),设计未给出其位置与独立性来源 = UNPROVEN。

---

## T5. Lifecycle

### OBSERVED
- 状态机(`models.py` L232, L293-304):REJECTED / INVALIDATED 为 terminal;VALIDATED → 仅许 INVALIDATED;terminal 后 append 任何事件抛 ValueError。**无 re-grant 路径**。
- Rev-2 未解决项表**未提及** invalidation 触发者、re-grant、invalidation 持久性(OQ-2/OQ-3 降为 NOTE,AuthoritySnapshot 归"实现后补")。
- ledger per-run 内存(见 T1):invalidation 事件随进程消失。

### ATTACK(A-3-7,BLOCKER)
- **Invalidation 不持久 → replay 洗白**:人工 INVALIDATED 后重跑同一逻辑执行——fresh 内存 ledger 无历史 → claim 直接重新 validated → Authority 复活。生命周期在此设计下**不闭合**:撤销可被 replay 无痕逆转。"replay 后状态是否确定"的答案按当前设计 = **不确定**(取决于进程内存状态)。
- 谁触发 invalidation:Rev-2 零定义(继承 Rev-1 未回应,RDQ-004 遗留)。

### UNPROVEN
- re-grant 路径:Rev-2 未设计 → INVALIDATED 终态下同 candidate 修复后无法重新授权(继承 Rev-1 V6 PARTIAL,无改进)= UNPROVEN。

---

## T6. Identity Binding

```
AuthorityIdentity = (source_version_id, candidate_id, claim_id)
```

### OBSERVED
- ValidationEvent 字段(`models.py` L184-191):event_id、claim_id、validation_result、checks、validation_method、validator、reference_ids、validated_at。**无 candidate_id、无 source_version_id、无 run_id**。
- claim_id 实际取值 = `root.unit_id`(`service.py` L195-197),**文档本地字符串**(如 "Q1")。
- source_version_id 存于 candidate(`snapshot.py` L51-53),le_hash 不含 source_version_id(经 annotation_id 间接锚定)。

### ATTACK(A-3-8,BLOCKER)
- **三元组无法从事件重建**:AuthorityIdentity 含 candidate_id,但 ValidationEvent 不携带 candidate_id/source_version_id。ledger 一旦跨 run 持久化(设计必需),claim_id="Q1" 在全局 ledger 中**跨文档撞号**(每份文档都有 Q1),无法唯一反查所属 candidate → Identity Match 检查不可执行。要修复必须给 ValidationEvent 加 candidate_id/source_version_id 字段——这正是 DEC-015 红线句式("实现阶段再增加字段")→ **UNPROVEN,计为未回应**。
- claim collision(同 candidate 内):candidate 本身按 unit 粒度创建(le_hash 含 unit_id),同 candidate 内 claim_id 恒定单值 → 无碰撞,但 claim_id 维度由此**冗余**(NOTE,非阻断)。

### ATTACK(A-3-9,WARNING)
- **evidence mutation 防线依赖上游不变性而非 Identity 自身**:annotation_payload_hash 经 `_annotation_identity_projection` **剔除 line_refs**(`service.py` L287-296 注释:Semantic Identity 不含 Source Binding Claim)。Authority 三元组不含 resolver_input_hash(含 line_refs)。当前靠 annotation 行 append-only(OBSERVED:snapshot 表 append-only,`snapshot_repository.py` L158-160)兜底——换 line_refs 必须新 annotation_id → 新 le_hash → 新 candidate,攻击不可达。但该防线是**数据层惯例,不是 Identity 设计属性**;一旦出现任何 payload 可变路径(如 migration 回填),Authority 静默覆盖变更后的 evidence。标记 WARNING 并要求 Rev-2 显式声明该依赖。

---

## 汇总

| 方向 | 结论 | 关键项 |
|---|---|---|
| T1 Bootstrap | 部分成立 | 自动路径循环已破(VERIFIED);人工路径生产机制缺失 + 持久化 UNPROVEN |
| T2 Run Identity | **FAILED** | A-3-2: I2 与 ON CONFLICT DO NOTHING 矛盾,replay 证明失效,cross-run transfer 按构造发生;A-3-3 状态机矛盾回归 |
| T3 Trust Root | **FAILED** | A-3-4: prefix = 被禁止形态;C7 = 后续 Phase(UNPROVEN);A-3-5 绑定缺失 |
| T4 Independence | **FAILED** | A-3-6: 单检查点与 DEC-013 双前置抵触;同源同 run = duplicate check |
| T5 Lifecycle | **FAILED** | A-3-7: invalidation 不持久,replay 洗白;触发者/再授权零定义 |
| T6 Identity Binding | **FAILED** | A-3-8: 三元组无法从事件重建(candidate_id 字段缺失,claim_id 跨文档撞号) |

### 成立部分(公平陈述)
1. 自动路径 Bootstrap 的 Producer/Consumer 分层正确,循环依赖在该路径上确实解除(T1 VERIFIED);
2. 把候选身份问题从"run 语义"重述为"逻辑执行身份"的方向是对的——只是 Rev-2 没有意识到自己的设计已经指向 (stage, le_hash) 而非新 UUID;
3. issuer_type 从 validation_method 确定性派生(C1)是干净的消除歧义设计;
4. 本轮文档**已 commit**(9bf8878),审查锚定纪律首次完全满足。

### BLOCKER 清单(进入 DEC-013 终裁前必须解决)
1. **B3-01(T2)**:Run Identity 建立在与代码矛盾的假前提上;replay/cross-run 证明失效,状态机矛盾回归;
2. **B3-02(T3)**:人工信任根仍是默认可信(前缀约束 + 后续 Phase),review_trail↔ValidationEvent 无绑定;
3. **B3-03(T4)**:双 Boundary 消解与 DEC-013 双前置抵触;同源同 run 消费无 independence;
4. **B3-04(T5/T6)**:Authority 持久化缺失使生命周期不闭合(invalidation 可被 replay 洗白),且 AuthorityIdentity 无法从 ValidationEvent 重建(修复 = 加字段 = UNPROVEN 红线)。

### REQUIRED_DECISION(提请 Owner)
- **RD-A**:Rev-2 B4 将 IR 层检查移除是否偏离 DEC-013"Semantic IR 准入前置"?若是,请 Owner 裁决 provisional IR 的下游消费禁令要求;若否,请 Owner 明示"IR Admission"与 Admission 的关系。
- **RD-B**:持久化(ledger 入库)应升格为 Rev-3 的**设计义务**(定义 schema/身份字段/invalidation 语义)而非实现期事项;是否同意按此门槛受理 Rev-3?

---
*Review-3 执行:DSH · 2026-09-15 · 零代码修改 · 输出限定 OBSERVED/VERIFIED/ATTACK/UNPROVEN/REQUIRED_DECISION*

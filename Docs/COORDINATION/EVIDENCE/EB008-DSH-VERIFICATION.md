# EB-008 Revision-1 Evidence Audit

> 审查对象:`D:\Project\AITutors-v3\Docs\DECISIONS\88_EB008_EVIDENCE_AUTHORITY_ENFORCEMENT_REVISION1.md`(v1.0.0-revision1),sha256 = `2AEA1A81B1F1B5EA47CB3A97968225B5AD07B4EA439DCF4544BC0365A0229250`
> 状态:**未 commit(`??`)→ REPORTED 级**;本审计结论对该 sha 的文本成立,文本变更须重审。
> 审计原则(Owner 指令):只接受 OBSERVED Evidence;拒绝设计意图 / 未来实现计划 / "应该如此" / "理论可以"。
> 执行:DSH,2026-09-15。证据全部为 V3 工作树代码亲读 + 对 doc 88 的机器检索。

**台账级 OBSERVED(先于 V1–V7)**:
- doc 88 `Derives From` 列出 "DSH adversarial review FACT-025~028" = 回应对象是 **Review-1(handoff 008)**;**Review-2(handoff 009)的 RDQ-1~11 未列为派生源**;
- id 纪律未修(R2-P2 重犯且加重):§1.1/§1.3 用本地 FACT-012~024(与 canonical FACT-012~024 全部撞号,如 §1.3 "FACT-021 = EvidenceReference.source_version_id" vs canonical FACT-021 = P3.2 bypass 实锤),§0/§1.2 又用 canonical FACT-025~028——**同一文档内两套编号体系混用**;
- D3 依据表引用 "Owner 裁决:「Human Review 不直接等价 Authority,而应通过统一机制产生 Authority」"——Owner 原文为 "'human review 可以进入 Admission' 不能直接推出 'review_trail 本身就是 Evidence Authority'";后半句为设计方引申,非 Owner 原话,该依据行效力降级。

---

## V1 RDQ-1 Cold Start

**Claim**(doc 88):D7 定义 IR Boundary 六项必要条件(含"每个 EvidenceReference 都有至少一个 ValidationEvent""latest = validated""run_id == 当前 run_id"),Revision-1 声称解决 Revision-0 经 DSH review 发现的四个问题(§0 表)。

**Evidence**:
- 机器检索 doc 88 全文 `冷启动|bootstrap|首次运行|first run|循环依赖` = **0 命中**;
- §0 变更摘要四行仅列 FACT-025~028,**无 RDQ-1 条目**;
- D7 条件原文 L355-360(尤其条件 2/3/5);
- 生产顺序(OBSERVED,`service.py` L171-197):IRBuilder.build → Compiler → evaluate → record_validation。

**Verification**:自动路径唯一的 ValidationEvent 生产者 `record_validation` 的输入是 gate evaluate,evaluate 依赖 IR + Compiler;D7 条件 5 进一步要求事件 `run_id == 当前 run_id`,即**前 run 的事件也不计入**——冷启动 ledger 为空 → IR 无法 ready → 无 candidate → 人工路径无对象 → 无任何事件生产者,死锁闭合,且从冷启动扩展到**每一个 run**。Revision-0 的循环依赖(RDQ-1)在 Revision-1 中未被回应,亦未被缓解。

**Result: FAILED**

---

## V2 RDQ-2 Run Semantics

**Claim**(doc 88 D4/D5/D8):四元组含 run_id(MUST);Admission Identity Match 检查 `latest.run_id != current_run_id`;replay 确定性;handoff 004 称 FACT-025 已 resolved。

**Evidence(OBSERVED)**:
- `approve()` 签名无 run 上下文(`admission.py` L63-68,自动/人工同函数);API approve 端点无 run 参数(`candidates.py` L47-74);
- candidate schema 无 run_id 列(`models/snapshot.py` L42-64,仅有 attempt_id 且段 H 接入前恒 NULL);
- `current_run_id` 全文唯一出现处 = D8 伪代码 L426,**无来源定义**;
- 状态机冻结规则(`models.py` L293-304):REJECTED/INVALIDATED terminal;VALIDATED → 只许 INVALIDATED;doc 88 全文无状态机修改主张。

**Verification**:Run A approved → approve no-op 早退(`admission.py` L77-78),check 不触发(无害);**Run A pending → Run B 重跑 same candidate**:`record_validation(validated)` 撞 "VALIDATED → 只许 INVALIDATED" → **ValueError 崩 run**(Review-2 R2-A2-2 原攻击,Revision-1 零回应);different candidate(payload 变 → 新 le_hash → 新 candidate_id → 新事件键)隔离成立 ✓;**人工 approve 时 `current_run_id` 无来源** → Identity Match 第三行在人工路径不可执行。

**Result: FAILED**(same-candidate replay 冲突未解;run_id 检查输入未定义)

---

## V3 RDQ-4 Human Authority

**Claim**(doc 88 D3):选择 B(human review → ValidationEvent(human_review) → projection → Authority)+ Issuer Contract 四条件;handoff 004 称 "Issuer contract defined"。

**Evidence**:
- D3 条件 2 原文:"reviewer_id 必须是已认证的 reviewer(identity 来源待定义——OPEN QUESTION)";
- OQ-1 原文:"建议 Phase 1 接受任意非空字符串,Phase 2 引入认证";
- 条件 4:"签发动作本身是确定性的(从 review_trail entry 投影为 ValidationEvent)";
- review_trail 生产点现状(OBSERVED,FACT-027,未变):API 硬编码 `verified_by="human"`,reviewer_id = 请求体字符串,confirmed_fields 不校验(`candidates.py` L58-64);`_has_human_approve` 不看 confirmed_fields(`admission.py` L450-456)。

**Verification**(四步逐项):
1. **issuer identity**:依赖"任意非空字符串"(OQ-1 Phase 1 建议)= **默认可信**;
2. **review authenticity**:投影输入 = 原样继承的无认证 review_trail 生产点,FACT-027 未修——伪造 entry 即伪造事件;
3. **event creation condition**:条件 3(confirmed_fields 覆盖全部 content role)无验证机制,条件 2 依赖第 1 步;
4. **authority derivation**:投影确定性(机械部分)合格 ✓。

按 Owner 规则:第 1、2 步依赖"默认可信" → 整链 FAILED。issuer contract 是**纸面四条,其中一条自认 OPEN、一条的输入可伪造**。

**Result: FAILED**

---

## V4 Identity Binding

**Claim**(doc 88 D4/D5):AuthorityIdentity 四元组 (source_version_id, candidate_id, run_id, claim_id) 存在、强制、可验证、不可绕过。

**Evidence(OBSERVED)**:
- 代码现状:`ValidationEvent` 字段 = {event_id, claim_id, result, checks, method, validator, reference_ids, validated_at}(`models.py` L184-191 亲读复核)——四元组字段**均不存在**;
- D5 "不可伪造条件"原文:"candidate_id / source_version_id / run_id 由产生 ValidationEvent 的上下文自动填充,不由调用方传入"——填充器、写入路径、强制机制**全文无定义**;
- D8 伪代码 L416-423:`events = db.load_validation_events(candidate.id, unit_id)` **按 candidate_id 过滤**,随后检查 `latest.candidate_id != candidate.id`——**恒真同义反复,该行零信息量**;
- ledger append 无授权检查(Review-2 R2-A5-1,Revision-1 仅重申"任何模块不得手动创建",无机制)。

**Verification**:存在 = 设计层成立 / 代码层不存在;强制 = 未证(写入器未定义);可验证 = source_version 行可执行、candidate 行恒真、run 行输入未定义(V2);不可绕过 = 未证。

**Result: PARTIAL**(四元组定义本身是实质改进;但 强制/不可绕过/两项可验证性 均无证据支持,且伪代码含恒真检查)

---

## V5 Join Correctness

**Claim**(doc 88 D5):ValidationEvent 直接携带 candidate_id;按 (candidate_id, claim_id) 分组;join = event.candidate_id == Candidate.id AND claim_id ∈ payload units。

**Verification**:两 candidate 同 claim_id 攻击——设计语义下 candidate B 的加载路径按其自身 candidate_id 过滤,**读不到** candidate A 的事件,错误共享在设计层不可构造 ✓;但防线全部重量压在写入端"自动填充"(V4:机制未定义)与 ledger 写入授权(R2-A5-1:无)之上——写入端未强制前,该 join 的不可伪造性不可证;代码层碰撞(FACT-025)现状未变。

**Result: PARTIAL**(设计层闭合,写入端强制未证)

---

## V6 Lifecycle

**Claim**(doc 88 D6):Authority = projection,不直接持久化,从 DB events 重算;restart/replay 确定性;source re-seal → 批量 INVALIDATED;candidate immutability 为前提。

**Verification**(逐能力):
- **restart**:确定性重算机制自洽,无新假设 ✓(设计意图,但机制无隐藏依赖);
- **replay**:确定性 ✓;但 same-candidate 重跑撞状态机(V2 同根,零回应);
- **invalidation**:触发条件点名(re-seal)但**执行者与机制未设计**("批量 append" = 计划,非设计,Review-2 RDQ-6 只回应一半);且 `_TERMINAL_STATES = {rejected, invalidated}`(`models.py` L232)——**INVALIDATED 为 terminal,REVOKED 后同一 (candidate, claim) 无法再 GRANT**;re-seal 场景可由"新 source_version → 新 candidate → 新键"绕开,同 candidate 修复场景无出路,Revision-1 lifecycle 表(§D6)无 re-grant 行;
- **mutation**:candidate payload 冻结 = 现状 OBSERVED 成立(无应用层写路径)✓。

**Result: PARTIAL**(restart/mutation 合格;re-grant 缺位 + invalidation 执行者未设计)

---

## V7 Boundary Independence

**Claim**(doc 88 D9 + handoff 004):"Proven independent"——IR Boundary 查 evidence 链(compile 阶段),Admission Boundary 查 candidate identity+validity(admission 阶段),不同 failure mode。

**Verification**:两层确为**不同 invariant**(时机/粒度/检查内容/失败语义四维不同,✓ 成立);但 "independent/Proven" 过强:
1. 两层消费**同一 ValidationEvent ledger**(同表、同投影规则);
2. auto 路径事件与 gate_decision **同根于同一次 evaluate()**(FACT-028 原攻击,Revision-1 未引入任何独立第二计算);
3. ledger 级攻击(伪造事件 / 写入器未授权 / V2 的 run 输入未定义)使**两层同时失效**。

"如果 IR Boundary 被绕过,Admission Boundary 仍能拦截"(D9 论点 3)成立的前提恰是 ledger 写入端可信——该前提未证(循环论证)。证据只支持"两层是不同检查",不支持"两层是独立防线"。

**Result: PARTIAL**(handoff 004 "Proven independent" 措辞不成立,须降级)

---

## V8 Final Recommendation

**DECISION: REQUIRES_REVISION**

终裁阻断项(必须先解决):
1. **V1 冷启动死锁(致命)**:RDQ-1 零回应,D7 条件 5 使死锁扩展到每个 run;
2. **V2 run 语义**:same-candidate 重跑状态机冲突未解 + `current_run_id` 在人工 approve 路径无来源;
3. **V3 人工 authority 默认可信**:issuer contract 依赖"任意非空字符串"+ 无认证投影输入,整链 FAILED。

非阻断但须修正:V4 恒真检查与写入器机制、V6 re-grant 路径与 invalidation 执行者、V7 "Proven independent" 措辞降级、id 纪律(doc 88 内两套编号混用)、doc 88 + handoff 004 **commit**(REPORTED → 可验证)。

成立部分(不因阻断项埋没):Authority = Projection 的抽象修正(D1/D2)、candidate_id 直接绑定的 join 设计(D5)、AuthoritySnapshot 冻结意图(D7)、双入口统一机制图(D10)——方向与 DEC-013 一致,问题集中在**循环依赖未破、运行时输入未定义、信任根未立**三处。

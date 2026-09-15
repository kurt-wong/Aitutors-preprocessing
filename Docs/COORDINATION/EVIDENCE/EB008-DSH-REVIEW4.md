# EB-008 Review-4 — Rev-3 对抗验证(Owner 四项冻结决策逐项核验)

- **Reviewer**: DSH(Preprocessing)
- **Date**: 2026-09-15
- **审查对象**: V3 commit `a80d55517950982c42c81ff63c1afaf2083c9f94`(COMMITTED 级)
- **文档**: `Docs/DECISIONS/90_EB008_EVIDENCE_AUTHORITY_ENFORCEMENT_REVISION3.md`(614 行)
- **文档 sha256**: `2ED71A2BA5D3322650F99E0C12F5ACA10A6E7BA94FEC8333C6269F838715E566`
- **任务约束**: 非重设计;判据 = 是否符合 Owner 业务模型(不因不用 IAM 判失败,不因 run_id 不存在判失败)
- **VERDICT**: **VERIFIED — 无 BLOCKER,具备进入 DEC-013 终裁的条件(待 Decision-4 收口)**

---

## ① Identity Model(Run = Process / Candidate = Entity)

### OBSERVED
- `gate/service.py:214-216` find-then-reuse;`models/snapshot.py:46-48` `UniqueConstraint(logical_execution_stage, logical_execution_hash)` — Rev-3 引用与代码逐行一致;
- le_hash 输入(`service.py:279-296`)= `annotation_id + annotation_payload_hash(_annotation_identity_projection 剔除 confidence+line_refs)+ unit_id`;**不含 run_id / attempt_id / 时间戳**;
- Rev-3 §3 I1-I7:"Run 是 conceptual entity,不是 database entity"、"跨 Run 复用是 by design(Decision-1)"。

### VERIFIED
- Run(Process)与 Candidate(Entity)区分正确,与 Owner 冻结模型一致;
- Authority 不依赖 run_id(I5);R1-R5 replay 语义自洽:同 hash → 同 candidate → 同 AuthorityIdentity,replay = no-op;
- Review-3 B3-01("每 Run 新 UUID"假前提)被正确**删除而非辩护**;
- hash 无时间戳/attempt 漂移源。

### ATTACK
- WARNING(非 Rev-3 之过):hash 剔除 `line_refs` 与 70 号 OQ-1 Gate A 冻结决策一致(Semantic Identity 不含 Source Binding Claim);恢复路径 L2 靠 annotation_id 变化产生新 Entity,闭环成立。声明完整性建议:Rev-4 显式引用 70 号作为剔除依据。

## ② Human Authority(Review Proof Token)

### OBSERVED
- `gate/admission.py:450-456` `_has_human_approve` 无 proof 验证(Rev-3 引用准确);
- 全库 grep `APP_SECRET|app_secret` 零命中 → proof 机制为纯新增设计(设计文档阶段合规)。

### VERIFIED(Owner 五项检查逐项)
| 检查项 | Rev-3 落点 | 判定 |
|---|---|---|
| 绑定 candidate identity | proof 含 `candidate_id` | ✅ |
| 绑定审核内容 | 含 `review_result`;内容经 candidate_id 间接锚定(candidate payload 创建后冻结) | ✅(间接) |
| 绑定时间/action | 含 `reviewed_at` + `review_result` | ✅ |
| 可 replay | 确定性 SHA256(canonical_json),可从存储字段重算 | ✅ |
| 可验证 | Admission Boundary 重算比对,不匹配 → fail-closed | ✅ |

**Owner 直接提问"数据库被复制,token 是否还能错误关联?"** 三分:
1. DB 复制到另一部署、无对应 `.env` → proof 重算不匹配 → human Authority 全部无效 → fail-closed(pending_review),**不会错误关联,只会保守拒绝** ✅;
2. DB + `.env` 整套复制 → proof 依然有效,属"部署环境整体被克隆",Rev-3 已显式标记超出威胁模型(Deployment Environment Boundary),与 Owner 接受的弱信任模型一致;
3. DB 内直改 `review_trail` 伪造 approve → 无 APP_SECRET 无法生成合法 proof;Authority 判定以 `validation_events.review_proof` 为准,review_trail 降级为审计记录 ✅。

### ATTACK
- WARNING:proof 粒度 = candidate 级,ValidationEvent 粒度 = claim 级;同 candidate 内一条 human approve proof 可复用于该 candidate 任意 claim 事件。家庭场景人工审核为整卷操作,风险可接受,但 Rev-4 应显式声明"proof 粒度 = candidate 级"。
- WARNING:`candidates.py` approve 端点无认证、`reviewer_id` 自由字符串——proof 防"绕过系统的 DB 直改",不防"走正规 API 的未授权调用"。与 Deployment Environment Boundary 自洽,但信任边界段应把"API 层访问控制缺失"明列为不防御项(当前仅列 APP_SECRET 泄露)。

## ③ Evidence Persistence

### OBSERVED
- `evidence/promotion.py:207-209` in-memory 属实;Rev-3 §5 **主动标记其违反 Decision-3**(自曝);
- `validation_events` schema 含 `candidate_id` FK + `source_version_id` + `claim_id`,双 INDEX,INSERT-only + 状态机(`models.py:268-304`)移至写 DB 前调用;
- Authority = latest-event 确定性投影,非独立存储。

### VERIFIED
- INVALIDATED 防洗白成立:持久化后 replay 遇 VALIDATED = no-op(R3),遇 INVALIDATED/REJECTED = 终态不复活(R5)——Review-3 B3-04"fresh 内存洗白"攻击面消除;
- 无事件 → Authority = none → fail-closed;
- claim_id 跨文档撞号因 candidate_id 入表而消解(事件按 (candidate_id, claim_id) 定位)。

### ATTACK
- NOTE:DB 层 append-only 触发器推迟 Phase-1——Rev-3 明确标记 trade-off 并列入风险表,schema/投影/状态机均已在设计期定死,**不触发 DEC-015"实现阶段再决定"红线**。

## ④ IR Boundary

### OBSERVED
- `compile/ir.py:1-2` "transient;span 只存 id" — Rev-3 职责解释与代码一致;
- grep `ir_snapshot` 仅 payload 构建 + admission 消费两处 → "IR 当前只流向 Admission"属实;
- Rev-3 §7:职责四条(装配/验证/Gate 输入/冻结)+ Option A/B 对比 + 显式不预设结论。

### VERIFIED
- 符合 Owner 指令(先解释职责、再对比方案);Option A 冷启动死锁分析与 Review-3 已 VERIFIED 的 bootstrap 事实一致;Option B 与当前 pipeline 顺序一致且无循环依赖;
- Option B 已知弱点(IR 可含未验证 evidence)自列,并给出重评触发条件("IR 出现 Admission 之外的消费者")——诚实设计。

### ATTACK
- 无新增。(Decision-4 最终裁决见 DEC-016:Owner 选定 Option B。)

---

## 汇总

- **BLOCKER: 0**
- **WARNING: 3**(proof 粒度声明 / API 层不防御项声明 / line_refs 剔除依据引用)——均为声明完整性问题,并入 Rev-4 与实现期清单,不阻断;
- **NOTE: 1**(DB 触发器 Phase-1 trade-off,合规)。

**REQUIRED_DECISION(已由 Owner 裁决,DEC-016)**:Decision-4 = **Option B**——IR 可先生成但非可信知识资产;Authority = 进入 Question Knowledge Layer 的必要条件。

**结论**:Rev-3 正确实现 Owner Decision-1~3 及 Decision-4 的分析要求,无 BLOCKER;Rev-4 按 DEC-016 合入 Option B 终稿后,Review-5 执行最终一致性审查,通过即建议进入 DEC-013 终裁。

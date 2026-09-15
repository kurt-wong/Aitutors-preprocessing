# EB-008 Review-5 — Rev-4 最终一致性审查(Decision-4 Option B 合入核验)

> **[ARCHIVED 2026-09-15]** Owner 已确认本审查结果(DEC-017):四项核心设计方向全接受,三条信任模型声明固化(proof 粒度 candidate 级 / API 访问控制不在当前威胁模型 / APP_SECRET 泄露属 Deployment Environment Boundary)。EB-008 → DECIDED 候选,等 DEC-013 最终裁决。本报告结论即终审结论,不再迭代。

- **Reviewer**: DSH(Preprocessing)
- **Date**: 2026-09-15
- **审查对象**: V3 commit `2ad6f99342ce6a75a843980d619a164b05579b5c`(COMMITTED 级)
- **文档**: `Docs/DECISIONS/91_EB008_EVIDENCE_AUTHORITY_ENFORCEMENT_REVISION4.md`(408 行)
- **任务约束**: 最终一致性审查,非重设计;Owner 五检查点;无 BLOCKER → 建议进入 DEC-013 终裁
- **FINAL VERDICT**: **VERIFIED — 无 BLOCKER。建议进入 DEC-013 终裁**(附 4 项 WARNING 与 1 项台账修正,均不阻断)

---

## 检查点 1:IR 是否被错误描述为可信事实

### OBSERVED
- §2:"**IR 本身不代表事实可信**"(独立加粗声明);
- §2 非属性表:"不是知识资产 / 不是 Authority 载体 / 不是最终产物 / **不是可信声明**——IR 内容的可信性由 ValidationEvent → Authority 表达,不由 IR 自身表达";
- §1 D4-2:冻结规则原文"IR 不是可信知识资产";
- §2 "已删除的描述"段:显式声明"Rev-4 中不存在任何要求 IR 先获得 Authority 的设计",Option A 仅存于 §7 历史注记(被否决方案)——Owner 五条要求第 1 条(删除所有暗示 IR 须先获 Authority 的描述)已执行。

### VERIFIED
✅ 全文 408 行无任何"IR 可信/IR 已验证/IR 是知识"形态表述;IR = Intermediate Representation 三职责(结构化原始材料/Gate 输入/后续编译输入)与代码一致(`compile/ir.py:1-2` transient;`payload.py:59` ir_snapshot 冻结;gate 消费)。

### ATTACK
- NOTE:§13 标题笔误"DSH Review-4 攻击目标"应为 Review-5/终审,纯编号瑕疵。

## 检查点 2:Admission Boundary 是否仍阻止 unvalidated IR 进入 Question

### OBSERVED
- §3 Boundary 双层定义:IR Layer(无 Authority 要求,provisional 允许)/ Question Knowledge Layer(`Authority == VALIDATED` 唯一入口条件 + human_review 附加 proof 验证;`Admission.approve()` 唯一入口);
- §4 执行机制:approve() 五步检查(query events → 投影 → 非 VALIDATED → RepositoryError → fail-closed → pending_review;human_review → proof 验证;全过 → 物化);
- §3 流程图:"无 Authority 的 IR 永远停留在 IR Layer,不产生 Knowledge Layer 实体";
- 代码现状(`admission.py:63-114`):approve() 当前**无** Authority 检查(仅 gate_decision/review_trail 校验)——属实现期缺口,EB-008 为 L2 设计阶段,设计已定死执行点与失败行为,符合 DEC-015 红线边界(schema/检查步骤/失败语义均已在设计期规定,非"实现阶段再决定")。

### VERIFIED
✅ Owner 五条要求第 3、4 条完整落实:双 Layer Boundary 定义 + 未验证 IR 权限边界(可存在/调试/重新编译/Gate 评估/失败重试;禁入 Question 实体/禁被下游消费/禁被当知识资产引用);enforcement 执行点唯一且明确。

### ATTACK
- WARNING-R5-01:"禁止被下游学习系统消费/被当作知识资产引用"的执行点标注为"系统边界/使用约定"——文档级约束,无代码 enforcement。已列入 Rev-4 风险表 #3,与家庭系统单机部署形态匹配;若未来 IR 暴露任何导出 API,须按 Rev-4 自设触发条件重评。可接受。
- NOTE:approve() 拒绝路径措辞 `RepositoryError` ——语义上属策略拒绝而非仓储错误,实现期建议区分异常类型(不影响设计正确性)。

## 检查点 3:Authority Projection 是否完整(ValidationEvent → Authority → Admission)

### OBSERVED
- §5.1 投影定义:`Authority(candidate_id, claim_id) = latest ValidationEvent.validation_result`;无事件 → none(fail-closed);
- §5.2 生命周期状态机:六条转换 + INVALIDATED 专用恢复路径(新 evidence → 新 Entity → 新 VALIDATED,旧 claim 保持终态);
- §5.3 时机与一致性:on-demand 计算、Phase-1 无缓存、同 DB 事务内一致(approve 单事务)、完全可重建(丢失投影 = 重新查询);
- §5.4/5.5 消费点:Admission Boundary 唯一 enforcement 消费者;Gate/Human Review 只生产事件不读投影;IR Layer 不涉及投影——生产/消费无循环;
- 与 `evidence/models.py:232` `_TERMINAL_STATES = {rejected, invalidated}` 一致。

### VERIFIED
✅ 链条完整:事件(append-only,§10 表含 candidate_id/source_version_id FK)→ 投影(确定性 latest)→ 消费(唯一 enforcement 点)→ 物化;每环有定义、有时序、有失败语义。Owner 五条要求第 5 条(Authority Projection 生命周期)完整补充。

### ATTACK
- NOTE:§5.6 表"Source 变更 → validated → invalidated"未指明触发者(哪个组件执行 System invalidate)。Rev-3 已把 invalidation 列为设计义务、validator="system/v1" 已定义,触发机制归实现期可接受;建议实现清单明列"source 变更 → 级联 invalidate 扫描"。

## 检查点 4:Replay 语义(同 hash → same Question + same Authority)

### OBSERVED
- 继承 Rev-3 R1-R5(§0 显式声明继承不变):同 le_hash → 复用 candidate → 同一 AuthorityIdentity;replay 不改变 Authority;VALIDATED 重复 append = no-op;INVALIDATED/REJECTED 终态不复活;
- §5.6:"Replay(同输入)→ 投影不变(幂等 no-op)→ 投影稳定";
- §8 Lifecycle 与 Rev-3 §11 一致,补入 Boundary 流转语义。

### VERIFIED
✅ Owner Decision-1(同 hash = same Question Entity)与 replay 语义在 Rev-4 中自洽保持;检查点 4 通过。

### ATTACK
- 无新增(相关攻击面已在 Review-3/4 两轮清零)。

## 检查点 5:Human Review Proof 是否满足家庭内部系统可信模型

### OBSERVED
- §1 Decision-2 原文级复述(无 IAM/proof token/绑定+持久化/合法 proof = 可信);
- §3/§4/§6:human_review 路径在 Boundary 检查中附加 proof 验证;
- 机制继承 Rev-3 §4(SHA256 五字段绑定、验证步骤、防 DB 直改、Trust Model = Deployment Environment Boundary)未被 Rev-4 削弱。

### VERIFIED
✅ 与 Owner Decision-2 冻结模型一致;Review-4 已验证的"DB 复制无 .env → fail-closed 保守拒绝"结论继续成立。

### ATTACK(Review-4 WARNING 未合入的核验)
- WARNING-R5-02:handoff 011 要求合入的 3 项 WARNING(W1 proof 粒度 = candidate 级声明 / W2 "API 层访问控制缺失"列入不防御清单 / W3 line_refs 剔除引用 70 号 OQ-1 Gate A)**未合入**(全文 grep 粒度/API 层/访问控制/70 号/OQ-1 零命中;Claude 完成报告亦未声称合入)。判定:三项均为**声明完整性**问题,不改变任何设计语义,降级为实现期文档清单,不阻断终裁;Owner 终裁时知悉即可。

## 台账一致性(附加审查)

- WARNING-R5-03(**跨台账 ID 冲突,提请 Owner 知悉**):Claude 在 V3 state.yaml 注册 `DEC-013` = "Owner business rules (frozen): (1)~(4) Option B",而 preprocessing canonical ledger 的 DEC-013 = "Authority 必须作为 Semantic IR **与** Knowledge Asset Admission 双前置"(更早的方向性裁决)。两者同 ID 异文,且语义上 DEC-016(Option B)**已收窄** DEC-013 的 IR 侧前置(RD-A 之争的最终答案)。若不修正,未来 agent 引用 DEC-013 原文可推出与 Rev-4 相反的结论。**处理**:DSH 侧在 preprocessing ledger DEC-013 加注"IR 前置部分被 DEC-016 Option B 收窄,superseded on IR clause";V3 侧建议 Claude 把该条改名为 DEC-013-AMEND 或引用 DEC-016,避免同 ID 异文。此项为台账卫生,不阻断终裁。

---

## 汇总

| 级别 | 数量 | 清单 |
|---|---|---|
| BLOCKER | **0** | — |
| WARNING | 3 | R5-01(IR 下游消费为文档级约束,风险表已列) / R5-02(handoff 011 的 3 项声明性 WARNING 未合入,转实现期清单) / R5-03(DEC-013 跨台账同 ID 异文,已加注修正) |
| NOTE | 3 | §13 标题笔误 / RepositoryError 措辞 / invalidate 触发者归实现期 |

**FINAL VERDICT:VERIFIED — 无 BLOCKER,建议进入 DEC-013 终裁。**

Rev-1→Rev-4 收敛轨迹:Rev-1(未 commit)→ Rev-2(4 BLOCKER)→ Rev-3(0 BLOCKER,3 WARNING)→ Rev-4(0 BLOCKER;Owner Decision-4 Option B 完整合入,五检查点全过)。设计侧无已知未回应项;实现期入口条件 = 终裁通过后的 implementation 清单(validation_events 表 + proof 机制 + approve() enforcement + invalidate 触发器)。

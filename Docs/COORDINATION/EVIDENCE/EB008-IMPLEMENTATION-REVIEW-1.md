# EB-008 Implementation Adversarial Review-1 — 四域代码攻击验证

> **审查者**: DSH(adversarial validation only;不重设计、不改 V3 代码)
> **日期**: 2026-09-15
> **攻击对象**: V3 commit `88aeae8`(EB-008 Phase-1 实现)+ `b5ddbe3`(EB008-P1-IMPLEMENTATION-NOTES.md)
> **判据**: `EB008-DSH-IMPL-ACCEPTANCE.md`(DEC-018 四验收域)+ Owner 指令四攻击域(Identity / Human Proof / Admission Boundary / Lifecycle)
> **范围边界**: 只验证实现是否符合冻结设计(92号 FINAL `2ad6f99` + DEC-016/017);不重开设计讨论。残余风险按冻结的已接受风险(R-1~R-4)分类,不重复上报。

---

## 0. 执行摘要

```
VERDICT: 实现与冻结设计一致 —— 0 BLOCKER / 2 WARNING / 4 NOTE
FACT-021 基线复跑: P3.2 N1/N2/N7/N8 四向量 全部 BYPASS → 全部 BLOCKED(C-1 验收通过)
攻击测试: 23/23 按预期收敛(21 项攻击被阻断 + 2 项 FINDING 演证成功复现残余风险)
V3 既有验收套件: test_eb008_evidence_authority.py 26/26 通过(DSH 独立复跑)
```

**关键结论**:Owner 四攻击域全部达成验收要求——同 hash 复用 candidate 且 Authority 一致(A);proof 篡改/删除/伪造全部 fail-closed(B);无 Authority 的 approve 全部被拒且无 Question 物化(C);INVALIDATED 不可洗白、Authority 不复活(D)。两项 WARNING 均为**冻结设计已声明边界内的残余风险**(R-3 DB 直连能力 / latest-by-validated_at 排序规则的潜在面),实现未偏离设计,是否需要 Phase-2 处置由 Owner 裁决。

---

## 1. 方法与锚

| 项 | 值 |
|---|---|
| V3 HEAD(攻击时) | `b5ddbe3`(实现 `88aeae8` + 说明文档 `b5ddbe3`) |
| admission.py sha256 | `AD2CC30D...18BC13` |
| proof.py sha256 | `D2026FA9...55B346` |
| evidence_repository.py sha256 | `5F813CEF...584F195` |
| models/evidence.py(ORM)sha256 | `0D71AFA9...19041C7` |
| domains/evidence/models.py(状态机)sha256 | `43C1AD63...40617F5E` |
| 攻击套件 | `Papers/attacks/test_eb008_impl_attack.py`(23 用例,四域)+ `attacks/conftest.py` |
| 运行环境 | Python 3.12.9 / pytest 9.0.3 / PostgreSQL localhost `aitutors`(V3 测试库);每用例 rollback 隔离,跨 session 用例自带 FK 全链清理,终态库内 0 残留(亲验 documents/candidates/events/questions 计数 = 0) |
| V3 仓库状态 | 攻击全程零改动(`git status` 空,亲验) |

方法双轨:**动态攻击**(绕过正常路径直接构造事件/raw SQL 篡改/直连 approve)+ **静态审计**(全树 grep、hash 输入域逐键核对、调用链追踪)。证据分级按 DEC-014:OBSERVED(亲跑/亲读)/ INFERRED(代码链推导,标注)。

---

## 2. 验收域 A:Identity(Owner 攻击域 ①)

| 攻击 | 用例 | 结果 | 证据 |
|---|---|---|---|
| 同输入重复 Gate | A-1 | **BLOCKED 意图达成**:candidate 复用(同 id)、validation_events 恰 1 行(replay no-op)、Authority 投影一致 | OBSERVED |
| 不同 Run replay(新 session/新实例,已 COMMIT) | A-2 | 同 candidate id、恰 1 行事件、投影 `validated` 不变(持久化非内存) | OBSERVED |
| attempt_id 混入身份 | A-3 | 不同 attempt_id 两次 run → 同一 candidate(attempt_id 不进 le_hash) | OBSERVED |
| hash 输入域审计 | A-4 | `input_domain` = {annotation_id, annotation_payload_hash, unit_id};`contract_domain` = 4 个版本号;**无 run/attempt/time/created 任何键**;同输入跨时重算 hash 一致 | OBSERVED |
| claim_id 同源性 | A-5 | Gate 落库 claim == `_candidate_claim_id`(payload `units[0].unit_id`)——enforcement 与落库同源,`payload._ir_snapshot` = `[root] + sub_questions` 保证 units[0]=root | OBSERVED |
| le_hash 公式 | 静态 | `SHA256(canonical_json({task_type, stage, contract_domain, input_domain}))`(hashing.py:65-82);canonical_json 键字典序、禁 float、禁隐式转换 | OBSERVED |

**判定:A-1/A-3/D-1/D-2/D-3 全部通过。** 同 hash 复用 = 设计目标(DEC-017 ①),实现达成。

---

## 3. 验收域 B:Human Proof(Owner 攻击域 ②)

攻击模型:DB 直连能力(R-3 边界内)+ 无 APP_SECRET 攻击者。全部攻击均先落生产等价 human_review 事件(合法 proof),再行篡改。

| 攻击 | 用例 | 结果 | 证据 |
|---|---|---|---|
| SQL 改 validated_at(状态不变) | B-1a | **BLOCKED**:proof 重算失配 → `RepositoryError("proof invalid")`,candidate 保持 pending,0 Question | OBSERVED |
| SQL 改 review_result | B-1b | **BLOCKED 双层**:①`verify_review_proof` = False(声明 2 兑现);②approve 被状态机 terminal 拒(ValueError)——两层独立拦截 | OBSERVED |
| SQL 改 candidate_id(重绑他 candidate) | B-2 | **BLOCKED**:原 candidate 投影 = none → fail-closed | OBSERVED |
| SQL 删 proof(NULL 化) | B-3 | **BLOCKED**:replay no-op 返回既有行 → verify False → `proof invalid` 拒 | OBSERVED |
| 伪造 proof(攻击者自算,错 secret)直插 ORM 行 | B-4 | **BLOCKED**:verify False → 拒 | OBSERVED |
| APP_SECRET 置空 | B-5 | **BLOCKED fail-closed**:`require_app_secret` 抛 RepositoryError(非放行);非 test 环境 main.py:20-21 启动即校验 | OBSERVED |
| proof 生成字段完整性(B-1 判据) | 静态 | 五维齐全(candidate_id/review_result/reviewer_id/reviewed_at/app_secret,proof.py:66-74);canonical_json `sort_keys=True`;验证 `hmac.compare_digest` 恒时 | OBSERVED |
| secret 硬编码/日志泄露(B-4 判据) | 静态 | 全 app 树 grep 无硬编码 secret、无 proof/secret 入 log | OBSERVED |

**判定:B-1/B-2/B-3/B-4 全部通过**,附 F-1(WARNING,见 §7)。

---

## 4. 验收域 C:Admission Boundary(Owner 攻击域 ③)

每个被拒攻击均断言三件套:异常 + `decision_status == "pending_review"`(不自动 reject)+ **Question 计数不变(0)**。

| 攻击 | 用例 | P3.2 基线(FACT-021) | 本轮结果 | 证据 |
|---|---|---|---|---|
| N1:candidate 在、无 ValidationEvent → approve | C-1 | BYPASS | **BLOCKED**(`fail-closed: authority='none'`) | OBSERVED |
| N2:ValidationEvent 在但结果非法(raw 插 `maybe`) | C-2 | BYPASS | **BLOCKED**(state≠validated → fail-closed) | OBSERVED |
| N7:绕过 promotion 直连 AdmissionService.approve(核心) | C-3 | BYPASS | **BLOCKED**;并静态确认 `_materialize` 唯一调用点 = approve(),`create_question` 全树唯一调用点 = `_materialize`(admission.py:122/297) | OBSERVED |
| N8:gate_decision=auto_approve 但 Authority=REJECTED(核心) | C-4 | BYPASS | **BLOCKED** | OBSERVED |
| INVALIDATED 后 human approve | C-5 | — | **BLOCKED**(terminal 状态机拒新事件),0 Question | OBSERVED |
| human approve 无 review_trail entry | C-6 | — | **BLOCKED**(20 §8.2 双入口纪律) | OBSERVED |

**判定:C-1/C-2 全部通过。** `approve()` 内 `_require_evidence_authority` 为**必经路径**(非可选分支,admission.py:118-120 在物化之前);enforcement 机制存在且不可绕——FACT-021 时代的"机制不存在"已闭合。

---

## 5. 验收域 D:Lifecycle(Owner 攻击域 ④)

| 攻击 | 用例 | 结果 | 证据 |
|---|---|---|---|
| VALIDATED → INVALIDATED(annotation supersede 级联) | D-1 | 投影 `invalidated`;approve 被拒;级联事件含 `INVALIDATE_CASCADE` 审计 | OBSERVED |
| INVALIDATED 后 Gate replay | D-2 | **Authority 不复活**:投影保持 `invalidated`;无任何晚于 INVALIDATED 的 VALIDATED 行;无新 approve/物化 | OBSERVED |
| 重复 invalidate | D-3 | 第二次级联返回空、事件恰 2 行(validated+invalidated)、投影不变——幂等 | OBSERVED |
| INVALIDATED 后同结果重放 | D-4 | replay no-op 返回既有行,不新增,不复活 | OBSERVED |
| INVALIDATED 后再 append validated | 静态+既有测试 | 状态机 `ValueError`(terminal),V3 验收套件 `test_invalidate_is_terminal_no_resurrection` 同证 | OBSERVED |
| [演证] 未来时间戳复活(见 F-2) | D-5 | **复现成功**:未来 validated_at 使 cascade 的 INVALIDATED 不是 latest → 投影回 VALIDATED → approve 放行 | OBSERVED |

**判定:A-4 通过(在冻结排序规则内);F-2 记录排序规则的潜在面。** 恢复路径符合设计:INVALIDATED terminal,恢复 = 新 le_hash → 新 candidate → 新 Authority(旧 candidate 不复活)。

---

## 6. 实现期义务对照(7 项逐项)

| 义务(来源) | 状态 | 证据 |
|---|---|---|
| validation_events 持久化(DEC-017 ③) | **DONE** | migration 0011 + ORM + 唯一写入口;A-1/A-2 跨 session 亲验 |
| invalidate 状态机(DEC-017 ③) | **DONE** | `enforce_state_transition` 单一实现,DB/内存共用;D 域全过 |
| replay 稳定性(DEC-017 ③) | **DONE** | 同结果 no-op 返回既有行;A-1/A-2/D-4 亲验 |
| proof 机制 + APP_SECRET 启动校验非空 | **DONE** | B 域全过;main.py 启动校验(非 test) |
| approve() Authority enforcement | **DONE** | 必经路径,N1/N2/N7/N8 全 BLOCKED |
| invalidate 级联触发 | **PARTIAL(设计内)** | annotation supersede 已接(`set_annotation_status` →203);source_version supersede 未接(R-4 已接受:Source 域尚无 supersede 生产流程) |
| DB append-only 触发器 | **Phase-2(已接受 trade-off)** | 应用层 append-only 亲验:全 app 树 grep 无 UPDATE/DELETE validation_events;探针函数恒抛 AppendOnlyViolation |

---

## 7. FINDINGS

### F-1(WARNING)DB 直连可将 human_review 行"洗白"为 machine 外观,绕过 proof 校验

- **复现(B-6 用例,OBSERVED)**:raw SQL 将 human_review 事件改为 `validation_method='byte_proven', validator='gate/v1', review_proof=NULL` 后,`_require_evidence_authority` 跳过 proof 校验(仅对 `human_review` 方法校验),投影 VALIDATED → **approve 成功物化**。
- **攻击者能力要求**:DB 直连写(UPDATE)。同能力下攻击者也可直接 INSERT 伪造 machine validated 事件(machine 事件无 proof 要求)——即 proof 从设计上就不防御"伪造 machine 事件",只防御"篡改 human 行的 review_result / 重放旧 proof"(92号 声明 2 原文范围)。
- **分类依据**:R-3(冻结)明确 "拥有 DB 直连权限者可 UPDATE/DELETE 属 Deployment Environment Boundary";实现行为与冻结设计一致,**非 BLOCKER**。作为声明 2 防护完备性的残余风险记录;Phase-2 DB 触发器落地时该面自然闭合。**是否需要额外处置由 Owner 裁决,DSH 不提设计。**

### F-2(WARNING)`latest-by-validated_at` 排序存在潜在"时间戳复活"面(当前无生产暴露)

- **复现(D-5 用例,OBSERVED)**:经 `append_event` 写入未来时间戳(UTC+1h)的 VALIDATED 事件后,invalidate 级联写入的 INVALIDATED(now)不是 latest → 投影回 VALIDATED → approve 放行。
- **生产暴露面核查(OBSERVED)**:机器事件 `validated_at` = 服务端 `_utcnow`(promotion.py:137-145,不传即默认);人工事件 = `append_review_trail` 服务端强制注入 `{**entry, "time": now}`,**调用方传入的 time 被覆盖**(snapshot_repository.py:253);级联 = 服务端 now。**当前无任何生产路径接受调用方时间输入**,该向量需要 raw 写入或未来 bug 才能构造。
- **分类依据**:排序规则本身是冻结设计(latest-by-validated_at wins,Rev-4 §5),实现忠实;暴露面当前为零。记 WARNING(潜在),不构成当前 BYPASS。

### F-3(NOTE)invalidate 不回溯撤销已完成的 approve 物化

- **观察(D-2,OBSERVED)**:gate auto_approve 在 run 内即 approve+物化;annotation supersede 后 Authority → INVALIDATED,但已物化 Question/Instance 保留,`decision_status` 保持 approved。
- **分类**:冻结设计只规定 Authority 状态与**后续** approve 拒绝,未含 retroactive un-materialization 条款。事实记录,业务预期(失效文档的已入库 Question 是否应下架)由 Owner 定性。

### F-4(NOTE)machine-VALIDATED claim 的人工改判 reject 会撞状态机(INFERRED,未动态复跑)

- **代码链(INFERRED)**:`reject(source=human)` → `_record_human_review(review_result="rejected")` → `append_event` → 状态机:latest=validated 时仅允许 INVALIDATED 迁移 → `ValueError` → reject 失败,candidate 留在 pending_review。触发前提 = claim 已 VALIDATED 但 candidate 仍 pending(例:approve 因 APP_SECRET 缺失等中途失败)。
- **性质**:可得性边缘场景,非 bypass(方向 fail-closed)。恢复路径存在(级联 invalidate 后走新 Entity)。事实记录。

### F-5(NONE)四域全部 BLOCKER 清零

P3.2 基线 FACT-021(N1/N2/N7/N8 全 BYPASS)已闭合;Rev-3 四 BLOCKER(B3-01~04)对应实现全部落地且亲验。本轮无新增 BLOCKER。

---

## 8. 判据纪律自查

- 全部结果标注 OBSERVED / INFERRED,无混写;"后续 migration/再加字段"未作为任何判据的通过条件(DEC-015 红线遵守);
- DSH 未改 V3 任何文件(`git status` 空亲验);攻击套件落在 Papers 仓 `attacks/`;
- 攻击测试对 V3 测试库的 COMMIT 数据已全链清理,终态计数 0(亲验);
- 本报告不包含任何新设计提案;两项 WARNING 的处置(接受/Phase-2 加固/其他)属 Owner 裁决权。

---

## 9. 建议(非设计)

1. **EB-008 P1 实现验收 = VERIFIED(0 BLOCKER,2 WARNING 在冻结边界内)**;实现顺序⑤ 完成,可进入顺序⑥(完整 V3 业务链)。
2. F-1/F-2 由 Owner 定性:接受(现边界)/ 转 Phase-2(DB 触发器 + 排序加固)/ 其他。
3. F-3 业务定性:invalidate 后已物化 Question 的下架策略是否纳入后续阶段。
4. 既有治理遗留不因本轮消失:R5-03 DEC-013 同 ID 异文 + DEC-017/018 同步 V3 台账(handoff 013 再提,仍未处理)。

---

*攻击套件:`D:\Project\Papers\attacks\test_eb008_impl_attack.py`(23 用例)+ `attacks/conftest.py`。复跑命令见套件文件头;V3 既有验收套件 `backend/tests/test_eb008_evidence_authority.py` 26/26 同轮亲验通过。*

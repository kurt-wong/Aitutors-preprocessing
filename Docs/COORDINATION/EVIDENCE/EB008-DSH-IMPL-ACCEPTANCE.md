# EB-008 实现阶段验收标准 — DSH Implementation Adversarial Review

- **Authority**: DEC-018(Owner 2026-09-15,设计冻结 + 实现阶段路线 + DSH 实现期对抗审查指令)
- **Status**: ACTIVE — 实现阶段唯一验收判据来源(与 DEC-017 Owner 点名三项并用)
- **DSH 职责**: Implementation Adversarial Review(代码级攻击验证;**不重设计、不改 V3 代码**)
- **设计依据锚**: V3 `Docs/DECISIONS/91_EB008_..._REVISION4.md` @ `2ad6f99`(sha256 见 EVIDENCE/EB008-DSH-REVIEW5.md)+ DEC-016 四项冻结决策 + DEC-017 确认
- **审查范围边界**: 只验证实现是否符合已冻结设计;**不重开设计讨论**(DEC-018 §①)。实现与设计冲突时 → ATTACK 报告,由 Owner 裁决,不自行改设计。

---

## 实现顺序(Owner 冻结,不可调换)

```
EB-008 Design Frozen(已完成 2026-09-15)
        ↓
① 实现 validation_events
        ↓
② 实现 proof
        ↓
③ 实现 Admission enforcement
        ↓
④ 实现 invalidate
        ↓
⑤ DSH 代码攻击测试(本清单)
        ↓
⑥ 进入完整 V3 业务链
```

每步完成 = commit + 回执 hash(CLAUDE → DSH);DSH 对每步做增量验收,⑤ 为全量攻击测试。

---

## 验收域 A:validation_events 实现(顺序①)

| # | 验收点 | 判据(通过条件) | 攻击手法 |
|---|---|---|---|
| A-1 | 是否真正持久化 | ValidationEvent 落 DB 表(Rev-4 §validation_events schema:含 candidate_id + source_version_id FK);进程重启后事件不丢、Authority 投影可重建 | 写入事件 → 重启服务 → 查询投影;对比内存 EvidencePromotionService per-run log 旧基质(FACT-026) |
| A-2 | 是否 append-only | 无 UPDATE/DELETE 路径;任何代码路径不能改写历史事件 | grep 全树 UPDATE/DELETE;尝试 API/服务层修改已存事件 |
| A-3 | replay 是否稳定 | 同一事件序列 replay → Authority 投影逐字节一致;顺序无关性按设计定义验证 | 打乱可交换事件顺序重放;重复 replay 幂等 |
| A-4 | invalidate 是否可能洗白 | INVALIDATED/REJECTED 为 terminal;恢复必须 = 新 evidence → 新 annotation → 新 le_hash → 新 candidate;旧 candidate 不可复活 | 试图对 INVALIDATED candidate 重放旧 validation / 直接 approve / replay 恢复 authority(Rev-3 B3-04 攻击面) |

## 验收域 B:Review Proof(顺序②)

| # | 验收点 | 判据 | 攻击手法 |
|---|---|---|---|
| B-1 | proof 生成字段是否完整 | SHA256(canonical_json({candidate_id, review_result, reviewer_id, reviewed_at, app_secret})) 五维齐全;canonical_json 序列化稳定(key 排序) | 缺字段生成;乱序 key 重算比对 |
| B-2 | proof 验证是否严格 | 验证失败 fail-closed(拒绝,非放行);APP_SECRET 缺失/为空 → 拒绝;时间格式/结果枚举不合法 → 拒绝 | 空 proof / 错 proof / 篡改 reviewed_at 重算 |
| B-3 | candidate 绑定是否正确 | proof 绑定粒度 = candidate 级(DEC-017 声明 a);DB 复制/迁移后 token 不能错误关联到其他 candidate(DEC-016 攻击面) | 复制 candidate 行换 id,携带原 proof 提交 approve |
| B-4 | APP_SECRET 边界 | APP_SECRET 从 .env 读取,启动校验非空;泄露属 Deployment Environment Boundary(DEC-017 声明 c),代码内不硬编码、不入 log | grep 硬编码/日志泄露;无 .env 启动验证 fail-closed |

## 验收域 C:Admission Enforcement(顺序③)

| # | 验收点 | 判据 | 攻击手法 |
|---|---|---|---|
| C-1 | approve() 是否强制检查 Authority | approve() 内 Authority 检查为必经路径(非可选分支);`Authority(candidate_id, claim_id) = latest ValidationEvent.validation_result`;无事件 → none → fail-closed → pending_review | 复跑 P3.2 N1/N2/N7/N8 四向量(FACT-021 基线 = 全部 BYPASS,验收要求 = 全部 BLOCKED) |
| C-2 | 未验证 IR 是否可能绕过进入 Question | Option B 边界:IR 可 provisional 存在/调试/重编译,但无 Authority 的 IR 不得物化为 Question 实体;Admission Boundary 为唯一 enforcement 点 | 直连物化路径 / 绕 Gate 提交 IR / 双入口(20 §8.2)任一入口缺 Authority 进入 |

> P3.2 N3~N6 为 Owner deferred(DEC-012),补跑窗口仅 Owner 重开;C-1 验收不要求 N3~N6,但实现不得为其预留 bypass 后门。

## 验收域 D:Identity Model(顺序②③贯穿)

| # | 验收点 | 判据 | 攻击手法 |
|---|---|---|---|
| D-1 | le_hash 计算是否稳定 | 同输入 → 同 hash(跨进程/跨重启/跨序列化路径);hash 输入域 = 身份域,不含随机量 | 重启后重算;不同入口路径重算比对 |
| D-2 | 是否错误加入非身份因素 | hash 输入不含 run_id / timestamp / attempt_id / 主键 id 等非身份字段(DEC-016 攻击面) | 审计 hash 构造代码;构造同内容不同 run 的输入比对 hash |
| D-3 | 同 hash 是否真正复用 | `UniqueConstraint(logical_execution_stage, logical_execution_hash)` + ON CONFLICT DO NOTHING → 同 hash 复用同一 Candidate(设计目标,DEC-017 ①);复用时 Authority 投影一致 | 同输入二次执行,断言 candidate_id 相同 + authority 相同(replay 同 hash → same Question + same Authority,Review-5 检查点④) |

---

## 判据纪律(继承)

- 证据四级分写:OBSERVED(亲验代码/亲跑)/ VERIFIED(通过)/ INFERRED / PROPOSED,禁混写(DEC-014);
- **"实现阶段再加字段 / 后续 migration 解决" = UNPROVEN**(DEC-015 红线,实现期继续适用);
- 每轮攻击测试报告落 `EVIDENCE/EB008-DSH-IMPL-REVIEW-*.md`,锚 V3 commit hash + sha256(COMMITTED 级);
- 严重度:BLOCKER(违反冻结设计/可 bypass)/ WARNING(声明性缺口)/ NOTE(措辞/文档);
- DSH 不改 V3 代码、不重设计;发现与设计冲突 → ATTACK 报告 → Owner 裁决。

## 已知实现期义务对照(来源锚)

| 义务 | 来源 | 验收域 |
|---|---|---|
| validation_events 持久化 | DEC-017 ③(Owner 点名) | A-1 |
| invalidate 状态机 | DEC-017 ③(Owner 点名) | A-4 / 顺序④ |
| replay 稳定性 | DEC-017 ③(Owner 点名) | A-3 / D-3 |
| proof 机制(APP_SECRET 启动校验非空) | Review-4/5 遗留 | B-1/B-2/B-4 |
| approve() 五步 Authority enforcement | Review-3/4 遗留 | C-1 |
| invalidate 级联触发(source 变更扫描) | Review-5 NOTE | 顺序④ |
| DB append-only 触发器 | Review-4 NOTE(Phase-2 trade-off) | A-2(Phase-2 验收) |

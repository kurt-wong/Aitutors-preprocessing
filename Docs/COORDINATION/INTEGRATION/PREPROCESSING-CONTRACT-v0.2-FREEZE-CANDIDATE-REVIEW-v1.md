# PREPROCESSING-V3 CONTRACT v0.2 — FREEZE CANDIDATE REVIEW v1(DSH 生产侧评审)

> Status: **v1(2026-09-16)** · Authority: Owner 统一任务指令「进入 PREPROCESSING Contract v0.2 Freeze Candidate Review」(原文照录于 `PREPROCESSING-OWNER-DECISION-RECORD-v1.md` §1sexies;ledger = `state.yaml.decisions[DEC-024]`)
> 评审对象:V3 仓 `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md`(Claude 起草,558 行,**全文逐行亲读**,DSH 评审时 V3 侧状态 = DRAFT / Frozen Candidate / NOT FROZEN)
> Role:DSH = Source Evidence Producer 侧评审(核验 + 落字建议);**Contract 正文起草责任仍在 Claude**(DEC-022 Part 7 / DEC-023 Part 7),DSH 正文零改动。
> 本轮纪律(Owner 令 D):**禁止修改任何代码和数据**——零代码 / 零 schema / 零数据 / 零 IR 重生成 / 零图片恢复 / 零 daemon / 零 Contract 冻结(冻结令权在 Owner);全部 implementation 状态保持 **not started**。
> Discipline:DECISION 段 = Owner 原文保守义;PROPOSED 段 = DSH 建议(非裁决);OBSERVED = 复用既有工件 + 本次全文亲读,**零新测量、零新探针**。

---

## A. Contract v0.2 Freeze Candidate(Owner 输出 A)

### A.1 Owner 六项原则逐条核验(对 Claude v0.2 DRAFT 全文)

| # | Owner 原则(本轮令) | v0.2 DRAFT 落点(亲读定位) | 核验结论 |
|---|---|---|---|
| 1 | `source_version_id = SHA256(raw bytes)`;path 仅 locator,禁参与 identity 判断 | §1.2(DEC-SOURCE-IDENTITY,64 小写 hex)+ §2.1 + §1.3(path 非身份,含 V3 现状合规性核验) | **PASS** —— 与 DEC-023 Part 1/2 逐字一致;「Source identity belongs to content hash, not storage location」原文在位 |
| 2 | Manifest = Source Identity Authority;IR = Semantic Consumption Authority;V3 语义消费来自 IR,身份验证独立于 IR | §1.1(双层 + DEC-B1 细化「身份对账不以 IR 存在为前提」)+ §3.1(载体分工)+ §0.5(责任边界) | **PASS** —— 双禁互替 + 身份自足性(保守义三条)均已落字 |
| 3 | 16 份 = Identity Available + Semantic Pending;允许重生成 IR;四约束 + 禁止覆盖历史事实 | §1.6(Part 3 四约束 + 四禁全文)+ §0 冻结项 ⑤ | **PASS(主体)** —— 但 §5.3 DA-20 行与 §7 差异表仍残留旧表述「Semantic Unavailable 正常态」= **F-4 文字修正项** |
| 4 | Semantic `ready/incomplete/unknown` + Decision `pending_review/approved/rejected`,禁合并 | §3.2(两层词表表 + 禁合并 + 取代声明)+ §4.1/§4.2 + §0 冻结项 ③ | **PASS** —— 与 DEC-023 Part 5/6 一致;unknown → reviewable record → pending_review 强制路由在位 |
| 5 | **`source_version_id` 最终命名方案**(避免 Producer hash identity 与 V3 UUID FK 同名) | §1.3 仅登记同名异义**警告** + §6 OQ-8′ + §8 冻结前提 item 6(「须 v0.2 落字」)——**方案本身未给** | **REQUIRED CHANGE** —— 本轮由 DSH 提出最终命名方案(N-1~N-4,见 A.2),待 Owner 采纳后 Claude 落字 §1.3 |
| 6 | source bytes 交付:**只冻结能力要求**(V3 必须能获得 raw bytes 并验证 hash),不冻结传输方案 | §0.5 末段 + §2.3 把 bytes 可达性列为「可执行前提 UNKNOWN」;OQ-12′ = logistics 开放项——**能力要求本身未升格为 REQUIREMENT** | **REQUIRED CHANGE** —— 按本轮 Owner 令须新增能力条款(草案文本见 A.3),传输方案维持不冻结 |

### A.2 `source_version_id` 最终命名方案(PROPOSED-NAMING,Owner 本轮令第 5 项)

**事实基线(OBSERVED,零新测量)**:契约键名 `source_version_id` 已由 DEC-019/020/023 三轮冻结(名 + 算法 + 格式三要素全裁);与之撞名的是 V3 内部 `document_source_versions` 的 **UUID 主键/FK**(同名 `source_version_id`,`models/source.py:44-57`,Seal 层明令禁用 sha 作唯一)——类型与语义均不同(64-hex sha vs UUID)。生产侧 `ir.source_sha256` 71 份已是 64 小写 hex,**契约名不改 = 零迁移**。

**方案原则:跨系统身份名保持冻结,内部代理键让名。**

| # | 规则 | 内容 |
|---|---|---|
| **N-1** | 契约键冻结 | 接口面(Manifest / IR / 任何跨系统工件)中,**`source_version_id` 名字只有一种语义一种类型**:`SHA256(original source bytes)`,`CHAR(64)` 小写 hex。该名已被 DEC-023 冻结,**不改名** |
| **N-2** | 内部代理键让名 | 任何系统内部的 UUID 主键/行键 **禁止使用 `source_version_id` 命名**。V3 内部 UUID FK **改名为 `source_version_row_id`**(type UUID)。命名通则:跨系统身份语义字段用 `*_id` + 内容哈希语义;内部代理键一律 `*_row_id` / `*_uuid` |
| **N-3** | 绑定关系 | V3 ingest 时建立 `(source_version_row_id, source_version_id)` 绑定;`source_version_id` 列 = `CHAR(64)` + UNIQUE;V3 对外对账只暴露 `source_version_id`(sha),`source_version_row_id` 不得出 V3 边界 |
| **N-4** | 引用纪律(重命名落地前的过渡) | 双向文档引用撞名字段时必须带限定语:「`source_version_id`(contract, sha256)」vs「`source_version_id`(V3 internal UUID, 拟改名 `source_version_row_id`)」;两侧契约文档各自维护对照注记 |

**为什么改 V3 侧而不是契约侧**:①契约名经 DEC-019/020/023 三轮冻结,改契约名 = 重开已关闭的接口讨论(本轮 Owner 令明令不再扩展);②生产侧 71 份 IR 实证形态零迁移;③V3 UUID 列属 V3 内部 schema,其改名 = **V3 实现动作,not started**,不在五步序内,不阻塞契约冻结。

**采纳后果**:Owner 采纳后 OQ-8′ 关闭;Claude 将 N-1~N-4 落字 v0.2 §1.3/§5.2-1;V3 schema 改名排期归 Claude(implementation = not started,契约冻结不依赖其实现)。

### A.3 source bytes 能力要求条款草案(PROPOSED-BYTES,供 Claude 合入 v0.2;Owner 本轮令第 6 项)

> **Capability Requirement(冻结能力要求,不冻结传输方案)**:
> V3 **必须能够获得**某 `source_version_id` 对应 source 的 **raw bytes(original source bytes)**,并**独立重算 `SHA256(raw bytes)`** 与接口声明的 `source_version_id` 比对;不一致 → fail-closed 拒收(承接 v0.1 §3.3-3)。
> **明确不冻结**:bytes 的传输/获取机制(共享文件系统 / 对象存储 / 打包交付 / API 拉取等)——属部署形态,后续独立裁决(现 OQ-12′ 降级为 delivery logistics)。
> Producer 侧对应义务:接口面 87 份的 source bytes **保持在位且字节稳定**(OBSERVED:v2 面 87 source md 零缺失,FACT-035④;IR 71/71 sha 零漂移,FACT-033③)。

该条款与 §0.5「可执行前提 UNKNOWN」不冲突:能力要求是**义务面**(冻结),传输机制是**实现面**(不冻结)。Claude 合入后 §0.5 末段措辞应相应升格。

### A.4 其他评审发现(全文亲读)

| ID | 级别 | 发现 |
|---|---|---|
| F-4 | WARNING(文字层) | §5.3 DA-20 行 + §7 差异表残留「**Semantic Unavailable 正常态**」旧表述,与同文件 §1.6/§0 冻结项 ⑤ 的「Semantic Pending(可恢复)」不一致(DEC-023 Part 3 已取代)——Claude 修正两处即可,零结构影响 |
| F-5 | NOTE | 文档尾锚点 producer @ `1657625`(+并行未提交工作树);DSH 侧本轮后 main = `eed83ee`(DEC-023 全量已提交)。**冻结时须更新锚点**,非内容问题 |
| F-6 | PROPOSED(待 Owner) | **OQ-18(E1 残留冲突)DSH 立场**:Dependency Map E1「契约冻结 → 回填(字段未定义不得回填)」的前提已被消解——DEC-021 D4 五步序裁 Step 2 回填先于 Step 3 契约冻结,且 DEC-023 已把字段**名/算法/格式**三要素全裁(E1 所虑「字段未定义」不再成立)。**建议 Owner 在冻结令中一并关闭 OQ-18:E1 由五步序取代**,Dependency Map 下轮同步 |
| F-7 | NOTE | V3 侧 DEC 编号撞号已累积 3 处(draft header 自认:DSH DEC-021/022/023 ≠ V3 同号条目);引用纪律 = 双向标注(维持现状,R5-03 治理归 Claude) |
| F-8 | NOTE(正面) | 零矛盾项确认:①§1.1/§1.3 把「路径值相等关联」明确定性为**不合规现状**(非背书),与 path 非身份裁决一致;②§2.2 禁作跨系统 identity 的 hash 表与生产侧事实零出入(body_hash/line_hash producer 零产出、norm_sha256 仅审计内部);③§5.4 Implementation Status 全表 not started/deferred/UNKNOWN,DECISION ≠ IMPLEMENTATION 纪律执行到位 |

### A.5 冻结就绪判定(DSH 侧)

**CONDITIONAL READY** —— 六项 Owner 原则中 1–4 已完整契约化(PASS);5、6 为**文字层落字项**(命名方案 N-1~N-4 / bytes 能力条款 A.3),零数据依赖、零实现依赖。三项收口动作全部属文字层:

1. Owner 采纳 N-1~N-4 → Claude 落字 §1.3(关闭 OQ-8′);
2. Claude 合入 A.3 能力条款(§0.5/§2.3 升格,OQ-12′ 降级为 logistics);
3. Claude 修正 F-4 两处旧表述 + 更新 F-5 锚点。

**冻结程序边界(不可绕过)**:按 DEC-021 D4 五步序,Contract v0.2 冻结 = **Step 3**,前置 = Step 1 接口快照冻结 + Step 2 `source_version_id` 回填(87 份)——两项执行令均未下达,属 Owner 权限。本轮评审**只判断文本冻结候选质量,不启动任何 Step**;冻结令 = Owner。

## B. 剩余未决问题列表(Owner 输出 B;只保留真正未裁)

| # | 事项 | 性质 | 备注 |
|---|---|---|---|
| 1 | **命名方案 N-1~N-4 采纳**(Owner 本轮令第 5 项的回应) | Owner 裁决(本轮即决) | 采纳后 OQ-8′ 关闭;V3 UUID 改名 = Claude 实现动作(不阻塞冻结) |
| 2 | **bytes 能力条款 A.3 文本采纳与合入** | Owner 裁决 + Claude 落字 | 传输方案维持不冻结 |
| 3 | 两层状态载体(字段名/落点)+ reviewable record 形态 | v0.2 落字面(未裁) | 生产侧最小冻结集残留项之一;G5 守卫与 16 份呈现字段(OQ-21)同源 |
| 4 | 接口面 87 表达载体(清单工件形态,C.1) | v0.2 落字面(未裁) | 生产侧最小冻结集残留项之一;V3 侧识别接口面能力依赖此项 |
| 5 | 执行令族:Step 1(快照载体与 R50 血统,D-6)/ Step 2 回填 87 / 存量 1 例 D-3 / 2 份三重成员 D-4 / 16 份再生成批次与 R52 工件版本策略 | Owner 执行令 | 冻结(Step 3)前置 = Step 1 + Step 2 |
| 6 | OQ-18 E1 残留冲突 | PROPOSED 关闭(F-6),待 Owner | 关闭后 Dependency Map 下轮同步 |
| 7 | F-4 旧表述修正 + F-5 锚点更新 | Claude 文字层 | 不阻塞评审结论,阻塞冻结文本终稿 |
| 8 | 弱项:legacy 79 披露形态(OQ-15)/ OCR 清单纳入(OQ-10)/ 17 拒收披露(OQ-13)/ `_imgs/` 恢复产物接口地位(OQ-3) | v0.2 文字层(弱) | 均不构成冻结前置 |

## C. Implementation Gap(Owner 输出 C;全部 = not started)

**Producer(DSH)侧**——冻结(Step 3)后按令执行,本轮零动作:

| 项 | 状态 | 依赖 |
|---|---|---|
| G1 `source_version_id` 回填 87 份 manifest(64 小写 hex) | not started | Step 2 执行令;前置 Step 1 快照;须配对 R50 再冻结(E2) |
| G2 双层关联由「path 值相等」升级为 `source_version_id` 关联 | not started | 随 G1 |
| 接口面 87 清单工件发布(C.1) | not started | 未裁载体形态 |
| G5 unit_type 值域守卫(unknown → reviewable record 语义落生产链) | not started | 两层载体未裁 |
| Step 1 接口快照冻结(D-6) | not started | Owner 执行令 |
| 命名方案采纳对 producer 的改名需求 | **无**(契约名 `source_version_id` 不变,零迁移) | — |

**Consumer(V3)侧**——登记不代排期(五步序无 V3 步骤):

| 项 | 状态 |
|---|---|
| V3 identity verification capability(Part 9 指定登记) | **not implemented = not started**;未来消费必须依赖 `source_version_id`,不得依赖 path |
| 六项消费义务(验证 Manifest / 重算 hash / 判断接受 / 验证 IR / Gate / 拒收) | not started |
| N-2 若采纳:UUID FK 改名 `source_version_row_id` + 绑定列(CHAR(64) UNIQUE) | not started(V3 内部 schema,不阻塞契约冻结) |
| SEMANTIC_STATUS 解冻加 `unknown` + reviewable record 机制 | not started(词表/路由已裁,实现未动) |

## D. 纪律自查(Owner 输出 D)

零代码 / 零 schema / 零数据 / 零 IR 重生成 / 零图片恢复 / 零 daemon / 零 Contract 冻结;Contract 正文(DSH 侧 v0.1 与 V3 侧 v0.2 DRAFT)零改动;写入面 = 本评审文档 + ODR v1.5(§1sexies)+ 台账三件;全部 implementation = not started;PROPOSED 与 DECISION 分栏标注(N-1~N-4 / A.3 / F-6 均为 PROPOSED,待 Owner)。

*v1 · 2026-09-16 · DSH(Source Evidence Producer)。评审基准 = Owner §1sexies 原文 + Claude v0.2 DRAFT 全文亲读;如有文字冲突,以 Owner 原文为准。*

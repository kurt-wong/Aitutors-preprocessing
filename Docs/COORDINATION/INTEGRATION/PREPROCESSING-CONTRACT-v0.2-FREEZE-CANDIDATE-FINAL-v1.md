# PREPROCESSING-V3 CONTRACT v0.2 — FREEZE CANDIDATE FINAL v1(DSH 生产侧)

> Status: **v1(2026-09-16)** · Authority: Owner Final Decision Instruction「Contract v0.2 Freeze Candidate Finalization」(原文照录于 `PREPROCESSING-OWNER-DECISION-RECORD-v1.md` §1septies;ledger = `state.yaml.decisions[DEC-025]`)
> 承接:`PREPROCESSING-CONTRACT-v0.2-FREEZE-CANDIDATE-REVIEW-v1.md`(v1;其 PROPOSED-NAMING N-1~N-4 **已被 Decision 1 取代**——Owner 采纳改契约侧命名而非 V3 侧改名,见 §FC-1 注)
> Role:DSH = Source Evidence Producer 侧终稿条款文本(FC-1~FC-5,供 Claude 合入 Contract v0.2 正文);**Contract 正文组装与 V3 侧落字仍归 Claude**(DEC-022 Part 7),DSH 对两仓 Contract 正文零改动。
> 本轮纪律(Owner 约束):禁改业务代码 / schema / 数据;禁 IR 重新生成 / 图片恢复 / daemon 执行;全部 implementation = **not started**;完成后**等待 Owner Freeze 令**(本文件不构成冻结)。
> Discipline:DECISION 段 = Owner 原文保守义;PROPOSED 段显式标注;OBSERVED = 复用既有工件,零新测量。

---

## A. Contract v0.2 Freeze Candidate Final 版(Owner 输出 A;终稿条款文本 FC-1~FC-5)

> 以下五条 = v0.2 冻结候选的**终稿条款文本**。Claude 合入 Contract 正文时应以此为准逐字落字;每条标注 Owner 裁决来源。

### FC-1 Identity Field Naming(`DECISION`,Owner Decision 1;取代 DEC-023 的契约键名)

> **跨系统 Source Identity 字段 = `source_content_sha256`。**
> **定义:`source_content_sha256` = `SHA256(original source bytes)`**;格式 = 64 字符小写 hex 字符串(继承 DEC-023,不变)。
> **禁止**:`source_file` / path 参与 identity 判断(继承 DEC-023 Part 1/2,不变)。
> **V3 内部 `source_version_id` 保持内部含义(UUID FK),不作为跨系统身份键。**

**保守义与存量映射(DSH)**:

- **命名变更面** = 仅契约侧字段名:`source_version_id`(契约键)→ **`source_content_sha256`**;算法、格式、"id 即 sha 值"语义全部不变。**OQ-8′(同名异义消歧)就此关闭**——消歧方式 = 契约侧让名(取代 Review v1 的 N-1~N-4「V3 侧改名」方案;V3 UUID 列**无需任何改名**)。
- **存量零迁移**:71 份 IR 实证值(`ir.source_sha256` == `provenance.source_version` == 当前磁盘 md 字节 sha,FACT-033③)即 `source_content_sha256` 的值;算法代码(`resolver_reference.py:52-53`)零改动。
- **字段名对齐映射(OBSERVED → REQUIREMENT)**:IR 现有 `source_sha256`(文件级,`:249`)与 `provenance.source_version`(单元级,`:167`)**语义上就是 `source_content_sha256`**;其字段名是否对齐改名 = producer 实现动作(**not started**,须执行令,见 §D)。manifest 侧回填(Step 2)将直接写入 `source_content_sha256`——**因回填尚未执行,不存在二次迁移**。
- **文档引用纪律(即刻生效)**:两侧文档中曾作为**契约键**使用的 `source_version_id` 一律读作 `source_content_sha256`;`source_version_id` 一名此后**仅指 V3 内部 UUID FK**。原文冲突以本条 + ODR §1septies 为准。

### FC-2 Source Bytes Capability(`DECISION`,Owner Decision 2)

> **Contract 冻结能力要求**:V3 必须能够:①**获取 raw bytes** ②**独立计算 SHA256** ③**与 `source_content_sha256` 比较** ④**不一致 fail-closed**。
> **不冻结具体传输方式。**

**保守义(DSH)**:

- 四项为**义务面(REQUIREMENT,冻结)**;传输/获取机制(共享文件系统 / 对象存储 / 打包 / API)= **实现面,明确不冻结**(OQ-12′ 降级为 delivery logistics,不再属冻结前提)。
- Producer 对应义务(OBSERVED 已满足):接口面 87 份 source bytes 在位(FACT-035④)、71 份 sha 零漂移(FACT-033③);内容变更 → hash 变化 → 身份失效的原则(五步序依据)保持。
- V3 侧现状:自算 hash 为 canonical_json 包裹非 raw bytes(`runner.py:71-73`),四项能力 **not started**(如实登记,不构成冻结阻塞)。

### FC-3 State Boundary(`DECISION`,Owner Decision 3;与 DEC-023 Part 5/6 一致再确认)

> 双状态体系,**禁止合并**:Semantic = `ready` / `incomplete` / `unknown`;Decision = `pending_review` / `approved` / `rejected`。
> unknown 语义单元必须:**生成 reviewable record,进入 pending_review 流程**。
> **禁止**:silent skip / silent conversion / silent fallback。

**保守义(DSH)**:与 DEC-023 Part 5/6 逐字一致,无新裁决;`reviewable record` 载体形态与两层状态字段落点**仍未裁**(§B-1)。生产侧存量映射:1 例 `andalone_question` 按本词表 = semantic 层非 ready → decision 层 pending_review 目标态;载体与存量处置(D-3)待令。

### FC-4 Scope 表达确认(`DECISION`,Owner Decision 4.5;确认既有)

> **87 / 71 / 16 范围表达确认**:87 = 正式身份接口范围(Interface Scope,不得改 71);71 = 当前已有 IR 语义消费范围;16 = 等待 semantic processing(Identity Available / Semantic Pending,可恢复);79 v1 legacy = historical asset 不入接口。禁 "IR available = Interface available"。

### FC-5 文字收口与删除项(`DECISION`,Owner Decision 4.1-4.4;Claude 执行面)

> ①Contract v0.2 文字收口;②**删除旧表述**:「Semantic Unavailable 等错误表述」全部移除(= Review v1 F-4:§5.3 DA-20 行 + §7 差异表);③**`source_version_id` 歧义全部消除**(= 按 FC-1 文档引用纪律全文替换 + §1.3 同名异义警告节改写为「契约键已改名,歧义消除」);④补充 bytes capability requirement(= FC-2 合入 §0.5/§2.3);⑤确认 87/71/16 范围表达(= FC-4 核对)。

**DSH 侧同步义务(本轮已执行)**:Gap List v1.4 / Interface Facts v2.3 / Dependency Map v2.4 / Review v1 承接注记 / 台账——契约键引用全部切换为 `source_content_sha256`,旧名仅注 V3 内部 UUID。

## B. 最终 Remaining UNKNOWN 列表(Owner 输出 B;冻结不依赖依赖①②,执行依赖③)

| # | 事项 | 性质 | 冻结阻塞? |
|---|---|---|---|
| 1 | 两层状态载体(字段名/落点)+ `reviewable record` 形态 | v0.2 落字面未裁 | **否**——FC-3 冻结的是词表+路由+禁令,载体可后续落字 |
| 2 | 接口面 87 表达载体(清单工件 C.1)+ 16 份呈现字段(OQ-21) | v0.2 落字面未裁 | **否**——87 口径已冻结(FC-4),载体属实现 |
| 3 | 执行令族:Step 1(快照载体与 R50 血统,D-6)/ Step 2 回填(`source_content_sha256` × 87,配对 R50 再冻结)/ 存量 1 例 D-3 / 2 份三重成员 D-4 / 16 份再生成批次与 R52 工件版本策略 | Owner 执行令 | **是(对 Step 2/3 程序而言)**——五步序 Step 3 冻结前置 = Step 1 + Step 2 |
| 4 | IR 侧字段名对齐(`source_sha256`/`provenance.source_version` 是否改名 `source_content_sha256`) | producer 实现动作 | 否——语义已一致,改名仅一致性收益,可与 Step 2 同令或另令 |
| 5 | bytes 传输方式 | **明确不冻结**(FC-2) | 否 |
| 6 | 文字层弱项:OQ-10(OCR 清单纳入)/ OQ-13(17 拒收披露)/ OQ-15(legacy 79 披露)/ OQ-3(`_imgs/` 接口地位) | v0.2 文字层(弱) | 否 |

## C. Freeze 前执行步骤清单(Owner 输出 C;按 DEC-021 D4 五步序定位)

| Step | 动作 | 执行方 | 状态 |
|---|---|---|---|
| C-0a | FC-1~FC-5 合入 Contract v0.2 正文(删旧表述 / 歧义替换 / bytes 条款 / 87·71·16 核对 / 锚点更新至 `b9c4404`+本轮) | Claude | **待执行** |
| C-0b | DSH 五文档同步(本文件 + Gap List v1.4 + Facts v2.3 + DepMap v2.4 + Review v1 注记) | DSH | **本轮完成** |
| C-0c | Owner 确认 C-0a 落字质量(可令 DSH 复核,同 Freeze Candidate Review 模式) | Owner | 待令 |
| **Step 1**(五步序) | Freeze interface snapshot(载体形态 + R50 血统,D-6) | DSH 按令 | **待 Owner 执行令** |
| **Step 2**(五步序) | 回填 `source_content_sha256` × 87(+ R50 配对再冻结:新 audit_id + 血统注记);可同令裁 IR 字段名对齐(UNKNOWN-4) | DSH 按令 | **待 Owner 执行令** |
| C-verify | 回填后逐份对账:`manifest.source_content_sha256 == sha256(当前 md 字节) == ir.source_sha256`(有 IR 者);快照/新基线 verify PASS | DSH | 随 Step 2 |
| **Step 3**(五步序) | **Owner Freeze 令 → Contract v0.2 冻结** | Owner | 前置 = Step 1 + Step 2 完成 + C-0a 收口 |
| (Step 4/5) | 数据治理 / 图片恢复 | 另令 | 不属本轮 |

**本文件完成后状态 = 等待 Owner Freeze 令(及 Step 1/Step 2 执行令)。**

## D. Implementation Gap Matrix(Owner 输出 D;全部 = not started)

| # | 项 | 侧 | 性质 | 状态 | 依赖 |
|---|---|---|---|---|---|
| D-1 | manifest 回填 `source_content_sha256`(87 份,64 小写 hex) | producer | schema + 数据 | **not started** | Step 2 执行令;前置 Step 1;配对 R50 再冻结(E2) |
| D-2 | 双层关联由 path 值相等升级为 `source_content_sha256` 关联 | producer | 派生(随 D-1) | **not started** | 随 D-1 |
| D-3 | 接口面 87 清单工件发布(C.1) | producer | 数据 | **not started** | 载体未裁(§B-2) |
| D-4 | IR 字段名对齐(`source_sha256` → `source_content_sha256`,如令) | producer | 数据(改写 IR 工件) | **not started** | Owner 令;R52 工件版本策略(§B-3) |
| D-5 | G5 unit_type 值域守卫 + unknown → reviewable record 生产链语义 | producer | 代码 | **not started** | 两层载体未裁(§B-1) |
| D-6 | Step 1 接口快照冻结(D-6 载体与 R50 血统) | producer | 数据 | **not started** | Owner 执行令 |
| D-7 | V3 获取 raw bytes + 独立重算 SHA256 + 比较 `source_content_sha256` + fail-closed(FC-2 四项) | V3 | 代码 | **not started**(自算现为 canonical_json 包裹) | 不阻塞契约冻结;排期归 Claude |
| D-8 | V3 六项消费义务(验证 Manifest / 重算 hash / 判断接受 / 验证 IR / Gate / 拒收) | V3 | 代码 | **not started** | 同上 |
| D-9 | SEMANTIC_STATUS 解冻加 `unknown` + reviewable record → pending_review 机制 | V3 | 代码 | **not started**(词表/路由已裁) | 同上 |
| D-10 | V3 内部 UUID `source_version_id` | V3 | — | **无需改名**(FC-1 消歧 = 契约侧让名;Review v1 N-2 方案作废) | — |
| D-11 | V3 identity verification capability(Part 9 登记项) | V3 | 代码 | **not implemented = not started**;消费必须依赖 `source_content_sha256`,不得依赖 path | 同 D-7 |

## 纪律自查

零业务代码 / 零 schema / 零数据 / 零 IR 重生成 / 零图片恢复 / 零 daemon;两仓 Contract 正文零改动(Claude 合入义务另记);写入面 = 本文件 + Gap List v1.4 + Facts v2.3 + DepMap v2.4 + Review v1 注记 + ODR v1.6 + 台账三件;全部 implementation = not started;本文件**不是冻结令**,冻结 = Owner(五步序 Step 3)。

*v1 · 2026-09-16 · DSH(Source Evidence Producer)。终稿条款文本基准 = Owner §1septies 原文;如有文字冲突,以 Owner 原文为准。*

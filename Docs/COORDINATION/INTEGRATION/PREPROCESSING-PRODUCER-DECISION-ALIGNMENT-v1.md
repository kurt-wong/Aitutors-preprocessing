# PRODUCER DECISION ALIGNMENT v1 — Producer 侧对 CONTRACT-DECISION-FINALIZATION 四项裁决的对齐报告

> Status: **v1(2026-09-16)** · 本轮 = 裁决入册 + Contract v0.2 起草准备阶段;**零数据动作,Contract 保持 v0.2 DRAFT / NOT FROZEN**
> 唯一事实基线:`PREPROCESSING-OWNER-DECISION-RECORD-v1.md`(v1.2,§1 + §1bis + §1ter)+ `PREPROCESSING-PRODUCER-INTERFACE-FACTS-v2.md` + `PREPROCESSING-PRODUCER-READINESS-v3.md` / `PREPROCESSING-IMPLEMENTATION-GAP-LIST.md`
> 工件基线:`data/producer_interface_probe_v2.json` / `data/producer_readiness_probe_v3.json` / `data/audit_snapshot_R50_input_baseline.json`
> Ledger:`state.yaml.decisions[DEC-019/DEC-020/DEC-021]`
> 结构:按 Owner 令输出 OBSERVED / DECISION / IMPLEMENTATION GAP / UNKNOWN 四段。实现状态一律 **not started**。

---

## A. OBSERVED(既有实测事实,本轮零新测量)

### A.1 三个规模数字(D1 输入)

| 面 | 数值 | 证据 |
|---|---|---|
| historical manifest inventory | **166** | probe_v2(当前树复扫,与 DQE 时点一致) |
| v2 接口面(字段口径 `identity_version=="2"`) | **87** | IF-v2 / probe_v2;目录口径 88(差 1 = resliced-pilot 三十一中混入件,IR 已 REJECTED_V1) |
| IR semantic consumption 面 | **71 ADMITTED**(1,664 单元;sha 71/71 与当前 md 字节一致,零漂移) | probe_v2 `p3`;r52 冻结工件 |
| v1 legacy 面 | **79** | IF-v2;C-IN-1 下必拒 |

### A.2 检查项 1:Manifest 是否能够承载 `source_version_id`

- **结构上能,现状为空**:manifest v2 是自由 JSON 面,schema 无禁止;但 **0/166** 携 `source_version_id`,**0/166** 携任何 sha/hash 键(probe_v2 `p1b`)——今天 Source Identity Authority 无承载;
- **值今天就能算**:`SHA-256(源 md raw bytes)`,生产点 `scripts/resolver_reference.py:52-53`,71 份已在 IR 面实证(Readiness v3 §1.1);
- **回填 = 数据写入动作**,须等 Owner 执行令(五步序 Step 2),本轮零动作;
- **硬约束**:87/87 接口面 manifest 是 R50 基线成员(probe_v3),回填必致 R50 DRIFT,必须配对再冻结(E2)。

### A.3 检查项 2:87 interface scope 如何表达

- 现状**无任何文件级"接口面"清单工件**;87 是探针口径(`identity_version=="2"` 字段过滤)算出的集合,不是已发布的接口 manifest;
- 目录口径 88 与字段口径 87 的差 1 实例已闭合(混入件,IR 拒收);
- **结论:87 的"表达"本身是 IMPLEMENTATION GAP**(见 C.2),现状只有口径定义,没有承载物。

### A.4 检查项 3:IR 71 当前冻结面的边界

- 边界事实:88 记录(= v2 目录面全集)中 71 ADMITTED / 16 QC_FAIL / 1 REJECTED_V1;71 份 sha 自洽零漂移;R52 一次性冻结,无持续产出;
- DEC-B1 已裁:IR 缺席不使 source 身份失效 → 71 面不满不阻塞身份权威性;
- 71 面与 87 面关系:71 ⊂ 87(集合包含已实测);16 份接口面内无 IR 语义承载。

### A.5 检查项 4:v1 legacy 79 的隔离

- 现状:C-IN-1 拒收语义已生效(IR 生成时 `identity_version < 2` → REJECTED_V1);79 份无接口地位定义,无迁移动作发生;
- 存量树中零自动迁移、零补齐、零 IR 重生成已发生(79 份自 R52 后未被触碰)。

### A.6 检查项 5:回填与数据清理的依赖关系(事实面)

- 五点交集(Dependency Map v2.1):dangling 1,396 ∩ 接口面 87 = ∩ IR 71 = ∩ R50 = 同 **2** 份(三重成员);
- 排除该 2 份后,D2 批跑 1,394 份与接口面**零交集** → D2 改写不影响任何已回填 `source_version_id`;
- 但 87/87 manifest 本身全为 R50 成员 → G1 回填与 R50 基线构成 E2 硬配对;
- B3 现状:非标 `unit_type` 恰 1 例(`andalone_question`)双面显式保留,链零守卫(行为正确,机制为零)。

### A.7 Contract 现状(DSH 侧)

- DSH 侧契约文件 = `PREPROCESSING-INTEGRATION-CONTRACT.md` **v0.1 DRAFT**;**v0.2 DRAFT 尚未起草**(等 Owner 起草令,本轮为起草准备);
- V3 侧需求稿 untracked(REPORTED 级),两侧文档面不同步是已登记事实(FACT-029)。

---

## B. DECISION(Owner 裁决登记,DSH 侧生效解释)

### B.1 D1 Interface Scope(DEC-021-1)

- **Manifest interface scope = 87**;**IR semantic consumption current frozen scope = 71 ADMITTED**;166 = 历史资产规模 ≠ 正式接口;
- 生产侧生效:G6(面口径)关闭为"已裁 = 87(字段口径)";v0.2 正文必须写死 87;16 份无 IR 承载的接口面成员**仍在接口面内**(身份面自足,DEC-B1),不得因 IR 缺席被移出;
- IR 71 = "当前冻结面"表述进入 v0.2;扩展机制保持开放(见 C.3)。

### B.2 D2 Legacy v1 Handling(DEC-021-2)

- 79 份 = **historical asset,not part of v0.2 interface**;四禁 = 禁自动迁移 / 禁自动补齐 / 禁自动重新生成 IR / 禁自动加入 87 接口;
- 未来处置唯一合法路径 = 独立 **Legacy Migration Plan**,不得混入当前 Contract;
- 生产侧生效:A5 关闭;G6 从"三选一未裁"变为"已裁 = 隔离";v0.2 以文字层披露该面存在与规模,不定义其字段语义。

### B.3 D3 Semantic Boundary(DEC-021-3)

- 状态词表四值:**READY / INCOMPLETE / PENDING_REVIEW / REJECTED**;
- 强制规则:任何 unknown semantic 禁 automatic conversion / silent fallback / silent skip,必须显式进入 **PENDING_REVIEW 或 REJECTED**,路由由明确规则决定;
- 生产侧生效:A6 的"词表"部分关闭(取代 DEC-019 的 UNKNOWN/PENDING 泛称——引用时以四值为准);G5 守卫目标态确定 = 值域外单元显式落 PENDING_REVIEW(REJECTED 规则待 v0.2 明确);**载体仍未裁**(见 C.4);
- 现状对账:1 例 `andalone_question` 在 IR 中 disposition = ADMITTED——按 D3 口径,该单元在四状态机下**不应是 READY**(unit_type 非法);其在 v0.2 下的呈现态属存量处置面(见 C.4/D.3)。

### B.4 D4 Execution Ordering(DEC-021-4)

- 五步序:**①Freeze interface snapshot → ②Generate/backfill source_version_id → ③Freeze Contract v0.2 → ④Data hygiene → ⑤Image recovery / historical cleanup**;
- 生产侧生效:D-1(执行序)关闭——采纳"快照先行"变体;**D-5 关闭 = D2 不得先于冻结解禁**(图片恢复在 Step 5 最后);FACT-034④/FACT-035 的互斥定量继续有效,2 份三重成员在 Step 5 仍须单独裁决(D-4 未裁);
- 与 E2 的接口:Step 2 回填 87 份必致 R50 DRIFT → **Step 1 快照必须承担"配对再冻结"基线角色**,其与既有 R50 的血统关系需执行令明确(见 C.1)。

---

## C. IMPLEMENTATION GAP(不得认为已实现;实现状态全部 = not started)

| # | Gap | 内容 | 阻塞 v0.2 冻结? | 依赖 |
|---|---|---|---|---|
| C.1 | **接口面表达 + Step 1 快照载体** | 87 面今天只有口径没有承载物:需要 ①v0.2 写死 scope 定义(字段口径);②Step 1 接口快照的载体形态(新基线工件?R50 血统注记?)与 audit_id 规则;③快照成员清单如何发布供 V3 核验 | **是**(scope 表达是 v0.2 正文内容) | Owner 起草令 + Step 1 执行令 |
| C.2 | **`source_version_id` 字段名/格式** | 裸 hex 64 vs 带前缀;md 面 vs PDF 面(OCR 清单钉 PDF 字节,语义不同)分层声明;回填范围已裁 87,字段细节未裁 | **是**(G1 字段定义,最小冻结集项) | Owner 起草令 |
| C.3 | **`source_version_id` 覆盖 87 的生产机制** | 回填是数据写入(E2 配对 R50 再冻结);此后新文件如何**持续**携带(生成链写入点)未设计;IR 扩展机制未定义(D1 只裁"当前面") | 否(回填可后置于冻结+执行令) | Step 2 执行令 |
| C.4 | **四状态机载体 + B3 守卫落点** | 词表已裁,载体未裁:生产侧标记字段名/形态、PENDING_REVIEW 与 REJECTED 的判定规则文本、守卫插入点(`resolver_reference.py:152` 复制点前);存量 1 例在四状态机下的呈现态 | **是**(载体定义,最小冻结集项) | Owner 起草令 + A7 守卫实施令 |
| C.5 | **v0.2 正文起草** | DSH 侧契约现为 v0.1;v0.2 需落字:scope 87 / IR 冻结面 71 / legacy 79 historical 披露 / 四状态机 / 五步序 / G1 字段——起草令未下,本轮只备料 | **是**(本轮任务边界 = 准备,不起草) | Owner 起草令 |
| C.6 | **legacy 隔离的披露形态** | 隔离已裁,v0.2 文字层如何披露(仅规模?路径清单?)未定 | 否(文字层) | 随 C.5 |
| C.7 | **实现面全部 not started** | G1 回填 / G5 守卫 / Step 1 快照 / 持续携带机制——四项均零代码零数据动作,按 Owner 令本轮禁执行 | — | 各执行令 |

## D. UNKNOWN(无证据/未裁,明示不预设)

| # | 项 | 状态 |
|---|---|---|
| D.1 | Step 1 "Freeze interface snapshot" 的具体所指:新接口基线工件 vs 对 R50 的再确认;与既有 R50(356 成员)的血统关系 | UNKNOWN,需执行令细化 |
| D.2 | 16 份接口面内无 IR 成员在 v0.2 的消费语义(身份自足可入接口,但语义消费如何声明) | UNKNOWN(v0.2 起草面) |
| D.3 | 存量 1 例(`andalone_question`,位于 R50 成员 manifest + IR 冻结工件)在四状态机下的呈现态与处置原子性(原 D-3) | UNKNOWN |
| D.4 | 2 份三重成员(接口面+IR+R50)的图片恢复做/不做(原 D-4);若做 = 三重 DRIFT 联动处置 | UNKNOWN |
| D.5 | PENDING_REVIEW → REJECTED 的路由规则内容(Owner 要求"由明确规则决定",规则本身未给) | UNKNOWN |
| D.6 | IR 扩展机制(新批/重产/工件版本策略)与持续产出要否 | UNKNOWN(D1 只裁当前面) |
| D.7 | V3 侧消费侧对齐状态(Claude 任务项) | 不属本报告;以 V3 侧 Consumer Alignment Report 为准 |

---

## E. Contract v0.2 DRAFT 一致性检查(起草准备,非起草)

DSH 侧现稿 v0.1 与四项裁决的差距清单(v0.2 起草时必须落字):

| v0.2 必须表达 | v0.1 现状 | 差距 |
|---|---|---|
| Interface scope = 87(字段口径),166 = 历史资产 | 未写 scope;基线引用 R50 88 份 | 新增 scope 节,并处理 88/87 口径表述 |
| IR current frozen scope = 71 ADMITTED + 扩展条款 | 有 71/88 数字但无"冻结面"地位声明 | 升格为正式声明 |
| manifest = Source Identity Authority(携 `source_version_id`,自足可验) | manifest 定位为"回源凭据",身份锚在 IR 侧 sha | **重写身份层**:manifest 携 id(DEC-B1 + D1) |
| legacy 79 = historical asset,隔离,四禁,Legacy Migration Plan 通道 | 仅 C-IN-1 拒收条款 | 新增披露节 |
| 四状态机 READY/INCOMPLETE/PENDING_REVIEW/REJECTED + unknown 路由强制规则 | §3 用 "PENDING 通道" 泛称 | 词表统一 + 路由规则文本 |
| 五步执行序(身份冻结优先) | 无 | 新增执行序节 |
| R50 / Step 1 快照配对再冻结(E2) | 无 | 新增基线治理条款 |

## F. 纪律自查

本轮写入面 = 本文档 + ODR v1.2(§1ter 照录)+ Gap List v1.2 / Readiness v3.2 / Dependency Map v2.2 增量 + 台账三件;**零数据修改 / 零 schema 修改 / 零图片恢复 / 零 daemon 修改 / Contract 正文零改动(v0.1 原样,未起草 v0.2)**;所有实现项状态 = not started;无证据项已入 UNKNOWN 节。

*v1 · 2026-09-16 · DSH(Producer side alignment report)。*

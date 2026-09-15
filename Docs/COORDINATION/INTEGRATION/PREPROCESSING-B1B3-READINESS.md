# PREPROCESSING B1-B3 IMPLEMENTATION READINESS REPORT

> Status: **v1(2026-09-16)** · Basis: Owner B1-B3 Decision Record(2026-09-16)+ `PREPROCESSING-PRODUCER-INTERFACE-FACTS-v2.md`(下称 IF-v2)
> Purpose: 回答"producer 侧为落地 B1/B2/B3 各需做什么、哪些今天就能做、哪些必须等 Contract 冻结",并提供 Contract v0.2 的生产侧输入(§3)。
> Discipline: 不修改 Contract 正文;不修改数据文件;不假设 V3 消费方式;不提出 V3 代码方案。执行动作全部**未执行**,仅计划。
> Evidence: `data/producer_interface_probe_v2.json`(本轮 commit)/ `data/producer_interface_census.json`(v1)/ 代码行锚见 IF-v2。

---

## 1. Readiness 总表

| 裁决项 | producer 侧今天状态 | READY 判定 | 阻塞点 |
|---|---|---|---|
| **B1** Manifest=Source Identity Authority | manifest 0/166 携身份字段(IF-v2 §2.2) | **NOT READY(结构缺口 G1/G2)** | Contract v0.2 定 `source_version_id` 字段语义 + Owner 令数据回填 |
| **B1** IR=Semantic Consumption Authority | 71/166 覆盖、sha 自洽 71/71、一次性冻结(IF-v2 §3) | **PARTIAL**(样本面 READY,全语料面 NOT READY) | 覆盖扩产(G3)/ 持续产出(G4)均需 Owner 令 |
| **B1** 双层 source_version_id 关联 | 现有关联 = `source_file` 绝对路径值相等(IF-v2 §2.1/§3.4) | **NOT READY** | 同 G1 |
| **B2** source identity = raw bytes SHA-256 | **已达成**:md + PDF 双语料单点生产,IR 71/71 + OCR 1,801/1,801(IF-v2 §4.1) | **READY(零动作)** | 无 |
| **B2** 其他 hash 仅内部 | norm_sha256/corpus_sha256/清单指纹均内部;body_hash/line_hash/integrity_hash 零产出(IF-v2 §4.2) | **READY(事实即合规)** | 无(注:V3 侧自算 hash 不在 producer 权限面,属消费侧) |
| **B3** unknown unit_type → UNKNOWN/PENDING | 恰 1 例非标值原样进入 ADMITTED IR;链上零守卫(IF-v2 §5) | **NOT READY(缺口 G5)** | Contract v0.2 落字 B3 语义 + 守卫实施令(数据修复本轮暂缓) |

---

## 2. B1 实施准备(生产侧)

### 2.1 `source_version_id` 需求(提交 v0.2,producer 视角)

| 需求 | 内容 | producer 依据 |
|---|---|---|
| 定义 | `source_version_id = SHA-256(raw bytes of 源 md 文件)`(hex 小写 64 字符) | B2 裁决 + `resolver_reference.py:52-53` 既有算法;IR 面 71/71 已按此语义产出且与当前字节一致 |
| 载体 | manifest 文件级新增键(每 manifest 一条,指向其 `source_file` 所指 md) | manifest 今天 0/166(IF-v2 §2.2) |
| 与 IR 对齐 | IR `source_sha256`(文件级)与各单元 `provenance.source_version` 已同语义;v0.2 只需令 manifest 侧同值 | 实证:三值一致 71/71(`p3_ir_sha_self_consistency`) |
| 双语料注意 | OCR 清单的 `source_sha256` 钉的是 **PDF** 字节(IF-v2 §4.3)——`source_version_id` 若定义在 md 面,两者语义不同,不可混用 | 分层钉链既有事实(Reconciliation v0.2 B2) |
| 不变量 | 源 md 不可变性下 id 恒定;daemon 新增 md 属新 source_version,append-only | OCR 清单 append-only 先例 |

### 2.2 Manifest 字段需求(生产侧提交清单)

1. **必需**:`source_version_id`(§2.1);
2. **待 v0.2 裁决**:`source_file` 绝对路径 → 仓库相对路径(跨机解析;现状实测为 `D:\Project\Papers\...` 本机路径);
3. **口径声明**:接口面 = 字段口径 `identity_version == "2"` 的 **87 份**(IF-v2 §2.4;目录口径 88 含 1 份 legacy 混入件,IR 已按 C-IN-1 拒收);
4. v1 面 79 份:排除 / 迁移 / 披露三选一待 Owner(G6),producer 不预设。

### 2.3 IR 输出约束(生产侧提交清单)

1. **身份约束**:IR `source_sha256` = raw bytes SHA-256(已满足,71/71);
2. **关联约束**:IR ↔ manifest 关联须从"绝对路径值相等"升级为 `source_version_id` 显式关联(与 G1 同批;IR 侧字段已存在,主要缺口在 manifest 侧);
3. **覆盖约束**:v0.2 须明示 IR 权威面 = 71 份 ADMITTED(1,664 单元)还是要求扩产;**扩产未获令前,IR 面承诺 = 现状 71**;
4. **拒收面约束**:17 份拒收记录(16 QC_FAIL + 1 REJECTED_V1,逐条 reasons 在 `p7_rejected_records`)保留披露价值,v0.2 宜明示其在接口中的地位(披露 vs 排除)——生产侧无偏好;
5. **冻结约束**:IR 为冻结工件;任何重产/修补 = 基线 DRIFT,须配对再冻结(沿 R50 既有治理)。

### 2.4 unknown unit_type 处理约束(生产侧提交清单,B3)

1. **语义落字(建议 v0.2 原文承载)**:值域外 `unit_type` → 不修正、不转换 → 单元级 **UNKNOWN/PENDING** 态(具体状态名以 Contract 定,producer 只要求"有明示态");
2. **守卫位置**:producer 生成链(manifest 产出 + IR 生成 `resolver_reference.py:152` 复制点前)须有值域检查——今天零守卫(IF-v2 §5);
3. **存量处置**:恰 1 例(`2020北京高中合格考化学（第一次）(教师版)(1)` Q1,`andalone_question`,双面同值);处置 = 数据修复,**本轮暂缓**(Owner 令),且该文件为 R50 基线成员,修复须配对再冻结;
4. **边界**:B3 处置不改 identity(B2),不改传输(B1)——三裁决正交,可分别验收。

---

## 3. Contract v0.2 生产侧输入汇总(一页)

| v0.2 议题 | 生产侧提供的事实/需求 | 出处 |
|---|---|---|
| source_version_id 需求 | 定义 = raw bytes SHA-256;载体 = manifest 文件级;对齐点 = IR `source_sha256`/`provenance.source_version`(71/71 实证);与 PDF sha 语义分层 | IF-v2 §4.1 + §3.2;本文件 §2.1 |
| Manifest 字段需求 | +`source_version_id`(0/166 现状);`source_file` 形态待裁;接口面口径 = 87(字段口径) | IF-v2 §2.2–2.4;本文件 §2.2 |
| IR 输出约束 | 身份已合规;关联待升级;覆盖 71/166(扩产待令);拒收 17 份地位待定;冻结不可回改 | IF-v2 §3;本文件 §2.3 |
| unknown unit_type 约束 | 不修正/不转换 → UNKNOWN/PENDING;守卫位置 = 生成链;存量 1 例暂缓处置(基线约束) | IF-v2 §5;本文件 §2.4 |
| B2 附注 | body_hash/line_hash/integrity_hash/norm_sha256 仅内部——producer 侧现状即合规,零动作 | IF-v2 §4.2 |

---

## 4. B2 单独结论

**B2 在 producer 侧已 READY,零实施动作**。raw bytes SHA-256 从项目早期即为唯一输出面身份算法;其余 hash 从未发布为接口。B2 的剩余工作全部在 v0.2 文字层(把身份定义写死)+ 消费侧(非 DSH 权限面)。

## 5. 数据治理执行计划(本轮全部暂缓,依赖标注)

Owner 令:接口冻结优先。以下四项**均未执行**;标注与 Contract 冻结的依赖关系:

| # | 动作 | 规模/事实基线 | 依赖 Contract 冻结? | 备注 |
|---|---|---|---|---|
| D1 | unit_type 单点修复(`andalone_question` → 正确值) | 恰 1 例;manifest 面 + IR 面双改 | **是**(B3 语义须先落字,否则修复无验收标准);且破坏 R50 基线成员,须配对再冻结 | 排序:B3 落字 → 令 → 修复 → 基线再冻结 |
| D2 | recover_images 批量恢复 | 1,394 份(PDF 在位 99.86%;R50 交集 2 份已隔离;无 PDF 2 份单列)——closure plan v1 §B | **间接**:恢复产物是否入接口面由 v0.2 定(OQ-3 图片资产形态未决);执行本身不依赖身份字段 | 可在 v0.2 冻结前完成技术准备,写入须令 |
| D3 | flags registry 登记 | 值域天然闭合 2 值 + 596 unresolved 槽位 | **间接**:registry 形态属 schema 面,宜随 v0.2 一并定 | 登记属登记册写入,非语料写入 |
| D4 | D5-C / D5-D | D5-C·D5-D 待跑;输入口径 = DQE 四账 | **否**(纯审计动作) | 但 Owner 令本轮暂缓,待解禁令 |
| D5(E) | D5-E | 🔒 锁定 | 否 | 沿既有排期 |

**解禁条件(建议令格式)**:Contract v0.2 冻结 + 逐项执行令。D4 与冻结无技术依赖,可单独解禁(Owner 权限)。

## 6. 风险与 UNKNOWN 登记

| 项 | 态 |
|---|---|
| v0.2 是否要求 manifest 回填 `source_version_id` 至 v1 面 79 份 | **UNKNOWN**(G6 未裁) |
| IR 是否扩产至全语料 | **UNKNOWN**(G3,Owner 未令) |
| IR 是否建持续产出机制 | **UNKNOWN**(G4,Owner 未令) |
| UNKNOWN/PENDING 的具体状态机落点(manifest 字段 vs IR 字段 vs 双侧) | **UNKNOWN**(待 v0.2 定义;producer 侧仅承诺"有明示态 + 零静默") |
| daemon 持续新增 md(今日 raw face 4,224,v1 时点同值——本轮复算零增长) | OBSERVED;接口冻结时须锚定快照口径 |

## 7. 纪律自查

未改 Contract 正文 / 未改数据文件(除证据工件 `data/producer_interface_probe_v2.json`)/ 未改两仓代码 / 未执行任何治理动作 / 无 V3 假设与 V3 方案。

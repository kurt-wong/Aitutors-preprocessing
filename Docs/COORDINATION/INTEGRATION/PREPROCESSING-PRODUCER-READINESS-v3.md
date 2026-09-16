# PRODUCER READINESS v3 — preprocessing 侧对 Contract v0.2 的实现缺口

> Status: **v3.1(2026-09-16,DEC-B1 后增量更新)** · Basis: **Owner Decision Record v1**(§1 总纲 + **§1bis DEC-B1**)+ IF-v2 + Readiness v1(本轮升版取代)+ Closure Plan v2
> DEC-B1 生效更新:①唯一关联键已裁(`source_version_id`)→ U3 目标态确定;②**source 身份不依赖 IR 存在** → U4(IR 覆盖)从身份路径解耦,IR 现状 71 不阻塞 B1-M/B1-L 达成;③G1 目标态新增身份自足性验收。
> Purpose: 明确 preprocessing 生产侧距离 Contract v0.2 冻结接口的实现缺口:已满足 / 未满足 / 需 Owner 批准。
> Evidence: `data/producer_interface_probe_v2.json`(上轮)+ `data/producer_readiness_probe_v3.json`(本轮新增,交集定量)+ `data/audit_snapshot_R50_input_baseline.json`(R50 成员资格亲验)。
> Discipline: 零数据修改 / 零 schema 修改 / 零图片恢复 / 零 daemon 修改 / 零 Contract 修改。无证据标 UNKNOWN。

---

## 0. 一页结论

| 裁决项 | Readiness | 一句话 |
|---|---|---|
| **B2** source identity = SHA-256(raw bytes) | ✅ **已满足(零动作)** | producer 输出面从始即为此算法,双语料单点生产,IR 71/71 实证 |
| **B1-M** Manifest = Source Identity Authority | ❌ **未满足** | manifest **0/166** 携 `source_version_id`、**0/166** 携任何 sha 字段——authority 无承载 |
| **B1-I** IR = Semantic Consumption Authority | ◐ **部分满足** | 71/166 覆盖,sha 自洽零漂移;覆盖面与持续性未裁,维持现状 |
| **B1-L** 双层 source_version_id 关联 | ❌ **未满足** | 现有关联 = `source_file` 绝对路径值相等,非 id |
| **B3** unknown unit_type 显式保留 | ◐ **行为满足 / 机制未满足** | 恰 1 例已被原样保留进 IR(行为正确);但链上零守卫,正确性无机制保证 |

---

## 1. Producer 输出面确认(B1/B2 核心)

### 1.1 `source_version_id` 来源 = raw bytes SHA-256(OBSERVED,已确认)

| 项 | 事实 |
|---|---|
| 算法 | `SHA-256(源 md 原始字节)`,hex 小写 64 位 |
| 生产点 | `scripts/resolver_reference.py:52-53`(`_sha256` = `hashlib.sha256(p.read_bytes()).hexdigest()`) |
| 既有产出 | IR 文件级 `source_sha256`(`:249`)+ 单元级 `provenance.source_version`(`:167`) |
| 实证 | 71/71 与当前磁盘 md 字节一致(probe_v2 `p3`,裁决当日复验零漂移) |
| PDF 面注意 | OCR 清单 `source_sha256`(`r67_manifest_bootstrap.py:181`)钉 **PDF** 字节——与 md 面 `source_version_id` **语义不同,不可混用**(分层钉链既有事实) |

**结论:`source_version_id` 的值 producer 今天就能算(代码在库、算法唯一、71 份已实证);缺的只是 manifest 载体字段。**

### 1.2 Manifest 当前不是 identity authority(实测)

| 检查 | 结果 |
|---|---|
| 携 `source_version_id` 的 manifest | **0 / 166**(probe_v2 `p1b`) |
| 携任何 `*sha*` / `*hash*` 键的 manifest | **0 / 166** |
| 现有"身份样"字段 | `source_file` = 本机绝对路径字符串(路径不是 id:不含内容指纹、机器绑定) |
| 现有版本样字段 | `identity_version` = 标注 schema 版本("2"),**不是** source 版本 |

**结论:manifest 今天在内容身份上完全空载——Source Identity Authority 角色 = NOT READY,缺口是确定性的字段缺失,不是能力缺失。**

**当前缺失字段登记(按裁决必须补齐)**:

| 缺失字段 | 期望语义 | 生产侧可提供性 |
|---|---|---|
| `source_version_id` | SHA-256(源 md raw bytes) | ✅ 算法/代码就绪,回填待令 |
| sha 类字段(文件自钉) | manifest 自证或互证用 | 语义由 v0.2 定(可与 `source_version_id` 合一或分设);producer 不预设 |

---

## 2. 已满足项(Satisfied)

| # | 项 | 证据 |
|---|---|---|
| S1 | source identity 算法 = raw bytes SHA-256,单一无歧义 | §1.1;IF-v2 §4.1 |
| S2 | 其余 hash 全部内部:norm_sha256(`r64:61` 算法)/ corpus_sha256(`audit_integrity.py:134`)/ r67 清单指纹(`:309-321`)从未发布为接口;body_hash / line_hash / integrity_hash **零产出** | IF-v2 §4.2;B2 裁决下现状即合规 |
| S3 | IR 71 份 sha 自洽(= provenance = 当前字节),零漂移 | probe_v2 `p3`(71/71) |
| S4 | IR provenance 七字段完备(source_lines 行区间溯源) | census `ir.provenance_keys` |
| S5 | **B3 行为面**:非标准 `unit_type` 恰 1 例已被**显式保留**(原值 `andalone_question` 原样进入 manifest 与 IR,零转换零丢弃) | probe_v2 `p6`(双面同值);`resolver_reference.py:152` 逐字复制 |
| S6 | v2 接口面(字段口径 87)source md 全部在位(87/87 可解析,零缺失) | probe_v3 `v2_face_source_md_missing: []` |
| S7 | 拒收面可披露:17 份拒收记录携 qc_verdict + reasons(16 QC_FAIL + 1 REJECTED_V1) | probe_v2 `p7` |

## 3. 未满足项(Unsatisfied — 结构缺口)

| # | 缺口 | 裁决映射 | 现状 | 实施内容 | 阻塞 |
|---|---|---|---|---|---|
| U1 | manifest 缺 `source_version_id` | B1-M / B1-L | 0/166 | 字段新增 + 回填(范围 87 或 166 待裁) | **v0.2 定义 + Owner 回填令** |
| U2 | manifest 缺 sha 类字段 | B1-M | 0/166 | 同 U1(字段形态待 v0.2 定) | 同上 |
| U3 | 双层关联 = 路径值相等 | B1-L(**DEC-B1 已裁唯一键**) | `ir.source_file == manifest.source_file` | 关联键升级为 `source_version_id` 唯一关联(IR 侧字段已有,manifest 侧随 U1) | 随 U1 |
| U4 | IR 覆盖 71/166 | B1-I(**DEC-B1 解耦**) | 95 份无语义承载 | 扩产(若 v0.2 要求);**已不阻塞身份面** | **UNKNOWN(覆盖面未裁)** |
| U5 | IR 无持续产出机制 | B1-I | R52 一次性冻结 | 机制建设(若要求) | **UNKNOWN(未裁)** |
| U6 | B3 零守卫 | B3 | 生成链无 unit_type 值域检查;正确性靠"恰好没转换"而非机制 | 生成链引入值域检查 + 显式 UNKNOWN/PENDING 落点 | **v0.2 落字 B3 载体** |
| U7 | v1 legacy 面 79 份无接口地位 | B1 面口径 | C-IN-1 拒收语义之外无处置定义 | 排除/迁移/披露三选一 | **UNKNOWN(未裁)** |

## 4. 需要 Owner 批准项(Approval Required)

| # | 项 | 批准粒度 | 依赖 |
|---|---|---|---|
| A1 | `source_version_id` 字段定义(名/格式/md 面 vs PDF 面分层声明) | v0.2 内容裁决 | — |
| A2 | 回填范围:**87**(接口面)vs **166**(全语料) | 范围令 | A1 |
| A3 | 回填执行令(数据写入;与 R50 基线 DRIFT 治理配对,见 Gap List G1-3) | 执行令 | A1+A2+v0.2 冻结 |
| A4 | IR 权威覆盖面(71 现状 vs 扩产)+ 持续产出要否 | 二选一 ×2 | — |
| A5 | v1 面 79 份处置 | 三选一 | — |
| A6 | B3 UNKNOWN/PENDING 载体(字段/状态机落点) | v0.2 内容裁决 | — |
| A7 | B3 守卫实施令(生成链值域检查) | 执行令 | A6+v0.2 冻结 |

---

## 5. B3 生产侧责任(按 Owner Decision Record v1 §2 严格版)

1. **显式保留**:非标准 `unit_type` 原样落盘(manifest 与 IR 双面)——**现状已达成**(S5);
2. **禁止自动转换**:生成链不得 typo 修正、不得近似映射——**现状已达成**(零转换点);
3. **禁止静默丢弃**:非标准单元不得被跳过/过滤——**现状已达成**(该单元 disposition = ADMITTED,完整消费字段齐全);
4. **机制化(未满足 U6)**:上述正确性目前是"行为偶然",不是"机制保证"——链上零守卫,任何未来代码改动都可能无声破坏;UNKNOWN/PENDING 显式态依赖 v0.2 定义。

**生产侧承诺(v0.2 冻结后可执行)**:守卫 fail-closed——值域外单元进入显式态,**永不**自动修复。

## 6. 新增定量事实(本轮 probe_v3,依赖图输入)

| 事实 | 数值 |
|---|---|
| dangling figure 文件面(自算,口径同 DQE) | 1,396 |
| **dangling ∩ v2 接口面(87 source md)** | **恰 2 份**(首师大附中高一化学 / 高三物理) |
| **dangling ∩ IR ADMITTED 71** | **同 2 份** |
| **dangling ∩ R50 基线(356 成员)** | **同 2 份**(与 closure plan v1 "R50 交集恰 2 份"完全一致,三点交集闭合) |
| R50 基线组成 | 88 manifest.json + 88 annotated.md + 176 source md + 4 其他 = 356 |
| **v2 接口面 87 manifest 的 R50 成员资格** | **87/87 全部是 R50 成员** |
| IR 71 source md 的 R50 成员资格 | 71/71 |

**含义**:G1 回填(改 87 份 manifest)与 D2 图片恢复(改 md 字节)都会触发 R50 基线 DRIFT——依赖关系的完整重整理见 `PREPROCESSING-EXECUTION-DEPENDENCY-MAP.md`。

## 7. 纪律自查

零数据修改 / 零 schema 修改 / 零图片恢复 / 零 daemon 修改 / 零 Contract 修改(本轮写入面 = 文档 + 台账 + 只读探针工件 `data/producer_readiness_probe_v3.json`);不假设 V3 消费方式;不提出 V3 方案。

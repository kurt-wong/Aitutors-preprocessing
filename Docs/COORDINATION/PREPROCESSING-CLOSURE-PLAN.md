# PREPROCESSING-CLOSURE-PLAN v1(DRAFT · 收口准备)

> **基于**:commit `4d78513` + `EVIDENCE/PREPROCESSING-DATA-QUALITY-REPORT.md`(DQE 四重点测量)+ 本轮三项补充只读测量(`data/dq_figure_pdf_availability.json`、R50 基线交集、异常件基线成员核验)。
> **本轮禁止(Owner 明令)**:不修改数据、不修改 schema、不修改 V3、不冻结 Integration Contract(保持 DRAFT)。本文件 = 决策支持文档,所有执行动作等 Owner 逐项批准。
> **新测量口径声明**:本轮三测均为只读、确定性;两测为 `.pytest_work/` 一次性探针(不入库,数字已固化于本文件与工件)。

---

## §1 BUG-14-DATA 裁决清单(A/B/C 分类)

### A. 必须修复才能冻结 Contract

**判定:当前 0 项。**

理由:契约的冻结对象是"**实测值域 + fail-closed 消费条款**",不是"清洁数据"。全部已知异常——unit_type 1 例非标准值、27,240 处悬空 figure、flags 未入登记册、596 unresolved 槽位——**均已在契约 v0.1 文本中如实披露**(§2.1 值域表含噪声注记 / §2.4 无注册表 / §3.2-3.3 空值与阻断条款),并配消费侧隔离。冻结一份"如实描述脏数据并规定如何 fail-closed"的契约,不被数据清洁度阻塞。

**唯一近 A 项与路线二选一(请 Owner 裁决)**:

| 路线 | 内容 | 代价 |
|---|---|---|
| **披露路线(推荐)** | 数据不动;契约 §2.1 已含异常注记,冻结即成立 | 消费面永远带 1 个 PENDING 单元(损失 = 1 单元自动消费) |
| 清洁路线 | 冻结前执行 unit_type 单点修复(§2) | **破坏 R50 冻结基线成员**,须连带再冻结决策 + 迁移报告 |

另注:按 Owner 已有裁令,契约冻结的真正前置 = **Claude Consumer Review**,与数据项无关。

### B. 数据清洗阶段解决(建议执行序)

| 序 | 项 | 前置 | 依赖本文件章节 |
|---|---|---|---|
| B1 | unit_type 单点修复(若走清洁路线) | Owner 批准 + R50 基线再冻结决策 | §2 |
| B2 | recover_images 批量恢复(1,396 份) | Owner 批范围 + 批次令;冻结清单机制 | §3 |
| B3 | flags 登记入 rule_registry | Owner 批词条与 taxonomy 归类 | §4 |
| B4 | BUG-14-DATA 既有闸门:6 needs_ruling 逐份裁定 | Owner 逐份裁定(月考/答案/初三卷等) | DQE §5 |
| B5 | D5-C 幂等复跑 → D5-D 重审计(干净 baseline,吸收 DQE 四账) | B2/B4 完成后排期 | DQE §5 |
| B6 | D5-E 语义去重(72 collisions,66 同名异字节 + 6 字节全同) | 冻结中,须 Owner 单独启动令 | R64/R67.x 台账 |

### C. 属于 V3 消费限制(不修;写入消费面,契约已/应载明)

1. **unresolved 596 槽位**:禁止 `answers.get(q,"")` 类静默默认,必须显式通道(契约 §3.2 特别条款,G-BOUND-1);
2. **悬空 figure**:恢复完成前,相关单元 figure 内容不可得——V3 按引用原文保留、不得假设图在;外链 codecogs 9 处 = 外部依赖,离线不可解析(已登记家族);
3. **既有四态**:printed=null(27.1%)/ 源面无答案 / v1 manifest 拒收 / 非标准 unit_type 隔离 PENDING——契约 §3 全载;
4. **manifest 不钉 sha(0/166)**:V3 对账必须用 IR provenance 或独立重算源 sha,不得指望 manifest 自证(契约 §1 已写,本项确认为长期结构事实,非待修缺陷)。

---

## §2 unit_type:`andalone_question`(事实 / 影响 / 修复范围 / snapshot)

**事实(OBSERVED,DQE §1 口径)**:
- 值 = `"andalone_question"`(疑 `standalone_question` 首字符丢失);**全语料 166 manifest × 4,609 单元 + IR 1,664 单元穷举,恰 1 例**;
- 位置:`Ocr-markdown\reslice-batch-C\合格考\化学\2020北京高中合格考化学（第一次）（教师版）(1).manifest.json`,unit `Q1`,identity v2 **可消费面内**;
- 产生点 = LLM 标注输出原样落盘(producer 链对 unit_type 无值域校验);Reference Resolver 零重塑忠实携带(R52 IR 同值);
- 语义对照:该单元为单道选择题,`composite_question` 判定无任何源面依据,`standalone_question` 为唯一符合证据的修复值。

**影响**:
- 消费侧:契约 §3.3-6 隔离条款已覆盖——非闭集值 → PENDING 通道,不静默消费,**fail-closed 生效中**;
- 损失面:恰 1 单元不可自动消费;无扩散(值不被任何键引用,unit_id 仍为 Q1 不变);
- 风险面:若消费方假设闭枚举(`if type == composite: ... else: standalone`)则被绕过——契约已禁止该假设。

**修复范围(若批准,最小面)**:
- 恰 1 个文件内 1 个 JSON 字段(`units[0].unit_type`);"修复范围 = 单点"成立;
- **不涉**:schema、源 md、annotated.md、切片、IR(`resolver_ref_r52/resolver_ir.json` = 冻结审计工件,provenance 纪律,永不回改);
- 执行纪律(先例 = R31 迁移):默认 dry-run、before/after sha、迁移报告逐单元留 old/new、幂等、CI 回归。

**是否破坏历史 snapshot:是(硬事实)**。
- 该 manifest 为 **R50_input_baseline 成员**(356 文件之一,pin sha = `58058c4f…e3cc`,同卷 4 成员全部在册);
- 原地修复 → `audit_integrity verify R50_input_baseline` 必报 DRIFT,该基线是 Resolver 审查冻结输入面(契约附录 B.3 引用);
- 若走清洁路线,**必须配对**:Owner 批准再冻结新基线(新 audit_id,R50 血统注记),或接受旧基线退役;**不得**只改数据不改基线(制造隐性 drift)。

---

## §3 figure 悬空恢复计划草案(不执行)

**范围(OBSERVED)**:
- **1,396 份 md / 27,240 处**悬空引用,全部为未恢复原始 `imgs/` 形态;目录分布:高二 435 / 高三 414 / 高一 378 / 未分类 109 / 高考真题 48 / 合格考 12;
- **源 PDF 在位率:1,394/1,396(99.86%)**(stem 精确匹配 `original/` 树 12,707 PDF 索引);**2 份无 PDF**(均为 `(1)(1)` 重复 stem 家族:`高三\化学\2022北京五中高三三模化学(1)(1).md`、`高二\生物\2023北京顺义高二（上）期末生物(1)(1).md`)→ 单列人工裁定,不猜;
- **R50 基线交集:恰 2 份**(首师大附中高一化学 / 高三物理月考卷源 md)——批跑默认**排除这 2 份**(隔离至 §2 同款 snapshot 决策),其余 1,394 份零基线冲突;
- 完成态定义:引用全部改写为 `../../_imgs/<stem>/…`(该形态悬空率实测 = 0)。

**输入**:
- 执行时点**冻结清单**:1,394 份(排除 2 基线成员 + 2 无 PDF 单列)逐文件 sha 快照——daemon 持续向源树产出,清单必须时点冻结(D5-B plan 指纹先例);
- `original/` PDF 树(只读);工具 = `scripts/recover_images.py`(R58 修复 + R59 审查通过:排除制扫描、pdf_miss fail-closed、账目 sha 闭环、`--dry-run`/`--limit` 支持、CI 钉 5 项);
- **零 OCR 配额消耗**(PyMuPDF 本地 PDF 提取)。

**输出**:
- 图片资产 `_imgs/<卷 stem>/` 就地落盘 + md 引用就地改写 + 审计账 `recover_images_audit.jsonl` append;
- dry-run 统计报告(先) + apply 执行报告(后,逐文件 before/after sha);
- 验收:执行后独立复扫(同 DQE 武器口径)→ 批内 dangling **归零**;非目标文件 sha 闭环零漂移。

**幂等要求**:
- 工具既有:`already_done` 跳过(已改写/资产在位)、重复执行零增量(R58 实测 2,182 already_done);执行前后各跑一次 dry-run,统计必须一致;
- 批次纪律(参照 D5-B 四闸先例):B2-1 冻结清单指纹 / B2-2 无 PDF 件 fail-closed 单列 / B2-3 `--limit` 分批 + 每批独立报告 / B2-4 批后反验证(dangling 归零 + 账目 append + 未触碰闭环);
- 失败语义:单文件失败不中止整批、如实入账(R63 批隔离先例);恢复权在人,不自动重跑 PDF 缺失件。

---

## §4 flags 规则登记需求(纯登记,零 schema 变更)

**缺口**:`governance/rule_registry.md` 对 flags **零注册**(grep 0 命中);值域、定义、消费禁令散落于 log/契约,无双向钉保护。

**需登记词条(2 条,建议 taxonomy 归类待批)**:

| flag | 计数 | 建议归类 | purpose | attack surface | retirement |
|---|---|---|---|---|---|
| `answer_table_unresolved` | 502 单元 / 596 槽位 | STRUCTURE | 答案区单行 `<table>` 按题号键位不可机器归属,如实标注 | 下游静默默认(`answers.get(q,"")` 把 unresolved 洗成"已解为空",R-ACC-14 量化) | 源面事实,不退役 |
| `answer_number_mismatch` | 91 单元 | IDENTITY | 答案区局部编号 ≠ 全卷 canonical(BUG-22 家族答案区体现),观察而不重绑 | 消费方误当裁决语义(flag 是结构观察非保证,R-ACC-12) | 源面事实,不退役 |

**登记实施需求(批准后)**:
1. 词条入册(purpose / attack surface / evidence 指针 R53·R-ACC-14·DQE / retirement),归类二选一定案;
2. `test_rule_registry.py` 双向钉范围扩展(set-diff 覆盖 flags 词条);
3. 退役政策同款管辖:**新增 flag 值必须先登记后实现**;
4. **明确不做**:不改 IR schema、不加新 flag、不加任何自动 PASS/FAIL 逻辑(审计惯性防线 + R47"不得为 PASS 率扩展自动规则")。

---

## §5 汇总:待 Owner 批准项(本轮零执行)

| # | 项 | 类 | 批准粒度 |
|---|---|---|---|
| 1 | 契约路线:披露路线 vs 清洁路线(unit_type) | A 判定 | 二选一 |
| 2 | unit_type 单点修复(若清洁路线)+ R50 基线再冻结 | B1 | 修复令 + 基线决策 |
| 3 | recover_images 批跑范围(1,394 份)与批次切分 | B2 | 范围令 + 批次令 |
| 4 | flags 词条与 taxonomy 归类 | B3 | 登记令 |
| 5 | 6 份 needs_ruling 逐份裁定 | B4 | 逐份裁定 |
| 6 | D5-C/D 排期、D5-E 启动令 | B5/B6 | 排期令 |

---

*v1 DRAFT · 2026-09-15 · DSH(preprocessing)。基于 `4d78513`;全部数字可复现(DQE 工件 + `data/dq_figure_pdf_availability.json` + 本轮探针);四禁(数据/schema/V3/契约冻结)零触碰。*

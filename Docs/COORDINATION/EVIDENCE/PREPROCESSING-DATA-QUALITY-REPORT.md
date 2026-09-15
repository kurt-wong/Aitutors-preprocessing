# PREPROCESSING-DATA-QUALITY-REPORT v1

> **触发**:Owner 指令(2026-09-15)——暂停 Integration Contract 扩展,进入 preprocessing 内部收口;优先 BUG-14-DATA,重点四方向:unit_type 值域 / figure / unresolved flags / manifest·source 输出稳定性。
> **性质**:只读测量报告。本轮**零语料写入、零生产代码变更、未触碰 V3、未冻结 Integration Contract**(Owner 明令)。
> **武器**:`scripts/dq_data_quality_scan.py`(dq-data-quality-scan-1,一次性,确定性输出)→ 工件 `data/preprocessing_data_quality_scan.json`。
> **口径**:全语料 166 份 manifest(Ocr-markdown 全树)+ 源树 4,223 份 md(排除派生目录,排除政策单一来源 = `recover_images` 常量)+ 真实 IR(`data/resolver_ref_r52/resolver_ir.json`,88 文件/1,664 单元)+ OCR 输出清单(`data/ocr_output_manifest.jsonl`,1,801 条)+ R50 冻结基线(356 文件)。

---

## §0 结论摘要

| # | 重点 | 结论 | 处置建议(均待 Owner 裁决,本轮零执行) |
|---|---|---|---|
| 1 | unit_type 值域 | 全语料 **恰 1 例非标准值**(`andalone_question`,v2 可消费面内) | 单点确定性修复(§1) |
| 2 | figure | 形态高度统一(99.99% 行内 HTML 相对路径);**悬空 27,240 处/1,396 份,全部 = 未恢复的原始 `imgs/` 形态**;已改写形态悬空 = **0** | recover_images 批量恢复(§2);最小 registry **不需要** |
| 3 | flags | 值域天然闭合恰 2 值;**登记册零注册**(缺口) | 登记入 rule_registry,不改 schema(§3) |
| 4 | 输出稳定性 | 分层钉链完好:**IR 71/71 源 sha 全对账零漂移;R50 基线 356/356 零漂移;OCR 清单 append-only、PDF sha 抽样 3/3 吻合**;唯一结构事实 = manifest 本身不钉 sha(0/166) | 维持分层现状(§4);sha 入 manifest 按 G-SCHEMA-1 延期 |

---

## §1 unit_type 值域

**当前所有真实值(OBSERVED,166 manifest × 4,609 单元 + IR 1,664 单元穷举)**:

| 值 | manifest 全语料 | IR(88 审计面) | 判定 |
|---|---|---|---|
| `standalone_question` | 3,935 | 1,385 | canonical |
| `composite_question` | 673 | 278 | canonical |
| **`andalone_question`** | **1** | **1** | **非标准(拼写噪声)** |

- 唯一异常定位:`Ocr-markdown\reslice-batch-C\合格考\化学\2020北京高中合格考化学（第一次）（教师版）(1).manifest.json`,unit `Q1`。该文件属 **identity v2 可消费面**(batch-C),不是 legacy 边角;IR **忠实携带**(零重塑纪律的反面实证:噪声也原样过界)。
- 产生点 = LLM 标注输出,producer 链无值域校验(`write_outputs` 原样落盘)。身份面其他值域(basis/printed_provenance)经 R34 回填 + 反伪造贯穿检查,**unit_type 是唯一无守卫的单元级枚举**。

**是否建立 canonical enum**:建议 = **是**,词表恰 2 值 `standalone_question | composite_question`(实测穷举支撑;Integration Contract §2.1 已按实测写此值域,标注 OQ-2)。

**非标准值如何处理(三选项,推荐 A+B)**:
- **A(消费侧,零代码)**:非标准值 → 隔离进 PENDING 通道(契约 §3.3-6 既有条款),不静默当 standalone 吃——**已生效,无需动作**;
- **B(producer 单点修复)**:对 Q1 做确定性修复(`andalone_question` → `standalone_question`),按 R31 迁移先例留迁移报告;**属数据修复非 schema 变更,但动 v2 冻结面,须 Owner 批准**;证据充分性:该单元题干 = 单道选择题,composite 判定无源面依据;
- **C(producer 加守卫)**:`write_outputs`/消费入口加 closed-set 校验——按 R47/R50 basis 值域先例属"契约完整性检查",**建议与 basis schema-only(排期③)合并实施,不单独立项**(审计惯性防线)。

## §2 figure

**当前图片引用方式(OBSERVED,源树 4,223 份 md 全量)**:

- 总引用 **70,838** 处,分布于 3,578 份文件:**行内 HTML `<img src>` 本地相对路径 70,829(99.99%)+ 外链 http 9(latex.codecogs SVG,化学卷 `\bigcirc` 类)**;markdown `![]()` 形态 = **0**;绝对路径 = 0;data URI = 0;
- **悬空 27,240 处 / 1,396 份文件,归因全部单一**:`bare_imgs_no_asset_anywhere`——原始 OCR 输出形态 `imgs/img_in_image_box_*.jpg`,图片资产从未从 PDF 恢复(recover_images 积压家族)。**已改写形态(`../../_imgs/...`)悬空 = 0**——凡被 recover_images 处理过的引用,目标全部在位;
- 台账连续性:R58 时点积压 = 499 份/10,439 处;本轮 1,396 份/27,240 处,**增长主因 = daemon 恢复运行后持续产出新 OCR 文件(其原始形态即含 `imgs/` 引用),属已知机制,非新缺陷**;
- 外链 9 处为已登记家族(R59 F-r59-3:外部依赖,非本地缺图债)。

**是否需要最小 registry**: **不需要(当前)**。事实:引用 = 行内相对路径 + 资产落在 `_imgs/<卷 stem>/` 目录,行锚已由 span 承载;缺的是**资产恢复执行**,不是注册结构。建 registry = 为尚不存在的消费需求提前造结构,违反 Owner "不提前满足 V3 未来需求"。若未来 V3 要求图片 sha/独立清单,属 OQ-3,由 Claude Consumer Review 提出后再议。

**处置建议**:批准 recover_images 批量恢复跑(工具经 R58/R59 验证,本地 PDF 提取、**零 OCR 配额**,但会写语料 → 按纪律须 Owner 逐批批准);恢复后悬空引用由工具改写至 `_imgs/` 形态(该形态悬空率实测 = 0)。

## §3 unresolved flags

**flags 定义(OBSERVED 值域,IR 1,664 单元穷举)**——恰 2 值,均产生于 Reference Resolver(结构观察,非裁决):

| flag | 计数 | 定义 | 语义 |
|---|---|---|---|
| `answer_table_unresolved` | 502 单元 | 答案区为单行 `<table>`,按题号键位取不出本单元答案 | 源面答案表不可机器归属;槽位级明细在 `answers.unresolved[]`(全 IR **596 槽位**) |
| `answer_number_mismatch` | 91 单元 | 答案区行首局部编号 ≠ 全卷 canonical 编号 | 结构观察(BUG-22 家族在答案区的体现),**观察而不重绑** |

**消费方责任(已冻结,不新增)**:G-BOUND-1 + R-ACC-14——unresolved 槽位禁止 `answers.get(q,"")` 类静默默认,必须走显式通道;flags 是结构事实不是语义保证(R-ACC-12:结构全绿语义可错,正确性归 Admission/人工)。

**是否需要标准化**: **登记需要,schema 不需要**。缺口 = 规则登记册(`governance/rule_registry.md`)对 flags **零注册**(grep 0 命中)——值域、定义、消费禁令散落在 log/契约文档。建议:登记册新增 flags 词条(2 值 + 定义 + R-ACC-14 消费禁令指针),受双向钉测试管辖;**不改 IR schema、不扩 flag 值域**。

## §4 manifest/source 输出稳定性

**hash(OBSERVED,分层钉链)**:

| 层 | 钉什么 | 现状测量 |
|---|---|---|
| manifest v2 | (无 sha) | **0/166 携带任何 sha 键**(精确键遍历;"shared" 子串误命中已排除)——manifest 只钉 `source_file` 路径 + 行号锚 |
| IR(resolver-ir-0.1) | `source_sha256` = 源 md 字节 sha256 | **71/71(全部含 ir 的文件)与当前源对账,0 缺失 0 不符**——IR↔源绑定完好 |
| OCR 输出清单(R66) | `source_sha256` = 源 **PDF** 字节 sha256 + size + pages | 1,801 条 append-only;抽样 3/3 与 `original/` 树内 PDF 吻合;输出文件 4/4 在位 |
| R50 冻结基线 | 356 文件 sha256 快照 | `audit_integrity verify` = **0 drift / 0 missing** |

- 注意两处 sha 语义不同、不可混用:OCR 清单钉 **PDF**,IR 钉 **OCR md**;manifest 自身不钉——源身份完整性依赖相邻层(IR/审计快照/OCR 清单),这是**如实的结构事实,非缺陷**,但消费方文档必须写明(契约 §1 已写)。

**snapshot**:R50_input_baseline(356 文件)为审计面冻结基线,本轮复核零漂移;全语料层面无整体快照(daemon 持续写入,快照即过期)——冻结面与运行面分离是既定设计。

**reproducibility(既有证据,非本轮新测)**:回填幂等字节一致(c16 真实 batch-C 15/15);F1 确定性输出 + 88 份控制组 2403/2403;修复/迁移类动作全部 before-after sha 闭环(R63/R67.x 家族);输出路径派生纪律 C-OUT-1。

**结论**:输出稳定性分层钉链当前**完好**;manifest 无 sha 的分层事实已量化,增强提案按 G-SCHEMA-1 纪律延期(IR vNext 落点),本轮不提。

## §5 BUG-14-DATA 收口状态(优先项对账)

| 闸门 | 状态 | 证据 |
|---|---|---|
| D5-A 停跑步机 | ✅(R66 + R66.1 + R67.1 运行时实证) | manifest append-only,MANIFEST_DONE 切断重 OCR |
| D5-B 全量 reclassify | ✅(R67.2~R67.4:13 + 20 + 37 = **70/70 moves**) | 四闸协议,独立复核 bad=0 |
| D5-C 幂等复跑 | ⏸ 待跑 | 机制已由 R66.1 受控实证 |
| D5-D 重审计(干净 baseline) | ⏸ 待跑 | **本轮四重点测量为其提供输入口径**(unit_type/figure/flags/稳定性四账) |
| D5-E 语义去重 | 🔒 冻结 | 72 collisions(66 同名异字节 + 6 字节全同)零裁定 |
| needs_ruling | ⏳ **6 份等 Owner 逐份裁定**(月考/答案/初三卷等) | `data/d5b_reclassify_plan.json` needs_ruling 桶 |

**本轮新增证据(并入 D5-D 输入)**:daemon 运行使未恢复图片积压持续增长(499→1,396 份),D5-D 重审计时点应同时统计该账;unit_type 单点异常在 v2 可消费面内,D5-D 前修复可使干净 baseline 不携带已知噪声。

## §6 武器缺陷与边界(如实)

- **F-DQ-1(武器口径缺陷,当轮发现当轮修)**:首版对账误用 IR 顶层 `file`(annotated 路径)计算 sha,得 10/10 假 mismatch;正确对象 = `ir.source_file`(源树路径)。修正后 **71/71 全量对账零漂移**。若不修,本报告会把完好的稳定性误报为系统性漂移——"审计工具必须先被真实数据校准"家族(R49/R53/R54/R55/R59/R62 后第 7 次)。
- **F-DQ-2(同轮修)**:sha 键检测正则 `"([a-z_]*sha...)"` 把 `"shared"` 误命中(850 处假阳性);改为精确键遍历后真实值 = 0。
- 边界:悬空图片归因按"当前 `_imgs/` 树在位性"判定,不含 PDF 本身缺图的情形(R58 已单列 499 份无引用族);flags 测量基于 R52 审计面 IR(唯一真实 IR 工件),非全语料重解析。

## §7 待 Owner 裁决清单(本轮零执行)

1. **unit_type 单点修复**(§1 选项 B):批准后按 R31 迁移先例执行 + 留报告;
2. **recover_images 批量恢复**(§2):批准范围(建议 = 1,396 份悬空文件)与批次切分;
3. **flags 登记入 rule_registry**(§3):批准后加词条 + 双向钉;
4. **BUG-14-DATA 剩余闸门**:6 份 needs_ruling 逐份裁定;D5-C/D 排期;D5-E 启动裁决;
5. 知会:Claude Consumer Review 可基于本报告 §1~§4 核对 Integration Contract §2/§3 的消费面描述(契约按 Owner 明令**保持 DRAFT 不冻结**)。

---

*v1 · 2026-09-15 · DSH(preprocessing)。全部数字可由 `data/preprocessing_data_quality_scan.json` + `scripts/dq_data_quality_scan.py` 复现;两处武器缺陷已修正并如实入账。*

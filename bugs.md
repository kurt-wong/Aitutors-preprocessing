# 缺陷记录 (bugs.md)

> **用途**：记录项目出现过的每一个 bug / 缺陷 —— 现象、根因、位置、解决方案、教训，供避免复发与回溯。
> **格式约定**：分「待修复」与「已修复」两区；每条 `BUG-{nn}` 带 状态/级别/现象/根因/位置/解决/教训。
> **更新规则**：新 bug **追加到对应分区末尾**并附**登记时间戳** `YYYY-MM-DD HH:MM`；状态变更（待修→已修）追加时间戳更正，不改写历史。
> 本文件存量条目均登记于 **2026-09-11 00:36**（回填）；此后每条自带时间戳。修复后从"待修复"移入"已修复"并补 解决+教训。相关轮次见 `log.md`。

**级别图例**：🔴 正确性/数据损坏　🟠 功能/规模化阻塞　🟡 运维/安全/卫生

---

## 一、待修复（Open）

### BUG-11 · 图片恢复目录覆盖落后于重归类　🟠
- **状态**：✅ 修复（2026-09-13 R58，用户指令"开BUG-11"；数据卫生轮序 11→14→15 第一项）
- **现象**：`高考真题/合格考/会考/竞赛自招/其他汇编/学业水平考试` 目录里的缺图文件无法增量修复。
- **根因**：`recover_images.py:48` 的 `SCAN_DIRS = ["高一","高二","高三","未分类"]`；而 `reclassify_unknown.py` 已把 599+ 份迁出到上述新目录，且 OCR 仍在产出缺图新文件（`batch_convert_pdf` 不下载 `outputImages`）。
- **位置**：`scripts\recover_images.py:48`。
- **解决（R58）**：废弃白名单，改为**"排除派生目录，其余顶层目录一律为源"**（单一来源）——`EXCLUDED_TOP_NAMES={"_imgs",".cache"}` + `EXCLUDED_TOP_PREFIXES=("auto-annotated","reslice")`，`scan_md_files(root=OCR_ROOT)` 遍历全部顶层目录。故障方向被翻转：未来新增源目录**自动纳入**（原缺陷形态不可能复发），误纳派生目录的代价只是多扫（已重写/无引用幂等跳过），不会漏修。顺带把 `import fitz` 改惰性导入（`_fitz()`），扫描/干跑/CI 离线可用（CI 不装 PyMuPDF）。
- **修复证据（全部实测）**：① 视野 2,421→**3,119** 份（新可见 **698**：高考真题 599/合格考 71/会考 17/竞赛自招 6/其他汇编 4/学业水平考试 1，`data/r58_bug11_coverage.json`，只读测量）；② dry-run 端到端 3,119 份零异常，统计与证据脚本逐项一致（with_refs 499/already_done 2182/pdf_miss 0），账目文件备份-还原 sha 闭环；③ 回归钉 `tests/test_recover_images_scan.py` 5 用例（合成契约 t1–t4 + 真实语料冒烟 t5），变异 M1 回退旧白名单 → t1+t5 双拦、M2 去 `_imgs` 排除 → t2+t4 双拦，还原后 5/5 过；全套件 184 passed + 1 xfailed。
- **⚠ 实测修正（防夸大）**：盲区 698 份中**当前缺图候选 = 0**——迁出文件在迁移前（还在旧目录时）已被恢复（高考真题 515/599 已标记 `_imgs`，余 84 无引用）。本 bug 的现实危害是**流程性潜伏风险**（今后带悬空引用的文件一经重归类即逃出恢复视野），而非既成数据缺失。当前 499 份/10,439 处缺图积压**全部在旧视野内**（OCR 新产出的常规增量积压，未分类 129/高二 136/高三 130/高一 104），是否执行恢复跑属独立决策，未在本轮擅自执行。
- **教训**：一个流程改了目录布局，凡硬编码目录白名单的其它流程都会静默失配；目录清单应单一来源或全树遍历。**且"修复覆盖盲区"与"盲区内恰有欠账"是两件事**——修复价值要用真实数据分别度量，别拿潜伏风险冒充已挽回损失。
- **⚠ R59 对抗性审查更正（2026-09-13）**：R58 台账措辞"误纳派生目录的代价只是多扫（幂等跳过），不会漏修"**经实测证伪**——无排除政策下 **84 份派生 md**（auto-annotated-v3 82 + reslice-batch-C 2，含裸 `imgs/*.jpg` 且 basename 命中 PDF 索引）会被 `process_one` **真实处理**（提取图片 + 就地重写 + 审计记录），不是只读扫描。**当前代码行为正确**（11 个派生目录全被现有排除表覆盖，现实风险=0），错的是反事实代价评估：机制性残余风险 = 未来新增**前缀不匹配**的派生目录会被误纳并就地重写。不改排除制（改回白名单即复发本 bug），以措辞更正 + 风险登记收口。**风险已按用户裁定登记为 RISK-FUTURE-001（GOVERNANCE/Boundary,非生产缺陷,不进缺陷统计）,见 `governance/risk_register.md`**。R59 其余复证：视野账目 3119/2421/698 独立重算全对账；盲区 0 缺图在扩展语法下稳健（12,316 处 `src` 全指 `_imgs` 且落盘在，悬空形态 0）；dry-run 重跑统计逐项复现 + 账目 sha 闭环；变异 M3–M6 补 4 组全咬合。明细 `log.md` R59 / `data/r59_r58_review.json`。

### BUG-14-DATA · 未分类"跑步机" + 重复源(原 BUG-14)　🟡
- **状态**：待修复
- **⚠ R61 命名拆分(用户 R60 审核裁定,不重写历史)**:原 BUG-14 与 R60 执行的"BUG-14 第一阶段(事实一致性攻击)"是两件事。按用户裁定:**历史引用 BUG-14 保持稳定**,本条定名 **BUG-14-DATA**;事实一致性轨道另立 **BUG-14-CHAIN**(见下)。未来"BUG-14-DATA CLOSED"只指数据卫生关闭。(R60 期间的命名澄清记录见 log.md R60,不改写。)
- **⚠ R60 命名澄清（2026-09-13）**：用户 R59 审核裁定的下一轮"BUG-14 第一阶段"经实测核对为 **Source → Resolver → IR 事实一致性攻击**(已于 R60 执行完毕,证据 `data/r60_fact_drift_attack.json`),与本条登记的**数据卫生问题**(未分类跑步机 + 73 重复 basename)是两件事。本条保持开放、顺延;命名冲突留待用户裁定是否重编号。
- **现象**：`未分类` 目录现存 145 份且**仍在接收**（OCR 日志实证 `未分类/历史/2012-2021高考真题汇编…`）；`status.md` 曾误称"已清除"。全库 **73 个重复 basename**（多为高考真题汇编），会重复 OCR/重切/入题库。
- **根因**：`batch_convert_pdf.py:75-88` 的 `extract_grade_subject` 对文件名不含年级的 PDF 默认落 `未分类`；重归类清过一次又被 OCR 灌回。重复源来自同一 PDF 在根目录与子目录各存一份。
- **位置**：`ocr_service\batch_convert_pdf.py:75-88`；`Ocr-markdown\未分类\`。
- **解决**：① OCR 端按源 PDF 相对路径归位，或定期跑 `reclassify_unknown`；② 去重 73 份（保一份、归档另一份）。
- **教训**：上游不断产出时，"清理目标目录"是治标；要么改上游归位逻辑，要么周期任务；重复源须在入库前去重。

### BUG-14-CHAIN · Source→Resolver→IR 事实一致性轨道(用户命名"BUG-14 第一阶段")　🟢 PHASE-1 DONE
- **状态**：第一阶段 ✅ 完成(R60 执行,用户 R60 审核裁决通过);**后续扩面暂缓**(用户裁定:F1 已证明价值,先稳定,F1→F2→F3 是规则膨胀路径)
- **登记**：2026-09-13(R61 命名拆分落地;R60 期间以"BUG-14 第一阶段"名义执行)
- **第一阶段结论(R60)**:四攻击面无一静默漏网——A 字节篡改由 C8 整文件锚点保真拦(F1 区级不变量对 span 外漂移如实 MATCH,C8/F1 互补);B 越界 REJECTED_STALE、界内平移 resolver 静默属契约(已写入 G-TRUTH-1/附录 D.5)而 F1 捕获;C provenance 断裂抓获 BUG-31(已修复);D "QC PASS+ADMITTED 双绿而答案错归属"坐实,F1 为唯一防线。证据 `data/r60_fact_drift_attack.json` + `tests/test_r60_fact_drift.py` + 变异 M1–M7(R60 M1–M3 + R61 M4–M7)。
- **架构结论(用户 R60 审核裁决原文级)**:QC/Resolver/F1 不是重复防线,是不同层级的不变量保护;Resolver Admission ≠ Semantic Truth Validation(契约附录 D.5 G-TRUTH-1)。
- **关闭条件核对**:① 契约澄清落地 ✅(D.5);② BUG-31 修复 ✅(R61);③ 用户第一阶段验收 ✅(R60 裁决)。**本条作为轨道登记保留,不再扩面**;重启须用户裁定并新开轮次。

### BUG-04-residual · 括号式裸 LaTeX 漏网（105 行）　🟡
- **状态**：待处理（BUG-04 收紧正则的取舍代价）
- **现象**：`Fe(OH)_{3}` 这类带括号的化学式未被自动包 `$`（TOKEN 不含 `()`）。
- **解决**：半自动/人工处理这批 105 行（连同复杂类 610 行）。
- **教训**：不吞句读 vs 不漏括号式是取舍；靠人工兜底而非放松正则（放松会复发 BUG-04）。

### BUG-15 · 全库既存的"半定界"数学（$ 岛 + 岛外裸命令）　🟠
- **状态**：待处理（修 BUG-09 时实测发现，**既存**、非工具引入）
- **登记**：2026-09-11 00:48
- **现象**：大量行同时含 `$…$` 数学岛和散落岛外的裸 `\命令`，如 `$NH_{3}$\cdot $H_{2}O$`、`…\therefore…$a_{n}$…`、`$x$\quad$y$`。岛内渲染、岛外命令当字面文本 → 数学渲染不一致/破损，数/化/生最重。
- **规模（实测全库 3120 份）**：**1490 份 / 23,221 行**。高频残留命令：`\quad`(3.8万) `\frac`(2.7万) `\mathrm`(1.3万) `\left/\right`(1.4万) `\sqrt`(7千) `\therefore`(6千) `\times`(5千) `\cdot`(4.9千) 等。
- **根因**：源（OCR/原始）本就半定界；`corpus_scan` 与 `fix_bare_latex` 都 `if "$" in line: continue`，**双双跳过含 `$` 行**，故这批既看不见也修不着——此前"裸 LaTeX 954 份/5528 行"仅是**无 `$` 子集**，严重低估了数学债。
- **位置**：全库；`scripts\corpus_scan.py:44`、`scripts\fix_bare_latex.py:52` 的 `$` 跳过逻辑是盲区来源。
- **解决（未做，需用户定向）**：半自动"整段定界"——按公式段而非按词元，把含裸命令的段整体包 `$…$`（CJK 段用 `\text{}`），或交渲染前归一化。工程量大，须先小样验证 KaTeX 兼容再批量。
- **教训**：质检工具的"跳过已处理行"优化会造成**系统性盲区**；量化缺陷前先确认检测器覆盖了全部形态（含 `$` 行）。多数 `\quad/\times/\cdot/\therefore` 是外观退化，`\frac/\sqrt/\mathrm/\left\right` 是结构性破损——可分级处理。
- **⚠ 规模修正与方案重估（2026-09-11 09:23 · R12）**：原登记数字 **23,221 系检测器 bug 虚高**——检测器用 `re.sub(r"\$[^$]*\$")` 剥岛时，把 `$$…$$` display 块误当空内联 `$…$` 剥掉，块内命令被判"岛外"（含 `$$` 块行 23,154 行即虚报来源）。**正确检测（先剥 `$$` 块、再剥内联 `$`）后真正半定界仅 1,476 行**。构成异质：`\quad` 选项间距 463（岛外排版命令）+ 表格 `\n` 残留 291（**非数学，误报**）+ 跨行 `\begin/\end` 块 480（需多行感知）+ OCR 错乱/裸化学式/`\text{}` 混排 ~240。**"整段定界（CJK 用 `\text{}`）"方案经实样检验基本不适用**（这些行是中文叙述+散落数学+OCR 错乱混排，整段包 `$` 会让中文进 math 模式大量报错）。**须重新分类后分别处置，勿批量整段定界**。
- **处置进展（2026-09-11 10:14 · R13）**：按分类处置——**SPACE（岛外 `\quad/\qquad`→全角空格，状态机保证数学岛内不动）+ TABLE（表格字面 `\n`→`<br>`）已修 832 行**（space 456 + table 376）。工具 `scripts\fix_half_delim.py`，审计 `data\bug15_fix_log.json`（含每行 before/after，可回滚）。验证：状态机岛内保留/岛外改/混合均正确；lint 前后对比无回归；幂等重跑=0。**残留 714 行**：主要为 BLOCK（跨行/`\begin\end` 被错误 `$` 定界打断，需多行感知）454 + COMPLEX（OCR 烂行）228，**留档待人工/专门设计**，不阻塞吞吐/定价测试。
- **⚠ R14 对抗性审查修正（2026-09-11 10:56）**：审查发现 **TABLE 修复有缺陷**——`line.replace("\\n","<br>")` 未保护 `$` 岛，拆坏数学命令 `\nearrow`（67 处确证，在 `$ \nearrow` 岛内）；且"命令 vs 换行残留"无法可靠自动区分（叠加货币 `$`）。**table 376 已整体回滚**（审计还原，验证 table 全=before / space 全=after）。**space 456 经状态机独立验证（8/8 用例 + 全 record 自洽）正确，保留**。表格 `\n` 换行残留并入待人工。**当前生效：space 456；table / BLOCK / COMPLEX 留档**。
- **⚠ R15 第二轮审查修正（2026-09-11 11:28）**：进一步发现 space 亦非零误改——`$` 错乱（货币/OCR 孤立 `$`）与真岛交错时状态机误改岛内 `\quad`（C1 反例 `costs $5 then $a \quad b$` 确证）。块感知检测：31288 处替换中**3 处误改**（display 块内孤立 `$` 翻转），已**精确回滚，space 达零误改（保留 453）**。教训：`$`计数岛判定在 `$`错乱时必失效；改进方向=修复前跳过 `$` 错乱行。**当前生效：space 453 零误改；table / BLOCK / COMPLEX 留档**。

### BUG-21 · `--file`/`--pilot` 调试跑覆盖批量账目 JSON　🟡（工具/记账）
- **状态**：✅ 修复（2026-09-12 R28，用户指令"先修复 bug"）
- **现象**：`reslice_pipeline.py --file <src> --out <dir>` 的 `--out` 只重定向**产物**目录；结果账目恒写 `data/reslice_pilot_result.json`（`main()` 629 行，非 batch 模式无条件走该路径）→ 一次单文件调试跑把 16 份试点账目覆盖成 1 条。R27 真 LLM 冒烟实际触发，靠 `git checkout` 恢复（建仓第 3 天即回本）。
- **影响**：账目丢失（可恢复，git 已追踪）；若发生在未追踪时期即不可逆。全量/批量跑不受影响（batch 模式走独立 `reslice_{tag}_result.json`）。
- **修复（R28）**：路径选择提为纯函数 `derive_run_paths(out, batch)`——**凡 `--out` 独立输出，log/result 一律跟随输出目录名派生**（与 R23 batch+`--out` 既有语义统一）；默认账目只在不带 `--out` 的正式跑（pilot/batch-C）时写。回归测试 `tests/test_run_paths.py` 4 用例：纯函数契约 3 + **真实子进程集成 1**（无配置环境跑 `--file --out`，LLM 必失败，断言账目落派生路径且 pilot 账目/日志根本不被创建）。mutation M4 回退旧行为 → 单元+集成双咬住。**集成测试附带抓出第二个缺陷**：账目目录假定存在，fresh checkout（含 CI）无 `logs/`、`data/` 时 `open()` 崩 → 补 `mkdir(parents=True)` 兜底（含 `logs/reslice_debug`）。
- **教训**：调试入口与生产入口共享写路径 = 定时炸弹；"输出隔离"必须覆盖**全部写路径**（产物+账目+日志），R23 给 fixer 加 `--out/--log` 时漏了 pipeline 自身。

### BUG-22 · 大题内编号被当全卷题号 → 题号重复归属（8/50 真实产物）　🟡（Phase 1 关闭 / 建模 OPEN）
- **状态（第五轮审查分层裁定,R32 记账）**：Prompt defect 🟢 CLOSED / QC detection 🟢 CLOSED / batch-C migration 🟢 CLOSED / **resolver identity model 🟡 OPEN** / **V3 canonical identity integration 🟡 OPEN**。系统性根因(QuestionIdentity 未进入 resolver 正式模型)的修复设计见 `question_identity_design.md`(R32 设计评审稿),实现属 Phase 2 实施任务。
- **⚠ R33 更正(2026-09-12)**:"QC detection 🟢 CLOSED" 需限定口径——回迁突变实测 scoped C13 对 BUG-22 原始回归形态(跨分节重号)漏放 6/7,检测能力实际有洞,已登记 **BUG-23**;R31 的"C13 残留 0"结论只证明存量已修,不证明守卫仍有效。
- **⚠ R34 状态重述(第五轮审查裁定,正式执行)**:撤销"QC detection CLOSED"——**存量问题已修复;检测守卫直到 BUG-23 关闭前不得宣称 detection closed**。R34 BUG-23 已修复(v2 守卫真实数据 7/7 复拦)后,状态为:原始 prompt defect 🟢 / batch-C 存量 🟢已迁移 / C13 最终检测器 🟢(v2,含回迁突变复验)/ **Resolver Identity 🟡 等 resolver 消费 v2 模型**(preprocessing 侧身份模型已落地,resolver/IR 集成属下游)。v1 历史产物(pilot 等)仍走旧语义,回填列为后续任务。
- **发现**：第三轮审查（R29）指示专攻"结构合法但语义错误"；`scripts/semantic_probe.py` 对 batch-C 50 份真实 LLM 产物零成本测量,P15 报警经人工逐条分诊确证。
- **确证证据**：① 合格考化学（第一次）：选择题 Q1-Q9 与非选择题 N1-N9 **题号 1-9 各双重归属**（非选择题卷面用大题内编号"1.-9.",答案区实键 26-34,N1→26…N9→34 逐条对上）；② 全量普查：**8/50 文件（16%）**含重复题号。
- **根因(R31 确诊,R32 定性升级)**：不止"模型缺维度"——**prompt v2.1 第 247 行明确指示"分节各自从 1 编号…按原样照抄题号即可"。正式定性:Prompt Contract 与下游 Identity Contract 不一致(Prompt Specification Defect),LLM 是正确遵循,不是模型理解错误。**
- **第四轮审查核心裁定(R31 执行)**：重号并非总是错误——选考模块（"任选一个模块作答",三模块印刷号 1-3 本来就相同）与教师用书汇编（各考点块独立编号）的重号是**合法真实形态**。因此:
  1. **C13 升级为 Scoped Question Identity**:身份键 = (section, 题号),同分节重复 FAIL、跨分节同号放行;无 section 字段的存量数据退化为全卷判定。契约测试 +3(同分节报/跨分节放/无 section 报)。
  2. **Prompt v2.2**:"分节照抄"条款删除,改为"题号身份必须全卷唯一,以答案区键位为准,无键位按分节顺延";输出 schema 新增 `section` 字段;版本号两处升 v2.2。
  3. **确定性迁移(方案 C,零 LLM)**:`scripts/fix_bug22_renumber.py` 读旧 manifest → 写新 manifest + 重编译 annotated/切片,变更全部记 `data/bug22_migration_report.json`(旧值/新值/证据)。三条证据驱动规则:answer_key(答案区键位 26-34)、shift(运行最大值顺延:生物+40/地理+50/英语+25/博雅 11-15/化学必答 26-31,与 LLM 自身 unit_id 命名互相印证)、keep(选考模块/汇编保持印刷号,凭 section 区分)。默认 dry-run,落盘前强制 scoped 唯一性断言。**迁移后 batch-C QC 重跑:C13 残留 0 份,38/50 PASS**(回到 C13 引入口径,4 份 FAIL 均为既有 C3/C5/C6 缺陷,与题号无关)。
- **迁移实测踩坑(教训)**：① 汇编 manifest 的 unit_id 大量重复,分节归属必须按**单元位置**分配而非 unit_id 为键;② 消歧序号必须按**标题出现次序**分配而非单元计数;③ `[答案]` 写成字符类会把含"方案"的"考点3 制备实验方案"标题误杀,OCR 丢 `##` 前缀的裸考点标题需单独匹配。
- **防回归**：`tests/test_bug22_migration.py` 7 用例锁定三条算法 + scoped 断言双向语义 + 同名标题消歧;mutation(shift -1)被测试拦截后回退。
- **方案 B(manifest section 字段 + (section,number) 复合键进 resolver/IR)按审查意见并入 Phase 2 resolver 正式设计**,不在本轮打补丁。
- **教训**：**"QC 全绿"≠"切分正确"**;而修复此类缺陷时**必须先辨认合法重号形态**,否则全局唯一性检查会把真实的选考模块/汇编结构误判为错误——检测器的假阳性与假阴性同样致命。

### BUG-23 · scoped C13 对 BUG-22 回归形态失去守卫(跨分节 canonical 重号漏放)　🔴（语义/QC 守卫漏洞）
- **状态**：✅ 修复(2026-09-12 R34,Phase 2 实施;正式定名 **C13 Guard Soundness Failure:Scoped Identity 被错误当成合法性证明**)
- **修复(R34)**：QuestionIdentity v2(`scripts/question_identity.py`,QC/回填/resolver 共用同一验证):**划分语义**——非 keep 持有者之间 canonical 全卷唯一;keep 为**个体豁免**(会考化学实测:选择题 1 与选考模块 keep 1 天然同号,故不能要求"重复各方全 keep"),但每个 keep 必须携带可回源证据(`basis_evidence` 含 L{行号} 且界内),证据不足 → PENDING_REVIEW(证据不足 ≠ 非法,三态裁决);同分节重复永远 FAIL。batch-C 50 份确定性回填 v2(`phase2_identity_backfill.py`,0 fail);**真实数据回迁突变复验:A3 保留 section 7/7 全拦(修复前 1/7)、A4 缺 section 8/8 显式告警(修复前 0/8)**(`data/phase2_adversarial_review_r34.json`)。原 xfail 修复义务测试已转正(`test_bug22_cross_section_regression_is_flagged`)。
- **登记**：2026-09-12(R33,Phase 2 设计对抗性审查)
- **发现**:`scripts/phase2_adversarial_probe.py` A3 回迁突变——把 R31 迁移的 7 份真实产物题号全部回退到 old 值(BUG-22 原始形态:选择题与非选择题各自从 1 编号),跑**生产** `reslice_qc.check()`:**保留 section 字段时仅 1/7 被拦**(唯一命中是博雅语文,回退后恰成同分节重复);**删除 section 字段则 7/7 全拦**。
- **根因**：C13 身份键 = (section, 题号),跨分节同号一律放行。但 BUG-22 的原始形态**恰恰是跨分节重号**(选择 1-9 vs 非选择 1-9)——R31 的 scoped 升级在区分"合法重号(选考/汇编)"与"非法重号(BUG-22)"时,把"分节不同"当成了合法性充分条件,而真正判据应是**是否存在显式 keep 依据**。Prompt v2.2 修复后新产物靠 prompt 约束不复发,但 QC 层面对 section 标注数据已无回归检测能力——一旦 prompt 或模型再退化,缺陷将静默通过。
- **位置**：`scripts\reslice_qc.py:201-214`(C13)。
- **解决方向(不得盲修)**：canonical_number 全卷唯一 + `canonical_basis=="keep"` 显式豁免(选考模块/汇编);需要 manifest 增 basis 字段后实施,属 `question_identity_design.md` R33 修订版不变量 1。在 basis 字段落地前不可简单改回全卷唯一——会把合法选考/汇编重号误判(BUG-22 修复期已实证该假阳性)。
- **测试固化**：`tests/test_question_identity_adversarial.py`——`test_bug22_cross_section_regression_must_be_flagged` xfail(strict=True)(修复后 XPASS 强制失败提醒转绿);`test_section_field_is_sole_discriminant_for_bug22` 锁定分叉点。
- **教训**：**守卫升级必须做回迁突变验证**——修复缺陷后要把缺陷形态重新注入产物跑守护,证明"修复后的检测器仍能拦住原始缺陷"。R31 只验证了"C13 残留 0",没有验证"C13 还拦得住 BUG-22",这是检测器换键时的系统性验证盲区。

### BUG-24 · 分节标题过滤器误杀含"答案"note 的真实分节标题 → SectionLocator 假阴性　🟢 CLOSED（Source structure 层 / R37 修复 + R38 独立对抗复核 / 2026-09-13 用户裁定关闭）
- **状态**：🟢 CLOSED(R36 发现并上报;用户裁定"应修、现在修、作为独立 SectionLocator correctness 修复,不得顺手重设计 Identity/keep 语义";R37 执行修复;R38 独立对抗复核后修复成立;2026-09-13 用户裁定 B24-01~08 全部 🟢,正式关闭)。**三概念分账(用户裁定,不得混写)**:① BUG-24 correctness 缺陷 = **CLOSED**;② 3 例 straddle 跨界标题(书面表达参考答案/等级评分标准/【点睛】答案要点) = **ACCEPTED KNOWN BOUNDARY**(当前确定性规则无法在保 precision 下提 recall,非 BUG,扩窗 11 实测误杀合法标题);③ 1 例 OCR 行融合(标题与 `1.【答案】B` 同行) = **ACCEPTED OCR LIMITATION**(源缺陷,非 BUG)。**"BUG-24 closed, all heading detection issues resolved"无证据,不成立**。保留独立决策点:三十一中化学 Q1-11/F1-11 keep 三方裁决(不被本关闭吞并,B24-04 已固化不得自动豁免)。
- **发现**：R36 pilot v1→v2 确定性迁移 dry-run——`2021北京三十一中高一（下）期中化学`被 C13 拒写(单选题 1-45 与填空题 1-11 落进同一分节 → 11 组同分节重号)。人工回源核查:该卷 L324 `## 二、 填空题(共11题,共计55分) 注意:只有填写在答题纸上的答案才计分。`是**真实分节标题**(填空题独立局部编号 1-11,卷面结构合法),但 `question_identity._heading_rows` 的 `答案|解析|评分` 排除器对**整行**做子串匹配,标题尾部 note 含"答案"→ 整个填空题节被误杀,F1-F11 落入 S1(单选题节,L11-519)→ 同分节重号 FAIL。
- **定性**：SectionLocator 假阴性(真分节未被建模),不是该卷数据缺陷;该卷 v1 legacy 同样 FAIL(无 section 退化全卷),**裁决无翻转,无非法 PASS**——缺陷是"FAIL 的理由错了 + 修复后仍需 keep 裁决",不是"漏放"。
- **修复阻碍(为什么本轮不动)**：排除器收窄(仅当 marker 位于标题头部才排除)经全语料实测:**batch-C 50 份中 ≥3 份**已提交 v2 产物的 section 划分会改变(会考化学 L287 二、选答题 / 春季会考数学 L5、L198 一、…备选答案 / 平谷历史 L19 一、选择题…),牵动 612 个 SectionLocator 中的对应条目、R34/R35 证据链与回填幂等口径;naive 收窄更会把 135 行【解析】/☑答案 误升为分节。修复 = 重划 batch-C section + 重跑回填与 QC 全链复验,应作为独立受审变更执行。
- **次要层(修复后仍在)**:即使填空题节被正确建模,Q1-11 与 F1-11 是**两个非 keep 跨节重号**,v2 划分语义仍 FAIL——需 R31 式三方裁决(是否 keep+证据)或对该卷单独重切,不能由确定性回填自动豁免(自动 keep 正是 R33 攻击过的"信任字段"陷阱)。
- **教训**:答案/解析/评分子串排除器是"为答案区标题设计的过滤器"被"note 含关键词的真实分节标题"击穿——**排除规则的作用域必须限定在 marker 语义位(标题头部),而不是整行任意位置**;pilot 迁移这类"低治理"存量是发现长尾结构形态的高产探测器。
- **R37 修复(只动 Source structure 层)**：排除器改**两阶段结构角色识别**——先结构归一化(剥 `#{1,6}`/第X部分/中文数字与印刷题号序号前缀/括号装饰符到不动点,`_norm_heading_head`),再只在归一头部前 10 字符窗口内判 marker(`_is_answer_heading`)。marker 集不变(答案|解析|评分),不新增 QC 规则,不动 keep/basis/C13/C14 语义。修复证据(全链):全语料盘点 3120 源卷,恢复 848 行、**0 行答案内容行误升**;reslice-scope 恢复 13 行(6 条真分节标题 + 7 条源结构标题,逐条人检,`data/bug24_exclusion_inventory.json`);**11 份已提交 manifest 重生成**(batch-C 7 + pilot 4;三十一中仍被 C13 如实拒写故字节不变);QC 裁决集**零翻转**(batch-C 38 PASS/12 FAIL、pilot 15/1 FAIL 与修复前逐文件一致);二次重跑字节级幂等 66/66;NEW-OLD 逐文件 diff `data/bug24_fix_report.json` + before/after 快照对;验收 `tests/test_bug24_section_locator.py` 13/13(B24-01~08 + 变异 sanity:整行排除回灌/窗口归零/窗口无限三类破坏全被数据区分力拦截)。
- **修复后状态(诚实边界)**：三十一中化学 FAIL 理由从"同分节重复归属"(错误建模)变为"跨分节重号含多个非 keep"(正确建模)——Q1-11 与 F1-11 仍需 R31 式三方裁决(是否 keep+证据),确定性回填不得自动豁免(B24-04 已固化);残留假阴性:纯 topic 词标题(`## 解析几何`,全语料 1 例,汇编卷)仍被排除——marker 词义歧义,不为 1 例扩大规则面。
- **R38 对抗性审查(强制复核 R37 全部结论;上一行与"R37 修复"行中的"0 行答案内容行误升"以本行为准)**:8 个攻击面独立复核——A2 QC issue 明细级 NEW-OLD(66/66 零差异)、A3 全单元 basis/printed 漂移(0)、A4 其它产物目录 v2 存量(0)、A6 结构完整性(新增 start_line 恰等于 13 条恢复行、丢失 heading 0)、A7 生产代码独立复现(44211/10899/848/13 逐位吻合)全部通过;**A1 证伪 R37 的过强主张**:OCR 转义点(`26 \.`)击穿序号前缀剥离,8 例【答案】/【解析】/答案示例块被误升(全部 full-corpus 非提交范围,提交产物零影响)→ **已修**(序号前缀允许转义点,恢复面 848→840,4 条真实回归语料入库);**诚实残留 4 例**(straddle 跨界 3 + OCR 行融合 1,均 full-corpus):扩窗到 11 会误杀合法标题"综合题(40分)(答案书写在答题卡上)"(marker 恰在 9),按证据记录不硬修。另补 R37 遗留测试缺口:`--refresh-v2` FACTS 锚点守卫 3 条真实测试(漂移拒刷/缺锚拒刷/一致放行)。正确口径:**reslice-scope 13 行 0 误升(逐条人检)**;全语料 840 行含 4 例已知残留(0.5%),明细 `data/r38_audit_report.json`。
- **R38 教训**:全称主张(如"0 误升")必须**穷尽验证**后才可写下——shape 聚类抽样+人检只支撑"提交范围 0 误升",全语料主张需独立检测器全量重扫(R38 正是这样证伪它的);"marker 位置"这类数值边界要对边界位(8~12)逐行人检,防窗口数字是凑出来的。方法论已固化 `review_protocol.md` 规则 1。
- **R37 主张正式撤销(R40 补记,消除仅有 supersession 措辞的缺口)**:上"R37 修复"行中的"全语料恢复 848 行、**0 行答案内容行误升**"主张 **❌ RETRACTED**(R38 穷举复核证伪;2026-09-13 用户裁定撤销)。唯一有效口径:**提交范围 13 行 0 误升(逐条人检);全语料 840 行含 4 例已知残留(0.5%)**。

### BUG-25 · OCR 转义点 `\.` 击穿序号前缀剥离 → 8 例答案块被误升为分节标题　🟢 CLOSED（Source structure 层 / R38 修复）
- **状态**:🟢 FIX VERIFIED(R38 发现并修复;2026-09-13 用户裁定"正式判定为真实 BUG,现已关闭")。
- **发现**:R38 对 R37 的对抗性审计 A1——独立五类检测器全量重扫 3120 卷,229 条可疑行逐条人读,查出 `### 26 \.（12分）【答案】C`、`### 18 \.（8分）答案示例` 等 **8 例**:OCR 转义点 `\.` 使 `_NUM_PREFIX` 数字序号前缀剥离失败 → marker(【答案】/【解析】/答案示例)被推出归一头部窗口 → 整行被当作真分节标题恢复。**全部位于 full-corpus 非提交范围,66 份提交产物零影响**。
- **根因**:`_NUM_PREFIX` 正则数字后只接受字面 `[.、．]`,不接受转义形态 `\.`——机械性缺陷,非窗口/规则面问题。
- **修复**:序号前缀允许转义点(`\d{1,3}\s*\\?\s*[.、．]`);恢复面 848→**840**(恰减 8,与缺陷计数严格对账);**66 份提交 manifest 重生成后字节零变化**(与已提交 after 快照逐字节一致);4 条真实 `\.` 行入 `tests/test_bug24_section_locator.py` B24-02 回归语料。修复后全量重扫数字逐位吻合(840/10907/13)。
- **教训**:正则类源结构规则必须有"同一字符的转义/全半角/变体形态"专项攻击面;R37 的抽样人检未覆盖该形态,直到穷举审计才暴露——规则 1(全称命题必须穷尽验证)的直接实证。

---

### BUG-31 · resolver/QC 对缺 `source_file` 的 manifest 非 fail-closed(三组件崩溃)　🟡（Resolver 边界 / R60 发现 / R61 修复）
- **状态**：✅ 修复(2026-09-13 R61,用户 R60 审核裁定批准;修复边界=只加显式失败态,禁 fallback/禁补 source_file/禁猜路径/禁降级 ADMITTED)
- **登记**：2026-09-13(R60,用户 R59 裁定的 Source→Resolver→IR 攻击面 C)
- **现象**：manifest 缺 `source_file` 键时三组件全崩,无一 fail-closed——resolver `man.get("source_file") or ""` → `Path(".")` 存在性为真 → `read_text` 崩 **PermissionError: Permission denied: '.'**;`reslice_qc.check` 直接 `man["source_file"]` 崩 **KeyError**;`audit_f1_consistency.check_file` 同 resolver 家族崩溃。批处理中一份坏 manifest 即杀死整批,且错误信息("Permission denied: '.'")完全失焦,不指向真因(source_file 缺失)。
- **位置**：`scripts/resolver_reference.py`(resolve_file 源读取);`scripts/reslice_qc.py`(src_of 裸下标);`scripts/audit_f1_consistency.py`(check_file 源守卫)。
- **性质定性**：数据安全无损(崩溃 ≠ 静默 PASS),但违反 fail-closed 契约族(C-FAIL-1/2:不可计算必须以机器可读理由拒收,不得崩)。
- **修复(R61,三处,全部只加显式失败态)**:① resolver:`src.is_file()` 守卫 → MISSING("source_file missing or not a file (provenance break, fail-closed)"),另加 `OSError` 兜底 → MISSING("source unreadable");② QC:**新 C15**(规则登记册 §1 已登记,CI 双向钉住范围 14→15):provenance 缺失/非文件 → 显式 **FAIL**(verdict 三态内,不是新裁决态),`src_of` 改 `.get`;③ F1:`is_file` 守卫 → DRIFT(note 显式)。**未新增任何 fallback/猜测/路径补全,未降级任何 ADMITTED**。
- **修复证据**:t7 转正(strict xfail→普通通过,断言三层全显式失败态 + QC 理由含 C15)+ **t7b 新增:批处理继续**(一份坏 manifest 不杀整批:{ADMITTED:1, MISSING:1});变异 M4(resolver 守卫回退)/M5(QC C15 回退)/M6(F1 守卫回退)/M7(登记册范围回退致 C15 幽灵行)4/4 咬合,还原后文件逐字节一致。M4 附带实证:resolver 的 is_file 守卫与 OSError 兜底互为双层,单层回退仍 fail-closed(t7b 如实过),t7 靠理由串区分两层。
- **教训**：fail-closed 必须覆盖**自身**的每一条 I/O 路径,不能只包下游调用;`Path("")` 的存在性语义是 `.`(目录恒存在),`or ""` 默认值不是安全网,是通往目录读取的暗门。

### BUG-32 · 非字符串 `source_file`(int/dict/list/bool)三组件 TypeError 全崩 + 批处理整批死　🟠（Resolver 边界 / R62 审查发现 / 待裁定）
- **状态**：**PENDING_REVIEW**(R62 对抗审查发现;R62 不擅改生产件,修复方案待用户裁定)
- **登记**：2026-09-13(R62,BUG-31 修复边界的对抗延伸:值类型攻击面)
- **现象**：manifest `source_file` 为非字符串 JSON 值时,三组件全部 `TypeError: argument should be a str or an os.PathLike object ... not 'int'` 崩溃,无一 fail-closed;批处理 `resolver_reference.run()` 一份此类 manifest 即杀死整批(L254 列表推导无逐文件兜底)。实测 K7(int)/K8(dict)/K9(list)/K10(bool)四形态全崩,K13 批处理 BATCH_KILLED。
- **性质定性**：**预存缺口,非 R61 回归**(R61 前 `Path(123)` 同样 TypeError);数据安全无损(崩溃≠静默 PASS),但违反 C-FAIL-1(不可计算必须机器可读拒收,禁崩)。可达性:生产 `write_outputs` 恒写字符串,缺口仅经篡改/损坏/手编 manifest 触达——低概率,但 t7b 承诺的"一份坏 manifest 不杀整批"对本家族不成立。
- **位置**：三组件的 `Path(man.get("source_file") or "")` 家族构造点;`resolver_reference.run()` L254。
- **修复方向（待裁定）**：显式类型校验 `isinstance(str)` 否则同 MISSING/C15/DRIFT 家族;run() 逐文件兜底。禁 fallback、禁猜测(同 BUG-31 边界)。
- **证据**：`data/r62_boundary_audit.json` K7–K10/K13;义务钉 `tests/test_r62_boundary.py`(strict xfail,修复转正时强制翻绿)。

### BUG-33 · 源文件拒读(OSError)时 QC/F1 未兜底崩溃(resolver 已兜底)　🟠（QC/F1 层 / R62 审查发现 / 待裁定）
- **状态**：**PENDING_REVIEW**(R62 对抗审查发现;R62 不擅改生产件,修复方案待用户裁定)
- **登记**：2026-09-13(R62,BUG-31 修复边界的对抗延伸:文件系统态攻击面 K12)
- **现象**：源文件存在但拒读(Windows 独占句柄 sharing violation → `PermissionError`,沙箱内真实制造成功并实证)时:resolver 经 R61 的 `except OSError` 兜底 **MISSING("source unreadable ... fail-closed")** ✅(该兜底层首次获得活体实证,非纸面推断);但 QC `src.read_text`(C15 之后)与 F1 `check_file` 读源**无 OSError 守卫 → 两组件 CRASH**。
- **性质定性**：**预存缺口,非 R61 回归**(R61 前 QC/F1 同样裸读);违反 C-FAIL-1。可达性:文件被其它进程独占(OCR 守护写入中)/ACL 变更/网络盘抖动——低概率瞬态,但 QC 是冻结生产链组件,批处理中同样整批死。
- **位置**：`reslice_qc.check()` C15 之后的 `src.read_text`;`audit_f1_consistency.check_file` 读源 + `read_bytes`。
- **修复方向（待裁定）**：QC/F1 同 resolver 双层口径(C15 扩到"不可读"语义或新增守卫),只加显式失败态。
- **证据**：`data/r62_boundary_audit.json` K12(condition=PRODUCIBLE(PermissionError) 条件先实证后观测);义务钉 `tests/test_r62_boundary.py`(strict xfail)。

## 二、已修复 / 已规避（Fixed / Mitigated）

### BUG-01 · DSH 拉起的跨会话进程被杀　🟡
- **状态**：已规避（运维约定）
- **现象**：agent 用 `Start-Process` 起的 OCR 守护在 pwsh 调用返回后被 DSH 进程树清理杀掉；`schtasks` 注册被沙箱挡（`找不到路径`）。
- **解决**：常驻守护一律**用户手动启动**（`start_ocr_watchdog.bat` / 用户自己的 shell）；agent 只验证、不代起。
- **教训**：DSH 不适合托管长驻进程；守护与 agent 生命周期解耦。

### BUG-02 · 本地页数用量计数虚高　🟡
- **状态**：已修复
- **现象**：本地 `ocr_page_usage.json` 记 19105，API 侧真实 5881，导致误判额度用尽。
- **解决**：以 API 仪表盘为准把本地计数改写为 5881；确立"API 侧为最终闸门"。
- **教训**：本地计数是缓存不是权威；冲突时以外部真值校正。

### BUG-03 · BOM 破坏 JSON → 批处理退出 1 → 守护重试循环　🔴
- **状态**：已修复
- **现象**：改写用量 JSON 后 `batch_convert` 退出码 1，watchdog 报"转换进程退出，退出码: 1"并每 5 分钟重试。
- **根因**：用 PowerShell `Set-Content -Encoding UTF8` 写 JSON，**带 BOM** → Python `json.load` 崩 → `get_page_usage` 捕获异常返回 0 → 循环。
- **解决**：改用 Python `write_text`/`json.dump`（无 BOM）重写；确立编码铁律。
- **教训**：**凡 Python 读的 JSON 一律用 Python 写**；PowerShell 的 UTF8 带 BOM 是隐形炸弹。（已在 README/PRD 固化为铁律）

### BUG-04 · fix_bare_latex 贪婪 TOKEN 吞句读　🔴
- **状态**：已修复（残留见 BUG-04-residual；回归见 BUG-09）
- **现象**：旧宽松 TOKEN 把外围括号/句号吞进 `$`，产出 `($X_{CH4})$`、`$y=x^{2}.$` 等错位。
- **根因**：TOKEN 词元字符集含 `()` 与 `.`，贪婪匹配越界。
- **解决**：收紧为"基+`_{}`/`^{}` 核"（`fix_bare_latex.py:27`），刻意不含外围括号/句号。
- **教训**：dry-run 采样人工过目后再批量落地——正是这一步在大规模应用前抓到了吞句读。

### BUG-05 · OCR 伪标题 `## （3）进一步研究发现…`　🟡
- **状态**：已修复（源缺陷类）
- **现象**：生物西城 L331 的小问被 OCR 打成 markdown 二级标题，渲染成粗体 H2。
- **解决**：去掉行首 `## `；QC 16/16 复验通过。
- **教训**：OCR 会把正文误判为结构标记；`#+` 命中需人工甄别（全库扫描 39 处 `#+`，仅此 1 处为真缺陷）。

### BUG-06 · pdf_fidelity 近零覆盖率假象 + 系统性高假阳性　🟠
- **状态**：已修复（方法）+ 降级（定位）
- **现象**：① 初版 16 字符 shingle 精确匹配覆盖率仅 0.086（全盘假阴性）；② 改写后中位 0.988，但连地理散文 0.45 复核也是**假警报**（源文全有，只是 `20°W 和` vs `20W和` 的系统性表示差异）。
- **根因**：PDF 文本层与 OCR 有系统性差异（度数/空格/标点/分段/双重识别；PDF 反丢 π/矢量而 OCR 写全），精确+前缀子串匹配抗不住。
- **解决**：改写为散文段（归一化≥12 字符）+ 首/尾 10 字宽松匹配（中位 0.988）；**诚实降级为"仅粗筛排序，不作权威丢内容检测"**；源保真改靠"渲染预览 vs PDF"人眼比对 + C1–C10 + 图/公式定点 PDF 视觉核对。
- **教训**：工具不达标时诚实降级用途、不硬当权威；要可靠需改 difflib 序列对齐（工程大、收益不确定，暂不投入）。

### BUG-07 · 沙箱拒绝写 `Ocr-markdown`　🟡
- **状态**：已解决
- **现象**：裸 LaTeX 批量落地时 workspace-write 沙箱拒绝写 `Ocr-markdown` 下文件。
- **解决**：一次性 escalate 到 `danger-full-access` + justification；因流程幂等，可安全重跑。
- **教训**：涉及核心数据目录写入时预判沙箱边界；幂等设计让失败重跑零成本。

### BUG-08 · LLM 输出截断/损坏 + 编号类缺陷　🟠
- **状态**：已修复（内建于流水线）
- **现象**：LLM JSON 截断/损坏；子题编号漂移；分节重号卷跨节串号；卷末作文无题号。
- **解决**：`call_llm` 截断即抛错重试 + `extract_json` 容错解析（围栏/尾逗号/控制字符）+ 失败留档 `logs/reslice_debug`；无题号单元按全卷顺序自动补号；分节重号降级 warning + 答案单元内局部解析防串号。
- **教训**：LLM 输出永远不可信，必须确定性校验 + 容错解析 + 失败可回溯；分节重号是真实试卷形态，别当错误硬拒。

### 源/渲染缺陷（试点审中修，R4）
- **状态**：已修复
- render_lint 修复 **32 处** `alt="Image"" />` HTML 属性损坏（严格解析器会吞内容）+ **2 处**字面货币 `$` 转义（防 `$` 定界渲染器误吞）。
- 试点人工审核就地修：石景山语文 U9-12 material 边界、五十六数学 Q8 图文错序（x 坐标重排）+ Q9 配图漂移致包络吞题（extra 改卫星锚）、三十一中化学 Q27 双重识别 + Q39 丢行（PDF 文本层回填）。
- **遗留（历史）**：四十三中历史 4 题源缺答案；2 份化学 3 处 `\ce{}` 需消费方开 mhchem。

### BUG-09 · 裸 LaTeX 半包残损（R5 收紧 TOKEN 引入的回归）　🔴
- **状态**：已修复（2026-09-11 00:48 · R8）
- **现象**：R5 收紧 TOKEN 自动包 `$` 后，部分行"下标进了数学岛、命令留在岛外"，如 `Zn + $H_{2}SO_{4}$ = $ZnSO_{4}$ + $H_{2}$\uparrow`、`$NH_{3}$\cdot $H_{2}O$`、`…\xlongequal[\Delta]{催化剂}…`。**规模修正：实为 103 行**（早先报 36 系检测命令表过窄，漏了 `\uparrow/\triangle/\cdot/\rightarrow/\rightleftharpoons` 等）；分布 高一48/高三23/高二14/高考真题18，**无一在 `未分类`**（无 OCR 写冲突）。
- **根因**：收紧 TOKEN 只包"基+`_{}`/`^{}` 核"，不可包这些命令；`COMPLEX` 白名单漏 `\xlongequal` 等 → 本应整段跳过的行被"半包"。
- **位置**：`scripts\fix_bare_latex.py`（原 `:24,:27,:54`）；受损行见 `data\bare_latex_fix_log.json`。
- **解决**：① 按日志逐行**回退 103 行**（93 唯一行落地，10 为重复日志记录；每行先比对"当前==logged after"再回退）至修复前裸形态 → 审计 `data\bug09_revert_log.json`；② `fix_bare_latex.py` 加 `BARE_CMD` 防回归：仅当"数学岛外无残留 `\命令`"才落地，否则整行保留裸形态交人工。已加 `COMPLEX` 补 `\xlongequal`。
- **教训**：收紧正则修一类 bug 时须同步核查"不可包命令"白名单，否则从"吞句读"翻成"留残损"；**检测缺陷规模要用最宽命令表核实**（36→103 即因表窄）。回退前逐行比对当前内容==日志 after，确保确定性、可回滚。
- **顺带发现**：修复过程中实测出既存的**全库"半定界"数学债 1490 份/23,221 行**（见 BUG-15）——远大于本 BUG，且是 corpus_scan/fix_bare_latex 双双跳过 `$` 行造成的盲区。

### BUG-10 · 锚点同点 LIFO 闭合死逻辑　🟠
- **状态**：已修复（2026-09-11 06:23 · R9）
- **现象/根因**：`compile_anchor` 的闭合排序键 `-unit_start.get(x[1],0)` 中 `x[1]` 是闭合标签串而 `unit_start` 以 uid 为键 → 恒取 0，注释宣称的"LIFO"从不生效；同深度同行闭合（如共享答案表跨单元）会乱序。
- **解决**：`closes` 元组改带 span 起始行 `(depth, tag, rg[0])`，排序键改 `-x[2]`（同深度按起始行降序 = 后开先关）；删除死变量 `unit_start`。单测验证：Q1(answer[5,10]) + Q2(answer[6,10]) 同闭 line10 → `answer:end:2` 先于 `answer:end:1`（LIFO 正确）。recompile 16 份 + QC 仍 16/16 PASS。
- **教训**：排序/查表的 key 类型必须与字典键一致；C10 刻意不查严格嵌套，故这类 bug 只能靠代码审查 + 针对性单测，回归靠 recompile+QC 兜底。
- **复审补强（2026-09-11 08:49 · R10）**：对抗性复审发现 R9 的"起始行"方案在**两单元同起同止**（共享完全相同区间，如整张共享答案表）时仍交叉非法——起始行相同无法区分先后，实测产出 `start:1,start:2,end:1,end:2`。根治：改用**全局注册序号** `_seq`，opens 按 `(depth,order)` 升序、closes 按 `(-depth,-order)` 降序（后注册先关）。复测：不同起止 + 同起同止**均合法嵌套**，recompile+QC 16/16 PASS（退出码 0）。

### BUG-12 · 守护进程 stdout PIPE 死锁　🟡
- **状态**：已修复（2026-09-11 06:23 · R9）
- **现象/根因**：`ocr_watchdog.py` 用 `stdout=PIPE` 拉起转换子进程却从不读，子进程 `print(flush=True)` 写满管道缓冲即阻塞；watchdog `poll()` 恒 None、60s 空转、无法察觉停摆。
- **解决**：子进程 stdout/stderr 改 `subprocess.DEVNULL`（batch 的 `log()` 本就落盘 `ocr_batch_log.txt`，不丢信息），彻底消除管道死锁。
- **教训**：`Popen(stdout=PIPE)` 必须有消费方；日志已落文件时无需再捕获 stdio，直接 DEVNULL。
- **复审补强（2026-09-11 08:49 · R10）**：对抗性复审发现 R9 把 **stderr 也 DEVNULL**，会丢子进程未捕获异常的 traceback（诊断信息随洗澡水倒掉）。改为 stderr 重定向到 `logs\ocr_child_err.log`（非管道、不死锁、保留 traceback），进程退出后由 watchdog 关闭句柄。stdout 仍 DEVNULL（batch 自落盘）。

### BUG-13 · OCR API token 明文硬编码　🟡（安全）
- **状态**：已修复（2026-09-11 06:23 · R9）
- **现象/根因**：`batch_convert_pdf.py` 硬编码 `TOKEN = "b955…"`，与 LLM key 已外部化不一致，泄露即配额盗刷。
- **解决**：token 值提取到 `data\.ocr_config`（`token=…`，与 `.llm_config` 同款，勿外泄）；代码加 `_load_token()`：优先环境变量 `OCR_API_TOKEN`，其次 `.ocr_config`，缺则 `sys.exit` 报错。硬编码已删（脚本提取，值未在会话中显示）；加载测试返回 40 字符 hex；`SyntaxWarning` 清零、py_compile 通过。当前运行进程不受影响，下次 watchdog 重启无缝续跑。
- **教训**：密钥统一外部化；改 token 读取时先把值落到配置再改代码，保证服务不断；提取用脚本避免密文入消息。

### BUG-19 · 题号行被 OCR 误标为 markdown 标题（渲染加粗）　🟡（展示质量）
- **状态**：✅ 修复（2026-09-11 R22）· 134/158 行剥离，24 行结构标题保留
- **发现**：用户抽审平谷历史见 `### 52. 中国古代文明光辉灿烂` 渲染加粗，判断普遍性问题；全批扫描证实 20/50 份、158 行。
- **区分规则**：行在 unit 区间内=题干/答案内容误标（134 行，剥）；区间外=教师用书小节标题等真结构（24 行，保留）。正则 `^\s*#{1,6}\s*(\d{1,3}[.．、].*)$` 对 4 位年份卷标题零误伤（抽样验证）。
- **修复**：`fix_heading_qnum.py`（newline="" 读写，逐行审计 `data/bug19_heading_fix_log.json`）；dry-run/apply 数字精确对账 134/24。
- **插曲**：房山高三二模政治单文件三写被拒——初判"进程占用"**是误判**，第三次错误带 `[sandbox: file access denied under workspace-write mode]` 标记，实为 DSH 沙箱对该路径的拒绝（同目录其他文件均放行），按流程 escalation（danger-full-access + justification）后写入成功。教训：PermissionError 先看有无 sandbox 标记再归因。
- **副产物事故**：该文件 recompile 时误传 `mf.stem`（含 `.manifest`）生成错误命名产物（`xxx.manifest.md` 等 3 文件），使 QC 一度显示 51 份；已删除并用正确命名重生成。recompile 一律 `mf.stem.replace(".manifest","")`。

### BUG-18 · 无主配图（题前版式图被 LLM 行区间漏掉）　🟡（切片完整性）
- **状态**：✅ 修复（2026-09-11 R20）· 全批 204 张无主 img 三层定性
- **发现**：用户判定立体几何源完整无图集页后，嫌疑转向 LLM 划行；取证确认题前版式图（PDF 图排题号前）被 stem 起点漏掉，入库按区间提取会丢图（几何题缺图=废题）。
- **三层定性**：①题干区题前图 56 张=真丢失 → 并入修复；②详解区复述图 92 张=BUG-17 镜像冗余（宽高比验证同图复述）→ 不并入；③详解区前 keep 56 张=归属不明留档。
- **修复**：`fix_orphan_imgs.py` 确定性归属（gap≤6+中间仅空行/分隔线 → 区间端点扩展），merge=56，审计 `data/bug18_orphan_img_fix_log.json`；QC 35→36 PASS。
- **教训**：行区间模型对"图排题号前"版式天然脆弱，全量 prompt 应加"题图必须纳入 stem 区间"；角色白名单要含 material/questions_lines、排除 question_numbers（题号非行区间）；详解区复述图并入会制造重复，定性先行再动手。

### BUG-17 · 详解区含原题复述（教师版格式）导致切片"题干重复出现在详解区"　🟡（展示冗余）
- **状态**：✅ 修复（2026-09-11 R18）
- **发现**：用户人工抽审 batch-C"统计与概率"切片 HTML——QC C1-C10 结构校验查不出此类内容级问题。
- **根因**：教师版详解区自带完整原题复述（题号+题干+选项），LLM 忠实划行后 explanation_lines 起点落在复述块上。非 LLM 错、非管线错，是源文出版格式 × 划行忠实的组合。
- **量化**：585 有详解 unit 中真正"完整复述"仅统计与概率 1 份（60/60）；另 4 份（54 unit）为"题号+解析正文"格式，定性假阳性未动手。
- **修复**：`fix_explanation_prefix.py` 确定性收缩起点到首个【分析】/【解答】行（fix=60，审计 `data/bug17_explanation_fix_log.json`）+ recompile + QC 新增 **C11**（详解首行与题干首行文本相似>0.85 且无标记 → FAIL；两轮消除假阳性：题号+解析格式、解答首句引用题设）。
- **已知无害副作用**：清洗后统计与概率 C5/C6 报警（复述块内图/表变无主），已定性为冗余引用（图裁剪框 748×267 vs 750×271 吻合、表格行 28/31 文本复述），无信息损失，QC 保持报警不放松。
- **教训**：QC 结构校验有内容盲区，人工抽审不可省；"题号开头"启发式会误伤多种详解格式，清洗必须配文本级相似判定；区间收缩要预期"引用跟随"副作用。

### BUG-16 · 保留编辑脚本的 EOL 静默转换（Windows newline）　🟠（工具）
- **状态**：已修复代码 + 单测通过（2026-09-11 ~12:00 · R16）；历史数据恢复**受限**（见下）；**R30 仓库级根治：`.gitattributes` 锁定 LF**（编辑工具复发实证：reslice_qc.py 被 edit 翻成 CRLF，提交前 EOL 审计抓获）
- **现象/根因**（第三轮对抗审查发现）：`fix_half_delim.py` / `fix_bare_latex.py` 用 `Path.read_text()/write_text()`，默认 `newline=None` → Windows 下**读时 `\r\n`→`\n`、写时 `\n`→`\r\n`**：原 LF 文件被**整文件**静默转成 CRLF，远超声称的"仅改 N 行"。
- **证据链**：① 全语料 2974 md 行尾分布 = 纯 CRLF 1694 + 纯 LF 1280（LF 文件大量存在）；② 被脚本写过的 469 文件当前 100% 纯 CRLF（概率上≈200 个应为 LF）；③ **同目录对照排除混淆**：几乎每个目录"未碰文件含大量 LF（如高考真题\历史 7/105 CRLF）而被碰文件全 CRLF"；④ 机制源码实证（write_text 的 newline 语义）。
- **解决**：两脚本读写改 `io.open(..., newline="")` 双向保真；单测：LF 文件写后仍 LF、CRLF 写后仍 CRLF、`\quad` 替换均生效。`recover_images.py` 用 `newline=""` 本就正确（反例印证）。
- **历史数据影响（如实记录）**：469 被碰文件 + BUG-09 回退 88 文件（同 100% CRLF 嫌疑）。**下游影响实测 = 0**（所有工具链用 Python 文本读=universal newlines，splitlines 行内容逐行一致，1035/1035 验证）；损害面=审计完整性（字节层被改，无字节级快照无法精确恢复）。嫌疑分桶：目录未碰对照 ≥90% LF 仅 2 个（历史卷）、50–90% 205、<50% 260。**未做概率性恢复**（目录先验反向恢复可能制造新的不一致——避免二次伤害）；若必须恢复：从原始 PDF 重转或对高置信目录按用户指令执行。
- **教训**：Windows 下任何"保留编辑"（读-改-写）必须 `newline=""`；审计叙事必须涵盖**文件级副作用**（EOL/BOM/末行换行），只数"改动行数"会漏；`write_text` 便利性是陷阱。
- **用户决策（2026-09-11 · R17）**：暂不恢复；后续有空时用 LLM 扫描嫌疑文件、结合原始 PDF 判断能否补全原行尾。挂起为待办。

### BUG-20 · 模块 import 期硬依赖开发机私有配置 → CI collection 全灭　🔴（工程/CI）
- **状态**：✅ 修复（2026-09-12 R27）
- **发现**：ChatGPT 第二轮对抗审查（H-01），证据为 GitHub Actions 真实 Run（head `8d2c3f4`，conclusion=failure，pytest exit 4，0 用例执行）。
- **根因**：`reslice_pipeline.py` 顶部 `ROOT = Path(r"D:\Project\Papers")`（开发机绝对路径硬编码）+ `CFG = load_cfg()` 在 **import 期**读 `data/.llm_config`（gitignored，CI runner 上不存在）→ `FileNotFoundError` → conftest import 失败 → collection 阶段全灭，27 用例 0 执行。
- **本地等价复现**：沙箱禁改生产配置文件，改用 read_text 定向注入 FileNotFoundError 模拟缺文件 → 同一调用栈（conftest:18 → reslice_pipeline:50 → load_cfg:43），exit 4，与 CI 日志逐行吻合。
- **修复**：① `ROOT` 改为 `RESLICE_ROOT` 环境变量可覆盖、默认取仓库相对路径（`Path(__file__).parents[1]`）；② 配置**惰性加载**——`CFG = load_cfg()` 删除，`call_llm` 内调用点加载，缺配置**显式抛** `FileNotFoundError`（拒绝吞异常式假修复，见 mutation M2）；③ 确定性渲染路径（`compile_anchor`/`compile_slices`/`write_outputs`）的模型名改为参数 `model=DEFAULT_MODEL`，不再触碰配置文件；`model_tag()` 仅供产物元数据兜底。
- **回归测试**：`tests/test_no_config_import.py` 3 用例——子进程 `RESLICE_ROOT` 指向空目录（配置**真实**不存在，与 CI 同构，非 monkeypatch）：import 成功 / `call_llm` 显式失败 / `write_outputs` 离线三产出齐全。
- **mutation 验证**（审查要求"破坏生产代码→测试必须失败"）：M1 回退 import 期加载 → 3 用例全 FAIL ✅；M2 吞异常假修复 → fails-loudly 用例 FAIL ✅；M3 `clamp_intervals` 空操作 → 8 用例 FAIL ✅。全部回退后 30 passed + 1 xfailed。
- **教训**：① "本地全绿"≠"CI 可执行"——本地开发机恰好满足隐式依赖，掩盖了 import 期副作用；可测试性重构必须连**环境依赖**一起进测试边界。② 声称"CI 就绪"前必须看真实 Run 结果，不能只看 workflow 文件存在。

### BUG-26 · `--recompile` 静默洗掉 QuestionIdentity v2 身份头 → QC 降级 v1 语义　🟢 CLOSED（生产路径层 / R41 readiness gate 修复）
- **状态**:🟢 FIX VERIFIED(R41 System Readiness Gate 攻击面 B「失败传播」发现并修复;mutation 验证通过)。
- **发现**:Gate B-01 真实测试——取 batch-C 真实 v2 manifest + 真实源,在隔离目录跑生产入口重编译,产物 `identity_version` 与 `sections` **双双消失**(单元级 section_ref/basis 等仍在)。旧实现 `main()` 的 `--recompile` 分支只把 `{"units": man_full["units"]}` 传给 `write_outputs`,而 write_outputs 的身份头拷贝(`for k in ("identity_version","sections"): if k in man`)恒不触发——R34 在 write_outputs 侧加的守卫被调用方绕开。
- **危害定性(如实量化)**:① 契约破坏:重编译产物不再是 v2,QC 静默降级走 v1 存量语义,"resolver 只消费 v2" 契约失效;② B-02 爆炸半径实测:当前 65 份生产 v2 文件在降级模拟下 **0 个裁决翻转**(生产语料当前无跨分节重号,身份检查无 FAIL/PENDING),即**今天无 verdict 级后果,但机制真实存在**,任何未来重编译都会静默腐蚀身份层;③ 潜伏原因:v2 回填(R34)后从未跑过 `--recompile`。
- **修复**:`--recompile` 主体抽成可测函数 `recompile_outputs(out_root)`,传**完整 manifest**;BUG-26 注释入 docstring。
- **回归测试**:`tests/test_recompile_identity.py` 2 用例(合成 v2 卷 → recompile_outputs → 身份头逐字保留 + 单元级字段逐项相等 + 切片字节确定性;QC 仍走 v2 分支)。
- **mutation 验证**:调用点退回 `{"units": ...}` 传参 → 2 用例全 FAIL;恢复修复 → 全 PASS;真实 batch-C 产物端到端复验:重编译后 identity_version=2、sections=13 保留。
- **教训**:① 守卫加在被调方(write_outputs)不等于调用方(main)会触发——**守卫的触发条件本身必须有测试**;② "R34 加了守卫"这类历史结论在新攻击面下必须重测,不可引用代替验证。

### BUG-27 · basis 契约词表三处不一致 + 生产值 `explicit` 游离于声明词表外　🟢 CLOSED(契约文档层 / R42 V8 发现)
- **状态**:🟢 文档勘误完成(R42 对抗性审查发现;identity 代码冻结,零逻辑改动)。
- **发现**:R42 V8 对 80 份产物做值域审计(契约词表来源 `question_identity.py:22-23`):batch-C 三十五中英语 `Q86-essay` 的 `basis='explicit'` **不在声明词表** {answer_key|shift|keep|printed_as_is|unverified} 内。溯源:`explicit` 是 `fix_bug22_renumber.PLAN` 的合法 mode(逐单元指定,唯一用例 Q86→印刷号 96),回填脚本按设计把 PLAN mode 直写 basis;设计文档统计行(L244)也如实记了 explicit 1——**数据合法,契约词表漏收**。
- **三处不一致**:① `question_identity.py:23` 声明 5 值(漏 explicit);② 设计文档 L62 声明 `answer_key|running_max|printed_as_is` 3 值(running_max 为 shift 旧名,严重过时);③ 生产数据实际 6 值。
- **修复**:两处词表统一勘误为 6 值全集 + 勘误注记(纯文档;identity 逻辑零改动,不破冻结)。
- **已知限制(不掩饰)**:`check_identity` **不校验 basis 值域**——词表当前只存在于文档,无机器强制;未来新值仍可静默进入生产数据。是否加域校验属**新规则**(会改变裁决面),受 Identity 冻结约束,**列为用户决策点,本轮不擅自加**。
- **教训**:契约词表必须与生产数据的**实际值域**对账(值域审计应是 schema 检查的标准项,存在性检查不够);"字段在"≠"值合法"。

### BUG-28 · batch summary 硬编码写生产账目,--out 隔离不彻底　🟢 FIXED(mutation-sensitive / Gate 首攻面 PAC 批注前发现)
- **状态**:🟢 FIXED(R43 发现并修复;回归测试 + 变异验证)。
- **发现**:PAC 对抗语料批注前核查 batch 模式账目路径:BUG-21 已把 log/result 改为随 `--out` 派生(`derive_run_paths`),但 batch 汇总仍**硬编码**写 `data/reslice_batch_c_summary.json`(原 `reslice_pipeline.py` main 末段)——任何带 `--out` 的独立批量跑都会**静默冲掉生产 batch-C 的证据工件**。定性:C-01 家族(证据工件被覆盖/过期),触发条件 = 下一次任何 `--batch --out` 运行(PAC 即将触发,属于"不修就会真实发生"的缺陷)。
- **修复**:`derive_summary_path(out)` 与 `derive_run_paths` 同则派生(`--out` → `data/reslice_{目录名}_summary.json`;默认行为保持写 batch-C 路径,生产口径零变化)。
- **证据**:`tests/test_batch_summary_isolation.py` 3 用例——默认路径不变 / --out 派生隔离 / **集成级**(monkeypatch process_file 真跑 main():summary 落派生路径且 batch-C 文件不存在);**变异验证**(调用点回退硬编码 → 恰 1 条集成测试 FAIL → 备份还原 3 passed)。
- **教训**:隔离修复必须**穷举账目面**——BUG-21 当时只隔离了 log/result,summary 漏网;"同一次修复里的兄弟路径"是系统性盲区,改路径派生时应 grep 同目录下所有硬编码写盘点。

### BUG-29 · identity 回填报告硬编码写生产账目(BUG-28 家族第二例,不同脚本)　🟢 FIXED(R43 发现并修复)
- **状态**:🟢 FIXED(Gate 首攻面 PAC v2 回填前发现;`--out` 独立跑必须自带 `--report`)。
- **发现**:BUG-28 修复后按"账目面穷举"教训 grep 同类硬编码,`phase2_identity_backfill.py` 的回填报告硬编码写 `data/phase2_identity_backfill_report.json`——PAC 回填一跑就会冲掉生产 batch-C 的回填证据工件。
- **修复**:加 `--report` 选项(默认保持生产路径,生产口径零变化)。
- **证据**:真实运行验证——PAC 回填 `--out ... --report data/pac_identity_backfill_report.json` 后,生产报告 sha256 前后逐字节不变(True);PAC 22/22 applied / 0 fail。
- **教训(升级 BUG-28 教训)**:"账目面穷举"不能只看正在改的那个脚本——硬编码生产账目是**跨脚本家族**(BUG-21 log/result → BUG-28 summary → BUG-29 backfill report);readiness 面 D-02 硬编码治理时应把"硬编码证据工件写路径"并入同一扫描面。

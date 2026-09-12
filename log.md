# 变更日志 (log.md)

> **用途**：按轮次记录每一轮的**代码变动 + 相关操作 + 产出 + 遗留**，供回溯"什么时候改了什么、为什么改"。
>
> **更新规则（务必遵守）**：
> 1. **追加式**：新一轮记录一律**流式追加到本文档末尾**，**不重写、不置顶、不倒序**；最新记录永远在文末。
> 2. **时间戳**：每条记录带**当前时间戳**，格式 `YYYY-MM-DD HH:MM`（24h）。回填的历史条目无精确时刻者标 `(时刻从略)`。
> 3. **不可变**：已写入的历史条目不改写；纠错用追加「更正」条目，不覆盖旧条目。
> 4. **编号递增**：轮次 `R{n}` 单调递增，只在文末新增。
>
> 缺陷与修复细节见 `bugs.md`，规格见 `prd.md`，进度见 `status.md`。

---

## R1 · 2026-09-08 (时刻从略) · OCR 流水线 + v6 规则批注

**目标**：建立 OCR 转换服务与首版规则批注。

**代码变动**：
- **新建** `ocr_service\batch_convert_pdf.py` + `ocr_service\ocr_watchdog.py` + `start_ocr_watchdog.bat` + `ocr_task.xml`：PaddleOCR-VL-1.6 批量转换 + 守护（每日 20000 页额度，午夜重置，达限停）。
- **新建/迭代** `auto_annotate v1–v7`、`fix_markers v1–v9`（规则批注，现已归档 `_archive`）。

**操作**：批量 OCR → 源 md；v6 规则批注 1433 份 / 36,438 题 / 25,873 答案 → `auto-annotated-v6\`。

**产出**：OCR 源库；v6 批注基线（后经 R3 判定不可用，仅留历史对照）。

**遗留**：v6 切片距"完整题入库"差距大（→ R3 弃用）；OCR 缺图（→ R2 recover_images）。

---

## R2 · 2026-09-09 (时刻从略) · 源处理工具 + 审核基线 + 冗余整理

**目标**：修源（补图/重归类）、建立人工审核基线、清理历史冗余。

**代码变动**：
- **新建** `scripts\recover_images.py`：PDF 坐标裁剪恢复配图（PyMuPDF 2x/144DPI），引用名内嵌坐标定位页+框，幂等 + 审计可回滚。
- **新建** `scripts\make_review_sample.py`：分层抽样（年级×科目，种子 20260909）。
- **新建** `scripts\reclassify_unknown.py`：698 份"未分类"按考试类型重归类。
- **新建** `scripts\prereview_check.py`：v6 结构完整性机器预审。

**操作**：恢复配图 43,463 张（0.64 GB），修复悬空引用 66,400+；重归类 698 份到 `高考真题`(599)/`合格考`(71)/`会考`(17) 等；生成 94 份审核清单；冗余整理归档 3101 文件 / 80.7 MB（只移动不删除）。

**修 bug**：BUG-02（用量计数虚高 19105→5881）、BUG-03（BOM 炸 JSON → 批处理退出 1）。

**产出**：`_imgs\` 图片库；`reclassify_report.md/.csv`；`review_checklist`；`_archive\2026-09-09_冗余整理\`。

**遗留**：`batch_convert_pdf.py` 不下载 `outputImages`，新产出 md 仍缺图（需 recover_images 增量补）。

---

## R3 · 2026-09-10 (时刻从略) · 重切路线确立（弃 v6，锚点式定型）

**目标**：确定批注根本形态与路线。

**代码变动**：无独立新脚本；`prereview_check.py` 的 `normalize_qnum`/`parse_answer_tables`/`parse_range_answers` 三 helper 被重切复用。

**操作/决策**：
- v6 样本预审 94 份 → 判定分布（合格 9 / 基本合格 15 / 需返修 47 / 不合格 23），**合格率仅 4.0%** → 决策**废弃 v6 规则批注、废弃 BERT+CRF 本地训练路线**，改 LLM 驱动重切。
- 确立**锚点式批注**为根本形态：源 md 原文逐行不动，只插 META 注释锚点；LLM 只输出行号、从不誊写正文（R12）。

**产出**：路线决策（→ `prd.md` §12）；预审报告 `reports\prereview_report_full.md`。

---

## R4 · 2026-09-10 (时刻从略) · LLM 重切试点 + 回归质检 + 人工签核

**目标**：落地 LLM 重切流水线并用试点验证路线。

**代码变动**：
- **新建** `scripts\reslice_pipeline.py`（v2.1 嵌套格式）：行号化 → mimo-x-pro-preview 输出 semantic_units（仅行号）→ 确定性校验 → 三产出（manifest / `.annotated.md` 锚点 / 切片 md）。支持 `--resume`/`--recompile`。
- **新建** `scripts\reslice_qc.py`：回归质检 C1–C10。
- **新建** `scripts\render_lint.py`：LaTeX/HTML 渲染风险静态检测。
- 容错内建：LLM JSON 截断/损坏（max_tokens 30000 + 容错解析 + 失败留档）、子题编号漂移、分节重号降级 warning + 答案局部解析、无题号作文自动补号、图片行覆盖强化。

**操作**：跑试点 16 份（九科×三学段）；render_lint 修复 32 处 `alt="Image"" />` 损坏 + 2 处字面货币 `$`；用户逐份人工审核 **16/16 全通过**（审中修：石景山语文 material 边界、五十六数学 Q8 图文错序 + Q9 extra 卫星锚、西城生物 L331 伪标题等）；目录整理 reorganize。

**修 bug**：BUG-05（西城生物伪标题）、BUG-08（LLM 截断/编号类）；render_lint 修源/渲染缺陷（见 `bugs.md`）。

**产出**：`Ocr-markdown\resliced-pilot\` 16 份三产出；`reslice_qc` 16/16 PASS；签核表（→ `status.md`）。

**遗留**：分节重号卷 Resolver 需"大题+题号"二元键；历史四十三中源缺 4 题答案。

---

## R5 · 2026-09-10 (时刻从略) · 全库质检批（源缺陷量化 + 自动修复 + 溯源比对）

**目标**：在全量重切前，量化并清理源层缺陷，建立源保真工具。

**代码变动**：
- **新建** `scripts\corpus_scan.py`：全库源缺陷量化（difflib 双重识别 + 裸 LaTeX 简单/复杂），只读 → `data\corpus_scan.json`。
- **新建** `scripts\fix_bare_latex.py`：裸 LaTeX 自动包 `$`（确定性/幂等/可回滚）。**收紧 TOKEN 正则**（只包"基+`_{}`/`^{}` 核"，不含外围括号句号）以修 BUG-4 的吞句读问题 → `data\bare_latex_fix_log.json`（4388 处）。
- **新建** `scripts\pdf_fidelity.py`：PDF 文本层 vs 源覆盖率；先用 16 字符 shingle（覆盖率仅 0.086，失败），**改写**为散文段+首尾 10 字匹配（中位 0.988）→ `data\pdf_fidelity.json`。
- **新建** `scripts\render_preview.py`：源 MD→独立 HTML（KaTeX 0.16.9 + mhchem CDN），`--pilot` 渲染 16 份 → `reports\preview\`。

**操作**：corpus_scan 全库 3120 份；fix_bare_latex 落地 954 份/4388 行；pdf_fidelity 全库 3113 份；render_preview 渲染试点 16 份供人眼比对 PDF。

**修 bug**：BUG-04（贪婪 TOKEN 吞句读，收紧正则修复）。

**产出**：全库缺陷量化（双重识别 138/148；裸 LaTeX 954 份 简单 4918/复杂 610）；4388 行自动修复；16 份渲染预览。

**遗留**：BUG-04 残留（括号式 105 行漏网）；BUG-09 裸 LaTeX 半包残损 36 行（本轮收紧 TOKEN 引入，R6 审查发现）；pdf_fidelity 高假阳性 → 降级为粗筛（BUG-06）。

---

## R6 · 2026-09-11 00:36 · 对抗性审查 + 文档体系冻结

**目标**：从第一性原理对全项目做严格对抗性审查，并把项目规格冻结进文档。

**代码变动**：无（本轮纯审查 + 文档）。

**操作**：
- 通读全部现役脚本（`reslice_pipeline` / `reslice_qc` / `prereview_check` / `fix_bare_latex` / `corpus_scan` / `pdf_fidelity` / `render_preview` / `render_lint` / `recover_images` / `ocr_watchdog` / `batch_convert_pdf`）+ 实证核对活数据（fix log、QC json、corpus_scan、pdf_fidelity、manifest、运行日志）。
- 发现并登记问题 A1–A3 / B1–B2 / C1–C4 / D1–D2（见 `bugs.md` BUG-09~14）。
- **重写** `status.md`：删除自相矛盾的"BERT+CRF 训练 / 1433 份"旧叙事，改为进度快照 + 风险登记。
- **重写** `README.md`：改为纯目录导航，置顶"从哪读起"，修失效的 `finetune` 引用，补编码铁律。
- **新建** `prd.md`（规格冻结）、`log.md`、`bugs.md`。

**决策**：
- **撤回**上一轮审查中"大文件会超 LLM 输入上下文（B1）"的误判——实测 MIMO 支持 1M，最大文件仅 ~128K 输入 / ~8K 输出，规模化非 blocker（→ `prd.md` §11）。

**产出**：`prd.md`、`log.md`、`bugs.md`（新）；`status.md`、`README.md`（重写）。

**遗留**：审查发现的待修项全部登记 `bugs.md`（BUG-09 36 行残损 / BUG-10 LIFO / BUG-11 图片目录 / BUG-12 stdout 死锁 / BUG-13 token 明文 / BUG-14 未分类跑步机 + 73 重复）。

---

## R7 · 2026-09-11 00:36 · 确立文档更新规则（追加式 + 时间戳）

**目标**：明确状态/变更类文档的更新规则，纠正上一轮 log.md 倒序、无时间戳的问题。

**代码变动**：
- **重写** `log.md`：由"倒序、最新在上"改为**追加式、最新在文末**，每条记录补时间戳；顶部固化更新规则（追加式 / 时间戳 / 不可变 / 编号递增）。
- **`prd.md`** 新增「文档体系与维护规则」小节（权威规则）。
- **`bugs.md`** 头部补登记时间戳规范；**`README.md`** 修正 log.md 描述（倒序→追加式）。

**规则（已固化）**：变更/状态记录一律**流式追加到文档末尾**，带当前时间戳 `YYYY-MM-DD HH:MM`，历史条目不改写（纠错追加「更正」条目），编号单调递增。

**产出**：`prd.md` 文档维护规则；`log.md` 追加式 + 时间戳。

**遗留**：无。

---

## R8 · 2026-09-11 00:48 · 修复 BUG-09（裸 LaTeX 半包残损）+ 新发现 BUG-15

**目标**：修复 BUG-09（R5 收紧 TOKEN 引入的半包残损行）。

**代码变动**：
- **`scripts\fix_bare_latex.py`**：新增 `BARE_CMD` 正则 + 防回归守卫——`process` 里仅当"包裹后数学岛外无残留 `\命令`"才落地，否则整行保留裸形态交人工；`COMPLEX` 补 `\xlongequal`。经测试：`Na_{2}SO_{4}`→`$Na_{2}SO_{4}$`（净包照常），`2Na+2H_{2}O=…H_{2}\uparrow`→跳过（不再半包）。**此后该工具不可能再产出半包行。**
- **回退受损行**：按 `data\bare_latex_fix_log.json` 的 before/after，把 **103 行**半包行（93 唯一行，10 为重复日志）逐行比对"当前==logged after"后回退至修复前裸形态 → 审计 `data\bug09_revert_log.json`（可回滚）。分布 高一48/高三23/高二14/高考真题18，无一在 `未分类`（无 OCR 写冲突）。

**规模修正**：BUG-09 实为 **103 行**（早先报 36 系检测命令表过窄，漏 `\uparrow/\triangle/\cdot/\rightarrow/\rightleftharpoons` 等）——教训：量化缺陷须用最宽命令表核实。

**新发现（BUG-15，既存·待定）**：修 BUG-09 时顺带全库扫描发现**"半定界"数学债 1490 份 / 23,221 行**（`$` 岛 + 岛外裸 `\quad/\frac/\mathrm/\left\right/\sqrt/\therefore/\times` 等）。因 `corpus_scan`/`fix_bare_latex` 均跳过含 `$` 行而长期不可见；此前"裸 LaTeX 954 份/5528 行"仅是无 `$` 子集，**严重低估数学债**。既存、非工具引入，需半自动整段定界，量大须先小样验证——已登记 `bugs.md` BUG-15，待用户定向。

**文档变动**：`bugs.md`（BUG-09 移入已修复并修正103；新增 BUG-15）、`status.md`（进行中/清单/风险登记）、`prd.md`（§10-A 标已修复 + 新增 §10-A2 半定界债）。

**产出**：`data\bug09_revert_log.json`；`fix_bare_latex.py` 防回归守卫；BUG-09 关闭。

**遗留**：BUG-15（半定界数学 1490/23221，待定向）；BUG-04 残留括号式 105 行；其余待修项见 `bugs.md`。

---

## R9 · 2026-09-11 06:23 · B 阶段：修复 BUG-10/12/13（三个低成本确定性项）

**目标**：清掉审查发现的三个零 LLM 成本确定性 bug（用户定向 B → A → C 顺序）。

**代码变动**：
- **BUG-10** `scripts\reslice_pipeline.py` `compile_anchor`：闭合元组改带 span 起始行 `(depth, tag, rg[0])`，同深度闭合排序键改 `-x[2]`（起始行降序 = 后开先关，真 LIFO）；删死变量 `unit_start`。
- **BUG-12** `ocr_service\ocr_watchdog.py` `run_conversion`：子进程 `stdout/stderr` 由 `PIPE` 改 `DEVNULL`（batch 自落盘日志），消除长跑管道死锁。
- **BUG-13** `ocr_service\batch_convert_pdf.py`：硬编码 token 外部化到 `data\.ocr_config`（新，`token=…`）；加 `_load_token()`（优先环境变量 `OCR_API_TOKEN`，其次 `.ocr_config`）。脚本提取 token 值入配置，**值未在会话显示**。

**验证**：
- BUG-10 单测：Q1(answer[5,10])+Q2(answer[6,10]) 同闭 line10 → `answer:end:2` 先于 `answer:end:1`（LIFO 正确）；recompile 16 份 + QC **16/16 PASS**（未破坏现有产出）。
- BUG-13：`_load_token` 返回 40 字符 hex；`SyntaxWarning` 清零；`py_compile` 通过。
- 三个脚本 `py_compile` 全通过。

**影响**：均为确定性、幂等；当前运行的 OCR 进程不受影响（下次 watchdog 重启用新代码，`.ocr_config` 已就位故无缝）。

**产出**：`data\.ocr_config`（token 外部化）；三个脚本修复；`bugs.md` BUG-10/12/13 移入已修复。

**遗留**：待修复剩 BUG-11（图片目录）、BUG-14（未分类/重复）、BUG-04-residual（括号式）、**BUG-15（半定界数学，下一步 A）**。

---

## R10 · 2026-09-11 08:49 · 对 R8/R9 修复的 bug 执行对抗性审查 + 补强

**目标**：用怀疑视角复查本轮修复（BUG-09/10/12/13），找出修复不彻底处或新引入问题。

**审查发现 + 处置**：
- **BUG-10 残留（已补强）**：R9 用"span 起始行"做 LIFO tiebreak，但**两单元同起同止**（共享完全相同区间，如整张共享答案表）时起始行相同 → 仍交叉非法（实测 `start:1,start:2,end:1,end:2`）。根治：改**全局注册序号** `_seq`，opens `(depth,order)` 升序 / closes `(-depth,-order)` 降序（后注册先关）。
- **BUG-12 弱点（已补强）**：R9 把 stderr 也 `DEVNULL`，丢子进程未捕获异常 traceback。改 stderr → `logs\ocr_child_err.log`（非管道不死锁、保留诊断），进程退出后关句柄；stdout 仍 DEVNULL。
- **BUG-13（说明性，不改）**：token 从代码移到明文 `.ocr_config`，**降低随代码泄露面但未加密**；手编 config 若带 BOM 会复现加载失败（`k.strip()=="token"` 不匹配 `\ufefftoken`）。本地单人够用，非根治，如实记录。
- **BUG-09（说明性，不改）**：`BARE_CMD` 防回归守卫使更多含 `\times/\cdot/\sqrt` 的行转**手工队列**（自动覆盖率下降是有意取舍：宁可不修也不错修）；回退是"回到未处理"非"修成正确"，已如实标注。

**验证**：`py_compile`（reslice_pipeline / ocr_watchdog）通过；BUG-10 单测**不同起止 + 同起同止均合法嵌套**；recompile 16 份 + QC **16/16 PASS**。
**假警报澄清**：先前 `Select-Object -First 1` 截断管道致 Python broken-pipe 显示 `exit 1`；实测 `reslice_qc.py` **真实退出码 0**，QC 无失败。

**代码变动**：`scripts\reslice_pipeline.py`（`_seq` 注册序号替代起始行）；`ocr_service\ocr_watchdog.py`（stderr→`ocr_child_err.log` + 关句柄）。

**产出**：BUG-10/12 补强落地；`bugs.md` 两条目追加复审补强记录。

**遗留**：BUG-13/BUG-09 的说明性弱点记录在案（不阻塞）；待修复剩 BUG-11/14/04-residual/**BUG-15（下一步 A）**。

---

## R11 · 2026-09-11 08:57 · 二次对抗性审查：确认四 BUG 真实修复

**目标**：不重跑自己的单测（避免确认偏误），改用**独立/更强**手段验证 BUG-09/10/12/13 是否真修复。

**验证方法与结果**：
- **BUG-10（LIFO）**：新写**独立锚点嵌套栈检查器**（纯解析输出文本，不依赖编译逻辑）：end 必须匹配栈顶 start 否则判交叉。合成 3 场景（同起同止 answer / 三层同止 composite / material 包含于 questions）+ **16 份真实 annotated.md** → 总交叉/未闭合 = **0**。✅
- **BUG-12（stderr）**：隔离复刻 `run_conversion` 的 Popen 模式，跑一个抛异常的子进程 → stderr（含 traceback）确实进文件非 DEVNULL。✅（首测显示 False 系我测试脚本 `-c` 内 `\n` 转义 bug，非机制问题，已换文件式子进程复测通过）
- **BUG-13（token）**：grep batch 脚本**无 40 位 hex 残留**；设环境变量 `OCR_API_TOKEN` 后 `TOKEN` 确实取环境变量（优先级生效）。✅
- **BUG-09（裸 LaTeX）**：防回归守卫 3 例全对（`Na_{2}SO_{4}` 落地、`\uparrow`/`\cdot` 残留行跳过不半包）；`bug09_revert_log` 的 93 条 applied（无 status 键）抽样 15 行**当前全无 `$`**（回到 pre-fix 裸形态）。✅

**审查新发现（审计弱点，非阻塞）**：`data\bug09_revert_log.json` 的 93 条成功回退记录**未写 status 标记**，仅 10 条跳过记录标了 `MISMATCH_SKIP`——审计时只能以"无 status=成功"推断，不严谨。建议未来回退脚本对成功记录也写 `status="applied"`。

**结论**：四 BUG 均**真实修复**，经独立/边界验证。二次审查本身也暴露两处"审查工具"失误（测试转义 bug、JSON 字段假设错），均当场澄清、未误判被测代码。无代码变动（纯验证）。

**遗留**：待修复剩 BUG-11/14/04-residual/**BUG-15（下一步 A）**；R8 日志审计弱点记录在案。

---

## R12 · 2026-09-11 09:23 · A 阶段：BUG-15 小样试点 → 推翻原定性

**目标**：BUG-15 半定界数学小样试点，评估"整段定界"能否安全批量。

**过程与发现**：
- 抽样扫描真实数据时发现 **BUG-15 原检测器有 bug**：`re.sub(r"\$[^$]*\$","")` 剥岛时把 `$$…$$` display 块误当空内联 `$…$` 剥掉，块内命令被判"岛外"。含 `$$` 块行 **23,154** 行即虚报来源。
- **正确检测（先剥 `$$` 块、再剥内联 `$`）后真正半定界仅 1,476 行**（原登记 23,221，虚高 ~15 倍）。
- 构成异质：`\quad` 选项间距 463（岛外排版命令）+ 表格 `\n` 残留 291（**非数学，误报**）+ 跨行 `\begin/\end` 块 480（需多行感知）+ OCR 错乱/裸化学式/`\text{}` 混排 ~240。
- **"整段定界（CJK 用 `\text{}`）"方案经实样检验基本不适用**：这些行是"中文叙述+散落数学+OCR 错乱"混排，整段包 `$` 会让中文进 math 模式大量报错；跨行块/OCR 质量问题更非定界算法能解。

**结论**：小样试点的价值=**避免了盲目批量**。BUG-15 须重新定性分类（误报剔除 / 排版命令转文本 / 跨行重定界 / OCR 质量人工），分别处置。

**文档变动**：`bugs.md` BUG-15 追加"规模修正与方案重估"（23,221→1,476 + 方案不适用）。

**产出**：修正版扫描 + 样本 `data\bug15_samples2.txt`；BUG-15 定性纠正。

**遗留**：BUG-15 待用户重新定向（分类处置）；无代码改动。

---

## R13 · 2026-09-11 10:14 · 修复 BUG-15 SPACE+TABLE（832 行半定界数学）

**目标**：修 BUG-15 中可确定性修复的两类（用户确认：OCR 烂行先放，其余先修再跑测试）。

**代码变动**：
- 新增 `scripts\fix_half_delim.py`：**状态机**精确追踪是否在 `$` 岛内（`\$\$`/`\$` 切换 in_math），只改岛外；奇数 `$` 异常行保守后半不改。
  - **SPACE**：岛外 `\quad/\qquad` → 全角空格（岛内含 `\begin{array}` 列间距**保留不动**）。
  - **TABLE**：表格单元格字面 `\n` → `<br>`。
  - apply 时写审计 `data\bug15_fix_log.json`（每行 before/after，可回滚）。

**过程（含一次自我纠错）**：首版用正则 `\$\$.*?\$\$|\$[^$]*\$` 保护岛，dry-run 抓到**误改了岛内 `\quad`**（长/复杂 array 行保护失效）→ 改状态机，验证岛内保留/岛外改/混合/display 均正确。

**验证**：状态机 4 例全对；`render_lint` 前后对比（space/table 各一样本）lint 问题数**均未增加**（8→8、4→4）；apply 后**幂等重跑 dry=0**；残留 714 行。

**落地**：`--apply --all` 共 **832 行**（space 456 + table 376），escalate danger-full-access（写 Ocr-markdown）。

**残留（留档）**：BLOCK（跨行/`\begin\end` 被错误 `$` 定界打断，需多行感知）454 + COMPLEX（OCR 烂行）228 ≈ 714 行，待人工/专门设计，不阻塞测试。

**文档变动**：`bugs.md` BUG-15 追加处置进展。

**遗留**：BUG-15 剩 BLOCK+COMPLEX（留档）；BUG-11/14/04-residual 未动；下一步 C（50 份测速批）。

---

## R14 · 2026-09-11 10:56 · 对抗性审查 BUG-15 SPACE+TABLE：抓到 TABLE 缺陷并回滚

**目标**：第一性原理审查 R13 修复，每个结论须真实测试证据，不自我合理化、不强行解释未通过项。

**审查发现（含一次自我纠错 + 一个真实缺陷）**：
- **状态机（space 核心）首测 5 FAIL → 系我测试预期错，非实现缺陷**：预期漏算 `\quad` 前后原始空格（`A. $x$ \quad B` 里 `\quad` 前后本有空格，替换后保留是对的）。修正预期后 **8/8 OK** → space 状态机正确。
- **TABLE 修复有真实缺陷（blind replace）**：`fix_line` 对表格行用 `line.replace("\\n","<br>")`，**未保护 `$` 岛**，把数学命令 `\nearrow`(↗)的 `\n` 也替换 → 拆成 `<br>earrow`。量化：215 处 `\n`+拉丁字母被替换，**\nearrow 67 处确证真命令被拆坏**（在 `$ \nearrow` 岛内，B2 样例 `> $ \nearrow` 直接证实）；另 `\nii/\nPM/\nFe` 等是"换行残留+文本"、替换正确。
- **货币 `$` 干扰**：英语广告表格 `Just $1 a week\n` 的 `$1` 是货币，致岛判定误报，但那些 `\n` 确在文本、替换正确。
- **A3 自洽**：space 456 + table 376 全自洽（`R(before)==after` / `replace==after`），审计日志准确。

**结论与处置**：
- ✅ **space（456）**：状态机保护岛 + 验证正确，**保留**。
- ❌ **table（376）**：blind replace 拆坏命令，且"命令 vs 换行残留"无法可靠自动区分（叠加货币 `$`），风险 > 收益，**整体回滚**（按审计还原 376 行；验证 table 全=before、space 全=after）。表格 `\n` 换行残留归入待人工。

**教训**：`replace` 类源修复**必须保护 `$` 岛**（否则拆坏岛内命令）；`\n` 开头命令（nearrow/ne/nu/nabla）与"换行残留+文本"（nii/PM/Fe）不可靠自动区分；货币 `$` 污染岛判定。修复前的 dry-run + lint **不足以**抓这类（需针对性审查"岛内误改"）。

**文档变动**：`bugs.md` BUG-15 处置更新；审计 `bug15_fix_log.json` 标注 table 回滚。

**当前生效**：space 456；table / BLOCK / COMPLEX 留档待人工。

---

## R15 · 2026-09-11 11:28 · 第二轮对抗性审查 BUG-15 space：抓到 3 处误改并回滚

**目标**：审查第一轮保留的 space，不重复第一轮验证，专攻第一轮"推测未测"的盲点。

**审查发现**：
- **C1 构造反例证伪第一轮推测**：第一轮我推测"货币 `$` 只致漏改、不致误改"。实测 `costs $5 then $a \quad b$ ok` → 状态机把真岛 `$a \quad b$` 内 `\quad` 误判岛外改掉。**证伪：`$` 错乱（货币/孤立）与真岛交错时会误改岛内 `\quad`**。
- **块感知检测量化**（U+3000 落在 `$$`/`\begin..\end` 块内=误改）：space 共 31288 处替换，**块内误改 3 处**（L757/L447/L2528，`$$\begin{aligned}` 块内 OCR 孤立 `$` 翻转），块外正确 31285。抽样：L1371 块外（正确，检测正确排除）、L2528 before `\quad\ $ 3)\quad A` 第二个 `\quad` 因孤立 `$` 翻转被改（确证误改）。

**处置**：精确回滚这 3 行（整行还原 before），**space 达零误改**。验证：当前块内全角空格=0，保留 453、回滚 3。

**教训（比 R14 更深）**：**任何基于 `$` 计数的岛判定，在 `$` 错乱（货币/OCR 孤立 `$`）时都会失效**——table 用 blind replace 直接大面积中招；space 用状态机 + 块感知把误改从"能力"压到 3/31288（0.01%），但**不能理论归零**。改进方向：修复前先跳过 `$` 错乱行（行内 `$` 奇数/孤立），保守不改。

**文档变动**：审计 `bug15_fix_log.json` 标注 space 最终 453 零误改。

**当前生效**：space 453（零误改）；table / BLOCK / COMPLEX 留档待人工。

---

## R16 · 2026-09-11 ~12:00 · 第三轮对抗审查：抓到 EOL 静默转换（BUG-16）并修复代码

**目标**：第三轮换维度——不打替换逻辑，打**文件 I/O 层**（前两轮完全没查的面）。

**审查发现（本轮最重）**：
- **`Path.read_text()/write_text()` 默认 `newline=None` 在 Windows 上静默规范化行尾**（读 `\r\n`→`\n`、写 `\n`→`\r\n`）→ `fix_half_delim`/`fix_bare_latex` 会把原 LF 文件**整文件**转 CRLF。
- **证据链**：全语料 2974 md = CRLF 1694 + **LF 1280**（LF 文件大量存在）；被碰 469 文件当前 **100% CRLF**（按基率 ≈200 个应为 LF）；**同目录对照**排除混淆：几乎每目录"未碰文件大量 LF（高考真题\历史 7CRLF/105LF）而被碰全 CRLF"。BUG-09 回退的 88 文件同 100% CRLF 嫌疑。
- **下游影响实测 = 0**：所有工具链用 Python 文本读（universal newlines），`read_text` 后 `\r`=0、splitlines 行内容逐行一致（1035/1035）。
- 嫌疑分桶（按目录未碰 LF 占比）：高 2 / 中 205 / 低 260 / 无对照 2。

**处置**：
- **代码修复**：`fix_half_delim.py` + `fix_bare_latex.py` 读写改 `io.open(..., newline="")` 双向保真；**单测通过**（LF 写后仍 LF、CRLF 仍 CRLF、替换均生效）。`recover_images.py` 本就正确（`newline=""`）。
- **历史数据**：无字节级快照，**精确恢复不可行**；未做概率性恢复（目录先验反向恢复可能制造新不一致）。如实记录 BUG-16，若需恢复走"从原始 PDF 重转/用户指令"。

**教训**：Windows 下"保留编辑"必须 `newline=""`；审计叙事必须涵盖**文件级副作用**（EOL/BOM），只数改动行数会漏；`write_text` 便利即陷阱。

**文档变动**：`bugs.md` 新登记 **BUG-16**；两脚本已修 + 单测。

---

## R17 · 2026-09-11 下午 · C 测速批：50 份实跑完成 + 补跑

**用户决策**：BUG-16 历史 EOL 暂不恢复（后续 LLM 扫描 + 原始 PDF 补全，挂起）；启动 C。

**代码**：`select_batch_c.py`（选样：分层 + 最大 6 份必进 + 排除未分类，seed=20260911）；`reslice_pipeline.py` 加 `--batch/--out`、token 用量（`LAST_USAGE`）、每文件计时、批量汇总落盘；输出独立 `Ocr-markdown\reslice-batch-C`，不碰 pilot。

**结果**：
- 选样 50 份：3.27MB / 51415 行，xlarge 1 + large 5 + medium 8 + small 36，8 个年级组 × 10 科。
- 主跑 39/50 成功；补跑（--resume）救回 10/11（IncompleteRead 确认偶发）；**终态 49/50 成功、44 份零校验问题**，唯一失败：`几何(1)`（两轮 IncompleteRead，待单独处理）。
- **吞吐**：合计 prompt 1,376,653 + completion 482,524 ≈ **186 万 tokens**；LLM 纯耗 14,188s ≈ 3.9h，均 290s/份。
- **大文件结论**：xlarge（6717 行、41.5 万字、23.1 万 prompt tokens）**一次成功、0 问题、112s**——上下文远超 128K，**大文件不需拆卷**。
- **质量**：全绿率 88%（44/50）；有 issues 5 份共 16 条（缺 answer_lines 为主，化学 3 份；英语 2 份卷面指令混入；平谷历史 5 条缺 answer）。
- **外推全量 2956 份**：≈ 1.1 亿 tokens、串行 ≈ 9.8 天 → 全量必须并发（8 并发 ≈ 1.2 天）。
- **发现的代码缺陷**：`extract_json` 失败不触发重新调用（仅网络层重试）——会考数学 1 例 JSON 损坏直接失败，待修。

**产物**：`data/reslice_batch_c_{files,result,summary}.json`、`logs/reslice_batch_c_log.txt`、50 份三件套在 `reslice-batch-C`。

---

## R18 · 2026-09-11 傍晚 · BUG-17 详解区原题复述:人工抽审发现 + 确定性清洗

**触发**：用户抽审"统计与概率"切片 HTML，发现题干重复出现在详解区（Q1-Q4 均有）——QC C1-C10 盲区。

**取证定性**：教师版详解区（卷末答案区）自带完整原题复述（题号+题干+选项+【分析】/【解答】）。LLM 划行忠实，非重切错误。量化：585 有详解 unit 中 114 个首行题号开头，但经样本核对，**真正"完整题干+选项复述"的仅统计与概率 1 份（60/60）**；其余 4 份（英语/生物/物理/化学共 54 个）是"题号+解析正文"的详解区自带编号格式，假阳性。

**修复（方案A，确定性，零 LLM）**：
- `fix_explanation_prefix.py`：explanation_lines 起点收缩到区间内第一个【分析】/【解答】行。apply：fix=60（全部统计与概率）、keep_no_mark=54（假阳性正确跳过）。审计 `data/bug17_explanation_fix_log.json`。Q1 验证 [658,686]→[668,686]，60/60 收缩到位。
- `--recompile` 重编 49 份切片/锚点。
- QC 新增 **C11**（详解区首行与题干首行相似>0.85 且无【分析】/【解答】标记）。两轮修正：v1 误报 2 份"题号+解析"→改文本相似；v2 误报立体几何 Q36"解答首句引用题设"（数学标准写法，相似 0.915）→标记开头放行。终态 C11 命中 0。

**已知无害副作用**：统计与概率清洗后 C5（10 图）/C6（31 表格行）报警——已逐一定性为详解复述块的冗余引用（L690 图与题干 L17 图裁剪框 748×267 vs 750×271 吻合；31 表格行中 28 行与已引用行文本相似>0.9，余 3 行为 table 开标签），**无信息损失**，QC 保持报警不放松。

**QC 终态**：35/49 PASS（统计与概率因上述已知无害项 FAIL，其余 12 份 FAIL 为 R17 已知的 LLM 质量问题，属抽审范围）。

---

## R19 · 2026-09-11 晚 · 抽审判定:会考化学 + 共享答案表决策

**会考化学(2018春季)U-org1-3/U-cp1-3 答案空 —— 判定:源缺陷,记档不修**。
取证:该卷选考为三模块各 3 题(化学与生活 U-cl1-3 / 有机 U-org1-3 / 原理 U-cp1-3),答案区只印《化学与生活》模块 3 题答案(L566-584),内容与 U-cl1-3 精确匹配(重阳糕阳糕①③②④/判断对×4/硝化菌·pH=8),LLM 划分正确;用户对照原 PDF 确认原卷只印了化学与生活答案 → 6 单元记档"源无答案",不阻塞全量。

**共享答案表(单行 HTML table 被多题引用)—— 决策:切片层不修**。
取证:全批 14 份 304 unit 的 answer_lines 指向同一单行 `<table>`(行级引用模型下 LLM 只能整行引用,非错误)。用户决策:入库 Resolver 做单元格级切分(按题号取对应 td),确保每题只挂自己的答案格 → 转记入库前置任务(status 全量推广前准备清单)。

---

## R20 · 2026-09-11 深夜 · BUG-18 无主配图:三层定性 + 确定性并入

**触发**：用户判定立体几何"无图集页、源完整"→ 无主图嫌疑指向 LLM 划行边界。

**取证三层定性**（全批 204 张无主 img，8 份文件）：
1. **题干区题前图（56 张，真丢失）**：PDF 版式图排题号前，LLM stem 从题号行起算漏图。例：Q30 题干"三视图如图所示"，立体示意图 L496 排题号前无主。
2. **详解区复述图（92 张，冗余无害）**：详解区复述完整题干+选项+图（BUG-17 镜像：此卷 LLM 只划【答案】起的部分，复述块整体无主）。验证：详解图 box 449×358 vs 试题区原图 377×302，宽高比 1.248/1.254 一致 = 同图复述。不并入（并入即 BUG-17 式重复）。
3. **详解区前 keep（56 张）**：gap>6 或归属不明，留档待后续。

**修复**：`fix_orphan_imgs.py`（确定性：无主 img 距区间≤6 行且中间仅空行/分隔线 → R-pre/R-post 并入端点；角色表含 material/questions_lines，排除 question_numbers）。apply：merge=56、keep=148，审计 `data/bug18_orphan_img_fix_log.json`。recompile 49 份，QC 35→36 PASS。

**插曲**：dry-run 首版角色白名单漏 material_lines/questions_lines 且误收 question_numbers（题号当行区间），merge/keep 数与全批统计对不上 → 修正后 204 张对账一致。

---

## R21 · 2026-09-11 深夜 · IncompleteRead 第三者重试成功,C 批 50/50 齐装

**结果**：两轮 IncompleteRead 的最后一份（真名 `2012-2021高考真题数学汇编：空间向量与立体几何（2）（教师版）(1)`，此前被控制台 GBK 乱码显示为"几何(1)"）第三次重试**成功**：units=60、覆盖 60、0 校验问题、QC PASS。证实 IncompleteRead 全部为服务端偶发抖动，无文件级稳定故障。

**C 批终态**：50/50 成功；QC **37/50 PASS**（13 FAIL 均已定性：源缺陷记档/详解复述冗余/题前图已修/余少量待审）。累计 prompt 1,455,427 + completion 507,046 ≈ 196 万 tokens；LLM 纯耗 15,026s ≈ 4.2h（含重试浪费）。

**教训入档**：控制台 GBK 乱码曾三次误导判断（"基因工程"误入失败清单、"立体几何/尖端"混淆、"几何(1)"真名）——涉文件名的结论一律以 UTF-8 文件落盘 + read 工具核对为准。

---

## R22 · 2026-09-11 深夜 · 抽审闭环：BUG-19 标题误标清洗 + 平谷历史三问题定性

**平谷历史抽审三问题定性（用户逐项判定）**：
1. Q7 表格尾 `A A B B C C D D`：OCR 把涂卡标记行收进选项表格（源 L83 如此），全批仅此 1 例；记档，列入入库清洗规则。
2. Q20 图文交错：OCR 线性化丢失二维版式（4 图横排+4 选项横排→交错线性序），4 图+4 选项零丢失；展示层排版解决。
3. 5 个答案空（Q2/Q12/Q25/Q39/Q44）：**OCR 丢独立答案行**——源【答案】行序列 1.C→(Q2 无)→3.A 等，49 行 vs 54 题恰缺 5；详解区"故X正确"5/5 齐全。用户确认 PDF 有独立答案行。LLM 如实留空无错。处理=方案 A：入库 Resolver 从详解提取答案（记档）。
   附全批定性：会考化学 6 空=原卷未印（R19）；专题十六 2 空=教师用书源本无。

**BUG-19 题号标题误标清洗**：用户报 `### 52.` 加粗且判断普遍——全批 20/50 份、158 行；区间内 134 行剥（题干/答案误标）、区间外 24 行保留（教师用书小节标题）。`fix_heading_qnum.py` dry-run/apply 对账 134/24 精确，EOL 保留验证通过。

**插曲两则（均记 BUG-19）**：①房山政治三写被拒，误判"进程占用"，实为 DSH 沙箱路径拒绝（错误带 sandbox 标记），escalation 后成功——PermissionError 先看标记再归因；②recompile 误传 `mf.stem` 生成 `.manifest.md` 系列错误产物致 QC 虚报 51 份，已删并用正确命名重生成。

**C 批 QC 终态**：37/50 PASS。抽审至此全部闭环。

---

## R23 · 2026-09-12 上午 · 阶段一完成：v2.1 工具链 + 全流程测试抓出 7 个缺陷并修复

**交付**：①prompt v2.1（题前图入 stem、独立【答案】行强制入 answer_lines）+ extract_json 解析失败自动重调（2 次）；②并发 runner（`--workers N`，ThreadPoolExecutor + log 加锁 + usage 随返回值传递，线程安全）；③修复链 `run_fix_chain.py`（BUG-17/18/19 → 重编译 → QC 一键串行，全程可 --dry）。

**测试抓出并修复 7 个缺陷**（按危险度）：
1. `--out` 未联动 log/result 路径——独立测试会覆盖 C 批正式账目（30 秒内 kill，零污染）；
2. **429 退避不足**（5s/10s→指数 30/60/120/240s，识别 429/5xx）；
3. **max_tokens=30000 截断大文件**→提到 50000（C 批实测天花板 24522）；
4. **LLM 幻觉行号越界**（Q60 [3707,3762] 源仅 3761 行 → 锚点 end 缺失，C10 不配对）→ 行号确定性截断兜底；
5. 修复链缺 `--out` 参数（BUG-17 脚本）；
6. run_fix_chain GBK 打印崩溃（reconfigure utf-8/replace）；
7. prompt 初版题前图规则无效→v2.1 强化措辞后**重切立体几何题干区无主图 0/0**（验收通过，从源头解决 BUG-18 类问题）。

**压测结论**：10 份 8 路并发 9/10 成功（均 93.4s/份 vs 串行 300s，加速 3.2×）；修复链幂等（对 C 批重跑 0 修改）；--resume 断点续跑正确跳过。**残留**：`2012-2021高考真题政治汇编（三）`（2805 行/预期输出 >5 万 tokens）三轮均败于服务端（截断→429→IncompleteRead），属"超长输出+服务端不稳定"组合，全量时对此类文件启用多次退避重试或分段策略。压测 4 个 FAIL 定性：C7 卷面指令漏排（LLM 偶发，抽审项）、C3 两空答案（待定源有无）、C10 即行号越界（已修）、C5 四图残留（抽审项）。

---

## R24 · 2026-09-12 · 全量前对抗性审查：11 项全实测，抓出 4 个真实缺陷并修复

**方法**：每项假设必须真实测试（真调用/真跑/构造用例），三态记录（通过/失败/未验证禁当通过）。

| 项 | 假设 | 实测结果 |
|---|---|---|
| A1 | max_tokens=50000 服务端接受 | ✅ 真调 200，usage 正常 |
| A2 | 路径 startswith 判断无前缀混淆 | ❌ `Ocr-markdown2\` 误判 True→relative_to 崩整批 → ✅ 改 try/except 两处复验通过 |
| A3 | 倒置区间有兜底 | ❌ 实测 `[500,400]` 锚点 end 先于 start 输出（协议破坏）→ ✅ 兜底加倒置交换，复验 ['start','end'] |
| A4 | C 批无行号越界 | ❌ 4477 区间中 1 例（首师大化学 Q20 [616,642]，正是其 QC FAIL 的 C10）→ ✅ 截断修复转 PASS |
| A5 | 并发+resume 一致性 | ✅ 两轮实跑：2/2 成功、results 零重复、resume 日志 2 条跳过、零新调用 |
| B1 | material⊆questions 嵌套不变量 | ❌ 242 composite 中 12 违反：1 例 fix_orphan_imgs 扩 material 未联动（真缺陷→已修+联动补丁）、11 例会考英语系**听力原文在卷末的合法分离结构**（重定性放行）→ ✅ QC 新增 C12（相交才强制嵌套），C12 报错 0 |
| B2/B3/C1/C2/C3 | dry 语义/C11 边界/参数防护/extract 边界/日志撕裂 | ✅ 均通过（C11 已知边界：composite 详解复述不检测，记录不修） |

**审查产出修复**：路径崩溃×2、倒置归一化、C 批越界 1 例、专题十六 U-eg2 嵌套、fix_orphan 联动、QC C12。C 批 QC 37→**38/50 PASS**。

---

## R25 · 2026-09-12 · 对 R24 审查结论的复审：抓出 1 个一审遗漏

**复审方法**：不信一审——修复在库 grep 复核、边界用例补测、修复产物独立验证、幂等硬指标重跑。

| 复审项 | 结果 |
|---|---|
| R1 一审 8 项修复真在代码里 | ✅ grep 全部命中 |
| R7 倒置夹取怪值边界（[0,5]/[-5,-1]/[150,200] 等 5 用例） | ✅ 一审未测，本次补测全 OK |
| **R4 token 计账** | ❌ **一审遗漏**：extract 重试循环 `usage` 被第二次调用覆盖，第一次失败调用的 token 漏账 → 全量预算低估 → ✅ 改累加计账 |
| R3 修复产物独立验证 | ✅ 首师大化学 PASS 0 issues；专题十六 C10/C12/C8 全过（余 5 issue 均为已定性源问题） |
| R2 修复链幂等（联动改动后重跑） | ✅ apply 模式清洗 0/0/0 |
| R5 测试目录隔离 | ✅ 全量走独立输出目录不受影响；test-v21/stress10/audit-a5 三测试目录共 42 文件建议全量前清理（待用户确认） |
| R6 A1 盲点标注 | max_tokens=50000 仅小请求验证过；**大 prompt+50000 组合未验证**（标注为已知未验证项；政治汇编重试时自然覆盖） |

**结论**：R24 审查主体成立，复审补 1 项修复（计账）+ 1 项标注（大 prompt 上限未验证）。QC 38/50 保持。

---

## R26 · 2026-09-12 · 固化测试套件 + CI(响应 ChatGPT 第一轮审查)

**背景**:ChatGPT 审查确认仓库缺少可重复自动化测试体系(High)。R24/R25 的对抗性审查测试全部是一次性脚本,证据有效但不可重复。

**交付**:
1. **可测性重构**:提取 `clamp_intervals` / `rel_out` 为模块级函数;三个 fixer 加 `--out` / `--log` 参数(测试隔离,不触碰生产审计日志);
2. **pytest 套件 27 用例**(全离线,零 LLM 依赖):
   - `test_extract_json.py` 4 例(C2 固化)
   - `test_interval_guard.py` 8 例(A3/A4/R7 固化:越界/倒置/怪值/正常)
   - `test_anchor.py` 5 例(A3/B1 固化:锚点顺序/嵌套/分离)
   - `test_path_safety.py` 3 例(A2 固化:路径前缀混淆)
   - `test_qc_contract.py` 4 例(B1 固化:C12 三种场景 + 合成卷过 QC)
   - `test_fix_contracts.py` 3 例(修复层三元契约:生效/幂等/不触无关)
3. **conftest.py**:合成试卷 fixture(32 行,覆盖题前图/共享材料/独立答案/详解),`make_repo()` 生成与生产同构的完整产物;
4. **CI**:`.github/workflows/ci.yml` — push/PR 自动跑 pytest;
5. **pytest.ini**:禁用 cacheprovider(DSH 沙箱限制),basetemp 固定到仓库内。

**测试过程中发现并修复**:
- 测试断言 bug ×3(锚点顺序方向反、regex 无捕获组、切片 vs 源文件混淆)——均为测试代码自身问题,非生产代码缺陷;
- `.pytest_tmp` 目录被沙箱拒绝访问(rmtree WinError 5)→ 改用 `.pytest_work` 自管目录。

**结果**:27/27 PASS,0.51s。CI 就绪。

---
---

## R27 · 2026-09-12 · 修复 H-01:CI 真实失败(import 期硬依赖私有配置)

**背景**:ChatGPT 第二轮对抗审查以 GitHub Actions 真实 Run 证据(head `8d2c3f4`,conclusion=failure)确认 H-01:pytest collection 阶段即崩溃,27 用例 0 执行——`reslice_pipeline.py` 在 import 期 `CFG = load_cfg()` 读开发机绝对路径下的 gitignored 配置文件。

**本地复现**(沙箱禁改生产配置 → 等价模拟):read_text 定向注入 FileNotFoundError → 同一调用栈(conftest:18 → :50 → :43),exit 4。**审查结论 CONFIRMED**。

**修复**(拒绝吞异常式假修复):
1. `ROOT` 去硬编码:`RESLICE_ROOT` 环境变量可覆盖,默认 `Path(__file__).parents[1]`(仓库相对);
2. 配置惰性加载:删除模块级 `CFG = load_cfg()`,`call_llm` 调用点加载,缺配置**显式抛** FileNotFoundError;
3. 确定性渲染路径与配置彻底解耦:`compile_anchor`/`compile_slices`/`write_outputs` 增加 `model=DEFAULT_MODEL` 参数;`model_tag()` 仅供产物元数据。

**新增测试**(27 → 30 passed + 1 xfailed):
- `test_no_config_import.py` 3 用例:子进程 `RESLICE_ROOT` 指空目录(配置**真实**不存在,与 CI runner 同构)——import 成功 / call_llm 显式失败 / write_outputs 离线三产出;
- `test_e2e_pipeline.py` 1 用例(回应 T-03):process_file 端到端,唯一 fake 边界是 call_llm,产物过真实 QC;
- T-02:test_anchor 倒置 bug 形状测试改 `xfail(strict=True)` 负向回归语义("缺陷仍在"),实现内建兜底时 CI 会提醒翻转断言。

**mutation 对抗验证**(审查要求,破坏生产代码→测试必须失败):
- M1 回退 import 期加载 → 3 FAIL ✅;M2 吞异常假修复 → 1 FAIL(精准)✅;M3 clamp_intervals 空操作 → 8 FAIL ✅。全部回退复跑:30 passed + 1 xfailed,0.8s。

**生产路径真实冒烟**:101生物样本(392 行)真 LLM 单跑 → 21 units 覆盖 21 题,0 issues 0 警告,manifest model=真实配置模型。惰性化未破坏 live 调用链。

**结论**:H-01 已修复并以真实测试+mutation 锁定。**CI 最终证据:GitHub Actions Run 34669715877(head `969dad6`,Ubuntu 24.04 / Python 3.12)= success,日志行 `30 passed, 1 xfailed in 0.63s`**——对比修复前 Run 34668680018(head `8d2c3f4`)= failure、0 用例执行。

---

## R28 · 2026-09-12 · 修复 BUG-21:调试跑覆盖正式账目(+附带发现账目目录假定存在)

**背景**:用户指令"先修复 bug"(BUG-21)。

**修复**:
1. 账目/日志路径选择提为纯函数 `derive_run_paths(out, batch)`:凡 `--out` 独立输出,log/result 一律跟随输出目录名派生(与 R23 batch+`--out` 语义统一);默认账目(pilot/batch-C)只在正式跑时写;
2. **附带修复(集成测试抓出)**:账目/日志目录假定存在——fresh checkout(含 CI)无 `logs/`、`data/` 时 `open()` 直接崩 → 补 `mkdir(parents=True, exist_ok=True)` 兜底(含 `logs/reslice_debug`)。

**测试**:`tests/test_run_paths.py` 4 用例——纯函数契约 3(batch+--out 派生不回归 / 默认路径不漂移 / --out 绝不触 pilot)+ 真实子进程集成 1(RESLICE_ROOT 空目录无配置,跑 `--file --out`,LLM 必失败,断言账目落派生路径、pilot 账目/日志不被创建)。

**mutation M4**:回退旧行为(非 batch 忽略 --out)→ 单元+集成双 FAIL ✅;回退后 34 passed + 1 xfailed。

**结果**:套件 27 → 34 用例;BUG-21 关闭。**CI 实测:Run 34670926001(head `8c79ad4`)= success**。

---

## R29 · 2026-09-12 · 第三轮外部审查结论存档 + 攻击方向转换

**审查方**:ChatGPT(基准 main@d3332ad,交叉核对代码/测试/CI/PRD/status/bugs/历史修复记录)。

**最终评级**:🟡 有条件通过代码层审查 / 🔴 不通过全量生产放行审查。

**接受的结论(逐条核对无误)**:
1. CI 真实绿灯 35 collected / 34 passed / 1 strict xfail(与 Run 34670926001 一致);
2. H-01、BUG-21 正式关闭(subprocess integration + CI 三层证据);
3. `compile_anchor()` 倒置自防御不足 = KNOWN DEFECT / MITIGATED(生产有 clamp_intervals 前置防护,strict xfail 锁定);
4. C 级 OPEN 债:BUG-11(图片恢复目录覆盖)/ BUG-14(重复源 73 + 未分类跑步机)/ BUG-15(半定界数学残留 BLOCK 454 + COMPLEX 228 + 裸 LaTeX 105);
5. **D 级 TEST GAP(本轮审查核心价值)**:D1 语义合法但内容错误的区间(answer 属于下一题)、D2 跨题污染(stem 吃进相邻题)、D3 composite 复杂组合、D4 连续 orphan 链、D5 真实 OCR 噪声、D6 OCR 服务链零覆盖、D7 真实 MIMO 语义准确率;
6. "34 PASS"只证明 deterministic/reslice/fixer/QC 路径,不等于全 preprocessing 项目已验证。

**方向转换(审查建议,采纳)**:停止增加"程序会不会崩"类测试,下一轮专攻**"结构合法但语义错误"**——correctness boundary 从 crash-safety 升级到 silent-mis-segmentation。

**拟定下一轮攻击方案(待用户确认)**:
- 战术 A(零 LLM 成本,最高性价比):对 batch-C 已有的 50 份**真实 LLM 产物**跑语义代理检测——C13 答案区间内容核验(answer_lines 文本须含【答案】/答案表/字母行)、C14 stem 区间题号密度(stem 含 ≥2 个题号行 → 疑似 D2 跨题污染)、C15 answer 行区间与题号归属错位疑似(D1)。先测量真实产物里 D1/D2 形状的实际发生率,再决定是否入 QC;
- 战术 B:合成 adversarial fixture 注入"合法但错误"区间,验证 QC 检测器能咬住(检测器先造、测试后跟);
- 战术 C:D4 orphan 链式组合测试(相邻 orphan/多角色候选冲突/material 联动后再遇 orphan);
- 不动项:OCR 服务链(D6)属另一测试域,单独排期。

**本轮无代码改动,纯审查存档。**

---

## R30 · 2026-09-12 · 战术 A 落地:语义代理探针实测真实产物,确证 BUG-22

**背景**:R29 审查方向转换——停止"程序会不会崩"类测试,专攻"结构合法但语义错误"(D1/D2)。战术 A:对 batch-C 50 份**真实 LLM 产物**零成本测量。

**交付**:`scripts/semantic_probe.py`(P13 答案虚指 / P14 正文跨题污染 / P15 答案归属错位)。探针纪律:报警≠缺陷,人工逐条分诊;未经验证不进 QC。

**测量与分诊过程(两轮)**:
- 首轮:P13=562 / P14=12 / P15=123 → 分诊发现大半是**探针自身盲区**(空格连写"17. A 18. B"、☑/☐/✉答案、"故选/故答案为"、单字母"2. A"、小数"9.5%"、解答步骤编号"1、DNA连接酶");
- refine 正则后二轮:P13=120 / P14=11 / P15=23 → 逐条人工核对源文档区间原文。

**确证结论**:
1. 🔴 **BUG-22(新,🔴)**:题号重复归属 **8/50 文件(16%)**——大题内编号/分卷重编号被当全卷题号;合格考化学(第一次)1-9 双重归属,答案区实键 26-34 逐条对上。**QC C1-C12 全放行 = silent mis-segmentation 在真实数据上实锤**。已加 QC **C13 题号唯一性**+契约测试;batch-C QC 口径 38→**34/50**。
2. 🟠 answer_lines 起点落在题干复述块(BUG-17 家族 answer_lines 变体):四中生物 Q2/Q9/Q19、化学实验汇编 Q17/Q39 实证(真答案在详解"故选X");解析入库需复述感知,已知家族量化+5。
3. 🟡 政治 U35:源文档同行合并导致上一题尾行("…金名片。35.(16分)")并入 material 首行——边界污染 1 行,源驱动。
4. 🟡 地理 U13-14:答案区"4. A"实为"14."OCR 丢字——resolver 按题号取数会漏 Q14,已列入 resolver 入库前置清单。
5. ✅ 洗清:领军物理 Q16(stem"6."系 OCR 丢字,归属正确)、历史 Q25(印刷"5."系源噪音,LLM 靠答案表正确归 25)、十四中物理(答案即解析,合法格式)、醋 Q39/申请书 Q51(材料内编号)。

**教训**:合成 fixture 覆盖不了真实卷的编号花样;**探针两轮迭代本身证明"检测器必须先被真实数据校准,再谈当门卫"**。P13/P14/P15 维持测量仪定位,QC 只收了证据最硬的 C13。

**结果**:套件 35 passed + 1 xfailed(C13 契约 +1);BUG-22 入册 Open,修复方案 A/B/C 待用户拍板。

**附:提交前 EOL 审计抓到 BUG-16 家族复发并根治**:commit diff 出现 464 行假性重写 → 实测 reslice_qc.py 由纯 LF 被编辑工具翻成纯 CRLF(功能零影响,字节层审计受损)。处置:LF 归一 + **`.gitattributes` 仓库级锁死**(`*.py/*.md/*.json/*.yml/*.ini/*.txt → LF`,BUG-16 从"脚本自觉 newline='' "升级为"仓库强制");存量 CRLF 的 reslice_pipeline.py(首个 commit 起即 CRLF)一次性归一。教训:编辑工具也是"保留编辑",同样要过 EOL 审计;git diff 行数暴涨是 EOL 翻转的信号弹。

<!-- 新一轮记录从此行下方追加，R{n} 递增，附 YYYY-MM-DD HH:MM 时间戳 -->

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

## R31 · BUG-22 修复:C13 升级 Scoped Identity + Prompt v2.2 + 确定性迁移(2026-09-12)

**输入**:第四轮对抗性审查(基于 R30 的 e52bd74)。裁决:BUG-22 确认 🔴;A+C 先行、B 并入 resolver 设计;**C13 必须从"题号唯一性"升级为"Question Identity 唯一性"**,否则会把真实试卷结构(选考模块/汇编)误判为错误;C 不得人工改 JSON,须确定性迁移脚本 + migration log。

**根因补确诊**:prompt v2.1 第 247 行"有的试卷分节各自从 1 编号…按原样照抄题号即可"——BUG-22 不是模型漏判,是 **prompt 主动指示**的产物。

**执行**:

1. **C13 → Scoped Question Identity**(reslice_qc.py):身份键 = (section, 题号);同分节重复 FAIL,跨分节同号放行(选考模块三模块印刷号 1-3 本来就相同、汇编各块独立编号,均为合法真实形态);无 section 字段的存量数据退化为全卷判定(R30 口径)。契约测试 +3(同分节报 / 跨分节放 / 全卷退化报)。
2. **Prompt v2.2**(reslice_pipeline.py):删除"分节照抄"条款,改为"题号身份必须全卷唯一,以答案区键位为准,无键位按前面分节最大题号顺延;选考模块保留印刷号但必须输出 section";schema 两个单元样例均加 `section` 字段;版本号两处升 v2.2;validate_manifest 同步升级(同分节重复升 issue,跨分节同号降为 warning,covered 键改 (section,题号) tuple)。
3. **确定性迁移**(scripts/fix_bug22_renumber.py,方案 C,零 LLM):读旧 manifest → 写新 manifest + 重编译 annotated/切片,每单元变更(旧值/新值/规则/证据)记入 `data/bug22_migration_report.json`。三条证据驱动规则:
   - **answer_key**:答案区键位行直接给出全卷题号(合格考化学 N1-N9→26-34,键位"26.【答案】"…"34.【答案】"逐行对应);
   - **shift**:运行最大值顺迁(生物+40、地理+50、英语笔试+25、博雅 11/12-14/15、化学2018必答+25——与 LLM 自己的 unit_id 命名 Q41-50/U26-60/U11-U15 **互相独立地印证**同一答案);
   - **keep**:选考模块("任选一个模块作答")与教师用书汇编保持印刷号,身份由 section 区分。
   默认 dry-run;落盘前强制 scoped 唯一性断言,冲突即拒绝写入。
4. **迁移执行与验证**:8/8 文件 apply 成功;抽验化学合格考 manifest(N1-N9→26-34、section="第二部分 非选择题"、审计记录在、纯 LF);**batch-C QC 重跑(reslice_batch_c_qc_r31.json):C13 残留 0 份,38/50 PASS**——回到 C13 引入前口径,剩余 4 份 FAIL 均为既有 C3/C5/C6 缺陷(缺答案区/丢图/丢表),与题号无关。

**迁移实测踩坑(三个教训,均已固化为代码注释)**:① 汇编 manifest 的 unit_id 大量重复(U1/Q1/Q2 各出现多次),分节归属必须按**单元位置** zip 分配,以 unit_id 为键会静默互相覆盖;② 同名标题消歧序号必须按**标题出现次序**分配(同一标题块下所有单元必须同 section),按单元计数会把同块拆散;③ 排除答案行的正则 `[答案]` 是字符类,把含"方案"的"考点3 制备实验方案的设计与评价"整个误杀 → 改字面;OCR 丢 `##` 前缀的裸考点标题需单独匹配分支。

**防回归**:tests/test_bug22_migration.py 7 用例(shift 递推/无冲突不动/answer_key/keep/scoped 断言双向/同名标题消歧);mutation 验证(shift 故意 -1 → 测试失败 → 回退)。QC 契约 +4。套件 **45 passed + 1 xfailed**。

**方案 B 去向**:manifest section 字段 + (section, number) 复合键消费属 resolver/IR 正式设计(Phase 2),按审查意见不在本轮打补丁;本轮 section 字段只作为身份消歧元数据写入 manifest,不改 resolver 侧任何代码(resolver 尚不存在)。

**结果**:BUG-22 关闭;审查 Phase 1(立即止血)三项全部完成。

## R32 · 第五轮审查验收 + Phase 2 设计评审稿落盘(2026-09-12)

**输入**:第五轮审查(基于 R31 的 e3e4e47)。裁决:**R31 Phase 1 🟢 PASS / ACCEPTED**;BUG-22 分层记账——Prompt defect / QC detection / batch-C migration 三层 🟢 CLOSED,resolver identity model 与 V3 canonical identity integration 🟡 OPEN;**下一步优先进入 Phase 2(resolver 引入 QuestionIdentity 正式模型),不启动全量 rollout**。

**本轮执行(纯设计,零代码变更)**:落盘 `question_identity_design.md` —— QuestionIdentity 第一性原理设计评审稿,逐条回答审查四问:

1. **Identity 层级**:拆分 `SourceOccurrenceIdentity`(source_version + section_ref + printed_number + span,Source Fact,永不被覆盖)与 `CanonicalQuestionIdentity`(section_ref + canonical_number + basis,Preprocessing Interpretation,可重推但每次留证据);unit_id 降级为 display alias(R31 实测其在汇编中大量重复,不可作任何键);长期 locator 契约 = (source_span, semantic_role, ordinal),list position 仅限迁移期临时使用。
2. **Section 定义**:`SectionLocator = (source_version, ordinal, start_line, end_line)`,title 只是 display metadata(可重复/可空/可被 OCR 损坏);OCR 丢标题的三级 fallback,降级必须产生显式 warning,禁止静默。
3. **printed vs canonical number**:schema 目标形态 `{printed_number, canonical_number, canonical_basis, section}`;printed_number 为 Source Fact 永不可改写(化学 2018 非选择卷面印 1-9、答案区键 26-34,只存 26 会永久丢失源事实);现有 `number` 字段语义 = canonical_number,不静默改义;printed_number 不参与 C13。
4. **答案区键位语义**:定性为"全卷答案编排编号(canonical answer-key slot)",是 canonical_number 的最强证据源,**不是答案顺序、不是数据库 identity**;推导证据链 answer_key > running-max(旁证 unit_id 命名)> keep,无证据编号不允许。

另固化:概念漂移防火墙(C13 的 (section,number) 只是 manifest scope invariant,不等于 V3 canonical identity)、7 条不变量清单(Phase 2 验收逐条测)、Phase 3 Question Identity Adversarial Corpus 11 条 fixture 规划(每条全链路:Prompt→Manifest→C13→Resolver→Migration→IR)。

**BUG-22 状态更新**:分层记账,bugs.md/status.md 同步(Prompt/QC/迁移 🟢,identity 建模 🟡)。

**勘误**:`data/reslice_batch_c_qc_r31.json` 实测为 **38 PASS / 12 FAIL**(非 R31 记录所称"剩余 4 份 FAIL");已逐条核对 12 份 FAIL 的 issues 全部为 C3/C5/C6/C7/C9 既有缺陷,**无一条含 C13**——"C13 残留 0"的结论不变,但 FAIL 总数口径以本条为准。

**结果**:Phase 2 设计评审稿待审;实现代码按裁定在设计验收后另起实施任务。

## R33 · Phase 2 设计对抗性审查:设计不变量 1 被真实突变证伪,登记 BUG-23(2026-09-12)

**输入**:用户指令"针对 Phase 2 开启对抗性审查;每个结论必须有真实测试作为证据;不降标准、不自我合理化、不推测"。审查对象:`question_identity_design.md`(R32 v0.1)。

**方法**:全部可测声称落到真实 batch-C 50 份产物上的**生产代码**测量,探针 `scripts/phase2_adversarial_probe.py` → 证据 `data/phase2_adversarial_review.json`;关键结论另固化为 pytest(`tests/test_question_identity_adversarial.py`)。

**核心发现(A3 回迁突变,本轮最重要结论)**:把 R31 迁移的 7 份产物题号全部回退到 old 值(BUG-22 原始形态:选择题与非选择题各自从 1 编号),跑生产 C13:
- **保留 section → 仅 1/7 被拦**(唯一命中博雅语文,是回退后恰成同分节重复才触发);
- **删除 section → 7/7 全拦**。

即:**scoped C13 一旦有 section 字段,就对 BUG-22 的跨分节重号形态失去守卫能力**——R31 把"分节不同"当成了合法性的充分条件,而真正判据应是"是否存在显式 keep 依据"。设计 v0.1 不变量 1("跨节同号 = LEGAL")被证伪,修订为 **canonical 全卷唯一 + `basis=="keep"` 显式豁免**。生产侧登记 **BUG-23**(修复依赖 basis 字段,不盲修——简单改回全卷唯一会重新误伤选考/汇编合法重号,该假阳性 R31 已实证)。测试固化:xfail(strict=True) 锁定"回归形态必须被拦"的修复义务,修复后 XPASS 强制失败提醒转绿。

**其余探针裁定**:
- A1 section 覆盖率:**291/1484 单元(19.6%),42/50 文件零 section**——scoped identity 现实生效面不足两成,Phase 2 必须含存量回填;
- A4 静默降级:删 section 后 **0/8 份**产物 QC 输出任何"缺 section"显式告警——设计不变量 6 当前未实现,列为实施必测;
- A5 printed 回填覆盖:migration report 含 old 值仅 **41/1484 单元(2.8%)**——§3 回填策略修订:v2.1 存量须从源 md 新增确定性推导,推不出标 `provenance=unknown`,禁止把 canonical 猜成 printed(伪造 Source Fact 比缺失更糟);
- A6 unit_id 重复:1/50 文件(专题十六)**78 单元**重复——§1.3 声称成立并量化;
- A7 SectionLocator 字段普查:50 份 manifest **无任何 ordinal/span 类字段**,section 仅裸 title——§2 设计在现有 schema 上不可实现,manifest 必须扩展;
- A2 scoped 不变量普查:真实数据零冲突(但该检查与 C13 同源,不构成独立证据)。

**设计文档修订**:`question_identity_design.md` 升 v0.2——不变量 1 重写、§2/§3 补现实约束、新增 §5.1 审查裁定表(每条含测量数字与证据文件指针)。

**过程记录(沙箱行为)**:DSH workspace-write 沙箱拒绝在**新建子目录**内写文件(策略快照只放行既有目录),探针改为预建目录内 uuid 前缀平铺;此为环境约束,非代码缺陷。

**教训**:**守卫升级必须做回迁突变验证**——修完缺陷要把缺陷形态重新注入真实产物跑守卫,证明"新检测器仍拦得住原始缺陷"。R31 只验证了"C13 残留 0"(存量已修),没验证"C13 还拦得住 BUG-22"(守卫有效性),这是检测器换键时的系统性验证盲区;已写入 BUG-23 教训。

**结果**:设计 v0.1 判定存在 1 个被真实数据证伪的不变量 + 3 个未实现/不可实现项,全部修订并留痕;BUG-23 登记;套件 **46 passed + 2 xfailed**。Phase 2 实施前置条件收敛:先验收 v0.2 设计,再实施。

## R34 · Phase 2 实施:QuestionIdentity v2 四项一体落地,BUG-23 修复(2026-09-12)

**输入**:第五轮审查对 R33 的验收——v0.2 设计方向 🟢 通过,附 4 项实施条件(basis 字段 / SectionLocator schema / C13 升级且 BUG-22 回迁突变从 XFAIL 转正 / 存量确定性回填),冻结验收标准 P2-01~P2-08,三方向测试纪律(非法 FAIL / 合法 PASS / 证据不足 PENDING_REVIEW)。核心设计裁定:**Identity 与 Legitimacy 分离;QC 只验证已建立的语义事实,不做语义推理**。

**实施语义修正(落地时发现的真实边界)**:"canonical 全卷唯一 + keep 豁免"不能要求"重复各方全部 keep"——会考化学实测选择题 1-25 与选考模块 keep 1-3 天然同号。裁定为**划分语义**:非 keep 持有者之间全卷唯一(BUG-22 回归 = 两个非 keep 跨节重号 → FAIL);keep 为个体豁免但必须带可回源证据(`basis_evidence` 含 L{行号} 且界内),证据不足 → PENDING_REVIEW;同分节重复永远 FAIL。

**落地组件**:
1. `scripts/question_identity.py`:共用身份模型(构建 + 验证),QC/回填/resolver 同一实现,杜绝各处自行推断合法性;`build_section_locators`(ordinal+span,同名标题按出现次序消歧,复用 R31 迁移脚本踩平过的标题规则)、`assign_identity`(按位置分配,绝不以 unit_id 为键)、`check_identity`(三态)。
2. `reslice_qc.py` C13/C14 v2 + 裁决三态 FAIL/PENDING_REVIEW/PASS;v1 存量(无 identity_version)保留 R31 scoped 语义。
3. `reslice_pipeline.py`:Prompt v2.3(printed_number 必填,源事实与入库编号分离,禁止把入库题号抄作印刷题号);**write_outputs 修复实施中抓到的真缺陷——自组装 manifest 会把 identity 字段静默洗掉**。
4. `scripts/phase2_identity_backfill.py`:零 LLM 确定性回填,basis 取自 R31 审计过的 PLAN,printed 取 migration report old 值或题干首行解析,解析不出 = null+unknown(禁止猜测);落盘前 check_identity fail 即拒写。

**存量回填结果(batch-C 50 份)**:50/50 apply,**0 fail / 0 review**,612 个 SectionLocator;printed provenance:source_line 948(63.9%)/ migration_report 134 / unknown 402(27.1%,全部 printed=null);basis:printed_as_is 948 / keep 93 / shift 31 / answer_key 9 / explicit 1 / unverified 402。回填后 QC(`reslice_batch_c_qc_r34.json`):**38 PASS / 0 PENDING_REVIEW / 12 FAIL**——与 R31 PASS 集完全一致,零回归。

**验收证据(P2-01~P2-08 全绿,`tests/test_question_identity_phase2.py` + 复跑探针 `data/phase2_adversarial_review_r34.json`)**:
- **P2-03 关键复验:BUG-22 回迁突变在真实产物上保留 section 7/7 全拦**(修复前 1/7);
- **P2-05:A4 缺 section 8/8 显式告警**(修复前 0/8);
- P2-04 反方向同时成立:合法 keep 93 单元零误杀(回填 0 fail);同分节 keep 重复仍 FAIL;
- 第三方向:fake keep / 越界证据 → PENDING_REVIEW(证据不足 ≠ 非法);变异校验三连(空证据/越界/双非 keep)全部被拦截;
- BUG-22 回迁突变测试从 strict xfail 转正为普通通过用例(审查要求的"XFAIL → 转正"达成)。

**实施中测试抓到的生产缺陷(测试先行的价值)**:write_outputs 洗 identity 字段(已修);PRINTED_LINE 正则要求数字后必有空格导致"26.【答案】"解析不出(已修)。

**已知残留(不隐瞒)**:v1 历史产物(pilot 16 份等)仍走旧语义,回填列为后续任务;unverified 402 单元 printed 无证据(多为综合题多号单元),显式 unknown 不猜;basis_evidence 的语义充分性需 Phase 3 对抗语料覆盖(PENDING_REVIEW 通道即为此)。

**结果**:BUG-23 关闭;BUG-22 状态重述(撤销 detection CLOSED,待 BUG-23 修复后 C13 检测器 🟢、Resolver Identity 🟡 等下游消费);套件 **64 passed + 1 xfailed**。

## R35 · Phase 3:Evidence Soundness 对抗语料,第二层证据语义检查(2026-09-12)

**输入**:第五轮审查对 R34 的验收——Phase 2 🟢 ACCEPTED,BUG-23 🟢 CLOSED,四项全 🟢;Phase 3 指令明确:**不再堆规则,攻击"PASS 为什么成立"**,验收标准从 Guard Soundness 提升为 **Evidence Soundness**;裁决语义:PASS=机器能证明 / FAIL=机器能证伪 / PENDING_REVIEW=无法证明也无法证伪。核心 test gap(不是 BUG,是义务):basis_evidence 机器校验只证明了"引用存在且位置合法",未证明"引用内容构成局部编号语义"。

**执行**:

1. **第二层证据语义检查**(`question_identity.evidence_semantic_reason`,QC 与回填共用):keep 豁免引用行必须承载编号语义(题号式 26./一、;结构性 模块/任选/考点/汇编/针对训练/X 组;或分节标题行 SECTION_RE 豁免题号相关性),纯 prose/OCR 噪声行 → PENDING_REVIEW;非标题引用行的行首题号与本单元(印刷号∪canonical)完全无关(如引用"26.【答案】"行)→ PENDING_REVIEW。**诚实边界:只升级到"内容承载编号语义且题号相关",不宣称语义真值证明**——深度语义仍走人工复核通道。
2. **真实数据复验**:batch-C 50 份跑第二层检查 **0 新增 review**(既有 keep 证据全部确实引用分节标题行,新检查未误伤);QC 38 PASS / 0 PENDING_REVIEW 不变。
3. **对抗语料** `tests/test_identity_adversarial_corpus.py` 16 用例全绿,覆盖审查冻结的全部攻击面:baseline / 合法模块 / BUG-22 原型 / 同节 keep bypass / 同名 section occurrence / 缺 section / 证据越界 / 证据缺失 / **证据行无编号语义(核心)** / **证据题号无关(核心)** / OCR 内容错 / printed 保持 unknown / unit_id 解耦 / section 顺序重排 / locator 漂移证伪 / **回填重跑幂等(真实 batch-C 字节一致)**。
4. **变异验证**:短路 evidence_semantic_reason → 恰好 c09/c10/c11 三条核心攻击用例失败 → 回退;另仓库级幂等佐证:--apply 重跑后 backfill 报告与已提交版本零差异。

**结果**:Evidence Soundness 第一层机器可证增量落地,语料 16/16;套件 **80 passed + 1 xfailed**;无新增 confirmed BUG(test gap 按审查意见保持为 PENDING_REVIEW 义务而非缺陷)。

## R36 · pilot 16 份 v1→v2 确定性迁移清尾 + BUG-24 发现(2026-09-13)

**输入**:第五轮审查对 R35 的验收——Phase 3 第一阶段 🟢 ACCEPTED,"闭环质量高于 R34";**Identity 层正式冻结**(不再堆规则);裁定下一步优先级 ① 先清 pilot 16 份 v1 回填(生产数据不得并存两套 identity contract)→ ② 全量 rollout 是更高层 system readiness gate,Identity 闭环不能替代 → ③ resolver 必须消费 v2,不得重新发明 identity。验收标准六条冻结:migration success / schema validation / C13+C14 / idempotency / 不产生非法 PASS / 不改变既有正确 identity。

**执行**:

1. **基线盘点**:pilot 16 份全部纯 v1(无 identity_version/sections/basis/printed);源文件 16/16 存在、行号无漂移;v1 legacy QC 基线 = **15 PASS / 1 FAIL**(三十一中化学,C13 重号),留档 `data/phase3_pilot_v1_baseline_qc.json`。
2. **迁移工具** `scripts/phase3_pilot_v1_migration.py`(零 LLM):复用 batch-C 回填核心(BUG-22 PLAN/迁移报告均不覆盖 pilot → basis 全走题干首行确定性解析 printed_as_is 或 unverified,绝不猜测);**迁移后自检四条**(identity v2 成立 / 内容事实按位置逐单元不变 / printed_provenance=source_line 必须回源成立 / check_identity 无 fail),任一违反即原样回滚该文件——自检是工具级验证,**未新增任何 QC 规则**(守住 Identity 冻结)。
3. **迁移结果:15/16 applied,0 violations;第 16 份(三十一中化学)被 C13 如实拒写**。迁移后 QC(`data/phase3_pilot_v2_qc.json`)= 15 PASS / 1 FAIL,**与 v1 基线裁决集零翻转**;幂等:字节级 15/15 通过 + --apply 重跑 0 写入;事实快照 `data/phase3_pilot_v1_facts.json`(16 份 / 389 单元,只写一次,防未来漂移锚点)。
4. **验收测试** `tests/test_pilot_v1_migration.py` 10/10:六条验收逐条固化 + **变异 sanity**——伪造 printed(source_line 但源行解析不出)/ 事实漂移(偷改 canonical)/ 注入同分节 keep 重号,三类破坏全部被 verify_post 拦截。

**BUG-24 发现(本轮最重要的负发现,详见 bugs.md)**:三十一中化学被拒写的真实根因不是数据缺陷——L324 `## 二、 填空题…注意:…答案才计分` 是合法分节标题(填空题独立编号 1-11),`_heading_rows` 的 `答案|解析|评分` 排除器对整行子串匹配,标题尾 note 含"答案"→ 填空题节被误杀 → 11 组同分节重号误判。**裁决无翻转(v1 同 FAIL),无非法 PASS**;但按 R35 冻结令**不擅自修**:收窄排除器实测会改变 batch-C ≥3 份已提交 v2 产物的 section 划分(naive 收窄更会把 135 行【解析】误升分节),牵动 R34/R35 证据链,应作为独立受审变更;且即使节被正确建模,该卷仍是两个非 keep 跨节重号,需三方裁决,不能自动豁免。

**结果**:pilot 迁移 15/16 完成并关闭;唯一残留挂 **BUG-24 OPEN(决策点上报)**;套件 **90 passed + 1 xfailed**;生产数据 v1 残留面从 16 份缩至 1 份(且该份 v1/v2 裁决一致 FAIL,无契约撕裂风险)。

## R37 · BUG-24 SectionLocator correctness 修复 + 受影响真实 corpus 全链复验(2026-09-13)

**输入**:用户对 R36 的裁定——pilot migration 🟢 ACCEPTED;BUG-24 🔴 CONFIRMED(deterministic source-structure extraction defect),**应修、现在修、不带进 Resolver 消费**;限定边界:**只修 SectionLocator,不修 Identity**——不得顺手重设计 keep/basis/canonical 语义,不得为了让三十一中化学"过"而自动制造 keep;修复前先锁定历史 corpus 影响面(before 快照),修复后比对 NEW-OLD 而不是只看 pytest;验收标准冻结 B24-01~B24-08。

**执行**:

1. **全语料排除器盘点(改代码前)**:3120 源卷 + reslice-scope 75 源。第一版候选规则(naive 头部窗口 4)过度恢复 4902 行——聚类定位主形态 `### 9. 【答案】C`(归一化未剥印刷题号前缀)与 `###### 【答案】32. A`(六级 # 漏网,SECTION_RE 实际带可选 `#{1,4}\s*` 前缀组);规则迭代到 V2(剥 `#{1,6}` + 序号前缀交替到不动点 + 头部窗口 10)后恢复面收敛到 848 行,reslice-scope 13 行**逐条人检**:6 条真分节标题(A 类,修复目标)+ 7 条源结构标题(benign:参考答案卷 H1 题/解题要求/听力小节),**0 条答案内容行误升**;反向残留假阴性扫描(`解析几何` 类 topic 词)全语料仅 1 例(汇编卷,非提交范围)→ 诚实记录为规则边界,不为 1 例扩规则面。证据 `data/bug24_exclusion_inventory.json`。
2. **影响面快照(B24 §6 冻结要求)**:`scripts/bug24_locator_snapshot.py` 对 batch-C 50 + pilot 16 记录 manifest sha256 / sections 全量 / 逐单元 section_ref+basis+printed / check_identity fails+reviews → `data/bug24_locator_snapshot_{before,after}.json`;before QC 复现 R34 已提交裁决集**逐文件零差异**(38 PASS/12 FAIL),环境一致性先行验证。
3. **修复**:`question_identity._heading_rows` 排除器改两阶段(`_norm_heading_head` 结构归一化 + `_is_answer_heading` 头部窗口判定);marker 集不变、不新增 QC 规则、Identity/keep 语义零改动(冻结令边界)。
4. **全链重跑**:batch-C 回填 50/50 applied(0 fail);迁移工具新增 `--refresh-v2`(v2 存量随 locator 修复重刷 sections,须与 R36 FACTS 事实快照逐单元一致否则拒写,自检违规即回滚)→ pilot 15 refreshed + 三十一中化学被 C13 如实拒写(字节不变)。
5. **NEW-OLD 比对**:`data/bug24_fix_report.json`——**11 份 manifest 重生成**(batch-C 7:会考化学/地理/数学/物理、巴蜀化学、平谷历史、三十五中英语;pilot 4:人大附中地理、西城生物、石景山语文、石景山一模物理);单元移节最大 54(平谷历史 50 道选择题移入恢复的"一、选择题"节,非选择题回归第二部分——语义抽查正确);**QC 裁决集零翻转**(batch-C 38 PASS/12 FAIL、pilot 15/1 FAIL 逐文件一致);changed 文件 check_identity fails 全部 0→0;二次重跑字节级幂等 66/66。
6. **三十一中化学(修复的正确结果)**:FAIL 理由从"同分节重复归属"(错误建模)变为"**跨分节重号含多个非 keep**"(正确建模)——填空题节恢复、F1-F11 获得正确 section_ref,**未自动产生 keep**,文件依旧 fail-closed 拒写。SectionLocator correctness 与 Identity legitimacy 两个问题就此在实数据上分离证明。
7. **验收测试** `tests/test_bug24_section_locator.py` 13/13:B24-01(真题恢复,合成+真实卷双层)/ B24-02(8 条真实答案行回归语料 + 5 条 note-marker 标题 + benign/残留行为锁)/ B24-03(7 份受影响 batch-C 全链 QC)/ B24-04(不自动 keep、仍拒写)/ B24-05(BUG-22 原型仍 FAIL)/ B24-06(既有 PASS 集 53 份零非法翻转)/ B24-07(确定性,合成+真实卷)/ B24-08(Evidence Soundness 路径不变);**变异 sanity** 三类破坏(整行排除回灌缺陷形态 / 窗口归零 / 窗口无限)全被数据区分力拦截。R35 对抗语料 16/16 重跑不回归。

**结果**:BUG-24 🟢 CLOSED(bugs.md 结案);套件 **103 passed + 1 xfailed**;生产数据 v1 残留仍 1 份(三十一中,但其 FAIL 已是正确理由,等待 keep 三方裁决——独立决策点,不由本修复吞并);下一站按用户路线图:**Identity v2 final freeze → system readiness gate(BUG-11/14/15、OCR 覆盖、真实 LLM/OCR 可重复性)→ rollout / Resolver 契约级设计**。

## R38 · 对 R37 全部结论的对抗性审查(每个结论必须有真实测试)(2026-09-13)

**输入**:用户指令——对 R37 开启严格对抗性审查,不降低测试标准、不自我合理化、不强行解释未通过项、不靠推测下结论。自查先行声明 R37 证据链最弱两环:① "全语料 0 答案内容行误升"只做了 shape 抽样人检,**未穷尽**;② "裁决零翻转"只比对 verdict,**未比对 issue 明细**。

**执行与裁决(8 个攻击面,全部独立实现,不复用 R37 探针)**:

- **A1 恢复行穷尽审计(独立检测器)**:方括号答案/☑/闭括号/答案区词/行首题号五类检测器全量重扫 → **证伪 R37 主张**:840/848 条恢复行中检出 229 条可疑,逐条人读裁决——224 条为 `# …参考答案` 答案卷 H1 文档题(benign 类,reslice-scope 5 条已人检);**13 条真实坏/边界恢复**:8 条 `\.` 转义点击穿数字前缀剥离(`### 26 \.（12分）【答案】`、`### 18 \.（8分）答案示例` 等)+ 3 条 marker/窗口跨界 straddle(`## 书面表达第一节参考答案：`、`附：等级评分标准`、`## 【点睛】…答案要点：`×2)+ 1 条 OCR 行融合(标题与 `1.【答案】B` 同行)+ 1 条合法标题(育英数学"三、 解答题…参照评分标准给分",人检为真分节)。**全部位于 full-corpus 非提交范围,提交产物零影响**。
- **A2 QC issue 明细级比对**:batch-C + pilot 全部 66 份,issues/review_notes 逐条 diff → **0 差异**(verdict 相同且理由相同)。
- **A3 事实漂移**:66 份 manifest 全部单元的 basis / printed_number 前后比对 → **0 漂移**。
- **A4 静默甩下扫描**:batch-C/pilot 之外全部产物目录(audit-a5/stress10/test-v21/auto-annotated)扫 identity v2 存量 → **0 份**(R37"11 份=全部受影响 v2 产物"成立)。
- **A5 测试缺口(自查发现)**:`--refresh-v2` FACTS 锚点守卫此前**零测试覆盖** → 补 3 条真实测试(事实漂移拒刷+字节不动 / 锚点缺失拒刷 / 锚点一致放行并重算),漂移用例即变异注入。
- **A6 结构级完整性证明**:66 份 before/after sections 比对——**新增 start_line 集合恰等于 13 条已知恢复行**(无未解释新增)、**丢失 heading = 0**(排除器收紧方向性证明:新规则排除集是旧规则的子集,不可能丢标题)。
- **A7 数字复现**:生产代码独立重扫 3120 卷 → head 44211 / excluded 10899 / restored 848 / reslice 13,与 R37 已提交证据**逐位吻合**(修复后 840/10907/13 再次吻合)。
- **A8 窗口边界人检**:marker 归一头位置 8~12 的 41 行全部列出人读——合法恢复(备选答案@12、附加题@11、综合题@9…)与坏行(全部归入 A1)各就各位,**窗口 10 有数据支撑而非凑数**;扩窗到 11 即误杀"综合题(40分)(答案书写在答题卡上)"(实测证据,故不扩)。

**修复(仅一处,机械性根因)**:`_NUM_PREFIX` 序号前缀允许 OCR 转义点(`\d{1,3}\s*\\?\s*[.、．]`)→ 8 例误升全灭,恢复面 848→840;**66 份提交 manifest 字节零变化**(重生成快照与已提交 after 快照逐字节一致);4 条真实 `\.` 行入 B24-02 回归语料。

**结果**:R37 结论逐条重新裁决——B24-01/03/04/05/06/07/08、幂等、确定性、CI **维持成立且证据更强**(A2/A3/A4/A6 为新增强证据);**"0 答案内容行误升"修正为"提交范围 13 行 0 误升;全语料 840 行含 4 例已知残留(0.5%,均非提交范围,明细入库)"**;补 1 个测试缺口 + 1 个规则缺陷(转义点)。套件 **106 passed + 1 xfailed**。审计工件:`data/r38_audit_report.json`、`data/r38_qc_issue_diff.json`。

## R39 · 2026-09-13 · R38 用户裁定落盘:BUG-24/25 关闭、R37 全称主张撤销、审查协议建立、冻结基线登记(纯记账轮,零代码变更)

**输入**:用户对 R38 的最终裁定——R38 **🟢 ACCEPTED**(评价为"高质量 adversarial review,审查机制已能主动推翻自己的过强结论");BUG-24 **🟢 CLOSED**(B24-01~08 全部成立);8 例 `\.` 缺陷 **🟢 FIX VERIFIED**(正式判定为真实 BUG,现已关闭);4 例残留 **🟡 ACCEPTED KNOWN LIMITATION**(定性:当前确定性规则无法在提高 recall 的同时保持 precision——不是 BUG,也不得塞进 BUG-24 的 closed 结论里);R37"全语料 0 误升" **❌ RETRACTED**(被 R38 穷举复核证伪);新增审计方法论规则 **🟢 ESTABLISHED**;`7f37be9 / R38` 定为 **Identity v2 + SectionLocator 冻结候选基线**,项目从 Identity correctness 切换到 **Preprocessing system readiness**。用户同时要求:HEAD_WINDOW=10 只能记录为"当前审计语料上经验验证的边界参数",不得记录为"理论上正确的窗口"。

**执行(零代码变更,纯记账)**:

1. `bugs.md`:BUG-24 状态改 **🟢 CLOSED**,附**三概念分账**(① correctness 缺陷 CLOSED / ② 3 例 straddle 跨界 = ACCEPTED KNOWN BOUNDARY / ③ 1 例 OCR 行融合 = ACCEPTED OCR LIMITATION;明确禁写"heading detection 问题全部解决"这类无证据表述);**新增 BUG-25**(`\.` 转义点击穿序号前缀剥离,🟢 CLOSED:发现=A1 独立检测器、根因=`_NUM_PREFIX` 不认转义形态、修复=允许转义点、对账=848→840 恰减 8 + 66 份提交 manifest 字节零变化 + 4 条回归语料);三十一中化学 keep 三方裁决保持为独立决策点,不被关闭吞并。
2. **新建 `review_protocol.md`**:规则 1 **全称命题必须由全称验证支撑**(触发词:全部/所有/零/没有/唯一/无遗漏/无误升/全量保持/100%;两问:验证域是什么、是否穷举;非穷举只能写"在 X 范围内";R37 证伪案例挂账);规则 2 **readiness claim 三列制**(claim / 证据域 / 证据类型,未测行必须显式写"尚待测")**+ 禁止"局部 PASS → 系统 PASS" + "套件绿灯 ≠ system readiness"**;规则 3 汇总既有方法论六条(修复正确≠结论充分 / 窗口参数经验表述 / 守卫升级回迁突变验证 / Source-structure 五步法 / 实现存在≠受保护 / 三概念分账)。
3. `question_identity_design.md`:§10.4 BUG-24"OPEN 待裁决"过期措辞更正为 CLOSED 链路;§10.5 增 HEAD_WINDOW 精确表述(**经验验证参数,扩到 11 实测误杀合法标题 `综合题(40分)(答案书写在答题卡上)`,当前不应扩大,未来扩窗提案必须附全语料误杀实验**);新增 §10.6(R39 最终裁定 + 冻结基线 + Identity 层不再扩展规则 + resolver 必须消费 v2)。
4. `status.md`:一句话现状/当前阶段切换 System Readiness Gate;风险表更新 BUG-24 CLOSED 行、BUG-25 新行、R37 行内全称主张标注 **RETRACTED**、R38 行改 🟢 ACCEPTED、新增 R39 冻结基线行。
5. **测试基建硬化(本轮唯一非文档改动,`pytest.ini`)**:本地裸 `pytest` 首次跑出收集期全灭——① 仓库根被沙箱留下 4 个 ACL 异常的 `pytest-cache-files-*` 空目录(连 Get-Acl 都 Unauthorized),收集遍历即 PermissionError;升级 danger-full-access 删除恢复;② 裸 pytest 还误收 `_archive` 归档区的历史 `test_*.py` 导致收集错误(CI 一直用 `pytest tests/` 故从未暴露)。修复:`testpaths = tests`(与 CI 口径一致)+ `norecursedirs` 防御清单。复跑:**106 passed + 1 xfailed(17.24s)**,与 R38 基线一致。

**结果**:R38 全部裁定入库,三本台账与设计文档口径一致;冻结候选基线 `7f37be9 / R38` 登记;下一阶段 = **System Readiness Gate**(BUG-11/14/15、OCR 覆盖与真实行为、image recovery、真实 LLM 稳定性、Resolver 契约消费,每 claim 按三列制举证);Identity 层不再扩展规则。生产代码零变更(仅 pytest.ini 基建硬化),套件 **106 passed + 1 xfailed**。

## R40 · 2026-09-13 · 对 R39 全部结论的对抗性审查(16 个攻击面,每个结论真实测试)

**输入**:用户指令——对 R39 全部结论开启严格对抗性审查,每个结论必须有真实测试证据;不降标准、不自我合理化、不强行解释未通过项、不靠推测。自查先行声明:R39 是记账轮,最弱环节是①记账数字只是转抄 R38 工件而非独立复现;②"三处撤销/空目录/CI 一直"这类全称与存在性主张;③pytest.ini 硬化声称的"口径对齐"与排除功能。

**执行与裁决(独立实现,不复用 R38 探针;探针用后即删)**:

- **V1 基线完整性 🟢**:`git diff 7f37be9..8fb7e48` = 6 文件(5 md + pytest.ini),`scripts/ tests/ ocr_service/` 零改动——"R39 未动生产代码,冻结基线不受影响"成立。
- **V2 CI 🟢**:`gh run view 34700526059` → conclusion=success,headSha=8fb7e48 精确匹配。
- **V3 套件 🟢**:重跑 **106 passed + 1 xfailed**(18.12s)。
- **V4 收集口径 🟢**:裸 `pytest` 与 `pytest tests/` 收集列表 Compare-Object 逐项一致(107 项,_archive 命中 0);变异对照:`pytest _archive` 显式传路径即复现收集错误 → `testpaths` 确为保护源,非巧合。
- **V5 norecursedirs 功能 🟢**:投毒 `pytest-cache-files-zzz/test_poison.py`(import 即 raise)——裸跑 exit 0 不收集;显式传该路径即爆 `RuntimeError: POISON COLLECTED` → 排除规则功能性成立,变异对照成立。
- **V6 "空目录"主张 🔴 证伪(证据资格)**:当时唯一证据是 `dir /a /b` 返回 "File Not Found",与"拒绝访问"不可区分——**"空"没有证据资格**,R39 行文按规则 1 精确化为"内容不可读(ACL 拒绝),是否为空无法证实"。因果链本身仍成立:删除后同一收集命令错误 6→2(仅剩 _archive),目录确为致错因;且删除后已不可再验(如实记录)。
- **V7 "CI 一直用 pytest tests/" 🟢(全称主张穷举)**:git 历史穷举——ci.yml 仅一个历史版本(a7d78f6),内容即 `pytest tests/`;"一直"以穷举成立。
- **V8 三概念分账 🟢**:`ACCEPTED KNOWN BOUNDARY` / `ACCEPTED OCR LIMITATION` 在 bugs.md / status.md / log.md 三处各 1 命中。
- **V9 "三处 RETRACTED" 🔴 半证伪 + 当场修复**:status.md 2 处、log.md 2 处成立;**bugs.md 0 处**(唯一"撤销"命中属 BUG-22 历史行)——review_protocol 出处句在 bugs.md 上仅有 supersession 措辞支撑。修复:bugs.md BUG-24 条目补"R37 主张正式撤销(RETRACTED)"显式行;复验三文件命中 ≥1。
- **V10 BUG-25 全语料记账 🟢(最终逐位复现,过程中两次自查纠偏)**:独立重实现扫描。第一轮用我自己的过滤器得 3134 文件/56023 候选,与已提交 3120/44211 不符——未绕过,分目录量化定位第一层口径差为产品测试目录(reslice-audit-a5 2 份 + reslice-stress10 9 份 + reslice-test-v21 3 份,后者恰贡献 17 行整行排除,精确解释 excluded 偏差)。对齐后**九个数字全部逐位复现**:files 3120 / head 44211(候选−整行排除)/ 整行排除 11747 / 生产排除 10907 / 去转义点排除 10899 / restored 840 / restored 前 848 / reslice 源 75 / reslice restored 13。新旧差集恰 8 行,8/8 含 `\.` 且现被生产排除。第二层:inventory `files_full=3045` 与 3120 的差——先后两个假说(零候选文件、旧字段未更新)**均被实测证伪**,最终结构解释经专项验证成立:**75 份 manifest(batch-C 50 + pilot 16 + stress10 9)→ 75 个去重源全部在 3120 集内,3120 − 75 = 3045**(full 计数即排除 reslice-scope 源后的口径),无遗留疑点。
- **V11 🟢**:8 行逐一复验(朝阳二模历史 L291、西城一模历史 L374、西城二模历史 L323、通州语文 L489、临川政治 L266/L274、东城物理 L445/L461)生产现全部排除。
- **V12 窗口边界 🟢 结论成立 / 措辞 🔴 修正**:实测临川地理 L283 `## 二、 综合题（40分）（答案书写在答题卡上）`:归一头『答』= **第 10 字符**(0 基 index 9)、『案』= 第 11;窗口 10 保留、窗口 11 误杀——结论成立,但"marker 恰在第 9 位"表述不精确(1 基应为第 10),设计文档 §10.5 与 `question_identity.py` 注释已改为"『答案』跨第 10~11 字符"。
- **V13 BUG-25 保护力 🟢(变异验证)**:临时回退 `_NUM_PREFIX` 转义点 → `test_b24_02_answer_lines_stay_excluded` **FAIL**(1 failed/12 passed)→ `git checkout` 恢复 → 13 passed。修复受测试保护(协议规则 3.5 实证,非"实现存在")。
- **V14 字节稳定性 🟢**:66/66 manifest 当前 sha256 == 已提交 after 快照,0 不一致。
- **V15/V16 🟢**:R39 引用的 8 个工件文件全部存在;`7f37be9` 基线串在 status/log/设计文档一致。

**发现汇总**:0 个结论级翻转;3 个措辞/落盘级问题(V6"空目录"无证据资格、V9 bugs.md 缺显式 RETRACTED、V12"第 9 位"1 基不精确)——**全部当场修正并复验**。复现方法论事实留痕:语料 gitignored,数字复现必须先从已提交工件反推口径定义再对账;"files 3045 vs 3120"这类表层矛盾在深挖后都有结构性解释,**禁止用"字段过期"之类的猜测收尾**(本条 V10 即先猜后纠的实例)。

**结果**:R39 全部实质结论经真实测试维持成立;R40 修正 3 处后,BUG-24/25 关闭、R37 撤销、review_protocol、冻结基线登记的证据链闭合。套件 **106 passed + 1 xfailed**。

---

## R41(2026-09-13):R40 用户裁定落盘 + System Readiness Gate 正式启动

**用户裁定 R40:🟢 ACCEPTED(合格的"审查审查"闭环)**。裁定要点:
- 接受 16 攻击面验证、变异/穷举方法、V10 两次假说证伪不猜测收尾、BUG-25 mutation-sensitive protection、66 manifest 字节级稳定、R37 正式撤销;
- **限定措辞被采纳并落盘**:"R40 独立复核范围内,R39 的实质工程结论未发生结论级翻转;发现 3 项证据表达或台账完整性问题,均已修正并复验"——即"结论级翻转 = 0"成立 且 "原报告完全无错误 = false" 必须同时成立(V6 证伪了"空目录"这一原始陈述,虽不影响核心因果结论);
- **方法论事实确认:CI 绿只是证据链一环,不等于审查结论正确**;
- **R40 ACCEPTED ≠ 系统冻结**:preprocessing 项目不得宣布全面完成,转入 **System Readiness Gate**——"从局部缺陷对抗,升级为端到端系统不变量对抗",Gate 不重复 R40;
- 四个一级攻击面:**A 生产路径完整性**(Input→preprocessing→artifact→manifest→QC→identity→handoff;字段丢失/schema 漂移/v1v2 混用/Git 忽略工件依赖/fresh checkout 不可运行/生产数据与 fixture 语义不一致);**B 失败传播**(FAIL/PENDING_REVIEW/MISSING/STALE 是否可能被后续阶段静默转换为 PASS——用户标记为当前最危险系统级攻击面之一);**C 工件可追溯性**(Source→Output→QC→Fix→Snapshot 完整回溯,防"产物正确但无法证明为什么正确");**D Fresh 环境可复现**(fresh clone + 无隐藏本地语料 + 无忽略工件依赖 + 无预存在目录;R36"本地有数据→CI 没有"为一级先例);
- **三十一中化学 keep 三方裁决作为独立语义裁决事项保留**,不与 readiness gate 混为同一问题;keep 是显式豁免,不能因 SectionLocator 已修自动合法,也不能因当前 FAIL 默认 Locator 仍有问题(R33/R34 原则)。

### R41 Gate 执行明细(四攻击面实测)

**A 生产路径完整性**:
- A1 schema 全量(80 份 manifest:pilot 16 + batch-C 50 + stress10 9 + test-v21 3 + audit-a5 2):JSON/必需键/units 字段/section_ref 可解析/printed_provenance/basis/源在位/切片+annotated 在位——**80/80 零缺陷**(`data/r41_gate_ac_report.json`)。
- A2 v1/v2 混用盘点:生产交付范围(pilot+batch-C)= 66 份,**65 v2 + 1 v1**(三十一中,keep 裁决挂起件,已知);测试语料 stress10/test-v21/audit-a5 共 14 份全 v1(未回填历史件,非交付范围)。readiness 声明必须限定范围:"生产 66 份中 65 v2"。
- A3 当前 QC vs 已提交 QC 证据逐份对比:batch-C/stress10 零漂移;pilot 见 C-01。

**B 失败传播**:
- **B-01 🔴 CONFIRMED → BUG-26 🟢 修复**:`--recompile` 只传 `{"units":...}` → write_outputs 身份头拷贝恒不触发 → 重编译静默洗掉 `identity_version/sections`,QC 降级 v1 语义、违反 resolver v2 契约。详见 bugs.md BUG-26。
- B-02 降级爆炸半径量化(65 份生产 v2 逐一模拟剥离身份头重算):**53 PASS→PASS、12 FAIL→FAIL、0 翻转**——当前语料无 verdict 级后果,机制风险如实记录,不夸大。
- B-03 裁决优先级(真实 PASS 文件副本攻击):剥 1 个 section_ref → **PENDING_REVIEW**(不静默 PASS,C14 命中);再注入 C1 issue → **FAIL 压过 PENDING**。优先级正确。
- B-04(设计事实,非缺陷):process_file 对 validation_issues 非空仍写产物(记入 annotation_meta),QC 是唯一闸门——**下游 resolver 契约必须消费 QC verdict,不得只看产物存在**;已列入 resolver 契约约束。
- 过程失误如实记录:B-03 首轮选了本就 FAIL 的会考化学做基线(6 条既有 C3)误读为异常,换真实 PASS 文件后复测通过——选样错误,非系统缺陷。

**C 工件可追溯性**:
- C1 切片重编译确定性:每语料抽样(pilot 全 16 + 其余各 3)manifest+源 → compile_slices vs 已提交切片 md **字节级全等,0 不一致**。
- **C-01 🔴 已修**:`data/reslice_pilot_qc.json` 停留在 R25(85784a9),记载三十一中 **PASS/0 issues**,与当前真实裁决 FAIL(C13)矛盾——过期证据工件,任何读该工件的人会得出"pilot 16/16 PASS"的错误结论。已重跑 QC 刷新:**15 PASS / 1 FAIL**,与台账一致。
- C2 BUG-24 快照链(before/after/fix report/66 manifest sha256)R40 已验,本轮不重复。

**D Fresh 环境可复现**:
- D-01 🟢:`git archive HEAD` → 独立目录(确认无 Ocr-markdown)→ `pytest tests` = **89 passed / 17 skipped / 1 xfailed**——corpus 依赖测试独立 skip,无隐藏本地依赖。
- D-02 🟠 记录:10 个脚本仍硬编码 `Path(r"D:\Project\Papers")`(reslice_qc/prereview_check/render_lint/select_batch_c/run_fix_chain/fix_* 等)——BUG-20 只根治了 reslice_pipeline。当前不崩 CI(路径不在 import 期触盘),但换机/换路径即断;列为硬化待办,不冒充已修。
- 操作教训:二进制 `git archive | tar` 过 PowerShell 管道损坏(bad header checksum),改走临时 .tar 文件;mutation 恢复误用 `git checkout` 把未提交修复一并还原,当场重施——**变异恢复必须用补丁式还原,checkout 只可用于已提交状态**。

**Gate 结论**:发现并修复 1 个生产路径缺陷(BUG-26)+ 1 个过期证据工件(C-01 已刷新)+ 1 个硬化待办(D-02);A/B(优先级)/C(确定性)/D 主体通过。readiness 三列表更新依据:`data/r41_gate_ac_report.json`、`data/r41_gate_b02_report.json`。套件 108 passed + 1 xfailed。

---

## R42(2026-09-13):对 R41 报告的对抗性审查("audit of audit" 第二轮)

原则:R41 每个结论独立重测;优先攻击我自己的薄弱面(B-02 是模拟非真实 check、A1 只查存在性、A3 漏两语料、fresh checkout 跑的旧 HEAD)。

| # | 被攻击的 R41 结论 | 裁决 | 真实测试 |
|---|---|---|---|
| V1 | 套件 108 passed + 1 xfailed | 🟢 | 重跑复现(17.8s) |
| V2 | CI 绿(head 9240a1c) | 🟢 | `gh run view 34703603339`:conclusion=success,headSha 精确匹配 |
| V3 | BUG-26 mutation 敏感 | 🟢 重做(补丁式恢复) | 退回 `{"units":...}` → 恰好 2 条新测试 FAIL(邻近 9 条不受影响=耦合不过宽)→ 备份恢复 → 11 passed。上次误用 git checkout 还原未提交修复,本次备份-还原闭环 |
| V4 | B-02 "0 裁决翻转"(R41 是**模拟**) | 🟢 真实 check 证实 | 65 份生产 v2 落盘剥离身份头副本,跑真实 `qc.check()`:53 PASS→PASS、12 FAIL→FAIL、**0 翻转**,与模拟一致(`data/r42_v4_real_downgrade.json`) |
| V5 | 修复在 CLI 真实入口有效 | 🟢 | subprocess 跑 `reslice_pipeline.py --recompile --out`:v2 身份头/units/切片字节全保持;**幂等**(两轮一致);v1 文件(三十一中)不崩、保持 v1 |
| V6 | 重编译确定性(R41 仅抽样) | 🟢 升级为穷举 | 全 80 份 manifest+源重编译 vs 已提交切片:**0 不一致** |
| V7 | QC 与已提交证据零漂移(R41 漏 test-v21/audit-a5) | 🟢 穷举补齐 | 80 份全跑:裁决分布 pilot 15/1、batch-C 38/12、stress10 5/4、test-v21 1/2、audit-a5 2/0;与三份已提交证据**0 漂移**。**披露补全**:R41 未列 stress10 4 FAIL / test-v21 2 FAIL(测试语料,非交付范围;R41 无假声明但披露不全,现入账) |
| V8 | A1 schema "零缺陷"(R41 只查存在性) | 🔴 **值域审计抓到 BUG-27** | 契约词表对账:三十五中英语 Q86-essay `basis='explicit'` 游离于声明词表;溯源为 PLAN 合法 mode,契约三处不一致(5值/3值 running_max/实际6值)→ **文档勘误完成**,域校验缺失列为决策点(不破冻结擅自加规则)。A1 存在性本身独立复算:80 份/0 缺陷 🟢 |
| V9 | C-01 刷新后工件可信 | 🟢 | 重跑 QC → 与已提交 json **sha256 逐字节一致**(确定性可复现);R25 出处 `85784a9` git 历史复验 |
| V10 | fresh checkout 全绿(R41 跑的是旧 HEAD) | 🟢 新 HEAD 重验 | `git archive HEAD`(9240a1c,无 Ocr-markdown):**91 passed / 17 skipped / 1 xfailed**(91=89+2 新测试,算术自洽);17 个 skip **全部**带 corpus 缺席理由(-rs 穷举:5+1+10+1) |
| V11 | D-02 "10 个脚本硬编码" | 🔴 **计数不准** | 独立重数:**9 个文件(10 处命中**,phase2_adversarial_probe 占 2 处)。status.md 已勘误;log.md 按 append-only 以本条勘误为准 |
| V12 | B-02 报告工件与结论一致 | 🟢 | `r41_gate_b02_report.json` 复算:rows=65、tally 精确吻合声明 |
| V13 | B-03 优先级正确(R41 单文件) | 🟢 泛化 | 换 pilot 石景山物理重放:剥 section_ref → PENDING_REVIEW(C14);叠加 C1 issue → FAIL |
| 补 | BUG-26 修复有无同类盲区(其他顶层键被 recompile 丢?) | 🟢 | 80 份顶层键型穷举:仅 v1 四键/v2 六键两种形态,write_outputs 输出与之平价——无隐藏键丢失面 |
| 补 | B-04 "issues 非空仍写产物" | 🟡 证据类型=代码位置(write_outputs 无条件调用),非运行时测试(LLM 路径不可离线触发)——如实标注,不冒充运行证据 |

**发现汇总**:2 个新问题——**BUG-27**(契约词表不一致+explicit 游离,文档层,已勘误)与 **D-02 计数不准**(9 非 10,已勘误);1 项披露补全(stress10/test-v21 裁决入账);R41 其余全部结论经独立重测维持,其中 V4/V6/V7/V10 由抽样/模拟/旧基线**升级为穷举/真实 check/新 HEAD**。套件 108 passed + 1 xfailed。

---

## R43(2026-09-13):R42 用户裁定落盘 + 审查循环正式收口 + Gate 攻击序调整与首攻面立项

**用户裁定 R42:🟢 ACCEPTED(明确验收,无需再对 R41 做重复性审查)**。裁定要点原样入库:

1. **总体**:R41 实质结论 🟢 维持;"R41 报告完全无错误" ❌ 明确不成立;BUG-26 🟢 CLOSED(mutation-sensitive + mutation locality evidence:"恰好 2 条新测试 FAIL + 邻近 9 条保持"给出耦合边界证据);BUG-27 🟢 CLOSED(契约文档问题,未为让测试绿而改数据 = 正确处理);D-02 🟢 CLOSED WITH ERRATUM(正式口径 **9 个文件 / 10 个引用点**,文件数与引用位置数不得混为一谈)。
2. **证据升级被点名为 R42 最大价值**:模拟→真实 `qc.check()`(这才真正证明"BUG-26 修复没有改变已有 QC 判定结果")、抽样→穷举(结论升级为 **VERIFIED — defined scope exhaustive**,口径必须保持 "defined scope = 80 份当前目标工件",**不得外推为"对任意未来输入均确定性"**)、旧 HEAD→新 HEAD(fresh checkout 精确表述 = "当前 HEAD 在缺失相应 corpus 时 fresh checkout 可重复且全部 skip 均有明确 corpus 缺失原因",**不得简化为"全部测试通过"**,因 17 个是 skipped)、字段存在性→值域审计。
3. **审查递归终止(R42 最重要节点)**:R37→R42 六轮已过,"再攻击上一轮报告有没有说错"易进入审查递归——**现在转换攻击对象:不要再审查审查报告,开始审查系统**。R42 定义为 Identity/SectionLocator/Recompile/QC Stability 的**最后一次审查闭环**,除非出现新反证,不再做 R43/R44 式报告审查。
4. **系统现状分账**:Deterministic Core(Identity v2 + SectionLocator + BUG-24/25 + migration + QC/recompile stability)🟢 已非常接近冻结;Real-world Input(真实 OCR/LLM 行为)🟡 仍是主要未知区域;System Readiness 🟡 正式启动。
5. **Gate 攻击序调整(用户排序,非按我列出的顺序)**:**第一优先级 = 真实 OCR + 真实 LLM → annotation → Resolver → Compiler → Gate 的端到端生产链验证**——当前大量证据证明的是 deterministic post-processing,而生产入口是 OCR + LLM 语义批注 + 真实源噪声,前半段真实行为证据明显弱于后半段;但**不能一上来大规模跑**,第一轮不追求数量,先建 **Production Adversarial Corpus**(13 类:原生文本 PDF/扫描 OCR PDF/DOCX/图像/数学 LaTeX/化学图题/答案解析混排/跨页题/多 section 同号/题图分离/OCR 行融合/OCR 错号/composite 复杂题),每样本记录 source→OCR→annotation→resolver→compiler→gate→final disposition **全 stage 轨迹,不只看终局 PASS/FAIL**。**第二优先级 = BUG-11/14/15 数据卫生**(注意:历史 BUG 不得自动视为当前 BUG,正确做法 = 历史 BUG → 构造当前版本针对性 detector → 跑完整目标 corpus → PASS/FAIL/PENDING_REVIEW)。**第三优先级 = D-02 硬编码根治**(定性为工程卫生/可维护性,不是当前最大系统正确性风险;最终目标是 environment portability invariant,覆盖面含路径/配置/模型/provider/token/临时目录/输出目录/日志/fixture,不是一次 grep)。**第四 = 全链路失败状态传播**。
6. **三十一中化学 keep**:不插入 System Readiness 主线——它是 specific semantic adjudication,System Readiness 是 system-wide operational correctness;独立裁决、并行处理,除非最终暴露通用 identity/section 规则缺陷,否则不得作为整体 readiness 前置条件。
7. **basis 值域**:正式登记为 **DESIGN DECISION / CONTRACT ENFORCEMENT CANDIDATE**(非 BUG-28);决策矩阵:closed-set=是 / 需要机器校验=是 / 现在直接改=**否** / 立项=是 / 重定义 Identity 语义=不需要 / 新增自动 PASS/FAIL 逻辑=不应该 / migration 视非法历史值情况决定。**批准进入下一阶段 Contract Enforcement Decision,但不允许在当前 Identity 冻结基线中偷偷加入**;若 Frozen Spec 未明确封闭域,先修 Spec 再决定代码行为;若批准实施,测试最低覆盖 valid/invalid/missing/null/empty/case/whitespace/unknown-future,尤其 `"explicit "`/`"Explicit"`/`"EXPLICIT"` 是否允许必须由契约明确规定。决策矩阵原文已登记 `question_identity_design.md` §10.7。

**本轮执行(纯记账 + 立项,零生产代码变更)**:

1. `question_identity_design.md` 新增 §10.7:审查闭环收口 + basis 值域 CONTRACT ENFORCEMENT CANDIDATE 完整决策矩阵;
2. `status.md`:一句话现状/当前阶段改写为 Gate 攻击序四条;basis 候选行 + Gate 首攻面行入风险表;R42 行改 ACCEPTED 并按用户限定口径补精确表述(defined scope / fresh checkout 措辞);
3. 事实盘点(为对抗语料选样提供依据,零 LLM 成本):`original` 树源格式 = **PDF 38,893 / DOCX 30,254 / DOC 207 / PPTX 164**(独立 JPG/PNG 仅各 1,"图像输入"类须以扫描 PDF 承载);OCR 生产队列 `maintainess\PDF` = **12,707 份纯 PDF**(守护进程 PaddleOCR-VL-1.6,aistudio API,日额度 20,000 页;`data/ocr_page_usage.json` 停留在 2026-09-10 used 6639,队列守护由用户手动启动);Ocr-markdown 学科树现存 高一 884/高三 798/高二 594/高考真题 599/未分类 145/auto-annotated-v6 1434 等;
4. Gate 首攻面设计稿落盘 `production_adversarial_corpus_design.md`(13 类覆盖、选样纪律、全 stage 轨迹 schema、成本估算);**启动须用户批准样本量与成本预算**。

**结果**:R42 裁定全部入库,"审查审查"阶段正式终止;下一工作轮 = Gate 首攻面(Production Adversarial Corpus),待用户批准预算。套件状态不变(108 passed + 1 xfailed,本轮零代码变更)。

---

## R44(2026-09-13):Gate 首攻面第一轮执行——PAC 22 份真实 OCR+LLM 全链跑通 + 2 个新缺陷

**输入**:用户预算裁定(目标 26 份每类 2;OCR 直调 API 单跑;本轮缩范围只跑 PDF 类 → 11 类 × 2 = 22 份,C3 DOCX/C4 图像 BLOCKED 如实声明)。

### 选样(R43 尾完成,过程发现先入账)

22 份全部真实源 + hazard 证据(禁合成),`data/pac_selection.json` 指纹留档(sha256+页数+文本层)。选样测量抓到两个事实:① **"扫描卷"不能靠推定**——首批按印象挑的 2 份"扫描卷"文本层实测均为 native_text,换为队列明示"图片版"且 md 基线在位的真扫描件(实测 scanned);② 全语料融合形态扫描找到第二例融合实证(一六一中数学 L137 三重融合)。**重要事实:22 份中 20 份 hazard 源 PDF 是原生文本层**——行融合/错号等 OCR 缺陷主要来自 PaddleOCR 对数字排版 PDF 的版面解析,不是扫描噪声。

### 全 stage 轨迹(逐样本 `data/pac_track_round1.json`,设计稿 §4 schema 落地)

| stage | 结果 | 证据 |
|---|---|---|
| source | 22/22 指纹化 | `pac_selection.json`(293 页) |
| OCR | **22/22 OK,293 页入账**(与实测页数逐份相等;全局额度 293/20000) | `pac_track_ocr.json` |
| annotation | **22/22 成功,57.7 万 tokens**(prompt 33.7万+completion 24.1万,低于 82 万预估),18/22 零校验问题 | `reslice_reslice-pac-annotated_result.json` |
| manifest | 22/22;**pipeline 原生输出是 v1**,经生产同款确定性回填 → 22/22 v2(sections 5–26,0 fail/0 review) | `pac_identity_backfill_report.json` |
| QC(v2 后) | **18 PASS / 4 FAIL,0 PENDING_REVIEW**;4 FAIL 恰为带 validation_issues 的文件(无静默 PASS,B 面证据) | `pac_qc_v2.json` |
| identity | 22/22 v2,check_identity 0 fail | 回填报告 + 盘点探针 |
| artifact | 22×3 工件在位(annotated/manifest/slices) | 目录盘点 66 文件 |
| resolver/compiler/gate/admission | **NOT_BUILT**(如实,不伪造端到端) | — |

### OCR 漂移量化(D6 首批真实证据,`data/pac_ocr_drift.json`)

- **字节一致 0/22**——同源 PDF 同模型(PaddleOCR-VL-1.6)重跑,产物不字节确定;相似度 0.955–1.000,行数几乎全同(仅 c11-01 560→561);
- **hazard 形态可复现**:转义点序号头(BUG-25 家族)在 c05-01 2→2、c06-01 1→1、c12-01 2→2、c12-02 2→2 逐行复现(c12 两份与台账行号精确一致);
- **随机结构漂移实证**:c06-02 历史跑 12 处答案行为普通行、本次跑升为 `###` 标题(c10-02 6 处同理;同位置同内容,并非全升)——**OCR 对答案行的标题化是随机的**;下游 QC 对该漂移 0 issue(鲁棒);注意基线可能被既有 fix 链碰过,漂移数字口径 = "历史产物 vs 今日直跑"。

### 危害面复核(深度 11 份 / 抽验 11 份,逐份记入轨迹 human_review)

- **c12-01/02(BUG-25 台账卷)**:转义点行复现且 **SectionLocator 0 误升**——BUG-25 修复在全新数据上成立;
- **c11-02(融合卷)**:L137 三重融合被 SectionLocator 如实收为 section start(标题文本污染,ACCEPTED OCR LIMITATION 家族),下游 C7/C9 咬住 → **FAIL 非静默**;
- **c09-01(BUG-22 卷)**:prompt v2.3 + identity v2 下 printed(1-9)与 canonical(答案键 26-34)分离正确,0 identity fail;6 题源面答案缺失 → QC 如实 FAIL;
- **c11-01(三十一中化学)**:L324 注记分节标题在新鲜 OCR 逐字复现(偏移 1 行),BUG-24 修复后被正确建模为分节;keep 三方裁决仍独立挂起,不因本链路结果关闭;
- 4 份 QC FAIL 分诊:c07-01(BUG-17 家族 8 题 C3+C5+C11)、c09-01(6×C3 源面答案缺失)、c09-02(C9 结构行混入)、c11-02(C7/C9 融合后果)——全部是"如实暴露",无一静默转 PASS。

### 新缺陷(账目面,均已在修复后真实验证)

- **BUG-28 🟢 FIXED**:batch summary 硬编码写 `data/reslice_batch_c_summary.json`,--out 独立批量跑会静默冲掉生产 batch-C 证据工件(C-01 家族);修复=`derive_summary_path` 派生;回归 3 用例含集成级(main 真跑),**变异验证**(调用点回退→恰 1 条集成测试 FAIL→还原 3 passed);
- **BUG-29 🟢 FIXED**:BUG-28 家族第二例——`phase2_identity_backfill.py` 回填报告硬编码;修复=`--report` 选项;真实运行验证生产报告 sha256 前后不变;
- **Gate 发现(非缺陷,契约事实)**:pipeline 原生输出 v1,v2 依赖回填步骤——fresh 产物在回填前不是 v2,下游若直接消费 pipeline 输出违反 "resolver 只消费 v2" 契约;PAC 按生产同款流程回填后达成 v2。列入 resolver 契约约束与 rollout 流程清单。

### 结果

PAC 第一轮 22 份全链(真实 OCR + 真实 LLM)跑通,轨迹工件完整,FAIL 全部可解释且非静默;OCR 服务链从"零测试"升级为 22 份真实轨迹 + 漂移量化;抓 2 个账目覆盖缺陷(均修复+验证)。套件 **111 passed + 1 xfailed**(BUG-28 回归 +3)。残留:① 人工复核深度不均(hazard 卷深度、PASS 卷抽验,已如实标注,逐题全查留待用户抽查);② C3/C4 类 BLOCKED;③ 第二轮扩样(每类 2 份=26)待第一轮分诊裁定后决定。

### R44 补记(同日):CI 三连红排查与修复 + BUG-16 家族清尾

- **CI 三连 failure 实锤排查**:R44 的 BUG-28 提交起 CI 连红三次。日志定位:**我自己写的测试不可移植**——`test_summary_path_out_isolated` 用 `Path(r"D:\x\reslice-pac")`,Windows 本地 `.name` 取到目录名,CI(Linux)反斜杠不是分隔符 → `.name` 返回整串 → FAIL。生产代码 `derive_summary_path` 本身无缺陷(生产在 Windows 跑)。修复:测试改平台无关构造(`Path("x")/"reslice-pac"`)。**教训**:R36"本地过≠CI 过"先例在我这轮复现,写测试用 Windows 字面路径语法 = 埋 CI 炸弹;新测试须默认平台无关。
- **BUG-16 家族清尾**:CI 修复过程中 git warning 暴露 `flush_results`/summary 写盘漏 `newline=""`(账目 json 被翻 CRLF)——已修 + 已提交的 PAC result json 归一纯 LF(CRLF count=0)。
- **CI 复绿**:`gh run view 34723215654`(43e24a2)= success。套件 111 passed + 1 xfailed 维持。

---

## R45(2026-09-13):PAC 第一轮完成标准③补齐——22/22 深度语义复核 + 语义探针全量分诊

**输入**:Goal 轮 2;R44 残留①(10 份 PASS 卷仅抽验级)。本轮全部升级为深度复核,完成标准①②③④⑤齐。

### 语义探针(R30 校准的 P13/P14/P15)全量跑 + 78 报警逐条分诊

`scripts/semantic_probe.py --dir reslice-pac-annotated` → **530 单元 / 78 报警 / 涉及 11 文件**(`data/pac_semantic_probe.json`)。逐条分诊结论:**0 个新缺陷**——
- **76 处 = 探针盲区**(探针系 v2 时代前设计):括号答案键 `(21)(22)` 连写行 ×7、紧凑答案行 `9.1 10.-1` 与答案即解析格式 ×8、子问编号 `1)2)3)` ×8、材料内编号 `1.-4.` ×4、写作提示/评分细则内部编号 ×17、**printed/canonical 错位 ×21**(c09-01/c11-01——探针拿 canonical 对比 printed,恰是 BUG-22 修复后 v2 的正确行为,**反证 v2 生效**);
- **2 处 = 源卷版本噪音(实查坐实)**:c13-02 Q20(二选一作文)尾部解析两条 P15 报警——题干区写"六、本大题共**1**小题"(Q20 顺位编号),解析区自称"共**2**小题"且编号 **10/11**:**源卷题干区与答案区是不同版本**;LLM 把唯一存在的作文解析绑定给 Q20 语义正确,printed=None 未伪造。**resolver 契约须知:answer 区编号可与题干区不一致**(与 R19 答案表键位语义同族)。

### 10 份原抽验卷深度复核证据升级

- **题号覆盖完整性**:10/10 完美(并集=1..max,**0 缺号 0 重号**;c01-01 30/30、c08-01 44/44(9 单元整块化)、c13-01 34/34(19 单元)等);
- **新发现(非缺陷,回收边界)**:c01-02 printed **零回收(28/28 unverified)**——根因实查:源卷题号为 `(1)(2)(3)` 括号式,`printed_from_stem` 解析正则只认 `NN.` 前缀。printed_provenance=unknown 如实未伪造;**列入硬化候选**(扩解析正则属新能力,待用户决策,不擅改);
- 复核记录全部更新为"深度"(`data/pac_track_round1.json` 重新生成,22/22 深度)。

### 结果

完成标准:① 22 份选样留档 ✅;② 全 stage 轨迹(NOT_BUILT 如实)✅;③ **22/22 深度语义复核**(QC+identity+语义探针分诊+覆盖完整性+危害面实查)✅;④ 分诊报告(18 PASS/4 FAIL 全可解释)+ BUG-28/29 入册 ✅;⑤ 台账更新+CI 绿 ✅。套件 111 passed + 1 xfailed。

---

## R46(2026-09-13):PAC 第一轮结果对抗性审查——逐结论真实测试复证

**输入**:用户指令"针对 PAC 第一轮的结果开启一轮严格的对抗性审查,每个结论必须有真实测试作为证据;不降低标准、不自我合理化、不强行解释、不推测"。审查对象 = R44/R45 的全部对外结论。

### (a) track 数字独立重算:`scripts/pac_audit_recompute.py` → `data/pac_audit_recompute.json`

不信任 track 任何字段,从原始工件(源 PDF/OCR md/annotated 产物/QC/回填/LLM result)逐项重算:**550 项比对,0 不一致,0 findings**。全局量全部复证:页数实测=计费=**293**;tokens 重算=**577,225**(336,640+240,585);单元和=**530**=探针 n_units;QC 重数=**18/4**;探针报警重数=**78**=header 分项和。附加不变量 22/22 全过:I2 区间零越界、I3 section_ref 零悬空、I4 C8 独立复算逐行相等、I1 canonical 零重复、I6 覆盖=1..max 零缺重(manifest∩LLM result 双侧互证)、I7 model 全部 mimo-x-pro-preview。**R45"覆盖 10/10"升级为机器复证的 22/22。**

### (b) QC 对抗变异:`scripts/pac_audit_qc_mutation.py` → `data/pac_audit_qc_mutation.json`

真实产物整目录拷贝(原件零触碰),**17 条变异 0 失手**:控制组(零变异拷贝)逐字复现 pac_qc_v2 → 拷贝保真成立;C1/C2/C3/C5/C6/C7/C8/C9/C10/C11/C12/C13(同节+跨节双非keep)/C14/C4 各注入一个已知缺陷,**期望检查码全部命中且 verdict 正确降级**(C14 → PENDING_REVIEW 而非静默)。"18 PASS"背后的 QC 不存在已知结构性盲区(在这些检查族的设计语义内)。

### (c) 语义探针攻击:`scripts/pac_audit_probe.py` → `data/pac_audit_probe.json`

- **灵敏度双向验证 8 条 0 失手**:注入 P14(stem 吞下题题号行)/P15(answer 指别题题号答案行)/P13(answer 指纯散文行)必报;阴性对照(共享答案表行、区间连写 `1-5 ACDBA`、解答步骤编号 `1、目的基因…`)必不报。
- **78 报警独立再分诊**(不沿用 R45 口头分类):规则分类 54(R1 printed/canonical 错位×21、R2 括号答案键×5、R3 子问编号×11、R4 写作提示/评分细则×5、R5 答案内容在但形态正则未覆盖×12)+ **残差 24 条逐条人工读原文裁决**——全部为探针盲区或已记录噪音(`略`式答案×2、题干内材料编号×4、紧凑答案行×6+1、作文提示/评分细则编号×5、printed=None 的 printed/canonical 家族×2、散文式解析答案×1、c13-02 解析材料编号×1、**新盲区子类:答案键字母超 A-D(`35-39 DEFGB`,ANS 字母表过窄)×1**)。**"0 新缺陷"结论经独立再分诊成立。**
- **如实更正**:R45 的分项计数(7+8+8+4+17+21=65,+2 噪音=67)与总数 78 对不上账——结论正确但分项算术不成立,以本次机器分类为准。

### (d) BUG-28/29 修复独立验证

- BUG-28:`test_batch_summary_isolation` 3/3 绿(套件内);batch-C summary 未被 PAC 跑动过。
- BUG-29:真实 dry-run(`--out reslice-pac-annotated --report <临时>`)→ 默认报告 sha256 前后一致、临时报告 22 份 0 fail/0 review。**发现覆盖缺口:BUG-29 只有人工实测、无 CI 回归** → 新增 `tests/test_backfill_report_isolation.py` 钉死。
- 变异自证伪:BUG-29 复发变异 → 恰 1 测试红;C7 失敏变异 → 恰 test_c7 红;P14 失敏变异 → 恰 P14/P15 两测试红;恢复后全绿。

### (e)(f)(g) 选样指纹 / 回填 / 文本层

- `pac_select.py --check`:**22/22 指纹一致**(源 PDF 无漂移)。
- 回填 dry-run:22 份 0 fail 0 review,与 track 完全一致。
- QC 确定性重跑:与 pac_qc_v2 唯一差异 = `file` 字段路径写法(相对 vs 绝对),verdict/issues 全等。
- 文本层独立 fitz 重测(逐页字符数入档):**22/22 与 track/selection 一致**,20 native_text + 2 scanned 复证。

### hazard 形态逐条复证(新鲜 OCR 产物上)

c12-01 转义点行 **L266/L274 逐行复现**(与台账锚点同位)、c12-02 **L445/L461 复现**,【答案】【解析】转义点行 **0 误升分节** = BUG-25 修复成立;c06-02 答案行标题化 fresh-baseline **差恰 12**、c10-02 **差恰 6**;c11-01 融合行 baseline L324 与 fresh L325 **逐字相等**;c11-02 L137 三重融合行在。drift json 内部一致(0/22 字节一致,相似度 0.9549–1.0000)。**一处定性澄清**:c05-01 两条转义点行(`17\.`/`19\.`)确被升为分节,但其非转义孪生(`18.`/`20.`)同样被 SECTION_RE 收为分节——是解答题标题的定位器设计行为,非 BUG-25 类答案块误升;"0 误升"仅在答案块语义下成立,特此限定措辞。

### 审查发现汇总(无新生生产缺陷;3 项台账/覆盖问题 + 1 项卫生问题,全部处置)

1. **R45 分项计数对不上账**(65+2≠78)→ 本轮回填机器分类,如实更正;
2. **c09-01 printed 声明措辞过宽**:实测 34 单元中 23 recovered(Q27→printed 2、Q32→7 等分离正确),Q26/Q30 等 11 个 printed=None(题干 `1\.` 转义点/无印刷号行,回收正则边界同 c01-02 家族)——"输出 printed(1-9)"应限定为"已回收子集";
3. **BUG-29 无 CI 回归** → 新增测试 + 变异自证伪;
4. **未跟踪证据工件**:`data/pac_qc.json`(回填前 v1 QC)、`data/reslice_reslice-pac-annotated_summary.json` 补入版本库。

### 资产沉淀

新增 `scripts/pac_audit_{recompute,qc_mutation,probe}.py`(语料依赖,本地跑)+ `tests/test_qc_mutation_sensitivity.py`(12)、`tests/test_probe_sensitivity.py`(6)、`tests/test_backfill_report_isolation.py`(1)——**CI 合成语料钉住 QC 14 检查族灵敏度、探针双向契约、BUG-29 隔离,共 +19 测试**。套件 **130 passed + 1 xfailed**。

### 残留(如实)

- 探针对"答案键字母超 A-D""散文式解析答案""题干内材料编号"三类为已证实盲区(测量仪语义,非缺陷);探针仍未进 QC(维持"报警≠缺陷"纪律);
- c12-02 Q24 answer 区为【解析】散文(答案内容在解析内)——绑定语义正确但"答案/解析分离"质量项留待 resolver 阶段裁定;
- 审查范围限定 PAC 22 份与本轮结论;历史 66 份生产产物不在本次攻击面。

### R46 补记:变异自审的爆炸半径

M1(BUG-29 复发变异)期间,被变异的代码把**真实默认报告** `data/phase2_identity_backfill_report.json` 冲掉(777 行→6 行)——变异测试本身测试失败(符合预期),但污染已发生;`git checkout` 恢复后 sha256 核验与 HEAD 一致,工作树净。**教训入册:对"写死工件路径"类缺陷做复发变异,变异体会直接攻击真实工件——今后此类变异必须先备份目标工件或在副本上做**(BUG-28/29 家族的变异测试同理)。

---

## R47(2026-09-13):用户对 R31–R46 审查链的架构级复核裁定落盘(纯记账轮,零生产代码变更)

**输入**:用户基于 R31–R46 审查记录的架构级复核(声明为证据链层复核,非独立代码重扫)。裁定与建议原样入库:

### 裁定要点

1. **R46 = 整个审查链中证据等级最高的一轮**;审查方法已从"修复→写测试→证明修复有效"升级为"假设结论可能错误→构造攻击→用独立测量推翻或保留"。**R46 作为 Identity + PAC 阶段结束标志;不建议继续无限增强 preprocessing 规则**。
2. **组件状态表(用户口径)**:Question Identity v2 🟢 基本冻结 / SectionLocator 🟢 / C13-C14 语义保护 🟢 / migration-backfill 🟢 / PAC 审计框架 🟢 首轮验证通过 / OCR-LLM 真实性验证 🟡 尚未进入 / Resolver 消费 identity 🟡 下一阶段风险 / Resolver→IR 🔴 未审。
3. **BUG-29 评级 🟡 Medium**(test isolation failure,非业务错误;但若发生在生产 migration 会破坏审计链)。**建议升级为统一 ArtifactWriter Contract**:所有脚本禁止直接 `open("data/foo.json","w")`,必须经 writer 控制 output root / overwrite policy / atomic write / backup——否则 resolver/gate 会重复出现同族缺陷。
4. **semantic overclaim 纪律(R46 c09-01 事件的规则化)**:报告禁止「全部/完整/零缺失/成功恢复」类措辞,除非同时给出 **denominator / numerator / proof method**(正确范式:"printed number recovered for 23/34 units; remaining 11 units preserve unknown provenance")。**数据恢复成功 ≠ 数据完整恢复**。
5. **最大剩余风险转移判定**:Identity 层经 BUG-22~29 连续攻击后已稳,剩余最大风险在 `Evidence → Resolver → Question IR` 边界。三个必须保持的边界:**Resolver 只回答"能不能定位"(structural only,禁止 `looks_like_solution` 类语义判断)、Gate 只证明约束、Admission 承接人类不确定性**;PENDING_REVIEW 通道必须保持,**不得为提高 PASS 比例扩展自动规则**(Evidence Soundness 局限:机器只能证明 evidence exists + shape valid,不能证明 evidence means what we think)。
6. **下一阶段优先级(用户排序)**:① **Gate + Resolver Boundary**(验证 identity v2 → resolver consumer → IR correctness;最优先)→ ② BUG-11/14/15 数据卫生(结构正确但内容错误,直接影响 Question IR)→ ③ basis 值域(**schema validation only**:invalid enum → schema violation,**不得** basis invalid → FAIL,否则改变历史数据裁决)→ ④ printed 正则硬化(**必须保持 unknown > guessed**,不得为 recovered 数量牺牲 provenance)。

### 我方事实核对(真实测试,非转抄)

- **resolver/compiler/gate/admission 在仓库内确认 NOT_BUILT**:`data/pac_track_round1.json` 全 stage 轨迹如实记录;"resolver 只消费 v2"契约已多处固化(`tests/test_recompile_identity.py`、`reslice_qc.py` L210 共用校验、`phase3_pilot_v1_migration.py`);resolver 实体代码不存在(grep 确认)。**推论:用户建议的"下一轮转向 Resolver 消费 v2 的对抗性审查"在开审前必须先定义审查对象**——当前可审的是契约/接口设计与消费约束(pac_track 中已列:消费 v2 仅经回填、消费 QC verdict 而非产物存在、answer 区编号可与题干区不一致等),实现级对抗审查须待 resolver 实现存在。此为决策点上报,不擅选路线。
- **一处口径澄清(不改变裁定)**:用户组件表"OCR/LLM 真实性验证 🟡 尚未进入"——PAC 第一轮已有 22 份真实 OCR+LLM 链证据(293 页 OCR 全轨迹、57.7 万 tokens、漂移量化 0/22 字节一致、R46 独立重算复证);"尚未进入"的部分准确说是 **Resolver/IR 消费层行为与 D-02 环境可移植性**,以及扩样面(C3 DOCX/C4 图像 BLOCKED)。台账以本口径为准。

### 落盘动作(本轮执行)

1. `review_protocol.md` 新增**规则 4(恢复/成功类声明三要素)**:出处 = R46 用户裁定 + c09-01 printed 23/34 事件;
2. `question_identity_design.md` §10.7 追加 R47 修订:basis 值域实施方向收窄为 **schema validation only(invalid → schema violation,不进 FAIL 语义)**,仍待正式批准;
3. ArtifactWriter Contract 登记为 **治理候选**,并入 D-02 / BUG-21/28/29 家族同一扫描面(实施待批准);
4. `status.md` 同步:阶段标记切换(PAC 第一轮含 R46 审查结案;下一攻击目标 = Resolver 消费边界)。

**结果**:R31–R46 审查链获用户架构级验收;preprocessing Identity Layer 判为 Frozen Candidate;下一轮工作对象待用户在「Resolver 契约纸面审 / Resolver 实现后审 / 先 BUG-11/14/15」间裁定。本轮零生产代码变更,套件状态不变(130 passed + 1 xfailed)。

---

## R48(2026-09-13):Resolver 消费契约纸面冻结 + 生产侧前置条件实测(用户裁定下一轮对象)

**输入**:R47 决策点用户裁定——下一轮 = **Resolver 契约纸面审**(先冻结消费契约并预置对抗语料,零 resolver 实现;实现存在后再开实现级对抗审查)。

### 交付

1. **`resolver_contract_design.md` v0.1**:消费契约逐条挂证据出处——三边界(R47:Resolver structural only / Gate 只证明约束 / Admission 承接人类不确定性);输入契约 C-IN-1~8(只消费 v2、消费 QC verdict 而非产物存在、三态传播、身份只读不重推断、basis 只读、answer 区编号可不一致、答案表 td 按题号取、行号锚定不重解析标题);失败传播 C-FAIL-1~3(四态不得静默转 PASS、人工放行走 Admission、异常 fail-closed 不降级重算);输出工件 C-OUT-1~3(ArtifactWriter 候选首批条款 + 规则 4);已知消费风险登记(printed unknown 402/1484=27.1%、源面答案缺失、答案在解析内、OCR 融合、PENDING_REVIEW 是设计产物);验收标准 R-ACC-1~8(实现审查逐条测,含变异义务);附录 A 对抗语料登记(PAC 22 + batch-C 50 + pilot 16 + R30 校准卷,ready-to-fire)。
2. **`scripts/resolver_contract_preflight.py`**:生产侧前置条件预检 pc1–pc10,全部复用生产共用实现(`question_identity.check_identity` / `reslice_qc.check`),不新增 QC 规则、不重新发明校验。
3. **实测结果(真实语料,`data/resolver_contract_preflight.json`)**:88 份(batch-C 50 + pilot 16 + PAC 22)逐份检查——**87/88 零 findings**;唯一 finding = pc1×1 三十一中化学 v1(known,keep 挂起件,恰证明拒收路径有真实命中);pc2–pc10 全 0;QC verdict 分布与台账算术闭合(PASS 71 = 38+15+18;FAIL 16 = 12+4)。**限定口径:producer-side 前置条件成立,不构成 resolver 实现正确性的任何证明。**
4. **CI 契约测试 +4** `tests/test_resolver_contract_preflight.py`:干净 v2 合成语料 0 findings(且 QC verdict=PASS 可计算)+ 三条变异注入即测试(伪造 printed→pc7 / 非法 basis "Explicit"→pc5 / v1 输入→pc1)——预检区分力由缺陷形态本身证明。

### 边界与残留(如实)

- 本稿是**纸面契约**,全部条款验证状态 = 纸面冻结待实测;唯 §6 生产侧前置为本轮实测;
- resolver 实现存在后,开审纪律同 PAC/R46(独立重算 + 变异 + 穷举,不得抽样冒充全称);R-ACC-4(import 面审计)只能在实现后做;
- 契约本身未经过独立对抗审查轮(用户如需,可对本稿开启"审查审查"——按 R42 收口先例,由用户裁定是否豁免)。

**结果**:Gate 攻击序①的消费侧纸面边界冻结;套件 **134 passed + 1 xfailed**;生产代码零变更(新增 preflight 脚本为审计工具,不进生产链路)。

---

## R49(2026-09-13):对 R47/R48 的对抗性审查——逐结论真实测试复证

**输入**:用户指令"针对 R47 和 R48 开启一轮严格的对抗性审查,每个结论必须有真实测试作为证据;不降低标准、不自我合理化、不强行解释、不推测"。自查先行声明最弱环节:① "87/88 零 findings"由被审脚本自测,无独立重算;② pc2/3/4/6/8/9/10 零变异验证;③ 设计稿数字系转抄;④ 零生产代码变更/CI 声明;⑤ 契约覆盖矩阵完整性。

### (a) 独立重算:`scripts/r48_audit_recompute.py` → `data/r48_audit_recompute.json`

不 import 被审脚本,pc5–pc10 独立重实现,88 份逐份比对:**0 不一致**(每份 pc 集合与 preflight 完全相同)。非空转证明:basis 六值全出现(printed_as_is 1546 / unverified 667 / shift 31 / keep 93 / answer_key 9 / explicit 1)、provenance 三值全出现(source_line 1546 / unknown 667 / migration_report 134)——检查族输入域真实非退化。**设计稿转抄数字全部独立复证**:batch-C unknown **402/1484(27.1% ✓)**、keep **93 ✓**、c09-01 **23/34 ✓**、c01-02 **0/28 ✓**;QC verdict 与三份已提交工件逐文件对账 **88/88 真实命中、0 不一致**(batch-C 50 / pilot 16 / PAC 22)。

- **发现 1(时点口径,已修设计稿)**:R19 答案表声明"14 份 304 单元"在当前工件 batch-C 单独口径 = **15 份/305 单元**(三语料合计 29/554)——R19 时点数字,因 R31/R37 fix 链再生成 manifest 不可逐位复现;设计稿补当前口径,契约条款 C-IN-7 本身不受影响。

### (b) pc 检查族变异攻击:`scripts/r48_audit_pc_mutation.py` → `data/r48_audit_pc_mutation.json`

真实 PAC 产物整目录拷贝(原件 sha 前后不变),**控制组 + 11 条变异 12/12 命中**:控制组逐字复现 0 findings/PASS;pc0–pc10 每族注入一个已知缺陷形态(manifest 缺失/v1 输入/跨节非 keep 重号/keep 无证据/QC 不可计算/basis 大小写漂移/provenance 非法/伪造 printed/section 悬空/span 越界/源缺失),**全部恰好命中对应前缀,0 失手**。

- **发现 3(审查工具自身缺陷,控制组抓获,已修)**:首跑控制组 MISS——staging 把源 md 与产物 md 同名拷贝自我覆盖 + 漏拷 `.annotated.md` 兄弟件(C8 依赖)。**控制组保真检查的价值实证**:若无控制组,11 条"全中"是在被污染的基线上得出的。修复后重跑 12/12。
- **发现 2(设计边界,实读坐实,定性非缺陷)**:keep 证据复核仅在题号 ≥2 持有者时触发(`len(own)<2 continue`)——孤立 keep 无豁免效应故不复核;豁免只在被使用时校验,语义自洽;M3 变异按真实语义重构为"跨节重号 + keep 无证据"后恰中 pc3。

### (c) 台账声明复证

- **零生产代码变更**:R47 diff = 4 md;R48 diff = 6 文件(设计稿/审计脚本/测试/json/log/status)——`reslice_pipeline`/`reslice_qc`/`question_identity` 等生产脚本**零触碰** ✓;
- **CI**:两 run headSha 精确匹配(f97f261 / 10a8a41,均 success)。**发现 4(措辞级,已补)**:台账"套件 130/134 passed"是**本地口径**;CI 口径 = 113 passed+17 skipped / 117 passed+17 skipped(130−17=113、134−17=117 算术自洽),按规则 2 补精确表述;
- **确定性**:preflight 重跑与已提交工件**字节级一致**(sha 相同);
- **NOT_BUILT 复证**:全仓 `*resolver*.py` 仅审计工具与其测试,无 resolver 实现。

### (d) 纸面审:契约覆盖矩阵 + 规则 4 自适用

- **发现 5(真实缺口,已修)**:v0.1 契约 C 条款→R-ACC 映射 4 处缺口(C-IN-5 basis 只读 / C-IN-8 行号锚定 / C-OUT-2 IR 携带 provenance / C-FAIL-1 的 MISSING·STALE 两态)→ 当场补 **R-ACC-9/10/11** 闭合(`resolver_contract_design.md` §7.1);
- 规则 4 自适用扫描:R47/R48 台账声明全部带分子分母或经穷举复证("pc2–pc10 全部 0"域 = 88 份,本轮独立重算成立)。

### 审查发现汇总

**无结论级翻转、无新生生产缺陷**;5 项发现 = 1 时点口径(R19 数字)+ 1 设计边界定性(孤立 keep)+ 1 审查工具 staging 缺陷(控制组抓获)+ 1 CI/本地口径措辞 + 1 契约覆盖矩阵缺口,全部当场修正并复验。套件 **134 passed + 1 xfailed**(本地;CI 117+17 skip)。

---

## R50(2026-09-13):用户 R49 评价与架构级裁定落盘 + 审计治理机制实施(Audit Snapshot Manifest + Input Integrity Gate)

**输入**:用户对 R49 报告的架构级评价与裁定(原样入库要点):

### 用户裁定要点

1. **R49 定性 = PAC 阶段最后一类高价值攻击:攻击审查体系自身的可信度**——验证"之前的绿色结论是不是测试体系自证循环造成的假安全"。独立重算(不 import 被审脚本)被点名为正确审计方式(import 式审计只能证明"两套代码共享同一个错误");pc mutation 12/12 命中排除了"规则存在但永远不会执行"的系统性风险。
2. **最终裁决:PAC + Identity 阶段 🟢 通过冻结;Identity v2 可作为 V3 Resolver 输入协议;不建议继续扩大 preprocessing 规则**。最大风险已从 `文件 → identity` 迁移到 `identity → question model`。
3. **下一轮正式启动:Resolver Consumer Adversarial Audit**——审查目标不是"resolver 能不能跑",而是 **resolver 是否会重新解释已冻结的事实层、重新制造 V2 式隐性错误**(V3 进入业务核心前最后一个高风险边界)。用户指定攻击清单:① section 丢失 ② basis 被重新解释 ③ provenance 丢失 ④ composite material 合并错误 ⑤ single question material 丢失 ⑥ shared material duplication。
4. **优先序(用户排序)**:① Resolver Identity Consumer Audit → ② BUG-11/14/15 数据卫生(结构对但内容错,直接影响教学质量)→ ③ basis schema-only **正式批准**(严格限定:只做 invalid enum detection;**schema violation => REVIEW(PENDING_REVIEW),不得 FAIL**,不得静默 PASS)→ ④ printed 硬化(unknown > wrong certainty:宁可 printed=null,不写猜测值)。
5. **治理指令两条(用户原话级)**:① R19 时点漂移(14/304 vs 15/305)不要只修文档,**建立 Audit Snapshot Manifest**——报告引用 `R19@sha256(xxxx)` 而非动态目录,否则未来 R60 还会再现;② R49 staging 缺陷定性 **Test Oracle Pollution**(测试数据被污染,"全绿"在非原数据上得出),**所有审查工具必须有 Input Integrity Gate**(执行前后输入文件数/hash/manifest 对应关系,`before_sha == after_sha`)。
6. **provenance 必须成为一等公民**:IR provenance 不得只是 metadata,应接近 `EvidenceProvenance(source_version, source_line, extraction_method, confidence_state)` 结构(并入 C-OUT-2 实施基准)。

### 本轮落盘(治理机制实施,审计基建,零生产代码变更)

1. **`scripts/audit_integrity.py`(新)**:`gate_snapshot`/`gate_assert_unchanged`(Input Integrity Gate,漂移即 RuntimeError fail-closed)+ `record`/`verify`/`inputs_from_preflight`(Audit Snapshot Manifest:确定性快照,同一输入集字节级相同、无时间戳;`corpus_sha256` = 全文件 sha 的 sha)。
2. **Gate 接线**:`r48_audit_recompute.py`(输入面 = preflight + 88 份切片/manifest/annotated/源 + 3 份 QC 工件)与 `r48_audit_pc_mutation.py`(原件集 5 类 + preflight)执行前后 sha 对账——R49 staging 自我覆盖类污染今后将直接 fail-closed。**接线后重跑实证**:recompute 输出与已提交工件**字节级一致**(findings=0);mutation 重跑 **12/12 all_ok**,输出唯一差异 = pc10 raw 文本内的随机 staging uuid(benign,已 checkout 恢复已提交版本)。
3. **R50 输入基线冻结**:88 份输入面共 **356 文件**快照 → `data/audit_snapshot_R50_input_baseline.json`,引用口径 **`R50_input_baseline@sha256:795ee1e7663424c1245e651d2139573d3bd2322f06662cc677bc0e7e3bc89beb`**;`verify` 实测 0 drift / 0 missing。Resolver 审查轮输入以此为准,数字声明引用快照摘要(BUG-30 类时点漂移治理)。
4. **CI 契约测试 +8** `tests/test_audit_integrity.py`:gate 放行/变异注入咬住(改写输入→RuntimeError 指出漂移文件)/缺失咬住/record→verify 回路/快照后漂移与缺失检出/record 字节确定性/inputs_from_preflight 完整输入面推导且去重/缺失输入 fail-closed。沙箱约束如实:pytest 内建 tmp_path 不可用(WinError 5),按仓库惯例用 conftest.workdir。
5. **台账同步**:`question_identity_design.md` §10.7 补 R50 批准(basis schema-only 正式批准,限定三条,排期优先序③);`resolver_contract_design.md` 新增**附录 B**(R50 裁决:攻击清单 6 条 / provenance 一等公民方向 / 输入基线引用口径 / Input Integrity Gate 纪律 / printed 硬化方向);`status.md` 阶段切换。

### 边界(如实)

- 本轮零生产代码变更(`scripts/audit_integrity.py` 为审计治理工具,不进生产链路;两个 r48 审计工具为 R49 既有审计资产);
- Audit Snapshot 机制从本轮起生效,历史轮次(R19 等)时点数字不可回溯快照(当时未建机制),台账以"时点口径"注记保留;
- Resolver Consumer Adversarial Audit 的审查对象问题:resolver 实体仍 NOT_BUILT——按用户裁定"下一轮正式启动",该轮的可审对象与实施路径(参考实现 vs 纸面+语料预备)作为下一轮的开审前置,待用户在下一轮指令中明确或按契约附录 A 开审条件执行。

**结果**:用户裁定全部入库;两项治理机制从建议变为带 CI 测试的实现;下一阶段输入基线冻结。套件 **142 passed + 1 xfailed**(本地;CI 口径 125 passed + 17 skipped + 1 xfailed)。

---

## R51(2026-09-13):对 R50 治理轮的对抗性审查(收口)+ 用户裁定:参考 Resolver 先行

**输入**:用户指令"针对 R50 的内容开启一轮严格的对抗性审查,每个结论必须有真实测试作为证据;不降标准、不自我合理化、不强行解释、不推测"。审查中途用户追加裁定:**"先做严格按冻结契约实现的参考 resolver,再基于该实现启动 Resolver Consumer Adversarial Audit(R-ACC-1~11 + 附录 A 语料);不要先纸面审查"**——理由:风险已从"设计是否合理"转移到"契约是否被代码真实执行",必须有可攻击的实现对象。本行为在途 R50 审查的收口(审的正是下一轮要用的治理工具与台账声明),收口后立即开工参考实现。

### 攻击面与裁决(`scripts/r50_audit_governance.py` → `data/r50_audit_governance.json`)

- **A1 快照独立重算 🟢**:不 import 被审模块,独立重实现输入面推导 + sha256——**356/356 文件集零对称差、逐文件 sha 0 不一致、corpus_sha256 摘要一致**(795ee1e7…beb);356 个 resolved path 互异(无同文件重复计入);ROOT 外文件 0。
- **A2 record 字节确定性 🟢(首跑假阴性,审计工具自身缺陷,如实入册)**:真实语料重跑 record 与已提交快照**字节级全等**。首跑 A2 MISS——审计脚本漏传 metrics,比对对象不等价(与 R49 control-group 教训同族:比对必须等价);修正后全绿。
- **A3 Gate 作用域攻击 🔴 证实过强主张**:重建 R49 staging 自我覆盖形态(原件零触碰、staging 拷贝被同名源覆盖)——**Gate 对原件集放行(绿),而 oracle 已被污染**。证伪 R50 台账"R49 staging 自我覆盖类污染今后将直接 fail-closed":Gate 的真实作用域 = 防"审查/变异代码改动原件"(R46 BUG-29 家族);staging 拷贝污染仍靠控制组保真检查——**两道防线缺一不可,不可互相替代**。已勘误 `audit_integrity.py` docstring / 契约设计稿附录 B / status.md。
- **A4 Gate 接线活性(sabotage 变异注入)🟢**:备份后把 `gate_assert_unchanged` 改为无条件 raise,真实重跑两个审计工具——**双双被 `[SABOTAGE]` 咬住(exit 1)**,证明调用点在真实语料运行中确实执行(非死代码);还原后 sha 与备份一致,干净重跑 exit 0。
- **A5 台账声明复证 🟢**:recompute 重跑输出与已提交工件字节级稳定;mutation 工件 all_ok=True、12 条结果在册。

### 发现汇总与修正(全部当场修正并复验)

1. **R50 过强主张(A3 证伪)**:Gate 防 staging 污染不成立 → 三处台账按真实作用域勘误(log.md append-only 以本条为准);
2. **死代码**:`gate_assert_unchanged` 的 `added` 分支不可达(前后同一 paths 派生键集,恒空)→ 删除,新增输入由调用方加入 paths 声明;
3. **工件复现性缺陷**:`r48_audit_pc_mutation.json` 含随机 staging uuid,永远无法字节复现 → raw findings 归一为 `<STAGING>`,重跑两轮**字节级一致**,工件 1 行变更入库;
4. 审计工具自身缺陷 2 处(A2 漏传 metrics、A4 锚点随函数修订失配)→ 均当场修复并留痕;另补 CI 测试 t9(record 顺序无关性)。

**结果**:R50 治理机制经对抗审查维持成立(快照确定性/摘要/接线活性全部实证),1 处过强主张已勘误;套件 **143 passed + 1 xfailed**(本地;CI 口径 126+17 skip)。**下一工作物 = 用户裁定的参考 Resolver 实现**(scripts/resolver_reference.py,严格按冻结契约),实现存在后开 R-ACC-1~11 + 附录 A 实现级对抗审查。

---

## R52(2026-09-13):参考 Resolver 实现(用户裁定:实现先行,不做纸面审)+ 真实语料首跑

**输入**:用户裁定"先做严格按冻结契约实现的参考 resolver,再基于该实现启动 Resolver Consumer Adversarial Audit(R-ACC-1~11 + 附录 A);不要先纸面审查——风险已从设计合理性转移到契约是否被代码真实执行,必须有可攻击的实现对象"。

### 交付:`scripts/resolver_reference.py`(参考实现,不进生产链路)

契约条款逐条落地:**C-IN-1** v1 fail-closed 拒收(在 QC 之前);**C-IN-2** 唯一裁决来源 = 生产共用 `reslice_qc.check`(不看产物存在性,不重新发明校验);**C-IN-3** 四态传播(REJECTED_V1 / REJECTED_QC_FAIL / REJECTED_STALE / MISSING / REJECTED_QC_UNCOMPUTABLE / ADMITTED_PENDING_REVIEW / ADMITTED),PENDING_REVIEW 走 Admission 通道**永不自动转 PASS**;**C-IN-4/5** 身份与 basis 只读搬运(逐字段,不重塑);**C-IN-6** answer 区题号与本单元无关 → `answer_number_mismatch` 结构 flag,不重绑不崩;**C-IN-7** 答案表 td 双形态(键位按题号取 / 纯位置按序对齐),推不出标 unresolved **不猜**;**C-IN-8** 内容只按 span 行号切片,不重解析标题;**C-OUT-1** 输出全部派生自 --out;**C-OUT-2** 逐单元一等公民 provenance(EvidenceProvenance:source_version=源 sha256 / source_lines=spans / extraction_method / confidence_state,含 materials 去重引用——shared material 不复制、single material 不丢);**C-OUT-3** 报告按规则 4 带 numerator/denominator/proof。三边界:只做 structural 判断;**import 面零身份推断逻辑**(不 import question_identity,身份唯一来源 = manifest 字段,R-ACC-4);STALE 结构信号 = span 越界(先于 QC 判定)。

### CI 契约测试 +12(`tests/test_resolver_reference.py`)

t1 ADMITTED + 身份逐字段只读(R-ACC-3)+ provenance 齐全(R-ACC-11)+ 材料去重 + 行号锚定;t2 v1 拒收(R-ACC-1);t3 QC FAIL 拒收(R-ACC-2);t4 PENDING_REVIEW 进 Admission 通道不转 PASS(C-FAIL-2);t5 STALE(源截断);t6 MISSING(源缺失);t7 答案表 td 三形态(键位/位置/unresolved 不猜,C-IN-7);t8 题号错位 flag 不重绑(C-IN-6/R-ACC-5);t9 跨节重号 fail-closed 且 basis 不被重解释(R-ACC-9/C-IN-5);t10 输出仅落 --out(C-OUT-1);t11 run 字节确定性;t12 import 面审计(R-ACC-4)。

### 真实语料首跑(88 份,输入 = R50 冻结基线)

`--preflight data/resolver_contract_preflight.json --out data/resolver_ref_r52`:**ADMITTED 71 / REJECTED_QC_FAIL 16 / REJECTED_V1 1(三十一中化学)——与 preflight QC verdict 分布(PASS 71 / FAIL 16)+ v1 拒收路径精确对账**;units_in_ir **1664**;0 MISSING / 0 STALE / 0 UNCOMPUTABLE。**字节确定性**:同输入重跑两轮输出逐字节一致。工件策略:report(0.6KB)入库;IR(11MB)**不入库**——字节确定性已证,可从冻结基线复现,按 Audit Snapshot 纪律以摘要引用 `resolver_ir.json@sha256:fbcf41ab025fd786…65b04a5`。

### 边界(如实)

- **本实现尚未经对抗审查**——"71 ADMITTED"只是首跑观测,不是正确性证明;
- R-ACC 逐条实测(R-ACC-6 真实答案表 15 份/305 单元、R-ACC-8 附录 A 全量、R-ACC-2/7/9/10 变异敏感性、独立重算)属下一轮 **Resolver Consumer Adversarial Audit**;
- STALE 检测当前只有 span 越界一个结构信号(源内容漂移但行数不变时不可检出——如实记录为已知检测边界,审查轮须攻击此面)。

**结果**:参考 Resolver 落地并跑通真实 88 份语料;套件 **155 passed + 1 xfailed**(本地;CI 口径 138+17 skip)。

---

## R53(2026-09-13):Resolver Consumer Adversarial Audit——R-ACC-1~11 逐条实测 + 附录 A 全量 + 独立重算 + 变异攻击

**输入**:Goal 轮(用户裁定的实现级对抗审查);纪律同 R46:独立重算 + 变异 + 穷举,不得抽样冒充全称;受审工件 `resolver_reference.py` 审查期间字节冻结(git diff 复证)。

### (a) 独立重算:`scripts/r53_resolver_audit_recompute.py` → `data/r53_resolver_audit_recompute.json`

不信任 IR 任何字段,正则/映射/判定全部独立重实现(仅裁决源复用生产共用 qc.check,契约 C-IN-2 即如此要求):**88 份 / 1664 单元穷举,0 findings**——disposition 全链重算逐文件相等(71/16/1);身份 8 字段逐单元只读(R-ACC-3);provenance 七字段完备且 source_version 与独立计算源 sha 逐文件核对(R-ACC-11);反伪造贯穿(unknown → printed 必空);内容切片逐 zone 与独立源行切片全等(行号锚定 C-IN-8);**材料 278 条** consumers 集合精确(共享不复制、单题不丢);section 全解析(R50 攻击清单①);flags 独立重算逐条相等;IR 工件 sha 与台账引用一致。

- **答案表实测(限定口径:71 份 ADMITTED 内)**:**528 单元** answer span 指向单行 `<table>`——键位可解析 **26**(按题号取,抽验正确:值全部 ∈ td 原文)、**502 如实 unresolved 不猜**(全量 v2 口径 554 为 R49 数字,含 FAIL 文件);R19 答案表格级切分前置任务仍然成立;
- **answer_number_mismatch 91 例(b-C 26 / pilot 11 / PAC 54)逐例分诊**:全部为正确结构观察——答案区局部编号(`1. 本题共10分…`、`1. (5分)`)vs 全卷 canonical(51/41…),即 BUG-22 家族在答案区的体现;flag 观察而不重绑,零误报;
- **c13-02 具名样本**:ADMITTED / 10 单元 / 1 mismatch flag——不崩、不静默错配、处置留痕(R-ACC-5)。

### (b) 变异攻击:`scripts/r53_resolver_mutation.py` → `data/r53_resolver_mutation.json`

**15/15 全中**(原件 sha 前后不变,Gate 在场):**代码变异 6 条**(PENDING 悄转 ADMITTED→t4 咬、basis 重解释→t1 咬、撤销 v1 拒收→t2 咬、猜 unresolved→t7 咬、丢 source_version→t1 咬、硬编码写 data/→**data/ 目录 Gate 咬住**)+ 还原复绿;**真实语料 staged 变异 7 条**(控制组逐字复现原件内容):v1 剥离→REJECTED_V1、切片答案区破坏→REJECTED_QC_FAIL、剥 section_ref→PENDING_REVIEW 通道、源缺失→MISSING、截断→STALE、跨节非 keep 重号→fail-closed 且 basis 不动(R-ACC-9)、**标题变异→IR 内容切片与控制组全等**(R-ACC-10 行号锚定实证)。

### 发现汇总(全部如实入册)

1. **F1(边界事实,C2 首跑 MISS 定性产物)**:QC 的 C3 裁决对象是**切片 md 锚点**,resolver 抽取对象是 **manifest spans**——二者漂移(改 manifest 不改切片)时 QC 与 resolver 均无检测;该态生产不可产生(pipeline 同编译),首跑 MISS 定性为**变异设计缺陷**(改用生产可 representable 的切片破坏后咬住);登记为消费侧防御纵深候选(结构性 flag 可加,受审工件审查期间冻结不改,实施待批);
2. **t10 盲区如实**:CI t10 只断言 --out 内容,捕捉不到越界写 data/——M6 证明 data/ 目录 Gate 是必要补位(C-OUT-7 证据 = Gate 咬住);
3. 审计工具自身缺陷 3 处当场修:重算脚本 IR 键路径形态不匹配(绝对 vs 相对,归一化)、unresolved∩answers 并存误判(键位部分命中为合法态,t7 实证)、变异脚本 c6 note 类型错;
4. STALE 检测边界沿 R52 声明:仅 span 越界信号(源内容漂移但行数不变不可检出),provenance 已嵌源 sha256 供下游检测。

### R-ACC 逐条裁决(全部真实测试)

R-ACC-1 ✅(真实 v1 + C1)/ 2 ✅(16 真实 FAIL + C2/C3 + CI t3t4)/ 3 ✅(1664 单元穷举)/ 4 ✅(t12 import 面 + R2 穷举复制证明;间接依赖经生产 QC 本体如实声明)/ 5 ✅(c13-02)/ 6 ✅ 限定口径(528 机器穷举 + 键位抽验,502 unresolved 诚实)/ 7 ✅(M6 Gate + 盲区声明)/ 8 ✅(附录 A 88 份全量,处置全可归因)/ 9 ✅(C6)/ 10 ✅(C7)/ 11 ✅(provenance 穷举 + C4/C5)。

**结果**:参考 Resolver 通过首轮实现级对抗审查——**0 结论级翻转、0 新生 resolver 缺陷**;1 项防御纵深候选(F1)+ 3 处审计工具自身缺陷(当场修)。套件 **155 passed + 1 xfailed**(本地;CI 138+17 skip);受审工件审查期间零变更。

---

## R54(2026-09-13):用户 R53 验收裁决落盘 + F1 Audit Invariant 实施 + Resolver 审查第二轮边界攻击

**输入**:用户对 R51–R53 的验收裁决(原样入库要点):

### 用户裁定要点

1. **R53 第一轮验收:通过 🟢**;但定性必须区分:"没有证明 Resolver 正确,而是证明 **Resolver 按冻结契约实现时,没有发现违反契约的行为**"。Reference Resolver **继续保持审查对象,不进入生产链路**;"参考实现 → 对抗验证 → 再消费"隔离策略维持。
2. **F1:实施,但定位 = Audit Invariant only,不是 Resolver admission rule,不升硬 Gate**——不得让 Resolver 变成第二套 QC(否则违反"Resolver 不重新判断事实,只消费已过 QC 的事实"的冻结原则)。检查面严格限定四项:**source_version_sha / start_line / end_line / span hash 必须一致**;不检查语义正确性/题目完整性/答案合理性(属 QC/Admission)。输出形态:`{question_id, qc_span_hash, resolver_span_hash, status: MATCH}`。
3. **STALE 检测边界:维持不扩大**。STALE 三分类:Structural stale(Resolver 可检)/ Source stale(provenance 检)/ Semantic stale(人工/LLM 审);Resolver 只负责第一类,检测 semantic stale = V2 失败模式回归。
4. **进入 Resolver Consumer Adversarial Audit 第二轮**(非 rollout),目标从"Resolver 是否违反契约"转为"**Resolver 周边系统是否能制造契约合法但语义错误的数据**"——重点是边界组合攻击:
   - **R-ACC-12 QC→Resolver 边界攻击**:QC PASS + manifest 合法 + Resolver ADMITTED,但题目事实错误(如题干 span 缺最后一个条件)——结构完全合法,当前最大剩余风险;
   - **R-ACC-13 Material Consumer Attack**:material 顺序交换 / shared material 错绑定 / single question 错继承 material / composite material 泄漏;
   - **R-ACC-14 答案表 unresolved 消费攻击**:unresolved → 下游默认值 → 误变 admitted(尤其未来 Agent/UI 层)。
5. **优先级(用户排序)**:P0 = F1 + Resolver 第二轮边界攻击;P1 = BUG-11/14/15 数据卫生、basis schema-only;P2 = 三十一中 keep 三方裁决;P3 = 生产 Resolver(最后一步)。
6. 项目价值定性(用户):当前最重要的价值不是"能解析题目",而是已形成"事实来源冻结 → 确定性身份 → 证据绑定 → 结构解析 → 可攻击验证"链路;**下一阶段重点继续攻击边界,不增加功能**。

### 本轮执行(R54,裁定后随即开工)

(本轮执行结果见下方 R54 收口补记;本节为裁决落盘。)

---

## R54 收口补记(2026-09-13):F1 落地 + 第二轮边界攻击实测结果

### 交付

1. **F1 Audit Invariant**:`scripts/audit_f1_consistency.py`(f1-consistency-0.1)。三方对账:resolver 侧(manifest spans × 当前源)vs QC 侧(annotated META 锚点区间 + 切片区文本),四项检查 = source_version_sha / start_line / end_line / span hash;期望值独立重实现(不 import 生产 compile);可选 `--ir` 与运行时刻 provenance 三方对账;共享答案表区如实 UNCOMPARABLE;确定性输出 + Input Integrity Gate 接线。**定位严格按裁决:Audit invariant only,零生产代码变更,resolver_reference.py 审查期间零触碰。**
2. **CI 契约测试 +11**(`tests/test_audit_f1.py`):干净产物全 MATCH / manifest 漂移 / 切片漂移 / 源内容漂移(行数不变)四类注入 + 确定性 + C-OUT 收敛 + IR cross-check 精确隔离 source_version + R-ACC-14 消费不变量 I0–I3(含 shape 防回归 t11)。
3. **第二轮攻击脚本**:`scripts/r54_round2_attack.py`(R-ACC-12/13/14 + F1 灵敏度),工件 `data/r54_round2_attack.json`。

### 实测结果(全部真实测试证据)

- **F1 真实语料控制组(输入 = R50 冻结基线 88 份)**:**88/88 文件、2403/2403 单元 MATCH、0 漂移**;294 shared-answer 区 UNCOMPARABLE(内容不回引,行号注释逐字比对)。工件:`data/r54_f1/f1_summary.json`(入库)+ `f1_report.json`(4.8MB,`sha256` 见 summary,不入库,R52 先例)。
- **F1 灵敏度**:代码变异 **4/4** 被 CI 咬住(含 Gate sabotage 接线活性);真实语料 staged manifest 漂移(不重编译)→ F1 报 DRIFT(1 单元)而 **Resolver 同一态照常 ADMITTED**——F1 必要性直接实证;控制组零变异 staging 复现原件 MATCH。
- **R-ACC-12**:stem 尾行丢弃 **6/6**、answer 错绑下一单元 **6/6** 全链绿(QC PASS + ADMITTED + F1 MATCH)——**结构链全绿而语义已错,量化坐实语义正确性只能由 Admission 承接**(用户预判的"当前最大剩余风险"获实测确认);answer 错绑 6/6 未触发 answer_number_mismatch(flag 为结构观察非保证)。options 丢尾 1/1 绿;material 外扩族样本无合格单元(0/0 如实)。
- **R-ACC-13**:material 交换/错绑定/丢失三族 resolver 与独立重算期望 **consumers 精确相等、文本单份、零重塑**;composite 泄漏被 C12 咬住 fail-closed;控制组复现原件。
- **R-ACC-14**:真实 IR 528 表单元消费不变量 **0 findings**;口径对账 26 键位单元/30 键、502 全 unresolved 单元/596 unresolved 槽位(与 R53 互洽);负向对照 6/6 咬住。**下游默认值攻击面:`answers.get(q,"")` 会把 596 个 unresolved 槽位静默变"已解为空"** → 登记 C-OUT 消费侧条款候选(未来 Agent/UI 必须显式处理 unresolved)。

### 审计工具自身缺陷(本轮抓获,如实入册)

1. **R-ACC-14 检查器首版 schema 误读**(审计工具缺陷,非 resolver 缺陷):按"逐题映射"错误形状编码,真实 IR 产生 **2210 条伪 findings**;真实数据校准后按 `{cells, method, answers, unresolved}` 表对象重写 → 0 findings;I0 形状检查 + t11 防回归入 CI。
2. **F1 匹配逻辑缺陷**:无 span 单元误消费同题号键下他单元锚点(教师用书汇编 84 单元/20 重复键触发,首跑 2 份文件 92 单元伪 DRIFT)——88 份控制组抓获,修复后 2403/2403。
3. 全量套件复跑时 `-W error` 放大下既有 `test_run_paths.py`(R28 子进程集成)报 thread exception warning(本轮未触碰该路径;正常口径绿灯)——如实记录,不属本轮缺陷。

### 套件与治理

- 套件 **166 passed + 1 xfailed**(本地;R53 155 + 本轮 11);生产链路脚本(`reslice_pipeline`/`reslice_qc`/`question_identity`/`resolver_reference`)零变更。
- 两个新工具均过 Input Integrity Gate;staging 规范执行(源拷贝 `src_*` 防自我覆盖、控制组、备份还原 sha 闭环、原件零触碰)。
- 设计稿:`resolver_contract_design.md` 新增**附录 C**(R54 裁决 + F1 定义 + 二轮结果 + 边界)。

**结果**:用户 R53 裁决全部落地;F1 以 Audit Invariant 形态实施并经真实语料 + 变异双向验证;Resolver 审查第二轮(R-ACC-12/13/14)完成——**0 新生 resolver 缺陷**,最大剩余风险(结构合法但语义错误)获量化证据,归宿 = Admission 层。待用户裁定下一轮(优先序:P1 BUG-11/14/15 数据卫生 / basis schema-only;或对本轮验收 + 攻击面扩样)。

**闭环证据**:提交 `971c887`(8 文件,+2386)→ 推送 `d18307e..971c887` → **CI Run 34734417644 = success,`149 passed, 17 skipped, 1 xfailed`**(本地 166 − 17 语料 skip = 149,算术闭合)。受审对象 `resolver_reference.py` 与生产三脚本本轮零变更(git diff 复证)。

---

## R55(2026-09-13):对 R45 声明结果的对抗性审查——逐声明真实测试复证

**输入**:用户指令——"针对 R45 的声明结果开启一轮严格的对抗性审查,每个结论必须有真实测试作为证据;不降低测试和验证标准,不自我合理化任何问题,不强行解释未通过测试的内容,不靠推测输出结论"。

### 被审声明逐条复证(方法全部为真实测试,不 import 被审审计脚本逻辑)

| R45 声明 | 复证方法 | 结果 |
|---|---|---|
| L1 探针全量:530 单元/78 报警/11 文件,P13:24+P14:32+P15:22 | 工件独立重算 + 逐文件单元数 vs 磁盘 manifest 穷举 + semantic_probe 确定性重放(如实标注 import-based,仅作漂移检查) | ✅ 逐项相等 |
| L2 78 报警 = 76 探针盲区 + 2 源卷噪音,**0 个新缺陷** | 新写独立分类器三方交叉(R45 口头/R46 机器/R55 独立)+ 族级一致率 + 残差 24 条逐条机器证据分诊 | ✅ 顶层命题成立:族级一致 **78/78,跨族 0**;分项数字不可作事实层(F-r55-3) |
| L3 分项 7/8/8/4/17/21 | 算术复核 | ❌ 65+2=67≠78(R46 已更正;本轮独立复证更正成立) |
| L4 c13-02 两条 P15 = 源卷版本噪音,printed=None 未伪造 | 源文件行级证据(题干区"共1小题" vs 解析区"共2小题"逐行留档)+ Q20 manifest 字段实查 | ✅ |
| L5 覆盖 10/10(c01-01 30/30、c08-01 44/44、c13-01 34/34) | 22/22 全量穷举(声明域 + 扩展攻击域分开记账) | ✅ 具名数字逐个相等;扩展域 22/22 亦全部完美(0 缺号 0 重号) |
| L6 c01-02 printed 28/28 unverified + 根因 = `NN.` 正则不认括号式 | manifest 穷举 + `PRINTED_LINE` 对 28 条真实题干首行逐条测试 + c01-01 阳性对照 | ✅ 28/28 unverified;括号式首行正则命中 0;阳性对照命中 >0 |
| L7 22/22 深度语义复核 | track 工件字段级(method=深度 ×22、notes 全非空、verdict 18/4 与头一致) | ✅ 工件级;"人类确实逐题阅读"属过程声明,机器不可证,如实限定不冒充 |
| L8 套件 111 passed + 1 xfailed(R45 时点) | `294f5c7` 隔离 worktree 离线重跑 = **94 passed + 17 skipped + 1 xfailed**(=111−17 语料 skip,算术闭合)+ R45 head CI Run 34723840150 = success | ✅(历史 CI 日志 blob 拉取 TLS 超时,如实声明证据局限,以 worktree 可复现重跑 + run 结论替代) |

### 发现(全部入 `data/r55_r45_audit.json` findings 字段)

- **F-r55-1**(在案复证):R45 分项算术不成立,65+2≠78;R46 更正成立。
- **F-r55-2(本轮新发现)**:R46 对 R45 的更正**自身亦有分项缺口**——残差 24 条的分项之和 = **23**,漏计 `pac-c12-02 Q20` P13 行 `20. （1）铯（2）b（3）a`(括号子问答案连写,良性盲区;R46 的"紧凑答案行 6+1"计入了 c11-01 Q52,该行无归属)。不影响顶层结论,但坐实"分项计数从未被机器账目钉住"这一缺陷家族在 R45/R46 两代台账中均存在。
- **F-r55-3(方法论)**:三套分类桶界互异——标签级一致仅 43/78(分歧 35 条全部为同族内桶界差异,如括号连写 vs 格式盲区、评分细则 vs 子问编号),而**族级一致 78/78、跨族 0**。结论:分项数字不是事实层,顶层命题(良性家族归属 + 0 新缺陷)才是被复证的对象;今后分诊报告以族级账目 + 逐行留档为准。
- **F-r55-4(审计工具自身缺陷,当场修)**:R55 独立分类器首版两处缺陷——M1 错误限定 `check=="P15"`(R46 R1 的 21 行多为 P14,致 M1 仅命中 3/21)与行首正则不认 OCR 转义点(`1\.`)——均由与 R46 分类的交叉比对抓获;修复后 M1 21/21 对齐、族级 78/78;CI t1/t2 防回归。

### 变异与灵敏度(全部咬合,原件零触碰)

- **M-a**:staged 探针工件删 1 条报警 → 独立重算立即失配 ✓;
- **M-b**:真实语料答案值篡改 X→Z(重编译,生产可 representable)→ **QC PASS、探针报警数不变**——结构链对答案值级语义错误无检出义务;"0 新缺陷"是 78 报警的分诊结论,**不是**语料无缺陷的证明(R45 原文措辞即为分诊结论,无过度声明;此项为边界量化);
- **RM1/RM2/RM3**:本工具自身代码变异(撤销转义点容忍 / M1 退回 P15 限定 / md_of 退回 with_suffix 陷阱)→ 9 条 CI 测试中 3 条精准咬合 + 还原 sha 闭环;
- **Input Integrity**:R50 冻结基线 356 文件 verify **0 漂移**(与 R50 时点一致;R45/R46 时点输入一致性由 R46(e) pac_select 22/22 指纹检查承接,本轮如实限定不越界声称)。

### 资产与套件

新增 `scripts/r55_r45_audit.py`(语料依赖,本地跑)+ `tests/test_r55_r45_audit.py`(**CI +9**:M1-P14 回归/转义点回归/M2-M5 契约/残差分诊桶 8 类/coverage 三态/md_of 陷阱回归);工件 `data/r55_r45_audit.json`(24KB,入库)。套件 **175 passed + 1 xfailed**(本地)。

**结果**:R45 顶层声明 L1/L2/L4–L8 全部以真实测试复证成立;L3 分项算术为已知更正在案;新增 F-r55-2(R46 更正自身的分项缺口)与 F-r55-3(方法论:分项数字非事实层)。**0 新的 PAC/生产缺陷**;本轮审计工具自身缺陷 3 项当场修(R49/R53/R54 同族纪律第四次实证)。审计结论待用户裁定收口(R42 先例)。

**闭环证据**:提交 `1f32952`(5 文件,+1811)→ 推送 `3c3d2a5..1f32952` → **CI Run 34736885133 = success,`158 passed, 17 skipped, 1 xfailed`**(本地 175 − 17 语料 skip = 158,算术闭合)。受审对象 `resolver_reference.py`/生产三脚本/`audit_f1_consistency.py` 本轮零变更(git diff 复证)。过程记录:首次推送因本地代理(127.0.0.1)瞬断失败,重试成功;R45 时点 CI 日志 blob 拉取 TLS 超时,以 worktree 可复现重跑 + run 结论(success)替代,证据局限已如实声明。

---

## R56(2026-09-13):外部架构级审核意见登记 + 实测定量回应 + 治理候选登记

**输入**:用户转交一份外部架构审核意见(基于 R31–R55 台账/报告/提交记录)。**审核方自述边界:未拉取仓库源码,非代码级扫描**;其对系统的事实描述与本台账一致,无新增可证伪事实主张,唯一可测断言由本轮实测定量回应。

### 实测定量(本轮真实测量,非认可式背书)

- **代码规模账目**(`scripts/` 48 文件 10,384 行;`tests/` 25 文件 2,882 行 172 个测试函数):
  - 冻结生产链核心(reslice_pipeline 804 + reslice_qc 266 + question_identity 281)= **1,351 行 / 3 文件**;
  - 审计/轮次/变异家族(r53×2/r54/r55/r48×2/r50/pac_audit×3/audit_integrity/audit_f1/semantic_probe/phase2_adversarial_probe/pac_ocr_drift 等)≈ **4,400 行 / 17 文件**;
  - 审计+测试合计 ≈ 7,300 行,为冻结生产链的 **~5.4 倍**。
- **结论:审核意见"测试/审计代码复杂度超过核心生产代码"的断言成立**(按冻结生产链口径定量;即便放宽到全部 scripts 亦同量级)。同时如实记录另一面:审计脚本是历轮一次性武器 + 工件产生方式的 provenance 证据,其复杂度不进入运行时生产面;复杂度倒挂是**维护成本风险**,不是正确性风险。
- **规则面实测**:QC verdict C1–C14(14 项,`reslice_qc.py` 内机器计数);语义探针 P13–P15(3 项,测量仪非 QC);F1 不变量 I0–I3 + MATCH/DRIFT;Gate 快照/对账机制(audit_integrity 209 行)。规则总量远未失控,但**缺统一分类学**——审核意见的"规则森林"预警在增长趋势上成立。

### 审核意见要点与本方立场(逐条)

1. **事实源/推理源分离、Resolver 只做结构判断**——与 R50 冻结裁定及三边界纪律一致,维持。
2. **basis 字段拆分建议**(`identity_policy` + `evidence`)——方向认可(事实/决策/来源三概念混于单字段确有 schema 压力);但 **manifest v2 已冻结(R50),不得原地改 schema**;候选落点 = IR/Admission 层字段演进,与排期③ basis schema-only(仅检测)不冲突。登记 **G-SCHEMA-1(候选,实施待批)**。
3. **Rule Taxonomy**(FACT_INTEGRITY/STRUCTURE/IDENTITY/EVIDENCE/QUALITY)——采纳为治理候选 **G-TAX-1**:给 Gate/QC/探针/审计不变量打类型标签,防"规则森林"。实施待批。
4. **统一审计框架**(audit/runner + assertions + mutations + reports,替代 r45_xxx/r55_xxx 无限增长)——采纳为治理候选 **G-AUD-1**,但加一条本项目特有约束:**历史轮次脚本冻结为 provenance 证据**(它们证明了各工件如何产生),统一框架自批准后的下一轮起用,不做历史迁移。实施待批。
5. **不继续加 regex 防"OCR 规则地狱"**——与既有三边界(机器=结构/证据存在/范围;人工=语义真实性)一致;④ printed 硬化维持 unknown > 错误确定性。
6. **Resolver 禁能力膨胀("顺便判断是不是同一道题"= 禁止,归 Question Similarity 层)**——三边界已有,建议在 `resolver_contract_design.md` 显式写入禁令条款(**候选 G-RES-1,实施待批**)。
7. **阶段定位:preprocessing = V3 Data Admission Layer;V3 backend 不得重复 OCR/section/identity 判断**——与 R50 冻结一致,登记为跨仓库边界原则(候选 G-BOUND-1)。
8. **下一阶段转向"稳定接口"**:① BUG-11/14/15 数据卫生(= 既有优先序②)② Question IR → Admission → V3 Backend 消费链验证 ③ 端到端重放测试——与现有待裁定清单同向;②③ 需用户排期。

### 本轮动作边界

**仅登记,零执行**:无代码/契约/schema 变更;所有候选(G-SCHEMA-1/G-TAX-1/G-AUD-1/G-RES-1/G-BOUND-1)待用户裁定采纳与排期。R55 结论仍待收口。

---

## R57(2026-09-13):二审裁定落地——规则登记册 + Resolver 禁令 + 阶段定位(R56 审核意见收口)

**输入**:外部二审意见(基于 R51–R56 记录,自述非代码级)含最终裁决。

### 裁决与处置(全部落地,零生产代码变更)

1. **R55 收口 ✅**(R45 声明复证轮,提交 1f32952/52da2e3,CI 34736885133/34737142579 success)。
2. **G-TAX-1 + Rule Retirement Policy → `governance/rule_registry.md`**:五类 taxonomy(FACT_INTEGRITY/STRUCTURE/IDENTITY/EVIDENCE/QUALITY);登记 C1–C14(逐条取自 reslice_qc.py 真实描述)/ P13–P15(测量仪)/ F1+I0–I3 / 审计治理机制 / R-ACC 攻击家族;每条含 purpose/attack surface/evidence/retirement;退役政策 5 条(新增必登记、C 族退役须裁定、审计脚本冻结为 provenance、探针替换须同级校准、**默认拒绝"审计审计系统"**)。
3. **G-RES-1 → 契约附录 D.2**:Resolver 四项显式禁令(semantic inference / similarity judgment / knowledge classification / answer correctness judgment);违禁判定标准 = 输出超出"结构事实+出处"即拒,路由后续层。
4. **G-BOUND-1 → 附录 D.3**:preprocessing = V3 Data Admission Layer;Backend 不得重复 OCR/section/identity 判断;消费面 = IR + provenance + unresolved 显式通道(596 槽位,禁静默默认)。
5. **G-SCHEMA-1 延期**:basis 拆分落 IR vNext/Admission vNext,不反向改 Identity v2(多轮验证资产,现改重开 migration/resolver/admission 风险)。
6. **G-AUD-1 暂不实施**:历史 audit artifact = provenance,不重构。
7. 审计惯性防线(附录 D.4):复杂度倒挂(5.4×,R56 实测定性)治理手段 = 冻结增长+分类学+退役政策,不削减已证明必要的检查。

### 测试与证据

- `tests/test_rule_registry.py` **+4**:代码↔登记册**双向 set-diff 钉住**(册上幽灵规则与代码未登记规则都被咬)+ taxonomy/字段/退役政策在册断言。
- 变异咬合:staged 删册上 C14 行 → t1 精准咬合;还原 sha 闭环。
- 下一阶段路线(用户裁定):**Identity v2 冻结 → BUG-11/14/15 数据卫生(序 11→14→15)→ basis schema-only(排期③)→ Admission Layer 稳定化 → V3 Backend 消费**。

---

## R58(2026-09-13):BUG-11 修复——图片恢复扫描范围白名单废弃,改"排除派生目录"单一来源制

**输入**:用户指令"开BUG-11"(数据卫生轮序 11→14→15 第一项)。对象:`scripts/recover_images.py`(非冻结生产链,冻结链三脚本零变更)。

### 缺陷与修复

- **根因(原登记确认属实)**:`SCAN_DIRS = ["高一","高二","高三","未分类"]` 硬编码;重归类已把 599+ 份迁至 `高考真题/合格考/会考/竞赛自招/其他汇编/学业水平考试`,六个目录对图片恢复完全不可见——目录布局变更 → 白名单静默失配。
- **修法(故障方向翻转)**:白名单废弃,`is_source_top_dir()` = 排除派生目录(`EXCLUDED_TOP_NAMES={"_imgs",".cache"}` + `EXCLUDED_TOP_PREFIXES=("auto-annotated","reslice")`),其余顶层目录一律视为源。未来**新增源目录自动纳入**(原缺陷形态不可能复发);误纳派生目录的代价只是多扫(已重写/无引用幂等跳过),不会漏修。顺带 `import fitz` 改惰性(`_fitz()`),扫描/干跑/CI 离线可用(CI 只装 pytest,不装 PyMuPDF)。

### 实测证据(全部真实测量)

1. **视野扩张**(`data/r58_bug11_coverage.json`,只读全库测量):扫描面 2,421 → **3,119** 份,新可见 **698**(高考真题 599 / 合格考 71 / 会考 17 / 竞赛自招 6 / 其他汇编 4 / 学业水平考试 1)。
2. **⚠ 实测修正(防夸大,本轮最重要事实)**:盲区 698 份中**当前缺图候选 = 0**——迁出文件在迁移前(还在旧目录时)已被恢复(高考真题 515/599 已标 `_imgs`,余 84 无引用)。BUG-11 的现实危害 = **流程性潜伏风险**(今后带悬空引用的文件一经重归类即逃出恢复视野),不是既成数据缺失。当前缺图积压 499 份/10,439 处**全部在旧视野内**(未分类 129/高二 136/高三 130/高一 104;OCR 新产出的常规增量积压,与本 bug 无因果),**是否执行恢复跑属独立决策,本轮未擅自写任何语料**。
3. **dry-run 端到端**:全量 3,119 份零异常,统计(with_refs 499 / already_done 2182 / no_refs 438 / pdf_miss 0)与证据脚本逐项一致;账目文件 `recover_images_summary.json` 备份→dry-run 覆盖→还原,**sha256 闭环**(32FF802A…,git 零漂移)。
4. **回归钉** `tests/test_recover_images_scan.py` **+5**:t1 新源目录自动纳入(白名单回退必咬)/ t2 派生目录全排除 / t3 嵌套 `_imgs` 与非 md 不扫 + 确定性排序 / t4 排除表纯函数双向断言 / t5 **真实语料冒烟**(六个重归类目录必须在扫描结果中,旧口径为新口径真子集)。
5. **变异咬合**:M1 回退旧白名单 → t1+t5 双拦;M2 去 `_imgs` 排除 → t2+t4 双拦;两次还原后 5/5 过。沙箱环境注记:系统 temp 不可写(WinError 5),测试用仓库既有 `workdir` fixture(`.pytest_work/`),tmp_path 不可用。
6. **全套件**:本地 **184 passed + 1 xfailed**(原 179+1);CI 口径 = 184 − 18 语料 skip(原 17 + t5)= 166 passed 预期。

### 台账同步

`bugs.md` BUG-11 → ✅ 修复(含实测修正段);`prd.md` §10-C → 已修复;`status.md` 配图恢复行同步。

**结果**:BUG-11 关闭。**盲区内当前零欠账是实测事实,不冒充挽回损失**;499 份旧视野积压的恢复执行留给用户决策。下一项按序 = BUG-14(跑步机 + 73 重复源)。

---

## R59(2026-09-13):R58(BUG-11 修复轮)对抗性审查——逐结论真实测试复证,1 项措辞证伪、其余成立

**输入**:用户指令"针对R58结果开启严格对抗性审查,每个结论必须有真实测试作为证据;不降标准、不自我合理化、不强行解释、不推测"。方法同 R55:被审结论一律独立实现重测(不复用被审函数 `scan_md_files`/`is_source_top_dir`/`REF`),分歧以审查工具为准并记 finding。工具 `scripts/r59_r58_review.py` → 工件 `data/r59_r58_review.json`(只读,零语料写入)。

### 逐结论裁定

| # | R58 结论 | 审查方法 | 裁定 |
|---|---|---|---|
| 1 | 视野 2,421→3,119,新可见 698(逐目录 599/71/17/6/4/1) | 独立 os.walk 重算(源目录表硬取自 R58 工件,非被审代码)+ 顶层目录分类穷举 | ✅ **成立**:总数/旧口径/新可见/逐目录 10 项全对账;classification_gap=0;排序确定 |
| 2 | 盲区 698 份当前缺图候选=0 | 扩展语法攻防:`imgs/` 任意扩展名 + 完整 `src="…"` 属性解析(12,321 处)+ markdown 图片语法 + 落盘存在性 | ✅ **成立且稳健**:悬空 `imgs/` 形态 0;12,316 处 src 全指 `_imgs/`,`_imgs/{base}` 目录 515/515 落盘在;84 份未标记文件 0 悬空引用 |
| 3 | dry-run 统计(499/2182/438/0)与证据脚本一致、账目 sha 闭环 | 重跑 dry-run 逐项比对 + 备份-还原 sha256 | ✅ **成立**:六项统计逐项复现;499+2182+438=3119 算术闭合;sha 32FF802A… 前后全等 |
| 4 | 变异咬合(M1 白名单回退→t1+t5;M2 去 `_imgs`→t2+t4) | 重演 + **充分性扩展 M3–M6** | ✅ **成立并加固**:M3 撤前缀排除→t2+t4;M4 忽略 root→3 拦;M5 撤嵌套 `_imgs` 过滤→t3;M6 过度排除`高`→5 全拦;全部还原后 5/5 过,文件与 `dc4a1f7` 逐字节一致(git diff 空) |
| 5 | lazy fitz 后 CI 离线可用 | CI Run 34739744860 日志逐条 | ✅ **成立**:t1–t4 在只装 pytest 的 ubuntu runner PASSED;t5 SKIPPED(corpus 缺席,skipif 生效),skip 17→18 算术如实 |
| 6 | 冻结生产链零变更 | git diff 9df4557..dc4a1f7 全量 | ✅ **成立**:8 文件 +357/−17,全为本轮对象;冻结三脚本 + resolver_reference + audit_f1 diff = 0 |
| 7 | **"误纳派生目录的代价只是多扫(幂等跳过),不会漏修"** | 无排除政策全量推演:11 个派生目录 1,762 份 md 逐份测裸引用 + PDF 命中 | 🔴 **证伪(F-r59-1)**:**84 份派生 md**(auto-annotated-v3 82 + reslice-batch-C 2)会被 `process_one` **真实处理**(提取图片+就地重写+审计),非只读扫描。**当前代码行为正确**(排除表全覆盖,现实风险=0),错在反事实代价评估;机制性残余风险=未来前缀不匹配的新派生目录会被误纳就地重写。**处置:不改排除制**(改回白名单=复发 BUG-11),bugs.md 追加更正 + 风险登记收口 |

### 审查工具自身缺陷(同族纪律,R49/R53/R54/R55 后第 5 次)

- **F-r59-2**:审查工具 v1 的 P2 用裸 token 正则,目录名含 `(1)` 使其在括号处截断 → 12,302 个假阳性"裸 .jpg"(实为 `src="../../_imgs/{名}(1)/…"` 的尾段);`.gif` 命中为英文单词 "gift" 假阳性。当场改为完整 `src="…"` 属性解析,claim_robust 由 false 翻转为 **true**;抽样脚本 v2 独立复核一致。**若不修,审查会把 R58 正确结论误判为错误**。
- **F-r59-3(信息项)**:根层 1 份 md = `README.md`(非试卷,目录遍历语法不覆盖根层文件,无现实影响);盲区 5 处 `src` 为 codecogs 外链 SVG(外部依赖,非本地缺图债,消费面事项);`.restored.md` 在 `resliced-pilot`(派生目录)排除正确。
- **F-r59-4(记账卫生)**:R58 留下已追踪文件 `logs/recover_images_log.txt` 未提交修改(dry-run 追加行),R59 发现后连同本轮复跑行一并提交收口。

### 结果

R58 七项结论:**6 项成立、1 项措辞级证伪(已更正)**;0 代码行为缺陷;0 生产/语料写入。套件复验见提交。

## R60(2026-09-13):用户 R59 审核裁定落盘 + Source→Resolver→IR 事实漂移攻击(A/B/C/D 四面)

**输入**:用户对 R59 的审核裁定——R59 🟢 通过收口;F-r59-1 定性为**治理文档过度推论**,应登记 **RISK-FUTURE(GOVERNANCE/Boundary)而非生产 BUG**(当前未发生,防污染缺陷统计);F-r59-2 点名为本轮最高价值发现("审计工具也必须被审计"),建议固化 **Audit Tool Trust Boundary** 规则;下一轮目标 = **"BUG-14 第一阶段:Source → Resolver → IR 事实一致性攻击,不增加生产能力,只验证边界是否可靠"**,四攻击面 A 字节事实保持(改源行→必须 STALE)/ B Span 边界(start-1/end+1 不得静默裁剪)/ C provenance 断裂(Admission 拒绝)/ D Resolver↔QC 分叉(必须 F1 结构漂移,禁"两系统各自正确")。

**命名澄清(如实上报,不吞并)**:用户命名"BUG-14 第一阶段"所指内容(事实一致性攻击)与 `bugs.md` BUG-14 原登记(未分类跑步机 + 73 重复 basename,数据卫生)**不是同一件事**。本轮按用户明确指定的内容执行(攻击面 A/B/C/D 原文级落地);BUG-14 原登记条目保持开放顺延,命名冲突已在 bugs.md 标注留待用户裁定。

**执行**:`scripts/r60_fact_drift_attack.py`(一次性武器,含 G-AUDTB-1 首个覆盖范围声明)——全部变异只作用于 `.pytest_work` staged 合成副本(生产同构四件套经 `rp.write_outputs` 真实编译),SUT(resolver_reference / reslice_qc / audit_f1_consistency)黑盒观测三层(resolver disposition / QC verdict / F1 zone);`--corpus` 模式对 88 份真实控制组只读复核(audit_f1 内建 Input Integrity Gate)。工件 `data/r60_fact_drift_attack.json`。

### 四攻击面实测裁定

| 攻击 | 变异 | 实测结果 | 裁定 |
|---|---|---|---|
| A1 界内字节篡改 | 源题干行改字,行数不变 | resolver **REJECTED_QC_FAIL**(理由=C8 锚点保真,非 STALE)+ F1 DRIFT | ✅ 无静默 PASS;**防线身份如实:C8 整文件比对**,不是 STALE(冻结契约 STALE=结构信号,R53 裁定不扩大) |
| A2 span 外字节篡改 | L2 空行→文本 | C8 拦(FAIL);**F1 如实 MATCH** | ✅ 拦截成立 + **互补性事实入账:F1 是区级不变量,看不见 span 外漂移**,与 C8 互为补集,谁都不是全集 |
| A3 旧 IR + 篡改源 | IR 产出于原始源后改源 | F1 --ir:**source_version_match=false → DRIFT** | ✅ 陈旧 IR 必须被三方对账捕获 |
| B1 start-1 界内平移 | stem [5,9]→[4,9] | resolver **ADMITTED(静默)**,IR 内容实测被平移(多吸入空行+图行);QC PASS;F1 DRIFT:stem | ⚠️ **resolver 层静默 = 已裁定边界**(结构性 STALE 语义);**捕获层=F1 实证有效**;事实漂移坐实(非纸面推演) |
| B2 end+1 越界 | stem end→33(源 32 行) | **REJECTED_STALE** + F1 DRIFT | ✅ 结构信号按契约工作 |
| B3 answer end+1 界内 | answer [25,25]→[25,26] | 同 B1 家族:ADMITTED + F1 DRIFT:answer | ⚠️ 同上,家族行为一致 |
| C1 manifest 缺 source_file | 删键 | **resolver CRASH(PermissionError: '.')/ QC CRASH(KeyError)/ F1 CRASH** | 🔴 **新缺陷 BUG-31**:三组件无一 fail-closed;崩溃≠静默 PASS(数据安全无损),但违 C-FAIL 契约族 + 批处理整批死 + 错误信息失焦 |
| C2 source 重定向诱饵 | source_file→诱饵文件 | C8 拦(前缀差异 32)+ F1 全区 DRIFT(9 zone) | ✅ |
| C3 IR provenance 删 source_version | 删键 | F1 ir zone DRIFT | ✅ |
| D1 只改 manifest 不重编译 | Q1/Q2 answer_lines 互换 | **resolver ADMITTED + QC PASS(双绿)**;IR 里 Q1 答案实测="2.【答案】B"(错归属坐实);**F1 DRIFT:answer+answer_zone** | ✅ 用户 D 面核心命题实证:**双绿≠系统正确,分叉必须被 F1 捕获**;QC 看切片(旧)、Resolver 看 manifest(新)的裁决对象分离再次坐实 |
| D2 阴性对照 | 未变异 | ADMITTED + PASS + MATCH 全绿 | ✅ 对照成立(无假阳性) |

### 变异咬合(3/3)与语料复核

- M1 禁用 QC C8 → t1/t2/t8 拦;M2 F1 恒 MATCH → t4/t9/t10 拦;M3 Resolver 去 STALE 上界 → t5 拦;**全部还原后文件 sha256 与改前逐字节一致**(`.pytest_work/r60_mutation_driver.py`,一次性)。
- 语料复核 `--corpus`:**88/88 文件、2,403/2,403 单元、0 DRIFT**——R54 基线在 R60 独立复现(gate 保护,零语料写入)。

### 审查工具自身缺陷(同族纪律,R49/R53/R54/R55/R59 后第 6 次)

- **攻击脚本 v1 观测缺陷**:A3 首版未把旧 IR 索引真正传入 F1(`observe(resolve_first=True)` 后又 `observe()` 覆盖),ir zone 根本没跑——探针 JSON 读出后当场发现,改为 resolve→edit→`check_file(md, idx)` 直连,复跑确认 `source_version_match=false`。已作为 G-AUDTB-1 evidence 入册。

### 治理落盘(按"先登记后实施")

1. `governance/rule_registry.md` §4 新增 **G-AUDTB-1 Audit Tool Trust Boundary**(禁复用生产 parser/须阳性阴性控制/解析器声明覆盖范围/审计工具缺陷与生产缺陷同级当轮修复记账);§5 追加 R-ACC-15~18 攻击家族。
2. `governance/risk_register.md` 新建:**RISK-FUTURE-001 Unclassified Derived Tree Admission Risk**(F-r59-1 按用户裁定登记为风险而非缺陷,含触发路径/监测/关闭条件)。
3. `bugs.md`:新登记 **BUG-31**(resolver/QC 缺 source_file 非 fail-closed,strict xfail 修复义务钉 `test_t7` 已就位);BUG-14 条目补命名澄清;BUG-11 R59 更正块补风险登记指针。
4. `tests/test_r60_fact_drift.py` 14 用例(13 passed + t7 strict xfail);生产/冻结链(reslice_pipeline/reslice_qc/question_identity/resolver_reference/audit_f1)**本轮零变更**(变异全部还原)。

**结果**:用户 R59 裁定全部落盘;四攻击面**无一静默放行事件漏网**(A 面 C8 拦、B 面越界拦+界内平移 F1 拦、C 面 1 崩溃如实入账、D 面分叉 F1 拦);唯一新缺陷 BUG-31(崩溃型,非静默型);套件 **197 passed + 2 xfailed**(CI 预期 178 passed / 19 skipped / 2 xfailed,t13 语料冒烟 CI skip 算术 +1)。

## R61(2026-09-13):用户 R60 审核裁决落盘 + BUG-31 修复(fail-closed 三处)+ BUG-14 命名拆分

**输入**:用户 R60 审核裁决——R60 ✅ 收口通过;核心架构裁定:**QC/Resolver/F1 不是重复防线,是不同层级的不变量保护**(QC=准入前事实约束 / Resolver=结构解析不承担全部事实证明 / F1=跨阶段一致性检测);**Resolver Admission ≠ Semantic Truth Validation 写入契约(改文档不改代码)**;BUG-31 **批准修复**,修复边界严格限定:只加"missing required provenance → explicit failure state",**禁止**新增 fallback / 自动补 source_file / 猜测路径 / 降级 ADMITTED(缺事实 ≠ 推测事实);BUG-14 命名**拆分不重写历史**(BUG-14-DATA / BUG-14-CHAIN);F1 冻结不扩面(防规则膨胀);下一阶段序:BUG-31 → BUG-14-DATA。

**执行(先登记后实施)**:

1. **契约**:`resolver_contract_design.md` 新增 **D.5 G-TRUTH-1**(Admission ≠ 语义真值;三层不变量分层事实;F1 冻结不扩面)。
2. **规则登记册**:§1 新增 **C15**(FACT_INTEGRITY:manifest 必需 provenance 缺失/非文件必须显式 FAIL,禁崩溃);§4 新增 **G-TRUTH-1** 行;`test_rule_registry.py` 双向钉住范围 14→15。
3. **BUG-31 修复(三处,全部只加显式失败态,零 fallback)**:
   - `resolver_reference.resolve_file`:`src.is_file()` 守卫 → **MISSING**("source_file missing or not a file (provenance break, fail-closed)");另加 `OSError` 兜底 → MISSING("source unreadable")——**双层防御**;
   - `reslice_qc.check`:**C15** 守卫 → 显式 **FAIL**(三态内,非新裁决态),`src_of` 裸下标改 `.get`;
   - `audit_f1_consistency.check_file`:`is_file` 守卫 → **DRIFT**(note 显式)。
4. **测试**:`test_t7` 由 strict xfail **转正**(断言 resolver MISSING + 理由串 + QC FAIL 含 C15 + F1 DRIFT,三层无 exc);**新增 t7b 批处理继续**(一份坏 manifest 不杀整批:{ADMITTED:1, MISSING:1}——用户要求的"记录原因 + 继续处理其它单元"实证)。
5. **命名拆分(bugs.md)**:BUG-14 → **BUG-14-DATA**(原数据卫生,历史引用稳定);新增 **BUG-14-CHAIN**(事实一致性轨道,PHASE-1 DONE,关闭条件三项核对全 ✅,扩面暂缓);BUG-31 → ✅ 修复结案。
6. **变异咬合(4/4,还原逐字节一致)**:M4 回退 resolver 守卫 → t7 拦(附带实证:守卫回退后 OSError 兜底层仍 fail-closed,t7b 如实过——双层防御各司其职,t7 靠理由串区分);M5 回退 QC C15 → t7 拦;M6 回退 F1 守卫 → t7 拦;M7 登记册范围回退 → rr_t2 幽灵规则拦。

**冻结链变更申报**:`reslice_qc.py` 本轮有变更(C15,用户批准的 BUG-31 修复范围),变更面 = `src_of` 裸下标改 `.get` + `check()` 顶部 provenance 守卫(FAIL 早退),**既有 C1–C14 检查逻辑零改动**;`resolver_reference.py` / `audit_f1_consistency.py` 同轮变更均为 fail-closed 守卫。R60 攻击脚本与 R60 工件**未修改**(provenance 纪律;t7 改断言而非改武器)。

**结果**:BUG-31 🟢 CLOSED(修复边界内);G-TRUTH-1 + C15 入册;BUG-14 命名拆分落地;套件 **199 passed + 1 xfailed**(197+2: t7 转正 + t7b 新增;CI 预期 180 passed / 19 skipped / 1 xfailed)。下一项按用户排序 = **BUG-14-DATA**(未分类跑步机 + 73 重复源)。

---

## R62(2026-09-13):R61 全部结果对抗性审查(用户令:每结论必须真实测试证据)

**输入**:用户令——对 R61 全部结果开启严格对抗审查;不降低测试标准、不自我合理化、不强行解释未通过项、不靠推测下结论。

**审查结论一览(9 主张:8 成立 / 1 项发现台账重复缺陷;另获 2 个新缺陷 + 1 测试隐患,均已处置)**:

1. ✅ **R61 diff 面核对**:变更集恰为预期 10 文件(`git diff --stat 5335adc 0d64549`);"C1–C14 逻辑零改动"经完整 diff 逐 hunk 复核成立(reslice_qc 仅 2 hunk:`src_of` 改 `.get` + C15 守卫,插在 `src_text` 读取之前);R60 武器 `r60_fact_drift_attack.py` + `data/r60_fact_drift_attack.json` diff 为空(provenance 纪律)✅。
2. ✅ **本地套件独立重跑**:199 passed + 1 xfailed(xfail 落点 = `test_anchor.py` 锚点顺序义务钉,与 R61 无关);t7/t7b 单独跑 PASSED ✅。
3. ✅ **CI 复核(按 sha)**:run 34742571215 headSha 精确匹配 `0d64549`,conclusion=success,CI 日志原文 **"180 passed, 19 skipped, 1 xfailed"** 逐字复现 ✅。
4. ✅ **M4–M7 变异独立复跑**(`.pytest_work/r61_mutation_driver.py`):4/4 BITE + 全部 restored=True(逐字节还原)✅。
5. ✅ **G-TRUTH-1/C15 实证文本核对**:契约 D.5 全文在册(含"F1 冻结不扩面");rule_registry C15 行(L39)+ G-TRUTH-1 行(L71)在册;双向钉靠 rr_t1/rr_t2 + M7 咬合(注:登记册测试钉的是文本存在,行为钉在 t7——分工如实记录)✅。
6. ✅ **BUG-31 修复边界(值域族)对抗延伸**:`source_file` = null/""/纯空白/不存在路径/**已存在目录**(K2–K6,新攻击面,R61 未测)全部三层 fail-closed(MISSING/C15 FAIL/DRIFT),无一崩、无一降级 ADMITTED ✅。"禁 fallback/禁猜路径/禁降级"经 diff + 行为双证 ✅。
7. ✅ **K11 非法 UTF-8 源**:三组件零崩溃(`errors="replace"` 契约成立);resolver 如实消费 QC 裁决 REJECTED_QC_FAIL(篡改使 C8 保真失败);F1 无 IR 索引时区级 MATCH 属如实(sha 比对在 IR zone)——观察入账,非缺陷。
8. 🔴 **F-r62-1(台账缺陷,当轮修复)**:R61 在 bugs.md **重复插入 BUG-14-CHAIN 两次**(L35/L118,措辞分歧)——保留 L35(位置与 BUG-14-DATA 相邻,条款等义),删除 L118 副本。
9. 🟠 **F-r62-2(测试隐患,当轮修复)**:`test_no_config_import.py:27` / `test_run_paths.py:48` 的 `subprocess.run(text=True)` 未指定编码 → 读线程按宿主 GBK 解码子进程 UTF-8 输出失败(全量跑实测 `PytestUnhandledThreadExceptionWarning: 'gbk' codec can't decode byte 0x8c`)。修:显式 `encoding="utf-8", errors="replace"`。**前后对比**:修前全量 1 warning,修后 0 warning。

**新缺陷(对抗延伸抓获,PENDING_REVIEW,本轮不擅改生产件)**:

- **BUG-32(🟠)**:非字符串 `source_file`(int/dict/list/bool,K7–K10)三组件全部 `TypeError` 崩;**K13 实测批处理整批死**(`run()` L254 列表推导无逐文件兜底)。预存(非 R61 回归),违反 C-FAIL-1;生产 `write_outputs` 恒写字符串,可达性=篡改/损坏/手编。义务钉 `test_r62_t4`(strict xfail,修复转正强制翻绿)。
- **BUG-33(🟠)**:源文件拒读(OSError)时 **resolver 兜底层活体实证 MISSING("source unreadable")**(R61 新增层首次获得真实条件证明,非纸面推断),但 QC(C15 之后裸读)/ F1 无 OSError 守卫 → 双 CRASH(K12)。预存,违反 C-FAIL-1;可达性=进程独占/ACL/网络盘瞬态。K12 条件制造过程如实入账:icacls 被沙箱拒(rc=5)→ 改用 CreateFileW 独占句柄,条件先实证(PermissionError)后观测。义务钉 `test_r62_t5`(strict xfail)+ `test_r62_t3`(resolver 兜底活体证明,现即通过,Windows-only)。

**新增回归钉**:`tests/test_r62_boundary.py` 9 用例(t1×5 值族 fail-closed / t2 非法 UTF-8 禁崩 / t3 resolver 兜底活体 / t4 BUG-32 xfail / t5 BUG-33 xfail;t3/t5 Windows-only skipif,CI ubuntu 如实 skip)。

**武器**:`scripts/r62_boundary_audit.py`(一次性,黑盒观测,变异只落 `.pytest_work/r62` 合成件)+ 工件 `data/r62_boundary_audit.json`(13 用例全量观测)。

**审计纪律自证**:K12 首跑条件未成立(NOT_PRODUCIBLE)即如实 SKIP 而非宣称通过,换手段把条件真实制造出来后才出结论;BUG-32/33 定性"预存非回归"以 R61 前代码路径为据(`Path(123)` TypeError / 裸 `read_text` 均先于 R61 存在)。

**结果**:R61 八项主张全部复证成立;F-r62-1/F-r62-2 当轮修复;BUG-32/BUG-33 登记待裁定;套件 **206 passed + 3 xfailed**(CI 预期 185 passed / 21 skipped / 3 xfailed = 本地 −19 corpus −2 win-only +2 skip)。下一项维持用户排序 = **BUG-14-DATA**。

### R62 台账更正(2026-09-13,当轮 CI 实测后)

**R62 结尾"CI 预期 185 passed / 21 skipped / 3 xfailed"为算术口误**——把 win-only 的 `test_r62_t5`(本地即 xfail)重复从 passed 里扣减了一次。正确闭合:本地 206 passed 已含 `test_r62_t3`(win-only,本地通过);CI(ubuntu)仅 t3 由 passed→skip、t5 由 xfail→skip,故正确预期 = **186 passed / 21 skipped / 2 xfailed**。**CI Run 34744003063(headSha 5c53d53,conclusion=success)实测原文"186 passed, 21 skipped, 2 xfailed"与正确算术逐项一致**:186+21+2 = 209 = 本地 206 passed + 3 xfailed 总数闭合 ✅。按纪律:预期数字错误照实入账,不改写上文原文。


---

## R63(2026-09-13):用户 R62 审核裁决落盘 + BUG-32/33 修复(同一 source_file fail-closed 攻击族一次完成)

**输入**:用户 R62 裁决——R62 🟢 ACCEPTED;BUG-31 关闭保持;**BUG-32/33 批准修复(P0,同一攻击族)**;修复原则 = 显式失败、fail-closed、批处理隔离,禁 fallback、禁猜测(不把 123 当文件名)、禁 `str()` 强转、禁自动修正 manifest、禁降级 ADMITTED;修完做针对性对抗回归,**随即转 BUG-14-DATA**,不对 source_file 做无限边界枚举(BUG-31/32/33 = 完整攻击族,非新语义类别不再拆 BUG-34+)。

**修复面(三组件 + 三批入口,全部只加显式失败态)**:

1. **BUG-32 非字符串 provenance**:`isinstance(str)` 守卫——resolver → MISSING("source_file not a string … invalid provenance, fail-closed");QC `src_of` 折 `""` 哨兵 + check() C15 显式 FAIL("必需 provenance 无效…非字符串");F1 → DRIFT(note 显式)。
2. **BUG-33 源拒读(OSError)**:QC `src.read_text` 包 `except OSError` → C15 显式 FAIL("源文件不可读");F1 读源 + `read_bytes` 包 `except OSError` → DRIFT("source unreadable … fail-closed")。与 resolver R61 兜底层形成三层同族语义。
3. **批处理隔离(用户裁定原则落三个批入口)**:resolver `run()` `_safe` 逐文件兜底(异常 → `REJECTED_UNCOMPUTABLE`,即 C-IN-3 第五态 UNCOMPUTABLE);QC `main()` 逐文件兜底(异常 → 显式 FAIL 行);F1 `run()` 逐文件兜底(异常 → 显式 DRIFT 行)+ 输入门禁面 manifest 读取防崩(损坏 manifest 的 source 不入输入面,由 check_file 显式 DRIFT 承接)。
4. **顺带修复同族缺口(如实入账,非扩面)**:F1 `check_file` 快捷 DRIFT 返回缺 `n_units/n_match` 键 → `run()` 批汇总必 KeyError(R62 观测器只调 check_file 单件,未暴露批面);补齐键 + t9 钉算术完整性。

**对抗回归(R63,全部真实测试)**:

- **冻结武器零改动重放**:`scripts/r62_boundary_audit.py` 原样重放(仅重定向输出 → `data/r63_rerun_k_matrix.json`,R62 冻结工件未触碰),K1–K13 全矩阵:**crash_gaps=NONE**;K7–K10 CRASH_GAP:resolver,qc,f1 → NO_CRASH(MISSING/C15 FAIL/DRIFT);K12 CRASH_GAP:qc,f1 → NO_CRASH(条件 CreateFileW 独占句柄再次先实证 PRODUCIBLE(PermissionError) 后观测);K13 BATCH_KILLED → **BATCH_CONTINUED**{ADMITTED:1, MISSING:1}。
- **`scripts/r63_fix_verification.py`(一次性验证武器,`data/r63_fix_verification.json` overall=PASS)**:A 全矩阵零缺口 ✅ / B K2–K12 篡改件无一 ADMITTED(反洗白)✅ / C **K1–K6(R61 既有防线)before/after 逐态不变**(修复不得削弱旧防线)✅ / D 未篡改基线保持 ADMITTED/PASS/MATCH(修复不得误伤)✅。
- **义务钉转正**:`test_r62_t4`(strict xfail → 正式,参数化 int/dict/list/bool 四形态)、`test_r62_t5`(strict xfail → 正式,独占句柄条件先实证)全绿;新增 t6(resolver good+bad+good 批续行)/t7(坏 JSON → REJECTED_UNCOMPUTABLE)/t8(QC 批入口)/t9(F1 批入口 + 算术)。
- **变异咬合 13/13**(`.pytest_work/r63_mutation_driver.py`,全部 restored=True 逐字节还原):M1–M3 三组件类型守卫逐个回退、M4–M5 QC/F1 拒读守卫回退(re-raise)、M6–M8 三批入口隔离移除、M9 resolver R61 OSError 兜底回退 + R61 的 M4–M7 重放。

**审查工具自身缺陷/教训(如实入账)**:

- **F-r63-1(变异分辨率缺陷,当轮处置)**:首轮重跑 R61 驱动 M5/M6 **NO-BITE**——根因非防线漏洞,而是 BUG-33 新增 OSError 守卫把 is_file 守卫回退变异**等价补偿**(裁决仍 fail-closed,但裁决级断言分辨不出哪层在守)。处置:回归钉升级**消息级断言**(t1:QC 必须"非文件"族、F1 note 必须 "missing or not a file",不得被"不可读"族顶替),R61-M5/M6 重放恢复咬合。教训入 bugs.md:分层防御下回归钉必须带理由族断言。
- **武器脚本自身 bug**:r63 验证武器首版用短名(K2)索引全名行(K2_null)→ KeyError;当轮修复后重跑,结论不变。

**结果**:BUG-32/33 关闭(fix + 对抗回归 + 变异咬合三证);生产链三组件 + 三批入口 fail-closed 语义统一(C-FAIL-1 跨组件贯彻,未建大型公共异常框架——按用户裁定先最小修改);全量套件 **215 passed + 1 xfailed**(xfail = 锚点顺序义务钉;较 R62 的 206+3:新增 9 钉全过,t4/t5 两 xfail 转正)。下一项(用户排序)= **BUG-14-DATA**(未分类跑步机 + 73 重复源)。


### R63 收口(CI 实测,2026-09-13)

**CI Run 34745890960(headSha 62739e8,conclusion=success)日志原文"194 passed, 21 skipped, 1 xfailed"**。算术闭合:194+21+1 = 216 = 本地 215 passed + 1 xfailed;skip 21 = 19 corpus + 2 win-only(t3/t5,ubuntu 无 Windows 共享语义);win-only 两钉本地均真实通过(非 xfail)。R63 全链收口:修复 → 冻结武器重放 → 验证武器 PASS → 变异 13/13 → 全量本地绿 → CI 绿。下一项(用户排序)= BUG-14-DATA。

---

## R64(2026-09-13)BUG-14-DATA D0~D5:数据事实冻结与归因(只读,零修改生产数据)

**用户 R63 裁决落盘**:R63 PASS;BUG-31/32/33 攻击族正式关闭(不拆 BUG-34;唯一 xfail 保留不顺手处理);转 BUG-14-DATA,严格 D0→D5:"数据事实 → 分类归因 → identity fingerprint → 攻击 runner 边界 → 决定修复",**本轮不写清理/归并代码**;BUG-14-DATA 与 BUG-14-CHAIN 保持分账,不重编号。

**D0 冻结(武器 scripts/r64_data_inventory.py,只读+fail-closed+确定性)**:全库 md 4,881(源树 3,119 + 派生树 1,762)逐份冻结 path/basename/suffix/size/SHA-256/归一化 SHA-256/目录/derived/runner 分类/manifest 状态;口径对账全中台账(未分类 145 / 碰撞 73 组 146 文件 / PDF 索引 12,707);**新事实**:散落 高三/未分类 2 份、源树 manifest 为零(源文件身份=落位路径)、reclassify 搬移审计 698 条。工件:data/r64_corpus_inventory.json。

**D1 归因(145 → 机器可复现 buckets)**:141 NAME_RULE_COVERED(高考真题 125/合格考 15/学业水平 1;72 有孪生=回流件,69 无孪生=积压)+ 4 UNDETERMINED(高—笔误×2 / 高考适应性月考 / 初三越界,→ PENDING_REVIEW)+ 2 stray PLACEMENT_MISMATCH。**145 不是单一 bug,是 1 机制缺陷 + 4 类数据事实**。

**D2/D3 碰撞指纹与重复真实性**:73 组四层证据——SHA-256:6 组字节全同/67 组字节不同(两次独立 OCR);归一化层无新增;PDF 侧 73/73 exact stem 命中;**搬移审计 73/73 在册**。跑步机机制实锤:reclassify 搬移 → runner skip-check(batch_convert_pdf.py:118,身份=输出路径存在且>100B)落空 → 同一 PDF 重 OCR 回流(mtime 未分类份更晚 68/73)。**⚠ 根因更正:推翻旧登记"根目录+子目录各一份"**。语义层(哪份 canonical)一律 PENDING_REVIEW。

**D4 runner 边界攻击(tests/test_r64_data_inventory.py 14 钉全过,合成夹具零 API)**:身份=输出路径仅此而已(t11);搬移机制复现钉(t12);净化碰撞 a<b/a>b 同名静默跳过(t13);大小写歧义 exists 判真(win,t14);副本行为电池含高—/初三缺口钉(t10);runner/reclassify 源码锚防副本漂移(t8/t9);武器自身 fail-closed(非法 UTF-8 t6 / 独占句柄不可读 t7 win)+ 确定性(t1)。

**D5 修复决策(仅决策,未实施,待用户裁定)**:① 先修跑步机机制(skip-check 咨询搬移审计/自维护输出清单)——否则现在跑 reclassify 会触发 145 份重 OCR(烧配额+造新重复);② 机制修复后才谈周期 reclassify;③ 4 份规则缺口逐份裁定;④ 67 组孪生 canonical 语义裁定后才可去重;⑤ 2 份散落并入①。报告:reports/r64_bug14_data_d0_d5.md。

**对抗与质量**:武器变异 5/5 咬合(M1 fail-closed 移除/M2 bucket 守卫失效/M3 审计静默/M4 指纹判层放宽/M5 UTF-8 strict 放松),全部字节级还原;全量套件 **229 passed + 1 xfailed**(215+14 新钉;CI 预期 206 passed / 23 skipped / 1 xfailed = −19 corpus −4 win-only)。本轮零修改生产数据(只读审计;未跑 reclassify、未移动/删除/归并任何文件、未改 runner)。下一项待用户裁定(BUG-14-DATA 修复域 / 其余排序)。

### R64 收口(CI 实测,2026-09-13)

**F-r64-1(跨平台缺陷,CI 抓获,当轮修复)**:首轮 CI Run 34747603049(ubuntu)失败——reclassify_audit.jsonl 由 Windows 写入(反斜杠路径),武器 os.path.basename 在 POSIX 上不切 \ → 审计索引键错位、in_reclassify_audit 恒 False(t3 咬合;计数行"1 failed, 205 passed, 23 skipped, 1 xfailed"与预期算术 206-19-4 一致,即失败恰为 1)。修复:basename 前双分隔符归一(src.replace(chr(92), "/"));真实语料结论不变(重跑 audit_hit_groups 73/73、各项计数逐项相同,JSON 字节级还原免时间戳噪音)。教训:**跨平台审计武器对"另一平台 authored 的路径"必须显式归一分隔符;win-only 语义测试之外,反模式是假设 os.path 行为与产物来源平台一致**。

**收口:修复提交 857e3b9 → CI Run 34747741001 = success,日志原文 "206 passed, 23 skipped, 1 xfailed"**。算术闭合:206+23+1 = 230 = 本地 229 passed + 1 xfailed;skip 23 = 19 corpus + 4 win-only(R62 t3/t5 + R64 t7/t14,本地均真实通过非 xfail)。R64 全链:用户裁决落盘 → D0–D5 只读实测 → 14 钉 + 变异 5/5 → 台账 → CI 绿。main = 857e3b9(前序:d7d17d3 主提交 / 7ded519 D5 报告强收)。下一项待用户裁定(BUG-14-DATA 修复域:先修跑步机机制 → 周期 reclassify → 语义去重)。

**台账转写缺陷披露(F-r64-2,当轮修复)**:本轮 log.md 追加误用 PowerShell 双引号 here-string,反引号转义吞掉行内代码标记,且 `r 被转义为 CR 致 L1558 处 reclassify 首字母丢失。机械修复:CR 还原为字母 r(diff 仅 1 行,无任何主张改动);被吞反引号仅为格式损失,文字与数字未损,不回填以免二次噪音。教训:向 log.md 追加含反引号/反斜杠的内容必须用单引号 here-string(@'...'@)或文件写入工具。

---

## R65(2026-09-13)对抗性审查:R64 全部结论独立复证(用户令:严格审查,不降标准、不圆场)

**方法**:审查武器 scripts/r65_r64_review.py(只读;A 三 JSON 交叉一致性+逐行独立重判 / B 文件系统全量重哈希 / C OCR 日志级物证+审计路径交叉 / D PDF 唯一性独立重算 / E 提交武器可重现性)+ 脚本外:变异独立复跑、套件重跑、CI 日志 skip 逐节点枚举。证据:data/r65_r64_review.json + reports/r65_r64_adversarial_review.md。

**复证结果:R64 十一项主张全部成立**。要点:① D1 逐行独立重判 147/147 一致(141/4/2;72/69 拆分;143 带(N));② D2 指纹标记独立重算零偏差(6/67);③ PDF 独立索引 {1:73} 坐实旧登记"根+子目录各一份"对碰撞集确属错误;④ 审计 73/73 from/to 路径与实际成员逐组吻合;⑤ 冻结 4881 份全量重哈希 0 变化 0 缺失(零修改生产数据成立);⑥ E 段现跑=提交 JSON records 零差异(REPRODUCIBLE);⑦ 变异 5/5 独立复跑咬合字节还原;⑧ CI skip 枚举 23 = 19 corpus + 4 win-only 逐节点点名闭合。

**跑步机机制证据升级(结构推断 → 日志级直接证明)**:68/73 碰撞组期望输出路径在 ocr_batch_log.txt 被处理 ≥2 次(0 单次/5 窗口外零次);67/73 回流侧写入 mtime 与日志时间戳 ±6h 吻合;抽样人工核对原始行(资本主义制度的确立(三)(1).pdf 09-06 12:22:25 与 09-10 21:27:45 两次处理同落 未分类/历史,第二次与 mtime 秒级一致);6 组字节全同者 6/6 亦双次处理(字节同源于 OCR 输出确定性,非复制)。措辞收紧:62/67 字节不同组有日志双次直接证明,5/67(09-11/09-12 日志窗口外写入,未识别进程)维持强推断并如实标注无直接证明,机制结论不变。

**审查发现 3 项,全部当轮处置**:F-r65-1(轻微)D0"全库"口径遗漏 Ocr-markdown 根级 README.md(非语料)→ 修复=meta 点名披露 + t16 钉 + M7 咬合;F-r65-2 审查工具日志匹配两次自纠(日志行 filename[:50] 截断且为 PDF 名;v1 61DIRECT/v2 6DIRECT 均误,v3 67DIRECT 经原始行抽验+双次统计复证;中间错误数字未被采用)——教训:**对截断日志的匹配必须按截断规则构造期望串,扩展名替换先于截断**;F-r65-3 classify_unknown_file 全局索引未构建时静默空孪生证据(python 进程实测)→ 修复=显式 RuntimeError + t15 钉 + M6 咬合,对已发布证据无影响(A4 独立重算吻合)。

**结果**:R64 复证成立;修复变异 2/2 咬合;全量套件 **231 passed + 1 xfailed**(229+2 新钉;CI 预期 208 passed / 23 skipped / 1 xfailed = −19 corpus −4 win-only)。R64 D5 修复决策维持,待用户裁定。

### R65 收口(CI 实测,2026-09-13)

**提交 7122765 → CI Run 34750043799 = success,日志原文 "208 passed, 23 skipped, 1 xfailed"**。算术闭合:208+23+1 = 232 = 本地 231 passed + 1 xfailed;skip 23 = 19 corpus + 4 win-only(R62 t3/t5 + R64 t7/t14),本轮前已逐节点点名枚举。main = 7122765。R65 审查全链收口:审查武器 → 11 主张复证 → 3 发现当轮修复+咬合 → 台账 → CI 绿。下一项待用户裁定(R64 D5:先修跑步机机制 → 周期 reclassify → 语义去重)。

---

## R66(2026-09-13):BUG-14-DATA D5-A — 跑步机切断机制修复(R-OHM-1)+ 修复前冻结快照

**输入**:用户 R65 裁决落盘——R65 PASS 收口;D5 协议冻结为 **D5-A 停跑步机 → D5-B 全量 reclassify 一次 → D5-C 幂等复跑 → D5-D 重审计 → D5-E 语义去重**;本轮只做 D5-A + 修复前冻结快照,不碰语义去重/canonical identity/BUG-14-CHAIN。证据分层裁定同步冻结:62/67 字节不同组=日志直接证明、5/67=强推断(日志窗口外)、6/6 字节相同组=重复处理证据(非复制证据)。

### 修复前冻结快照(先于任何代码改动)

武器 `scripts/r66_d5a_snapshot_check.py`(确定性、无时间戳、只读,复用 r64 采集/哈希实现):baseline = R64 D0 冻结清单(R65 已复证)。实测 **4,881/4,881,changed=0/missing=0/new=0**,corpus_digest = `6940f2ec…21f8d`;身份口径 (rel_path,size,sha256,norm_sha256),mtime 不入身份,根级 md 单独点名(F-r65-1 口径)。daemon 静默:ocr_batch_log 停笔于 09-10 21:27:45,快照前后 mtime 不变;两个 09-10 启动的 python 进程未杀(用户进程),如实披露。

### 机制修复(治理先行,先登记后实现)

1. `governance/rule_registry.md` §7 新增 **R-OHM-1**(FACT_INTEGRITY+EVIDENCE)+ runner R25 冻结的**限定解冻声明**;CI 双向钉在册。
2. 新模块 `ocr_service/output_manifest.py`(纯 stdlib):append-only JSONL 清单(source_rel/size/sha256/output_rel/written_at/pages,先校验后写+fsync);`decide_skip` 保留既有 EXISTS(>100B)语义,期望输出落空时查清单:**同 source(size+sha256 级)已在册 → MANIFEST_DONE skip**;坏行/缺键 → ManifestError → runner SystemExit(2)(fail-closed,禁静默降级重跑);路径键正斜杠归一(F-r64-1)。
3. runner 4 处接线:清单载入 fail-closed / decide_skip 替换旧 exists / `[DECIDE:<reason>]` 显式留证(EXISTS 保持静默)/ 成功写出即记账(清单故障=FATAL)。process_pdf 主体与 OCR API 语义零改动。
4. **设计裁定(自 caught,如实入账)**:MANIFEST_DONE 首版要求"记录输出仍在原位"——但跑步机场景恰是已被搬走,分支永不命中,切不断回流;修正为 sha 级已处理即 skip,记录输出现状(present/missing-or-moved)只入日志留证。**输出丢失不自动重跑**(auto-fix 禁;重跑权在人,删清单记录=显式授权,t4 实测恢复重跑)。

### 测试与对抗(全部真实执行)

- `tests/test_r66_treadmill_fix.py` **10 钉全绿**;核心 t2 跑**真实 main()**(仅 stub process_pdf,零 API):OCR→记账→模拟 reclassify 搬移→二轮 main() → MANIFEST_DONE skip、stub 调用保持 1、未分类零回流。CI 无 requests/urllib3 → import 级 stub(测试禁网),如实披露。
- 变异 **5/5 BITE 全部字节还原**(M1 skip 拆除/M2 坏行静默/M3 接线回退/M4 sha 拆除/M5 append 校验拆除);快照武器阳性控制 t10(篡改必入 changed/幽灵 missing/新文件 new)。
- 全量套件 **241 passed + 1 xfailed**(231+10)。
- **修复后快照重跑与修复前逐字节一致**(sha256 93E77E86…16EF 前后相同,corpus_digest 不变)→ 机器证据:本轮零触碰语料。

### 边界(如实)

- runner 本体未真实执行(不调 OCR API);证据等级 = 真实 main() 集成 + 源码锚 + 变异咬合。现存两个 09-10 进程持旧代码,修复对其无效,**需用户重启 daemon 生效**;清单从零开始,首跑不改变既有 skip 结构(在位产出照旧 EXISTS),之后逐份记账。
- D5-B/C/D/E 本轮不启动;reclassify --apply 仍未运行过。

报告 `reports/r66_d5a_treadmill_fix.md`;证据 `data/r66_d5a_snapshot_check.json`。

### R66 收口(CI 实测,2026-09-13)

**F-r66-1(测试线缺陷,CI 抓获,当轮修复)**:首轮 CI Run 34752098948(8f8ef26,ubuntu)失败——`_stub_optional_deps` 不幂等:首测注入 spec-less stub 后,后续调用 `importlib.util.find_spec("requests")` 对 `__spec__ is None` 模块抛 ValueError(4 failed,214 passed,23 skipped,1 xfailed;本地装有 requests 走不到该分支,属 CI-only 路径未本地覆盖)。修复 = 成员检查先行 + ValueError 防御(`_ensure_stub`),本地以 CI 形态 subprocess 复现验证("OK: idempotent, no ValueError")+ t11 回归钉(spec-less 短路)。**缺陷属测试线,机制代码(output_manifest/runner)零改动;失败计数算术自洽:214+4+23+1=242=本地 241+1。**

**收口**:修复提交 aa9065f → **CI Run 34752741370 = success,日志原文 "219 passed, 23 skipped, 1 xfailed"**。算术闭合:219+23+1 = 243 = 本地 242 passed + 1 xfailed(242−23 skip=219;skip 23 = 19 corpus + 4 win-only,历轮已逐节点点名)。main = aa9065f(前序:8f8ef26 D5-A 主体)。R66 全链:修复前快照 → 登记 → 机制实现 → 10+1 钉 → 变异 5/5 → 修复后快照字节一致 → 台账 → CI 绿。**下一步待用户:重启 daemon(修复生效)→ 观察首跑 → D5-B 全量 reclassify(生效前禁止)。**

---

## R66.1(2026-09-13):D5-A 生效验收(Runtime Activation Verification)
**输入**:用户 R66 裁定 = PASS(code-level complete,**runtime activation pending**);明令下一步只做 R66.1 三项(进程归属 / 首次真实运行 / 二次扫描零 OCR),**证据拿到前禁止 D5-B**;并裁定 manifest 语义必须写死为 processing history(≠ output availability index)。

### 进程取证与旧 daemon 终止(A 前半)
Get-CimInstance 命令行 + Get-Process 实测:PID 38160 = `python ocr_watchdog.py`(09-10 21:21 启动)→ PID 33036 = runner `batch_convert_pdf.py`(21:27 拉起),均 Python312 解释器、持旧代码;PID 42124 = hermes 网关,无关未触碰。**runner 卡死实锤**:ocr_batch_log 停笔于 09-10 21:27:45(75/12703,当日 6481/20000 页),进程存活 2.7 天零输出。终止顺序先看门狗后 runner(防 5 分钟自动重拉),BOTH DEAD 确认。**今日配额 293 页矛盾排查**:page_usage mtime=09-13 01:11:38 与 reslice-pac 26 个 pac-c*.md 写入时间(01:11:22–01:11:38)完全吻合 → 系 reslice-pac 流水线自身 OCR 所耗,非 daemon。

### 激活前预检(只读,发现清单引导缺口)
武器 `scripts/r66_1_preflight.py` + `r66_1_victim_split.py`。全量 12,703 PDF,EXISTS 在位 skip 仅 2,421;**清单从零开始 → 首扫将真实 OCR 10,282 份(20.2 GB)**。拆分(md 名==sanitize_stem 精确等值,runner 自身输出路径语义,非语义去重):**625 份跑步机受害者候选**(语料已有同名 md=历史已处理、输出被搬走,重 OCR=重复+污染)+ **9,657 份从未处理**(daemon 本职,配额闸门约束)。结论:**直启看门狗 ≠ 最小验证,生产重启暂停,待用户裁决引导策略**(甲 审计记录回填 manifest=证据级引导 / 乙 接受直启如实入账 / 丙 维持停机先做引导工具)。证据 `data/r66_1_preflight.json` / `r66_1_victim_split.json`。

### 受控激活验证(B/C,真实 runner + 真实 OCR API + 沙箱根,生产代码零改动)
武器 `scripts/r66_1_activation_driver.py`:import 真实 batch_convert_pdf,仅进程内重定向 PDF_ROOT/OUTPUT_ROOT/MANIFEST_FILE/LOG_FILE 至 `.pytest_work\r66_1_activation`;**PAGE_USAGE_FILE 保持生产路径,真实页数诚实入账**;source = 真实 PDF 沙箱副本(西城高二地理参考答案,228,485B,sha256 dd239c…);Ocr-markdown 零写入。实测 4/4:
- **P1 首跑**:`[DECIDE:NO_MANIFEST_ENTRY]` → 真实 OCR `[OK] 2 pages` → output 写出 + manifest 0→1(含 source_sha256/pages);配额 293→295;
- **P2 复扫(在位)**:EXISTS 静默 skip,manifest 字节不变,零 OCR;
- **P3 搬移复扫(模拟 reclassify)**:**`[DECIDE:MANIFEST_DONE]`(recorded_output_status="missing-or-moved")→ 零 OCR、零回流、manifest 不变——跑步机切断在真实运行时的直接证据**(t2 测试用 stub,此处真实 API 闭环);
- **P4 归位**:manifest 不变。
证据全文 `data/r66_1_activation_evidence.json`。

### 语义边界写死(用户 R66 裁定 §4)
`output_manifest.py` 模块头 + 登记册 §7 增补:manifest = **processing history / execution ledger**(证明"该 source 已成功执行过 OCR"),**不是 output availability index**;禁止未来以"恢复丢失输出"为由给 output-missing 加自动重跑 fallback(丢失输出恢复 = 人工删清单记录,显式授权)。

### 结果与边界
全量回归 **242 passed + 1 xfailed**(与 R66 收口态一致,零回退)。**R66.1 = B/C 受控通过、A(生产 daemon 重启+新代码进程归属)暂停待用户裁决;D5-B 继续禁止**。625/9,657 拆分是风险预检口径,不构成逐份"已处理"裁定;引导回填若实施须逐份日志证据 + 新轮治理(登记+测试+变异)。报告 `reports/r66_1_activation.md`。

---

## R67 设计轮(2026-09-13):Manifest 审计级引导 DESIGN ONLY + daemon「跑飞」归因
**输入**:用户先裁决路线甲(审计回填),随即指令改为**先出设计、勿实施**;并要求回答 daemon 为何会跑飞。
**归因(报告 §一)**:旧 daemon 并未跑飞——是**卡死**(runner 日志冻结于 09-10 21:27:45 / 75/12703,进程存活 2.7 天零输出);「跑飞」是直启的前瞻风险,三层成因:① 清单冷启动语义(R-OHM-1 只保护记账之后,manifest 从零开始);② 历史搬移存量(跑步机遗产);③ 9,657 份从未处理 = daemon 本职(配额闸门内,非故障)。
**探针实测(只读,`scripts/_r67_design_probe.py`)**:审计 698 条 from→to **698/698 全匹配**——from 恰为唯一 PDF 的 runner 期望输出(共享歧义 0),to 全部在位;**但 625 首扫候选中仅 1 份期望输出 ∈ 审计 from 集**(697/698 审计源当前期望输出在位=已被跑步机回填,EXISTS skip)。**设计含义:审计回填的受益时点是 D5-B 再次搬移被 MANIFEST_DONE 拦截,不是首扫;625 无证明者禁止推断回填(禁 stem 级身份/禁 fallback)。**
**设计落盘** `reports/r67_manifest_bootstrap_design.md`:工具形态(离线、默认 dry-run、--apply 显式)、匹配规则(完整路径等值,歧义/to 缺失 fail-closed 入 excluded 桶)、条目 schema(provenance=r63-audit-bootstrap + processed_at unknown + pages 0 之代价如实披露)、五 fail-closed 点、幂等、与生产激活的顺序契约、测试 9 项 + 变异 5 项计划。**四个用户决策点待裁决:① pages 未知表达(0 vs -1 哨兵);② written_at=写入时刻+processed_at unknown;③ 625 首扫候选处置(接受重跑/逐份裁定/日志考古扩展探针);④ apply 时机。**
**边界**:零实施、零生产写入;探针只读;698/698 是当下对账,apply 前语料若变动须重跑探针。

---

## R67 实施轮(2026-09-13):Bootstrap 工具落地(dry-run 为止,apply 待批)+ F-r67-1
**输入**:用户冻结五项裁决(pages nullable+provenance 禁-1禁假0 / 时间字段 recorded_at 语义不冒充 processed_at / 625 先日志考古 A-B-C 分桶 / apply=dry-run+diff 人工批准 / **bootstrap 禁覆盖已有 manifest**);原则"manifest 是事实账本,不是推测账本"。
**实施**:
1. 登记册 §7 R-OHM-1 行增补 R67 扩展(schema/覆盖禁令/无证据不入账);`output_manifest.validate_entry` 扩展:pages 允许 null **仅当 provenance 在场**(t8 双向钉:合法/无出处拒绝/字符串拒绝)。
2. 新工具 `scripts/r67_manifest_bootstrap.py`:证据源仅两种——① R63 审计(from==唯一 PDF 期望输出、完整路径等值、to 在位>100B;歧义/未匹配/to 缺失 fail-closed 入 excluded);② OCR 日志考古(按 F-r65-2 截断规则构造 `[ts] [i/total] grade/subject/{fn[:50]}...`+`[OK] N pages`,fragment 全量歧义统计,歧义/无 OK → B 类 PENDING_REVIEW 只入报告);无同名 md 者不 seed(其首扫重跑=有价值的数据恢复,如实放行)。**禁覆盖**:source_rel 已在册 → 跳过计数,绝不修改;幂等:二次 apply 追加 0。条目:written_at=记录写入时刻(recorded_at 语义)、processed_at 恒 null(OCR 时刻本轮未提取,不用 written_at 冒充)、provenance ∈ {r63-audit-bootstrap, ocr-log-archaeology}、审计行号/日志 OK 行号留证。
3. **测试 13 钉全绿**(`tests/test_r67_bootstrap.py`;t5 净化碰撞用 monkeypatch 合成——Windows 禁用字符造不出真实碰撞,如实披露;t13 真实语料冒烟 corpus 门控);**变异 5/5 BITE 字节还原**(M1 null无出处放行/M2 禁覆盖拆除/M3 匹配放宽/M4 fragment 歧义拆除/M5 dry-run 偷偷落盘);全量套件 **255 passed + 1 xfailed**(242+13)。
4. **真实语料 dry-run(零落盘)**:`planned=698,全部 provenance=r63-audit-bootstrap,excluded=0,B_pending=0,already_in_manifest=0`;日志富化 698/698 补到真实页数(pages null=0);报告 `data/r67_bootstrap_report.json`。**apply 未执行,待用户审 diff 授权**。
**⚠ F-r67-1(当轮自查更正,结论反转)**:设计轮探针 `_r67_design_probe.py` 的统计循环 `hit += 1; break` 早退,把 **625/625 审计可证** 误报为"仅 1 份";由此设计轮"审计回填只保 D5-B 不保首扫"的说法**作废**。修正探针复证 625/625,与 dry-run(624 受害者全经审计入账、B=0;差 1 份系 md 索引按口径排除 reslice 试验目录,其 source 仍作为审计源入账)一致。**更正后结论:审计回填同时保护首扫(重 OCR 规模 10,282 → ~9,658)与 D5-B 搬移拦截**。教训与 F-r65-2 同族:审计统计禁止 early-break,计数必须穷举。
**边界**:manifest 生产文件未创建、daemon 未重启、D5-B 未跑;下一动作 = 用户审 698 条 diff(data/r67_bootstrap_report.json)→ 授权 apply → daemon 激活验收 → D5-B。

---

## R67 闸门轮(2026-09-13):双向一致性复核 + preview/hash guard(apply 仍未授权)
**输入**:用户 R67 裁决——设计/实现/dry-run/mutation/CI 五项 PASS,但 **apply 暂不批准**;前置两检查:① 698 条 bootstrap↔审计源**双向一致性复核**(PDF 路径/输出路径/sha256/pages 四字段逐项);② 生成**不可变 apply preview + hash guard**(base manifest sha + entries sha,漂移即拒);顺序冻结 apply→daemon→D5-B,禁先 D5-B;措辞谨慎化:剩余 ~9,658 是**未处理 source 而非错误 source**,只写"bootstrap 消除约 625 个历史搬移受害源的重复 OCR 风险,其余由真实 runner 决定"。
**实施**:
1. **preview/hash guard**(工具内):`--preview` 冻结 written_at + 双指纹(base_manifest_sha256,manifest 不存在=None,区别于空文件;entries_sha256=canonical JSON sha256);`--apply` 必须有未漂移 preview,否则 BootstrapError 显式拒绝零写入——防"dry-run 后语料/清单被改,旧 diff 写入新状态"。
2. **双向闸门武器** `scripts/r67_apply_gate.py`:枚举/净化/年级科目/路径归一/哈希/日志解析**全部独立重推**(不复用 bootstrap 推导,G-AUDTB-1 精神);forward(审计→条目,逐行恰一条)+ backward(条目→审计行合法且 to 一致)+ 四字段逐项;log-archaeology 条目单列核日志。
3. **F-r67-2(闸门首跑抓获,当轮修复)**:闸门初版把"日志行多次出现"(跑步机双次处理的正常证据)误当归属歧义 → 129 处 PAGES 假错配;修正为候选侧两个 PDF 共享 fragment 才算歧义、多次出现取最近一次 [OK](与 bootstrap 同语义、独立实现)。修正后真实语料 **consistent=True:698/698 双向一致、forward_missing=0、forward_dup=0、mismatches=0**。
4. **测试 19 钉全绿**(新增 t14 preview 确定性/t15 base 漂移拒/t16 规划漂移拒/t17 无 preview 拒/t18 闸门咬住错误 bootstrap 输出/t19 闸门咬住 forward 缺口);**变异 9/9 BITE 字节还原**(M6 base 指纹拆除/M7 entries 指纹拆除/M8 闸门 sha 比对拆除/M9 forward 静默);全量 **261 passed + 1 xfailed**。
5. **真实语料 preview 已生成**(`data/r67_manifest_apply_preview.json`):append_count=698,base_manifest_sha256=null(manifest 仍不存在),entries_sha256=7e197088…1246;闸门报告 `data/r67_apply_gate_report.json`。
**边界**:apply 未执行、manifest 生产文件不存在、daemon 未重启、D5-B 未跑。剩余动作等用户批准:`--apply`(将校验 preview 未漂移)→ daemon 激活验收 → D5-B。

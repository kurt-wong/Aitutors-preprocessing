# PRD · 智能题库预处理（LLM 重切）

> **冻结文档**：本文件是项目的规格基准（single source of truth）。背景、结构、数据契约、
> 实现逻辑以本文为准；`status.md` 记录进度快照，`log.md` 记录逐轮变更，`bugs.md` 记录缺陷与修复，
> `README.md` 只做目录导航。
> 冻结日期：2026-09-10 · 最近规格校准：2026-09-15(项目定位重校准,charter §12) · 负责人：Kurt

---

## 文档体系与维护规则

**五份根文档分工**：`prd.md`（规格冻结，唯一基准）· `status.md`（进度快照）· `log.md`（变更日志）· `bugs.md`（缺陷记录）· `README.md`（目录导航）。

**更新规则（状态/变更类文档，务必遵守）**
1. **追加式**：变更/状态记录一律**流式追加到文档末尾**，**不重写、不置顶、不倒序**；最新记录永远在文末。
2. **时间戳**：每条记录带**当前时间戳**，格式 `YYYY-MM-DD HH:MM`（24h）。回填的历史条目无精确时刻者标 `(时刻从略)`。
3. **不可变**：已写入的历史条目不改写；纠错用追加「更正」条目，不覆盖旧条目。
4. **编号递增**：轮次 `R{n}`、缺陷 `BUG-{nn}` 单调递增，只在文末新增。
5. `prd.md` 为规格基准，仅在规格变更时改动（非追加式日志）；`README.md` 为导航，随时可更新。

---

## 0. 文档目的

把北京高中试卷扫描 PDF，稳定地转成**可验证、可定位、可追溯的 Source Evidence(Document Evidence Manifest)**，
供 V3 `Source → Evidence → Resolver/IR → Gate → Admission` 链路消费。**preprocessing 不负责生产最终 Question/Instance**。

本 PRD 冻结：目标与非目标、核心概念、系统架构、数据契约、批注规则、各模块实现逻辑、质检体系、已知局限、路线图。

---

## 1. 项目背景与目标

### 1.1 业务背景
题库需要"完整可解的题"作为入库单元（题干＋选项＋配图/表格＋标准答案＋详解可选）。原始资料是扫描版
试卷 PDF，需先 OCR 成 Markdown，再把线性文本**切分成题目单元**并打上结构化元数据。

### 1.2 核心目标
> **【2026-09-15 项目定位重校准,详见 `governance/phase_p2_charter.md` §12】**
> preprocessing = **Source Evidence Producer**:从异构考试文档生产可验证、可定位、可追溯的
> **Source Evidence(Document Evidence Manifest)**,作为 V3 `Source → Evidence → Resolver/IR → Gate → Admission`
> 链路的上游事实输入。**不负责**把这些事实解释为最终知识资产(Question/Instance)。
>
> **preprocessing:原文有什么、在哪里。V3:它意味着什么、能不能进知识库。**
> (精确版:preprocessing 发现并表达"文档中的结构事实";V3 把结构事实解释为领域语义并决定是否准入。)

1. **保真**：批注绝不改写、生成题目内容，只插入锚点元数据（`去锚点 == 源文件原文`）。
2. **完整**：每个入库单元是完整可解的题；综合题（共享材料）整合为一个原子单元，子题/答案齐全。
3. **可溯源**：一切产出都能回指到源 `.md` 的具体行号；一切源修复都确定性、可回滚。
4. **可规模化**：从 16 份试点扩展到全库 ~3120 份，流程可断点续跑、可回归校验。

**已实证的 Evidence 类型(P3 冻结候选)**:`source_identity` / `producer_provenance` / `unit_boundary` /
`question_numbers` / `unit_type` / `stem_region` / `options_region` / `answer_evidence` /
`explanation_region` / `material_region` / `figure_reference`。provenance 保持轻量
(`source_hash`/`manifest_version`/`producer_version`/`generated_at`),不建版本图/血缘平台/事件溯源。

### 1.3 非目标（明确不做）
- **不判答案对错**，只判结构与完整性。
- **LLM 不誊写正文**，只输出行号引用（消除幻觉污染正文的风险）。
- **不做本地小模型训练**（早期"BERT+Span+CRF"路线已废弃，见 §12 决策记录）。
- 卷面指令（"本大题共X小题""请在答题卡作答"）不入库；解题必需的作答要求保留。
- **【2026-09-15 §12 Boundary 2】不做 V3 语义/准入职责**:Question canonicalization / dedup /
  similarity·family / knowledge mapping / canonical Question identity / QuestionInstance identity /
  Admission·Gate decision / semantic correctness judgment / V3 domain lifecycle。
  不得因为 preprocessing"知道两道题一样"就在此合并 Question。
- **【2026-09-15 §12.7】不规划仓库合并**:preprocessing 与 V3 保持独立仓库,只验证 Evidence Producer →
  V3 Consumer 稳定接口;合并/嵌入/独立**依据真实维护成本决定,不提前设计**(不设计 monorepo /
  domains/preprocessing / internal package migration / service extraction)。

---

## 2. 核心概念与术语

### 2.1 数据分层
| 层 | 载体 | 定位 |
|---|---|---|
| 原始 | `maintainess\PDF\*.pdf` | OCR 输入源 |
| **源 markdown** | `Ocr-markdown\{年级}\{科目}\*.md` | **一切的 ground truth**；源修复的目标对象 |
| 锚点批注 | `*.annotated.md` | **本质产物**：源原文逐行不动 + META 注释锚点 |
| 清单 | `*.manifest.json` | 纯行号引用的结构化元数据（供 Resolver/入库） |
| 切片视图 | `*.md`（resliced-pilot 内） | 仅供人工查看的展示视图，非批注正文 |
| 图片库 | `Ocr-markdown\_imgs\{文件名}\` | 从 PDF 坐标裁剪恢复的配图 + manifest |

### 2.2 题目单元模型
- **standalone_question**：无共享材料的独立题，一个单元 = 题干＋选项（选择题）＋配图/表格＋答案（＋详解可选）。
- **composite_question**：若干小题共享同一段前置材料（文言文/现代文阅读、英语阅读/完形/语法填空/七选五、
  理化实验、工艺流程、材料题……脱离材料无法作答）。**整块就是一道题，不拆子题**。
- **嵌套**：composite 中 `material ⊆ questions`（材料是题目区的前段/内段；完形填空里带空格的文章本身即题目）。

### 2.3 角色（role）与锚点
单元由若干"角色区间"组成，每个区间用一对 META 注释锚点包裹：
| 角色 | 深度 | 含义 | 适用 |
|---|---|---|---|
| `unit` | 0 | 单元包络（**只圈题干主体**，不含答案/详解/extra） | 全部 |
| `questions` | 1 | composite 的整块题目区 | composite |
| `material` | 2 | composite 的材料/文章（嵌套在 questions 内） | composite |
| `stem` | 1 | 题干 | standalone |
| `options` | 1 | 选项 | standalone |
| `answer` | 1 | 答案区（【评分标准】并入此区） | 全部 |
| `explanation` | 1 | 详解区（【分析】【解答】【点评】等） | 可选 |
| `extra` | 1 | **卫星锚**：配图/表格因排版漂移到题干区之外时的归属标注（不撑大 unit 包络） | 可选 |

> **extra 语义要点**：如题9的图被排到题11之后，图行放 `extra_lines`；若让它撑大包络，会把平级的题10/11吞进来。
> 因此 unit 包络只由 material/stem/options/questions 撑起，extra 靠题号标签单独标注归属。

---

## 3. 系统架构与数据流

### 3.1 端到端流水线
```
原始 PDF
 → ① OCR(PaddleOCR-VL-1.6 API)                → 源 .md
 → ② 源修复(去双重识别 / 裸LaTeX包$ / 补丢图丢行) → 干净源 .md
 → ③ LLM 重切(mimo-x-pro-preview, 只输出行号)    → units(行号引用)
 → ④ 确定性校验 + 编译                          → manifest + .annotated.md + 切片.md
 → ⑤ QC(C1–C10) + 渲染质检 + 人工签核            → 题库
```

### 3.2 目录结构
| 目录 | 内容 |
|---|---|
| `Ocr-markdown\` | 核心数据（勿动）：源 md、`auto-annotated-v6\`(旧)、`resliced-pilot\`(试点)、`_imgs\` |
| `maintainess\` | 待转换区：`PDF\`(OCR 源)、DOCX、待转换DOC |
| `original\` | 原始资料（五三资料等） |
| `scripts\` | 全部项目脚本 |
| `ocr_service\` | OCR 转换服务（守护进程 + 批量转换 + 计划任务） |
| `logs\` `data\` | 运行日志 / 运行数据与状态（含 `.llm_config`） |
| `reports\` | 分析报告与渲染预览 |
| `_archive\` | 归档（可回溯，勿删） |

### 3.3 脚本索引（现役）
| 脚本 | 层 | 职责 |
|---|---|---|
| `ocr_service\batch_convert_pdf.py` | ① | PDF→OCR MD（带每日页额度） |
| `ocr_service\ocr_watchdog.py` | ① | 守护：0:00 重置额度、达限停、跨日续 |
| `scripts\corpus_scan.py` | ② | 全库源缺陷量化（只读） |
| `scripts\fix_bare_latex.py` | ② | 裸 LaTeX 自动包 `$`（确定性、可回滚） |
| `scripts\recover_images.py` | ② | PDF 坐标裁剪恢复配图（PyMuPDF，幂等） |
| `scripts\pdf_fidelity.py` | ② | PDF 文本层 vs 源覆盖率（**仅粗筛**，见 §10） |
| `scripts\reslice_pipeline.py` | ③④ | **LLM 重切主线**：行号化→LLM→校验→三产出 |
| `scripts\reslice_qc.py` | ⑤ | 重切产出回归质检 C1–C10 |
| `scripts\render_lint.py` | ⑤ | LaTeX/HTML 结构渲染风险静态检测 |
| `scripts\render_preview.py` | ⑤ | 源 MD→独立 HTML（KaTeX+mhchem），供人眼比对 PDF |
| `scripts\prereview_check.py` | (旧) | v6 预审；**仅其 `normalize_qnum`/`parse_answer_tables`/`parse_range_answers` 三 helper 被重切复用** |

---

## 4. 数据契约（冻结）

### 4.1 源 markdown
- 每份由 OCR 分页拼接，页间分隔符 `---`；图片引用 `![](imgs/xxx_box_x0_y0_x1_y1.jpg)`（引用名内嵌版面框坐标）。
- 源是唯一 ground truth：修复、批注、校验全部相对它进行。

### 4.2 manifest JSON schema
```jsonc
{
  "source_file": "绝对路径.md",
  "model": "mimo-x-pro-preview",
  "annotation_meta": {
    "prompt_version": "reslice-pilot-v2.1",
    "validation_issues": [],          // 确定性校验的硬问题（应为空）
    "warnings": []                     // 分节重号/自动补号等软提示
  },
  "units": [
    { // standalone_question
      "unit_id": "Q1",
      "unit_type": "standalone_question",
      "question_numbers": [1],
      "original_question_type": "single_choice",   // 见附录 A（12 类）
      "stem_lines":     [起, 止],   // 或 null
      "options_lines":  [起, 止],   // 或 null
      "extra_lines":    [起, 止],   // 或 null
      "answer_lines":   [起, 止],   // 必填（校验强制非 null）
      "explanation_lines": [起, 止] // 或 null
    },
    { // composite_question
      "unit_id": "U2-5",
      "unit_type": "composite_question",
      "question_numbers": [2,3,4,5],
      "original_question_type": "reading",
      "material_lines":  [起, 止],   // ⊆ questions_lines
      "questions_lines": [起, 止],
      "answer_lines":    [起, 止],
      "explanation_lines": [起, 止]  // 或 null
    }
  ]
}
```
- 所有行号为**源 md 的 1-based 行号**；区间 `[起, 止]` 闭区间，须落在 `[1, n_lines]` 且 `起 ≤ 止`。
- manifest **不含任何正文**。

### 4.3 锚点批注格式（.annotated.md）
- 文档头：
  ```
  <!-- META:annotation:start -->
  <!-- META:doc:source={名}, model={模型}, prompt=reslice-pilot-v2.1 -->
  <!-- META:annotation:end -->
  ```
- 单元锚点（就地插在源原文行之间，源行一字不动）：
  ```
  <!-- META:unit:start:Q1 type=standalone_question q=1 -->   // 开：深度升序（外先开）
  …源原文行…
  <!-- META:stem:start:1 --> … <!-- META:stem:end:1 -->
  <!-- META:answer:start:1 --> … <!-- META:answer:end:1 -->
  <!-- META:unit:end:Q1 -->                                   // 闭：深度降序（内先关）
  ```
- **保真不变量**：`.annotated.md` 去掉所有 `<!-- META:…` 行后，逐行 == 源文件（QC C8 强制）。

### 4.4 区间语义与嵌套
- 开锚点按深度升序（unit0 → questions1 → material2）；闭锚点按深度降序（material2 → questions1 → unit0）。
- `material ⊆ questions`；`unit` 包络 = material/stem/options/questions 的并区间（**不含** answer/explanation/extra）。
- 共享答案表（45 题答案表、"1-5 ACDBA" 区间连写）在切片视图里**按题号取值、不整段回引**，避免重复；manifest 用行号引用原样保留。

---

## 5. 批注根本规则（R1–R12，与用户逐条确认）

1. **R1** 入库单元 = 完整可解的题：题干＋选项（选择）＋配图/表格＋标准答案（详解可选）。
2. **R2** 共享前置材料 ⇒ 整合为一道综合题（composite）：材料＋全部子题＋全部子题答案。
3. **R3** 答案区跟随综合题，逐小题答案齐全；**【评分标准】并入答案区**。
4. **R4** 子题逐题齐全，缺一个 = 严重问题。
5. **R5** 表格必须保留（Markdown/HTML 表格），缺失 = 严重问题。
6. **R6** 图片保留（`[img]` 占位 + 锚点即可；源已带 `_imgs` 实链，等价满足）。
7. **R7** 作文算完整题（题干要求＋范文即答案）。
8. **R8** 不判答案对错，只判结构/完整性。
9. **R9** 卷面指令不入库（"本大题共X小题""请在答题卡作答""考试时间/满分/注意事项"）；解题必需要求（"任选三小题""保留两位小数""不少于100词"）保留。
10. **R10** 元数据形态以 V3 契约为准（`semantic_units`：standalone_question / composite_unit；12 个 canonical 题型）。
11. **R11** 入库的是 question，不是 paper：试卷标题、大题标题、"参考答案"标题、班级/姓名/学号/日期 不属于任何单元区间（管线校验 `PAPER_LINE_IN_UNIT` + QC C9 强制）。
12. **R12** 批注不动源内容，只插锚点；LLM 只输出行号引用（QC C8 逐行保证）。

---

## 6. 实现方式与代码逻辑

### 6.1 OCR 服务（`ocr_service\`）
- **batch_convert_pdf.py**：POST PDF → PaddleOCR-VL-1.6 job → 轮询 `state==done` → 下载 jsonl →
  合并各页 `markdown.text`（页间 `\n\n---\n\n`）→ 写 `{年级}\{科目}\{名}.md`。
  - 每日额度 20000 页，`data\ocr_page_usage.json` 记 `{date,used}`，**每处理一份文件后落盘**。
  - `extract_grade_subject` 从文件名解析年级/科目；解析不出 → 落 `未分类`（见 §10 技术债）。
  - **已知**：不下载 OCR 返回的 `outputImages`，新产出 md 缺图，靠 `recover_images.py` 增量补。
- **ocr_watchdog.py**：`while True`——读用量→达限则等午夜并重置→拉起转换子进程→每 60s 查用量、达限则
  terminate→异常退出 5 分钟重试。**须用户手动启动**（`start_ocr_watchdog.bat`）；DSH 拉起会被进程树清理杀掉。

### 6.2 源修复（`scripts\`，②层）
- **corpus_scan.py**（只读）：遍历全库源 md，统计①双重识别（difflib：同行号、行距≤4、归一化相似度≥0.7）
  ②裸 LaTeX（含命令但整行无 `$`），细分简单/复杂 → `data\corpus_scan.json`。
- **fix_bare_latex.py**：给含 LaTeX 但无 `$` 的行补 `$…$`。确定性、幂等（跳过已含 `$` 的行）。
  - TOKEN（`:27`）只包"基＋`_{}`/`^{}` 核"，刻意不含外围括号/句号，避免吞句读。
  - `COMPLEX` 白名单（`:24`）跳过 `\mathrm/\xrightarrow/\text{/\ce{/\frac/\begin` 等，交人工整段包 `$`。
  - 变更日志 `data\bare_latex_fix_log.json`（file/line/before/after）可回滚。
- **recover_images.py**：引用名内嵌坐标 = PDF 以 144DPI(2x) 渲染的像素空间；按 `---` 分页定位到页；
  PyMuPDF 渲染并按框裁剪 → `_imgs\{名}\`；重写 md 引用为相对路径，审计 `recover_images_audit.jsonl` 可回滚。幂等。
- **pdf_fidelity.py**：对有文本层的 PDF，抽中文长句段（归一化后 ≥12 字符），与源归一化全文做子串/首尾 10 字匹配，
  算覆盖率 → `data\pdf_fidelity.json`。**精度不足，仅作粗筛排序**（见 §10）。

### 6.3 LLM 重切（`reslice_pipeline.py`，③④层，主线）
- **行号化** `number_lines`：每行前缀 `[L0001]`，供 LLM 受控引用，不转录正文。
- **提示词契约** `PROMPT_HEAD`：注入根本规则 R1–R12 + 输出 JSON schema；要求**只引用行号、只输出一个 JSON 对象**。
- **LLM 调用** `call_llm`：`mimo-x-pro-preview`，`base_url=https://api.xiaomimimo.com/v1`，
  temp=0.1，`max_tokens=30000`，超时 600s，重试 2 次；`finish_reason==length` 视为截断并抛错。
  密钥在 `data\.llm_config`（**永不打印**）。顺序调用，**无并发**（有意为之）。
- **JSON 提取** `extract_json`：容忍 ```json 围栏/前后杂文；修复尾逗号、控制字符；多候选回退。
- **确定性校验** `validate_manifest`：行区间合法性、题号覆盖、答案非空、composite 材料齐全、
  R11 试卷结构行不得混入单元区间（`PAPER_LINE` 正则）。硬问题进 `issues`，分节重号进 `warnings`。
  - 兜底：无题号单元（多为卷末作文）按全卷顺序自动顺延补号。
- **编译产出** `write_outputs`：
  - `compile_anchor` → `.annotated.md`（本质产物，见 §4.3/4.4）。
  - `compile_slices` → 切片 md（展示视图）：题干区/答案区/详解区；共享答案表按题号取值不整段回引。
- **CLI**：`--pilot`（跑 `reslice_pilot_files.json`）/ `--file`（单文件）/ `--resume`（断点续跑，跳过已有 manifest）/
  `--recompile`（从已有 manifest 重编译，不调 LLM）。

### 6.4 质检（⑤层）
- **reslice_qc.py** C1–C10（见 §7）；**render_lint.py** 静态查渲染风险；**render_preview.py** 出 HTML 供人眼比对 PDF。

---

## 7. 质检体系总表

| 编码 | 检查 | 手段 |
|---|---|---|
| C1 | 题干区/答案区标记配对 | 切片标记计数 |
| C2 | manifest 题号覆盖 = 源题号集合（无遗漏） | `normalize_qnum` 抽源题号做差集（启发式，见 §10） |
| C3 | 每单元答案区非空 | 切片解析 |
| C4 | composite 必含 material/questions | manifest 字段 |
| C5 | 源图片行全部被单元区间覆盖 | 区间覆盖集 vs `<img>` 行 |
| C6 | 源表格行全部被覆盖（须知/答题卡表除外） | 区间覆盖集 vs 表格行 |
| C7 | 卷面指令不出现 | BOILER 正则（豁免 ESSENTIAL 作答要求） |
| C8 | **锚点保真**：`.annotated.md` 去锚点 == 源文件逐行 | 逐行 diff |
| C9 | 试卷结构行不混入单元区间 | `PAPER_LINE` 匹配覆盖行 |
| C10 | 每种 META 标记 start/end 数量配对 | 计数（**刻意不查严格嵌套**：共享答案表使多单元包络在文档层必然交错，是连续区间模型的现实） |
| R-L1/2/3 | `$` 配对 / `\ce{}`(需 mhchem) / 命令损坏 | render_lint |
| R-T1/2/3 | table/tr/td 配平 / `alt="Image"" />` 属性损坏 / div 配平 | render_lint |

> 判定：`PASS` = 0 issues。试点 16/16 PASS。

---

## 8. 运维

- **重启守护**：`ocr_service\start_ocr_watchdog.bat`（**用户手动**；DSH 拉起会被杀）。
- **每日额度**：20000 页，午夜重置；`data\ocr_page_usage.json` 为本地计数，**API 侧为最终闸门**。
- **计划任务定义**：`ocr_service\ocr_task.xml`（`schtasks /create /tn OcrWatchdog /xml …`，沙箱下 `schtasks` 受限，需用户侧执行）。
- **编码铁律**：改 Python 读的 JSON 一律用 Python `write_text`/`json.dump`，**禁止** PowerShell `Set-Content -Encoding UTF8`（带 BOM → `json.load` 崩 → 批处理退出码 1 → 守护 5 分钟重试循环）。

---

## 9. 当前状态（诚实快照，2026-09-15）

> **阶段:P2 收口 → P3 Evidence Contract Validation**(定位重校准见 charter §12)。

- **重切路线成立**：试点 16 份 / 9 科 × 3 学段，用户全部签核；QC C1–C10 16/16 PASS。
- **P2.1 ✅ CLOSED**：Question / Answer Evidence Boundary(prompt v2.4→v2.5;contamination 76→3,残留 3 例 accepted exception)。
- **P2.2 ✅ CLOSED**：Figure Evidence Boundary(prompt v2.7;题面图引用 154 条 b1→b2 **lost=0**、admission 272/272=100%、
  adjacent orphan 14→0;剩余 58 条 100% 为解析区重复配图,不影响 V3 契约,按裁定不修;产物 `Ocr-markdown/reslice-p2-b2/` 8 卷全 v2.7)。
- **V3 对接实测**:Phase 0 Span Compatibility / 0.2-R2 Evidence→IR Compatibility / 0.3-B source-grounded Option Resolution(527/548)——
  **证明两项目接口是 Source Evidence / Resolved Evidence,不是 Question IR**。
- **源缺陷已量化**（corpus_scan，3120 份）：双重识别 138 份/148 处；裸 LaTeX 954 份（简单 4918 / 复杂 610）。
- **全量推广一步未迈**：3120 份里仅重切试点 + P2 小批。**P4 之前不全量重跑**(charter §12.8)。

---

## 10. 已知局限与技术债

- **A（正确性）裸 LaTeX 半包残损**：~~收紧 TOKEN 后 `\xlongequal`/`\cdot`/`\sqrt`/`\triangle` 等被留在数学岛外当字面文本~~
  **已修复（R8/BUG-09）**：实为 **103 行**（非 36），按日志逐行回退至修复前裸形态 + `fix_bare_latex.py` 加 `BARE_CMD` 防回归（仅当"数学岛外无残留 `\命令`"才落地）。残留 105 行括号式（`Fe(OH)_{3}`）因 TOKEN 不含 `()` 而漏网——为不吞句读的取舍。
- **A2（正确性，既存）全库"半定界"数学债（BUG-15）**：**1490 份 / 23,221 行**同时含 `$…$` 岛与散落岛外的裸命令（`\quad/\frac/\mathrm/\left\right/\sqrt/\therefore/\times` 等），渲染不一致/破损。因 `corpus_scan` 与 `fix_bare_latex` 均跳过含 `$` 行而长期不可见。**既存、非工具引入**，是数/化/生的主导数学债；需半自动"整段定界"（CJK 段用 `\text{}`），量大，须先小样验证 KaTeX 兼容再批量。多数 `\quad/\times/\cdot` 为外观退化、`\frac/\sqrt/\mathrm` 为结构性破损，可分级。
- **B（正确性）锚点 LIFO 闭合**：~~死逻辑~~ **已修复（R9/BUG-10）**：闭合元组带 span 起始行、同深度闭合排序键改起始行降序（真 LIFO）；单测验证 + recompile/QC 16/16 通过。
- **C（覆盖）图片恢复目录落后**：~~`recover_images.py:48` 只扫 `高一/高二/高三/未分类`~~
  **已修复（R58/BUG-11）**：白名单废弃，改"排除派生目录（`_imgs`/`.cache`/`auto-annotated*`/`reslice*`），其余顶层一律为源"，视野 2,421→3,119（新可见 698）。实测盲区当前缺图候选=0（迁出前已恢复），危害定性为流程潜伏风险；5 用例回归钉 + 双变异咬合，见 `bugs.md` BUG-11。
- **D（运维）守护 stdout PIPE 死锁**：~~风险~~ **已修复（R9/BUG-12）**：子进程 stdout/stderr 改 `DEVNULL`（batch 自落盘日志），消除长跑管道死锁。
- **E（安全）OCR token 明文**：~~硬编码~~ **已修复（R9/BUG-13）**：外部化到 `data\.ocr_config` + `_load_token()`（环境变量优先）；硬编码已删、加载验证 40 字符、当前进程不受影响。
- **F（数据）未分类跑步机 + 重复源**：OCR 对文件名不含年级的 PDF 默认落 `未分类`（现存 145 份且仍在接收，`status.md` 曾误称已清除）；全库 **73 个重复 basename**（多为高考真题汇编），会重复 OCR/重切/入题库。需去重 + 周期重归类。
- **G（方法）pdf_fidelity 高假阳性**：PDF 文本层与 OCR 有系统性表示差异（`20°W 和` vs `20W和`、度数/空格/标点/分段/双重识别；PDF 反而丢 π/矢量符号而 OCR 写全）。精确+前缀子串匹配抗不住，连地理散文 0.45 复核也是假警报。**仅作粗筛排序，不作权威丢内容检测**；源保真主靠"渲染预览 vs PDF"人眼比对 + C1–C10 + 图/公式定点 PDF 视觉核对。
- **H（遗留 artifact）**：`.restored.md`（三十一中化学，42KB）仍在，污染 corpus_scan 计数（3120 vs 真源 3119），建议归档。
- **I（历史）**：四十三中历史 4 题源缺答案；2 份化学 3 处 `\ce{}` 需消费方开 mhchem。

---

## 11. 可扩展性评估（含 MIMO 1M 上下文）

**结论：输入/输出规模不是全量推广的 blocker。** 实测（3120 份源，196 份 >100KB，7 份 >200KB）：

| 文件档 | 输入(行号化后) | 输出(units JSON) | vs 上限 |
|---|---|---|---|
| 最大（557KB / 6717 行 / ~89 题） | ~128K tokens | ~8K tokens | 输入 ≪ 1M；输出 ≪ 30K |
| 次大（250KB / ~60 题） | ~56K tokens | ~5K tokens | 同上 |

- MIMO `mimo-x-pro-preview` 支持 **1M 上下文**，最大文件输入 ~128K，**余量充足**；输出最大 ~8K，远低于 `max_tokens=30000`，**不会截断**。
- **残留的真实约束**（非硬失败）：
  1. **长扫描质量**：6717 行文件要求模型扫全篇才能完整覆盖题号，"lost-in-the-middle" 可能漏题。→ 用**大文件冒烟测试**（并入定时测速批）实证覆盖率，而非假设失败。
  2. **成本/时延**：128K-token 输入 × 大文件尾部，累计 token 成本可观；顺序执行、无并发是保守取舍。
- 故 §12 的"50 份测速批"应**刻意包含最大几份文件**，一次性验证质量 + 定价吞吐。

---

## 12. 路线图与决策记录

**决策记录**
- 2026-09-09：放弃 v6 规则批注（预审合格率仅 4.0%）；**废弃** "BERT+Span+CRF 本地训练" 路线，改 **LLM 驱动重切**。
- 2026-09-10：确立"锚点式批注"（源不动、只插锚点、LLM 只给行号）为根本形态；试点 16/16 通过。
- 2026-09-15：**项目定位重校准**(charter §12)——preprocessing 从"输出 V3 Admission 可消费的 Question IR"
  收缩为 **Source Evidence Producer**;接口 = Evidence Manifest(非 Question IR);P2.3 更名 P3;
  不规划仓库合并;preprocessing 新增功能必须是"生产 V3 当前实际缺失的 Source Evidence",否则不做。

**当前路线(P2 已收口,进入 P3)**
- [x] P2.1 Question / Answer Evidence Boundary — CLOSED。
- [x] P2.2 Figure Evidence Boundary — CLOSED。
- [ ] **P3.1 Producer Output Freeze Candidate**:冻结 Evidence 类型集合(§1.2),只定义事实。
- [ ] **P3.2 V3 Consumer Compatibility**:真实产物 + 小批卷 + V3 实际 Gate/Admission 验证
      `Manifest → EvidenceAdapter → Resolved Evidence → IR → Gate → Admission`(**不建正式 import API**)。
- [ ] **P3.3 Gap-driven Repair**:只修真实 gap,**问题在哪层就在哪层修**。
- [ ] **P4 Small-scale Real Admission**:小批真实卷 + 实际 V3 Gate + Admission + Question/Instance 产物验证;
      之后再决定是否扩大规模 / 全量重跑 / 正式 import path。

**推广前准备清单(P4 后再启)**
- [ ] 源修复收尾：回修残损行(§10-A) + 处理复杂裸 LaTeX + 删双重识别。
- [ ] 数据卫生：去重 73 份、周期重归类 `未分类`、归档 `.restored.md`。
- [ ] `reslice_pipeline` 加**全量 runner**（枚举全库 + 吞吐/配额控制）；现 CLI 仅试点版。
- [ ] 全量重切 + QC C1–C10 回归 + 渲染预览抽查(**须 V3 Consumer Path 稳定后**,charter §12.8)。

---

## 附录 A · 题型枚举（12 canonical）
`single_choice` `multiple_choice` `fill_in` `short_answer` `essay` `cloze` `reading` `grammar_fill` `vocabulary_fill` `seven_to_five` `reading_expression` `true_false`

## 附录 B · 数据文件
| 文件 | 内容 |
|---|---|
| `data\.llm_config` | LLM 密钥（provider/base_url/model/api_key，**勿外泄**） |
| `data\corpus_scan.json` | 全库源缺陷量化 |
| `data\bare_latex_fix_log.json` | 裸 LaTeX 修复变更（可回滚） |
| `data\pdf_fidelity.json` | PDF 溯源覆盖率（粗筛） |
| `data\reslice_pilot_{files,result,qc}.json` | 试点清单/结果/QC |
| `data\recover_images_{summary.json,audit.jsonl}` | 配图恢复汇总/审计 |
| `data\ocr_page_usage.json` | OCR 页额度 `{date,used}` |

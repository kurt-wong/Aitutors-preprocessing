# Papers 项目目录导航

> 智能题库预处理：北京高中试卷 PDF → OCR Markdown → LLM 重切批注 → 题库单元
> 最近整理：2026-09-10

## 从哪读起

- **`prd.md`** —— **规格基准（冻结）**：背景、结构、数据契约、批注规则 R1–R12、代码逻辑、质检体系、已知局限、路线图。**读这份就能理解整个项目。**
- **`status.md`** —— 进度快照：里程碑、签核、推广前清单、风险登记。
- **`log.md`** —— 变更日志：每轮的代码变动 + 操作 + 产出 + 遗留（**追加式，最新在文末**，附时间戳）。
- **`bugs.md`** —— 缺陷记录：每个 bug 的现象/根因/位置/解决方案/教训（待修复在前，附登记时间戳）。
- 本 README —— 目录导航。

## 目录结构

| 目录 | 内容 | 说明 |
|---|---|---|
| `Ocr-markdown\` | **核心数据**（勿动） | 源 md（ground truth）、`resliced-pilot\` 重切试点、`auto-annotated-v6\`(旧规则批注，历史对照)、`_imgs\` 图片库 |
| `maintainess\` | 待转换/维护区 | `PDF\`（OCR 源）、`DOCX\`、`待转换DOC\`、`质量测试\` |
| `original\` | 原始资料 | 五三资料、各年级原始文档 |
| `scripts\` | 全部项目脚本 | 见下表 |
| `ocr_service\` | OCR 转换服务 | 守护进程 + 批量转换 + 计划任务定义（见"服务运维"） |
| `logs\` | 运行日志 | `ocr_batch_log.txt`、`ocr_watchdog.log`、`reslice_pilot_log.txt`、`recover_images_log.txt` |
| `data\` | 运行数据/状态 | `.llm_config`(密钥)、页数统计、试点 json、corpus/pdf 溯源、修复日志、审计 jsonl |
| `reports\` | 分析报告 | **重切试点报告**、v6 预审报告（历史）、渲染预览 `preview\` |
| `_archive\` | 归档（可回溯，勿删） | 历次冗余整理、tmp docx 提取工具与结果 |

根目录仅保留 `prd.md`、`status.md`、`log.md`、`bugs.md` 与本 README。

## scripts\ 脚本索引（现役）

| 脚本 | 层 | 用途 |
|---|---|---|
| `reslice_pipeline.py` | ③④ | **LLM 重切主线**：`--pilot` / `--file` / `--resume` 断点续跑 / `--recompile` 免 LLM 重编译 |
| `reslice_qc.py` | ⑤ | 重切产出回归质检 C1–C10 |
| `render_lint.py` / `render_preview.py` | ⑤ | 渲染风险静态检测 / 源 MD→HTML 预览（供人眼比对 PDF） |
| `corpus_scan.py` | ② | 全库源缺陷量化（只读） |
| `fix_bare_latex.py` | ② | 裸 LaTeX 自动包 `$`（确定性、可回滚） |
| `recover_images.py` | ② | PDF→`_imgs` 配图恢复（PyMuPDF，幂等） |
| `pdf_fidelity.py` | ② | PDF 文本层 vs 源覆盖率（**仅粗筛**，高假阳性） |
| `prereview_check.py` | (旧) | v6 预审；仅 `normalize_qnum`/`parse_answer_tables`/`parse_range_answers` 3 个 helper 被重切复用 |

已删除（无效）：`_tmp_llm_ping.py`、`test_single.py`、`test_ocr_api.py`、`__pycache__`。

## 服务运维（OCR 转换）

- 守护进程须**用户手动启动**（DSH 拉起会被进程树清理杀掉）：
  ```bat
  D:\Project\Papers\ocr_service\start_ocr_watchdog.bat
  ```
  （每日 0:00 重置 20000 页额度，达限自动停止等跨日续跑）
- 计划任务定义：`ocr_service\ocr_task.xml`（如需重注册：`schtasks /create /tn OcrWatchdog /xml …`，沙箱下受限需用户侧执行）
- 页数余额：`data\ocr_page_usage.json`
- **编码铁律**：改 Python 读的 JSON 用 Python 写，勿用 PowerShell `Set-Content -Encoding UTF8`（带 BOM 会崩 `json.load` → 批处理退出码 1 → 守护重试循环）。

## 快速入口

- 项目规格与批注根本规则（R1–R12）：`prd.md`
- LLM 重切试点报告（16 份 9 科全过）：`reports\reslice_pilot_report.md`
- v6 全量预审报告（历史对照）：`reports\prereview_report_full.md`

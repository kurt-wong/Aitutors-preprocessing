# 目录整理审计（2026-09-10 08:25）
所有移动均为原样搬移，未修改文件内容；按本清单反向移动即可完整还原。

MOVE  D:\Project\Papers\reslice_pipeline.py  ->  D:\Project\Papers\scripts\reslice_pipeline.py
MOVE  D:\Project\Papers\reslice_qc.py  ->  D:\Project\Papers\scripts\reslice_qc.py
MOVE  D:\Project\Papers\prereview_check.py  ->  D:\Project\Papers\scripts\prereview_check.py
MOVE  D:\Project\Papers\recover_images.py  ->  D:\Project\Papers\scripts\recover_images.py
MOVE  D:\Project\Papers\reclassify_unknown.py  ->  D:\Project\Papers\scripts\reclassify_unknown.py
MOVE  D:\Project\Papers\analyze_quality.py  ->  D:\Project\Papers\scripts\analyze_quality.py
MOVE  D:\Project\Papers\make_review_sample.py  ->  D:\Project\Papers\scripts\make_review_sample.py
MOVE  D:\Project\Papers\full_analysis.py  ->  D:\Project\Papers\scripts\full_analysis.py
MOVE  D:\Project\Papers\_tmp_pick_pilot.py  ->  D:\Project\Papers\scripts\_tmp_pick_pilot.py
MOVE  D:\Project\Papers\ocr_watchdog.py  ->  D:\Project\Papers\ocr_service\ocr_watchdog.py
MOVE  D:\Project\Papers\batch_convert_pdf.py  ->  D:\Project\Papers\ocr_service\batch_convert_pdf.py
MOVE  D:\Project\Papers\start_ocr_watchdog.bat  ->  D:\Project\Papers\ocr_service\start_ocr_watchdog.bat
MOVE  D:\Project\Papers\ocr_task.xml  ->  D:\Project\Papers\ocr_service\ocr_task.xml
MOVE  D:\Project\Papers\ocr_watchdog.log  ->  D:\Project\Papers\logs\ocr_watchdog.log
MOVE  D:\Project\Papers\ocr_batch_log.txt  ->  D:\Project\Papers\logs\ocr_batch_log.txt
MOVE  D:\Project\Papers\reslice_pilot_log.txt  ->  D:\Project\Papers\logs\reslice_pilot_log.txt
MOVE  D:\Project\Papers\recover_images_log.txt  ->  D:\Project\Papers\logs\recover_images_log.txt
MOVE  D:\Project\Papers\ocr_page_usage.json  ->  D:\Project\Papers\data\ocr_page_usage.json
MOVE  D:\Project\Papers\reslice_pilot_files.json  ->  D:\Project\Papers\data\reslice_pilot_files.json
MOVE  D:\Project\Papers\reslice_pilot_result.json  ->  D:\Project\Papers\data\reslice_pilot_result.json
MOVE  D:\Project\Papers\reslice_pilot_qc.json  ->  D:\Project\Papers\data\reslice_pilot_qc.json
MOVE  D:\Project\Papers\recover_images_summary.json  ->  D:\Project\Papers\data\recover_images_summary.json
MOVE  D:\Project\Papers\recover_images_audit.jsonl  ->  D:\Project\Papers\data\recover_images_audit.jsonl
MOVE  D:\Project\Papers\reclassify_audit.jsonl  ->  D:\Project\Papers\data\reclassify_audit.jsonl
MOVE  D:\Project\Papers\prereview_report.md  ->  D:\Project\Papers\reports\prereview_report.md
MOVE  D:\Project\Papers\prereview_report.json  ->  D:\Project\Papers\reports\prereview_report.json
MOVE  D:\Project\Papers\prereview_report_full.md  ->  D:\Project\Papers\reports\prereview_report_full.md
MOVE  D:\Project\Papers\prereview_report_full.json  ->  D:\Project\Papers\reports\prereview_report_full.json
MOVE  D:\Project\Papers\reclassify_report.md  ->  D:\Project\Papers\reports\reclassify_report.md
MOVE  D:\Project\Papers\reclassify_report.csv  ->  D:\Project\Papers\reports\reclassify_report.csv
MOVE  D:\Project\Papers\reslice_pilot_report.md  ->  D:\Project\Papers\reports\reslice_pilot_report.md
MOVE  D:\Project\Papers\tmp  ->  D:\Project\Papers\_archive\2026-09-10_tmp_docx提取
DEL   D:\Project\Papers\_tmp_llm_ping.py  （一次性测试脚本，已被 batch_convert_pdf.py / reslice 流水线取代）
DEL   D:\Project\Papers\test_single.py  （一次性测试脚本，已被 batch_convert_pdf.py / reslice 流水线取代）
DEL   D:\Project\Papers\test_ocr_api.py  （一次性测试脚本，已被 batch_convert_pdf.py / reslice 流水线取代）
DEL   D:\Project\Papers\__pycache__  （可再生）

## Ocr-markdown 子目录整理（2026-09-10）
- MOVE Ocr-markdown\finetune\.llm_config -> data\.llm_config（活跃配置，reslice_pipeline 已改指向）
- MOVE Ocr-markdown\finetune\ -> _archive\2026-09-10_Ocr-markdown清理\finetune\（1.4GB 微调实验，内部脚本路径为历史绝对路径）
- MOVE Ocr-markdown\scripts\ -> _archive\...\scripts\（v6 时代标注/质检脚本）
- MOVE Ocr-markdown\LLM-marked\ -> _archive\...\LLM-marked\（v0 期 LLM 批注产出）
- MOVE Ocr-markdown\{README,PREPROCESS_SOLUTION,status}.md -> _archive\...（描述旧结构的过时文档）
- MOVE Ocr-markdown\批注模式参考.md -> reports\Ocr-markdown批注模式参考.md（仍有参考价值）
- 保留不动：各年级/类别原始 OCR 目录（watchdog 活跃写入）、_imgs（相对路径基准）、auto-annotated-v3/v6、resliced-pilot、.cache

## 渲染缺陷确定性修复（2026-09-10）
- T2 修复 2019北京交大附中高三（上）12月月考化学含答案(1).md: alt="Image"" /> -> alt="Image" /> ×15
- L1 修复 2020北京东城高一（上）期末英语（教师版）.md: 货币$转义 ×2

# -*- coding: utf-8 -*-
"""R66.1 激活前只读预检(零 API、零写入、确定性输出)

目的:在重启 daemon 之前,量化"新代码首扫将真实 OCR 多少 source"。
依据 runner batch_convert_pdf.main() 的扫描枚举与期望输出路径决策(逐行复刻,
sanitize/extract_grade_subject 与 runner 字节级同规则),manifest 为空(现状事实)。

输出 data/r66_1_preflight.json:
  would_ocr[]   : 首扫将真实 OCR 的 source(期望输出缺失或<=100B,且无清单记录)
  exists_skip   : EXISTS 静默跳过数量
  page_usage    : 当日配额状态快照
  log_state     : ocr_batch_log.txt 大小/mtime(激活前后对照锚点)
不猜测页数:仅报告 would_ocr 的文件数与字节数,页数不作估计(禁推断)。
"""
import hashlib
import json
import os
import re

BASE = r"D:\Project\Papers"
PDF_ROOT = os.path.join(BASE, "maintainess", "PDF")
OUTPUT_ROOT = os.path.join(BASE, "Ocr-markdown")
LOG_FILE = os.path.join(BASE, "logs", "ocr_batch_log.txt")
PAGE_USAGE_FILE = os.path.join(BASE, "data", "ocr_page_usage.json")
OUT = os.path.join(BASE, "data", "r66_1_preflight.json")


def sanitize_stem(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "_", os.path.splitext(name)[0])


def extract_grade_subject(filename: str):
    grade = "未分类"
    subject = "未分类"
    if re.search(r"高一|高1", filename):
        grade = "高一"
    elif re.search(r"高二|高2", filename):
        grade = "高二"
    elif re.search(r"高三|高3", filename):
        grade = "高三"
    for s in ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"]:
        if s in filename:
            subject = s
            break
    return grade, subject


def enumerate_pdfs():
    """与 runner main() 完全相同的枚举顺序与 output_dir 决策。"""
    files = []
    for filename in sorted(os.listdir(PDF_ROOT)):
        if filename.lower().endswith(".pdf"):
            grade, subject = extract_grade_subject(filename)
            files.append((os.path.join(PDF_ROOT, filename),
                          os.path.join(OUTPUT_ROOT, grade, subject), filename))
    for grade in ["高一", "高二", "高三"]:
        grade_path = os.path.join(PDF_ROOT, grade)
        if not os.path.isdir(grade_path):
            continue
        for subject in sorted(os.listdir(grade_path)):
            subject_path = os.path.join(grade_path, subject)
            if not os.path.isdir(subject_path):
                continue
            for filename in sorted(os.listdir(subject_path)):
                if filename.lower().endswith(".pdf"):
                    files.append((os.path.join(subject_path, filename),
                                  os.path.join(OUTPUT_ROOT, grade, subject), filename))
    return files


def main():
    files = enumerate_pdfs()
    exists_skip, would_ocr = 0, []
    for file_path, output_dir, filename in files:
        output_md = os.path.join(output_dir, sanitize_stem(filename) + ".md")
        if os.path.exists(output_md) and os.path.getsize(output_md) > 100:
            exists_skip += 1
        else:
            try:
                size = os.path.getsize(file_path)
            except OSError:
                size = None
            would_ocr.append({
                "source_rel": os.path.relpath(file_path, BASE).replace("\\", "/"),
                "expected_output_rel": os.path.relpath(output_md, BASE).replace("\\", "/"),
                "source_bytes": size,
                "output_state": "missing" if not os.path.exists(output_md) else "present<=100B",
            })

    page_usage = None
    if os.path.exists(PAGE_USAGE_FILE):
        with open(PAGE_USAGE_FILE, encoding="utf-8") as f:
            page_usage = json.load(f)

    log_state = None
    if os.path.exists(LOG_FILE):
        st = os.stat(LOG_FILE)
        log_state = {"size": st.st_size,
                     "sha256_head_64k": hashlib.sha256(
                         open(LOG_FILE, "rb").read(65536)).hexdigest()}

    report = {
        "purpose": "R66.1 activation preflight (read-only, manifest assumed empty as-is)",
        "total_pdfs": len(files),
        "exists_skip": exists_skip,
        "would_ocr_count": len(would_ocr),
        "would_ocr_total_source_bytes": sum(w["source_bytes"] or 0 for w in would_ocr),
        "would_ocr": would_ocr,
        "page_usage": page_usage,
        "ocr_batch_log_state": log_state,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print(f"total_pdfs={len(files)} exists_skip={exists_skip} "
          f"would_ocr={len(would_ocr)} bytes={report['would_ocr_total_source_bytes']}")
    print(f"page_usage={page_usage}")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
r"""
reclassify_unknown.py — 将 Ocr-markdown\未分类 的 md 按考试类型重归类

背景:
  batch_convert_pdf.py 用文件名提取年级, 提取不到的一律落入"未分类"。
  经扫描, 这 697 份并非缺失年级的校内试卷, 而是考试类型不同:
  高考真题汇编 / 合格考(合格性考试) / 会考 / 学业水平考试 / 等级考 /
  竞赛自招模拟 等。强行归入高一/高二/高三会污染数据, 故按类型建目录。

归类规则(按优先级):
  文件名关键词 -> 类型目录;  文件名无法判定时扫描正文前 3000 字。
  两份"未分类\未分类"的文件额外做科目的内容推断。

输出:
  Ocr-markdown\{类型}\{科目}\*.md      (apply 模式移动文件)
  reclassify_report.md / .csv          归类报告
  reclassify_audit.jsonl               移动审计(可回滚)

用法:
  python reclassify_unknown.py            # 先出报告, 不动文件
  python reclassify_unknown.py --apply    # 执行移动
"""

import argparse
import csv
import glob
import io
import json
import os
import re
import shutil
import sys
import time

OCR_ROOT = r"D:\Project\Papers\Ocr-markdown"
UNKNOWN = os.path.join(OCR_ROOT, "未分类")
EXTRA_DIRS = [os.path.join(OCR_ROOT, "高三", "未分类")]  # 散落在别处的未分类
REPORT_MD = r"D:\Project\Papers\reports\reclassify_report.md"
REPORT_CSV = r"D:\Project\Papers\reports\reclassify_report.csv"
AUDIT = r"D:\Project\Papers\data\reclassify_audit.jsonl"

SUBJECTS = ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"]

# (类型目录, 关键词列表) —— 顺序即优先级; 高考真题额外支持正则(如"高考英语真题")
TYPE_RULES = [
    ("高考真题", ["高考真题", "真题汇编"]),
    ("合格考",   ["合格考", "合格性考试", "合性试"]),
    ("会考",     ["会考"]),
    ("学业水平考试", ["学业水平", "学考", "水平考试"]),
    ("等级考",   ["等级考"]),
    ("竞赛自招", ["竞赛", "博雅", "强基", "自主招生", "领军", "筑梦"]),
]
GAOKAO_RE = re.compile(r"高考[^，。；]{0,6}真题|真题汇编")

# 科目优先于关键词打分的特殊写法
SUBJECT_SPECIAL = [("文综", "文综"), ("理综", "理综"), ("理科综合", "理综"), ("文科综合", "文综")]

SUBJECT_HINTS = {
    "语文": ["阅读下面", "作文", "古诗文", "默写", "文言文"],
    "数学": ["函数", "方程", "数列", "概率", "几何", "导数", "不等式"],
    "英语": ["阅读理解", "完形填空", "作文", "单词", "听力"],
    "物理": ["受力", "加速度", "电路", "磁场", "动能", "折射"],
    "化学": ["化学", "离子", "溶液", "氧化还原", "有机", "元素周期"],
    "生物": ["细胞", "基因", "光合作用", "遗传", "DNA"],
    "历史": ["朝代", "历史", "封建", "革命", "近代化"],
    "地理": ["纬度", "气候", "地形", "洋流", "等高线"],
    "政治": ["政治", "经济制度", "哲学", "人民代表大会", "市场经济"],
}


def sniff_text(path, n=3000):
    try:
        with io.open(path, encoding="utf-8") as f:
            return f.read(n)
    except Exception:
        return ""


def classify(path):
    name = os.path.basename(path)
    text = sniff_text(path)
    hay = name + "\n" + text
    if GAOKAO_RE.search(name):
        return "高考真题", "文件名"
    for cat, kws in TYPE_RULES:
        if any(k in hay for k in kws):
            return cat, "内容" if not any(k in name for k in kws) else "文件名"
    return "其他汇编", "未判定"


def detect_subject(path, fallback="未分类"):
    name = os.path.basename(path)
    for kw, sub in SUBJECT_SPECIAL:
        if kw in name:
            return sub, "文件名(综合卷)"
    for s in SUBJECTS:
        if s in name:
            return s, "文件名"
    parent = os.path.basename(os.path.dirname(path))
    if parent in SUBJECTS:
        return parent, "父目录"
    text = sniff_text(path, 5000)
    scores = {s: sum(text.count(k) for k in kws) for s, kws in SUBJECT_HINTS.items()}
    best = max(scores, key=scores.get)
    if scores[best] >= 3:
        return best, "内容推断"
    return fallback, "未判定"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="执行移动(默认只出报告)")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(UNKNOWN, "*", "*.md")))
    for d in EXTRA_DIRS:
        if os.path.isdir(d):
            files.extend(sorted(glob.glob(os.path.join(d, "*.md"))))

    rows = []
    for f in files:
        cat, src = classify(f)
        sub, ssrc = detect_subject(f)
        rows.append({
            "file": f,
            "name": os.path.basename(f),
            "old_dir": os.path.relpath(os.path.dirname(f), OCR_ROOT).replace("\\", "/"),
            "category": cat,
            "cat_src": src,
            "subject": sub,
            "sub_src": ssrc,
        })

    # 统计
    from collections import Counter
    cat_cnt = Counter((r["category"], r["subject"]) for r in rows)
    total = len(rows)
    print(f"待归类: {total}")
    for (c, s), n in sorted(cat_cnt.items()):
        print(f"  {c}/{s}: {n}")

    # 报告
    with io.open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("# 未分类文件重归类报告\n\n")
        f.write(f"- 生成时间: {time.strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"- 待归类文件: {total}\n")
        f.write(f"- 模式: {'执行移动' if args.apply else '仅报告(未移动)'}\n\n")
        f.write("## 归类汇总\n\n| 类型 | 科目 | 数量 |\n|---|---|---|\n")
        for (c, s), n in sorted(cat_cnt.items()):
            f.write(f"| {c} | {s} | {n} |\n")
        f.write("\n## 说明\n\n")
        f.write("- 这批文件并非缺失年级的校内试卷, 而是按考试类型区分的汇编/真题,\n")
        f.write("  因此归入 `高考真题`/`合格考`/`会考`/`学业水平考试`/`等级考`/`竞赛自招`/`其他汇编` 目录。\n")
        f.write("- `auto_annotate_v7.py` 目前只扫描 高一/高二/高三, 如需把这些纳入批注,\n")
        f.write("  把新目录加入其 source_dirs 即可。\n\n")
        f.write("## 明细\n\n| 原路径 | 新路径 | 类型判定 | 科目判定 |\n|---|---|---|---|\n")
        for r in rows:
            newp = f"{r['category']}/{r['subject']}/{r['name']}"
            f.write(f"| {r['old_dir']}/{r['name']} | {newp} | {r['cat_src']} | {r['sub_src']} |\n")

    with io.open(REPORT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["old_dir", "category", "subject", "cat_src", "sub_src", "name"])
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in w.fieldnames})

    print(f"报告: {REPORT_MD}")

    if not args.apply:
        print("仅报告模式。加 --apply 执行移动。")
        return

    moved = failed = 0
    with io.open(AUDIT, "a", encoding="utf-8") as audit:
        for r in rows:
            dst_dir = os.path.join(OCR_ROOT, r["category"], r["subject"])
            os.makedirs(dst_dir, exist_ok=True)
            dst = os.path.join(dst_dir, r["name"])
            try:
                if os.path.exists(dst):
                    print(f"  [SKIP] 目标已存在: {r['name']}")
                    continue
                shutil.move(r["file"], dst)
                audit.write(json.dumps({"from": r["file"], "to": dst}, ensure_ascii=False) + "\n")
                moved += 1
            except Exception as e:
                failed += 1
                print(f"  [FAIL] {r['name']}: {e}")

    # 清理空目录
    for d in [UNKNOWN] + EXTRA_DIRS:
        if os.path.isdir(d) and not os.listdir(d):
            try:
                os.rmdir(d)
                print(f"已移除空目录: {d}")
            except OSError:
                pass

    print(f"完成: 移动 {moved} | 失败 {failed} | 审计: {AUDIT}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()

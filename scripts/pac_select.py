# -*- coding: utf-8 -*-
"""Production Adversarial Corpus(PAC)选样与留档工具(R43,2026-09-13)。

System Readiness Gate 首攻面:真实 OCR + 真实 LLM 生产链。本脚本只做
**零成本选样与指纹留档**——把 22 份对抗样本(11 个 PDF 可进链类别 × 2)
的源 PDF、历史 OCR md、页数、文本层统计、sha256 全部固化进
`data/pac_selection.json`,供后续 OCR 重跑 / LLM 批注 / QC / 人工复核
逐 stage 对账。C3(DOCX)/C4(独立图像)按用户裁定本轮 BLOCKED。

选样纪律(production_adversarial_corpus_design.md §3):
1. 真实源,禁止合成;
2. 每样本先有 hazard 证据再入选(台账已知坏形态文件优先);
3. 样本选定后路径+sha256+页数只字不改留档;
4. known-hazard 样本的期望行为 = 坏形态被如实暴露,而非"跑完就算过"。

用法:
    python scripts/pac_select.py            # 选样+测量,写 data/pac_selection.json
    python scripts/pac_select.py --check    # 只校验已留档 selection 未漂移
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDF_ROOT = ROOT / "maintainess" / "PDF"
MD_ROOT = ROOT / "Ocr-markdown"
OUT = ROOT / "data" / "pac_selection.json"

# (sample_id, category, Ocr-markdown 相对路径, hazard 证据)
# md 相对路径 = 当前历史 OCR 产物(留档基线,用于 OCR 重跑漂移对比);
# OCR 重跑输入是它对应的源 PDF,不是这份 md。
PICKS = [
    # C1 原生文本 PDF(文本层实测后确认;若实测为扫描则如实改判)
    ("pac-c01-01", "C1 原生文本PDF", "会考\\数学\\2018北京春季高中会考数学（教师版）(1).md",
     "基础路径:会考卷疑为数字原生排版,测 OCR 服务对文本层 PDF 的行为"),
    ("pac-c01-02", "C1 原生文本PDF", "合格考\\数学\\2021北京高中合格考数学（第二次）（教师版）(1).md",
     "基础路径:合格考数学,含 \\d+ \\. 序号头形态"),
    # C2 扫描 PDF(OCR 噪声主战场)。首轮实测教训:原先按推定挑的"扫描卷"
    # (平谷历史/师大二附中数学)文本层实测均为 native_text——选样必须测量,
    # 不能靠文件名推定。改用队列中明示"图片版"且 md 基线在位的真扫描件。
    ("pac-c02-01", "C2 扫描PDF", "高一\\物理\\2021北京房山高一（下）期中物理（教师版）（图片版）(1).md",
     "图片版=图像页扫描件;物理图题 + 扫描噪声双暴露"),
    ("pac-c02-02", "C2 扫描PDF", "高一\\历史\\2021北京昌平高一（下）期末历史（图片版）（答案版）(1).md",
     "图片版=图像页扫描件;答案版卷面,答案区绑定 + 扫描噪声"),
    # C5 数学 LaTeX
    ("pac-c05-01", "C5 数学LaTeX", "高二\\数学\\2018北京五十六中高二（下）期中数学（理）（教师版）(1).md",
     "pilot 已知:pilot 曾修 Q8 图文错序、Q9 配图漂移;含 \\d+ \\. 形态"),
    ("pac-c05-02", "C5 数学LaTeX", "高三\\数学\\2021北京八十中高三考前练习数学（教师版）(1).md",
     "pilot 已知:公式/图形密集,ANSWER_IN_TABLE"),
    # C6 化学图片题(material/figure)
    ("pac-c06-01", "C6 化学图片题", "高三\\化学\\2019北京交大附中高三（上）12月月考化学含答案(1).md",
     "pilot 已知:裸 LaTeX 18+2、丢图×2(曾 PDF 文本层回填);\\d+ \\. 形态"),
    ("pac-c06-02", "C6 化学图片题", "高一\\化学\\2022北京首都师大附中高一12月月考化学（教师版）(1).md",
     "batch-C 已知:实验装置图密集卷"),
    # C7 答案与解析混排(region binding)
    ("pac-c07-01", "C7 答案解析混排", "高一\\生物\\2021北京四中高一（上）期中生物（教师版）.md",
     "BUG-17 家族实证卷:answer_lines 落在题干复述块(Q2/Q9/Q19)"),
    ("pac-c07-02", "C7 答案解析混排", "高三\\生物\\2020北京西城高三（上）期末生物含答案(1).md",
     "pilot 已知:Q20(3) 伪标题 ##;详解与答案混排"),
    # C8 跨页题(span continuity)
    ("pac-c08-01", "C8 跨页题", "高三\\英语\\2021北京丰台高三二模英语（教师版）(1).md",
     "pilot 已知:36 题长卷,完形/阅读跨页概率高;页分隔符 --- 承载跨页连续性"),
    ("pac-c08-02", "C8 跨页题", "高三\\地理\\2021北京东城高三二模地理（教师版）(1).md",
     "batch-C 卷;图表+材料跨页;含 \\d+ \\. 形态"),
    # C9 多 section 同号题(identity)
    ("pac-c09-01", "C9 多section同号", "合格考\\化学\\2020北京高中合格考化学（第一次）（教师版）(1).md",
     "BUG-22 原形态实证卷:大题内 1-9 被当全卷题号,答案区实键 26-34"),
    ("pac-c09-02", "C9 多section同号", "高一\\英语\\2019北京三十五中新高一分班考试英语含答案(1).md",
     "batch-C 卷:Q86-essay→96 唯一 basis=explicit 用例;汇编多 section"),
    # C10 题图与正文分离(material binding)
    ("pac-c10-01", "C10 题图分离", "高三\\物理\\2021北京石景山高三一模物理（教师版）(1).md",
     "pilot 已知:IMAGE_DANGLING;高考难度物理图题密集"),
    ("pac-c10-02", "C10 题图分离", "高三\\物理\\2022北京首都师大附中高三9月月考物理（教师版）(1).md",
     "batch-C 卷:物理图题 + 解析混排"),
    # C11 OCR 行融合(SectionLocator 攻击面)
    ("pac-c11-01", "C11 OCR行融合", "高一\\化学\\2021北京三十一中高一（下）期中化学（教师版）(1).md",
     "BUG-24/OCR LIMITATION 实证卷:L324 标题与 1.【答案】B 行融合;keep 三方裁决挂起件(独立事项)"),
    ("pac-c11-02", "C11 OCR行融合", "高二\\数学\\2023北京一六一中高二3月月考数学（教师版）(1).md",
     "融合实证:L137 分节标题+题1+【答案】B 三重行融合(全语料融合形态扫描命中)"),
    # C12 OCR 错号(转义点击穿,R38 台账行号锚定)
    ("pac-c12-01", "C12 OCR错号", "高二\\政治\\2018北京临川学校高二（下）期中政治含答案(1).md",
     "BUG-25 台账锚定:L266/L274 两条 ### 26 \\. 【答案】 转义点形态"),
    ("pac-c12-02", "C12 OCR错号", "高二\\物理\\2018北京东城高二（下）期末物理（教师版）(1).md",
     "BUG-25 台账锚定:L445/L461 两条 ### NN \\. 【解析】 转义点形态"),
    # C13 复杂 composite(question boundaries)
    ("pac-c13-01", "C13 composite", "高一\\地理\\2019北京人大附中高一（上）期中地理含答案.md",
     "pilot 已知:复合题最密集(16 个);FIG_REF_NO_IMAGE"),
    ("pac-c13-02", "C13 composite", "高一\\语文\\2020北京石景山高一（上）期末语文含答案.md",
     "pilot 已知:阅读复合题嵌套 + material 边界曾需人工修"),
]

BLOCKED = [
    {"category": "C3 DOCX", "status": "BLOCKED",
     "reason": "OCR 服务只吃 PDF;DOCX→PDF 归一路径未确认(用户裁定本轮缩范围只跑 PDF 类)"},
    {"category": "C4 JPG/PNG 图像", "status": "BLOCKED",
     "reason": "original 树独立 JPG/PNG 各仅 1 张;图像输入现实以扫描 PDF 承载(已由 C2 覆盖)"},
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_pdf(md_rel: str) -> Path | None:
    """按 basename 在 maintainess\\PDF(根+子目录)配对源 PDF。"""
    base = Path(md_rel).stem
    cand = PDF_ROOT / f"{base}.pdf"
    if cand.exists():
        return cand
    hits = list(PDF_ROOT.rglob(f"{base}.pdf"))
    return hits[0] if hits else None


def pdf_stats(pdf: Path) -> dict:
    """页数 + 文本层统计(fitz);区分原生文本/扫描。"""
    import fitz  # PyMuPDF

    doc = fitz.open(pdf)
    pages = doc.page_count
    chars = []
    for page in doc:
        chars.append(len(page.get_text("text").strip()))
    doc.close()
    total = sum(chars)
    nonempty = sum(1 for c in chars if c >= 50)
    kind = "native_text" if nonempty >= max(1, pages * 0.6) else "scanned"
    return {"pages": pages, "text_chars_total": total,
            "pages_with_text": nonempty, "text_layer": kind}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="只校验已留档 selection 的文件未漂移(sha256 复算)")
    args = ap.parse_args()

    if args.check:
        if not OUT.exists():
            sys.exit("selection 未留档,先跑不带 --check 的选样")
        old = json.loads(OUT.read_text(encoding="utf-8"))
        bad = []
        for row in old["samples"]:
            for key in ("pdf", "md_baseline"):
                p = Path(row[key]["path"])
                if not p.exists():
                    bad.append((row["sample_id"], key, "MISSING"))
                elif sha256(p) != row[key]["sha256"]:
                    bad.append((row["sample_id"], key, "SHA_DRIFT"))
        if bad:
            for b in bad:
                print("DRIFT:", b)
            sys.exit(1)
        print(f"OK: {len(old['samples'])} 份样本指纹全部一致")
        return

    samples = []
    errors = []
    for sid, cat, md_rel, hazard in PICKS:
        md = MD_ROOT / md_rel
        pdf = resolve_pdf(md_rel)
        if not md.exists():
            errors.append((sid, "md 不存在:", md_rel))
            continue
        if not pdf is None and not pdf.exists():
            pdf = None
        if pdf is None:
            errors.append((sid, "源 PDF 未配对:", md_rel))
            continue
        st = pdf_stats(pdf)
        samples.append({
            "sample_id": sid,
            "category": cat,
            "hazard_evidence": hazard,
            "pdf": {"path": str(pdf), "sha256": sha256(pdf), **st},
            "md_baseline": {"path": str(md), "sha256": sha256(md),
                            "lines": sum(1 for _ in open(md, encoding="utf-8", errors="replace"))},
        })
        print(f"[ok] {sid} {cat}: {st['pages']}p {st['text_layer']} <- {pdf.name}")

    if errors:
        for e in errors:
            print("ERROR:", *e)
        sys.exit(1)

    out = {
        "pac_version": 1,
        "note": "Production Adversarial Corpus 第一轮选样(用户批准:目标26份,本轮PDF类22份);"
                "OCR 重跑输入 = pdf 字段;md_baseline = 历史 OCR 产物,仅作漂移对比基线,不作流水线输入",
        "blocked_categories": BLOCKED,
        "samples": samples,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n留档: {OUT} ({len(samples)} 份)")


if __name__ == "__main__":
    main()

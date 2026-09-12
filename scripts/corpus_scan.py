# -*- coding: utf-8 -*-
r"""
corpus_scan.py — 全库源文件缺陷量化（只读，不改任何文件）。
统计两类已知 OCR 缺陷在全部源 .md 的规模，为全量重切推广定策略：
  1. 双重识别（difflib：同题号、行距<=4、相似度>=0.7）
  2. 裸 LaTeX（含 LaTeX 命令但整行无 $ 定界符）；细分简单/复杂行
结果写 data\corpus_scan.json 并打印汇总。
"""
import re, json, sys
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OCR = ROOT / "Ocr-markdown"
QNUM = re.compile(r'^\s*(\d{1,3})\s*[.、．]\s*(\S.*)$')
LATEX = re.compile(r'\\[a-zA-Z]+\{|\^\{|\_\{|\\xrightarrow|\\frac|\\sqrt|\\times|\\ce\b')
COMPLEX = re.compile(r'\\mathrm|\\xrightarrow|\\xleftarrow|\\text\{|\\underset|\\overset|\\ce\{|\\frac|\\begin')

def norm(s): return re.sub(r'[\s,。，、：:；;（）()]', '', s)

def scan_file(p):
    try:
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return None
    # 双重识别
    items = []
    for i, ln in enumerate(lines, 1):
        m = QNUM.match(ln)
        if m: items.append((i, m.group(1), m.group(2)))
    dup = []
    for a in range(len(items)):
        for b in range(a+1, len(items)):
            la, na, ca = items[a]; lb, nb, cb = items[b]
            if lb - la > 4: break
            if na != nb: continue
            x, y = norm(ca), norm(cb)
            if len(x) < 8 or len(y) < 8: continue
            if SequenceMatcher(None, x, y).ratio() >= 0.7:
                dup.append((la, lb, na))
    # 裸 LaTeX
    bare_simple, bare_complex = [], []
    for i, ln in enumerate(lines, 1):
        if "$" in ln: continue
        if LATEX.search(ln):
            (bare_complex if COMPLEX.search(ln) else bare_simple).append(i)
    return {"file": str(p), "dup": dup,
            "bare_simple": bare_simple, "bare_complex": bare_complex}

def main():
    files = [p for p in OCR.rglob("*.md")
             if "resliced-pilot" not in str(p) and "auto-annotated" not in str(p)
             and not p.name.endswith(".annotated.md")]
    print(f"扫描 {len(files)} 份源 .md ...")
    results = []
    tot_dup = tot_s = tot_c = 0
    files_dup = files_bare = 0
    for n, p in enumerate(files, 1):
        r = scan_file(p)
        if not r: continue
        results.append(r)
        if r["dup"]: files_dup += 1; tot_dup += len(r["dup"])
        if r["bare_simple"] or r["bare_complex"]:
            files_bare += 1; tot_s += len(r["bare_simple"]); tot_c += len(r["bare_complex"])
        if n % 500 == 0: print(f"  ...{n}/{len(files)}")
    out = {"total_files": len(files), "files_with_dup": files_dup, "dup_total": tot_dup,
           "files_with_bare": files_bare, "bare_simple_total": tot_s, "bare_complex_total": tot_c,
           "results": results}
    (ROOT / "data" / "corpus_scan.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n===== 全库缺陷量化 =====")
    print(f"源文件总数: {len(files)}")
    print(f"双重识别: {files_dup} 份文件、{tot_dup} 处")
    print(f"裸 LaTeX: {files_bare} 份文件（简单 {tot_s} 行 / 复杂 {tot_c} 行）")
    print("明细 → data/corpus_scan.json")

if __name__ == "__main__":
    main()

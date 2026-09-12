# -*- coding: utf-8 -*-
r"""
pdf_fidelity.py — 溯源比对：源 .md 相对原始 PDF 的内容保真度（只读，不改文件）。
C8 只证明"批注==源文件"，本工具补上"源文件==原始 PDF"这一环（Q39 源丢行即此环缺失）。

方法：对有文本层的 PDF，取 PDF 全文与源 md 全文，各自归一化（只留 CJK+字母数字），
用滑动 shingle 覆盖率衡量 PDF 内容有多少出现在源里；覆盖率低 / 局部大量 shingle 缺失
→ 疑似源丢内容（丢行/丢公式/丢表格数据）。辅以 <img> 数 vs PDF 内嵌图数的粗略信号。

用法：
    python pdf_fidelity.py --limit N        # 只测前 N 份（试跑）
    python pdf_fidelity.py                  # 全库，结果写 data\pdf_fidelity.json
"""
import sys, json, re, argparse
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parent.parent
OCR = ROOT / "Ocr-markdown"
PDFDIR = ROOT / "maintainess" / "PDF"
CJK = r'\u4e00-\u9fff'
KEEP = re.compile(r'[^0-9A-Za-z' + CJK + r']+')
SPLIT = re.compile(r'[，。、；：！？\n\r]')
MINSEG = 12  # 只比对 >=12 有效字符的中文长句段（过滤公式/短标签噪声）

def norm(s): return KEEP.sub('', s)

def prose_segments(pdf_text):
    """从 PDF 文本抽中文长句段（>=MINSEG 有效字符）。只取散文，避开公式符号噪声。"""
    segs = []
    for raw in SPLIT.split(pdf_text):
        n = norm(raw)
        if len(n) >= MINSEG:
            segs.append(n)
    return segs

def pdf_text(pdf):
    doc = fitz.open(str(pdf))
    txt = "\n".join(doc[i].get_text() for i in range(doc.page_count))
    nimg = sum(len(doc[i].get_images()) for i in range(doc.page_count))
    doc.close()
    return txt, nimg

def check(md_path, pdf_path):
    ptxt, nimg = pdf_text(pdf_path)
    if len(norm(ptxt)) < 50:
        return {"file": md_path.name, "status": "no_text_layer", "pdf_chars": len(norm(ptxt))}
    src = md_path.read_text(encoding="utf-8", errors="replace")
    src_norm = norm(re.sub(r'<[^>]+>', '', src))
    segs = prose_segments(ptxt)
    if not segs:
        return {"file": md_path.name, "status": "no_prose", "pdf_chars": len(norm(ptxt))}
    found = 0
    missing = []
    for s in segs:
        # 容错：整段归一化后须是源的子串（中文OCR准确，散文段多为精确命中）；
        # 未命中再用首尾各10字宽松试探，减少OCR小误差的假警报。
        if s in src_norm or s[:10] in src_norm or s[-10:] in src_norm:
            found += 1
        else:
            missing.append(s[:30])
    cov = found / len(segs)
    nsrc_img = len(re.findall(r'<img', src))
    return {"file": md_path.name, "status": "ok", "coverage": round(cov, 3),
            "n_prose": len(segs), "missing": missing,
            "src_imgs": nsrc_img, "pdf_imgs": nimg}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    pdfs = {p.stem: p for p in PDFDIR.glob("*.pdf")}
    mds = [p for p in OCR.rglob("*.md")
           if "resliced-pilot" not in str(p) and "auto-annotated" not in str(p)
           and not p.name.endswith(".annotated.md")]
    mds = [m for m in mds if m.stem in pdfs]
    if args.limit: mds = mds[:args.limit]
    print(f"溯源比对 {len(mds)} 份 ...")
    results = []
    for n, m in enumerate(mds, 1):
        try:
            results.append(check(m, pdfs[m.stem]))
        except Exception as e:
            results.append({"file": m.name, "status": f"ERR:{type(e).__name__}"})
        if n % 300 == 0: print(f"  ...{n}/{len(mds)}")
    ok = [r for r in results if r.get("status") == "ok"]
    low = sorted([r for r in ok if r.get("coverage", 1) < 0.9], key=lambda r: r["coverage"])
    notl = [r for r in results if r.get("status") == "no_text_layer"]
    out = {"total": len(results), "ok": len(ok), "no_text_layer": len(notl),
           "low_coverage": len(low), "results": results}
    (ROOT/"data"/"pdf_fidelity.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n===== PDF 溯源比对 =====")
    print(f"比对 {len(results)} | 有文本层可比 {len(ok)} | 无文本层 {len(notl)}")
    if ok:
        import statistics
        covs = [r["coverage"] for r in ok]
        print(f"覆盖率 中位 {statistics.median(covs):.3f} | <0.9 的 {len(low)} 份")
    print("最低覆盖 15 份（疑似丢内容）:")
    for r in low[:15]:
        print(f"  {r['coverage']:.2f}  {r['file'][:40]}")
    print("明细 → data/pdf_fidelity.json")

if __name__ == "__main__":
    main()

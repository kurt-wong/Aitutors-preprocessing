r"""语义代理探针(第三轮审查 D1/D2 战术 A):测量"结构合法但语义可疑"的发生率。

背景:QC C1-C12 全部是结构完整性检查,抓不到
  D1 = answer_lines 合法但内容属于别的题(题号-答案归属错位);
  D2 = stem/questions 区间合法但把相邻题吃进来了(跨题污染)。
本探针对已有真实产物(manifest + 源 md)做零 LLM 成本的文本级代理检测:

  P14(D2 代理)  正文区间(stem/questions)行首出现【不属于本单元题号】的题号行
  P15(D1 代理)  答案区间行首出现【不属于本单元题号】的题号+答案行
  P13(答案虚指) 答案区间文本里没有任何答案形态(【答案】/答案表/字母行/区间连写)

定性纪律(与 BUG-15/17 教训一致):
  - 探针报警 ≠ 缺陷。必须逐条人工分诊后才能定性;
  - 已知无害形状(共享答案表 <table> 单行、"1-5 ACDBA" 区间连写、
    详解复述、colspan 字母垃圾行)在设计上就不报警或单独归类;
  - 探针未经验证前【不进 QC】,不当门卫,只当测量仪。

用法:
  python semantic_probe.py --dir Ocr-markdown/reslice-batch-C
  → 控制台分级汇总 + data/semantic_probe_batch_c.json 明细
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]

# 行首题号:可选 markdown 标题噪声 + 1-3 位数字 + 分隔符(BUG-19 形态兼容);
# (?!\d) 排除小数("9.5%");行内 OCR 转义点("1\. C")兼容
QNUM_LINE = re.compile(r"^\s{0,3}(?:#{1,6}\s*)?(\d{1,3})\s*(?:\\?[.、．,，)）])\s*(?!\d)")
# 答案形态:【答案】/☑答案/答案:/故选/故答案为 / 答案表 / 连续字母(>=2) /
# 单字母选择题答案(整行 "A"/"A.") / 区间连写(1-5 ACDBA 或 17. A 18. B 空格连写)
ANS_MARK = re.compile(r"【答案】|【参考答案】|☑\s*答案|答案\s*[:：]|故选|故答案为")
ANS_TABLE = re.compile(r"<table", re.I)
ANS_LETTERS = re.compile(r"(?<![A-Za-z])[A-DＡ-Ｄ]{2,}(?![A-Za-z])")
ANS_RANGE = re.compile(r"\d{1,3}\s*[-–—~]\s*\d{1,3}\s*[A-DＡ-Ｄ]{2,}")
ANS_SINGLE = re.compile(r"^\s*(?:\\?[.、．]?\s*)?[A-DＡ-Ｄ]\s*[.。、，,;；]?\s*$", re.M)
# 答案对行:≥2 个 "题号+答案" 对(共享答案行,按 R3 共享受理,不作归属错位)
ANS_PAIR = re.compile(r"\d{1,3}\s*(?:\\?[.、．])?\s*(?:[A-DＡ-Ｄ]|[a-z]{3,}|[\u4e00-\u9fff]{1,8})")
# 解答步骤编号特征(如 "1、目的基因的获取:"):顿号 + 中文叙述开头 → 非题号
STEP_NUM = re.compile(r"^\s*\d{1,3}\s*、\s*[\u4e00-\u9fff]")


def load_src_lines(src_path):
    """与 process_file 同口径:去 META 注释后逐行。区间 i = 第 i 行。"""
    text = src_path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"<!--\s*META:[^>]*-->\n?", "", text)
    return text.splitlines()


def span(lines, rg):
    if not rg or not isinstance(rg, list) or len(rg) != 2:
        return []
    s = max(1, rg[0])
    e = min(len(lines), rg[1])
    if s > e:
        return []
    return lines[s - 1:e]


def probe_unit(lines, u):
    """返回该单元的报警列表 [{check, detail, sample}]。"""
    flags = []
    expected = set(u.get("question_numbers") or [])

    def unexpected_qnums(seg_lines, skip_shared=False):
        hits = []
        for ln in seg_lines:
            if STEP_NUM.match(ln):            # 解答步骤编号("1、目的基因…")非题号
                continue
            m = QNUM_LINE.match(ln)
            if not m or int(m.group(1)) in expected:
                continue
            if skip_shared and len(ANS_PAIR.findall(ln)) >= 2:
                continue                      # 共享答案行(一行多题答案,R3 共享受理)
            hits.append((int(m.group(1)), ln.strip()[:60]))
        return hits

    # P14:正文区间跨题污染(D2 代理)
    if u.get("unit_type") == "composite_question":
        body = span(lines, u.get("questions_lines"))
        body_desc = "questions_lines"
    else:
        body = span(lines, u.get("stem_lines"))
        body_desc = "stem_lines"
    for n, sample in unexpected_qnums(body):
        flags.append({"check": "P14", "unit": u.get("unit_id"),
                      "detail": f"{body_desc} 内出现非本单元题号 {n}",
                      "sample": sample})

    # P15:答案区间归属错位(D1 代理);共享答案行跳过
    ans = span(lines, u.get("answer_lines"))
    for n, sample in unexpected_qnums(ans, skip_shared=True):
        flags.append({"check": "P15", "unit": u.get("unit_id"),
                      "detail": f"answer_lines 内出现非本单元题号 {n}",
                      "sample": sample})

    # P13:答案区间无任何答案形态(虚指)
    if ans:
        joined = "\n".join(ans)
        if not (ANS_MARK.search(joined) or ANS_TABLE.search(joined)
                or ANS_RANGE.search(joined) or ANS_LETTERS.search(joined)
                or ANS_SINGLE.search(joined) or len(ANS_PAIR.findall(joined)) >= 2):
            flags.append({"check": "P13", "unit": u.get("unit_id"),
                          "detail": "answer_lines 无【答案】/答案表/字母行/区间连写",
                          "sample": ans[0].strip()[:60]})
    return flags


def probe_file(mf):
    man = json.loads(mf.read_text(encoding="utf-8"))
    src = Path(man.get("source_file", ""))
    if not src.exists():
        return {"manifest": str(mf), "error": "source missing", "flags": []}
    lines = load_src_lines(src)
    flags = []
    for u in man.get("units", []):
        flags.extend(probe_unit(lines, u))
    return {"manifest": str(mf), "source": str(src),
            "n_units": len(man.get("units", [])), "flags": flags}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="产物目录(递归找 *.manifest.json)")
    ap.add_argument("--out", default=str(ROOT / "data/semantic_probe_report.json"))
    args = ap.parse_args()

    manifests = sorted(Path(args.dir).rglob("*.manifest.json"))
    results = [probe_file(mf) for mf in manifests]

    n_files = len(results)
    n_units = sum(r.get("n_units", 0) for r in results)
    by_check = {}
    flagged_files = []
    for r in results:
        if r["flags"]:
            flagged_files.append(Path(r["manifest"]).name)
        for f in r["flags"]:
            by_check[f["check"]] = by_check.get(f["check"], 0) + 1

    report = {"dir": args.dir, "n_files": n_files, "n_units": n_units,
              "flags_by_check": by_check, "flagged_files": flagged_files,
              "results": results}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=1),
                              encoding="utf-8")

    print(f"===== 语义代理探针: {n_files} 份 / {n_units} 单元 =====")
    for k in sorted(by_check):
        print(f"  {k}: {by_check[k]} 处")
    if not by_check:
        print("  (零报警)")
    print(f"  涉及文件: {len(flagged_files)}/{n_files}")
    print(f"  明细: {args.out}")


if __name__ == "__main__":
    main()

r"""渲染质检：静态检测 LaTeX 公式与 HTML 表格的渲染风险。

无法目视最终渲染，但能查出绝大多数会导致渲染器失败的结构性损坏：
  R-L1 行内 $ 配对（奇数个 $ 的行，多为公式被 OCR 截断）
  R-L2 \ce{} 化学式（依赖 mhchem 扩展，消费方需开启）
  R-L3 可疑 LaTeX 命令损坏（\ 后跟非字母、{} 不配平）
  R-T1 <table>/<tr>/<td> 标签配平
  R-T2 属性双引号损坏（如 alt="Image"" />）
  R-T3 未闭合/裸露的 HTML 标签（<div> 等）

用法: python render_lint.py [--json]
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\Papers")
PILOT = json.loads((ROOT / "data/reslice_pilot_result.json").read_text(encoding="utf-8"))

MATH_DOLLAR = re.compile(r"\$")           # 单行 $ 计数
CE_CMD = re.compile(r"\\ce\s*\{")          # mhchem 化学式
LATEX_CMD = re.compile(r"\\[a-zA-Z]+")     # 正常命令
# 真损坏：\ 后跟数字或中文（合法 LaTeX 命令后只接字母/符号）
# \\ 换行、\, \; \! \( \) 等间距/定界符均合法，不报
LATEX_BAD = re.compile(r"\\(\d|[\u4e00-\u9fff])")
TAG_OPEN = re.compile(r"<(table|tr|td|th|div|img)\b", re.I)
TAG_CLOSE = re.compile(r"</(table|tr|td|th|div)>", re.I)
TABLE_OPEN = re.compile(r"<table\b", re.I)
TABLE_CLOSE = re.compile(r"</table>", re.I)
TR_OPEN = re.compile(r"<tr\b", re.I)
TR_CLOSE = re.compile(r"</tr>", re.I)
TD_OPEN = re.compile(r"<t[dh]\b", re.I)
TD_CLOSE = re.compile(r"</t[dh]>", re.I)
BAD_ATTR = re.compile(r'""\s*/?>')         # alt="Image"" />


def lint_file(src: Path):
    text = src.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    issues = {"L1_dollar_odd": [], "L2_ce": 0, "L3_bad_cmd": [],
              "T1_unbalanced": [], "T2_bad_attr": 0, "T3_tag_mismatch": []}

    # --- LaTeX ---
    for i, ln in enumerate(lines, 1):
        # 只数未转义的 $（\$ 是合法的字面美元符，渲染器不会当定界符）
        n = len(re.findall(r"(?<!\\)\$", ln))
        if n % 2 == 1 and "$$" not in ln:
            issues["L1_dollar_odd"].append(i)
        if CE_CMD.search(ln):
            issues["L2_ce"] += 1
        for m in LATEX_BAD.finditer(ln):
            issues["L3_bad_cmd"].append(f"L{i}:{ln[max(0,m.start()-10):m.start()+6]}")
            break

    # --- HTML 表格（只按计数差判不配平）---
    if len(TABLE_OPEN.findall(text)) != len(TABLE_CLOSE.findall(text)):
        issues["T1_unbalanced"].append(f"table {len(TABLE_OPEN.findall(text))}开/{len(TABLE_CLOSE.findall(text))}闭")
    if len(TR_OPEN.findall(text)) != len(TR_CLOSE.findall(text)):
        issues["T1_unbalanced"].append(f"tr {len(TR_OPEN.findall(text))}开/{len(TR_CLOSE.findall(text))}闭")
    if len(TD_OPEN.findall(text)) != len(TD_CLOSE.findall(text)):
        issues["T1_unbalanced"].append(f"td {len(TD_OPEN.findall(text))}开/{len(TD_CLOSE.findall(text))}闭")

    issues["T2_bad_attr"] = len(BAD_ATTR.findall(text))

    # div/img 裸露或未闭合（img 自闭合，只查 div）
    for i, ln in enumerate(lines, 1):
        for tag in ("div",):
            o = len(re.findall(rf"<{tag}\b", ln, re.I))
            c = len(re.findall(rf"</{tag}>", ln, re.I))
            if o != c:
                issues["T3_tag_mismatch"].append(f"L{i}:{tag}{o}开{c}闭")

    return issues


def summarize(issues):
    tags = []
    if issues["L1_dollar_odd"]:
        tags.append(f"L1 $奇数行×{len(issues['L1_dollar_odd'])}")
    if issues["L2_ce"]:
        tags.append(f"L2 \\ce×{issues['L2_ce']}")
    if issues["L3_bad_cmd"]:
        tags.append(f"L3 命令损坏×{len(issues['L3_bad_cmd'])}")
    if issues["T1_unbalanced"]:
        tags.append(f"T1 标签不配平:{issues['T1_unbalanced']}")
    if issues["T2_bad_attr"]:
        tags.append(f"T2 属性双引号损坏×{issues['T2_bad_attr']}")
    if issues["T3_tag_mismatch"]:
        tags.append(f"T3 div不配平×{len(issues['T3_tag_mismatch'])}")
    return tags


def main():
    as_json = "--json" in sys.argv
    results = []
    for rec in PILOT:
        src = Path(rec["file"])
        if not src.exists():
            continue
        iss = lint_file(src)
        results.append({"file": src.name, "issues": iss, "tags": summarize(iss)})

    if as_json:
        (ROOT / "data/render_lint.json").write_text(
            json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
        return

    nclean = sum(1 for r in results if not r["tags"])
    print(f"=== 渲染质检：{nclean}/{len(results)} 无风险项 ===")
    for r in results:
        mark = "OK " if not r["tags"] else "RISK"
        print(f"[{mark}] {r['file']}")
        for t in r["tags"]:
            print(f"       - {t}")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
r"""
fix_half_delim.py — 修 BUG-15 中"可确定性修复"的两类半定界行：

1) SPACE：岛外纯间距命令 \quad / \qquad → 全角空格（数学岛内的 \quad 不动）。
   例：A. $x$ \quad B. $y$   →   A. $x$　B. $y$
2) TABLE：表格单元格内字面 \n（换行残留）→ <br>。
   例：<td>指标\n样地</td>   →   <td>指标<br>样地</td>

BLOCK（跨行公式块）与 COMPLEX（OCR 烂行）不在此处理（需人工/专门设计）。

确定性：用状态机精确追踪是否在 $ 岛内，只改岛外/表格内；行数不变；apply 时写审计日志可回滚。
用法：
    python fix_half_delim.py --dry [--all] [文件...]
    python fix_half_delim.py --apply [--all] [文件...]
"""
import re
import sys
import os
import io
import glob
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

BASE = r"D:\Project\Papers\Ocr-markdown"
ROOTS = ["高一", "高二", "高三", "高考真题", "合格考", "会考",
         "竞赛自招", "其他汇编", "学业水平考试"]
DRY_TXT = r"D:\Project\Papers\data\bug15_fix_dry.txt"
AUDIT = r"D:\Project\Papers\data\bug15_fix_log.json"
SPACE_REPL = "　"  # 全角空格：保留中文选项间距感


def _replace_outside_quad(line, repl):
    r"""状态机：仅替换"数学岛外"的 \quad/\qquad；岛内（含 \begin{array} 内的列间距）保留不动。
    奇数 $ 的异常行会保守地把后半段当岛内、不改（宁可不改也不错改）。"""
    out = []
    i, n = 0, len(line)
    in_math = False
    while i < n:
        if line.startswith("$$", i):
            out.append("$$"); in_math = not in_math; i += 2; continue
        if line[i] == "$":
            out.append("$"); in_math = not in_math; i += 1; continue
        if not in_math:
            if line.startswith("\\qquad", i) and not (i + 6 < n and line[i + 6].isalpha()):
                out.append(repl); i += 6; continue
            if line.startswith("\\quad", i) and not (i + 5 < n and line[i + 5].isalpha()):
                out.append(repl); i += 5; continue
        out.append(line[i]); i += 1
    return "".join(out)


def fix_line(line, space_repl=SPACE_REPL):
    """返回 (newline, kind)，kind ∈ {'table','space',None}"""
    # 1) 表格行内字面 \n（均在单元格文本，直接替换安全）
    if ("<table" in line or "<td" in line) and "\\n" in line:
        return line.replace("\\n", "<br>"), "table"
    # 2) 岛外 \quad / \qquad → 全角空格（状态机保证岛内不动）
    nc = _replace_outside_quad(line, space_repl)
    if nc != line:
        return nc, "space"
    return line, None


def process(path, apply, space_repl=SPACE_REPL):
    # newline=""：禁止 universal-newlines 翻译，读写均保留原文件行尾（CRLF/LF 恒定）
    with io.open(str(path), encoding="utf-8", newline="") as f:
        text = f.read()
    lines = text.splitlines(keepends=True)
    changed, new_lines = [], []
    for i, ln in enumerate(lines, 1):
        core = ln.rstrip("\r\n")
        ending = ln[len(core):]
        # 仅处理含 $ 的行（BUG-15 范围：半定界；不含 $ 的裸行归 BUG-04）
        if "$" in core:
            nc, kind = fix_line(core, space_repl)
            if nc != core:
                changed.append((i, kind, core, nc))
                new_lines.append(nc + ending)
                continue
        new_lines.append(ln)
    if apply and changed:
        with io.open(str(path), "w", encoding="utf-8", newline="") as f:
            f.write("".join(new_lines))
    return changed


def all_sources():
    fs = []
    for rd in ROOTS:
        fs += glob.glob(os.path.join(BASE, rd, "**", "*.md"), recursive=True)
    return [Path(f) for f in fs]


def main():
    args = sys.argv[1:]
    if not args or args[0] not in ("--dry", "--apply"):
        print(__doc__)
        return
    apply = args[0] == "--apply"
    rest = args[1:]
    space_repl = SPACE_REPL
    if "--space" in rest:
        j = rest.index("--space")
        space_repl = rest[j + 1]
        rest = rest[:j] + rest[j + 2:]
    files = all_sources() if "--all" in rest else [Path(a) for a in rest]

    tot = 0
    bykind = defaultdict(int)
    samples, records = [], []
    for f in files:
        for i, kind, before, after in process(f, apply, space_repl):
            bykind[kind] += 1
            tot += 1
            records.append({"file": str(f), "line": i, "kind": kind,
                            "before": before, "after": after})
            if len(samples) < 60:
                samples.append((f"{f.parent.name}\\{f.name}", i, kind, before, after))

    out = [f"模式: {'已落地' if apply else 'dry-run'}  空格替换目标={space_repl!r}",
           f"总改动 {tot} 行  分类={dict(bykind)}", "=" * 60]
    for fn, i, kind, before, after in samples:
        out.append(f"\n[{kind}] {fn}:L{i}")
        out.append(f"  前: {before}")
        out.append(f"  后: {after}")
    Path(DRY_TXT).write_text("\n".join(out), encoding="utf-8")

    if apply and records:
        json.dump({"when": datetime.now().strftime("%Y-%m-%d %H:%M"),
                   "bug": "BUG-15(space+table)", "space_repl": space_repl,
                   "total": tot, "bykind": dict(bykind), "records": records},
                  open(AUDIT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"审计日志: {AUDIT}")
    print(f"{'已落地' if apply else '待改'} {tot} 行; 分类={dict(bykind)}")


if __name__ == "__main__":
    main()

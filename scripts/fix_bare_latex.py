# -*- coding: utf-8 -*-
r"""
fix_bare_latex.py — 给源 markdown 里"含 LaTeX 但无 $ 定界符"的裸公式补 $...$ 包裹。
确定性：只在既有 LaTeX 词元外加 $，不改任何公式内容本身。

规则：
- LaTeX 词元 = 极大连续 run（字符集 [A-Za-z0-9\{}_^().=+-]，不含空格/CJK/$），
  且 run 内含信号：反斜杠命令(\xxx) 或 _{ 或 ^{。
- 每个满足信号的 run 单独包 $...$（CJK 天然在 run 边界断开，故中文不入内）。
- 跳过已含 $ 的行。

用法：
    python fix_bare_latex.py --dry <文件...>   # 只打印改前/改后，不写盘
    python fix_bare_latex.py --apply <文件...> # 落地（行数不变，无需重映射）
"""
import re
import sys
import io
from pathlib import Path

# 词元字符集：字母数字 + LaTeX 结构符号（不含空格、CJK、$）
TOKEN_CHARS = r"A-Za-z0-9\{\}\^\_\(\)\.\=\+\-"
SIGNAL = re.compile(r'\\[a-zA-Z]|\_\{|\^\{')
# 复杂排版命令：含括号参数/布局，朴素词元器会切乱，跳过交由手工整段包 $（如 \xrightarrow[..]{..}、\mathrm{..}）
COMPLEX = re.compile(r'\\mathrm|\\xrightarrow|\\xleftarrow|\\text\{|\\underset|\\overset|\\ce\{|\\frac|\\begin')
# 收紧的词元核心：基(字母数字/反斜杠) + 一个或多个 _{...}/^{...} 组（可带尾随基字符，如 Na_{2}SO_{4}）。
# 刻意不含外围括号/句号/等号，避免把句读吞进 $ 内（此前宽松版会产出 ($X_{CH4})$ 这类错位）。
TOKEN = re.compile(r'[A-Za-z0-9\\]+(?:[_^]\{[^{}]*\}[A-Za-z0-9]*)+')
# 裸命令检测（BUG-09 防回归）：把数学岛 $...$ 抹掉后，若仍残留 \命令，则说明包裹不完整。
BARE_CMD = re.compile(r'\\[a-zA-Z]+')


def wrap_line(line: str) -> str:
    """把一行里的裸 LaTeX 词元包 $...$（仅紧凑核心，不动外围标点）。"""
    if "$" in line:
        return line
    def repl(m):
        tok = m.group(0)
        if SIGNAL.search(tok) and "$" not in tok:
            return "$" + tok + "$"
        return tok
    return TOKEN.sub(repl, line)


def process(path: Path, apply: bool):
    # newline=""：禁止 universal-newlines 翻译，读写均保留原文件行尾（CRLF/LF 恒定）
    with io.open(str(path), encoding="utf-8", newline="") as f:
        text = f.read()
    lines = text.splitlines(keepends=True)
    changed = []
    new_lines = []
    for i, ln in enumerate(lines, 1):
        core = ln.rstrip("\r\n")
        ending = ln[len(core):]
        if "$" not in core and SIGNAL.search(core) and not COMPLEX.search(core):
            wrapped = wrap_line(core)
            # BUG-09 防回归：仅当包裹后"数学岛外无残留 \命令"时才落地；
            # 否则整行保留裸形态（交人工/半自动整段包 $），绝不产出部分包裹的残损行。
            if wrapped != core and not BARE_CMD.search(re.sub(r"\$[^$]*\$", "", wrapped)):
                changed.append((i, core, wrapped))
                new_lines.append(wrapped + ending)
                continue
        new_lines.append(ln)
    if apply and changed:
        with io.open(str(path), "w", encoding="utf-8", newline="") as f:
            f.write("".join(new_lines))
    return changed


def main():
    args = sys.argv[1:]
    if not args or args[0] not in ("--dry", "--apply"):
        print(__doc__); return
    apply = args[0] == "--apply"
    files = [Path(a) for a in args[1:]]
    total = 0
    for f in files:
        ch = process(f, apply)
        if ch:
            print(f"\n===== {f.parent.name}\\{f.name} : {len(ch)} 行 =====")
            for ln, before, after in ch:
                print(f"L{ln} 改前: {before}")
                print(f"     改后: {after}")
            total += len(ch)
    print(f"\n合计 {'已修改' if apply else '待修改'} {total} 行")


if __name__ == "__main__":
    main()

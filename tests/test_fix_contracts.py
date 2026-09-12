# -*- coding: utf-8 -*-
"""修复脚本契约测试(固化 R25 对 ChatGPT「修复层叠加风险」的回应):
每个 fixer 必须满足三元契约——
  1) 修复目标生效(合成反例上可复现)
  2) 幂等(第二次运行 0 修改)
  3) 不触碰无关数据
全部经 subprocess 跑真实命令行(与生产同路径),不 import 内部函数仿造。
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import SYNTH_LINES, SYNTH_MAN, make_repo

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def run_fix(script, out_dir, log_path, apply=True):
    """真实命令行跑 fixer,返回 (exit_code, stdout)。"""
    cmd = [sys.executable, str(SCRIPTS / script),
           "--out", str(out_dir), "--log", str(log_path)]
    if apply:
        cmd.append("--apply")
    p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=120)
    return p.returncode, p.stdout + p.stderr


# ---------- fix_orphan_imgs:题前图并入 + 幂等 ----------

def test_orphan_img_merged_into_stem(workdir):
    # 用变体 man:Q1 stem [6,9] → L5 图成为孤儿(默认 synth 已覆盖图)
    from conftest import SYNTH_MAN
    man_orphan = json.loads(json.dumps(SYNTH_MAN))
    man_orphan["units"][0]["stem_lines"] = [6, 9]
    src, mf, out = make_repo(workdir, man=man_orphan)
    man = json.loads(mf.read_text(encoding="utf-8"))
    assert man["units"][0]["stem_lines"] == [6, 9]     # 前置条件:图未覆盖

    log1 = workdir / "l1.json"
    rc, _ = run_fix("fix_orphan_imgs.py", out, log1)
    assert rc == 0
    log = json.loads(log1.read_text(encoding="utf-8"))
    assert log["summary"]["merge"] == 1

    man2 = json.loads(mf.read_text(encoding="utf-8"))
    assert man2["units"][0]["stem_lines"] == [5, 9]    # 图已并入 stem

    # 幂等:第二次 0 修改
    log2 = workdir / "l2.json"
    rc, _ = run_fix("fix_orphan_imgs.py", out, log2)
    assert rc == 0
    assert json.loads(log2.read_text(encoding="utf-8"))["summary"]["merge"] == 0
    assert json.loads(mf.read_text(encoding="utf-8"))["units"][0]["stem_lines"] == [5, 9]


# ---------- fix_heading_qnum:区间内剥离标题前缀 + 区间外保留 + 幂等 ----------

def _lines_heading():
    lines = list(SYNTH_LINES)
    lines[5] = "### 1. 下列说法正确的是（ ）"   # L6 在 Q1 区间内 → 应剥
    lines[23] = "## 3. 参考答案"               # L24 在所有区间外 → 应留
    return lines


def test_heading_prefix_strip_inside_keeps_outside(workdir):
    src, mf, out = make_repo(workdir, lines=_lines_heading())
    log1 = workdir / "l1.json"
    rc, _ = run_fix("fix_heading_qnum.py", out, log1)
    assert rc == 0
    log = json.loads(log1.read_text(encoding="utf-8"))
    assert log["summary"]["strip"] == 1
    assert log["summary"]["keep_structure"] == 1

    # fix_heading_qnum 编辑的是源 md(非切片),检查源文件
    src_text = src.read_text(encoding="utf-8")
    # 区间内标题前缀已剥:不应再有 "### 1.",应有裸 "1."
    assert "### 1." not in src_text
    assert "1. 下列说法正确的是" in src_text
    # 区间外结构标题保留
    assert "## 3. 参考答案" in src_text

    # 幂等
    log2 = workdir / "l2.json"
    rc, _ = run_fix("fix_heading_qnum.py", out, log2)
    assert rc == 0
    assert json.loads(log2.read_text(encoding="utf-8"))["summary"]["strip"] == 0


# ---------- fix_explanation_prefix:题号复述收缩到标记行 + 幂等 ----------

def _repo_explanation_repeat(workdir):
    lines = [
        "# 标题", "", "## 选择", "",
        "1. 下列说法正确的是（ ）",     # L5 stem [5,5]
        "A. 甲",                        # L6 options [6,6]
        "",                             # L7
        "1. 下列说法正确的是（ ）",     # L8 explanation 复述 [8,9]
        "【解答】解析正文。",           # L9
        "1.【答案】A",                  # L10 answer [10,10]
    ]
    man = {"units": [
        {"unit_id": "Q1", "unit_type": "standalone_question",
         "question_numbers": [1], "original_question_type": "single_choice",
         "stem_lines": [5, 5], "options_lines": [6, 6],
         "answer_lines": [10, 10], "explanation_lines": [8, 9]}]}
    return make_repo(workdir, lines=lines, man=man)


def test_explanation_prefix_shrinks_and_idempotent(workdir):
    src, mf, out = _repo_explanation_repeat(workdir)
    log1 = workdir / "l1.json"
    rc, _ = run_fix("fix_explanation_prefix.py", out, log1)
    assert rc == 0
    assert json.loads(log1.read_text(encoding="utf-8"))["summary"]["fix"] == 1
    man = json.loads(mf.read_text(encoding="utf-8"))
    assert man["units"][0]["explanation_lines"] == [9, 9]   # 复述行已收缩掉

    log2 = workdir / "l2.json"
    rc, _ = run_fix("fix_explanation_prefix.py", out, log2)
    assert rc == 0
    assert json.loads(log2.read_text(encoding="utf-8"))["summary"]["fix"] == 0
    assert json.loads(mf.read_text(encoding="utf-8"))["units"][0]["explanation_lines"] == [9, 9]

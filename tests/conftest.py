# -*- coding: utf-8 -*-
"""pytest 共享 fixture:合成微型试卷 + 完整切片产物生成。

设计原则(R25 固化 ChatGPT 第一轮审查要求):
- 不依赖真实题库数据(版权+可控性),全部自造合成;
- make_repo() 生成与生产完全同构的产物(manifest/annotated/切片)——
  测试跑的是真实代码路径(write_outputs/QC/fix 脚本),不是仿制品。
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import reslice_pipeline as rp  # noqa: E402

# 合成试卷:30 行,覆盖场景——题前图(L5)、独立题×2、共享材料综合题(2 子题)、
# 独立【答案】行、详解区。
SYNTH_LINES = [
    "# 2024 合成测试卷",                  # L1
    "",                                   # L2
    "## 一、选择题",                      # L3
    "",                                   # L4
    '<div><img src="box_100_100_200_200.jpg" /></div>',   # L5 题前图(Q1 的图)
    "1. 下列说法正确的是（ ）",           # L6
    "",                                   # L7
    "A. 甲",                              # L8
    "B. 乙",                              # L9
    "",                                   # L10
    "2. 第二题题干（ ）",                 # L11
    "A. 一",                              # L12
    "B. 二",                              # L13
    "",                                   # L14
    "## 二、综合题",                      # L15
    "阅读下列材料:",                      # L16
    "材料内容甲乙丙。",                   # L17
    "",                                   # L18
    "3. 依据材料,下列正确的是（ ）",      # L19
    "A. ①",                              # L20
    "4. 依据材料,错误的是（ ）",          # L21
    "A. 甲",                              # L22
    "",                                   # L23
    "## 参考答案",                        # L24
    "1.【答案】A",                        # L25
    "",                                   # L26
    "【解析】第一题解析正文。",           # L27
    "2.【答案】B",                        # L28
    "",                                   # L29
    "【解析】第二题解析正文。",           # L30
    "3.【答案】C",                        # L31
    "4.【答案】D",                        # L32
]

SYNTH_MAN = {
    "units": [
        {"unit_id": "Q1", "unit_type": "standalone_question",
         "question_numbers": [1], "original_question_type": "single_choice",
         "stem_lines": [5, 9], "options_lines": [8, 9],
         "answer_lines": [25, 25], "explanation_lines": [27, 27]},
        {"unit_id": "Q2", "unit_type": "standalone_question",
         "question_numbers": [2], "original_question_type": "single_choice",
         "stem_lines": [11, 13], "options_lines": [12, 13],
         "answer_lines": [28, 28], "explanation_lines": [30, 30]},
        {"unit_id": "U3-4", "unit_type": "composite_question",
         "question_numbers": [3, 4], "original_question_type": "short_answer",
         "material_lines": [16, 17], "questions_lines": [19, 22],
         "answer_lines": [31, 32], "explanation_lines": None},
    ]
}


def make_repo(tmp_path, lines=None, man=None, src_name="synthetic.md"):
    """在 tmp_path 生成与生产同构的产物:源 md + manifest + annotated + 切片。

    返回 (src_path, manifest_path, out_dir)。
    """
    lines = list(lines if lines is not None else SYNTH_LINES)
    man = json.loads(json.dumps(man if man is not None else SYNTH_MAN))
    src = tmp_path / src_name
    src.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="")
    out_dir = tmp_path / "out"
    out_dir.mkdir(exist_ok=True)
    stem = src.stem
    mf = out_dir / f"{stem}.manifest.json"
    man_full = dict(man)
    man_full["source_file"] = str(src)
    mf.write_text(json.dumps(man_full, ensure_ascii=False, indent=1),
                  encoding="utf-8", newline="")
    issues, summary = rp.validate_manifest(man, len(lines), lines)
    rp.write_outputs(out_dir, stem, lines, man, issues, summary, src.name, src)
    return src, mf, out_dir


@pytest.fixture
def workdir():
    """仓库内自管临时目录(函数级)。

    DSH 沙箱下系统 temp 不可写(WinError 5),pytest 内建 tmp_path 不可用;
    本 fixture 在 .pytest_work/ 下建唯一子目录,清理 best-effort(沙箱可能禁删)。
    """
    import shutil
    import uuid
    base = ROOT / ".pytest_work"
    base.mkdir(exist_ok=True)
    d = base / uuid.uuid4().hex[:8]
    d.mkdir()
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def synth_repo(workdir):
    """标准合成试卷产物(默认态)。"""
    return make_repo(workdir)

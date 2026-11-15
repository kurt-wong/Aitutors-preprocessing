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
    "identity_version": 1,
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


def attach_json_evidence(man, src_path):
    """E-1 后 recompile/门禁需合法双源输入：同目录 jsonl + 一致性 json_evidence。

    按源 md 逐非空行造块并计算映射/摘要/单元指针（与正式链同构），
    写入 man.annotation_meta.json_evidence 并返回 jsonl 路径。
    """
    import hashlib
    import json_evidence_map

    src_path = Path(src_path)
    lines = src_path.read_text(encoding="utf-8", errors="replace").splitlines()
    blocks, bid = [], 0
    for i, ln in enumerate(lines):
        if not ln.strip():
            continue
        blocks.append({
            "block_label": "text", "block_content": ln,
            "block_bbox": json.dumps([10, 20 + i * 10, 500, 30 + i * 10]),
            "block_id": bid, "block_order": bid + 1, "group_id": bid,
            "block_polygon_points": "[]",
        })
        bid += 1
    jl = src_path.parent / f"{src_path.stem}.ocr_raw.jsonl"
    jl.write_text(json.dumps({
        "logId": "fixture", "errorCode": 0, "errorMsg": "Success",
        "result": {"layoutParsingResults": [{
            "prunedResult": {"width": 1000, "height": 1400,
                             "parsing_res_list": blocks,
                             "layout_det_res": {"boxes": []}},
            "markdown": {"text": "", "images": {}}}],
            "dataInfo": {"numPages": 1}},
    }, ensure_ascii=False), encoding="utf-8")
    ev = json_evidence_map.build_line_evidence("\n".join(lines), jl)
    man.setdefault("annotation_meta", {})
    man["annotation_meta"]["json_evidence"] = {
        "map_sha256": json_evidence_map.evidence_digest(ev),
        "jsonl_file": jl.name,
        "page_count_md": ev["page_count_md"],
        "page_count_json": ev["page_count_json"],
        "page_split_consistent": ev["page_split_consistent"],
        "match_counts": ev["match_counts"],
        "unmapped_lines": ev["unmapped_lines"],
        "unmapped_blocks": ev["unmapped_blocks"],
        "skipped_blocks": ev["skipped_blocks"],
        "evidence_marker_count": 0,
        "units": json_evidence_map.unit_evidence_pointers(ev, man.get("units", [])),
        "md_sha256": hashlib.sha256(src_path.read_bytes()).hexdigest(),
        "json_sha256": hashlib.sha256(jl.read_bytes()).hexdigest(),
        "prompt_sha256": "fixture-no-prompt-run-anchor",
    }
    return jl


def make_repo(tmp_path, lines=None, man=None, src_name="synthetic.md"):
    """在 tmp_path 生成与生产同构的产物:源 md + 同目录 ocr_raw.jsonl + manifest
    + annotated + 切片（E-1 后 recompile 需合法双源输入，夹具同构补齐）。

    返回 (src_path, manifest_path, out_dir)。
    """
    lines = list(lines if lines is not None else SYNTH_LINES)
    man = json.loads(json.dumps(man if man is not None else SYNTH_MAN))
    src = tmp_path / src_name
    src.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="")
    attach_json_evidence(man, src)
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

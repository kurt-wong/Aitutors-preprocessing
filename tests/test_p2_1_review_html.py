# -*- coding: utf-8 -*-
"""P2.1-d 审核 HTML 生成器最小钉(人工审核界面,禁 LLM 分类)。"""

import importlib.util
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = _load("p21rh", os.path.join(ROOT, "scripts", "p2_1_review_html.py"))
M = _load("p21m_rh", os.path.join(ROOT, "scripts", "p2_1_measure.py"))


def _item(workdir):
    src = workdir / "src"
    (src / "高一" / "物理").mkdir(parents=True, exist_ok=True)
    lines = [
        "12. 实验题干",
        '<div><img src="../../_imgs/p/img1.jpg" alt="Image" width="20%" /></div>',
        "（1）小问一",
        '<script>alert(1)</script>',
        "13. 答案区题",
    ]
    (src / "高一" / "物理" / "a.md").write_text("\n".join(lines), encoding="utf-8")
    return src, {"file": str(src / "高一" / "物理" / "a.md"), "subject": "物理",
                 "unit_id": "C12", "question_numbers": [12],
                 "stem_lines": [1, 4], "answer_lines": [5, 5]}


def test_t1_html_contains_item_radio_and_export(workdir):
    src, item = _item(workdir)
    html = H.build_review_html([item], src, generated_at="T")
    assert "S001" in html and "C12" in html
    for lb in ("KEEP", "SPLIT", "LOST", "UNCERTAIN"):
        assert f"value='{lb}'" in html
    assert "exportJSON" in html and "localStorage" in html
    assert "小问一" in html                      # 源文原文呈现


def test_t2_img_src_rewritten_absolute(workdir):
    src, item = _item(workdir)
    html = H.build_review_html([item], src, generated_at="T")
    assert "../../_imgs/p/img1.jpg" not in html
    assert "file:///" in html and "img1.jpg" in html


def test_t3_non_whitelist_tags_escaped(workdir):
    src, item = _item(workdir)
    html = H.build_review_html([item], src, generated_at="T")
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "<img" in html                       # 白名单标签保留


def test_t4_cli_end_to_end(workdir, monkeypatch):
    src = workdir / "src"
    out = workdir / "out"
    (src / "高一" / "历史").mkdir(parents=True, exist_ok=True)
    out.mkdir()
    (src / "高一" / "历史" / "b.md").write_text("材料……\n12. 无小问", encoding="utf-8")
    man = {"source_file": "x", "model": "m",
           "annotation_meta": {"prompt_version": "v", "validation_issues": [],
                               "warnings": []},
           "units": [{"unit_id": "C1", "unit_type": "composite_question",
                      "question_numbers": [12], "original_question_type": "solve",
                      "material_lines": [1, 1], "questions_lines": [1, 2],
                      "answer_lines": None,
                      "answer_evidence": {"type": "absent", "lines": None,
                                          "value": None}}]}
    (out / "高一" / "历史").mkdir(parents=True, exist_ok=True)
    (out / "高一" / "历史" / "b.manifest.json").write_text(
        json.dumps(man, ensure_ascii=False), encoding="utf-8")
    M.SRC = src
    items = M.build_suspect_sample(out, [{"file": str(src / "高一" / "历史" / "b.md"),
                                          "subject": "历史"}])["items"]
    assert len(items) == 1
    html = H.build_review_html(items, src, generated_at="T")
    dst = workdir / "review.html"
    dst.write_text(html, encoding="utf-8")
    assert dst.read_text(encoding="utf-8") == html
    assert "材料……" in html

# -*- coding: utf-8 -*-
r"""P2.2 图片绑定 baseline 最小钉(charter §11.2:识别率 / 归属事实 / 人工审核单)。

口径:确定性复算,不依赖 LLM;引用解析失败如实计 broken,不猜不修。
"""

import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


IB = _load("ib_p22", os.path.join(ROOT, "scripts", "p2_2_image_baseline.py"))


def _mk_corpus(workdir):
    """合成卷:题前孤儿图 L2 / Q1 可解析图 / Q2 缺失图 / 组合题共享材料图。"""
    src_root = workdir / "src"
    img_dir = src_root / "_imgs" / "test"
    img_dir.mkdir(parents=True)
    (img_dir / "img1.jpg").write_bytes(b"\xff\xd8fake")
    md_dir = src_root / "高一" / "化学"
    md_dir.mkdir(parents=True)
    lines = [
        "# 合成卷",                                              # L1
        '<div><img src="../../_imgs/test/img1.jpg"></div>',     # L2 题前图(孤儿)
        "1. 第一题",                                             # L3
        '<div><img src="../../_imgs/test/img1.jpg"></div>',     # L4 Q1 stem 内
        "A. 甲",                                                 # L5
        "2. 第二题",                                             # L6
        '<div><img src="../../_imgs/test/missing.jpg"></div>',  # L7 Q2 stem 内(文件缺失)
        "A. 乙",                                                 # L8
        "材料共享图如下",                                         # L9
        '<div><img src="../../_imgs/test/img1.jpg"></div>',     # L10 组合题材料区
        "3. 依据材料第一问",                                      # L11
        "4. 依据材料第二问",                                      # L12
        "## 参考答案",                                            # L13
        "1.【答案】A",                                            # L14
        '<div><img src="../../_imgs/test/img1.jpg"></div>',      # L15 Q1 解析区图
        "【解析】第一题解析正文",                                   # L16
    ]
    src = md_dir / "test.md"
    src.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="")
    man = {
        "source_file": str(src),
        "units": [
            {"unit_id": "Q1", "unit_type": "standalone_question",
             "question_numbers": [1], "original_question_type": "single_choice",
             "stem_lines": [3, 5], "answer_lines": [14, 14],
             "explanation_lines": [15, 16]},
            {"unit_id": "Q2", "unit_type": "standalone_question",
             "question_numbers": [2], "original_question_type": "single_choice",
             "stem_lines": [6, 8], "answer_lines": None},
            {"unit_id": "U3-4", "unit_type": "composite_question",
             "question_numbers": [3, 4], "original_question_type": "short_answer",
             "material_lines": [9, 10], "questions_lines": [11, 12],
             "answer_lines": None},
        ],
    }
    out_root = workdir / "out"
    (out_root / "高一" / "化学").mkdir(parents=True)
    (out_root / "高一" / "化学" / "test.manifest.json").write_text(
        json.dumps(man, ensure_ascii=False), encoding="utf-8", newline="")
    entry = {"file": str(src), "subject": "化学"}
    return src_root, out_root, entry


def test_t1_extract_refs_forms():
    # 生产实测形态:div 包裹、table 单元格多图、markdown 图片语法
    t1 = '<div style="text-align: center;"><img src="../../_imgs/a/img_x.jpg" alt="Image" width="48%" /></div>'
    assert IB.extract_refs(t1) == ["../../_imgs/a/img_x.jpg"]
    t2 = ('<td><img src="p/1.jpg" /></td><td><img src="p/2.jpg" /></td>'
          '<td><img src="p/3.jpg" /></td>')
    assert IB.extract_refs(t2) == ["p/1.jpg", "p/2.jpg", "p/3.jpg"]
    assert IB.extract_refs("![图](imgs/q9.png)") == ["imgs/q9.png"]
    assert IB.extract_refs("普通文字无图") == []
    # 无 src 的 img 不认(不猜)
    assert IB.extract_refs('<img alt="x">') == []


def test_t2_refs_in_span_bounds(workdir):
    lines = ["x", '<img src="a.jpg">', "y", '<img src="b.jpg">']
    (workdir / "a.jpg").write_bytes(b"j")
    got = IB.refs_in_span(lines, [1, 2])
    assert got == [(2, "a.jpg")]
    # 非法区间不猜
    assert IB.refs_in_span(lines, None) == []
    assert IB.refs_in_span(lines, [0, 9]) == []
    p = IB.resolve_ref("a.jpg", workdir)
    assert p.is_file()
    assert not IB.resolve_ref("b.jpg", workdir).is_file()
    # 绝对路径直用
    assert IB.resolve_ref(str(p), workdir / "other").is_file()


def test_t3_analyze_paper_facts(workdir):
    src_root, out_root, entry = _mk_corpus(workdir)
    rec = IB.analyze_paper(out_root, entry, src_root)
    assert rec["status"] == "OK"
    # 依赖题 = Q1(stem 图)/ Q2(stem 图)/ U3-4(材料图)——L2 孤儿图不算题
    assert rec["img_dep_questions"] == 3
    assert rec["dep_with_ref"] == 3
    assert rec["dep_with_resolvable"] == 2      # Q2 的 missing.jpg 缺失
    assert rec["refs_total"] == 3
    assert rec["refs_resolvable"] == 2
    assert rec["refs_broken"] == 1
    # 共享:img1 被 Q1 与 U3-4 引用
    assert rec["shared_images"] == 1
    assert rec["questions_on_shared"] == 2
    # 真孤儿:L2 题前图,附最近单元与行距(贴题未圈入信号)
    assert len(rec["orphan_refs"]) == 1
    o = rec["orphan_refs"][0]
    assert o["line"] == 2 and o["exists"] is True
    assert o["nearest_unit"] == "Q1" and o["gap"] == 1
    assert rec["orphan_adjacent"] == 1
    # 答案/解析区引用:归属 Q1 解析区,不进题面计数
    assert len(rec["ans_exp_refs"]) == 1
    ae = rec["ans_exp_refs"][0]
    assert ae["unit_id"] == "Q1" and ae["zone"] == "explanation" and ae["exists"]
    # 绑定区标注
    zones = {q["unit_id"]: {r["zone"] for r in q["refs"]}
             for q in rec["questions"]}
    assert zones == {"Q1": {"stem"}, "Q2": {"stem"}, "U3-4": {"material"}}
    # 明细含解析后绝对路径
    q1 = next(q for q in rec["questions"] if q["unit_id"] == "Q1")
    assert os.path.isabs(q1["refs"][0]["resolved"])
    assert q1["refs"][0]["exists"] is True


def test_t4_no_manifest_and_aggregate(workdir):
    src_root, out_root, entry = _mk_corpus(workdir)
    rec = IB.analyze_paper(out_root, {"file": str(workdir / "src" / "无.md"),
                                      "subject": "无"}, src_root)
    assert rec["status"] == "NO_MANIFEST" and "questions" not in rec
    ok = IB.analyze_paper(out_root, entry, src_root)
    tot = IB.aggregate([ok, rec])
    assert tot["papers"] == 2 and tot["no_manifest"] == 1
    assert tot["img_dep_questions"] == 3
    assert tot["img_recognition_rate"] == 1.0            # 3/3 持有引用
    assert tot["img_resolvable_rate"] == round(2 / 3, 4)
    assert tot["ref_resolvable_rate"] == round(2 / 3, 4)
    assert tot["refs_ans_exp"] == 1
    assert tot["orphan_refs"] == 1 and tot["orphan_adjacent"] == 1
    assert tot["orphan_far"] == 0


def test_t5_review_sample_deterministic(workdir):
    src_root, out_root, entry = _mk_corpus(workdir)
    ok = IB.analyze_paper(out_root, entry, src_root)
    s1 = IB.build_sample([ok], 2)
    s2 = IB.build_sample([ok], 2)
    assert [x["unit_id"] for x in s1] == [x["unit_id"] for x in s2]
    assert len(s1) == 2                       # 池 3 题 + 1 孤儿 → 等距取 2
    big = IB.build_sample([ok], 99)
    assert len(big) == 4                      # 全量:3 题 + 1 孤儿
    assert sum(1 for x in big if x["kind"] == "orphan") == 1


def test_t6_review_html(workdir):
    src_root, out_root, entry = _mk_corpus(workdir)
    ok = IB.analyze_paper(out_root, entry, src_root)
    html = IB.build_review_html(IB.build_sample([ok], 99), src_root)
    assert html.count("class='item'") == 4
    assert "p2_2_image_labels.json" in html
    assert "孤儿引用" in html
    for lb in IB.LABELS:
        assert f"value='{lb}'" in html
    # 图以 file:// 绝对 URI 渲染(HTML 位置无关)
    assert "file:///" in html
    assert "❌文件缺失" in html and "✅可解析" in html


def test_t7_synth_repo_integration(synth_repo):
    """conftest 合成卷走真实 write_outputs 产物:Q1 stem 题前图,文件缺失 → broken。"""
    src, _mf, out_dir = synth_repo
    rec = IB.analyze_paper(out_dir, {"file": str(src), "subject": "合成"},
                           src.parent)
    assert rec["status"] == "OK"
    assert rec["img_dep_questions"] == 1
    assert rec["refs_total"] == 1 and rec["refs_broken"] == 1
    assert rec["orphan_refs"] == []

# -*- coding: utf-8 -*-
"""json_struct_gate 定向与反向测试（G2-A 方案 A ④/⑤）。

覆盖：缺证据判失败 / ev_map 缺失判失败 / 双向映射 / 跨页页证据 / 图像归属 /
差异登记 / 消费证明（逐页标记、块溯源、指针一致、同 run 锚）/
反向（删 JSONL、篡改文本、篡改坐标、缺页块、跨 run 混用、删改指针）/
验证器不修改 units / recompile 语义。
"""

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from json_evidence_map import (  # noqa: E402
    annotate_json_evidence,
    build_line_evidence,
    evidence_digest,
    unit_evidence_pointers,
)
from json_struct_verify import run_generation_gate  # noqa: E402


def _block(bid, order, content, bbox, label="text"):
    return {
        "block_label": label, "block_content": content,
        "block_bbox": json.dumps(bbox), "block_id": bid,
        "block_order": order, "group_id": bid, "block_polygon_points": "[]",
    }


def _write_jsonl(path, pages_blocks):
    recs = []
    for blocks in pages_blocks:
        recs.append(json.dumps({
            "logId": "g", "errorCode": 0, "errorMsg": "Success",
            "result": {"layoutParsingResults": [{
                "prunedResult": {"width": 1000, "height": 1400,
                                 "parsing_res_list": blocks,
                                 "layout_det_res": {"boxes": []}},
                "markdown": {"text": "", "images": {}},
            }], "dataInfo": {"numPages": 1}},
        }, ensure_ascii=False))
    path.write_text("\n".join(recs), encoding="utf-8")
    return path


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _make_world(tmp_path, img_unmapped=False, omit_lines=()):
    """两页合成卷：p1 题干+材料，p2 跨页续+图行。

    img_unmapped=True 时页面无任何图块证据 → 图行不可归属 → 单元不可靠
    （E-2 整卷 FAIL 用例）；默认图块存在（结构配对可归属）→ 全可靠。
    """
    lines = [
        "材料甲乙丙。",            # L1
        "1. 题干一（ ）",          # L2
        "A. 甲",                  # L3
        "---",                    # L4 分页
        "2. 题干二（ ）",          # L5
        '<div><img src="img_in_image_box_10_10_20_20.jpg" /></div>',  # L6
    ]
    md = "\n".join(lines)
    jl = _write_jsonl(tmp_path / "t.ocr_raw.jsonl", [
        [b for b in (
            _block(0, 1, "材料甲乙丙。", [0, 0, 10, 10]),
            _block(1, 2, "1. 题干一（ ）", [0, 11, 10, 20]),
            _block(2, 3, "A. 甲", [0, 21, 10, 30])) if b["block_id"] not in omit_lines],
        [_block(0, 1, "2. 题干二（ ）", [0, 0, 10, 10])] if img_unmapped else
        [_block(0, 1, "2. 题干二（ ）", [0, 0, 10, 10]),
         _block(1, 2, "img_in_image_box_10_10_20_20.jpg",
                [0, 11, 10, 30], label="image")],
    ])
    units = [
        {"unit_id": "U01", "stem_lines": [2, 2], "options_lines": [3, 3],
         "material_lines": [1, 1]},
        {"unit_id": "U02", "stem_lines": [5, 5], "material_lines": [6, 6]},
    ]
    ev = build_line_evidence(md, jl)
    prompt_text = annotate_json_evidence(md, ev)
    recorded = {
        "map_sha256": evidence_digest(ev),
        "jsonl_file": jl.name,
        "page_count_md": ev["page_count_md"],
        "page_count_json": ev["page_count_json"],
        "page_split_consistent": ev["page_split_consistent"],
        "match_counts": ev["match_counts"],
        "unmapped_lines": ev["unmapped_lines"],
        "unmapped_blocks": ev["unmapped_blocks"],
        "skipped_blocks": ev["skipped_blocks"],
        "evidence_marker_count": prompt_text.count("〔j p"),
        "units": unit_evidence_pointers(ev, units),
        "md_sha256": hashlib.sha256(md.encode("utf-8")).hexdigest(),
        "json_sha256": _sha(jl),
        "prompt_sha256": hashlib.sha256(prompt_text.encode("utf-8")).hexdigest(),
    }
    man = {"units": units, "annotation_meta": {"json_evidence": recorded}}
    return {"md": md, "jl": jl, "ev": ev, "prompt": prompt_text,
            "recorded": recorded, "man": man}


def _run(world, **kw):
    args = dict(man=world["man"], ev_map=world["ev"], md_text=world["md"],
                jsonl_path=world["jl"], recorded=world["recorded"],
                prompt_text=world["prompt"],
                prompt_sha256=world["recorded"]["prompt_sha256"])
    args.update(kw)
    return run_generation_gate(**args)


class TestGateBaseline:
    def test_good_generation_passes(self, tmp_path):
        w = _make_world(tmp_path)
        g = _run(w)
        assert g["verdict"] == "PASS", g["checks"]
        assert g["consumption_proof"]["unit_pointers_match"] is True

    def test_missing_json_evidence_fails_not_skips(self, tmp_path):
        w = _make_world(tmp_path)
        g = _run(w, recorded=None)
        assert g["verdict"] == "FAIL"
        assert g["checks"][0]["id"] == "G1_evidence_presence"
        assert g["checks"][0]["status"] == "fail"

    def test_missing_ev_map_fails(self, tmp_path):
        w = _make_world(tmp_path)
        g = _run(w, ev_map=None)
        assert g["verdict"] == "FAIL"


class TestReverse:
    def test_deleted_jsonl_fails(self, tmp_path):
        w = _make_world(tmp_path)
        w["jl"].unlink()
        g = _run(w, ev_map=None)
        assert g["verdict"] == "FAIL"

    def test_tampered_jsonl_text_detected(self, tmp_path):
        w = _make_world(tmp_path)
        raw = w["jl"].read_text(encoding="utf-8").replace("材料甲乙丙。", "材料甲乙丙丁。")
        w["jl"].write_text(raw, encoding="utf-8")
        g = _run(w)  # recorded.json_sha256 是篡改前哈希
        assert g["verdict"] == "FAIL"
        assert any(c["id"] == "G2_binding" and c["status"] == "fail" for c in g["checks"])

    def test_tampered_bbox_detected(self, tmp_path):
        w = _make_world(tmp_path)
        raw = w["jl"].read_text(encoding="utf-8").replace("[0, 0, 10, 10]", "[9, 9, 99, 99]", 1)
        w["jl"].write_text(raw, encoding="utf-8")
        # 字节哈希变了 → G2 捕获（位置篡改同样落指纹）
        g = _run(w)
        assert g["verdict"] == "FAIL"

    def test_missing_page_blocks_detected(self, tmp_path):
        w = _make_world(tmp_path)
        # 删除 p2 的全部块（保留 p1）→ 重算映射与记录摘要不符 + U02 页证据缺口
        raw = json.loads(w["jl"].read_text(encoding="utf-8").split("\n")[1])
        raw["result"]["layoutParsingResults"][0]["prunedResult"]["parsing_res_list"] = []
        lines = w["jl"].read_text(encoding="utf-8").split("\n")
        lines[1] = json.dumps(raw, ensure_ascii=False)
        w["jl"].write_text("\n".join(lines), encoding="utf-8")
        ev2 = build_line_evidence(w["md"], w["jl"])
        g = _run(w, ev_map=ev2)  # recorded 仍是原摘要
        assert g["verdict"] == "FAIL"
        assert any("unmapped_block" in r or "page" in r
                   for fl in g["unit_flags"].values() for r in fl["reasons"]) or \
               any(c["id"] == "G2_binding" and c["status"] == "fail" for c in g["checks"])

    def test_cross_run_mix_detected(self, tmp_path):
        w = _make_world(tmp_path)
        other = tmp_path / "other.ocr_raw.jsonl"
        _write_jsonl(other, [[_block(0, 1, "完全不同的内容", [0, 0, 1, 1])]])
        g = _run(w, jsonl_path=other)
        assert g["verdict"] == "FAIL"

    def test_tampered_unit_pointers_detected(self, tmp_path):
        w = _make_world(tmp_path)
        w["recorded"]["units"] = {"U01": {"pages": [1], "block_ids": [0], "line_span": [1, 3]}}
        g = _run(w)
        assert g["verdict"] == "FAIL"
        assert any("指针" in c["detail"] for c in g["checks"] if c["id"] == "G7_consumption_proof")


class TestValidatorNeverMutates:
    def test_units_unchanged(self, tmp_path):
        w = _make_world(tmp_path)
        before = copy.deepcopy(w["man"]["units"])
        _run(w)
        assert w["man"]["units"] == before


class TestCoverageAndEvidence:
    def test_cross_page_unit_pages_have_evidence(self, tmp_path):
        w = _make_world(tmp_path)
        g = _run(w)
        cov = next(c for c in g["checks"] if c["id"] == "G4_cross_page_coverage")
        assert cov["status"] == "pass"

    def test_image_line_unmapped_flagged(self, tmp_path):
        w = _make_world(tmp_path, img_unmapped=True)
        # 图行 L6 所在页无任何图块证据 → G5 warn + U02 不可靠 → E-2 整卷 FAIL
        g = _run(w)
        img_chk = next(c for c in g["checks"] if c["id"] == "G5_image_attribution")
        assert img_chk["status"] == "warn"
        assert g["unit_flags"]["U02"]["reliable"] is False
        assert g["verdict"] == "FAIL"
        assert g["unreliable_units"] == ["U02"]

    def test_divergence_register_populated(self, tmp_path):
        w = _make_world(tmp_path)
        g = _run(w)
        assert "text_unmapped_lines" in g["divergence_register"]
        assert g["divergence_register"]["note"].startswith("仅描述证据差异")

    def test_prompt_markers_referenced_blocks_exist(self, tmp_path):
        w = _make_world(tmp_path)
        g = _run(w)
        assert g["consumption_proof"]["marker_blocks_in_jsonl"] is True
        assert g["consumption_proof"]["marked_pages"] == [1, 2]

    def test_ghost_marker_blocks_fail(self, tmp_path):
        w = _make_world(tmp_path)
        bad_prompt = w["prompt"] + "\n[L9999] x 〔j p1 b42 box 0,0-1,1〕"
        g = _run(w, prompt_text=bad_prompt)
        assert g["verdict"] == "FAIL"
        assert any("不存在的块" in c["detail"] for c in g["checks"] if c["id"] == "G7_consumption_proof")


class TestRecompileMode:
    def test_recompile_without_prompt_checks_pointers_only(self, tmp_path):
        w = _make_world(tmp_path)
        g = _run(w, prompt_text=None, mode="recompile")
        assert g["verdict"] == "PASS", g["checks"]
        assert g["consumption_proof"]["prompt_marker_check"] == "not_applicable_recompile"

    def test_recompile_missing_evidence_fails(self, tmp_path):
        w = _make_world(tmp_path)
        g = _run(w, recorded=None, prompt_text=None, mode="recompile")
        assert g["verdict"] == "FAIL"

    def test_recompile_tampered_pointers_fails(self, tmp_path):
        w = _make_world(tmp_path)
        w["recorded"]["units"] = {}
        g = _run(w, prompt_text=None, mode="recompile")
        assert g["verdict"] == "FAIL"


class TestE2VolumeRules:
    """E-2（Owner 裁决）：unit_flags.reliable=false → 整卷 FAIL；WARN 语义不误升级。"""

    def test_all_reliable_passes(self, tmp_path):
        w = _make_world(tmp_path)
        g = _run(w)
        assert g["verdict"] == "PASS"
        assert g["unreliable_units"] == []

    def test_unreliable_unit_fails_volume_even_if_rest_pass(self, tmp_path):
        w = _make_world(tmp_path, img_unmapped=True)
        g = _run(w)
        # G1/G2/G7 均 pass，但 U02 不可靠 → 整卷 FAIL（其他 PASS 不可覆盖）
        assert g["verdict"] == "FAIL"
        g8 = next(c for c in g["checks"] if c["id"] == "G8_volume_reliability")
        assert g8["status"] == "fail"
        assert "U02" in g8["detail"]

    def test_unreliable_plus_warn_fails_volume(self, tmp_path):
        w = _make_world(tmp_path, img_unmapped=True)
        # 再加一个单位外噪声行 → G3 warn；U02 仍不可靠 → 整卷 FAIL
        w2 = dict(w)
        w2["md"] = w["md"] + "\n卷外噪声行XYZ"
        g = _run(w2)
        assert g["verdict"] == "FAIL"

    def test_plain_warn_all_reliable_stays_warn(self, tmp_path):
        w = _make_world(tmp_path)
        # 单位区间外的未映射文本行 → G3 warn 但不株连单元 → verdict=WARN（不升级）
        import hashlib
        w2 = dict(w)
        w2["md"] = w["md"] + "\n卷外噪声行XYZ"
        w2["ev"] = build_line_evidence(w2["md"], w["jl"])
        w2["prompt"] = annotate_json_evidence(w2["md"], w2["ev"])
        rec = dict(w["recorded"])
        rec["map_sha256"] = evidence_digest(w2["ev"])
        rec["units"] = unit_evidence_pointers(w2["ev"], w["man"]["units"])
        rec["prompt_sha256"] = hashlib.sha256(w2["prompt"].encode("utf-8")).hexdigest()
        w2["recorded"] = rec
        g = _run(w2)
        assert g["verdict"] == "WARN", g["checks"]
        assert g["unreliable_units"] == []

    def test_multiple_unreliable_units_all_listed(self, tmp_path):
        # 稳定世界：U01 题干行（L2，块 id 1）缺块 + U02 页面无图块 → 两个不可靠单元
        w = _make_world(tmp_path, img_unmapped=True, omit_lines=(1,))
        g = _run(w)
        assert g["verdict"] == "FAIL"
        assert set(g["unreliable_units"]) >= {"U01", "U02"}
        assert all(g["unit_flags"][u]["reliable"] is False for u in g["unreliable_units"])
        # 全部不可靠单元都进诊断（不止第一个）
        g8 = next(c for c in g["checks"] if c["id"] == "G8_volume_reliability")
        assert "U01" in g8["detail"] and "U02" in g8["detail"]
# -*- coding: utf-8 -*-
"""json_evidence_map 定向测试（G2-A 方案 A 约束钉住）。

覆盖：JSON 契约解析 / 页界规则 / 精确与折叠匹配 / 一对多与多对一 /
未映射显式保留 / 摘要稳定性 / 单元证据指针（不复制原文）。
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from json_evidence_map import (  # noqa: E402
    annotate_json_evidence,
    build_line_evidence,
    evidence_digest,
    load_ocr_pages,
    split_md_pages,
    unit_evidence_pointers,
)


def _block(bid, order, content, bbox, label="text", group=0):
    return {
        "block_label": label, "block_content": content,
        "block_bbox": json.dumps(bbox), "block_id": bid,
        "block_order": order, "group_id": group,
        "block_polygon_points": json.dumps(
            [[bbox[0], bbox[1]], [bbox[2], bbox[1]], [bbox[2], bbox[3]], [bbox[0], bbox[3]]]),
    }


def _make_jsonl(tmp_path, pages_blocks):
    """pages_blocks: list[list[block]]，一页一块列表。返回 jsonl 路径。"""
    recs = []
    for blocks in pages_blocks:
        recs.append(json.dumps({
            "logId": "test", "errorCode": 0, "errorMsg": "Success",
            "result": {
                "layoutParsingResults": [{
                    "prunedResult": {
                        "width": 1000, "height": 1400,
                        "parsing_res_list": blocks,
                        "layout_det_res": {"boxes": []},
                    },
                    "markdown": {"text": "", "images": {}},
                }],
                "dataInfo": {"numPages": 1},
            },
        }, ensure_ascii=False))
    p = tmp_path / "t.ocr_raw.jsonl"
    p.write_text("\n".join(recs), encoding="utf-8")
    return p


class TestLoadOcrPages:
    def test_parses_real_contract_fields(self, tmp_path):
        jl = _make_jsonl(tmp_path, [[
            _block(0, 1, "标题", [10, 20, 30, 40], label="doc_title"),
            _block(1, 2, "正文第一段", [10, 50, 30, 80]),
        ]])
        pages = load_ocr_pages(jl)
        assert len(pages) == 1
        b = pages[0]["blocks"][0]
        assert b["block_id"] == 0 and b["block_order"] == 1
        assert b["block_label"] == "doc_title"
        assert b["bbox"] == [10, 20, 30, 40]
        assert b["content"] == "标题"

    def test_page_order_matches_all_md_assembly(self, tmp_path):
        jl = _make_jsonl(tmp_path, [
            [_block(0, 1, "P1", [0, 0, 1, 1])],
            [_block(0, 1, "P2", [0, 0, 1, 1])],
            [_block(0, 1, "P3", [0, 0, 1, 1])],
        ])
        pages = load_ocr_pages(jl)
        assert [p["blocks"][0]["content"] for p in pages] == ["P1", "P2", "P3"]
        assert [p["page_no"] for p in pages] == [1, 2, 3]


class TestSplitMdPages:
    def test_separator_rule_same_as_annotate_img_boxes(self):
        # 与 annotate_img_boxes 同规则：仅独立 --- 行是分页符，空行留属各页
        text = "a\nb\n\n---\n\nc\n\n---\n\nd"
        segs = split_md_pages(text)
        assert [s["page_no"] for s in segs] == [1, 2, 3]
        assert [s["lines"] for s in segs] == [["a", "b", ""], ["", "c", ""], ["", "d"]]

    def test_line_numbers_are_global(self):
        segs = split_md_pages("a\nb\n---\nc")
        assert segs[0]["start_line"] == 1 and segs[0]["end_line"] == 2
        assert segs[1]["start_line"] == 4


class TestMatching:
    def test_exact_multiline_block(self, tmp_path):
        jl = _make_jsonl(tmp_path, [[
            _block(0, 1, "第一行内容\n第二行内容", [0, 0, 10, 10]),
        ]])
        ev = build_line_evidence("第一行内容\n第二行内容", jl)
        assert ev["lines"][1]["block_ids"] == [0]
        assert ev["lines"][2]["block_ids"] == [0]
        assert ev["lines"][1]["status"] == "mapped_exact"
        assert ev["unmapped_lines"] == []

    def test_exact_match_tolerates_heading_prefix(self, tmp_path):
        # '# ' 前缀不阻碍子串精确命中（块内容是行内子串）
        jl = _make_jsonl(tmp_path, [[_block(5, 1, "一、阅读（74 分）", [0, 0, 10, 10])]])
        ev = build_line_evidence("# 一、 阅读（74 分）", jl)
        assert ev["lines"][1]["block_ids"] == [5]
        assert ev["lines"][1]["status"] == "mapped_exact"

    def test_folded_match_md_inline_decor(self, tmp_path):
        # 内部装饰符（**…**/表格竖线）阻断精确匹配 → 折叠第二遍命中
        jl = _make_jsonl(tmp_path, [[_block(5, 1, "一、阅读（74 分）", [0, 0, 10, 10])]])
        ev = build_line_evidence("一、**阅读**（74 分）", jl)
        assert ev["lines"][1]["block_ids"] == [5]
        assert ev["lines"][1]["status"] == "mapped_folded"

    def test_many_blocks_one_line(self, tmp_path):
        jl = _make_jsonl(tmp_path, [[
            _block(0, 1, "选项A", [0, 0, 5, 5]),
            _block(1, 2, "选项B", [6, 0, 10, 5]),
        ]])
        ev = build_line_evidence("选项A 选项B", jl)
        assert set(ev["lines"][1]["block_ids"]) == {0, 1}

    def test_one_block_many_lines(self, tmp_path):
        jl = _make_jsonl(tmp_path, [[_block(3, 1, "段落甲段落乙", [0, 0, 9, 9])]])
        ev = build_line_evidence("段落甲\n段落乙", jl)
        assert ev["lines"][1]["block_ids"] == [3] and ev["lines"][2]["block_ids"] == [3]

    def test_unmapped_preserved_not_forced(self, tmp_path):
        jl = _make_jsonl(tmp_path, [[
            _block(0, 1, "已知文本", [0, 0, 5, 5]),
            _block(9, 2, "块里有但MD没有", [0, 0, 5, 5]),
        ]])
        ev = build_line_evidence("已知文本\nMD独有噪声行", jl)
        assert ev["unmapped_blocks"] == [{"page_no": 1, "block_id": 9, "block_label": "text"}]
        assert ev["unmapped_lines"] == [2]
        assert ev["match_counts"]["unmapped_blocks"] == 1

    def test_empty_block_skipped_not_unmapped(self, tmp_path):
        jl = _make_jsonl(tmp_path, [[
            _block(0, 1, "有文本", [0, 0, 5, 5]),
            _block(1, 2, "", [0, 6, 5, 9], label="image"),
        ]])
        ev = build_line_evidence("有文本", jl)
        assert ev["unmapped_blocks"] == []
        assert ev["skipped_blocks"] == [
            {"page_no": 1, "block_id": 1, "block_label": "image", "class": "empty_or_structural"}]
        assert ev["match_counts"]["skipped_blocks"] == 1

    def test_page_mismatch_falls_back_without_forcing(self, tmp_path):
        jl = _make_jsonl(tmp_path, [
            [_block(0, 1, "P1文本", [0, 0, 1, 1])],
            [_block(0, 1, "P2文本", [0, 0, 1, 1])],
        ])
        # MD 无 --- 分页 → 页数 1 vs json 2 → 不一致，走全卷模式
        ev = build_line_evidence("P1文本\nP2文本", jl)
        assert ev["page_split_consistent"] is False
        assert ev["match_counts"]["mapped_exact"] == 2  # 全卷匹配仍可确定性命中
        assert ev["unmapped_lines"] == []


class TestOutput:
    def test_annotate_format_and_no_text_copy(self, tmp_path):
        jl = _make_jsonl(tmp_path, [[_block(7, 1, "题干文本", [1, 2, 3, 4])]])
        ev = build_line_evidence("题干文本", jl)
        out = annotate_json_evidence("题干文本", ev)
        assert out == "题干文本 〔j p1 b7 box 1,2-3,4〕"
        # 注解只含引用：不得复制块原文
        assert "题干文本 〔j" in out

    def test_digest_stable_and_sensitive(self):
        e1 = {"lines": {1: {"page": 1, "block_ids": [0], "bbox": None, "status": "mapped_exact"}},
              "unmapped_blocks": [], "skipped_blocks": [], "unmapped_lines": [],
              "page_count_md": 1, "page_count_json": 1, "page_split_consistent": True}
        e2 = json.loads(json.dumps(e1))
        assert evidence_digest(e1) == evidence_digest(e2)
        e2["lines"]["1"]["block_ids"] = [1]
        assert evidence_digest(e1) != evidence_digest(e2)

    def test_unit_pointers_reference_only(self, tmp_path):
        jl = _make_jsonl(tmp_path, [[
            _block(0, 1, "材料文本", [0, 0, 5, 5]),
            _block(1, 2, "问题文本", [0, 6, 5, 9]),
        ]])
        text = "材料文本\n问题文本"
        ev = build_line_evidence(text, jl)
        units = [{"unit_id": "U01", "material_lines": [1, 1], "questions_lines": [2, 2]}]
        ptr = unit_evidence_pointers(ev, units)
        assert ptr["U01"]["block_ids"] == [0, 1]
        assert ptr["U01"]["pages"] == [1]
        assert ptr["U01"]["line_span"] == [1, 2]
        # 指针不含原文
        assert "材料文本" not in json.dumps(ptr, ensure_ascii=False)


class TestRealSampleSmoke:
    @pytest.mark.skipif(
        not Path(r"D:\Project\AITutors\Preprocessing\runs\qcore_answer_fidelity_02"
                 r"\chinese\ocr_output\高三\语文\2019江苏高考真题语文（教师版）(1).ocr_raw.jsonl").is_file(),
        reason="real ocr_raw.jsonl sample not present")
    def test_real_jsonl_parses(self):
        jl = Path(r"D:\Project\AITutors\Preprocessing\runs\qcore_answer_fidelity_02"
                  r"\chinese\ocr_output\高三\语文\2019江苏高考真题语文（教师版）(1).ocr_raw.jsonl")
        pages = load_ocr_pages(jl)
        assert len(pages) >= 3
        assert all(p["blocks"] for p in pages)
        assert all(b["bbox"] for b in pages[0]["blocks"] if b["content"])

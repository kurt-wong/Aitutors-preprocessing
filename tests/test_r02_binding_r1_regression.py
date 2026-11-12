# -*- coding: utf-8 -*-
"""R-02 真实数据回归：14 条历史 mismatch 全部被确定性识别（哈希夹具，零试卷内容）。

数据源=封存 R1 工作区（Question Core/runs/qcore_s2q_repair_01_r1，不在 git）。
夹具=tests/fixtures/r02_binding_r1_expectations.json（仅 ID/哈希/期望分级）。
工作区缺失 → skip（CI/无数据环境）。只读复算，不写任何数据。
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import answer_binding as ab  # noqa: E402

AITORS = Path(__file__).resolve().parents[2]  # .../AITutors
RUN = AITORS / "Question Core" / "runs" / "qcore_s2q_repair_01_r1"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "r02_binding_r1_expectations.json"

pytestmark = pytest.mark.skipif(
    not RUN.exists(), reason="封存 R1 工作区不存在（真实回归需本地封存数据）")


def sha16(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()[:16]


def find_md(mp: Path) -> Path | None:
    stem = mp.name[: -len(".manifest.json")]
    cands = [p for p in RUN.rglob(f"{stem}.md")]
    pref = [p for p in cands if "ocr_output" in p.parts]
    return (pref or cands or [None])[0]


def struct_sig(man: dict) -> list:
    sig = []
    for u in man.get("units", []):
        sig.append({k: u.get(k) for k in (
            "unit_id", "unit_type", "question_numbers", "printed_number",
            "stem_lines", "options_lines", "material_lines", "questions_lines",
            "answer_lines", "explanation_lines")})
    return sig


@pytest.fixture(scope="module")
def bound_all():
    """对三份封存 manifest 复算绑定（内存中，不落盘）。"""
    fx = json.loads(FIXTURE.read_text(encoding="utf-8"))
    out = {}
    for mp in sorted(RUN.rglob("*.manifest.json")):
        md = find_md(mp)
        if md is None:
            continue
        paper = mp.parents[1].name
        lines = md.read_text(encoding="utf-8", errors="replace").splitlines()
        man = json.loads(mp.read_text(encoding="utf-8"))
        man2 = copy.deepcopy(man)
        before = struct_sig(man2)
        ab.bind_answers(man2, lines)
        out[paper] = {"man": man2, "before": before, "after": struct_sig(man2)}
    return fx, out


def test_structure_unchanged(bound_all):
    fx, out = bound_all
    for paper, d in out.items():
        assert d["before"] == d["after"], f"{paper} 结构发生非目标变化"


def test_aggregates_match_fixture(bound_all):
    fx, out = bound_all
    from collections import Counter
    tiers, classes = Counter(), Counter()
    n = 0
    for d in out.values():
        for u in d["man"].get("units", []):
            for it in u.get("answers") or []:
                b = it.get("value_binding") or {}
                if b.get("tier") == "not_applicable" and not (it.get("value_text") or "").strip():
                    tiers["not_applicable"] += 1
                    continue
                n += 1
                tiers[b.get("tier")] += 1
                if b.get("mismatch_class"):
                    classes[b.get("mismatch_class")] += 1
    exp = fx["aggregates"]
    assert dict(tiers) == exp["tier_counts"], f"tier 分布不符：{dict(tiers)}"
    assert dict(classes) == exp["mismatch_class_counts"]
    assert n == exp["items_total"]


# DSH 复算锁定的 14 条历史非等值条目（paper, unit, idx）——零内容，仅身份键
HISTORICAL_14 = [
    ("chemistry", "Q9", 4), ("chemistry", "Q9", 5), ("chemistry", "Q9", 6),
    ("chemistry", "Q10", 0), ("chemistry", "Q10", 2), ("chemistry", "Q10", 3),
    ("chemistry", "Q10", 4), ("chemistry", "Q10", 5),
    ("chemistry", "Q11", 5), ("chemistry", "Q11", 7),
    ("chemistry", "Q12", 3), ("chinese", "Q11", 1),
    ("english", "U10", 0), ("english", "U11", 0),
]


def test_all_14_historical_mismatches_identified(bound_all):
    """14 条历史非等值条目必须逐条命中期望处置（13 mismatch + 1 compressed_weak）。"""
    fx, out = bound_all
    watch = fx["watch_entries"]
    keys = {(w["paper"], w["unit"], w["idx"]): w for w in watch}
    for k in HISTORICAL_14:
        assert k in keys, f"历史条目 {k} 不在回归夹具中"
        w = keys[k]
        d = out[w["paper"]]
        unit = next(u for u in d["man"]["units"] if u.get("unit_id") == w["unit"])
        entry = unit["answers"][w["idx"]]
        b = entry.get("value_binding") or {}
        assert b.get("tier") == w["expect_tier"], (
            f"{w['paper']}/{w['unit']}[{w['idx']}] tier {b.get('tier')} != {w['expect_tier']}")
        assert b.get("mismatch_class") == w["expect_mismatch_class"]
        assert sha16(entry.get("model_value_text") or "") == w["sha_model_value"]
        assert sha16(entry.get("value_text") or "") == w["sha_value_after_16"]


def test_no_pass_tier_for_mismatch_entries(bound_all):
    """红线：被标记 mismatch 的条目，其 value_text 不得等于模型声明原文。"""
    fx, out = bound_all
    for w in fx["watch_entries"]:
        d = out[w["paper"]]
        unit = next(u for u in d["man"]["units"] if u.get("unit_id") == w["unit"])
        entry = unit["answers"][w["idx"]]
        b = entry.get("value_binding") or {}
        if b.get("tier") in ("mismatch_recovered", "mismatch_withheld"):
            model = entry.get("model_value_text") or ""
            assert entry.get("value_text") != model or entry.get("value_text") is None, (
                f"{w['paper']}/{w['unit']}[{w['idx']}] 失锚后仍保留模型原文为事实值")

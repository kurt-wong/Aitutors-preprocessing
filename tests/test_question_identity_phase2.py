# -*- coding: utf-8 -*-
"""Phase 2 QuestionIdentity 验收测试(R34)——冻结标准 P2-01~P2-08。

三方向测试纪律(第五轮审查 §十二/§十四):
  非法(必须 FAIL)/ 合法(必须 PASS)/ 证据不足(必须 PENDING_REVIEW)。
BUG-22 回迁突变(P2-03)与合法 local numbering(P2-04)必须同时通过——
R33 教训:抓 BUG-22 和不误杀合法结构是两个相反方向,只测一个不够。
"""
import json

import pytest

import question_identity as qi
import reslice_qc as qc
from conftest import SYNTH_LINES, SYNTH_MAN, make_repo

N_LINES = len(SYNTH_LINES)


def _qc(manifest_path):
    md = manifest_path.parent / (manifest_path.name.replace(".manifest.json", ".md"))
    return qc.check(md)


def _v2(units=None, sections=None, version=2):
    """合成 v2 manifest:sections locator + 单元身份字段由调用方显式给出。"""
    man = json.loads(json.dumps(SYNTH_MAN))
    if units is not None:
        man["units"] = units
    man["identity_version"] = version
    man["sections"] = sections or [
        {"id": "S1", "title": "一、选择题", "ordinal": 1, "start_line": 3, "end_line": 14},
        {"id": "S2", "title": "二、综合题", "ordinal": 2, "start_line": 15, "end_line": N_LINES},
    ]
    for u, sec in zip(man["units"], ["S1", "S1", "S2"]):
        u.setdefault("section_ref", sec)
        u.setdefault("section", "一、选择题" if sec == "S1" else "二、综合题")
        u.setdefault("basis", "printed_as_is")
        u.setdefault("basis_evidence", "")
        u.setdefault("printed_number", list(u.get("question_numbers") or []))
        u.setdefault("printed_provenance", "source_line")
    return man


def _unit(uid, nums, sec, basis="printed_as_is", evidence="", section_title=None):
    return {"unit_id": uid, "unit_type": "standalone_question",
            "section_ref": sec, "section": section_title or sec,
            "question_numbers": list(nums), "original_question_type": "fill_in",
            "stem_lines": [19, 19], "options_lines": None,
            "answer_lines": [31, 31], "explanation_lines": None,
            "printed_number": list(nums), "printed_provenance": "source_line",
            "basis": basis, "basis_evidence": evidence}


# ── P2-01 正常 canonical 全卷唯一 → 无身份问题,全链路 PASS ──────────────────
def test_p2_01_unique_canonical_passes(workdir):
    man = _v2()
    fails, reviews = qi.check_identity(man, N_LINES)
    assert fails == [] and reviews == []
    _, mf, _ = make_repo(workdir, man=man)
    assert _qc(mf)["verdict"] == "PASS"


# ── P2-02 keep + 可回源证据才允许重复;keep 与非 keep 天然同号合法 ───────────
def test_p2_02_keep_duplicate_with_evidence_allowed(workdir):
    """真实结构(会考化学):非 keep 的综合题 3/4 与选考模块 keep 3/4 同号。"""
    ev = "选考模块互斥,印刷号保持;分节标题 L15:二、综合题"
    man = _v2()
    man["sections"] = _v2()["sections"] + [
        {"id": "S3", "title": "《有机》模块", "ordinal": 3, "start_line": 15, "end_line": N_LINES},
        {"id": "S4", "title": "《结构》模块", "ordinal": 4, "start_line": 15, "end_line": N_LINES},
    ]
    man["units"] += [
        _unit("M1-1", [3], "S3", basis="keep", evidence=ev, section_title="《有机》模块"),
        _unit("M2-1", [4], "S4", basis="keep", evidence=ev, section_title="《结构》模块"),
    ]
    fails, reviews = qi.check_identity(man, N_LINES)
    assert fails == [] and reviews == []
    _, mf, _ = make_repo(workdir, man=man)
    assert _qc(mf)["verdict"] == "PASS"


def test_p2_02_keep_colliding_with_non_keep_allowed():
    """真实结构(会考化学):选择题 1(非 keep)与选考模块 keep 1 天然同号。"""
    man = _v2(units=[
        _unit("Q1", [1], "S1"),
        _unit("M1-1", [1], "S2", basis="keep",
              evidence="模块互斥;分节标题 L15:二、综合题"),
    ])
    fails, _ = qi.check_identity(man, N_LINES)
    assert fails == []


# ── P2-03 BUG-22 原始回归形态必须被 C13 v2 捕获(回迁突变) ──────────────────
def test_p2_03_bug22_regression_caught(workdir):
    """选择题/综合题与非选择题各自从 1 编号、均无 keep 依据 → 必须 FAIL。"""
    units = [
        _unit("Q1", [1], "S1"), _unit("Q2", [2], "S1"),
        _unit("N1", [1], "S2", basis="shift"), _unit("N2", [2], "S2", basis="shift"),
    ]
    fails, _ = qi.check_identity(_v2(units=units), N_LINES)
    assert any("C13" in f for f in fails)
    # 全链路:基础合成卷(题号覆盖完整)+ 回归单元,走真实 write_outputs + QC
    man = _v2()
    man["sections"] = _v2()["sections"] + [
        {"id": "S3", "title": "二、非选择题", "ordinal": 3, "start_line": 15, "end_line": N_LINES}]
    man["units"].append(
        _unit("N3", [3], "S3", basis="shift", section_title="二、非选择题"))
    _, mf, _ = make_repo(workdir, man=man)
    r = _qc(mf)
    assert r["verdict"] == "FAIL"
    assert any(i.startswith("C13") for i in r["issues"])


# ── P2-04 合法 local numbering 不被误杀(P2-03 的反方向,必须同时成立) ──────
def test_p2_04_legal_local_numbering_not_falsely_flagged():
    ev = "汇编各块独立编号;分节标题 L3:一、选择题"
    man = _v2(units=[
        _unit("A1", [1], "S1", basis="keep", evidence=ev),
        _unit("B1", [1], "S2", basis="keep", evidence=ev),
    ])
    fails, reviews = qi.check_identity(man, N_LINES)
    assert fails == [] and reviews == []


def test_p2_04_keep_cannot_excuse_same_section_duplicate():
    """keep 豁免是跨分节豁免;同分节重复永远 FAIL。"""
    ev = "证据;分节标题 L3:一、选择题"
    man = _v2(units=[
        _unit("A1", [1], "S1", basis="keep", evidence=ev),
        _unit("A2", [1], "S1", basis="keep", evidence=ev),
    ])
    fails, _ = qi.check_identity(man, N_LINES)
    assert any("同分节重复" in f for f in fails)


# ── 证据不足(第三方向):fake keep → PENDING_REVIEW,不 FAIL 也不 PASS ──────
def test_fake_keep_without_evidence_pending_review(workdir):
    """第三方向:声明 keep 但无证据 → PENDING_REVIEW,不 FAIL 也不 PASS。"""
    man = _v2()
    man["sections"] = _v2()["sections"] + [
        {"id": "S3", "title": "模块一", "ordinal": 3, "start_line": 15, "end_line": N_LINES},
        {"id": "S4", "title": "模块二", "ordinal": 4, "start_line": 15, "end_line": N_LINES}]
    man["units"] += [
        _unit("M1-1", [3], "S3", basis="keep", evidence="", section_title="模块一"),
        _unit("M2-1", [3], "S4", basis="keep", evidence="", section_title="模块二"),
    ]
    fails, reviews = qi.check_identity(man, N_LINES)
    assert fails == []
    assert any("keep 依据不足" in r for r in reviews)
    _, mf, _ = make_repo(workdir, man=man)
    assert _qc(mf)["verdict"] == "PENDING_REVIEW"


def test_keep_evidence_line_out_of_bounds_pending_review():
    man = _v2(units=[
        _unit("A1", [1], "S1", basis="keep", evidence="分节标题 L99999:一、选择题"),
        _unit("B1", [1], "S2", basis="keep", evidence="分节标题 L99999:一、选择题"),
    ])
    fails, reviews = qi.check_identity(man, N_LINES)
    assert fails == []
    assert any("keep 依据不足" in r for r in reviews)


# ── P2-05 缺 section 不得静默 PASS ─────────────────────────────────────────
def test_p2_05_missing_section_not_silently_passing(workdir):
    man = _v2()
    for u in man["units"]:
        u.pop("section_ref", None)
    _, mf, _ = make_repo(workdir, man=man)
    r = _qc(mf)
    assert r["verdict"] != "PASS"
    assert any("identity_scope_missing" in n for n in r["review_notes"])


# ── P2-06 SectionLocator 唯一定位 Source(同名分节按 ordinal/span 消歧) ────
def test_p2_06_section_locator_disambiguates_duplicate_titles():
    lines = ["# 卷", "", "## 实验题", "1. 甲", "", "## 实验题", "1. 乙"]
    secs = qi.build_section_locators(lines)
    real = [s for s in secs if not s.get("derived")]
    # "# 卷" 也是标题(一级);两个同名"实验题"必须靠 ordinal/span 区分
    assert [s["title"] for s in real] == ["卷", "实验题", "实验题"]
    duos = [s for s in real if s["title"] == "实验题"]
    assert [s["ordinal"] for s in duos] == [2, 3]
    assert (duos[0]["start_line"], duos[0]["end_line"]) == (3, 5)
    assert (duos[1]["start_line"], duos[1]["end_line"]) == (6, 7)
    # assign_identity 按位置分配 → 两个同 unit_id 的单元落不同 section
    man = {"units": [
        {"unit_id": "U1", "question_numbers": [1], "stem_lines": [4, 4]},
        {"unit_id": "U1", "question_numbers": [1], "stem_lines": [7, 7]},
    ]}
    qi.assign_identity(man, lines)
    assert man["units"][0]["section_ref"] != man["units"][1]["section_ref"]


def test_p2_06b_same_printed_number_across_sections_needs_keep():
    lines = ["# 卷", "", "## 实验题", "1. 甲", "", "## 实验题", "1. 乙"]
    man = {"units": [
        {"unit_id": "U1", "question_numbers": [1], "stem_lines": [4, 4]},
        {"unit_id": "U1", "question_numbers": [1], "stem_lines": [7, 7]},
    ]}
    qi.assign_identity(man, lines)
    fails, _ = qi.check_identity(man, len(lines))
    assert any("非 keep" in f for f in fails)


# ── P2-07 printed_number 无证据必须 unknown,禁止 canonical 回填 ───────────
def test_p2_07_printed_unknown_not_guessed():
    from phase2_identity_backfill import printed_from_stem
    lines = ["", "", "", "26.【答案】A", "", "综合材料开头无题号"]
    u_multi = {"question_numbers": [26, 27], "stem_lines": [4, 4]}
    assert printed_from_stem(u_multi, lines) == (None, "unknown")
    u_nostem = {"question_numbers": [30], "stem_lines": [6, 6]}
    assert printed_from_stem(u_nostem, lines) == (None, "unknown")
    # 印刷题号可解析时记录源事实(即使与 canonical 不同)
    u_real = {"question_numbers": [26], "stem_lines": [4, 4]}
    # "26.【答案】" 首行可解析为 26——若卷面印的是别的号,记录的就是那个号
    pn, prov = printed_from_stem(u_real, lines)
    assert prov == "source_line" and pn == [26]


def test_p2_07_backfill_marks_unknown_provenance(tmp_path_factory=None):
    """真实回填产物:凡无源行证据的 printed 必须为 null+unknown(抽查 batch-C)。"""
    import phase2_identity_backfill as bf
    batch = bf.DEFAULT_OUT
    if not batch.exists():
        pytest.skip("batch-C 数据不在本 checkout")
    checked = 0
    for p in sorted(batch.rglob("*.manifest.json")):
        man = json.loads(p.read_text(encoding="utf-8"))
        if (man.get("identity_version") or 0) < 2:
            continue
        for u in man["units"]:
            prov = u.get("printed_provenance")
            pn = u.get("printed_number")
            if prov == "unknown":
                assert pn is None, (p.name, u.get("unit_id"))
            if prov == "migration_report":
                assert pn, (p.name, u.get("unit_id"))
            checked += 1
    assert checked > 1000  # 覆盖面保证:不是只抽了个别文件


# ── P2-08 unit_id 重复不得导致身份碰撞(位置分配,unit_id 仅展示) ──────────
def test_p2_08_duplicate_unit_ids_no_collision():
    lines = ["# 卷", "", "## 一、选择题", "1. 甲", "2. 乙",
             "", "## 二、非选择题", "1. 丙"]
    man = {"units": [
        {"unit_id": "Q1", "question_numbers": [1], "stem_lines": [4, 4]},
        {"unit_id": "Q1", "question_numbers": [2], "stem_lines": [5, 5]},
        {"unit_id": "Q1", "question_numbers": [3], "stem_lines": [8, 8]},
    ]}
    qi.assign_identity(man, lines)
    refs = [u["section_ref"] for u in man["units"]]
    assert refs[0] == refs[1] != refs[2]
    fails, reviews = qi.check_identity(man, len(lines))
    assert fails == [] and reviews == []


@pytest.mark.parametrize("bad", ["-1", "-2", "-3"])
def test_mutation_sanity_keep_evidence_is_enforced(bad):
    """变异校验:证据机制三处破坏(空证据/越界证据/两个非 keep 混重号)必须
    都被拦截——保证本文件的 PASS 不是'代码跑完就算'。"""
    ev_ok = "分节标题 L15:二、综合题"
    if bad == "-3":
        # 两个非 keep 同号(BUG-22 形态)→ 必须 FAIL
        units = [_unit("A1", [1], "S1", basis="shift", evidence=ev_ok),
                 _unit("B1", [1], "S2", basis="printed_as_is")]
        fails, _ = qi.check_identity(_v2(units=units), N_LINES)
        assert fails, "两个非 keep 跨分节重号必须 FAIL"
    else:
        ev_bad = "" if bad == "-1" else "L99999 越界"
        units = [_unit("A1", [1], "S1", basis="keep", evidence=ev_bad),
                 _unit("B1", [1], "S2", basis="keep", evidence=ev_ok)]
        fails, reviews = qi.check_identity(_v2(units=units), N_LINES)
        assert reviews and not fails, "证据缺失/越界必须 PENDING_REVIEW"

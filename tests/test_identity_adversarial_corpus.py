# -*- coding: utf-8 -*-
"""Phase 3:Question Identity 对抗语料(R35)——Evidence Soundness。

第五轮审查裁定:Phase 3 不再堆规则,攻击"PASS 为什么成立":
  PASS  = 机器能够证明
  FAIL  = 机器能够证伪
  PENDING_REVIEW = 机器无法证明也无法证伪
核心新增:第二层证据语义检查——basis_evidence 引用的行必须真的承载
编号语义(question_identity.evidence_semantic_reason)。

语料覆盖审查冻结的 16 类攻击面;每条走生产代码
(question_identity.check_identity / reslice_qc.check / backfill)。
"""
import json
from pathlib import Path

import pytest

import phase2_identity_backfill as bf
import question_identity as qi

# 对抗语料卷:正常编号 + 合法模块 + 纯 prose 行 + 无关答案键位行
LINES = [
    "# 2024 对抗语料卷",                    # L1
    "",                                     # L2
    "## 一、选择题",                        # L3
    "1. 下列说法正确的是（ ）",              # L4
    "A. 甲",                               # L5
    "2. 第二题题干（ ）",                   # L6
    "",                                     # L7
    "## 《有机化学基础》模块试题",            # L8
    "1. 模块题干甲（ ）",                    # L9
    "2. 模块题干乙（ ）",                    # L10
    "",                                     # L11
    "## 二、非选择题",                       # L12
    "3. 综合题干（ ）",                      # L13
    "",                                     # L14
    "本卷依据课程标准命制,注重考查核心素养。",  # L15 纯 prose,无编号语义
    "26.【答案】A",                          # L16 行首题号与 keep 单元无关
]
N = len(LINES)


def _u(uid, nums, stem, basis="printed_as_is", ev="", printed=None):
    return {"unit_id": uid, "unit_type": "standalone_question",
            "question_numbers": list(nums), "original_question_type": "fill_in",
            "stem_lines": [stem, stem], "options_lines": None,
            "answer_lines": None, "explanation_lines": None,
            "printed_number": list(printed if printed is not None else nums),
            "printed_provenance": "source_line",
            "basis": basis, "basis_evidence": ev}


def _man(units):
    man = {"units": units}
    qi.assign_identity(man, LINES)
    return man


EV_MODULE = "选考模块互斥;分节标题 L8:《有机化学基础》模块试题"


# 1 baseline:正常全局编号 → 无问题
def test_c01_baseline_global_numbering():
    man = _man([_u("Q1", [1], 4), _u("Q2", [2], 6), _u("N3", [3], 13)])
    assert qi.check_identity(man, N, LINES) == ([], [])


# 2 合法独立模块:keep + 标题行证据 → PASS
def test_c02_legal_module_keep_passes():
    man = _man([_u("Q1", [1], 4), _u("Q2", [2], 6),
                _u("M1", [1], 9, basis="keep", ev=EV_MODULE)])
    assert qi.check_identity(man, N, LINES) == ([], [])


# 3 非法跨 section 重号(BUG-22 原型)→ FAIL
def test_c03_illegal_cross_section_dup_fails():
    man = _man([_u("Q1", [1], 4), _u("N1", [1], 13, basis="shift")])
    fails, _ = qi.check_identity(man, N, LINES)
    assert any("非 keep" in f for f in fails)


# 4 同 section 重号:keep 不得成为万能 bypass → FAIL
def test_c04_same_section_keep_bypass_fails():
    man = _man([_u("Q1", [1], 4),
                _u("Q1b", [1], 6, basis="keep", ev=EV_MODULE)])
    fails, _ = qi.check_identity(man, N, LINES)
    assert any("同分节重复" in f for f in fails)


# 5 同名 section:occurrence 消歧后 keep 跨块合法
def test_c05_same_title_sections_occurrence():
    lines = ["# 卷", "", "## 实验题", "1. 甲", "", "## 实验题", "1. 乙"]
    man = {"units": [
        _u("A1", [1], 4, basis="keep", ev="汇编独立编号;分节标题 L3:实验题"),
        _u("B1", [1], 7, basis="keep", ev="汇编独立编号;分节标题 L6:实验题"),
    ]}
    qi.assign_identity(man, lines)
    assert man["units"][0]["section_ref"] != man["units"][1]["section_ref"]
    assert qi.check_identity(man, len(lines), lines) == ([], [])


# 6 section 缺失 → PENDING_REVIEW(identity_scope_missing),绝不静默 PASS
def test_c06_missing_section_pending_review():
    man = _man([_u("Q1", [1], 4), _u("Q2", [2], 6)])
    for u in man["units"]:
        u.pop("section_ref", None)
    fails, reviews = qi.check_identity(man, N, LINES)
    assert fails == []
    assert any("identity_scope_missing" in r for r in reviews)


# 7 evidence 越界 → PENDING_REVIEW
def test_c07_evidence_out_of_bounds():
    man = _man([_u("Q1", [1], 4),
                _u("M1", [1], 9, basis="keep", ev="分节标题 L99999:模块")])
    fails, reviews = qi.check_identity(man, N, LINES)
    assert fails == [] and reviews


# 8 evidence 不存在 → PENDING_REVIEW
def test_c08_evidence_missing():
    man = _man([_u("Q1", [1], 4),
                _u("M1", [1], 9, basis="keep", ev="")])
    fails, reviews = qi.check_identity(man, N, LINES)
    assert fails == [] and reviews


# 9 ★核心攻击:evidence 行存在但无编号语义(纯 prose)→ 不得据此放行
def test_c09_evidence_line_without_numbering_semantics():
    man = _man([_u("Q1", [1], 4),
                _u("M1", [1], 9, basis="keep", ev="依据说明;L15")])
    fails, reviews = qi.check_identity(man, N, LINES)
    assert fails == []
    assert any("无编号语义" in r for r in reviews), reviews


# 10 ★核心攻击:evidence 指向题号与本单元无关的行("26.【答案】")
def test_c10_evidence_points_to_wrong_question():
    man = _man([_u("Q1", [1], 4),
                _u("M1", [1], 9, basis="keep", ev="答案区键位;L16")])
    fails, reviews = qi.check_identity(man, N, LINES)
    assert fails == []
    assert any("行首题号与本单元无关" in r for r in reviews), reviews


# 11 OCR 行号正确但内容错(引用行是 OCR 噪声)→ 同机制拦截
def test_c11_evidence_line_ocr_noise():
    lines = LINES + ["鍚tériBeginInit 骞囧簲瀵�"]  # 噪声行 L17
    man = {"units": [
        _u("Q1", [1], 4),
        _u("M1", [1], 9, basis="keep", ev="噪声;L17"),
    ]}
    qi.assign_identity(man, lines)
    fails, reviews = qi.check_identity(man, len(lines), lines)
    assert fails == []
    assert any("无编号语义" in r for r in reviews), reviews


# 12 canonical 正确、printed 无证据 → 保持 unknown,不得猜测
def test_c12_printed_unknown_preserved():
    u = {"question_numbers": [26], "stem_lines": [15, 15]}
    pn, prov = bf.printed_from_stem(u, LINES)  # L15 无题号前缀
    assert (pn, prov) == (None, "unknown")


# 13 duplicate unit_id → 身份与 unit_id 解耦,不碰撞
def test_c13_duplicate_unit_id_decoupled():
    man = _man([_u("U", [1], 4), _u("U", [2], 6), _u("U", [3], 13)])
    assert qi.check_identity(man, N, LINES) == ([], [])


# 14 section 顺序变化:插入新分节后重派 → ordinal 确定性重排,无冲突
def test_c14_section_reorder_reassigns_deterministically():
    lines2 = LINES[:7] + ["## 新增分节", "1. 新题（ ）", ""] + LINES[7:]
    man = {"units": [_u("Q1", [1], 4), _u("M1", [1], 12, basis="keep",
                                         ev="模块;L11:新增分节")]}
    qi.assign_identity(man, lines2)
    ords = [s["ordinal"] for s in man["sections"] if not s.get("derived")]
    assert ords == sorted(ords) and len(set(ords)) == len(ords)
    assert qi.check_identity(man, len(lines2), lines2)[0] == []


# 15 section 拆分/合并 → 旧 locator 越界必须被证伪(FAIL)
def test_c15_locator_drift_detected():
    man = _man([_u("Q1", [1], 4), _u("Q2", [2], 6), _u("N3", [3], 13)])
    fails, _ = qi.check_identity(man, 8, LINES[:8])  # 源被截断,span 越界
    assert any("span 非法" in f for f in fails)


# 16 migration 重跑幂等:真实 batch-C 二次回填必须字节一致
def test_c16_backfill_idempotent_on_real_data():
    if not bf.DEFAULT_OUT.exists():
        pytest.skip("batch-C 数据不在本 checkout")
    mig = json.loads(bf.MIGRATION.read_text(encoding="utf-8"))
    mig_by_file = {Path(f["file"]).name: f["changes"] for f in mig["files"]}
    mds = sorted(bf.DEFAULT_OUT.rglob("*.manifest.json"))[:5]
    assert mds
    for p in mds:
        md = p.with_name(p.name[: -len(".manifest.json")] + ".md")
        bf.backfill_file(md, mig_by_file, apply=True)
        first = p.read_bytes()
        bf.backfill_file(md, mig_by_file, apply=True)
        assert p.read_bytes() == first, f"非幂等: {p.name}"

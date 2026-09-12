# -*- coding: utf-8 -*-
"""R36:pilot 16 份 v1 → QuestionIdentity v2 确定性迁移验收。

第五轮审查 R35 裁定后的收尾动作:生产数据不得并存两套 identity contract。
六条验收(用户冻结):
  1. migration success(15/16;第 16 份被 C13 如实拒写,见 BUG-35)
  2. identity schema validation
  3. C13/C14 无 fail
  4. 幂等(二次迁移字节一致)
  5. 不产生非法 PASS(既有缺陷卷迁移后仍 FAIL)
  6. 不改变既有正确 identity(内容事实逐单元不变,对照迁移前快照)
另含 verify_post 变异 sanity:三类破坏(伪造 printed/事实漂移/注入同节重号)
必须全部被迁移自检拦截,证明验收不是"代码跑完就算"。
"""
import json
from pathlib import Path

import pytest

import phase2_identity_backfill as bf
import phase3_pilot_v1_migration as p3m
import question_identity as qi
import reslice_qc

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "Ocr-markdown/resliced-pilot"
FACTS = ROOT / "data/phase3_pilot_v1_facts.json"

# 已知被拒写卷(BUG-35:填空题分节标题被过滤器误杀 + 需 keep 三方裁决)
KNOWN_V1 = "2021北京三十一中高一（下）期中化学（教师版）(1).md"


def _pilot_mds():
    if not PILOT.exists():
        pytest.skip("pilot 数据不在本 checkout")
    return sorted(p for p in PILOT.rglob("*.md")
                  if not (p.name.endswith(".annotated.md")
                          or p.name.endswith(".restored.md")))


def _v2_manifests():
    out = []
    for p in _pilot_mds():
        mp = p.with_suffix(".manifest.json")
        man = json.loads(mp.read_text(encoding="utf-8"))
        if (man.get("identity_version") or 1) >= 2:
            out.append((p, mp, man))
    return out


# ── 验收 1:migration success ──────────────────────────────────────────
def test_migration_success_15_of_16():
    mds = _pilot_mds()
    v2 = _v2_manifests()
    assert len(mds) == 16
    assert len(v2) == 15, "应恰好 15 份迁移成功"
    still_v1 = {p.name for p in mds} - {p.name for p, _, _ in v2}
    assert still_v1 == {KNOWN_V1}, f"未迁移卷必须恰是已知被拒写卷: {still_v1}"


# ── 验收 2:schema validation ─────────────────────────────────────────
def test_identity_schema_valid():
    for p, _, man in _v2_manifests():
        assert man["identity_version"] == 2
        assert man["sections"], p.name
        ordinals = [s["ordinal"] for s in man["sections"]]
        assert len(set(ordinals)) == len(ordinals), p.name
        for u in man["units"]:
            assert u.get("section_ref"), (p.name, u.get("unit_id"))
            assert "basis" in u and "printed_provenance" in u, (p.name, u.get("unit_id"))
            assert "printed_number" in u and "basis_evidence" in u, (p.name, u.get("unit_id"))


# ── 验收 3:C13/C14 无 fail ───────────────────────────────────────────
def test_c13_c14_no_fail_after_migration():
    for p, _, man in _v2_manifests():
        lines = bf.load_lines(man)
        fails, _ = qi.check_identity(man, len(lines), lines)
        assert fails == [], (p.name, fails)


# ── 验收 4:幂等(字节级)────────────────────────────────────────────────
def test_migration_idempotent_byte_identical():
    for p, mp, _ in _v2_manifests():
        bf.backfill_file(p, {}, apply=True)
        first = mp.read_bytes()
        bf.backfill_file(p, {}, apply=True)
        assert mp.read_bytes() == first, f"非幂等: {p.name}"


# ── 验收 5:不产生非法 PASS ────────────────────────────────────────────
def test_no_illegal_pass():
    for p in _pilot_mds():
        r = reslice_qc.check(p)
        if p.name == KNOWN_V1:
            assert r["verdict"] != "PASS", "既有缺陷卷迁移后不得变 PASS"
        elif r["verdict"] == "PASS":
            assert r["identity_version"] == 2, (p.name, "PASS 必须建立在 v2 契约上")


# ── 验收 6:不改变既有正确 identity(对照迁移前事实快照)──────────────────
def test_fact_preservation_against_snapshot():
    _pilot_mds()  # 语料 gitignored:CI 等无语料环境必须 skip,不得只看快照存在
    if not FACTS.exists():
        pytest.skip("迁移前事实快照不在本 checkout")
    snap = json.loads(FACTS.read_text(encoding="utf-8"))["files"]
    assert len(snap) == 16
    for rel, facts in snap.items():
        man = json.loads((ROOT / rel).with_suffix(".manifest.json")
                         .read_text(encoding="utf-8"))
        live = p3m.facts_of(man)
        assert live == facts, f"内容事实被改动: {rel}"


# ── provenance 自洽(source_line 必须回源成立)───────────────────────────
def test_printed_provenance_sound():
    n = 0
    for _, _, man in _v2_manifests():
        lines = bf.load_lines(man)
        for u in man["units"]:
            if u.get("printed_provenance") != "source_line":
                continue
            pn, prov = bf.printed_from_stem(u, lines)
            assert prov == "source_line" and pn == u["printed_number"], \
                (man["source_file"], u.get("unit_id"))
            n += 1
    assert n > 100, "覆盖面保证:不是只查了个别单元"


# ── 变异 sanity:迁移自检必须对三类破坏敏感 ─────────────────────────────
@pytest.mark.parametrize("bad", ["-1", "-2", "-3"])
def test_mutation_sanity_verify_post_catches(bad):
    p, _, man = _v2_manifests()[0]
    lines = bf.load_lines(man)
    pre_facts = p3m.facts_of(man)
    import copy
    m2 = copy.deepcopy(man)
    if bad == "-1":
        # 伪造 printed:provenance=source_line 但源行解析不出该号
        u = next(u for u in m2["units"]
                 if u.get("printed_provenance") == "source_line")
        u["printed_number"] = [999]
    elif bad == "-2":
        # 事实漂移:偷偷改 canonical 题号
        m2["units"][0]["question_numbers"] = [999]
    else:
        # 注入同分节重号(keep bypass 形态不允许在这里放行)
        m2["units"].append(copy.deepcopy(m2["units"][0]))
        m2["units"][-1]["basis"] = "keep"
        m2["units"][-1]["basis_evidence"] = "分节标题 L1:伪造证据"
    viol = p3m.verify_post(m2, lines, pre_facts)
    assert viol, f"变异 {bad} 必须被迁移自检拦截"


# ── R38 A5:--refresh-v2 的 FACTS 事实锚点守卫(此前零测试覆盖) ─────────────
GUARD_LINES = ["# 合成刷新守卫卷", "", "## 一、选择题", "1. 甲（ ）", "",
               "## 二、非选择题", "2. 乙（ ）"]


def _guard_repo(workdir):
    d = workdir / "pilot_refresh_guard"
    d.mkdir()
    src = d / "guard.md"
    src.write_text("\n".join(GUARD_LINES) + "\n", encoding="utf-8", newline="")
    man = {"identity_version": 2, "units": [
        {"unit_id": "Q1", "unit_type": "standalone_question",
         "question_numbers": [1], "original_question_type": "fill_in",
         "stem_lines": [4, 4], "options_lines": None, "answer_lines": None,
         "explanation_lines": None},
        {"unit_id": "Q2", "unit_type": "standalone_question",
         "question_numbers": [2], "original_question_type": "fill_in",
         "stem_lines": [7, 7], "options_lines": None, "answer_lines": None,
         "explanation_lines": None}],
        "source_file": str(src)}
    mf = d / "guard.manifest.json"
    mf.write_text(json.dumps(man, ensure_ascii=False, indent=1),
                  encoding="utf-8", newline="\n")
    rel = str(src.relative_to(ROOT)).replace("\\", "/")
    return src, mf, rel, man


def test_refresh_v2_refuses_on_facts_drift(workdir, monkeypatch):
    """事实与 R36 FACTS 快照不一致 → 拒绝刷新,manifest 字节不动。"""
    src, mf, rel, man = _guard_repo(workdir)
    pre = mf.read_bytes()
    drifted = [dict(f, question_numbers=[999]) for f in p3m.facts_of(man)]
    monkeypatch.setattr(p3m, "FACTS_MAP", {rel: drifted})
    entry, _ = p3m.migrate_file(src, apply=True, refresh_v2=True)
    assert entry.get("violations") and "FACTS" in entry["violations"][0]
    assert mf.read_bytes() == pre, "拒刷时 manifest 必须字节不动"


def test_refresh_v2_refuses_when_anchor_missing(workdir, monkeypatch):
    """FACTS 快照缺该文件 → 拒绝刷新(无锚点不得静默覆盖)。"""
    src, mf, rel, man = _guard_repo(workdir)
    pre = mf.read_bytes()
    monkeypatch.setattr(p3m, "FACTS_MAP", {})
    entry, _ = p3m.migrate_file(src, apply=True, refresh_v2=True)
    assert entry.get("violations") and "缺该文件" in entry["violations"][0]
    assert mf.read_bytes() == pre


def test_refresh_v2_proceeds_when_anchor_matches(workdir, monkeypatch):
    """锚点一致 → 正常刷新(无 violations),身份键重算后仍 v2。"""
    src, mf, rel, man = _guard_repo(workdir)
    monkeypatch.setattr(p3m, "FACTS_MAP", {rel: p3m.facts_of(man)})
    entry, _ = p3m.migrate_file(src, apply=True, refresh_v2=True)
    assert not entry.get("violations"), entry.get("violations")
    assert entry.get("applied") and entry.get("refresh_v2")
    post = json.loads(mf.read_text(encoding="utf-8"))
    assert post["identity_version"] == 2 and post["sections"]
    assert all(u.get("section_ref") for u in post["units"])

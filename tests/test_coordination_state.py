# -*- coding: utf-8 -*-
"""Cross-Agent Coordination Protocol v0.1 — state.yaml schema 钉住测试。

目的:保证 Docs/COORDINATION/state.yaml 始终机器可读、EB/FACT/DEC 结构不腐化。
性质:只读文件 + schema 断言,不涉及 pipeline/Resolver/Contract 任何行为。
"""
import pathlib

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
STATE = ROOT / "Docs" / "COORDINATION" / "state.yaml"
PROTOCOL = ROOT / "Docs" / "COORDINATION" / "PROTOCOL.md"
CURRENT = ROOT / "Docs" / "COORDINATION" / "CURRENT.md"
HANDOFFS = ROOT / "Docs" / "COORDINATION" / "HANDOFFS"

EB_STATES = {"DISCOVERED", "EVIDENCED", "ATTRIBUTED", "PROPOSED",
             "DECIDED", "IMPLEMENTED", "VERIFIED", "CLOSED"}


def _load():
    with open(STATE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_state_yaml_machine_readable():
    d = _load()
    assert isinstance(d, dict)
    assert d["coordination_version"] == 1
    for key in ("workstream", "agents", "facts", "decisions",
                "open_questions", "prohibitions"):
        assert key in d, f"missing top-level key: {key}"


def test_single_master_ledger_declared():
    """单主规则:canonical ledger 只有一个,V3 侧为镜像。"""
    d = _load()
    agents = d["agents"]
    canonical = [k for k, v in agents.items() if v.get("ledger_role") == "canonical"]
    assert canonical == ["preprocessing"]
    assert agents["v3"]["ledger_role"] == "mirror_via_handoff"


def test_eb_ids_unique_and_status_valid():
    d = _load()
    ids = [q["id"] for q in d["open_questions"]]
    assert len(ids) == len(set(ids)), "duplicate EB id"
    for q in d["open_questions"]:
        assert q["id"].startswith("EB-")
        assert q["status"] in EB_STATES, f"{q['id']} invalid status {q['status']}"
        assert q["owner"] in {"dsh", "v3", "joint"}
        assert q.get("facts"), f"{q['id']} must reference facts"


def test_facts_carry_evidence_and_confidence():
    """FACT 必须带 evidence + confidence(REPORTED 不得冒充 OBSERVED)。"""
    d = _load()
    ids = [f["id"] for f in d["facts"]]
    assert len(ids) == len(set(ids)), "duplicate FACT id"
    for f in d["facts"]:
        assert f["id"].startswith("FACT-")
        assert f.get("evidence"), f"{f['id']} missing evidence"
        assert f["confidence"] in {"OBSERVED", "INFERRED", "REPORTED"}
        assert f["source"] in {"preprocessing", "v3", "both"}
        assert f["status"] in {"observed", "disputed", "retracted"}


def test_decisions_carry_authority():
    d = _load()
    ids = [x["id"] for x in d["decisions"]]
    assert len(ids) == len(set(ids)), "duplicate DEC id"
    for x in d["decisions"]:
        assert x["id"].startswith("DEC-")
        assert x.get("authority"), f"{x['id']} missing authority"
        assert x["status"] in {"active", "frozen", "superseded"}


def test_prohibitions_present():
    """两侧共同禁止事项必须在册(至少覆盖不改 Frozen Spec / 不合并分母)。"""
    d = _load()
    text = " ".join(d["prohibitions"])
    assert "Frozen Spec" in text
    assert "分母" in text


def test_coordination_layer_files_exist():
    assert PROTOCOL.is_file()
    assert CURRENT.is_file()
    assert HANDOFFS.is_dir()
    assert any(HANDOFFS.glob("*.md")), "at least one handoff must exist"


def test_first_handoff_present():
    h = HANDOFFS / "2026-09-15-DSH-to-Claude-001.md"
    assert h.is_file()
    text = h.read_text(encoding="utf-8")
    for section in ("## From", "## To", "## New Evidence",
                    "## Questions for Receiver", "## Explicitly Do Not Do"):
        assert section in text, f"handoff missing section {section}"


def test_coordination_layer_not_architecture_authority():
    """协议自证:协调层明文声明不是架构权威层。"""
    text = PROTOCOL.read_text(encoding="utf-8")
    assert "不是架构权威层" in text
    assert "不产生" in text and "L0" in text

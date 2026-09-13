# -*- coding: utf-8 -*-
"""R57(G-TAX-1 裁定落地):规则登记册与代码双向钉住。

  rr_t1  reslice_qc.py 中出现的每个 C 族 verdict id 必须登记在册
  rr_t2  登记册 §1 的 C 族行不得多于代码(防"册上幽灵规则")
  rr_t3  探针 P13–P15 / F1 / I0–I3 必须在册
  rr_t4  五类 taxonomy 与登记字段表头齐备 + 退役政策在册
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG = (ROOT / "governance/rule_registry.md").read_text(encoding="utf-8")
QC = (ROOT / "scripts/reslice_qc.py").read_text(encoding="utf-8")


def qc_verdict_ids():
    ids = {int(m.group(1)) for m in re.finditer(r"C(\d{1,2})", QC)
           if 1 <= int(m.group(1)) <= 14}
    return {f"C{i}" for i in ids}


def registry_c_rows():
    sec1 = REG.split("## 2.")[0]
    return set(re.findall(r"^\|\s*(C\d{1,2})\s*\|", sec1, re.M))


def test_rr_t1_code_rules_all_registered():
    missing = qc_verdict_ids() - registry_c_rows()
    assert not missing, f"代码存在但未登记: {sorted(missing)}"


def test_rr_t2_no_phantom_registry_rows():
    phantom = registry_c_rows() - qc_verdict_ids()
    assert not phantom, f"登记册幽灵规则(代码无): {sorted(phantom)}"


def test_rr_t3_probe_f1_invariants_registered():
    for rid in ("P13", "P14", "P15", "F1", "I0", "I1", "I2", "I3"):
        assert rid in REG, rid


def test_rr_t4_taxonomy_and_retirement_fields():
    for cls in ("FACT_INTEGRITY", "STRUCTURE", "IDENTITY", "EVIDENCE",
                "QUALITY"):
        assert cls in REG, cls
    for field in ("purpose", "attack surface", "evidence", "retirement"):
        assert field in REG, field
    assert "Rule Retirement Policy" in REG
    assert "审计审计系统" in REG  # 递归审计防线条款在册

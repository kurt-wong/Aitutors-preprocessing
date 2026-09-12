# -*- coding: utf-8 -*-
"""R48:Resolver 消费契约生产侧前置条件预检的 CI 契约测试(合成语料)。

pc1–pc10 中可离线测的核心分支:
  t1 干净 v2 产物 → 0 findings,且 QC verdict 可计算(C-IN-2 前提);
  t2 伪造 printed(provenance=unknown 但 printed 非空)→ pc7 必须咬住;
  t3 非法 basis(大小写漂移 "Explicit")→ pc5 必须咬住(schema violation);
  t4 v1 输入 → pc1 拒收标记(C-IN-1:resolver 只消费 v2)。

t2/t3/t4 即变异注入——预检的区分力由缺陷形态本身证明。
"""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import question_identity as qi  # noqa: E402
import resolver_contract_preflight as pf  # noqa: E402
from conftest import make_repo, SYNTH_LINES, SYNTH_MAN  # noqa: E402


def _v2_man():
    man = copy.deepcopy(SYNTH_MAN)
    qi.assign_identity(man, list(SYNTH_LINES))
    for u in man["units"]:
        u["basis"] = "printed_as_is"
        u["printed_provenance"] = "source_line"
        u["printed_number"] = list(u["question_numbers"])
    return man


def _repo(workdir, man=None):
    _, _, out_dir = make_repo(workdir, lines=list(SYNTH_LINES),
                              man=man if man is not None else _v2_man())
    return out_dir


def _check(out_dir):
    return pf.check_manifest(out_dir / "synthetic.md")


def test_clean_v2_repo_zero_findings(workdir):
    out_dir = _repo(workdir)
    findings, meta = _check(out_dir)
    assert findings == [], findings
    assert meta["identity_version"] == 2
    assert meta["qc_verdict"] == "PASS", \
        f"合成基线 QC verdict 应可计算且为 PASS,实际 {meta['qc_verdict']}"


def test_fabricated_printed_fires_pc7(workdir):
    man = _v2_man()
    # provenance=unknown 却携带 printed_number = 伪造 Source Fact 形态
    man["units"][0]["printed_provenance"] = "unknown"
    out_dir = _repo(workdir, man=man)
    findings, _ = _check(out_dir)
    hits = [f for f in findings if f.startswith("pc7")]
    assert hits, f"伪造 printed 未被 pc7 咬住: {findings}"


def test_invalid_basis_fires_pc5(workdir):
    man = _v2_man()
    man["units"][0]["basis"] = "Explicit"  # 大小写漂移,R42 BUG-27 家族
    out_dir = _repo(workdir, man=man)
    findings, _ = _check(out_dir)
    hits = [f for f in findings if f.startswith("pc5")]
    assert hits, f"非法 basis 未被 pc5 咬住: {findings}"


def test_v1_input_fires_pc1(workdir):
    man = _v2_man()
    for k in ("identity_version", "sections"):
        man.pop(k, None)
    for u in man["units"]:
        u.pop("section_ref", None)
    out_dir = _repo(workdir, man=man)
    findings, meta = _check(out_dir)
    hits = [f for f in findings if f.startswith("pc1")]
    assert hits and meta["identity_version"] == 1, \
        f"v1 输入未被 pc1 标记: {findings}"

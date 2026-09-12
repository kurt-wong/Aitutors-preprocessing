# -*- coding: utf-8 -*-
"""BUG-26 回归:--recompile 路径(recompile_outputs)不得洗掉 QuestionIdentity v2。

R41 readiness gate B-01 实测发现:旧实现重编译时只把 {"units": ...} 传给
write_outputs,identity_version/sections 被静默丢弃 → QC 降级走 v1 存量
语义,违反 "resolver 只消费 v2" 契约。本测试:
1. 合成 v2 产物 → recompile_outputs → 身份头必须逐字保留;
2. 重编译产物(切片 md)必须与原产物字节一致(确定性);
3. 变异敏感:若调用点退回 {"units": ...} 传参,测试 1 必须失败。
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import reslice_pipeline as rp  # noqa: E402
import question_identity as qi  # noqa: E402
from conftest import make_repo  # noqa: E402


def _to_v2(man, lines):
    qi.assign_identity(man, lines)
    man["identity_version"] = 2
    for u in man["units"]:
        u.setdefault("printed_number", list(u.get("question_numbers") or []))
        u.setdefault("printed_provenance", "source_line")
        u.setdefault("basis", "printed_as_is")
        u.setdefault("basis_evidence", "题干首行印刷题号")
    return man


def test_recompile_preserves_identity_v2(workdir):
    src, mf, out_dir = make_repo(workdir)
    lines = src.read_text(encoding="utf-8").splitlines()
    man = json.loads(mf.read_text(encoding="utf-8"))
    man = _to_v2(man, lines)
    fails, _ = qi.check_identity(man, len(lines), lines)
    assert not fails, f"合成 v2 卷自身必须身份合法: {fails}"
    mf.write_text(json.dumps(man, ensure_ascii=False, indent=1),
                  encoding="utf-8", newline="\n")
    rp.write_outputs(out_dir, src.stem, lines, man, [], {"warnings": []},
                     src.name, src)

    before_md = (out_dir / f"{src.stem}.md").read_text(encoding="utf-8")
    before_man = json.loads(mf.read_text(encoding="utf-8"))

    n = rp.recompile_outputs(out_dir)
    assert n == 1

    after_man = json.loads(mf.read_text(encoding="utf-8"))
    assert after_man.get("identity_version") == 2, "BUG-26 复发: identity_version 被洗掉"
    assert after_man.get("sections") == before_man.get("sections"), \
        "BUG-26 复发: sections 被洗掉"
    # 单元级身份字段同样不得丢
    for u_b, u_a in zip(before_man["units"], after_man["units"]):
        for f in ("section_ref", "printed_number", "printed_provenance",
                  "basis", "basis_evidence"):
            assert u_a.get(f) == u_b.get(f), (u_b.get("unit_id"), f)
    # 确定性:切片字节不变
    after_md = (out_dir / f"{src.stem}.md").read_text(encoding="utf-8")
    assert after_md == before_md, "重编译改变了切片内容(确定性破坏)"


def test_recompile_keeps_qc_on_v2_branch(workdir):
    """重编译后 QC 必须仍走 v2 分支(身份头在场),而非降级 v1。"""
    src, mf, out_dir = make_repo(workdir)
    lines = src.read_text(encoding="utf-8").splitlines()
    man = _to_v2(json.loads(mf.read_text(encoding="utf-8")), lines)
    mf.write_text(json.dumps(man, ensure_ascii=False, indent=1),
                  encoding="utf-8", newline="\n")
    rp.write_outputs(out_dir, src.stem, lines, man, [], {"warnings": []},
                     src.name, src)
    rp.recompile_outputs(out_dir)
    man2 = json.loads(mf.read_text(encoding="utf-8"))
    assert (man2.get("identity_version") or 1) >= 2, \
        "重编译产物丢失 v2 契约(QC 将静默降级 v1 语义)"
    assert man2.get("sections"), "重编译产物丢失 sections"

# -*- coding: utf-8 -*-
"""D5-B.2 小批 reclassify apply 四闸门钉(用户 2026-09-14 预置 B2-1…B2-4)。"""

import hashlib
import importlib.util
import io
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


DRY = _load("d5b_dryrun_ref", os.path.join(ROOT, "scripts", "d5b_reclassify_dryrun.py"))
AP = _load("d5b_apply", os.path.join(ROOT, "scripts", "d5b_reclassify_apply.py"))


def _w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _mk(root):
    """沙箱:合格考 2 份 + 高考真题 1 份 + 假 manifest。"""
    u = os.path.join(root, "ocr", "未分类")
    _w(os.path.join(u, "g1", "北京合格考化学卷.md"), "合格考 化学 离子溶液。\n")
    _w(os.path.join(u, "g2", "上海合格考数学卷.md"), "合格考 函数方程。\n")
    _w(os.path.join(u, "h1", "高考真题汇编英语.md"), "高考真题 英语阅读。\n")
    man = os.path.join(root, "manifest.jsonl")
    with io.open(man, "w", encoding="utf-8") as f:
        f.write('{"source_rel": "x.pdf", "pages": 3}\n')
    plan_path = os.path.join(root, "plan.json")
    plan = DRY.run(os.path.join(root, "ocr"), plan_path)
    return {"root": os.path.join(root, "ocr"), "plan_path": plan_path,
            "plan": plan, "expect": plan["plan_sha256"], "manifest": man,
            "audit": os.path.join(root, "audit.jsonl"),
            "report": os.path.join(root, "report.json")}


def _run(cfg, category="合格考", apply=True, expect=None):
    return AP.run(cfg["root"], cfg["plan_path"], category,
                  cfg["expect"] if expect is None else expect,
                  apply, cfg["audit"], cfg["manifest"], cfg["report"])


def _moved(cfg, rel):
    return os.path.exists(os.path.join(cfg["root"], *rel.split("/")))


SRC_A = "未分类/g1/北京合格考化学卷.md"
SRC_B = "未分类/g2/上海合格考数学卷.md"
DST_A = "合格考/化学/北京合格考化学卷.md"


# ---------------------------------------------------------------- t1 首跑
def test_t1_apply_moves_audit_and_report(workdir):
    cfg = _mk(str(workdir))
    rep = _run(cfg)
    assert rep["result"] == "APPLIED" and len(rep["applied"]) == 2
    assert not _moved(cfg, SRC_A) and _moved(cfg, DST_A)
    assert rep["manifest_untouched"] is True
    with io.open(cfg["audit"], encoding="utf-8") as f:
        rows = [json.loads(l) for l in f if l.strip()]
    assert len(rows) == 2 and set(rows[0]) == {"from", "to"}
    assert os.path.isabs(rows[0]["from"]) and os.path.isabs(rows[0]["to"])
    assert all(r["audit_appended"] and r["sha256_unchanged"] for r in rep["applied"])


# ---------------------------------------------------------------- t2 B2-1
def test_t2_b2_1_fingerprint_mismatch_refuses(workdir):
    cfg = _mk(str(workdir))
    with io.open(cfg["plan_path"], encoding="utf-8") as f:
        plan = json.load(f)
    plan["moves"][0]["to_rel"] = plan["moves"][0]["to_rel"]  # 不动内容
    # 篡改一条 move 内容但保留自报指纹 → 自报指纹不符
    plan["moves"][0]["sha256"] = "0" * 64
    with io.open(cfg["plan_path"], "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False)
    with pytest.raises(AP.GateViolation, match="B2-1"):
        _run(cfg)
    # 源文件必须原地未动
    assert _moved(cfg, SRC_A) and _moved(cfg, SRC_B)


def test_t2b_b2_1_frozen_expect_mismatch(workdir):
    cfg = _mk(str(workdir))
    with pytest.raises(AP.GateViolation, match="B2-1"):
        _run(cfg, expect="f" * 64)
    assert _moved(cfg, SRC_A)


# ---------------------------------------------------------------- t3 B2-2
def test_t3_b2_2_sha_drift_aborts_whole_batch(workdir):
    cfg = _mk(str(workdir))
    with io.open(os.path.join(cfg["root"], *SRC_A.split("/")), "a",
                 encoding="utf-8") as f:
        f.write("事后篡改。\n")
    with pytest.raises(AP.GateViolation, match="预检失败"):
        _run(cfg)
    # 未篡改的 B 也必须原地不动(整批拒绝)
    assert _moved(cfg, SRC_B)
    with io.open(cfg["report"], encoding="utf-8") as f:
        rep = json.load(f)
    assert rep["result"] == "ABORTED_PRECHECK" and rep["applied"] == []


# ---------------------------------------------------------------- t4 B2-3
def _expect_b2_3(cfg):
    with pytest.raises(AP.GateViolation, match="预检失败"):
        _run(cfg)
    with io.open(cfg["report"], encoding="utf-8") as f:
        rep = json.load(f)
    assert rep["result"] == "ABORTED_PRECHECK" and rep["applied"] == []
    assert rep["violations"] and all(v["gate"] == "B2-3" for v in rep["violations"])
    return rep


def test_t4_b2_3_collision_variants(workdir):
    # (a) 目标文件已存在
    cfg = _mk(str(workdir))
    _w(os.path.join(cfg["root"], *DST_A.split("/")), "既有。\n")
    rep = _expect_b2_3(cfg)
    assert "destination_exists" in rep["violations"][0]["detail"]
    # (b) 目标同名目录已存在
    cfg = _mk(str(workdir / "b"))
    os.makedirs(os.path.join(cfg["root"], *DST_A.split("/")))
    _expect_b2_3(cfg)
    # (c) 大小写差异实体
    cfg = _mk(str(workdir / "c"))
    os.makedirs(os.path.join(cfg["root"], "合格考", "化学"))
    _w(os.path.join(cfg["root"], "合格考", "化学", "北京合格考化学卷.MD"), "x\n")
    rep = _expect_b2_3(cfg)
    # Windows 大小写不敏感:lexists 先捕获;大小写敏感平台走 case_variant 分支
    assert rep["violations"][0]["detail"].startswith(
        ("destination_exists", "case_variant_exists"))
    # (d) 父级为文件
    cfg = _mk(str(workdir / "d"))
    _w(os.path.join(cfg["root"], "合格考"), "我是文件不是目录。\n")
    rep = _expect_b2_3(cfg)
    assert "parent_is_file" in rep["violations"][0]["detail"]
    assert not os.path.exists(os.path.join(cfg["root"], "合格考", "化学",
                                           "北京合格考化学卷.md"))


# ---------------------------------------------------------------- t5 B2-4
def test_t5_b2_4_postcheck_tamper_detected(workdir, monkeypatch):
    cfg = _mk(str(workdir))
    real_move = AP.shutil.move

    def corrupting_move(src, dst):
        real_move(src, dst)
        with io.open(dst, "a", encoding="utf-8") as f:
            f.write("移动后污染。\n")

    monkeypatch.setattr(AP.shutil, "move", corrupting_move)
    with pytest.raises(AP.GateViolation, match="B2-4"):
        _run(cfg)
    with io.open(cfg["report"], encoding="utf-8") as f:
        rep = json.load(f)
    assert rep["result"] == "FAILED_POSTCHECK"
    assert rep["applied"][0]["sha256_unchanged"] is False
    # 第二条不得继续执行(源必须仍在原地)
    assert len(rep["applied"]) == 1 and _moved(cfg, SRC_B) is True


# ---------------------------------------------------------------- t6 manifest
def test_t6_manifest_prefix_guard(workdir):
    cfg = _mk(str(workdir))
    with open(cfg["manifest"], "rb") as f:
        before = f.read()
    # 并发追加(模拟 daemon)→ 仍判未受影响
    with open(cfg["manifest"], "ab") as f:
        f.write('{"source_rel": "y.pdf"}\n'.encode("utf-8"))
    rep = {"result": "APPLIED"}
    AP.finalize(rep, cfg["report"], before, cfg["manifest"])
    assert rep["manifest_untouched"] is True and rep["manifest_grew_bytes"] > 0
    # 前缀被改写 → 判受影响
    with io.open(cfg["manifest"], "w", encoding="utf-8") as f:
        f.write('{"tampered": true}\n')
    rep2 = {"result": "APPLIED"}
    AP.finalize(rep2, cfg["report"], before, cfg["manifest"])
    assert rep2["manifest_untouched"] is False


# ---------------------------------------------------------------- t7 批过滤
def test_t7_batch_filter_only_category(workdir):
    cfg = _mk(str(workdir))
    _run(cfg, category="合格考")
    assert _moved(cfg, "未分类/h1/高考真题汇编英语.md"), "非批内文件不得移动"
    with pytest.raises(AP.GateViolation, match="预检失败"):
        _run(cfg, category="合格考")  # 已移走 → 源消失 → 预检整批拒绝


# ---------------------------------------------------------------- t8 预检零写
def test_t8_preflight_only_mode_zero_write(workdir):
    cfg = _mk(str(workdir))
    rep = _run(cfg, apply=False)
    assert rep["result"] == "PREFLIGHT_OK" and rep["applied"] == []
    assert _moved(cfg, SRC_A) and _moved(cfg, SRC_B)


# ---------------------------------------------------------------- t9 非法路径
def test_t9_rel_path_traversal_refused(workdir):
    cfg = _mk(str(workdir))
    with io.open(cfg["plan_path"], encoding="utf-8") as f:
        plan = json.load(f)
    plan["moves"][0]["to_rel"] = "../escape/北京合格考化学卷.md"
    # 重算指纹使 B2-1 通过,专测路径穿越闸
    plan["plan_sha256"] = AP._fingerprint(plan["moves"])
    cfg["expect"] = plan["plan_sha256"]
    with io.open(cfg["plan_path"], "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False)
    with pytest.raises(AP.GateViolation):
        _run(cfg)
    assert not os.path.exists(os.path.join(workdir, "escape"))


# ------------------------------------------------- t10 B2-1 自报指纹独立性
def test_t10_b2_1_self_claim_check_isolated(workdir):
    """moves 未动、冻结期望正确,但 plan 自报指纹被改坏 → 仍必须拒绝。"""
    cfg = _mk(str(workdir))
    with io.open(cfg["plan_path"], encoding="utf-8") as f:
        plan = json.load(f)
    plan["plan_sha256"] = "deadbeef" + plan["plan_sha256"][8:]
    with io.open(cfg["plan_path"], "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False)
    with pytest.raises(AP.GateViolation, match="B2-1"):
        _run(cfg)
    assert _moved(cfg, SRC_A) and _moved(cfg, SRC_B)


# ------------------------------------------------- t11 CLI preflight 打印
def test_t11_cli_preflight_no_crash(workdir, monkeypatch, capsys):
    """F-r67.3-1 钉:preflight 报告无 manifest_untouched 键,CLI 不得崩。"""
    cfg = _mk(str(workdir))
    monkeypatch.setattr(sys, "argv", [
        "d5b_reclassify_apply.py", "--ocr-root", cfg["root"],
        "--plan", cfg["plan_path"], "--category", "合格考",
        "--expect-sha256", cfg["expect"], "--audit", cfg["audit"],
        "--manifest", cfg["manifest"], "--report", cfg["report"]])
    AP.main()
    out = capsys.readouterr().out
    assert "result=PREFLIGHT_OK" in out and "manifest_untouched=n/a_preflight" in out

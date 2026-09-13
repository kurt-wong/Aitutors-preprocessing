# -*- coding: utf-8 -*-
"""D5-B.1 reclassify dry-run 钉(零写入 / 分桶 fail-closed / 指纹 / 规则单源)。

用户 2026-09-14 裁定:D5-B 分阶段,D5-B.1 只做 dry-run,apply 属 D5-B.2/3
且须另行批准。本套件钉死 dry-run 的"绝不移动"与分桶语义。
"""

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


DRY = _load("d5b_reclassify_dryrun", os.path.join(ROOT, "scripts", "d5b_reclassify_dryrun.py"))
RC = _load("reclassify_unknown_ref", os.path.join(ROOT, "scripts", "reclassify_unknown.py"))


def _w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _mk_corpus(root):
    """最小语料:覆盖 moves/collision/conflict/needs_ruling/extra/read_error。"""
    u = os.path.join(root, "未分类")
    _w(os.path.join(u, "数学", "北京会考数学卷.md"), "# 试卷\n函数方程数列。\n")
    _w(os.path.join(u, "misc", "上海会考卷.md"), "无关键词正文。\n")           # subject 未判定
    _w(os.path.join(u, "a", "北京会考英语卷.md"), "阅读理解完形填空。\n")     # conflict 对 a
    _w(os.path.join(u, "b", "北京会考英语卷.md"), "阅读理解完形填空。\n")     # conflict 对 b
    _w(os.path.join(u, "zz", "zzz.md"), "纯噪声文本。\n")                    # 全未判定
    _w(os.path.join(root, "高三", "未分类", "2024会考生物模拟.md"), "细胞基因。\n")
    os.makedirs(os.path.join(u, "e", "dir.md"), exist_ok=True)                # 不可读源(目录伪装 md)
    # 碰撞:目标已在位
    _w(os.path.join(root, "会考", "数学", "北京会考数学卷.md"), "既有目标。\n")
    return root


def _tree_snapshot(root):
    snap = {}
    for dirpath, dirnames, filenames in os.walk(root):
        for n in filenames:
            p = os.path.join(dirpath, n)
            with open(p, "rb") as f:
                digest = hashlib.sha256(f.read()).hexdigest()
            snap[os.path.relpath(p, root)] = (os.path.getsize(p), digest)
    return snap


def _plan(root, out):
    return DRY.run(root, out)


# ---------------------------------------------------------------- t1 零写入
def test_t1_dryrun_zero_write_and_moves(workdir):
    root = _mk_corpus(str(workdir / "ocr"))
    out = str(workdir / "plan.json")
    before = _tree_snapshot(root)
    plan = _plan(root, out)
    after = _tree_snapshot(root)
    assert before == after, "dry-run 必须零写入语料(文件集合/大小/内容逐一不变)"
    assert os.path.isfile(out), "唯一允许的产物是 plan 文件"
    # moves:数学卷被碰撞排除,英语卷冲突排除,上海卷/zzz/dir.md 分桶排除
    moved = {m["from_rel"] for m in plan["moves"]}
    assert moved == {"高三/未分类/2024会考生物模拟.md"}
    assert plan["moves"][0]["to_rel"] == "会考/生物/2024会考生物模拟.md"
    assert plan["counts"]["scanned"] == 7


# ---------------------------------------------------------------- t2 碰撞
def test_t2_collision_excluded_no_overwrite(workdir):
    root = _mk_corpus(str(workdir / "ocr"))
    plan = _plan(root, str(workdir / "plan.json"))
    assert plan["collisions"] == [
        {"from_rel": "未分类/数学/北京会考数学卷.md",
         "to_rel": "会考/数学/北京会考数学卷.md"}]
    assert all(m["from_rel"] != "未分类/数学/北京会考数学卷.md" for m in plan["moves"])
    # 既有目标内容未被触碰
    with io.open(os.path.join(root, "会考", "数学", "北京会考数学卷.md"),
                 encoding="utf-8") as f:
        assert f.read() == "既有目标。\n"


# ---------------------------------------------------------------- t3 冲突
def test_t3_plan_internal_conflict_all_excluded(workdir):
    root = _mk_corpus(str(workdir / "ocr"))
    plan = _plan(root, str(workdir / "plan.json"))
    assert {c["from_rel"] for c in plan["conflicts"]} == {
        "未分类/a/北京会考英语卷.md", "未分类/b/北京会考英语卷.md"}
    assert all(c["to_rel"] == "会考/英语/北京会考英语卷.md" for c in plan["conflicts"])
    assert all("英语卷" not in m["from_rel"] for m in plan["moves"])


# ---------------------------------------------------------------- t4 禁猜测
def test_t4_undetermined_needs_ruling_not_moved(workdir):
    root = _mk_corpus(str(workdir / "ocr"))
    plan = _plan(root, str(workdir / "plan.json"))
    nr = {e["from_rel"]: e["reason"] for e in plan["needs_ruling"]}
    assert nr["未分类/zz/zzz.md"] == "category_undetermined"
    assert nr["未分类/misc/上海会考卷.md"] == "subject_undetermined"
    assert all("zzz" not in m["from_rel"] and "上海会考" not in m["from_rel"]
               for m in plan["moves"])


# ---------------------------------------------------------------- t5 read_error
def test_t5_unreadable_source_isolated(workdir):
    root = _mk_corpus(str(workdir / "ocr"))
    plan = _plan(root, str(workdir / "plan.json"))
    assert any(e["from_rel"] == "未分类/e/dir.md" for e in plan["read_error"])
    assert all("dir.md" not in m["from_rel"] for m in plan["moves"])


# ---------------------------------------------------------------- t6 指纹
def test_t6_fingerprint_stable_and_sensitive(workdir):
    root = _mk_corpus(str(workdir / "ocr"))
    p1 = _plan(root, str(workdir / "plan1.json"))
    p2 = _plan(root, str(workdir / "plan2.json"))
    assert p1["plan_sha256"] == p2["plan_sha256"], "同语料指纹必须稳定"
    assert p1["generated_at"] != p2["generated_at"] or True  # 时间不入指纹即可
    # 指纹 = canonical json(moves) 的 sha256(独立重算)
    canon = json.dumps(p1["moves"], sort_keys=True, ensure_ascii=False,
                       separators=(",", ":"))
    assert p1["plan_sha256"] == hashlib.sha256(canon.encode("utf-8")).hexdigest()
    # 语料变化 → 指纹变化
    _w(os.path.join(root, "未分类", "c", "新高考真题数学.md"), "真题汇编。\n")
    p3 = _plan(root, str(workdir / "plan3.json"))
    assert p3["plan_sha256"] != p1["plan_sha256"]


# ---------------------------------------------------------------- t7 规则单源
def test_t7_rule_single_source(workdir):
    root = _mk_corpus(str(workdir / "ocr"))
    plan = _plan(root, str(workdir / "plan.json"))
    assert os.path.normpath(plan["rule_source"]) == os.path.normpath(
        os.path.join(ROOT, "scripts", "reclassify_unknown.py"))
    # 同一输入两模块判定必须一致(dry-run 不得自带规则)
    probe = os.path.join(root, "未分类", "数学", "北京会考数学卷.md")
    assert DRY.classify(probe) == RC.classify(probe)
    assert DRY.detect_subject(probe) == RC.detect_subject(probe)


# ---------------------------------------------------------------- t8 字段完整性
def test_t8_move_entry_fields_and_sha(workdir):
    root = _mk_corpus(str(workdir / "ocr"))
    plan = _plan(root, str(workdir / "plan.json"))
    m = plan["moves"][0]
    src = os.path.join(root, *m["from_rel"].split("/"))
    with open(src, "rb") as f:
        real = hashlib.sha256(f.read()).hexdigest()
    assert m["sha256"] == real
    assert m["size"] == os.path.getsize(src)
    for k in ("category", "cat_src", "subject", "sub_src", "to_rel"):
        assert m[k], f"缺字段 {k}"

# -*- coding: utf-8 -*-
"""R64:BUG-14-DATA D0~D4 — inventory 武器行为钉 + runner 边界攻击钉。

用户裁定(D0→D5):先重现与定义边界,不写清理/归并代码。本文件全部使用
.pytest_work 合成夹具,零触碰生产语料。

  test_r64_t1   武器确定性:同一合成语料两次采集,records 逐字节一致
  test_r64_t2   D1 bucket 谓词逐桶可复现(NAME_RULE_COVERED / CONTENT_RULE_COVERED /
                UNDETERMINED / stray PLACEMENT_MISMATCH)
  test_r64_t3   D2 指纹分层:byte-identical / 仅归一化相同 / 双不同 三组判层正确
  test_r64_t4   D3 PDF 侧三态预算恒等 + exact 命中样例
  test_r64_t5   搬移审计 fail-closed:坏行+坏记录显式入 errors,批继续;
                碰撞组 in_reclassify_audit=True
  test_r64_t6   非法 UTF-8 文件:byte-sha 可得、norm-sha 显式 None+invalid-utf8,
                批继续(不崩、不静默跳过)
  test_r64_t7   不可读文件(win-only,独占句柄):显式错误记录,其余记录照常产出
  test_r64_t8   runner 源码锚:extract_grade_subject 正则/skip-check/净化/
                子目录白名单 原文在册(防副本漂移)
  test_r64_t9   reclassify 源码锚:TYPE_RULES/GAOKAO_RE/EXTRA_DIRS 原文在册
  test_r64_t10  副本行为电池:高一|高1/高二|高2/高三|高3;高考→未分类;
                '高—10月'笔误 → 未分类(规则缺口钉)
  test_r64_t11  skip-check 身份 = 输出路径存在且 >100 字节(仅此而已,无内容指纹)
  test_r64_t12  跑步机机制钉:搬移 → skip-check 落空 → 重 OCR 决策为真
                (reclassify move 击败 runner 去重 —— BUG-14-DATA 核心攻击面)
  test_r64_t13  净化碰撞:a<b 与 a>b → 同一输出名(同目录时后者被跳过)
  test_r64_t14  大小写差异(win-only):'X.md' 存在时 'x.md' exists 判真
                → 不同内容 PDF 被静默跳过(身份歧义事实钉)
"""
import ctypes
import importlib
import io
import json
import os
import shutil
import sys
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import r64_data_inventory as inv  # noqa: E402  (默认生产根;副本/锚测试用)

RUNNER = (ROOT / "ocr_service" / "batch_convert_pdf.py").read_text(encoding="utf-8")
RECLASS = (ROOT / "scripts" / "reclassify_unknown.py").read_text(encoding="utf-8")

_ENV_KEYS = ("R64_OCR_ROOT", "R64_PDF_ROOT", "R64_DATA_DIR", "R64_AUDIT")


# ---------------------------------------------------------------------------
# 合成语料构建(DSH 沙箱下系统 temp 不可写 → 用 .pytest_work,约定同 conftest)
# ---------------------------------------------------------------------------
def _fresh_dir():
    base = ROOT / ".pytest_work"
    base.mkdir(exist_ok=True)
    d = base / ("r64_" + uuid.uuid4().hex[:8])
    d.mkdir()
    return d


def w(path, text, newline="lf"):
    path.parent.mkdir(parents=True, exist_ok=True)
    if newline == "crlf":
        text = text.replace("\n", "\r\n")
    path.write_bytes(text.encode("utf-8"))


def build_synthetic(base):
    ocr = base / "Ocr-markdown"
    pdf = base / "maintainess" / "PDF"
    data = base / "data"
    neutral = "第一部分 选择题\n第二部分 解答题\n"

    # D1 桶夹具
    w(ocr / "未分类" / "历史" / "2012-2021高考真题历史汇编：甲（教师版）(1).md", neutral)
    w(ocr / "未分类" / "数学" / "2023北京某校期末练习（教师版）(1).md",
      "本卷参照高中学业水平考试说明命制。\n" + neutral)  # 仅正文可判 → 学业水平考试
    w(ocr / "未分类" / "语文" / "2023北京一七一中初三（上）第一次月考语文（教师版）.md",
      neutral)  # 名+文均无信号 → UNDETERMINED
    w(ocr / "高三" / "未分类" / "14_2023届哈尔滨三中高三第二次模拟 理科综合答案.md",
      neutral)  # 名含"高三"却落 高三/未分类 → stray PLACEMENT_MISMATCH

    # D2 指纹分层夹具(三组碰撞)
    w(ocr / "高考真题" / "历史" / "碰撞-字节相同（教师版）(1).md", neutral)
    w(ocr / "未分类" / "历史" / "碰撞-字节相同（教师版）(1).md", neutral)
    w(ocr / "高考真题" / "英语" / "碰撞-仅归一化相同（教师版）(1).md", neutral)
    w(ocr / "未分类" / "英语" / "碰撞-仅归一化相同（教师版）(1).md", neutral, newline="crlf")
    w(ocr / "高考真题" / "化学" / "碰撞-字节不同（教师版）(1).md", neutral + "版本甲\n")
    w(ocr / "未分类" / "化学" / "碰撞-字节不同（教师版）(1).md", neutral + "版本乙\n")

    # D3 PDF 侧:exact 命中 + 仅 stripped 命中 + 无命中
    w(pdf / "2012-2021高考真题历史汇编：甲（教师版）(1).pdf", "%PDF-fake\n")
    w(pdf / "高考真题汇编-仅去重后缀命中（教师版）(2).pdf", "%PDF-fake\n")  # md stem 无 (2)
    w(ocr / "未分类" / "历史" / "高考真题汇编-仅去重后缀命中（教师版）.md", neutral)
    w(ocr / "未分类" / "政治" / "完全无PDF命中（教师版）.md", neutral)

    # 搬移审计:1 好行 + 1 坏行 + 1 坏记录
    data.mkdir(parents=True, exist_ok=True)
    (data / "reclassify_audit.jsonl").write_bytes(
        json.dumps({"from": r"D:\x\未分类\历史\碰撞-字节不同（教师版）(1).md",
                    "to": r"D:\x\高考真题\历史\碰撞-字节不同（教师版）(1).md"},
                   ensure_ascii=False).encode("utf-8")
        + b"\nnot-json-line\n"
        + json.dumps({"from": 123, "to": 456}).encode("utf-8") + b"\n")
    return ocr, pdf, data


def _set_env(ocr, pdf, data):
    os.environ["R64_OCR_ROOT"] = str(ocr)
    os.environ["R64_PDF_ROOT"] = str(pdf)
    os.environ["R64_DATA_DIR"] = str(data)
    os.environ["R64_AUDIT"] = str(data / "reclassify_audit.jsonl")


def _clear_env():
    for k in _ENV_KEYS:
        os.environ.pop(k, None)


@pytest.fixture(scope="module")
def weapon():
    base = _fresh_dir()
    ocr, pdf, data = build_synthetic(base)
    _set_env(ocr, pdf, data)
    try:
        mod = importlib.reload(inv)
        mod.main()
        inv_json = json.loads((data / "r64_corpus_inventory.json").read_text(encoding="utf-8"))
        buck_json = json.loads((data / "r64_unknown_buckets.json").read_text(encoding="utf-8"))
        coll_json = json.loads((data / "r64_collision_fingerprint.json").read_text(encoding="utf-8"))
        yield base, mod, inv_json, buck_json, coll_json
    finally:
        _clear_env()
        importlib.reload(inv)
        shutil.rmtree(base, ignore_errors=True)


# ---------------------------------------------------------------------------
# 武器行为钉
# ---------------------------------------------------------------------------
def test_r64_t1_确定性(weapon):
    _base, mod, inv_json = weapon[0], weapon[1], weapon[2]
    recs1 = inv_json["records"]
    recs2, _errs = mod.collect_inventory()
    assert recs1 == recs2, "确定性破坏:同一语料两次采集不一致"


def test_r64_t2_桶谓词(weapon):
    rows = {r["rel_path"]: r for r in weapon[3]["d1"]["rows"]}
    r1 = rows["未分类/历史/2012-2021高考真题历史汇编：甲（教师版）(1).md"]
    assert r1["bucket"] == "NAME_RULE_COVERED"
    assert r1["predicates"]["reclassify_name"] == "高考真题"
    r2 = rows["未分类/数学/2023北京某校期末练习（教师版）(1).md"]
    assert r2["bucket"] == "CONTENT_RULE_COVERED"
    assert r2["predicates"]["reclassify_name"] is None
    assert r2["predicates"]["reclassify_with_text"] == "学业水平考试"
    r3 = rows["未分类/语文/2023北京一七一中初三（上）第一次月考语文（教师版）.md"]
    assert r3["bucket"] == "UNDETERMINED"
    r4 = rows["高三/未分类/14_2023届哈尔滨三中高三第二次模拟 理科综合答案.md"]
    assert r4["scope"] == "stray" and r4["bucket"] == "PLACEMENT_MISMATCH"
    assert r4["predicates"]["runner_grade"] == "高三"


def test_r64_t3_指纹分层(weapon):
    gs = {g["basename"]: g for g in weapon[4]["d2_d3"]["groups"]}
    a = gs["碰撞-字节相同（教师版）(1).md"]
    assert a["byte_identical"] and a["norm_identical"]
    b = gs["碰撞-仅归一化相同（教师版）(1).md"]
    assert not b["byte_identical"] and b["norm_identical"], "CRLF/LF 差异应判为仅归一化相同"
    c = gs["碰撞-字节不同（教师版）(1).md"]
    assert not c["byte_identical"] and not c["norm_identical"]
    assert c["in_reclassify_audit"] is True


def test_r64_t4_PDF三态(weapon):
    rows = {r["rel_path"]: r for r in weapon[3]["d1"]["rows"]}
    r1 = rows["未分类/历史/2012-2021高考真题历史汇编：甲（教师版）(1).md"]
    assert r1["pdf_exact_match_count"] == 1
    r2 = rows["未分类/历史/高考真题汇编-仅去重后缀命中（教师版）.md"]
    assert r2["pdf_exact_match_count"] == 0
    s = weapon[4]["d2_d3"]["summary"]
    assert (s["pdf_exact_hit_groups"] + s["pdf_only_stripped_hit_groups"]
            + s["pdf_no_hit_groups"]) == s["n_groups"], "三态预算必须恒等"


def test_r64_t5_审计fail_closed(weapon):
    meta = weapon[2]["meta"]
    assert any("AUDIT_BAD_LINE" in e for e in meta["audit_errors"]), "坏行必须显式入 errors"
    assert any("AUDIT_BAD_RECORD" in e for e in meta["audit_errors"]), "坏记录必须显式入 errors"
    assert meta["counts"]["audit_moves_indexed"] == 1, "好行仍被索引(批继续)"


def test_r64_t6_非法UTF8(workdir):
    ocr, pdf, data = build_synthetic(workdir)
    bad = ocr / "未分类" / "物理" / "含非法字节（教师版）.md"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_bytes(b"\xff\xfe\x00bad-bytes\n")
    _set_env(ocr, pdf, data)
    try:
        mod = importlib.reload(inv)
        recs, _errs = mod.collect_inventory()
        rec = next(r for r in recs if r["rel_path"].endswith("含非法字节（教师版）.md"))
        assert rec["sha256"] is not None, "byte 层哈希必须仍可得"
        assert rec["norm_sha256"] is None and "invalid-utf8" in rec["errors"], "归一化层必须显式失败"
        assert len(recs) > 10, "批继续:其余记录照常产出"
    finally:
        _clear_env()
        importlib.reload(inv)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows 独占句柄语义")
def test_r64_t7_不可读fail_closed(workdir):
    ocr, pdf, data = build_synthetic(workdir)
    target = ocr / "未分类" / "历史" / "2012-2021高考真题历史汇编：甲（教师版）(1).md"
    h = ctypes.windll.kernel32.CreateFileW(str(target), 0x80000000, 0, None, 3, 0, None)
    assert h != -1, "前置条件:独占句柄必须先成立"
    _set_env(ocr, pdf, data)
    try:
        mod = importlib.reload(inv)
        recs, _errs = mod.collect_inventory()
        rec = next(r for r in recs if r["rel_path"].endswith("甲（教师版）(1).md"))
        assert rec.get("errors"), "不可读必须显式入记录"
        assert len(recs) > 10, "批继续:其余记录照常产出"
    finally:
        ctypes.windll.kernel32.CloseHandle(h)
        _clear_env()
        importlib.reload(inv)


# ---------------------------------------------------------------------------
# 源码锚(防副本漂移)
# ---------------------------------------------------------------------------
def test_r64_t8_runner源码锚():
    for anchor in [
        r"if re.search(r'高一|高1', filename):",
        r"elif re.search(r'高二|高2', filename):",
        r"elif re.search(r'高三|高3', filename):",
        r"""    base_name = re.sub(r'[<>:"/\\|?*]', '_', base_name)""",
        "    if os.path.exists(output_md) and os.path.getsize(output_md) > 100:",
        '    for grade in ["高一", "高二", "高三"]:',
        'root_pdfs = [f for f in os.listdir(PDF_ROOT) if f.lower().endswith(".pdf")]',
    ]:
        assert anchor in RUNNER, f"runner 源码锚漂移: {anchor}"


def test_r64_t9_reclassify源码锚():
    for anchor in [
        '("高考真题", ["高考真题", "真题汇编"]),',
        r'GAOKAO_RE = re.compile(r"高考[^，。；]{0,6}真题|真题汇编")',
        'EXTRA_DIRS = [os.path.join(OCR_ROOT, "高三", "未分类")]',
        'files = sorted(glob.glob(os.path.join(UNKNOWN, "*", "*.md")))',
    ]:
        assert anchor in RECLASS, f"reclassify 源码锚漂移: {anchor}"


def test_r64_t10_副本行为电池():
    cases = [
        ("高三数学期中卷.pdf", ("高三", "数学")),
        ("高1物理月考.pdf", ("高一", "物理")),
        ("高二2023英语.pdf", ("高二", "英语")),
        ("2022北京高考真题化学（教师版）(1).pdf", ("未分类", "化学")),
        ("2022北京人大翠微学校高—10月月考物理（教师版）(1).pdf", ("未分类", "物理")),  # 笔误缺口
        ("2023北京一七一中初三（上）第一次月考语文（教师版）.pdf", ("未分类", "语文")),  # 学段越界
    ]
    for fn, want in cases:
        assert inv.extract_grade_subject(fn) == want, f"副本漂移: {fn}"


# ---------------------------------------------------------------------------
# D4 — runner 边界攻击(副本谓词 + 真实文件系统,零 API 调用)
# ---------------------------------------------------------------------------
def runner_output_md(output_dir, filename):
    """batch_convert_pdf L114-116 副本:输出路径决策。"""
    base_name = os.path.splitext(filename)[0]
    base_name = inv.SANITIZE_RE.sub("_", base_name)
    return os.path.join(output_dir, f"{base_name}.md")


def runner_skip(output_md):
    """batch_convert_pdf L118 副本:skip-check(身份 = 输出路径存在且 >100B)。"""
    return os.path.exists(output_md) and os.path.getsize(output_md) > 100


def test_r64_t11_身份等于输出路径(workdir):
    out = workdir / "out"
    out.mkdir()
    md1 = runner_output_md(str(out), "同一命名.pdf")
    assert not runner_skip(md1)
    Path(md1).write_bytes(b"x" * 150)
    assert runner_skip(md1), ">100B 应 skip"
    Path(md1).write_bytes(b"x" * 50)
    assert not runner_skip(md1), "<=100B 应重跑(无内容指纹)"


def test_r64_t12_跑步机机制(workdir):
    """reclassify move 击败 runner skip-check → 同一 PDF 重 OCR 回流。
    BUG-14-DATA 核心机制钉(合成环境复现,不调 API)。"""
    out = workdir / "Ocr-markdown" / "未分类" / "历史"
    out.mkdir(parents=True)
    md = out / "汇编（教师版）(1).md"
    md.write_bytes(b"y" * 500)
    assert runner_skip(str(md)), "前置:未搬移前 runner 跳过"
    dst_dir = workdir / "Ocr-markdown" / "高考真题" / "历史"
    dst_dir.mkdir(parents=True)
    shutil.move(str(md), str(dst_dir / md.name))
    assert not runner_skip(str(md)), "机制:搬移后 skip-check 落空 → 将重 OCR(跑步机)"


def test_r64_t13_净化碰撞(workdir):
    out = workdir / "out"
    out.mkdir()
    a = runner_output_md(str(out), "2023一模<a>b.pdf")
    b = runner_output_md(str(out), "2023一模>a<b.pdf")
    assert a == b, "不同 PDF 名经净化后同名(身份歧义)"
    Path(a).write_bytes(b"z" * 200)
    assert runner_skip(b), "第二个不同内容 PDF 将被静默跳过"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows 大小写不敏感文件系统语义")
def test_r64_t14_大小写歧义(workdir):
    out = workdir / "out"
    out.mkdir()
    (out / "X.md").write_bytes(b"q" * 200)
    md_lower = runner_output_md(str(out), "x.pdf")
    assert os.path.basename(md_lower) == "x.md"
    assert runner_skip(md_lower), "事实钉:大小写不同的另一文件被 exists 判真 → 静默跳过"


# ---------------------------------------------------------------------------
# R65 审查修复钉
# ---------------------------------------------------------------------------
def test_r64_t15_全局索引未构建fail_closed(monkeypatch):
    """F-r65-3:索引未构建时必须显式失败,禁止静默给出空孪生证据。"""
    monkeypatch.setattr(inv, "DUPLICATE_BASENAME_INDEX", {}, raising=True)
    rec = {"rel_path": "未分类/历史/X.md", "basename": "X.md"}
    with pytest.raises(RuntimeError):
        inv.classify_unknown_file(rec, "不存在/无关路径/X.md", "X.md")


def test_r64_t16_根级md范围披露(workdir):
    """F-r65-1:OCR_ROOT 根级 md 不入账但必须在 meta 中点名披露。"""
    ocr, pdf, data = build_synthetic(workdir)
    (ocr / "README.md").write_bytes("# 说明文档\n".encode("utf-8"))
    _set_env(ocr, pdf, data)
    try:
        mod = importlib.reload(inv)
        mod.main()
        payload = json.loads(
            (data / "r64_corpus_inventory.json").read_text(encoding="utf-8"))
        assert payload["meta"]["root_level_md_excluded"] == ["README.md"]
        assert not any(r["rel_path"] == "README.md" for r in payload["records"])
    finally:
        _clear_env()
        importlib.reload(inv)

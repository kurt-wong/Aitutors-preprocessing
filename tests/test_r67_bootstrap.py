# -*- coding: utf-8 -*-
"""R67:manifest 引导工具钉(用户 2026-09-13 五项裁决冻结)。

覆盖:默认 dry-run / apply 合法载入 / **禁覆盖已有条目** / 幂等 /
审计歧义 fail-closed / to 缺失排除 / 既有清单损坏中止 /
pages null+provenance schema / decide_skip 集成 / 日志考古 A·B 分桶 /
日志名截断规则(F-r65-2)/ fragment 歧义降级 / 真实语料冒烟(corpus 门控)。
"""
import importlib.util
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    "r67_manifest_bootstrap", os.path.join(ROOT, "scripts", "r67_manifest_bootstrap.py"))
BOOT = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(BOOT)

sys.path.insert(0, os.path.join(ROOT, "ocr_service"))
from output_manifest import ManifestError, decide_skip, load_manifest  # noqa: E402

HAS_CORPUS = (os.path.isdir(r"D:\Project\Papers\maintainess\PDF")
              and os.path.exists(r"D:\Project\Papers\data\reclassify_audit.jsonl"))


@pytest.fixture()
def work():
    """工作区内临时目录(系统 Temp 在沙箱/CI 上不可靠,统一走 .pytest_work)。"""
    import shutil
    import uuid
    from pathlib import Path
    d = Path(ROOT) / ".pytest_work" / "r67_t" / uuid.uuid4().hex
    d.mkdir(parents=True, exist_ok=True)
    yield d
    shutil.rmtree(d, ignore_errors=True)


def _mk_pdf(root, rel, content=b"%PDF-fake-"):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
        f.write(content)
    return p


def _mk_audit(path, records):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _mk_log(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _env(work, pdfs, audit_recs, log_lines, existing_manifest=None):
    base = str(work)
    pdf_root = os.path.join(base, "pdf")
    out_root = os.path.join(base, "out")
    os.makedirs(out_root, exist_ok=True)
    for rel, content in pdfs:
        _mk_pdf(pdf_root, rel, content)
    audit = os.path.join(base, "audit.jsonl")
    _mk_audit(audit, audit_recs)
    log = os.path.join(base, "ocr.log")
    _mk_log(log, log_lines)
    manifest = os.path.join(base, "manifest.jsonl")
    if existing_manifest is not None:
        with open(manifest, "w", encoding="utf-8") as f:
            f.write(existing_manifest)
    report = os.path.join(base, "report.json")
    return dict(pdf_root=pdf_root, output_root=out_root, audit_file=audit,
                log_file=log, manifest_file=manifest, report_file=report)


PDF_NAME = "2022北京西城高二（下）期末地理参考答案(1).pdf"


def _std_env(work):
    """标准夹具:1 PDF + 1 审计记录(from=期望输出,to=已搬移在位)+ 空日志。"""
    return _env(
        work,
        pdfs=[(PDF_NAME, b"%PDF-A" * 40)],
        audit_recs=[{
            "from": os.path.join(str(work), "out", "高二", "地理",
                                 "2022北京西城高二（下）期末地理参考答案(1).md"),
            "to": os.path.join(str(work), "out", "高考真题", "地理",
                               "2022北京西城高二（下）期末地理参考答案(1).md")}],
        log_lines=["[2026-09-08 10:00:00] [1/1] 高二/地理/" + PDF_NAME[:50] + "...",
                   "[2026-09-08 10:00:05]   [OK] 7 pages"])


def _pv_env(env):
    """make_preview 用 kwargs(env + preview_file)。"""
    return dict(env, preview_file=os.path.join(
        os.path.dirname(env["manifest_file"]), "preview.json"))


def _apply(env, written_at):
    """apply 前置流程(用户裁决 §四-B):先生成 preview,再走 hash guard 落盘。"""
    env = dict(env)
    env.setdefault("preview_file",
                   os.path.join(os.path.dirname(env["manifest_file"]), "preview.json"))
    BOOT.make_preview(written_at=written_at, **env)
    return BOOT.run(apply=True, **env)


def _mk_to(env, rel="高考真题/地理/2022北京西城高二（下）期末地理参考答案(1).md",
           content=b"x" * 200):
    p = os.path.join(env["output_root"], *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
        f.write(content)
    return p


# ---------------------------------------------------------------- t1 dry-run
def test_r67_t1_dry_run_zero_write(work):
    env = _std_env(work)
    _mk_to(env)
    rep = BOOT.run(apply=False, written_at="2026-09-13 00:00:00", **env)
    assert rep["applied"] is False and "appended" not in rep
    assert not os.path.exists(env["manifest_file"]), "dry-run 绝不创建清单"
    assert rep["planned_entries"] == 1
    assert os.path.exists(env["report_file"])


# ---------------------------------------------------------------- t2 apply
def test_r67_t2_apply_entries_valid_and_loadable(work):
    env = _std_env(work)
    _mk_to(env)
    _apply(env, "2026-09-13 00:00:00")
    man = load_manifest(env["manifest_file"])
    assert len(man) == 1
    e = list(man.values())[0]
    assert e["provenance"] == "r63-audit-bootstrap"
    assert e["pages"] == 7 and e["processed_at"] is None  # 日志证明的真实页数
    assert e["audit_line"] == 1 and e["log_ok_lines"] == [2]
    assert e["source_sha256"] and e["written_at"] == "2026-09-13 00:00:00"


# ------------------------------------------------------- t3 禁覆盖已有条目
def test_r67_t3_never_overwrites_existing_entry(work):
    env = _std_env(work)
    _mk_to(env)
    _apply(env, "2026-09-13 00:00:00")
    before = open(env["manifest_file"], "rb").read()
    # 再次 preview + apply:已有条目必须原样保留(禁覆盖),不得追加重复
    rep = _apply(env, "2026-09-13 01:00:00")
    after = open(env["manifest_file"], "rb").read()
    assert before == after, "bootstrap 禁止覆盖/重复追加已有条目"
    assert rep["appended"] == 0
    assert rep["skipped_already_present"] == [
        {"source_rel": PDF_NAME, "reason": "ALREADY_IN_MANIFEST"}]


# ---------------------------------------------------------------- t4 幂等
def test_r67_t4_idempotent_second_apply_appends_zero(work):
    env = _std_env(work)
    _mk_to(env)
    r1 = _apply(env, "2026-09-13 00:00:00")
    r2 = _apply(env, "2026-09-13 00:00:01")
    assert r1["appended"] == 1 and r2["appended"] == 0
    assert len(load_manifest(env["manifest_file"])) == 1


# -------------------------------------------------- t5 审计歧义 fail-closed
def test_r67_t5_ambiguous_expected_output_excluded(work, monkeypatch):
    # 真实 Windows 文件名造不出净化碰撞(< > : 等均为非法字符),
    # 故用 monkeypatch 合成"两 PDF 声明同一期望输出"的防御分支(R64 t-系列同款手法)。
    env = _env(
        work,
        pdfs=[("甲.pdf", b"1" * 50), ("乙.pdf", b"2" * 50)],
        audit_recs=[{
            "from": os.path.join(str(work), "out", "未分类", "未分类", "甲.md"),
            "to": os.path.join(str(work), "out", "高一", "数学", "甲.md")}],
        log_lines=[])
    _mk_to(env, rel="高一/数学/甲.md")
    real_enum = BOOT.enumerate_pdfs

    def fake_enum(pdf_root):
        recs = real_enum(pdf_root)
        # 把两条记录都声明为未分类/未分类/甲.pdf → 同一期望输出被两个 source 共享
        p1 = os.path.join(pdf_root, "甲.pdf")
        p2 = os.path.join(pdf_root, "乙.pdf")
        return [(p1, "未分类", "未分类", "甲.pdf"),
                (p2, "未分类", "未分类", "甲.pdf")]

    monkeypatch.setattr(BOOT, "enumerate_pdfs", fake_enum)
    rep = BOOT.run(apply=False, written_at="2026-09-13 00:00:00", **env)
    assert rep["planned_entries"] == 0
    assert rep["excluded"][0]["reason"] == "AUDIT_FROM_AMBIGUOUS"
    assert rep["excluded"][0]["owner_count"] == 2


# ------------------------------------------------------ t6 to 缺失 → 排除
def test_r67_t6_to_missing_excluded(work):
    env = _std_env(work)  # 不创建 to
    rep = BOOT.run(apply=False, written_at="2026-09-13 00:00:00", **env)
    assert rep["planned_entries"] == 0
    assert rep["excluded"][0]["reason"] == "AUDIT_TO_MISSING"


# ------------------------------------------------ t7 既有清单损坏 → 中止
def test_r67_t7_corrupt_existing_manifest_aborts(work):
    env = _std_env(work)
    _mk_to(env)
    with open(env["manifest_file"], "w", encoding="utf-8") as f:
        f.write("{bad json\n")
    with pytest.raises(ManifestError):
        BOOT.run(apply=False, written_at="2026-09-13 00:00:00", **env)


# -------------------------------------------- t8 pages null schema(裁决①)
def test_r67_t8_pages_null_requires_provenance():
    base = {"source_rel": "a.pdf", "source_size": 1, "source_sha256": "x",
            "output_rel": "a.md", "written_at": "2026-09-13 00:00:00",
            "pages": None, "provenance": "r63-audit-bootstrap"}
    BOOT.validate_entry(dict(base))  # null + provenance → 合法
    bad = dict(base); bad.pop("provenance")
    with pytest.raises(ManifestError):
        BOOT.validate_entry(bad)  # null 无 provenance → 拒绝
    with pytest.raises(ManifestError):
        BOOT.validate_entry(dict(base, pages="3"))
    with pytest.raises(ManifestError):
        BOOT.validate_entry(dict(base, pages=True))


# ------------------------------- t9 集成:bootstrap 条目 → MANIFEST_DONE
def test_r67_t9_decide_skip_with_bootstrap_entry(work):
    # 日志可证的受害者(A 类)→ 入账;随后期望输出落空态跑真实 decide_skip
    env = _env(
        work,
        pdfs=[(PDF_NAME, b"%PDF-B" * 40)],
        audit_recs=[],
        log_lines=["[2026-09-08 10:00:00] [1/1] 高二/地理/" + PDF_NAME[:50] + "...",
                   "[2026-09-08 10:00:05]   [OK] 5 pages"])
    _mk_to(env, rel="高考真题/地理/2022北京西城高二（下）期末地理参考答案(1).md")
    rep = _apply(env, "2026-09-13 00:00:00")
    assert rep["appended"] == 1
    e = list(load_manifest(env["manifest_file"]).values())[0]
    assert e["provenance"] == "ocr-log-archaeology" and e["pages"] == 5
    # 真实 decide_skip:期望输出不在位(跑步机场景)→ MANIFEST_DONE 零 OCR
    out_md = os.path.join(env["output_root"], "高二", "地理",
                          "2022北京西城高二（下）期末地理参考答案(1).md")
    skip, reason, detail = decide_skip(
        output_md=out_md, source_pdf=os.path.join(env["pdf_root"], PDF_NAME),
        pdf_root=env["pdf_root"], output_root=env["output_root"],
        manifest=load_manifest(env["manifest_file"]))
    assert (skip, reason) == (True, "MANIFEST_DONE")
    # 审计条目(to 在位)集成:记录输出状态 present
    env2 = _std_env(work / "s2")
    _mk_to(env2)
    _apply(env2, "2026-09-13 00:00:00")
    out_md2 = os.path.join(env2["output_root"], "高二", "地理",
                           "2022北京西城高二（下）期末地理参考答案(1).md")
    skip2, reason2, detail2 = decide_skip(
        output_md=out_md2, source_pdf=os.path.join(env2["pdf_root"], PDF_NAME),
        pdf_root=env2["pdf_root"], output_root=env2["output_root"],
        manifest=load_manifest(env2["manifest_file"]))
    assert (skip2, reason2) == (True, "MANIFEST_DONE")
    assert detail2["recorded_output_status"] == "present"


# ------------------------------------- t10 日志考古 A 类(无审计也可证)
def test_r67_t10_log_archaeology_seeds_victim(work):
    long_name = "2012-2021高考真题历史汇编：法律与教化（三）（教师版）(1).pdf"
    env = _env(
        work,
        pdfs=[(long_name, b"%PDF-C" * 40)],
        audit_recs=[],
        log_lines=["[2026-09-08 10:00:00] [5/12703] 未分类/历史/" + long_name[:50] + "...",
                   "[2026-09-08 10:00:06]   [OK] 34 pages"])
    _mk_to(env, rel="高考真题/历史/" + long_name[:-4] + ".md")  # 同名 md 在别处 = 受害者
    rep = _apply(env, "2026-09-13 00:00:00")
    assert rep["appended"] == 1
    e = list(load_manifest(env["manifest_file"]).values())[0]
    assert e["provenance"] == "ocr-log-archaeology"
    assert e["pages"] == 34 and e["log_ok_lines"] == [2]
    assert rep["buckets"]["A_seeded"][0]["audit_line"] is None


# ---------------------- t11 B 类:有名行无 OK / fragment 歧义 → 不入账
def test_r67_t11_weak_evidence_goes_pending_not_manifest(work):
    base = "2021北京海淀高三一模数学汇编专题训练" + "压轴" * 20  # >50 字符
    n1 = base + "(1).pdf"
    n2 = base + "(1)(1).pdf"  # 与 n1 前 50 字符相同(截断后同 fragment)
    env = _env(
        work,
        pdfs=[(n1, b"1" * 60), (n2, b"2" * 60)],
        audit_recs=[],
        log_lines=["[2026-09-08 10:00:00] [1/2] 高三/数学/" + n1[:50] + "...",
                   "[2026-09-08 10:00:05] [ERROR] submit failed"])
    _mk_to(env, rel="高考真题/数学/" + n1[:-4] + ".md")
    _mk_to(env, rel="高考真题/数学/" + n2[:-4] + ".md")
    rep = _apply(env, "2026-09-13 00:00:00")
    assert rep["appended"] == 0, "弱证据绝不入账"
    reasons = {b["reason"] for b in rep["buckets"]["B_pending_review"]}
    assert "LOG_FRAGMENT_AMBIGUOUS" in reasons  # n1/n2 截断后同 fragment


# ---------------------- t12 截断规则钉(F-r65-2:按 [:50] 构造期望串)
def test_r67_t12_truncation_rule_pin(work):
    long_name = "x" * 60 + ".pdf"
    env = _env(
        work,
        pdfs=[(long_name, b"3" * 60)],
        audit_recs=[],
        log_lines=["[2026-09-08 10:00:00] [9/9] 未分类/未分类/" + long_name[:50] + "...",
                   "[2026-09-08 10:00:02]   [OK] 3 pages"])
    _mk_to(env, rel="其他/" + long_name[:-4] + ".md")
    rep = _apply(env, "2026-09-13 00:00:00")
    assert rep["appended"] == 1, "必须按 filename[:50] 截断规则匹配日志"


# ============ preview + hash guard(用户裁决 §四-B)============

def test_r67_t14_preview_frozen_fingerprints(work):
    env = _std_env(work)
    _mk_to(env)
    pv1 = BOOT.make_preview(written_at="2026-09-13 00:00:00", **_pv_env(env))
    pv2 = BOOT.make_preview(written_at="2026-09-13 00:00:00", **_pv_env(env))
    assert pv1 == pv2, "同 written_at 的 preview 必须确定性一致"
    assert pv1["base_manifest_sha256"] is None  # manifest 不存在 = None,区别于空文件
    assert pv1["append_count"] == 1 and len(pv1["entries_sha256"]) == 64
    with open(_pv_env(env)["preview_file"], encoding="utf-8") as f:
        assert json.load(f) == pv1


def test_r67_t15_apply_refused_on_base_drift(work):
    env = _std_env(work)
    _mk_to(env)
    BOOT.make_preview(written_at="2026-09-13 00:00:00", **_pv_env(env))
    # dry-run 之后 manifest 被改动(模拟并发写入)
    with open(env["manifest_file"], "w", encoding="utf-8") as f:
        f.write('{"tampered": true}\n')
    before = open(env["manifest_file"], "rb").read()
    with pytest.raises(BOOT.BootstrapError, match="manifest 已漂移"):
        BOOT.run(apply=True, **_pv_env(env))
    assert open(env["manifest_file"], "rb").read() == before, "拒绝后零写入"


def test_r67_t16_apply_refused_on_plan_drift(work):
    env = _std_env(work)
    to = _mk_to(env)
    BOOT.make_preview(written_at="2026-09-13 00:00:00", **_pv_env(env))
    os.remove(to)  # 语料变动:审计 to 消失 → 规划漂移
    with pytest.raises(BOOT.BootstrapError, match="规划已漂移"):
        BOOT.run(apply=True, **_pv_env(env))
    assert not os.path.exists(env["manifest_file"]), "拒绝后零写入"


def test_r67_t17_apply_without_preview_refused(work):
    env = _std_env(work)
    _mk_to(env)
    with pytest.raises(BOOT.BootstrapError, match="preview 不存在"):
        BOOT.run(apply=True, **_pv_env(env))
    assert not os.path.exists(env["manifest_file"])


# ============ 双向一致性闸门(用户裁决 §四-A)============

def test_r67_t18_gate_catches_wrong_bootstrap_output(work, monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "r67_apply_gate", os.path.join(ROOT, "scripts", "r67_apply_gate.py"))
    GATE = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(GATE)
    env = _std_env(work)
    _mk_to(env)
    # 正常规划 → 闸门一致
    rep = GATE.run_gate(**dict(env, report_file=os.path.join(str(work), "gate1.json")))
    assert rep["consistent"] is True and rep["audit_rows"] == 1
    # 破坏 bootstrap 输出(sha 计算错误)→ 闸门独立重推必须咬住
    # (闸门内部 import 的 BOOT 是独立实例,必须 patch GATE.BOOT)
    monkeypatch.setattr(GATE.BOOT, "file_sha256", lambda p: "deadbeef")
    rep2 = GATE.run_gate(**dict(env, report_file=os.path.join(str(work), "gate2.json")))
    assert rep2["consistent"] is False
    assert any(m["kind"] == "SHA256" for m in rep2["backward_mismatches"])


def test_r67_t19_gate_catches_forward_missing(work, monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "r67_apply_gate", os.path.join(ROOT, "scripts", "r67_apply_gate.py"))
    GATE = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(GATE)
    env = _std_env(work)
    _mk_to(env)
    # bootstrap 侧枚举丢失该 PDF → 审计行无对应条目 → forward 缺口必须被咬
    monkeypatch.setattr(GATE.BOOT, "enumerate_pdfs", lambda root: [])
    rep = GATE.run_gate(**dict(env, report_file=os.path.join(str(work), "gate3.json")))
    assert rep["consistent"] is False
    assert rep["forward_missing"] == [1]
@pytest.mark.skipif(not HAS_CORPUS, reason="corpus 不在(CI 离线)")
def test_r67_t13_real_corpus_smoke(work):
    rep = BOOT.run(
        apply=False, written_at="2026-09-13 00:00:00",
        pdf_root=r"D:\Project\Papers\maintainess\PDF",
        output_root=r"D:\Project\Papers\Ocr-markdown",
        audit_file=r"D:\Project\Papers\data\reclassify_audit.jsonl",
        log_file=r"D:\Project\Papers\logs\ocr_batch_log.txt",
        manifest_file=os.path.join(str(work), "m.jsonl"),
        report_file=os.path.join(str(work), "r.json"))
    # R67 设计探针复证:审计 698/698 全匹配,零排除
    assert len(rep["excluded"]) == 0, rep["excluded"][:3]
    for e in rep["entries"]:
        BOOT.validate_entry(e)
    provs = {e["provenance"] for e in rep["entries"]}
    assert provs <= {"r63-audit-bootstrap", "ocr-log-archaeology"}
    print(f"\n[R67 smoke] planned={rep['planned_entries']} "
          f"A={len(rep['buckets']['A_seeded'])} "
          f"B_pending={len(rep['buckets']['B_pending_review'])} "
          f"victims={rep['victim_candidates']} "
          f"already={len(rep['skipped_already_present'])}")


# ---------------- t20 manifest 模式(R67.1 Gate B:审落盘本体,非规划)
def _load_gate():
    spec = importlib.util.spec_from_file_location(
        "r67_apply_gate", os.path.join(ROOT, "scripts", "r67_apply_gate.py"))
    GATE = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(GATE)
    return GATE


def _load_manifest(mf):
    return [json.loads(l) for l in open(mf, encoding="utf-8") if l.strip()]


def _write_manifest(mf, rows):
    with open(mf, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def test_r67_t20_gate_manifest_mode_reads_landed_entries(work):
    GATE = _load_gate()
    env = _std_env(work)
    _mk_to(env)
    _apply(env, "2026-09-13 21:40:50")
    mf = env["manifest_file"]

    def _gate(tag):
        return GATE.run_gate(source="manifest", **dict(
            env, report_file=os.path.join(str(work), f"g_{tag}.json")))

    # 落盘后 plan 因 no-overwrite 全空;manifest 模式必须审到落盘条目本体
    rep = _gate("clean")
    assert rep["source"] == "manifest"
    assert rep["consistent"] is True and rep["audit_entries"] == 1
    # 篡改落盘条目的 source_sha256 → 独立重推必须咬住
    orig = _load_manifest(mf)
    rows = [dict(r) for r in orig]
    rows[0]["source_sha256"] = "deadbeef"
    _write_manifest(mf, rows)
    rep2 = _gate("sha")
    assert rep2["consistent"] is False
    assert any(m["kind"] == "SHA256" for m in rep2["backward_mismatches"])
    # 仅篡改 pages(sha 恢复正确)→ PAGES 独立日志重推必须咬住
    rows = [dict(r) for r in orig]
    rows[0]["pages"] = rows[0]["pages"] + 1
    _write_manifest(mf, rows)
    rep3 = _gate("pages")
    assert rep3["consistent"] is False
    assert any(m["kind"] == "PAGES" for m in rep3["backward_mismatches"])


def test_r67_t21_verify_gate_a_catches_tamper(work):
    """Gate A 十项检查逐项可咬:每场景独立 fresh apply + 单点篡改。"""
    spec = importlib.util.spec_from_file_location(
        "r67_apply_verify", os.path.join(ROOT, "scripts", "r67_apply_verify.py"))
    VER = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(VER)

    def _t_processed_at(rows):
        rows[0]["processed_at"] = "2020-01-01 00:00:00"

    def _t_drop_row(rows):
        del rows[-1]

    def _t_duplicate(rows):
        rows.append(dict(rows[0]))

    def _t_provenance(rows):
        rows[0]["provenance"] = "looks-processed"

    def _t_pages(rows):
        rows[0]["pages"] = rows[0]["pages"] + 1  # 仅指纹可侦测的单点漂移

    def _t_pdf_sha(rows):
        rows[0]["source_sha256"] = "deadbeef"

    def _t_output_missing(rows, env):
        os.remove(os.path.join(env["output_root"], rows[0]["output_rel"]))

    cases = [
        ("processed_at_all_null", _t_processed_at),
        ("append_count", _t_drop_row),
        ("duplicate_zero", _t_duplicate),
        ("provenance_uniform", _t_provenance),
        ("entries_sha256", _t_pages),
        ("pdf_rehash", _t_pdf_sha),
        ("output_rehash", _t_output_missing),
    ]
    import uuid
    for i, (expect_check, tamp) in enumerate(cases):
        sub = os.path.join(str(work), f"case{i}")
        os.makedirs(sub, exist_ok=True)
        env = _std_env(sub)
        _mk_to(env)
        pv = _pv_env(env)
        _apply(env, "2026-09-13 21:40:50")
        kw = dict(pdf_root=env["pdf_root"], output_root=env["output_root"],
                  audit_file=env["audit_file"], manifest_file=env["manifest_file"],
                  preview_file=pv["preview_file"])
        clean = VER.run_verify(**dict(kw, report_file=os.path.join(sub, "v0.json")))
        assert clean["consistent"] is True, (expect_check, clean["checks"])
        rows = _load_manifest(env["manifest_file"])
        tamp(rows, env) if tamp is _t_output_missing else tamp(rows)
        _write_manifest(env["manifest_file"], rows)
        dirty = VER.run_verify(**dict(kw, report_file=os.path.join(sub, "v1.json")))
        assert dirty["consistent"] is False, expect_check
        assert dirty["checks"][expect_check]["ok"] is False, (
            expect_check, dirty["checks"])

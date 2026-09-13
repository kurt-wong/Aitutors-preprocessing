r"""R53 Resolver Consumer Adversarial Audit (b):变异攻击(灵敏度 + 真实语料形态)。

A. resolver 代码变异(备份-注入-跑 CI 测试-还原,sha 核验闭环):
   M1 PENDING_REVIEW 悄悄转 ADMITTED(违反 C-FAIL-2)→ t4 必须红
   M2 IR 身份重塑(printed := canonical)→ t1 必须红
   M3 撤销 v1 拒收 → t2 必须红
   M4 unresolved 答案表猜值 → t7 必须红
   M5 丢 provenance source_version → t1 必须红
   M6 硬编码写 data/(违反 C-OUT-1)→ data/ 目录 Gate 必须咬住
     (t10 只断言 --out 内容,捕捉不到越界写——Gate 补位,如实记录)

B. 真实语料 staged 变异(整组拷贝,原件零触碰 + Gate;控制组必须复现
   原件 disposition,拷贝保真检查):
   C1 剥 v2 身份 → REJECTED_V1(R-ACC-1)
   C2 注入 C3 缺答案 → REJECTED_QC_FAIL(R-ACC-2)
   C3 剥 section_ref → PENDING_REVIEW → ADMITTED_PENDING_REVIEW(C-FAIL-2)
   C4 删源文件 → MISSING(R-ACC-11)
   C5 截断源 → REJECTED_STALE(R-ACC-11)
   C6 跨节非 keep 重号 → REJECTED_QC_FAIL 且 manifest basis 不动(R-ACC-9)
   C7 只改 section 标题(spans 不动)→ IR 内容切片与控制组全等
     (R-ACC-10:行号锚定,定位与标题无关)

语料依赖(本地跑)。输出: data/r53_resolver_mutation.json
用法: python scripts/r53_resolver_mutation.py
"""
import hashlib
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".pytest_work"
OUT = ROOT / "data/r53_resolver_mutation.json"
RR = ROOT / "scripts/resolver_reference.py"
PREFLIGHT = ROOT / "data/resolver_contract_preflight.json"

MUTATIONS = {
    "M1_pending转admitted": (
        'rec["disposition"] = ("ADMITTED" if verdict == "PASS"\n'
        '                          else "ADMITTED_PENDING_REVIEW")',
        'rec["disposition"] = "ADMITTED"'),
    "M2_basis重解释": (
        '"basis": u.get("basis"),',
        '"basis": "keep",'),
    "M3撤销v1拒收": (
        'if (man.get("identity_version") or 1) < 2:',
        'if False:'),
    "M4猜unresolved": (
        '            else:\n'
        '                unresolved.append(q)',
        '            else:\n'
        '                answers[str(q)] = cells[0] if cells else None\n'
        '                unresolved.append(q)'),
    "M5丢source_version": (
        '"source_version": _sha256(src),',
        '"source_version": None,'),
    "M6硬编码写data": (
        '    out_dir.mkdir(parents=True, exist_ok=True)',
        '    out_dir.mkdir(parents=True, exist_ok=True)\n'
        '    (ROOT / "data/resolver_hardcoded_probe.json").write_text(\n'
        '        "{}", encoding="utf-8")'),
}
EXPECT = {"M1_pending转admitted": "test_t4", "M2_basis重解释": "test_t1",
          "M3撤销v1拒收": "test_t2", "M4猜unresolved": "test_t7",
          "M5丢source_version": "test_t1", "M6硬编码写data": None}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run_ci_tests():
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_resolver_reference.py",
         "-q"], capture_output=True, encoding="utf-8", errors="replace",
        cwd=str(ROOT))
    return r.returncode, r.stdout + r.stderr


def data_snapshot():
    return {str(p.relative_to(ROOT)): sha(p)
            for p in sorted((ROOT / "data").rglob("*.json"))}


def main():
    results = []
    backup = RR.read_bytes()
    backup_sha = hashlib.sha256(backup).hexdigest()

    # ---------- A. 代码变异 ----------
    try:
        for tag, (old, new) in MUTATIONS.items():
            src = backup.decode("utf-8")
            assert old in src, f"{tag} 锚点失配"
            RR.write_text(src.replace(old, new, 1), encoding="utf-8",
                          newline="")
            if tag == "M6硬编码写data":
                before = data_snapshot()
                subprocess.run(
                    [sys.executable, str(RR), "--preflight",
                     str(PREFLIGHT.relative_to(ROOT)),
                     "--out", str(WORK / "r53_m6_out")],
                    capture_output=True, cwd=str(ROOT))
                after = data_snapshot()
                hit = set(after) - set(before)
                results.append({"m": tag, "gate_hit": bool(hit),
                                "new_files": sorted(hit)[:3],
                                "ok": bool(hit)})
                (ROOT / "data/resolver_hardcoded_probe.json").unlink(
                    missing_ok=True)
            else:
                code, out = run_ci_tests()
                failed_marker = EXPECT[tag] in out and code != 0
                results.append({"m": tag, "exit": code,
                                "expected_test": EXPECT[tag],
                                "caught": failed_marker, "ok": failed_marker})
            RR.write_bytes(backup)
    finally:
        RR.write_bytes(backup)
    assert sha(RR) == backup_sha, "resolver 模块还原失败!"
    code, _ = run_ci_tests()
    results.append({"m": "restore_clean", "exit": code, "ok": code == 0})

    # ---------- B. 真实语料 staged 变异 ----------
    pf = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    row = next(r for r in pf["rows"]
               if r["corpus"] == "ocr" and not r["findings"]
               and r.get("qc_verdict") == "PASS")
    md_rel = row["file"]
    src_md = ROOT / md_rel
    man_path = src_md.with_suffix(".manifest.json")
    orig_src = Path(json.loads(man_path.read_text(
        encoding="utf-8"))["source_file"])
    originals = [p for p in (src_md, man_path, orig_src,
                             src_md.with_suffix(".annotated.md"))
                 if p.exists()]
    sys.path.insert(0, str(ROOT / "scripts"))
    import audit_integrity as ai
    import resolver_reference as rr
    gate_before = ai.gate_snapshot(originals)

    def stage():
        d = WORK / f"r53_stg_{uuid.uuid4().hex[:8]}"
        d.mkdir(parents=True)
        md_c = d / src_md.name
        shutil.copy2(src_md, md_c)
        ann = src_md.with_suffix(".annotated.md")
        if ann.exists():
            shutil.copy2(ann, d / ann.name)
        src_c = d / f"src_{orig_src.name}"  # R49 教训:同名自我覆盖防御
        shutil.copy2(orig_src, src_c)
        man = json.loads(man_path.read_text(encoding="utf-8"))
        man["source_file"] = str(src_c)
        man_c = d / man_path.name
        man_c.write_text(json.dumps(man, ensure_ascii=False, indent=1),
                         encoding="utf-8", newline="")
        return d, md_c, man_c, src_c

    # 控制组:零变异拷贝必须复现原件 disposition + IR 内容
    d, md_c, man_c, src_c = stage()
    base = rr.resolve_file(md_c)
    orig_rec = next(r["file"] for r in
                    json.loads((ROOT / "data/resolver_ref_r52/resolver_ir.json")
                               .read_text(encoding="utf-8"))["files"]
                    if r["file"].endswith(md_rel.replace("/", "\\")))
    orig_ir = next(r for r in
                   json.loads((ROOT / "data/resolver_ref_r52/resolver_ir.json")
                              .read_text(encoding="utf-8"))["files"]
                   if r["file"] == orig_rec)["ir"]
    ctrl_ok = (base["disposition"] == "ADMITTED"
               and [u["content"] for u in base["ir"]["units"]]
               == [u["content"] for u in orig_ir["units"]])
    results.append({"m": "control", "disposition": base["disposition"],
                    "content_equal_original": ctrl_ok, "ok": ctrl_ok})
    shutil.rmtree(d, ignore_errors=True)

    def run_case(tag, mutate, expect):
        d, md_c, man_c, src_c = stage()
        man = json.loads(man_c.read_text(encoding="utf-8"))
        man, note = mutate(man, d, src_c, md_c)
        if man is not None:
            man_c.write_text(json.dumps(man, ensure_ascii=False, indent=1),
                             encoding="utf-8", newline="")
        rec = rr.resolve_file(md_c)
        ok = rec["disposition"] == expect
        extra = note(rec) if note else {}
        results.append({"m": tag, "expected": expect,
                        "got": rec["disposition"], "ok": ok, **extra})
        shutil.rmtree(d, ignore_errors=True)

    run_case("C1_v1剥离",
             lambda man, d, s, m: (dict(man, identity_version=1), None),
             "REJECTED_V1")

    def c2(man, d, s, m):
        # R53 教训:QC C3 的裁决对象是**切片 md 锚点标记**,不是 manifest
        # spans——只改 manifest 造出生产不可产生的工件对漂移(首跑 MISS,
        # 定性为变异设计缺陷)。生产可 representable 的 FAIL 形态 = 改切片。
        txt = m.read_text(encoding="utf-8")
        m.write_text(txt.replace("“答案区开始”", "“删”", 1),
                     encoding="utf-8", newline="")
        return man, None
    run_case("C2_切片答案区破坏", c2, "REJECTED_QC_FAIL")

    def c3(man, d, s, m):
        man["units"][0].pop("section_ref", None)
        return man, None
    run_case("C3_pending_review通道", c3, "ADMITTED_PENDING_REVIEW")

    run_case("C4_源缺失",
             lambda man, d, s, m: (dict(man, source_file=str(
                 d / "ghost.md")), None), "MISSING")

    def c5(man, d, s, m):
        lines = s.read_text(encoding="utf-8").splitlines()
        s.write_text("\n".join(lines[:8]) + "\n", encoding="utf-8",
                     newline="")
        return man, None
    run_case("C5_截断源_STALE", c5, "REJECTED_STALE")

    def c6(man, d, s, m):
        a = next(u for u in man["units"] if u.get("section_ref")
                 and u.get("basis") != "keep")
        b = next(u for u in man["units"]
                 if u.get("section_ref") != a.get("section_ref")
                 and u.get("unit_id") != a.get("unit_id"))
        b["question_numbers"] = list(a["question_numbers"])
        return man, None
    run_case("C6_跨节非keep重号", c6, "REJECTED_QC_FAIL")

    def c7(man, d, s, m):
        for sec in man.get("sections") or []:
            sec["title"] = "【变异】" + str(sec.get("title"))
        return man, None
    d, md_c, man_c, src_c = stage()
    man = json.loads(man_c.read_text(encoding="utf-8"))
    man, _ = c7(man, d, src_c, md_c)
    man_c.write_text(json.dumps(man, ensure_ascii=False, indent=1),
                     encoding="utf-8", newline="")
    rec = rr.resolve_file(md_c)
    same = ([u["content"] for u in rec["ir"]["units"]]
            == [u["content"] for u in base["ir"]["units"]])
    results.append({"m": "C7_标题变异_行号锚定", "disposition":
                    rec["disposition"], "content_equal_control": same,
                    "ok": rec["disposition"] == "ADMITTED" and same})
    shutil.rmtree(d, ignore_errors=True)

    # 原件零触碰(Gate)
    ai.gate_assert_unchanged(gate_before, originals, "r53_resolver_mutation")

    ok = all(r["ok"] for r in results)
    Path(OUT).write_text(json.dumps(
        {"sample": md_rel, "all_ok": ok, "results": results},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="")
    for r in results:
        print(f'{r["m"]}: {"OK" if r["ok"] else "**MISS**"} {r}')
    print("all_ok =", ok)


if __name__ == "__main__":
    main()

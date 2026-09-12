"""Phase 2 存量身份回填(R34):把 batch-C 50 份真实产物确定性升级到
QuestionIdentity v2。零 LLM,证据全部可回源:

  - Identity:question_identity.assign_identity() 按单元位置构建
    SectionLocator(ordinal+span)并分配 section(R31 教训:绝不以
    unit_id 为键)。
  - basis:来自 R31 审计过的迁移计划 fix_bug22_renumber.PLAN
    (answer_key/shift/keep/explicit);未列入计划的单元 basis=
    printed_as_is 或 unverified(无法从源行验证印刷题号时)。
  - printed_number:迁移件取 migration report 的 old 值(provenance=
    migration_report);其余从题干首行确定性解析印刷题号
    (provenance=source_line);解析不出 = null + provenance=unknown
    ——绝不把 canonical 猜成 printed(R33/A5:伪造 Source Fact 比缺失更糟)。
  - keep 证据:迁移计划证据 + 所在分节标题行号(分节标题 L{n}:{title}),
    使 evidence_ok() 可机器验证。
  - 落盘前跑 check_identity:fail 非空即拒绝写入该文件;review 允许写入
    并进报告(证据不足 ≠ 非法)。

默认 dry-run;--apply 写回 manifest。报告:data/phase2_identity_backfill_report.json
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import question_identity as qi  # noqa: E402
from fix_bug22_renumber import PLAN, strip_meta  # noqa: E402  R31 审计过的迁移计划

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "Ocr-markdown/reslice-batch-C"
REPORT = ROOT / "data/phase2_identity_backfill_report.json"
MIGRATION = ROOT / "data/bug22_migration_report.json"


def load_lines(man):
    src = Path(man["source_file"])
    return strip_meta(src.read_text(encoding="utf-8", errors="replace")).splitlines()


def printed_from_stem(u, lines):
    """确定性解析印刷题号:题干首行 'NN.' 前缀。返回 (list|None, provenance)。"""
    rg = u.get("stem_lines")
    nums = u.get("question_numbers") or []
    if (isinstance(rg, list) and len(rg) == 2 and 0 < rg[0] <= len(lines)
            and len(nums) == 1):
        m = qi.PRINTED_LINE.match(lines[rg[0] - 1])
        if m:
            return [int(m.group(1))], "source_line"
    return None, "unknown"


def backfill_file(md_path, mig_by_file, apply=False):
    man_path = md_path.with_suffix(".manifest.json")
    man = json.loads(man_path.read_text(encoding="utf-8"))
    lines = load_lines(man)
    qi.assign_identity(man, lines)
    sec_by_id = {s["id"]: s for s in man["sections"]}

    changes = mig_by_file.get(md_path.name, [])
    old_by_uid = {c["unit_id"]: c for c in changes}

    basename = md_path.name
    ops = (PLAN.get(basename) or {}).get("ops") or []
    prov = Counter()
    basis_cnt = Counter()
    for u in man["units"]:
        op = next((o for o in ops
                   if o["units"] == "*" or u["unit_id"] in o["units"]), None)
        sec = sec_by_id.get(u.get("section_ref")) or {}
        if op:
            u["basis"] = op["mode"]
            ev = op["evidence"]
            if sec.get("title") and sec.get("start_line"):
                ev = f"{ev};分节标题 L{sec['start_line']}:{sec['title']}"
            u["basis_evidence"] = ev
            ch = old_by_uid.get(u["unit_id"])
            if ch:
                u["printed_number"] = list(ch["old"])
                u["printed_provenance"] = "migration_report"
            elif op["mode"] == "keep":
                # keep:印刷号 = 现 canonical(R31 按印刷保持),来源为迁移计划
                u["printed_number"] = list(u.get("question_numbers") or [])
                u["printed_provenance"] = "migration_report"
            else:
                u["printed_number"], u["printed_provenance"] = printed_from_stem(u, lines)
        else:
            pn, p = printed_from_stem(u, lines)
            u["printed_number"], u["printed_provenance"] = pn, p
            u["basis"] = "printed_as_is" if p == "source_line" else "unverified"
            u["basis_evidence"] = (
                f"题干首行印刷题号 L{u['stem_lines'][0]}" if p == "source_line" else "")
        prov[u.get("printed_provenance")] += 1
        basis_cnt[u.get("basis")] += 1

    fails, reviews = qi.check_identity(man, len(lines))
    entry = {"file": str(md_path), "units": len(man["units"]),
             "sections": len(man["sections"]),
             "basis": dict(basis_cnt), "printed_provenance": dict(prov),
             "fail_issues": fails, "review_notes": reviews,
             "applied": bool(apply and not fails)}
    if apply and not fails:
        man_path.write_text(json.dumps(man, ensure_ascii=False, indent=1),
                            encoding="utf-8", newline="\n")
    return entry


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    mig = json.loads(MIGRATION.read_text(encoding="utf-8"))
    mig_by_file = {Path(f["file"]).name: f["changes"] for f in mig["files"]}
    out = Path(args.out)
    results = []
    for p in sorted(out.rglob("*.manifest.json")):
        md = p.with_name(p.name[: -len(".manifest.json")] + ".md")
        if not md.exists():
            continue
        results.append(backfill_file(md, mig_by_file, apply=args.apply))
    REPORT.write_text(json.dumps({"applied": args.apply, "files": results},
                                 ensure_ascii=False, indent=1),
                      encoding="utf-8", newline="\n")
    nfail = sum(1 for r in results if r["fail_issues"])
    napp = sum(1 for r in results if r["applied"])
    nrev = sum(1 for r in results if r["review_notes"])
    print(f"=== identity 回填:{len(results)} 份,apply={napp},"
          f"fail={nfail},含 review={nrev} ===")
    for r in results:
        if r["fail_issues"] or r["review_notes"]:
            print(f"[!] {Path(r['file']).name}")
            for i in r["fail_issues"]:
                print(f"    FAIL {i}")
            for i in r["review_notes"]:
                print(f"    REV  {i}")


if __name__ == "__main__":
    main()

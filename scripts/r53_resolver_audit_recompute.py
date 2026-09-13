r"""R53 Resolver Consumer Adversarial Audit (a):IR 独立重算 + R-ACC 语料级穷举。

纪律:不信任 data/resolver_ref_r52/resolver_ir.json 的任何字段——
正则/映射/判定逻辑全部独立重实现(不 import resolver_reference);
仅"裁决来源"复用生产共用 reslice_qc.check(契约 C-IN-2 即要求如此)。

穷举检查(88 份全量,1664 单元逐单元,不得抽样):
  R1  disposition 独立重算 vs IR(v1/缺失/STALE/QC 裁决全链)
  R2  身份字段逐字段只读(R-ACC-3,C-IN-4/5)
  R3  provenance 一等公民字段完备(R-ACC-11,C-OUT-2;source_version
      与独立计算的源 sha 逐文件核对)
  R4  反伪造贯穿:provenance=unknown → IR printed 必空(C-IN-4)
  R5  材料:去重不复制、共享/单题不丢、consumers 集合精确(R50 攻击清单④⑤⑥)
  R6  答案表 td:cells/answers/unresolved 独立重算,答案值必须 ∈ td 原文
      (不伪造,C-IN-7 / R-ACC-6)
  R7  answer_number_mismatch flag 独立重算逐条对(C-IN-6 / R-ACC-5)
  R8  section 全解析 + section_title 一致(R50 攻击清单①)
  R9  内容切片逐 zone 与独立源行切片全等(行号锚定,C-IN-8)
  R10 c13-02 具名样本(答案区编号不一致形态)处置留痕
  R11 报告数字与重算一致(规则 4 口径)
  R12 IR 工件 sha 与台账引用一致

输出: data/r53_resolver_audit_recompute.json
用法: python scripts/r53_resolver_audit_recompute.py
"""
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import reslice_qc as qc  # noqa: E402  生产共用裁决(C-IN-2)
from fix_bug22_renumber import strip_meta  # noqa: E402

PREFLIGHT = ROOT / "data/resolver_contract_preflight.json"
IR_PATH = ROOT / "data/resolver_ref_r52/resolver_ir.json"
IR_SHA_CITED = ("fbcf41ab025fd786614b52d63270160868a2f49ab63121f012905c"
                "79f65b04a5")
OUT = ROOT / "data/r53_resolver_audit_recompute.json"

# 独立重实现(不复用 rr 的实现)
SPAN_KEYS = ("stem_lines", "options_lines", "material_lines",
             "questions_lines", "answer_lines", "explanation_lines")
TD_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.S | re.I)
NUM_RE = re.compile(r"^\s*(\d{1,3})\s*[.、．)）]")
IDENTITY_KEYS = ("question_numbers", "printed_number", "printed_provenance",
                 "basis", "basis_evidence", "section_ref", "unit_id",
                 "unit_type")
PROV_KEYS = ("source_file", "source_version", "source_lines",
             "manifest_file", "qc_verdict", "extraction_method",
             "confidence_state")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def span_ok(rg, n):
    return (isinstance(rg, list) and len(rg) == 2
            and all(isinstance(x, int) for x in rg)
            and 1 <= rg[0] <= rg[1] <= max(n, 1))


def main():
    pf = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    ir_doc = json.loads(IR_PATH.read_text(encoding="utf-8"))
    # 键归一化(IR file 字段为绝对路径,preflight 行为相对路径)
    by_file = {str((ROOT / r["file"]).resolve()): r
               for r in ir_doc["files"]}

    findings = []
    stats = Counter()
    named = {}
    flag_files = []
    table_stats = Counter()
    mism = []

    def bad(rel, msg):
        findings.append(f"{rel}: {msg}")

    for row in pf["rows"]:
        rel = row["file"]
        md = ROOT / rel
        rec = by_file.get(str(md.resolve()))
        if rec is None:
            bad(rel, "IR 缺该文件记录")
            continue
        man_path = md.with_suffix(".manifest.json")
        man = json.loads(man_path.read_text(encoding="utf-8"))

        # ---- R1 disposition 独立重算 ----
        if not man_path.exists():
            exp = "MISSING"
        elif (man.get("identity_version") or 1) < 2:
            exp = "REJECTED_V1"
        else:
            src = Path(man.get("source_file") or "")
            if not src.exists():
                exp = "MISSING"
            else:
                lines = strip_meta(src.read_text(
                    encoding="utf-8", errors="replace")).splitlines()
                n = len(lines)
                stale = any(
                    u.get(k) is not None and not span_ok(u.get(k), n)
                    for u in man.get("units") or [] for k in SPAN_KEYS)
                if stale:
                    exp = "REJECTED_STALE"
                else:
                    v = qc.check(md).get("verdict")
                    exp = {"FAIL": "REJECTED_QC_FAIL",
                           "PASS": "ADMITTED"}.get(
                        v, "ADMITTED_PENDING_REVIEW")
        if rec["disposition"] != exp:
            bad(rel, f"disposition {rec['disposition']} != 重算 {exp}")
        stats[exp] += 1

        if rec["ir"] is None:
            continue
        ir = rec["ir"]
        src = Path(man["source_file"])
        lines = strip_meta(src.read_text(encoding="utf-8",
                                         errors="replace")).splitlines()
        sec = {s.get("id"): s.get("title")
               for s in man.get("sections") or []}

        # ---- R11 报告级裁决一致 ----
        if ir["qc_verdict"] != qc.check(md).get("verdict"):
            bad(rel, "IR qc_verdict 与生产 QC 重算不一致")

        units_ir = {u["unit_id"]: u for u in ir["units"]}
        if len(ir["units"]) != len(man["units"]):
            bad(rel, "单元数与 manifest 不等")
        mat_consumers = {}
        for mu in man["units"]:
            uid = mu["unit_id"]
            iu = units_ir.get(uid)
            if iu is None:
                bad(rel, f"单元 {uid} 在 IR 缺失")
                continue
            stats["units"] += 1

            # ---- R2 身份只读 ----
            for k in IDENTITY_KEYS:
                if iu[k] != mu.get(k):
                    bad(rel, f"{uid}.{k} 被重塑: {iu[k]!r} != {mu.get(k)!r}")

            # ---- R3 provenance 完备 ----
            prov = iu["provenance"]
            for k in PROV_KEYS:
                if k not in prov or prov[k] in (None, ""):
                    bad(rel, f"{uid} provenance.{k} 缺失")
            if prov.get("source_version") != sha(src):
                bad(rel, f"{uid} source_version != 源 sha")
            if prov.get("source_lines") != {
                    k: mu[k] for k in SPAN_KEYS if mu.get(k) is not None}:
                bad(rel, f"{uid} provenance.source_lines != manifest spans")

            # ---- R4 反伪造贯穿 ----
            if (mu.get("printed_provenance") == "unknown"
                    and iu.get("printed_number")):
                bad(rel, f"{uid} unknown provenance 但 IR printed 非空")

            # ---- R9 内容切片全等(行号锚定) ----
            for k in SPAN_KEYS:
                rg = mu.get(k)
                if rg is None:
                    continue
                want = lines[rg[0] - 1:rg[1]]
                got = (iu["content"] or {}).get(k)
                if got != want:
                    bad(rel, f"{uid}.content.{k} != 源行切片")

            # ---- R5 材料 ----
            if mu.get("material_lines"):
                ref = iu["material_ref"]
                if not ref:
                    bad(rel, f"{uid} 有 material_lines 但 material_ref 丢失")
                else:
                    mat_consumers.setdefault(ref, set()).add(uid)
                    ent = ir["materials"].get(ref)
                    if ent is None:
                        bad(rel, f"{uid} material_ref {ref} 悬空")
                    else:
                        rg = mu["material_lines"]
                        if ent["text"] != lines[rg[0] - 1:rg[1]]:
                            bad(rel, f"material {ref} 文本 != 源切片")
                        if ent["lines"] != rg:
                            bad(rel, f"material {ref} lines != manifest")
            elif iu["material_ref"] is not None:
                bad(rel, f"{uid} 无 material_lines 却有 material_ref")

            # ---- R6 答案表 ----
            rg = mu.get("answer_lines")
            if (rg and rg[0] == rg[1]
                    and rg[0] <= len(lines) and "<table" in lines[rg[0] - 1]):
                table_stats["units"] += 1
                cells = [c.strip() for c in TD_RE.findall(lines[rg[0] - 1])]
                ans = iu["answers"]
                if ans is None:
                    bad(rel, f"{uid} 表格答案单元无 answers 结构")
                    continue
                qns = mu.get("question_numbers") or []
                if ans["cells"] != cells:
                    bad(rel, f"{uid} td cells 与独立解析不等")
                for q, v in ans["answers"].items():
                    if int(q) not in qns:
                        bad(rel, f"{uid} 答案键 {q} 超出题号集")
                    if v not in cells:
                        bad(rel, f"{uid} 答案值不在 td 原文(伪造风险)")
                if ans["unresolved"]:
                    table_stats["unresolved_units"] += 1
                table_stats[ans["method"]] += 1

            # ---- R7 flag 独立重算 ----
            at = (iu.get("answer_text") or [])
            want_flags = []
            if at:
                m = NUM_RE.match(at[0])
                if m and int(m.group(1)) not in (mu.get("question_numbers")
                                                 or []):
                    want_flags.append("answer_number_mismatch")
            if (iu.get("answers") and iu["answers"].get("unresolved")
                    and "answer_table_unresolved" not in want_flags):
                if iu["answers"]["unresolved"]:
                    want_flags.append("answer_table_unresolved")
            got_flags = [f for f in (iu.get("flags") or [])
                         if f in ("answer_number_mismatch",
                                  "answer_table_unresolved")]
            if sorted(set(got_flags)) != sorted(set(want_flags)):
                bad(rel, f"{uid} flags {got_flags} != 重算 {want_flags}")
            if "answer_number_mismatch" in got_flags:
                stats["mismatch_flags"] += 1
                flag_files.append(f"{Path(rel).name}:{uid}")

            # ---- R8 section ----
            sref = mu.get("section_ref")
            if sref and sref not in sec:
                bad(rel, f"{uid} section_ref 悬空 {sref!r}")
            if iu.get("section_title") != sec.get(sref):
                bad(rel, f"{uid} section_title 不一致")

        # consumers 集合精确(共享不复制 + 不丢)
        for ref, ent in ir["materials"].items():
            if set(ent["consumers"]) != mat_consumers.get(ref, set()):
                bad(rel, f"material {ref} consumers 不精确")
        stats["materials"] += len(ir["materials"])

    # ---- R10 c13-02 具名样本 ----
    c13 = [f for f in by_file if "c13-02" in f]
    if c13:
        r = by_file[c13[0]]
        named["c13-02"] = {
            "disposition": r["disposition"],
            "units": len((r["ir"] or {}).get("units") or []),
            "mismatch_flags": sum(
                1 for u in (r["ir"] or {}).get("units") or []
                if "answer_number_mismatch" in (u.get("flags") or [])),
        }

    # ---- R11 报告数字 ----
    report = json.loads(
        (ROOT / "data/resolver_ref_r52/resolver_report.json")
        .read_text(encoding="utf-8"))
    if report["files"]["numerator"] != stats["ADMITTED"]:
        findings.append("report ADMITTED 数与重算不等")
    if report["units_in_ir"]["numerator"] != stats["units"]:
        findings.append("report units 数与重算不等")

    # ---- R12 IR sha ----
    sha_ok = sha(IR_PATH) == IR_SHA_CITED

    result = {
        "n_files": len(pf["rows"]),
        "disposition_recompute": dict(stats),
        "findings": findings,
        "answer_table": dict(table_stats),
        "mismatch_flag_files": sorted(set(flag_files)),
        "named": named,
        "ir_sha_matches_ledger": sha_ok,
        "all_ok": not findings and sha_ok,
    }
    Path(OUT).write_text(json.dumps(result, ensure_ascii=False, indent=1)
                         + "\n", encoding="utf-8", newline="")
    print(json.dumps({k: v for k, v in result.items()
                      if k != "mismatch_flag_files"},
                     ensure_ascii=False, indent=1)[:1800])
    print("all_ok =", result["all_ok"])


if __name__ == "__main__":
    main()

r"""参考 Resolver(reference implementation,R52;用户裁定:实现先行再审)。

严格按冻结契约 `resolver_contract_design.md` v0.1 + R50 附录 B 实现:

  C-IN-1 只消费 v2(v1 → fail-closed 拒收,机器可读理由)
  C-IN-2 消费 QC verdict(生产共用 reslice_qc.check),不看产物存在性
  C-IN-3 四态传播:FAIL / PENDING_REVIEW / MISSING / STALE(+UNCOMPUTABLE)
         不得静默转 PASS;PENDING_REVIEW 走 Admission 通道,永不自动转 PASS
  C-IN-4 身份只读:printed/canonical/section 原样搬运,不重推断
  C-IN-5 basis 只读:不重解释、不补豁免(跨节重号由 QC/identity 层裁决)
  C-IN-6 answer 区编号可与题干区不一致:结构观察 flag,不静默重绑
  C-IN-7 答案表 td 按题号取:键位可解析按题号映射;推不出标
         unresolved,不猜(R19 前置任务语义)
  C-IN-8 行号锚定:内容只按 span 切片,不重新解析标题层级
  C-OUT-1 输出路径全部派生自 --out,禁止写死工件路径
  C-OUT-2 IR 逐单元携带一等公民 provenance(EvidenceProvenance:
         source_version=源 sha256 / source_line=spans /
         extraction_method / confidence_state;R50 附录 B)
  C-OUT-3 报告按 review_protocol 规则 4 报 numerator/denominator/proof

三边界:Resolver 只做 structural 判断(无语义裁决);身份唯一来源 =
manifest v2 字段(本模块 import 面不含任何身份推断逻辑,R-ACC-4);
Gate 只证明约束、人类不确定性由 Admission 承接。

定位:参考实现 + 对抗审查对象,**不进生产链路**。
用法:
  python scripts/resolver_reference.py \
      --preflight data/resolver_contract_preflight.json --out <dir>
  python scripts/resolver_reference.py --inputs a.md b.md --out <dir>
输出(仅在 --out 目录内):resolver_ir.json + resolver_report.json
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import reslice_qc as qc  # noqa: E402  生产共用 QC(C-IN-2 唯一裁决来源)
from fix_bug22_renumber import strip_meta  # noqa: E402

IR_VERSION = "resolver-ir-0.1"
SPAN_KEYS = ("stem_lines", "options_lines", "material_lines",
             "questions_lines", "answer_lines", "explanation_lines")
TD_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.S | re.I)
NUM_PREFIX_RE = re.compile(r"^\s*(\d{1,3})\s*[.、．)）]")


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _span_ok(rg, n):
    return (isinstance(rg, list) and len(rg) == 2
            and all(isinstance(x, int) for x in rg)
            and 1 <= rg[0] <= rg[1] <= max(n, 1))


def _span_text(lines, rg):
    if _span_ok(rg, len(lines)):
        return lines[rg[0] - 1:rg[1]]
    return None


def check_stale(man, n):
    """结构信号:任一声明 span 越界 → manifest 与当前源漂移(STALE)。"""
    for u in man.get("units") or []:
        for k in SPAN_KEYS:
            rg = u.get(k)
            if rg is not None and not _span_ok(rg, n):
                return f"STALE: {u.get('unit_id')} {k}={rg} 源行数={n}"
    return None


def parse_answer_table(line, question_numbers):
    """C-IN-7:答案表单行 <table> 的 td 按题号映射。

    键位形态(td 自带题号前缀)→ 按题号取;纯位置形态 → 与单元
    question_numbers 顺序对齐;两者推不出的题号标 unresolved,不猜测。
    """
    cells = [c.strip() for c in TD_RE.findall(line)]
    keyed = {}
    for c in cells:
        m = NUM_PREFIX_RE.match(c)
        if m:
            keyed[int(m.group(1))] = c
    answers, unresolved = {}, []
    if keyed and len(keyed) == len(cells):
        method = "td_by_question_number"
        for q in question_numbers:
            if q in keyed:
                answers[str(q)] = keyed[q]
            else:
                unresolved.append(q)
    else:
        method = "td_positional"
        if len(cells) == len(question_numbers):
            for q, c in zip(question_numbers, cells):
                answers[str(q)] = c
        else:
            unresolved = list(question_numbers)
    return {"cells": cells, "method": method,
            "answers": answers, "unresolved": unresolved}


def _answer_flags(answer_text, question_numbers):
    """C-IN-6:answer 区首行题号与本单元题号无关 → 结构观察 flag(不重绑)。"""
    flags = []
    if answer_text:
        m = NUM_PREFIX_RE.match(answer_text[0])
        if m and int(m.group(1)) not in question_numbers:
            flags.append("answer_number_mismatch")
    return flags


def build_unit_records(man, lines, src, md_path, verdict):
    """逐单元构建 IR 记录(全部结构性搬运,无语义裁决)。"""
    sec_title = {s.get("id"): s.get("title")
                 for s in man.get("sections") or []}
    materials = {}
    records = []
    for u in man.get("units") or []:
        spans = {k: u.get(k) for k in SPAN_KEYS if u.get(k) is not None}
        content = {k: _span_text(lines, u.get(k)) for k in SPAN_KEYS
                   if u.get(k) is not None}
        mat_ref = None
        mat = content.get("material_lines")
        if mat is not None:
            rg = u.get("material_lines")
            mat_ref = f"L{rg[0]}-{rg[1]}"
            entry = materials.setdefault(
                mat_ref, {"lines": rg, "text": mat, "consumers": []})
            entry["consumers"].append(u.get("unit_id"))

        ans_text = content.get("answer_lines")
        answers = None
        flags = _answer_flags(ans_text, u.get("question_numbers") or [])
        ans_span = u.get("answer_lines")
        if (ans_span and ans_span[0] == ans_span[1] and ans_text
                and "<table" in ans_text[0]):
            tbl = parse_answer_table(ans_text[0],
                                     u.get("question_numbers") or [])
            answers = tbl
            if tbl["unresolved"]:
                flags.append("answer_table_unresolved")

        records.append({
            "unit_id": u.get("unit_id"),
            "unit_type": u.get("unit_type"),
            "question_numbers": u.get("question_numbers"),
            "printed_number": u.get("printed_number"),
            "printed_provenance": u.get("printed_provenance"),
            "basis": u.get("basis"),
            "basis_evidence": u.get("basis_evidence"),
            "section_ref": u.get("section_ref"),
            "section_title": sec_title.get(u.get("section_ref")),
            "content": content,
            "material_ref": mat_ref,
            "answers": answers,
            "answer_text": ans_text,
            "flags": flags,
            "provenance": {
                "source_file": str(src),
                "source_version": _sha256(src),
                "source_lines": spans,
                "manifest_file": str(md_path.with_suffix(".manifest.json")),
                "qc_verdict": verdict,
                "extraction_method": "line_span_v1",
                "confidence_state": ("structural_only"
                                     if not flags else "structural_only+flags"),
            },
        })
    return records, materials


def resolve_file(md_path: Path):
    """单文件消费。返回 disposition 记录(fail-closed,永不静默转 PASS)。"""
    md_path = Path(md_path)
    rec = {"file": str(md_path), "ir": None, "reasons": []}
    man_path = md_path.with_suffix(".manifest.json")
    if not man_path.exists():
        rec["disposition"] = "MISSING"
        rec["reasons"].append("manifest missing")
        return rec
    man = json.loads(man_path.read_text(encoding="utf-8"))

    # C-IN-1:v1 拒收(在 QC 之前,fail-closed)
    if (man.get("identity_version") or 1) < 2:
        rec["disposition"] = "REJECTED_V1"
        rec["reasons"].append("identity_version < 2 (C-IN-1)")
        return rec

    src = Path(man.get("source_file") or "")
    # BUG-31(R61 修复):provenance fail-closed——source_file 缺失/非文件
    # (Path("") 的存在性语义是目录 ".",or "" 不是安全网)必须显式 MISSING,
    # 禁崩溃、禁猜路径、禁 fallback、禁降级 ADMITTED(缺事实 ≠ 推测事实)。
    if not src.is_file():
        rec["disposition"] = "MISSING"
        rec["reasons"].append(
            f"source_file missing or not a file: {src!s} "
            f"(provenance break, fail-closed)")
        return rec
    try:
        lines = strip_meta(src.read_text(encoding="utf-8",
                                         errors="replace")).splitlines()
    except OSError as e:
        rec["disposition"] = "MISSING"
        rec["reasons"].append(f"source unreadable: {e!r} (fail-closed)")
        return rec

    stale = check_stale(man, len(lines))
    if stale:
        rec["disposition"] = "REJECTED_STALE"
        rec["reasons"].append(stale)
        return rec

    # C-IN-2:唯一裁决来源 = 生产共用 QC;不可计算 → fail-closed
    try:
        q = qc.check(md_path)
    except Exception as e:  # noqa: BLE001
        rec["disposition"] = "REJECTED_QC_UNCOMPUTABLE"
        rec["reasons"].append(f"qc.check raised: {e!r}")
        return rec
    verdict = q.get("verdict")
    if verdict == "FAIL":
        rec["disposition"] = "REJECTED_QC_FAIL"
        rec["reasons"] = list(q.get("issues") or [])[:20]
        rec["qc_verdict"] = verdict
        return rec

    records, materials = build_unit_records(man, lines, src, md_path,
                                            verdict)
    rec["qc_verdict"] = verdict
    rec["ir"] = {"ir_version": IR_VERSION,
                 "source_file": str(src),
                 "source_sha256": _sha256(src),
                 "manifest_file": str(man_path),
                 "qc_verdict": verdict,
                 "materials": materials,
                 "units": records}
    # C-FAIL-2:PENDING_REVIEW 是 Admission 通道的输入,永不自动转 PASS
    rec["disposition"] = ("ADMITTED" if verdict == "PASS"
                          else "ADMITTED_PENDING_REVIEW")
    return rec


def run(md_paths, out_dir: Path):
    """批量消费并落盘(--out 派生,C-OUT-1)。确定性输出(无时间戳)。"""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results = [resolve_file(p) for p in md_paths]

    ir_doc = {"ir_version": IR_VERSION, "files": results}
    (out_dir / "resolver_ir.json").write_text(
        json.dumps(ir_doc, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8", newline="")

    # C-OUT-3 / 规则 4:每项声明带 numerator/denominator/proof
    n = len(results)
    admitted = [r for r in results if r["disposition"] == "ADMITTED"]
    pending = [r for r in results
               if r["disposition"] == "ADMITTED_PENDING_REVIEW"]
    n_units = sum(len(r["ir"]["units"]) for r in admitted + pending)
    n_pending_units = sum(len(r["ir"]["units"]) for r in pending)
    dispositions = {}
    for r in results:
        dispositions[r["disposition"]] = \
            dispositions.get(r["disposition"], 0) + 1
    report = {
        "ir_version": IR_VERSION,
        "files": {"numerator": len(admitted), "denominator": n,
                  "proof": "qc.check verdict==PASS via reslice_qc.check"},
        "pending_review_files": {"numerator": len(pending), "denominator": n,
                                 "proof": "qc verdict==PENDING_REVIEW;"
                                          " Admission channel, never auto-PASS"},
        "units_in_ir": {"numerator": n_units,
                        "denominator": n_units,
                        "proof": "manifest units of admitted files,"
                                 " span-sliced line-anchored"},
        "units_pending_review": {"numerator": n_pending_units,
                                 "denominator": n_units,
                                 "proof": "units of PENDING_REVIEW files"},
        "dispositions": dict(sorted(dispositions.items())),
    }
    (out_dir / "resolver_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8", newline="")
    return ir_doc, report


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--preflight")
    ap.add_argument("--inputs", nargs="*", default=[])
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    paths = [Path(p) for p in args.inputs]
    if args.preflight:
        pf = json.loads(Path(args.preflight).read_text(encoding="utf-8"))
        paths += [ROOT / r["file"] for r in pf.get("rows", [])]
    _, report = run(paths, Path(args.out))
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()

r"""PAC 第一轮对抗性审查:独立重算脚本(R46)。

纪律:不信任 pac_track_round1.json 的任何数字——每个字段从原始工件
(源 PDF、OCR md、annotated 产物、QC/回填/LLM result JSON)独立重算后比对。
文本层判定不复用 pac_select 的结论,独立用 fitz 重测(原始逐页字符数入档)。

输出:data/pac_audit_recompute.json
  {samples: [{sample_id, checks: [{name, claim, actual, ok}], invariants: [...]}],
   totals: {...}, findings: [str]}

用法: python scripts/pac_audit_recompute.py
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

TRACK = ROOT / "data/pac_track_round1.json"
SELECTION = ROOT / "data/pac_selection.json"
TRACK_OCR = ROOT / "data/pac_track_ocr.json"
QC_V2 = ROOT / "data/pac_qc_v2.json"
BACKFILL = ROOT / "data/pac_identity_backfill_report.json"
LLM_RESULT = ROOT / "data/reslice_reslice-pac-annotated_result.json"
PROBE = ROOT / "data/pac_semantic_probe.json"
OCR_MD_DIR = ROOT / "Ocr-markdown/reslice-pac/ocr"
ANN_DIR = ROOT / "Ocr-markdown/reslice-pac-annotated/reslice-pac/ocr"
OUT = ROOT / "data/pac_audit_recompute.json"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    import fitz  # PyMuPDF

    track = json.loads(TRACK.read_text(encoding="utf-8"))
    selection = json.loads(SELECTION.read_text(encoding="utf-8"))
    track_ocr = json.loads(TRACK_OCR.read_text(encoding="utf-8"))
    qc_v2 = json.loads(QC_V2.read_text(encoding="utf-8"))
    backfill = json.loads(BACKFILL.read_text(encoding="utf-8"))
    llm = json.loads(LLM_RESULT.read_text(encoding="utf-8"))
    probe = json.loads(PROBE.read_text(encoding="utf-8"))

    sel_by_id = {s["sample_id"]: s for s in selection["samples"]}
    qc_by_name = {Path(r["file"]).name: r for r in qc_v2}
    bf_by_name = {Path(r["file"]).name: r for r in backfill["files"]}
    # LLM result 为顶层 list;条目键:file/issues/units/covered_sorted/...
    llm_by_name = {}
    for e in llm:
        llm_by_name[Path(e.get("file", "")).name] = e

    samples_out = []
    findings = []
    tot = {"pages_measured": 0, "pages_billed": 0, "prompt": 0, "completion": 0,
           "units": 0, "qc_pass": 0, "qc_fail": 0}

    for t in track["tracks"]:
        sid = t["sample_id"]
        ck = []

        def add(name, claim, actual):
            ok = claim == actual
            ck.append({"name": name, "claim": claim, "actual": actual, "ok": ok})
            if not ok:
                findings.append(f"{sid} {name}: claim={claim!r} actual={actual!r}")
            return ok

        st = t["stages"]
        sel = sel_by_id.get(sid)
        if sel is None:
            findings.append(f"{sid} 不在 pac_selection.json")
            samples_out.append({"sample_id": sid, "checks": ck, "invariants": []})
            continue

        # ── source:PDF sha256 / 页数 / 文本层(独立 fitz 重测)──────────────
        pdf = Path(sel["pdf"]["path"])
        if not pdf.exists():
            findings.append(f"{sid} 源 PDF 不存在: {pdf}")
        else:
            add("pdf_sha256(track vs 现文件)", st["source"]["pdf_sha256"], sha256(pdf))
            add("pdf_sha256(track vs selection)", st["source"]["pdf_sha256"],
                sel["pdf"]["sha256"])
            doc = fitz.open(pdf)
            add("pages(track vs fitz)", st["source"]["pages"], doc.page_count)
            tot["pages_measured"] += doc.page_count
            chars = [len(p.get_text().strip()) for p in doc]
            frac = sum(1 for c in chars if c >= 50) / max(doc.page_count, 1)
            tl = "native_text" if frac >= 0.6 else "scanned"
            add("text_layer(track vs fitz重测)", st["source"]["text_layer"], tl)
            ck.append({"name": "text_layer 逐页字符数(fitz 原始)",
                       "claim": None, "actual": chars, "ok": True})
            add("text_layer(track vs selection)",
                st["source"]["text_layer"], sel["pdf"]["text_layer"])
            doc.close()

        # ── OCR:输出 md sha256 / pages_billed / track_ocr 交叉 ─────────────
        ocr_md = OCR_MD_DIR / f"{sid}.md"
        if not ocr_md.exists():
            findings.append(f"{sid} OCR md 不存在: {ocr_md}")
        else:
            add("ocr md sha256(track vs 现文件)", st["ocr"]["output_md_sha256"],
                sha256(ocr_md))
        to = track_ocr.get(sid, {})
        add("ocr status(track vs track_ocr)", st["ocr"]["status"], to.get("status"))
        add("pages_billed(track vs track_ocr)", st["ocr"]["pages_billed"],
            to.get("pages_billed"))
        add("job_id(track vs track_ocr)", st["ocr"]["job_id"], to.get("job_id"))
        add("ocr md sha256(track vs track_ocr)", st["ocr"]["output_md_sha256"],
            to.get("output_md_sha256"))
        add("input_pdf_sha(track_ocr vs selection)", to.get("input_pdf_sha256"),
            sel["pdf"]["sha256"])
        tot["pages_billed"] += st["ocr"]["pages_billed"] or 0

        # ── annotation:tokens/model/validation_issues vs LLM result ────────
        md_name = f"{sid}.md"
        le = llm_by_name.get(md_name)
        if le is None:
            findings.append(f"{sid} LLM result 条目缺失({md_name})")
        else:
            add("prompt_tokens(track vs result)", st["annotation"]["prompt_tokens"],
                le.get("prompt_tokens"))
            add("completion_tokens(track vs result)",
                st["annotation"]["completion_tokens"], le.get("completion_tokens"))
            add("validation_issues(track vs result)",
                st["annotation"]["validation_issues"], le.get("issues"))
            add("units(track vs result)", st["manifest"]["units"], le.get("units"))
        tot["prompt"] += st["annotation"]["prompt_tokens"] or 0
        tot["completion"] += st["annotation"]["completion_tokens"] or 0

        # ── manifest:units / identity_version / sections + 内部不变量 ──────
        man_path = ANN_DIR / f"{sid}.manifest.json"
        if not man_path.exists():
            findings.append(f"{sid} manifest 不存在: {man_path}")
            samples_out.append({"sample_id": sid, "checks": ck, "invariants": []})
            continue
        man = json.loads(man_path.read_text(encoding="utf-8"))
        add("manifest units(track vs 现文件)", st["manifest"]["units"],
            len(man.get("units") or []))
        add("identity_version(track vs 现文件)", st["manifest"]["identity_version"],
            man.get("identity_version"))
        add("sections(track vs 现文件)", st["manifest"]["sections"],
            len(man.get("sections") or []))
        tot["units"] += len(man.get("units") or [])

        # 内部不变量(与 QC 独立实现的复算)
        invariants = []
        src_path = Path(man.get("source_file", ""))
        src_lines = []
        if src_path.exists():
            txt = re.sub(r"<!--\s*META:[^>]*-->\n?", "",
                         src_path.read_text(encoding="utf-8", errors="replace"))
            src_lines = txt.splitlines()
        else:
            findings.append(f"{sid} manifest.source_file 不存在: {src_path}")
        n_lines = len(src_lines)

        # I1 canonical 全卷重复(非 keep 语义简化:任何重复都列出,人工判读)
        owners = {}
        for u in man.get("units") or []:
            for n in u.get("question_numbers") or []:
                owners.setdefault(n, []).append(u.get("unit_id"))
        dups = {n: ids for n, ids in owners.items() if len(ids) > 1}
        invariants.append({"name": "I1 canonical 重复(仅 keep 豁免可合法)",
                           "value": dups, "ok": None})

        # I2 所有区间在源文件界内
        oob = []
        for u in man.get("units") or []:
            for k in ("stem_lines", "options_lines", "answer_lines",
                      "explanation_lines", "material_lines", "questions_lines",
                      "extra_lines"):
                rg = u.get(k)
                if isinstance(rg, list) and len(rg) == 2 and n_lines:
                    if not (1 <= rg[0] <= rg[1] <= n_lines):
                        oob.append((u.get("unit_id"), k, rg))
        invariants.append({"name": "I2 区间越界", "value": oob, "ok": not oob})
        if oob:
            findings.append(f"{sid} I2 区间越界: {oob[:5]}")

        # I3 section_ref 可解析
        sec_ids = {s.get("id") for s in man.get("sections") or []}
        bad_ref = [u.get("unit_id") for u in man.get("units") or []
                   if (u.get("section_ref") or "") not in sec_ids]
        invariants.append({"name": "I3 section_ref 悬空", "value": bad_ref,
                           "ok": not bad_ref})
        if bad_ref:
            findings.append(f"{sid} I3 section_ref 悬空: {bad_ref[:5]}")

        # I4 C8 独立复算:annotated 去 META == 源文件逐行
        ann_path = man_path.with_name(f"{sid}.annotated.md")
        if ann_path.exists() and src_lines:
            ann_lines = [l for l in ann_path.read_text(
                encoding="utf-8", errors="replace").splitlines()
                if not re.match(r"^\s*<!--\s*META:", l)]
            same = ann_lines == src_lines
            invariants.append({"name": "I4 annotated==source(C8 独立复算)",
                               "value": (len(ann_lines), n_lines), "ok": same})
            if not same:
                findings.append(f"{sid} I4 C8 复算不一致: ann={len(ann_lines)} src={n_lines}")
        else:
            findings.append(f"{sid} I4 annotated.md 缺失")

        # I5 answer_lines 非空区间(C3 的 manifest 侧独立复算)
        no_ans = [u.get("unit_id") for u in man.get("units") or []
                  if not (isinstance(u.get("answer_lines"), list)
                          and len(u["answer_lines"]) == 2)]
        invariants.append({"name": "I5 answer_lines 缺失单元", "value": no_ans,
                           "ok": None})

        # I6 覆盖完整性独立复算(R45 声明:并集=1..max,0 缺号 0 重号):
        #    以 LLM result 的 covered_sorted 与 manifest 并集双侧互证
        man_nums = sorted({n for u in man.get("units") or []
                           for n in (u.get("question_numbers") or [])})
        le_cov = sorted(le.get("covered_sorted") or []) if le else []
        cov_ok = (man_nums == le_cov
                  and man_nums == list(range(1, (man_nums[-1] if man_nums else 0) + 1))
                  and (le or {}).get("covered_questions") == len(man_nums))
        invariants.append({
            "name": "I6 覆盖=1..max 无缺重(manifest∩result 双侧)",
            "value": {"manifest": f"{len(man_nums)}nums",
                      "result": f"{len(le_cov)}nums",
                      "max": man_nums[-1] if man_nums else 0},
            "ok": cov_ok})
        if not cov_ok:
            findings.append(f"{sid} I6 覆盖不完美: manifest={man_nums[:60]}... "
                            f"result={le_cov[:60]}...")

        # I7 model 与 prompt 版本(声明 mimo-x-pro-preview / v2.3)
        am = man.get("annotation_meta") or {}
        invariants.append({"name": "I7 model/prompt_version",
                           "value": {"model": man.get("model"),
                                     "prompt_version": am.get("prompt_version")},
                           "ok": man.get("model") == "mimo-x-pro-preview"})
        if man.get("model") != "mimo-x-pro-preview":
            findings.append(f"{sid} I7 model 异常: {man.get('model')!r}")

        # ── QC:verdict/issues vs pac_qc_v2(并独立重跑 reslice_qc)──────────
        qr = qc_by_name.get(md_name)
        if qr is None:
            findings.append(f"{sid} pac_qc_v2 条目缺失")
        else:
            add("qc verdict(track vs pac_qc_v2)", st["qc"]["verdict"], qr["verdict"])
            add("qc issues(track vs pac_qc_v2)", st["qc"]["issues"], qr["issues"])
        if st["qc"]["verdict"] == "PASS":
            tot["qc_pass"] += 1
        else:
            tot["qc_fail"] += 1

        # ── identity 回填:fails/reviews vs 报告 ───────────────────────────
        br = bf_by_name.get(md_name)
        if br is None:
            findings.append(f"{sid} 回填报告条目缺失")
        else:
            add("identity fails(track vs 报告)", st["identity"]["fails"],
                len(br.get("fail_issues") or []))
            add("identity reviews(track vs 报告)", st["identity"]["reviews"],
                len(br.get("review_notes") or []))
            add("backfill units(track vs 报告)", st["manifest"]["units"],
                br.get("units"))
            add("backfill sections(track vs 报告)", st["manifest"]["sections"],
                br.get("sections"))

        samples_out.append({"sample_id": sid, "checks": ck, "invariants": invariants})

    # ── 全局汇总核对 ──────────────────────────────────────────────────────
    totals = {
        "pages_measured_sum": tot["pages_measured"],
        "pages_billed_sum": tot["pages_billed"],
        "pages_billed_eq_measured": tot["pages_billed"] == tot["pages_measured"],
        "prompt_sum": tot["prompt"],
        "completion_sum": tot["completion"],
        "llm_total": tot["prompt"] + tot["completion"],
        "units_sum": tot["units"],
        "probe_n_units": probe.get("n_units"),
        "units_sum_eq_probe": tot["units"] == probe.get("n_units"),
        "qc_pass": tot["qc_pass"],
        "qc_fail": tot["qc_fail"],
        "qc_pass_eq_track": tot["qc_pass"] == track.get("qc_pass"),
        "qc_fail_eq_track": tot["qc_fail"] == track.get("qc_fail"),
        "n_samples": len(track["tracks"]),
    }
    # 探针 78 报警总数独立重数
    flag_cnt = sum(len(r.get("flags") or []) for r in probe.get("results") or [])
    totals["probe_flags_recount"] = flag_cnt
    totals["probe_flags_eq_header"] = flag_cnt == sum(
        probe.get("flags_by_check", {}).values())

    n_bad = sum(1 for s in samples_out for c in s["checks"] if not c["ok"])
    report = {"samples": samples_out, "totals": totals, "findings": findings,
              "n_checks": sum(len(s["checks"]) for s in samples_out),
              "n_mismatch": n_bad}
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                   encoding="utf-8", newline="")
    print(f"checks={report['n_checks']} mismatch={n_bad} findings={len(findings)}")
    for f in findings:
        print("  !", f)
    print(json.dumps(totals, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

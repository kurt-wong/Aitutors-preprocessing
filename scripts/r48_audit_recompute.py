r"""R49 对抗性审查(a):对 R48 preflight 结论的独立重算。

纪律:不 import resolver_contract_preflight(被审对象),pc 类检查全部独立
重实现;QC verdict 不重算(QC 确定性 R42/R46 已穷举),改为与三份已提交
QC 工件(batch-C / pilot / PAC)逐文件对账。同时重测 R48 设计稿转抄的
数字声明(printed provenance 分布 / keep 单元 / c09-01 / c01-02 / R19 答案表)。

输出: data/r48_audit_recompute.json
用法: python scripts/r48_audit_recompute.py
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fix_bug22_renumber import strip_meta  # noqa: E402

PREFLIGHT = ROOT / "data/resolver_contract_preflight.json"
OUT = ROOT / "data/r48_audit_recompute.json"

BASIS_VOCAB = {"answer_key", "shift", "keep", "printed_as_is",
               "explicit", "unverified"}
PROV_VOCAB = {"source_line", "migration_report", "unknown"}
SPAN_KEYS = ("stem_lines", "options_lines", "material_lines",
             "questions_lines", "answer_lines", "explanation_lines")


def load_qc(path, key):
    data = json.loads((ROOT / path).read_text(encoding="utf-8"))
    rows = data if isinstance(data, list) else data.get("files", data)
    return {Path(r["file"]).name: r.get("verdict") for r in rows}


def main():
    pf = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    rows_by_file = {r["file"]: r for r in pf["rows"]}

    findings = []          # 与 preflight 不一致或声明证伪
    independent = {}       # 独立重算结果
    dist = Counter()       # basis 分布(非空转证明)
    prov_dist = Counter()  # provenance 分布
    batchc_units = {"total": 0, "unknown": 0, "keep": 0}
    named = {}             # 按文件名的具名声明

    for rel, row in sorted(rows_by_file.items()):
        md = ROOT / rel
        man = json.loads(md.with_suffix(".manifest.json")
                         .read_text(encoding="utf-8"))
        iv = man.get("identity_version") or 1
        ind_findings = []
        src = Path(man.get("source_file") or "")
        if not src.exists():
            ind_findings.append("pc10")
        n = None
        lines = None
        if src.exists():
            lines = strip_meta(src.read_text(encoding="utf-8",
                                             errors="replace")).splitlines()
            n = len(lines)
        if iv < 2:
            ind_findings.append("pc1")
        else:
            # pc5/6/7/8/9 独立重实现
            sec_ids = {s.get("id") for s in man.get("sections") or []}
            for u in man.get("units") or []:
                b = u.get("basis")
                dist[b if b in BASIS_VOCAB else f"INVALID:{b!r}"] += 1
                p = u.get("printed_provenance")
                prov_dist[p if p in PROV_VOCAB else f"INVALID:{p!r}"] += 1
                pn = u.get("printed_number")
                if "reslice-batch-C" in rel:
                    batchc_units["total"] += 1
                    if p == "unknown":
                        batchc_units["unknown"] += 1
                    if b == "keep":
                        batchc_units["keep"] += 1
                if b not in BASIS_VOCAB:
                    ind_findings.append("pc5")
                if p not in PROV_VOCAB:
                    ind_findings.append("pc6")
                if (p == "unknown" and pn) or (p == "source_line" and not pn):
                    ind_findings.append("pc7")
                sref = u.get("section_ref")
                if sref and sref not in sec_ids:
                    ind_findings.append("pc8")
                if n:
                    for k in SPAN_KEYS:
                        rg = u.get(k)
                        if (isinstance(rg, list) and len(rg) == 2
                                and all(isinstance(x, int) for x in rg)):
                            if not (1 <= rg[0] <= rg[1] <= max(n, 1)):
                                ind_findings.append("pc9")
        # pc2/pc3: 生产共用校验重跑(这正是契约要求"复用共用实现"的对象)
        pc23 = []
        if iv >= 2 and lines is not None:
            import question_identity as qi
            fails, reviews = qi.check_identity(man, len(lines), lines)
            pc23 = (["pc2"] * len(fails)) + (["pc3"] * len(reviews))
        ind = sorted(set(ind_findings + pc23))
        pf_pcs = sorted({f.split()[0] for f in row["findings"]})
        if ind != pf_pcs:
            findings.append(f"{rel}: 独立重算 {ind} != preflight {pf_pcs}")
        independent[rel] = {"pcs": ind, "id_version": iv,
                            "qc_verdict": row.get("qc_verdict")}

    # ---- 与已提交 QC 工件对账(verdict 不重算,对账三方证据) ----
    qc_maps = {
        "reslice-batch-C": load_qc("data/reslice_batch_c_qc_r34.json", "b"),
        "resliced-pilot": load_qc("data/phase3_pilot_v2_qc.json", "p"),
        "ocr": load_qc("data/pac_qc_v2.json", "pac"),
    }
    verdict_mismatch = []
    verdict_tally = Counter()
    for rel, ind in independent.items():
        v = ind["qc_verdict"]
        if v is None:
            continue
        verdict_tally[(rel.split("/")[1] if "/" in rel else "?", v)] += 1
        for corpus, qm in qc_maps.items():
            name = Path(rel).name
            if corpus in rel and name in qm and qm[name] != v:
                verdict_mismatch.append(
                    f"{rel}: preflight {v} != 已提交 QC {qm[name]}")
    if verdict_mismatch:
        findings += verdict_mismatch

    # ---- 具名数字声明重测 ----
    def man_of(sub):
        hits = [r for r in rows_by_file if sub in r]
        assert len(hits) == 1, f"{sub} 命中 {len(hits)} 个文件"
        md = ROOT / hits[0]
        return json.loads(md.with_suffix(".manifest.json")
                          .read_text(encoding="utf-8"))

    c09 = man_of("c09-01")
    named["c09-01"] = {
        "units": len(c09["units"]),
        "printed_nonnull": sum(1 for u in c09["units"]
                               if u.get("printed_number")),
    }
    c01 = man_of("c01-02")
    named["c01-02"] = {
        "units": len(c01["units"]),
        "printed_nonnull": sum(1 for u in c01["units"]
                               if u.get("printed_number")),
    }
    # R19 答案表声明:answer_lines 单行且该行含 <table
    tab_files, tab_units = set(), 0
    for rel, row in rows_by_file.items():
        if row.get("identity_version", 1) < 2:
            continue
        md = ROOT / rel
        man = json.loads(md.with_suffix(".manifest.json")
                         .read_text(encoding="utf-8"))
        src = Path(man.get("source_file") or "")
        if not src.exists():
            continue
        lines = strip_meta(src.read_text(encoding="utf-8",
                                         errors="replace")).splitlines()
        for u in man.get("units") or []:
            rg = u.get("answer_lines")
            if (isinstance(rg, list) and len(rg) == 2 and rg[0] == rg[1]
                    and 1 <= rg[0] <= len(lines)
                    and "<table" in lines[rg[0] - 1]):
                tab_units += 1
                tab_files.add(rel)
    named["r19_answer_table"] = {"files": len(tab_files), "units": tab_units}

    report = {
        "n_files": len(rows_by_file),
        "mismatch_preflight_vs_independent": findings,
        "qc_verdict_tally": {f"{c}/{v}": n for (c, v), n
                             in sorted(verdict_tally.items())},
        "basis_dist": dict(dist.most_common()),
        "prov_dist": dict(prov_dist.most_common()),
        "batchc_units": batchc_units,
        "named_claims": named,
    }
    Path(OUT).write_text(json.dumps(report, ensure_ascii=False,
                                    indent=1) + "\n",
                         encoding="utf-8", newline="")
    print(f"files={len(rows_by_file)} findings={len(findings)} "
          f"basis={dict(dist)} prov={dict(prov_dist)}")
    print(f"batch-C units={batchc_units}")
    print(f"named={json.dumps(named, ensure_ascii=False)}")
    print(f"verdict_tally={dict(verdict_tally)}")


if __name__ == "__main__":
    main()

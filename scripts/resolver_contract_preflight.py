r"""Resolver 消费契约生产侧前置条件预检(R48)。

对 batch-C + pilot + PAC 三组产物逐份检查 resolver 输入契约
(resolver_contract_design.md §2/§3)的**生产侧前置条件**——即:
当 resolver 实现存在时,这些产物是否满足契约要求的输入形态。

十条检查(全部复用生产共用实现,不重新发明):
  pc1  identity v2 在册(C-IN-1:pipeline 原生 v1 不可直接消费)
  pc2  check_identity fails == 0(生产共用校验,非预检私有规则)
  pc3  check_identity reviews == 0(有 review 即须走 PENDING_REVIEW 通道)
  pc4  QC verdict 可计算(C-IN-2:消费 verdict 而非产物存在)
  pc5  basis ∈ 6 值封闭词表(schema violation,不进 FAIL 裁决——R47 修订)
  pc6  printed_provenance ∈ {source_line, migration_report, unknown}
  pc7  provenance 与 printed_number 反伪造一致性
       (unknown → printed 必空;source_line → printed 必非空)
  pc8  section_ref 可解析到 sections(C-IN-4 身份键)
  pc9  行号区间界内(stem/options/material/questions/answer/explanation)
  pc10 源文件在位(行号锚定的前提)

语料不在本 checkout 时干净 skip(快照 JSON 已提交,语料存在性独立验证)。
用法: python scripts/resolver_contract_preflight.py
输出: data/resolver_contract_preflight.json
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import question_identity as qi  # noqa: E402
import reslice_qc as qc  # noqa: E402
from fix_bug22_renumber import strip_meta  # noqa: E402

OUT = ROOT / "data/resolver_contract_preflight.json"
DIRS = [ROOT / "Ocr-markdown/reslice-batch-C",
        ROOT / "Ocr-markdown/resliced-pilot",
        ROOT / "Ocr-markdown/reslice-pac-annotated/reslice-pac/ocr"]

BASIS_VOCAB = {"answer_key", "shift", "keep", "printed_as_is",
               "explicit", "unverified"}
PROV_VOCAB = {"source_line", "migration_report", "unknown"}
SPAN_KEYS = ("stem_lines", "options_lines", "material_lines",
             "questions_lines", "answer_lines", "explanation_lines")


def check_manifest(md_path: Path):
    """返回 (findings, meta)。findings 为 pcN 前缀字符串列表。"""
    findings = []
    man_path = md_path.with_suffix(".manifest.json")
    if not man_path.exists():
        return ["pc0 manifest 缺失"], {}
    man = json.loads(man_path.read_text(encoding="utf-8"))
    meta = {"identity_version": man.get("identity_version") or 1,
            "units": len(man.get("units") or [])}

    src = Path(man.get("source_file") or "")
    if not src.exists():
        return findings + [f"pc10 源文件缺失: {src}"], meta
    lines = strip_meta(src.read_text(encoding="utf-8",
                                     errors="replace")).splitlines()
    n = len(lines)
    meta["src_lines"] = n

    # pc1: v2 在册(v1 文件如实记录,后续检查跳过——v1 不是 resolver 输入)
    if meta["identity_version"] < 2:
        findings.append("pc1 非 identity v2(pipeline 原生 v1,须经回填;"
                        "resolver 只消费 v2)")
        return findings, meta

    # pc2/pc3: 生产共用身份校验
    fails, reviews = qi.check_identity(man, n, lines)
    findings += [f"pc2 identity fail: {f}" for f in fails]
    findings += [f"pc3 identity pending: {r}" for r in reviews]

    # pc4: QC verdict 可计算(FAIL 是合法输入态,不可计算才是违反契约)
    try:
        q = qc.check(md_path)
        meta["qc_verdict"] = q.get("verdict")
    except Exception as e:  # noqa: BLE001 —— 预检如实记录任何计算失败
        findings.append(f"pc4 QC verdict 不可计算: {e!r}")
        meta["qc_verdict"] = None

    # pc5-pc9: 单元字段 schema 与一致性
    sec_ids = {s.get("id") for s in man.get("sections") or []}
    for u in man.get("units") or []:
        uid = u.get("unit_id")
        b = u.get("basis")
        if b not in BASIS_VOCAB:
            findings.append(f"pc5 basis schema violation: {uid} basis={b!r}")
        p = u.get("printed_provenance")
        if p not in PROV_VOCAB:
            findings.append(
                f"pc6 printed_provenance schema violation: {uid} prov={p!r}")
        pn = u.get("printed_number")
        if p == "unknown" and pn:
            findings.append(
                f"pc7 provenance=unknown 但 printed_number 非空: {uid}={pn!r}")
        if p == "source_line" and not pn:
            findings.append(
                f"pc7 provenance=source_line 但 printed_number 为空: {uid}")
        sref = u.get("section_ref")
        if sref and sref not in sec_ids:
            findings.append(f"pc8 section_ref 悬空: {uid} -> {sref!r}")
        for k in SPAN_KEYS:
            rg = u.get(k)
            if (isinstance(rg, list) and len(rg) == 2
                    and all(isinstance(x, int) for x in rg)):
                a, b2 = rg
                if not (1 <= a <= b2 <= max(n, 1)):
                    findings.append(
                        f"pc9 行号区间越界: {uid} {k}={rg} 源行数={n}")
    return findings, meta


def run_dirs(dirs):
    rows = []
    for d in dirs:
        if not d.exists():
            continue
        for md in sorted(d.rglob("*.md")):
            if md.with_suffix(".manifest.json").exists():
                f, meta = check_manifest(md)
                rows.append({"file": str(md.relative_to(ROOT)),
                             "corpus": d.name, "findings": f, **meta})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    rows = run_dirs(DIRS)
    tally = Counter()
    for r in rows:
        for f in r["findings"]:
            tally[f.split()[0]] += 1
    v1 = [r["file"] for r in rows if r.get("identity_version", 1) < 2]
    verdicts = Counter(r.get("qc_verdict") for r in rows
                       if r.get("qc_verdict"))
    report = {
        "contract": "resolver_contract_design.md v0.1 (R48)",
        "n_files": len(rows),
        "tally": dict(sorted(tally.items())),
        "v1_files": v1,
        "qc_verdicts": dict(verdicts),
        "rows": rows,
    }
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False,
                                         indent=1) + "\n",
                              encoding="utf-8", newline="")
    n_clean = sum(1 for r in rows if not r["findings"])
    print(f"preflight: {len(rows)} 份,0 findings {n_clean} 份,"
          f"v1 {len(v1)} 份,tally={dict(tally)}")


if __name__ == "__main__":
    main()

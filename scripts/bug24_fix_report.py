# -*- coding: utf-8 -*-
"""BUG-24 修复报告(R37):before/after 快照 + QC 裁决集逐文件 NEW-OLD 比对。

用户冻结的 B24 验收 §6:修复不得只看 pytest,必须比对产物。本工具产出
data/bug24_fix_report.json:
  - 哪些 manifest 字节变化(sha256);
  - 每个变化文件的 sections 差异(增/减/改)与单元 section_ref 迁移数;
  - check_identity fails/reviews 的前后差异(理由级);
  - QC 裁决集翻转(必须为 0:修复不产生非法 PASS,也不误杀既有 PASS)。
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(tag):
    return json.loads(
        (ROOT / f"data/bug24_locator_snapshot_{tag}.json").read_text(encoding="utf-8"))["files"]


def qc_verdicts(name):
    data = json.loads((ROOT / f"data/{name}").read_text(encoding="utf-8"))
    return {Path(r["file"]).name: r["verdict"] for r in data}


def sec_key(s):
    return (s.get("id"), s.get("ordinal"), s.get("start_line"),
            s.get("end_line"), s.get("title"), bool(s.get("derived")))


def main():
    before, after = load("before"), load("after")
    assert set(before) == set(after), "快照文件集不一致"

    changed, report_files = [], {}
    for rel in sorted(before):
        b, a = before[rel], after[rel]
        if b["manifest_sha256"] == a["manifest_sha256"]:
            continue
        changed.append(rel)
        bsec = {sec_key(s) for s in b["sections"]}
        asec = {sec_key(s) for s in a["sections"]}
        unit_moves = [
            {"i": ub["i"], "unit_id": ub["unit_id"],
             "from": ub["section_ref"], "to": ua["section_ref"]}
            for ub, ua in zip(b["units"], a["units"])
            if ub["section_ref"] != ua["section_ref"]]
        report_files[rel] = {
            "identity_version": [b["identity_version"], a["identity_version"]],
            "sections_added": [list(x) for x in sorted(asec - bsec)],
            "sections_removed": [list(x) for x in sorted(bsec - asec)],
            "unit_section_moves": len(unit_moves),
            "unit_moves_sample": unit_moves[:6],
            "fails_before": b["fails"], "fails_after": a["fails"],
            "reviews_before": b["reviews"], "reviews_after": a["reviews"]}

    flips = {}
    for tag_pair, qc_pair in ((("bug24_before_batch_c_qc.json",
                               "bug24_after_batch_c_qc.json"), "batch-C"),
                              (("bug24_before_pilot_qc.json",
                                "bug24_after_pilot_qc.json"), "pilot")):
        vb, va = qc_verdicts(tag_pair[0]), qc_verdicts(tag_pair[1])
        assert set(vb) == set(va), f"{qc_pair} QC 文件集不一致"
        f = {k: [vb[k], va[k]] for k in vb if vb[k] != va[k]}
        flips[qc_pair] = {"verdict_flips": f,
                          "before": {v: list(vb.values()).count(v)
                                     for v in sorted(set(vb.values()))},
                          "after": {v: list(va.values()).count(v)
                                    for v in sorted(set(va.values()))}}

    out = {"changed_manifests": len(changed), "files": report_files,
           "qc_verdict_comparison": flips}
    (ROOT / "data/bug24_fix_report.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"changed manifests: {len(changed)}")
    for rel in changed:
        f = report_files[rel]
        print(f"  {rel}")
        print(f"    sections +{len(f['sections_added'])}/-{len(f['sections_removed'])},"
              f" 单元移节 {f['unit_section_moves']},"
              f" fails {len(f['fails_before'])}→{len(f['fails_after'])}")
    for k, v in flips.items():
        print(f"{k}: flips={v['verdict_flips']} before={v['before']} after={v['after']}")


if __name__ == "__main__":
    main()

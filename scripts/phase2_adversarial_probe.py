"""Phase 2 设计对抗性审查探针(R33)。

对 question_identity_design.md 的每条可测声称做真实产物测量,不做推测:
  A1 section 字段覆盖率:50 份 batch-C manifest 中带 section 的单元占比
     (设计 §2 scoped identity 的现实生效面)
  A2 scoped 不变量普查:真实 50 份产物 (section,题号) 是否唯一(设计 §5-1)
  A3 BUG-22 回迁突变:把 R31 迁移的 8 份产物题号全部回退到 old 值、保留
     section,再跑生产 C13——检验 scoped 守卫能否拦住 BUG-22 原始形态
     (选择题 1-9 vs 非选择题 1-9 是跨分节重号)。对照组:同样回退但删除
     section 字段(全卷口径),应被拦住。
  A4 静默降级:删除 section 后生产 QC 是否产生任何"缺 section"显式告警
     (设计 §5-6 不变量)
  A5 printed_number 回填证据覆盖:migration report 覆盖的文件/单元 vs 全量
     (设计 §3 兼容性策略的现实覆盖率)
  A6 unit_id 重复普查(设计 §1.3 "unit_id 不可作键"声称)
  A7 SectionLocator 字段普查:manifest 是否含 ordinal/span 类字段
     (设计 §2 的可实现性)
输出 data/phase2_adversarial_review.json(UTF-8, LF)。
"""
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reslice_qc  # noqa: E402  生产 QC,突变测试必须打真代码

ROOT = Path(r"D:\Project\Papers")
BATCH = ROOT / "Ocr-markdown/reslice-batch-C"
MIG = ROOT / "data/bug22_migration_report.json"
OUT = Path(r"D:\Project\Papers\data\phase2_adversarial_review.json")
if len(sys.argv) > 1:
    OUT = Path(sys.argv[1])


def manifests():
    for p in sorted(BATCH.rglob("*.manifest.json")):
        yield p, json.loads(p.read_text(encoding="utf-8"))


def run_check_in_tmp(man, orig_md):
    """把突变后的 manifest 与切片/批注复制到工作区临时目录,跑生产 check()。

    沙箱不允许在新建子目录内写文件(只放行既有目录),故在预建目录内
    用 uuid 前缀平铺,check() 依据 md stem 派生 manifest/annotated 路径。
    """
    import uuid
    base = ROOT / "data/_p2adv_tmp"
    base.mkdir(parents=True, exist_ok=True)
    tag = uuid.uuid4().hex[:8]
    md_dst = base / f"{tag}__{orig_md.name}"
    shutil.copy2(orig_md, md_dst)
    ann = orig_md.with_name(orig_md.stem + ".annotated.md")
    shutil.copy2(ann, base / f"{tag}__{ann.name}")
    mf = base / f"{tag}__{orig_md.stem}.manifest.json"
    mf.write_text(json.dumps(man, ensure_ascii=False, indent=1),
                  encoding="utf-8", newline="\n")
    try:
        return reslice_qc.check(md_dst)
    finally:
        for p in (md_dst, base / f"{tag}__{ann.name}", mf):
            p.unlink(missing_ok=True)


def main():
    report = {"generated_by": "scripts/phase2_adversarial_probe.py",
              "design_doc": "question_identity_design.md", "probes": {}}

    all_mans = list(manifests())
    report["manifest_count"] = len(all_mans)

    # ---- A1 section 覆盖率 ----
    a1 = []
    tot_u = tot_sec = 0
    for p, man in all_mans:
        us = man.get("units") or []
        ns = sum(1 for u in us if (u.get("section") or "").strip())
        a1.append({"file": str(p.relative_to(ROOT)), "units": len(us), "with_section": ns})
        tot_u += len(us)
        tot_sec += ns
    report["probes"]["A1_section_coverage"] = {
        "files": len(a1), "units_total": tot_u, "units_with_section": tot_sec,
        "pct": round(100 * tot_sec / tot_u, 1) if tot_u else 0,
        "files_fully_covered": sum(1 for x in a1 if x["units"] == x["with_section"]),
        "files_zero_section": sum(1 for x in a1 if x["with_section"] == 0)}

    # ---- A2 scoped 不变量普查(真实数据;v2 按 section_ref,同名标题
    #      occurrence 由 locator 区分——title 仅展示,不得作身份键) ----
    viol = []
    for p, man in all_mans:
        ident = Counter()
        for u in man.get("units") or []:
            sec = (u.get("section_ref") or u.get("section") or "")
            for n in (u.get("question_numbers") or []):
                ident[(sec, n)] += 1
        d = sorted(str(k) for k, c in ident.items() if c > 1)
        if d:
            viol.append({"file": str(p.relative_to(ROOT)), "dups": d[:10]})
    report["probes"]["A2_scoped_invariant_real"] = {"violations": viol, "pass": not viol}

    # ---- A3 BUG-22 回迁突变(8 份迁移产物) ----
    mig = json.loads(MIG.read_text(encoding="utf-8"))
    a3 = []
    for f in mig["files"]:
        if not f.get("changes"):
            continue
        md_path = Path(f["file"])
        man = json.loads(md_path.with_suffix(".manifest.json").read_text(encoding="utf-8"))
        # 回退:unit_id + current==new 双条件定位(R31 教训:unit_id 可能重复,
        # 题号必须匹配当前值才安全),改回 old
        n_reverted = 0
        for u in man["units"]:
            for ch in f["changes"]:
                if u.get("unit_id") == ch["unit_id"] and u.get("question_numbers") == ch["new"]:
                    u["question_numbers"] = list(ch["old"])
                    n_reverted += 1
        assert n_reverted == len(f["changes"]), (md_path.name, n_reverted, len(f["changes"]))
        with_sec = run_check_in_tmp(man, md_path)
        # 对照组:同样回退 + 删除 section/section_ref
        man2 = json.loads(json.dumps(man))
        for u in man2["units"]:
            u.pop("section", None)
            u.pop("section_ref", None)
        no_sec = run_check_in_tmp(man2, md_path)
        a3.append({
            "file": str(md_path.relative_to(ROOT)),
            "units_reverted": n_reverted,
            "mode": sorted({c["mode"] for c in f["changes"]}),
            "c13_with_section": [i for i in with_sec["issues"] if i.startswith("C13")],
            "c13_without_section": [i for i in no_sec["issues"] if i.startswith("C13")],
        })
    report["probes"]["A3_bug22_regression_mutation"] = {
        "files": a3,
        "caught_with_section": sum(1 for x in a3 if x["c13_with_section"]),
        "caught_without_section": sum(1 for x in a3 if x["c13_without_section"]),
        "total": len(a3)}

    # ---- A4 静默降级:无 section 时是否有显式告警 ----
    a4 = []
    for p, man in all_mans:
        if not any((u.get("section") or "").strip() for u in man.get("units") or []):
            continue
        md_path = p.with_name(p.name[: -len(".manifest.json")] + ".md")
        man2 = json.loads(json.dumps(man))
        for u in man2["units"]:
            u.pop("section", None)
            u.pop("section_ref", None)
        res = run_check_in_tmp(man2, md_path)
        warn = [i for i in (res["issues"] + (res.get("review_notes") or []))
                if re.search(r"section|scope_missing|C14|分节|缺.*节", i)]
        a4.append({"file": str(p.relative_to(ROOT)),
                   "issues": len(res["issues"]), "section_warnings": warn})
        if len(a4) >= 8:
            break
    report["probes"]["A4_silent_degradation"] = {
        "files_tested": len(a4),
        "files_with_explicit_warning": sum(1 for x in a4 if x["section_warnings"]),
        "detail": a4}

    # ---- A5 printed_number 回填证据覆盖 ----
    mig_files = {f["file"] for f in mig["files"] if f.get("changes")}
    mig_units = sum(len(f["changes"]) for f in mig["files"])
    report["probes"]["A5_printed_provenance"] = {
        "files_with_changes": len(mig_files), "files_total": len(all_mans),
        "units_with_old_value": mig_units, "units_total": tot_u,
        "pct_units": round(100 * mig_units / tot_u, 1)}

    # ---- A6 unit_id 重复普查 ----
    a6 = []
    for p, man in all_mans:
        ids = [u.get("unit_id") for u in man.get("units") or []]
        d = sorted(k for k, c in Counter(ids).items() if c > 1)
        if d:
            a6.append({"file": str(p.relative_to(ROOT)),
                       "dup_ids": d[:5], "dup_units": sum(c for c in Counter(ids).values() if c > 1)})
    report["probes"]["A6_unit_id_duplication"] = {
        "files_with_dup_unit_id": len(a6), "files_total": len(all_mans), "detail": a6[:10]}

    # ---- A7 SectionLocator 字段普查 ----
    fields = Counter()
    for p, man in all_mans:
        for u in man.get("units") or []:
            fields.update(u.keys())
    locator_like = {k: v for k, v in fields.items()
                    if re.search(r"ordinal|span|start_line|end_line|section_", k)}
    report["probes"]["A7_section_locator_fields"] = {
        "all_unit_fields": dict(fields.most_common()),
        "locator_like_fields": locator_like,
        "has_locator": bool(locator_like)}

    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                   encoding="utf-8", newline="\n")
    print(f"written {OUT}")


if __name__ == "__main__":
    main()

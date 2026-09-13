r"""R49 对抗性审查(b):pc0–pc10 全检查族变异攻击(R48 只对 pc1/5/7 做过 CI)。

纪律(R46 补记):变异只在 .pytest_work 整目录拷贝上做,原件零触碰;
控制组(零变异拷贝)必须与原件 findings/verdict 完全一致(拷贝保真)。
每条变异注入一个已知缺陷形态,期望恰好命中对应 pcN。

语料依赖(本地跑;corpus gitignored)。
输出: data/r48_audit_pc_mutation.json
用法: python scripts/r48_audit_pc_mutation.py
"""
import hashlib
import json
import shutil
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from resolver_contract_preflight import check_manifest  # noqa: E402

PREFLIGHT = ROOT / "data/resolver_contract_preflight.json"
WORK = ROOT / ".pytest_work"
OUT = ROOT / "data/r48_audit_pc_mutation.json"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def stage(md_rel):
    """整组拷贝 annotated md + manifest + 源 md,manifest.source_file 改指拷贝。"""
    src_md = ROOT / md_rel
    man_path = src_md.with_suffix(".manifest.json")
    man = json.loads(man_path.read_text(encoding="utf-8"))
    src = Path(man["source_file"])
    d = WORK / f"r48_mut_{uuid.uuid4().hex[:8]}"
    d.mkdir(parents=True)
    md_c = d / src_md.name
    man_c = d / man_path.name
    # R49 教训:PAC 源 md 与产物 md 同名(pac-c01-01.md),直接拷同名会
    # 自我覆盖(控制组保真检查抓到)——源拷贝必须改名隔离。
    src_c = d / f"src_{src.name}"
    shutil.copy2(src_md, md_c)
    shutil.copy2(src, src_c)
    ann = src_md.with_suffix(".annotated.md")  # C8 依赖锚点批注版兄弟件
    if ann.exists():
        shutil.copy2(ann, d / ann.name)
    man["source_file"] = str(src_c)
    man_c.write_text(json.dumps(man, ensure_ascii=False, indent=1),
                     encoding="utf-8", newline="")
    return d, md_c, man_c, src_c, sha(man_path), sha(src_md)


def fresh(md_rel):
    return stage(md_rel)


def write_man(man_c, man):
    man_c.write_text(json.dumps(man, ensure_ascii=False, indent=1),
                     encoding="utf-8", newline="")


def pcs(findings):
    return sorted({f.split()[0] for f in findings})


def main():
    pf = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    # 选一份 findings 为空的 PAC 样本(控制组基线干净)
    row = next(r for r in pf["rows"]
               if r["corpus"] == "ocr" and not r["findings"]
               and r.get("qc_verdict") == "PASS")
    md_rel = row["file"]

    results = []
    orig_man = (ROOT / md_rel).with_suffix(".manifest.json")
    orig_man_sha = sha(orig_man)

    # ---- 控制组:零变异拷贝必须复现原件结论 ----
    d, md_c, man_c, src_c, _, _ = fresh(md_rel)
    f, meta = check_manifest(md_c)
    results.append({"m": "control", "expected": [], "got": pcs(f),
                    "ok": pcs(f) == [] and meta.get("qc_verdict") == "PASS",
                    "qc": meta.get("qc_verdict")})
    shutil.rmtree(d, ignore_errors=True)

    def run(tag, mut, expected):
        d, md_c, man_c, src_c, _, _ = fresh(md_rel)
        man = json.loads(man_c.read_text(encoding="utf-8"))
        man, extra = mut(man, d, src_c)
        if extra is None:  # manifest 已删除(pc0)
            f, meta = check_manifest(md_c)
        else:
            write_man(man_c, man)
            f, meta = check_manifest(md_c)
        got = pcs(f)
        results.append({"m": tag, "expected": expected, "got": got,
                        "ok": got == expected, "raw": f[:4]})
        shutil.rmtree(d, ignore_errors=True)

    # M0 pc0:manifest 缺失
    def m0(man, d, src_c):
        (d / (Path(md_rel).with_suffix(".manifest.json").name)).unlink()
        return man, None
    run("M0_manifest缺失", m0, ["pc0"])

    # M1 pc1:剥离 v2 身份
    def m1(man, d, src_c):
        man.pop("identity_version", None)
        man.pop("sections", None)
        for u in man["units"]:
            u.pop("section_ref", None)
        return man, True
    run("M1_v1输入", m1, ["pc1"])

    # M2 pc2:跨分节非 keep 重号(BUG-22 原型)
    def m2(man, d, src_c):
        us = man["units"]
        a = next(u for u in us if u.get("section_ref"))
        b = next(u for u in us
                 if u.get("section_ref") != a["section_ref"]
                 and u.get("basis") != "keep"
                 and u.get("unit_id") != a.get("unit_id"))
        if a.get("basis") == "keep":
            a["basis"] = "printed_as_is"
        b["question_numbers"] = list(a["question_numbers"])
        return man, True
    run("M2_跨节非keep重号", m2, ["pc2"])

    # M3 pc3:跨节重号下 keep 无证据 → PENDING_REVIEW
    # (实读边界:孤立 keep 无豁免效应不触发复核(len(own)<2 continue),
    #  故必须构造重号场景让 keep 豁免真正被使用)
    def m3(man, d, src_c):
        us = man["units"]
        a = next(u for u in us if u.get("section_ref")
                 and u.get("basis") != "keep")
        b = next(u for u in us
                 if u.get("section_ref") != a["section_ref"]
                 and u.get("unit_id") != a.get("unit_id"))
        b["question_numbers"] = list(a["question_numbers"])
        b["basis"] = "keep"
        b["basis_evidence"] = None
        return man, True
    run("M3_keep无证据", m3, ["pc3"])

    # M4 pc4:manifest 无 units → qc.check 崩 → verdict 不可计算
    def m4(man, d, src_c):
        man.pop("units", None)
        return man, True
    run("M4_QC不可计算", m4, ["pc4"])

    # M5 pc5:非法 basis(大小写漂移)
    def m5(man, d, src_c):
        man["units"][0]["basis"] = "Explicit"
        return man, True
    run("M5_basis大小写", m5, ["pc5"])

    # M6 pc6:非法 provenance
    def m6(man, d, src_c):
        man["units"][0]["printed_provenance"] = "source"
        return man, True
    run("M6_provenance非法", m6, ["pc6"])

    # M7 pc7:provenance=unknown 却带 printed(伪造 Source Fact)
    def m7(man, d, src_c):
        u = next(u for u in man["units"] if u.get("printed_number"))
        u["printed_provenance"] = "unknown"
        return man, True
    run("M7_伪造printed", m7, ["pc7"])

    # M8 pc8:section_ref 悬空
    def m8(man, d, src_c):
        man["units"][0]["section_ref"] = "sec-999-dangling"
        return man, True
    run("M8_section悬空", m8, ["pc8"])

    # M9 pc9:行号区间越界
    def m9(man, d, src_c):
        u = next(u for u in man["units"] if u.get("stem_lines"))
        u["stem_lines"] = [u["stem_lines"][0], 99999]
        return man, True
    run("M9_span越界", m9, ["pc9"])

    # M10 pc10:源文件缺失
    def m10(man, d, src_c):
        man["source_file"] = str(d / "nonexistent_source.md")
        return man, True
    run("M10_源缺失", m10, ["pc10"])

    assert sha(orig_man) == orig_man_sha, "原件 manifest 被变异触碰!"
    ok = all(r["ok"] for r in results)
    Path(OUT).write_text(json.dumps(
        {"sample": md_rel, "all_ok": ok, "results": results},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="")
    for r in results:
        print(f'{r["m"]}: expected={r["expected"]} got={r["got"]} '
              f'{"OK" if r["ok"] else "**MISS**"}')
    print("all_ok =", ok)


if __name__ == "__main__":
    main()

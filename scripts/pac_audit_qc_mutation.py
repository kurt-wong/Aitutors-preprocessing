r"""PAC 对抗性审查 B 项:QC(reslice_qc.check)变异灵敏度测试(R46)。

方法:对真实 PAC 产物做整目录拷贝(绝不触碰原件),每条变异单独施加:
  1) control:无变异拷贝必须逐字复现原 verdict+issues(证明拷贝保真);
  2) 变异:注入一个已知缺陷,断言期望的检查码必须出现在 issues/review_notes。
任何"注入缺陷但 QC 仍 PASS"= QC 盲区,如实入 findings,不找补。

覆盖检查族:C1 C2 C3 C4 C5 C6 C7 C8 C9 C10 C11 C12 C13 C14。

用法: python scripts/pac_audit_qc_mutation.py
输出: data/pac_audit_qc_mutation.json
"""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import reslice_qc  # noqa: E402

ANN_DIR = ROOT / "Ocr-markdown/reslice-pac-annotated/reslice-pac/ocr"
WORK = ROOT / ".pytest_work/pac_audit_mut"
OUT = ROOT / "data/pac_audit_qc_mutation.json"

SID = "pac-c01-01"          # 基线 PASS 卷(30 独立单元)
SID_COMPOSITE = "pac-c13-01"  # 复合题卷(C4/C12 用)


def stage(sid):
    """整目录拷贝一份产物 + 源 md,manifest.source_file 重写到拷贝。"""
    d = WORK / sid
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    for ext in (".md", ".manifest.json", ".annotated.md"):
        shutil.copy2(ANN_DIR / f"{sid}{ext}", d / f"{sid}{ext}")
    man = json.loads((d / f"{sid}.manifest.json").read_text(encoding="utf-8"))
    src = Path(man["source_file"])
    src_copy = d / f"{sid}.src.md"
    shutil.copy2(src, src_copy)
    man["source_file"] = str(src_copy)
    (d / f"{sid}.manifest.json").write_text(
        json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8", newline="")
    return d, man, src_copy


def run_check(d, sid):
    return reslice_qc.check(d / f"{sid}.md")


def save_man(d, sid, man):
    (d / f"{sid}.manifest.json").write_text(
        json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8", newline="")


def has_code(res, code):
    return any(i.startswith(code) for i in res["issues"]) or \
           any(i.startswith(code) for i in res.get("review_notes") or [])


def main():
    results = []

    def record(name, sid, expect_code, res, expect_verdict=None):
        ok = has_code(res, expect_code)
        vok = True
        if expect_verdict:
            vok = res["verdict"] == expect_verdict
        results.append({
            "mutation": name, "sample": sid, "expect": expect_code,
            "got_issues": res["issues"], "got_reviews": res.get("review_notes"),
            "verdict": res["verdict"], "ok": ok and vok})
        status = "OK " if (ok and vok) else "FAIL"
        print(f"[{status}] {name}: expect={expect_code} verdict={res['verdict']}")
        if not (ok and vok):
            for i in res["issues"]:
                print("      !", i)

    # ── control:拷贝保真 ──────────────────────────────────────────────────
    d, man, src = stage(SID)
    base = run_check(d, SID)
    orig = json.loads((ROOT / "data/pac_qc_v2.json").read_text(encoding="utf-8"))
    orig_r = next(r for r in orig if Path(r["file"]).name == f"{SID}.md")
    results.append({
        "mutation": "control(拷贝零变异)", "sample": SID, "expect": "复现原结果",
        "got_issues": base["issues"], "verdict": base["verdict"],
        "ok": base["issues"] == orig_r["issues"] and base["verdict"] == orig_r["verdict"]})
    print(f"[{'OK ' if results[-1]['ok'] else 'FAIL'}] control: verdict={base['verdict']}")
    if not results[-1]["ok"]:
        print("      原:", orig_r["issues"], orig_r["verdict"])
        print("      拷:", base["issues"], base["verdict"])

    # ── C1:删一个“题干区结束”标记 ─────────────────────────────────────────
    d, man, src = stage(SID)
    md = d / f"{SID}.md"
    t = md.read_text(encoding="utf-8")
    t = t.replace("“题干区结束”", "", 1)
    md.write_text(t, encoding="utf-8", newline="")
    record("M-C1 标记破坏", SID, "C1", run_check(d, SID), "FAIL")

    # ── C2:manifest 抹掉题号 5 ────────────────────────────────────────────
    d, man, src = stage(SID)
    u5 = next(u for u in man["units"] if 5 in (u.get("question_numbers") or []))
    u5["question_numbers"] = [999]
    save_man(d, SID, man)
    record("M-C2 题号丢失(5→999)", SID, "C2", run_check(d, SID), "FAIL")

    # ── C3:清空第一个答案区 ──────────────────────────────────────────────
    d, man, src = stage(SID)
    md = d / f"{SID}.md"
    t = md.read_text(encoding="utf-8")
    t = t.replace("“答案区开始”", "“答案区开始”", 1)
    i = t.index("“答案区开始”") + len("“答案区开始”")
    j = t.index("“答案区结束”", i)
    t = t[:i] + "\n" + t[j:]
    md.write_text(t, encoding="utf-8", newline="")
    record("M-C3 答案区清空", SID, "C3", run_check(d, SID), "FAIL")

    # ── C5:源文件追加未覆盖图片行 ─────────────────────────────────────────
    d, man, src = stage(SID)
    with open(src, "a", encoding="utf-8", newline="") as f:
        f.write('\n<img src="mgs/mutation_injected.jpg">\n')
    record("M-C5 图片行未覆盖", SID, "C5", run_check(d, SID), "FAIL")

    # ── C6:源文件追加未覆盖表格行 ─────────────────────────────────────────
    d, man, src = stage(SID)
    with open(src, "a", encoding="utf-8", newline="") as f:
        f.write("\n| 变异注入 | 表格行 |\n")
    record("M-C6 表格行未覆盖", SID, "C6", run_check(d, SID), "FAIL")

    # ── C7:输出 md 注入卷面指令 ───────────────────────────────────────────
    d, man, src = stage(SID)
    md = d / f"{SID}.md"
    t = md.read_text(encoding="utf-8")
    md.write_text(t + "\n考试时间 90 分钟\n", encoding="utf-8", newline="")
    record("M-C7 卷面指令混入", SID, "C7", run_check(d, SID), "FAIL")

    # ── C8:annotated 加一行 ──────────────────────────────────────────────
    d, man, src = stage(SID)
    ann = d / f"{SID}.annotated.md"
    ann.write_text(ann.read_text(encoding="utf-8") + "\n变异行\n",
                   encoding="utf-8", newline="")
    record("M-C8 锚点版与源不一致", SID, "C8", run_check(d, SID), "FAIL")

    # ── C10:annotated 删一个 META:end ────────────────────────────────────
    d, man, src = stage(SID)
    ann = d / f"{SID}.annotated.md"
    t = ann.read_text(encoding="utf-8")
    t2 = re.sub(r"<!--\s*META:\w+:end[^>]*-->\n?", "", t, count=1)
    assert t2 != t, "未找到 META:end 行"
    ann.write_text(t2, encoding="utf-8", newline="")
    record("M-C10 锚点不配对", SID, "C10", run_check(d, SID), "FAIL")

    # ── C11:详解首行指向题干首行(复述) ───────────────────────────────────
    d, man, src = stage(SID)
    u = next(u for u in man["units"]
             if isinstance(u.get("explanation_lines"), list)
             and isinstance(u.get("stem_lines"), list))
    u["explanation_lines"] = [u["stem_lines"][0], u["stem_lines"][0]]
    save_man(d, SID, man)
    record("M-C11 详解区原题复述", SID, "C11", run_check(d, SID), "FAIL")

    # ── C13:同分节 canonical 重复 ─────────────────────────────────────────
    d, man, src = stage(SID)
    u1 = man["units"][0]
    dup = dict(u1)
    dup["unit_id"] = "Q1-MUTDUP"
    man["units"].append(dup)
    save_man(d, SID, man)
    record("M-C13 同分节重号", SID, "C13", run_check(d, SID), "FAIL")

    # ── C13b:跨分节两个非 keep 重号 ───────────────────────────────────────
    d, man, src = stage(SID)
    u1, u2 = man["units"][0], man["units"][1]
    u2["question_numbers"] = list(u1["question_numbers"])
    u2["basis"] = "answer_key"
    u1["basis"] = "answer_key"
    save_man(d, SID, man)
    record("M-C13b 跨分节双非keep重号", SID, "C13", run_check(d, SID), "FAIL")

    # ── C14:单元缺 section_ref(应 PENDING_REVIEW 不得静默) ────────────────
    d, man, src = stage(SID)
    man["units"][0]["section_ref"] = None
    save_man(d, SID, man)
    res = run_check(d, SID)
    results.append({"mutation": "M-C14 缺 section_ref", "sample": SID,
                    "expect": "C14 review + verdict PENDING_REVIEW",
                    "got_issues": res["issues"],
                    "got_reviews": res.get("review_notes"),
                    "verdict": res["verdict"],
                    "ok": has_code(res, "C14") and res["verdict"] == "PENDING_REVIEW"})
    print(f"[{'OK ' if results[-1]['ok'] else 'FAIL'}] M-C14: verdict={res['verdict']}")
    if not results[-1]["ok"]:
        for i in res["issues"]:
            print("      !", i)
        for i in res.get("review_notes") or []:
            print("      ?", i)

    # ── C9:单元区间吞入试卷结构行 ─────────────────────────────────────────
    d, man, src = stage(SID)
    lines = src.read_text(encoding="utf-8", errors="replace").splitlines()
    hit = next((i for i, ln in enumerate(lines, 1)
                if reslice_qc.PAPER_LINE.match(ln.strip())), None)
    if hit is None:
        with open(src, "a", encoding="utf-8", newline="") as f:
            f.write("\n## 参考答案\n")
        hit = len(lines) + 2
    u9 = man["units"][0]
    u9["extra_lines"] = [hit, hit]
    save_man(d, SID, man)
    record("M-C9 结构行混入单元区间", SID, "C9", run_check(d, SID), "FAIL")

    # ── C4 / C12:复合题卷 ────────────────────────────────────────────────
    d, man, src = stage(SID_COMPOSITE)
    comp = next((u for u in man["units"]
                 if u.get("unit_type") == "composite_question"), None)
    results.append({"mutation": "C4/C12 前置:复合题存在", "sample": SID_COMPOSITE,
                    "expect": "至少 1 个 composite 单元", "got_issues": [],
                    "verdict": None, "ok": comp is not None})
    print(f"[{'OK ' if comp else 'FAIL'}] composite 单元存在: {bool(comp)}")
    if comp:
        d2, man2, src2 = stage(SID_COMPOSITE)
        c2 = next(u for u in man2["units"]
                  if u.get("unit_type") == "composite_question")
        c2["material_lines"] = None
        c2["questions_lines"] = None
        save_man(d2, SID_COMPOSITE, man2)
        record("M-C4 综合题缺材料区间", SID_COMPOSITE, "C4",
               run_check(d2, SID_COMPOSITE), "FAIL")

        d3, man3, src3 = stage(SID_COMPOSITE)
        c3 = next(u for u in man3["units"]
                  if u.get("unit_type") == "composite_question"
                  and isinstance(u.get("material_lines"), list)
                  and isinstance(u.get("questions_lines"), list))
        # 构造相交但未嵌套:mat=[10,30] q=[20,40](真实行号范围内微调)
        n = 200
        c3["material_lines"] = [10, 30]
        c3["questions_lines"] = [20, 40]
        assert 40 <= n
        save_man(d3, SID_COMPOSITE, man3)
        record("M-C12 material 相交未嵌套", SID_COMPOSITE, "C12",
               run_check(d3, SID_COMPOSITE), "FAIL")

    n_fail = sum(1 for r in results if not r["ok"])
    OUT.write_text(json.dumps({"n": len(results), "n_fail": n_fail,
                               "results": results}, ensure_ascii=False, indent=1),
                   encoding="utf-8", newline="")
    print(f"\n=== 变异测试:{len(results)} 条,{n_fail} 条未达期望 ===")


if __name__ == "__main__":
    main()

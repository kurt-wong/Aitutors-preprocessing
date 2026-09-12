r"""PAC 对抗性审查 C 项:语义探针(P13/P14/P15)攻击(R46)。

两部分:
  1) 灵敏度变异:向真实产物拷贝注入合成语义错误,探针必须报警;
     反向阴性对照(已知无害形态)必须不报警。双向都验才算探针可信。
  2) 78 报警独立再分诊:不沿用 R45 的口头分类,用可执行规则对每条报警
     重新归类;规则归不了类的全部列出,人工逐条读原文裁决。

用法: python scripts/pac_audit_probe.py
输出: data/pac_audit_probe.json
"""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import semantic_probe as sp  # noqa: E402
import question_identity as qi  # noqa: E402

ANN_DIR = ROOT / "Ocr-markdown/reslice-pac-annotated/reslice-pac/ocr"
WORK = ROOT / ".pytest_work/pac_audit_probe"
OUT = ROOT / "data/pac_audit_probe.json"

SID = "pac-c01-01"


def stage(sid):
    d = WORK / sid
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    man_path = ANN_DIR / f"{sid}.manifest.json"
    shutil.copy2(man_path, d / f"{sid}.manifest.json")
    man = json.loads(man_path.read_text(encoding="utf-8"))
    src = Path(man["source_file"])
    src_copy = d / f"{sid}.src.md"
    shutil.copy2(src, src_copy)
    man["source_file"] = str(src_copy)
    return d, man, src_copy


def save_man(d, sid, man):
    (d / f"{sid}.manifest.json").write_text(
        json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8", newline="")


def flags_of(d, sid):
    return sp.probe_file(d / f"{sid}.manifest.json")["flags"]


def main():
    results = []

    def record(name, flags, expect_check=None, expect_unit=None, expect_fire=True):
        if expect_fire:
            hit = any((expect_check is None or f["check"] == expect_check)
                      and (expect_unit is None or f["unit"] == expect_unit)
                      for f in flags)
        else:
            hit = len(flags) == 0
        results.append({"mutation": name, "expect_fire": expect_fire,
                        "got": flags, "ok": hit})
        print(f"[{'OK ' if hit else 'FAIL'}] {name}: "
              f"got {[(f['check'], f['unit']) for f in flags]}")

    # ── 控制组:无变异拷贝复现原报警 ───────────────────────────────────────
    d, man, src = stage(SID)
    base = flags_of(d, SID)
    rep = json.loads((ROOT / "data/pac_semantic_probe.json").read_text(encoding="utf-8"))
    orig = next(r for r in rep["results"] if Path(r["manifest"]).name == f"{SID}.manifest.json")
    ok = base == orig["flags"]
    results.append({"mutation": "control(拷贝零变异复现)", "expect_fire": None,
                    "got_n": len(base), "ok": ok})
    print(f"[{'OK ' if ok else 'FAIL'}] probe control: {len(base)} flags 复现={ok}")

    # ── P14 灵敏度:stem 吞入下一题题号行 ──────────────────────────────────
    d, man, src = stage(SID)
    q1 = next(u for u in man["units"] if 1 in (u.get("question_numbers") or []))
    q2_start = qi.unit_start(next(u for u in man["units"]
                                 if 2 in (u.get("question_numbers") or [])))
    q1["stem_lines"] = [q1["stem_lines"][0], q2_start]
    save_man(d, SID, man)
    record("M-P14 stem 吞入 2. 题号行", flags_of(d, SID), "P14", q1["unit_id"], True)

    # ── P15 灵敏度:answer 指向别题题号+答案行 ─────────────────────────────
    d, man, src = stage(SID)
    lines = sp.load_src_lines(src)
    q1 = next(u for u in man["units"] if 1 in (u.get("question_numbers") or []))
    hit = next((i for i, ln in enumerate(lines, 1)
                if sp.QNUM_LINE.match(ln)
                and int(sp.QNUM_LINE.match(ln).group(1)) not in (1,)
                and len(sp.ANS_PAIR.findall(ln)) < 2), None)
    assert hit, "未找到单题号行"
    q1["answer_lines"] = [hit, hit]
    save_man(d, SID, man)
    record("M-P15 answer 指向别题题号行", flags_of(d, SID), "P15", q1["unit_id"], True)

    # ── P13 灵敏度:answer 指向纯散文行 ────────────────────────────────────
    d, man, src = stage(SID)
    lines = sp.load_src_lines(src)
    q1 = next(u for u in man["units"] if 1 in (u.get("question_numbers") or []))
    prose = next((i for i, ln in enumerate(lines, 1)
                  if len(ln.strip()) > 20
                  and not sp.ANS_MARK.search(ln)
                  and not sp.ANS_TABLE.search(ln)
                  and not sp.ANS_RANGE.search(ln)
                  and not sp.ANS_LETTERS.search(ln)
                  and not sp.ANS_SINGLE.search(ln)
                  and len(sp.ANS_PAIR.findall(ln)) < 2
                  and not sp.QNUM_LINE.match(ln)), None)
    assert prose, "未找到纯散文行"
    q1["answer_lines"] = [prose, prose]
    save_man(d, SID, man)
    record("M-P13 answer 指向纯散文行", flags_of(d, SID), "P13", q1["unit_id"], True)

    # ── 阴性对照:已知无害形态不得报警 ─────────────────────────────────────
    # N1 共享答案表 <table> 行
    d, man, src = stage(SID)
    lines = sp.load_src_lines(src)
    tbl = next((i for i, ln in enumerate(lines, 1) if "<table" in ln.lower()), None)
    q1 = next(u for u in man["units"] if 1 in (u.get("question_numbers") or []))
    if tbl:
        q1["answer_lines"] = [tbl, tbl]
        save_man(d, SID, man)
        record("N-P13 共享答案表行不报警", flags_of(d, SID), expect_fire=False)
    else:
        results.append({"mutation": "N-P13 共享答案表行", "ok": None,
                        "note": f"{SID} 源无 <table 行,改用合成行"})
        d, man, src = stage(SID)
        with open(src, "a", encoding="utf-8", newline="") as f:
            f.write("\n<table><tr><td>A</td><td>B</td></tr></table>\n")
        q1 = next(u for u in man["units"] if 1 in (u.get("question_numbers") or []))
        q1["answer_lines"] = [len(sp.load_src_lines(src)), len(sp.load_src_lines(src))]
        save_man(d, SID, man)
        record("N-P13 共享答案表行(合成)不报警", flags_of(d, SID), expect_fire=False)

    # N2 区间连写答案 "1-5 ACDBA"
    d, man, src = stage(SID)
    with open(src, "a", encoding="utf-8", newline="") as f:
        f.write("\n1-5 ACDBA\n")
    n = len(sp.load_src_lines(src))
    q1 = next(u for u in man["units"] if 1 in (u.get("question_numbers") or []))
    q1["answer_lines"] = [n, n]
    save_man(d, SID, man)
    record("N-P13 区间连写答案不报警", flags_of(d, SID), expect_fire=False)

    # N3 解答步骤编号 "1、目的基因的获取:" 不算题号
    d, man, src = stage(SID)
    with open(src, "a", encoding="utf-8", newline="") as f:
        f.write("\n1、目的基因的获取：PCR扩增\n")
    n = len(sp.load_src_lines(src))
    q1 = next(u for u in man["units"] if 1 in (u.get("question_numbers") or []))
    q1["stem_lines"] = [n, n]  # 只指向步骤编号行本身,不吞别的题
    save_man(d, SID, man)
    record("N-P14 解答步骤编号不报警", flags_of(d, SID), expect_fire=False)

    # ── 第 2 部分:78 报警独立再分诊(规则分类 + 残差人工)──────────────────
    triage = []
    unclassified = []
    for r in rep["results"]:
        mf = Path(r["manifest"])
        man = json.loads(mf.read_text(encoding="utf-8"))
        srcp = Path(man.get("source_file", ""))
        if not srcp.exists():
            for f in r["flags"]:
                triage.append({**f, "file": mf.name, "rule": "SOURCE_MISSING"})
            continue
        lines = sp.load_src_lines(srcp)
        by_id = {}
        for u in man["units"]:
            by_id.setdefault(u.get("unit_id"), []).append(u)
        for f in r["flags"]:
            units = by_id.get(f["unit"]) or []
            u = units[0] if units else {}
            printed = {int(x) for x in (u.get("printed_number") or [])
                       if isinstance(x, (int, str)) and str(x).isdigit()}
            canon = set(u.get("question_numbers") or [])
            m = re.search(r"非本单元题号 (\d+)", f["detail"])
            n = int(m.group(1)) if m else None
            rule = None
            # R1 printed/canonical 错位:报警号恰是本单元印刷号(v2 正确行为)
            if n is not None and n in printed and n not in canon:
                rule = "R1 printed/canonical错位(v2 正确)"
            else:
                # R2 括号答案键连写:(21)(22) ... 同一行多题答案
                if n is not None:
                    for rg in (u.get("answer_lines"), u.get("stem_lines"),
                               u.get("questions_lines")):
                        seg = sp.span(lines, rg)
                        for ln in seg:
                            if f"({n})" in ln.replace("（", "(").replace("）", ")") \
                               or f"（{n}）" in ln:
                                rule = "R2 括号答案键连写"
                                break
                        if rule:
                            break
                # R3 子问编号 (1) 2) 3) 行首
                if rule is None and n is not None:
                    seg = sp.span(lines, u.get("answer_lines") or u.get("stem_lines"))
                    for ln in seg:
                        if re.match(rf"^\s*{n}\s*[)）]", ln):
                            rule = "R3 子问编号行首"
                            break
                # R4 写作提示/评分细则内部编号
                if rule is None and n is not None:
                    seg = sp.span(lines, u.get("answer_lines") or u.get("stem_lines"))
                    for ln in seg:
                        if re.search(r"评分|写作|提示|范文|词数|作文|开放性", ln) and \
                           re.match(rf"^\s*{n}\s*[.、．]", ln.strip()):
                            rule = "R4 写作提示/评分细则编号"
                            break
            # R5 P13:答案区确有答案语义(人工已核的格式盲区)——检查行内是否
            # 实际存在 latex/数学答案内容($ ... $ 或中文答案短语)
            if rule is None and f["check"] == "P13":
                seg = sp.span(lines, u.get("answer_lines"))
                joined = "\n".join(seg)
                if "$" in joined or re.search(r"[=＝]", joined):
                    rule = "R5 P13格式盲区(答案内容在,形态正则未覆盖)"
            triage.append({**f, "file": mf.name, "printed": sorted(printed),
                           "canon": sorted(canon), "rule": rule})
            if rule is None:
                unclassified.append({**f, "file": mf.name,
                                     "printed": sorted(printed), "canon": sorted(canon)})

    from collections import Counter
    rule_cnt = Counter(t.get("rule") for t in triage)
    OUT.write_text(json.dumps(
        {"mutation_results": results, "triage": triage,
         "rule_counts": dict(rule_cnt), "unclassified": unclassified},
        ensure_ascii=False, indent=1), encoding="utf-8", newline="")
    n_fail = sum(1 for r in results if r["ok"] is False)
    print(f"\n=== 探针变异:{len(results)} 条,{n_fail} 条未达期望 ===")
    print("=== 78 报警规则再分诊 ===")
    for k, v in rule_cnt.items():
        print(f"  {k}: {v}")
    print(f"  未归类(需人工读原文): {len(unclassified)}")


if __name__ == "__main__":
    main()

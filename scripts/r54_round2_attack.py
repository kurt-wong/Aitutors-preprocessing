r"""R54 Resolver Consumer Adversarial Audit 第二轮:边界组合攻击。

用户 R53 裁定:第二轮目标不是"Resolver 是否违反契约"(R53 已闭环),而是
"Resolver 周边系统是否能制造契约合法但语义错误的数据"。

  Part A — R-ACC-12 QC→Resolver 边界攻击:manifest span 语义性收缩/错绑
           后**重编译全部工件**(生产可 representable),整链测量
           QC verdict × Resolver disposition × F1 status。预期:结构链
           全绿而语义已错 —— 这正是 Admission 层存在的证据,不是
           resolver 缺陷。选取规则 = manifest 序前 K 个合格单元
           (非按结果挑选),如实报 numerator/denominator。
  Part B — R-ACC-13 Material Consumer Attack:material 顺序交换 /
           shared 错绑定 / single 丢失 / composite 泄漏。对 resolver
           输出做**独立期望对账**(expected_materials 由 manifest 独立
           重算,不 import resolver 内部逻辑):消费者集合必须精确反映
           变异后 manifest,零重塑/零合并/零复制。
  Part C — R-ACC-14 unresolved 消费攻击:真实 IR 跑消费不变量检查器
           (audit_ir_answers I1/I2/I3)+ 四条负向对照(逐条必须被咬)
           + 下游默认值攻击面量化(answers.get(q,"") 会把多少 unresolved
           槽位静默变成"已解为空")。
  Part D — F1 工具灵敏度:代码变异(备份-注入-pytest-还原-sha 闭环)+
           真实语料 staged 漂移(F1 必须咬;同时演示 resolver 对同一
           漂移态照常 ADMITTED —— F1 存在的理由)。

治理:Input Integrity Gate(原件零触碰)、staging 规范(R49 教训:
源拷贝改名 src_* 防自我覆盖)、控制组(零变异 staging 必须复现原件)。
输出:data/r54_round2_attack.json
用法:python scripts/r54_round2_attack.py
"""
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import audit_f1_consistency as f1  # noqa: E402
import audit_integrity as ai  # noqa: E402
import reslice_pipeline as rp  # noqa: E402
import reslice_qc as qc  # noqa: E402
import resolver_reference as rr  # noqa: E402
from fix_bug22_renumber import strip_meta  # noqa: E402

WORK = ROOT / ".pytest_work"
OUT = ROOT / "data/r54_round2_attack.json"
PREFLIGHT = ROOT / "data/resolver_contract_preflight.json"
IR_PATH = ROOT / "data/resolver_ref_r52/resolver_ir.json"
F1_SRC = ROOT / "scripts/audit_f1_consistency.py"
K = 6  # 每个攻击族枚举上限(manifest 序前 K 个合格单元)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ------------------------------------------------------------ staging 基建

def stage(md_rel):
    """整组拷贝到 staging(源改名 src_* 防自我覆盖,R49 教训)。"""
    src_md = ROOT / md_rel
    man_path = src_md.with_suffix(".manifest.json")
    orig_src = Path(json.loads(man_path.read_text(
        encoding="utf-8"))["source_file"])
    d = WORK / f"r54_stg_{uuid.uuid4().hex[:8]}"
    d.mkdir(parents=True)
    md_c = d / src_md.name
    shutil.copy2(src_md, md_c)
    ann = src_md.with_suffix(".annotated.md")
    if ann.exists():
        shutil.copy2(ann, d / ann.name)
    src_c = d / f"src_{orig_src.name}"
    shutil.copy2(orig_src, src_c)
    man = json.loads(man_path.read_text(encoding="utf-8"))
    man["source_file"] = str(src_c)
    return {"dir": d, "md": md_c, "src": src_c,
            "man_path": d / man_path.name, "man": man}


def recompile(stg):
    """变异 manifest 后重编译全部工件(生产可 representable)。"""
    man, src_c, d = stg["man"], stg["src"], stg["dir"]
    lines = strip_meta(src_c.read_text(encoding="utf-8",
                                       errors="replace")).splitlines()
    issues, summary = rp.validate_manifest(man, len(lines), lines)
    rp.write_outputs(d, stg["md"].stem, lines, man, issues, summary,
                     src_c.name, src_c)
    # write_outputs 重写 manifest(source_file 等同值);identity 字段保留
    stg["man"] = json.loads(stg["man_path"].read_text(encoding="utf-8"))
    return stg


def save_man(stg):
    stg["man_path"].write_text(
        json.dumps(stg["man"], ensure_ascii=False, indent=1),
        encoding="utf-8", newline="")


def measure(md_c):
    """整链测量:QC verdict × Resolver disposition × F1 status。"""
    q = qc.check(md_c)
    rec = rr.resolve_file(md_c)
    o = WORK / f"r54_f1_{uuid.uuid4().hex[:8]}"
    rep = f1.run([md_c], o)
    f1_status = rep["files"][0]["status"]
    shutil.rmtree(o, ignore_errors=True)
    return {"qc": q.get("verdict"), "resolver": rec.get("disposition"),
            "f1": f1_status,
            "resolver_flags": sorted({fl for u in (rec.get("ir") or {})
                                      .get("units", [])
                                      for fl in u.get("flags") or []})
            if rec.get("ir") else []}


def expected_materials(man):
    """独立期望:manifest → {ref: [consumers]}(不 import resolver)。"""
    mats = {}
    for u in man.get("units") or []:
        rg = u.get("material_lines")
        if isinstance(rg, list) and len(rg) == 2:
            mats.setdefault(f"L{rg[0]}-{rg[1]}",
                            []).append(u.get("unit_id"))
    return mats


def actual_materials(rec):
    if not rec.get("ir"):
        return None
    return {ref: e.get("consumers")
            for ref, e in rec["ir"].get("materials", {}).items()}


# ------------------------------------------------------ Part A:R-ACC-12

def part_a(md_rel):
    base = stage(md_rel)
    units = copy.deepcopy(base["man"]["units"])
    shutil.rmtree(base["dir"], ignore_errors=True)

    def run_family(tag, candidates, mutate):
        rows = []
        for i, u in enumerate(candidates):
            stg = stage(md_rel)
            mu = stg["man"]["units"][u["_idx"]]
            mutate(mu, stg["man"], stg["src"])
            save_man(stg)
            recompile(stg)
            m = measure(stg["md"])
            # 语义描述(攻击意图),供人工审阅;不做语义裁决
            m.update({"attack": tag, "unit": mu.get("unit_id"),
                      "qnums": mu.get("question_numbers"),
                      "chain_green": (m["qc"] == "PASS"
                                      and m["resolver"] == "ADMITTED"
                                      and m["f1"] == "MATCH")})
            rows.append(m)
            shutil.rmtree(stg["dir"], ignore_errors=True)
        green = sum(1 for r in rows if r["chain_green"])
        return {"rows": rows,
                "chain_green": {"numerator": green, "denominator":
                                len(rows),
                                "proof": "qc PASS + resolver ADMITTED + "
                                         "f1 MATCH on recompiled "
                                         "production-representable "
                                         "artifacts"}}

    for idx, u in enumerate(units):
        u["_idx"] = idx

    def _span_ge2(u, k):
        rg = u.get(k)
        return isinstance(rg, list) and rg[1] > rg[0]

    def drop_last(k):
        def f(mu, man, src):
            mu[k] = [mu[k][0], mu[k][1] - 1]
        return f

    out = {}
    stems = [u for u in units if _span_ge2(u, "stem_lines")][:K]
    out["a12_1_stem尾行丢弃(题干缺最后一个条件)"] = run_family(
        "a12_1", stems, drop_last("stem_lines"))
    opts = [u for u in units if _span_ge2(u, "options_lines")][:K]
    out["a12_2_options尾行丢弃"] = run_family(
        "a12_2", opts, drop_last("options_lines"))

    # a12_3:答案区间错绑到下一单元的答案例行(答案归属错位,结构合法)
    ans_pairs = []
    for i, u in enumerate(units):
        rg = u.get("answer_lines")
        nxt = next((v for v in units[i + 1:]
                    if v.get("answer_lines") and v["answer_lines"] != rg),
                   None)
        if rg and nxt:
            ans_pairs.append((u, nxt))
    def shift_answer(pair):
        u, nxt = pair
        def f(mu, man, src):
            mu["answer_lines"] = list(nxt["answer_lines"])
        return f
    rows = []
    for u, nxt in ans_pairs[:K]:
        stg = stage(md_rel)
        mu = stg["man"]["units"][u["_idx"]]
        mu["answer_lines"] = list(nxt["answer_lines"])
        save_man(stg)
        recompile(stg)
        m = measure(stg["md"])
        m.update({"attack": "a12_3", "unit": mu.get("unit_id"),
                  "borrowed_from": nxt.get("unit_id"),
                  "chain_green": (m["qc"] == "PASS"
                                  and m["resolver"] == "ADMITTED"
                                  and m["f1"] == "MATCH")})
        rows.append(m)
        shutil.rmtree(stg["dir"], ignore_errors=True)
    green = sum(1 for r in rows if r["chain_green"])
    out["a12_3_answer错绑下一单元"] = {
        "rows": rows,
        "chain_green": {"numerator": green, "denominator": len(rows),
                        "proof": "同 a12 家族;另记录 resolver 是否产生 "
                                 "answer_number_mismatch 结构 flag"}}

    # a12_4:composite material 尾部外扩 1 行(跨题污染形状)
    comps = [u for u in units if u.get("unit_type") == "composite_question"
             and isinstance(u.get("material_lines"), list)
             and isinstance(u.get("questions_lines"), list)][:K]
    def grow_mat(mu, man, src):
        n = len(strip_meta(src.read_text(encoding="utf-8",
                                         errors="replace")).splitlines())
        mu["material_lines"] = [mu["material_lines"][0],
                                min(mu["material_lines"][1] + 1, n)]
    out["a12_4_material尾行外扩"] = run_family("a12_4", comps, grow_mat)
    return out


# ------------------------------------------------------ Part B:R-ACC-13

def part_b(md_rel):
    out = {}

    def case(tag, mutate, check_materials=True):
        stg = stage(md_rel)
        note = mutate(stg["man"], stg["src"])
        save_man(stg)
        recompile(stg)
        rec = rr.resolve_file(stg["md"])
        row = {"attack": tag, "disposition": rec.get("disposition"),
               "qc": qc.check(stg["md"]).get("verdict"), "note": note}
        if check_materials and rec.get("ir"):
            exp = expected_materials(stg["man"])
            act = actual_materials(rec)
            row["expected_materials"] = exp
            row["actual_materials"] = act
            row["consumers_exact"] = (exp == act)
            row["text_single_copy"] = all(
                len(e.get("text") or []) == (e["lines"][1] - e["lines"][0]
                                             + 1)
                for e in rec["ir"].get("materials", {}).values())
        shutil.rmtree(stg["dir"], ignore_errors=True)
        return row

    def pick_pair(man):
        comps = [(i, u) for i, u in enumerate(man["units"])
                 if isinstance(u.get("material_lines"), list)]
        return comps

    base = stage(md_rel)
    comps = pick_pair(base["man"])
    shutil.rmtree(base["dir"], ignore_errors=True)
    if len(comps) < 2:
        return {"error": f"样本 composite 单元不足: {len(comps)}"}

    ia, ua = comps[0]
    ib, ub = comps[1]

    def b1_swap(man, src):
        a, b = man["units"][ia], man["units"][ib]
        a["material_lines"], b["material_lines"] = (list(b["material_lines"]),
                                                    list(a["material_lines"]))
        return f"swap {ua.get('unit_id')} x {ub.get('unit_id')}"
    out["b1_material顺序交换"] = case("b1", b1_swap)

    def b2_misbind(man, src):
        man["units"][ib]["material_lines"] = list(
            man["units"][ia]["material_lines"])
        return f"{ub.get('unit_id')} 错绑定到 {ua.get('unit_id')} 的材料"
    out["b2_shared错绑定"] = case("b2", b2_misbind)

    def b3_loss(man, src):
        man["units"][ia]["material_lines"] = None
        return f"{ua.get('unit_id')} material 丢失"
    out["b3_material丢失"] = case("b3", b3_loss)

    def b4_leak(man, src):
        u = man["units"][ia]
        n = len(strip_meta(src.read_text(encoding="utf-8",
                                         errors="replace")).splitlines())
        q = u.get("questions_lines")
        u["material_lines"] = [u["material_lines"][0],
                               min(max(q[1] + 3, u["material_lines"][1] + 3),
                                   n)]
        return (f"{ua.get('unit_id')} material 外扩越过 questions"
                f"(相交不嵌套 → C12 面)")
    out["b4_composite泄漏"] = case("b4", b4_leak)

    # 控制组:零变异 staging 必须复现原件
    stg = stage(md_rel)
    save_man(stg)
    recompile(stg)
    rec = rr.resolve_file(stg["md"])
    orig = rr.resolve_file(ROOT / md_rel)
    ctrl_ok = (rec.get("disposition") == orig.get("disposition")
               and actual_materials(rec) == actual_materials(orig))
    out["control"] = {"disposition": rec.get("disposition"),
                      "materials_equal_original": ctrl_ok, "ok": ctrl_ok}
    shutil.rmtree(stg["dir"], ignore_errors=True)
    return out


# ------------------------------------------------------ Part C:R-ACC-14

def part_c():
    doc = json.loads(IR_PATH.read_text(encoding="utf-8"))
    findings = f1.audit_ir_answers(doc)
    n_table_units = sum(1 for f in doc["files"] if f.get("ir")
                        for u in f["ir"]["units"]
                        if u.get("answers") is not None)
    n_keys = sum(len((u.get("answers") or {}).get("answers") or {})
                 for f in doc["files"] if f.get("ir")
                 for u in f["ir"]["units"] if u.get("answers") is not None)
    n_unres = sum(len((u.get("answers") or {}).get("unresolved") or [])
                  for f in doc["files"] if f.get("ir")
                  for u in f["ir"]["units"]
                  if u.get("answers") is not None)
    # 下游默认值攻击面:answers.get(q, "") 会把 unresolved 槽位静默变 ""
    naive_defaults = n_unres

    def _tbl(ans, unres, cells=None):
        return {"cells": cells or [], "method": "td_positional",
                "answers": ans, "unresolved": unres}

    def ctrl(build, expect_frag):
        cdoc = {"ir_version": "resolver-ir-0.1", "files": [
            {"file": "x.md", "disposition": "ADMITTED",
             "ir": {"units": [build]}}]}
        fnd = f1.audit_ir_answers(cdoc)
        return {"expect": expect_frag, "findings": fnd,
                "ok": any(expect_frag in x for x in fnd)}

    controls = {
        "c1_overlap": ctrl({"unit_id": "X", "question_numbers": [1, 2],
                            "answers": _tbl({"1": "1. A"}, [1])},
                           "overlap"),
        "c2_missing_unresolved": ctrl({"unit_id": "X",
                                       "question_numbers": [1, 2],
                                       "answers": _tbl({"1": "1. A"}, [])},
                                      "missing_from_unresolved"),
        "c3_sentinel_empty": ctrl({"unit_id": "X", "question_numbers": [1, 2],
                                   "answers": _tbl({"1": ""}, [2])},
                                  "sentinel"),
        "c4_sentinel_none": ctrl({"unit_id": "X", "question_numbers": [1, 2],
                                  "answers": _tbl({"1": None}, [2])},
                                 "sentinel"),
        "c5_shape_violation": ctrl({"unit_id": "X",
                                    "question_numbers": [1],
                                    "answers": {"cells": ["1. A"]}},
                                   "shape"),
        "c6_clean_zero_findings": {"ok": f1.audit_ir_answers(
            {"files": [{"ir": {"units": [
                {"unit_id": "X", "question_numbers": [1, 2],
                 "answers": _tbl({"1": "1. A"}, [2])}]}}]}) == []},
    }
    return {"real_ir_findings": findings, "n_findings": len(findings),
            "table_units": n_table_units, "answers_keys": n_keys,
            "unresolved_slots": n_unres,
            "naive_default_conversions": naive_defaults,
            "controls": controls,
            "controls_all_ok": all(c["ok"] for c in controls.values())}


# ------------------------------------------------- Part D:F1 灵敏度

F1_MUTATIONS = {
    "D1_unit状态硬编码MATCH": (
        'status = ("MATCH" if (list(a_rec) == list(rg) and r_hash == q_hash)\n'
        '                  else "DRIFT")',
        'status = "MATCH"', "test_f1_t2"),
    "D2_slice检查失效": (
        '"status": "MATCH" if b == a else "DRIFT"}',
        '"status": "MATCH"}', "test_f1_t3"),
    "D3_消费不变量检查器失效": (
        '    findings = []\n    for f in doc.get("files") or []:',
        '    return []\n    for f in doc.get("files") or []:',
        "test_f1_t8"),
    "D4_Gatesabotage(接线活性)": (
        '    after = {}\n    missing = []',
        '    raise RuntimeError("[SABOTAGE] gate forced")\n'
        '    after = {}\n    missing = []',
        "test_f1_t1"),
}


def part_d(md_rel):
    results = []
    backups = {p: p.read_bytes() for p in (F1_SRC,
                                           ROOT / "scripts/audit_integrity.py")}
    targets = {"D1_unit状态硬编码MATCH": F1_SRC,
               "D2_slice检查失效": F1_SRC,
               "D3_消费不变量检查器失效": F1_SRC,
               "D4_Gatesabotage(接线活性)": ROOT /
               "scripts/audit_integrity.py"}
    try:
        for tag, (old, new, expect_test) in F1_MUTATIONS.items():
            p = targets[tag]
            src = backups[p].decode("utf-8")
            assert old in src, f"{tag} 锚点失配"
            p.write_text(src.replace(old, new, 1), encoding="utf-8",
                         newline="")
            r = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/test_audit_f1.py",
                 "-q"], capture_output=True, encoding="utf-8",
                errors="replace", cwd=str(ROOT))
            out = r.stdout + r.stderr
            caught = r.returncode != 0 and expect_test in out
            results.append({"m": tag, "exit": r.returncode,
                            "expected_test": expect_test,
                            "caught": caught, "ok": caught})
            p.write_bytes(backups[p])
    finally:
        for p, b in backups.items():
            p.write_bytes(b)
    assert all(sha(p) == hashlib.sha256(b).hexdigest()
               for p, b in backups.items()), "工具还原失败!"
    r = subprocess.run([sys.executable, "-m", "pytest",
                        "tests/test_audit_f1.py", "-q"],
                       capture_output=True, cwd=str(ROOT))
    results.append({"m": "restore_clean", "exit": r.returncode,
                    "ok": r.returncode == 0})

    # 真实语料 staged 漂移:改 manifest 不重编译(F1 态生产不可产生,
    # 但 F1 的存在意义就是抓它;同时演示 resolver 照常 ADMITTED)
    stg = stage(md_rel)
    n_src = len(strip_meta(stg["src"].read_text(
        encoding="utf-8", errors="replace")).splitlines())
    mutated_k, mutated_u = None, None
    for u in stg["man"]["units"]:
        for k in ("stem_lines", "questions_lines", "material_lines",
                  "answer_lines", "options_lines"):
            rg = u.get(k)
            if isinstance(rg, list) and rg[1] < n_src:
                u[k] = [rg[0], rg[1] + 1]
                mutated_k, mutated_u = k, u.get("unit_id")
                break
        if mutated_k:
            break
    assert mutated_k, "未找到可变异 span"
    save_man(stg)  # 不重编译
    rec = rr.resolve_file(stg["md"])
    o = WORK / f"r54_f1_{uuid.uuid4().hex[:8]}"
    rep = f1.run([stg["md"], ], o)
    drift_units = sum(1 for f in rep["files"] for x in f["units"]
                      if x["status"] == "DRIFT")
    shutil.rmtree(o, ignore_errors=True)
    results.append({"m": "E1_staged_manifest漂移",
                    "mutated": mutated_k, "mutated_unit": mutated_u,
                    "resolver_disposition": rec.get("disposition"),
                    "f1_file_status": rep["files"][0]["status"],
                    "f1_drift_units": drift_units,
                    "ok": (rep["files"][0]["status"] == "DRIFT"
                           and drift_units > 0)})
    shutil.rmtree(stg["dir"], ignore_errors=True)

    # 控制组:零变异 staging 复现原件 F1 MATCH
    stg = stage(md_rel)
    save_man(stg)
    o = WORK / f"r54_f1_{uuid.uuid4().hex[:8]}"
    rep = f1.run([stg["md"]], o)
    shutil.rmtree(o, ignore_errors=True)
    results.append({"m": "E2_control_zero_mutation",
                    "f1_file_status": rep["files"][0]["status"],
                    "ok": rep["files"][0]["status"] == "MATCH"})
    shutil.rmtree(stg["dir"], ignore_errors=True)
    return results


def main():
    pf = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    row_a = next(r for r in pf["rows"] if r["corpus"] == "ocr"
                 and not r["findings"] and r.get("qc_verdict") == "PASS")
    md_a = row_a["file"]
    # R-ACC-13 样本:首个含 ≥2 个带 material 单元的 PASS 文件
    md_b = None
    for r in pf["rows"]:
        if r.get("qc_verdict") != "PASS":
            continue
        mpath = (ROOT / r["file"]).with_suffix(".manifest.json")
        man = json.loads(mpath.read_text(encoding="utf-8"))
        n_mat = sum(1 for u in man.get("units") or []
                    if isinstance(u.get("material_lines"), list))
        if n_mat >= 2:
            md_b = r["file"]
            break
    assert md_b, "未找到含 ≥2 material 单元的样本"

    originals = []
    for rel in (md_a, md_b):
        p = ROOT / rel
        originals += [p, p.with_suffix(".manifest.json"),
                      p.with_suffix(".annotated.md"),
                      Path(json.loads(p.with_suffix(".manifest.json")
                                      .read_text(encoding="utf-8"))
                           ["source_file"])]
    originals += [IR_PATH, F1_SRC, ROOT / "scripts/audit_integrity.py"]
    gate_before = ai.gate_snapshot(originals)

    a = part_a(md_a)
    b = part_b(md_b)
    c = part_c()
    d = part_d(md_a)

    ai.gate_assert_unchanged(gate_before, originals, "r54_round2")

    ok = (c["controls_all_ok"]
          and all(x["ok"] for x in d)
          and b.get("control", {}).get("ok", False)
          and a.get("control", True))
    doc = {"samples": {"a12": md_a, "a13": md_b},
           "part_a_racc12": a, "part_b_racc13": b,
           "part_c_racc14": c, "part_d_f1_sensitivity": d,
           "all_ok": ok}
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8", newline="")
    print(json.dumps({
        "a12_chain_green": {k: v["chain_green"] for k, v in a.items()},
        "b_control": b.get("control"), "c_findings": c["n_findings"],
        "c_controls_ok": c["controls_all_ok"],
        "d_all_ok": all(x["ok"] for x in d), "all_ok": ok},
        ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

r"""R60 · 事实漂移边界攻击(Source → Resolver → IR)——一次性审计武器。

用户 R59 审核裁定(2026-09-13)所指定的下一轮目标:
  "BUG-14 第一阶段:Source → Resolver → IR 事实一致性攻击,
   不增加生产能力,只验证边界是否可靠。"

四个攻击面(用户原文级):
  A 字节事实保持  改 source 行 → 观察 resolved_span,预期不得静默 PASS
  B Span 边界     start_line-1 / end_line+1 → 不得静默裁剪
  C provenance 断裂 删 source_sha256 / 改 source_version / 断 source_file
                  → 预期 Admission 拒绝(fail-closed)
  D Resolver↔QC 分叉 QC 看到 A、Resolver 看到 B → 必须产生 F1 结构漂移,
                  不允许"两个系统各自正确"

方法纪律:
  - 全部变异只作用于 .pytest_work 下的 staged 合成副本,原件零接触;
    语料模式(--corpus)只读,audit_f1_consistency.run 内建 Input
    Integrity Gate。
  - SUT(resolver_reference / reslice_qc / audit_f1_consistency)以黑盒
    调用;staging/变异逻辑为本脚本独立实现,不 import SUT 的解析函数。
  - 确定性输出(无时间戳),可字节复现。

Audit Tool Trust Boundary 声明(R60 新规则 G-AUDTB-1 首次适用):
  parser: 自建 staging 变异器 + SUT 黑盒调用
  supports:
    - 合成 v2 manifest 全链(源/manifest/annotated/切片)staged 攻击
    - resolver disposition / qc verdict / F1 zone 状态三层观测
    - --corpus 模式:88 份真实控制组 F1 只读复核(gate 保护)
  does_not_support:
    - 源文件重编译攻击(改源后必须保持 annotated/slice 不一致——
      本武器就是要测"不重编译"的漂移面)
    - 语义正确性裁决(属 QC/Admission,三边界纪律)
    - LLM 产物攻击(属 prompt/QC 家族,非本轮)

用法:
  python scripts/r60_fact_drift_attack.py --out data/r60_fact_drift_attack.json
  python scripts/r60_fact_drift_attack.py --corpus \
      --out data/r60_fact_drift_attack.json
"""
import argparse
import copy
import hashlib
import json
import shutil
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import audit_f1_consistency as af1  # noqa: E402  SUT(F1 审计不变量)
import question_identity as qi  # noqa: E402
import reslice_pipeline as rp  # noqa: E402  仅用于 staging 编译(生产路径)
import reslice_qc as qc  # noqa: E402  SUT(生产 Gate)
import resolver_reference as rr  # noqa: E402  SUT(参考 Resolver)

ATTACK_VERSION = "r60-fact-drift-0.1"

# 合成微型试卷(与 tests/conftest.SYNTH_LINES 同构;审计武器自持副本,
# 不 import 测试夹具——staging 是本武器的独立实现面)。
SYNTH_LINES = [
    "# 2024 合成测试卷",
    "",
    "## 一、选择题",
    "",
    '<div><img src="box_100_100_200_200.jpg" /></div>',
    "1. 下列说法正确的是（ ）",
    "",
    "A. 甲",
    "B. 乙",
    "",
    "2. 第二题题干（ ）",
    "A. 一",
    "B. 二",
    "",
    "## 二、综合题",
    "阅读下列材料:",
    "材料内容甲乙丙。",
    "",
    "3. 依据材料,下列正确的是（ ）",
    "A. ①",
    "4. 依据材料,错误的是（ ）",
    "A. 甲",
    "",
    "## 参考答案",
    "1.【答案】A",
    "",
    "【解析】第一题解析正文。",
    "2.【答案】B",
    "",
    "【解析】第二题解析正文。",
    "3.【答案】C",
    "4.【答案】D",
]

SYNTH_MAN = {
    "units": [
        {"unit_id": "Q1", "unit_type": "standalone_question",
         "question_numbers": [1], "original_question_type": "single_choice",
         "stem_lines": [5, 9], "options_lines": [8, 9],
         "answer_lines": [25, 25], "explanation_lines": [27, 27]},
        {"unit_id": "Q2", "unit_type": "standalone_question",
         "question_numbers": [2], "original_question_type": "single_choice",
         "stem_lines": [11, 13], "options_lines": [12, 13],
         "answer_lines": [28, 28], "explanation_lines": [30, 30]},
        {"unit_id": "U3-4", "unit_type": "composite_question",
         "question_numbers": [3, 4], "original_question_type": "short_answer",
         "material_lines": [16, 17], "questions_lines": [19, 22],
         "answer_lines": [31, 32], "explanation_lines": None},
    ]
}


# ------------------------------------------------------------------ staging

def _v2_man():
    man = copy.deepcopy(SYNTH_MAN)
    qi.assign_identity(man, list(SYNTH_LINES))
    for u in man["units"]:
        u["basis"] = "printed_as_is"
        u["printed_provenance"] = "source_line"
        u["printed_number"] = list(u["question_numbers"])
    return man


def stage_repo(base: Path):
    """在 base 下生成与生产同构的四件套(源/manifest/annotated/切片)。

    返回 dict:src / man / md(切片) / out_dir。
    """
    base = Path(base)
    base.mkdir(parents=True, exist_ok=True)
    lines = list(SYNTH_LINES)
    man = _v2_man()
    src = base / "synthetic.md"
    src.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="")
    out_dir = base / "out"
    out_dir.mkdir(exist_ok=True)
    mf = out_dir / "synthetic.manifest.json"
    man_full = dict(man)
    man_full["source_file"] = str(src)
    mf.write_text(json.dumps(man_full, ensure_ascii=False, indent=1),
                  encoding="utf-8", newline="")
    issues, summary = rp.validate_manifest(man, len(lines), lines)
    rp.write_outputs(out_dir, "synthetic", lines, man, issues, summary,
                     src.name, src)
    return {"src": src, "man": mf, "md": out_dir / "synthetic.md",
            "out_dir": out_dir}


def _man_edit(repo, fn):
    man = json.loads(repo["man"].read_text(encoding="utf-8"))
    fn(man)
    repo["man"].write_text(json.dumps(man, ensure_ascii=False, indent=1),
                           encoding="utf-8", newline="")


def _src_edit(repo, fn):
    lines = repo["src"].read_text(encoding="utf-8").splitlines()
    lines = fn(lines)
    repo["src"].write_text("\n".join(lines) + "\n", encoding="utf-8",
                           newline="")


# ------------------------------------------------------------------ 观测器

def observe(repo, resolve_first=False):
    """黑盒观测一个 staged 仓库:resolver disposition / qc verdict / F1。"""
    md = repo["md"]
    obs = {}
    try:
        rec = rr.resolve_file(md)
        obs["resolver"] = rec["disposition"]
        if rec.get("reasons"):
            obs["resolver_reason_head"] = rec["reasons"][0]
        obs["resolver_content_q1_stem"] = (
            (rec.get("ir") or {}).get("units") or [{}])[0].get(
                "content", {}).get("stem_lines")
    except Exception as e:  # noqa: BLE001  崩溃本身就是要测的事实
        obs["resolver"] = "CRASH"
        obs["resolver_exc"] = f"{type(e).__name__}: {e}"
    try:
        obs["qc"] = qc.check(md)["verdict"]
    except Exception as e:  # noqa: BLE001
        obs["qc"] = "CRASH"
        obs["qc_exc"] = f"{type(e).__name__}: {e}"

    ir_path = None
    if resolve_first:
        ir_dir = repo["out_dir"] / "ir"
        try:
            rr.run([md], ir_dir)
            ir_path = ir_dir / "resolver_ir.json"
        except Exception:  # noqa: BLE001
            obs["ir_run"] = "CRASH"
    try:
        idx = af1.build_ir_index(ir_path) if ir_path else None
        f = af1.check_file(md, idx)
        obs["f1"] = f["status"]
        obs["f1_drift_zones"] = sorted({
            f"{z.get('status')}:{k}"
            for r in f["units"]
            for k, z in list(r["annotated"].items())
            + list(r["slice"].items())
            + ([("ir", r["ir"])] if "ir" in r else [])
            if isinstance(z, dict) and z.get("status") == "DRIFT"})
        if "ir" in (f["units"] or [{}])[0]:
            obs["f1_ir_zone"] = f["units"][0]["ir"]
    except Exception as e:  # noqa: BLE001
        obs["f1"] = "CRASH"
        obs["f1_exc"] = f"{type(e).__name__}: {e}"
        obs["f1_trace"] = traceback.format_exc()[-500:]
    return obs


def silent_pass(obs):
    """静默放行 = resolver 拒收面(非 ADMITTED*)之外无任何防线报警。"""
    admitted = str(obs.get("resolver", "")).startswith("ADMITTED")
    return admitted and obs.get("qc") == "PASS" and obs.get("f1") == "MATCH"


# ------------------------------------------------------------------ 攻击面

def attack_A(workdir):
    """A 字节事实保持:改源字节(行数不变)→ 预期不得静默 PASS。"""
    out = {}

    # A1 题干行内字节篡改(行数不变,span 仍在界内)
    r = stage_repo(workdir / "A1")
    _src_edit(r, lambda ls: [l.replace("下列说法正确的是",
                                       "【篡改】说法正确的是")
                             if i == 5 else l for i, l in enumerate(ls)])
    out["A1_stem_byte_edit"] = observe(r)

    # A2 span 外行篡改(L2 空行→文本):测 C8 是否整文件口径
    r = stage_repo(workdir / "A2")
    _src_edit(r, lambda ls: ["MUTATED-OUTSIDE-SPAN" if i == 1 else l
                             for i, l in enumerate(ls)])
    out["A2_outside_span_edit"] = observe(r)

    # A3 旧 IR + 篡改源:F1 --ir 对账必须报 DRIFT(source_version 漂移)。
    # 关键:IR 产出于**原始源**,篡改后用该旧 IR 索引跑 F1 三方对账。
    r = stage_repo(workdir / "A3")
    ir_dir = r["out_dir"] / "ir"
    rr.run([r["md"]], ir_dir)  # 原始源上产出 IR
    _src_edit(r, lambda ls: [l.replace("第二题题干", "【篡改】第二题题干")
                             if i == 10 else l for i, l in enumerate(ls)])
    idx = af1.build_ir_index(ir_dir / "resolver_ir.json")
    fr = af1.check_file(r["md"], idx)
    out["A3_stale_ir_then_edit"] = {
        "resolver": "see A1 family (source edited, C8 same)",
        "f1": fr["status"],
        "f1_ir_zone": (fr["units"][0].get("ir")
                       if fr["units"] else None),
    }
    return out


def attack_B(workdir):
    """B Span 边界:start-1 / end+1 → 不得静默裁剪。"""
    out = {}

    # B1 start-1(界内平移)
    r = stage_repo(workdir / "B1")
    _man_edit(r, lambda m: m["units"][0].__setitem__("stem_lines", [4, 9]))
    out["B1_start_minus_1_in_bounds"] = observe(r)

    # B2 end+1(越界)
    r = stage_repo(workdir / "B2")
    _man_edit(r, lambda m: m["units"][0].__setitem__(
        "stem_lines", [5, len(SYNTH_LINES) + 1]))
    out["B2_end_plus_1_oob"] = observe(r)

    # B3 answer end+1(界内,吸入 L26 空行)
    r = stage_repo(workdir / "B3")
    _man_edit(r, lambda m: m["units"][0].__setitem__(
        "answer_lines", [25, 26]))
    out["B3_answer_end_plus_1_in_bounds"] = observe(r)
    return out


def attack_C(workdir):
    """C provenance 断裂:断 source 指针 / 篡 IR provenance → fail-closed。"""
    out = {}

    # C1 manifest 缺 source_file 键(provenance 断裂)
    r = stage_repo(workdir / "C1")
    _man_edit(r, lambda m: m.pop("source_file"))
    out["C1_manifest_no_source_file"] = observe(r)

    # C2 source_file 重定向到诱饵文件(同存在、内容不同)
    r = stage_repo(workdir / "C2")
    decoy = r["out_dir"].parent / "decoy.md"
    decoy.write_text("\n".join(["诱饵行"] * len(SYNTH_LINES)) + "\n",
                     encoding="utf-8", newline="")
    _man_edit(r, lambda m: m.__setitem__("source_file", str(decoy)))
    out["C2_source_retarget_decoy"] = observe(r)

    # C3 IR provenance.source_version 被删 → F1 --ir 必须 DRIFT
    r = stage_repo(workdir / "C3")
    ir_dir = r["out_dir"] / "ir"
    rr.run([r["md"]], ir_dir)
    ir_path = ir_dir / "resolver_ir.json"
    doc = json.loads(ir_path.read_text(encoding="utf-8"))
    for f in doc["files"]:
        if f.get("ir"):
            for u in f["ir"]["units"]:
                u["provenance"].pop("source_version", None)
    ir_path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n",
                       encoding="utf-8", newline="")
    idx = af1.build_ir_index(ir_path)
    fr = af1.check_file(r["md"], idx)
    out["C3_ir_provenance_deleted"] = {
        "f1": fr["status"],
        "f1_ir_zone": fr["units"][0].get("ir"),
    }
    return out


def attack_D(workdir):
    """D Resolver↔QC 分叉:只改 manifest 重切、不重编译工件。"""
    out = {}

    # D1 交换 Q1/Q2 answer_lines(答案归属错位;切片/annotated 不变)
    r = stage_repo(workdir / "D1")
    _man_edit(r, lambda m: (
        m["units"][0].__setitem__("answer_lines", [28, 28]),
        m["units"][1].__setitem__("answer_lines", [25, 25])))
    out["D1_recut_no_recompile"] = observe(r)
    # 事实漂移坐实:IR 里 Q1 的答案内容 = 源 L28(错归属)
    out["D1_ir_q1_answer"] = None
    try:
        rec = rr.resolve_file(r["md"])
        for u in (rec.get("ir") or {}).get("units") or []:
            if u["unit_id"] == "Q1":
                out["D1_ir_q1_answer"] = u["content"].get("answer_lines")
    except Exception:  # noqa: BLE001
        pass

    # D2 对照组:未变异 → 全绿(MATCH/ADMITTED/PASS)
    r = stage_repo(workdir / "D2")
    out["D2_control_untouched"] = observe(r)
    return out


def run_attacks(workdir: Path):
    workdir = Path(workdir)
    if workdir.exists():
        shutil.rmtree(workdir, ignore_errors=True)
    workdir.mkdir(parents=True, exist_ok=True)
    return {
        "attack_version": ATTACK_VERSION,
        "parser_coverage": {
            "parser": "staged mutation harness + SUT black-box observation",
            "supports": ["synthetic v2 full-chain staged attacks",
                         "resolver/qc/f1 three-layer observation",
                         "read-only corpus F1 recheck (--corpus)"],
            "does_not_support": ["source recompile attacks",
                                 "semantic adjudication", "LLM output attacks"],
        },
        "A_byte_fact": attack_A(workdir / "A"),
        "B_span_boundary": attack_B(workdir / "B"),
        "C_provenance_break": attack_C(workdir / "C"),
        "D_resolver_qc_divergence": attack_D(workdir / "D"),
    }


# ------------------------------------------------------------------ 语料复核

def corpus_recheck():
    """--corpus:88 份真实控制组 F1 只读复核(R54 基线复证)。

    Input Integrity Gate 内建于 audit_f1_consistency.run。
    """
    pf = ROOT / "data/resolver_contract_preflight.json"
    if not pf.exists():
        return {"status": "SKIPPED", "reason": "preflight missing"}
    doc = json.loads(pf.read_text(encoding="utf-8"))
    paths = [ROOT / row["file"] for row in doc.get("rows", [])
             if (ROOT / row["file"]).exists()]
    if not paths:
        return {"status": "SKIPPED", "reason": "corpus absent (CI)"}
    out_dir = ROOT / ".pytest_work" / "r60_corpus_f1"
    rep = af1.run(paths, out_dir)
    s = rep["summary"]
    return {
        "status": "OK",
        "files": {"numerator": s["files_match"]["numerator"],
                  "denominator": s["files_match"]["denominator"]},
        "units": {"numerator": s["units_match"]["numerator"],
                  "denominator": s["units_match"]["denominator"]},
        "units_drift": s["units_drift"],
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/r60_fact_drift_attack.json")
    ap.add_argument("--workdir", default=".pytest_work/r60_attack")
    ap.add_argument("--corpus", action="store_true")
    args = ap.parse_args(argv)
    report = run_attacks(ROOT / args.workdir)
    if args.corpus:
        report["corpus_recheck"] = corpus_recheck()
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8", newline="")
    print(f"wrote {out}")
    return report


if __name__ == "__main__":
    main()

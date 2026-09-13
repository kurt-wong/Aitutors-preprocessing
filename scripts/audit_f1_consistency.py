r"""F1 Structural Consistency Check(R54,用户 R53 裁决:实施,定位 Audit Invariant only)。

背景(R53 F1 边界发现):QC 的裁决对象是**切片 md 锚点标记**(以及 annotated
锚点),而 Resolver 的抽取对象是 **manifest spans + 当前源文件**——二者漂移
(如改 manifest 不重编译切片)时 QC 与 Resolver 双方各自合法,系统整体错误。
该态生产不可产生(pipeline 同编译),但属跨组件一致性风险(consumer
boundary integrity failure)。

**定位(用户裁定原文级)**:Audit invariant only——
  - 不是 Resolver admission rule(Resolver 不得变成第二套 QC);
  - 不升硬 Gate;
  - 只比较结构一致性四项:source_version_sha / start_line / end_line /
    span hash;
  - 不检查语义正确性、题目完整性、答案合理性(属 QC / Admission)。

三方对象:
  - resolver 侧 = manifest spans 应用于当前源文件(与 resolver_reference
    同一取数方式:strip_meta 后按行切片);
  - QC 侧(两份独立工件):
      ① annotated.md 的 META 锚点区间(锚点位置 = 行号锚定事实,
         区间内文本 = 编译时刻源行的逐字留档);
      ② 切片 md 的区文本(题干区/答案区/详解区,QC C1/C3/C7 的裁决对象)。
  - (可选 --ir)Resolver 运行时刻的 provenance(source_version /
    source_lines)与当前 manifest/源的三方对账。

期望值为独立重实现(不 import reslice_pipeline.compile_slices):若重实现
与生产编译语义有出入,88 份真实语料控制组会立即暴露(0 DRIFT 是实证要求,
不是假设)。

输出(--out 内,确定性,无时间戳):f1_report.json
  每单元一行:{question_id, question_numbers, source_version_sha,
    annotated: {zone: {manifest_lines, annotated_lines, resolver_span_hash,
                       qc_span_hash, status}},
    slice:    {zone: {resolver_hash, qc_hash, status}},
    status: MATCH | DRIFT}
  汇总按 review_protocol 规则 4 带 numerator/denominator/proof。

用法:
  python scripts/audit_f1_consistency.py \
      --preflight data/resolver_contract_preflight.json --out <dir> \
      [--ir data/resolver_ref_r52/resolver_ir.json]
  python scripts/audit_f1_consistency.py --inputs a.md b.md --out <dir>
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import audit_integrity as ai  # noqa: E402  Input Integrity Gate
from fix_bug22_renumber import strip_meta  # noqa: E402
from prereview_check import parse_answer_tables, parse_range_answers  # noqa: E402

F1_VERSION = "f1-consistency-0.1"
META_RE = re.compile(r"^\s*<!--\s*META:")
ANCHOR_RE = re.compile(r"^\s*<!--\s*META:(\w+):(start|end):(\S+?)(?:\s.*?)?-->\s*$")
ZONE_KINDS = ("stem", "options", "material", "questions",
              "answer", "explanation", "extra")
Z_BEGIN, Z_END = "“题干区开始”", "“题干区结束”"
A_BEGIN, A_END = "“答案区开始”", "“答案区结束”"
E_BEGIN, E_END = "“详解区开始”", "“详解区结束”"


def _sha_lines(lines) -> str:
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def _norm(lines):
    """归一化:去首尾空白、丢空行(屏蔽编译期空串 join 产物)。"""
    return [l.strip() for l in lines if l.strip()]


def _span_lines(lines, rg):
    if (isinstance(rg, list) and len(rg) == 2
            and all(isinstance(x, int) for x in rg)
            and 1 <= rg[0] <= rg[1] <= len(lines)):
        return lines[rg[0] - 1:rg[1]]
    return None  # 越界/非法 = 与 Resolver STALE 同族的结构信号


# ---------------------------------------------------------------- annotated

def parse_anchors(ann_text):
    """annotated.md → {(kind, tag): [(start_line, end_line), ...]}(文档序)。

    行号 = 去掉 META 行后的源行序号(与 C8 的口径一致)。
    开/闭按 (kind, tag) 栈配对(编译器保证同点 LIFO 合法嵌套)。
    另返回 unpaired 残留(锚点不配对 = 结构漂移信号)。
    """
    anchors, unpaired = {}, []
    stack = {}
    counter = 0
    for ln in ann_text.splitlines():
        m = ANCHOR_RE.match(ln)
        if not m:
            if not META_RE.match(ln):
                counter += 1
            continue
        kind, pos, tag = m.group(1), m.group(2), m.group(3)
        if kind in ("annotation", "doc"):
            continue
        if pos == "start":
            stack.setdefault((kind, tag), []).append(counter + 1)
        else:
            st = stack.get((kind, tag))
            if st:
                s = st.pop(0) if len(st) > 1 else st.pop()
                anchors.setdefault((kind, tag), []).append((s, counter))
            else:
                unpaired.append(f"{kind}:end:{tag} 无配对 start")
    for (kind, tag), st in stack.items():
        for s in st:
            unpaired.append(f"{kind}:start:{tag}@{s} 无配对 end")
    return anchors, unpaired


# ------------------------------------------------------------ slice 期望值
# 独立重实现 compile_slices 的确定性部分(不 import 生产模块)。

def expected_stem_zone(lines, u):
    parts = []
    if u.get("unit_type") == "composite_question":
        mat, que = u.get("material_lines"), u.get("questions_lines")
        parts += _span_lines(lines, mat) or []
        if que:
            qs, qe = que
            rem_start = max(qs, (mat[1] + 1) if mat else qs)
            if rem_start <= qe:
                parts += lines[rem_start - 1:qe]
        parts += _span_lines(lines, u.get("extra_lines")) or []
    else:
        parts += _span_lines(lines, u.get("stem_lines")) or []
        parts += _span_lines(lines, u.get("options_lines")) or []
        parts += _span_lines(lines, u.get("extra_lines")) or []
    return parts


def expected_answer_zone(lines, u, tbl_ans, rng_ans):
    rg = u.get("answer_lines")
    ans_lines = _span_lines(lines, rg) if rg else None
    ans_span = "\n".join(ans_lines) if ans_lines else ""
    loc_tbl = parse_answer_tables(ans_span) if ans_span else {}
    loc_rng = parse_range_answers(ans_span) if ans_span else {}
    values = {str(n): loc_tbl.get(n) or loc_rng.get(n)
                        or tbl_ans.get(n) or rng_ans.get(n)
              for n in (u.get("question_numbers") or [])}
    values = {k: v for k, v in values.items() if v}
    loc_nums = set(loc_tbl) | set(loc_rng)
    shared = bool(loc_nums) and not loc_nums <= set(u.get("question_numbers")
                                                    or [])
    out = []
    if values:
        out.append(" ".join(f"{k}.{v}" for k, v in
                            sorted(values.items(), key=lambda x: int(x[0]))))
    if ans_span:
        if shared:
            out.append(f"<!-- 源答案区 L{rg[0]:04d}-L{rg[1]:04d} 为多题共享"
                       f"（答案表/区间连写），已按题号取值，不整段回引 -->")
        else:
            out += ans_lines
    return out, shared


def _zone_from_block(block, b_mark, e_mark):
    """从切片单元块提取区文本行。b_mark=None 表示块首(题干区开始标记
    已被外层 split 消费)。"""
    if b_mark is None:
        body = block
    else:
        if b_mark not in block:
            return None
        body = block.split(b_mark, 1)[1]
    if e_mark not in body:
        return None
    return body.split(e_mark, 1)[0].splitlines()


# --------------------------------------------------------------- 单元检查

def check_unit(u, lines, anchors, consumed, block, tbl_ans, rng_ans,
               src_sha, ir_unit=None):
    """一个 manifest 单元的 F1 对账。返回单元 row。"""
    nums_s = ",".join(str(n) for n in (u.get("question_numbers") or []))
    uid = u.get("unit_id")
    ann_zone, sl_zone = {}, {}

    # ---- ① annotated 锚点 vs manifest spans(行号 + span hash)----
    for kind in ZONE_KINDS:
        rg = u.get(f"{kind}_lines")
        if rg is None:
            # 本单元无该 span:同题号键的锚点属于其他持有该 span 的单元
            # (汇编卷题号跨块重复),不得消费、不得判漂移。
            continue
        key = (kind, nums_s)
        recs = anchors.get(key) or []
        idx = consumed.get(key, 0)
        a_rec = recs[idx] if idx < len(recs) else None
        if _span_lines(lines, rg) is None:
            ann_zone[kind] = {"manifest_lines": rg, "status": "DRIFT",
                              "reason": "manifest span 越界(结构 STALE 信号)"}
            continue
        consumed[key] = idx + 1
        r_hash = _sha_lines(_norm(_span_lines(lines, rg)))
        if a_rec is None:
            ann_zone[kind] = {"manifest_lines": rg,
                              "resolver_span_hash": r_hash,
                              "status": "DRIFT",
                              "reason": "annotated 缺锚点(工件与 manifest 漂移)"}
            continue
        a_lines = a_rec[1] - a_rec[0] + 1
        q_hash = _sha_lines(_norm(_span_lines(ANN_SRC["lines"], list(a_rec))))
        status = ("MATCH" if (list(a_rec) == list(rg) and r_hash == q_hash)
                  else "DRIFT")
        ann_zone[kind] = {"manifest_lines": list(rg),
                          "annotated_lines": list(a_rec),
                          "resolver_span_hash": r_hash,
                          "qc_span_hash": q_hash,
                          "status": status}
        _ = a_lines

    # ---- ② 切片区文本 vs manifest spans + 当前源(内容 hash)----
    if block is not None:
        b = _norm(expected_stem_zone(lines, u))
        a = _norm(_zone_from_block(block, None, Z_END) or [])
        sl_zone["stem_zone"] = {
            "resolver_hash": _sha_lines(b), "qc_hash": _sha_lines(a),
            "status": "MATCH" if b == a else "DRIFT"}
        exp_ans, shared = expected_answer_zone(lines, u, tbl_ans, rng_ans)
        act_ans = _zone_from_block(block, A_BEGIN, A_END)
        if act_ans is None:
            sl_zone["answer_zone"] = {"status": "DRIFT",
                                      "reason": "切片缺答案区标记"}
        else:
            act_n = _norm(act_ans)
            exp_n = _norm(exp_ans)
            if shared:
                # 共享答案表:切片只留 L 区间注释,内容 hash 不可比 →
                # 注释行逐字比对(行号锚定),内容项如实标 UNCOMPARABLE。
                ok = act_n == exp_n
                sl_zone["answer_zone"] = {
                    "resolver_hash": _sha_lines(exp_n),
                    "qc_hash": _sha_lines(act_n),
                    "status": "MATCH" if ok else "DRIFT",
                    "content": "UNCOMPARABLE(shared answer table, "
                               "range comment only)"}
            else:
                sl_zone["answer_zone"] = {
                    "resolver_hash": _sha_lines(exp_n),
                    "qc_hash": _sha_lines(act_n),
                    "status": "MATCH" if exp_n == act_n else "DRIFT"}
        exp_e = _span_lines(lines, u.get("explanation_lines"))
        act_e = _zone_from_block(block, E_BEGIN, E_END)
        if exp_e and act_e is not None:
            e1, e2 = _norm(exp_e), _norm(act_e)
            sl_zone["explanation_zone"] = {
                "resolver_hash": _sha_lines(e1), "qc_hash": _sha_lines(e2),
                "status": "MATCH" if e1 == e2 else "DRIFT"}
        elif exp_e and act_e is None:
            sl_zone["explanation_zone"] = {"status": "DRIFT",
                                           "reason": "manifest 有详解 span "
                                                     "而切片无详解区"}
    else:
        sl_zone["block"] = {"status": "DRIFT", "reason": "切片块数少于单元数"}

    # ---- ③ (可选)Resolver 运行时刻 provenance 对账 ----
    ir_zone = None
    if ir_unit is not None:
        prov = ir_unit.get("provenance") or {}
        ir_zone = {
            "source_version_match":
                prov.get("source_version") == src_sha,
            "source_lines_match":
                prov.get("source_lines")
                == {k: u.get(k) for k in
                    ("stem_lines", "options_lines", "material_lines",
                     "questions_lines", "answer_lines", "explanation_lines")
                    if u.get(k) is not None},
        }
        ir_zone["status"] = ("MATCH" if all(ir_zone.values()) else "DRIFT")

    zones = list(ann_zone.values()) + list(sl_zone.values())
    if ir_zone is not None:
        zones.append(ir_zone)
    drift = any(z.get("status") == "DRIFT" for z in zones)
    row = {"question_id": uid, "question_numbers": u.get("question_numbers"),
           "source_version_sha": src_sha,
           "annotated": ann_zone, "slice": sl_zone}
    if ir_zone is not None:
        row["ir"] = ir_zone
    row["status"] = "DRIFT" if drift else "MATCH"
    return row


# 模块级暂存:check_unit 读取 annotated 源行视图(避免逐层传参噪音)
ANN_SRC = {"lines": []}


def check_file(md_path: Path, ir_index=None):
    """单文件 F1 对账。返回 {file, n_units, units:[rows...], status}。"""
    md_path = Path(md_path)
    man_path = md_path.with_suffix(".manifest.json")
    man = json.loads(man_path.read_text(encoding="utf-8"))
    src = Path(man.get("source_file") or "")
    if not src.exists():
        return {"file": str(md_path), "status": "DRIFT",
                "note": f"source missing: {src}", "units": []}
    lines = strip_meta(src.read_text(encoding="utf-8",
                                     errors="replace")).splitlines()
    src_sha = hashlib.sha256(src.read_bytes()).hexdigest()
    ann_path = md_path.with_name(md_path.stem + ".annotated.md")
    if not ann_path.exists():
        return {"file": str(md_path), "status": "DRIFT",
                "note": "annotated missing", "units": []}
    ANN_SRC["lines"] = [l for l in ann_path.read_text(
        encoding="utf-8", errors="replace").splitlines()
        if not META_RE.match(l)]
    anchors, unpaired = parse_anchors(ann_path.read_text(
        encoding="utf-8", errors="replace"))

    text = md_path.read_text(encoding="utf-8", errors="replace")
    blocks = text.split(Z_BEGIN)[1:]

    whole = "\n".join(lines)
    _t = parse_answer_tables(whole)
    _r = parse_range_answers(whole)
    tbl_ans = {n: (_t.get(n) or _r.get(n)) for n in range(1, 1000)
               if _t.get(n) or _r.get(n)}

    consumed = {}
    rows = []
    for i, u in enumerate(man.get("units") or []):
        block = blocks[i] if i < len(blocks) else None
        ir_unit = None
        if ir_index is not None:
            ir_unit = ir_index.get((str(md_path.resolve()),
                                    u.get("unit_id")))
        rows.append(check_unit(u, lines, anchors, consumed, block,
                               tbl_ans, tbl_ans, src_sha, ir_unit))
    leftover = []
    for key, recs in anchors.items():
        n_left = len(recs) - consumed.get(key, 0)
        if n_left > 0 and key[0] in ZONE_KINDS:
            leftover.append(f"{key[0]}:{key[1]} x{n_left}")
    note = []
    if unpaired:
        note.append(f"锚点不配对 {len(unpaired)}: {unpaired[:3]}")
    if leftover:
        note.append(f"annotated 存在未消费锚点(多于 manifest): {leftover[:5]}")
    if len(blocks) != len(man.get("units") or []):
        note.append(f"切片块数 {len(blocks)} != manifest 单元数 "
                    f"{len(man.get('units') or [])}")
    status = "DRIFT" if (any(r["status"] == "DRIFT" for r in rows)
                         or note) else "MATCH"
    return {"file": str(md_path), "n_units": len(rows),
            "n_match": sum(1 for r in rows if r["status"] == "MATCH"),
            "status": status, "notes": note, "units": rows}


def build_ir_index(ir_path):
    """可选:resolver IR → {(resolved_path, unit_id): unit_record}。"""
    if not ir_path:
        return None
    doc = json.loads(Path(ir_path).read_text(encoding="utf-8"))
    idx = {}
    for f in doc.get("files") or []:
        if not f.get("ir"):
            continue
        key_base = str(Path(f["file"]).resolve())
        for u in f["ir"].get("units") or []:
            idx[(key_base, u.get("unit_id"))] = u
    return idx


# ------------------------------------------------- R-ACC-14 消费不变量(审计级)

def audit_ir_answers(doc):
    """R-ACC-14:答案表 unresolved 消费不变量(审计检查器,非 admission)。

    数据形状(R54 真实 IR 实测纠正):IR 单元的 `answers` 字段是解析器
    返回的**整个表对象** `{cells, method, answers, unresolved}`,逐题
    答案映射在其内层 `answers` 键;`unresolved` 同在表对象内(不是单元
    顶层字段)。首版检查器按错误形状编码,真实 IR 上产生 2210 条伪
    findings——审计工具自身缺陷家族(R49/R53 先例),已按真实 schema
    重写并以真实 IR 复验 + 负向对照逐条锁定。

    对每个尝试过答案表解析(answers 非 None)的单元检查:
      I0 表对象必须含内层 answers/unresolved 键(schema 形状);
      I1 内层 answers 键与 unresolved 交集必须为空(同一题不得既"已解"
         又"未解"——下游若优先读 answers,unresolved 就被静默吞掉);
      I2 question_numbers 中未出现在内层 answers 的题号必须全部在
         unresolved(遗漏 = 下游静默丢弃,unresolved 不是可选字段);
      I3 内层 answers 值不得为空串/None 哨兵(下游 `answers.get(q, "")`
         类默认值会把 unresolved 误变成"已解为空"——正是 R-ACC-14
         攻击面;宁缺勿猜与 printed 硬化同律)。
    返回 findings 列表(空 = 不变量成立)。
    """
    findings = []
    for f in doc.get("files") or []:
        if not f.get("ir"):
            continue
        for u in f["ir"].get("units") or []:
            tbl = u.get("answers")
            if tbl is None:
                continue
            uid = u.get("unit_id")
            if not isinstance(tbl, dict) or (
                    "answers" not in tbl and "unresolved" not in tbl):
                findings.append(f"{uid}: shape 表对象缺内层 answers/"
                                f"unresolved 键: {type(tbl).__name__}")
                continue
            ans = tbl.get("answers") or {}
            unres = tbl.get("unresolved") or []
            qnums = {str(q) for q in (u.get("question_numbers") or [])}
            keys = {str(k) for k in ans}
            unres_s = {str(q) for q in unres}
            for k in sorted(keys & unres_s):
                findings.append(f"{uid}: overlap 题{k} 同时在 answers 与 "
                                f"unresolved")
            for q in sorted(qnums - keys - unres_s):
                findings.append(f"{uid}: missing_from_unresolved 题{q} "
                                f"既不在 answers 也不在 unresolved")
            for k, v in ans.items():
                if not isinstance(v, str) or not v.strip():
                    findings.append(f"{uid}: sentinel answers[{k!r}]={v!r} "
                                    f"(空值会被下游默认值误读为已解)")
    return findings


def run(md_paths, out_dir: Path, ir_path=None):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ir_index = build_ir_index(ir_path)

    # Input Integrity Gate:输入面 = 切片 md + manifest + annotated + 源
    inputs, seen = [], set()
    for p in md_paths:
        p = Path(p)
        for q in (p, p.with_suffix(".manifest.json"),
                  p.with_name(p.stem + ".annotated.md")):
            if q.exists() and str(q) not in seen:
                seen.add(str(q))
                inputs.append(q)
        mp = p.with_suffix(".manifest.json")
        if mp.exists():
            s = json.loads(mp.read_text(encoding="utf-8")).get("source_file")
            if s and Path(s).exists() and str(Path(s)) not in seen:
                seen.add(str(Path(s)))
                inputs.append(Path(s))
    gate_before = ai.gate_snapshot(inputs)

    files = [check_file(p, ir_index) for p in md_paths]

    ai.gate_assert_unchanged(gate_before, inputs, "f1_consistency")

    n_files = len(files)
    n_files_match = sum(1 for f in files if f["status"] == "MATCH")
    n_units = sum(f["n_units"] for f in files)
    n_match = sum(f.get("n_match", 0) for f in files)
    n_drift_units = sum(1 for f in files for r in f["units"]
                        if r["status"] == "DRIFT")
    n_uncomparable = sum(1 for f in files for r in f["units"]
                         for z in list(r["annotated"].values())
                         + list(r["slice"].values())
                         if isinstance(z, dict)
                         and str(z.get("content", "")).startswith(
                             "UNCOMPARABLE"))
    report = {
        "f1_version": F1_VERSION,
        "scope": "audit invariant only — not a Gate, not an admission rule;"
                 " structural consistency (source_version_sha / start_line /"
                 " end_line / span hash); semantics belong to QC/Admission",
        "ir_crosscheck": bool(ir_path),
        "summary": {
            "files_match": {"numerator": n_files_match,
                            "denominator": n_files,
                            "proof": "per-file status = MATCH iff no unit "
                                     "DRIFT and no structural note"},
            "units_match": {"numerator": n_match, "denominator": n_units,
                            "proof": "annotated anchor (line+hash) + slice "
                                     "zone text vs manifest spans on current"
                                     " source"},
            "units_drift": n_drift_units,
            "zones_uncomparable": n_uncomparable,
        },
        "files": files,
    }
    (out_dir / "f1_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8", newline="")
    # 紧凑 summary(入库):全量逐单元明细报告按 R52 先例以 sha256 引用,
    # 不入库(4.8MB,可从冻结基线字节级复现)。
    full_bytes = (out_dir / "f1_report.json").read_bytes()
    summary_doc = {
        "f1_version": F1_VERSION,
        "scope": report["scope"],
        "ir_crosscheck": report["ir_crosscheck"],
        "summary": report["summary"],
        "full_report": {"path": "f1_report.json",
                        "sha256": hashlib.sha256(full_bytes).hexdigest()},
        "files": [{k: f.get(k) for k in
                   ("file", "n_units", "n_match", "status", "notes")}
                  for f in files],
    }
    (out_dir / "f1_summary.json").write_text(
        json.dumps(summary_doc, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8", newline="")
    return report


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--preflight")
    ap.add_argument("--inputs", nargs="*", default=[])
    ap.add_argument("--ir")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    paths = [ROOT / p for p in args.inputs]
    if args.preflight:
        pf = json.loads((ROOT / args.preflight).read_text(encoding="utf-8"))
        paths += [ROOT / r["file"] for r in pf.get("rows", [])]
    report = run(paths, Path(args.out),
                 ir_path=ROOT / args.ir if args.ir else None)
    print(json.dumps(report["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
r"""
p2_1_measure.py — Phase P2.1 批量切分结果度量(最小闭环版)

输入:抽样清单 JSON + reslice 输出目录。
输出:逐卷指标 + 汇总 + (可选)人工抽检清单。

指标口径(governance/phase_p2_charter.md §7 用户裁定):
  - 卷级成功率 = manifest 存在且 validation_issues 为空 的卷数 / 批卷数
  - 答案齐全率 = answer_lines 非空的问题单元 / 全部问题单元
  - admission_ready_rate = stem非空 ∧ answer可定位 ∧ source anchor有效 ∧ 题型可判断
  - 答案可信度分桶(启发式,基于行区间引用而非 LLM 生成文本):
      exact   = 独立题且答案区间有内容
      partial = 组合题答案区间缺失部分小问标记
      suspect = 组合题 stem 无小问标记(疑似拍平,交人工)
      missing = 无 answer_lines
  - sub_question_integrity = 组合题 stem 保留 (1)(2)(3) 小问层级的比例
  - 图片依赖基线 = stem 区间含 <img/![ 的题数(P2.2 目标输入)
  - 题号覆盖 = question_numbers 并集跨度与缺号列表(供人工复核)

用法:
  python scripts/p2_1_measure.py --batch data/p2_1_batch1.json \
      --out Ocr-markdown/reslice-p2-b1 --result data/p2_1_b1_measure.json \
      [--human-sample data/p2_1_b1_human_review.json]
"""

import argparse
import io
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Ocr-markdown"
Q_TYPES = ("standalone_question", "composite_question")
SUB_MARK_RE = re.compile(r"[（(]\s*(\d{1,2})\s*[)）]")
IMG_MARK_RE = re.compile(r"<img\s|!\[[^\]]*\]\(")


def manifest_path_for(out_root: Path, src: str) -> Path:
    p = Path(src)
    try:
        rel = p.relative_to(SRC)
    except ValueError:
        rel = Path(p.name)
    return out_root / rel.parent / f"{p.stem}.manifest.json"


def _span_text(src_lines, span):
    """返回 (ok, text):span 为 [start, end](1-based 闭区间)。"""
    if not span or not isinstance(span, (list, tuple)) or len(span) != 2:
        return False, ""
    s, e = span
    if not (isinstance(s, int) and isinstance(e, int) and 1 <= s <= e <= len(src_lines)):
        return False, ""
    return True, "\n".join(src_lines[s - 1:e])


def _credibility(unit, src_lines):
    """启发式答案可信度分桶(见模块 docstring)。"""
    ok, ans = _span_text(src_lines, unit.get("answer_lines"))
    if not (ok and ans.strip()):
        return "missing"
    if unit.get("unit_type") != "composite_question":
        return "exact"
    stem_ok, stem = _span_text(src_lines, unit.get("stem_lines"))
    stem_subs = {int(m) for m in SUB_MARK_RE.findall(stem)} if stem_ok else set()
    ans_subs = {int(m) for m in SUB_MARK_RE.findall(ans)}
    if not stem_subs:
        return "suspect"          # 组合题 stem 无小问标记:疑似拍平
    if stem_subs <= ans_subs:
        return "exact"
    return "partial"              # 答案缺部分小问


def measure_paper(out_root: Path, entry: dict) -> dict:
    src = entry["file"]
    mp = manifest_path_for(out_root, src)
    rec = {"file": src, "subject": entry.get("subject"),
           "manifest_exists": mp.exists()}
    if not mp.exists():
        rec["status"] = "NO_MANIFEST"
        return rec
    man = json.loads(mp.read_text(encoding="utf-8"))
    units = man.get("units") or []
    qs = [u for u in units if u.get("unit_type") in Q_TYPES]

    # 源文行(行区间真实性校验用;读不到不猜,显式标记)
    try:
        sp = Path(src)
        try:
            rel = sp.relative_to(SRC)
        except ValueError:
            rel = Path(sp.name)
        src_lines = (SRC / rel).read_text(encoding="utf-8", errors="replace").splitlines()
        source_readable = True
    except OSError:
        src_lines, source_readable = [], False

    answered = [u for u in qs if u.get("answer_lines")]
    nums = sorted({n for u in qs for n in (u.get("question_numbers") or [])})
    meta = man.get("annotation_meta") or {}

    admission, cred, comp_total, comp_intact, img_dep = 0, {}, 0, 0, 0
    for u in qs:
        stem_ok, stem = _span_text(src_lines, u.get("stem_lines"))
        ans_ok, ans = _span_text(src_lines, u.get("answer_lines"))
        anchor_ok = (stem_ok and stem.strip()) if source_readable else bool(u.get("stem_lines"))
        answer_loc = (ans_ok and ans.strip()) if source_readable else bool(u.get("answer_lines"))
        type_ok = bool(u.get("original_question_type"))
        if anchor_ok and answer_loc and type_ok:
            admission += 1
        bucket = _credibility(u, src_lines) if source_readable else \
            ("missing" if not u.get("answer_lines") else "unverifiable")
        cred[bucket] = cred.get(bucket, 0) + 1
        if u.get("unit_type") == "composite_question":
            comp_total += 1
            if stem_ok and len({int(m) for m in SUB_MARK_RE.findall(stem)}) >= 2:
                comp_intact += 1
        if stem_ok and IMG_MARK_RE.search(stem):
            img_dep += 1

    rec.update({
        "status": "OK" if not meta.get("validation_issues") else "VALIDATION_ISSUES",
        "source_readable": source_readable,
        "units": len(units),
        "questions": len(qs),
        "answered": len(answered),
        "answer_rate": round(len(answered) / len(qs), 4) if qs else None,
        "admission_ready": admission,
        "admission_ready_rate": round(admission / len(qs), 4) if qs else None,
        "answer_credibility": cred,
        "composite_total": comp_total,
        "composite_intact": comp_intact,
        "sub_question_integrity": round(comp_intact / comp_total, 4) if comp_total else None,
        "image_dependent_questions": img_dep,
        "qnum_min": nums[0] if nums else None,
        "qnum_max": nums[-1] if nums else None,
        "qnum_missing": [n for n in range(nums[0], nums[-1] + 1)
                         if n not in nums] if nums else [],
        "validation_issues": meta.get("validation_issues") or [],
        "warnings": len(meta.get("warnings") or []),
    })
    return rec


def build_human_sample(out_root: Path, entries, per_paper: int = 10) -> dict:
    """确定性人工抽检清单:每卷取 per_paper 道题(按 unit_id 稳定散列取前 N)。"""
    import hashlib
    sample = []
    for e in entries:
        mp = manifest_path_for(out_root, e["file"])
        if not mp.exists():
            continue
        man = json.loads(mp.read_text(encoding="utf-8"))
        qs = [u for u in (man.get("units") or []) if u.get("unit_type") in Q_TYPES]
        ranked = sorted(qs, key=lambda u: hashlib.sha256(
            (e["file"] + "|" + str(u.get("unit_id"))).encode("utf-8")).hexdigest())
        for u in ranked[:per_paper]:
            sample.append({
                "file": e["file"], "subject": e.get("subject"),
                "unit_id": u.get("unit_id"),
                "question_numbers": u.get("question_numbers"),
                "unit_type": u.get("unit_type"),
                "stem_lines": u.get("stem_lines"),
                "answer_lines": u.get("answer_lines"),
            })
    return {"per_paper": per_paper, "papers": len({s["file"] for s in sample}),
            "questions": len(sample), "items": sample}


def main():
    global SRC
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", default=str(ROOT / "data/p2_1_batch1.json"))
    ap.add_argument("--out", default=str(SRC / "reslice-p2-b1"))
    ap.add_argument("--result", default=str(ROOT / "data/p2_1_b1_measure.json"))
    ap.add_argument("--src", default=str(SRC), help="源语料根(默认 Ocr-markdown)")
    ap.add_argument("--human-sample", default=None,
                    help="输出人工抽检清单 JSON 路径(每卷 10 题,确定性)")
    args = ap.parse_args()

    SRC = Path(args.src)

    entries = json.loads(Path(args.batch).read_text(encoding="utf-8"))
    out_root = Path(args.out)
    papers = [measure_paper(out_root, e) for e in entries]

    total = len(papers)
    ok = sum(1 for p in papers if p["status"] == "OK")
    no_man = sum(1 for p in papers if p["status"] == "NO_MANIFEST")
    vi = sum(1 for p in papers if p["status"] == "VALIDATION_ISSUES")
    tq = sum(p.get("questions") or 0 for p in papers)
    ta = sum(p.get("answered") or 0 for p in papers)
    tadm = sum(p.get("admission_ready") or 0 for p in papers)
    tcomp = sum(p.get("composite_total") or 0 for p in papers)
    tci = sum(p.get("composite_intact") or 0 for p in papers)
    timg = sum(p.get("image_dependent_questions") or 0 for p in papers)
    cred = {}
    for p in papers:
        for k, v in (p.get("answer_credibility") or {}).items():
            cred[k] = cred.get(k, 0) + v
    by_subject = {}
    for p in papers:
        s = by_subject.setdefault(p["subject"], {"papers": 0, "ok": 0, "questions": 0,
                                                "admission_ready": 0})
        s["papers"] += 1
        s["ok"] += (p["status"] == "OK")
        s["questions"] += p.get("questions") or 0
        s["admission_ready"] += p.get("admission_ready") or 0

    report = {
        "schema_version": 2,
        "batch": os.path.abspath(args.batch),
        "out": os.path.abspath(args.out),
        "totals": {
            "papers": total, "ok": ok,
            "validation_issues": vi, "no_manifest": no_man,
            "parse_success_rate": round(ok / total, 4) if total else None,
            "questions": tq, "answered": ta,
            "answer_rate": round(ta / tq, 4) if tq else None,
            "admission_ready": tadm,
            "admission_ready_rate": round(tadm / tq, 4) if tq else None,
            "answer_credibility": cred,
            "composite_total": tcomp, "composite_intact": tci,
            "sub_question_integrity": round(tci / tcomp, 4) if tcomp else None,
            "image_dependent_questions": timg,
        },
        "by_subject": by_subject,
        "papers": papers,
    }
    Path(args.result).parent.mkdir(parents=True, exist_ok=True)
    with io.open(args.result, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
        f.write("\n")
    t = report["totals"]
    print("papers={papers} ok={ok} vi={validation_issues} no_manifest={no_manifest} "
          "parse_success={parse_success_rate} questions={questions} "
          "answer_rate={answer_rate} admission_ready_rate={admission_ready_rate} "
          "sub_q_integrity={sub_question_integrity} img_dep={image_dependent_questions}".format(**t))
    print("credibility=" + json.dumps(cred, ensure_ascii=False))
    print("result: " + args.result)

    if args.human_sample:
        hs = build_human_sample(out_root, entries)
        Path(args.human_sample).parent.mkdir(parents=True, exist_ok=True)
        with io.open(args.human_sample, "w", encoding="utf-8") as f:
            json.dump(hs, f, ensure_ascii=False, indent=1)
            f.write("\n")
        print("human_sample: papers={papers} questions={questions} -> {path}".format(
            path=args.human_sample, **hs))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()

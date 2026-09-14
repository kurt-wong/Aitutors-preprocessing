# -*- coding: utf-8 -*-
r"""
p2_2_image_baseline.py — P2.2 图片绑定 baseline(charter §11.2,只回答三个问题)

① 图片识别率:img 依赖题(与 p2_1_measure.img_dep 同口径:stem/材料行区间命中
   `<img` 或 `![...](`)中,(a) 持有 ≥1 条图片引用,(b) ≥1 条引用可解析
   (相对源 md 所在目录解析后文件真实存在)的比例;
② 图片归属确定性事实:引用落在哪个绑定区(stem / material)、同一图片被 ≥2 题
   引用(共享)、题面之外的引用细分——落在答案/解析区(记 unit 归属)与真孤儿
   (所有单元区间外,附最近单元行距;gap≤3 记 adjacent,即"贴题未圈入"信号)。
   "这张图是不是属于这个题"的对错判定由人工审核单完成,LLM 不参与(charter §11.2);
③ V3 消费方式:结论由报告 + 台账给出,本脚本不做 schema 变更。

口径:不猜、不修复——引用解析失败如实计 broken;无 manifest 的卷如实跳过。

用法:
  python scripts/p2_2_image_baseline.py \
      --batch data/p2_1_batch1.json --out Ocr-markdown/reslice-p2-b1 \
      --result data/p2_2_image_baseline.json \
      --review-html data/p2_2_image_review.html --sample-size 24
"""

import argparse
import datetime
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Ocr-markdown"
Q_TYPES = ("standalone_question", "composite_question")

HTML_IMG_REF_RE = re.compile(r'<img[^>]*?\bsrc="([^"]+)"')
MD_IMG_REF_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def extract_refs(text):
    """一行文本里的全部图片引用(HTML <img src> 与 markdown ![]() 两种形态)。"""
    return HTML_IMG_REF_RE.findall(text) + MD_IMG_REF_RE.findall(text)


def resolve_ref(ref, src_dir):
    """相对引用以源 md 所在目录为基准解析;返回绝对 Path(存在性由调用方判断)。"""
    p = Path(ref)
    if not p.is_absolute():
        p = src_dir / p
    return p


def refs_in_span(lines, span):
    """行区间内的图片引用 → [(lineno, ref), ...];区间非法返回空。"""
    if not span or not isinstance(span, (list, tuple)) or len(span) != 2:
        return []
    s, e = span
    if not (isinstance(s, int) and isinstance(e, int) and 1 <= s <= e <= len(lines)):
        return []
    out = []
    for ln in range(s, e + 1):
        for r in extract_refs(lines[ln - 1]):
            out.append((ln, r))
    return out


def _unit_zones(unit):
    """(stem_zone, material_zone):stem_lines/questions_lines 优先,材料区独立计。"""
    st = unit.get("stem_lines") or unit.get("questions_lines")
    mat = unit.get("material_lines")
    stem_zone = st or mat
    mat_zone = mat if st else None      # stem 已退化到 material 时不重复计
    return stem_zone, mat_zone


def analyze_paper(out_root: Path, entry: dict, src_root: Path) -> dict:
    """单卷图片绑定事实;无 manifest / 源不可读如实标记,不猜。"""
    src = entry["file"]
    p = Path(src)
    try:
        rel = p.relative_to(src_root)
    except ValueError:
        rel = Path(p.name)
    src_path = src_root / rel
    mp = out_root / rel.parent / f"{p.stem}.manifest.json"
    rec = {"file": src, "subject": entry.get("subject"),
           "manifest_exists": mp.exists()}
    if not mp.exists():
        rec["status"] = "NO_MANIFEST"
        return rec

    man = json.loads(mp.read_text(encoding="utf-8"))
    try:
        lines = src_path.read_text(encoding="utf-8", errors="replace").splitlines()
        source_readable = True
    except OSError:
        lines, source_readable = [], False
    src_dir = src_path.parent
    rec["status"] = "OK"
    rec["source_readable"] = source_readable

    qs = [u for u in (man.get("units") or []) if u.get("unit_type") in Q_TYPES]
    line_ann = {}          # 行号 → (unit_id, zone):stem/material/answer/explanation/other
    img_to_units = {}      # 解析后图片路径 → 引用它的 unit_id 集合(共享判定)
    q_records = []

    def _annotate(u, span, zone):
        if span and isinstance(span, (list, tuple)) and len(span) == 2 \
                and all(isinstance(x, int) for x in span):
            for ln in range(span[0], span[1] + 1):
                line_ann.setdefault(ln, (u.get("unit_id"), zone))

    for u in qs:
        stem_zone, mat_zone = _unit_zones(u)
        _annotate(u, stem_zone, "stem")
        _annotate(u, mat_zone, "material")
        _annotate(u, u.get("options_lines"), "other")
        _annotate(u, u.get("extra_lines"), "other")
        _annotate(u, u.get("answer_lines"), "answer")
        _annotate(u, u.get("explanation_lines"), "explanation")
        if not source_readable:
            continue
        stem_refs = refs_in_span(lines, stem_zone)
        mat_refs = refs_in_span(lines, mat_zone)
        if not (stem_refs or mat_refs):
            continue                      # 非 img 依赖题不进明细
        detail = []
        for zone, pairs in (("stem", stem_refs), ("material", mat_refs)):
            for ln, ref in pairs:
                ap = resolve_ref(ref, src_dir)
                exists = ap.is_file()
                detail.append({"line": ln, "zone": zone, "ref": ref,
                               "resolved": str(ap), "exists": exists})
                if exists:
                    img_to_units.setdefault(str(ap), set()).add(u["unit_id"])
        q_records.append({
            "unit_id": u.get("unit_id"),
            "question_numbers": u.get("question_numbers"),
            "unit_type": u.get("unit_type"),
            "stem_zone": stem_zone, "material_zone": mat_zone,
            "refs": detail,
        })

    # 题面(stem/material)之外的引用:答案/解析区归属 → 记 unit;完全在所有单元区间外
    # → 真孤儿,附确定性事实:最近单元与其行距(相邻贴题图的识别信号,不做归属猜测)
    ans_exp_refs, orphan = [], []
    span_edges = []        # (行号边界, unit_id):全部单元全部区间
    for u in qs:
        for f in ("stem_lines", "questions_lines", "material_lines",
                  "options_lines", "extra_lines", "answer_lines",
                  "explanation_lines"):
            sp = u.get(f)
            if sp and isinstance(sp, (list, tuple)) and len(sp) == 2 \
                    and all(isinstance(x, int) for x in sp):
                span_edges.append((sp[0], sp[1], u.get("unit_id")))
    if source_readable:
        for ln in range(1, len(lines) + 1):
            refs = extract_refs(lines[ln - 1])
            if not refs:
                continue
            ann = line_ann.get(ln)
            if ann and ann[0] in {q["unit_id"] for q in q_records} \
                    and ann[1] in ("answer", "explanation"):
                for ref in refs:
                    ap = resolve_ref(ref, src_dir)
                    ans_exp_refs.append({"line": ln, "unit_id": ann[0],
                                         "zone": ann[1], "ref": ref,
                                         "resolved": str(ap), "exists": ap.is_file()})
                continue
            if ann:
                continue                  # 其他已圈定区(如题前单元 stem):不算孤儿
            for ref in refs:
                ap = resolve_ref(ref, src_dir)
                gap, near = None, None
                for s, e, uid in span_edges:
                    g = (s - ln) if ln < s else ((ln - e) if ln > e else 0)
                    if gap is None or g < gap:
                        gap, near = g, uid
                orphan.append({"line": ln, "ref": ref, "resolved": str(ap),
                               "exists": ap.is_file(),
                               "nearest_unit": near, "gap": gap})

    shared_imgs = {p_: sorted(us) for p_, us in img_to_units.items() if len(us) >= 2}
    refs_total = sum(len(q["refs"]) for q in q_records)
    refs_ok = sum(1 for q in q_records for r in q["refs"] if r["exists"])
    dep_with_ref = len(q_records)
    dep_with_resolvable = sum(
        1 for q in q_records if any(r["exists"] for r in q["refs"]))
    shared_units = {q["unit_id"] for q in q_records
                    if any(r["exists"] and str(r["resolved"]) in shared_imgs
                           for r in q["refs"])}
    orphan_adjacent = sum(1 for o in orphan if (o.get("gap") or 99) <= 3)

    rec.update({
        "img_dep_questions": dep_with_ref,
        "dep_with_ref": dep_with_ref,
        "dep_with_resolvable": dep_with_resolvable,
        "refs_total": refs_total,
        "refs_resolvable": refs_ok,
        "refs_broken": refs_total - refs_ok,
        "shared_images": len(shared_imgs),
        "shared_detail": shared_imgs,
        "questions_on_shared": len(shared_units),
        "ans_exp_refs": ans_exp_refs,
        "orphan_refs": orphan,
        "orphan_adjacent": orphan_adjacent,
        "questions": q_records,
    })
    return rec


def aggregate(papers):
    tot = {"papers": len(papers),
           "no_manifest": sum(1 for p in papers if p.get("status") == "NO_MANIFEST"),
           "source_unreadable": sum(1 for p in papers
                                    if p.get("status") == "OK"
                                    and not p.get("source_readable")),
           "img_dep_questions": 0, "dep_with_ref": 0, "dep_with_resolvable": 0,
           "refs_total": 0, "refs_resolvable": 0, "refs_broken": 0,
           "shared_images": 0, "questions_on_shared": 0,
           "refs_ans_exp": 0, "orphan_refs": 0, "orphan_adjacent": 0,
           "orphan_far": 0}
    for p in papers:
        if p.get("status") != "OK":
            continue
        for k in ("img_dep_questions", "dep_with_ref", "dep_with_resolvable",
                  "refs_total", "refs_resolvable", "refs_broken",
                  "shared_images", "questions_on_shared"):
            tot[k] += p.get(k) or 0
        tot["refs_ans_exp"] += len(p.get("ans_exp_refs") or [])
        o = p.get("orphan_refs") or []
        tot["orphan_refs"] += len(o)
        tot["orphan_adjacent"] += p.get("orphan_adjacent") or 0
        tot["orphan_far"] += len(o) - (p.get("orphan_adjacent") or 0)
    d = tot["img_dep_questions"]
    tot["img_recognition_rate"] = round(tot["dep_with_ref"] / d, 4) if d else None
    tot["img_resolvable_rate"] = round(tot["dep_with_resolvable"] / d, 4) if d else None
    tot["ref_resolvable_rate"] = (round(tot["refs_resolvable"] / tot["refs_total"], 4)
                                  if tot["refs_total"] else None)
    return tot


# ---------------- ② 人工归属审核单(确定性抽样) ----------------

LABELS = ["属于该题", "不属于该题", "存疑"]
LABEL_DESC = {
    "属于该题": "图与本题绑定正确,V3 可直接消费",
    "不属于该题": "错绑:图属于他题/题前装饰/答案区,需修绑定",
    "存疑": "无法判断(图缺失/模糊/归属不明)",
}


def build_sample(papers, sample_size):
    """确定性均匀抽样:①题面绑定题 与 ②真孤儿引用(相邻贴题信号)两个池分别等距取样,
    配额 = 题面 2/3 + 孤儿 1/3(孤儿不足用题面补)。"""
    qpool, opool = [], []
    for p in papers:
        if p.get("status") != "OK":
            continue
        for q in p.get("questions") or []:
            qpool.append({"kind": "question", "file": p["file"],
                          "subject": p.get("subject"), **q})
        for o in p.get("orphan_refs") or []:
            opool.append({"kind": "orphan", "file": p["file"],
                          "subject": p.get("subject"),
                          "unit_id": "nearest:" + str(o.get("nearest_unit")),
                          "question_numbers": None,
                          "stem_zone": [max(1, o["line"] - 2), o["line"] + 1],
                          "material_zone": None,
                          "gap": o.get("gap"),
                          "refs": [{**o, "zone": "outside"}]})
    qpool.sort(key=lambda x: (x["file"], str(x["unit_id"])))
    opool.sort(key=lambda x: (x["file"], x["refs"][0]["line"]))
    n_o = min(len(opool), max(1, sample_size // 3)) if opool else 0
    n_q = min(len(qpool), sample_size - n_o)

    def _even(pool, n):
        m = len(pool)
        if m <= n:
            return list(pool)
        idx = sorted({round(i * (m - 1) / (n - 1)) for i in range(n)}) if n > 1 else [0]
        return [pool[i] for i in idx]

    return _even(qpool, n_q) + _even(opool, n_o)


def build_review_html(items, src_root, generated_at=None) -> str:
    """复用 P2.1-d2 审核单骨架:图直接渲染(file:// URI),单选 + 备注 + 导出 JSON。"""
    RH = _load("rh_p22", Path(__file__).resolve().parent / "p2_1_review_html.py")
    generated_at = generated_at or datetime.datetime.now().isoformat(timespec="seconds")
    parts = []
    for idx, it in enumerate(items, 1):
        sp = Path(it["file"])
        try:
            rel = sp.relative_to(src_root)
        except ValueError:
            rel = Path(sp.name)
        try:
            lines = (src_root / rel).read_text(
                encoding="utf-8", errors="replace").splitlines()
        except OSError:
            lines = []
        src_dir = (src_root / rel).parent
        body = RH.render_span_html(lines, it.get("stem_zone"), src_dir)
        mat_zone = it.get("material_zone")
        if mat_zone:
            mat = ("<details><summary>材料区(L%d-L%d)</summary>%s</details>"
                   % (mat_zone[0], mat_zone[1],
                      RH.render_span_html(lines, mat_zone, src_dir)))
        else:
            mat = ""
        refs_html = "".join(
            "<li>L{line} [{zone}] <code>{ref}</code> {ok}</li>".format(
                line=r["line"], zone=r["zone"], ref=RH._escape(r["ref"]),
                ok="✅可解析" if r["exists"] else "❌文件缺失")
            for r in it["refs"])
        radios = "".join(
            f"<label class='lab'><input type='radio' name='lab_{idx}' "
            f"value='{lb}' onchange='saveDraft()'> {lb}</label>"
            for lb in LABELS)
        kind_zh = ("题面绑定题" if it.get("kind") != "orphan"
                   else f"孤儿引用(距最近单元 {it.get('gap')} 行,请判断是否其实属于 {it['unit_id'].replace('nearest:', '')})")
        parts.append(f"""
<div class='item' id='item_{idx}' data-idx='{idx}'>
  <div class='hd'>S{idx:03d} · {it['subject']} · 题号 {it['question_numbers']}
      · {it['unit_id']} · {kind_zh}
      <span class='st' id='st_{idx}'></span></div>
  <div class='meta'>源卷:<code>{RH._escape(it['file'])}</code>
      · 引用清单:<ul>{refs_html}</ul></div>
  <div class='qbody'>{body}</div>
  {mat}
  <div class='judge'>{radios}
    <input type='text' id='note_{idx}' placeholder='备注(可选)'
           oninput='saveDraft()' style='margin-left:8px'>
  </div>
</div>""")

    legend = " · ".join(f"{k}={v}" for k, v in LABEL_DESC.items())
    meta_js = json.dumps([{"id": f"S{i+1:03d}", "file": it["file"],
                           "unit_id": it["unit_id"],
                           "kind": it.get("kind"),
                           "question_numbers": it["question_numbers"],
                           "refs": [r["ref"] for r in it["refs"]]}
                          for i, it in enumerate(items)], ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>图片归属人工审核(P2.2,{len(items)} 条)</title>
<style>
 body {{ font-family: "Microsoft YaHei", sans-serif; margin: 0 auto;
        max-width: 1080px; padding: 16px; background: #f7f7f9; }}
 .item {{ background: #fff; border: 1px solid #ddd; border-radius: 8px;
          padding: 14px 18px; margin: 14px 0; }}
 .item.done {{ border-color: #4caf50; }}
 .hd {{ font-weight: bold; font-size: 15px; }}
 .meta {{ color: #888; font-size: 12px; margin: 4px 0 8px; }}
 .qbody {{ background: #fcfcf7; border: 1px dashed #e0dcb8; padding: 10px;
           border-radius: 6px; font-size: 14px; line-height: 1.7; }}
 .ln {{ white-space: pre-wrap; word-break: break-all; }}
 .sp {{ height: 8px; }}
 .na {{ color: #a00; }}
 .judge {{ margin-top: 10px; }}
 .lab {{ margin-right: 14px; cursor: pointer; }}
 .st {{ font-size: 12px; color: #4caf50; margin-left: 8px; }}
 #bar {{ position: sticky; top: 0; background: #fff; border-bottom: 2px solid #4caf50;
         padding: 10px 16px; z-index: 9; }}
 code {{ background: #eee; padding: 1px 4px; border-radius: 3px; font-size: 12px; }}
 img {{ max-width: 320px; }}
 details {{ margin-top: 6px; }}
</style></head><body>
<div id="bar">
  <b>图片归属人工审核(P2.2)</b> — 共 {len(items)} 条;生成于 {generated_at}
  <div style="margin-top:6px">词表:{RH._escape(legend)}</div>
  <div style="margin-top:6px">
    进度:<span id="prog">0 / {len(items)}</span>
    <button onclick="exportJSON()" style="margin-left:16px">导出标注 JSON</button>
    <button onclick="importJSON()">导入(恢复进度)</button>
    <span id="msg" style="color:#a00;margin-left:12px"></span>
  </div>
</div>
{''.join(parts)}
<script>
const N = {len(items)};
const META = {meta_js};
const KEY = "p22_image_labels_v1";
function load() {{ try {{ return JSON.parse(localStorage.getItem(KEY)) || {{}}; }}
                  catch(e) {{ return {{}}; }} }}
function saveDraft() {{
  const d = load();
  for (let i = 1; i <= N; i++) {{
    const r = document.querySelector("input[name='lab_"+i+"']:checked");
    const n = document.getElementById("note_"+i);
    if (r || (n && n.value)) d[i] = {{ label: r ? r.value : null,
                                      note: n ? n.value : "" }};
    else delete d[i];
  }}
  localStorage.setItem(KEY, JSON.stringify(d));
  paint(d);
}}
function paint(d) {{
  let done = 0;
  for (let i = 1; i <= N; i++) {{
    const it = document.getElementById("item_"+i);
    const st = document.getElementById("st_"+i);
    if (d[i] && d[i].label) {{ it.classList.add("done");
        st.textContent = "✓ " + d[i].label; done++; }}
    else {{ it.classList.remove("done"); st.textContent = ""; }}
  }}
  document.getElementById("prog").textContent = done + " / " + N;
}}
function restore() {{
  const d = load();
  for (let i = 1; i <= N; i++) {{
    if (d[i]) {{
      if (d[i].label) {{
        const r = document.querySelector(
          "input[name='lab_"+i+"'][value='"+d[i].label+"']");
        if (r) r.checked = true;
      }}
      const n = document.getElementById("note_"+i);
      if (n && d[i].note) n.value = d[i].note;
    }}
  }}
  paint(d);
}}
function exportJSON() {{
  const d = load();
  const items = [];
  let missing = 0;
  for (let i = 1; i <= N; i++) {{
    if (!(d[i] && d[i].label)) {{ missing++; continue; }}
    items.push(Object.assign({{}}, META[i-1],
              {{ label: d[i].label, note: d[i].note || "" }}));
  }}
  const out = {{ schema_version: 1, round: "P2.2",
                 exported_at: new Date().toISOString(),
                 items: items }};
  const blob = new Blob([JSON.stringify(out, null, 1)],
                        {{type: "application/json"}});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "p2_2_image_labels.json";
  a.click();
  document.getElementById("msg").textContent = missing ?
    ("已导出 " + items.length + " 条;仍有 " + missing + " 条未标注") :
    ("全部 " + items.length + " 条已导出");
}}
function importJSON() {{
  const inp = document.createElement("input");
  inp.type = "file"; inp.accept = ".json";
  inp.onchange = () => {{
    const f = inp.files[0]; if (!f) return;
    f.text().then(t => {{
      const j = JSON.parse(t);
      const d = {{}};
      (j.items || []).forEach(x => {{
        const i = parseInt(x.id.slice(1), 10);
        if (i >= 1 && i <= N) d[i] = {{ label: x.label, note: x.note || "" }};
      }});
      localStorage.setItem(KEY, JSON.stringify(d));
      restore();
    }});
  }};
  inp.click();
}}
restore();
</script></body></html>
"""


def build_binding_table(papers):
    """逐条已圈定引用的归属身份(确定性、不含路径):用于 before/after 逐卷对账。

    key=(basename(file), unit_id, line, ref) —— 跨输出目录比较时绝对路径不可比
    (两个 out root 不同),故只取文件名与卷内行号。同一行多引用各自成条。
    """
    tbl = {}
    for p in papers:
        if p.get("status") != "OK":
            continue
        fb = os.path.basename(p["file"])
        for q in p.get("questions") or []:
            for r in q.get("refs") or []:
                tbl.setdefault((fb, q.get("unit_id"), r.get("line"), r.get("ref")),
                               {"zone": r.get("zone"), "exists": r.get("exists")})
    return tbl


def diff_bindings(before_tbl, after_tbl):
    """逐条绑定 delta:新增 / 消失 / 换绑(unit 或 zone 变化)。不做对错判定。"""
    added = [{"key": list(k), **after_tbl[k]}
             for k in sorted(set(after_tbl) - set(before_tbl))]
    removed = [{"key": list(k), **before_tbl[k]}
               for k in sorted(set(before_tbl) - set(after_tbl))]
    moved = []
    for k in sorted(set(before_tbl) & set(after_tbl)):
        b, a = before_tbl[k], after_tbl[k]
        if b.get("zone") != a.get("zone"):
            moved.append({"key": list(k), "from_zone": b.get("zone"),
                          "to_zone": a.get("zone")})
    return {"added": added, "removed": removed, "moved": moved}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", default=str(ROOT / "data/p2_1_batch1.json"))
    ap.add_argument("--out", default=str(SRC / "reslice-p2-b1"))
    ap.add_argument("--result", default=str(ROOT / "data/p2_2_image_baseline.json"))
    ap.add_argument("--src", default=str(SRC), help="源语料根(默认 Ocr-markdown)")
    ap.add_argument("--review-html", default=None, help="②人工归属审核单 HTML 输出路径")
    ap.add_argument("--sample-size", type=int, default=24)
    ap.add_argument("--label-from", default=None,
                    help="修复轮对账:另一输出目录,对同一批卷算绑定 delta + 孤儿变化")
    args = ap.parse_args()

    src_root = Path(args.src)
    entries = json.loads(Path(args.batch).read_text(encoding="utf-8"))
    papers = [analyze_paper(Path(args.out), e, src_root) for e in entries]
    tot = aggregate(papers)

    report = {"schema_version": 1, "round": "P2.2",
              "batch": os.path.abspath(args.batch),
              "out": os.path.abspath(args.out),
              "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
              "totals": tot, "papers": papers}

    if args.label_from:
        base = [analyze_paper(Path(args.label_from), e, src_root) for e in entries]
        btot = aggregate(base)
        bt = build_binding_table(base)
        at = build_binding_table(papers)
        base_orph = {}
        for p in base:
            if p.get("status") == "OK":
                base_orph[os.path.basename(p["file"])] = p.get("orphan_refs") or []
        orphan_delta = []
        for p in papers:
            if p.get("status") != "OK":
                continue
            fb = os.path.basename(p["file"])
            orphan_delta.append({
                "file": p["file"],
                "orphan_before": len(base_orph.get(fb, [])),
                "orphan_after": len(p.get("orphan_refs") or []),
                "orphan_after_detail": p.get("orphan_refs") or [],
            })
        report["label_from"] = {
            "baseline_out": os.path.abspath(args.label_from),
            "totals_before": btot, "totals_after": tot,
            "binding_diff": diff_bindings(bt, at),
            "orphan_delta": orphan_delta,
        }

    Path(args.result).parent.mkdir(parents=True, exist_ok=True)
    with open(args.result, "w", encoding="utf-8", newline="") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)

    if args.review_html:
        items = build_sample(papers, args.sample_size)
        html = build_review_html(items, src_root)
        Path(args.review_html).parent.mkdir(parents=True, exist_ok=True)
        Path(args.review_html).write_text(html, encoding="utf-8", newline="")
        print(f"review sample={len(items)} -> {args.review_html}")

    print("P2.2 image baseline: papers={papers} no_manifest={no_manifest} "
          "img_dep={img_dep_questions} with_ref={dep_with_ref} "
          "with_resolvable={dep_with_resolvable} "
          "refs={refs_total}(ok={refs_resolvable} broken={refs_broken}) "
          "shared_imgs={shared_images} on_shared={questions_on_shared} "
          "ans_exp={refs_ans_exp} orphan={orphan_refs}"
          "(adjacent<={orphan_adjacent} far={orphan_far})".format(**tot))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()

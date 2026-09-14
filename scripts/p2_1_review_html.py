# -*- coding: utf-8 -*-
r"""
p2_1_review_html.py — 组合题 suspect 人工审核 HTML 生成器(P2.1-d,用户要求)

把 71 条 suspect 组合题连同源文原文(材料+小问+答案区)渲染成**单个自包含 HTML**:
每条一组单选按钮(KEEP/SPLIT/LOST/UNCERTAIN)+ 备注框,localStorage 自动保存,
"导出 JSON"按钮一键下载标注结果(存回 data/ 即可交给流水线)。
人工判断,LLM 不参与分类(用户裁定 charter §9.2)。

用法:
  python scripts/p2_1_review_html.py --batch data/p2_1_batch1.json \
      --out Ocr-markdown/reslice-p2-b1 --html data/p2_1_c_suspect_review.html
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


def _load_measure():
    spec = importlib.util.spec_from_file_location(
        "p2_1_measure", Path(__file__).resolve().parent / "p2_1_measure.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["p2_1_measure"] = mod
    spec.loader.exec_module(mod)
    return mod


LABELS = ["KEEP", "SPLIT", "LOST", "UNCERTAIN"]
LABEL_DESC = {
    "KEEP": "一题(材料+多小问),V3 不改模型",
    "SPLIT": "应拆为多个 QuestionInstance",
    "LOST": "切分丢失信息,需修 reslice",
    "UNCERTAIN": "无法判断,需增加策略",
}

_ALLOWED_TAGS = {"img", "table", "tr", "td", "th", "div", "br", "hr",
                 "sup", "sub", "b", "i", "u", "center"}
_TAG_RE = re.compile(r"</?([A-Za-z][A-Za-z0-9]*)\b[^>]*>")
_IMG_SRC_RE = re.compile(r'src="([^"]+)"')


def _escape(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _rewrite_img_src(tag_html: str, src_dir: Path) -> str:
    """把源文中的相对图片路径改写为绝对 file:// URI(HTML 位置无关)。"""
    def rep(m):
        raw = m.group(1)
        p = Path(raw)
        if not p.is_absolute():
            p = (src_dir / p).resolve()
        return f'src="{p.as_uri()}"'
    return _IMG_SRC_RE.sub(rep, tag_html)


def render_span_html(lines, span, src_dir: Path) -> str:
    """行区间 → HTML:普通行转义,白名单内联标签(img/table/div…)保留。"""
    if not span or not isinstance(span, (list, tuple)) or len(span) != 2:
        return "<p class='na'>(无区间)</p>"
    out = []
    for raw in lines[span[0] - 1: span[1]]:
        line = raw.rstrip()
        if not line.strip():
            out.append("<div class='sp'></div>")
            continue
        # 逐标签过滤:白名单标签保留(转义其外文本),其余整体转义
        buf, pos = [], 0
        for m in _TAG_RE.finditer(line):
            if m.group(1).lower() not in _ALLOWED_TAGS:
                continue
            buf.append(_escape(line[pos:m.start()]))
            tag = _rewrite_img_src(m.group(0), src_dir)
            buf.append(tag)
            pos = m.end()
        buf.append(_escape(line[pos:]))
        out.append("<div class='ln'>" + "".join(buf) + "</div>")
    return "\n".join(out)


def build_review_html(items, src_root, generated_at=None) -> str:
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
        body = render_span_html(lines, it.get("stem_lines"), src_dir)
        ans_lines = it.get("answer_lines")
        if ans_lines:
            ans = ("<details><summary>答案区(L%d-L%d)</summary>%s</details>"
                   % (ans_lines[0], ans_lines[1],
                      render_span_html(lines, ans_lines, src_dir)))
        else:
            ans = "<p class='na'>答案区:无独立区间(或经 answer_evidence 定位)</p>"
        radios = "".join(
            f"<label class='lab'><input type='radio' name='lab_{idx}' "
            f"value='{lb}' onchange='saveDraft()'> {lb}</label>"
            for lb in LABELS)
        parts.append(f"""
<div class='item' id='item_{idx}' data-idx='{idx}'>
  <div class='hd'>S{idx:03d} · {it['subject']} · 题号 {it['question_numbers']}
      · {it['unit_id']} <span class='st' id='st_{idx}'></span></div>
  <div class='meta'>源卷:<code>{_escape(it['file'])}</code></div>
  <div class='qbody'>{body}</div>
  {ans}
  <div class='judge'>{radios}
    <input type='text' id='note_{idx}' placeholder='备注(可选)'
           oninput='saveDraft()' style='margin-left:8px'>
  </div>
</div>""")

    legend = " · ".join(f"{k}={v}" for k, v in LABEL_DESC.items())
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>组合题 suspect 人工审核(P2.1-c,71 条)</title>
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
  <b>组合题 suspect 人工审核</b> — 共 {len(items)} 条;词表:{_escape(legend)}
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
const META = {json.dumps([{"id": f"S{i+1:03d}", "file": it["file"],
                           "unit_id": it["unit_id"],
                           "question_numbers": it["question_numbers"]}
                          for i, it in enumerate(items)], ensure_ascii=False)};
const KEY = "p21_suspect_labels_v1";
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
  const out = {{ schema_version: 1, round: "P2.1-c",
                 exported_at: new Date().toISOString(),
                 items: items }};
  const blob = new Blob([JSON.stringify(out, null, 1)],
                        {{type: "application/json"}});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "p2_1_c_suspect_labels.json";
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", default=str(ROOT / "data/p2_1_batch1.json"))
    ap.add_argument("--out", default=str(ROOT / "Ocr-markdown/reslice-p2-b1"))
    ap.add_argument("--html", default=str(ROOT / "data/p2_1_c_suspect_review.html"))
    args = ap.parse_args()

    M = _load_measure()
    entries = json.loads(Path(args.batch).read_text(encoding="utf-8"))
    ss = M.build_suspect_sample(Path(args.out), entries)
    html = build_review_html(ss["items"], M.SRC)
    Path(args.html).parent.mkdir(parents=True, exist_ok=True)
    Path(args.html).write_text(html, encoding="utf-8")
    print(f"items={ss['questions']} -> {args.html}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()

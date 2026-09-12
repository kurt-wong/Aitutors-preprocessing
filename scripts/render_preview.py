# -*- coding: utf-8 -*-
r"""
render_preview.py — 把 OCR 源 markdown 整份渲染成独立 HTML，供人工与原 PDF 逐页比对。
解决"表格/配图/复杂版式看不出是否忠实原文"的盲区。

用法：
    python render_preview.py <源.md> [输出.html]
    python render_preview.py --pilot            # 渲染全部试点 16 份到 reports\preview\

要点：
- 忠实还原源文（不重敲内容），HTML 表格/图片原样透传；
- 图片相对路径 ../../_imgs/ 换成绝对 file:// 路径，本地浏览器直接显示；
- LaTeX 由 KaTeX + mhchem 从 CDN 渲染（需联网；离线则显示原始命令）；
- 单 $ / $$ / \\( \\) 三种定界符都识别（源文多用单 $）。
"""
import sys
import re
import json
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parent.parent
IMG_BASE = "file:///D:/Project/Papers/Ocr-markdown/_imgs/"

KATEX_HEAD = (
    '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">\n'
    '<style>\n'
    ' body{font-family:"Microsoft YaHei",sans-serif;max-width:1080px;margin:24px auto;'
    'color:#1a1a1a;line-height:1.75;padding:0 20px}\n'
    ' table{border-collapse:collapse;margin:14px auto}\n'
    ' td,th{border:1px solid #666;padding:6px 10px;text-align:center;vertical-align:middle}\n'
    ' img{max-width:420px;display:block;margin:6px auto}\n'
    ' h1{font-size:22px;border-bottom:2px solid #333;padding-bottom:6px}\n'
    ' h2{font-size:19px;margin-top:22px;border-bottom:1px solid #aaa;padding-bottom:4px}\n'
    ' h3{font-size:16px;margin-top:16px}\n'
    ' p{margin:6px 0}\n'
    ' hr{border:none;border-top:1px dashed #bbb;margin:16px 0}\n'
    ' .banner{background:#e3f2fd;border-left:4px solid #1976d2;padding:8px 14px;'
    'font-size:12.5px;margin-bottom:16px;color:#333}\n'
    '</style>\n'
)

KATEX_TAIL = (
    '<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>\n'
    '<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/mhchem.min.js"></script>\n'
    '<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>\n'
    '<script>renderMathInElement(document.body,{delimiters:['
    '{left:"$$",right:"$$",display:false},'
    '{left:"\\\\(",right:"\\\\)",display:false},'
    '{left:"$",right:"$",display:false}],'
    'strict:false,trust:true,throwOnError:false});</script>\n'
)


def md_to_html(md_text: str) -> str:
    """把 OCR 源 markdown 转成 HTML：HTML 块透传，标题转换，其余按段落包裹。"""
    md_text = md_text.replace('src="../../_imgs/', 'src="' + IMG_BASE)
    lines = md_text.splitlines()
    out = []
    i = 0
    while i < len(lines):
        raw = lines[i]
        s = raw.strip()
        if not s:
            i += 1
            continue
        # 整行 HTML（表格/div/图片块）：原样透传（可能跨多行，累积到标签闭合）
        if s.startswith("<"):
            block = [raw]
            # 简单配平：累计到主要开闭标签数量相等
            depth_open = len(re.findall(r'<(table|div|tr|td)\b', s))
            depth_close = len(re.findall(r'</(table|div|tr|td)>', s))
            while depth_open > depth_close and i + 1 < len(lines):
                i += 1
                block.append(lines[i])
                depth_open += len(re.findall(r'<(table|div|tr|td)\b', lines[i]))
                depth_close += len(re.findall(r'</(table|div|tr|td)>', lines[i]))
            out.append("\n".join(block))
            i += 1
            continue
        # markdown 标题
        m = re.match(r'^(#{1,6})\s+(.*)$', s)
        if m:
            lv = min(len(m.group(1)), 4)
            out.append(f"<h{lv}>{m.group(2)}</h{lv}>")
            i += 1
            continue
        # 水平线（--- 或 ___）
        if re.fullmatch(r'-{3,}|_{3,}', s):
            out.append("<hr>")
            i += 1
            continue
        # 普通文本行 → 段落（escape 保护，KaTeX 之后处理 $ ）
        # 但源文含行内 HTML 如 <img>，仅在该行含 HTML 时少转义
        if "<" in raw and ">" in raw:
            out.append(f"<p>{raw.strip()}</p>")
        else:
            out.append(f"<p>{escape(raw.strip())}</p>")
        i += 1
    return "\n".join(out)


def build(md_path: Path, out_path: Path, title: str = None) -> Path:
    md_text = md_path.read_text(encoding="utf-8")
    body = md_to_html(md_text)
    title = title or md_path.stem
    html = (
        "<!DOCTYPE html><html lang=\"zh\"><head><meta charset=\"utf-8\">\n"
        f"<title>渲染预览 · {escape(title)}</title>\n"
        + KATEX_HEAD + "</head><body>\n"
        f"<div class=\"banner\">渲染预览（源文忠实还原，供与原 PDF 比对）。"
        f"LaTeX 由 KaTeX+mhchem 渲染（需联网加载 CDN）；图片取自本地 _imgs。</div>\n"
        + body + "\n" + KATEX_TAIL + "</body></html>"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


def main():
    args = sys.argv[1:]
    if args and args[0] == "--pilot":
        RP = ROOT / "Ocr-markdown" / "resliced-pilot"
        outdir = ROOT / "reports" / "preview"
        n = 0
        for mp in sorted(RP.rglob("*.manifest.json")):
            man = json.loads(mp.read_text(encoding="utf-8"))
            src = Path(man["source_file"])
            out = outdir / f"{src.parent.name}__{src.stem}.html"
            build(src, out)
            n += 1
            print(f"[{n}] {out.name}")
        print(f"完成：{n} 份 → {outdir}")
        return
    if not args:
        print(__doc__)
        return
    src = Path(args[0])
    out = Path(args[1]) if len(args) > 1 else ROOT / "reports" / f"preview_{src.stem}.html"
    p = build(src, out)
    print("已导出:", p, "（", p.stat().st_size, "字节）")


if __name__ == "__main__":
    main()

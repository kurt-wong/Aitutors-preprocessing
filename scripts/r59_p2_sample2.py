# -*- coding: utf-8 -*-
"""R59 抽样 v2:按 src 属性完整解析盲区图片引用(修 v1 括号截断假阳性),只读。"""
import io, os, re, sys
from collections import Counter

OCR_ROOT = r"D:\Project\Papers\Ocr-markdown"
OLD = {"高一", "高二", "高三", "未分类"}
RE_SRC = re.compile(r'src\s*=\s*"([^"]+)"', re.IGNORECASE)
RE_IMGS_ANY = re.compile(r"(?<!_)imgs/", re.IGNORECASE)
RE_MD_IMG = re.compile(r"!\[[^\]]*\]\(")

new_tops = [t for t in os.listdir(OCR_ROOT)
            if os.path.isdir(os.path.join(OCR_ROOT, t))
            and t not in OLD and not t.startswith(("auto-annotated", "reslice"))
            and t not in {"_imgs", ".cache"}]

cls = Counter()
other_samples = []
gif_ctx = []
files_with_dangling_src = set()
md_img_count = 0
for t in new_tops:
    for r, dirs, files in os.walk(os.path.join(OCR_ROOT, t)):
        dirs[:] = [x for x in dirs if x != "_imgs"]
        for fn in files:
            if not fn.lower().endswith(".md"):
                continue
            p = os.path.join(r, fn)
            text = io.open(p, encoding="utf-8", errors="replace").read()
            md_img_count += len(RE_MD_IMG.findall(text))
            for m in RE_SRC.finditer(text):
                v = m.group(1)
                if "_imgs/" in v:
                    cls["src->_imgs(已恢复)"] += 1
                elif RE_IMGS_ANY.search(v):
                    cls["src->imgs(悬空形态)"] += 1
                    files_with_dangling_src.add(p)
                else:
                    cls["src->其它"] += 1
                    if len(other_samples) < 10:
                        other_samples.append((fn, v))
            if ".gif" in text.lower():
                for line in text.splitlines():
                    if ".gif" in line.lower() and len(gif_ctx) < 6:
                        gif_ctx.append((fn, line.strip()[:150]))

print("src_class=", dict(cls))
print("md_markdown_img_syntax=", md_img_count)
print("files_with_dangling_src=", len(files_with_dangling_src))
print("--- src 其它形态样本 ---")
for fn, v in other_samples:
    print(f"[{fn}] {v}")
print("--- gif 上下文 ---")
for fn, ln in gif_ctx:
    print(f"[{fn}] {ln}")

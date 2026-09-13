# -*- coding: utf-8 -*-
"""R59 抽样:盲区文件里"裸 .jpg token"与 <img> 的真实上下文(定性用,只读)。"""
import io, os, re, sys
from collections import Counter

OCR_ROOT = r"D:\Project\Papers\Ocr-markdown"
OLD = {"高一", "高二", "高三", "未分类"}
RE_IMG_TOKEN = re.compile(r"[^\s()\"'<>]+\.(?:jpg|jpeg|png|gif|webp|bmp)", re.IGNORECASE)
RE_IMGS_ANY = re.compile(r"(?<!_)imgs/([^)\"'\s>]+)", re.IGNORECASE)

new_tops = [t for t in os.listdir(OCR_ROOT)
            if os.path.isdir(os.path.join(OCR_ROOT, t))
            and t not in OLD and not t.startswith(("auto-annotated", "reslice"))
            and t not in {"_imgs", ".cache"}]

bare_ctx = []
src_forms = Counter()
n_bare = 0
for t in new_tops:
    for r, dirs, files in os.walk(os.path.join(OCR_ROOT, t)):
        dirs[:] = [x for x in dirs if x != "_imgs"]
        for fn in files:
            if not fn.lower().endswith(".md"):
                continue
            p = os.path.join(r, fn)
            text = io.open(p, encoding="utf-8", errors="replace").read()
            for line in text.splitlines():
                for m in RE_IMG_TOKEN.finditer(line):
                    tok = m.group(0)
                    if "imgs/" in tok.lower():
                        continue
                    n_bare += 1
                    # 归类 src 形态
                    if "_imgs/" in tok:
                        src_forms["_imgs(已恢复)"] += 1
                    elif tok.startswith("imgs/"):
                        src_forms["imgs(悬空)"] += 1
                    elif "box_" in tok:
                        src_forms["box_裸名"] += 1
                    elif "/" in tok or "\\" in tok:
                        src_forms["带路径其它"] += 1
                    else:
                        src_forms["纯文件名"] += 1
                    if len(bare_ctx) < 25:
                        bare_ctx.append((fn, tok, line.strip()[:120]))

print("bare_total=", n_bare)
print("src_forms=", dict(src_forms))
print("--- 抽样上下文 ---")
for fn, tok, ln in bare_ctx:
    print(f"[{fn}] tok={tok}\n    line={ln}")

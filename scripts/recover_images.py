# -*- coding: utf-8 -*-
r"""
recover_images.py — 从源 PDF 恢复 OCR markdown 中悬空的图片引用

背景:
  batch_convert_pdf.py 批量 OCR 时只保存了 markdown 文本, 丢弃了结果中的图片,
  导致 md 中的 imgs/xxx.jpg 引用全部悬空。旧 jobId 的临时下载链接已失效,
  因此改为本地用 PyMuPDF 从源 PDF 按坐标裁剪恢复。

原理:
  1. 引用名内嵌版面框坐标, 如 img_in_image_box_202_486_390_655.jpg
     经验证坐标系 = PDF 页面以 144DPI(2x) 渲染后的像素空间 (A4 => 1191x1684)。
  2. md 按 "^---" 分页, 每段对应 PDF 同序号页, 据此把引用定位到具体页。
  3. 以 2x 渲染该页, 按 (x0,y0,x1,y1) 裁剪并保存为 jpg。
  4. 重写 md 中的引用为指向统一图片库的相对路径, 并写入审计日志供回滚。

输出:
  Ocr-markdown\_imgs\{md文件名}\{原引用文件名}   裁剪出的图片
  Ocr-markdown\_imgs\{md文件名}\manifest.json     引用->页码/框/状态
  recover_images_audit.jsonl                     每处引用改写的 old/new 记录
  recover_images_log.txt                         运行日志
  recover_images_summary.json                    运行汇总

用法:
  python recover_images.py --limit 5        # 试跑 5 份
  python recover_images.py                  # 全量
  python recover_images.py --dry-run        # 只统计不写文件
"""

import argparse
import io
import json
import os
import re
import sys
import time

BASE = r"D:\Project\Papers"
OCR_ROOT = os.path.join(BASE, "Ocr-markdown")
PDF_ROOT = os.path.join(BASE, "maintainess", "PDF")
IMG_LIB = os.path.join(OCR_ROOT, "_imgs")
AUDIT = os.path.join(BASE, "data", "recover_images_audit.jsonl")
LOG = os.path.join(BASE, "logs", "recover_images_log.txt")
SUMMARY = os.path.join(BASE, "data", "recover_images_summary.json")

# BUG-11 修复:不再硬编码源目录白名单(目录布局变更会静默失配),
# 改为"排除派生目录,其余顶层目录一律视为源"——新增源目录自动纳入;
# 误纳派生目录的代价只是多扫(已重写/无引用文件幂等跳过),不会漏修。
EXCLUDED_TOP_NAMES = {"_imgs", ".cache"}                     # 精确排除
EXCLUDED_TOP_PREFIXES = ("auto-annotated", "reslice")        # 前缀排除(派生/输出目录)

PAGE_SEP = re.compile(r"(?m)^---\r?\n")
REF = re.compile(r"(?<!_)imgs/([^)\"'\s\>]+?\.jpg)")
BOX = re.compile(r"_box_(\d+)_(\d+)_(\d+)_(\d+)")
BASE_ZOOM = 2.0  # 144DPI


def _fitz():
    """惰性导入 PyMuPDF:扫描/干跑/测试离线可用,CI 无需安装 fitz。"""
    import fitz
    return fitz


def log(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def build_pdf_index():
    idx = {}
    for root, _dirs, files in os.walk(PDF_ROOT):
        for fn in files:
            if fn.lower().endswith(".pdf"):
                idx.setdefault(os.path.splitext(fn)[0], os.path.join(root, fn))
    return idx


def is_source_top_dir(name):
    """顶层目录是否为源 md 目录(排除派生/输出目录)。"""
    if name in EXCLUDED_TOP_NAMES:
        return False
    return not name.startswith(EXCLUDED_TOP_PREFIXES)


def scan_md_files(root=OCR_ROOT):
    out = []
    for name in sorted(os.listdir(root)):
        if not is_source_top_dir(name):
            continue
        full = os.path.join(root, name)
        if not os.path.isdir(full):
            continue
        for r, dirs, files in os.walk(full):
            dirs[:] = [x for x in dirs if x != "_imgs"]
            for fn in files:
                if fn.lower().endswith(".md"):
                    out.append(os.path.join(r, fn))
    return sorted(out)


def refs_by_page(text):
    """按分页符切分, 返回 [(page_idx, [ref_name, ...]), ...]"""
    segments = PAGE_SEP.split(text)
    result = []
    for i, seg in enumerate(segments):
        names = list(dict.fromkeys(REF.findall(seg)))  # 去重保序
        if names:
            result.append((i, names))
    return result, len(segments)


def crop_page(pdf, page_idx, names, zoom=BASE_ZOOM):
    """渲染指定页并按引用名中的坐标裁剪。返回 {name: bytes|None}"""
    fitz = _fitz()
    page = pdf[page_idx]
    pw, ph = page.rect.width, page.rect.height

    # 坐标可能超出当前缩放, 自动提升 zoom
    need_w = need_h = 0
    for n in names:
        m = BOX.search(n)
        if m:
            need_w = max(need_w, int(m.group(3)))
            need_h = max(need_h, int(m.group(4)))
    if need_w > pw * zoom or need_h > ph * zoom:
        zoom = max(need_w / pw, need_h / ph) + 0.01

    # 坐标在 zoom 像素空间, 转回页面点坐标后用 clip 渲染
    W, H = pw * zoom, ph * zoom
    out = {}
    for n in names:
        m = BOX.search(n)
        if not m:
            out[n] = None
            continue
        x0, y0, x1, y1 = (int(m.group(i)) for i in (1, 2, 3, 4))
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(W - 1, x1), min(H - 1, y1)
        if x1 - x0 < 4 or y1 - y0 < 4:
            out[n] = None
            continue
        clip = fitz.Rect(x0 / zoom, y0 / zoom, x1 / zoom, y1 / zoom)
        sub = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip)
        out[n] = sub.tobytes("jpeg", jpg_quality=90)
    return out


def rewrite_refs(text, mapping):
    """mapping: {name: new_rel_path}; 返回 (new_text, n_changes)"""
    n = 0

    def sub(m):
        nonlocal n
        name = m.group(1)
        if name in mapping:
            n += 1
            return mapping[name]
        return m.group(0)

    return REF.sub(sub, text), n


def rel(from_dir, to_path):
    r = os.path.relpath(to_path, from_dir).replace("\\", "/")
    return r


def process_one(md_path, pdf_index, audit_f, stats, dry_run):
    base = os.path.splitext(os.path.basename(md_path))[0]
    text = io.open(md_path, encoding="utf-8").read()
    # 已重写过(引用已指向 _imgs/{base}/)则跳过, 保证幂等
    if f"_imgs/{base}/" in text:
        stats["already_done"] += 1
        return
    page_refs, n_pages = refs_by_page(text)
    total_refs = sum(len(v) for _k, v in page_refs)
    if total_refs == 0:
        stats["no_refs"] += 1
        return

    stats["with_refs"] += 1
    stats["refs_total"] += total_refs

    out_dir = os.path.join(IMG_LIB, base)
    manifest_path = os.path.join(out_dir, "manifest.json")

    pdf_path = pdf_index.get(base)
    if not pdf_path:
        stats["pdf_miss"] += 1
        log(f"  [MISS-PDF] {base}")
        return

    if dry_run:
        return

    os.makedirs(out_dir, exist_ok=True)
    mapping = {}
    manifest = {"md": md_path, "pdf": pdf_path, "pages": n_pages, "images": []}

    try:
        pdf = _fitz().open(pdf_path)
    except Exception as e:
        stats["pdf_error"] += 1
        log(f"  [PDF-ERR] {base}: {e}")
        return

    try:
        for page_idx, names in page_refs:
            if page_idx >= pdf.page_count:
                for n in names:
                    manifest["images"].append({"ref": n, "page": page_idx, "status": "page_out_of_range"})
                stats["ref_fail"] += len(names)
                continue
            try:
                crops = crop_page(pdf, page_idx, names)
            except Exception as e:
                for n in names:
                    manifest["images"].append({"ref": n, "page": page_idx, "status": f"render_error:{e}"})
                stats["ref_fail"] += len(names)
                continue
            for n, data in crops.items():
                target = os.path.join(out_dir, n)
                if data:
                    with open(target, "wb") as f:
                        f.write(data)
                    mapping[n] = rel(os.path.dirname(md_path), target)
                    manifest["images"].append({"ref": n, "page": page_idx, "status": "ok"})
                    stats["img_ok"] += 1
                else:
                    manifest["images"].append({"ref": n, "page": page_idx, "status": "crop_failed"})
                    stats["ref_fail"] += 1
    finally:
        pdf.close()

    if mapping:
        new_text, n_ch = rewrite_refs(text, mapping)
        written = False
        for attempt in range(4):  # 与 OCR 流水线写同目录可能瞬时冲突, 重试
            try:
                with io.open(md_path, "w", encoding="utf-8", newline="") as f:
                    f.write(new_text)
                written = True
                break
            except (PermissionError, OSError):
                time.sleep(2 + attempt * 3)
        if not written:
            stats["md_locked"] += 1
            log(f"  [LOCKED] 无法写入(已提取图片): {md_path}")
            return
        audit_f.write(json.dumps({
            "md": md_path,
            "changes": n_ch,
            "mapping": mapping,
        }, ensure_ascii=False) + "\n")
        stats["md_rewritten"] += 1
        stats["ref_rewritten"] += n_ch

    with io.open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)


def rewrite_v6(pdf_index, stats, dry_run):
    """auto-annotated-v6 中同名 md 的引用同步重写(图片已在 _imgs 中)"""
    if dry_run:
        return
    v6_root = os.path.join(OCR_ROOT, "auto-annotated-v6")
    if not os.path.isdir(v6_root):
        return
    for root, _dirs, files in os.walk(v6_root):
        for fn in files:
            if not fn.lower().endswith(".md"):
                continue
            md_path = os.path.join(root, fn)
            base = os.path.splitext(fn)[0]
            manifest_path = os.path.join(IMG_LIB, base, "manifest.json")
            if not os.path.exists(manifest_path):
                continue
            text = io.open(md_path, encoding="utf-8").read()
            refs = set(REF.findall(text))
            if not refs or any(f"../_imgs/{base}/" in text or f"_imgs/{base}/" in text for _ in [0]):
                # 已重写过则跳过(引用中已含 _imgs/{base})
                if any(f"_imgs/{base}/" in text for _ in [0]):
                    continue
            with io.open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)
            ok_refs = {im["ref"] for im in manifest["images"] if im["status"] == "ok"}
            mapping = {}
            for n in refs & ok_refs:
                mapping[n] = rel(root, os.path.join(IMG_LIB, base, n))
            if mapping:
                new_text, n_ch = rewrite_refs(text, mapping)
                with io.open(md_path, "w", encoding="utf-8", newline="") as f:
                    f.write(new_text)
                stats["v6_rewritten"] += 1
                stats["v6_ref_rewritten"] += n_ch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="只处理前 N 份(0=全量)")
    ap.add_argument("--dry-run", action="store_true", help="只统计, 不写文件")
    args = ap.parse_args()

    log("=" * 60)
    log("图片恢复开始 (PyMuPDF 坐标裁剪)")
    log("=" * 60)

    t0 = time.time()
    pdf_index = build_pdf_index()
    md_files = scan_md_files()
    log(f"源PDF索引: {len(pdf_index)} | 待扫描md: {len(md_files)}")
    if args.limit:
        md_files = md_files[: args.limit]
        log(f"试跑模式: 只处理前 {len(md_files)} 份")

    stats = {"with_refs": 0, "no_refs": 0, "refs_total": 0, "img_ok": 0,
             "ref_fail": 0, "pdf_miss": 0, "pdf_error": 0, "md_rewritten": 0,
             "ref_rewritten": 0, "v6_rewritten": 0, "v6_ref_rewritten": 0,
             "already_done": 0, "md_locked": 0}

    mode = "a" if os.path.exists(AUDIT) else "w"
    with io.open(AUDIT, mode, encoding="utf-8") as audit_f:
        for i, md in enumerate(md_files, 1):
            try:
                process_one(md, pdf_index, audit_f, stats, args.dry_run)
            except Exception as e:
                stats["pdf_error"] += 1
                log(f"  [ERR] {md}: {e}")
            if i % 20 == 0:
                log(f"进度 {i}/{len(md_files)} | 成图 {stats['img_ok']} | 失败 {stats['ref_fail']} | 已重写 {stats['md_rewritten']}")

    log("同步重写 auto-annotated-v6 引用 ...")
    rewrite_v6(pdf_index, stats, args.dry_run)

    stats["elapsed_sec"] = round(time.time() - t0, 1)
    stats["md_total"] = len(md_files)
    with io.open(SUMMARY, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    log(f"完成: {json.dumps(stats, ensure_ascii=False)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()

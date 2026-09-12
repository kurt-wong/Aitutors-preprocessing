# -*- coding: utf-8 -*-
r"""select_batch_c.py — C 测速批选样：50 份，分层 + 最大文件必进，固定 seed 可复现。

输出 data\reslice_batch_c_files.json：[{file, bytes, lines, subject, grade, tier}, ...]
排除：未分类（watchdog 写入中）、auto-annotated-*、resliced-pilot、试点 16 份。
"""
import json
import random
from pathlib import Path

ROOT = Path(r"D:\Project\Papers")
SRC = ROOT / "Ocr-markdown"
ROOTS = ["高一", "高二", "高三", "高考真题", "合格考", "会考", "竞赛自招", "其他汇编", "学业水平考试"]
N_TOTAL = 50
N_BIG = 6          # 最大的 N 份必进
SEED = 20260911    # 固定随机种子：选样可复现


def main():
    # 试点 16 份的 stem 集合（排除重叠）
    pilot = json.loads((ROOT / "data/reslice_pilot_files.json").read_text(encoding="utf-8"))
    pilot_stems = {Path(p["file"]).stem for p in pilot}

    cands = []
    for g in ROOTS:
        for f in (SRC / g).rglob("*.md"):
            parts = f.relative_to(SRC).parts
            if any(x.startswith("auto-annotated") or x == "resliced-pilot"
                   or x == "未分类" for x in parts):
                continue
            if f.stem in pilot_stems:
                continue
            b = f.read_bytes()
            lines = b.count(b"\n") + 1
            size = len(b)
            tier = "xlarge" if size > 400_000 else "large" if size > 150_000 else \
                   "medium" if size > 50_000 else "small"
            cands.append({"file": str(f), "bytes": size, "lines": lines,
                          "grade": parts[0], "subject": parts[1] if len(parts) > 2 else "?",
                          "tier": tier})

    picks = sorted(cands, key=lambda r: -r["bytes"])[:N_BIG]
    rest = [r for r in cands if r not in picks]

    # 分层抽样：grade×subject 层内按比例抽，固定 seed
    random.seed(SEED)
    by_layer = {}
    for r in rest:
        by_layer.setdefault((r["grade"], r["subject"]), []).append(r)
    need = N_TOTAL - len(picks)
    total_rest = len(rest)
    quota = []
    keys = sorted(by_layer)
    # 每层至少 1 份（若有），余量按规模比例分
    base = {k: 1 for k in keys if by_layer[k]}
    for _ in range(need - len(base)):
        # 按层规模比例追加名额
        quota_best, best_val = None, -1
        for k in keys:
            val = len(by_layer[k]) / (base[k] + 0.5)
            if val > best_val:
                best_val, quota_best = val, k
        base[quota_best] += 1
    for k in keys:
        picks += random.sample(by_layer[k], min(base[k], len(by_layer[k])))
    picks = picks[:N_TOTAL]

    out = ROOT / "data/reslice_batch_c_files.json"
    out.write_text(json.dumps(picks, ensure_ascii=False, indent=1), encoding="utf-8")
    # 摘要
    from collections import Counter
    print(f"候选 {len(cands)} 份 → 选中 {len(picks)} 份 → {out}")
    print("tier 分布:", dict(Counter(r["tier"] for r in picks)))
    print("grade 分布:", dict(Counter(r["grade"] for r in picks)))
    print("subject 分布:", dict(Counter(r["subject"] for r in picks)))
    print("总字节:", sum(r["bytes"] for r in picks), "总行数:", sum(r["lines"] for r in picks))
    print("最大 6 份:")
    for r in picks[:6]:
        print(f"  {r['bytes']/1000:.0f}KB {r['lines']:5}行  {r['grade']}/{r['subject']}  {Path(r['file']).name[:40]}")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""BUG-24 影响面快照工具(R37):对 batch-C + pilot 全部 manifest 记录
SectionLocator 产物与身份裁决的完整"指纹",用于修复前后的 NEW-OLD 逐文件比对
(用户冻结的 B24 验收 §6:修复不能只看 pytest,必须比对产物)。

每文件记录:
  - manifest 字节 sha256(哪些文件被改动,字节级可证)
  - identity_version、sections 全量(id/title/ordinal/start/end/occurrence/derived)
  - 逐单元(unit 位置序)unit_id + section_ref + basis + printed_number
  - check_identity 的 fails / reviews(v2)或 v1 legacy scoped 重复(等价口径)

语料不在本 checkout 时干净 skip(与 c16 同款守卫;快照 JSON 已提交,
但语料存在性必须独立验证——R36 CI 教训)。
用法:python scripts/bug24_locator_snapshot.py --tag before|after
输出:data/bug24_locator_snapshot_{tag}.json
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase2_identity_backfill as bf  # noqa: E402
import question_identity as qi  # noqa: E402
from fix_bug22_renumber import strip_meta  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DIRS = [ROOT / "Ocr-markdown/reslice-batch-C",
        ROOT / "Ocr-markdown/resliced-pilot"]

SEC_KEYS = ("id", "title", "ordinal", "start_line", "end_line",
            "occurrence", "derived")


def snapshot_file(md_path):
    man_path = md_path.with_suffix(".manifest.json")
    raw = man_path.read_bytes()
    man = json.loads(raw.decode("utf-8"))
    src = Path(man.get("source_file") or "")
    entry = {"manifest_sha256": hashlib.sha256(raw).hexdigest(),
             "identity_version": man.get("identity_version") or 1,
             "sections": [{k: s.get(k) for k in SEC_KEYS}
                          for s in man.get("sections") or []],
             "units": [{"i": i, "unit_id": u.get("unit_id"),
                        "section_ref": u.get("section_ref"),
                        "section": u.get("section"),
                        "basis": u.get("basis"),
                        "printed_number": u.get("printed_number")}
                       for i, u in enumerate(man.get("units") or [])]}
    if not src.exists():
        entry["error"] = f"source missing: {src}"
        return entry
    lines = strip_meta(src.read_text(encoding="utf-8", errors="replace")).splitlines()
    if entry["identity_version"] >= 2:
        fails, reviews = qi.check_identity(man, len(lines), lines)
        entry["fails"], entry["reviews"] = fails, reviews
    else:
        from collections import Counter
        ident = Counter()
        for u in man.get("units") or []:
            sec = u.get("section") or ""
            for n in (u.get("question_numbers") or []):
                ident[(sec, n)] += 1
        dups = sorted((s or "∅", n) for (s, n), c in ident.items() if c > 1)
        entry["fails"] = [f"v1-legacy 同分节重复归属: {dups}"] if dups else []
        entry["reviews"] = []
    return entry


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True, choices=["before", "after"])
    args = ap.parse_args()
    files = {}
    ndirs = 0
    for d in DIRS:
        if not d.exists():
            continue
        ndirs += 1
        for p in sorted(d.rglob("*.manifest.json")):
            md = p.with_name(p.name[: -len(".manifest.json")] + ".md")
            if not md.exists() or md.name.endswith((".annotated.md", ".restored.md")):
                continue
            rel = str(md.relative_to(ROOT)).replace("\\", "/")
            files[rel] = snapshot_file(md)
    if ndirs < len(DIRS):
        print(f"SKIP: 语料目录缺失({ndirs}/{len(DIRS)} 在场),不写快照")
        return
    out = ROOT / f"data/bug24_locator_snapshot_{args.tag}.json"
    out.write_text(json.dumps({"tag": args.tag, "files": files},
                              ensure_ascii=False, indent=1),
                   encoding="utf-8", newline="\n")
    nsec = sum(len(f["sections"]) for f in files.values())
    print(f"快照[{args.tag}]:{len(files)} 份 manifest,{nsec} 个 SectionLocator → {out.name}")


if __name__ == "__main__":
    main()

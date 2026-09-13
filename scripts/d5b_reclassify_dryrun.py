# -*- coding: utf-8 -*-
r"""
d5b_reclassify_dryrun.py — D5-B.1 全量 reclassify 冻结预演(零写入)

用户 2026-09-14 裁定:D5-B 分阶段 D5-B.0 观察 → D5-B.1 dry-run → D5-B.2 小批
apply → D5-B.3 全量。本脚本只做 D5-B.1:产出带指纹的冻结 plan,供 D5-B.2/3
的 apply 武器消费(R67 preview/apply 同款漂移拒付模式)。

设计要点:
  - 规则单源:category/subject 判定直接 import reclassify_unknown 的
    classify/detect_subject,禁止本脚本复制规则(防规则漂移)。
  - 零写入:除 plan 输出文件外不触碰任何语料文件;不做 makedirs/move。
  - 分桶 fail-closed:
      moves         — 类型与科目均已判定,可移动;
      needs_ruling  — cat_src==未判定 或 subject==未分类(禁猜测,
                      对应用户冻结协议"4 规则缺口文件逐份裁定");
      collisions    — 目标路径已存在(排除出 moves,禁覆盖);
      conflicts     — plan 内两源映射同一 to_rel(全部排除,禁择一);
      read_error    — 源文件不可读(排除,禁静默)。
  - plan_sha256 = sha256(canonical json(moves)),generated_at 不入指纹。

用法:
  python scripts/d5b_reclassify_dryrun.py \
      --ocr-root D:\Project\Papers\Ocr-markdown \
      --out data/d5b_reclassify_plan.json
"""

import argparse
import glob
import hashlib
import importlib.util
import io
import json
import os
import sys
import time

SCHEMA_VERSION = 1

# ---- 规则单源:import reclassify_unknown(与本脚本同目录) ----
_HERE = os.path.dirname(os.path.abspath(__file__))
_RC_PATH = os.path.join(_HERE, "reclassify_unknown.py")
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
_spec = importlib.util.spec_from_file_location("reclassify_unknown", _RC_PATH)
_rc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_rc)
classify = _rc.classify
detect_subject = _rc.detect_subject
RULE_SOURCE = os.path.abspath(_RC_PATH)


def _file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _fingerprint(moves):
    """plan 指纹:只覆盖 moves 本体(canonical JSON),与生成时间无关。"""
    canon = json.dumps(moves, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def scan_corpus(ocr_root):
    """枚举扫描集(与 legacy reclassify_unknown --apply 完全同口径):
    未分类/*/*.md + {ocr_root}/高三/未分类/*.md。返回绝对路径列表。"""
    unknown = os.path.join(ocr_root, "未分类")
    files = sorted(glob.glob(os.path.join(unknown, "*", "*.md")))
    extra = os.path.join(ocr_root, "高三", "未分类")
    if os.path.isdir(extra):
        files.extend(sorted(glob.glob(os.path.join(extra, "*.md"))))
    return files


def root_level_md(ocr_root):
    """未分类 根层 *.md(legacy 扫描口径之外)——只报告可见性,不纳入 moves。"""
    return sorted(glob.glob(os.path.join(ocr_root, "未分类", "*.md")))


def build_plan(ocr_root):
    ocr_root = os.path.abspath(ocr_root)
    files = scan_corpus(ocr_root)
    moves, needs_ruling, read_error = [], [], []
    to_index = {}

    for f in files:
        rel_from = os.path.relpath(f, ocr_root).replace("\\", "/")
        try:
            size = os.path.getsize(f)
            sha = _file_sha256(f)
        except OSError as e:
            read_error.append({"from_rel": rel_from, "error": str(e)})
            continue
        cat, cat_src = classify(f)
        sub, sub_src = detect_subject(f)
        base = {
            "from_rel": rel_from,
            "category": cat,
            "cat_src": cat_src,
            "subject": sub,
            "sub_src": sub_src,
            "size": size,
            "sha256": sha,
        }
        if cat_src == "未判定" or sub == "未分类":
            base["reason"] = "category_undetermined" if cat_src == "未判定" \
                else "subject_undetermined"
            needs_ruling.append(base)
            continue
        to_rel = "{}/{}/{}".format(cat, sub, os.path.basename(f))
        base["to_rel"] = to_rel
        to_index.setdefault(to_rel, []).append(base)

    collisions, conflicts = [], []
    for to_rel, entries in sorted(to_index.items()):
        if len(entries) > 1:
            for e in entries:
                conflicts.append({"from_rel": e["from_rel"], "to_rel": to_rel})
            continue
        e = entries[0]
        if os.path.exists(os.path.join(ocr_root, *to_rel.split("/"))):
            collisions.append({"from_rel": e["from_rel"], "to_rel": to_rel})
            continue
        moves.append(e)

    moves.sort(key=lambda e: e["from_rel"])
    plan = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "ocr_root": ocr_root,
        "rule_source": RULE_SOURCE,
        "scan_roots": ["未分类/*/*.md", "高三/未分类/*.md"],
        "counts": {
            "scanned": len(files),
            "moves": len(moves),
            "needs_ruling": len(needs_ruling),
            "collisions": len(collisions),
            "conflicts": len(conflicts),
            "read_error": len(read_error),
            "root_level_md_out_of_scope": len(root_level_md(ocr_root)),
        },
        "plan_sha256": _fingerprint(moves),
        "moves": moves,
        "needs_ruling": needs_ruling,
        "collisions": collisions,
        "conflicts": conflicts,
        "read_error": read_error,
    }
    return plan


def write_plan(plan, out_path):
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with io.open(out_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=1)
        f.write("\n")


def run(ocr_root, out_path):
    plan = build_plan(ocr_root)
    write_plan(plan, out_path)
    return plan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ocr-root", default=r"D:\Project\Papers\Ocr-markdown")
    ap.add_argument("--out", default=r"D:\Project\Papers\data\d5b_reclassify_plan.json")
    args = ap.parse_args()
    plan = run(args.ocr_root, args.out)
    c = plan["counts"]
    print("D5-B.1 dry-run(零写入)")
    print("  scanned={} moves={} needs_ruling={} collisions={} conflicts={} read_error={} root_level_out_of_scope={}".format(
        c["scanned"], c["moves"], c["needs_ruling"], c["collisions"],
        c["conflicts"], c["read_error"], c["root_level_md_out_of_scope"]))
    print("  plan_sha256={}".format(plan["plan_sha256"]))
    print("  plan: {}".format(args.out))
    print("  (dry-run 不执行任何移动;apply 属 D5-B.2/3,须用户另行批准)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()

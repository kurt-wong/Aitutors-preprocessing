# -*- coding: utf-8 -*-
"""Backfill composite options evidence onto existing manifests.

Applies the same deterministic expansion the pipeline now runs at generation
time (`_expand_option_spans` + `_expand_composite_option_spans`) to artifacts
that were produced before composite options transport existed.

Usage:
  python backfill_composite_options.py --root <manifest_dir> [--dry-run]

Reads each *.manifest.json, loads its source .md lines, expands options, and
writes the manifest back only when something changed (unless --dry-run).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import reslice_pipeline as rp  # noqa: E402


def load_source_lines(source_file: str) -> list[str] | None:
    p = Path(source_file)
    if not p.is_file():
        return None
    return p.read_text(encoding="utf-8").splitlines()


def backfill_manifest(man_path: Path, dry_run: bool = False) -> dict:
    man = json.loads(man_path.read_text(encoding="utf-8"))
    lines = load_source_lines(man.get("source_file") or "")
    if lines is None:
        # fall back: sibling .md with same stem
        cand = man_path.with_suffix("").with_suffix(".md")
        if not cand.is_file():
            cand = man_path.parent / (man_path.name.replace(".manifest.json", ".md"))
        if cand.is_file():
            lines = cand.read_text(encoding="utf-8").splitlines()
        else:
            return {"file": str(man_path), "status": "skip_no_source", "changed": 0}

    before = {
        u.get("unit_id"): (
            [o.get("label") for o in (u.get("options") or [])],
            u.get("options_lines"),
        )
        for u in man.get("units") or []
    }

    notes = []
    notes.extend(rp._expand_option_spans(man, lines))
    notes.extend(rp._expand_composite_option_spans(man, lines))

    after = {
        u.get("unit_id"): (
            [o.get("label") for o in (u.get("options") or [])],
            u.get("options_lines"),
        )
        for u in man.get("units") or []
    }
    changed = [uid for uid in after if after[uid] != before.get(uid)]

    if changed and not dry_run:
        man_path.write_text(
            json.dumps(man, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return {
        "file": str(man_path),
        "status": "updated" if changed else "unchanged",
        "changed_units": changed,
        "changed": len(changed),
        "notes": notes,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="directory containing *.manifest.json")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    root = Path(args.root)
    manifests = sorted(root.rglob("*.manifest.json"))
    results = [backfill_manifest(p, dry_run=args.dry_run) for p in manifests]
    n_upd = sum(1 for r in results if r.get("changed"))
    print(f"manifests={len(manifests)} updated={n_upd}")
    for r in results:
        if r.get("changed") or r.get("status") != "unchanged":
            print(f"  {r['status']:10} {r['file']} units={r.get('changed_units')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

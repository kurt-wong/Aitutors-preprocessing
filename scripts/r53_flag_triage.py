r"""R53 分诊:mismatch flags 与键位答案表的人工可读抽验证据。"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fix_bug22_renumber import strip_meta  # noqa: E402

IR = json.loads((ROOT / "data/resolver_ref_r52/resolver_ir.json")
                .read_text(encoding="utf-8"))
NUM_RE = re.compile(r"^\s*(\d{1,3})\s*[.、．)）]")

mismatch = []
keyed_tables = []
by_corpus = Counter()
for r in IR["files"]:
    if not r["ir"]:
        continue
    corpus = ("batch-C" if "reslice-batch-C" in r["file"] else
              "pilot" if "resliced-pilot" in r["file"] else "PAC")
    src = Path(r["ir"]["source_file"])
    lines = strip_meta(src.read_text(encoding="utf-8",
                                     errors="replace")).splitlines()
    for u in r["ir"]["units"]:
        if "answer_number_mismatch" in (u.get("flags") or []):
            by_corpus[corpus] += 1
            at = u["answer_text"]
            mismatch.append({
                "file": Path(r["file"]).name, "unit": u["unit_id"],
                "qns": u["question_numbers"],
                "answer_first_line": at[0][:60] if at else None})
        ans = u.get("answers")
        if ans and ans["method"] == "td_by_question_number":
            keyed_tables.append({
                "file": Path(r["file"]).name, "unit": u["unit_id"],
                "cells": ans["cells"][:4],
                "answers": ans["answers"],
                "unresolved": ans["unresolved"]})

print("mismatch total:", len(mismatch), "by_corpus:", dict(by_corpus))
for m in mismatch[:8]:
    print(" ", json.dumps(m, ensure_ascii=False))
print("keyed tables:", len(keyed_tables))
for k in keyed_tables[:4]:
    print(" ", json.dumps(k, ensure_ascii=False)[:200])

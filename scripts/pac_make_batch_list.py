# -*- coding: utf-8 -*-
"""生成 PAC 批注批量清单:data/pac_batch_list.json([{file,tier},...])。

file = PAC 新鲜 OCR md(Ocr-markdown/reslice-pac/ocr/{sid}.md),
tier = PAC 类别(汇总 by_tier 用)。仅当 22 份 OCR 全部 OK 时生成,
防"半份开跑"造成账目口径混乱。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sel = json.loads((ROOT / "data/pac_selection.json").read_text(encoding="utf-8"))
track = json.loads((ROOT / "data/pac_track_ocr.json").read_text(encoding="utf-8"))

missing = [s["sample_id"] for s in sel["samples"]
           if track.get(s["sample_id"], {}).get("status") != "OK"]
if missing:
    sys.exit(f"OCR 未齐:{missing}")

picks = [{"file": track[s["sample_id"]]["output_md_path"],
          "tier": s["category"]} for s in sel["samples"]]
out = ROOT / "data/pac_batch_list.json"
out.write_text(json.dumps(picks, ensure_ascii=False, indent=1),
               encoding="utf-8", newline="")
print(f"批量清单 {out}:{len(picks)} 份")

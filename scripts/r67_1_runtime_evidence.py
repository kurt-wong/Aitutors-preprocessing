# -*- coding: utf-8 -*-
"""r67_1_runtime_evidence.py — R67.1 Gate C2/C3 运行时消费证据采集(只读)

从生产日志与 manifest 采集:
  C2:[MANIFEST_LOAD] 行(entries + digest),与 Gate A 记录 digest 对账;
  C3:本次运行(激活时刻之后)的决策路径计数——MANIFEST_DONE / NO_MANIFEST_ENTRY /
      SOURCE_CHANGED / SOURCE_UNVERIFIABLE / EXISTS(静默,不计),真实 OCR 成功追加。

输出 data/r67_1_runtime_evidence.json(确定性,除时间戳行原样引用)。
用法:python scripts/r67_1_runtime_evidence.py
"""
import hashlib
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BATCH_LOG = os.path.join(BASE, "logs", "ocr_batch_log.txt")
MANIFEST = os.path.join(BASE, "data", "ocr_output_manifest.jsonl")
BOOT_REPORT = os.path.join(BASE, "data", "r67_bootstrap_report.json")
GATE_A_DIGEST = "68762c3c68c61e7115c9528fee9b8916e512ba4da5c50b5a28625017522938ca"
ACTIVATED_AT = "2026-09-14 00:09:46"  # Gate C1:SCM 创建 watchdog/runner 时刻
REPORT = os.path.join(BASE, "data", "r67_1_runtime_evidence.json")

DECIDE_RE = re.compile(r"^\[(?P<ts>[0-9: -]+)\] \[DECIDE:(?P<reason>\w+)\] ")
LOAD_RE = re.compile(
    r"^\[(?P<ts>[0-9: -]+)\] \[MANIFEST_LOAD\] entries=(?P<n>\d+) sha256=(?P<sha>\S+)")
OK_RE = re.compile(r"^\[[0-9: -]+\]   \[OK\] (\d+) pages")
NAME_RE = re.compile(r"^\[[0-9: -]+\] \[\d+/\d+\] (.*)\.\.\.$")


def main():
    sys.path.insert(0, os.path.join(BASE, "ocr_service"))
    from output_manifest import load_manifest, validate_entry

    lines = open(BATCH_LOG, encoding="utf-8").read().splitlines()

    loads = []
    for ln in lines:
        m = LOAD_RE.match(ln)
        if m:
            loads.append({"ts": m.group("ts"), "entries": int(m.group("n")),
                          "sha256": m.group("sha")})

    # 本次激活运行窗口:激活时刻之后的行
    win = [ln for ln in lines if ln[1:20] >= ACTIVATED_AT]
    decides = {}
    for ln in win:
        m = DECIDE_RE.match(ln)
        if m:
            r = m.group("reason")
            decides[r] = decides.get(r, 0) + 1
    ok_pages = sum(int(OK_RE.match(ln).group(1)) for ln in win
                   if OK_RE.match(ln))

    # manifest 现状:可载入 + 全条目合法 + 与 bootstrap 698 的差集
    manifest = load_manifest(MANIFEST)
    for e in manifest.values():
        validate_entry(e)
    with open(BOOT_REPORT, encoding="utf-8") as f:
        boot = json.load(f)
    boot_srcs = {e["source_rel"] for e in boot["entries"]}
    new_srcs = sorted(set(manifest) - boot_srcs)
    with open(MANIFEST, "rb") as f:
        manifest_sha = hashlib.sha256(f.read()).hexdigest()

    c2_ok = (any(l["entries"] == 698 and l["sha256"] == GATE_A_DIGEST
                 for l in loads) and all(l["sha256"] != "absent" for l in loads))
    report = {
        "purpose": "R67.1 Gate C2/C3: runtime consumption of bootstrapped manifest",
        "activated_at": ACTIVATED_AT,
        "gate_c2": {
            "manifest_load_lines": loads,
            "gate_a_digest": GATE_A_DIGEST,
            "load_matches_gate_a": c2_ok,
        },
        "gate_c3": {
            "decision_counts_this_run": decides,
            "ok_pages_this_run": ok_pages,
            "manifest_done_expected": "bootstrap sources skipped via MANIFEST_DONE",
            "process_expected": "NO_MANIFEST_ENTRY sources go to real OCR",
        },
        "manifest_now": {
            "entries": len(manifest),
            "sha256": manifest_sha,
            "bootstrap_entries": len(boot_srcs),
            "appended_by_runner": len(new_srcs),
            "appended_source_rels": new_srcs,
            "all_entries_valid": True,
        },
        "consistent": bool(c2_ok and decides.get("MANIFEST_DONE", 0) > 0
                           and decides.get("NO_MANIFEST_ENTRY", 0) > 0),
    }
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in report.items() if k != "gate_c2"},
                     ensure_ascii=False, indent=1)[:1200])
    print(f"gate_c2.load_matches_gate_a={c2_ok}")
    print(f"-> {REPORT}")
    return 0 if report["consistent"] else 1


if __name__ == "__main__":
    sys.exit(main())

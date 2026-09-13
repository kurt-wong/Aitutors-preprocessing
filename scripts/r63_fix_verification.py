# -*- coding: utf-8 -*-
"""R63 一次性验证武器:BUG-32/33 修复的对抗回归(用户 R62 裁决批准修复)。

方法(黑盒,零改动重放):
  1. 冻结武器 scripts/r62_boundary_audit.py 原样重放(K1-K13 全矩阵,
     仅重定向输出到 data/r63_rerun_k_matrix.json,不触碰 R62 冻结工件);
  2. 与冻结基线 data/r62_boundary_audit.json 逐案例 before/after 对照;
  3. 断言四条:
     A. 修复后 K1-K13 全部 NO_CRASH / BATCH_CONTINUED(gap_count=0);
     B. K2-K10(损坏 provenance 家族)无一案例进入 ADMITTED*(反洗白);
     C. K1-K6(R61 既有防线)before/after 裁决不变(修复不得削弱旧防线);
     D. 基线组(未篡改四件套)保持 ADMITTED/PASS/MATCH(修复不得误伤)。
所有变异仅落 .pytest_work 合成语料;结论落 data/r63_fix_verification.json。
"""
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import r60_fact_drift_attack as r60      # noqa: E402
import r62_boundary_audit as r62         # noqa: E402  冻结武器,只重放不改

FROZEN = ROOT / "data" / "r62_boundary_audit.json"
RERUN = ROOT / "data" / "r63_rerun_k_matrix.json"
OUT = ROOT / "data" / "r63_fix_verification.json"


def main():
    # 基线组:未篡改四件套必须保持三绿(修复不得误伤正常路径)
    repo = r62._stage("R63_baseline")
    base_obs = r60.observe(repo)

    # 冻结武器零改动重放(仅换输出口)
    r62.DATA = RERUN
    r62.main()
    after = json.loads(RERUN.read_text(encoding="utf-8"))
    before = json.loads(FROZEN.read_text(encoding="utf-8"))

    rows = {}
    for name in before["manifest_cases"]:
        b, a = before["manifest_cases"][name], after["manifest_cases"][name]
        rows[name] = {"before": b["verdict"], "after": a["verdict"],
                      "before_states": {k: b["obs"].get(k)
                                        for k in ("resolver", "qc", "f1")},
                      "after_states": {k: a["obs"].get(k)
                                       for k in ("resolver", "qc", "f1")},
                      "after_reason": a["obs"].get("resolver_reason_head")}
    for name in ("K11", "K12"):
        rows[name] = {"before": before[name]["verdict"],
                      "after": after[name]["verdict"],
                      "after_states": {k: after[name].get("obs", {}).get(k)
                                       for k in ("resolver", "qc", "f1")}}
    rows["K13"] = {"before": before["K13"]["verdict"],
                   "after": after["K13"]["verdict"],
                   "after_dispositions": after["K13"].get("dispositions")}

    # 断言 A:全矩阵零崩溃缺口
    gaps_after = after["summary"]["crash_gap_cases"]
    assert_a = {"claim": "K1-K13 修复后全部 NO_CRASH/BATCH_CONTINUED",
                "gaps": gaps_after, "pass": gaps_after == []
                and after["K13"]["verdict"] == "BATCH_CONTINUED"
                and after["K12"]["verdict"] != "CONDITION_NOT_PRODUCIBLE"}

    # 断言 B:损坏 provenance 家族禁洗白(不得 ADMITTED)
    full = {n.split("_", 1)[0]: n for n in rows if "_" in n}
    washed = []
    for s in [f"K{i}" for i in range(2, 11)]:
        n = full[s]
        if str(rows[n].get("after_states", {}).get(
                "resolver", "")).startswith("ADMITTED"):
            washed.append(n)
    for n in ("K11", "K12"):
        if str(rows[n].get("after_states", {}).get(
                "resolver", "")).startswith("ADMITTED"):
            washed.append(n)
    assert_b = {"claim": "K2-K12 篡改件无一 ADMITTED(反洗白)",
                "violations": washed, "pass": not washed}

    # 断言 C:R61 既有防线(K1-K6)裁决不因修复而改变
    weakened = [full[f"K{i}"] for i in range(1, 7)
                if rows[full[f"K{i}"]]["before"] != rows[full[f"K{i}"]]["after"]
                or rows[full[f"K{i}"]]["before_states"]
                != rows[full[f"K{i}"]]["after_states"]]
    assert_c = {"claim": "K1-K6(R61 防线)before/after 逐态不变",
                "violations": weakened, "pass": not weakened}

    # 断言 D:基线组三绿
    ok_base = (base_obs.get("resolver") == "ADMITTED"
               and base_obs.get("qc") == "PASS"
               and base_obs.get("f1") == "MATCH")
    assert_d = {"claim": "未篡改基线保持 ADMITTED/PASS/MATCH",
                "obs": base_obs, "pass": ok_base}

    verdicts = {"A_no_crash": assert_a["pass"], "B_no_washthrough":
                assert_b["pass"], "C_no_weakening": assert_c["pass"],
                "D_baseline_green": assert_d["pass"]}
    result = {
        "meta": {"round": "R63", "date": date.today().isoformat(),
                 "weapon": "scripts/r63_fix_verification.py (one-off)",
                 "baseline": "data/r62_boundary_audit.json (frozen R62)",
                 "note": "冻结 R62 武器零改动重放;变异仅落 .pytest_work"},
        "rows": rows,
        "assertions": {"A": assert_a, "B": assert_b, "C": assert_c,
                       "D": assert_d},
        "verdicts": verdicts,
        "overall": "PASS" if all(verdicts.values()) else "FAIL",
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1),
                   encoding="utf-8", newline="")
    print(json.dumps({"verdicts": verdicts, "overall": result["overall"]},
                     ensure_ascii=False))
    for n, r in rows.items():
        print(f"  {n}: {r['before']} -> {r['after']}  {r.get('after_states', r.get('after_dispositions'))}")


if __name__ == "__main__":
    main()

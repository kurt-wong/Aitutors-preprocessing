# -*- coding: utf-8 -*-
"""R62 一次性对抗武器:BUG-31 修复边界攻击(R61 结果对抗审查)。

攻击面(全部在 .pytest_work/r62 合成四件套上黑盒观测,不触碰语料):
  K1   source_file 键缺失(R61 t7 回归参考)
  K2   source_file = null
  K3   source_file = ""
  K4   source_file = "   "(纯空白)
  K5   source_file = 不存在的相对路径
  K6   source_file = 已存在目录
  K7   source_file = 123(非字符串:int)
  K8   source_file = {"a":1}(非字符串:dict)
  K9   source_file = ["x"](非字符串:list)
  K10  source_file = true(非字符串:bool)
  K11  源文件含非法 UTF-8 字节(errors="replace" 路径不得崩)
  K12  源文件 ACL 拒读(OSError 路径:resolver 兜底层实证;QC/F1 观察)
  K13  批处理:good + source_file=123 的 bad(一份坏 manifest 是否杀整批)

裁决口径:三组件任一 CRASH = fail-closed 缺口(契约 C-FAIL-1:不可计算
必须机器可读拒收,禁崩);不许事后合理化。
武器一次性:本脚本不被生产链 import,结论落 data/r62_boundary_audit.json。
"""
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import r60_fact_drift_attack as r60  # noqa: E402  复用 staging/观测器
import resolver_reference as rr      # noqa: E402

WORK = ROOT / ".pytest_work" / "r62"
DATA = ROOT / "data" / "r62_boundary_audit.json"
EVERYONE = "*S-1-1-0"


def _stage(name):
    WORK.mkdir(parents=True, exist_ok=True)
    for p in (WORK / name).glob("**/*"):  # 干净重建
        if p.is_file():
            p.unlink()
    return r60.stage_repo(WORK / name)


def _classify(obs):
    crashed = [k for k in ("resolver", "qc", "f1") if obs.get(k) == "CRASH"]
    return ("CRASH_GAP:" + ",".join(crashed)) if crashed else "NO_CRASH"


def run_manifest_cases():
    cases = {
        "K1_missing_key": ("pop source_file key",
                           lambda r: r60._man_edit(r, lambda m: m.pop("source_file"))),
        "K2_null": ("source_file=null",
                    lambda r: r60._man_edit(r, lambda m: m.update(source_file=None))),
        "K3_empty": ("source_file=''",
                     lambda r: r60._man_edit(r, lambda m: m.update(source_file=""))),
        "K4_whitespace": ("source_file='   '",
                          lambda r: r60._man_edit(r, lambda m: m.update(source_file="   "))),
        "K5_nonexistent": ("source_file='nope.md'",
                           lambda r: r60._man_edit(r, lambda m: m.update(source_file="nope.md"))),
        "K6_directory": ("source_file=已存在目录(out_dir)",
                         lambda r: r60._man_edit(r, lambda m: m.update(source_file=str(r["out_dir"])))),
        "K7_int": ("source_file=123",
                   lambda r: r60._man_edit(r, lambda m: m.update(source_file=123))),
        "K8_dict": ("source_file={'a':1}",
                    lambda r: r60._man_edit(r, lambda m: m.update(source_file={"a": 1}))),
        "K9_list": ("source_file=['x']",
                    lambda r: r60._man_edit(r, lambda m: m.update(source_file=["x"]))),
        "K10_bool": ("source_file=true",
                     lambda r: r60._man_edit(r, lambda m: m.update(source_file=True))),
    }
    out = {}
    for name, (desc, mutate) in cases.items():
        repo = _stage(name)
        mutate(repo)
        obs = r60.observe(repo)
        out[name] = {"mutation": desc, "verdict": _classify(obs), "obs": obs}
        print(f"[{out[name]['verdict']}] {name} ({desc}) "
              f"resolver={obs.get('resolver')} qc={obs.get('qc')} f1={obs.get('f1')}")
    return out


def run_k11_invalid_utf8():
    repo = _stage("K11_invalid_utf8")
    repo["src"].write_bytes(repo["src"].read_bytes() + b"\x8c\x8d\xfe\xff garbage\n")
    obs = r60.observe(repo)
    res = {"mutation": "源文件追加非法 UTF-8 字节", "verdict": _classify(obs), "obs": obs}
    print(f"[{res['verdict']}] K11 resolver={obs.get('resolver')} "
          f"qc={obs.get('qc')} f1={obs.get('f1')}")
    return res


def run_k12_acl_unreadable():
    repo = _stage("K12_acl_unreadable")
    src = repo["src"]
    deny = subprocess.run(["icacls", str(src), "/deny", f"{EVERYONE}:(R)"],
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    # 先实证"拒绝读"条件真的成立,不许拿未成立的条件宣称通过
    condition = None
    method = "icacls-deny"
    try:
        src.read_text(encoding="utf-8")
        condition = "NOT_PRODUCIBLE(读取未被拒绝)"
    except OSError as e:
        condition = f"PRODUCIBLE({type(e).__name__})"
    handle = None
    if not condition.startswith("PRODUCIBLE"):
        # icacls 不可用(沙箱 rc=5)→ 换 CreateFileW 独占句柄(share=0),
        # 其它 open 一律 sharing violation → PermissionError(OSError 家族)
        method = "CreateFileW-exclusive"
        import ctypes
        GENERIC_READ = 0x80000000
        OPEN_EXISTING = 3
        handle = ctypes.windll.kernel32.CreateFileW(
            str(src), GENERIC_READ, 0, None, OPEN_EXISTING, 0, None)
        if handle == -1:
            condition = f"NOT_PRODUCIBLE(CreateFileW 失败 err={ctypes.GetLastError()})"
        else:
            try:
                src.read_text(encoding="utf-8")
                condition = "NOT_PRODUCIBLE(独占句柄下仍可读)"
            except OSError as e:
                condition = f"PRODUCIBLE({type(e).__name__})"
    res = {"mutation": "源文件拒读", "method": method,
           "condition": condition, "icacls_rc": deny.returncode}
    if condition.startswith("PRODUCIBLE"):
        obs = r60.observe(repo)
        res["verdict"] = _classify(obs)
        res["obs"] = obs
        print(f"[{res['verdict']}] K12({method}) resolver={obs.get('resolver')} "
              f"qc={obs.get('qc')} f1={obs.get('f1')} | {condition}")
    else:
        res["verdict"] = "CONDITION_NOT_PRODUCIBLE"
        print(f"[SKIP] K12 条件未成立: {condition}")
    if handle not in (None, -1):
        ctypes.windll.kernel32.CloseHandle(handle)
    subprocess.run(["icacls", str(src), "/remove:d", EVERYONE],
                   capture_output=True, text=True,
                   encoding="utf-8", errors="replace")
    return res


def run_k13_batch():
    good = _stage("K13_batch/good")
    bad = _stage("K13_batch/bad")
    r60._man_edit(bad, lambda m: m.update(source_file=123))
    res = {"mutation": "批处理:good + source_file=123 bad"}
    try:
        _, rep = rr.run([good["md"], bad["md"]], WORK / "K13_batch" / "ir")
        res["verdict"] = "BATCH_CONTINUED"
        res["dispositions"] = rep.get("dispositions")
        res["files"] = rep.get("files")
        print(f"[BATCH_CONTINUED] K13 dispositions={rep.get('dispositions')}")
    except Exception as e:  # noqa: BLE001
        res["verdict"] = "BATCH_KILLED"
        res["exc"] = f"{type(e).__name__}: {e}"
        print(f"[BATCH_KILLED] K13 {res['exc']}")
    return res


def main():
    result = {
        "meta": {"round": "R62", "date": date.today().isoformat(),
                 "weapon": "scripts/r62_boundary_audit.py (one-off)",
                 "note": "黑盒观测;所有变异仅落在 .pytest_work/r62 合成件"},
        "manifest_cases": run_manifest_cases(),
        "K11": run_k11_invalid_utf8(),
        "K12": run_k12_acl_unreadable(),
        "K13": run_k13_batch(),
    }
    gaps = [k for k, v in list(result["manifest_cases"].items())
            if v["verdict"].startswith("CRASH_GAP")]
    for key in ("K11", "K12"):
        if result[key]["verdict"].startswith("CRASH_GAP"):
            gaps.append(key)
    if result["K13"]["verdict"] == "BATCH_KILLED":
        gaps.append("K13")
    result["summary"] = {"crash_gap_cases": gaps, "gap_count": len(gaps)}
    DATA.write_text(json.dumps(result, ensure_ascii=False, indent=1),
                    encoding="utf-8", newline="")
    print(f"\nSUMMARY crash_gaps={gaps or 'NONE'} -> {DATA}")


if __name__ == "__main__":
    main()

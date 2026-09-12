# -*- coding: utf-8 -*-
r"""run_fix_chain.py — 确定性修复批处理链(清洗 → 重编译 → QC)。

串联全部已验收的确定性修复(每个脚本自身幂等,重复执行无副作用):
  1. fix_explanation_prefix.py  (BUG-17 详解区原题复述收缩)
  2. fix_orphan_imgs.py         (BUG-18 题前图并入)
  3. fix_heading_qnum.py        (BUG-19 题号行标题误标剥离)
  4. reslice_pipeline.py --recompile  (从 manifest 重编译切片/锚点)
  5. reslice_qc.py              (C1-C11 回归)

用法:
  python run_fix_chain.py --out <切片目录> [--result <qc结果路径>] [--dry]
  --dry: 全部走 dry-run,不落盘(重编译/QC 仍执行以便对比)
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\Papers")
SCRIPTS = ROOT / "scripts"
PY = sys.executable


def run(cmd, name):
    print(f"\n========== [{name}] ==========", flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    print((r.stdout or "").strip()[-2000:])
    if r.returncode != 0:
        print(f"[{name}] exit={r.returncode}")
        print((r.stderr or "").strip()[-1500:])
    return r.returncode


def main():
    # Windows 控制台 GBK:统一容错,避免子进程输出含替换字符时 print 崩溃
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="切片输出目录")
    ap.add_argument("--result", help="QC 结果 JSON 路径")
    ap.add_argument("--dry", action="store_true", help="修复步骤走 dry-run")
    args = ap.parse_args()

    apply_flag = [] if args.dry else ["--apply"]
    steps = [
        ("BUG-17 详解复述收缩", [PY, str(SCRIPTS / "fix_explanation_prefix.py"), "--out", args.out] + apply_flag),
        ("BUG-18 题前图并入", [PY, str(SCRIPTS / "fix_orphan_imgs.py")] + apply_flag),
        ("BUG-19 标题误标剥离", [PY, str(SCRIPTS / "fix_heading_qnum.py")] + apply_flag),
        ("重编译", [PY, str(SCRIPTS / "reslice_pipeline.py"), "--recompile", "--out", args.out]),
    ]
    if args.result:
        steps.append(("QC C1-C11", [PY, str(SCRIPTS / "reslice_qc.py"),
                                    "--out", args.out, "--result", args.result]))

    codes = {}
    for name, cmd in steps:
        codes[name] = run(cmd, name)

    print("\n========== [修复链汇总] ==========")
    for k, v in codes.items():
        print(f"  {'OK ' if v == 0 else 'FAIL'} {k}")
    sys.exit(1 if any(codes.values()) else 0)


if __name__ == "__main__":
    main()

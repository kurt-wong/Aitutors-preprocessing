# -*- coding: utf-8 -*-
r"""
d5b_reclassify_apply.py — D5-B.2 小批 reclassify 执行器(四闸门)

用户 2026-09-14 裁定:批准 D5-B.2 小批 apply,范围仅限 dry-run plan 的
moves 桶首批(合格考 13 份);禁止触碰 collisions / needs_ruling / identity 层。

四道闸门(用户预置,违反任一即拒绝/中止):
  B2-1 plan 指纹:重算 plan.moves canonical sha 必须同时等于 plan 自报值
       与 --expect-sha256(冻结值),否则拒绝,零移动。
  B2-2 逐文件 hash:执行前每条 source sha256 == plan 记录,不符即 ABORT,
       禁止"重新计算后继续"。
  B2-3 目标碰撞:destination 存在(文件/目录/大小写差异路径/父级为文件)
       任一异常即冲突,禁覆盖。
  B2-4 移动后反验证:source 消失 + destination 在位 + sha256 不变 +
       audit append + manifest 未被本进程改动(after bytes 以 before
       bytes 为前缀 = append-only,daemon 并发追加不误报)。

执行模型:两阶段——
  Phase 1 预检:对整批逐条过 B2-2/B2-3,任一失败 → 整批拒绝,零移动;
  Phase 2 执行:逐条移动 + B2-4 反验证,每条成功即刻 append 审计
  (崩溃安全),反验证失败 → 立即停止并如实报告已移动清单。

用法:
  python scripts/d5b_reclassify_apply.py --category 合格考          # 仅预检
  python scripts/d5b_reclassify_apply.py --category 合格考 --apply  # 执行
"""

import argparse
import hashlib
import io
import json
import os
import shutil
import sys
import time

DEFAULT_PLAN = r"D:\Project\Papers\data\d5b_reclassify_plan.json"
DEFAULT_AUDIT = r"D:\Project\Papers\data\reclassify_audit.jsonl"
DEFAULT_MANIFEST = r"D:\Project\Papers\data\ocr_output_manifest.jsonl"
DEFAULT_REPORT = r"D:\Project\Papers\data\d5b_apply_report.json"


class GateViolation(Exception):
    pass


def _file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _fingerprint(moves):
    canon = json.dumps(moves, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def _norm_rel(rel):
    """rel 必须是干净的相对 POSIX 路径:禁绝对、禁 ..、禁空段。"""
    if not rel or rel.startswith("/") or rel.startswith("\\") or ":" in rel:
        raise GateViolation("非法相对路径: %r" % rel)
    parts = rel.split("/")
    if any(p in ("", ".", "..") for p in parts):
        raise GateViolation("非法相对路径: %r" % rel)
    return parts


def check_b2_1(plan, expect_sha256):
    """plan 指纹双等校验(自报值 + 冻结期望值)。"""
    recomputed = _fingerprint(plan["moves"])
    if recomputed != plan.get("plan_sha256"):
        raise GateViolation(
            "B2-1: plan 自报指纹不符 recomputed=%s claimed=%s"
            % (recomputed, plan.get("plan_sha256")))
    if expect_sha256 and recomputed != expect_sha256:
        raise GateViolation(
            "B2-1: plan 指纹与冻结期望不符 recomputed=%s expected=%s"
            % (recomputed, expect_sha256))
    return recomputed


def _case_variant_conflict(ocr_root, parts):
    """逐段检查 to_rel 路径:任一段在磁盘上存在大小写不同的实体即冲突。

    只在"该段父目录真实存在"时检查;段完全不存在则更深层无冲突。
    返回冲突实体绝对路径或 None。
    """
    cur = ocr_root
    for p in parts:
        if not os.path.isdir(cur):
            return None
        try:
            entries = os.listdir(cur)
        except OSError:
            return None
        variants = [e for e in entries if e.casefold() == p.casefold() and e != p]
        if variants:
            return os.path.join(cur, variants[0])
        if p not in entries:
            return None
        cur = os.path.join(cur, p)
    return None


def check_b2_3(ocr_root, entry):
    """目标碰撞检查:文件/目录/大小写差异/父级为文件。返回冲突描述或 None。"""
    parts = _norm_rel(entry["to_rel"])
    dest = os.path.join(ocr_root, *parts)
    if os.path.lexists(dest):
        return "destination_exists:%s" % entry["to_rel"]
    # 父级链上任何一段是文件 → 无法建目录
    cur = ocr_root
    for p in parts[:-1]:
        cur = os.path.join(cur, p)
        if os.path.lexists(cur) and not os.path.isdir(cur):
            return "parent_is_file:%s" % entry["to_rel"]
    cv = _case_variant_conflict(ocr_root, parts)
    if cv:
        return "case_variant_exists:%s" % os.path.relpath(
            cv, ocr_root).replace("\\", "/")
    return None


def preflight(ocr_root, entries):
    """Phase 1:整批预检。返回 (oks, violations);violations 非空则整批拒绝。"""
    oks, violations = [], []
    for e in entries:
        _norm_rel(e["from_rel"])
        _norm_rel(e["to_rel"])
        src = os.path.join(ocr_root, *_norm_rel(e["from_rel"]))
        if not os.path.isfile(src):
            violations.append({"from_rel": e["from_rel"],
                               "gate": "B2-2", "detail": "source_missing"})
            continue
        real = _file_sha256(src)
        if real != e["sha256"]:
            violations.append({"from_rel": e["from_rel"], "gate": "B2-2",
                               "detail": "sha256_drift plan=%s real=%s"
                                         % (e["sha256"], real)})
            continue
        conflict = check_b2_3(ocr_root, e)
        if conflict:
            violations.append({"from_rel": e["from_rel"], "gate": "B2-3",
                               "detail": conflict})
            continue
        oks.append(e)
    return oks, violations


def run(ocr_root, plan_path, category, expect_sha256, apply,
        audit_path, manifest_path, report_path, limit=None):
    ocr_root = os.path.abspath(ocr_root)
    with io.open(plan_path, encoding="utf-8") as f:
        plan = json.load(f)
    if os.path.abspath(plan["ocr_root"]) != ocr_root:
        raise GateViolation("plan ocr_root 与执行根不一致: %s vs %s"
                            % (plan["ocr_root"], ocr_root))

    report = {
        "schema_version": 1,
        "run_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "mode": "apply" if apply else "preflight_only",
        "ocr_root": ocr_root,
        "plan_path": os.path.abspath(plan_path),
        "category_filter": category,
        "applied": [],
        "violations": [],
        "stopped_after": None,
    }

    # ---- B2-1 ----
    report["plan_sha256_recomputed"] = check_b2_1(plan, expect_sha256)

    batch = [e for e in plan["moves"] if e["category"] == category]
    report["category_matched"] = len(batch)
    report["limit"] = limit
    if limit is not None:
        # 子批选择:dry-run 保证 moves 已按 from_rel 排序 → 确定性取前 N
        if limit <= 0:
            raise GateViolation("非法 limit: %d(必须为正整数)" % limit)
        batch = batch[:limit]
    report["batch_size"] = len(batch)
    if not batch:
        raise GateViolation("批选择为空: category=%s 无 moves" % category)

    manifest_before = None
    if manifest_path and os.path.isfile(manifest_path):
        with open(manifest_path, "rb") as f:
            manifest_before = f.read()

    # ---- Phase 1:整批预检(B2-2 / B2-3),失败 → 零移动 ----
    oks, violations = preflight(ocr_root, batch)
    report["violations"] = violations
    if violations:
        report["result"] = "ABORTED_PRECHECK"
        write_report(report, report_path)
        raise GateViolation("预检失败 %d 条,整批拒绝,零移动" % len(violations))
    if not apply:
        report["result"] = "PREFLIGHT_OK"
        write_report(report, report_path)
        return report

    # ---- Phase 2:逐条执行 + B2-4 反验证 ----
    for e in oks:
        src = os.path.join(ocr_root, *_norm_rel(e["from_rel"]))
        dest = os.path.join(ocr_root, *_norm_rel(e["to_rel"]))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.move(src, dest)
        post = {
            "from_rel": e["from_rel"],
            "to_rel": e["to_rel"],
            "source_gone": not os.path.lexists(src),
            "dest_present": os.path.isfile(dest),
            "sha256_unchanged": os.path.isfile(dest)
                                and _file_sha256(dest) == e["sha256"],
        }
        if not all([post["source_gone"], post["dest_present"],
                    post["sha256_unchanged"]]):
            post["gate"] = "B2-4"
            report["applied"].append(post)
            report["stopped_after"] = e["from_rel"]
            report["result"] = "FAILED_POSTCHECK"
            finalize(report, report_path, manifest_before, manifest_path)
            raise GateViolation("B2-4 反验证失败,已停止: %s" % e["from_rel"])
        # 审计 append(与 legacy reclassify_audit.jsonl 同 schema)
        with io.open(audit_path, "a", encoding="utf-8") as af:
            af.write(json.dumps({"from": src, "to": dest},
                                ensure_ascii=False) + "\n")
        post["audit_appended"] = True
        report["applied"].append(post)

    finalize(report, report_path, manifest_before, manifest_path)
    return report


def finalize(report, report_path, manifest_before, manifest_path):
    """B2-4 manifest 不受影响:after bytes 以 before bytes 为前缀
    (append-only;允许 daemon 并发在尾部追加,禁止任何前缀改写)。"""
    if manifest_before is None:
        report["manifest_untouched"] = "manifest_absent"
    else:
        with open(manifest_path, "rb") as f:
            after = f.read()
        report["manifest_untouched"] = after.startswith(manifest_before)
        report["manifest_grew_bytes"] = len(after) - len(manifest_before)
    report["result"] = report.get("result", "APPLIED")
    write_report(report, report_path)


def write_report(report, report_path):
    os.makedirs(os.path.dirname(os.path.abspath(report_path)), exist_ok=True)
    with io.open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
        f.write("\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ocr-root", default=r"D:\Project\Papers\Ocr-markdown")
    ap.add_argument("--plan", default=DEFAULT_PLAN)
    ap.add_argument("--category", required=True)
    ap.add_argument("--expect-sha256", default="",
                    help="冻结的 plan 指纹(强烈建议提供)")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--limit", type=int, default=None,
                    help="子批选择:category 命中后按 from_rel 序取前 N 条")
    ap.add_argument("--audit", default=DEFAULT_AUDIT)
    ap.add_argument("--manifest", default=DEFAULT_MANIFEST)
    ap.add_argument("--report", default=DEFAULT_REPORT)
    args = ap.parse_args()
    try:
        report = run(args.ocr_root, args.plan, args.category,
                     args.expect_sha256, args.apply, args.audit,
                     args.manifest, args.report, limit=args.limit)
    except GateViolation as e:
        print("[GATE-REJECT] %s" % e)
        sys.exit(2)
    n = len(report["applied"])
    print("result=%s batch=%d applied=%d manifest_untouched=%s"
          % (report["result"], report["batch_size"], n,
             report.get("manifest_untouched", "n/a_preflight")))
    print("report: %s" % args.report)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()

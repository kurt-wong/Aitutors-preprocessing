# -*- coding: utf-8 -*-
"""Phase 3 收尾(R36):pilot 16 份 v1 → QuestionIdentity v2 确定性迁移。

第五轮审查 R35 裁定:Identity preprocessing contract 已闭环,但生产数据
不得并存两套 identity contract(v1 historical / v2 current)——resolver 消费
时的隐性复杂度。本脚本对 Ocr-markdown/resliced-pilot 执行零 LLM 迁移:

  - 复用 phase2_identity_backfill.backfill_file(BUG-22 迁移计划与
    bug22_migration_report 均不覆盖 pilot → basis 全部走题干首行确定性
    解析(printed_as_is)或 unknown(unverified),绝不猜测)。

迁移后自检(工具级验证,不新增 QC 规则——Identity 层已冻结;
任一违反即回滚该文件并记录 violations):
  1. migration success:identity_version==2 + sections 非空 + 单元全部
     携带 section_ref;
  2. 事实保持:question_numbers 与全部行区间(stem/answer/explanation/
     options)逐单元(按位置)不变——迁移只增 identity 键,绝不改内容事实;
  3. printed provenance 自洽:provenance==source_line ⇒ 题干首行可解析
     且解析值 == printed_number(源行证据必须回源成立);
  4. C13/C14:check_identity fails 必须为空(backfill 已拒写,此处落盘复验)。

幂等性由 tests/test_pilot_v1_migration.py 验证(二次迁移字节一致)。
默认 dry-run;--apply 写回。
报告:data/phase3_pilot_v1_migration_report.json
事实快照:data/phase3_pilot_v1_facts.json(迁移前事实,供长期回归比对)
"""
import argparse
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase2_identity_backfill as bf  # noqa: E402
import question_identity as qi  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "Ocr-markdown/resliced-pilot"
REPORT = ROOT / "data/phase3_pilot_v1_migration_report.json"
FACTS = ROOT / "data/phase3_pilot_v1_facts.json"

FACT_KEYS = ("question_numbers", "stem_lines", "answer_lines",
             "explanation_lines", "options_lines")

# --refresh-v2 时的 R36 事实锚点(main 里装载;无快照文件时保持 {})
FACTS_MAP = {}


def facts_of(man):
    """按位置提取内容事实(unit_id 可重复,位置是唯一可信键)。"""
    return [{k: u.get(k) for k in FACT_KEYS} for u in man.get("units") or []]


def verify_post(man, lines, pre_facts):
    """迁移后自检,返回 violations 列表(空 = 全部通过)。"""
    viol = []
    # 1. migration success
    if (man.get("identity_version") or 0) != 2:
        viol.append(f"identity_version != 2: {man.get('identity_version')}")
    if not man.get("sections"):
        viol.append("sections 缺失")
    units = man.get("units") or []
    if any(not u.get("section_ref") for u in units):
        viol.append("存在无 section_ref 的单元")

    # 2. 事实保持(按位置比对)
    post_facts = facts_of(man)
    if len(post_facts) != len(pre_facts):
        viol.append(f"单元数量变化: {len(pre_facts)} -> {len(post_facts)}")
    else:
        for i, (a, b) in enumerate(zip(pre_facts, post_facts)):
            if a != b:
                viol.append(f"单元#{i} 内容事实被改动: {a} -> {b}")
                break  # 一份报一条即可,避免刷屏

    # 3. printed provenance 自洽(source_line 必须回源成立)
    for u in units:
        if u.get("printed_provenance") != "source_line":
            continue
        pn, prov = bf.printed_from_stem(u, lines)
        if prov != "source_line" or pn != u.get("printed_number"):
            viol.append(f"{u.get('unit_id')}: printed_provenance=source_line "
                        f"但源行解析不成立(printed={u.get('printed_number')},"
                        f" 源行解析={pn})")

    # 4. C13/C14 落盘复验
    fails, _ = qi.check_identity(man, len(lines), lines)
    for f in fails:
        viol.append(f"check_identity: {f}")
    return viol


def migrate_file(md_path, apply=False, refresh_v2=False):
    man_path = md_path.with_suffix(".manifest.json")
    pre_bytes = man_path.read_bytes()
    pre = json.loads(pre_bytes.decode("utf-8"))
    entry = {"file": str(md_path.relative_to(ROOT)).replace("\\", "/"),
             "pre_identity_version": pre.get("identity_version") or 1}
    pre_facts = facts_of(pre)
    if (pre.get("identity_version") or 1) >= 2:
        if not refresh_v2:
            entry["skipped"] = "already_v2"
            return entry, pre_facts
        # R37 BUG-24:v2 存量也需随 SectionLocator 修复重刷 sections。
        # 刷新前必须与 R36 写入的 FACTS 事实快照逐单元一致(防内容漂移被
        # 重刷掩盖);不一致即拒绝,绝不静默覆盖。
        snap = FACTS_MAP.get(entry["file"])
        if snap is None:
            entry["violations"] = ["R36 FACTS 快照缺该文件,拒绝刷新"]
            return entry, pre_facts
        if snap != pre_facts:
            entry["violations"] = ["内容事实与 R36 FACTS 快照不一致,拒绝刷新"]
            return entry, pre_facts
        entry["refresh_v2"] = True

    src = Path(pre.get("source_file") or "")
    if not src.exists():
        entry["violations"] = [f"源文件不存在: {src}"]
        return entry, pre_facts

    e1 = bf.backfill_file(md_path, {}, apply=apply)
    entry.update({k: e1[k] for k in
                  ("units", "sections", "basis", "printed_provenance",
                   "fail_issues", "review_notes")})
    if not apply:
        entry["applied"] = False
        return entry, pre_facts
    if e1["fail_issues"]:
        # backfill 已拒绝写入(fails 非空即不落盘)
        entry["applied"] = False
        return entry, pre_facts

    post = json.loads(man_path.read_text(encoding="utf-8"))
    lines = bf.load_lines(post)
    viol = verify_post(post, lines, pre_facts)
    if viol:
        man_path.write_bytes(pre_bytes)  # 自检失败:原样回滚,绝不留半升级产物
        entry["applied"] = False
        entry["post_violations"] = viol
    else:
        entry["applied"] = True
    return entry, pre_facts


def main():
    global FACTS_MAP
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--refresh-v2", action="store_true",
                    help="R37 BUG-24:对已 v2 文件重跑回填以刷新 sections"
                         "(须与 R36 FACTS 快照一致,否则拒写)")
    args = ap.parse_args()
    if args.refresh_v2:
        if not FACTS.exists():
            print("拒绝:R36 FACTS 快照不存在,--refresh-v2 无事实锚点")
            return
        FACTS_MAP = json.loads(FACTS.read_text(encoding="utf-8"))["files"]
    results, facts = [], {}
    for p in sorted(PILOT.rglob("*.manifest.json")):
        md = p.with_name(p.name[: -len(".manifest.json")] + ".md")
        if not md.exists():
            continue
        entry, pre_facts = migrate_file(md, apply=args.apply,
                                        refresh_v2=args.refresh_v2)
        results.append(entry)
        if pre_facts is not None:
            facts[entry["file"]] = pre_facts
    if args.apply and not FACTS.exists():
        # 快照只写一次:它是防未来内容漂移的锚点,重跑不许覆写
        # (apply 时点的事实保持证明在 REPORT:15 applied / 0 violations)
        FACTS.write_text(json.dumps({"note": "迁移验证时点的内容事实快照(按位置);"
                                             "迁移只增 identity 键,事实必须不变",
                                     "files": facts},
                                    ensure_ascii=False, indent=1),
                         encoding="utf-8", newline="\n")
    elif args.apply:
        print(f"事实快照已存在,跳过写入({len(facts)} 份在场)")
    report_path = (ROOT / "data/bug24_pilot_refresh_report.json"
                   if args.refresh_v2 else REPORT)
    report_path.write_text(json.dumps(
        {"applied": args.apply, "refresh_v2": args.refresh_v2,
         "files": results}, ensure_ascii=False, indent=1),
        encoding="utf-8", newline="\n")
    napp = sum(1 for r in results if r.get("applied"))
    nviol = sum(1 for r in results if r.get("post_violations")
                or r.get("violations"))
    nfail = sum(1 for r in results if r.get("fail_issues"))
    print(f"=== pilot v1→v2 迁移:{len(results)} 份,applied={napp},"
          f"fail_issues={nfail},violations={nviol} ===")
    for r in results:
        if r.get("fail_issues") or r.get("post_violations") \
                or r.get("violations") or r.get("review_notes"):
            print(f"[!] {r['file']}")
            for i in (r.get("fail_issues") or []):
                print(f"    FAIL {i}")
            for i in (r.get("post_violations") or r.get("violations") or []):
                print(f"    VIOL {i}")
            for i in (r.get("review_notes") or []):
                print(f"    REV  {i}")


if __name__ == "__main__":
    main()

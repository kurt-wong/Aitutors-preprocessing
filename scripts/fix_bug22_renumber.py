# -*- coding: utf-8 -*-
"""BUG-22 确定性迁移工具:修复"大题内编号/分卷重编号被当全卷题号"的 8 份 batch-C 产物。

原则(R31 审查裁定的方案 C,零 LLM、全程确定性、可审计):
- 不人工改 JSON:本脚本读旧 manifest → 写新 manifest + 重新编译 annotated/切片,
  每一步变更都记录到 data/bug22_migration_report.json(旧值/新值/证据)。
- 题号身份 = (section, 题号)(R31 审查升级):迁移同时为每个单元标注所属分节,
  分节内编号(选考模块/教师用书汇编)保持印刷号——它们本来就合法重号。
- 三条证据驱动的迁移规则:
  * answer_key:答案区键位行("26.【答案】…")直接给出全卷题号(化学合格考 N1-N9→26-34);
  * shift:后分节按运行最大值顺延(生物+40、地理+50、英语+25、博雅 11-15、
    化学2018必答 26-31——与 LLM 自身 unit_id 命名(Q41-50/U26-40/U11-U15)互相印证);
  * keep:选考模块("任选一个模块作答")与汇编保持印刷号,仅凭 section 区分身份。
- 默认 dry-run;--apply 才落盘。落盘前必须通过 scoped 身份唯一性断言,否则拒绝写入。
"""
import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reslice_pipeline as rp  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

# 分节标题行:Markdown 标题、"一、/二、…"编号标题、"第X部分"、"《XX》模块试题"
SECTION_RE = re.compile(
    r"^\s*(?:#{1,4}\s*)?(?:"
    r"[一二三四五六七八九十]{1,3}\s*[、．.]\s"
    r"|第[一二三四五]部分"
    r"|《[^》]+》(?:模块)?试题?"
    r"|#{1,4}\s+\S"      # 任意 Markdown 标题(答案行由调用方另行过滤)
    r"|(?:考点|考向|考法|微专题|针对训练)\s*\d+)"  # 裸考点标题(OCR 丢 ## 前缀,如"考点3 制备…")
)
ANS_KEY_RE = re.compile(r"^\s*(\d{1,3})\s*[\.、．\\]?\s*【答案】")

# ── 迁移计划:逐文件显式声明(证据随行,审计可复算) ─────────────────────────
# mode: answer_key(答案区键位) | shift(运行最大值顺延) | keep(保持印刷号) | explicit(逐单元指定)
PLAN = {
    "2020北京高中合格考化学（第一次）（教师版）(1).md": {
        "evidence": "答案区 L698-L805 依次印 '26.【答案】'…'34.【答案】',与 N1-N9 answer_lines 起点逐行对应",
        "ops": [{"units": ["N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8", "N9"],
                 "mode": "answer_key", "evidence": "答案区键位 26-34"}],
    },
    "2018北京春季高中会考生物（教师版）(1).md": {
        "evidence": "选择题答案表(L497)键位 1-40;第二部分非选择题(L325起)印刷 1-10;LLM unit_id 已命名 Q41-Q50",
        "ops": [{"units": [f"Q{i}" for i in range(41, 51)],
                 "mode": "shift", "evidence": "非选择题顺延 +40"}],
    },
    "2018北京春季高中会考地理（教师版）(1).md": {
        "evidence": "选择题答案表(L601)键位 1-50;第二部分非选择题(L454起)印刷 1-5",
        "ops": [{"units": [f"U-P2-{i}" for i in range(1, 6)],
                 "mode": "shift", "evidence": "非选择题顺延 +50"}],
    },
    "2020北京高中合格考英语（第二次）（教师版）(1).md": {
        "evidence": "听力 1-25(答案区 L1056-1060 键位);笔试完形/阅读/写作分节续编 1-36;LLM unit_id 已命名 U26-60/Q61",
        "ops": [{"units": ["U26-40", "U41-44", "U45-48", "U49-52", "U53-56", "U57-60", "Q61"],
                 "mode": "shift", "evidence": "笔试顺延 +25"}],
    },
    "2019北京大学博雅计划模拟语文（教师版）(1).md": {
        "evidence": "大题一 10 题(L17);大题二断句(L63)/三现代文阅读(L67)/四作文(L111)各自从 1 编号;LLM unit_id 已命名 U11/U12-14/U15",
        "ops": [{"units": ["U11", "U12-14", "U15"],
                 "mode": "shift", "evidence": "二/三/四大题顺延 11/12-14/15"}],
    },
    "2018北京春季高中会考化学（教师版）(1).md": {
        "evidence": "选择题答案表(L513)键位 1-25;必答题(L208)印刷 1-6;选答题(L287)三模块任选其一,模块内印刷 1-3 为合法同号",
        "ops": [{"units": [f"U-req{i}" for i in range(1, 7)],
                 "mode": "shift", "evidence": "必答题顺延 +25"},
                {"units": [f"U-cl{i}" for i in range(1, 4)] + [f"U-org{i}" for i in range(1, 4)]
                          + [f"U-cp{i}" for i in range(1, 4)],
                 "mode": "keep", "evidence": "选考模块互斥,印刷号 1-3 保持,身份由 section 区分"}],
    },
    "2019北京三十五中新高一分班考试英语含答案(1).md": {
        "evidence": "附加题(L430起)印刷题号 86-95(L438-440);作文(L418-426)卷面无印刷题号,LLM 权宜编 86 撞附加题首号",
        "ops": [{"units": ["Q86-essay"],
                 "mode": "explicit", "values": {"Q86-essay": 96},
                 "evidence": "作文无印刷题号,按附加题最大号 95 顺延为 96"}],
    },
    "1_16_专题十六　化学实验综合　教师用书PDF.md": {
        "evidence": "教师用书汇编:各考点/针对训练/考向块独立成篇,各自从 1 编号,无全卷编号体系——身份由 section(含重复标题消歧)区分",
        "ops": [{"units": "*", "mode": "keep", "evidence": "汇编保持印刷号,scoped 身份"}],
    },
}


def strip_meta(text: str) -> str:
    return re.sub(r"<!--\s*META:[^>]*-->\n?", "", text)


def unit_start(u: dict):
    for k in ("stem_lines", "material_lines", "questions_lines", "options_lines"):
        rg = u.get(k)
        if isinstance(rg, list) and len(rg) == 2:
            return rg[0]
    return None


def derive_sections(lines, units):
    """每个单元标注最近的前置分节标题;同名标题按出现次序消歧(汇编多块'针对训练')。

    消歧序号按【标题出现次序】分配(不是按单元计数):同一标题块下的所有单元
    必须落在同一 section,否则 scoped 身份失效。小问式标题('(3) 探究…'、
    circled 数字开头)不是分节边界,排除。
    """
    sub_q = re.compile(r"^\s*[（(]\s*\d{1,3}\s*[）)]|^\s*[①②③④⑤⑥⑦⑧⑨⑩]")
    heads = []  # (line_no, text, occ)
    text_seen = Counter()
    for i, ln in enumerate(lines, 1):
        s = ln.strip()
        if SECTION_RE.match(s) and not re.search(r"答案|解析|评分", s):
            t = re.sub(r"^#{1,4}\s*", "", s)[:40]
            if sub_q.match(t):   # 小问式行('(3) 探究…')不是分节边界
                continue
            text_seen[t] += 1
            heads.append((i, t, text_seen[t]))
    out = []
    for u in units:
        st = unit_start(u)
        sec = None
        if st:
            for hl, ht, occ in heads:
                if hl <= st:
                    sec = f"{ht}#{occ}" if text_seen[ht] > 1 else ht
                else:
                    break
        out.append(sec)
    return out


def apply_ops(man, lines, ops, report):
    """按计划应用迁移规则,返回变更列表。shift 用运行最大值递推(分节重编号顺延)。"""
    running_max = 0
    changes = []
    ordered = sorted(man["units"], key=lambda x: unit_start(x) or 0)
    for u in ordered:
        uid = u["unit_id"]
        nums = list(u.get("question_numbers") or [])
        op = next((o for o in ops if o["units"] == "*" or uid in o["units"]), None)
        if op is None or not nums:
            running_max = max(running_max, *(nums or [0]))
            continue
        mode = op["mode"]
        new_nums = nums
        if mode == "shift":
            if min(nums) <= running_max:
                off = running_max - min(nums) + 1
                new_nums = [n + off for n in nums]
        elif mode == "answer_key":
            a = u.get("answer_lines")
            if a and isinstance(a, list) and a[0] <= len(lines):
                m = ANS_KEY_RE.match(lines[a[0] - 1])
                if m:
                    new_nums = [int(m.group(1))]
        elif mode == "explicit":
            new_nums = [op["values"][uid]]
        elif mode == "keep":
            new_nums = nums
        if new_nums != nums:
            changes.append({"unit_id": uid, "old": nums, "new": new_nums,
                            "mode": mode, "evidence": op.get("evidence")})
            u["question_numbers"] = new_nums
        running_max = max(running_max, *(u.get("question_numbers") or [0]))
    return changes


def assert_scoped_unique(man):
    ident = Counter()
    for u in man["units"]:
        sec = u.get("section") or ""
        for n in (u.get("question_numbers") or []):
            ident[(sec, n)] += 1
    dups = sorted((s or "∅", n) for (s, n), c in ident.items() if c > 1)
    if dups:
        raise AssertionError(f"迁移后 scoped 身份仍冲突: {dups[:10]}")


def migrate_file(md_path: Path, apply=False):
    man_path = md_path.with_suffix(".manifest.json")
    man = json.loads(man_path.read_text(encoding="utf-8"))
    plan = PLAN[md_path.name]
    src_path = Path(man["source_file"])
    src_text = strip_meta(src_path.read_text(encoding="utf-8", errors="replace"))
    lines = src_text.splitlines()

    # 注意:汇编类 manifest 的 unit_id 会重复(U1/Q1/Q2 各出现多次),
    # 分节按【单元位置】分配,绝不能以 unit_id 为键(R31 迁移实测踩坑)。
    sections = derive_sections(lines, man["units"])
    for u, sec in zip(man["units"], sections):
        u["section"] = sec

    issues_before, _ = rp.validate_manifest(man, len(lines), lines)
    changes = apply_ops(man, lines, plan["ops"], None)
    assert_scoped_unique(man)
    issues_after, _ = rp.validate_manifest(man, len(lines), lines)

    entry = {"file": str(md_path), "source": str(src_path),
             "plan_evidence": plan["evidence"],
             "changes": changes,
             "sections": [[u["unit_id"], u.get("section")] for u in man["units"]],
             "validate_issues_before": issues_before,
             "validate_issues_after": issues_after,
             "applied": bool(apply)}
    if apply:
        model = man.get("model") or rp.DEFAULT_MODEL
        ann = rp.compile_anchor(lines, man, src_path.name, src_path, model=model)
        ann = ann.replace("prompt=reslice-pilot-v2.2",
                          "prompt=reslice-pilot-v2.1+migration-bug22-r31", 1)
        (md_path.with_name(md_path.stem + ".annotated.md")).write_text(ann, encoding="utf-8", newline="\n")
        md, _ = rp.compile_slices(lines, man, src_path.name, src_path, model=model)
        md_path.write_text(md, encoding="utf-8", newline="\n")
        man.setdefault("annotation_meta", {})["bug22_migration"] = {
            "round": "r31", "changes": changes,
            "plan_evidence": plan["evidence"],
            "report": "data/bug22_migration_report.json"}
        man_path.write_text(json.dumps(man, ensure_ascii=False, indent=1),
                            encoding="utf-8", newline="\n")
    return entry


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT / "Ocr-markdown/reslice-batch-C"))
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--report", default=str(ROOT / "data/bug22_migration_report.json"))
    args = ap.parse_args()

    entries, missing = [], []
    for name in sorted(PLAN):
        hits = list(Path(args.root).rglob(name))
        if not hits:
            missing.append(name)
            continue
        e = migrate_file(hits[0], apply=args.apply)
        entries.append(e)
        n_chg = len(e["changes"])
        print(f"[{'APPLY' if args.apply else 'DRY'}] {name}: {n_chg} 单元变更, "
              f"验证 issue {len(e['validate_issues_before'])}→{len(e['validate_issues_after'])}")
        for c in e["changes"]:
            print(f"    {c['unit_id']}: {c['old']} → {c['new']} ({c['mode']})")

    report = {"generated": datetime.now().isoformat(timespec="seconds"),
              "applied": bool(args.apply), "files": entries, "missing": missing}
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=1),
                                 encoding="utf-8", newline="\n")
    print(f"报告已写入 {args.report}")
    if missing:
        print(f"!! 未找到 {len(missing)} 份计划内文件: {missing}")
        sys.exit(2)


if __name__ == "__main__":
    main()

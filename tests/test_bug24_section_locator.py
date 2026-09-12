# -*- coding: utf-8 -*-
"""BUG-24 验收测试(R37)——用户冻结的 8 条标准 B24-01~B24-08。

变更边界(冻结令):只修 SectionLocator 的 Source structure 层
(question_identity._heading_rows 排除器两阶段识别),不动 Identity/keep/
basis/C13/C14 语义。

测试纪律(与 R34/R35/R36 一致):
  - 真实语料测试无语料时干净 skip(快照 JSON 存在不作为语料存在性证明);
  - 每个方向同时测"该恢复的恢复"与"该排除的排除"(R33 反方向教训);
  - 变异 sanity:回灌 BUG-24 缺陷形态与两种窗口破坏,证明测试数据有区分力。
"""
import json
import re
from pathlib import Path

import pytest

import phase2_identity_backfill as bf
import question_identity as qi
import reslice_qc as qc

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "Ocr-markdown/resliced-pilot"
BATCH = bf.DEFAULT_OUT

# ── 真实语料回归语料(全部取自 R37 全语料盘点发现的真实行,硬编码入库) ──────

# A 类:真实分节标题,marker(答案/评分)只出现在尾部 note——修复目标
NOTE_MARKER_HEADINGS = [
    # 三十一中化学 L324(B24-01 主案例)
    "## 二、 填空题(共11题，共计55分) 注意：只有填写在答题纸上的答案才计分。",
    # 会考化学 L287(选答题分节,含"评分"note)
    "## 二、 选答题（共20分。请在以下三个模块试题中任选一个模块试题作答，"
    "若选答了多个模块的试题，以所答第一模块的试题评分）",
    # 会考数学 L5/L198(备选答案)
    "## 一、 在每个小题给出的四个备选答案中，只有一个符合题目要求的",
    # 平谷历史 L19(选择题分节,答案填涂 note)
    "## 一、 选择题(本大题共50小题,每题1分,共50分。每小题四个选项中只有一项"
    "符合题目要求,请将正确答案填涂在机读卡相应位置。)",
    # 石景山一模物理 L234(计算题分节,答案要求 note)
    "## 三、 本题共4小题，共40分。解答应写出必要的文字说明、方程和重要步骤。"
    "只写出最后答案的不能得分。有数值计算的题，答案中必须明确写出数值和单位。",
]

# B 类:答案区行/答案块标题——必须维持排除(R36 的 135 行 naive 收窄风险面)
ANSWER_SHAPE_LINES = [
    "### 9. 【答案】C",                        # 合格考政治 答案键位(###题号)
    "###### 【答案】32. A 33. C 34. A 35. B",  # 甲卷英语 六级标题(六 # 漏网形态)
    "## 【1~10题答案】阅读理解",                # 一零一英语 答案块
    "### 【解答】【答案】见解析",                # 政治汇编 解答块
    "## ☑答案 B",                              # 教师用书专题 ☑答案 行
    "## 选、填答案",                            # 八十中数学 答案块标题
    "### （12分）参考答案示例：",               # 人大附中高三三模历史
    "## （2） 答案见解析",                      # 丰台高一期中数学
    # R38 审计发现:OCR 转义点("26 \.")曾击穿数字前缀剥离,8 例答案块被误升;
    # 修复(序号前缀允许转义点)后必须维持排除
    r"### 26 \. （12分）【答案】",              # 临川高二政治
    r"### 23 \. (6分) 【解析】",                # 东城高二物理
    r"### 18 \. （8分）答案示例",               # 朝阳高三二模历史
    r"### 20 \. （14分）参考答案示例：",        # 西城高三一模历史
]

# C 类:行为锁定(人检裁定为 benign 的恢复 + 诚实残留边界)
BENIGN_RESTORED = [
    "# 2018年北京市春季普通高中会考 地理试卷答案及评分参考",  # 答案卷 H1 题
]
KNOWN_RESIDUAL_EXCLUDED = [
    "## 解析几何",  # topic 词假阴性:全语料仅此 1 例(汇编卷),不为 1 例扩规则面
]

AFFECTED_BATCH_C = [
    "2018北京春季高中会考化学（教师版）(1).md",
    "2018北京春季高中会考地理（教师版）(1).md",
    "2018北京春季高中会考数学（教师版）(1).md",
    "2018北京春季高中会考物理（教师版）(1).md",
    "19_2023重庆市巴蜀中学高考适应性月考卷（九）化学答案.md",
    "2020北京平谷高一（上）期末历史含答案.md",
    "2019北京三十五中新高一分班考试英语含答案(1).md",
]


def _require_corpus():
    if not (BATCH.exists() and PILOT.exists()):
        pytest.skip("reslice 语料不在本 checkout(快照存在不作为语料存在性证明)")


def _find_md(root, name):
    hits = [p for p in root.rglob(name) if not p.name.endswith(
        (".annotated.md", ".restored.md"))]
    assert hits, f"语料缺文件: {name}"
    return hits[0]


# ── B24-01 真实错误标题被恢复(合成镜像 + 真实卷双层) ──────────────────────
def test_b24_01_heading_with_note_marker_restored_synthetic():
    lines = ["# 卷", "", NOTE_MARKER_HEADINGS[0], "1. 甲（ ）"]
    heads = qi._heading_rows(lines)
    assert any(ln == 3 and "填空题" in t for ln, t, _ in heads), \
        "note-marker 真分节标题必须被识别"
    secs = qi.build_section_locators(lines)
    fill = [s for s in secs if s.get("title", "") and "填空题" in s["title"]]
    assert fill and fill[0]["start_line"] == 3


def test_b24_01_real_file_chemistry_restored():
    _require_corpus()
    md = _find_md(PILOT, "2021北京三十一中高一（下）期中化学（教师版）(1).md")
    lines = bf.load_lines(json.loads(
        md.with_suffix(".manifest.json").read_text(encoding="utf-8")))
    heads = qi._heading_rows(lines)
    assert any(ln == 324 and "填空题" in t for ln, t, _ in heads), \
        "B24-01:三十一中化学 L324 填空题分节必须被恢复"
    # 数据有效性:该行确实含 marker(旧整行排除器会杀它)——变异 sanity 的锚
    assert re.search(r"答案|解析|评分", lines[323])


# ── B24-02 已知答案区行不得被误识别为分节(135 行风险面回归语料) ─────────────
def test_b24_02_answer_lines_stay_excluded():
    for ln in ANSWER_SHAPE_LINES:
        assert qi.SECTION_RE.match(ln), f"回归语料失效(不再是标题候选): {ln}"
        assert re.search(r"答案|解析|评分", ln), f"回归语料失效(无 marker): {ln}"
        assert qi._heading_rows([ln]) == [], f"答案区行被误升为分节: {ln}"
        assert qi._is_answer_heading(ln), f"排除判定失效: {ln}"


def test_b24_02b_note_marker_headings_all_restored():
    for ln in NOTE_MARKER_HEADINGS:
        assert qi.SECTION_RE.match(ln)
        assert re.search(r"答案|解析|评分", ln), "数据失效:无 marker 则测不出区分力"
        assert qi._heading_rows([ln]) != [], f"真分节标题仍被误杀: {ln[:30]}"


def test_b24_02c_behavior_locks():
    for ln in BENIGN_RESTORED:
        assert qi._heading_rows([ln]) != [], f"行为漂移(benign 恢复被撤销): {ln[:30]}"
    for ln in KNOWN_RESIDUAL_EXCLUDED:
        assert qi._heading_rows([ln]) == [], f"行为漂移(残留边界被扩大): {ln}"


# ── B24-03 受影响真实产物全链重跑(source→sections→identity→C13/C14→QC) ─────
def test_b24_03_affected_batch_c_full_chain():
    _require_corpus()
    after = json.loads((ROOT / "data/bug24_after_batch_c_qc.json")
                       .read_text(encoding="utf-8"))
    verdict = {Path(r["file"]).name: r["verdict"] for r in after}
    for name in AFFECTED_BATCH_C:
        md = _find_md(BATCH, name)
        man = json.loads(md.with_suffix(".manifest.json").read_text(encoding="utf-8"))
        lines = bf.load_lines(man)
        fails, _ = qi.check_identity(man, len(lines), lines)
        assert fails == [], f"{name} 身份层 fail: {fails}"
        assert qc.check(md)["verdict"] == verdict[name], f"{name} QC 裁决漂移"


# ── B24-04 SectionLocator 修复不得自动产生 keep;三十一中仍 fail-closed ──────
def test_b24_04_no_auto_keep_still_refused():
    _require_corpus()
    md = _find_md(PILOT, "2021北京三十一中高一（下）期中化学（教师版）(1).md")
    entry = bf.backfill_file(md, {}, apply=False)  # dry-run:绝不落盘
    assert entry["fail_issues"], "两个非 keep 跨节重号必须仍然 FAIL(fail-closed)"
    assert all("跨分节" in f for f in entry["fail_issues"]), \
        f"FAIL 理由必须是正确建模后的跨分节冲突: {entry['fail_issues'][:2]}"
    assert "keep" not in (entry["basis"] or {}), "确定性回填不得自动制造 keep"


# ── B24-05 BUG-22 原型不得重新放行(修 locator 时 C13 不退回 R33) ─────────────
def test_b24_05_bug22_prototype_still_fails():
    lines = ["# 卷", "", NOTE_MARKER_HEADINGS[0], "1. 甲（ ）", "",
             "## 一、选择题", "1. 乙（ ）"]
    man = {"units": [
        {"unit_id": "F1", "question_numbers": [1], "stem_lines": [4, 4],
         "unit_type": "standalone_question"},
        {"unit_id": "Q1", "question_numbers": [1], "stem_lines": [7, 7],
         "unit_type": "standalone_question"},
    ]}
    qi.assign_identity(man, lines)
    assert man["units"][0]["section_ref"] != man["units"][1]["section_ref"]
    fails, _ = qi.check_identity(man, len(lines))
    assert any("非 keep" in f for f in fails), "两个非 keep 跨节重号必须 FAIL"


# ── B24-06 既有 PASS 集不发生非法翻转(batch-C 38 + pilot 15) ─────────────────
def test_b24_06_existing_pass_set_no_regression():
    _require_corpus()
    pairs = [("bug24_before_batch_c_qc.json", BATCH),
             ("bug24_before_pilot_qc.json", PILOT)]
    checked = 0
    for report, out_dir in pairs:
        data = json.loads((ROOT / "data" / report).read_text(encoding="utf-8"))
        for r in data:
            if r["verdict"] != "PASS":
                continue
            md = _find_md(out_dir, Path(r["file"]).name)
            got = qc.check(md)["verdict"]
            assert got == "PASS", f"非法翻转: {Path(r['file']).name} PASS→{got}"
            checked += 1
    assert checked >= 50, f"覆盖面不足: 仅 {checked} 份"


# ── B24-07 locator 确定性:同源重跑 sections/ordinal/occurrence/span 全同 ─────
def test_b24_07_locator_deterministic():
    lines = ["# 卷", ""] + NOTE_MARKER_HEADINGS + ANSWER_SHAPE_LINES + [
        "", "## 一、选择题", "1. 甲", "## 一、选择题", "2. 乙"]
    assert qi.build_section_locators(lines) == qi.build_section_locators(lines)
    assert qi._heading_rows(lines) == qi._heading_rows(lines)


def test_b24_07b_real_file_deterministic():
    _require_corpus()
    md = _find_md(PILOT, "2021北京三十一中高一（下）期中化学（教师版）(1).md")
    lines = bf.load_lines(json.loads(
        md.with_suffix(".manifest.json").read_text(encoding="utf-8")))
    assert qi.build_section_locators(lines) == qi.build_section_locators(lines)


# ── B24-08 Evidence Soundness 层不受影响(note-marker 标题行仍是结构证据载体) ─
def test_b24_08_evidence_semantics_untouched():
    ev = "分节依据;L3"
    u = {"basis_evidence": ev, "question_numbers": [1], "printed_number": [1]}
    # L3 是带 note marker 的真分节标题:SECTION_RE 命中 → 语义豁免路径不变
    assert qi.evidence_semantic_reason(u, ["# 卷", "", NOTE_MARKER_HEADINGS[0]],
                                       3) is None
    # 纯 prose 行依旧无编号语义(R35 c09 回归锚)
    u2 = {"basis_evidence": "L2", "question_numbers": [1], "printed_number": [1]}
    assert qi.evidence_semantic_reason(u2, ["# 卷", "本卷依据课标命制。"], 2)


# ── 变异 sanity:回灌缺陷形态与两种窗口破坏,证明测试数据有区分力 ─────────────
def test_mutation_sanity_b24_defect_shapes_discriminate(monkeypatch):
    # 变异 1:还原 BUG-24 缺陷(整行子串排除)→ 真分节标题必须全部消失
    monkeypatch.setattr(qi, "_is_answer_heading",
                        lambda s: bool(re.search(r"答案|解析|评分", s)))
    for ln in NOTE_MARKER_HEADINGS[:1]:
        assert qi._heading_rows([ln]) == [], \
            "变异无效:缺陷形态回灌后标题仍在,测试数据无区分力"

    # 变异 2:窗口归零(无排除)→ 答案行必须被误升
    monkeypatch.undo()
    monkeypatch.setattr(qi, "HEAD_WINDOW", 0)
    assert qi._heading_rows([ANSWER_SHAPE_LINES[4]]) != [], \
        "变异无效:排除机制不是 load-bearing"

    # 变异 3:窗口无限(marker 任意位置)→ note-marker 标题必须被误杀
    monkeypatch.undo()
    monkeypatch.setattr(qi, "HEAD_WINDOW", 10 ** 6)
    assert qi._heading_rows([NOTE_MARKER_HEADINGS[2]]) == [], \
        "变异无效:头部窗口不是 load-bearing"

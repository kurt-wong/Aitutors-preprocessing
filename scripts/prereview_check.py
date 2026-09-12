"""预审脚本：对 auto-annotated-v6 审核样本做结构完整性机器校验。

判定依据（与用户确认的批注规则 + V3 契约）：
  R1 入库单元=完整题：题干+选项+配图/表格+答案（详解可选）
  R2 共享前置材料=>材料+全部子题+答案整合为一道综合题（composite）
  R3 答案区跟随综合题，逐小题答案齐全
  R4 子题逐题齐全
  R5 表格必须保留
  R6 图片占位+锚点即可
  R7 作文算完整题
  R8 不判答案对错
  R9 卷面指令类（本大题共X小题/答题卡提示）不入库

输出：prereview_report.json + prereview_report.md
用法：python prereview_check.py [--sample <review_sample.json>]
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\Papers")
SAMPLE = ROOT / "Ocr-markdown/auto-annotated-v6/review_sample.json"

Q_START = re.compile(r"<!--\s*META:question:start:(\d+),([\w]+)\s*-->")
Q_END = re.compile(r"<!--\s*META:question:end:(\d+)\s*-->")
A_START = re.compile(r"<!--\s*META:answer:start:(\d+)\s*-->")
A_END = re.compile(r"<!--\s*META:answer:end:(\d+)\s*-->")
E_START = re.compile(r"<!--\s*META:explanation:start:(\d+)\s*-->")
E_END = re.compile(r"<!--\s*META:explanation:end:(\d+)\s*-->")

# ---- 题号 OCR 噪音归一化 ----
# 常见噪音：markdown 转义残留 "1.\"；全角句号/顿号 "1．" "1、"；加粗 "**1.**"；
# 标题符 "### 1."；全角数字 "１."；序号后多余空格/点 "1 ." "1.."；
_FW_DIGITS = str.maketrans("０１２３４５６７８９", "0123456789")
QNUM_CANON = re.compile(r"^(\d{1,3})\s*[\.．。、\)）\]］:：]\s*")


def normalize_qnum(line):
    """行首题号噪音归一化：返回 (题号, 归一化后剩余行) 或 None。
    可被重切流水线复用。"""
    s = line.strip()
    s = re.sub(r"^#{1,6}\s*", "", s)          # markdown 标题符
    s = re.sub(r"^\*\*+", "", s)               # 行首加粗
    s = s.replace("\\", "")                    # markdown 转义残留（\" \. 等）
    s = s.translate(_FW_DIGITS)                # 全角数字
    m = QNUM_CANON.match(s)
    if not m:
        return None
    return int(m.group(1)), s[m.end():]
# 疑似未标注答案区的行
ANS_LINE = re.compile(r"^\s*(?:参考答案|答案|【答案】)\s*$")
ANS_COMPACT = re.compile(r"\d{1,3}\s*[\.．、:：\-–]?\s*[（(]?\d{0,2}分?[)）]?\s*[A-DＡ-Ｄ]{1,4}(?:\s|$)")
ANS_RANGE = re.compile(r"\d{1,3}\s*[–\-~—]\s*\d{1,3}\s*[A-DＡ-Ｄ]{2,}")
# 综合题信号（材料依赖）
COMPOSITE_CUE = re.compile(
    r"阅读下面|阅读下列|读下列|读图|材料一|材料二|完成\s*\d+|回答下列|"
    r"根据材料|结合材料|完成下列|阅读材料|实验题|工艺流程|下列短文|"
    r"读图文|读图表|下图为|下表为|下图是|下表是|如图.{0,6}所示.{0,20}回答"
)
# 卷面指令（不入库元素，用于 R9 检查——若被包进题块则记录）
BOILERPLATE = re.compile(
    r"本大题共|本试题共|共\s*\d+\s*小题|请将答案.{0,10}答题卡|在答题卡|答题卡指定区域|"
    r"考试时间|满分\s*\d+\s*分|注意事项"
)
IMG_REF = re.compile(r"!\[[^\]]*\]\([^)]+\)|<img|配图|imgs/")
TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")

# ---- 答案表格解析（HTML table：数字行 + 字母行 成对交替） ----
TD = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
TR = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
TABLE = re.compile(r"<table[^>]*>(.*?)</table>", re.S)


def parse_answer_tables(text):
    """从 HTML 表格解析 题号->答案 映射（数字行配对紧随其后的字母行）。"""
    mapping = {}
    for tb in TABLE.findall(text):
        rows = []
        for tr in TR.findall(tb):
            cells = [re.sub(r"<[^>]+>", "", c).strip() for c in TD.findall(tr)]
            rows.append(cells)
        for i in range(len(rows) - 1):
            a, b = rows[i], rows[i + 1]
            if (len(a) == len(b) and len(a) >= 3
                    and all(c.isdigit() or c == "" for c in a)
                    and all(re.fullmatch(r"[A-DＡ-Ｄ]{1,4}", c) or c == "" for c in b)):
                for num, ans in zip(a, b):
                    if num.isdigit() and ans:
                        mapping[int(num)] = ans
    return mapping


# ---- 区间连写答案解析："1-5 ACDBA" / "1–5ACDBA" / "16–20ADBBC21–25CBADD"（粘连） ----
RANGE_ANS = re.compile(r"(?<![\d.])(\d{1,3})\s*[–\-~—]\s*(\d{1,3})\s*([A-DＡ-Ｄ]{2,})")
_FW = str.maketrans("ＡＢＣＤ", "ABCD")


def parse_range_answers(text):
    mapping = {}
    for m in RANGE_ANS.finditer(text):
        lo, hi = int(m.group(1)), int(m.group(2))
        letters = m.group(3).translate(_FW)
        if hi >= lo and len(letters) == hi - lo + 1 and hi - lo >= 1:
            for k, ch in enumerate(letters):
                mapping.setdefault(lo + k, ch)
    return mapping


def parse_blocks(text):
    """解析 META 标记，返回有序事件列表。"""
    events = []
    for rx, kind in ((Q_START, "q_start"), (Q_END, "q_end"),
                     (A_START, "a_start"), (A_END, "a_end"),
                     (E_START, "e_start"), (E_END, "e_end")):
        for m in rx.finditer(text):
            events.append((m.start(), kind, int(m.group(1)), m.group(0)))
    events.sort()
    return events


def segment(text, events):
    """把文本切成 [块类型, 标号, 正文] 列表，以及无标记区段。"""
    blocks = []
    open_stack = {}
    unmarked = []  # (起始偏移, 结束偏移, 正文)
    cursor = 0
    for pos, kind, num, raw in events:
        if kind.endswith("_start"):
            if kind[0] in open_stack:
                blocks.append(("MALFORMED", open_stack[kind[0]][1],
                               text[open_stack[kind[0]][0]:pos]))
            open_stack[kind[0]] = (pos + len(raw), num)
            if pos > cursor:
                seg = text[cursor:pos]
                if seg.strip():
                    unmarked.append((cursor, pos, seg))
        else:  # _end
            if kind[0] in open_stack:
                start, snum = open_stack.pop(kind[0])
                blocks.append((kind[0], snum, text[start:pos]))
                cursor = pos + len(raw)
    tail = text[cursor:]
    if tail.strip():
        unmarked.append((cursor, len(text), tail))
    return blocks, unmarked


def analyze(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    events = parse_blocks(text)
    blocks, unmarked = segment(text, events)
    issues = []   # (severity, code, desc)
    info = {}

    q_blocks = [(n, b) for t, n, b in blocks if t == "q"]
    a_blocks = [(n, b) for t, n, b in blocks if t == "a"]
    e_blocks = [(n, b) for t, n, b in blocks if t == "e"]
    malformed = [b for t, n, b in blocks if t == "MALFORMED"]
    info["questions"] = len(q_blocks)
    info["answers"] = len(a_blocks)
    info["explanations"] = len(e_blocks)

    if malformed:
        issues.append(("P0", "MARKER_MALFORMED", f"{len(malformed)} 处嵌套/未闭合标记"))

    # --- 重复标记号（如两个 answer:start:5） ---
    from collections import Counter as _C
    dup_a = [n for n, c in _C(n for n, _ in a_blocks).items() if c > 1]
    dup_q = [n for n, c in _C(n for n, _ in q_blocks).items() if c > 1]
    if dup_a:
        issues.append(("P1", "ANSWER_LABEL_DUP", f"答案标记号重复: {sorted(dup_a)[:10]}"))
    if dup_q:
        issues.append(("P1", "QUESTION_LABEL_DUP", f"题块标记号重复: {sorted(dup_q)[:10]}"))

    # --- 题块边界（综合题感知）：
    #     块内多题号 + 有综合题信号 => 整合正确（composite，符合 R2）；
    #     块内多题号 + 无综合题信号 => 独立题被合并（边界错误） ---
    merged_indep = []
    composite_ok = []
    contained_nums = set()   # 全部题块内出现的题号（子题粒度，用于答案覆盖）
    for n, b in q_blocks:
        nums = []
        for line in b.splitlines():
            hit = normalize_qnum(line)
            if hit:
                v = hit[0]
                if not nums or nums[-1] != v:
                    nums.append(v)
        distinct = sorted(set(nums))
        contained_nums.update(distinct)
        if len(distinct) > 1:
            if COMPOSITE_CUE.search(b):
                composite_ok.append((n, distinct))
            else:
                merged_indep.append((n, distinct))
    info["composite_blocks"] = len(composite_ok)
    if merged_indep:
        desc = "; ".join(f"块{n}含题号{ds}" for n, ds in merged_indep[:6])
        issues.append(("P1", "Q_BLOCK_MERGED_INDEPENDENT",
                       f"{len(merged_indep)} 个题块合并了多道独立题（无共享材料）: {desc}"))

    # --- 题号序列连续性：跳变若被前块吞入（题号在块内出现过）则不算缺口 ---
    labeled = [n for n, _ in q_blocks]
    gaps = []
    for i in range(1, len(labeled)):
        if labeled[i] != labeled[i - 1] + 1 and labeled[i] > labeled[i - 1]:
            mid = set(range(labeled[i - 1] + 1, labeled[i]))
            if not mid.issubset(contained_nums):
                gaps.append((labeled[i - 1], labeled[i]))
    if gaps:
        issues.append(("P2", "QNUM_GAP",
                       f"标记题号存在真实缺口（前块未包含）: {gaps[:8]}"))

    # --- 答案覆盖（子题粒度）：
    #     应有 = 所有题块内出现的题号；实有 = 答案块标记号 + 答案块正文内解析出的题号
    #     （综合题一个答案块可覆盖多个子题号，如 "11.C 12. D 13. A"） ---
    ANS_SUBNUM = re.compile(r"(?<![\d.\-–])(\d{1,3})\s*[\.．、]?\s*[（(]?\d{0,2}\s*分?[)）]?\s*[:：]?\s*[A-DＡ-ＤⅠⅡⅢⅣ]")
    available_nums = set(n for n, _ in a_blocks)
    for n, b in a_blocks:
        for m in ANS_SUBNUM.finditer(b):
            available_nums.add(int(m.group(1)))
    # 答案表格（数字行/字母行成对的 HTML table）也算答案来源
    tbl_ans = parse_answer_tables(text)
    if tbl_ans:
        available_nums.update(tbl_ans)
        info["table_answer_count"] = len(tbl_ans)
        only_tbl = sorted(set(tbl_ans) - set(n for n, _ in a_blocks))
        if only_tbl:
            issues.append(("P2", "ANSWER_IN_TABLE",
                           f"{len(only_tbl)} 题的答案仅存在于答案表格（未标注答案块，"
                           f"重切时需展开为逐题答案）: {only_tbl[:10]}"))
    # 区间连写答案（"1-5 ACDBA" 形态）也算答案来源
    rng_ans = parse_range_answers(text)
    if rng_ans:
        available_nums.update(rng_ans)
        info["range_answer_count"] = len(rng_ans)
        only_rng = sorted(set(rng_ans) - set(n for n, _ in a_blocks))
        if only_rng:
            issues.append(("P2", "ANSWER_IN_RANGE",
                           f"{len(only_rng)} 题的答案仅以区间连写形式存在（未标注答案块，"
                           f"重切时需展开为逐题答案）: {only_rng[:10]}"))
    expected_nums = contained_nums if contained_nums else set(n for n, _ in q_blocks)
    miss_a = sorted(expected_nums - available_nums)
    qset, aset = set(n for n, _ in q_blocks), set(n for n, _ in a_blocks)
    extra_a = sorted(aset - qset - contained_nums)
    if miss_a:
        issues.append(("P0" if len(miss_a) > len(expected_nums) * 0.3 else "P1",
                       "ANSWER_MISSING",
                       f"{len(miss_a)}/{len(expected_nums)} 题无对应答案: {miss_a[:15]}"))
    if extra_a:
        issues.append(("P1", "ANSWER_ORPHAN",
                       f"{len(extra_a)} 个答案标记无对应题块: {extra_a[:15]}"))

    # --- 疑似整段未标注的答案区（无标记区段中） ---
    bare_ans = []
    for _, _, seg in unmarked:
        lines = [l for l in seg.splitlines() if l.strip()]
        hit = sum(1 for l in lines
                  if ANS_RANGE.search(l) or ANS_COMPACT.match(l) or ANS_LINE.match(l.strip()))
        if lines and hit >= 3 and hit >= len(lines) * 0.4:
            bare_ans.append(seg.strip()[:60].replace("\n", " "))
        elif "参考答案" in seg and hit > 0:
            bare_ans.append(seg.strip()[:60].replace("\n", " "))
    if bare_ans:
        issues.append(("P0", "ANSWER_ZONE_UNANNOTATED",
                       f"{len(bare_ans)} 处疑似答案区未标注: {bare_ans[:3]}"))

    # --- 综合题信号与材料完整性 ---
    comp_blocks = [(n, b) for n, b in q_blocks if COMPOSITE_CUE.search(b)]
    info["composite_cue_blocks"] = len(comp_blocks)
    # 材料题块内是否含 (1)(2)(3) 子问与答案要点缺失: 仅记录，语义审查用
    # 材料出现在无标记区段（切散信号）
    for _, _, seg in unmarked:
        if COMPOSITE_CUE.search(seg) and len(seg.strip()) > 80:
            issues.append(("P1", "MATERIAL_OUTSIDE",
                           f"疑似材料/阅读文本在题块外: {seg.strip()[:50]}…"))

    # --- 图片归属：题块外的图片引用 => 悬空 ---
    outside_img = 0
    for _, _, seg in unmarked:
        outside_img += len(IMG_REF.findall(seg))
    if outside_img:
        issues.append(("P1", "IMAGE_DANGLING",
                       f"{outside_img} 处图片引用在题块外（无归属）"))
    # 题块内图片缺失但文本提到"如图"——记录为提示
    fig_no_img = 0
    for n, b in q_blocks:
        if re.search(r"如图|下图|右图|左图|图\s*\d|看图", b) and not IMG_REF.search(b):
            fig_no_img += 1
    if fig_no_img:
        issues.append(("P2", "FIG_REF_NO_IMAGE",
                       f"{fig_no_img} 个题块提到'如图'但块内无图片引用"))

    # --- 表格保留：含表格行的区段统计 ---
    tbl_blocks = sum(1 for _, b in q_blocks if any(TABLE_ROW.match(l) for l in b.splitlines()))
    tbl_unmarked = sum(1 for _, _, s in unmarked if any(TABLE_ROW.match(l) for l in s.splitlines()))
    info["table_blocks"] = tbl_blocks
    if tbl_unmarked:
        issues.append(("P2", "TABLE_OUTSIDE",
                       f"{tbl_unmarked} 处表格行在题块外"))

    # --- 卷面指令被包进题块（R9：应剔除） ---
    boiler = sum(1 for _, b in q_blocks if BOILERPLATE.search(b))
    if boiler:
        issues.append(("P2", "BOILERPLATE_INCLUDED",
                       f"{boiler} 个题块包含卷面指令（本大题共X小题/答题卡提示等）"))

    # --- 答案块完整性粗检：答案块内是否有实质内容 ---
    empty_a = [n for n, b in a_blocks if len(b.strip()) < 3]
    if empty_a:
        issues.append(("P0", "ANSWER_EMPTY", f"空答案块: {empty_a[:10]}"))

    # --- 详解（v6 全无，仅记录） ---
    # --- 题块含 OCR 页分隔符（---），说明跨页拼接，记录 ---
    # 评级
    sev = {c: s for s, c, _ in issues}
    if any(s == "P0" for s, _, _ in issues):
        verdict = "不合格"
    elif any(s == "P1" for s, _, _ in issues):
        verdict = "需返修"
    elif issues:
        verdict = "基本合格(有提示)"
    else:
        verdict = "合格"
    return {"file": str(path), "verdict": verdict, "info": info,
            "issues": [{"severity": s, "code": c, "desc": d} for s, c, d in issues]}


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        # 全量模式：扫描 auto-annotated-v6 全部 md
        base = ROOT / "Ocr-markdown/auto-annotated-v6"
        files = sorted(p for p in base.rglob("*.md")
                       if not p.name.startswith("review_"))
        out_name = "prereview_report_full"
    else:
        sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
        files = [Path(s["file"]) for s in sample["sample"]]
        out_name = "prereview_report"
    if len(sys.argv) > 2 and sys.argv[-2] == "--limit":
        files = files[: int(sys.argv[-1])]
    results = []
    for f in files:
        try:
            results.append(analyze(f))
        except Exception as e:  # 单文件失败不阻断
            results.append({"file": str(f), "verdict": "脚本异常",
                            "info": {}, "issues": [{"severity": "P0", "code": "SCRIPT_ERROR", "desc": str(e)}]})
    out = ROOT / "reports" / f"{out_name}.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")

    # 汇总
    from collections import Counter
    vc = Counter(r["verdict"] for r in results)
    ic = Counter(i["code"] for r in results for i in r["issues"])
    print("=== 预审汇总 ===")
    print("文件数:", len(results))
    for k, v in vc.most_common():
        print(f"  {k}: {v}")
    print("问题类型分布:")
    for k, v in ic.most_common():
        print(f"  {k}: {v} 文件")
    print("详细报告:", out)

    # ---- Markdown 报告 ----
    CODE_DESC = {
        "MARKER_MALFORMED": "META 标记嵌套/未闭合",
        "QUESTION_LABEL_DUP": "题块标记号重复",
        "ANSWER_LABEL_DUP": "答案标记号重复（同一题号两个答案块）",
        "Q_BLOCK_MERGED_INDEPENDENT": "多道独立题被合并进一个题块（无共享材料，边界错误）",
        "QNUM_GAP": "题号真实缺口（题目丢失）",
        "ANSWER_MISSING": "题无对应答案（子题粒度）",
        "ANSWER_ORPHAN": "答案标记指向不存在的题块",
        "ANSWER_ZONE_UNANNOTATED": "整段答案区未打标记（裸文本）",
        "ANSWER_IN_TABLE": "答案仅以答案表格形式存在（重切时需展开为逐题答案）",
        "ANSWER_IN_RANGE": "答案仅以区间连写形式存在（如 1-5 ACDBA，重切时需展开）",
        "ANSWER_EMPTY": "空答案块",
        "MATERIAL_OUTSIDE": "共享材料在题块外（综合题被切散）",
        "IMAGE_DANGLING": "图片引用无归属（在题块外）",
        "FIG_REF_NO_IMAGE": "题干提到'如图'但块内无图片引用",
        "TABLE_OUTSIDE": "表格行在题块外（可能丢失）",
        "BOILERPLATE_INCLUDED": "题块含卷面指令（本大题共X小题/答题卡提示，应剔除）",
        "SCRIPT_ERROR": "脚本异常",
    }
    order = {"不合格": 0, "需返修": 1, "基本合格(有提示)": 2, "合格": 3, "脚本异常": 4}
    md = ["# v6 样本人工审核预审报告（机器校验）",
          "",
          f"> 生成：prereview_check.py；样本：review_checklist_2026-09-09.md（94 份）",
          f"> 判定依据：确认的批注规则（完整题=题干+选项+图表+答案；综合题整合；子题齐全；"
          f"表格/图片完整；卷面指令不入库）+ V3 契约（composite 原子性、role 闭合）",
          "",
          "## 汇总",
          "",
          "| 判定 | 数量 |", "|---|---|"]
    for k, v in vc.most_common():
        md.append(f"| {k} | {v} |")
    md += ["", "| 问题类型 | 文件数 | 说明 |", "|---|---|---|"]
    for k, v in ic.most_common():
        md.append(f"| {k} | {v} | {CODE_DESC.get(k, '')} |")
    md += ["", "## 逐份判定", ""]
    for v in ("不合格", "需返修", "基本合格(有提示)", "合格", "脚本异常"):
        group = [r for r in results if r["verdict"] == v]
        if not group:
            continue
        md.append(f"### {v}（{len(group)} 份）")
        md.append("")
        for r in group:
            name = Path(r["file"]).name
            inf = r["info"]
            head = (f"**{name}** — 题块 {inf.get('questions','?')} / 答案块 "
                    f"{inf.get('answers','?')} / 综合题块 {inf.get('composite_blocks','?')}")
            md.append(head)
            for i in r["issues"]:
                md.append(f"- `{i['severity']}` {i['code']}: {i['desc']}")
            md.append("")
    md_path = ROOT / "reports" / f"{out_name}.md"
    md_path.write_text("\n".join(md), encoding="utf-8")
    print("Markdown 报告:", md_path)


if __name__ == "__main__":
    main()

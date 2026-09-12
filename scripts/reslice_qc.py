"""重切产出回归校验：检查 resliced-pilot 的切片 md + manifest。

对每份产出检查：
  C1 每个单元 题干区/答案区 标记配对完整
  C2 manifest 题号覆盖 = 源文件题号集合（无遗漏/无多余）
  C3 每单元答案区非空（答案必有）
  C4 综合题必含材料文本
  C5 源文件的图片引用全部被带入切片（无丢失）
  C6 源文件的表格行全部被带入切片
  C7 卷面指令不出现（本大题共X小题/答题卡提示）
  C13 题号身份唯一性:身份键=(section,题号),同分节重复归属必报(大题内编号冲突)；
      不同分节同号合法(选考模块/教师用书汇编的真实编号形态)。无 section 字段时按全卷题号判定。
输出 reslice_pilot_qc.json + 汇总
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prereview_check import normalize_qnum, parse_answer_tables, parse_range_answers  # noqa: E402

ROOT = Path(r"D:\Project\Papers")
OUT_ROOT = ROOT / "Ocr-markdown/resliced-pilot"
RESULT = ROOT / "data/reslice_pilot_result.json"

IMG = re.compile(r"<img\s|!\[[^\]]*\]\(")
TBL_ROW = re.compile(r"^\s*\|.*\|\s*$|<table|</tr>")
BOILER = re.compile(r"本大题共|请将答案.{0,10}答题卡|在答题卡上|答题卡指定区域|考试时间\s*\d|注意事项")
# 与卷面指令同处一行的作答必需要求：整行应保留，不算卷面指令混入
ESSENTIAL = re.compile(r"任选|不少于|不超过|按要求作答|保留.{0,4}小数|写一篇|自拟")
# C9 试卷级结构行（入库的是 question 不是 paper）
PAPER_LINE = re.compile(
    r"^#{1,4}\s*\d{4}\s*北京"
    r"|^#{1,4}\s*[一二三四五六七八九十]+\s*[、．.]\s*"
    r"(单选|选择|多选|填空|非选择|简答|实验|计算|作文|书面表达|阅读|完形|听力|解答|判断)"
    r"|^#{1,4}\s*参考答案|^#{1,4}\s*答案与解析|^#{1,4}\s*评分标准"
    r"|共\s*\d+\s*(小题|题).{0,12}(共\s*\d+\s*分|每题|每小题)"
    r"|^班级[：:]|^\s*姓名[：:]|^\s*学号[：:]"
    r"|考试时间\s*\d|满分\s*\d+|^\s*注意事项")


def src_of(md_path: Path):
    man_path = md_path.with_suffix(".manifest.json")
    man = json.loads(man_path.read_text(encoding="utf-8"))
    src = Path(man["source_file"])
    return src, man


def check(md_path: Path):
    issues = []
    text = md_path.read_text(encoding="utf-8", errors="replace")
    src, man = src_of(md_path)
    src_text = re.sub(r"<!--\s*META:[^>]*-->\n?", "", src.read_text(encoding="utf-8", errors="replace"))

    # C1 标记配对
    for tag in ("题干区开始", "题干区结束", "答案区开始", "答案区结束"):
        c = text.count(f"“{tag}”")
        if c == 0:
            issues.append(f"C1 无 {tag} 标记")
    if text.count("“题干区开始”") != text.count("“题干区结束”"):
        issues.append("C1 题干区标记不配对")
    if text.count("“答案区开始”") != text.count("“答案区结束”"):
        issues.append("C1 答案区标记不配对")

    # C2 题号覆盖：manifest 题号 vs 源文件题号
    src_nums = set()
    for line in src_text.splitlines():
        hit = normalize_qnum(line)
        if hit and 1 <= hit[0] <= 200:
            src_nums.add(hit[0])
    man_nums = set()
    for u in man["units"]:
        man_nums.update(u.get("question_numbers") or [])
    # 源题号集合含噪音（正文中的年份等不含点号，一般安全）；以 manifest 为准做差集提示
    missing = sorted(n for n in src_nums - man_nums if n > 0)
    # 只报告连续段内缺口（排除 OCR 噪音大数字）
    if missing and max(man_nums or [0]) <= max(missing or [0]):
        missing = [n for n in missing if n <= (max(man_nums) if man_nums else 0)]
    if missing:
        issues.append(f"C2 源有而 manifest 无的题号: {missing[:20]}")

    # C3 每单元答案区非空
    blocks = re.split(r"“题干区开始”", text)[1:]
    for i, b in enumerate(blocks):
        if "“答案区开始”" not in b:
            issues.append(f"C3 第{i+1}单元无答案区")
            continue
        ans = b.split("“答案区开始”")[1].split("“答案区结束”")[0].strip()
        if len(ans) < 2:
            issues.append(f"C3 第{i+1}单元答案区为空")

    # C4 综合题材料
    for u in man["units"]:
        if u.get("unit_type") == "composite_question":
            if not u.get("material_lines") and not u.get("questions_lines"):
                issues.append(f"C4 {u.get('unit_id')} 综合题缺 material_lines/questions_lines")
            # C12 嵌套不变量：material ⊆ questions（B1 审查新增）。
            # 分离式结构（material 与 questions 不相交，如听力原文在卷末答案区）合法，仅相交时强制嵌套。
            mat, q = u.get("material_lines"), u.get("questions_lines")
            if isinstance(mat, list) and isinstance(q, list) and len(mat) == 2 and len(q) == 2:
                overlap = not (mat[1] < q[0] or q[1] < mat[0])
                if overlap and not (q[0] <= mat[0] and mat[1] <= q[1]):
                    issues.append(f"C12 {u.get('unit_id')} material 与 questions 相交但未嵌套: mat={mat} q={q}")

    # 单元区间覆盖集合（锚点批注模式下，图片/表格只需被区间覆盖，无需整段回引）
    covered = set()
    for u in man["units"]:
        rgs = [u.get("material_lines"), u.get("questions_lines"), u.get("stem_lines"),
               u.get("options_lines"), u.get("answer_lines"),
               u.get("explanation_lines"), u.get("extra_lines")]
        for s in u.get("sub_questions") or []:
            rgs += [s.get("stem_lines"), s.get("options_lines")]
        for rg in rgs:
            if rg and len(rg) == 2:
                covered.update(range(rg[0], rg[1] + 1))

    # C5 图片完整性：每个源图片行必须被某单元区间覆盖
    lost_imgs = []
    for i, ln in enumerate(src_text.splitlines(), 1):
        if IMG.search(ln) and i not in covered:
            m = re.search(r'src="([^"]+)"|!\[[^\]]*\]\(([^)]+)\)', ln)
            lost_imgs.append(f"L{i}:{(m.group(1) or m.group(2))[-40:]}" if m else f"L{i}")
    if lost_imgs:
        issues.append(f"C5 {len(lost_imgs)} 个图片行未被任何单元覆盖: {lost_imgs[:3]}")

    # C6 表格完整性：每个源表格行必须被某单元区间覆盖（卷面须知/答题卡类表格除外）
    lost_tbl = [i for i, ln in enumerate(src_text.splitlines(), 1)
                if TBL_ROW.search(ln) and i not in covered
                and not re.search(r"考生须知|注意事项|答题卡|考场纪律|考[生试]须知", ln)]
    if lost_tbl:
        issues.append(f"C6 {len(lost_tbl)} 个表格行未被任何单元覆盖: {lost_tbl[:10]}")

    # C7 卷面指令（忽略混有必需作答要求的行）
    boiler = []
    for ln in text.splitlines():
        b = BOILER.findall(ln)
        if b and not ESSENTIAL.search(ln):
            boiler.extend(b)
    if boiler:
        issues.append(f"C7 含卷面指令: {list(dict.fromkeys(boiler))[:5]}")

    # C9 试卷结构行不得混入任何单元区间
    src_lines = src_text.splitlines()
    paper_hits = [f"L{i}:{src_lines[i-1].strip()[:40]}" for i in sorted(covered)
                  if i <= len(src_lines) and PAPER_LINE.match(src_lines[i - 1].strip())]
    if paper_hits:
        issues.append(f"C9 {len(paper_hits)} 处试卷结构行混入单元区间: {paper_hits[:3]}")

    # C8 锚点保真：annotated.md 去掉 META 锚点行后必须与源文件逐行一致
    # （批注不动源内容的根本原则）
    ann_path = md_path.with_name(md_path.stem + ".annotated.md")
    if not ann_path.exists():
        issues.append("C8 缺锚点批注版 .annotated.md")
    else:
        ann_lines = [l for l in ann_path.read_text(encoding="utf-8", errors="replace").splitlines()
                     if not re.match(r"^\s*<!--\s*META:", l)]
        src_lines = src_text.splitlines()
        if ann_lines != src_lines:
            diffs = sum(1 for a, b in zip(ann_lines, src_lines) if a != b)
            issues.append(f"C8 锚点版与源文件不一致（{len(ann_lines)} vs {len(src_lines)} 行, 前缀差异 {diffs}）")

    # C10 锚点配对：每种 META 标记 start/end 数量必须一致。
    # （不查严格嵌套：共享答案表使多题 unit 包络在文档层面必然交错——
    #   如45道选择题的包络都延伸到共享答案表行，与后续填空题包络相交，
    #   这是连续区间模型下的文档现实；同点闭合顺序由编译器保证 LIFO。）
    if ann_path.exists():
        from collections import Counter
        ann_text = ann_path.read_text(encoding="utf-8", errors="replace")
        starts = Counter(re.findall(r"META:(\w+):start", ann_text))
        ends = Counter(re.findall(r"META:(\w+):end", ann_text))
        for k in sorted(set(starts) | set(ends)):
            if starts.get(k, 0) != ends.get(k, 0):
                issues.append(f"C10 锚点 {k} 不配对: start×{starts.get(k, 0)} vs end×{ends.get(k, 0)}")

    # C11 详解区不含原题复述(R18 人工抽审发现：教师版详解区自带完整题干+选项复述,
    #   切片展示"题干重复出现在详解区"。确定性清洗见 fix_explanation_prefix.py)
    # 判定:explanation 首行与本 unit stem 首行文本高度相似 = 原题复述
    # (仅"题号开头"会误伤"题号+解析正文"的详解格式,故用文本相似)
    import difflib
    src_lines_all = src_text.splitlines()
    for u in man["units"]:
        e = u.get("explanation_lines")
        st = u.get("stem_lines")
        if not (isinstance(e, list) and len(e) == 2 and 0 < e[0] <= len(src_lines_all)):
            continue
        if not (isinstance(st, list) and len(st) == 2 and 0 < st[0] <= len(src_lines_all)):
            continue
        def _norm(s):
            return re.sub(r"\s+", "", s)
        first_e = src_lines_all[e[0] - 1]
        # 标记开头 = 解析正文(数学解答常首句引用题设,文本与题干相似但不是复述)
        if "【分析】" in first_e or "【解答】" in first_e:
            continue
        ratio = difflib.SequenceMatcher(
            None, _norm(first_e), _norm(src_lines_all[st[0] - 1])).ratio()
        if ratio > 0.85:
            issues.append(f"C11 详解区首行与题干首行相似{ratio:.2f}(原题复述未剥离): {u.get('unit_id')}")
            break  # 每份报一次即可

    # C13 题号身份唯一性(Scoped Question Identity,R30 探针实测 8/50 真实产物
    #   "大题内编号/分卷重编号"被当全卷题号 → 题库入库双重归属;R31 审查升级:
    #   重号并非总是错误——选考模块("任选一个模块作答")与教师用书汇编的分节内
    #   编号本来就会重复。身份键 = (section, 题号):同分节重复必报;不同分节
    #   同号合法。unit 无 section 字段时退化为全卷题号(R30 行为,存量数据口径)。
    from collections import Counter
    ident = Counter()
    for u in man["units"]:
        sec = u.get("section") or ""
        for n in (u.get("question_numbers") or []):
            ident[(sec, n)] += 1
    dups = sorted((s or "∅", n) for (s, n), c in ident.items() if c > 1)
    if dups:
        issues.append(f"C13 题号身份冲突(同分节重复归属): {dups[:10]}")

    return {"file": str(md_path), "units": len(man["units"]),
            "questions": len(man_nums), "issues": issues,
            "verdict": "PASS" if not issues else "FAIL"}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="产出目录（默认 resliced-pilot）")
    ap.add_argument("--result", help="QC 结果 JSON 路径（默认 data/reslice_pilot_qc.json）")
    args = ap.parse_args()
    out_root = Path(args.out) if args.out else OUT_ROOT
    result_path = Path(args.result) if args.result else (ROOT / "data/reslice_pilot_qc.json")
    mds = sorted(p for p in out_root.rglob("*.md")
                 if not (p.name.endswith(".annotated.md") or p.name.endswith(".restored.md")))
    results = [check(p) for p in mds]
    result_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    npass = sum(1 for r in results if r["verdict"] == "PASS")
    print(f"=== 重切回归：{npass}/{len(results)} PASS ===")
    for r in results:
        mark = "PASS" if r["verdict"] == "PASS" else "FAIL"
        print(f"[{mark}] {Path(r['file']).name}  units={r['units']} 题={r['questions']}")
        for i in r["issues"]:
            print(f"    ! {i}")


if __name__ == "__main__":
    main()

r"""LLM 重切流水线（试点版）。

流程：
  源 md（Ocr-markdown\{grade}\{subject}\，非 v6）
  → 行号化（[L0001] 前缀，供 LLM 受控引用，不转录正文）
  → LLM（正式 MIMO V2.6 PRO = mimo-v2.6-pro，见 llm_provider）按确认规则输出 semantic_units（仅行号引用+角色声明）
  → 确定性校验（行区间合法、题号覆盖、答案存在、composite 材料齐全）
  → 双格式产出：
      ① manifest JSON（V3 semantic_units 形态，无正文，供 Resolver/入库）
      ② 切片 md（题干区/答案区/详解区 展示形态，程序从行区间确定性提取正文）

规则（与用户确认）：
  R1 完整题=题干+选项+配图/表格+答案（详解可选）
  R2 共享前置材料=>整合为一道综合题（composite）
  R3 答案区跟随综合题，逐小题答案齐全；评分标准并入答案区
  R4 子题逐题齐全；R5 表格保留；R6 图片保留；R7 作文算完整题
  R9 卷面指令（本大题共X小题/答题卡提示）不入库

用法：
  python reslice_pipeline.py --pilot          # 跑 reslice_pilot_files.json
  python reslice_pipeline.py --file <src.md>  # 单文件
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prereview_check import (parse_answer_tables, parse_range_answers,  # noqa: E402
                             parse_inline_answers, normalize_qnum)
import llm_provider  # noqa: E402

# ROOT 不再硬编码开发机绝对路径(H-01):RESLICE_ROOT 环境变量可覆盖,
# 默认取本仓库根(scripts/ 的上一级)——任何 checkout 在任意机器上都成立。
ROOT = Path(os.environ.get("RESLICE_ROOT") or Path(__file__).resolve().parents[1])
CFG_PATH = llm_provider.legacy_config_path(ROOT)   # legacy fallback; formal uses env vars
OUT_ROOT = ROOT / "Ocr-markdown/resliced-pilot"
SRC_ROOT = ROOT / "Ocr-markdown"

# Formal MIMO V2.6 PRO (verified via /v1/models).
# mimo-x-pro-preview is LEGACY TEST MODEL CONFIG (live API rejects it).
DEFAULT_MODEL = llm_provider.MIMO_V26_PRO_MODEL


def _redact(text: str) -> str:
    """Strip API keys / bearer tokens from any string before logging."""
    text = re.sub(r"Bearer\s+[A-Za-z0-9_\-\.]{8,}", "Bearer [REDACTED]", text)
    text = re.sub(r"sk-[A-Za-z0-9]{8,}", "sk-[REDACTED]", text)
    text = re.sub(r"['\"]api_key['\"]:\s*['\"][^'\"]+['\"]", "'api_key': '[REDACTED]'", text)
    return text


def load_cfg():
    """Resolve LLM config (lazy). Formal path is llm_provider.resolve; fail-closed if missing."""
    return llm_provider.resolve(ROOT)


# Option label detection (source-grounded, no fabrication).
_OPT_LABEL_RE = re.compile(r"(?<![\w])([A-Ha-h])\s*[.．、:)）]")


def _detect_option_labels(lines, start, end):
    """Detect option label markers in source lines [start, end] (1-based).

    Returns list of (label, start_line, end_line) in source order.
    Only labels that actually appear as markers in the source text are returned.
    """
    labels = []
    for line_no in range(start, min(end + 1, len(lines) + 1)):
        text = lines[line_no - 1] if isinstance(lines[line_no - 1], str) else str(lines[line_no - 1])
        for m in _OPT_LABEL_RE.finditer(text):
            lab = m.group(1).upper()
            if lab not in [l for l, _, _ in labels]:
                labels.append((lab, line_no, line_no))
    return labels


def _expand_option_spans(man, lines):
    """Expand options_lines range into per-option label spans.

    Adds `options: [{label, start_line, end_line}]` to units that have
    options_lines but no per-option data. Source-grounded: labels are detected
    from actual markers in the source text, not fabricated.
    """
    notes = []
    for u in man.get("units", []):
        if u.get("options") or not u.get("options_lines"):
            continue
        opts = u.get("options_lines")
        if not isinstance(opts, (list, tuple)) or len(opts) != 2:
            continue
        start, end = int(opts[0]), int(opts[1])
        if start < 1 or end > len(lines) or start > end:
            continue
        spans = _detect_option_labels(lines, start, end)
        if spans:
            u["options"] = [{"label": lab, "start_line": s, "end_line": e}
                            for lab, s, e in spans]
        else:
            notes.append(f"{u.get('unit_id')}: options_lines=[{start},{end}] but no labels detected")
    return notes


def model_tag():
    """Metadata model tag only; real LLM calls use resolve()."""
    return llm_provider.default_model_tag(ROOT)

# （v2.1：call_llm 直接返回 usage，为并发执行消除共享全局状态）


def call_llm(prompt, max_tokens=50000, temperature=0.1, retries=4):
    cfg = load_cfg()   # 惰性:配置缺失在此显式抛 FileNotFoundError(H-01)
    body = json.dumps({
        "model": cfg["model"],
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }).encode("utf-8")
    last_err = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                cfg["base_url"].rstrip("/") + "/chat/completions",
                data=body,
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {cfg['api_key']}"},
            )
            with urllib.request.urlopen(req, timeout=600) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            choice = data["choices"][0]
            content = (choice.get("message") or {}).get("content") or ""
            if choice.get("finish_reason") == "length":
                raise RuntimeError(f"输出被 max_tokens={max_tokens} 截断")
            if not content.strip():
                raise RuntimeError(f"空回复 finish_reason={choice.get('finish_reason')}")
            return content, (data.get("usage") or {})
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (429, 500, 502, 503, 504):
                # 限流/服务端错误:指数退避(30/60/120/240s),不做无谓短重试
                wait = 30 * (2 ** attempt)
                time.sleep(wait)
            elif 400 <= e.code < 500:
                # 4xx (non-429): immediate failure — retrying cannot fix a client error
                raise RuntimeError(_redact(f"LLM 调用失败 (HTTP {e.code}): {e.reason}"))
            else:
                time.sleep(5 * (attempt + 1))
        except Exception as e:
            last_err = e
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(_redact(f"LLM 调用失败: {last_err}"))


def extract_json(text):
    """从 LLM 回复提取 JSON（容忍 ```json 围栏与前后杂文；带常见损坏修复）。"""
    cands = []
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    if m:
        cands.append(m.group(1))
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        cands.append(text[start:end + 1])
    if not cands:
        raise ValueError("回复中未找到 JSON")
    last_err = None
    for c in cands:
        for s in (c,
                  re.sub(r",\s*([}\]])", r"\1", c),          # 去尾逗号
                  re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", c)):  # 去控制字符
            try:
                return json.loads(s)
            except json.JSONDecodeError as e:
                last_err = e
    raise ValueError(f"JSON 解析失败: {last_err}")


def rel_out(f, root):
    """R24-A2:路径归属计算。startswith 判断有前缀混淆陷阱
    （'Ocr-markdown2' 会绕过 'Ocr-markdown' 导致 relative_to 崩整批），必须 try/except。"""
    try:
        return f.relative_to(root)
    except ValueError:
        return Path(f.name)


def number_lines(text):
    lines = text.splitlines()
    numbered = "\n".join(f"[L{i+1:04d}] {l}" for i, l in enumerate(lines))
    return lines, numbered


INTERVAL_ROLES = ("stem_lines", "options_lines", "answer_lines", "explanation_lines",
                  "extra_lines", "material_lines", "questions_lines")

# P2.1-c 答案证据类型词表(prompt v2.4;absent=源卷确无答案,不猜测)
AE_TYPES = ("answer_lines", "inline_in_explanation", "answer_table", "range_string", "absent")

PROMPT_VERSION = "reslice-pilot-v2.7"


def clamp_intervals(man, n_lines):
    """确定性行号兜底（R24-A3/R7）：越界截断到 [1, n_lines]，倒置交换。
    LLM 偶发多报/写反行号 → 锚点错乱（C10 不配对）。返回修复记录列表。"""
    notes = []
    for u in man.get("units", []):
        for role in INTERVAL_ROLES:
            v = u.get(role)
            if isinstance(v, list) and len(v) == 2 and all(isinstance(x, int) for x in v):
                s2 = max(1, min(v[0], n_lines))
                e2 = max(1, min(v[1], n_lines))
                if s2 > e2:
                    s2, e2 = e2, s2
                if [s2, e2] != v:
                    u[role] = [s2, e2]
                    notes.append(f"{u.get('unit_id')}/{role}: 越界/倒置行号 {v} → [{s2},{e2}]")
    return notes


PROMPT_HEAD = r"""你是试题切片专家。这是一份北京高中教师版试卷的 OCR Markdown（每行前有行号 [Lxxxx]）。
你的任务：识别出全部"完整题目单元"，输出 JSON。只引用行号，不要转录任何题目正文。

【根本规则】
1. 入库单元=完整可解的题：题干+选项（选择题）+配图/配表格（如有）+标准答案。详解如有也纳入。
2. 凡若干小题共享同一段前置材料/前提条件（文言文、现代文阅读、英语阅读/完形/语法填空/七选五、
   理化实验题、工艺流程题、材料题等——脱离材料无法作答），必须整合为一个"综合题"单元：
   材料+全部子题+全部子题的答案。
3. 无共享材料的独立题各自成单元。切勿把不相干的独立题合并。
4. 每个子题都必须有答案。答案可能有多种形态：逐题标注、区间连写（如"1-5 ACDBA"）、
   答案表格（数字行/字母行成对）、【答案】标记段——全部识别出来并归属到对应题目。
   独立的【答案】行（如 "2.【答案】D"、"5. 【答案】B"）本身必须落在 answer_lines
   区间内——answer_lines 至少要覆盖【答案】标记行，即使它与【解析】【详解】相邻。
4b. 答案证据：每个题目单元必须输出 "answer_evidence" 对象：
   {"type": "...", "lines": [起始行号, 结束行号] 或 null, "value": "..." 或 null, "shared": true 或 false}
   - type=answer_lines:存在独立答案行/答案区且 answer_lines 已圈中它;evidence lines 填同一区间。
   - type=inline_in_explanation:全卷无独立答案行,答案结论内嵌在【解答】【详解】块中
     （如块内"故选 D。""C符合题意"）：此时 answer_lines 填 null,evidence lines 圈结论所在行。
   - type=answer_table:答案由多题共享的答案表格给出;lines 圈该表所在行。
   - type=range_string:答案由区间连写给出（如"1-5 ACDBA"）;lines 圈该串所在行。
   - type=absent:源卷确无本题答案;lines 和 value 都填 null。
   - value:只允许抄录源文明文写出的答案值（"故选 D"→"D","1-5 ACDBA"第3题→"B"）;
     源文无明文答案值就填 null。绝不推断、绝不补全一个看似合理的答案。
   - shared:证据行区内含有**不属于本单元题号**的答案（整张答案表、多题连写答案串
     如"21\. B 22\. C 23\. A"、多题共用一行）时必须 true;区内只有本单元答案时填 false。
     shared=true 时 value 必须给出本单元各题的明文答案值（逐题定位,如多小题 "21.B 22.C 23.A"）。
4c. 答案边界（硬性,P2.1-e 答案区间污染修复）：
   - answer_lines 只圈本单元实际需要消费的答案证据:绝不圈题干/材料,绝不圈只属于他题的答案行。
   - 紧跟题目的题区内联【答案】块属于答案区:不圈入 stem/questions 区间,由 answer_lines 圈定。
   - 同一题答案在卷中出现两处（题区一份、卷末答案区一份）时,answer_lines 圈其中一处即可
     （优先卷末答案区）,另一处不圈入任何区间。
   - 答案表/连写答案串为多题共享时,answer_lines 允许圈整个共享区,但 answer_evidence 必须
     shared=true 且 value 给本题明文答案值。绝不为了"只圈自己的"把共享答案表切碎。
5. 题干中与解题无关的卷面指令（"本大题共3小题，共12分""请将答案填涂在答题卡上"
   "考试时间""注意事项"）不纳入任何单元的行区间。但解题必需的要求（"任选三小题作答"
   "结果保留两位小数""不少于100词"）属于题干。
6. 作文题（题干要求+范文/参考答案）算一个完整单元。
7. OCR 噪音题号（如 "5.\" 、全角 "１．"、"### 12."）都是题号，按数字识别。
11. 入库的是 question，不是 paper：试卷级结构行绝不纳入任何单元区间——
   试卷标题（"# 2021 北京三十一中高一（下）期中化学"）、大题标题
   （"## 一、 单选题（共45题，每题1分，共45分）"）、"参考答案/答案与解析"标题、
   班级/姓名/学号/日期、考试时间/满分/注意事项。单元区间从题目正文第一行开始。
   （注意："### 12." 这类 OCR 噪音题号行是题目的一部分，与此规则无关。）
8. 表格、图片（<img> 标签）行必须保留在相应单元的行区间内，不得遗漏。
   每一行含 <img> 或表格的行都必须被某个单元的区间覆盖——包括紧跟选项字母（如 "## D" 后）
   的图片、材料题的图片簇、以及答案/详解区里重复出现的图片。绝不允许留下无人认领的图片行。
   特别注意"题前图"版式：PDF 常把题图排在题号行的正上方（图行之后紧邻 "30. 题干…"行），
   该图属于其后的题目——stem_lines 起点必须前移到图行，把它纳入本题区间。
8b. 语义引用规则（P2.2 圈定遗漏修复）：题干、选项或题目内容**明确引用**某幅图/表/装置/
   实验图（“如图”“见图”“如图所示”“由图可知”“下图”“实验装置如图”等）时，该图所在的源行
   **必须包含在本题的行区间内**（stem_lines 起点前移，或排版漂移时放 extra_lines）。
   - 只在引用语义成立时纳入；**绝不因为图片离本题近就纳入**，也不引入“最近题目”这类
     按距离归属的规则。无明确题干引用的邻近图片行不圈入。
   - 图片归属只有两种合法落点：题目区间（stem/questions）或材料区间（material）；
     不要为此建立任何新的图片归属结构或关系字段。
   - **选项配图版式（理化常见，必须遵守）**：每个选项字母常独占一行（A. / B. / C. / D.），
     该选项的图排在字母行之后。此时 options_lines 必须**延伸覆盖到末选项的配图行**——
     选项区的终点是最后一个选项（含其配图）的最后一行，而不是最后一个字母行。
     切勿让配图落在 options_lines 之外变成无人认领的行。
9. 【评分标准】类行并入该题答案区间。
10. 详解区（【分析】【解答】【点评】【详解】等）如有，单独一个行区间。

【输出 JSON 格式（严格遵守，仅输出 JSON）】
{
 "units": [
  {
   "unit_id": "Q1",
   "unit_type": "standalone_question",
   "section": "一、选择题",
   "printed_number": "1",
   "question_numbers": [1],
   "original_question_type": "single_choice|multiple_choice|fill_in|short_answer|essay|cloze|reading|grammar_fill|vocabulary_fill|seven_to_five|reading_expression|true_false",
   "stem_lines": [起始行号, 结束行号],
   "options_lines": [起始行号, 结束行号] 或 null,
   "extra_lines": [起始行号, 结束行号] 或 null,
   "answer_lines": [起始行号, 结束行号] 或 null,
   "answer_evidence": {"type": "answer_lines|inline_in_explanation|answer_table|range_string|absent", "lines": [起始行号, 结束行号] 或 null, "value": "答案值原文" 或 null, "shared": true 或 false},
   "explanation_lines": [起始行号, 结束行号] 或 null
  },
  {
   "unit_id": "U2-5",
   "unit_type": "composite_question",
   "section": "三、阅读理解",
   "printed_number": "2",
   "question_numbers": [2,3,4,5],
   "original_question_type": "reading",
   "material_lines": [起始行号, 结束行号],
   "questions_lines": [起始行号, 结束行号],
   "answer_lines": [起始行号, 结束行号] 或 null,
   "answer_evidence": {"type": "answer_lines|inline_in_explanation|answer_table|range_string|absent", "lines": [起始行号, 结束行号] 或 null, "value": "答案值原文" 或 null, "shared": true 或 false},
   "explanation_lines": [起始行号, 结束行号] 或 null
  }
 ]
}
注意：
- 行号用阿拉伯数字整数，区间必须覆盖该内容实际所在行。
- extra_lines 仅在本题的配图/表格因排版漂移到题干区间之外时使用（如题9的图被排到题11之后）；
  此时 stem_lines 只圈题干自身文字，漂移的图/表行放 extra_lines。绝不允许用 stem_lines
  去吞并中间其他题目的行。正常情况 extra_lines 填 null。
- 综合题（composite_question）**整块就是一道题，不拆子题**：questions_lines 圈整块题目区
  （文章+选项/各小题，从材料首行到末尾配图）；material_lines 圈其中的材料/文章部分，
  **material 嵌套在 questions 内部**（material ⊆ questions）。完形填空里带空格的文章本身
  就是题目，文章到首个选项行之间都算 material；阅读题的 material 是文章，各小题在文章之后
  （仍在 questions 区内）。answer_lines 是这道综合题整体的答案区。
  不要输出 sub_questions 之类逐空/逐小问的细粒度结构。
- 所有题目必须出现且只出现在一个单元里；题号连续覆盖全卷。
- 试卷末尾的标题行、页眉页脚不纳入。
- 综合题的 question_numbers 填这道大题本身的题号（如完形填空是第11题就填 [11]）。
- 【题号身份规则(R33 审查后 v2.3)】question_numbers 是入库题目身份,必须是全卷唯一编号:
  * 试卷各分节依次编号(单选 1-25 后非选择题印刷"1.-9.")时,后续分节必须归一到全卷编号:
    以答案区键位为准——答案区"26.【答案】…"表明非选择题第1题实为全卷第26题,填 [26];
    答案区无明确键位时,按前面分节已出现的最大题号顺延(选择题到25,则非选择题"1."填26)。
  * 选考模块("请在以下三个模块试题中任选一个模块作答")各模块内印刷题号本来相同,
    question_numbers 保留印刷题号,但必须用 section 字段区分模块。
  * 每个单元必须输出 "section" 字段:所属分节标题(如"二、非选择题""《有机化学基础》模块试题"
    "考点2 物质的检验、分离和提纯"),无分节时填 null。
  * 每个单元必须输出 "printed_number" 字段:卷面实际印刷的题号原文(字符串,如"1""26"),
    与 question_numbers 分开记录——印刷题号是源事实,入库题号是归一化结果,二者不同必须
    都能查到(非选择题印刷"1."而入库 26 时,printed_number="1", question_numbers=[26])。
    卷面无印刷题号(如作文)填 null,绝不允许把入库题号直接抄作印刷题号。
- 教师用书/专题汇编中每个例题组各自从 1 编号是真实形态:保留印刷题号,用 section 字段标识例题组。
- 卷末作文等若没有印刷题号，按全卷顺序顺延编号（如前一题是 43 就填 44）。
- 只输出一个合法 JSON 对象本身：不要任何解释文字，字符串内不要未转义的换行或引号，
  不要尾逗号，不要注释。
"""


def build_prompt(doc_meta, numbered):
    meta = f"文档元数据：{doc_meta}\n" if doc_meta else ""
    return PROMPT_HEAD + "\n" + meta + "\n【试卷内容】\n" + numbered + "\n\n请输出 JSON。"


PAPER_LINE = re.compile(
    r"^#{1,4}\s*\d{4}\s*北京"                      # 试卷标题
    r"|^#{1,4}\s*[一二三四五六七八九十]+\s*[、．.]\s*"
    r"(单选|选择|多选|填空|非选择|简答|实验|计算|作文|书面表达|阅读|完形|听力|解答|判断)"  # 大题标题
    r"|^#{1,4}\s*参考答案|^#{1,4}\s*答案与解析|^#{1,4}\s*评分标准"
    r"|共\s*\d+\s*(小题|题).{0,12}(共\s*\d+\s*分|每题|每小题)"
    r"|^班级[：:]|^\s*姓名[：:]|^\s*学号[：:]"
    r"|考试时间\s*\d|满分\s*\d+|^\s*注意事项")


_ANS_NUM_AFTER = re.compile(r"【答案】\s*(\d{1,3})\s*[\.．、]")
_ANS_NUM_BEFORE = re.compile(r"(\d{1,3})\s*[\.．、]\s*【答案】")


def answer_line_nums(text):
    """从【答案】行解析题号(前缀"2.【答案】D"/后缀"【答案】60. …"两种版式)。
    用于 P2.1-e 重复答案块判定:同题答案已在他处圈定时,未覆盖的第二处降 warning。"""
    nums = {int(m.group(1)) for m in _ANS_NUM_AFTER.finditer(text)}
    nums |= {int(m.group(1)) for m in _ANS_NUM_BEFORE.finditer(text)}
    return nums


def validate_manifest(man, n_lines, lines=None):
    """确定性校验：行号合法、题号覆盖、答案存在。返回 (问题列表, 汇总)。

    分节重号（如单选 1-45 与填空 1-11 各自从 1 编号）是真实试卷形态，
    R31 起以 (section, 题号) 为身份键区分:同分节重复=身份冲突(issue);
    不同分节同号合法(warning)。无 section 字段的存量数据按全卷题号判定。
    """
    issues = []
    warns = []
    covered = {}   # (section, 题号) -> unit_id（检测身份冲突,见 R31/BUG-22）

    def chk_range(rg, what, uid):
        if rg is None:
            return
        if (not isinstance(rg, list) or len(rg) != 2
                or not all(isinstance(x, int) for x in rg)
                or rg[0] < 1 or rg[1] > n_lines or rg[0] > rg[1]):
            issues.append(f"{uid}: {what} 行区间非法 {rg}")

    units = man.get("units", [])
    if not units:
        issues.append("units 为空")
    for u in units:
        uid = u.get("unit_id", "?")
        nums = u.get("question_numbers") or []
        if not nums:
            issues.append(f"{uid}: 缺 question_numbers")
        for n in nums:
            # R31:身份键=(section,题号)。同分节重复=身份冲突(升 issue);
            #   不同分节同号(选考模块/汇编)合法,仅记 info 级 warning。
            key = (u.get("section") or "", n)
            if key in covered:
                issues.append(f"{uid}: 题号 {n} 与 {covered[key]} 同分节重复归属(身份冲突)")
            else:
                covered[key] = uid
                flat = [k for k in covered if isinstance(k, tuple) and k[1] == n and k[0] != key[0]]
                if flat:
                    warns.append(f"{uid}: 题号 {n} 与其他分节({flat[0][0] or '无分节'})同号(分节编号,合法)")
        if u.get("unit_type") == "composite_question":
            chk_range(u.get("material_lines"), "material", uid)
            chk_range(u.get("questions_lines"), "questions", uid)
            # 综合题整块一道题：material + questions 两个区间
            if u.get("material_lines") is None and u.get("questions_lines") is None:
                issues.append(f"{uid}: 综合题缺 material_lines/questions_lines")
        else:
            chk_range(u.get("stem_lines"), "stem", uid)
            chk_range(u.get("options_lines"), "options", uid)
        chk_range(u.get("answer_lines"), "answer", uid)
        chk_range(u.get("explanation_lines"), "explanation", uid)
        chk_range(u.get("extra_lines"), "extra", uid)
        # P2.1-c 答案证据契约:answer_evidence 可选(v2.3 遗留卷无此字段),
        # 但出现即必须合法;非 absent 证据可替代 answer_lines 的定位作用。
        ae = u.get("answer_evidence")
        ae_locates = False
        if ae is not None:
            if not isinstance(ae, dict):
                issues.append(f"{uid}: answer_evidence 非对象")
            else:
                t = ae.get("type")
                if t not in AE_TYPES:
                    issues.append(f"{uid}: answer_evidence.type 非法 {t!r}")
                elif t == "absent":
                    if ae.get("lines") is not None or ae.get("value") is not None:
                        issues.append(f"{uid}: answer_evidence absent 时 lines/value 必须为 null")
                else:
                    rg = ae.get("lines")
                    if not (isinstance(rg, list) and len(rg) == 2
                            and all(isinstance(x, int) for x in rg)):
                        issues.append(f"{uid}: answer_evidence({t}) 缺合法 lines")
                    else:
                        chk_range(rg, "answer_evidence", uid)
                        ae_locates = True
                    v = ae.get("value")
                    if v is not None and not isinstance(v, str):
                        issues.append(f"{uid}: answer_evidence.value 非字符串")
                    sh = ae.get("shared")
                    if sh is not None and not isinstance(sh, bool):
                        issues.append(f"{uid}: answer_evidence.shared 非布尔")
                    elif sh is True and not v:
                        issues.append(f"{uid}: answer_evidence.shared=true 必须给本题明文 value(逐题定位)")
        if u.get("answer_lines") is None and not ae_locates:
            issues.append(f"{uid}: 无 answer_lines（题号 {nums}）")
        # R11 入库的是 question 不是 paper：试卷级结构行不得进入任何单元区间
        if lines is not None:
            rgs = [u.get("material_lines"), u.get("questions_lines"), u.get("stem_lines"),
                   u.get("options_lines"), u.get("answer_lines"),
                   u.get("explanation_lines"), u.get("extra_lines")]
            for rg in rgs:
                if not rg:
                    continue
                for i in range(max(1, rg[0]), min(rg[1], len(lines)) + 1):
                    if PAPER_LINE.match(lines[i - 1].strip()):
                        issues.append(f"{uid}: L{i} 试卷结构行混入单元区间: {lines[i-1].strip()[:40]}")
    # P2.1-e 答案区间污染族(Answer Span Contamination)最小确定性校验
    # (71/71 人工标注实测形态:整表污染/相邻串题/题干混入,见 charter §10):
    # C-A4 【答案】行覆盖检测(重复答案块放宽) + C-A1 题干区混入答案 + C-A2 答案区混入题干
    # + C-A3 共享答案区必须显式(shared=true + 逐题 value)。
    if lines is not None and units:
        def _rows(rg):
            if isinstance(rg, list) and len(rg) == 2 and all(isinstance(x, int) for x in rg):
                return range(max(1, rg[0]), min(rg[1], len(lines)) + 1)
            return ()
        covered_rows = set()
        ans_rows = set()      # answer_lines/answer_evidence.lines 圈定行(答案身份)
        ans_nums_cov = set()  # 已覆盖【答案】行上解析出的题号(重复答案块判定)
        for u in units:
            for role in INTERVAL_ROLES:
                covered_rows.update(_rows(u.get(role)))
            ae0 = u.get("answer_evidence") if isinstance(u.get("answer_evidence"), dict) else {}
            for rg0 in (u.get("answer_lines"), ae0.get("lines")):
                ans_rows.update(_rows(rg0))
        for i in sorted(ans_rows):
            if "【答案】" in lines[i - 1]:
                ans_nums_cov |= answer_line_nums(lines[i - 1])
        for i, l in enumerate(lines, 1):
            if "【答案】" in l and i not in covered_rows:
                # C-A4 重复答案块放宽:同题答案已在他处圈定 → warning,
                # 不为消灭 issue 逼 LLM 把共享/重复答案切碎(用户裁定 §10.2)。
                if answer_line_nums(l) & ans_nums_cov:
                    warns.append(f"L{i}: 【答案】行未覆盖,同题答案已在他处圈定(重复答案块): {l.strip()[:40]}")
                else:
                    issues.append(f"L{i}: 【答案】行未被任何单元区间覆盖: {l.strip()[:40]}")
        for u in units:
            uid = u.get("unit_id", "?")
            own = {n for n in (u.get("question_numbers") or [])}
            # C-A1 题干区混入未圈定的【答案】行(实测:交大英语题区内联答案块并入 questions_lines)。
            # 题干+答案同行的行内版式因 answer_lines 同时圈定该行,不误伤。
            for role in ("stem_lines", "material_lines", "questions_lines"):
                hit = [i for i in _rows(u.get(role))
                       if "【答案】" in lines[i - 1] and i not in ans_rows]
                if hit:
                    issues.append(f"{uid}: 题干区 L{hit[0]} 混入未圈定的【答案】行: {lines[hit[0]-1].strip()[:40]}")
            # C-A2 答案区混入本题题干标题行(实测:丰台历史 U28 answer_lines 吞入答案区复述的题干)
            for i in _rows(u.get("answer_lines")):
                m = re.match(r"\s*#{1,6}\s*(\d{1,3})\s*[\.．、\s]", lines[i - 1])
                if m and int(m.group(1)) in own and "【答案】" not in lines[i - 1]:
                    issues.append(f"{uid}: 答案区 L{i} 含本题题干标题行: {lines[i-1].strip()[:40]}")
            # C-A3 共享答案区必须显式(实测:101地理整表/综合英语连写串/通州地理连写串):
            # 答案行区内解析出他题号 → 必须 shared=true 且逐题 value,否则 V3 无法定位本题答案。
            ae = u.get("answer_evidence") if isinstance(u.get("answer_evidence"), dict) else {}
            rg = u.get("answer_lines") or ae.get("lines")
            rows = list(_rows(rg))
            if rows:
                txt = "\n".join(lines[i - 1] for i in rows)
                loc = (set(parse_answer_tables(txt)) | set(parse_range_answers(txt))
                       | set(parse_inline_answers(txt)))
                foreign = loc - own
                if foreign:
                    if ae.get("shared") is not True:
                        issues.append(f"{uid}: 答案区含他题答案(题号{sorted(foreign)})但未标 answer_evidence.shared")
                    elif not ae.get("value"):
                        issues.append(f"{uid}: shared 答案区必须给本题明文 value(逐题定位)")
    return issues, {"units": len(units), "covered_questions": len({n for _, n in covered}),
                    "covered_sorted": sorted({n for _, n in covered}), "warnings": warns}


def contamination_report(man, lines):
    """P2.1-e 答案区间污染度量(charter §10.2:只看 contamination 升降,不发明新指标)。

    口径 = validate_manifest 污染族 issue 按形态计数(71/71 人工标注实测三形态):
      stem_has_answer_line       题干区混入未圈定【答案】行(交大英语题区内联答案)
      answer_has_stem_heading    答案区含本题题干标题行(丰台历史答案区复述题干)
      shared_unmarked            共享答案区未标 shared(101地理整表/连写串)
      shared_missing_value       shared 缺逐题明文 value
    """
    issues, _ = validate_manifest(man, len(lines), lines)
    marks = {"stem_has_answer_line": "混入未圈定的【答案】行",
             "answer_has_stem_heading": "含本题题干标题行",
             "shared_unmarked": "但未标 answer_evidence.shared",
             "shared_missing_value": "shared 答案区必须给本题明文 value"}
    counts = {k: 0 for k in marks}
    for it in issues:
        for k, mark in marks.items():
            if mark in it:
                counts[k] += 1
                break
    counts["total"] = sum(counts.values())
    return counts


def span_text(lines, rg):
    if not rg:
        return ""
    return "\n".join(lines[rg[0] - 1: rg[1]])


def compile_slices(lines, man, src_name, src_path, model=DEFAULT_MODEL):
    """确定性编译：行区间 → 切片 md（仅供人工查看的展示视图）。

    原则：标注本身绝不改写/生成题目内容。切片里出现的一切正文都来自源行区间
    的原样回引；程序生成的只有两类：①区标记 ②从共享答案表/区间确定性展开的
    逐题答案值。共享答案表覆盖多个单元时不再整段回引（避免 45 题答案表重复
    45 遍），只给本题答案值 + 源行号引用。
    """
    tbl_ans = parse_answer_tables("\n".join(lines))
    rng_ans = parse_range_answers("\n".join(lines))
    inl_ans = parse_inline_answers("\n".join(lines))
    slices = []
    for u in man["units"]:
        out = []
        if u["unit_type"] == "composite_question":
            # 综合题整块一道题：material 嵌套在 questions 内。
            # 切片渲染时 questions 须去掉与 material 重叠的前段，避免嵌套导致内容重复。
            out.append("“题干区开始”")
            mat = u.get("material_lines")
            que = u.get("questions_lines")
            out.append(span_text(lines, mat))
            if que:
                qs, qe = que
                rem_start = max(qs, (mat[1] + 1) if mat else qs)
                if rem_start <= qe:
                    out.append(span_text(lines, [rem_start, qe]))
            out.append(span_text(lines, u.get("extra_lines")))
            out.append("“题干区结束”")
        else:
            out.append("“题干区开始”")
            out.append(span_text(lines, u.get("stem_lines")))
            out.append(span_text(lines, u.get("options_lines")))
            out.append(span_text(lines, u.get("extra_lines")))
            out.append("“题干区结束”")

        # 答案区：确定性展开的逐题答案值 + 原始答案区间
        # 分节重号卷（选择 1-45 / 填空 1-11）必须先从本单元答案区间内局部取值，
        # 取不到才回退全卷解析，避免跨节串号。
        rg = u.get("answer_lines")
        ans_span = span_text(lines, rg)
        loc_tbl = parse_answer_tables(ans_span) if ans_span else {}
        loc_rng = parse_range_answers(ans_span) if ans_span else {}
        loc_inl = parse_inline_answers(ans_span) if ans_span else {}
        values = {str(n): loc_tbl.get(n) or loc_rng.get(n) or loc_inl.get(n)
                            or tbl_ans.get(n) or rng_ans.get(n) or inl_ans.get(n)
                  for n in u.get("question_numbers", [])}
        values = {k: v for k, v in values.items() if v}
        # 共享判定：答案区间内解析出的题号超出了本单元 → 区间为多单元共享
        # (表格/区间连写/密集连写行 "21\. B 22\. C" 三种实测形态,P2.1-e 扩展)
        loc_nums = set(loc_tbl) | set(loc_rng) | set(loc_inl)
        shared = bool(loc_nums) and not loc_nums <= set(u.get("question_numbers", []))
        out.append("“答案区开始”")
        if values:
            out.append(" ".join(f"{k}.{v}" for k, v in sorted(values.items(), key=lambda x: int(x[0]))))
        if ans_span:
            if shared:
                out.append(f"<!-- 源答案区 L{rg[0]:04d}-L{rg[1]:04d} 为多题共享"
                           f"（答案表/区间连写），已按题号取值，不整段回引 -->")
            else:
                out.append(ans_span)
        # P2.1-c:无独立答案区时,答案证据(type/lines/值原文)如实展示,不生成内容
        ae = u.get("answer_evidence") or {}
        if not ans_span and isinstance(ae, dict) and ae.get("type") not in (None, "absent"):
            ln = ae.get("lines")
            loc = f"L{ln[0]:04d}-L{ln[1]:04d}" if ln else "无行号"
            val = f" 值={ae['value']}" if ae.get("value") else ""
            sh = " shared=true" if ae.get("shared") else ""
            out.append(f"<!-- 答案证据 type={ae.get('type')} {loc}{val}{sh}(源文行区间引用,非生成) -->")
        out.append("“答案区结束”")
        exp = span_text(lines, u.get("explanation_lines"))
        if exp:
            out.append("“详解区开始”")
            out.append(exp)
            out.append("“详解区结束”")
        slices.append("\n".join(out))
    header = (f"<!-- resliced by {model} | source: {src_name} | 展示视图，非批注正文 -->\n")
    return header + "\n\n".join(slices) + "\n", {k: v for k, v in
                                                 {n: (tbl_ans.get(n) or rng_ans.get(n)
                                                      or inl_ans.get(n))
                                                  for n in range(1, 1000)}.items() if v}


def compile_anchor(lines, man, src_name, src_path, model=DEFAULT_MODEL):
    """锚点批注版：源 md 原文逐行不动，只在对应位置插入 META 注释锚点。

    这是批注的本质产物——不改写、不生成任何内容，锚点即切分元数据。
    """
    opens, closes = {}, {}   # 行号 -> [(depth, order, tag)]
    # 嵌套深度：数字小=外层。开锚点升序（外先开），闭锚点降序（内先关）。
    DEPTH = {"unit": 0, "questions": 1, "material": 2,
             "stem": 1, "options": 1, "answer": 1, "explanation": 1, "extra": 1}
    _seq = [0]  # 全局注册序号：同深度同起同止的重叠 span 也按 LIFO（后注册先关）合法嵌套（BUG-10 复审补强）

    def reg(rg, open_tag, close_tag, kind):
        d = DEPTH[kind]
        o = _seq[0]
        _seq[0] += 1
        opens.setdefault(rg[0], []).append((d, o, open_tag))
        closes.setdefault(rg[1], []).append((d, o, close_tag))

    for u in man["units"]:
        uid = u.get("unit_id", "?")
        ut = u.get("unit_type", "?")
        nums = ",".join(str(n) for n in (u.get("question_numbers") or []))
        spans = []
        if ut == "composite_question":
            # 综合题整块一道题：questions 包裹整块（文章+选项），material 嵌套在内指认文章。
            # 完形填空里带空格的文章本身就是题目，故 material ⊂ questions。
            spans = [("material", nums, u.get("material_lines")),
                     ("questions", nums, u.get("questions_lines"))]
        else:
            spans = [("stem", nums, u.get("stem_lines")),
                     ("options", nums, u.get("options_lines"))]
        spans += [("answer", nums, u.get("answer_lines")),
                  ("explanation", nums, u.get("explanation_lines")),
                  ("extra", nums, u.get("extra_lines"))]   # 配图/表格漂移归属
        valid = [(t, n, rg) for t, n, rg in spans if rg]
        if not valid:
            continue
        # unit 包络只圈题干主体（material/stem/options/questions），在题目区就地闭合；
        # 不延伸到答案/详解区（非 question 本身），也不含 extra——
        # extra 是漂移配图的"卫星锚点"，若撑大包络会把相邻题吞进来（如 Q9 图排在 Q11 后，
        # 包络就会套住平级的 Q10/Q11）。extra 靠题号标签单独标注归属即可。
        body = [(t, n, rg) for t, n, rg in valid
                if t not in ("answer", "explanation", "extra")]
        env = body if body else valid
        us = min(rg[0] for _, _, rg in env)
        ue = max(rg[1] for _, _, rg in env)
        reg([us, ue], f"<!-- META:unit:start:{uid} type={ut} q={nums} -->",
            f"<!-- META:unit:end:{uid} -->", "unit")
        for t, n, rg in valid:
            reg(rg, f"<!-- META:{t}:start:{n} -->", f"<!-- META:{t}:end:{n} -->", t)

    # META 版本戳取 manifest 自身的生成版本(重编译旧卷不得洗成当前版本);
    # 新生成卷无 annotation_meta 时落当前 PROMPT_VERSION。
    pv = (man.get("annotation_meta") or {}).get("prompt_version") or PROMPT_VERSION
    out = ["<!-- META:annotation:start -->",
           f"<!-- META:doc:source={src_name}, model={model}, prompt={pv} -->",
           "<!-- META:annotation:end -->"]
    for i, ln in enumerate(lines, 1):
        # 开锚点：unit 先开（外层包络先行）；闭锚点：角色先闭、unit 后关，
        # 开锚点：按深度升序（外层先开）——unit(0) → questions(1) → material(2)
        for d, o, t in sorted(opens.get(i, []), key=lambda x: (x[0], x[1])):
            out.append(t)
        out.append(ln)
        # 闭锚点：按深度降序（内层先关）——material(2) → questions(1) → unit(0)；
        # 同深度按注册序号降序（后注册先关 = LIFO），即使起止行完全相同也合法嵌套（BUG-10）
        for d, o, t in sorted(closes.get(i, []), key=lambda x: (-x[0], -x[1])):
            out.append(t)
    return "\n".join(out) + "\n"


def write_outputs(out_dir, stem, lines, man, issues, summary, src_name, src_path,
                  model=DEFAULT_MODEL):
    """三产出：① manifest JSON（无正文）② 锚点批注版源 md（本质产物）
    ③ 切片 md（人工查看的展示视图）。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    anchor = compile_anchor(lines, man, src_name, src_path, model=model)
    (out_dir / f"{stem}.annotated.md").write_text(anchor, encoding="utf-8")
    md, _ = compile_slices(lines, man, src_name, src_path, model=model)
    (out_dir / f"{stem}.md").write_text(md, encoding="utf-8")
    manifest = {
        "source_file": str(src_path),
        "model": model,
        "annotation_meta": {"prompt_version":
                            (man.get("annotation_meta") or {}).get("prompt_version")
                            or PROMPT_VERSION,
                            "validation_issues": issues,
                            "warnings": summary.get("warnings", [])},
        "units": man["units"],
    }
    # Identity v2: source_content_sha256 = SHA256(source md raw bytes).
    # Contract: PREPROCESSING-V3-CONTRACT-v0.2-DRAFT §0.1 ① — path is locator only.
    if src_path is not None and Path(src_path).is_file():
        manifest["source_content_sha256"] = hashlib.sha256(
            Path(src_path).read_bytes()).hexdigest()
    # QuestionIdentity v2(R34):身份字段随 manifest 落盘,write_outputs
    # 不得自组装丢弃(否则回填/校验建立的身份在重编译时被静默洗掉)。
    for k in ("identity_version", "sections", "source_content_sha256"):
        if k in man:
            manifest[k] = man[k]
    (out_dir / f"{stem}.manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1),
        encoding="utf-8", newline="\n")


def process_file(src_path: Path, log):
    text = src_path.read_text(encoding="utf-8", errors="replace")
    # 去掉 v6 META 标记（如果源是 v6 的话）；正源无标记
    text = re.sub(r"<!--\s*META:[^>]*-->\n?", "", text)
    lines, numbered = number_lines(text)
    doc_meta = ""
    prompt = build_prompt(doc_meta, numbered)
    log(f"[{src_path.name}] {len(lines)} 行, prompt {len(prompt)} 字")

    t0 = time.time()
    # JSON 解析失败 → 重调 LLM（共 2 次尝试）；网络类重试已在 call_llm 内
    man, usage = None, {}
    last_exc = None
    for attempt in range(2):
        reply, u2 = call_llm(prompt)
        # R4 复审：重试时 token 累加计账（覆盖会漏掉失败那次的成本）
        usage["prompt_tokens"] = (usage.get("prompt_tokens") or 0) + (u2.get("prompt_tokens") or 0)
        usage["completion_tokens"] = (usage.get("completion_tokens") or 0) + (u2.get("completion_tokens") or 0)
        try:
            man = extract_json(reply)
            break
        except Exception as e:
            last_exc = e
            dbg = ROOT / "logs/reslice_debug"
            dbg.mkdir(parents=True, exist_ok=True)
            (dbg / f"{src_path.stem}.reply.attempt{attempt+1}.txt").write_text(reply, encoding="utf-8")
            log(f"[{src_path.name}] JSON 提取失败(尝试{attempt+1}): {e}")
    if man is None:
        raise RuntimeError(f"JSON 提取失败(2次均失败): {last_exc}")
    elapsed = time.time() - t0

    # 确定性兜底：无题号单元（多为卷末作文）按全卷顺序顺延补号
    used = {n for u in man.get("units", []) for n in (u.get("question_numbers") or [])}
    nxt = (max(used) + 1) if used else 1
    fix_notes = []
    for u in man.get("units", []):
        if not u.get("question_numbers"):
            u["question_numbers"] = [nxt]
            fix_notes.append(f"{u.get('unit_id')}: 原缺题号，自动补 {nxt}")
            nxt += 1
    # 确定性兜底：行号越界截断 + 倒置归一化（逻辑见 clamp_intervals，可单测）
    fix_notes.extend(clamp_intervals(man, len(lines)))

    # Option span expansion: options_lines range → per-option label spans.
    # Source-grounded detection (no fabrication): labels must appear as markers
    # in the source text within the declared options region.
    fix_notes.extend(_expand_option_spans(man, lines))

    issues, summary = validate_manifest(man, len(lines), lines)
    summary.setdefault("warnings", []).extend(fix_notes)
    # Identity v2: fresh formal pipeline output carries identity_version = 2.
    if "identity_version" not in man:
        man["identity_version"] = 2
    log(f"[{src_path.name}] units={summary['units']} 覆盖题号={summary['covered_questions']} "
        f"校验问题={len(issues)} 警告={len(summary.get('warnings', []))}")
    for i in issues[:10]:
        log(f"    ! {i}")
    for w in summary.get("warnings", [])[:10]:
        log(f"    ~ {w}")

    rel = rel_out(src_path, SRC_ROOT)
    write_outputs(OUT_ROOT / rel.parent, src_path.stem, lines, man,
                  issues, summary, src_path.name, src_path, model=model_tag())
    return {"file": str(src_path), "issues": issues, **summary,
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "elapsed_s": round(elapsed, 1),
            "src_bytes": src_path.stat().st_size, "src_lines": len(lines)}


def derive_run_paths(out=None, batch=False):
    """(log_path, result_path)：账目/日志路径选择（BUG-21 可单测）。

    规则：--out 只隔离产物不隔离账目 = 定时炸弹（R27 冒烟实际覆盖过 pilot 账目，
    靠 git 恢复）。凡 --out 独立输出，log/result 一律跟随输出目录名派生，
    绝不写默认账目；默认账目只在不带 --out 的正式跑（pilot/batch-C）时写。
    """
    if out:
        tag = Path(out).name
        return (ROOT / f"logs/reslice_{tag}_log.txt",
                ROOT / f"data/reslice_{tag}_result.json")
    if batch:
        return (ROOT / "logs/reslice_batch_c_log.txt",
                ROOT / "data/reslice_batch_c_result.json")
    return (ROOT / "logs/reslice_pilot_log.txt",
            ROOT / "data/reslice_pilot_result.json")


def derive_summary_path(out=None):
    """batch 汇总路径(BUG-28 可单测):与 derive_run_paths 同则派生。

    BUG-28(Gate 首攻面发现):batch summary 此前硬编码写
    `data/reslice_batch_c_summary.json`——任何带 --out 的独立批量跑
    (如 PAC 对抗语料)都会静默冲掉生产 batch-C 的证据工件,
    属 C-01 家族(过期/被覆盖的证据工件)。--out 时一律按输出目录名派生。
    """
    if out:
        return ROOT / f"data/reslice_{Path(out).name}_summary.json"
    return ROOT / "data/reslice_batch_c_summary.json"


def recompile_outputs(out_root):
    """从已有 manifest 重编译切片/锚点产出(不调 LLM),返回份数。

    BUG-26(R41 readiness gate 发现):必须把完整 manifest(含
    identity_version/sections)传给 write_outputs——早期实现只传
    {"units": ...},write_outputs 的身份头拷贝(k in man)恒不触发,
    重编译会静默洗掉 v2 身份头,使 QC 降级走 v1 存量语义、违反
    "resolver 只消费 v2" 的契约。单元级身份字段(section_ref 等)虽在
    units 内,单独存在不足以支撑 v2 判定。
    """
    n = 0
    for mf in sorted(out_root.rglob("*.manifest.json")):
        man_full = json.loads(mf.read_text(encoding="utf-8"))
        src = Path(man_full["source_file"])
        text = re.sub(r"<!--\s*META:[^>]*-->\n?", "",
                      src.read_text(encoding="utf-8", errors="replace"))
        lines = text.splitlines()
        meta = man_full.get("annotation_meta", {})
        write_outputs(mf.parent, mf.stem.replace(".manifest", ""), lines,
                      man_full,
                      meta.get("validation_issues", []),
                      {"warnings": meta.get("warnings", [])}, src.name, src,
                      model=man_full.get("model", DEFAULT_MODEL))
        n += 1
        print(f"[recompile] {mf.stem.replace('.manifest', '')}")
    return n


def main():
    global OUT_ROOT
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--file")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--resume", action="store_true",
                    help="跳过 manifest 已存在的输出（断点续跑）")
    ap.add_argument("--recompile", action="store_true",
                    help="从已有 manifest 重编译切片/锚点产出（不调 LLM）")
    ap.add_argument("--batch",
                    help="批量清单 JSON（[{file,tier},...]），走独立输出/日志/结果")
    ap.add_argument("--out",
                    help="输出目录（默认随 pilot/batch；--out 可覆盖）")
    ap.add_argument("--workers", type=int, default=1,
                    help="并发执行的线程数（batch 模式用；默认 1=串行）")
    args = ap.parse_args()

    if args.recompile:
        n = recompile_outputs(OUT_ROOT)
        print(f"===== recompile 完成：{n} 份 =====")
        return

    tier_of = {}
    if args.batch:
        picks = json.loads(Path(args.batch).read_text(encoding="utf-8"))
        files = [Path(p["file"]) for p in picks]
        tier_of = {p["file"]: p.get("tier") for p in picks}
    elif args.pilot:
        picks = json.loads((ROOT / "data/reslice_pilot_files.json").read_text(encoding="utf-8"))
        # 试点优先：先跑失败代价小的
        files = [Path(p["file"]) for p in picks]
        # 重切源应为原始 md（非 v6）：同名文件在 Ocr-markdown\{grade}\{subject}\ 下
        resolved = []
        for f in files:
            rel = f.relative_to(SRC_ROOT / "auto-annotated-v6")
            cand = SRC_ROOT / rel
            resolved.append(cand if cand.exists() else f)
        files = resolved
    else:
        files = [Path(args.file)]
    if args.limit:
        files = files[: args.limit]

    # 输出目录：批量默认独立，不碰 pilot；--out 可覆盖
    if args.out:
        OUT_ROOT = Path(args.out)
    elif args.batch:
        OUT_ROOT = SRC_ROOT / "reslice-batch-C"

    # 账目/日志：--out 一律派生隔离（BUG-21），默认账目只在正式跑时写
    log_path, result_path = derive_run_paths(args.out, bool(args.batch))
    # fresh checkout 没有 logs/、data/（含 CI 环境）：目录兜底，避免 open() 崩
    log_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.parent.mkdir(parents=True, exist_ok=True)

    import threading
    log_lock = threading.Lock()

    def log(msg):
        with log_lock:
            print(msg, flush=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(msg + "\n")

    results = []
    prev = {}
    if args.resume and result_path.exists():
        try:
            for r in json.loads(result_path.read_text(encoding="utf-8")):
                prev[r.get("file", "")] = r
        except Exception:
            pass

    # 断点续跑分流：已有 manifest 的跳过，其余进入 todo
    todo = []
    for i, f in enumerate(files):
        rel = rel_out(f, SRC_ROOT)
        manifest_path = OUT_ROOT / rel.parent / f"{f.stem}.manifest.json"
        if args.resume and manifest_path.exists():
            log(f"===== [{i+1}/{len(files)}] {f.name} —— 已有输出，跳过 =====")
            results.append(prev.get(str(f), {"file": str(f), "skipped": True}))
        else:
            todo.append((i, f))

    def run_one(i, f):
        log(f"===== [{i+1}/{len(files)}] {f.name} =====")
        try:
            return process_file(f, log)
        except Exception as e:
            log(f"[FAIL] {f.name}: {type(e).__name__} {e}")
            return {"file": str(f), "error": str(e)}

    def flush_results():
        # 增量落盘：中断也不丢已完成结果
        result_path.write_text(
            json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8",
            newline="")  # BUG-16:禁 Windows CRLF 翻转

    if args.workers > 1 and len(todo) > 1:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        log(f"===== 并发模式：workers={args.workers}，待处理 {len(todo)} 份 =====")
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(run_one, i, f): f for i, f in todo}
            for fut in as_completed(futs):
                results.append(fut.result())
                flush_results()
    else:
        for i, f in todo:
            results.append(run_one(i, f))
            flush_results()

    flush_results()
    ok = sum(1 for r in results if not r.get("error") and not r.get("issues"))
    log(f"===== 完成：{ok}/{len(results)} 无校验问题 =====")

    if args.batch:
        from collections import Counter
        done = [r for r in results if not r.get("error") and not r.get("skipped")]
        tot_p = sum(r.get("prompt_tokens") or 0 for r in done)
        tot_c = sum(r.get("completion_tokens") or 0 for r in done)
        tot_t = sum(r.get("elapsed_s") or 0 for r in done)
        by_tier = {}
        for r in done:
            tr = tier_of.get(r.get("file"), "?") or "?"
            b = by_tier.setdefault(tr, {"n": 0, "bytes": 0, "llm_s": 0,
                                        "prompt_tokens": 0, "completion_tokens": 0})
            b["n"] += 1
            b["bytes"] += r.get("src_bytes") or 0
            b["llm_s"] += r.get("elapsed_s") or 0
            b["prompt_tokens"] += r.get("prompt_tokens") or 0
            b["completion_tokens"] += r.get("completion_tokens") or 0
        summary = {
            "when": time.strftime("%Y-%m-%d %H:%M"),
            "n_files": len(results),
            "n_ok": ok,
            "n_error": sum(1 for r in results if r.get("error")),
            "n_no_issues": ok,
            "total_src_bytes": sum(r.get("src_bytes") or 0 for r in done),
            "total_prompt_tokens": tot_p,
            "total_completion_tokens": tot_c,
            "total_llm_seconds": round(tot_t),
            "avg_llm_seconds_per_file": round(tot_t / max(len(done), 1), 1),
            "tokens_per_1k_chars": round((tot_p + tot_c) /
                                         max(1, sum(r.get("src_bytes") or 0 for r in done) / 1000 * 1), 2),
            "by_tier": by_tier,
            "files": [{"file": r.get("file"), "tier": tier_of.get(r.get("file")),
                       "elapsed_s": r.get("elapsed_s"),
                       "prompt_tokens": r.get("prompt_tokens"),
                       "completion_tokens": r.get("completion_tokens"),
                       "units": r.get("units"),
                       "n_issues": len(r.get("issues") or [])} for r in results],
        }
        derive_summary_path(args.out).write_text(
            json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8",
            newline="")  # BUG-16:禁 Windows CRLF 翻转
        log(f"[汇总] 成功 {len(done)}/{len(results)} | prompt {tot_p:,} + completion "
            f"{tot_c:,} tokens | LLM 合计 {round(tot_t)}s | 均 {summary['avg_llm_seconds_per_file']}s/份")


if __name__ == "__main__":
    main()

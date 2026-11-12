# -*- coding: utf-8 -*-
"""Answer Source Binding —— R-02 最小闭环：答案值的源文保真绑定。

职责边界（Owner 裁决 QCORE-PREPROCESSING-LLM-FIDELITY-01）：
  LLM 负责识别答案「在哪里、属于谁、是什么形式」；
  本模块负责「源文究竟写了什么」——按封闭规则从 evidence_lines 抽取候选，
  校验模型声明（原 value_text），把 canonical 值写回 value_text，模型原文
  降级为 model_value_text。一切判定为确定性字符串运算，禁止语义等同判断、
  禁止自动纠错、禁止调用任何模型。

V-1 返修（DSH Phase-7 复核）：
  mismatch 恢复仅当抽取候选与【本条目】唯一绑定（标签命中/位置命中/表元格/
  唯一结论）才允许；区域级候选（整行 R-LABELED-LINE / 整块 R-WHOLE / 标签
  未命中回退）一律不恢复 → withheld。恢复后同单元重复值守卫：与任何兄弟槽位
  值重合则本槽位 withheld（区域文本≠槽位答案，不得以"看似权威"的恢复值冒充）。
V-2：source_value_sha256 = 实写 value_text 的哈希（候选哈希另存 candidate_sha256）。
V-3：无 locator 时 value_text=None（与越界同处置），模型文本仅存 model_value_text。

设计文档：Question Core/runs/qcore_preprocessing_llm_fidelity_01/01_EXTRACTION_RULES_TABLE.md
"""
from __future__ import annotations

import hashlib
import re

# ---------------------------------------------------------------------------
# 归一（N1/N2）——格式白名单
# ---------------------------------------------------------------------------

_FW_TABLE = {i: i - 0xFEE0 for i in range(0xFF01, 0xFF5F)}  # 全角 ASCII→半角


def norm_text(s: str) -> str:
    """N1 去全部空白 + N2 全角 ASCII/数字→半角。无任何语义变换。"""
    if not s:
        return ""
    out = []
    for ch in s.translate(_FW_TABLE):
        if not ch.isspace():
            out.append(ch)
    return "".join(out)


def _norm_with_map(s: str):
    """归一串 + 归一下标→原始下标映射（定位源文匹配段用）。"""
    chars = []
    idx = []
    for i, ch in enumerate(s.translate(_FW_TABLE)):
        if not ch.isspace():
            chars.append(ch)
            idx.append(i)
    return "".join(chars), idx


def norm_find_raw_span(hay_raw: str, needle_raw: str):
    """在 hay_raw 中定位 needle_raw 的归一匹配，返回 (start, end) 原始半开区间。"""
    hn, hmap = _norm_with_map(hay_raw)
    nn, _ = _norm_with_map(needle_raw)
    if not nn:
        return None
    pos = hn.find(nn)
    if pos < 0:
        return None
    return hmap[pos], hmap[pos + len(nn) - 1] + 1


# ---------------------------------------------------------------------------
# 标签锚点（R-SHARED-LABEL / R-LABELED-LINE 共用）
# ---------------------------------------------------------------------------

_ANCHOR_RE = re.compile(
    r"（([ⅠⅡⅢⅣⅤ]+|\d{1,3})）"
    r"|\(([ⅠⅡⅢⅣⅤ]+|\d{1,3})\)\s*[\.．、]?"
    r"|(?<![\d\\.．、])(\d{1,3})\s*\\?\s*[\.．、](?!\d)"
)
_MARK_PREFIX_RE = re.compile(
    r"^\s*(?:【答案】|【解答】|【详解】|【答案与解析】)?\s*"
    r"(?:\d{1,3}\s*[\.．、](?!\d))?\s*(?:（[ⅠⅡⅢⅣⅤ\d]+）|\([ⅠⅡⅢⅣⅤ\d]+\))?\s*[\.．、]?\s*"
)
_CONCLUSION_RE = re.compile(
    r"(?:故选|故答案为|答案为|所以选|所以答案为)\s*[：:]?\s*"
    r"([A-HＡ-Ｈ]{1,4}|[^\s，。；、]{1,40})"
)
_RANGE_RE = re.compile(
    r"(\d{1,3})\s*[-–—~]\s*(\d{1,3})\s*[\.．、：:]?\s*([A-HＡ-Ｈ]{2,})"
)
_LABELED_TABLE_RE = re.compile(r"<table[^>]*>(.*?)</table>", re.S | re.I)

# 绑定来源：entry_bound=候选与本条目唯一绑定（可作 mismatch 恢复源）；
#           region_bound=区域级候选（整行/整块/回退，禁止恢复，只能校验）；
#           none=无候选。
ENTRY_BOUND = "entry_bound"
REGION_BOUND = "region_bound"


def _label_norm(x: str) -> str:
    t = norm_text(x)
    return t.strip("()（）[].．、 ")


def anchor_list(block: str):
    out = []
    for m in _ANCHOR_RE.finditer(block):
        lab = next((g for g in m.groups() if g), None)
        if lab:
            out.append((lab, m.start(), m.end()))
    return out


def label_segments(block: str):
    anchors = anchor_list(block)
    segs = []
    for i, (lab, _s, e) in enumerate(anchors):
        nxt = anchors[i + 1][1] if i + 1 < len(anchors) else len(block)
        segs.append((lab, block[e:nxt]))
    return segs


# ---------------------------------------------------------------------------
# 抽取规则（封闭候选集 + 绑定来源）
# ---------------------------------------------------------------------------


def _entry_labels(unit: dict, entry: dict) -> list[str]:
    keys = []
    sl = entry.get("sub_label")
    if sl:
        keys.append(_label_norm(str(sl)))
    for n in unit.get("question_numbers") or []:
        keys.append(_label_norm(str(n)))
    pn = unit.get("printed_number")
    if pn:
        keys.append(_label_norm(str(pn)))
    return [k for k in keys if k]


def extract_candidates(rule_id: str, block: str, unit: dict, entry: dict):
    """返回 (候选集, 绑定来源)。候选集=源文原文字符，不改写；封闭、有序。"""
    if rule_id == "R-NONE":
        return [], "none"
    if rule_id == "R-SHARED-LABEL":
        segs = label_segments(block)
        # 「标签唯一命中本条目」：有 sub_label 时只认 sub_label（禁止 question_numbers
        # 回退误绑同块其他标签段）；无 sub_label（独立题）才用题号/印刷号匹配。
        sl = entry.get("sub_label")
        keys = {_label_norm(str(sl))} if sl else set(_entry_labels(unit, entry))
        picked = [c for lab, c in segs if _label_norm(lab) in keys]
        if picked:
            cands = []
            for c in picked:
                stripped = _MARK_PREFIX_RE.sub("", c).strip()
                for v in (stripped, c.strip()):
                    if v and v not in cands:
                        cands.append(v)
            return cands, ENTRY_BOUND          # 标签唯一命中本条目
        if len(segs) == 1:
            c = segs[0][1]
            stripped = _MARK_PREFIX_RE.sub("", c).strip()
            cands = []
            for v in (stripped, c.strip()):
                if v and v not in cands:
                    cands.append(v)
            return cands, REGION_BOUND          # 回退=区域级，禁止恢复
        return [], "none"
    if rule_id == "R-LABELED-LINE":
        first = block.splitlines()[0] if block else ""
        stripped = _MARK_PREFIX_RE.sub("", first).strip() or first.strip()
        cands = []
        for v in (stripped, block.strip()):
            if v and v not in cands:
                cands.append(v)
        return cands, REGION_BOUND              # 整行/整块=区域级，禁止恢复
    if rule_id == "R-INLINE":
        hits = []
        for ln in block.splitlines():
            for m in _CONCLUSION_RE.finditer(ln):
                v = m.group(1).strip()
                if v and v not in hits:
                    hits.append(v)
        keys = set(_entry_labels(unit, entry))
        if len(hits) > 1 and keys:
            for lab, c in label_segments(block):
                if _label_norm(lab) in keys:
                    sub = []
                    for m in _CONCLUSION_RE.finditer(c):
                        v = m.group(1).strip()
                        if v and v not in sub:
                            sub.append(v)
                    if sub:
                        return sub[:1], ENTRY_BOUND   # 标签段内结论=条目绑定
        if len(hits) == 1:
            return hits[:1], ENTRY_BOUND              # 唯一结论=条目绑定
        if hits:
            return hits[:1], REGION_BOUND             # 多结论无法归属=区域级
        return [], "none"
    if rule_id == "R-RANGE":
        keys = set(_entry_labels(unit, entry))
        for m in _RANGE_RE.finditer(block):
            a, b, letters = int(m.group(1)), int(m.group(2)), m.group(3)
            letters = letters.translate(_FW_TABLE)
            for k in keys:
                if k.isdigit() and a <= int(k) <= b:
                    idx = int(k) - a
                    if 0 <= idx < len(letters):
                        return [letters[idx]], ENTRY_BOUND   # 位置命中=条目绑定
        return [], "none"
    if rule_id == "R-TABLE":
        mapping = _parse_labeled_answer_table(block)
        keys = {k for k in _entry_labels(unit, entry) if k.isdigit()}
        for k in keys:
            if int(k) in mapping:
                return [mapping[int(k)]], ENTRY_BOUND       # 表元格=条目绑定
        return [], "none"
    if rule_id == "R-WHOLE":
        return ([block.strip()] if block.strip() else []), REGION_BOUND  # 整块=区域级
    return [], "none"


def _parse_labeled_answer_table(block: str) -> dict:
    mapping: dict = {}
    labels = {"题号", "答案", "分数", "分值"}
    for tb in _LABELED_TABLE_RE.findall(block):
        rows = []
        for tr in re.findall(r"<tr\b[^>]*>(.*?)</tr>", tb, re.S | re.I):
            cells = [re.sub(r"<[^>]+>", "", c).strip()
                     for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S | re.I)]
            rows.append(cells)
        for i in range(len(rows) - 1):
            a, b = rows[i], rows[i + 1]
            if len(a) != len(b) or len(a) < 3:
                continue
            nums_ok = any(c.isdigit() for c in a if c and c not in labels)
            ans_ok = any(re.fullmatch(r"[A-DＡ-Ｄ]{1,4}", c) for c in b if c and c not in labels)
            if not (nums_ok and ans_ok):
                continue
            for num, ans in zip(a, b):
                num = (num or "").strip().translate(_FW_TABLE)
                ans = (ans or "").strip().translate(_FW_TABLE)
                if num.isdigit() and re.fullmatch(r"[A-D]{1,4}", ans):
                    mapping[int(num)] = ans
    return mapping


def dispatch_rule(unit: dict, entry: dict, block: str) -> str:
    if not (entry.get("value_text") or "").strip() and not entry.get("asset_ref"):
        return "R-NONE"
    if entry.get("asset_ref") and not (entry.get("value_text") or "").strip():
        return "R-NONE"
    ev_type = (unit.get("answer_evidence") or {}).get("type")
    if ev_type == "answer_table":
        return "R-TABLE"
    if ev_type == "range_string":
        return "R-RANGE"
    if ev_type == "inline_in_explanation":
        if _CONCLUSION_RE.search(block):
            return "R-INLINE"
        if len(anchor_list(block)) >= 2:
            return "R-SHARED-LABEL"
        return "R-WHOLE"
    n_anchors = len(anchor_list(block))
    if n_anchors >= 2:
        return "R-SHARED-LABEL"
    if n_anchors == 1 or "【答案】" in block:
        return "R-LABELED-LINE"
    return "R-WHOLE"


# ---------------------------------------------------------------------------
# display_value（D1 转义白名单）
# ---------------------------------------------------------------------------

_D1_SYMBOLS = {
    "rightleftharpoons": "⇌", "longrightarrow": "→", "rightarrow": "→", "to": "→",
    "leftarrow": "←", "leftrightarrow": "↔", "Rightarrow": "⇒", "Leftarrow": "⇐",
    "cdot": "·", "times": "×", "pm": "±", "le": "≤", "ge": "≥", "ne": "≠",
    "circ": "°", "approx": "≈", "infty": "∞", "propto": "∝", "partial": "∂",
    "nabla": "∇", "sum": "∑", "int": "∫", "sqrt": "√", "quad": " ", "qquad": "  ",
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε",
    "zeta": "ζ", "eta": "η", "theta": "θ", "iota": "ι", "kappa": "κ",
    "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ", "pi": "π", "rho": "ρ",
    "sigma": "σ", "tau": "τ", "upsilon": "υ", "phi": "φ", "chi": "χ",
    "psi": "ψ", "omega": "ω", "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ",
    "Lambda": "Λ", "Xi": "Ξ", "Pi": "Π", "Sigma": "Σ", "Phi": "Φ",
    "Psi": "Ψ", "Omega": "Ω", "ell": "ℓ", "hbar": "ℏ",
}
_D1_FONT_CMDS = ("mathrm", "text", "mathbf", "mathit", "mathsf", "mathtt",
                 "textbf", "textit", "textrm", "mbox", "textnormal")
_SUP_MAP = str.maketrans("0123456789+-=()ni", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱ")
_SUB_MAP = str.maketrans("0123456789+-=()aeox", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₒₓ")


def _d1_group(s: str, depth: int = 0) -> str:
    if depth > 6:
        return s
    out = re.sub(r"\$\$?", "", s)
    out = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}",
                 lambda m: _d1_group(m.group(1), depth + 1) + "/"
                 + _d1_group(m.group(2), depth + 1), out)
    for fc in _D1_FONT_CMDS:
        out = re.sub(r"\\" + fc + r"\{([^{}]*)\}",
                     lambda m, _d=depth: _d1_group(m.group(1), _d + 1), out)

    def _script(m, table):
        inner = m.group(1)
        conv = inner.translate(table)
        return conv if conv != inner and re.fullmatch(
            r"[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱ]+", conv) else m.group(0)
    out = re.sub(r"\^\{([^{}]*)\}", lambda m: _script(m, _SUP_MAP), out)
    out = re.sub(r"_\{([^{}]*)\}", lambda m: _script(m, _SUB_MAP), out)
    out = re.sub(r"\\([a-zA-Z]+)", lambda m: _D1_SYMBOLS.get(m.group(1), m.group(0)), out)
    out = out.replace("\\ ", " ").replace("\\,", " ").replace("\\;", " ")
    out = out.replace("\\%", "%").replace("\\&", "&").replace("\\#", "#")
    return out


def unescape_display(s: str) -> str:
    return _d1_group(s).strip()


# ---------------------------------------------------------------------------
# 绑定主逻辑
# ---------------------------------------------------------------------------


def _sha16(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()[:16]


def _slice_block(lines: list, el):
    if not el or el[0] is None:
        return None, ()
    a, b = int(el[0]), int(el[1]) if len(el) > 1 and el[1] is not None else int(el[0])
    if a < 1 or b > len(lines) or b < a:
        return None, (a, b)
    return "\n".join(lines[a - 1:b]), (a, b)


def _item_slice_lines(unit: dict, entry: dict):
    el = entry.get("evidence_lines")
    if el and el[0] is not None:
        return el
    ev = unit.get("answer_evidence") or {}
    el2 = ev.get("lines")
    if el2 and el2[0] is not None:
        return el2
    al = unit.get("answer_lines")
    return al if al and al[0] is not None else None


def _classify_miss(block: str, full_doc: str, model_val: str) -> str:
    """失锚分类（封闭谓词）：子串他处→outside_region；子序列行区内→in_region_edit；
    仅全卷子序列→outside_region；全卷无→absent_from_doc。"""
    nv = norm_text(model_val)
    if norm_find_raw_span(full_doc, model_val) is not None:
        return "outside_region"
    if _is_subseq(nv, norm_text(block)):
        return "in_region_edit"
    if _is_subseq(nv, norm_text(full_doc)):
        return "outside_region"
    return "absent_from_doc"


def _fail_closed(unit, entry, binding, candidates, recoverable, notes):
    """mismatch 失败处置（V-1）：仅 entry_bound 候选可作恢复源；否则 withheld。"""
    if candidates and recoverable:
        entry["value_text"] = candidates[0]
        binding["tier"] = "mismatch_recovered"
        dv = unescape_display(candidates[0])
        if dv != candidates[0]:
            entry["display_value"] = dv
            binding["display_rule"] = "D1-v1"
    else:
        entry["value_text"] = None
        binding["tier"] = "mismatch_withheld"
        binding["mismatch_class"] = binding.get("mismatch_class") or "extraction_failed"
        if entry.get("status") not in ("missing", "disputed"):
            entry["status"] = "missing"
            entry["missing_reason"] = "extraction_gap"
    notes.append(
        f"{unit.get('unit_id')}: value_text 与源文失锚（{binding['mismatch_class']}）→ "
        f"{'恢复条目绑定候选' if binding['tier'] == 'mismatch_recovered' else 'withheld'}，"
        f"模型声明存 model_value_text"
    )
    return notes


def bind_entry(unit: dict, entry: dict, lines: list, full_doc: str) -> list:
    """单条目绑定（就地改写 entry），返回问题/提示列表。"""
    notes = []
    form = entry.get("form") or "verbatim"
    model_val = (entry.get("value_text") or "").strip()
    el = _item_slice_lines(unit, entry)
    block, span = _slice_block(lines, el)

    if entry.get("asset_ref") and not model_val or not model_val:
        entry["value_binding"] = {"rule_id": "R-NONE", "tier": "not_applicable",
                                 "match": "none", "mismatch_class": None,
                                 "slice_lines": list(span) if span else None,
                                 "source_value_sha256": None, "candidate_sha256": None,
                                 "display_rule": None}
        return notes

    # V-3：locator 无效/缺失 → 与越界同处置（value_text=None），模型文本仅存声明
    if block is None:
        mclass = "locator_invalid" if el and el[0] is not None else "no_locator"
        entry["model_value_text"] = model_val
        entry["value_text"] = None
        if entry.get("status") not in ("missing", "disputed"):
            entry["status"] = "missing"
            entry["missing_reason"] = "extraction_gap"
        entry["value_binding"] = {"rule_id": "R-NONE", "tier": "mismatch_withheld",
                                 "match": "none", "mismatch_class": mclass,
                                 "slice_lines": list(span) if span else None,
                                 "source_value_sha256": None, "candidate_sha256": None,
                                 "display_rule": None}
        notes.append(f"{unit.get('unit_id')}: value 无有效 locator（{mclass}）→ "
                     f"fail-closed 置空，声明值存 model_value_text")
        return notes

    rule_id = dispatch_rule(unit, entry, block)
    candidates, bind_source = extract_candidates(rule_id, block, unit, entry)
    entry["model_value_text"] = model_val
    cand_hit = None
    match_kind = "none"
    for c in candidates:
        if model_val == c:
            cand_hit, match_kind = c, "exact"
            break
        if norm_text(model_val) == norm_text(c):
            cand_hit, match_kind = c, "normalized"
            break

    sub_span = norm_find_raw_span(block, model_val)
    doc_span = norm_find_raw_span(full_doc, model_val) if sub_span is None else sub_span

    binding = {"rule_id": rule_id, "tier": None, "match": match_kind,
               "mismatch_class": None, "slice_lines": list(span),
               "bind_source": bind_source,
               "source_value_sha256": None,
               "candidate_sha256": _sha16(candidates[0]) if candidates else None,
               "display_rule": None}
    entry["value_binding"] = binding

    def _set_display(val: str):
        if val:
            dv = unescape_display(val)
            if dv != val:
                entry["display_value"] = dv
                binding["display_rule"] = "D1-v1"

    if cand_hit is not None:
        if form in ("verbatim", "combined"):
            entry["value_text"] = cand_hit
        binding["tier"] = "rule_candidate"
        _set_display(entry.get("value_text") or "")
        return notes

    if sub_span is not None:
        raw_match = block[sub_span[0]:sub_span[1]]
        if form in ("verbatim", "combined"):
            entry["value_text"] = raw_match
        binding["tier"] = "source_substring" if form in ("verbatim", "combined") \
            else "compressed_strong"
        binding["match"] = "normalized" if raw_match != model_val else "exact"
        _set_display(entry.get("value_text") or "")
        return notes

    recoverable = (bind_source == ENTRY_BOUND and form == "verbatim")
    # V-1 收紧（返修）：恢复仅限 verbatim+条目绑定候选。compressed/combined 的值是
    # 「组织形态」（压缩/组合），机械无法从源段重建——失锚一律 withheld（源证据留痕）。

    if form in ("compressed", "descriptive"):
        nb, nv = norm_text(block), norm_text(model_val)
        lcs = _lcs_run(nv, nb)
        weak = bool(nv) and _is_subseq(nv, nb) and lcs >= 0.8
        if weak and form == "compressed":
            binding["tier"] = "compressed_weak"
            binding["lcs_share"] = round(lcs, 3)
            _set_display(entry.get("value_text") or "")
            notes.append(f"{unit.get('unit_id')}: compressed 弱锚定（LCS={lcs:.2f}）")
            return notes
        binding["mismatch_class"] = _classify_miss(block, full_doc, model_val)
        binding["lcs_share"] = round(lcs, 3)
        return _fail_closed(unit, entry, binding, candidates, recoverable, notes)

    binding["mismatch_class"] = _classify_miss(block, full_doc, model_val)
    binding["lcs_share"] = round(_lcs_run(norm_text(model_val), norm_text(block)), 3)
    return _fail_closed(unit, entry, binding, candidates, recoverable, notes)


def _postprocess_unit(unit: dict) -> list:
    """V-2 哈希实写值 + V-1 同单元重复值守卫（快照语义：同值互撞全组 withheld）。"""
    notes = []
    entries = [e for e in (unit.get("answers") or []) if isinstance(e, dict)]
    snap = {id(e): norm_text(e.get("value_text") or "") for e in entries}
    for e in entries:
        b = e.get("value_binding") or {}
        v = e.get("value_text")
        b["source_value_sha256"] = _sha16(v) if v is not None else None
    for e in entries:
        b = e.get("value_binding") or {}
        if b.get("tier") != "mismatch_recovered":
            continue
        v = snap[id(e)]
        if not v:
            continue
        dup = any(o is not e and snap[id(o)] == v for o in entries)
        if dup:
            b["tier"] = "mismatch_withheld"
            b["mismatch_class"] = b.get("mismatch_class") or "extraction_failed"
            b["duplicate_guard"] = True
            e["value_text"] = None
            e.pop("display_value", None)
            if e.get("status") not in ("missing", "disputed"):
                e["status"] = "missing"
                e["missing_reason"] = "extraction_gap"
            b["source_value_sha256"] = None
            notes.append(f"{unit.get('unit_id')}: 恢复值与兄弟槽位重复 → withheld（V-1 重复值守卫）")
    return notes


def _is_subseq(a: str, b: str) -> bool:
    it = iter(b)
    return all(ch in it for ch in a)


def _lcs_run(a: str, b: str) -> float:
    if not a:
        return 0.0
    best = 0
    for p in range(len(a)):
        for q in range(p + 1, len(a) + 1):
            if a[p:q] in b:
                best = max(best, q - p)
            else:
                break
    return best / len(a)


def bind_conflict_versions(unit: dict, lines: list, full_doc: str) -> list:
    """冲突版本只做校验记录不覆盖值（D-2）。"""
    notes = []
    for c in unit.get("answer_conflicts") or []:
        for v in (c.get("versions") or []):
            val = (v.get("value_text") or "").strip()
            if not val:
                continue
            block, span = _slice_block(lines, v.get("evidence_lines"))
            if block is None:
                tier, mclass = "mismatch_withheld", "locator_invalid"
            elif norm_text(val) in norm_text(block):
                tier, mclass = "source_substring", None
            elif norm_find_raw_span(full_doc, val) is not None:
                tier, mclass = "source_substring", "outside_region"
            else:
                tier, mclass = "mismatch_withheld", "absent_from_doc"
            v["value_binding"] = {
                "rule_id": "R-CONFLICT-VERSION", "tier": tier,
                "match": "normalized" if mclass is None else "none",
                "mismatch_class": mclass, "slice_lines": list(span) if span else None,
                "source_value_sha256": _sha16(val), "candidate_sha256": None,
                "display_rule": None, "value_preserved": True,
            }
            if mclass:
                notes.append(f"{unit.get('unit_id')}: conflict version 失锚（{mclass}），"
                             f"按 D-2 保留原值并记录（不覆盖）")
    return notes


def bind_answers(man: dict, lines: list) -> list:
    """主入口：answers[] 源文绑定 + 重复值守卫 + 冲突版本校验记录。"""
    full_doc = "\n".join(lines)
    notes = []
    for unit in man.get("units", []):
        for entry in unit.get("answers") or []:
            if isinstance(entry, dict):
                notes.extend(bind_entry(unit, entry, lines, full_doc))
        notes.extend(_postprocess_unit(unit))
        notes.extend(bind_conflict_versions(unit, lines, full_doc))
    return notes

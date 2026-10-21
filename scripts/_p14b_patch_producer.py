"""Patch reslice_pipeline.py — P1.4-B Rules A/B/C option label parsing."""
from pathlib import Path

p = Path(r"D:\Project\Papers\scripts\reslice_pipeline.py")
s = p.read_text(encoding="utf-8")

old = '''_OPT_LABEL_RE = re.compile(r"(?<![A-Za-z0-9_])([A-Ha-h])\\s*[.．、:，。)）]")

# Choice types that require options evidence (same set as V3 annotation_adapter).
_CHOICE_TYPES = frozenset({"single_choice", "multiple_choice", "true_false"})


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
'''

new = '''_OPT_LABEL_RE = re.compile(r"(?<![A-Za-z0-9_])([A-Ha-h])\\s*[.．、:，。)）]")
# P1.4-B Rule B — digit-glued label (`2D.`). Lookbehind on clean form rejects this
# because `2` is alnum. Scope: options_lines only + sequential gate (see _detect).
_OPT_DIGIT_GLUE_RE = re.compile(r"(?<![A-Za-z0-9_])(\\d)([A-Ha-h])\\s*[.．、:，。)）]")
# P1.4-B Rule C — missing separator at line start (`D 麦哲伦`). Not mid-sentence
# `B 是 1945年…` (that continues with 是/了/在/有 — blocked below). Sequential gate applies.
_OPT_SPACE_SEP_RE = re.compile(r"^(?:[ \\u00a0]*)([A-Ha-h])[ \\u00a0]{1,3}(?=[\\u4e00-\\u9fff])")
# Rule C rejectors: ordinary prose after the letter (NOT option content).
_SPACE_SEP_PROSE = re.compile(r"^[ \\u00a0]*[A-Ha-h][ \\u00a0]+(?:是|有|在|了|和|与|或|被|把|对|从|到|为|要|会|能|可|这|那|其|其中|其中|年|月|日)")

# Choice types that require options evidence (same set as V3 annotation_adapter).
_CHOICE_TYPES = frozenset({"single_choice", "multiple_choice", "true_false"})


def _text_at(lines, line_no):
    raw = lines[line_no - 1]
    return raw if isinstance(raw, str) else str(raw)


def _looks_option_like_content(text: str) -> bool:
    """Rule A trailing-content filter. Reject HTML/stems/markers; accept option bodies."""
    t = text.strip()
    if not t or len(t) < 4:
        return False
    if t.startswith("<") or t.startswith("#") or t.startswith("---"):
        return False
    if re.match(r"^\\d+\\s*[.．、\\\\]", t):
        return False
    if _OPT_LABEL_RE.search(t) or _OPT_DIGIT_GLUE_RE.search(t):
        return False
    return True


def _next_seq_letter(seen: set[str]) -> str | None:
    """Next sequential option letter after the highest seen (A..H)."""
    if not seen:
        return "A"
    ords = sorted(ord(c) for c in seen if "A" <= c <= "H")
    if not ords:
        return "A"
    nxt = ords[-1] + 1
    if nxt > ord("H"):
        return None
    return chr(nxt)


def _detect_option_labels(lines, start, end):
    """Detect option label markers in source lines [start, end] (1-based).

    Returns list of (label, start_line, end_line) in source order.
    Only labels that actually appear as markers in the source text are returned.

    P1.4-B source-local deterministic compatibility (NO answer evidence):
      clean     — existing `_OPT_LABEL_RE` (unchanged semantics)
      Rule B    — digit-glued `2D.` → label D (sequential gate)
      Rule C    — line-start `D 麦哲伦` (sequential gate + prose rejector)
      Rule A    — trailing unlabeled option content → next sequential label
    All damage rules are gated on `options_lines` by the caller range [start, end].
    """
    labels = []  # list of (label, start_line, end_line) in source order
    seen = set()
    last_line = start - 1

    # Pass 1: clean labels (unchanged).
    for line_no in range(start, min(end + 1, len(lines) + 1)):
        text = _text_at(lines, line_no)
        for m in _OPT_LABEL_RE.finditer(text):
            lab = m.group(1).upper()
            if lab not in seen:
                labels.append((lab, line_no, line_no))
                seen.add(lab)
                last_line = max(last_line, line_no)

    # Pass 2: Rule B digit-glue (sequential: letter must be next after highest seen,
    # or fill an exact gap in A..max). Rejects `2\\cos…` (no separator after letter)
    # and stray `2a)` outside sequential context.
    for line_no in range(start, min(end + 1, len(lines) + 1)):
        text = _text_at(lines, line_no)
        for m in _OPT_DIGIT_GLUE_RE.finditer(text):
            lab = m.group(2).upper()
            if lab in seen:
                continue
            nxt = _next_seq_letter(seen)
            if lab != nxt:
                continue
            # require option-like content after the separator (not more math glued)
            after = text[m.end():m.end() + 24]
            if after and after[0] in "0123456789\\\\^_{}":
                continue
            labels.append((lab, line_no, line_no))
            seen.add(lab)
            last_line = max(last_line, line_no)

    # Pass 3: Rule C space-sep (line-start only + prose rejector + sequential).
    for line_no in range(start, min(end + 1, len(lines) + 1)):
        text = _text_at(lines, line_no)
        if _SPACE_SEP_PROSE.search(text):
            continue
        for m in _OPT_SPACE_SEP_RE.finditer(text):
            lab = m.group(1).upper()
            if lab in seen:
                continue
            nxt = _next_seq_letter(seen)
            if lab != nxt:
                continue
            labels.append((lab, line_no, line_no))
            seen.add(lab)
            last_line = max(last_line, line_no)

    # Pass 4: Rule A — trailing unlabeled option content after last label line.
    for line_no in range(max(last_line + 1, start), min(end + 1, len(lines) + 1)):
        text = _text_at(lines, line_no)
        if not _looks_option_like_content(text):
            continue
        # content must not carry a clean/glue label token (those were pass 1-3)
        if _OPT_LABEL_RE.search(text) or _OPT_DIGIT_GLUE_RE.search(text):
            continue
        if _OPT_SPACE_SEP_RE.search(text) and not _SPACE_SEP_PROSE.search(text):
            continue
        lab = _next_seq_letter(seen)
        if lab is None:
            break
        labels.append((lab, line_no, line_no))
        seen.add(lab)
        last_line = line_no

    # stable source order
    labels.sort(key=lambda x: (x[1], x[2], x[0]))
    return labels
'''

if old not in s:
    print("OLD BLOCK NOT FOUND — trying flexible match")
    # show nearby
    idx = s.find("_OPT_LABEL_RE")
    print(repr(s[idx:idx+400]))
else:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8")
    print("patched _detect_option_labels + rules")

# Also patch _expand_option_spans to MERGE missing labels (not skip when options exist)
old2 = '''    notes = []
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
'''
new2 = '''    notes = []
    for u in man.get("units", []):
        if not u.get("options_lines"):
            continue
        opts = u.get("options_lines")
        if not isinstance(opts, (list, tuple)) or len(opts) != 2:
            continue
        start, end = int(opts[0]), int(opts[1])
        if start < 1 or end > len(lines) or start > end:
            continue
        spans = _detect_option_labels(lines, start, end)
        existing = u.get("options") or []
        existing_labs = {o.get("label") for o in existing if isinstance(o, dict)}
        if not existing:
            if spans:
                u["options"] = [{"label": lab, "start_line": s, "end_line": e}
                                for lab, s, e in spans]
            else:
                notes.append(
                    f"{u.get('unit_id')}: options_lines=[{start},{end}] but no labels detected"
                )
            continue
        # P1.4-B: fill MISSING labels on partial option lists (Q23/Q4/Q29).
        # Never drop/reorder Producer-declared labels; never invent content.
        added = []
        for lab, s, e in spans:
            if lab in existing_labs:
                continue
            existing.append({"label": lab, "start_line": s, "end_line": e})
            existing_labs.add(lab)
            added.append(lab)
        if added:
            # keep source order by start_line then label
            existing.sort(key=lambda o: (int(o.get("start_line") or 0), str(o.get("label") or "")))
            u["options"] = existing
            notes.append(
                f"{u.get('unit_id')}: recovered option labels {added} "
                f"from source-local structure within options_lines=[{start},{end}]"
            )
    return notes
'''
if old2 not in s:
    print("OLD2 BLOCK NOT FOUND")
    idx = s.find("def _expand_option_spans")
    print(s[idx:idx+600])
else:
    s = s.replace(old2, new2, 1)
    p.write_text(s, encoding="utf-8")
    print("patched _expand_option_spans merge-missing")

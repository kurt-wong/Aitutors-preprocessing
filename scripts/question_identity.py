"""QuestionIdentity Phase 2 核心模型(R34 实施)。

设计出处:question_identity_design.md v0.2/v0.3(R32 提出,R33 对抗审查修订,
第五轮审查附 4 项实施条件 + P2-01~P2-08 冻结验收)。核心裁决:
- Identity 与 Legitimacy 分离:(section, canonical_number) 只回答"叫什么";
  "为什么合法"由 basis 回答,且 basis 不是信任字段——keep 豁免是**个体豁免**
  (选择题 1 与选考模块 keep 1 天然同号),但每个 keep 都必须携带可回源证据
  (basis_evidence 含 L{行号} 且行号在源文件界内);非 keep 持有者之间必须
  全卷唯一。
- QC 不做语义推理,只验证已建立的语义事实(R33:让 C13 自己猜"分节不同
  应该合法"正是 BUG-23 guard soundness failure 的根因)。
- 三态裁决:FAIL(已证明非法)/ PENDING_REVIEW(证据不足)/ PASS。
  "没有证据证明合法" ≠ "已经证明非法"(第五轮审查 §十四)。
- v1 存量(manifest 无 identity_version)保留 R31 scoped 语义;新产物与
  回填产物一律 v2。

manifest identity v2 schema:
  顶层: "identity_version": 2,
        "sections": [{"id","title","ordinal","start_line","end_line","derived"?}]
  单元: "section"(title,展示元数据) + "section_ref"(-> sections.id)
        "printed_number"(list[str|int]|None,卷面印刷题号,Source Fact)
        "printed_provenance"(source_line|migration_report|unknown)
        "basis"(answer_key|shift|keep|printed_as_is|unverified)
        "basis_evidence"(str)
"""
import re
from collections import Counter

# 分节标题识别复用 R31 迁移脚本的实测规则(三个坑已在那里踩平:
# 字符类 [答案] 误杀、小问式行、OCR 丢 ## 的裸考点标题)
from fix_bug22_renumber import SECTION_RE  # noqa: E402

SUB_Q = re.compile(r"^\s*[（(]\s*\d{1,3}\s*[）)]|^\s*[①②③④⑤⑥⑦⑧⑨⑩]")
LINE_REF = re.compile(r"L(\d+)")
PRINTED_LINE = re.compile(r"^\s*(\d{1,3})\s*[\.、．]")

IDENTITY_VERSION = 2


def _heading_rows(lines):
    """返回 [(line_no, title, occ)]:分节标题行(答案/解析/评分与小问式行排除)。"""
    heads = []
    seen = Counter()
    for i, ln in enumerate(lines, 1):
        s = ln.strip()
        if SECTION_RE.match(s) and not re.search(r"答案|解析|评分", s):
            t = re.sub(r"^#{1,4}\s*", "", s)[:40]
            if SUB_Q.match(t):
                continue
            seen[t] += 1
            heads.append((i, t, seen[t]))
    return heads


def build_section_locators(lines):
    """确定性构建 SectionLocator 列表(设计 §2):(ordinal, span) 唯一定位,
    title 仅展示。文档头部无标题区合成 derived 节 S0;无任何标题则整卷
    合成一节(降级必须显式存在,由调用方产生 review note)。"""
    heads = _heading_rows(lines)
    n = len(lines)
    secs = []
    if not heads:
        secs.append({"id": "S0", "title": None, "ordinal": 0,
                     "start_line": 1, "end_line": max(n, 1), "derived": True})
        return secs
    if heads[0][0] > 1:
        secs.append({"id": "S0", "title": None, "ordinal": 0,
                     "start_line": 1, "end_line": heads[0][0] - 1, "derived": True})
    for idx, (hl, ht, occ) in enumerate(heads):
        end = heads[idx + 1][0] - 1 if idx + 1 < len(heads) else n
        secs.append({"id": f"S{len(secs)}", "title": ht, "ordinal": idx + 1,
                     "start_line": hl, "end_line": end,
                     "occurrence": occ})
    return secs


def unit_start(u):
    for k in ("stem_lines", "material_lines", "questions_lines", "options_lines"):
        rg = u.get(k)
        if isinstance(rg, list) and len(rg) == 2 and isinstance(rg[0], int):
            return rg[0]
    return None


def assign_identity(man, lines):
    """把 manifest 原地升级到 identity v2:构建 sections、按单元位置分配
    section(绝不以 unit_id 为键——R31 教训:汇编 unit_id 大量重复)。

    只负责 Identity,不动 basis/printed(由迁移/回填按证据设置)。
    """
    secs = build_section_locators(lines)
    man["identity_version"] = IDENTITY_VERSION
    man["sections"] = secs
    for u in man.get("units") or []:
        st = unit_start(u)
        hit = None
        if st is not None:
            for s in secs:
                if s["start_line"] <= st <= s["end_line"]:
                    hit = s
                    break
        if hit is None:
            hit = secs[0]
        u["section_ref"] = hit["id"]
        u["section"] = hit["title"]
    return man


def evidence_ok(text, n_lines):
    """keep 豁免证据:非空 + 至少一个 L{行号} 引用 + 行号全部在源文件界内。"""
    if not text or not isinstance(text, str):
        return False
    refs = [int(m) for m in LINE_REF.findall(text)]
    if not refs:
        return False
    return all(1 <= r <= max(n_lines, 1) for r in refs)


def check_identity(man, n_lines):
    """验证已建立的身份语义事实。返回 (fail_issues, review_notes)。

    - 仅对 identity_version >= 2 生效(v1 语义由 QC 旧代码路径保留)。
    - 非 keep 持有者之间 canonical 全卷唯一;keep 个体豁免(证据不足→复核)。
    - 同分节重复永远 FAIL(keep 不能豁免同节)。
    - keep 声明但证据缺失/越界 → PENDING_REVIEW(证据不足,不判非法)。
    - 缺 section → PENDING_REVIEW(identity_scope_missing,不得静默 PASS)。
    """
    if (man.get("identity_version") or 1) < 2:
        return [], []
    fails, reviews = [], []
    units = man.get("units") or []

    # locator 自检:ordinal 唯一、span 合法
    ordinals = [s.get("ordinal") for s in man.get("sections") or []]
    dup_ord = [o for o, c in Counter(ordinals).items() if c > 1]
    if dup_ord:
        fails.append(f"C13 SectionLocator ordinal 重复: {dup_ord[:5]}")
    for s in man.get("sections") or []:
        a, b = s.get("start_line"), s.get("end_line")
        if not (isinstance(a, int) and isinstance(b, int) and 1 <= a <= b <= max(n_lines, 1)):
            fails.append(f"C13 SectionLocator span 非法: {s.get('id')} [{a},{b}]")

    # C14 缺 section 不得静默 PASS
    missing = [u.get("unit_id") for u in units if not u.get("section_ref")]
    if missing:
        reviews.append(f"C14 identity_scope_missing: {len(missing)} 个单元缺 section_ref"
                       f" {missing[:5]}")

    # C13 canonical 全卷唯一 + keep 显式豁免(划分语义):
    #   - 非 keep 持有者之间必须全卷唯一(BUG-22 回归形态:两个非 keep 跨节
    #     重号 → FAIL);
    #   - keep 持有者个体豁免(真实结构:选择题 1-25 与选考模块 keep 1-3
    #     天然同号),但每个 keep 都必须携带可回源证据,否则 PENDING_REVIEW;
    #   - 同分节重复永远 FAIL,任何依据都救不了。
    owners = {}
    for u in units:
        sec = u.get("section_ref") or ""
        for n in u.get("question_numbers") or []:
            owners.setdefault(n, []).append((u, sec))
    for n, own in sorted(owners.items()):
        if len(own) < 2:
            continue
        ids = [u.get("unit_id") for u, _ in own]
        sec_cnt = Counter(sec for _, sec in own)
        if max(sec_cnt.values()) > 1:  # 同分节重复归属
            fails.append(f"C13 同分节重复归属: 题号 {n} → {ids}")
            continue
        non_keep = [u.get("unit_id") for u, _ in own
                    if (u.get("basis") or "") != "keep"]
        if len(non_keep) > 1:
            fails.append(f"C13 canonical身份冲突(跨分节重号含多个非 keep): "
                         f"题号 {n} → {ids}")
            continue
        bad = [u.get("unit_id") for u, _ in own
               if (u.get("basis") or "") == "keep"
               and not evidence_ok(u.get("basis_evidence"), n_lines)]
        if bad:
            reviews.append(f"C13 keep 依据不足(证据缺失或行号越界,需人工复核): "
                           f"题号 {n} → {bad}")
    return fails, reviews

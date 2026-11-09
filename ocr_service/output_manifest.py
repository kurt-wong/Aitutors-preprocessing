# -*- coding: utf-8 -*-
"""
output_manifest.py — runner 输出清单(R-OHM-1,BUG-14-DATA D5-A 跑步机切断)

机制(用户 R65 裁定 D5-A:只修重复处理/重复回流机制,不碰数据归并):
  1. runner 每次成功 OCR 写出后,append_entry 追加一条 JSONL 记录:
       source_rel / source_size / source_sha256 / output_rel / written_at / pages
  2. skip 决策(decide_skip)在期望输出路径落空时查清单:
       同一 source(size + sha256 级一致)已在册 → skip(MANIFEST_DONE)
     —— reclassify 搬移 md 后不再触发同 PDF 重 OCR 回流(跑步机根因)。
     设计裁定:记录输出当前在不在原位**不参与决策**。输出被搬移/丢失后的
     处置权在人,runner 不自动重跑(自动重跑 = auto-fix,且正是回流污染源);
     需要重跑时由操作者删除对应清单记录(显式动作)。

语义边界(用户 R66 裁定,防未来语义漂移):
  本清单是 **processing history / execution ledger** —— 只证明
  "该 source 已成功执行过一次 OCR 并记账";
  它**不是 output availability index** —— 不承诺"该 source 当前拥有有效输出"。
  两者混淆的典型事故:以"恢复丢失的输出"为由给 output-missing 加 fallback
  自动重跑 = 复活跑步机。丢失输出的恢复属于人工授权动作(删清单记录),
  绝不回写为 runner 的自动行为。

fail-closed 铁律(R-OHM-1 登记于 governance/rule_registry.md §7):
  - 清单坏行/缺键/非法类型 → ManifestError 显式中止;禁止静默跳过坏行
    (静默跳过会把"清单前置条件损坏"伪装成"无历史记录",退回重跑=跑步机复活)。
  - append_entry 先校验后写:坏记录绝不落盘。
  - source 无法验证(缺失/跨驱动器)→ 不 skip,显式 reason,不猜。

路径键一律正斜杠归一(F-r64-1 教训:Windows 反斜杠 JSONL 在跨平台读取时失配)。
"""

import hashlib
import json
import os

REQUIRED_KEYS = ("source_rel", "source_size", "source_sha256",
                 "output_rel", "written_at", "pages")

CHUNK = 1 << 20


class ManifestError(RuntimeError):
    """清单损坏/校验失败;调用方必须显式中止,禁止降级继续。"""


def normalize_rel(p):
    return str(p).replace("\\", "/")


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(CHUNK)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def make_entry(*, source_pdf, pdf_root, output_md, output_root, pages,
               written_at, output_json=None, ocr_run_id=None,
               ocr_model=None, ocr_params=None):
    """构造一次成功 OCR 的清单记录(路径相对各自根,正斜杠归一)。

    PREPROCESSING-OCR-JSON-01 / R2:可选 JSON 双输出字段。
    output_json 传入时记录 JSON 路径、SHA-256、完整性检查及 json_status;
    不传时行为与旧版完全一致(历史条目无 JSON 字段亦通过校验)。
    """
    entry = {
        "source_rel": normalize_rel(os.path.relpath(source_pdf, pdf_root)),
        "source_size": os.path.getsize(source_pdf),
        "source_sha256": file_sha256(source_pdf),
        "output_rel": normalize_rel(os.path.relpath(output_md, output_root)),
        "output_md_sha256": file_sha256(output_md),
        "written_at": written_at,
        "pages": pages,
    }
    if output_json is not None:
        entry["output_json_rel"] = normalize_rel(
            os.path.relpath(output_json, output_root))
        if os.path.isfile(output_json):
            entry["output_json_sha256"] = file_sha256(output_json)
        # G1:读 PDF 实际页数,与 JSON 页数核对(非自证)
        pdf_pc = get_pdf_page_count(source_pdf)
        entry.update(check_json_integrity(output_json, pages, pdf_page_count=pdf_pc))
    else:
        entry["json_status"] = "absent"
    if ocr_run_id is not None:
        entry["ocr_run_id"] = ocr_run_id
    if ocr_model is not None:
        entry["ocr_model"] = ocr_model
    if ocr_params is not None:
        entry["ocr_params"] = ocr_params
    validate_entry(entry)
    return entry


def check_json_integrity(json_path, expected_pages, pdf_page_count=None):
    """PREPROCESSING-OCR-JSON-01-R2 F2/G1:JSON 完整性检查。

    逐行解析 JSONL,统计 layoutParsingResults 页面数(非行数),
    与 PDF 实际页数(pdf_page_count)交叉核对。
    pdf_page_count 为 None 或读取失败 → json_page_check = not_verifiable。
    不修改 JSON 内容。
    返回 json_status / json_record_count / json_parse_ok /
    json_page_count / json_page_check / pdf_page_count 字典。
    """
    result = {
        "json_status": "absent",
        "json_record_count": 0,
        "json_parse_ok": False,
        "json_page_count": None,
        "json_page_check": "unknown",
        "pdf_page_count": pdf_page_count,
    }
    if not os.path.isfile(json_path):
        return result
    result["json_status"] = "invalid"
    parsed = 0
    page_total = 0
    parse_ok = True
    try:
        with open(json_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    parsed += 1
                    lpr = (obj.get("result") or {}).get("layoutParsingResults") or []
                    page_total += len(lpr)
                except (ValueError, TypeError):
                    parse_ok = False
    except OSError:
        return result
    result["json_record_count"] = parsed
    result["json_parse_ok"] = parse_ok
    result["json_page_count"] = page_total if parse_ok else None
    if not parse_ok:
        result["json_page_check"] = "not_verifiable"
        return result
    # G1:与 PDF 实际页数核对(非自证)
    if pdf_page_count is not None and isinstance(pdf_page_count, int):
        result["json_page_check"] = "match" if page_total == pdf_page_count else "mismatch"
    else:
        result["json_page_check"] = "not_verifiable"
    result["json_status"] = "complete" if (
        parsed > 0 and parse_ok and result["json_page_check"] in ("match", "not_verifiable")
    ) else "invalid"
    return result


def get_pdf_page_count(pdf_path):
    """读 PDF 实际页数。读取失败返回 None(不猜)。"""
    try:
        import pypdfium2
        doc = pypdfium2.PdfDocument(pdf_path)
        n = len(doc)
        doc.close()
        return n
    except Exception:
        return None


def validate_entry(entry):
    if not isinstance(entry, dict):
        raise ManifestError(f"记录必须是 JSON 对象: {entry!r}")
    missing = [k for k in REQUIRED_KEYS if k not in entry]
    if missing:
        raise ManifestError(f"记录缺键 {missing}: {entry!r}")
    for k in ("source_rel", "output_rel"):
        if not isinstance(entry[k], str) or not entry[k]:
            raise ManifestError(f"{k} 必须是非空字符串: {entry[k]!r}")
    for k in ("source_size",):
        if not isinstance(entry[k], int) or isinstance(entry[k], bool):
            raise ManifestError(f"{k} 必须是整数: {entry[k]!r}")
    # R67 扩展(用户裁决):pages 允许 null 表示页数未知,但仅当 provenance 在场
    # (禁 -1 哨兵污染数值语义、禁假 0 伪事实);runner 自身记账恒为真实整数。
    pages = entry["pages"]
    if pages is None:
        prov = entry.get("provenance")
        if not isinstance(prov, str) or not prov:
            raise ManifestError(
                f"pages=null 仅允许伴随非空 provenance(未知必须有出处): {entry!r}")
    elif not isinstance(pages, int) or isinstance(pages, bool):
        raise ManifestError(f"pages 必须是整数或 null: {pages!r}")
    for k in ("source_sha256", "written_at"):
        if not isinstance(entry[k], str) or not entry[k]:
            raise ManifestError(f"{k} 必须是非空字符串: {entry[k]!r}")
    # PREPROCESSING-OCR-JSON-01:可选 JSON 双输出字段校验(存在才检,历史条目不受影响)
    if "output_json_rel" in entry:
        if not isinstance(entry["output_json_rel"], str) or not entry["output_json_rel"]:
            raise ManifestError(f"output_json_rel 必须是非空字符串: {entry['output_json_rel']!r}")
    if "output_json_sha256" in entry:
        if not isinstance(entry["output_json_sha256"], str) or not entry["output_json_sha256"]:
            raise ManifestError(f"output_json_sha256 必须是非空字符串: {entry['output_json_sha256']!r}")
    if "ocr_run_id" in entry:
        if not isinstance(entry["ocr_run_id"], str) or not entry["ocr_run_id"]:
            raise ManifestError(f"ocr_run_id 必须是非空字符串: {entry['ocr_run_id']!r}")
    # PREPROCESSING-OCR-JSON-01-R2 F1:ocr_model / ocr_params 校验
    if "ocr_model" in entry:
        if not isinstance(entry["ocr_model"], str) or not entry["ocr_model"]:
            raise ManifestError(f"ocr_model 必须是非空字符串: {entry['ocr_model']!r}")
    if "ocr_params" in entry:
        if not isinstance(entry["ocr_params"], dict):
            raise ManifestError(f"ocr_params 必须是字典: {type(entry['ocr_params']).__name__}")
        try:
            json.dumps(entry["ocr_params"])
        except (TypeError, ValueError) as e:
            raise ManifestError(f"ocr_params 必须可 JSON 序列化: {e}")
    # PREPROCESSING-OCR-JSON-01-R2 F2:output_md_sha256 校验
    if "output_md_sha256" in entry:
        if not isinstance(entry["output_md_sha256"], str) or not entry["output_md_sha256"]:
            raise ManifestError(f"output_md_sha256 必须是非空字符串: {entry['output_md_sha256']!r}")
    # PREPROCESSING-OCR-JSON-01-R2 F5:json_status 校验
    if "json_status" in entry:
        _VALID_JSON_STATUS = ("complete", "invalid", "absent", "not_checked")
        if entry["json_status"] not in _VALID_JSON_STATUS:
            raise ManifestError(
                f"json_status 必须是 {_VALID_JSON_STATUS} 之一: {entry['json_status']!r}")
    # PREPROCESSING-OCR-JSON-01-R2 G1:pdf_page_count 校验(可选,int 或 None)
    if "pdf_page_count" in entry:
        if entry["pdf_page_count"] is not None:
            if not isinstance(entry["pdf_page_count"], int) or isinstance(entry["pdf_page_count"], bool):
                raise ManifestError(f"pdf_page_count 必须是整数或 null: {entry['pdf_page_count']!r}")
    return entry


def load_manifest(path):
    """读入清单 → {source_rel(归一): 记录},同键后写覆盖(append-only, last wins)。

    文件缺失 = 首次运行,空清单(不是损坏);
    任何坏行/缺键/非法类型 → ManifestError(含文件与行号),fail-closed。
    """
    if not os.path.exists(path):
        return {}
    manifest = {}
    with open(path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except ValueError as e:
                raise ManifestError(f"{path}:{lineno}: 非法 JSON: {e}")
            try:
                validate_entry(rec)
            except ManifestError as e:
                raise ManifestError(f"{path}:{lineno}: {e}")
            manifest[normalize_rel(rec["source_rel"])] = rec
    return manifest


def append_entry(path, entry):
    """单行追加 + fsync;先校验后写,坏记录绝不落盘。"""
    validate_entry(entry)
    line = json.dumps(entry, ensure_ascii=False, sort_keys=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())


_SKIP_REASONS = ("EXISTS", "MANIFEST_DONE", "NO_MANIFEST_ENTRY",
                 "SOURCE_CHANGED", "SOURCE_UNVERIFIABLE")


def decide_skip(*, output_md, source_pdf, pdf_root, output_root, manifest):
    """skip 决策。返回 (skip, reason, detail)。

    仅 EXISTS 与 MANIFEST_DONE 为 skip=True;其余原因一律放行 OCR
    (显式原因入日志,绝不猜测"可能已经处理过")。
    记录输出的现状(present / missing-or-moved)只入 detail 供日志留证,
    不参与决策(见模块头设计裁定)。

    ISOLATION-01 唯一增量:期望输出在位时,若台账在册且 size/sha256 与
    当前 source 不符(SOURCE_CHANGED),不得被 EXISTS 短路掩盖——同名文件
    不能在"源已换"时充当本轮产物。台账无记录时保持 R25 既有 EXISTS 语义
    (完整产物按名复用,处置权在人)。
    """
    # 期望输出存在且 >100B(R25 冻结语义):期望输出存在且 >100B → skip
    if os.path.exists(output_md) and os.path.getsize(output_md) > 100:
        try:
            rel = normalize_rel(os.path.relpath(source_pdf, pdf_root))
        except ValueError as e:
            return False, "SOURCE_UNVERIFIABLE", {"error": repr(e)}
        entry = manifest.get(rel)
        if entry is not None:
            try:
                size = os.path.getsize(source_pdf)
            except OSError as e:
                return False, "SOURCE_UNVERIFIABLE", {"source_rel": rel,
                                                      "error": repr(e)}
            if size != entry["source_size"]:
                return False, "SOURCE_CHANGED", {
                    "source_rel": rel, "current_size": size,
                    "recorded_size": entry["source_size"]}
            sha = file_sha256(source_pdf)
            if sha != entry["source_sha256"]:
                return False, "SOURCE_CHANGED", {
                    "source_rel": rel, "detail": "sha256 不一致(size 相同)"}
        return True, "EXISTS", {}

    try:
        rel = normalize_rel(os.path.relpath(source_pdf, pdf_root))
    except ValueError as e:
        return False, "SOURCE_UNVERIFIABLE", {"error": repr(e)}
    entry = manifest.get(rel)
    if entry is None:
        return False, "NO_MANIFEST_ENTRY", {"source_rel": rel}

    try:
        size = os.path.getsize(source_pdf)
    except OSError as e:
        return False, "SOURCE_UNVERIFIABLE", {"source_rel": rel,
                                              "error": repr(e)}
    if size != entry["source_size"]:
        return False, "SOURCE_CHANGED", {
            "source_rel": rel, "current_size": size,
            "recorded_size": entry["source_size"]}

    sha = file_sha256(source_pdf)
    if sha != entry["source_sha256"]:
        return False, "SOURCE_CHANGED", {
            "source_rel": rel, "detail": "sha256 不一致(size 相同)"}

    recorded = os.path.join(output_root, entry["output_rel"])
    status = ("present" if os.path.exists(recorded)
              and os.path.getsize(recorded) > 100 else "missing-or-moved")
    return True, "MANIFEST_DONE", {
        "source_rel": rel, "recorded_output_rel": entry["output_rel"],
        "recorded_output_status": status}

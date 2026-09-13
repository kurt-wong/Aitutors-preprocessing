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
               written_at):
    """构造一次成功 OCR 的清单记录(路径相对各自根,正斜杠归一)。"""
    entry = {
        "source_rel": normalize_rel(os.path.relpath(source_pdf, pdf_root)),
        "source_size": os.path.getsize(source_pdf),
        "source_sha256": file_sha256(source_pdf),
        "output_rel": normalize_rel(os.path.relpath(output_md, output_root)),
        "written_at": written_at,
        "pages": pages,
    }
    validate_entry(entry)
    return entry


def validate_entry(entry):
    if not isinstance(entry, dict):
        raise ManifestError(f"记录必须是 JSON 对象: {entry!r}")
    missing = [k for k in REQUIRED_KEYS if k not in entry]
    if missing:
        raise ManifestError(f"记录缺键 {missing}: {entry!r}")
    for k in ("source_rel", "output_rel"):
        if not isinstance(entry[k], str) or not entry[k]:
            raise ManifestError(f"{k} 必须是非空字符串: {entry[k]!r}")
    for k in ("source_size", "pages"):
        if not isinstance(entry[k], int) or isinstance(entry[k], bool):
            raise ManifestError(f"{k} 必须是整数: {entry[k]!r}")
    for k in ("source_sha256", "written_at"):
        if not isinstance(entry[k], str) or not entry[k]:
            raise ManifestError(f"{k} 必须是非空字符串: {entry[k]!r}")
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
    """
    # 既有行为原样保留(R25 冻结语义):期望输出存在且 >100B → skip
    if os.path.exists(output_md) and os.path.getsize(output_md) > 100:
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

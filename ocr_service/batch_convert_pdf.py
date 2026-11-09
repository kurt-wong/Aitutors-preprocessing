# -*- coding: utf-8 -*-
"""
批量转换PDF文档为Markdown (带每日页数限制)
使用PaddleOCR-VL-1.6 API
每日限制: 20000页
"""

import hashlib
import json
import os
import re
import requests
import sys
import tempfile
import time
import urllib3
import uuid
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# R66 D5-A(用户 R65 裁定限定解冻):输出清单 R-OHM-1,governance/rule_registry.md §7。
# 仅新增 skip 判定与记账接线;process_pdf 主体与 OCR API 语义不变。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from output_manifest import (ManifestError, append_entry, decide_skip,  # noqa: E402
                             load_manifest, make_entry, normalize_rel)

JOB_URL = "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"
# QCORE-E2E-01 阻断修复(同 H-01 模式):旧绝对路径 D:\Project\Papers 已迁移,
# 根目录改由脚本位置解析,任何 checkout 位置均成立。
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _load_token():
    """OCR API token: 环境变量 OCR_API_TOKEN 优先, 其次用户主目录 ~/.aitutors/ocr_token (仓库外私有配置)。"""
    t = os.environ.get("OCR_API_TOKEN")
    if t:
        return t.strip()
    cfgp = os.path.join(os.path.expanduser("~"), ".aitutors", "ocr_token")
    if os.path.isfile(cfgp):
        with open(cfgp, encoding="utf-8-sig") as f:
            t = f.read().strip()
        if t:
            return t
    return None

TOKEN = _load_token()
if not TOKEN:
    sys.exit("缺少 OCR API token: 请设置环境变量 OCR_API_TOKEN 或在 ~/.aitutors/ocr_token 写入 token")
MODEL = "PaddleOCR-VL-1.6"

DAILY_PAGE_LIMIT = 20000
PAGE_USAGE_FILE = os.path.join(BASE, "data", "ocr_page_usage.json")

optional_payload = {
    "useDocOrientationClassify": False,
    "useDocUnwarping": False,
    "useChartRecognition": False,
}

PDF_ROOT = os.path.join(BASE, "maintainess", "PDF")
OUTPUT_ROOT = os.path.join(BASE, "Ocr-markdown")
LOG_FILE = os.path.join(BASE, "logs", "ocr_batch_log.txt")
MANIFEST_FILE = os.path.join(BASE, "data", "ocr_output_manifest.jsonl")

session = requests.Session()
session.verify = False
session.proxies = {
    "http": "http://127.0.0.1:58182",
    "https": "http://127.0.0.1:58182",
}

def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_msg + "\n")

def _manifest_digest(path):
    """R67.1 Gate C2:manifest 加载时点文件 sha256(absent = 文件不存在,非空文件)。"""
    if not os.path.exists(path):
        return "absent"
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def load_page_usage():
    """加载页数使用记录"""
    today = time.strftime("%Y-%m-%d")
    if os.path.exists(PAGE_USAGE_FILE):
        with open(PAGE_USAGE_FILE, "r") as f:
            data = json.load(f)
        if data.get("date") == today:
            return data
    return {"date": today, "used": 0}

def save_page_usage(used):
    """保存页数使用记录"""
    today = time.strftime("%Y-%m-%d")
    with open(PAGE_USAGE_FILE, "w") as f:
        json.dump({"date": today, "used": used}, f)

def safe_get(url, retries=3, delay=3):
    for attempt in range(retries):
        try:
            r = session.get(url, timeout=60)
            if r.status_code == 200:
                return r
        except:
            if attempt < retries - 1:
                time.sleep(delay)
    return None

def extract_grade_subject(filename):
    grade = "未分类"
    subject = "未分类"
    if re.search(r'高一|高1', filename):
        grade = "高一"
    elif re.search(r'高二|高2', filename):
        grade = "高二"
    elif re.search(r'高三|高3', filename):
        grade = "高三"
    for s in ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"]:
        if s in filename:
            subject = s
            break
    return grade, subject

def _magic_ok(head):
    """JPEG / PNG / GIF / WEBP 魔数。"""
    return (head.startswith(b"\xff\xd8") or head.startswith(b"\x89PNG")
            or head.startswith(b"GIF8") or head.startswith(b"RIFF"))


_TRUE_ENV = {"1", "true", "yes"}
_FALSE_ENV = {"", "0", "false", "no"}


def _env_flag(name):
    """显式布尔开关:仅 1/true/yes(大小写不敏感)为真。

    未设置、空串、0/false/no 为假;非法值按假处理并显式留痕
    (ISOLATION-01 §四-C:不得依赖 Python truthiness,否则 "0" 会被误判为真)。
    """
    raw = os.environ.get(name)
    if raw is None:
        return False
    s = raw.strip().lower()
    if s in _TRUE_ENV:
        return True
    if s in _FALSE_ENV:
        return False
    log(f"  [ENV-INVALID] {name}={raw!r} 非法布尔值,按 False 处理(仅 1/true/yes 启用)")
    return False


def _unique_path(path):
    """返回不覆盖既有文件的路径;path 空闲时原样返回。"""
    if not os.path.exists(path):
        return path
    n = 1
    while os.path.exists(f"{path}.{n}"):
        n += 1
    return f"{path}.{n}"


def _atomic_write_bytes(path, data):
    """同目录临时文件写满 + fsync 后 os.replace 提交;失败清理临时文件。

    只有完整内容才会出现在 path;中断留下的是 .tmp,不会被产物检查当作有效文件。
    """
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=os.path.basename(path) + ".",
                               suffix=".tmp", dir=parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return path


def _atomic_write_text(path, text):
    """文本版原子写(保留默认换行转换,与原 open(..., 'w') 行为一致)。"""
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=os.path.basename(path) + ".",
                               suffix=".tmp", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return path


IMG_SRC_RE = re.compile(r'<img[^>]*src="([^"]*)"')

# 图片下载独立会话:直连,不随 OCR 会话的 mitm/系统代理(批量与直调行为一致)
_dl_session = requests.Session()
_dl_session.verify = False
_dl_session.proxies = {}
_dl_session.trust_env = False


def _split_refs(md_text):
    """(本地相对引用, 远端 http(s), data-uri 内嵌) 去重保序。"""
    remote, local, embedded, seen = [], [], [], set()
    for s in IMG_SRC_RE.findall(md_text or ""):
        if not s or s in seen:
            continue
        seen.add(s)
        if s.startswith("data:"):
            embedded.append(s)
        elif s.startswith(("http://", "https://")):
            remote.append(s)
        else:
            local.append(s)
    return local, remote, embedded


def _safe_dest(output_dir, ref):
    """ref 必须是 output_dir 之下的相对路径(防 ../ 穿越);返回绝对 dest 或 None。"""
    norm = str(ref).replace("\\", "/")
    if norm.startswith("/") or re.match(r"^[A-Za-z]:", norm) or ".." in norm.split("/"):
        return None
    dest = os.path.normpath(os.path.join(output_dir, norm))
    root = os.path.normpath(output_dir)
    if not (dest == root or dest.startswith(root + os.sep)):
        return None
    return dest


def _check_local_file(dest):
    """(ok, reason) 文件存在且字节/魔数合法。"""
    if not dest or not os.path.isfile(dest):
        return False, "file_not_found"
    with open(dest, "rb") as f:
        head = f.read(16)
        f.seek(0, os.SEEK_END)
        size = f.tell()
    if size <= 0:
        return False, "empty_file"
    if not _magic_ok(head):
        return False, "bad_magic"
    return True, "ok"


def _existing_delivery_ok(md_path, output_dir):
    """既有产物交付契约检查(ISOLATION-01 §四-A):
      ① md 可读 ② 不含远端 http(s) 引用(本地交付契约不接受悬空远端)
      ③ 每个本地引用实体存在、字节/魔数合法。
    附加绑定(增量,向后兼容):{base}.imgs_integrity.json 在场时,
    逐项 sha256 与 md_sha256(字段存在才查)必须与落盘字节一致——
    历史同名图片不得替代本轮所需图片;报告缺席时按 ①②③ 判定,
    不破坏既有产物(含已验收 22/22 基线)的复用语义。"""
    base = os.path.splitext(os.path.basename(md_path))[0]
    try:
        with open(md_path, "rb") as f:
            md_bytes = f.read()
    except OSError:
        return False
    local, remote, _embedded = _split_refs(
        md_bytes.decode("utf-8", errors="replace"))
    if remote:
        return False
    for ref in local:
        ok, _ = _check_local_file(_safe_dest(output_dir, ref))
        if not ok:
            return False
    rep_path = os.path.join(output_dir, f"{base}.imgs_integrity.json")
    try:
        with open(rep_path, encoding="utf-8") as f:
            rep = json.load(f)
    except Exception:
        rep = None
    if isinstance(rep, dict):
        if "md_sha256" in rep and \
                rep.get("md_sha256") != hashlib.sha256(md_bytes).hexdigest():
            return False
        item_sha = {it.get("src"): it.get("sha256")
                    for it in (rep.get("items") or [])
                    if it.get("status") == "ok"}
        for ref in local:
            recorded = item_sha.get(ref)
            if not recorded:
                return False
            try:
                with open(_safe_dest(output_dir, ref), "rb") as f:
                    if hashlib.sha256(f.read()).hexdigest() != recorded:
                        return False
            except OSError:
                return False
    return True


def _deliver_images(md_text, images_map, output_dir, base_name):
    """图片资源交付契约(TASK-PREPROC-IMG-DELIVERY-01 / DSH 复核 2.4):
      markdown.text 中每个本地图引用必须 ① 在 markdown.images 有映射
      ② 下载到 md 同目录 imgs/ ③ 存在且魔数/字节数合法。
    远端 http(s) 引用 = 显式失败(本地交付契约不接受悬空远端);data: 内嵌视为已交付。
    任一步缺失 => 显式失败(返回 False),禁止"md 已写出即完整成功"。
    始终写出 {base_name}.imgs_integrity.json 供追溯。同 basename 不同内容
    => basename_collision 显式失败(与 reslice 禁止静默合并同语义);
    同 hash 复用既有实体,不同 hash 绝不覆盖/沿用(TASK-PREPROC-IMG-DELIVERY-01
    既有契约:失败显式、留证,人工处置后重试可恢复)。
    """
    local, remote, embedded = _split_refs(md_text)
    items = []

    for ref in remote:
        items.append({"src": ref, "status": "remote_ref_not_local_delivery"})
    for ref in embedded:
        items.append({"src": ref[:60] + "…", "status": "embedded_ok"})

    ok = not remote
    for ref in local:
        item = {"src": ref, "mapped": ref in (images_map or {})}
        if not item["mapped"]:
            item["status"] = "unmapped"
            ok = False
            items.append(item)
            continue
        dest = _safe_dest(output_dir, ref)
        if dest is None:
            item["status"] = "unsafe_path"
            ok = False
            items.append(item)
            continue
        url = (images_map or {})[ref]
        if not isinstance(url, str) or not url:
            item["status"] = "invalid_url"
            ok = False
            items.append(item)
            continue
        item["url_host"] = url.split("/")[2] if "://" in url else None
        item["dest"] = dest
        try:
            if os.path.dirname(dest):
                os.makedirs(os.path.dirname(dest), exist_ok=True)
        except Exception as e:
            item["status"] = "write_failed"
            item["error"] = f"{type(e).__name__}: {e}"
            ok = False
            items.append(item)
            continue
        data = None
        for attempt in range(2):
            try:
                r = _dl_session.get(url, timeout=60)
                if r.status_code == 200 and r.content:
                    data = r.content
                    break
                item["http_status"] = r.status_code
            except Exception as e:
                item["error"] = f"{type(e).__name__}: {e}"
            time.sleep(2)
        if data is None:
            item["status"] = "download_failed"
            ok = False
            items.append(item)
            continue
        existing_same = False
        if os.path.exists(dest):
            with open(dest, "rb") as f:
                old_hash = hashlib.sha256(f.read()).hexdigest()
            new_hash = hashlib.sha256(data).hexdigest()
            if old_hash != new_hash:
                item["status"] = "basename_collision"
                item["existing_sha256"] = old_hash
                item["incoming_sha256"] = new_hash
                ok = False
                items.append(item)
                continue
            existing_same = True
        if not existing_same:
            try:
                _atomic_write_bytes(dest, data)
            except Exception as e:
                item["status"] = "write_failed"
                item["error"] = f"{type(e).__name__}: {e}"
                ok = False
                items.append(item)
                continue
        item["bytes"] = len(data)
        item["sha256"] = hashlib.sha256(data).hexdigest()
        item["magic_ok"] = _magic_ok(data[:16])
        item["status"] = "ok" if item["magic_ok"] and item["bytes"] > 0 else "invalid_bytes"
        if item["status"] != "ok":
            ok = False
        items.append(item)

    report = {
        "base": base_name,
        "local_refs": local,
        "remote_refs": remote,
        "embedded_refs": [s[:60] + "…" for s in embedded],
        "images_map_keys": sorted(images_map or {}),
        "items": items,
        "ok": ok,
    }
    rep_path = os.path.join(output_dir, f"{base_name}.imgs_integrity.json")
    _atomic_write_text(rep_path, json.dumps(report, ensure_ascii=False, indent=2))
    return ok


def process_pdf(file_path, output_dir, original_filename, page_usage):
    headers = {"Authorization": f"bearer {TOKEN}"}

    if not os.path.exists(file_path):
        return False, 0

    base_name = os.path.splitext(original_filename)[0]
    base_name = re.sub(r'[<>:"/\\|?*]', '_', base_name)
    output_md = os.path.join(output_dir, f"{base_name}.md")

    if os.path.exists(output_md) and os.path.getsize(output_md) > 100:
        # DSH 复核 P1:短路不得在图片不完整时洗成成功
        if _existing_delivery_ok(output_md, output_dir):
            return True, 0
        stale = _unique_path(output_md + ".incomplete")
        os.replace(output_md, stale)  # 不留可跳过产物,证据保留(唯一名防覆盖)
        log(f"  [IMG-INCOMPLETE] 既有 md 图片完整性不通过,已改名 "
            f"{os.path.basename(stale)},转为重处理: {base_name}")

    data = {"model": MODEL, "optionalPayload": json.dumps(optional_payload)}

    try:
        with open(file_path, "rb") as f:
            files = {"file": f}
            job_response = session.post(JOB_URL, headers=headers, data=data, files=files, timeout=120)
    except Exception as e:
        log(f"  [ERROR] Submit: {e}")
        return False, 0

    if job_response.status_code != 200:
        return False, 0

    jobId = job_response.json()["data"]["jobId"]

    jsonl_url = ""
    for _ in range(120):
        try:
            r = session.get(f"{JOB_URL}/{jobId}", headers=headers, timeout=60)
        except:
            time.sleep(5)
            continue
        if r.status_code != 200:
            return False, 0
        state = r.json()["data"]["state"]
        if state == "done":
            jsonl_url = r.json()["data"]["resultUrl"]["jsonUrl"]
            break
        elif state == "failed":
            return False, 0
        time.sleep(5)

    if not jsonl_url:
        return False, 0

    os.makedirs(output_dir, exist_ok=True)
    jsonl_response = safe_get(jsonl_url)
    if not jsonl_response:
        return False, 0

    lines = jsonl_response.text.strip().split("\n")
    all_md = []
    page_count = 0
    images_map = {}

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            result = json.loads(line)["result"]
            for res in result["layoutParsingResults"]:
                all_md.append(res["markdown"]["text"])
                page_count += 1
                for k, v in ((res.get("markdown") or {}).get("images") or {}).items():
                    images_map.setdefault(k, v)
        except:
            pass

    if not all_md:
        return False, 0

    merged = "\n\n---\n\n".join(all_md)
    # 原始响应留痕(TASK-PREPROC-IMG-DELIVERY-01)。含签名 URL,按凭据材料对待:
    # 仅本地留存(Ocr-markdown/ 已 gitignore),不进仓库/公开日志。
    raw_path = os.path.join(output_dir, f"{base_name}.ocr_raw.jsonl")
    _atomic_write_text(raw_path, jsonl_response.text)
    # 图片交付先于 md 最终落盘:失败不留可被 skip 的完整 md(DSH 复核 2 修复顺序)
    if not _deliver_images(merged, images_map, output_dir, base_name):
        inc_path = _unique_path(output_md + ".incomplete")
        _atomic_write_text(inc_path, merged)
        log(f"  [IMG-FAIL] 图片交付不完整: {base_name} "
            f"(文本存 {os.path.basename(inc_path)},不产生可跳过 md;详见 {base_name}.imgs_integrity.json)")
        return False, page_count
    _atomic_write_text(output_md, merged)
    # 交付凭证封口(ISOLATION-01 §四-B):报告补记 md_sha256 以落盘字节为准,
    # 此后 _existing_delivery_ok 才可能认证通过;封口失败 = 未认证,显式失败。
    rep_path = os.path.join(output_dir, f"{base_name}.imgs_integrity.json")
    try:
        with open(output_md, "rb") as f:
            md_sha = hashlib.sha256(f.read()).hexdigest()
        with open(rep_path, encoding="utf-8") as f:
            rep = json.load(f)
        rep["md_sha256"] = md_sha
        _atomic_write_text(rep_path, json.dumps(rep, ensure_ascii=False, indent=2))
    except Exception as e:
        log(f"  [WARN] 交付凭证封口失败({type(e).__name__}: {e}),"
            f"产物按未认证对待: {base_name}")
        return False, page_count
    log(f"  [OK] {page_count} pages")
    return True, page_count

def main():
    log("="*60)
    log("批量转换PDF文档 (带每日页数限制)")
    log(f"每日限制: {DAILY_PAGE_LIMIT} 页")
    log("="*60)

    # 加载今日页数使用情况
    page_usage = load_page_usage()
    used_pages = page_usage["used"]
    remaining_pages = DAILY_PAGE_LIMIT - used_pages

    log(f"今日已使用: {used_pages} 页")
    log(f"今日剩余: {remaining_pages} 页")

    if remaining_pages <= 0:
        log("已达今日页数限制，请明天再试")
        return

    # R-OHM-1:载入输出清单(fail-closed:损坏即中止,禁止静默降级为重跑)
    try:
        manifest = load_manifest(MANIFEST_FILE)
    except ManifestError as e:
        log(f"[FATAL] 输出清单损坏,拒绝继续(R-OHM-1 fail-closed): {e}")
        raise SystemExit(2)
    log(f"输出清单载入: {len(manifest)} 条 source 记录")
    # R67.1 Gate C2:结构化加载证据(条数 + 加载时点 digest;fail-closed 在上方,禁静默降级)
    log(f"[MANIFEST_LOAD] entries={len(manifest)} "
        f"sha256={_manifest_digest(MANIFEST_FILE)}")

    # 收集所有PDF文件
    all_files = []

    # 根目录下的PDF
    root_pdfs = [f for f in os.listdir(PDF_ROOT) if f.lower().endswith(".pdf")]
    for filename in root_pdfs:
        file_path = os.path.join(PDF_ROOT, filename)
        grade, subject = extract_grade_subject(filename)
        output_dir = os.path.join(OUTPUT_ROOT, grade, subject)
        all_files.append((file_path, output_dir, filename))

    # 子目录中的PDF
    for grade in ["高一", "高二", "高三"]:
        grade_path = os.path.join(PDF_ROOT, grade)
        if not os.path.isdir(grade_path):
            continue
        for subject in os.listdir(grade_path):
            subject_path = os.path.join(grade_path, subject)
            if not os.path.isdir(subject_path):
                continue
            for filename in os.listdir(subject_path):
                if filename.lower().endswith(".pdf"):
                    file_path = os.path.join(subject_path, filename)
                    output_dir = os.path.join(OUTPUT_ROOT, grade, subject)
                    all_files.append((file_path, output_dir, filename))

    total = len(all_files)
    log(f"共发现 {total} 个PDF文件")

    success = 0
    skip = 0
    fail = 0
    skip_img_incomplete = 0
    pages_used_today = used_pages
    start_time = time.time()
    limit_reached = False

    for i, (file_path, output_dir, filename) in enumerate(all_files, 1):
        # 检查页数限制
        if pages_used_today >= DAILY_PAGE_LIMIT:
            log(f"\n{'='*60}")
            log(f"已达今日页数限制 ({DAILY_PAGE_LIMIT} 页)")
            log(f"请明天继续运行脚本")
            log(f"{'='*60}")
            limit_reached = True
            break

        # 检查是否已存在(R-OHM-1:期望输出落空时查清单,MANIFEST_DONE 切断跑步机)
        base_name = os.path.splitext(filename)[0]
        base_name = re.sub(r'[<>:"/\\|?*]', '_', base_name)
        output_md = os.path.join(output_dir, f"{base_name}.md")

        skip_now, skip_reason, skip_detail = decide_skip(
            output_md=output_md, source_pdf=file_path, pdf_root=PDF_ROOT,
            output_root=OUTPUT_ROOT, manifest=manifest)
        if skip_reason != "EXISTS":
            # 既有 EXISTS 路径保持静默;其余决策(无论 skip 与否)显式留证
            log(f"[DECIDE:{skip_reason}] {filename[:50]} -> "
                f"{json.dumps(skip_detail, ensure_ascii=False)}")
        if skip_now:
            # 图片交付契约门(DSH 复核 2 修复顺序 3):台账跳过不得掩盖图片不完整。
            # 默认守 R-OHM-1 反跑批语义(不自动重跑);显式迁移设 OCR_REPROCESS_INCOMPLETE=1。
            if not _existing_delivery_ok(output_md, output_dir):
                if not _env_flag("OCR_REPROCESS_INCOMPLETE"):
                    # 交付检查不通过:默认不重处理(反跑批),但不得计为 skip/成功;
                    # 计为失败并显式阻断,等待人工授权迁移。
                    log(f"[IMG-INCOMPLETE-BLOCKED] {filename[:50]} 既有产物未通过交付检查;"
                        f"默认不重处理,如需迁移设 OCR_REPROCESS_INCOMPLETE=1")
                    skip_img_incomplete += 1
                    fail += 1
                    continue
                log(f"[IMG-MIGRATE] 强制重处理图片不完整产物: {filename[:50]}")
                skip_now = False
            else:
                # PREPROCESSING-OCR-JSON-01-R2 G2:json_status 非 complete 时
                # 不可复用,显式阻断(不自动重跑,同 IMG-INCOMPLETE-BLOCKED 模式)
                try:
                    _rel = normalize_rel(os.path.relpath(file_path, PDF_ROOT))
                    _prev = manifest.get(_rel)
                    _js = (_prev or {}).get("json_status")
                except Exception:
                    _js = None
                if _js is not None and _js != "complete":
                    log(f"[JSON-INCOMPLETE-BLOCKED] {filename[:50]} 台账 json_status={_js};"
                        f"不复用,不自动重跑,等待人工处置")
                    fail += 1
                    continue
                skip += 1
                continue

        grade = output_dir.replace(OUTPUT_ROOT, "").strip("\\").split("\\")[0]
        subject = output_dir.replace(OUTPUT_ROOT, "").strip("\\").split("\\")[1] if len(output_dir.replace(OUTPUT_ROOT, "").strip("\\").split("\\")) > 1 else ""

        log(f"[{i}/{total}] {grade}/{subject}/{filename[:50]}...")

        result, pages = process_pdf(file_path, output_dir, filename, page_usage)
        
        if result:
            # PREPROCESSING-OCR-JSON-01-R2 G2:JSON 完整性检查后再计成功
            output_json = os.path.join(output_dir, f"{base_name}.ocr_raw.jsonl")
            ocr_run_id = str(uuid.uuid4())
            try:
                entry = make_entry(source_pdf=file_path, pdf_root=PDF_ROOT,
                                   output_md=output_md, output_root=OUTPUT_ROOT,
                                   pages=pages,
                                   written_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                                   output_json=output_json,
                                   ocr_run_id=ocr_run_id,
                                   ocr_model=MODEL,
                                   ocr_params=optional_payload)
                append_entry(MANIFEST_FILE, entry)
                manifest[entry["source_rel"]] = entry
            except ManifestError as e:
                log(f"[FATAL] 输出清单写入失败,拒绝静默继续(R-OHM-1): {e}")
                raise SystemExit(2)
            # G2:json_status 非 complete → 不计成功,显式阻断(不自动重跑)
            js = entry.get("json_status")
            if js == "complete":
                success += 1
                pages_used_today += pages
                save_page_usage(pages_used_today)
            else:
                fail += 1
                log(f"  [JSON-BLOCKED] json_status={js}: {base_name} "
                    f"(records={entry.get('json_record_count')}, "
                    f"json_pages={entry.get('json_page_count')}, "
                    f"pdf_pages={entry.get('pdf_page_count')}, "
                    f"check={entry.get('json_page_check')}) — 不计成功,等待人工处置")
        else:
            fail += 1

        if i % 10 == 0:
            elapsed = time.time() - start_time
            log(f"\n--- 进度: {i}/{total} | 成功:{success} 跳过:{skip} 失败:{fail} | 今日已用:{pages_used_today}/{DAILY_PAGE_LIMIT}页 ---\n")

        time.sleep(0.5)

    elapsed = time.time() - start_time
    log(f"\n{'='*60}")
    if limit_reached:
        log("转换暂停 - 达到今日页数限制")
    else:
        log("转换完成!")
    log(f"总计处理: {success + skip + fail} | 成功: {success} | 跳过: {skip} | 失败: {fail}")
    if skip_img_incomplete:
        log(f"其中阻断未处理(既有产物未通过交付检查,需 OCR_REPROCESS_INCOMPLETE=1 迁移): {skip_img_incomplete}")
    log(f"今日使用页数: {pages_used_today} / {DAILY_PAGE_LIMIT}")
    log(f"用时: {elapsed/60:.1f}分钟")
    log(f"{'='*60}")

if __name__ == "__main__":
    main()


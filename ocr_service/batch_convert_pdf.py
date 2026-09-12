# -*- coding: utf-8 -*-
"""
批量转换PDF文档为Markdown (带每日页数限制)
使用PaddleOCR-VL-1.6 API
每日限制: 20000页
"""

import json
import os
import re
import requests
import sys
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

JOB_URL = "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"
BASE = r"D:\Project\Papers"

def _load_token():
    """OCR API token: 优先环境变量, 其次 data/.ocr_config (与 .llm_config 同款, 勿外泄)。"""
    t = os.environ.get("OCR_API_TOKEN")
    if t:
        return t.strip()
    cfgp = os.path.join(BASE, "data", ".ocr_config")
    if os.path.exists(cfgp):
        for line in open(cfgp, encoding="utf-8"):
            if "=" in line:
                k, v = line.strip().split("=", 1)
                if k.strip() == "token":
                    return v.strip()
    return None

TOKEN = _load_token()
if not TOKEN:
    sys.exit("缺少 OCR API token: 请设环境变量 OCR_API_TOKEN 或写入 data/.ocr_config")
MODEL = "PaddleOCR-VL-1.6"

DAILY_PAGE_LIMIT = 20000
PAGE_USAGE_FILE = r"D:\Project\Papers\data\ocr_page_usage.json"

optional_payload = {
    "useDocOrientationClassify": False,
    "useDocUnwarping": False,
    "useChartRecognition": False,
}

PDF_ROOT = r"D:\Project\Papers\maintainess\PDF"
OUTPUT_ROOT = r"D:\Project\Papers\Ocr-markdown"
LOG_FILE = r"D:\Project\Papers\logs\ocr_batch_log.txt"

session = requests.Session()
session.verify = False
session.proxies = {
    "http": "http://127.0.0.1:55219",
    "https": "http://127.0.0.1:55219",
}

def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_msg + "\n")

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

def process_pdf(file_path, output_dir, original_filename, page_usage):
    headers = {"Authorization": f"bearer {TOKEN}"}

    if not os.path.exists(file_path):
        return False, 0

    base_name = os.path.splitext(original_filename)[0]
    base_name = re.sub(r'[<>:"/\\|?*]', '_', base_name)
    output_md = os.path.join(output_dir, f"{base_name}.md")

    if os.path.exists(output_md) and os.path.getsize(output_md) > 100:
        return True, 0

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

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            result = json.loads(line)["result"]
            for res in result["layoutParsingResults"]:
                all_md.append(res["markdown"]["text"])
                page_count += 1
        except:
            pass

    if all_md:
        merged = "\n\n---\n\n".join(all_md)
        with open(output_md, "w", encoding="utf-8") as f:
            f.write(merged)
        log(f"  [OK] {page_count} pages")
        return True, page_count

    return False, 0

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

        # 检查是否已存在
        base_name = os.path.splitext(filename)[0]
        base_name = re.sub(r'[<>:"/\\|?*]', '_', base_name)
        output_md = os.path.join(output_dir, f"{base_name}.md")

        if os.path.exists(output_md) and os.path.getsize(output_md) > 100:
            skip += 1
            continue

        grade = output_dir.replace(OUTPUT_ROOT, "").strip("\\").split("\\")[0]
        subject = output_dir.replace(OUTPUT_ROOT, "").strip("\\").split("\\")[1] if len(output_dir.replace(OUTPUT_ROOT, "").strip("\\").split("\\")) > 1 else ""

        log(f"[{i}/{total}] {grade}/{subject}/{filename[:50]}...")

        result, pages = process_pdf(file_path, output_dir, filename, page_usage)
        
        if result:
            success += 1
            pages_used_today += pages
            save_page_usage(pages_used_today)
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
    log(f"今日使用页数: {pages_used_today} / {DAILY_PAGE_LIMIT}")
    log(f"用时: {elapsed/60:.1f}分钟")
    log(f"{'='*60}")

if __name__ == "__main__":
    main()


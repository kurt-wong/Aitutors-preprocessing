# -*- coding: utf-8 -*-
"""
PDF转换守护脚本
功能：
1. 每天0:00自动重置页数限制并启动转换
2. 达到页数限制后自动停止
3. 等待到第二天0:00后自动重启
"""

import json
import os
import subprocess
import time
from datetime import datetime, timedelta

PAGE_USAGE_FILE = r"D:\Project\Papers\data\ocr_page_usage.json"
MAIN_SCRIPT = r"D:\Project\Papers\ocr_service\batch_convert_pdf.py"
LOG_FILE = r"D:\Project\Papers\logs\ocr_watchdog.log"
CHILD_ERR_LOG = r"D:\Project\Papers\logs\ocr_child_err.log"
DAILY_LIMIT = 20000

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_msg + "\n")

def get_page_usage():
    today = datetime.now().strftime("%Y-%m-%d")
    if os.path.exists(PAGE_USAGE_FILE):
        try:
            with open(PAGE_USAGE_FILE, "r") as f:
                data = json.load(f)
            if data.get("date") == today:
                return data.get("used", 0)
        except:
            pass
    return 0

def reset_page_usage():
    today = datetime.now().strftime("%Y-%m-%d")
    with open(PAGE_USAGE_FILE, "w") as f:
        json.dump({"date": today, "used": 0}, f)
    log(f"页数记录已重置: 0/{DAILY_LIMIT}")

def run_conversion():
    """运行主转换脚本"""
    log("启动转换脚本...")
    errf = open(CHILD_ERR_LOG, "a", encoding="utf-8", errors="replace")
    process = subprocess.Popen(
        ["python", MAIN_SCRIPT],
        # stdout 不捕获管道（batch 的 log() 已落盘 ocr_batch_log.txt），避免长跑写满管道死锁（BUG-12）；
        # stderr 重定向到文件，保留未捕获异常 traceback 供诊断（纯 DEVNULL 会丢）。
        stdout=subprocess.DEVNULL,
        stderr=errf,
    )
    process._errf = errf  # 供调用方在进程退出后关闭
    return process

def wait_until_midnight():
    """等待到明天0:00"""
    now = datetime.now()
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=5, microsecond=0)
    wait_seconds = (tomorrow - now).total_seconds()
    log(f"等待到明天0:00 (约{wait_seconds/3600:.1f}小时)")
    time.sleep(wait_seconds)

def main():
    log("="*60)
    log("PDF转换守护脚本启动")
    log("="*60)
    
    while True:
        # 检查当前页数使用情况
        used = get_page_usage()
        log(f"当前页数使用: {used}/{DAILY_LIMIT}")
        
        if used >= DAILY_LIMIT:
            log("今日页数已用尽，等待明天...")
            wait_until_midnight()
            # 重置页数
            reset_page_usage()
        
        # 启动转换
        process = run_conversion()
        
        # 监控转换进程
        while process.poll() is None:
            time.sleep(60)  # 每分钟检查一次
            used = get_page_usage()
            
            # 检查是否达到限制
            if used >= DAILY_LIMIT:
                log(f"达到页数限制 ({used}/{DAILY_LIMIT})，停止转换")
                process.terminate()
                process.wait(timeout=30)
                break
        
        # 检查进程退出原因
        exit_code = process.returncode
        log(f"转换进程退出，退出码: {exit_code}")
        try:
            process._errf.close()
        except Exception:
            pass
        
        # 如果是正常退出（达到限制），等待明天
        used = get_page_usage()
        if used >= DAILY_LIMIT:
            log("等待明天继续...")
            wait_until_midnight()
            reset_page_usage()
        else:
            # 异常退出，等待一段时间后重试
            log("异常退出，5分钟后重试...")
            time.sleep(300)

if __name__ == "__main__":
    main()

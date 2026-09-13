@echo off
rem R67.2 (F-r67.1-1 / F-r67.2-1): watchdog launcher owned by Windows Task Scheduler.
rem Rationale: children of harness pwsh die with its Job object (F-r67.1-1);
rem even SCM-created (Win32_Process.Create) processes were killed by a console
rem control event at ~00:15 (F-r67.2-1). Task Scheduler owns the lifecycle.
rem Launch: schtasks /Create /TN "OcrWatchdogDaemon" /TR "cmd.exe /c D:\Project\Papers\ocr_service\run_watchdog.cmd" /SC ONCE /ST 00:00 /F
rem         schtasks /Run /TN "OcrWatchdogDaemon"
cd /d D:\Project\Papers
python.exe ocr_service\ocr_watchdog.py >> logs\ocr_watchdog_stdout.log 2>&1

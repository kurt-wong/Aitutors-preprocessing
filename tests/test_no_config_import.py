# -*- coding: utf-8 -*-
"""H-01 回归(ChatGPT 二轮审查):模块 import 不得依赖私有配置文件。

真实手段(非 monkeypatch):子进程里把 RESLICE_ROOT 指向空临时目录,
CFG_PATH 即真实不存在——与 GitHub Actions Ubuntu runner 的无配置环境同构。
断言三件事:
  1. import reslice_pipeline 成功(确定性函数可离线使用);
  2. call_llm 在缺配置时显式抛 FileNotFoundError(拒绝吞异常式假修复);
  3. write_outputs 全套产物离线可生成,manifest model 用默认常量。
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def _run(code, reslice_root, payload=None):
    env = dict(os.environ, RESLICE_ROOT=str(reslice_root),
               PYTHONPATH=str(SCRIPTS))
    if payload is not None:
        env["TEST_PAYLOAD"] = json.dumps(payload, ensure_ascii=False)
    # cwd=workdir:子进程产生的任何相对路径产物都落在临时目录,不污染仓库
    return subprocess.run([sys.executable, "-c", code], capture_output=True,
                          text=True, env=env, cwd=str(reslice_root), timeout=180)


def test_import_succeeds_without_config(workdir):
    r = _run("import reslice_pipeline as rp; print('IMPORT_OK', rp.DEFAULT_MODEL)",
             workdir)
    assert r.returncode == 0, r.stderr
    assert "IMPORT_OK" in r.stdout


def test_call_llm_fails_loudly_without_config(workdir):
    code = (
        "import reslice_pipeline as rp\n"
        "try:\n"
        "    rp.call_llm('hi')\n"
        "    print('SWALLOWED')\n"
        "except FileNotFoundError as e:\n"
        "    print('EXPECTED', '.llm_config' in str(e))\n"
    )
    r = _run(code, workdir)
    assert r.returncode == 0, r.stderr
    assert "SWALLOWED" not in r.stdout, "缺配置被吞掉——违反 H-01 修复契约"
    assert "EXPECTED True" in r.stdout, r.stdout + r.stderr


def test_write_outputs_offline_without_config(workdir):
    lines = ["1. 题干（ ）", "", "1.【答案】A"]
    man = {"units": [{"unit_id": "Q1", "unit_type": "standalone_question",
                      "question_numbers": [1], "original_question_type": "single_choice",
                      "stem_lines": [1, 1], "options_lines": None,
                      "answer_lines": [3, 3], "explanation_lines": None}]}
    code = (
        "import json, os, pathlib\n"
        "import reslice_pipeline as rp\n"
        "d = json.loads(os.environ['TEST_PAYLOAD'])\n"
        "out = pathlib.Path('out')\n"
        "issues, summary = rp.validate_manifest(d['man'], len(d['lines']), d['lines'])\n"
        "rp.write_outputs(out, 'synth', d['lines'], d['man'], issues, summary,\n"
        "                 'synth.md', None)\n"
        "names = sorted(p.name for p in out.iterdir())\n"
        "mf = json.loads((out / 'synth.manifest.json').read_text(encoding='utf-8'))\n"
        "print('RESULT', names, mf['model'], len(issues))\n"
    )
    r = _run(code, workdir, payload={"lines": lines, "man": man})
    assert r.returncode == 0, r.stderr
    assert "synth.annotated.md" in r.stdout
    assert "synth.manifest.json" in r.stdout
    assert "synth.md" in r.stdout
    assert "mimo-x-pro-preview" in r.stdout   # 默认元数据标签,无配置也成立

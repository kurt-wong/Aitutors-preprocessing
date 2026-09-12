# -*- coding: utf-8 -*-
"""process_file 端到端测试(ChatGPT 二轮 T-03:补齐 E2E 缺口)。

唯一被 fake 的边界是 call_llm(LLM 网络调用,CI 不可调);
其余全部真实代码:行号化 → build_prompt → extract_json → 无题号补号 →
clamp_intervals → validate_manifest → write_outputs → QC。
产物再过一遍真实 reslice_qc.check,锁"端到端产物必须全绿"。
"""
import json

from conftest import SYNTH_LINES, SYNTH_MAN
from reslice_qc import check

import reslice_pipeline as rp


def test_e2e_process_file_with_fake_llm(workdir, monkeypatch):
    src = workdir / "synthetic.md"
    src.write_text("\n".join(SYNTH_LINES) + "\n", encoding="utf-8", newline="")
    reply = json.dumps(SYNTH_MAN, ensure_ascii=False)
    monkeypatch.setattr(
        rp, "call_llm",
        lambda prompt, **kw: (reply, {"prompt_tokens": 10, "completion_tokens": 5}))
    monkeypatch.setattr(rp, "OUT_ROOT", workdir / "out")

    res = rp.process_file(src, lambda s: None)

    assert res["units"] == 3
    assert res["prompt_tokens"] == 10 and res["completion_tokens"] == 5
    out = workdir / "out"
    mf_path = out / "synthetic.manifest.json"
    assert mf_path.exists()
    assert (out / "synthetic.annotated.md").exists()
    assert (out / "synthetic.md").exists()
    mf = json.loads(mf_path.read_text(encoding="utf-8"))
    # 产物元数据不得依赖私有配置(H-01):无配置环境也应是默认模型标签
    assert mf["model"] == rp.DEFAULT_MODEL
    # 端到端产物必须过真实 QC(12 项检查全绿)
    r = check(out / "synthetic.md")
    assert r["verdict"] == "PASS", r["issues"]

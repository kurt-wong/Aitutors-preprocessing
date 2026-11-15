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


def _write_synthetic_jsonl(md_path, lines):
    """G2-A 方案 A：同目录合成 ocr_raw.jsonl（逐非空行一块，确定性可匹配）。"""
    blocks, bid = [], 0
    for i, ln in enumerate(lines):
        if not ln.strip():
            continue
        blocks.append({
            "block_label": "text", "block_content": ln,
            "block_bbox": json.dumps([10, 20 + i * 10, 500, 30 + i * 10]),
            "block_id": bid, "block_order": bid + 1, "group_id": bid,
            "block_polygon_points": "[]",
        })
        bid += 1
    rec = {"logId": "e2e", "errorCode": 0, "errorMsg": "Success",
           "result": {"layoutParsingResults": [{
               "prunedResult": {"width": 1000, "height": 1400,
                                "parsing_res_list": blocks,
                                "layout_det_res": {"boxes": []}},
               "markdown": {"text": "", "images": {}},
           }], "dataInfo": {"numPages": 1}}}
    jl = md_path.parent / f"{md_path.stem}.ocr_raw.jsonl"
    jl.write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")
    return jl


def test_e2e_process_file_with_fake_llm(workdir, monkeypatch):
    src = workdir / "synthetic.md"
    src.write_text("\n".join(SYNTH_LINES) + "\n", encoding="utf-8", newline="")
    _write_synthetic_jsonl(src, SYNTH_LINES)
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
    # G2-A §13.3 消费证明：JSON 证据必须进入生成链（注入行级证据列并留痕）
    je = mf["annotation_meta"]["json_evidence"]
    assert je["page_split_consistent"] is True
    assert je["evidence_marker_count"] > 0
    assert je["match_counts"]["mapped_exact"] >= 10
    assert je["units"], "单元级证据指针必须存在"
    # 强制门禁结果必须随产物落盘（④：自动执行、非人工可选）
    jv = mf["annotation_meta"]["json_struct_verification"]
    assert jv["verdict"] == "PASS", jv["checks"]
    assert res["json_struct_gate"] == "PASS"
    # 端到端产物必须过真实 QC(12 项检查全绿)
    r = check(out / "synthetic.md")
    assert r["verdict"] == "PASS", r["issues"]

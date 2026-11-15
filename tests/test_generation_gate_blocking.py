# -*- coding: utf-8 -*-
"""E-1 阻断控制流测试（Owner 2026-11-15 裁决 + 残留放大器修复）。

覆盖：FAIL 抛 GenerationGateError / write_outputs 不被调用 / 无可用 Manifest /
*.gate.json 失败标记（run_id/verdict/原因）/ 陈旧 manifest 改名隔离 /
--resume 三条件谓词 / manifest 原子写 / 批量一失败一成功 / recompile 阻断。
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
import reslice_pipeline as rp  # noqa: E402
from conftest import SYNTH_LINES, SYNTH_MAN  # noqa: E402


def _write_md(p: Path):
    p.write_text("\n".join(SYNTH_LINES) + "\n", encoding="utf-8", newline="")
    return p


def _write_jsonl_full(md_path: Path):
    """逐非空行一块（可全映射）。"""
    blocks, bid = [], 0
    for i, ln in enumerate(SYNTH_LINES):
        if not ln.strip():
            continue
        blocks.append({
            "block_label": "text", "block_content": ln,
            "block_bbox": json.dumps([10, 20 + i * 10, 500, 30 + i * 10]),
            "block_id": bid, "block_order": bid + 1, "group_id": bid,
            "block_polygon_points": "[]",
        })
        bid += 1
    rec = {"logId": "t", "errorCode": 0, "errorMsg": "Success",
           "result": {"layoutParsingResults": [{
               "prunedResult": {"width": 1000, "height": 1400,
                                "parsing_res_list": blocks,
                                "layout_det_res": {"boxes": []}},
               "markdown": {"text": "", "images": {}}}],
               "dataInfo": {"numPages": 1}}}
    jl = md_path.parent / f"{md_path.stem}.ocr_raw.jsonl"
    jl.write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")
    return jl


def _write_jsonl_empty(md_path: Path):
    """零块 → 全行未映射 → 门禁真 FAIL（集成用）。"""
    rec = {"logId": "t", "errorCode": 0, "errorMsg": "Success",
           "result": {"layoutParsingResults": [{
               "prunedResult": {"width": 1000, "height": 1400,
                                "parsing_res_list": [],
                                "layout_det_res": {"boxes": []}},
               "markdown": {"text": "", "images": {}}}],
               "dataInfo": {"numPages": 1}}}
    jl = md_path.parent / f"{md_path.stem}.ocr_raw.jsonl"
    jl.write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")
    return jl


@pytest.fixture()
def fake_llm(monkeypatch):
    reply = json.dumps(SYNTH_MAN, ensure_ascii=False)
    monkeypatch.setattr(rp, "call_llm",
                        lambda prompt, **kw: (reply, {"prompt_tokens": 1, "completion_tokens": 1}))


class TestE1Blocking:
    def test_real_gate_fail_raises_and_blocks(self, tmp_path, fake_llm, monkeypatch):
        src = _write_md(tmp_path / "bad.md")
        _write_jsonl_empty(src)
        out = tmp_path / "out"
        monkeypatch.setattr(rp, "OUT_ROOT", out)
        with pytest.raises(rp.GenerationGateError):
            rp.process_file(src, lambda s: None)
        assert not list(out.rglob("*.manifest.json")), "FAIL 卷不得产出正式 Manifest"

    def test_write_outputs_not_called_on_fail(self, tmp_path, fake_llm, monkeypatch):
        src = _write_md(tmp_path / "bad.md")
        _write_jsonl_empty(src)
        monkeypatch.setattr(rp, "OUT_ROOT", tmp_path / "out")
        calls = []
        monkeypatch.setattr(rp, "write_outputs", lambda *a, **k: calls.append(a))
        with pytest.raises(rp.GenerationGateError):
            rp.process_file(src, lambda s: None)
        assert calls == []

    def test_gate_record_written_with_run_id_verdict_reason(self, tmp_path, fake_llm, monkeypatch):
        src = _write_md(tmp_path / "bad.md")
        _write_jsonl_empty(src)
        out = tmp_path / "out"
        monkeypatch.setattr(rp, "OUT_ROOT", out)
        with pytest.raises(rp.GenerationGateError):
            rp.process_file(src, lambda s: None)
        rec = json.loads((out / "bad.gate.json").read_text(encoding="utf-8"))
        assert rec["verdict"] == "FAIL"
        assert rec["run_id"] and rec["reason"]
        assert rec["gate"]["checks"]

    def test_stale_manifest_quarantined_not_mistaken(self, tmp_path, fake_llm, monkeypatch):
        src = _write_md(tmp_path / "bad.md")
        _write_jsonl_empty(src)
        out = tmp_path / "out"
        out.mkdir()
        stale = out / "bad.manifest.json"
        stale.write_text('{"stale": true}', encoding="utf-8")
        monkeypatch.setattr(rp, "OUT_ROOT", out)
        with pytest.raises(rp.GenerationGateError):
            rp.process_file(src, lambda s: None)
        assert not stale.exists(), "陈旧 manifest 不得留在可用名上"
        assert list(out.glob("bad.manifest.json.superseded-gatefail-*")), "应改名隔离（保留字节）"
        assert (out / "bad.gate.json").exists()

    def test_successful_run_atomic_no_tmp_left(self, tmp_path, fake_llm, monkeypatch):
        src = _write_md(tmp_path / "good.md")
        _write_jsonl_full(src)
        out = tmp_path / "out"
        monkeypatch.setattr(rp, "OUT_ROOT", out)
        rp.process_file(src, lambda s: None)
        assert (out / "good.manifest.json").is_file()
        assert not list(out.glob("*.tmp-*")), "原子写不得残留临时文件"

    def test_batch_one_fail_one_pass(self, tmp_path, fake_llm, monkeypatch):
        d = tmp_path / "src"
        d.mkdir()
        good = _write_md(d / "good.md")
        _write_jsonl_full(good)
        bad = _write_md(d / "bad.md")
        _write_jsonl_empty(bad)
        out = tmp_path / "bout"
        batch = tmp_path / "batch.json"
        batch.write_text(json.dumps([
            {"file": str(good), "tier": "t"}, {"file": str(bad), "tier": "t"},
        ]), encoding="utf-8")
        monkeypatch.setattr(sys, "argv",
                            ["reslice_pipeline.py", "--batch", str(batch), "--out", str(out)])
        rp.main()
        assert (out / "good.manifest.json").is_file()
        assert not (out / "bad.manifest.json").exists()
        assert (out / "bad.gate.json").exists()
        results = json.loads(
            (rp.ROOT / "data" / f"reslice_{out.name}_result.json").read_text(encoding="utf-8"))
        by_file = {Path(r["file"]).name: r for r in results}
        assert not by_file["good.md"].get("error")
        assert by_file["bad.md"].get("gate_failed") is True
        assert any("bad.md" in (x or "") for x in
                   [r.get("file") for r in results if r.get("gate_failed")])

    def test_recompile_fail_blocks(self, tmp_path, fake_llm):
        out = tmp_path / "rout"
        out.mkdir()
        src = _write_md(tmp_path / "legacy.md")  # 无 jsonl
        legacy = {"source_file": str(src), "model": "x",
                  "annotation_meta": {"prompt_version": "old"},
                  "units": [{"unit_id": "U01", "question_numbers": [1],
                             "stem_lines": [1, 1]}]}
        (out / "legacy.manifest.json").write_text(
            json.dumps(legacy, ensure_ascii=False), encoding="utf-8")
        n = rp.recompile_outputs(out)
        assert n == 0
        assert not (out / "legacy.manifest.json").exists()
        assert (out / "legacy.gate.json").exists()
        assert list(out.glob("legacy.manifest.json.superseded-gatefail-*"))


class TestResumePredicate:
    def _man(self, verdict="PASS", sha="abc"):
        return {"source_content_sha256": sha,
                "annotation_meta": {"json_struct_verification": {"verdict": verdict}}}

    def test_no_manifest_cannot_skip(self, tmp_path):
        ok, why = rp._resume_can_skip(tmp_path / "x.manifest.json", tmp_path / "x.md")
        assert ok is False and "no manifest" in why

    def test_corrupt_half_file_cannot_skip(self, tmp_path):
        (tmp_path / "x.md").write_text("a", encoding="utf-8")
        mf = tmp_path / "x.manifest.json"
        mf.write_text('{"half": ', encoding="utf-8")  # 崩溃半截文件
        ok, why = rp._resume_can_skip(mf, tmp_path / "x.md")
        assert ok is False and "corrupt" in why

    def test_gate_non_pass_cannot_skip(self, tmp_path):
        import hashlib
        src = tmp_path / "x.md"
        src.write_text("a", encoding="utf-8")
        sha = hashlib.sha256(src.read_bytes()).hexdigest()
        mf = tmp_path / "x.manifest.json"
        for v in ("FAIL", "WARN", None):
            man = self._man(verdict=v, sha=sha) if v else {"source_content_sha256": sha}
            mf.write_text(json.dumps(man), encoding="utf-8")
            ok, why = rp._resume_can_skip(mf, src)
            assert ok is False, v

    def test_sha_mismatch_cannot_skip(self, tmp_path):
        src = tmp_path / "x.md"
        src.write_text("a", encoding="utf-8")
        mf = tmp_path / "x.manifest.json"
        mf.write_text(json.dumps(self._man(sha="deadbeef")), encoding="utf-8")
        ok, why = rp._resume_can_skip(mf, src)
        assert ok is False and "mismatch" in why

    def test_all_three_ok_can_skip(self, tmp_path):
        import hashlib
        src = tmp_path / "x.md"
        src.write_text("a", encoding="utf-8")
        sha = hashlib.sha256(src.read_bytes()).hexdigest()
        mf = tmp_path / "x.manifest.json"
        mf.write_text(json.dumps(self._man(sha=sha)), encoding="utf-8")
        ok, why = rp._resume_can_skip(mf, src)
        assert ok is True and why == "ok"

# -*- coding: utf-8 -*-
"""T20BF-CLOSURE regression: recompile must not drop Producer provenance fields.

DSH finding: write_outputs rebuilt the manifest and only copied
identity_version/sections/source_content_sha256, silently dropping
original_file / original_sha256 / t179_* lineage. original_sha256 is the V3
documents identity domain (≠ source_content_sha256); losing it makes
preprocessing_import skip the original-bytes check.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import reslice_pipeline as rp  # noqa: E402
from conftest import make_repo  # noqa: E402


def _seed_provenance(man: dict) -> dict:
    man["original_file"] = "2021某校期中数学（教师版）.pdf"
    man["original_sha256"] = "a" * 64
    man["t179_provenance"] = {"run": "t179", "tier": "A"}
    man["t179_subject"] = "math"
    man["t179_subject_label"] = "数学"
    return man


def test_write_outputs_preserves_provenance_fields(workdir):
    src, mf, out_dir = make_repo(workdir)
    lines = src.read_text(encoding="utf-8").splitlines()
    man = _seed_provenance(json.loads(mf.read_text(encoding="utf-8")))
    rp.write_outputs(out_dir, src.stem, lines, man, [], {"warnings": []},
                     src.name, src)
    got = json.loads((out_dir / f"{src.stem}.manifest.json").read_text(encoding="utf-8"))
    for k in ("original_file", "original_sha256", "t179_provenance",
              "t179_subject", "t179_subject_label"):
        assert got.get(k) == man.get(k), f"write_outputs dropped {k!r}"


def test_recompile_preserves_provenance_fields(workdir):
    src, mf, out_dir = make_repo(workdir)
    lines = src.read_text(encoding="utf-8").splitlines()
    man = _seed_provenance(json.loads(mf.read_text(encoding="utf-8")))
    man["identity_version"] = 2
    mf.write_text(json.dumps(man, ensure_ascii=False, indent=1),
                  encoding="utf-8", newline="\n")
    rp.write_outputs(out_dir, src.stem, lines, man, [], {"warnings": []},
                     src.name, src)
    n = rp.recompile_outputs(out_dir)
    assert n == 1
    got = json.loads(mf.read_text(encoding="utf-8"))
    for k in ("original_file", "original_sha256", "t179_provenance",
              "t179_subject", "t179_subject_label", "identity_version"):
        assert got.get(k) == man.get(k), f"recompile dropped {k!r}"


def test_recompile_still_computes_source_content_sha256(workdir):
    """source_content_sha256 remains the Source-md identity (different domain)."""
    src, mf, out_dir = make_repo(workdir)
    lines = src.read_text(encoding="utf-8").splitlines()
    man = _seed_provenance(json.loads(mf.read_text(encoding="utf-8")))
    rp.write_outputs(out_dir, src.stem, lines, man, [], {"warnings": []},
                     src.name, src)
    rp.recompile_outputs(out_dir)
    got = json.loads(mf.read_text(encoding="utf-8"))
    assert got.get("source_content_sha256")
    assert got.get("original_sha256") == "a" * 64
    assert got["original_sha256"] != got["source_content_sha256"]
